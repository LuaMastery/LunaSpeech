# 🌙 LunaSpeech v0.5.0 — mouse, configurações web, auto-update e telas limpas

Painel muito mais completo e fácil de usar.

## 🆕 O que há de novo

### 🖱️ Clique do mouse nos botões
Além das setas ▲▼ + Enter, agora você pode **clicar** diretamente nas opções do menu com o mouse (em terminais com suporte a mouse SGR: Windows Terminal, iTerm2, gnome/konsole…). As setas continuam funcionando como fallback.

### 🌐 Configurações de duas formas
Ao abrir **Configurações**, você escolhe:
- **🌐 Navegador (HTML)** — abre uma página bonita (tema noturno) no navegador com todos os ajustes; basta salvar.
- **⌨️ Terminal (CLI)** — configura pelo painel, com setas/clique.

### 🔁 Atualização automática
Nova opção **"Atualização automática"** (ligada por padrão): ao abrir o painel, o Luna verifica sozinho se há versão nova no GitHub e atualiza — sem precisar fazer isso toda hora.

### 🎧 Modo só teste
Nova opção **"Modo só teste"**: quando ligada, o Luna **toca o áudio sem salvar arquivo** (apenas para testar). Desligada = salva o `.wav` como antes.

### 🧹 Telas limpas (fim da "bagunça")
Ao clicar em um botão que troca de aba (Configurações, Testar, etc.), o terminal é **limpo** e só aparece a nova aba — não acumula mais menu sobre menu.

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.5.0"
lunaspeech
```

## 🆕 Instalação do zero
**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.5.0/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.5.0/scripts/install.sh | bash`

Full changelog: compare com [v0.4.1](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.4.1).
