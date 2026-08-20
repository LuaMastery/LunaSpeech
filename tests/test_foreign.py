"""Testes do tratamento de palavras estrangeiras."""

from __future__ import annotations

from lunaspeech.text.foreign import adapt_foreign_words
from lunaspeech.text.normalize import normalize_text


def test_value_in_dict():
    assert adapt_foreign_words("value") == "vâliu"
    assert adapt_foreign_words("Value") == "vâliu"      # case-insensitive
    assert adapt_foreign_words("VALUE") == "vâliu"


def test_plural_in_dict():
    assert adapt_foreign_words("values") == "vâlius"
    assert adapt_foreign_words("sites") == "sáitis"
    assert adapt_foreign_words("servers") == "sérvers"


def test_foreign_letters_spelled():
    out = adapt_foreign_words("python")          # tem 'y'
    assert "pê" in out
    assert adapt_foreign_words("youtube").startswith("ípsilon")
    assert adapt_foreign_words("play") != "play"  # 'y' → soletrado


def test_normal_pt_untouched():
    assert adapt_foreign_words("O gato subiu no telhado.") == "O gato subiu no telhado."
    assert adapt_foreign_words("Bem-vindo, tudo bem?") == "Bem-vindo, tudo bem?"
    assert adapt_foreign_words("casa jogo amigo") == "casa jogo amigo"


def test_lunaspeech_kept():
    # "LunaSpeech" não tem gatilho estrangeiro → mantido
    assert adapt_foreign_words("LunaSpeech") == "LunaSpeech"


def test_fixes_value_glitch_in_normalize():
    # o glitch do "value" (fonemas estranhos) some após normalização
    assert normalize_text("value") == "vâliu"
    assert normalize_text("server online") == "sérver ônlaini"
    assert normalize_text("background") == "bêckgraund"


def test_digits_preserved():
    # números continuam sendo tratados pelo normalizador de números
    assert adapt_foreign_words("valor 100") == "valor 100"
    assert normalize_text("valor 100") == "valor cem"


def test_spell_words():
    from lunaspeech.text.numbers import spell_words
    out = spell_words("casa")
    assert "cê" in out and "á" in out and "éssi" in out  # c-a-s-a
    assert "éfi" in spell_words("F")
    assert "éli" in spell_words("L")


def test_letter_names_no_glitch():
    """Regressão: nenhum nome de letra fonemiza com 'y' solto (bug do soletrar)."""
    from lunaspeech.text.numbers import LETTER_NAMES
    from lunaspeech.text.phonemize import phonemize
    for letter, nome in LETTER_NAMES.items():
        ph = [p for s in phonemize(nome, "pt-br") for p in s]
        assert ph and ph[-1] != "y", f"letra {letter} ({nome}) termina em y: {ph}"
