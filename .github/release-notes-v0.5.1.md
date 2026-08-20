# 🌙 LunaSpeech v0.5.1 — correção: clique do mouse + reprodução do modo teste

Dois bugs corrigidos.

## 🐛 1) Clique do mouse não funcionava (Windows)
Faltava habilitar o **Virtual Terminal na ENTRADA** do console do Windows (`ENABLE_VIRTUAL_TERMINAL_INPUT`). Sem isso, o Windows não gerava os eventos de clique. Agora o input VT é habilitado ao entrar no menu e restaurado ao sair — o **clique do mouse** passa a funcionar no Windows Terminal (as setas continuam como fallback).

## 🐛 2) Modo "só teste" não reproduzia
A reprodução usava `os.startfile` (abrindo um player externo, frágil). Agora, no Windows, usa **`winsound.PlaySound`** (biblioteca padrão) — **toca o WAV direto**, sem abrir nada. Se não conseguir tocar, mostra um aviso claro. (Modo só teste = toca o áudio sem salvar arquivo, exatamente pra testar.)

## 🔄 Atualizar
```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/LuaMastery/LunaSpeech.git@v0.5.1"
lunaspeech
```

## 🆕 Instalação do zero
**Windows:** `irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.5.1/scripts/install.ps1 | iex`
**Linux/macOS:** `curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.5.1/scripts/install.sh | bash`

Full changelog: compare com [v0.5.0](https://github.com/LuaMastery/LunaSpeech/releases/tag/v0.5.0).
