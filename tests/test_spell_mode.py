"""Testes da soletração automática e das versões Flash/Thinking."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
EN_TEST = REPO / "models" / "en-test" / "test_voice.onnx"
HAS_EN = EN_TEST.exists()


def test_should_spell_detection():
    from lunaspeech.text.numbers import should_spell
    # falar normalmente
    for t in ["casa", "Olá, tudo bem?", "oi", "programação", "R$ 1.234,56", "LunaSpeech"]:
        assert should_spell(t) is False, t
    # soletrar
    for t in ["xkcd", "www", "AB12", "x9k", "str", "mp3", "br"]:
        assert should_spell(t) is True, t


def test_should_spell_modes_logic():
    import lunaspeech.__main__ as m
    assert m._should_spell("xkcd", "on") is True     # sempre
    assert m._should_spell("casa", "on") is True
    assert m._should_spell("xkcd", "off") is False   # nunca
    assert m._should_spell("xkcd", "auto") is True   # detecta
    assert m._should_spell("casa", "auto") is False


def test_config_new_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("LUNASPEECH_CONFIG", str(tmp_path / "c.json"))
    from lunaspeech import config_store
    cfg = config_store.load()
    assert cfg["spell_mode"] == "auto"
    assert cfg["mode"] == "flash"


def test_crest_metric():
    import numpy as np
    from lunaspeech.core import _crest
    flat = np.ones(1000, dtype=np.float32) * 0.1
    spiky = flat.copy(); spiky[0] = 1.0
    assert _crest(flat) < _crest(spiky)  # pico isolado => crista maior


@pytest.mark.skipif(not HAS_EN, reason="modelo en-test ausente")
def test_thinking_mode_synthesizes():
    import numpy as np
    from lunaspeech import LunaSpeech
    from lunaspeech.core import _crest
    tts = LunaSpeech(voice="en-test", models_dir=str(REPO / "models"))
    text = "The quick brown fox jumps over the lazy dog."
    r_flash = tts.synthesize(text, mode="flash")
    r_think = tts.synthesize(text, mode="thinking")
    assert r_flash.audio.size > 0 and r_think.audio.size > 0
    assert r_think.sample_rate == r_flash.sample_rate
    # thinking escolhe a mais suave entre 4 variantes => crista <= mínimo das 4
    # (verificação indireta: crista do thinking é razoável/limitada)
    assert _crest(r_think.audio) < 10.0
