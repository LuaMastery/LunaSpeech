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


# --------------------------------------------------------------- limpar tela
def clear() -> None:
    """Limpa a tela e o histórico (scrollback); cursor no topo."""
    if not sys.stdout.isatty():
        return
    _enable_vt_windows()
    sys.stdout.write("\033[2J\033[3J\033[H")
    sys.stdout.flush()


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _read_key() -> str:
    """Lê uma tecla bruta. Retorna 'up','down','enter','esc' ou o caractere."""
    if os.name == "nt":
        import msvcrt

        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):  # tecla especial (setas etc.)
            ch2 = msvcrt.getch()
            return {72: "up", 80: "down", 75: "left", 77: "right"}.get(ord(ch2), "")
        v = ord(ch)
        if v == 13:
            return "enter"
        if v == 27:
            return "esc"
        return chr(v)
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":  # sequência de escape (setas)
                rest = sys.stdin.read(2)
                return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(rest, "esc")
            if ch in ("\r", "\n"):
                return "enter"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def select_menu(title: str, options: Sequence[Tuple[str, Optional[str]]],
                current: int = 0) -> int:
    """Menu navegável por setas ▲▼ + Enter. Retorna o índice, ou -1 se cancelado.

    ``options``: lista de ``(rótulo, descrição ou None)``. Em terminais não
    interativos, cai para o menu digitado (``menu`` + ``ask``).
    """
    options = list(options)
    n = len(options)
    if not _stdin_is_interactive():
        menu(title, [(str(i + 1), lbl, desc) for i, (lbl, desc) in enumerate(options)])
        ch = ask()
        if ch.isdigit() and 1 <= int(ch) <= n:
            return int(ch) - 1
        return -1

    print(fg(VIOLET, bold(f"  {title}")))
    hr()

    def render() -> None:
        for i, (lbl, desc) in enumerate(options):
            arrow = fg(GOLD, "❯ ") if i == current else "  "
            num = fg(GOLD, f"{i + 1} ")
            label_s = bold(fg(SILVER, lbl)) if i == current else fg(SILVER, lbl)
            desc_s = f"  {dim(desc)}" if desc else ""
            sys.stdout.write(f"\r\033[K{arrow}{num}{label_s}{desc_s}\n")
        sys.stdout.flush()

    render()
    while True:
        key = _read_key()
        if key in ("up", "down"):
            current = (current - 1) % n if key == "up" else (current + 1) % n
        elif key == "enter":
            sys.stdout.write("\n")
            return current
        elif key in ("esc", "q"):
            sys.stdout.write("\n")
            return -1
        elif key and key.isdigit() and 1 <= int(key) <= n:
            sys.stdout.write("\n")
            return int(key) - 1
        else:
            continue
        # redesenha só o bloco de opções (sobe n linhas)
        sys.stdout.write(f"\033[{n}A")
        render()
