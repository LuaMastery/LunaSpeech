# ✅ Fase 1 — MVP: "fala qualquer texto"

**Objetivo:** fazer o LunaSpeech falar texto pela primeira vez, provando que o pipeline completo funciona.
**Status:** concluída e testada.

## O que foi entregue

### Motor standalone (`lunaspeech/engine/piper_onnx.py`)
Nosso próprio código que executa um modelo Piper (VITS/ONNX) sem depender do pacote `piper-tts` nem de PyTorch:

```
texto → normalize → phonemize (espeak-ng) → _phonemes_to_ids → sessão ONNX → áudio
```

- Lê o `phoneme_id_map` do config da voz e monta os IDs no formato Piper (`^` BOS, `_` PAD entre fonemas, `$` EOS).
- Aplica o `phoneme_map` da voz (ex.: faber mapeia `c`→`k`).
- Suporta vozes multi-falante (`sid`) e controle de **velocidade** via `length_scale`.
- Roda em CPU com `onnxruntime` (`CPUExecutionProvider`).

### Demais módulos
- `lunaspeech/text/` — normalização (mínima; Fase 2 expande) + fonemização via `piper-phonemize` (espeak-ng embutido).
- `lunaspeech/config.py` — carregamento tipado do `.onnx.json`.
- `lunaspeech/audio.py` — normalização de pico, concatenação, escrita WAV PCM-16.
- `lunaspeech/voices.py` — catálogo + download sob demanda (HuggingFace; config da voz faber **embutido**; voz `en-test` via API do GitHub para redes restritas).
- `lunaspeech/core.py` — classe `LunaSpeech` (API de alto nível).
- `lunaspeech/__main__.py` — CLI.

### Testes (`tests/test_lunaspeech.py`)
**8 testes, todos passando** — incluindo integração com modelo piper real:
- normalização e fonemização pt-BR;
- carregamento do config faber;
- helpers de áudio;
- síntese com áudio audível (sem fonemas faltantes), streaming por sentença, e controle de velocidade.

## Como testar

```bash
pip install -r requirements.txt

# voz de teste (baixa via GitHub — funciona mesmo sem HuggingFace):
python -m lunaspeech "Hello world. LunaSpeech is working." --voice en-test

# voz pt-BR (baixa o faber do HuggingFace na 1ª execução):
python -m lunaspeech "Olá, mundo!"

# testes automatizados:
python -m pytest tests/
```

## Decisões técnicas importantes

1. **espeak-ng sem `apt`:** o sandbox não tem acesso ao `apt`, então usamos o pacote `piper-phonemize` (PyPI), que **embuti os dados do espeak-ng**. Resolve a fonemização sem instalar nada no sistema.
2. **Modelos:** os binários `.onnx` das vozes ficam no HuggingFace. O LunaSpeech baixa sozinho; em redes onde o HF está bloqueado, o erro mostra o link para download manual.
3. **Config pt-BR embutido:** o `.onnx.json` da voz faber vem no pacote, então a voz padrão só precisa baixar o binário.

## Limitação do ambiente de desenvolvimento
Este sandbox bloqueia o HuggingFace e os CDNs de modelos, então **não foi possível baixar o binário da voz faber aqui** para gerar áudio pt-BR. A fonemização pt-BR e o config estão validados; o áudio pt-BR é gerado assim que a voz faber é baixada (automático na máquina do usuário). O motor foi validado de ponta a ponta com a voz inglesa de teste (`en-test`), produzindo áudio real.

## Próximo passo
**Fase 2** — front-end de texto robusto (números, moeda `R$`, datas, horas, siglas, abreviações, SSML básico), que é o que mais melhora a qualidade percebida da fala em pt-BR.
