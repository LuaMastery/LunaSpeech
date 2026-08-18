"""Testes do front-end de texto (Fase 2)."""

from __future__ import annotations

from lunaspeech.text.normalize import normalize_text


def test_currency():
    assert normalize_text("R$ 1.234,56") == "mil duzentos e trinta e quatro reais e cinquenta e seis centavos"
    assert normalize_text("R$ 2,00") == "dois reais"
    assert normalize_text("R$ 1,50") == "um real e cinquenta centavos"
    assert normalize_text("R$ 0,50") == "cinquenta centavos"
    assert normalize_text("US$ 50") == "cinquenta dólares"


def test_percent():
    assert normalize_text("50%") == "cinquenta por cento"
    assert normalize_text("12,5%") == "doze vírgula cinco por cento"


def test_dates():
    assert normalize_text("18/08/2026") == "dezoito de agosto de dois mil e vinte e seis"
    assert normalize_text("15/03") == "quinze de março"
    assert normalize_text("2026-08-18") == "dezoito de agosto de dois mil e vinte e seis"


def test_times():
    assert normalize_text("14:30") == "quatorze e trinta"
    assert normalize_text("09:00") == "nove horas"
    assert normalize_text("14h30") == "quatorze e trinta"


def test_ordinals():
    assert normalize_text("1º") == "primeiro"
    assert normalize_text("2ª") == "segunda"
    assert normalize_text("século 21º") == "século vigésimo primeiro"


def test_units_and_temp():
    assert normalize_text("10kg") == "dez quilos"
    assert normalize_text("5km") == "cinco quilômetros"
    assert normalize_text("100km/h") == "cem quilômetros por hora"
    assert normalize_text("30°C") == "trinta graus celsius"
    assert normalize_text("100°F") == "cem graus fahrenheit"


def test_acronyms_and_abbreviations():
    assert normalize_text("Meu CPF") == "Meu cê pê éfe"
    assert normalize_text("Dr. Silva") == "doutor Silva"
    assert normalize_text("Sra. Ana") == "senhora Ana"
    assert normalize_text("etc.") == "etcétera"


def test_numbers_and_decimals_preserve_punctuation():
    assert normalize_text("Em 2026") == "Em dois mil e vinte e seis"
    assert normalize_text("Tenho 25 anos.") == "Tenho vinte e cinco anos."  # ponto final preservado
    assert normalize_text("1.234") == "mil duzentos e trinta e quatro"
    assert normalize_text("3,14") == "três vírgula um quatro"


def test_complex_sentence():
    assert normalize_text(
        "A conta deu R$ 1.234,56 em 18/08/2026 às 14:30."
    ) == (
        "A conta deu mil duzentos e trinta e quatro reais e cinquenta e seis centavos "
        "em dezoito de agosto de dois mil e vinte e seis às quatorze e trinta."
    )


def test_empty_and_whitespace():
    assert normalize_text("") == ""
    assert normalize_text("   ") == ""


def test_plain_text_passes_through():  # sem regressão em texto sem tokens especiais
    assert normalize_text("Olá, mundo!") == "Olá, mundo!"
    assert normalize_text("Hello, this is a test.") == "Hello, this is a test."
