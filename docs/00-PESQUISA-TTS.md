# 📚 Pesquisa Completa: O Cenário TTS Open Source (2026)

> **LunaSpeech** — Documento de pesquisa técnica que fundamenta a arquitetura do projeto.
> Data: 18/ago/2026 · Idioma de referência: **Português do Brasil (pt-BR)**

---

## 1. O que é TTS e como funciona (o pipeline completo)

**TTS (Text-to-Speech)** é o processo de converter texto escrito em fala sintetizada. Um sistema TTS moderno é uma **pipelina** com 3 grandes etapas:

```
TEXTO  →  [1. Front-end de texto]  →  [2. Modelo acústico]  →  [3. Vocoder]  →  ÁUDIO
```

### 1.1 Front-end de texto (o "cérebro linguístico")
É o que mais afeta a qualidade percebida em pt-BR e muitas vezes é subestimado:

- **Normalização** — transformar "R$ 1.234,56", "15/08/2026", "10kg", "Dr.", "COVID-19" em texto falável ("mil duzentos e trinta e quatro reais e cinquenta e seis centavos").
- **Tokenização** — dividir em sentenças/fonemas.
- **G2P (Grapheme-to-Phoneme)** — converter palavras escritas em fonemas (símbolos fonéticos, ex. IPA). Em pt-BR a grafia é quase fonética, mas há ambiguidades (ex. "sexo" vs "exame", "c" antes de e/i vs a/o/u).

### 1.2 Modelo acústico
Converte fonemas em uma representação espectral intermediária (geralmente o **mel-espectrograma**). Famílias principais:

| Família | Como funciona | Vantagens | Desvantagens |
|---|---|---|---|
| **Tacotron 2** | Seq2seq com atenção (autoregressivo) | Naturalidade alta | Atenção instável, lento |
| **FastSpeech 2** | Não-autoregressivo, prevê duração/tom/energia | Rápido, estável, controle prosódico | Mais peças para treinar |
| **VITS** | **End-to-end** (texto → waveform direto) | Sem vocoder separado, ótima qualidade | Treino mais delicado, mais memória |
| **Difusão / Flow-matching** | Refina ruído em fala (ex. F5-TTS) | Clonagem zero-shot forte | Custo computacional alto |

### 1.3 Vocoder
Converte o mel-espectrograma em **forma de onda** de áudio (os samples PCM que ouvimos).
- **HiFi-GAN** é o padrão de facto: 167× tempo-real em GPU, MOS ~4,4 (quase indistinguível de humano).
- No VITS o vocoder já vem **embutido** no modelo (por isso é "end-to-end").

> 💡 **Insight decisivo:** o VITS elimina a etapa do vocoder separado. É exatamente por isso que o **Piper** (que usa VITS exportado para ONNX) consegue rodar em CPU com <100 MB de RAM.

---

## 2. Comparação dos melhores modelos open source (2026)

Pontuação **MOS** (Mean Opinion Score, 1–5; humano ≈ 4,5+).

| Modelo | MOS | Parâmetros | VRAM | Clonagem? | Licença | Idiomas | Destaque |
|---|---|---|---|---|---|---|---|
| **Kokoro** | 4,2 | 82M | <1 GB | ❌ | Apache 2.0 | 9 | Mais natural por parâmetro; roda em CPU |
| **XTTS v2** (Coqui) | 4,0 | 467M | ~4 GB | ✅ (6s) | **CPML** (não-comercial) | 17 | Clonagem zero-shot madura |
| **F5-TTS** | 4,1 | 336M | ~4 GB | ✅ | CC-BY-NC (pesos) | — | Flow-matching, clonagem de ponta |
| **Chatterbox** | 4,1 | 500M | ~4 GB | ✅ (5s) | MIT | 23+ | Venceu ElevenLabs em teste cego do fabricante |
| **Bark** | 3,7 | 900M | ~6 GB | ⚠️ limitada | MIT | — | Riso, música, emoções |
| **Dia** | 4,0 | 1,6B | ~5 GB | ✅ | Apache 2.0 | EN | Diálogo multi-falante |
| **Piper** | 3,5 | 6–60M | **<100 MB (CPU)** | ❌ | **MIT/GPL** | **30+** | **Roda até em Raspberry Pi** |

### Critérios do nosso projeto → escolha
O usuário quer: **simples, grátis, eficiente, open source, pt-BR**. Isso filtra drasticamente:

- ❌ XTTS v2, F5-TTS, Fish Speech → licença **não-comercial** (bloqueia uso livre).
- ❌ Bark, Dia, Chatterbox, F5-TTS → exigem **GPU 4–6 GB+** (nosso sandbox tem 2 CPU / 3,8 GB RAM e o usuário final provavelmente tem hardware fraco).
- ✅ **Kokoro** (Apache 2.0, roda em CPU) — ótima qualidade, mas **poucas vozes pt-BR**.
- ✅ **Piper** (MIT/GPL, **CPU-only**, **30+ idiomas com vozes pt-BR prontas**, inferência instantânea RTF 0,008).

