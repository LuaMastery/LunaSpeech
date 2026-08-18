# 🌙 LunaSpeech v0.1.1 — correção para Windows

Correção de um bug que impedia a fala no **Windows**. Recomendado para todos (principalmente usuários Windows).

## 🐛 O que foi corrigido
No Windows, a saída IPA do `espeak-ng` (UTF-8) era lida com o code page local (cp1252), causando `UnicodeDecodeError` e falha na síntese. Agora:
- a saída do espeak-ng é sempre decodificada como **UTF-8**;
- o texto é enviado via **stdin** (evita problemas de acentos/code page no argv);
- o `install.ps1` não imprime "Pronto" se o teste falhar.

Nenhuma regressão: 8 testes passando; no Linux/macOS o caminho (`piper-phonemize`) é o mesmo.

## 🔄 Se você já instalou a v0.1.0 (Windows)
Não precisa re-rodar o instalador. Apenas **atualize o pacote** no PowerShell:

```powershell
C:\Users\<seu_usuario>\.lunaspeech-venv\Scripts\python.exe -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.1.1"
```

Depois teste:
```powershell
C:\Users\<seu_usuario>\.lunaspeech-venv\Scripts\lunaspeech "Olá! O LunaSpeech está funcionando agora."
```

## 🆕 Instalação do zero (uma linha)

**Windows** (PowerShell):
```powershell
irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.1.1/scripts/install.ps1 | iex
```

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.1.1/scripts/install.sh | bash
```

> Windows exige o binário `espeak-ng` (o `install.ps1` tenta instalar via winget/choco) e Python 3.9+.

## ✅ Estado da Fase 1
- Motor VITS/ONNX standalone, CLI (`lunaspeech`) e API Python (`LunaSpeech`).
- Multiplataforma: **Linux, macOS e Windows**.
- Fonemização plugável: `piper-phonemize` (Linux/macOS) ou `espeak-ng` binário (Windows).

Full changelog: compare com [v0.1.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.1.0).
