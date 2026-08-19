"""Testes do painel web/CLI, mouse e novas configurações."""

from __future__ import annotations

import threading
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer


def test_config_new_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("LUNASPEECH_CONFIG", str(tmp_path / "c.json"))
    from lunaspeech import config_store
    cfg = config_store.load()
    assert cfg["auto_update"] is True
    assert cfg["test_only"] is False


def test_web_config_page_has_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("LUNASPEECH_CONFIG", str(tmp_path / "c.json"))
    from lunaspeech import web_config, config_store
    html = web_config.page(config_store.load())
    for field in ['name="voice"', 'name="rate"', 'name="tone"',
                  'name="auto_update"', 'name="test_only"']:
        assert field in html
    assert "LunaSpeech" in html


def test_web_config_save_handler(tmp_path, monkeypatch):
    monkeypatch.setenv("LUNASPEECH_CONFIG", str(tmp_path / "c.json"))
    from lunaspeech import web_config, config_store
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web_config._Handler)
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}"
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        data = urllib.parse.urlencode(
            {"voice": "cadu", "rate": "1.2", "tone": "alegre", "auto_update": "on"}
        ).encode()
        resp = urllib.request.urlopen(
            urllib.request.Request(url + "/save", data=data, method="POST"), timeout=5
        ).read().decode()
        assert "salvas" in resp.lower()
    finally:
        httpd.shutdown()
    cfg = config_store.load()
    assert cfg["voice"] == "cadu"
    assert cfg["tone"] == "alegre"
    assert cfg["auto_update"] is True
    assert cfg["test_only"] is False  # não enviado na form -> False


def test_select_menu_mouse_click(monkeypatch):
    import lunaspeech.ui as ui
    monkeypatch.setattr(ui, "_stdin_is_interactive", lambda: True)
    monkeypatch.setattr(ui, "_color", False)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "_cursor_row", lambda timeout=0.4: 5)  # 1ª opção na linha 5
    monkeypatch.setattr(ui, "_read_event", lambda: ("mouse", 0, 3, 7, b"M"))  # clique na linha 7
    monkeypatch.setattr(ui, "_enable_mouse", lambda: None)
    monkeypatch.setattr(ui, "_disable_mouse", lambda: None)
    idx = ui.select_menu("T", [("a", None), ("b", None), ("c", None), ("d", None)])
    assert idx == 2  # linha 7 - linha 5 = índice 2 ("c")


def test_select_menu_mouse_outside_returns_nothing_then_enter(monkeypatch):
    import lunaspeech.ui as ui
    events = iter([("mouse", 0, 3, 1, b"M"), ("key", "enter")])  # clique fora (linha 1)
    monkeypatch.setattr(ui, "_stdin_is_interactive", lambda: True)
    monkeypatch.setattr(ui, "_color", False)
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "_cursor_row", lambda timeout=0.4: 5)
    monkeypatch.setattr(ui, "_read_event", lambda: next(events))
    monkeypatch.setattr(ui, "_enable_mouse", lambda: None)
    monkeypatch.setattr(ui, "_disable_mouse", lambda: None)
    idx = ui.select_menu("T", [("a", None), ("b", None)])
    assert idx == 0  # clique fora ignorado; Enter seleciona o atual (0)


def test_synthesize_play_only(monkeypatch):
    import numpy as np
    from lunaspeech.engine.base import SynthesisResult
    import lunaspeech.__main__ as m
    monkeypatch.setattr(m, "_play", lambda p: True)

    class FakeTTS:
        def synthesize(self, text, rate=1.0, tone="auto"):
            return SynthesisResult(audio=np.ones(8000, dtype=np.float32) * 0.3,
                                   sample_rate=16000, tone="neutro")

    rc = m._synthesize_play_only(FakeTTS(), "teste", 1.0, "auto")
    assert rc == 0
