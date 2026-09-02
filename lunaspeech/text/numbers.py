"""Conversão de números para palavras em Português do Brasil.

Implementa:
* cardinais (0 → trilhões+), com gênero (masculino/feminino);
* decimais (vírgula), respeitando a convenção pt-BR (``.`` = milhar, ``,`` = decimal);
* ordinais (``1º`` → "primeiro", ``2ª`` → "segunda");
* nomes das letras (para soletrar siglas).

Regras do "e" (conectivo) seguem o padrão do pt-BR:
* dentro de uma centena: "cento e vinte e três";
* entre grupos de milhar: " e " só quando o grupo inferior for < 100 ou == 100
  (ex.: "mil e um", "mil e cem", "mil duzentos e trinta e quatro").
"""

from __future__ import annotations

from typing import List

# ----------------------------------------------------------------- cardinais
_UNITS = {
    "m": [
        "zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito",
        "nove", "dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis",
        "dezessete", "dezoito", "dezenove",
    ],
    "f": [
        "zero", "uma", "duas", "três", "quatro", "cinco", "seis", "sete", "oito",
        "nove", "dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis",
        "dezessete", "dezoito", "dezenove",
    ],
}

# dezenas: índice 2..9 → 20,30,...,90
_TENS = [
    "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta",
    "noventa",
]

_HUNDREDS = {
    "m": {2: "duzentos", 3: "trezentos", 4: "quatrocentos", 5: "quinhentos",
          6: "seiscentos", 7: "setecentos", 8: "oitocentos", 9: "novecentos"},
    "f": {2: "duzentas", 3: "trezentas", 4: "quatrocentas", 5: "quinhentas",
          6: "seiscentas", 7: "setecentas", 8: "oitocentas", 9: "novecentas"},
}

# (singular, plural) por escala. "mil" é invariável.
_SCALES = [
    ("", ""),             # 10^0
    ("mil", "mil"),       # 10^3
    ("milhão", "milhões"),   # 10^6
    ("bilhão", "bilhões"),   # 10^9
    ("trilhão", "trilhões"),  # 10^12
    ("quatrilhão", "quatrilhões"),  # 10^15
]

_DIGITS = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"]


def _units(n: int, gender: str = "m") -> str:
    return _UNITS[gender][n]


def _under100(n: int, gender: str = "m") -> str:
    if n < 20:
        return _units(n, gender)
    tens, units = divmod(n, 10)
    words = _TENS[tens - 2]
    if units:
        words += " e " + _units(units, gender)
    return words


def _under1000(n: int, gender: str = "m") -> str:
    hundreds, rest = divmod(n, 100)
    if hundreds == 0:
        return _under100(rest, gender)
    if hundreds == 1:
        hw = "cem" if rest == 0 else "cento"
    else:
        hw = _HUNDREDS[gender][hundreds]
    if rest == 0:
        return hw
    return hw + " e " + _under100(rest, gender)


def int_to_words(n: int, gender: str = "m") -> str:
    """Cardinal de um inteiro não-negativo (até 10^15-1). Gênero ``'m'`` ou ``'f'``."""
    if n == 0:
        return "zero"
    if n < 0:
        return "menos " + int_to_words(-n, gender)
    if n >= 10 ** 15:
        # fora do alcance suportado: lê dígitos (evita resultado errado)
        return " ".join(_DIGITS[int(d)] for d in str(n))

    triples: List[int] = []
    work = n
    while work:
        triples.append(work % 1000)
        work //= 1000

    parts: List[tuple] = []  # (índice_da_escala, texto)
    for i, val in enumerate(triples):
        if val == 0:
            continue
        if i == 0:
            parts.append((i, _under1000(val, gender)))
        elif i == 1:  # mil (invariável)
            if val == 1:
                parts.append((i, "mil"))
            else:
                parts.append((i, _under1000(val, gender) + " mil"))
        else:
            sing, plur = _SCALES[i]
            word = sing if val == 1 else plur
            prefix = "um " if val == 1 else _under1000(val, gender) + " "
            parts.append((i, prefix + word))

    parts.reverse()  # ler do maior para o menor
    out = parts[0][1]
    for j in range(1, len(parts)):
        scale_idx, text = parts[j]
        val = triples[scale_idx]
        sep = " e " if (val < 100 or val == 100) else " "
        out += sep + text
    return out


# ------------------------------------------------------------------- decimais
def number_token_to_words(token: str, gender: str = "m") -> str:
    """Converte um token numérico (``1234``, ``1.234``, ``1,5``, ``1.234,56``).

    Heurística pt-BR:
    * há ``,`` → vírgula decimal; ``.`` removido (separador de milhar);
    * só ``.`` → milhar se após o ponto houver 3 dígitos e antes <= 3, senão decimal.
    A parte decimal é lida dígito a dígito após "vírgula".
    """
    token = token.strip()
    neg = token.startswith("-")
    if neg:
        token = token[1:]

    if "," in token and "." in token:
        int_part, dec_part = token.split(",", 1)
        int_part = int_part.replace(".", "")
    elif "," in token:
        int_part, dec_part = token.split(",", 1)
    elif "." in token:
        if token.count(".") > 1:
            int_part = token.replace(".", "")
            dec_part = ""
        else:
            before, after = token.split(".", 1)
            if len(after) == 3 and before.isdigit() and len(before) <= 3:
                int_part, dec_part = before + after, ""
            else:
                int_part, dec_part = before, after
    else:
        int_part, dec_part = token, ""

    int_val = int(int_part) if int_part.isdigit() else 0
    sign = "menos " if neg else ""

    if not int_part and dec_part:
        words = ""
    elif int_val == 0:
        words = "zero"
    else:
        words = int_to_words(int_val, gender)

    if dec_part:
        digits = " ".join(_DIGITS[int(d)] for d in dec_part if d.isdigit())
        if words:
            words = words + " vírgula " + digits
        else:
            words = "vírgula " + digits
    return (sign + words).strip()


