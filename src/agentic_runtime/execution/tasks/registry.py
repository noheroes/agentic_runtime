from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from .status import TaskStatus


@dataclass
class TaskRecord:
    task_id: str
    description: str
    owner_session_id: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    is_backgrounded: bool = False
    result: str | None = None
    session: Any = None
    error: str | None = None
    duration_ms: int = 0
    turn_count: int = 0
    end_reason: str | None = None
    end_detail: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    asyncio_task: Any = None


@runtime_checkable
class TaskRegistryProtocol(Protocol):
    def register(self, *, description: str, session_id: str | None = None) -> TaskRecord: ...
    def start(self, task_id: str, *, asyncio_task: asyncio.Task[Any] | None) -> None: ...
    def arm_watchdog(self, task_id: str, timeout_seconds: float) -> None: ...
    def get(self, task_id: str) -> TaskRecord | None: ...
    def list_all(self) -> list[TaskRecord]: ...
    def list_for(self, session_id: str | None) -> list[TaskRecord]: ...
    def set_backgrounded(self, task_id: str, value: bool) -> None: ...
    def push_event(self, task_id: str, event: dict[str, Any]) -> None: ...
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
        end_reason: str | None = None,
        end_detail: str | None = None,
    ) -> None: ...


class InMemoryTaskRegistry:

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._seq = 0

    def register(self, *, description: str, session_id: str | None = None) -> TaskRecord:
        self._seq += 1
        task_id = f"task_{self._seq}_{description[:16]}".replace(" ", "_")
        record = TaskRecord(
            task_id=task_id, description=description, owner_session_id=session_id
        )
        self._tasks[task_id] = record
        return record

    def start(self, task_id: str, *, asyncio_task: asyncio.Task[Any] | None) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.status = TaskStatus.RUNNING
            rec.asyncio_task = asyncio_task

    def arm_watchdog(self, task_id: str, timeout_seconds: float) -> None:
        pass

    def get(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def list_all(self) -> list[TaskRecord]:
        return list(self._tasks.values())

    def list_for(self, session_id: str | None) -> list[TaskRecord]:
        return [r for r in self._tasks.values() if r.owner_session_id == session_id]

    def set_backgrounded(self, task_id: str, value: bool) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.is_backgrounded = value

    def push_event(self, task_id: str, event: dict[str, Any]) -> None:
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
        end_reason: str | None = None,
        end_detail: str | None = None,
    ) -> None:
        rec = self._tasks.get(task_id)
        if rec is not None:
            rec.status = TaskStatus.COMPLETED
            rec.result = result
            rec.duration_ms = duration_ms
            rec.turn_count = turn_count
            rec.input_tokens = input_tokens
            rec.output_tokens = output_tokens
            rec.end_reason = end_reason
            rec.end_detail = end_detail


__all__ = ["InMemoryTaskRegistry", "TaskRecord", "TaskRegistryProtocol"]
