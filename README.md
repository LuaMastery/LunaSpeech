# 🌙 LunaSpeech

> Sistema de **Text-to-Speech (TTS)** open source, leve e gratuito — construído para **falar qualquer texto** em **Português do Brasil** (e outros idiomas), rodando em **CPU** comum, sem GPU e sem serviços pagos.

LunaSpeech é um projeto desenvolvido **aos poucos e de forma testável**, com o objetivo de entregar um sistema de fala simples, eficiente e livre — não tão poderoso quanto o ElevenLabs, mas acessível a todos.

## 🎯 Objetivos
- 🆓 **Grátis e open source** (licenças MIT/Apache/CC0)
- ⚡ **Leve**: roda em CPU, até em Raspberry Pi (< 100 MB de RAM)
- 🇧🇷 **Foco em pt-BR** (com caminho para outros idiomas)
- 🧩 **Nosso próprio código**: front-end de texto, motor, API e interface próprios

## 🧠 Arquitetura
Baseada em **VITS exportado para ONNX** (a mesma abordagem do [Piper](https://github.com/OHF-Voice/piper1-gpl)), executada de forma **standalone** com `onnxruntime` + `piper-phonemize` (espeak-ng embutido) — **sem PyTorch e sem GPU** no caminho de inferência.

```
TEXTO → [front-end pt-BR] → [fonemização espeak-ng] → [VITS/ONNX em CPU] → ÁUDIO
```

## 📦 Instalação

```bash
# dependências leves (piper-phonemize já traz o espeak-ng-data embutido)
pip install -e .
# ou, sem instalar como pacote:
pip install -r requirements.txt
```

Requisitos: Python ≥ 3.9. **Não precisa** de GPU, PyTorch nem `apt install espeak-ng`.

## 🚀 Uso

### Linha de comando
```bash
python -m lunaspeech "Olá, mundo!"                      # voz padrão pt-BR (faber)
python -m lunaspeech "Texto mais rápido." --rate 1.3    # 30% mais rápido
python -m lunaspeech "Texto lento." --rate 0.8 --out lento.wav
python -m lunaspeech --list-voices                      # ver vozes disponíveis
echo "Texto do stdin" | python -m lunaspeech
```

### Python
```python
from lunaspeech import LunaSpeech

tts = LunaSpeech()                  # voz padrão pt-BR (faber), baixa na 1ª execução
tts.say("Bem-vindo ao LunaSpeech!", "saida.wav")

# controle de velocidade e streaming por sentença
for trecho in tts.stream("Primeira frase. Segunda frase."):
    tocar(trecho.audio, trecho.sample_rate)
```

## 🗣️ Vozes
| Voz | Idioma | Notas |
|---|---|---|
| **faber** *(padrão)* | pt-BR | Masculina, 22 kHz, **domínio público (CC0)** |
| cadu | pt-BR | Masculina, 22 kHz, CC0 |
| edresson | pt-BR | 16 kHz, CC BY 4.0 |
| tugao | pt-PT | Masculina de Portugal |
| en-test | en-US | Voz de teste (lessac), baixada via GitHub — útil para validar o motor |

Na primeira execução, a voz é baixada automaticamente para `~/.local/share/lunaspeech/models` (ou `$LUNASPEECH_MODELS`).

## 📚 Documentação
- 🔬 **[Pesquisa completa do cenário TTS](docs/00-PESQUISA-TTS.md)** — comparação de modelos, escolha da arquitetura e roadmap.
- ✅ **[Fase 1 concluída](docs/FASE-1.md)** — detalhes do MVP e como testar.

## 🗺️ Roadmap
- ✅ **Fase 0** — Pesquisa técnica
- ✅ **Fase 1** — MVP funcional: motor VITS/ONNX standalone, CLI, fonemização pt-BR
- 🔧 **Fase 2** — Front-end de texto robusto (números, R$, datas, siglas, SSML)
- 🌐 **Fase 3** — API HTTP (FastAPI) + interface web
- 🎙️ **Fase 4** — Nossa própria voz pt-BR ("voz Luna")
- 🚀 **Fase 5** — Recursos avançados (multi-idioma, clonagem, motor Kokoro)

## ✅ Status da Fase 1 (testado)
- Motor standalone `PiperOnnxEngine`: fonemas → IDs → ONNX → WAV **validado com modelo real** (áudio audível).
- CLI e API Python funcionando; **8 testes** (pytest) passando, incluindo integração com modelo real.
- Fonemização pt-BR e config da voz faber funcionando.
- *Limitação conhecida do ambiente de desenvolvimento:* este sandbox bloqueia o HuggingFace (de onde vêm os binários `.onnx`), então o áudio pt-BR só é gerado após baixar a voz faber numa máquina com internet — o que o LunaSpeech faz **automaticamente** (`pip install huggingface-hub` opcional; caso o HF esteja indisponível, o próprio erro informa o link para download manual).

---
*Projeto em desenvolvimento ativo.*
