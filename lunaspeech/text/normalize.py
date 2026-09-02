"""Normalização de texto (front-end linguístico) — Fase 2.

Converte formas "escritas" em formas "faláveis" ANTES da fonemização:
números, moeda (R$), datas, horas, percentuais, ordinais, unidades, siglas e
abreviações. É a etapa que mais impacta a qualidade percebida da fala.

Aplicações na ordem correta (do mais específico ao mais genérico), de forma que
o resultado expandido (sem dígitos) não seja reprocessado por outra regra.
"""

from __future__ import annotations

import re
from typing import Tuple

from .numbers import (
    int_to_words,
    number_token_to_words,
    ordinal_to_words,
    spell_letters,
)
from .foreign import adapt_foreign_words

# ------------------------------------------------------------------ utilidades
_WHITESPACE = re.compile(r"\s+")

_MONTHS = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro",
    12: "dezembro",
}


def _split_decimal(num: str) -> Tuple[str, str]:
    """Heurística pt-BR: (parte_inteira, parte_decimal) como strings."""
    if "," in num and "." in num:
        i, d = num.split(",", 1)
        return i.replace(".", ""), d
    if "," in num:
        i, d = num.split(",", 1)
        return i, d
    if "." in num:
        if num.count(".") > 1:
            return num.replace(".", ""), ""
        before, after = num.split(".", 1)
        if len(after) == 3 and before.isdigit() and len(before) <= 3:
            return before + after, ""
        return before, after
    return num, ""


# ----------------------------------------------------------------- abreviações
_ABBREVIATIONS = {
    "dr": "doutor", "dra": "doutora", "drs": "doutores", "dras": "doutoras",
    "sr": "senhor", "sra": "senhora", "srs": "senhores", "sras": "senhoras",
    "prof": "professor", "profa": "professora",
    "eng": "engenheiro", "enga": "engenheira",
    "av": "avenida", "art": "artigo", "vol": "volume", "ed": "edição",
    "exmo": "excelentíssimo", "exma": "excelentíssima",
    "tel": "telefone", "etc": "etcétera", "pg": "página", "pp": "páginas",
    "ex": "exemplo", "mín": "mínimo", "máx": "máximo", "aprox": "aproximadamente",
}


def _build_abbrev_re() -> re.Pattern:
    keys = sorted(_ABBREVIATIONS, key=len, reverse=True)
    return re.compile(r"(?<![\w])(" + "|".join(re.escape(k) for k in keys) + r")\.", re.IGNORECASE)


_ABBREV_RE = _build_abbrev_re()


def _expand_abbreviations(text: str) -> str:
    return _ABBREV_RE.sub(lambda m: _ABBREVIATIONS[m.group(1).lower()], text)


# -------------------------------------------------------------------- moeda
_CURRENCY_RE = re.compile(r"(?P<sym>R\$|US\$|€|£|\$)\s*(?P<num>\d[\d.,]*)")
_CURRENCY_NOUNS = {  # (singular, plural)
    "R$": ("real", "reais"), "US$": ("dólar", "dólares"), "$": ("dólar", "dólares"),
    "€": ("euro", "euros"), "£": ("libra", "libras"),
}


def _currency_repl(m: re.Match) -> str:
    sym, num = m["sym"], m["num"]
    sing, plur = _CURRENCY_NOUNS.get(sym, ("real", "reais"))
    if sym == "R$":
        int_str, dec_str = _split_decimal(num)
        reais = int(int_str) if int_str else 0
        cents = int(dec_str) if (dec_str and len(dec_str) == 2 and dec_str.isdigit()) else 0
        parts = []
        if reais:
            parts.append("um real" if reais == 1 else f"{int_to_words(reais)} reais")
        if cents:
            parts.append("um centavo" if cents == 1 else f"{int_to_words(cents)} centavos")
        return " e ".join(parts) if parts else f"{number_token_to_words(num)} reais"
    return f"{number_token_to_words(num)} {plur}"


# ------------------------------------------------------------------ porcento
_PERCENT_RE = re.compile(r"(?P<num>\d[\d.,]*)\s*%")


# ---------------------------------------------------------------------- datas
_DATE_RE = re.compile(r"\b(?P<d>\d{1,2})/(?P<m>\d{1,2})(?:/(?P<y>\d{2,4}))?\b")
_DATE_ISO_RE = re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})\b")


