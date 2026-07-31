"""Entrada de audio — T1 invariante.

Sólo el **shape** del audio vive aquí: es lo que `RuntimeTask` transporta. Los
protocolos STT/TTS **no** son T1 invariante (hoy reciben el `ToolUseContext`
entero, fuga que `ID-6(b)` tipifica y `S30`/`S31` corrigen al exteriorizar la
battery de voz) y quedan **fuera del tramo 1**, declarados.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AudioInput:
    """Audio de entrada para STT.

    El runtime es agnóstico al códec y al origen; el motor STT del integrador
    interpreta `data` según `mime_type`/`sample_rate`."""

    data: bytes
    mime_type: str = "audio/wav"
    sample_rate: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = ["AudioInput"]
