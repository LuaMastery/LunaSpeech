# 🌙 LunaSpeech v0.5.2 — cursor invisível no painel

Pequena melhoria visual.

## ✨ O que mudou
- **Cursor invisível:** ao usar o painel (`lunaspeech`), a "risquinha" branca do cursor fica **escondida** durante a navegação e a digitação — visual mais limpo. O cursor volta automaticamente ao sair (com rede de segurança `atexit`, então nunca fica sem cursor).

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.5.2"
lunaspeech
```

**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.5.2/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.5.2/scripts/install.sh | bash`

Full changelog: compare com [v0.5.1](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.5.1).
