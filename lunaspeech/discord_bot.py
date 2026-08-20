"""Bot de Discord do LunaSpeech — fala o texto que você pedir.

Como o bot envia o áudio como arquivo (anexo), não precisa de canal de voz
nem de opus/ffmpeg — é simples e robusto.

Setup:
  1. Crie um app/bot em https://discord.com/developers/applications → pegue o TOKEN.
  2. pip install discord.py
  3. Defina o token:  $env:DISCORD_TOKEN="seu_token"   (PowerShell)
                      export DISCORD_TOKEN=seu_token    (Linux/macOS)
  4. Rode:  lunaspeech discord     (ou:  python -m lunaspeech.discord_bot)

No Discord, use:  !fala Olá, pessoal!   → o bot responde com o áudio (.wav).
"""

from __future__ import annotations

import io
import os
import sys

from . import voices as voices_mod


def main() -> int:
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ Defina a variável DISCORD_TOKEN (veja https://discord.com/developers/applications).")
        return 1
    try:
        import discord
        from discord.ext import commands
    except ImportError:
        print("❌ Instale o discord.py:  pip install discord.py")
        return 1

    import soundfile as sf
    from .audio import normalize_peak
    from .core import LunaSpeech

    voice = os.environ.get("LUNASPEECH_VOICE", voices_mod.DEFAULT_VOICE)
    rate = float(os.environ.get("LUNASPEECH_RATE", "1.0"))
    tts = LunaSpeech(voice=voice)

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"✓ Bot conectado como {bot.user}  (voz: {voice})  —  use !fala <texto>")

    @bot.command()
    async def fala(ctx, *, texto: str):
        async with ctx.typing():
            result = tts.synthesize(texto, rate=rate)
            buf = io.BytesIO()
            sf.write(buf, normalize_peak(result.audio), result.sample_rate,
                     format="WAV", subtype="PCM_16")
            buf.seek(0)
            await ctx.reply(file=discord.File(buf, filename="lunaspeech.wav"))

    bot.run(token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
