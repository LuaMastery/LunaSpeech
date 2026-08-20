# 🌙 LunaSpeech v0.6.1 — correção: NameError nas Integrações

## 🐛 Corrigido
Ao abrir **Integrações → Exemplos de API** (ou **Discord**) pelo painel, ocorria `NameError: name 'dim' is not defined`. Causa: chamadas `dim(...)` sem o prefixo `ui.`. Corrigido — agora abre normalmente.

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.6.1"
```
Depois: `lunaspeech` → **Integrações**.

Full changelog: compare com [v0.6.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.6.0).
