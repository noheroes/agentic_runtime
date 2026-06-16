"""
Session — estado de sesión concreto y nativo del runtime.

Satisface RuntimeSessionProtocol y es el default para que el runtime sea
ejecutable por sí solo. NO incluye presentación (display_messages): eso es
proyección del consumidor vía EventBus (G2/D4). La persistencia es responsabilidad
del runtime vía StorageProtocol, no de la sesión.
"""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class BackgroundTaskRef(BaseModel):
    """Referencia que el padre mantiene de un subagente background."""

    task_id: str
    description: str = ""
    status: str = "pending"


class SessionMetadata(BaseModel):
    subagent_depth: int = 0
    background_tasks: list[BackgroundTaskRef] = Field(default_factory=list)


def _new_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:12]}"


class Session(BaseModel):
    session_id: str = Field(default_factory=_new_session_id)
    messages: list = Field(default_factory=list)
    turn_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)

    # Vistas planas para satisfacer RuntimeSessionProtocol
    @property
    def subagent_depth(self) -> int:
        return self.metadata.subagent_depth

    @property
    def input_tokens(self) -> int:
        return self.usage.input_tokens

    @property
    def output_tokens(self) -> int:
        return self.usage.output_tokens


__all__ = ["Session", "SessionMetadata", "BackgroundTaskRef", "Usage"]
