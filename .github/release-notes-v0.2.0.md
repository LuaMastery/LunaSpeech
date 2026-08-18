# 🌙 LunaSpeech v0.2.0 — Fase 2 + CLI interativo

Primeira versão com o **front-end de texto pt-BR completo** e o **painel interativo com tema noturno**. Tudo validado no Windows pelo usuário (v0.1.1). 🎉

## 🆕 O que há de novo

### 🔧 Fase 2 — Normalização de texto pt-BR
O LunaSpeech agora "entende" e fala corretamente formas escritas antes de fonetizar:
- **Moeda:** `R$ 1.234,56` → "mil duzentos e trinta e quatro reais e cinquenta e seis centavos"
- **Números e decimais:** `1.234` → "mil duzentos e trinta e quatro"; `3,14` → "três vírgula um quatro"
- **Datas:** `18/08/2026` → "dezoito de agosto de dois mil e vinte e seis"
- **Horas:** `14:30` / `14h30` → "quatorze e trinta"
- **Porcentagem:** `50%` → "cinquenta por cento"
- **Ordinais:** `1º` → "primeiro", `2ª` → "segunda"
- **Unidades e temperatura:** `10kg`, `100km/h`, `30°C`
- **Siglas:** `CPF` → "cê pê éfe"
- **Abreviações:** `Dr.` → "doutor", `Sra.` → "senhora", `etc.` → "etcétera"

### 🌙 Painel interativo (tema noturno)
Digite só **`lunaspeech`** (sem texto) e abre um menu com cores no estilo "lua" (índigo/violeta/prateado/dourado):
- 🎙 **Testar fala** — digite um texto e ouça
- ⬆️ **Buscar atualizações** — verifica nova versão no GitHub e instala
- ♻️ **Reinstalar** — reinstala o LunaSpeech
- 🗣 **Listar vozes**

Banner ASCII com estrelas e lua também nos instaladores (`install.sh` / `install.ps1`).

## ⚡ Instalação

**Windows** (PowerShell):
```powershell
irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.2.0/scripts/install.ps1 | iex
```

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.2.0/scripts/install.sh | bash
```

## 🔄 Atualizar de versão anterior
```powershell
# Windows (no ambiente ativado):
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.2.0"
```
```bash
# Linux/macOS:
pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.2.0"
```
Ou, no menu interativo, escolha **2) Buscar atualizações**.

## ✅ Testes
- **19 testes** pytest passando (motor + normalização pt-BR), incluindo integração com modelo real.
- Fase 1 validada no Windows pelo usuário.

## 🗺️ Próximos passos
- SSML básico (`<break>`, `<prosody>`).
- **Fase 3:** API HTTP (FastAPI) + interface web.

Full changelog: compare com [v0.1.1](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.1.1).
