"""API de alto nível do LunaSpeech.

A classe :class:`LunaSpeech` esconde os detalhes do motor e do gerenciamento
de vozes, expondo uma interface simples:

    from lunaspeech import LunaSpeech
    tts = LunaSpeech()                    # voz padrão pt-BR (faber)
    tts.say("Olá, mundo!", "ola.wav")     # sintetiza e grava WAV
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional, Union

from . import voices
from .audio import write_wav
from .engine.base import AudioChunk, SynthesisResult
from .engine.piper_onnx import PiperOnnxEngine
from .tone import detect_tone, prosody_for_tone


class LunaSpeech:
    """Ponto de entrada principal do LunaSpeech."""

    def __init__(
        self,
        voice: str = voices.DEFAULT_VOICE,
        *,
        models_dir: Optional[Union[str, Path]] = None,
        num_threads: Optional[int] = None,
    ) -> None:
        self.voice_name = voice
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
    def synthesize(self, text: str, *, rate: float = 1.0,
                   tone: str = "auto", speaker: Optional[str] = None) -> SynthesisResult:
        """Sintetiza ``text``. ``rate`` > 1 deixa a fala mais rápida.

        ``tone`` define o tom de voz: ``"auto"`` detecta a emoção do texto
        (amigável, alegre, raivoso, triste) e ajusta a prosódia; ou um tom fixo.
        """
        detected = tone if tone != "auto" else detect_tone(text)
        p = prosody_for_tone(detected)
        length_scale = (p["length_scale"] / rate) if rate else p["length_scale"]
        result = self.engine.synthesize(
            text, length_scale=length_scale,
            noise_scale=p["noise_scale"], noise_w=p["noise_w"], speaker=speaker,
        )
        result.tone = detected
        return result

    def stream(self, text: str, *, rate: float = 1.0,
               tone: str = "auto", speaker: Optional[str] = None) -> Iterator[AudioChunk]:
        """Sintetiza por sentença (para streaming / baixa latência)."""
        detected = tone if tone != "auto" else detect_tone(text)
        p = prosody_for_tone(detected)
        length_scale = (p["length_scale"] / rate) if rate else p["length_scale"]
        return self.engine.stream(
            text, length_scale=length_scale,
            noise_scale=p["noise_scale"], noise_w=p["noise_w"], speaker=speaker,
        )

    def say(self, text: str, path: Union[str, Path] = "lunaspeech_out.wav",
            *, rate: float = 1.0) -> Path:
        """Sintetiza ``text`` e grava num arquivo WAV. Retorna o caminho."""
        result = self.synthesize(text, rate=rate)
        if result.audio.size == 0:
            raise RuntimeError("Nenhum áudio foi gerado (texto vazio ou sem fonemas).")
        return write_wav(path, result.audio, result.sample_rate)
