"""
Session — estado de sesión concreto y nativo del runtime.

Satisface RuntimeSessionProtocol y es el default para que el runtime sea
ejecutable por sí solo. NO incluye presentación (display_messages): eso es
proyección del consumidor vía EventBus (G2/D4). La persistencia es responsabilidad
del runtime vía StorageProtocol, no de la sesión.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ...contracts.events import Usage


class BackgroundTaskRef(BaseModel):
    """Referencia que el padre mantiene de un subagente background."""

    task_id: str
    description: str = ""
    status: str = "pending"


class SessionMetadata(BaseModel):
    subagent_depth: int = 0
    background_tasks: list[BackgroundTaskRef] = Field(default_factory=list)


class Session(BaseModel):
    #: Token **opaco**, atribuido por quien abre la sesión (integrador o `SessionRepo`).
    #: **Sin default a propósito (C9/`ID-1`)**: el autogen `sess_<hex>` que vivía aquí
    #: era la mímica que `SEAMS §S20` marca `existe-mímica`. Un runtime que inventa la
    #: identidad impide al integrador imponer la suya sin pelear con el default.
    session_id: str
    # `list[Any]` y no `list[dict[str, Any]]` A PROPÓSITO: en un `BaseModel` la anotación
    # no es documentación, es el validador. Estrecharla a `dict` hace que pydantic RECHACE
    # en construcción lo que antes aceptaba, y que copie los dicts en vez de guardarlos por
    # identidad — un cambio de conducta que ningún test pedía y que la suite verde no vería
    # porque nadie construye así dentro del repo. El estrechamiento es una decisión de
    # producto aparte, con su propia prueba; no un efecto lateral de callar a `mypy`.
    messages: list[Any] = Field(default_factory=list)
    turn_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)

    @property
    def id(self) -> str:
        """Lo único que el runtime lee de una sesión (`SEAMS §S20`, id opaco)."""
        return self.session_id

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


__all__ = ["BackgroundTaskRef", "Session", "SessionMetadata", "Usage"]
