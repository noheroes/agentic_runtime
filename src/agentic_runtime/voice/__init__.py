"""I/O por voz: primitivas STT/TTS de borde, conectadas por el integrador."""
from __future__ import annotations

from .protocol import AudioInput, SpeechToTextProtocol, TextToSpeechProtocol

__all__ = ["AudioInput", "SpeechToTextProtocol", "TextToSpeechProtocol"]
