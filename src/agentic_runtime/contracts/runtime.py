"""
AgentRuntime — protocolo de la unidad coordinable. T1 invariante (`01·CTR-01`, `SEAMS §S4`).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .events import Event, EventHandler
from .identity import Scope
from .tasks import TaskStatus
from .voice import AudioInput


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
    # Identidad de ciclo de vida que **atribuye el integrador** (p.ej. el BFF). Son
    # tokens OPACOS: el runtime los transporta y NUNCA los interpreta, compone ni
    # inventa. Si no vienen, no hay identidad — y eso es un hecho que se propaga
    # honestamente, no un `user_<hex>` autogenerado.
    #
    # El autogen que vivía aquí (`user_<hex>`/`sess_<hex>`, `runtime.py:208-209`) era
    # mímica, no un default benigno: `MemoryProvider._scope` keya por `user_id`, que
    # era un uuid **nuevo por despacho**, luego el agente principal escribía su memoria
    # en un directorio distinto cada vez y no la recuperaba nunca (`H-1`).
    owner_id: str | None = None    # token opaco de propietario
    session_id: str | None = None  # token opaco de sesión
    # Scope de PERSISTENCIA de esta task (`D-11`, `DEUDA-A ID-3`). Es un cable
    # **distinto** de `owner_id`: `owner_id` es transporte por tarea, `scope` es la
    # frontera de aislamiento bajo la que escriben los repos, y **no se deriva uno del
    # otro** (derivarlo sería el runtime componiendo identidad, `00-LEGEND §2.4`).
    # `None` = usar el scope del host (`RuntimeConfig.scope`); si tampoco lo hay, no
    # hay scope — y los repos que necesiten clave fallan, no inventan una.
    scope: Scope | None = None
    # Entrada por voz: si se adjunta audio y el STT está activo, el runtime lo
    # transcribe y usa la transcripción como prompt (`prompt` queda de fallback).
    audio_prompt: AudioInput | None = None


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
        on_event: EventHandler | None = None,
    ) -> str:
        """Despacha la task. Si se pasa `on_event`, se suscribe al stream completo de
        eventos en vivo de esa task (Token/ToolCall/ToolResult/Done/Error) antes de
        arrancar el loop — sin perder eventos."""
        ...

    def stream(self, task: RuntimeTask) -> AsyncIterator[Event]:
        """Despacha la task y produce sus eventos en vivo, en orden, hasta el cierre.
        Azúcar sobre `dispatch(on_event=...)` para consumo tipo SSE."""
        ...

    def status(self, task_id: str) -> TaskStatus | None: ...

    async def cancel(self, task_id: str) -> bool: ...

    def result(self, task_id: str) -> str | None: ...


__all__ = ["AgentRuntime", "RuntimeTask"]