def _date_repl(m: re.Match) -> str:
    d, mo = int(m["d"]), int(m["m"])
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return m.group(0)
    parts = [int_to_words(d), "de", _MONTHS[mo]]
    if m["y"]:
        parts += ["de", int_to_words(int(m["y"]))]
    return " ".join(parts)


def _date_iso_repl(m: re.Match) -> str:
    d, mo = int(m["d"]), int(m["m"])
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return m.group(0)
    return " ".join([int_to_words(d), "de", _MONTHS[mo], "de", int_to_words(int(m["y"]))])


# ---------------------------------------------------------------------- horas
_TIME_RE = re.compile(r"\b(?P<h>\d{1,2}):(?P<mi>\d{2})(?::(?P<s>\d{2}))?\b")
_TIME_H_RE = re.compile(r"\b(?P<h>\d{1,2})h(?P<mi>\d{2})?\b")


def _time_repl(m: re.Match) -> str:
    h, mi = int(m["h"]), int(m["mi"])
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        return m.group(0)
    out = f"{int_to_words(h, 'f')} e {int_to_words(mi)}" if mi else \
          f"{int_to_words(h, 'f')} hora" + ("" if h == 1 else "s")
    if m["s"]:
        sv = int(m["s"])
        out += " e " + int_to_words(sv) + (" segundo" if sv == 1 else " segundos")
    return out


def _time_h_repl(m: re.Match) -> str:
    h = int(m["h"])
    if not (0 <= h <= 23):
        return m.group(0)
    base = f"{int_to_words(h, 'f')} hora" + ("" if h == 1 else "s")
    if m["mi"]:
        mi = int(m["mi"])
        if 0 <= mi <= 59:
            return f"{int_to_words(h, 'f')} e {int_to_words(mi)}"
    return base


# ------------------------------------------------------------------- ordinais
_ORDINAL_RE = re.compile(r"(?P<num>\d+)(?P<suf>º|ª|°)")


def _ordinal_repl(m: re.Match) -> str:
    gender = "f" if m["suf"] == "ª" else "m"
    return ordinal_to_words(int(m["num"]), gender)


# -------------------------------------------------------------------- unidades
_UNITS_MAP = {
    "km/h": "quilômetros por hora", "km": "quilômetros", "kg": "quilos",
    "mg": "miligramas", "g": "gramas", "cm": "centímetros", "mm": "milímetros",
    "ml": "mililitros", "kw": "quilowatts", "min": "minutos",
    "m": "metros", "l": "litros", "h": "horas", "w": "watts",
}
_UNITS_ALT = "|".join(sorted(_UNITS_MAP, key=len, reverse=True))
_UNITS_RE = re.compile(rf"(?P<num>\d[\d.,]*)\s?(?P<unit>{_UNITS_ALT})(?![a-z])")
_TEMP_RE = re.compile(r"(?P<num>\d[\d.,]*)\s?°\s?(?P<scale>C|F)")


def _unit_repl(m: re.Match) -> str:
    return f"{number_token_to_words(m['num'])} {_UNITS_MAP[m['unit']]}"


def _temp_repl(m: re.Match) -> str:
    scale = "celsius" if m["scale"] == "C" else "fahrenheit"
    return f"{number_token_to_words(m['num'])} graus {scale}"


# ------------------------------------------------- sequências de letras isoladas
# "agora eu vou soletrar um A, B, C, D, E" -> soletra APENAS o A, B, C, D, E;
# o resto da frase é falado normalmente.
_LC = r"[A-ZÀ-Ý]"
_LETTER_SEQ_RE = re.compile(
    rf"\b{_LC}(?:\s*[,;]\s*{_LC}){{1,}}\s*[,;]?"   # A, B, C (vírgulas) — 2+
    rf"|\b{_LC}(?:\s+{_LC}){{2,}}"                    # A B C (espaços) — 3+
)


def _expand_letter_sequences(text: str) -> str:
    """Soletra apenas as sequências de letras isoladas do texto (não o resto)."""
    def repl(m: re.Match) -> str:
        return re.sub(r"[A-ZÀ-Ý]", lambda c: spell_letters(c.group()), m.group(0))
    return _LETTER_SEQ_RE.sub(repl, text)


