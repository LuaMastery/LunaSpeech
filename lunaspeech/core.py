"""API de alto nível do LunaSpeech.

A classe :class:`LunaSpeech` esconde os detalhes do motor e do gerenciamento
de vozes, expondo uma interface simples:

    from lunaspeech import LunaSpeech
    tts = LunaSpeech()                    # voz padrão pt-BR (faber)
    tts.say("Olá, mundo!", "ola.wav")     # sintetiza e grava WAV

Versões (``mode``):
- **flash**    — síntese em uma passada, resposta rápida (padrão);
- **thinking** — gera várias variantes por sentença e escolhe a mais suave
  (menor fator de crista = menos picos/glitches). Demora mais, sai melhor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional, Union

import numpy as np

from . import voices
from .audio import concatenate, write_wav
from .engine.base import AudioChunk, SynthesisResult
from .engine.piper_onnx import PiperOnnxEngine
from .tone import detect_tone, prosody_for_tone

MODES = ("flash", "thinking")
THINKING_CANDIDATES = 4


def _crest(audio: np.ndarray) -> float:
    """Fator de crista (pico/RMS). MENOR = áudio mais suave, menos glitches."""
    a = np.abs(np.asarray(audio, dtype=np.float32))
    if a.size == 0:
        return float("inf")
    rms = float(np.sqrt(np.mean(a ** 2))) + 1e-9
    peak = float(a.max())
    return peak / rms


class LunaSpeech:
    """Ponto de entrada principal do LunaSpeech."""

    def __init__(
        self,
        voice: str = voices.DEFAULT_VOICE,
        *,
        models_dir: Optional[Union[str, Path]] = None,
        num_threads: Optional[int] = None,
        mode: str = "flash",
    ) -> None:
        self.voice_name = voice
        self.mode = mode if mode in MODES else "flash"
        self._models_dir = voices.models_dir(models_dir)
        onnx_path, json_path = voices.ensure_voice(voice, self._models_dir)
        self.engine = PiperOnnxEngine(onnx_path, json_path, num_threads=num_threads)

    # ------------------------------------------------------------- propriedades
    @property
    def sample_rate(self) -> int:
        return self.engine.sample_rate

    @property
    def missing_phonemes(self) -> dict:
        return self.engine.missing_phonemes

    # ------------------------------------------------------------- síntese
    def _params(self, text: str, tone: str, rate: float):
        detected = tone if tone != "auto" else detect_tone(text)
        p = prosody_for_tone(detected)
        length_scale = (p["length_scale"] / rate) if rate else p["length_scale"]
        return detected, p, length_scale

    def _synthesize_thinking(self, text, p, length_scale, speaker, detected) -> SynthesisResult:
        """Versão Thinking: N variantes por sentença; escolhe a mais suave."""
        runs = [
            list(self.engine.stream(
                text, length_scale=length_scale,
                noise_scale=p["noise_scale"], noise_w=p["noise_w"], speaker=speaker))
            for _ in range(THINKING_CANDIDATES)
        ]
        if not runs or not runs[0]:
            return SynthesisResult(audio=np.zeros(0, dtype=np.float32),
                                   sample_rate=self.engine.sample_rate, tone=detected)
        n_sentences = len(runs[0])
        best_chunks = []
        for i in range(n_sentences):
            candidates = [run[i].audio for run in runs if i < len(run)]
            best_chunks.append(min(candidates, key=_crest))
        return SynthesisResult(
            audio=concatenate(best_chunks),
            sample_rate=self.engine.sample_rate,
            missing_phonemes=self.engine.missing_phonemes,
            tone=detected,
        )

    def synthesize(self, text: str, *, rate: float = 1.0, tone: str = "auto",
                   speaker: Optional[str] = None,
                   mode: Optional[str] = None) -> SynthesisResult:
        """Sintetiza ``text``.

        - ``rate`` > 1 deixa a fala mais rápida;
        - ``tone``: "auto" detecta a emoção do texto;
        - ``mode``: "flash" (rápida) ou "thinking" (mais lenta e aprimorada).
        """
        detected, p, length_scale = self._params(text, tone, rate)
        use_mode = mode if mode in MODES else self.mode
        if use_mode == "thinking":
            return self._synthesize_thinking(text, p, length_scale, speaker, detected)
        result = self.engine.synthesize(
            text, length_scale=length_scale,
            noise_scale=p["noise_scale"], noise_w=p["noise_w"], speaker=speaker,
        )
        result.tone = detected
        return result

    def stream(self, text: str, *, rate: float = 1.0, tone: str = "auto",
               speaker: Optional[str] = None) -> Iterator[AudioChunk]:
        """Sintetiza por sentença (para streaming / baixa latência)."""
        detected, p, length_scale = self._params(text, tone, rate)
        return self.engine.stream(
            text, length_scale=length_scale,
            noise_scale=p["noise_scale"], noise_w=p["noise_w"], speaker=speaker,
        )

    def say(self, text: str, path: Union[str, Path] = "lunaspeech_out.wav",
            *, rate: float = 1.0, tone: str = "auto",
            mode: Optional[str] = None) -> Path:
        """Sintetiza ``text`` e grava num arquivo WAV. Retorna o caminho."""
        result = self.synthesize(text, rate=rate, tone=tone, mode=mode)
        if result.audio.size == 0:
            raise RuntimeError("Nenhum áudio foi gerado (texto vazio ou sem fonemas).")
        return write_wav(path, result.audio, result.sample_rate)
