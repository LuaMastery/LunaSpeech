# 🌙 LunaSpeech v0.1.0 — Fase 1 (MVP)

Sistema de Text-to-Speech leve, open source e em CPU — **fala qualquer texto em Português do Brasil**. Não precisa de GPU, nem PyTorch, nem serviços pagos.

## ⚡ Teste rápido (uma linha — Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.1.0/scripts/install.sh | bash
```

Isso instala o LunaSpeech e baixa a voz pt-BR (faber), depois fala uma frase de teste. O áudio fica em `~/lunaspeech_teste.wav`.

## 🚀 Uso

```bash
source ~/.lunaspeech-venv/bin/activate          # ativa o ambiente (uma vez por sessão)

lunaspeech "Olá, mundo!"                         # fala em pt-BR (gera lunaspeech_out.wav)
lunaspeech "Texto mais rápido." --rate 1.3       # 30% mais rápido
lunaspeech "Texto lento." --rate 0.8
lunaspeech --list-voices                         # ver vozes disponíveis
echo "Texto do stdin" | lunaspeech
```

Python (API):
```python
from lunaspeech import LunaSpeech
tts = LunaSpeech()                       # voz padrão pt-BR (faber)
tts.say("Bem-vindo ao LunaSpeech!", "saida.wav")
```

## 📦 Downloads
- **Source code** (zip/tar.gz) — código completo desta versão (gerado automaticamente pelo GitHub).
- `scripts/install.sh` — instalador automático (dentro do source, ou via `raw.githubusercontent.com/.../v0.1.0/scripts/install.sh`).

> Se preferir não usar o `install.sh`:
> ```bash
> python3 -m venv .venv && source .venv/bin/activate
> pip install "git+https://github.com/LuaMastery/LunaSpeech.git@v0.1.0"
> lunaspeech "Olá!"   # baixa a voz do HuggingFace na 1ª execução
> ```

### 💡 Quer a voz pt-BR como arquivo de release (sem depender do HuggingFace)?
O workflow pronto está em `docs/release-workflow.yml`. Copie para `.github/workflows/release.yml`
(com permissão de administrador do repo) e ele anexará automaticamente a voz faber
ao release em futuras tags.

## ✅ O que funciona nesta versão (Fase 1)
- **Motor VITS/ONNX standalone** (próprio): fonemas espeak-ng → IDs → inferência em CPU → WAV.
- **Fonemização pt-BR** via espeak-ng (empacotado em `piper-phonemize`).
- **CLI** (`lunaspeech`) + **API Python** (`LunaSpeech`).
- **Controle de velocidade** (`--rate`), streaming por sentença, normalização de áudio.
- **8 testes** automatizados passando (incl. integração com modelo real).

## 🗺️ Próximas fases
- 🔧 **Fase 2** (em desenvolvimento): front-end de texto robusto — números, moeda `R$`, datas, horas, siglas, abreviações.
- 🌐 **Fase 3**: API HTTP (FastAPI) + interface web.
- 🎙️ **Fase 4**: nossa própria voz pt-BR ("voz Luna").

## ⚙️ Requisitos
- Python ≥ 3.9
- ~100 MB de RAM (roda em CPU; funciona até em Raspberry Pi)
- Linux ou macOS (para Windows, use WSL ou aguarde suporte nativo)

## 📄 Licença
Código: MIT. Voz faber: CC0 (domínio público).
