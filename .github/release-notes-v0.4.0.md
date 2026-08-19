# 🌙 LunaSpeech v0.4.0 — tom de voz emocional 🎭

Agora o Luna **sentem emoção do texto** e ajusta o tom de voz: amigável fica mais calmo/expressivo; raivoso fica mais rápido/tenso; triste fica lento/monótono.

## 🆕 Tom de voz emocional
- **Detecção automática** (pt-BR): analisa palavras-chave, MAIÚSCULAS, pontuação (!!!) e emojis para classificar o tom — **amigável, alegre, raivoso, triste** (ou neutro).
- Cada tom ajusta a **prosódia** (velocidade, variação de tom e ritmo — as escalas do VITS).
- Exemplos:
  - `"Que legal, valeu!"` → **amigável** (mais caloroso)
  - `"EU ODEIO ISSO!!!"` → **raivoso** (rápido e tenso)
  - `"Estou triste hoje..."` → **triste** (lento e monótono)
- Controle total:
  - CLI: `lunaspeech "texto" --tone auto` (ou `neutro`/`amigavel`/`alegre`/`raivoso`/`triste`)
  - Painel: **Configurações → Tom de voz** (escolher por setas)
  - O tom detectado aparece na saída: `✓ Áudio gerado ... (tom: raivoso)`

> Nota técnica: o efeito é uma *modelagem de prosódia* (sutil, mas perceptível), pois o modelo faber não é treinado em emoção. Ficará muito expressivo com a "voz Luna" própria (Fase 4).

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.4.0"
```

## 🆕 Instalação do zero
**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.4.0/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.4.0/scripts/install.sh | bash`

Full changelog: compare com [v0.3.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.3.0).
