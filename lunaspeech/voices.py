"""Catálogo de vozes e download sob demanda.

Vozes Piper = ``.onnx`` (modelo) + ``.onnx.json`` (config). Elas ficam no
HuggingFace (``rhasspy/piper-voices``). O LunaSpeech baixa sob demanda para um
diretório de modelos.

Detalhe importante: o **config** da voz padrão pt-BR (faber) já vem **embutido**
no pacote (``lunaspeech/voices_data``), então apenas o binário ``.onnx`` precisa
ser baixado — tornando a voz pt-BR robusta mesmo se apenas o ``.json`` estiver
acessível.

Há também uma voz de **teste** (``en-test``) obtida via API de blobs do GitHub,
que funciona mesmo em redes onde o HuggingFace está bloqueado — útil para
validar o motor.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

PKG_DIR = Path(__file__).parent
VOICES_DATA = PKG_DIR / "voices_data"

DEFAULT_VOICE = "faber"


class VoiceDownloadError(RuntimeError):
    """Falha ao obter os arquivos de uma voz (com mensagem acionável)."""


@dataclass(frozen=True)
class VoiceSpec:
    """Descrição de uma voz e de onde baixá-la."""

    name: str
    language: str
    description: str
    # --- fonte HuggingFace ---
    hf_repo: str = ""
    hf_path: str = ""          # caminho no repo (sem revision)
    revision: str = "main"
    embedded_config: Optional[str] = None  # nome do .json embutido em voices_data
    # --- fonte alternativa: blob do GitHub ---
    gh_repo: str = ""
    gh_onnx_sha: str = ""
    gh_json_sha: str = ""
    gh_filename: str = ""

    @property
    def is_hf(self) -> bool:
        return bool(self.hf_repo)

    @property
    def is_github_blob(self) -> bool:
        return bool(self.gh_repo and self.gh_onnx_sha)

    @property
    def onnx_name(self) -> str:
        return (Path(self.hf_path).name if self.is_hf else self.gh_filename) + ".onnx"

    @property
    def json_name(self) -> str:
        return self.onnx_name + ".json"


# fmt: off
VOICES: dict[str, VoiceSpec] = {
    "faber": VoiceSpec(
        "faber", "pt-BR",
        "Voz masculina pt-BR (medium, 22 kHz). Domínio público (CC0). [PADRÃO]",
        hf_repo="rhasspy/piper-voices",
        hf_path="pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
        revision="v1.0.0",
        embedded_config="pt_BR-faber-medium.onnx.json",
    ),
    "cadu": VoiceSpec(
        "cadu", "pt-BR",
        "Voz masculina pt-BR (medium, 22 kHz). CC0.",
        hf_repo="rhasspy/piper-voices",
        hf_path="pt/pt_BR/cadu/medium/pt_BR-cadu-medium.onnx",
        revision="v1.0.0",
    ),
    "edresson": VoiceSpec(
        "edresson", "pt-BR",
        "Voz pt-BR (low, 16 kHz). CC BY 4.0.",
        hf_repo="rhasspy/piper-voices",
        hf_path="pt/pt_BR/edresson/low/pt_BR-edresson-low.onnx",
        revision="v1.0.0",
    ),
    "tugao": VoiceSpec(
        "tugao", "pt-PT",
        "Voz masculina de Portugal (medium).",
        hf_repo="rhasspy/piper-voices",
        hf_path="pt/pt_PT/tugão/medium/pt_PT-tugão-medium.onnx",
        revision="v1.0.0",
    ),
    "en-test": VoiceSpec(
        "en-test", "en-US",
        "Voz inglesa de TESTE (lessac) do repo rhasspy/piper — baixada via API "
        "do GitHub. Útil para validar o motor sem depender do HuggingFace.",
        gh_repo="rhasspy/piper",
        gh_onnx_sha="575e2f053418501c47a6cdd79b1f7642079f894e",
        gh_json_sha="d64db2e768280bea5e5a90d3b71a29e512bf0899",
        gh_filename="test_voice",
    ),
}
# fmt: on


# ----------------------------------------------------------------- diretórios
def models_dir(override: Optional[str] = None) -> Path:
    """Onde as vozes são guardadas. Prioridade: arg > $LUNASPEECH_MODELS > padrão."""
    d = override or os.environ.get("LUNASPEECH_MODELS")
    if d:
        return Path(d)
    return Path.home() / ".local" / "share" / "lunaspeech" / "models"


def voice_dir(name: str, md: Optional[Path] = None) -> Path:
    return (md or models_dir()) / name


# ----------------------------------------------------------------- downloads
def _http_get(url: str, dest: Path, timeout: int = 180) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "lunaspeech/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def _hf_urls(spec: VoiceSpec) -> Tuple[str, str]:
    base = f"https://huggingface.co/{spec.hf_repo}/resolve/{spec.revision}/{spec.hf_path}"
    return base, base + ".json"


def _github_blob(repo: str, sha: str) -> bytes:
    url = f"https://api.github.com/repos/{repo}/git/blobs/{sha}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json", "User-Agent": "lunaspeech/0.1"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    return base64.b64decode(data["content"])


def _human_error(spec: VoiceSpec, exc: BaseException) -> str:
    """Mensagem de erro acionável (ex.: HuggingFace bloqueado na rede)."""
    if spec.is_hf:
        onnx_url, json_url = _hf_urls(spec)
        return (
            f"Não foi possível baixar a voz '{spec.name}' do HuggingFace.\n"
            f"  Causa: {exc}\n\n"
            f"Baixe manualmente e coloque em: {voice_dir(spec.name)}\n"
            f"  Modelo (.onnx): {onnx_url}\n"
            f"  Config  (.json): {json_url}\n\n"
            f"Ou use a voz de teste que não depende do HF:\n"
            f"  lunaspeech \"Hello world\" --voice en-test\n"
        )
    return f"Não foi possível baixar a voz '{spec.name}': {exc}"


def ensure_voice(name: str, md: Optional[Path] = None) -> Tuple[Path, Path]:
    """Garante que os arquivos da voz existam localmente, baixando se preciso.

    Returns:
        (caminho_onnx, caminho_json)
    """
    spec = VOICES.get(name)
    if spec is None:
        raise VoiceDownloadError(
            f"Voz desconhecida: {name!r}. Disponíveis: {', '.join(VOICES)}"
        )

    vdir = voice_dir(name, md)
    onnx_path = vdir / spec.onnx_name
    json_path = vdir / spec.json_name
    if onnx_path.exists() and json_path.exists():
        return onnx_path, json_path

    vdir.mkdir(parents=True, exist_ok=True)

    # 1) config: usa o embutido se houver (sempre disponível, mesmo offline)
    if not json_path.exists() and spec.embedded_config:
        embedded = VOICES_DATA / spec.embedded_config
        if embedded.exists():
            shutil.copyfile(embedded, json_path)

    # 2) baixa o que ainda falta
    try:
        if spec.is_hf:
            onnx_url, json_url = _hf_urls(spec)
            if not onnx_path.exists():
                _http_get(onnx_url, onnx_path)
            if not json_path.exists():
                _http_get(json_url, json_path)
        elif spec.is_github_blob:
            if not onnx_path.exists():
                onnx_path.write_bytes(_github_blob(spec.gh_repo, spec.gh_onnx_sha))
            if not json_path.exists():
                json_path.write_bytes(_github_blob(spec.gh_repo, spec.gh_json_sha))
    except (urllib.error.URLError, OSError, RuntimeError) as exc:
        raise VoiceDownloadError(_human_error(spec, exc)) from exc

    return onnx_path, json_path


def print_voices() -> None:
    """Imprime o catálogo de vozes."""
    for name, spec in VOICES.items():
        flag = " (padrão)" if name == DEFAULT_VOICE else ""
        print(f"  {name:<10} [{spec.language}]{flag} — {spec.description}")
