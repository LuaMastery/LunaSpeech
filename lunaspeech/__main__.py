"""CLI do LunaSpeech.

Uso:

    python -m lunaspeech "Olá, mundo!"
    python -m lunaspeech "Texto mais rápido." --rate 1.3 --out rapido.wav
    python -m lunaspeech --voice en-test "Hello world."     # voz de teste (GitHub)
    echo "Texto do stdin" | python -m lunaspeech
    python -m lunaspeech --list-voices
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from . import voices


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lunaspeech",
        description="🌙 LunaSpeech — fala qualquer texto (TTS leve, open source, em CPU).",
    )
    p.add_argument("text", nargs="?", help="Texto para falar (se omitido, lê do stdin).")
    p.add_argument("-v", "--voice", default=voices.DEFAULT_VOICE,
                   help=f"Nome da voz (padrão: {voices.DEFAULT_VOICE}). Use --list-voices para ver todas.")
    p.add_argument("-o", "--out", default="lunaspeech_out.wav",
                   help="Arquivo WAV de saída (padrão: lunaspeech_out.wav).")
    p.add_argument("-r", "--rate", type=float, default=1.0,
                   help="Velocidade relativa (ex.: 1.3 = mais rápido, 0.8 = mais lento).")
    p.add_argument("--models-dir", default=None,
                   help="Diretório de vozes (padrão: $LUNASPEECH_MODELS ou ~/.local/share/lunaspeech/models).")
    p.add_argument("--download-only", action="store_true",
                   help="Apenas baixa/prepara a voz, sem sintetizar.")
    p.add_argument("-l", "--list-voices", action="store_true", help="Lista as vozes disponíveis.")
    p.add_argument("--version", action="version", version=f"lunaspeech {__version__}")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.list_voices:
        print("Vozes disponíveis:")
        voices.print_voices()
        return 0

    # carrega a voz (baixa se necessário)
    try:
        from .core import LunaSpeech

        tts = LunaSpeech(voice=args.voice, models_dir=args.models_dir)
    except Exception as exc:  # noqa: BLE001 - mensagem já amigável
        print(f"❌ Não foi possível preparar a voz '{args.voice}':\n{exc}", file=sys.stderr)
        return 1

    if args.download_only:
        print(f"✓ Voz '{args.voice}' pronta.")
        return 0

    # obtém o texto (argumento ou stdin)
    text = args.text
    if text is None:
        text = sys.stdin.read()
    text = (text or "").strip()
    if not text:
        print("❌ Nenhum texto fornecido.", file=sys.stderr)
        return 2

    try:
        from .audio import write_wav

        result = tts.synthesize(text, rate=args.rate)
        if result.audio.size == 0:
            print("❌ Nenhum áudio gerado (texto vazio ou sem fonemas reconhecidos).", file=sys.stderr)
            return 1
        out_path = write_wav(args.out, result.audio, result.sample_rate)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Falha ao sintetizar: {exc}", file=sys.stderr)
        return 1

    dur = len(result.audio) / result.sample_rate
    miss = result.missing_phonemes or {}
    extra = f"  (fonemas não reconhecidos: {miss})" if miss else ""
    print(f"✓ Áudio gerado: {out_path}  ({dur:.2f}s, {result.sample_rate} Hz, voz={args.voice}){extra}")
    print(f"  Para ouvir: aplay {out_path}   # Linux")
    return 0


if __name__ == "__main__":
    sys.exit(main())
