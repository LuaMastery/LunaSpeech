# 🌙 LunaSpeech v0.6.0 — Integrações (transferir o Luna pra outros sistemas)

Agora você pode colocar o Luna em **qualquer sistema**: um servidor web + API, um **bot de Discord**, e mais.

## 🆕 Integrações (no painel → "Integrações" ou via terminal)
- **🌐 Servidor web + API** — `lunaspeech serve` sobe um servidor local com:
  - **Player web** em `/` (digite o texto e ouça no navegador — tema noturno, escolhe voz/tom/velocidade).
  - **API** `/speak` (GET ou POST JSON) → devolve **WAV**. Qualquer sistema chama.
  - `/voices`, `/tones`, `/health`.
- **💬 Bot de Discord** — `lunaspeech discord` roda um bot que responde a `!fala <texto>` com o **áudio em anexo** (sem precisar de canal de voz/ffmpeg). O painel mostra o passo a passo (criar bot, token, instalar `discord.py`).
- **📡 Exemplos de API** — curl, Python, JS pra integrar em qualquer lugar.

## 🧰 Como usar
```powershell
lunaspeech                 # painel → Integrações
lunaspeech serve           # sobe o servidor web + API (http://localhost:8000)
lunaspeech serve --port 9000 -v faber
lunaspeech discord         # bot de Discord (pede o token)
```
Exemplos de API (com o servidor rodando):
```bash
curl "http://localhost:8000/speak?text=ol%C3%A1&voice=faber" -o out.wav
# POST /speak  {"text":"olá","voice":"faber","rate":1.0,"tone":"auto"}
```

> Sem dependências novas no núcleo (servidor usa só a stdlib). Discord usa `discord.py` (instalado sob demanda).

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.6.0"
```

**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.6.0/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.6.0/scripts/install.sh | bash`

Full changelog: compare com [v0.5.2](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.5.2).
