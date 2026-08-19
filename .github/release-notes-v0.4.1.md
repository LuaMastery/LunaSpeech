# 🌙 LunaSpeech v0.4.1 — correção do glitch em termos estrangeiros

Corrige o bug em que palavras estrangeiras (como **"value"**) glitchavam severamente.

## 🐛 O que estava acontecendo
O espeak-ng com voz pt-BR **deturpava** palavras estrangeiras em sequências fonéticas estranhas (ex.: `"value"` → `v ˌ a l ˈ u y`) que o modelo não conseguia sintetizar — gerando um glitch audível.

## ✅ Correção
Novo módulo `lunaspeech/text/foreign.py` com duas frentes:
1. **Dicionário** de termos estrangeiros comuns (tecnologia) → pronúncia pt-BR **limpa e verificada** (fonemiza sem artefatos):
   - `value` → "vâliu", `server` → "sérver", `online` → "ônlaini", `game` → "gêimi", `site` → "sáiti", `download`, `background`, `stream`, `wifi`, `login`, `email`, `code`, `data`, `mouse`, `app`, `bug`, `link`, `web`… (~45 termos).
2. **Soletração** de palavras com a letra **'y'** (youtube, play, python) — sempre pronunciável, nunca glitcha. Seguro porque o português nativo não usa 'y'.

Resultados (antes → depois):
- `"value"`: `v ˌ a l ˈ u y` (glitch) → **`v ˈ æ l j u`** (limpo) ✅

**Sem falsos positivos:** palavras normais e empréstimos do pt-BR (`show`, `web`, `kilo`) e unidades (`km`, `kg`) **não são alterados** — só a letra 'y' dispara a soletração (além do dicionário curado).

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.4.1"
```

## 🆕 Instalação do zero
**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.4.1/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.4.1/scripts/install.sh | bash`

Full changelog: compare com [v0.4.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.4.0).