# --------------------------------------------------------------------- siglas
# Uma palavra em MAIÚSCULAS só é soletrada se parecer sigla DE VERDADE.
# Sequências de 2+ palavras em maiúsculas = GRITO/ÊNFASE (não soletra) —
# ex.: "EU ODEIO ISSO" é raiva, não três siglas.
_PRONOUNCE_AS_WORD = {"COVID", "SARSCOV", "NASA", "ONU", "UNESCO", "OTAN", "TIKTOK"}
_CAPS_RUN_RE = re.compile(  # cada palavra do run exige ao menos UMA letra
    r"(?=[A-ZÀ-Ý0-9]*[A-ZÀ-Ý])[A-ZÀ-Ý0-9]{2,}(?:-\d+)?"
    r"(?:[ \t]+(?=[A-ZÀ-Ý0-9]*[A-ZÀ-Ý])[A-ZÀ-Ý0-9]{2,}(?:-\d+)?)*"
)
_VOWELS_UPPER = set("AEIOUÁÉÍÓÚÂÊÔÃÕÀÜ")
# siglas com vogais que devem ser soletradas (fora da lista, caps com vogais
# são tratadas como ênfase e faladas como palavra: "ISSO", "ODEIO", "EU")
_KNOWN_ACRONYMS = {
    "IBGE", "ONU", "USP", "UFRJ", "UFMG", "UFRGS", "UNESP", "UNICAMP", "PUC",
    "MEC", "INSS", "OMS", "OEA", "OTAN", "UNESCO", "IP", "UV", "ID", "IR",
    "IGPM", "IPCA", "SELIC",
}


def _spell_token(tok: str) -> str:
    out = []
    i = 0
    while i < len(tok):
        ch = tok[i]
        if ch.isalpha() and ch.isupper():
            out.append(spell_letters(ch))
            i += 1
        elif ch.isdigit():
            j = i
            while j < len(tok) and tok[j].isdigit():
                j += 1
            out.append(int_to_words(int(tok[i:j])))
            i = j
        else:  # hífens etc.
            i += 1
    return " ".join(out)


def _is_true_acronym(tok: str) -> bool:
    """Palavra em CAPS isolada: é sigla (soletra) ou ênfase/grito (fala)?"""
    if tok in _PRONOUNCE_AS_WORD:
        return False  # lê como palavra
    if any(c.isdigit() for c in tok):
        return True           # MP3, COVID-19
    if not any(c in _VOWELS_UPPER for c in tok):
        return True           # CPF, CNPJ, PM (sem vogais)
    return tok in _KNOWN_ACRONYMS  # IBGE, ONU... (com vogais, mas é sigla)


def _expand_acronyms(text: str) -> str:
    def repl(m: re.Match) -> str:
        run = m.group(0)
        words = run.split()
        if len(words) >= 2:
            return run  # sequência de caps = grito/ênfase -> fala normalmente
        tok = words[0]
        if _is_true_acronym(tok):
            return _spell_token(tok)
        return run  # caps isolada com vogais -> ênfase -> fala como palavra
    return _CAPS_RUN_RE.sub(repl, text)


# -------------------------------------------------------------- números (geral)
_NUMBER_RE = re.compile(r"(?<![\w.])-?\d(?:[\d.,]*\d)?")


# --------------------------------------------------------------------- master
def normalize_text(text: str) -> str:
    """Normalização pt-BR completa (Fase 2)."""
    if not text:
        return ""
    text = adapt_foreign_words(text)
    text = _expand_abbreviations(text)
    text = _CURRENCY_RE.sub(_currency_repl, text)
    text = _PERCENT_RE.sub(lambda m: f"{number_token_to_words(m['num'])} por cento", text)
    text = _DATE_ISO_RE.sub(_date_iso_repl, text)
    text = _DATE_RE.sub(_date_repl, text)
    text = _TIME_RE.sub(_time_repl, text)
    text = _TIME_H_RE.sub(_time_h_repl, text)
    text = _expand_letter_sequences(text)
    text = _expand_acronyms(text)
    text = _TEMP_RE.sub(_temp_repl, text)
    text = _ORDINAL_RE.sub(_ordinal_repl, text)
    text = _UNITS_RE.sub(_unit_repl, text)
    text = _NUMBER_RE.sub(lambda m: number_token_to_words(m.group(0)), text)
    return _WHITESPACE.sub(" ", text).strip()
