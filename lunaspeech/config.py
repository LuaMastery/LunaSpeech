"""Configuração de voz, lida do arquivo ``.onnx.json`` do Piper.

Um arquivo de voz Piper contém dois arquivos:

* ``<voz>.onnx``       — o modelo neural VITS (binário).
* ``<voz>.onnx.json``  — metadados: sample_rate, voz do espeak-ng,
  parâmetros de inferência (noise/length/noise_w) e o ``phoneme_id_map``
  que mapeia cada fonema (IPA) a um ou mais IDs inteiros consumidos pelo modelo.

Este módulo carrega esse JSON num objeto tipado.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union


@dataclass
class InferenceConfig:
    """Parâmetros que controlam a geração (ruído, velocidade, prosódia)."""

    noise_scale: float = 0.667   # variação/expressividade (padrão Piper)
    length_scale: float = 1.0    # ⭐ velocidade: >1 = mais lento, <1 = mais rápido
    noise_w: float = 0.8         # variação da duração dos fonemas


@dataclass
class VoiceConfig:
    """Metadados de uma voz Piper."""

    sample_rate: int
    espeak_voice: str
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    phoneme_id_map: Dict[str, List[int]] = field(default_factory=dict)
    num_speakers: int = 1
    speaker_id_map: Dict[str, int] = field(default_factory=dict)
    phoneme_map: Dict[str, List[str]] = field(default_factory=dict)
    language: str = ""
    dataset: str = ""
    piper_version: str = ""

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "VoiceConfig":
        """Carrega a configuração a partir de um arquivo ``.onnx.json``."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        inf_raw = data.get("inference", {})
        inference = InferenceConfig(
            noise_scale=float(inf_raw.get("noise_scale", 0.667)),
            length_scale=float(inf_raw.get("length_scale", 1.0)),
            noise_w=float(inf_raw.get("noise_w", 0.8)),
        )
        lang = data.get("language", {}) or {}
        return cls(
            sample_rate=int(data["audio"]["sample_rate"]),
            espeak_voice=str(data["espeak"]["voice"]),
            inference=inference,
            phoneme_id_map={k: list(v) for k, v in data.get("phoneme_id_map", {}).items()},
            num_speakers=int(data.get("num_speakers", 1)),
            speaker_id_map=data.get("speaker_id_map", {}) or {},
            phoneme_map=data.get("phoneme_map", {}) or {},
            language=str(lang.get("code", "")),
            dataset=str(data.get("dataset", "")),
            piper_version=str(data.get("piper_version", "")),
        )

    @property
    def is_multispeaker(self) -> bool:
        return self.num_speakers > 1