# ------------------------------------------------------------------- ordinais
_ORD_UNITS = {
    "m": {1: "primeiro", 2: "segundo", 3: "terceiro", 4: "quarto", 5: "quinto",
          6: "sexto", 7: "sétimo", 8: "oitavo", 9: "nono"},
    "f": {1: "primeira", 2: "segunda", 3: "terceira", 4: "quarta", 5: "quinta",
          6: "sexta", 7: "sétima", 8: "oitava", 9: "nona"},
}
_ORD_TENS = {
    "m": {10: "décimo", 20: "vigésimo", 30: "trigésimo", 40: "quadragésimo",
          50: "quinquagésimo", 60: "sexagésimo", 70: "septuagésimo",
          80: "octogésimo", 90: "nonagésimo"},
    "f": {10: "décima", 20: "vigésima", 30: "trigésima", 40: "quadragésima",
          50: "quinquagésima", 60: "sexagésima", 70: "septuagésima",
          80: "octogésima", 90: "nonagésima"},
}
_ORD_HUNDREDS = {
    "m": {100: "centésimo", 200: "ducentésimo", 300: "trecentésimo",
          400: "quadringentésimo", 500: "quingentésimo", 600: "sexcentésimo",
          700: "septingentésimo", 800: "octingentésimo", 900: "nongentésimo"},
    "f": {100: "centésima", 200: "ducentésima", 300: "trecentésima",
          400: "quadringentésima", 500: "quingentésima", 600: "sexcentésima",
          700: "septingentésima", 800: "octingentésima", 900: "nongentésima"},
}


def ordinal_to_words(n: int, gender: str = "m") -> str:
    """Ordinal de 1 a 999 (``21`` → "vigésimo primeiro", ``1ª`` → "primeira")."""
    if n <= 0 or n >= 1000:
        return int_to_words(n, gender)  # fora do alcance: usa cardinal

    units = _ORD_UNITS[gender]
    tens = _ORD_TENS[gender]
    hundreds = _ORD_HUNDREDS[gender]

    parts: List[str] = []
    h, rest = divmod(n, 100)
    if h:
        parts.append(hundreds[h * 100])
    t, u = divmod(rest, 10)
    if t:
        parts.append(tens[t * 10])
    if u:
        parts.append(units[u])
    return " ".join(parts)


# -------------------------------------------------------------- soletrar (G2P)
# Nomes das letras em pt-BR (para soletrar siglas: CPF → "cê pê éfe")
LETTER_NAMES = {
    "A": "á", "B": "bê", "C": "cê", "D": "dê", "E": "éi", "F": "éfi",
    "G": "gê", "H": "agá", "I": "i", "J": "jóta", "K": "cá", "L": "éli",
    "M": "êmi", "N": "êni", "O": "ó", "P": "pê", "Q": "quê", "R": "érri",
    "S": "éssi", "T": "tê", "U": "u", "V": "vê", "W": "dábliu", "X": "xis",
    "Y": "ípsilon", "Z": "zê",
}


def spell_letters(letters: str) -> str:
    """Soletra uma sequência de letras maiúsculas: ``"CPF"`` → ``"cê pê éfi"``."""
    out = []
    for ch in letters:
        if ch.isalpha():
            out.append(LETTER_NAMES.get(ch.upper(), ch.lower()))
        else:
            out.append(ch)
    return " ".join(out)


def spell_words(text: str) -> str:
    """Soletra cada palavra do texto: ``"oi gato"`` → ``"ó i  gá á tê ó"``."""
    import re

    return re.sub(r"[^\W\d_]+", lambda m: spell_letters(m.group(0)), text, flags=re.UNICODE)


def should_spell(text: str) -> bool:
    """Detecta automaticamente se o texto deve ser soletrado (modo automático).

    Regras conservadoras (frases normais NÃO são soletradas):
    * mais de uma palavra → falar normalmente;
    * código com letras E dígitos ("AB12", "x9k") → soletrar;
    * palavra curta sem vogais ("xkcd", "www", "str") → soletrar.
    """
    t = (text or "").strip()
    if not t:
        return False
    words = t.split()
    if len(words) != 1:
        return False
    w = words[0].strip(".,!?;:()-")
    letters = [c for c in w.lower() if c.isalpha()]
    digits = [c for c in w if c.isdigit()]
    if letters and digits:  # código alfanumérico
        return True
    vowels = set("aeiouáéíóúâêôãõà")
    if letters and len(letters) <= 10 and not any(c in vowels for c in letters):
        return True  # sem vogais → impronunciável
    return False
