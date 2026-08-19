"""Interface abstrata dos motores de síntese (para futuros backends)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional

import numpy as np


@dataclass
class AudioChunk:
    """Trecho de áudio (uma sentença), útil para streaming."""

    audio: np.ndarray
    sample_rate: int


@dataclass
class SynthesisResult:
    """Resultado completo da síntese de um texto."""

    audio: np.ndarray
    sample_rate: int
    missing_phonemes: dict = None  # fonemas não reconhecidos pelo modelo
    tone: str = "neutro"           # tom detectado/aplicado

    @property
    def duration(self) -> float:
        return (len(self.audio) / self.sample_rate) if self.sample_rate else 0.0


class TTSEngine(ABC):
    """Contrato que todo motor LunaSpeech implementa.

    Hoje há apenas :class:`~lunaspeech.engine.piper_onnx.PiperOnnxEngine`, mas a
    interface permite plugar Kokoro, XTTS etc. no futuro sem mudar a API pública.
    """

    @property
    @abstractmethod
    def sample_rate(self) -> int: ...

    @abstractmethod
    def synthesize(self, text: str, *, length_scale: float = 1.0,
                   speaker: Optional[str] = None) -> SynthesisResult: ...

    @abstractmethod
    def stream(self, text: str, *, length_scale: float = 1.0,
               speaker: Optional[str] = None) -> Iterator[AudioChunk]: ...
