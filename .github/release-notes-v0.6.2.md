# 🌙 LunaSpeech v0.6.2 — correção: soletrar (e flag --spell)

## 🐛 Corrigido
A soletração glitchava em várias letras (F, L, M, N, R, S e E). Causa: os nomes dessas letras em pt-BR terminam em "e"/acento e o espeak os convertia num `y` solto (o mesmo bug do "value"). Agora usamos as formas limpas (éli, êmi, êni, érri, éssi, éfi, éi) — soam naturais e não glitcham. **Acronimos (CPF, CNPJ) e nomes estrangeiros agora soletram corretamente.**

## 🆕 Pedir pra soletrar explicitamente
- CLI: `lunaspeech "casa" --spell` → soletra letra por letra.
- Painel: em **Testar fala**, depois de digitar o texto, perguntamos "Soletrar letra por letra? [s/N]".

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.6.2"
```

Full changelog: compare com [v0.6.1](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.6.1).
