# 🌙 LunaSpeech v0.9.1 — correção: NameError ao testar fala no painel

## 🐛 Corrigido
Ao usar **Testar fala** no painel, ocorria `NameError: name 'cfg' is not defined` (a função referenciava a configuração sem recebê-la). Corrigido: o teste agora usa a configuração completa — **soletração automática**, **versão Flash/Thinking** e **modo só teste** funcionam no painel.

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.9.1"
```

Full changelog: compare com [v0.9.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.9.0).
