# 🌙 LunaSpeech v0.12.0 — soletração seletiva (só a parte que precisa)

## 🆕 Soletração inteligente por partes
Agora, quando o texto tem uma **sequência de letras** para soletrar, a Luna soletra **apenas essa parte** — o resto da frase é falado normalmente:

> "boa tarde, tudo bem, agora eu vou soletrar um A, B, C, D, E"
> → fala a frase normalmente e soletra **só** o "á, bê, cê, dê, éi"

Funciona com vírgulas (`A, B, C`) e espaços (`A B C`), no painel, CLI e site. E é seletiva de verdade:
- "E aí pessoal?" → **não** soletra (o "E" é palavra)
- letra isolada ("a letra X") → não soletra (só sequências)
- siglas (CPF) continuam sendo soletradas como sempre

## 🧹 Menos confusão com "sempre soletrar"
O modo "sempre" (que soletra TODO o texto) agora está com rótulo claro no site ("sempre — soletra TODO o texto") e o painel avisa em destaque quando está ligado.

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.12.0"
```
*(na v0.10.0+ é só abrir o painel — atualiza e reinicia sozinho)*

Full changelog: compare com [v0.11.1](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.11.1).
