# 🌙 LunaSpeech v0.11.0 — vírgula natural, tom de pergunta e emoções expressivas

Três correções grandes de naturalidade da voz.

## 🐛 1) Vírgula não é mais ponto final
No Windows (espeak CLI), cada cláusula virava uma "frase" separada — a vírgula parava como ponto final ("beleza, show de bola" virava duas frases). Agora as cláusulas com vírgula/dois-pontos/ponto-e-vírgula ficam **na mesma frase**, com pausa curta natural.

## 🆕 2) Perguntas com tom de dúvida
Frases que terminam em **"?"** agora recebem automaticamente um **contorno de pitch ascendente** no final (a voz sobe no fim, como numa pergunta de verdade). Funciona com o tom automático e com qualquer tom fixo.

## 🆕 3) Emoções muito mais expressivas (fim da voz "seca")
Cada emoção agora controla, além da prosódia do modelo, o **pitch** (com compensação de duração — não muda o tempo) e o **volume**, com valores calibrados por medição:

| Tom | Duração | Pitch | Volume |
|---|---|---|---|
| 😔 triste | +9% (lenta) | −8% (grave) | −22% (baixa) |
| 🙂 neutro | — | — | — |
| 😄 alegre | −15% (rápida) | +6% (aguda) | +10% |
| 😡 raivoso | −20% (muito rápida) | +4% | +50% (forte) |

Medido: `triste 5.46s/0.124/0.44` · `neutro 5.02s/0.135/0.57` · `alegre 4.69s/0.137/0.69` · `raivoso 4.00s/0.130/0.87`

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.11.0"
```
*(Se você já está na v0.10.0, é só abrir o painel que ele se atualiza e reinicia sozinho.)* 🔄

Full changelog: compare com [v0.10.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.10.0).
