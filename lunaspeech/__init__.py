"""🌙 LunaSpeech — Text-to-Speech leve, open source e em CPU.

Um sistema de síntese de fala que "fala qualquer texto", construído sobre a
arquitetura VITS exportada para ONNX (a mesma do Piper), executada de forma
*standalone* com ``onnxruntime`` + ``piper-phonemize`` (espeak-ng) — sem
PyTorch e sem GPU no caminho de inferência.

Uso rápido (CLI):

    python -m lunaspeech "Olá, mundo!"
    python -m lunaspeech "Texto mais longo." --voice faber --out saida.wav

Uso programático:

    from lunaspeech import LunaSpeech
    tts = LunaSpeech()                       # voz padrão pt-BR (faber)
    tts.synthesize("Olá, mundo!", "saida.wav")
"""

from .config import VoiceConfig, InferenceConfig
from .engine.piper_onnx import PiperOnnxEngine
from .engine.base import SynthesisResult, AudioChunk
from .core import LunaSpeech

__version__ = "0.2.1"

__all__ = [
    "LunaSpeech",
    "PiperOnnxEngine",
    "VoiceConfig",
    "InferenceConfig",
    "SynthesisResult",
    "AudioChunk",
    "__version__",
]
