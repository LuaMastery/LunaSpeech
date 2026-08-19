"""Tratamento de palavras estrangeiras (termos em inglês/tecnologia).

O espeak-ng com voz pt-BR **deturpa** palavras estrangeiras em sequências
fonéticas estranhas (ex.: "value" → ``v ˌ a l ˈ u y``) que o modelo não consegue
sintetizar bem — causando glitches severos.

Solução em duas frentes:
1. **Dicionário** de termos estrangeiros comuns → pronúncia pt-BR *limpa*
   (verificada — fonemiza sem artefatos).
2. **Detecção ortográfica** de palavras estrangeiras (com y/w/k ou dígrafos
   ingleses como th/sh/wh) → soletração (sempre pronunciável, nunca glitcha).
   Segura porque o português nativo **não usa** y/w/k nem esses dígrafos.
"""

from __future__ import annotations

import re

from .numbers import spell_letters

# termo estrangeiro (minúsculo) → pronúncia pt-BR limpa (verificada no espeak)
FOREIGN_DICT: dict[str, str] = {
    # tecnologia / internet
    "value": "vâliu", "values": "vâlius",
    "live": "laivi", "life": "laifi",
    "game": "gêimi", "games": "gêimis", "gamer": "gêimir",
    "video": "vídeo", "videos": "vídeos",
    "site": "sáiti", "sites": "sáitis", "website": "uêbi sáiti",
    "download": "daunlôudi", "downloads": "daunlôudis",
    "upload": "aplôudi", "uploads": "aplôudis",
    "background": "bêckgraund",
    "stream": "estrim", "streaming": "estremin",
    "online": "ônlaini", "offline": "oflâini",
    "server": "sérver", "servers": "sérvers",
    "client": "cláienti", "clients": "cláientis",
    "app": "épi", "apps": "épis",
    "bug": "bâgui", "bugs": "bâguis",
    "patch": "pêtchi", "patchs": "pêtchis",
    "code": "côudi", "codes": "côudis", "coding": "côudin",
    "data": "déita", "database": "déita beis",
    "link": "linqui", "links": "linquis",
    "scroll": "eskrôul", "scrolling": "eskrôulin",
    "web": "uêbi", "wifi": "uáifai",
    "login": "lôgin", "logins": "lôgins", "logout": "lôgaut",
    "email": "imeil", "emails": "imeils",
    "chat": "tcháti", "chats": "chátis",
    "post": "pósti", "posts": "póstis",
    "like": "laiki", "likes": "laikis",
    "software": "softuér",
    "api": "éipii", "mouse": "máus", "claude": "cláudi",
}

# Letra que NÃO ocorre em português nativo (nem na maioria dos nomes/loans comuns)
# → sinal seguro de palavra estrangeira. Não usamos w/k/th/sh etc. porque aparecem
# em empréstimos e nomes brasileiros (show, web, kilo, Thiago) — causando falsos positivos.
_FOREIGN_PATTERN = re.compile(r"y", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)  # palavras (letras/acentos), sem dígitos


def _looks_foreign(word: str) -> bool:
    return len(word) >= 2 and bool(_FOREIGN_PATTERN.search(word))


def adapt_foreign_words(text: str) -> str:
    """Substitui termos estrangeiros por pronúncias pt-BR (dicionário) ou soletração."""
    if not text:
        return text

    def repl(m: re.Match) -> str:
        word = m.group(0)
        low = word.lower()
        if low in FOREIGN_DICT:
            return FOREIGN_DICT[low]
        if _looks_foreign(word):
            return spell_letters(word)
        return word

    return _TOKEN_RE.sub(repl, text)