### 🏆 Recomendação técnica
**Piper (arquitetura VITS em ONNX) como base do LunaSpeech**, porque atende a TODOS os requisitos do usuário: leve, CPU, open source, gratuito, com vozes pt-BR prontas e caminho claro para treinar a nossa própria voz depois. Kokoro fica como motor "premium" opcional futuro.

Além disso, modelos Piper podem ser executados de forma **standalone** (apenas `onnxruntime` + `espeak-ng`), o que nos dá **controle total do código** — fundamental para um projeto "feito do zero".

---

## 3. Foco: Português do Brasil (pt-BR)

### 3.1 Vozes Piper prontas para pt-BR
| Voz | Qualidade | Especial | Notas |
|---|---|---|---|
| **pt_BR-faber-medium** | medium | Masculina | ~63 MB, 22050 Hz, **CC0 (domínio público!)** — a melhor escolha livre |
| **pt_BR-edresson-low** | low | — | 16000 Hz, CC BY 4.0 |
| **pt_BR-cadu-medium** | medium | — | Adicionada recentemente |
| **OpenVoiceOS pt-BR miro/dii** | medium | Femininas disponíveis | Coleção da comunidade (2025) |

A **faber-medium** é particularmente atraente: voz masculina pt-BR de qualidade, **domínio público**, roda standalone com onnxruntime.

### 3.2 Datasets pt-BR abertos (para treinar nossa própria voz no futuro)
| Dataset | Duração | Tipo | Licença |
|---|---|---|---|
| **TTS-Portuguese Corpus** (Edresson) | 10,5 h | 1 falante, 48 kHz | CC BY 4.0 — base do faber/edresson |
| **Mozilla Common Voice** (pt) | ~330 h | Multifalante | CC0/CC BY — multifalante, ruidoso |
| **pt-br_char** (firstpixel) | ~10–100k clipes | Derivado do Common Voice | CC BY-SA 3.0 |
| **VoxForge pt-BR** | ~4.130 enunciados | Multifalante | Livre |

> Para treinar uma voz **nova** de boa qualidade precisamos de **algumas horas** de áudio limpo de um único falante; para **multifalante/clonagem**, mais dados. O fine-tuning parte de um checkpoint Piper existente (ex.: lessac) e adapta para pt-BR — muito mais barato que treinar do zero absoluto.

### 3.3 Desafios específicos do pt-BR (o front-end de texto tem que resolver)
- **Abreviações**: Dr., Sra., km/h, etc.
- **Numerais e moeda**: "R$ 2.000" → "dois mil reais"; datas; horas.
- **Siglas**: "CPF", "CNPJ", "IBGE" (soletrar) vs "NASA" (ler como palavra).
- **Acréscimos de ditongos e nasalização** já bem cobertos pelo espeak-ng com voz `pt-br`.

---

## 4. Como o Piper funciona por dentro (para reimplementarmos enxuto)

```
texto → espeak-ng (voz pt-br, --ipa) → fonemas IPA
      → mapear fonemas → IDs inteiros (phoneme_id_map do config .json)
      → adicionar tokens especiais: ^ (início), _ (espaço), $ (fim)
      → sessão ONNX (CPUExecutionProvider):
            inputs:  input[ids], input_lengths, scales[noise, length, noise_w]
            output:  forma de onda float32
      → concatenar áudio das sentenças → gravar WAV (sample_rate do config)
```

**Três parâmetros de controle** (definidos no `inference` do config):
- `noise_scale` — variação/emoção (padrão ~0,667)
- `length_scale` — **velocidade** (>1 = mais lento; <1 = mais rápido) ⭐ controle útil
- `noise_w` — variação da duração dos fonemas (padrão ~0,8)

Isso é o suficiente para construir um motor próprio **sem depender do pacote `piper-tts`** (que puxa PyTorch e é pesado). Precisamos apenas de: `onnxruntime`, `numpy`, `soundfile` + binário `espeak-ng`.

---

## 5. A pergunta-chave: "fazer do zero"?

Honestidade técnica importante:

- Treinar um modelo neural TTS **do zero absoluto** (pesos aleatórios → modelo útil) exige: **dezenas de horas de áudio**, **GPU por dias**, e expertise em PyTorch + alinhamento de áudio. Não é viável na Fase 1.
- **Todos** os projetos open source sérios (Piper, Coqui, RVC, etc.) partem de modelos pré-treinados e os adaptam. É o padrão da indústria.

