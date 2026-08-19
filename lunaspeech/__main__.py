"""CLI do LunaSpeech — síntese + menu interativo navegável (tema noturno).

Uso:
    lunaspeech "Olá, mundo!"               # sintetiza texto
    lunaspeech                             # (sem texto) abre o PAINEL (setas + Enter)
    lunaspeech --voice faber --rate 1.2 -o saida.wav
    echo "texto" | lunaspeech
    lunaspeech --list-voices
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__, config_store, ui, voices


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lunaspeech",
        description="🌙 LunaSpeech — fala qualquer texto (TTS leve, open source, em CPU).",
    )
    p.add_argument("text", nargs="?", help="Texto para falar. Se omitido (e stdin for terminal), abre o painel.")
    p.add_argument("-v", "--voice", default=None, help="Voz (padrão: da configuração ou 'faber').")
    p.add_argument("-o", "--out", default="lunaspeech_out.wav", help="Arquivo WAV de saída.")
    p.add_argument("-r", "--rate", type=float, default=None, help="Velocidade (1.3 = mais rápido).")
    p.add_argument("--models-dir", default=None, help="Diretório de vozes.")
    p.add_argument("--download-only", action="store_true", help="Apenas prepara a voz, sem sintetizar.")
    p.add_argument("-l", "--list-voices", action="store_true", help="Lista as vozes disponíveis.")
    p.add_argument("--version", action="version", version=f"lunaspeech {__version__}")
    return p


# --------------------------------------------------------------- helpers
def _load_tts(voice: str, models_dir: Optional[str]):
    from .core import LunaSpeech
    return LunaSpeech(voice=voice, models_dir=models_dir)


def _play(path: Path) -> bool:
    s = platform.system()
    try:
        if s == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif s == "Darwin":
            subprocess.Popen(["afplay", str(path)])
        else:
            subprocess.Popen(["aplay", "-q", str(path)])
        return True
    except Exception:
        return False


def _synthesize_one(tts, text: str, out: str, rate: float) -> int:
    from .audio import write_wav
    result = tts.synthesize(text, rate=rate)
    if result.audio.size == 0:
        ui.error("Nenhum áudio gerado (texto vazio ou sem fonemas reconhecidos).")
        if result.missing_phonemes:
            ui.warn(f"fonemas não reconhecidos: {result.missing_phonemes}")
        return 1
    out_path = write_wav(out, result.audio, result.sample_rate)
    dur = len(result.audio) / result.sample_rate
    ui.success(f"Áudio gerado: {out_path}  ({dur:.2f}s, {result.sample_rate} Hz)")
    if result.missing_phonemes:
        ui.warn(f"fonemas não reconhecidos: {result.missing_phonemes}")
    return 0


def _startup_status(voice: str, models_dir: Optional[str]) -> None:
    from .text.phonemize import available_backend
    from . import voices as _v
    ui.hr()
    backend = available_backend()
    if backend == "nenhum":
        ui.error("fonetizador: nenhum (instale espeak-ng ou piper-phonemize)")
    else:
        ui.success(f"fonetizador: {backend}")
    spec = _v.VOICES.get(voice)
    present = bool(spec) and (
        (_v.voice_dir(voice, _v.models_dir(models_dir)) / spec.onnx_name).exists()
        and (_v.voice_dir(voice, _v.models_dir(models_dir)) / spec.json_name).exists()
    )
    (ui.success if present else ui.warn)(
        f"voz '{voice}': pronta" if present else f"voz '{voice}': será baixada ao testar fala"
    )
    ui.success(f"versão: {__version__}")
    ui.hr()


# ----------------------------------------------------------- painel (menu)
def _menu_test(voice: str, models_dir: Optional[str], rate: float) -> None:
    text = ui.ask("Texto para falar:")
    if not text:
        ui.warn("Texto vazio.")
        return
    try:
        tts = _load_tts(voice, models_dir)
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Não foi possível carregar a voz '{voice}':\n{exc}")
        return
    out = os.path.join(os.path.expanduser("~"), "lunaspeech_menu.wav")
    if _synthesize_one(tts, text, out, rate) == 0:
        ui.info(f"Salvo em: {out}")
        if ui.ask("Reproduzir agora? [s/N]").lower().startswith("s") and not _play(Path(out)):
            ui.warn("Não consegui reproduzir — abra o arquivo manualmente.")


def _menu_check_update() -> None:
    from . import update
    ui.step("Verificando atualizações...")
    latest = update.latest_version()
    if not latest:
        ui.error("Não foi possível acessar o GitHub (sem internet?).")
        return
    if update.is_newer(latest, __version__):
        ui.warn(f"Nova versão disponível: {latest} (você está na {__version__}).")
        if ui.ask(f"Atualizar para {latest}? [s/N]").lower().startswith("s"):
            rc = update.self_update(latest)
            (ui.success if rc == 0 else ui.error)(
                "Atualização concluída." if rc == 0 else f"Falha ao atualizar (código {rc}).")
            ui.info("Reinicie o LunaSpeech para usar a nova versão.")
    else:
        ui.success(f"Você já está na versão mais recente ({__version__}).")


def _menu_reinstall() -> None:
    from . import update
    if ui.ask("Reinstalar o LunaSpeech da versão atual? [s/N]").lower().startswith("s"):
        ui.step("Reinstalando...")
        tag = __version__ if __version__.startswith("v") else "v" + __version__
        rc = update.self_update(tag)
        (ui.success if rc == 0 else ui.error)(
            "Reinstalação concluída." if rc == 0 else f"Falha ao reinstalar (código {rc}).")


def _pick_voice(cfg: dict) -> None:
    names = list(voices.VOICES)
    opts = [(name, f"[{voices.VOICES[name].language}]") for name in names]
    idx = ui.select_menu("Escolha a voz padrão", opts, current=max(names.index(cfg["voice"]), 0) if cfg["voice"] in names else 0)
    if idx >= 0:
        cfg["voice"] = names[idx]
        config_store.save(cfg)
        ui.success(f"Voz padrão definida: {names[idx]}")


def _pick_rate(cfg: dict) -> None:
    presets = [("0,7×  (lenta)", 0.7), ("0,85×", 0.85), ("1,0×  (normal)", 1.0),
               ("1,15×", 1.15), ("1,3×  (rápida)", 1.3), ("1,5×  (muito rápida)", 1.5)]
    cur = min(range(len(presets)), key=lambda i: abs(presets[i][1] - cfg["rate"]))
    idx = ui.select_menu("Velocidade padrão", [(lbl, None) for lbl, _ in presets], current=cur)
    if idx >= 0:
        cfg["rate"] = presets[idx][1]
        config_store.save(cfg)
        ui.success(f"Velocidade padrão: {presets[idx][1]:.2f}×")


def _menu_settings(cfg: dict) -> dict:
    while True:
        ui.clear()
        ui.banner(__version__)
        idx = ui.select_menu("Configurações", [
            (f"Voz padrão: {cfg['voice']}", "escolher a voz padrão"),
            (f"Velocidade padrão: {cfg['rate']:.2f}×", "ajustar velocidade"),
            ("Restaurar padrões", "voz faber, 1.0×"),
            ("Voltar", None),
        ])
        if idx == 0:
            _pick_voice(cfg)
        elif idx == 1:
            _pick_rate(cfg)
        elif idx == 2:
            cfg = dict(config_store.DEFAULTS)
            config_store.save(cfg)
            ui.success("Configurações restauradas para o padrão.")
        else:
            return cfg
        ui.pause()


def interactive(voice: str, rate: float, models_dir: Optional[str], cfg: dict) -> int:
    ui.clear()
    ui.banner(__version__)
    _startup_status(voice, models_dir)
    while True:
        idx = ui.select_menu("O que você quer fazer?", [
            ("Testar fala", "digite um texto e ouça"),
            ("Buscar atualizações", "verifica nova versão no GitHub"),
            ("Configurações", "voz e velocidade padrão"),
            ("Reinstalar", "reinstala o LunaSpeech"),
            ("Listar vozes", "vozes disponíveis"),
            ("Sair", None),
        ])
        if idx == -1 or idx == 5:
            ui.info("Até logo! 🌙")
            break
        try:
            if idx == 0:
                _menu_test(cfg["voice"], models_dir, cfg["rate"])
            elif idx == 1:
                _menu_check_update()
            elif idx == 2:
                cfg = _menu_settings(cfg)
                voice = cfg["voice"]
            elif idx == 3:
                _menu_reinstall()
            elif idx == 4:
                voices.print_voices()
            ui.pause()
        except KeyboardInterrupt:
            print()
            ui.info("Até logo! 🌙")
            break
    return 0


# ------------------------------------------------------------------- entry
def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    cfg = config_store.load()
    voice = args.voice or cfg["voice"]
    rate = args.rate if args.rate is not None else cfg["rate"]

    if args.list_voices:
        ui.banner(__version__)
        print(ui.fg(ui.VIOLET, "  Vozes disponíveis:"))
        voices.print_voices()
        return 0

    text = args.text
    if text is None:
        if sys.stdin.isatty():
            return interactive(voice, rate, args.models_dir, cfg)
        text = sys.stdin.read()
    text = (text or "").strip()
    if not text:
        ui.error("Nenhum texto fornecido.")
        return 2

    if sys.stdout.isatty():
        ui.banner(__version__)

    try:
        tts = _load_tts(voice, args.models_dir)
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Não foi possível preparar a voz '{voice}':\n{exc}")
        return 1

    if args.download_only:
        ui.success(f"Voz '{voice}' pronta.")
        return 0

    rc = _synthesize_one(tts, text, args.out, rate)
    if rc == 0:
        s = platform.system()
        hint = (f'start "" "{args.out}"' if s == "Windows"
                else f'afplay "{args.out}"' if s == "Darwin"
                else f"aplay {args.out}")
        ui.info(f"Para ouvir: {hint}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
