"""Testes do LunaSpeech.

Os testes de unidade (normalização, fonemização, config, áudio) rodam sem modelo.
O teste de integração usa ``test_voice.onnx`` (modelo piper real) e é SKIPPED
automaticamente se o modelo não estiver presente (em ``models/``).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
TEST_VOICE_ONNX = REPO / "models" / "test_voice.onnx"
TEST_VOICE_JSON = REPO / "models" / "test_voice.onnx.json"
FABER_CFG = REPO / "lunaspeech" / "voices_data" / "pt_BR-faber-medium.onnx.json"

HAS_TEST_VOICE = TEST_VOICE_ONNX.exists() and TEST_VOICE_JSON.exists()


# --------------------------------------------------------- testes sem modelo
def test_normalize_collapses_whitespace():
    from lunaspeech.text.normalize import normalize_text

    assert normalize_text("  olá\tmundo  \n ") == "olá mundo"
    assert normalize_text("") == ""


def test_phonemize_ptbr_produces_ipa():
    from lunaspeech.text.phonemize import phonemize

    out = phonemize("Olá. Tudo bem?", "pt-br")
    assert isinstance(out, list) and out and isinstance(out[0], list)
    flat = "".join(out[0])
    # fonemas IPA esperados para "Olá"
    assert "l" in flat and "a" in flat


def test_embedded_faber_config_parses():
    from lunaspeech.config import VoiceConfig

    cfg = VoiceConfig.from_json(FABER_CFG)
    assert cfg.sample_rate == 22050
    assert cfg.espeak_voice == "pt-br"
    assert cfg.language == "pt_BR"
    assert cfg.num_speakers == 1
    assert not cfg.is_multispeaker
    # tokens especiais sempre presentes
    for tok in ("^", "$", "_", " "):
        assert tok in cfg.phoneme_id_map
    # remapeamento do faber: "c" -> "k"
    assert cfg.phoneme_map.get("c") == ["k"]
    assert cfg.inference.length_scale == 1.0
    assert cfg.inference.noise_scale == pytest.approx(0.667)


def test_audio_helpers(tmp_path):
    from lunaspeech.audio import concatenate, normalize_peak, write_wav

    # normalização de pico: 2.0 -> 1.0
    a = np.ones(8, dtype=np.float32) * 2.0
    assert normalize_peak(a).max() == pytest.approx(1.0)
    # pico <= 1.0 permanece inalterado
    b = np.ones(8, dtype=np.float32) * 0.3
    assert normalize_peak(b).max() == pytest.approx(0.3)
    # concatenação
    assert len(concatenate([np.zeros(5), np.ones(5), None])) == 10
    # escrita de WAV
    p = write_wav(tmp_path / "t.wav", np.zeros(16000, dtype=np.float32), 16000)
    assert p.exists() and p.stat().st_size > 0


def test_voices_catalog():
    from lunaspeech import voices

    assert voices.DEFAULT_VOICE in voices.VOICES
    assert voices.VOICES["faber"].embedded_config == "pt_BR-faber-medium.onnx.json"
    assert voices.VOICES["en-test"].is_github_blob
    assert voices.VOICES["faber"].is_hf


# ----------------------------------------------------- testes com modelo real
@pytest.mark.skipif(not HAS_TEST_VOICE, reason="models/test_voice.onnx ausente")
class TestEngineIntegration:
    """Valida o pipeline completo (fonemas → IDs → ONNX → áudio) com modelo real."""

    def _engine(self):
        from lunaspeech.engine.piper_onnx import PiperOnnxEngine

        return PiperOnnxEngine(TEST_VOICE_ONNX, TEST_VOICE_JSON)

    def test_synthesize_produces_audible_audio(self):
        eng = self._engine()
        result = eng.synthesize("Hello. This is a test of speech synthesis.")
        assert result.sample_rate == 16000
        assert result.audio.size > 1000
        assert float(np.abs(result.audio).max()) > 0.05
        # nenhum fonema deve ficar de fora do mapa
        assert not result.missing_phonemes

    def test_stream_yields_sentence_chunks(self):
        eng = self._engine()
        chunks = list(eng.stream("One. Two. Three."))
        assert len(chunks) >= 1
        assert all(c.sample_rate == 16000 and c.audio.size > 0 for c in chunks)

    def test_rate_changes_length(self):
        eng = self._engine()
        text = "The quick brown fox jumps over the lazy dog."
        slow = eng.synthesize(text, length_scale=1.5)
        fast = eng.synthesize(text, length_scale=0.7)
        # mais lento => mais amostras
        assert slow.audio.size > fast.audio.size
