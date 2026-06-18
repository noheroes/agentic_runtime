"""Primitivas de I/O por voz (STT/TTS).

La voz es una capability de **borde de I/O**, no de tools: no aporta catálogo ni
entra al pool. El runtime solo define las primitivas y la plomería; el motor real
(STT/TTS) lo inyecta el integrador y se activa/desactiva por configuración.

- STT (entrada): transcribe audio → texto, que el runtime entrega como prompt del
  turno. El modelo es agnóstico al origen del prompt.
- TTS (salida): el runtime deriva la salida del asistente, ya saneada, a la
  primitiva de forma incremental (baja latencia). El runtime no reproduce audio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext


@dataclass
class AudioInput:
    """Audio de entrada para STT.

    El runtime es agnóstico al códec y al origen; el motor STT del integrador
    interpreta `data` según `mime_type`/`sample_rate`."""

    data: bytes
    mime_type: str = "audio/wav"
    sample_rate: int | None = None
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class SpeechToTextProtocol(Protocol):
    """Primitiva de entrada por voz: transcribe audio → texto.

    El integrador la implementa con su motor STT. El runtime entrega la
    transcripción como prompt del turno (espejo de `RuntimeTask.prompt`)."""

    async def transcribe(self, audio: AudioInput, ctx: "ToolUseContext") -> str: ...


@runtime_checkable
class TextToSpeechProtocol(Protocol):
    """Primitiva de salida por voz: sintetiza texto → voz.

    La salida se deriva al integrador de forma incremental: el runtime llama
    `speak` por cada fragmento del stream (baja latencia) y `flush` al cerrar el
    turno de habla para que el integrador vacíe/cierre. El texto llega ya saneado
    por `PathPresentation` (nunca se leen en voz alta rutas reales de infra)."""

    async def speak(self, text: str, ctx: "ToolUseContext") -> None: ...

    async def flush(self, ctx: "ToolUseContext") -> None: ...


__all__ = ["AudioInput", "SpeechToTextProtocol", "TextToSpeechProtocol"]
