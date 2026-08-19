"""Testes do menu interativo e do sistema de configuração."""

from __future__ import annotations

import pytest


def _mock_ui(monkeypatch, events):
    """Configura o ui para modo interativo com eventos (keys/mouse) pré-definidos."""
    import lunaspeech.ui as ui

    monkeypatch.setattr(ui, "_stdin_is_interactive", lambda: True)
    monkeypatch.setattr(ui, "_color", False)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "_cursor_row", lambda timeout=0.4: 1)
    monkeypatch.setattr(ui, "_enable_mouse", lambda: None)
    monkeypatch.setattr(ui, "_disable_mouse", lambda: None)
    it = iter(events)
    monkeypatch.setattr(ui, "_read_event", lambda: next(it))


def test_config_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("LUNASPEECH_CONFIG", str(tmp_path / "cfg.json"))
    from lunaspeech import config_store

    config_store.save({"voice": "cadu", "rate": 1.3})
    cfg = config_store.load()
    assert cfg["voice"] == "cadu"
    assert cfg["rate"] == 1.3
    config_store.set_value("voice", "faber")
    assert config_store.load()["voice"] == "faber"


def test_config_store_defaults_when_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("LUNASPEECH_CONFIG", str(tmp_path / "inexistente.json"))
    from lunaspeech import config_store
    assert config_store.load() == config_store.DEFAULTS


def test_select_menu_arrow_navigation(monkeypatch):
    _mock_ui(monkeypatch, [("key", "down"), ("key", "down"), ("key", "enter")])
    import lunaspeech.ui as ui
    idx = ui.select_menu("T", [("a", None), ("b", None), ("c", None), ("d", None)])
    assert idx == 2  # desceu 2 → "c"


def test_select_menu_wraps_up(monkeypatch):
    _mock_ui(monkeypatch, [("key", "up"), ("key", "enter")])  # do 0, "up" wrapa pro último
    import lunaspeech.ui as ui
    idx = ui.select_menu("T", [("a", None), ("b", None), ("c", None)])
    assert idx == 2


def test_select_menu_digit_and_cancel(monkeypatch):
    import lunaspeech.ui as ui
    _mock_ui(monkeypatch, [("key", "3")])
    assert ui.select_menu("T", [("a", None), ("b", None), ("c", None)]) == 2
    _mock_ui(monkeypatch, [("key", "q")])
    assert ui.select_menu("T", [("a", None), ("b", None)]) == -1
