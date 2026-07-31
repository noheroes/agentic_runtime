from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine, Protocol, runtime_checkable

from .outcome import LoopOutcome

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext


@runtime_checkable
class LoopProtocol(Protocol):
    """Contrato mínimo de un loop agentico.

    `run` devuelve un `LoopOutcome` (`C4`/`02·A4`): quien compone el turno tiene que
    poder distinguir «cerró el modelo» de «se agotaron las vueltas», de «lo cortó
    `S11`», de «no había motor cableado». Devolver `None` obligaba a inferirlo del
    historial, que es justo lo que `L09` castiga.
    """

    async def run(self, prompt: str, ctx: "ToolUseContext") -> LoopOutcome: ...


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
