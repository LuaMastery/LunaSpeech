"""Configurações persistentes do LunaSpeech (preferências do usuário).

Armazenadas em ``~/.lunaspeech.json`` (ou ``$LUNASPEECH_CONFIG``). A CLI e o
menu interativo leem essas preferências como padrão (voz, velocidade).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULTS: Dict[str, Any] = {
    "voice": "faber",
    "rate": 1.0,
}


def config_path() -> Path:
    return Path(os.environ.get("LUNASPEECH_CONFIG") or (Path.home() / ".lunaspeech.json"))


def load() -> Dict[str, Any]:
    """Carrega as preferências (mescladas com os padrões). Nunca lança exceção."""
    cfg = dict(DEFAULTS)
    try:
        p = config_path()
        if p.exists():
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        pass
    # sanity
    if not isinstance(cfg.get("rate"), (int, float)) or not cfg["rate"]:
        cfg["rate"] = DEFAULTS["rate"]
    return cfg


def save(cfg: Dict[str, Any]) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def set_value(key: str, value: Any) -> Dict[str, Any]:
    cfg = load()
    cfg[key] = value
    save(cfg)
    return cfg
