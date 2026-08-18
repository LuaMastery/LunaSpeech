"""Fonemização (Grapheme-to-Phoneme) via espeak-ng.

Usa o pacote ``piper-phonemize``, que embute os dados do espeak-ng
(espeak-ng-data) — portanto **não depende** de uma instalação de sistema do
``espeak-ng``. Converte texto em listas de fonemas IPA agrupadas por sentença.
"""

from __future__ import annotations

from typing import List

import piper_phonemize


def phonemize(text: str, voice: str) -> List[List[str]]:
    """Converte ``text`` em fonemas IPA, agrupados por sentença.

    Args:
        text: texto já normalizado.
        voice: voz do espeak-ng (ex.: ``"pt-br"``, ``"en-us"``).

    Returns:
        Lista de sentenças; cada sentença é uma lista de fonemas (strings IPA,
        já decompostos em codepoints NFD, como o Piper espera).
    """
    return piper_phonemize.phonemize_espeak(text, voice)
