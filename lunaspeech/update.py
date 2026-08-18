"""Verificação de atualizações e auto-instalação."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from typing import Optional, Tuple

REPO = "LuaMastery/LunaSpeech"
_API = f"https://api.github.com/repos/{REPO}/releases/latest"


def _ver_tuple(v: str) -> Tuple[int, ...]:
    """'v0.2.0' ou '0.2.0' -> (0, 2, 0). Tolerante a sufixos (-alpha etc.)."""
    v = (v or "").lstrip("v").strip()
    parts = []
    for chunk in v.split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def latest_release() -> Optional[dict]:
    """Metadados do release 'latest' no GitHub, ou None se indisponível."""
    try:
        req = urllib.request.Request(
            _API,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "lunaspeech"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except Exception:
        return None


def latest_version() -> Optional[str]:
    """Tag da última release (ex.: 'v0.2.0'), ou None."""
    rel = latest_release()
    return rel.get("tag_name") if rel else None


def is_newer(remote: str, local: str) -> bool:
    return _ver_tuple(remote) > _ver_tuple(local)


def self_update(version: Optional[str] = None) -> int:
    """Reinstala o LunaSpeech a partir de uma tag (padrão: latest). Retorna exit code."""
    tag = version or latest_version()
    if not tag:
        return 1
    url = f"git+https://github.com/{REPO}.git@{tag}"
    return subprocess.call([sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-deps", url])
