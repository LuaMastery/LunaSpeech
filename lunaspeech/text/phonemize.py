"""Fonemização (Grapheme-to-Phoneme) — multiplataforma.

Converte texto em listas de fonemas IPA agrupadas por sentença. Tem dois backends,
escolhidos automaticamente:

1. **piper-phonemize** (pacote Python com espeak-ng embutido) — usado em
   **Linux/macOS**, onde há wheel no PyPI. É o caminho preferido.
2. **espeak-ng** (binário do sistema, via subprocess) — usado como *fallback*,
   em especial no **Windows** (onde o piper-phonemize não tem wheel). Basta o
   usuário ter o espeak-ng instalado.

A saída de ambos os backends é compatível: cada sentença é uma lista de fonemas
IPA já decomposta em codepoints NFD (formato esperado pelo ``phoneme_id_map``).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from typing import List

try:
    import piper_phonemize  # type: ignore

    _HAVE_PIPER_PHONEMIZE = True
except Exception:  # ImportError ou erro de carregamento do binding C++
    _HAVE_PIPER_PHONEMIZE = False

# artefatos de separação/tie do espeak-ng que não são fonemas
_ESPEAK_JUNK = {"͜", "͡", "_", "‿"}


class PhonemizeError(RuntimeError):
    """Nenhum backend de fonemização disponível."""


def _phonemize_with_piper(text: str, voice: str) -> List[List[str]]:
    return piper_phonemize.phonemize_espeak(text, voice)


def _find_espeak() -> str:
    for name in ("espeak-ng", "espeak"):
        path = shutil.which(name)
        if path:
            return path
    return ""


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_CONTINUERS = {",", ":", ";"}   # NÃO terminam a frase
_SENTENCE_FINALS = {".", "!", "?"}     # terminam a frase


def _split_sentences(text: str) -> List[str]:
    """Divide o texto em sentenças preservando o terminador (?, ., !)."""
    parts = _SENTENCE_SPLIT_RE.split((text or "").strip())
    return [p for p in parts if p.strip()]


def _phonemize_with_espeak_cli(text: str, voice: str) -> List[List[str]]:
    binary = _find_espeak()
    if not binary:
        raise PhonemizeError(
            "Nenhum fonemizador disponível.\n"
            "Opções:\n"
            "  • instale 'piper-phonemize'  →  pip install piper-phonemize  "
            "(Linux/macOS)\n"
            "  • ou instale o binário espeak-ng:\n"
            "      Windows : winget install espeak-ng.espeak-ng   |   "
            "choco install espeak-ng\n"
            "      macOS   : brew install espeak-ng\n"
            "      Linux   : sudo apt install espeak-ng\n"
            "      manual  : https://github.com/espeak-ng/espeak-ng/releases"
        )
    sentences: List[List[str]] = []
    # Uma chamada espeak por SENTENÇA (não por cláusula): cláusulas internas
    # (vírgula, dois-pontos, ponto-e-vírgula) são JUNTAS na mesma frase,
    # com a vírgula virando pausa curta — não ponto final.
    for sent in _split_sentences(text):
        # Texto via stdin (evita code page/escape no argv do Windows).
        # Saída em UTF-8: o espeak-ng emite IPA em UTF-8 (ˈ, ə, ̃...).
        result = subprocess.run(
            [binary, "-v", voice, "-q", "--ipa"],
            input=sent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        phonemes: List[str] = []
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            # NFD separa diacríticos ('ã' -> 'a' + '̃') para casar com o
            # phoneme_id_map. Remove artefatos de tie/separador.
            ph = [c for c in unicodedata.normalize("NFD", line) if c not in _ESPEAK_JUNK]
            if not ph:
                continue
            phonemes.extend(ph)
            if ph[-1] in _CLAUSE_CONTINUERS:
                phonemes.append(" ")  # vírgula: pausa curta DENTRO da frase
        if not phonemes:
            continue
        # Garante o terminador final da sentença original — em especial o "?",
        # que dá o tom de pergunta/dúvida (mesmo se o espeak não o emitir).
        final = sent.rstrip()[-1] if sent.rstrip() else ""
        if final in _SENTENCE_FINALS or final in _CLAUSE_CONTINUERS:
            while phonemes and phonemes[-1] in (_CLAUSE_CONTINUERS | _SENTENCE_FINALS | {" "}):
                phonemes.pop()
            phonemes.append(final)
        sentences.append(phonemes)
    return sentences


def phonemize(text: str, voice: str) -> List[List[str]]:
    """Converte ``text`` em fonemas IPA, agrupados por sentença.

    Usa piper-phonemize se instalado; caso contrário, o binário espeak-ng.
    """
    if _HAVE_PIPER_PHONEMIZE:
        try:
            return _phonemize_with_piper(text, voice)
        except PhonemizeError:
            raise
        except Exception:
            # se o binding falhar em runtime, cai para o espeak-ng
            pass
    return _phonemize_with_espeak_cli(text, voice)


def available_backend() -> str:
    """Nome do backend ativo (para diagnóstico)."""
    if _HAVE_PIPER_PHONEMIZE:
        return "piper-phonemize"
    if _find_espeak():
        return "espeak-ng (binário)"
    return "nenhum"
