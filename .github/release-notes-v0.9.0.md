# 🌙 LunaSpeech v0.9.0 — soletração automática + versões Flash/Thinking ⚡🧠

## 🆕 1) Soletração automática
A Luna agora **reconhece sozinha** se o texto deve ser soletrado:
- códigos com letras e números (`AB12`, `x9k`) → soletra;
- palavras sem vogais (`xkcd`, `www`, `str`) → soletra;
- frases e palavras normais → fala normalmente.

Configurável em **Configurações → Soletração**: `automática` (padrão), `sempre` ou `nunca`. Também na configuração web e no site (`spell` no `/speak`).

## 🆕 2) Versões da Luna: Flash e Thinking
- **⚡ Flash** — síntese em uma passada. Resposta rápida (padrão).
- **🧠 Thinking** — gera **4 variantes** por sentença e escolhe a **mais suave** (menor fator de crista = menos picos/glitches). Demora ~4×, sai com a voz mais aprimorada.

Como usar:
```powershell
lunaspeech "olá" --mode thinking     # versão Thinking
lunaspeech "olá" --mode flash        # versão Flash
```
Ou em **Configurações → Versão** (vale para o painel, CLI e site). No site, há um seletor **Versão** no player.

> No teste real: Flash = 0,30s (crista 6,00); Thinking = 0,91s (crista 5,54) — voz visivelmente mais suave.

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.9.0"
```

**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.9.0/scripts/install.ps1 | iex`

Full changelog: compare com [v0.8.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.8.0).
