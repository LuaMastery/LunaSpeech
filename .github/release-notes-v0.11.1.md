# 🌙 LunaSpeech v0.11.1 — fix: grito não é sigla + tom de pergunta forte

## 🐛 1) "EU ODEIO ISSO" não é mais soletrado
**Causa:** a regra de siglas soletrava QUALQUER palavra em maiúsculas — então um grito inteiro ("EU ODEIO ISSO") virava letra por letra. **Agora:**
- **Sequência de 2+ palavras em CAPS = grito/ênfase** → fala normalmente (e o tom emocional cuida da raiva/alegria);
- **Palavra em CAPS isolada** só é soletrada se for sigla de verdade: sem vogais (CPF, CNPJ, PM), com números (MP3) ou sigla conhecida (IBGE, ONU, USP…);
- CAPS isolada com vogais ("ISSO", "EU") = ênfase → fala como palavra.
- E se a soletração "sempre" estiver ligada nas Configurações, o painel agora **avisa em destaque** (era invisível antes).

## 🐛 2) Tom de dúvida muito mais forte
O contorno de pergunta estava sutil demais. Agora: a voz fica **+5% mais alta no geral** e **sobe até +5 semitons no final**, com curva acelerada (como uma pergunta de verdade). Duração compensada (a frase não encurta). Medido: pitch no fim da pergunta **+61%** vs. a mesma frase com ponto final.

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.11.1"
```
*(na v0.10.0+ é só abrir o painel — atualiza e reinicia sozinho)*

Full changelog: compare com [v0.11.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.11.0).
