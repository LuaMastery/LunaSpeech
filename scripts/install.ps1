# 🌙 LunaSpeech — instalador rápido para Windows (PowerShell)
#
# Uso (uma linha, no PowerShell):
#   irm https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.3.0/scripts/install.ps1 | iex
#
# Pré-requisitos: Python 3.9+ (python.org) e o espeak-ng instalado.
# O script tenta instalar o espeak-ng via winget/choco se faltar.

#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Repo    = "LuaMastery/LunaSpeech"
$Version = if ($env:LUNASPEECH_VERSION) { $env:LUNASPEECH_VERSION } else { "v0.6.0" }
$Py      = if ($env:PYTHON) { $env:PYTHON } else { "python" }

Write-Host ""
Write-Host "  ✦     ·     ✧        ·       ✦   " -ForegroundColor DarkYellow
Write-Host "   🌙   " -NoNewline; Write-Host "LunaSpeech" -ForegroundColor Magenta
Write-Host "        voz da lua  •  text-to-speech" -ForegroundColor Cyan
Write-Host "        ✦  instalador $Version  ✦" -ForegroundColor DarkYellow
Write-Host "-----------------------------------------"

# 1) verifica Python 3.9+
try { $pv = & $Py -c "import sys;print('%d.%d'%sys.version_info[:2])" } catch {
    Write-Host "❌  Python não encontrado ('$Py'). Instale o Python 3.9+ em https://python.org" -ForegroundColor Red
    exit 1
}
$major,$minor = $pv.Trim().Split('.')
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 9)) {
    Write-Host "❌  LunaSpeech precisa de Python 3.9+ (detectado $pv)." -ForegroundColor Red
    exit 1
}
Write-Host "✓  Python: $pv"

# 2) ambiente virtual isolado (reusa se já existir — evita "permission denied")
$Venv = if ($env:VENV) { $env:VENV } else { Join-Path $HOME ".lunaspeech-venv" }
if (Test-Path "$Venv\Scripts\python.exe") {
    Write-Host "→  Reusando ambiente virtual existente: $Venv"
} else {
    Write-Host "→  Criando ambiente virtual em: $Venv"
    & $Py -m venv "$Venv"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌  Falha ao criar o ambiente virtual." -ForegroundColor Red
        Write-Host "    Dica: feche outros terminais/Python e tente de novo, ou use outro caminho:" -ForegroundColor Yellow
        Write-Host "          `$env:VENV='C:\outro\caminho'; irm ... | iex" -ForegroundColor Yellow
        exit 1
    }
}
& "$Venv\Scripts\python.exe" -m pip install --upgrade pip --quiet

# 3) instala o LunaSpeech (núcleo multiplataforma) a partir da tag no GitHub
Write-Host "→  Instalando lunaspeech $Version..."
& "$Venv\Scripts\python.exe" -m pip install --quiet "git+https://github.com/$Repo.git@$Version"
if ($LASTEXITCODE -ne 0) { Write-Host "❌  Falha ao instalar o lunaspeech." -ForegroundColor Red; exit 1 }

# 3.1) disponibiliza 'lunaspeech' em qualquer terminal (PATH do usuário)
$ScriptsDir = Join-Path $Venv "Scripts"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($ScriptsDir -and ($userPath -notlike "*$ScriptsDir*")) {
    $newPath = if ($userPath) { "$userPath;$ScriptsDir" } else { "$ScriptsDir" }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "✓  'lunaspeech' disponível em novos terminais (sem precisar ativar)" -ForegroundColor Green
}

# 4) garante o espeak-ng (fonemização no Windows)
if (-not (Get-Command espeak-ng -ErrorAction SilentlyContinue) -and
    -not (Get-Command espeak -ErrorAction SilentlyContinue)) {
    Write-Host "→  espeak-ng não encontrado. Tentando instalar..."
    $ok = $false
    foreach ($cmd in @("winget install --silent --id espeak-ng.espeak-ng --accept-package-agreements --accept-source-agreements",
                       "choco install espeak-ng -y")) {
        try { Invoke-Expression $cmd | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } } catch {}
    }
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    if (-not (Get-Command espeak-ng -ErrorAction SilentlyContinue)) {
        Write-Host "⚠️  Não consegui instalar o espeak-ng automaticamente." -ForegroundColor Yellow
        Write-Host "    Instale manualmente: https://github.com/espeak-ng/espeak-ng/releases"
        Write-Host "    (depois, reabra o PowerShell para atualizar o PATH)"
    }
}

# 5) baixa a voz pt-BR (faber) — do release do GitHub; se não houver, do HuggingFace
$ModelsDir = if ($env:LUNASPEECH_MODELS) { $env:LUNASPEECH_MODELS } else { Join-Path $HOME ".local\share\lunaspeech\models" }
$FaberDir  = Join-Path $ModelsDir "faber"
Write-Host "→  Baixando voz pt-BR (faber) para: $FaberDir"
New-Item -ItemType Directory -Force -Path $FaberDir | Out-Null
$ReleaseBase = "https://github.com/$Repo/releases/download/$Version"
$HfBase      = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium"
function Get-VoiceFile($name) {
    $dst = Join-Path $FaberDir $name
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "$ReleaseBase/$name" -OutFile $dst -ErrorAction Stop
    } catch {
        Write-Host "   (asset ausente no release — baixando do HuggingFace)"
        Invoke-WebRequest -UseBasicParsing -Uri "$HfBase/$name" -OutFile $dst
    }
}
Get-VoiceFile "pt_BR-faber-medium.onnx"
Get-VoiceFile "pt_BR-faber-medium.onnx.json"

# 6) teste de fala
$Teste = Join-Path $HOME "lunaspeech_teste.wav"
Write-Host "→  Testando fala..."
& "$Venv\Scripts\python.exe" -m lunaspeech "Olá! O sistema de fala LunaSpeech está funcionando." --out "$Teste"
$testOk = $LASTEXITCODE -eq 0

Write-Host "-----------------------------------------"
if ($testOk) {
    Write-Host "✅  Pronto!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Instalação concluída, mas o teste de fala falhou." -ForegroundColor Yellow
    Write-Host "    Verifique se o espeak-ng está no PATH (reabra o PowerShell após instalá-lo)."
    Write-Host "    Rode novamente: lunaspeech `"texto`"  e veja a mensagem de erro."
}
Write-Host ""
Write-Host "   Para usar (ative o ambiente antes):"
Write-Host "     $Venv\Scripts\Activate.ps1"
Write-Host "     lunaspeech `"qualquer texto em português`""
Write-Host "     lunaspeech --list-voices"
Write-Host "     lunaspeech `"mais rápido`" --rate 1.3"
Write-Host ""
Write-Host "   Áudio de teste: $Teste"
Write-Host "   Ambiente:       $Venv"
