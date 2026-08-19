"""Testes do detector de tom de voz emocional."""

from __future__ import annotations

from lunaspeech.tone import detect_tone, prosody_for_tone


def test_friendly():
    assert detect_tone("Que legal, valeu! Obrigado pela ajuda.") == "amigavel"
    assert detect_tone("Olá, tudo bem? Muito obrigado!") == "amigavel"


def test_angry():
    assert detect_tone("EU ODEIO ISSO!!! Que raiva, chega!") == "raivoso"
    assert detect_tone("Vai se lascar, idiota, estou furioso!") == "raivoso"


def test_joyful():
    assert detect_tone("Uau, que incrível! Consegui finalmente!") == "alegre"


def test_sad():
    assert detect_tone("Estou tão triste hoje... muita saudade.") == "triste"


def test_neutral():
    assert detect_tone("O gato subiu no telhado ontem.") == "neutro"
    assert detect_tone("A reunião foi marcada para as quatorze horas.") == "neutro"
    assert detect_tone("") == "neutro"


def test_emojis():
    assert detect_tone(" Bom dia! 😊") == "amigavel"
    assert detect_tone("Não aguento mais 😡") == "raivoso"


def test_prosody_presets():
    p = prosody_for_tone("raivoso")
    # raivoso é mais rápido (length_scale menor) que amigável
    assert p["length_scale"] < prosody_for_tone("amigavel")["length_scale"]
    # triste é mais lento que neutro
    assert prosody_for_tone("triste")["length_scale"] > prosody_for_tone("neutro")["length_scale"]
    # triste é mais "monótono" (menos variação) que neutro
    assert prosody_for_tone("triste")["noise_scale"] < prosody_for_tone("neutro")["noise_scale"]
    # tom desconhecido cai no neutro
    assert prosody_for_tone("xxx") == prosody_for_tone("neutro")
