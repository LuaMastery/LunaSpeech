# 🌙 LunaSpeech v0.3.0 — painel clicável + configurações

O painel ficou muito mais fácil de usar: **navegação por setas** (sem digitar), **limpeza automática da tela** e um **sistema de configurações** no próprio terminal.

## 🆕 O que há de novo
- **🖱️ Menu navegável por setas:** use ▲▼ e Enter (ou clique nos números 1‑6). Não precisa mais digitar a opção — o `❯` mostra onde você está, em destaque.
- **🧹 Tela limpa:** ao abrir o painel (`lunaspeech`), o terminal é limpo e só fica o painel da Lua.
- **⚙️ Configurações no terminal:** nova opção **"Configurações"** no menu, onde você define (com setas, sem esforço):
  - **Voz padrão** (faber, cadu, edresson, tugao…)
  - **Velocidade padrão** (0,7× a 1,5×)
  - Restaurar padrões
  - As preferências ficam salvas em `~/.lunaspeech.json` e valem para o comando e o painel.

## 🐛 Sobre o "bug do 6"
Investigamos: ao falar "6" → "seis", o **texto/fonemas estão corretos** (`s ˈ e ɪ s`, 0 fonemas faltando). A leve falha é uma característica do **modelo faber** ao sintetizar o ditongo "ei" / palavras curtas — não é um erro do nosso código. Deve melhorar muito na Fase 4 (voz "Luna" própria).

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.3.0"
```
Depois é só digitar **`lunaspeech`** e usar as setas. 🌙

## 🆕 Instalação do zero
**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.3.0/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.3.0/scripts/install.sh | bash`

Full changelog: compare com [v0.2.2](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.2.2).
