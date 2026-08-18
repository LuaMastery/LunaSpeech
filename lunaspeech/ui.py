"""Interface de terminal do LunaSpeech — tema noturno (cores ANSI).

Paleta "lua": índigo → violeta → azul-lunar → prateado, com estrelas douradas.
Funciona em Linux, macOS e Windows 10+ (habilita Virtual Terminal no Windows).
Cores são desligadas automaticamente se a saída não for um terminal (pipes/logs).
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------- paleta "lua" (256)
INDIGO = 57      # noite profunda
VIOLET = 141     # violeta lunar
LUNAR = 117      # azul-lunar / brilho
SILVER = 252     # luz da lua
PALE = 153       # azul-pálido
GOLD = 221       # estrela dourada
GREEN = 114      # sucesso
RED = 203        # erro
YELLOW = 221     # aviso
DIM = 240        # cinza-esmaecido

_GRADIENT = [INDIGO, 99, VIOLET, LUNAR, PALE, SILVER]  # noite → lua

_color = None


def _color_enabled() -> bool:
    global _color
    if _color is None:
        if os.name == "nt":
            _enable_vt_windows()
        _color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    return _color


def _enable_vt_windows() -> None:
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VT_PROCESSING
    except Exception:
        pass


# ----------------------------------------------------------------- primitivas
def fg(code: int, text: str) -> str:
    return f"\x1b[38;5;{code}m{text}\x1b[0m" if _color_enabled() else text


def bold(text: str) -> str:
    return f"\x1b[1m{text}\x1b[0m" if _color_enabled() else text


def dim(text: str) -> str:
    return f"\x1b[2m{text}\x1b[0m" if _color_enabled() else text


def gradient(text: str, palette: Sequence[int] = _GRADIENT) -> str:
    if not _color_enabled() or not text:
        return text
    n = len(text)
    out = []
    for i, ch in enumerate(text):
        col = palette[min(int(i / max(1, n - 1) * (len(palette) - 1)), len(palette) - 1)]
        out.append(f"\x1b[38;5;{col}m{ch}")
    return "".join(out) + "\x1b[0m"


# --------------------------------------------------------------- mensagens
def info(msg: str) -> None:
    print(f"{fg(LUNAR, '→')} {msg}")


def step(msg: str) -> None:
    print(f"{fg(VIOLET, '→')} {msg}")


def success(msg: str) -> None:
    print(f"{fg(GREEN, '✓')} {msg}")


def warn(msg: str) -> None:
    print(f"{fg(YELLOW, '⚠')} {msg}")


def error(msg: str) -> None:
    print(f"{fg(RED, '✗')} {msg}")


def hr(char: str = "─", width: int = 52) -> None:
    print(fg(INDIGO, char * width))


# ------------------------------------------------------------------ banner
_STARS = "  ✦     ·     ✧        ·       ✦   "


def banner(version: str) -> None:
    print()
    print(fg(GOLD, _STARS))
    line = f"   🌙   {gradient('LunaSpeech')}   "
    print(line)
    print(fg(PALE, "        voz da lua  •  text-to-speech"))
    print(fg(GOLD, f"        ✦  ") + dim(f"v{version}") + fg(GOLD, "  ✦"))
    print(fg(GOLD, _STARS[::-1]))
    print()


# ------------------------------------------------------------------- menu
def menu(title: str, options: Sequence[Tuple[str, str, Optional[str]]]) -> None:
    """Imprime um menu. options = [(número, rótulo, descrição ou None), ...]."""
    print(fg(VIOLET, bold(f"  {title}")))
    hr()
    for num, label, desc in options:
        num_s = fg(GOLD, f"  {num} ")
        label_s = fg(SILVER, label)
        desc_s = f"  {dim(desc)}" if desc else ""
        print(f"{num_s} {label_s}{desc_s}")
    print()


def ask(prompt: str = "") -> str:
    try:
        return input(f"{fg(VIOLET, '❯')} {prompt}").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def pause() -> None:
    try:
        input(dim("\n  (Enter para voltar ao menu) "))
    except (EOFError, KeyboardInterrupt):
        print()
