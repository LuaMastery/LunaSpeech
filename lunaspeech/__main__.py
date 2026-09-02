"""CLI do LunaSpeech — painel (setas/clique) + síntese + configurações.

Uso:
    lunaspeech "Olá, mundo!"               # sintetiza texto
    lunaspeech                             # abre o PAINEL (setas ▲▼ ou clique 🖱️)
    lunaspeech --voice faber --rate 1.2 -o saida.wav
    lunaspeech --list-voices
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import List, Optional

from . import __version__, config_store, tone as tone_mod, ui, voices


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lunaspeech",
        description="🌙 LunaSpeech — fala qualquer texto (TTS leve, open source, em CPU).",
    )
    p.add_argument("text", nargs="?", help="Texto para falar. Se omitido (e stdin for terminal), abre o painel.")
    p.add_argument("-v", "--voice", default=None, help="Voz (padrão: da configuração ou 'faber').")
    p.add_argument("-o", "--out", default="lunaspeech_out.wav", help="Arquivo WAV de saída.")
    p.add_argument("-r", "--rate", type=float, default=None, help="Velocidade (1.3 = mais rápido).")
    p.add_argument("-t", "--tone", default=None, choices=tone_mod.ALL_TONES,
                   help="Tom de voz (auto detecta a emoção do texto).")
    p.add_argument("--spell", action="store_true", help="Soletra o texto letra por letra.")
    p.add_argument("--mode", default=None, choices=["flash", "thinking"],
                   help="Versão: flash (rápida) ou thinking (lenta e aprimorada).")
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
            # winsound toca o WAV direto (stdlib), sem abrir player externo
            try:
                import winsound
                winsound.PlaySound(str(path), winsound.SND_FILENAME)
                return True
            except Exception:
                os.startfile(str(path))  # type: ignore[attr-defined]
                return True
        elif s == "Darwin":
            subprocess.Popen(["afplay", str(path)])
            return True
        else:
            subprocess.Popen(["aplay", "-q", str(path)])
            return True
    except Exception:
        return False


def _should_spell(text: str, spell_mode: str) -> bool:
    """Decide se soletra: flag on/off, ou auto (detecta pelo texto)."""
    if spell_mode == "on":
        return True
    if spell_mode == "off":
        return False
    from .text.numbers import should_spell
    return should_spell(text)


def _tom(tone: str) -> str:
    return tone_mod.TONE_LABEL.get(tone, tone)


def _synthesize_save(tts, text: str, out: str, rate: float, tone: str, mode: str = "flash") -> int:
    from .audio import write_wav
    result = tts.synthesize(text, rate=rate, tone=tone, mode=mode)
    if result.audio.size == 0:
        ui.error("Nenhum áudio gerado (texto vazio ou sem fonemas reconhecidos).")
        if result.missing_phonemes:
            ui.warn(f"fonemas não reconhecidos: {result.missing_phonemes}")
        return 1
    out_path = write_wav(out, result.audio, result.sample_rate)
    dur = len(result.audio) / result.sample_rate
    ui.success(f"Áudio gerado: {out_path}  ({dur:.2f}s, {result.sample_rate} Hz, tom: {_tom(result.tone)})")
    if result.missing_phonemes:
        ui.warn(f"fonemas não reconhecidos: {result.missing_phonemes}")
    return 0


def _synthesize_play_only(tts, text: str, rate: float, tone: str, mode: str = "flash") -> int:
    """Modo só teste: toca o áudio sem salvar arquivo (arquivo temporário é apagado)."""
    from .audio import write_wav
    result = tts.synthesize(text, rate=rate, tone=tone, mode=mode)
    if result.audio.size == 0:
        ui.error("Nenhum áudio gerado (texto vazio ou sem fonemas reconhecidos).")
        return 1
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    write_wav(tmp.name, result.audio, result.sample_rate)
    ui.success(f"Modo só teste (tom: {_tom(result.tone)}) — reproduzindo, nada foi salvo.")
    if result.missing_phonemes:
        ui.warn(f"fonemas não reconhecidos: {result.missing_phonemes}")
    if not _play(Path(tmp.name)):
        ui.warn("Não consegui reproduzir automaticamente.")
    try:
        os.unlink(tmp.name)
    except OSError:
        pass
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
    d = _v.voice_dir(voice, _v.models_dir(models_dir))
    present = bool(spec) and (d / spec.onnx_name).exists() and (d / spec.json_name).exists()
    (ui.success if present else ui.warn)(
        f"voz '{voice}': pronta" if present else f"voz '{voice}': será baixada ao testar fala")
    ui.success(f"versão: {__version__}")
    ui.hr()


def _maybe_auto_update() -> None:
    from . import update
    try:
        latest = update.latest_version()
    except Exception:
        return
    if latest and update.is_newer(latest, __version__):
        ui.step(f"Atualização automática: {__version__} → {latest}")
        rc = update.self_update(latest)
        if rc == 0:
            ui.success("Atualizado! Reinicie o LunaSpeech para concluir.")
        else:
            ui.warn(f"Atualização automática falhou (código {rc}).")


# ----------------------------------------------------------- painel (menu)
def _menu_test(voice: str, models_dir: Optional[str], rate: float, tone: str, test_only: bool) -> None:
    ui.clear()
    ui.banner(__version__)
    text = ui.ask("Texto para falar:")
    if not text:
        ui.warn("Texto vazio.")
        return
    # soletração automática (config: auto | on | off)
    if _should_spell(text, cfg.get("spell_mode", "auto")):
        from .text.numbers import spell_words
        text = spell_words(text)
        ui.info("Soletrando automaticamente (detectado).")
    try:
        tts = _load_tts(voice, models_dir)
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Não foi possível carregar a voz '{voice}':\n{exc}")
        return
    if test_only:
        _synthesize_play_only(tts, text, rate, tone, cfg.get("mode", "flash"))
        return
    out = os.path.join(os.path.expanduser("~"), "lunaspeech_menu.wav")
    if _synthesize_save(tts, text, out, rate, tone, cfg.get("mode", "flash")) == 0:
        ui.info(f"Salvo em: {out}")
        if ui.ask("Reproduzir agora? [s/N]").lower().startswith("s") and not _play(Path(out)):
            ui.warn("Não consegui reproduzir — abra o arquivo manualmente.")


def _menu_check_update() -> None:
    ui.clear()
    ui.banner(__version__)
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
    ui.clear()
    ui.banner(__version__)
    from . import update
    if ui.ask("Reinstalar o LunaSpeech da versão atual? [s/N]").lower().startswith("s"):
        ui.step("Reinstalando...")
        tag = __version__ if __version__.startswith("v") else "v" + __version__
        rc = update.self_update(tag)
        (ui.success if rc == 0 else ui.error)(
            "Reinstalação concluída." if rc == 0 else f"Falha ao reinstalar (código {rc}).")


def _pick_voice(cfg: dict) -> None:
    ui.clear(); ui.banner(__version__)
    names = list(voices.VOICES)
    opts = [(name, f"[{voices.VOICES[name].language}]") for name in names]
    cur = names.index(cfg["voice"]) if cfg["voice"] in names else 0
    idx = ui.select_menu("Escolha a voz padrão", opts, current=cur)
    if idx >= 0:
        cfg["voice"] = names[idx]
        config_store.save(cfg)
        ui.success(f"Voz padrão: {names[idx]}")


def _pick_rate(cfg: dict) -> None:
    ui.clear(); ui.banner(__version__)
    presets = [("0,7×  (lenta)", 0.7), ("0,85×", 0.85), ("1,0×  (normal)", 1.0),
               ("1,15×", 1.15), ("1,3×  (rápida)", 1.3), ("1,5×  (muito rápida)", 1.5)]
    cur = min(range(len(presets)), key=lambda i: abs(presets[i][1] - cfg["rate"]))
    idx = ui.select_menu("Velocidade padrão", [(lbl, None) for lbl, _ in presets], current=cur)
    if idx >= 0:
        cfg["rate"] = presets[idx][1]
        config_store.save(cfg)
        ui.success(f"Velocidade padrão: {presets[idx][1]:.2f}×")


def _pick_tone(cfg: dict) -> None:
    ui.clear(); ui.banner(__version__)
    labels = [("automático (detecta emoção)", "auto"), ("neutro", "neutro"),
              ("amigável", "amigavel"), ("alegre", "alegre"),
              ("raivoso", "raivoso"), ("triste", "triste")]
    cur = next((i for i, (_, v) in enumerate(labels) if v == cfg["tone"]), 0)
    idx = ui.select_menu("Tom de voz padrão", [(lbl, None) for lbl, _ in labels], current=cur)
    if idx >= 0:
        cfg["tone"] = labels[idx][1]
        config_store.save(cfg)
        ui.success(f"Tom padrão: {labels[idx][0]}")


def _toggle(cfg: dict, key: str, label: str) -> None:
    cfg[key] = not cfg.get(key, False)
    config_store.save(cfg)
    ui.success(f"{label}: {'ligado' if cfg[key] else 'desligado'}")


def _pick_spell_mode(cfg: dict) -> None:
    ui.clear(); ui.banner(__version__)
    labels = [("automática (a Luna detecta pelo texto)", "auto"),
              ("sempre soletrar", "on"), ("nunca soletrar", "off")]
    cur = next((i for i, (_, v) in enumerate(labels) if v == cfg.get("spell_mode", "auto")), 0)
    idx = ui.select_menu("Soletração", [(lbl, None) for lbl, _ in labels], current=cur)
    if idx >= 0:
        cfg["spell_mode"] = labels[idx][1]
        config_store.save(cfg)
        ui.success(f"Soletração: {labels[idx][0]}")


def _pick_mode(cfg: dict) -> None:
    ui.clear(); ui.banner(__version__)
    labels = [("⚡ Flash — resposta rápida", "flash"),
              ("🧠 Thinking — mais lenta, voz aprimorada", "thinking")]
    cur = 1 if cfg.get("mode", "flash") == "thinking" else 0
    idx = ui.select_menu("Versão da Luna", [(lbl, None) for lbl, _ in labels], current=cur)
    if idx >= 0:
        cfg["mode"] = labels[idx][1]
        config_store.save(cfg)
        ui.success(f"Versão: {labels[idx][0]}")


def _menu_settings_cli(cfg: dict) -> dict:
    while True:
        ui.clear()
        ui.banner(__version__)
        idx = ui.select_menu("Configurações (terminal)", [
            (f"Voz padrão: {cfg['voice']}", "escolher a voz"),
            (f"Velocidade: {cfg['rate']:.2f}×", "ajustar"),
            (f"Tom de voz: {_tom(cfg['tone'])}", "auto detecta emoção"),
            (f"Soletração: {cfg.get('spell_mode', 'auto')}", "auto/ligada/desligada"),
            (f"Versão: {'⚡ Flash' if cfg.get('mode', 'flash') == 'flash' else '🧠 Thinking'}",
             "flash (rápida) ou thinking (aprimorada)"),
            (f"Atualização automática: {'ligada' if cfg.get('auto_update') else 'desligada'}", "liga/desliga"),
            (f"Modo só teste: {'ligado' if cfg.get('test_only') else 'desligado'}", "toca sem salvar arquivo"),
            ("Restaurar padrões", None),
            ("Voltar", None),
        ])
        if idx == 0:
            _pick_voice(cfg)
        elif idx == 1:
            _pick_rate(cfg)
        elif idx == 2:
            _pick_tone(cfg)
        elif idx == 3:
            _pick_spell_mode(cfg)
        elif idx == 4:
            _pick_mode(cfg)
        elif idx == 5:
            _toggle(cfg, "auto_update", "Atualização automática")
        elif idx == 6:
            _toggle(cfg, "test_only", "Modo só teste")
        elif idx == 7:
            cfg = dict(config_store.DEFAULTS)
            config_store.save(cfg)
            ui.success("Configurações restauradas para o padrão.")
        else:
            return cfg
        ui.pause()


def _open_html_config() -> dict:
    from . import web_config
    ui.clear()
    ui.banner(__version__)
    try:
        httpd, url = web_config.open_and_serve()
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Não foi possível abrir as configurações no navegador: {exc}")
        ui.pause()
        return config_store.load()
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    ui.info(f"Página aberta no navegador: {url}")
    ui.pause("\n  (Edite e clique em Salvar no navegador. Enter aqui para voltar)")
    try:
        httpd.shutdown()
    except Exception:
        pass
    ui.success("Configurações recarregadas do arquivo.")
    return config_store.load()


def _menu_config_entry(cfg: dict) -> dict:
    ui.clear()
    ui.banner(__version__)
    idx = ui.select_menu("Como abrir as configurações?", [
        ("🌐  Navegador (HTML)", "abre uma página no navegador"),
        ("⌨️  Terminal (CLI)", "configura pelo painel"),
        ("Voltar", None),
    ])
    if idx == 0:
        return _open_html_config()
    if idx == 1:
        return _menu_settings_cli(cfg)
    return cfg


def _run_server(cfg: dict) -> None:
    ui.clear()
    ui.banner(__version__)
    from . import server
    try:
        httpd, url = server.serve(voice=cfg["voice"])
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Não foi possível iniciar o servidor: {exc}")
        return
    ui.success(f"Servidor LunaSpeech no ar: {url}")
    ui.info(f"Player web:  {url}")
    ui.info(f"API:  GET {url}/speak?text=olá   |   POST {url}/speak (JSON)")
    ui.info("Pressione Ctrl+C para parar e voltar ao menu.")
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass
        ui.success("Servidor parado.")


def _run_discord(cfg: dict) -> None:
    ui.clear()
    ui.banner(__version__)
    token = os.environ.get("DISCORD_TOKEN") or ui.ask("Cole o TOKEN do seu bot Discord:")
    if not token:
        ui.warn("Sem token não dá pra continuar.")
        return
    import importlib.util
    if importlib.util.find_spec("discord") is None:
        ui.step("Instalando discord.py (necessário pro bot)...")
        rc = subprocess.call([sys.executable, "-m", "pip", "install", "discord.py"])
        if rc != 0:
            ui.error("Falha ao instalar discord.py. Tente: pip install discord.py")
            return
    ui.info("Iniciando o bot Discord... (Ctrl+C para parar)")
    env = os.environ.copy()
    env["DISCORD_TOKEN"] = token
    env["LUNASPEECH_VOICE"] = cfg["voice"]
    subprocess.call([sys.executable, "-m", "lunaspeech.discord_bot"], env=env)


def _discord_info() -> None:
    ui.clear()
    ui.banner(__version__)
    print(ui.fg(ui.VIOLET, "  💬  LunaSpeech no Discord"))
    ui.hr()
    print(ui.dim("  O bot responde a !fala <texto> com o áudio (.wav) em anexo."))
    print()
    print("  1. Crie um app/bot em https://discord.com/developers/applications")
    print("     e copie o TOKEN.")
    print("  2. Instale o discord.py:  pip install discord.py")
    print("  3. Ative o 'Message Content Intent' nas configurações do bot.")
    print("  4. Convide o bot pro seu servidor.")
    print("  5. Rode por aqui (Rodar o bot agora) ou no terminal:  lunaspeech discord")
    print()
    print(ui.dim("  No Discord:  !fala Olá, pessoal!"))


def _api_examples() -> None:
    ui.clear()
    ui.banner(__version__)
    print(ui.fg(ui.VIOLET, "  📡  Usar o Luna em outros sistemas (API)"))
    ui.hr()
    print(ui.dim("  Inicie o servidor (lunaspeech serve) e qualquer sistema chama /speak:"))
    print()
    print("  • Player web:  http://localhost:8000/")
    print('  • curl:  curl "http://localhost:8000/speak?text=ol%C3%A1&voice=faber" -o out.wav')
    print("  • Python:  requests.get('http://localhost:8000/speak',")
    print("             params={'text':'olá','voice':'faber'}).content")
    print('  • POST JSON:  POST /speak  {"text":"olá","voice":"faber","rate":1.0}')
    print()
    print(ui.dim("  Endpoints: /  /speak  /voices  /tones  /health"))


def _menu_integrations(cfg: dict) -> None:
    while True:
        ui.clear()
        ui.banner(__version__)
        idx = ui.select_menu("Integrações — transferir o Luna pra outros sistemas", [
            ("🌐  Servidor web + API", "inicia um servidor local (outros sistemas chamam /speak)"),
            ("💬  Discord (bot)", "como colocar o Luna no Discord"),
            ("📡  Exemplos de API", "curl/Python/JS para outros sistemas"),
            ("Voltar", None),
        ])
        if idx == 0:
            _run_server(cfg)
        elif idx == 1:
            _discord_info()
            ui.pause()
            if ui.ask("Rodar o bot agora? [s/N]").lower().startswith("s"):
                _run_discord(cfg)
                continue
        elif idx == 2:
            _api_examples()
        else:
            return
        ui.pause()


def interactive(voice: str, rate: float, models_dir: Optional[str], cfg: dict) -> int:
    if cfg.get("auto_update"):
        _maybe_auto_update()
    import atexit
    ui.hide_cursor()
    atexit.register(ui.show_cursor)  # rede de segurança: sempre devolve o cursor
    while True:
        ui.clear()
        ui.banner(__version__)
        _startup_status(cfg["voice"], models_dir)
        idx = ui.select_menu("O que você quer fazer?", [
            ("Testar fala", "digite um texto e ouça"),
            ("Buscar atualizações", "verifica nova versão no GitHub"),
            ("Configurações", "navegador (HTML) ou terminal (CLI)"),
            ("Integrações", "transferir o Luna (Discord, servidor web/API)"),
            ("Reinstalar", "reinstala o LunaSpeech"),
            ("Listar vozes", "vozes disponíveis"),
            ("Sair", None),
        ])
        if idx == -1 or idx == 6:
            ui.info("Até logo! 🌙")
            break
        try:
            if idx == 0:
                _menu_test(cfg["voice"], models_dir, cfg["rate"], cfg["tone"], cfg.get("test_only", False))
                ui.pause()
            elif idx == 1:
                _menu_check_update()
                ui.pause()
            elif idx == 2:
                cfg = _menu_config_entry(cfg)
            elif idx == 3:
                _menu_integrations(cfg)
            elif idx == 4:
                _menu_reinstall()
                ui.pause()
            elif idx == 5:
                ui.clear()
                ui.banner(__version__)
                print(ui.fg(ui.VIOLET, "  Vozes disponíveis:"))
                voices.print_voices()
                ui.pause()
        except KeyboardInterrupt:
            print()
            ui.info("Até logo! 🌙")
            break
    ui.show_cursor()
    return 0


# ------------------------------------------------------------------- entry
def _cli_serve(extra: List[str]) -> int:
    cfg = config_store.load()
    host, port, voice = "127.0.0.1", 8000, cfg["voice"]
    it = iter(extra)
    for tok in it:
        if tok in ("-p", "--port"):
            try:
                port = int(next(it))
            except (StopIteration, ValueError):
                pass
        elif tok == "--host":
            try:
                host = next(it)
            except StopIteration:
                pass
        elif tok in ("-v", "--voice"):
            try:
                voice = next(it)
            except StopIteration:
                pass
    # containers/plataformas (Render, Hugging Face, Koyeb) definem PORT e HOST
    host = os.environ.get("LUNASPEECH_HOST", host)
    port = int(os.environ.get("PORT", str(port)))
    from . import server
    try:
        httpd, url = server.serve(host=host, port=port, voice=voice)
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Não foi possível iniciar o servidor: {exc}")
        return 1
    print(f"🌙 LunaSpeech servidor no ar: {url}")
    print(f"   Player web: {url}")
    print(f"   API:        {url}/speak?text=olá&voice={voice}")
    print("   Ctrl+C para parar.")
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.shutdown()
    return 0


def _cli_discord() -> int:
    from . import discord_bot
    return discord_bot.main()


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("serve", "server"):
        return _cli_serve(argv[1:])
    if argv and argv[0] == "discord":
        return _cli_discord()
    args = _build_parser().parse_args(argv)
    cfg = config_store.load()
    voice = args.voice or cfg["voice"]
    rate = args.rate if args.rate is not None else cfg["rate"]
    tone = args.tone or cfg["tone"]

    if args.list_voices:
        ui.banner(__version__)
        print(ui.fg(ui.VIOLET, "  Vozes disponíveis:"))
        voices.print_voices()
        return 0

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

    text = args.text
    if text is None:
        if sys.stdin.isatty():
            cfg["tone"] = tone
            return interactive(voice, rate, args.models_dir, cfg)
        text = sys.stdin.read()
    text = (text or "").strip()
    if not text:
        ui.error("Nenhum texto fornecido.")
        return 2

    mode = args.mode or cfg.get("mode", "flash")
    spell_mode = "on" if args.spell else cfg.get("spell_mode", "auto")
    if _should_spell(text, spell_mode):
        from .text.numbers import spell_words
        text = spell_words(text)

    if cfg.get("test_only"):
        return _synthesize_play_only(tts, text, rate, tone, mode)

    rc = _synthesize_save(tts, text, args.out, rate, tone, mode)
    if rc == 0:
        s = platform.system()
        hint = (f'start "" "{args.out}"' if s == "Windows"
                else f'afplay "{args.out}"' if s == "Darwin"
                else f"aplay {args.out}")
        ui.info(f"Para ouvir: {hint}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
