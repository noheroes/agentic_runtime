"""
ExecutionObserver — protocolo y primitiva de observabilidad.

El exterior registra su implementación vía set_observer().
LocalAgentRuntime emite eventos vía get_observer() sin saber quién observa.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .events import SubagentStarted, SubagentStopped


@runtime_checkable
class ExecutionObserverProtocol(Protocol):
    async def on_subagent_started(self, event: SubagentStarted) -> None: ...
    async def on_subagent_stopped(self, event: SubagentStopped) -> None: ...


class NoopObserver:
    async def on_subagent_started(self, event: SubagentStarted) -> None:
        pass

    async def on_subagent_stopped(self, event: SubagentStopped) -> None:
        pass


_observer: ExecutionObserverProtocol = NoopObserver()


def set_observer(impl: ExecutionObserverProtocol) -> None:
    global _observer
    _observer = impl


def get_observer() -> ExecutionObserverProtocol:
    return _observer
