from __future__ import annotations

import asyncio
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Coroutine, Optional, TypeVar

T = TypeVar("T")


@dataclass
class ExecutionContext:
    """Identidad inmutable de una ejecución — aislada por cadena async vía ContextVar."""
    execution_id: str
    session_id: str
    agent_id: Optional[str] = None
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeState:
    """Estado global mutable del runtime — compartido entre todas las ejecuciones."""
    foreground_task_id: Optional[str] = None

    def set_foreground(self, task_id: str) -> None:
        self.foreground_task_id = task_id

    def clear_foreground(self) -> None:
        self.foreground_task_id = None


_ctx: ContextVar[Optional[ExecutionContext]] = ContextVar("_execution_ctx", default=None)


def set_execution_context(ctx: ExecutionContext) -> Token:
    return _ctx.set(ctx)


def get_execution_context() -> Optional[ExecutionContext]:
    return _ctx.get()


async def run_with_context(ctx: ExecutionContext, coro: Coroutine[Any, Any, T]) -> T:
    """
    Ejecuta una coroutine con un ExecutionContext específico.

    Crea un nuevo asyncio.Task que hereda una copia del ContextVar actual,
    luego sobreescribe _ctx con el contexto proporcionado — aislado del padre.
    """
    async def _wrapped() -> T:
        _ctx.set(ctx)
        return await coro

    return await asyncio.ensure_future(_wrapped())
