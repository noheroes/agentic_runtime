"""
AgentContext — identidad del agente en la cadena async actual.

Usa contextvars para aislar ejecuciones concurrentes en el mismo proceso,
resolviendo el problema que surge cuando múltiples subagentes corren en
paralelo: cada cadena async mantiene su propio contexto sin interferencia.
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Generator


@dataclass
class AgentContext:
    agent_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:12]}")
    parent_session_id: str | None = None
    user_id: str | None = None


_current: ContextVar[AgentContext | None] = ContextVar("agent_context", default=None)


def get_agent_context() -> AgentContext | None:
    return _current.get()


def get_current_user_id() -> str | None:
    ctx = _current.get()
    return ctx.user_id if ctx is not None else None


@contextmanager
def run_with_context(context: AgentContext) -> Generator[AgentContext, None, None]:
    token = _current.set(context)
    try:
        yield context
    finally:
        _current.reset(token)