Portanto, "do zero" para o LunaSpeech significa: **construir o nosso próprio sistema/produto completo** (front-end de texto, motor, API, interface, gestão de vozes, normalização pt-BR) — aproveitando os pesos de modelos abertos como "matéria-prima", exatamente como um app open source de imagem usa modelos abertos mas tem seu próprio código. Conforme avançarmos, treinaremos a **nossa própria voz pt-BR** ("voz Luna"), tornando cada vez mais partes do sistema genuinamente nossas.

Esse é o caminho realista, livre e eficiente que o usuário descreveu.

---

## 6. Arquitetura proposta do LunaSpeech

```
lunaspeech/
├── lunaspeech/
│   ├── text/              # Front-end (normalização pt-BR, SSML, sentencização)
│   │   ├── normalize.py   # números, moeda, datas, siglas, abreviações
│   │   └── phonemize.py   # wrapper do espeak-ng
│   ├── engine/
│   │   ├── base.py        # interface Engine abstrata
│   │   ├── piper_onnx.py  # motor standalone VITS/ONNX (nosso código)
│   │   └── voices.py      # catálogo/download de vozes
│   ├── audio.py           # WAV/PCM, concatenação, sample rate
│   └── api/
│       └── server.py      # FastAPI: /speak, /voices, /health (+ streaming)
├── web/                   # UI web simples (digita texto → ouve)
├── cli.py                 # `lunaspeech "texto"` na linha de comando
├── tests/
└── models/                # vozes baixadas (gitignored)
```

Princípios:
- **Sem dependência de GPU** nem PyTorch no caminho de inferência (só onnxruntime).
- **Interface de motor abstrata** → no futuro pluggamos Kokoro/XTTS sem reescrever o resto.
- **API HTTP + CLI + Web UI** → o usuário pode testar desde a Fase 1.

---

## 7. Roadmap faseado (desenvolver aos poucos, testar aos poucos)

### ✅ Fase 0 — Pesquisa (este documento)
- Mapear o cenário, escolher Piper/VITS-ONNX, definir arquitetura. **Concluída.**

### 🚧 Fase 1 — MVP funcional (meta: "fala qualquer texto")
- [ ] Setup: `requirements.txt`, instalar `espeak-ng` (sistema) + `onnxruntime`, `numpy`, `soundfile`, `fastapi`, `uvicorn`.
- [ ] Baixar a voz **pt_BR-faber-medium** (domínio público).
- [ ] Motor standalone `piper_onnx.py` (espeak-ng → IDs → ONNX → WAV).
- [ ] CLI: `python -m lunaspeech "Olá, mundo!"`.
- [ ] **Critério de teste do usuário:** ouvir pt-BR corretamente.

### 🔧 Fase 2 — Front-end de texto robusto (qualidade percebida)
- [ ] Normalização pt-BR: números, moeda (R$), datas, horas, siglas, abreviações, URLs.
- [ ] Sentencização e concatenação natural (pausas).
- [ ] Suporte a múltiplas vozes + controle de **velocidade** e **tom** (length_scale/noise).
- [ ] SSML básico (`<break>`, `<prosody rate>`).
- [ ] **Critério de teste:** textos do mundo real (notícias, números) bem falados.

### 🌐 Fase 3 — Serviço + Interface
- [ ] API FastAPI (`POST /speak` → WAV/MP3, `GET /voices`, streaming por sentença).
- [ ] Web UI: caixa de texto, seletor de voz, slider de velocidade, player de áudio.
- [ ] Docker para deploy fácil.
- [ ] **Critério de teste:** usar pelo navegador de qualquer dispositivo.

### 🎙️ Fase 4 — Nossa própria voz pt-BR ("voz Luna")
- [ ] Coletar/preparar dataset pt-BR (Common Voice + corpus Edresson).
- [ ] Fine-tune de um checkpoint Piper → voz Luna.
- [ ] Exportar para ONNX, integrar ao catálogo.
- [ ] **Critério de teste:** ouvir a voz Luna exclusiva.

### 🚀 Fase 5 — Recursos avançados (opcional)
- [ ] Motor Kokoro como backend "premium" (Apache 2.0).
- [ ] Clonagem de voz (referência de áudio).
- [ ] Multi-idioma; streaming em tempo real; pacote pip `lunaspeech`.

---

## 8. Conclusão da pesquisa

O LunaSpeech vai ser um sistema TTS **livre, leve e eficiente**, focado em pt-BR, construído sobre a arquitetura **VITS/ONNX** (mesma do Piper), com **nosso próprio código** para front-end de texto, motor, API e interface. Começamos com vozes pt-BR abertas (faber-medium — domínio público) e evoluímos até treinar a **voz Luna** própria. É exatamente o equilíbrio entre "do zero" (nosso produto) e pragmatismo (modelos abertos como matéria-prima) que torna o projeto viável, testável a cada etapa e verdadeiramente open source.

**Próximo passo:** iniciar a **Fase 1** — montar o esqueleto do projeto e fazer a primeira voz pt-BR "falar".
