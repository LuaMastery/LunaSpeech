# 🌙 LunaSpeech v0.2.1 — correção do instalador

Pequena correção de robustez nos instaladores. Mesmas funcionalidades da **v0.2.0** (Fase 2 + painel interativo).

## 🐛 O que foi corrigido
Re-executar o instalador quando o ambiente virtual já existia (e estava em uso) falhava com `Permission denied` no `python.exe`. Agora os instaladores **reusam** o ambiente virtual existente em vez de tentar recriá-lo.

## 🔄 Atualizar (você já tem uma versão anterior)
No ambiente ativado:
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.2.1"
```
Confirme: `lunaspeech --version` → `0.2.1`.

## 🆕 Instalação do zero
**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.2.1/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.2.1/scripts/install.sh | bash`

Full changelog: compare com [v0.2.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.2.0).
