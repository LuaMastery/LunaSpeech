#!/usr/bin/env bash
#
# 🌙 LunaSpeech — instalador rápido (Linux / macOS)
#
# Uso (uma linha):
#   curl -fsSL https://github.com/LuaMastery/LunaSpeech/releases/download/v0.3.0/install.sh | bash
#
# Ou, para uma versão específica:
#   LUNASPEECH_VERSION=v0.1.0 curl -fsSL https://raw.githubusercontent.com/LuaMastery/LunaSpeech/v0.1.0/scripts/install.sh | bash
#
set -euo pipefail

REPO="LuaMastery/LunaSpeech"
VERSION="${LUNASPEECH_VERSION:-v0.9.1}"
PYTHON="${PYTHON:-python3}"
RELEASE_BASE="https://github.com/${REPO}/releases/download/${VERSION}"

if [ -t 1 ]; then
  C_VIOLET='\033[38;5;141m'; C_LUNAR='\033[38;5;117m'; C_GOLD='\033[38;5;221m'
  C_DIM='\033[2m'; C_GREEN='\033[38;5;114m'; C_OFF='\033[0m'
else
  C_VIOLET=''; C_LUNAR=''; C_GOLD=''; C_DIM=''; C_GREEN=''; C_OFF=''
fi

printf "\n${C_GOLD}  ✦     ·     ✧        ·       ✦   ${C_OFF}\n"
printf "   🌙   ${C_VIOLET}LunaSpeech${C_OFF}   \n"
printf "${C_LUNAR}        voz da lua  •  text-to-speech${C_OFF}\n"
printf "        ${C_GOLD}✦${C_OFF}  ${C_DIM}instalador ${VERSION}${C_OFF}  ${C_GOLD}✦${C_OFF}\n"
echo "-----------------------------------------"

# 1) verifica Python 3.9+
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "❌  Python 3 não encontrado ('${PYTHON}'). Instale o Python 3.9+ e tente de novo." >&2
  exit 1
fi
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || {
  echo "❌  LunaSpeech precisa de Python 3.9+." >&2; exit 1; }
echo "✓  Python: $("$PYTHON" -V)"

# 2) ambiente virtual isolado (reusa se já existir)
VENV="${VENV:-$HOME/.lunaspeech-venv}"
if [ -x "$VENV/bin/python" ]; then
    echo "→  Reusando ambiente virtual existente: $VENV"
else
    echo "→  Criando ambiente virtual em: $VENV"
    "$PYTHON" -m venv "$VENV" || { echo "❌  Falha ao criar o ambiente virtual." >&2; exit 1; }
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip >/dev/null

# 3) instala o LunaSpeech a partir do release (tag) no GitHub
echo "→  Instalando lunaspeech ${VERSION}..."
python -m pip install --quiet "git+https://github.com/${REPO}.git@${VERSION}"
# fonemização: piper-phonemize traz o espeak-ng embutido (Linux/macOS)
python -m pip install --quiet piper-phonemize || \
  echo "   (aviso: piper-phonemize não instalado — instale o espeak-ng do sistema)"

# 3.1) disponibiliza 'lunaspeech' em qualquer terminal (novo shell)
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  [ -f "$rc" ] || continue
  grep -qF "$VENV/bin" "$rc" 2>/dev/null || \
    printf '\nexport PATH="%s:$PATH"  # lunaspeech\n' "$VENV/bin" >> "$rc"
done
[ -f "$HOME/.bashrc" ] && echo "✓  'lunaspeech' adicionado ao ~/.bashrc (abra um novo terminal)"

# 4) baixa a voz pt-BR (faber): primeiro do release do GitHub; se não houver, do HuggingFace
MODELS_DIR="${LUNASPEECH_MODELS:-$HOME/.local/share/lunaspeech/models}"
FABER_DIR="$MODELS_DIR/faber"
echo "→  Baixando voz pt-BR (faber) para: $FABER_DIR"
mkdir -p "$FABER_DIR"

HF_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium"
download_voice_file() {
  local name="$1"
  if curl -fsSL "$RELEASE_BASE/$name" -o "$FABER_DIR/$name"; then
    return 0
  fi
  echo "   (asset não encontrado no release — baixando do HuggingFace)"
  curl -fsSL "$HF_BASE/$name" -o "$FABER_DIR/$name"
}
download_voice_file "pt_BR-faber-medium.onnx"
download_voice_file "pt_BR-faber-medium.onnx.json"

# 5) teste de fala
TESTE="$HOME/lunaspeech_teste.wav"
echo "→  Testando fala..."
python -m lunaspeech "Olá! O sistema de fala LunaSpeech está funcionando." --out "$TESTE"

echo "-----------------------------------------"
echo "✅  Pronto!"
echo
echo "   Para usar (ative o ambiente antes):"
echo "     source $VENV/bin/activate"
echo "     lunaspeech \"qualquer texto em português\""
echo "     lunaspeech --list-voices          # ver vozes"
echo "     lunaspeech \"mais rápido\" --rate 1.3"
echo
echo "   Áudio de teste gerado em: $TESTE"
echo "   Ambiente virtual:         $VENV"
deactivate
