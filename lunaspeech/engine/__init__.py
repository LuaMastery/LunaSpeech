"""Motores de síntese."""

from .base import AudioChunk, SynthesisResult, TTSEngine
from .piper_onnx import PiperOnnxEngine

__all__ = ["TTSEngine", "PiperOnnxEngine", "AudioChunk", "SynthesisResult"]
