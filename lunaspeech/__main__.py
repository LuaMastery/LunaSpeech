"""CLI do LunaSpeech — síntese + menu interativo (tema noturno).

Uso:
    lunaspeech "Olá, mundo!"               # sintetiza texto
    lunaspeech "texto" --voice faber --rate 1.2 -o saida.wav
    lunaspeech                             # (sem texto) abre o MENU interativo
    echo "texto" | lunaspeech              # lê do stdin
    lunaspeech --list-voices
    lunaspeech --version
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__, ui, voices


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lunaspeech",
        description="🌙 LunaSpeech — fala qualquer texto (TTS leve, open source, em CPU).",
    )
    p.add_argument("text", nargs="?", help="Texto para falar. Se omitido (e stdin for terminal), abre o menu.")
    p.add_argument("-v", "--voice", default=voices.DEFAULT_VOICE,
                   help=f"Nome da voz (padrão: {voices.DEFAULT_VOICE}). Use --list-voices.")
    p.add_argument("-o", "--out", default="lunaspeech_out.wav", help="Arquivo WAV de saída.")
    p.add_argument("-r", "--rate", type=float, default=1.0,
                   help="Velocidade (1.3 = mais rápido, 0.8 = mais lento).")
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
    """Tenta reproduzir o WAV (best-effort, multiplataforma)."""
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


# ----------------------------------------------------------- menu interativo
def _menu_test(voice: str, models_dir: Optional[str]) -> None:
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
    if _synthesize_one(tts, text, out, 1.0) == 0:
        ui.info(f"Salvo em: {out}")
        if ui.ask("Reproduzir agora? [s/N]").lower().startswith("s"):
            if not _play(Path(out)):
                ui.warn("Não consegui reproduzir automaticamente — abra o arquivo manualmente.")


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
                "Atualização concluída." if rc == 0 else f"Falha ao atualizar (código {rc})."
            )
            ui.info("Reinicie o LunaSpeech para usar a nova versão.")
    else:
        ui.success(f"Você já está na versão mais recente ({__version__}).")


def _menu_reinstall() -> None:
    from . import update
    if ui.ask("Reinstalar o LunaSpeech da versão atual? [s/N]").lower().startswith("s"):
        ui.step("Reinstalando...")
        rc = update.self_update("v" + __version__ if not __version__.startswith("v") else __version__)
        (ui.success if rc == 0 else ui.error)(
            "Reinstalação concluída." if rc == 0 else f"Falha ao reinstalar (código {rc})."
        )


def interactive(args) -> int:
    ui.banner(__version__)
    voice = args.voice
    models_dir = args.models_dir
    while True:
        ui.menu(
            "O que você quer fazer?",
            [
                ("1", "Testar fala", "digite um texto e ouça"),
                ("2", "Buscar atualizações", "verifica nova versão no GitHub"),
                ("3", "Reinstalar", "reinstala o LunaSpeech"),
                ("4", "Listar vozes", "vozes disponíveis"),
                ("5", "Sair", None),
            ],
        )
        choice = ui.ask()
        try:
            if choice == "1":
                _menu_test(voice, models_dir)
            elif choice == "2":
                _menu_check_update()
            elif choice == "3":
                _menu_reinstall()
            elif choice == "4":
                voices.print_voices()
            elif choice in ("5", "q", "exit", "sair"):
                ui.info("Até logo! 🌙")
                break
            else:
                ui.warn("Opção inválida.")
            if choice != "5":
                ui.pause()
        except KeyboardInterrupt:
            print()
            ui.info("Até logo! 🌙")
            break
    return 0


# ------------------------------------------------------------------- entry
def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.list_voices:
        ui.banner(__version__)
        print(fg_voices_header())
        voices.print_voices()
        return 0

    text = args.text
    if text is None:
        # sem texto: se stdin é terminal, abre o menu; senão, lê do stdin
        if sys.stdin.isatty():
            return interactive(args)
        text = sys.stdin.read()
    text = (text or "").strip()
    if not text:
        ui.error("Nenhum texto fornecido.")
        return 2

    if sys.stdout.isatty():
        ui.banner(__version__)

    try:
        tts = _load_tts(args.voice, args.models_dir)
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Não foi possível preparar a voz '{args.voice}':\n{exc}")
        return 1

    if args.download_only:
        ui.success(f"Voz '{args.voice}' pronta.")
        return 0

    rc = _synthesize_one(tts, text, args.out, args.rate)
    if rc == 0:
        s = platform.system()
        hint = (f'start "" "{args.out}"' if s == "Windows"
                else f'afplay "{args.out}"' if s == "Darwin"
                else f"aplay {args.out}")
        ui.info(f"Para ouvir: {hint}")
    return rc


def fg_voices_header() -> str:
    return ui.fg(ui.VIOLET, "  Vozes disponíveis:")


if __name__ == "__main__":
    sys.exit(main())
