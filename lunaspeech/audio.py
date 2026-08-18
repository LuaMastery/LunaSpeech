"""Utilidades de áudio: normalização, concatenação e escrita de WAV."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union

import numpy as np


def normalize_peak(audio: np.ndarray) -> np.ndarray:
    """Converte para float32 e, se houver pico acima de 1.0, normaliza para [-1, 1]."""
    audio = np.asarray(audio, dtype=np.float32)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 1.0:
        audio = audio / peak
    return audio


def concatenate(chunks: Iterable[np.ndarray]) -> np.ndarray:
    """Concatena trechos de áudio (um por sentença) num único vetor."""
    parts = [np.asarray(c, dtype=np.float32).reshape(-1) for c in chunks if c is not None and np.asarray(c).size]
    if not parts:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(parts)


def write_wav(path: Union[str, Path], audio: np.ndarray, sample_rate: int) -> Path:
    """Escreve um WAV PCM 16-bit a partir de áudio float.

    Usa ``soundfile`` (libsndfile). Áudio é normalizado por pico para evitar
    clipping, já que a saída bruta do VITS pode ultrapassar ±1.0.
    """
    import soundfile as sf

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = normalize_peak(audio)
    sf.write(str(path), audio, int(sample_rate), subtype="PCM_16")
    return path


def to_int16(audio: np.ndarray) -> np.ndarray:
    """Converte float [-1, 1] para int16 PCM (útil para streaming/ALSA)."""
    audio = normalize_peak(audio)
    return (audio * 32767.0).clip(-32768, 32767).astype(np.int16)
