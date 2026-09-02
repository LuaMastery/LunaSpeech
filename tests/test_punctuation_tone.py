"""Testes: vírgula/pausa, contorno de pergunta e emoções expressivas."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
HAS_EN = (REPO / "models" / "en-test" / "test_voice.onnx").exists()


def test_cli_phonemizer_comma_stays_in_sentence(monkeypatch):
    """No backend espeak CLI, cláusulas com vírgula ficam NA MESMA frase."""
    import importlib
    ph = importlib.import_module("lunaspeech.text.phonemize")

    class R:
        stdout = "bl\u025b\u02c8ez\u0250 ,\n\u0283ow d\u0292i \u02c8b\u0254l\u0250\n"
    monkeypatch.setattr(ph, "subprocess", type("S", (), {"run": staticmethod(lambda *a, **k: R())}))
    monkeypatch.setattr(ph, "_find_espeak", lambda: "/fake/espeak-ng")
    out = ph.phonemize("beleza, show de bola", "pt-br")
    assert len(out) == 1            # vírgula NÃO fecha a frase
    assert "," in out[0] and " " in out[0]  # vírgula vira pausa curta interna


def test_cli_phonemizer_question_terminator(monkeypatch):
    import importlib
    ph = importlib.import_module("lunaspeech.text.phonemize")

    class R:
        stdout = "t\u02c8udu b\u025b\u0250\n"  # espeak 'comeu' o ?
    monkeypatch.setattr(ph, "subprocess", type("S", (), {"run": staticmethod(lambda *a, **k: R())}))
    monkeypatch.setattr(ph, "_find_espeak", lambda: "/fake/espeak-ng")
    out = ph.phonemize("Tudo bem?", "pt-br")
    assert out and out[0][-1] == "?"  # ? garantido -> tom de dúvida


def test_cli_phonemizer_splits_sentences(monkeypatch):
    import importlib
    ph = importlib.import_module("lunaspeech.text.phonemize")
    outs = iter(["t\u02c8udu b\u025b\u0250\n", "\u0283ow d\u0292i \u02c8b\u0254l\u0250\n"])

    class R:
        def __init__(self):
            self.stdout = next(outs)
    monkeypatch.setattr(ph, "subprocess", type("S", (), {"run": staticmethod(lambda *a, **k: R())}))
    monkeypatch.setattr(ph, "_find_espeak", lambda: "/fake/espeak-ng")
    out = ph.phonemize("Tudo bem? Show de bola.", "pt-br")
    assert len(out) == 2
    assert out[0][-1] == "?" and out[1][-1] == "."


def test_question_contour_rises():
    from lunaspeech.engine.piper_onnx import _question_contour
    sr = 22050
    t = np.linspace(0, 2.0, int(sr * 2), endpoint=False)
    audio = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    out = _question_contour(audio)
    tail_in = audio[int(len(audio) * 0.8):]
    tail_out = out[int(len(out) * 0.8):]
    zc_in = int(np.sum(np.diff(np.sign(tail_in)) != 0))
    zc_out = int(np.sum(np.diff(np.sign(tail_out)) != 0))
    assert zc_out > zc_in  # pitch subiu no final


def test_resample_pitch_shift():
    from lunaspeech.core import _resample
    a = np.ones(1000, dtype=np.float32)
    up = _resample(a, 2.0)   # 2x mais agudo = metade do tamanho
    dn = _resample(a, 0.5)   # 2x mais grave = dobro do tamanho
    assert up.size == 500
    assert dn.size == 2000


def test_tone_prosody_has_pitch_and_gain():
    from lunaspeech.tone import prosody_for_tone
    for tone in ("neutro", "amigavel", "alegre", "raivoso", "triste"):
        p = prosody_for_tone(tone)
        assert "pitch" in p and "gain" in p
    # alegre mais aguda que triste; raivoso mais forte que triste
    assert prosody_for_tone("alegre")["pitch"] > prosody_for_tone("triste")["pitch"]
    assert prosody_for_tone("raivoso")["gain"] > prosody_for_tone("triste")["gain"]


@pytest.mark.skipif(not HAS_EN, reason="modelo en-test ausente")
def test_emotions_end_to_end():
    from lunaspeech import LunaSpeech
    tts = LunaSpeech(voice="en-test", models_dir=str(REPO / "models"))
    text = "The quick brown fox jumps over the lazy dog today."
    r_triste = tts.synthesize(text, tone="triste")
    r_neutro = tts.synthesize(text, tone="neutro")
    r_raivoso = tts.synthesize(text, tone="raivoso")
    assert r_triste.audio.size > r_neutro.audio.size      # triste mais lenta
    assert r_raivoso.audio.size < r_neutro.audio.size     # raivoso mais rápida
    assert abs(r_raivoso.audio).max() > abs(r_triste.audio).max()  # mais forte
