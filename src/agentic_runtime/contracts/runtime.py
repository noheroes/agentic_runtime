"""
AgentRuntime — protocolo de la unidad coordinable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..events.protocol import Event, EventHandler
    from ..execution.tasks.status import TaskStatus


@dataclass
class RuntimeTask:
    """Descriptor de trabajo que se despacha a un AgentRuntime."""
    prompt: str
    description: str
    subagent_type: str | None = None
    model_override: str | None = None
    max_turns: int | None = None
    timeout_seconds: float | None = None
    fork_context: bool = False
    parent_execution_id: str = ""
    owner_id: str | None = None  # token opaco de identidad, lo setea el consumidor


@runtime_checkable
class AgentRuntime(Protocol):
    """
    Interfaz mínima de una unidad de ejecución agentica.

    LocalAgentRuntime la implementa en-proceso vía asyncio.
    RemoteAgentRuntime (futuro) la implementa via HTTP a un pod.
    """

    @property
    def runtime_id(self) -> str: ...

    async def dispatch(
        self,
        task: RuntimeTask,
        *,
        on_event: "EventHandler | None" = None,
    ) -> str:
        """Despacha la task. Si se pasa `on_event`, se suscribe al stream completo de
        eventos en vivo de esa task (Token/ToolCall/ToolResult/Done/Error) antes de
        arrancar el loop — sin perder eventos."""
        ...

    def stream(self, task: RuntimeTask) -> "AsyncIterator[Event]":
        """Despacha la task y produce sus eventos en vivo, en orden, hasta el cierre.
        Azúcar sobre `dispatch(on_event=...)` para consumo tipo SSE."""
        ...

    def status(self, task_id: str) -> TaskStatus | None: ...

    async def cancel(self, task_id: str) -> bool: ...

    def result(self, task_id: str) -> str | None: ...
