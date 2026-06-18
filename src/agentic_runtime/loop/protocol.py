from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext


@runtime_checkable
class LoopProtocol(Protocol):
    """Contrato mínimo de un loop agentico."""

    async def run(self, prompt: str, ctx: "ToolUseContext") -> None: ...


@runtime_checkable
class DrainableLoopProtocol(LoopProtocol, Protocol):
    """
    Extensión de LoopProtocol que permite al runtime inyectar hooks de turno.

    Proyectos que inyecten su propio loop deben implementar este protocolo
    para que el drenado del BackgroundNotificationChannel funcione automáticamente.
    Si no lo implementan, el drenado es responsabilidad del proyecto.
    """

    def register_turn_start_hook(self, hook: Callable[[], Coroutine[Any, Any, None]]) -> None: ...
    async def _run_turn_start_hooks(self) -> None: ...
