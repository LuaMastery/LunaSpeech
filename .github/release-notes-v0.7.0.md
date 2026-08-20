# 🌙 LunaSpeech v0.7.0 — o site da Luna 🌐

O `lunaspeech serve` agora serve o **site completo da LunaSpeech** — uma página linda (tema noturno, estrelas) onde você testa **todo o sistema** no navegador.

## 🆕 O site (http://localhost:8000)
- **Hero** com o título "LunaSpeech · voz da lua".
- **Player completo**: digite o texto, escolha **voz**, **tom** (auto/amigável/raivoso/...) e **velocidade**, clique em **🔊 Falar** e ouça — com botão de **⬇ Baixar .wav**.
- **Recursos**: cartões com tudo que a Luna faz (pt-BR, tom emocional, soletração, leve/CPU, integrações).
- **Vozes**: cartões clicáveis — clique numa voz pra testá-la no player.
- Rodapé com a versão e link do GitHub.

E continua com a **API** (`/speak`, `/voices`, `/tones`, `/health`) pra outros sistemas. O navegador abre sozinho ao rodar `lunaspeech serve`.

## ▶️ Como usar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.7.0"
lunaspeech serve          # abre o site no navegador
# ou pelo painel: lunaspeech → Integrações → Servidor web + API
```

**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.7.0/scripts/install.ps1 | iex`

Full changelog: compare com [v0.6.2](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.6.2).
