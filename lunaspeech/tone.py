"""Tom de voz emocional (prosódia, pitch e volume por emoção).

Detecta a emoção do texto em pt-BR (amigável, alegre, raivoso, triste) e mapeia
para parâmetros de síntese e pós-processamento:

- ``noise_scale`` / ``noise_w``  → variação de prosódia e ritmo (escalas do VITS);
- ``length_scale``               → velocidade;
- ``pitch``                      → tom (1.06 ≈ +1 semitom; aplicado com
  compensação de duração, então NÃO altera o tempo da fala);
- ``gain``                       → volume (raivoso mais forte, triste mais baixo).

Perguntas (frases terminadas em "?") recebem automaticamente um contorno de
pitch ascendente no final — o tom de dúvida — aplicado no motor.
"""

from __future__ import annotations

import re
from typing import Dict

# ----------------------------------------------------------------- léxico
_LEXICON: Dict[str, list] = {
    "raivoso": [
        "ódio", "odeio", "detesto", "raiva", "irritado", "irritada", "nervoso",
        "nervosa", "bravo", "brava", "furioso", "furiosa", "revoltado", "puta",
        "merda", "porra", "caralho", "idiota", "imbecil", "burro", "estúpido",
        "droga", "inferno", "desgraça", "horrível", "péssimo", "basta", "chega",
        "chega de", "nunca mais", "raivoso", "indignado", "fúria",
    ],
    "amigavel": [
        "obrigado", "obrigada", "valeu", "bem-vindo", "bem-vinda", "abraço",
        "beijo", "carinho", "amigo", "amiga", "querido", "querida", "legal",
        "massa", "top", "demais", "fofo", "lindo", "maravilhoso", "gentil",
        "prazer", "adoro", "adorei", "obrigadão", "bons", "feliz", "vibes",
        "olá", "ola", "oi", "salve", "tudo bem", "que bom", "que dia",
        "tranquilo", "de boa", "suave",
    ],
    "alegre": [
        "uau", "wow", "sensacional", "fantástico", "incrível", "maravilha",
        "viva", "finalmente", "consegui", "vitória", "comemorar", "uhuu",
        "show", "épico", "demais", "animei", "animado",
    ],
    "triste": [
        "triste", "infeliz", "chorar", "choro", "lágrima", "saudade",
        "saudades", "luto", "solidão", "sozinho", "sozinha", "desisto",
        "acabou", "fracasso", "fracassei", "deprimido", "deprimida", "mágoa",
        "decepcionado", "decepcionada",
    ],
}

# emojis → emoção
_EMOJI = {
    "amigavel": "😊🙂🥰❤️💛👍🤗😍😘",
    "alegre": "🎉🤩😄😃🥳✨",
    "triste": "☹️😢😔💔😞🥺",
    "raivoso": "😡🤬😤😠💢",
}

_THRESHOLD = 1.0  # pontuação mínima para aplicar um tom (evita falsos positivos)

# ----------------------------------------------------------- detecção
def detect_tone(text: str) -> str:
    """Classifica o tom do texto: neutro, amigavel, alegre, raivoso ou triste."""
    if not text or not text.strip():
        return "neutro"

    score: Dict[str, float] = {"raivoso": 0.0, "amigavel": 0.0, "alegre": 0.0, "triste": 0.0}
    low = text.lower()

    # palavras-chave (com borda de palavra)
    for emo, words in _LEXICON.items():
        for w in words:
            score[emo] += 1.5 * len(re.findall(r"\b" + re.escape(w) + r"\b", low))

    # PALAVRAS EM MAIÚSCULAS (grito = raiva ou empolgação)
    caps = re.findall(r"\b[A-ZÀ-Ý]{3,}\b", text)
    score["raivoso"] += 0.6 * len(caps)
    score["alegre"] += 0.6 * len(caps)

    # pontuação
    nex = text.count("!")
    if nex >= 3:
        score["alegre"] += 1.0
    elif nex >= 1:
        score["alegre"] += 0.4
        score["amigavel"] += 0.2
    if "..." in text or "…" in text:
        score["triste"] += 0.6

    # emojis
    for emo, chars in _EMOJI.items():
        for e in chars:
            if e in text:
                score[emo] += 1.0

    best = max(score, key=score.get)
    return best if score[best] >= _THRESHOLD else "neutro"


# ----------------------------------------------------------- prosódia
# tom → parâmetros de síntese e de áudio.
# pitch ≠ 1 é aplicado com compensação de duração (não altera o tempo da fala).
TONE_PROSODY: Dict[str, Dict[str, float]] = {
    # length_scale calibrado empiricamente (o noise_scale também afeta a duração)
    "neutro":   {"noise_scale": 0.667, "length_scale": 1.00, "noise_w": 0.80, "pitch": 1.00, "gain": 1.00},
    "amigavel": {"noise_scale": 0.88,  "length_scale": 1.10, "noise_w": 0.95, "pitch": 0.99, "gain": 1.03},
    "alegre":   {"noise_scale": 0.95,  "length_scale": 0.75, "noise_w": 1.00, "pitch": 1.06, "gain": 1.10},
    "raivoso":  {"noise_scale": 0.55,  "length_scale": 0.75, "noise_w": 0.40, "pitch": 1.04, "gain": 1.50},
    "triste":   {"noise_scale": 0.30,  "length_scale": 1.70, "noise_w": 0.35, "pitch": 0.92, "gain": 0.78},
}

TONE_LABEL = {
    "neutro": "neutro", "amigavel": "amigável", "alegre": "alegre",
    "raivoso": "raivoso", "triste": "triste",
}

ALL_TONES = ["auto", "neutro", "amigavel", "alegre", "raivoso", "triste"]


def prosody_for_tone(tone: str) -> Dict[str, float]:
    """Retorna {noise_scale, length_scale, noise_w, pitch, gain} do tom dado."""
    return dict(TONE_PROSODY.get(tone, TONE_PROSODY["neutro"]))
