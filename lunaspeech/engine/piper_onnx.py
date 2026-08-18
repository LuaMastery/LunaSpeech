"""Motor standalone VITS/ONNX (estilo Piper) — código próprio do LunaSpeech.

Pipeline de inferência:

    texto
      → normalização
      → fonemização espeak-ng (IPA, por sentença)
      → IDs inteiros (via ``phoneme_id_map`` do config, com tokens especiais
        ``^``=BOS, ``$``=EOS, ``_``=PAD)
      → sessão ONNX (CPU)  [inputs: input, input_lengths, scales, (sid?)]
      → áudio float32 (por sentença)
      → concatenação

Não depende de PyTorch nem de GPU. Usa apenas ``onnxruntime`` + ``piper-phonemize``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union

import numpy as np
import onnxruntime as ort

from ..audio import concatenate
from ..config import VoiceConfig
from ..text.normalize import normalize_text
from ..text.phonemize import phonemize
from .base import AudioChunk, SynthesisResult, TTSEngine

# Tokens especiais do formato Piper
_BOS = "^"   # início de utterance
_EOS = "$"   # fim de utterance
_PAD = "_"   # separador/padding entre fonemas


class PiperOnnxEngine(TTSEngine):
    """Executa um modelo Piper (VITS em ONNX) de forma standalone."""

    def __init__(
        self,
        model_path: Union[str, Path],
        config_path: Union[str, Path],
        *,
        num_threads: Optional[int] = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.config = VoiceConfig.from_json(config_path)

        sess_options = ort.SessionOptions()
        if num_threads:
            sess_options.intra_op_num_threads = num_threads
            sess_options.inter_op_num_threads = num_threads

        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=sess_options,
            providers=["CPUExecutionProvider"],
        )
        self._input_names = {i.name for i in self.session.get_inputs()}
        self._missing_phonemes: Dict[str, int] = {}

    # ------------------------------------------------------------------ props
    @property
    def sample_rate(self) -> int:
        return self.config.sample_rate

    @property
    def missing_phonemes(self) -> Dict[str, int]:
        """Fonemas presentes no texto mas ausentes no ``phoneme_id_map``."""
        return dict(self._missing_phonemes)

    # ----------------------------------------------------------- fonemas→IDs
    def _phonemes_to_ids(self, phonemes: List[str]) -> List[int]:
        """Converte fonemas IPA em IDs no formato esperado pelo modelo Piper."""
        pmap = self.config.phoneme_id_map
        # BOS seguido de PAD
        ids: List[int] = [pmap[_BOS][0], pmap[_PAD][0]]

        for phoneme in phonemes:
            # phoneme_map (ex.: faber mapeia "c"→"k") expande antes dos IDs
            targets = self.config.phoneme_map.get(phoneme, [phoneme])
            for target in targets:
                if target in pmap:
                    ids.extend(pmap[target])
                    ids.append(pmap[_PAD][0])  # PAD após cada fonema
                else:
                    self._missing_phonemes[target] = (
                        self._missing_phonemes.get(target, 0) + 1
                    )
        # EOS
        ids.append(pmap[_EOS][0])
        return ids

    # --------------------------------------------------------------- inferência
    def _run_session(
        self,
        ids: List[int],
        *,
        length_scale: float,
        speaker: Optional[str] = None,
    ) -> np.ndarray:
        scales = np.array(
            [
                self.config.inference.noise_scale,
                length_scale,                      # controla a velocidade
                self.config.inference.noise_w,
            ],
            dtype=np.float32,
        )
        feeds = {
            "input": np.array([ids], dtype=np.int64),
            "input_lengths": np.array([len(ids)], dtype=np.int64),
            "scales": scales,
        }
        # Vozes multi-falante recebem um "sid" (speaker id)
        if "sid" in self._input_names:
            sid = 0
            if speaker is not None and self.config.speaker_id_map:
                sid = int(self.config.speaker_id_map.get(speaker, 0))
            feeds["sid"] = np.array([sid], dtype=np.int64)

        output = self.session.run(None, feeds)[0]
        return np.asarray(output, dtype=np.float32).reshape(-1)

    # ----------------------------------------------------------- API pública
    def stream(
        self,
        text: str,
        *,
        length_scale: float = 1.0,
        speaker: Optional[str] = None,
    ) -> Iterator[AudioChunk]:
        """Sintetiza texto, gerando um :class:`AudioChunk` por sentença.

        Útil para streaming / reprodução com baixa latência percebida.
        """
        text = normalize_text(text)
        if not text:
            return
        for sentence_phonemes in phonemize(text, self.config.espeak_voice):
            ids = self._phonemes_to_ids(sentence_phonemes)
            if len(ids) < 3:
                continue
            audio = self._run_session(ids, length_scale=length_scale, speaker=speaker)
            if audio.size:
                yield AudioChunk(audio=audio, sample_rate=self.sample_rate)

    def synthesize(
        self,
        text: str,
        *,
        length_scale: float = 1.0,
        speaker: Optional[str] = None,
    ) -> SynthesisResult:
        """Sintetiza o texto inteiro e devolve o áudio concatenado."""
        chunks = [
            chunk.audio
            for chunk in self.stream(text, length_scale=length_scale, speaker=speaker)
        ]
        return SynthesisResult(
            audio=concatenate(chunks),
            sample_rate=self.sample_rate,
            missing_phonemes=self.missing_phonemes,
        )
