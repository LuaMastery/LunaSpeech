"""Testes do reinício automático pós-atualização."""

from __future__ import annotations

import sys


def test_restart_program_execv(monkeypatch):
    import lunaspeech.__main__ as m
    called = {}
    monkeypatch.setattr(m.os, "execv", lambda p, a: called.update(path=p, args=a))
    m._restart_program()
    monkeypatch.delenv("LUNASPEECH_RESTARTED", raising=False)
    assert called["path"] == sys.executable
    assert called["args"][1:3] == ["-m", "lunaspeech"]  # python -m lunaspeech ...


def _patch_update(monkeypatch, newer=True, rc=0):
    """Patcha o módulo real lunaspeech.update (importado dentro das funções)."""
    import lunaspeech.update as upd
    monkeypatch.setattr(upd, "latest_version", lambda: "v99.0.0" if newer else None)
    monkeypatch.setattr(upd, "is_newer", lambda a, b: newer)
    monkeypatch.setattr(upd, "self_update", lambda v: rc)


def test_auto_update_guard_against_restart_loop(monkeypatch):
    import lunaspeech.__main__ as m
    monkeypatch.setenv("LUNASPEECH_RESTARTED", "1")  # já reiniciou uma vez
    _patch_update(monkeypatch, newer=True, rc=0)
    restarted = []
    monkeypatch.setattr(m, "_restart_program", lambda: restarted.append(True))
    m._maybe_auto_update()
    assert not restarted  # NÃO reinicia de novo (evita laço infinito)


def test_auto_update_restarts_when_clean(monkeypatch):
    import time
    import lunaspeech.__main__ as m
    monkeypatch.delenv("LUNASPEECH_RESTARTED", raising=False)
    _patch_update(monkeypatch, newer=True, rc=0)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    restarted = []
    monkeypatch.setattr(m, "_restart_program", lambda: restarted.append(True))
    m._maybe_auto_update()
    assert restarted  # instalou e reiniciou


def test_auto_update_no_restart_on_failure(monkeypatch):
    import time
    import lunaspeech.__main__ as m
    monkeypatch.delenv("LUNASPEECH_RESTARTED", raising=False)
    _patch_update(monkeypatch, newer=True, rc=1)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    restarted = []
    monkeypatch.setattr(m, "_restart_program", lambda: restarted.append(True))
    m._maybe_auto_update()
    assert not restarted  # falha na instalação -> sem reinício


def test_no_update_no_restart(monkeypatch):
    import lunaspeech.__main__ as m
    _patch_update(monkeypatch, newer=False)
    restarted = []
    monkeypatch.setattr(m, "_restart_program", lambda: restarted.append(True))
    m._maybe_auto_update()
    assert not restarted  # sem versão nova -> nada acontece
