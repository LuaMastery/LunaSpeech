# 🌙 LunaSpeech v0.8.0 — publicar online (site público) 🌍

Agora dá pra colocar o site da Luna na internet, de graça, pra **qualquer pessoa** testar no navegador.

## 🆕 Publicação com 1 clique
- **Dockerfile** + **render.yaml** incluídos → **[Deploy to Render](https://github.com/LuaMastery/LunaSpeech#-publicar-online-site-público-pra-todo-mundo)** (botão no README, plano free). Você recebe um link público tipo `https://lunaspeech.onrender.com` com o **site + API**.
- Funciona também em **Hugging Face Spaces**, **Koyeb**, **Fly.io** (qualquer host Docker).
- `lunaspeech serve` agora lê `PORT` e `LUNASPEECH_HOST` do ambiente (padrão de containers); `docker run -p 8000:8000 -e PORT=8000 lunaspeech`.

## 🐛 Corrigido
- `lunaspeech --voice X --download-only` agora funciona sem precisar de texto (útil em containers/CI).

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.8.0"
```

**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.8.0/scripts/install.ps1 | iex`

Full changelog: compare com [v0.7.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.7.0).
