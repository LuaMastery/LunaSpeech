"""Testes do menu interativo e do sistema de configuração."""

from __future__ import annotations


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
    import lunaspeech.ui as ui

    monkeypatch.setattr(ui, "_stdin_is_interactive", lambda: True)
    monkeypatch.setattr(ui, "clear", lambda: None)
    keys = iter(["down", "down", "enter"])
    monkeypatch.setattr(ui, "_read_key", lambda: next(keys))
    idx = ui.select_menu("T", [("a", None), ("b", None), ("c", None), ("d", None)])
    assert idx == 2  # desceu 2 → "c"


def test_select_menu_wraps_up(monkeypatch):
    import lunaspeech.ui as ui

    monkeypatch.setattr(ui, "_stdin_is_interactive", lambda: True)
    monkeypatch.setattr(ui, "clear", lambda: None)
    keys = iter(["up", "enter"])  # do índice 0, "up" wrapa para o último
    monkeypatch.setattr(ui, "_read_key", lambda: next(keys))
    idx = ui.select_menu("T", [("a", None), ("b", None), ("c", None)])
    assert idx == 2


def test_select_menu_digit_and_cancel(monkeypatch):
    import lunaspeech.ui as ui

    monkeypatch.setattr(ui, "_stdin_is_interactive", lambda: True)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "_read_key", lambda: "3")
    assert ui.select_menu("T", [("a", None), ("b", None), ("c", None)]) == 2
    monkeypatch.setattr(ui, "_read_key", lambda: "q")
    assert ui.select_menu("T", [("a", None), ("b", None)]) == -1
