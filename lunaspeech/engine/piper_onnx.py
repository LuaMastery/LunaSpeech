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


# Contorno de pergunta: pitch global mais alto + subida ACCELERADA no fim
# (o tom de dúvida típico do português). A duração é compensada no length_scale.
_QUESTION_TAIL = 0.50    # fração final da frase com subida de pitch
_QUESTION_BASE = 1.05    # pitch global da pergunta (+5%)
_QUESTION_RISE = 1.32    # pitch no fim da subida (+~5 semitons)
_QUESTION_LS = 1.11      # compensação de duração (o contorno encurta o áudio)


def _question_contour(audio: np.ndarray) -> np.ndarray:
    """Aplica intonação de pergunta: voz levemente mais alta, subindo no fim."""
    n = audio.size
    if n < 1600:  # áudio muito curto: não mexe
        return audio
    head_end = int(n * (1.0 - _QUESTION_TAIL))
    head, tail = audio[:head_end], audio[head_end:]
    # cabeça: pitch global +5%
    h = head.size
    h_out = max(2, int(h / _QUESTION_BASE))
    new_head = np.interp(np.linspace(0, h - 1, h_out), np.arange(h), head)
    # cauda: fator sobe de BASE até RISE com aceleração (curva quadrática)
    m = tail.size
    out_len = max(8, int(m / ((_QUESTION_BASE + _QUESTION_RISE) / 2.0)))
    frac = (np.arange(out_len) / max(1, out_len - 1)) ** 1.6
    factors = _QUESTION_BASE + (_QUESTION_RISE - _QUESTION_BASE) * frac
    positions = np.cumsum(factors)
    positions -= positions[0]
    idx = np.clip(positions.astype(np.int64), 0, m - 1)
    new_tail = tail[idx]
    return np.concatenate([new_head.astype(audio.dtype), new_tail.astype(audio.dtype)])


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
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
        speaker: Optional[str] = None,
    ) -> np.ndarray:
        scales = np.array(
            [
                self.config.inference.noise_scale if noise_scale is None else noise_scale,
                length_scale,                      # controla a velocidade
                self.config.inference.noise_w if noise_w is None else noise_w,
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
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
        speaker: Optional[str] = None,
    ) -> Iterator[AudioChunk]:
        """Sintetiza texto, gerando um :class:`AudioChunk` por sentença.

        Útil para streaming / reprodução com baixa latência percebida.
        """
        text = normalize_text(text)
        if not text:
            return
        ls = self.config.inference.length_scale if length_scale is None else length_scale
        ns = self.config.inference.noise_scale if noise_scale is None else noise_scale
        nw = self.config.inference.noise_w if noise_w is None else noise_w
        for sentence_phonemes in phonemize(text, self.config.espeak_voice):
            ids = self._phonemes_to_ids(sentence_phonemes)
            if len(ids) < 3:
                continue
            # pergunta? aplica intonação ascendente (tom de dúvida)
            last = next((p for p in reversed(sentence_phonemes) if p != " "), "")
            is_question = last == "?"
            if is_question:
                ls = ls * _QUESTION_LS  # compensa o encurtamento do contorno
            audio = self._run_session(
                ids, length_scale=ls, noise_scale=ns, noise_w=nw, speaker=speaker
            )
            if audio.size:
                if is_question:
                    audio = _question_contour(audio)
                yield AudioChunk(audio=audio, sample_rate=self.sample_rate)

    def synthesize(
        self,
        text: str,
        *,
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
        speaker: Optional[str] = None,
    ) -> SynthesisResult:
        """Sintetiza o texto inteiro e devolve o áudio concatenado."""
        chunks = [
            chunk.audio
            for chunk in self.stream(
                text, length_scale=length_scale, noise_scale=noise_scale,
                noise_w=noise_w, speaker=speaker
            )
        ]
        return SynthesisResult(
            audio=concatenate(chunks),
            sample_rate=self.sample_rate,
            missing_phonemes=self.missing_phonemes,
        )
