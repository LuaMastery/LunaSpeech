"""Normalização de texto (front-end linguístico).

A normalização é a etapa que mais impacta a qualidade *percebida* da fala —
é o que decide como "R$ 1.234,56", "15/08/2026" ou "Dr." serão ditos.

Esta é a versão da **Fase 1** (mínima e correta). A **Fase 2** trará tratamento
robusto de: números cardinais/ordinais, moeda (R$), datas, horas, siglas
(CPF, IBGE), abreviações (Dr., Sra.), URLs/emails e SSML básico.
"""

from __future__ import annotations

import re

# Múltiplos espaços / quebras de linha → um espaço
_WHITESPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Normalização mínima da Fase 1.

    * remove espaços nas bordas;
    * colapsa sequências de espaços/quebras em um único espaço.

    Não altera maiúsculas/minúsculas nem pontuação — o ``espeak-ng`` lida com
    isso durante a fonemização.
    """
    if not text:
        return ""
    return _WHITESPACE.sub(" ", text.strip())
