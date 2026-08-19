"""Interface de terminal do LunaSpeech — tema noturno (cores ANSI).

Paleta "lua": índigo → violeta → azul-lunar → prateado, com estrelas douradas.
Funciona em Linux, macOS e Windows 10+ (habilita Virtual Terminal no Windows).
Cores são desligadas automaticamente se a saída não for um terminal (pipes/logs).

Menus navegáveis por **setas** ▲▼ + Enter **e por clique do mouse** (em terminais
com suporte a modo mouse SGR — Windows Terminal, iTerm2, gnome/konsole etc.).
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional, Sequence, Tuple

# ---------------------------------------------------------- paleta "lua" (256)
INDIGO = 57
VIOLET = 141
LUNAR = 117
SILVER = 252
PALE = 153
GOLD = 221
GREEN = 114
RED = 203
YELLOW = 221
DIM = 240

_GRADIENT = [INDIGO, 99, VIOLET, LUNAR, PALE, SILVER]

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
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
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
    print(f"   🌙   {gradient('LunaSpeech')}   ")
    print(fg(PALE, "        voz da lua  •  text-to-speech"))
    print(fg(GOLD, "        ✦  ") + dim(f"v{version}") + fg(GOLD, "  ✦"))
    print(fg(GOLD, _STARS[::-1]))
    print()


# --------------------------------------------------------------- perguntas
def menu(title: str, options: Sequence[Tuple[str, Optional[str]]]) -> None:
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


def pause(msg: str = "\n  (Enter para voltar)") -> None:
    try:
        input(dim(msg + " "))
    except (EOFError, KeyboardInterrupt):
        print()


# --------------------------------------------------------------- limpar tela
def clear() -> None:
    if not sys.stdout.isatty():
        return
    _enable_vt_windows()
    sys.stdout.write("\033[2J\033[3J\033[H")
    sys.stdout.flush()


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


# --------------------------------------------------------------- mouse / teclas
def _enable_mouse() -> None:
    _enable_vt_windows()
    sys.stdout.write("\033[?1000h\033[?1006h")  # eventos de botão + formato SGR
    sys.stdout.flush()


def _disable_mouse() -> None:
    sys.stdout.write("\033[?1006l\033[?1000l")
    sys.stdout.flush()


def _read_byte(timeout: float = 0.0) -> Optional[bytes]:
    """Lê 1 byte do stdin com timeout (None se nada em 'timeout' segundos)."""
    if os.name == "nt":
        import msvcrt

        end = time.time() + timeout if timeout else None
        while True:
            if msvcrt.kbhit():
                return msvcrt.getch()
            if end is None:
                continue
            if time.time() >= end:
                return None
    else:
        import select

        fd = sys.stdin.fileno()
        r, _, _ = select.select([fd], [], [], timeout)
        if r:
            return os.read(fd, 1)
    return None


def _read_until(delim: bytes, timeout: float) -> bytes:
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        b = _read_byte(timeout=min(0.05, max(0.0, end - time.time())))
        if b is None:
            continue
        buf += b
        if delim in buf:
            break
    return buf


def _cursor_row(timeout: float = 0.4) -> Optional[int]:
    """Linha atual do cursor via DEC CPR (\\033[6n). None se indisponível."""
    sys.stdout.write("\033[6n")
    sys.stdout.flush()
    data = _read_until(b"R", timeout)
    if not data.startswith(b"\x1b[") or b";" not in data or not data.endswith(b"R"):
        return None
    try:
        nums = data[2:-1]  # "row;col"
        return int(nums.split(b";")[0])
    except Exception:
        return None


def _read_event() -> Tuple:
    """Lê um evento: ('key', nome) ou ('mouse', btn, x, y, press_byte)."""
    b = _read_byte(timeout=3600)
    if not b:
        return ("key", "")
    if b == b"\x1b":
        b2 = _read_byte(timeout=0.03)
        if b2 is None:
            return ("key", "esc")
        if b2 == b"[":
            b3 = _read_byte(timeout=0.03)
            if b3 == b"<":  # mouse SGR: <btn;x;y M/m
                data = b""
                while True:
                    c = _read_byte(timeout=0.1)
                    if c is None:
                        break
                    data += c
                    if c in (b"M", b"m"):
                        break
                try:
                    body = data[:-1].decode()
                    btn, x, y = body.split(";")
                    return ("mouse", int(btn), int(x), int(y), data[-1:])
                except Exception:
                    return ("key", "")
            arrows = {b"A": "up", b"B": "down", b"C": "right", b"D": "left"}
            return ("key", arrows.get(b3, "esc"))
        return ("key", "esc")
    if b in (b"\r", b"\n"):
        return ("key", "enter")
    try:
        return ("key", b.decode("utf-8"))
    except Exception:
        return ("key", "")


def select_menu(title: str, options: Sequence[Tuple[str, Optional[str]]],
                current: int = 0) -> int:
    """Menu por setas ▲▼ + Enter **e clique do mouse**. Retorna índice, ou -1.

    Em terminais sem suporte a mouse ou não-interativos, cai para o menu digitado.
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

    # modo raw (unix) + mouse
    _enable_mouse()
    termios_old = None
    if os.name != "nt":
        try:
            import termios
            import tty

            fd = sys.stdin.fileno()
            termios_old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            termios_old = None  # stdin não é tty — segue sem modo raw

    start_row = _cursor_row()
    mouse_ok = start_row is not None

    def render() -> None:
        for i, (lbl, desc) in enumerate(options):
            arrow = fg(GOLD, "❯ ") if i == current else "  "
            num = fg(GOLD, f"{i + 1} ")
            label_s = bold(fg(SILVER, lbl)) if i == current else fg(SILVER, lbl)
            desc_s = f"  {dim(desc)}" if desc else ""
            sys.stdout.write(f"\r\033[K{arrow}{num}{label_s}{desc_s}\n")
        sys.stdout.flush()

    try:
        render()
        while True:
            ev = _read_event()
            if ev[0] == "key":
                k = ev[1]
                if k in ("up", "down"):
                    current = (current - 1) % n if k == "up" else (current + 1) % n
                elif k == "enter":
                    return current
                elif k in ("esc", "q"):
                    return -1
                elif k.isdigit() and 1 <= int(k) <= n:
                    return int(k) - 1
                else:
                    continue
            elif ev[0] == "mouse" and mouse_ok:
                _btn, _x, y, press = ev[1], ev[2], ev[3], ev[4]
                if _btn == 0 and press == b"M":  # botão esquerdo pressionado
                    idx = y - start_row
                    if 0 <= idx < n:
                        return idx
                continue
            else:
                continue
            # redesenha só o bloco de opções (sobe n linhas)
            sys.stdout.write(f"\033[{n}A")
            render()
    finally:
        if termios_old is not None:
            import termios

            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, termios_old)
        _disable_mouse()
        sys.stdout.write("\n")
        sys.stdout.flush()
