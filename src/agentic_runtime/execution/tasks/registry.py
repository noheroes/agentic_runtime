"""
TaskRegistry — protocolo y primitiva de conexión.

El exterior registra su implementación vía set_registry().
LocalAgentRuntime la obtiene vía get_registry() sin saber de dónde viene.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from .status import TaskStatus


@dataclass
class TaskRecord:
    task_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    # Eje "background" (= isBackgrounded del canónico): MUTABLE, relativo al observador.
    # Lo flipea el consumidor vía el registry. NO afecta el toolset (eso es por kind, B3).
    is_backgrounded: bool = False
    result: str | None = None
    session: Any = None
    error: str | None = None
    duration_ms: int = 0
    turn_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    events: list = field(default_factory=list)
    asyncio_task: Any = None


@runtime_checkable
class TaskRegistryProtocol(Protocol):
    def register(self, *, description: str) -> TaskRecord: ...
    def start(self, task_id: str, *, asyncio_task: asyncio.Task | None) -> None: ...
    def arm_watchdog(self, task_id: str, timeout_seconds: float) -> None: ...
    def get(self, task_id: str) -> TaskRecord | None: ...
    def set_backgrounded(self, task_id: str, value: bool) -> None: ...
    def push_event(self, task_id: str, event: dict) -> None: ...
    def kill(self, task_id: str) -> bool: ...
    def fail(self, task_id: str, error: str, *, duration_ms: int = 0) -> None: ...
    def complete(
        self,
        task_id: str,
        *,
        result: str,
        duration_ms: int = 0,
        turn_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None: ...


class InMemoryTaskRegistry:
    """Implementación concreta nativa de TaskRegistryProtocol, en-proceso.

    Default del runtime para ser ejecutable por sí solo. Un consumidor puede
    inyectar su propia implementación vía set_registry().
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._seq = 0

    def register(self, *, description: str) -> TaskRecord:
        self._seq += 1
        task_id = f"task_{self._seq}_{description[:16]}".replace(" ", "_")
        record = TaskRecord(task_id=task_id, description=description)
        self._tasks[task_id] = record
        return record

    def start(self, task_id: str, *, asyncio_task: asyncio.Task | None) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.status = TaskStatus.RUNNING
            rec.asyncio_task = asyncio_task

    def arm_watchdog(self, task_id: str, timeout_seconds: float) -> None:
        # En-proceso: el watchdog real lo arma el consumidor si lo necesita.
        # Aquí solo se registra el intento; mantener simple y sin efectos colaterales.
        pass

    def get(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def set_backgrounded(self, task_id: str, value: bool) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.is_backgrounded = value

    def push_event(self, task_id: str, event: dict) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.events.append(event)

    def kill(self, task_id: str) -> bool:
        rec = self._tasks.get(task_id)
        if rec is None:
            return False
        if rec.asyncio_task is not None and not rec.asyncio_task.done():
            rec.asyncio_task.cancel()
        rec.status = TaskStatus.KILLED
        return True

    def fail(self, task_id: str, error: str, *, duration_ms: int = 0) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.status = TaskStatus.FAILED
            rec.error = error
            rec.duration_ms = duration_ms

    def complete(
        self,
        task_id: str,
        *,
        result: str,
        duration_ms: int = 0,
        turn_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.status = TaskStatus.COMPLETED
            rec.result = result
            rec.duration_ms = duration_ms
            rec.turn_count = turn_count
            rec.input_tokens = input_tokens
            rec.output_tokens = output_tokens


_registry: TaskRegistryProtocol | None = None


def set_registry(impl: TaskRegistryProtocol) -> None:
    global _registry
    _registry = impl


def get_registry() -> TaskRegistryProtocol:
    if _registry is None:
        raise RuntimeError(
            "TaskRegistry not initialized. Call set_registry() before using the runtime."
        )
    return _registry
