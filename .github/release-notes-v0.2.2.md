# 🌙 LunaSpeech v0.2.2 — boot automático + comando global

Agora, ao digitar **`lunaspeech`** no terminal, o programa **inicia sozinho por completo**: banner, sequência de boot (verifica fonetizador, voz e versão) e o menu interativo. E o comando fica disponível em **qualquer terminal novo** (sem precisar ativar o ambiente).

## 🆕 O que mudou
- **Boot automático:** ao chamar `lunaspeech` (sem texto), além do menu aparece um diagnóstico rápido:
  - ✓ fonetizador (piper-phonemize ou espeak-ng)
  - ✓ voz padrão pronta / ⚠ será baixada
  - ✓ versão instalada
- **Comando global:** os instaladores adicionam `lunaspeech` ao PATH — funciona em novos terminais sem ativar o venv (Windows: PATH do usuário; Linux/macOS: `~/.bashrc`/`~/.zshrc`).

## 🔄 Atualizar
No ambiente ativado (ou em qualquer terminal se já atualizou o PATH):
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.2.2"
```
Depois é só digitar **`lunaspeech`** e o programa abre. 🌙

## 🆕 Instalação do zero
**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.2.2/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.2.2/scripts/install.sh | bash`

Full changelog: compare com [v0.2.1](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.2.1).
