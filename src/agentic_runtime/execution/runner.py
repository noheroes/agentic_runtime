"""
SubagentRunner — primitiva de ejecución de subagentes.

Punto de conexión entre AgentTool y el runtime que ejecuta el loop.
El runtime registra su implementación vía set_runner() al arrancar.
AgentTool llama get_runner() sin saber qué implementación está detrás.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .fork import ForkContext


@runtime_checkable
class SubagentRunnerProtocol(Protocol):
    async def run(self, fork_ctx: "ForkContext", *, background: bool) -> str | None:
        """
        Ejecuta un subagente.

        foreground (background=False): bloquea hasta que termina, retorna el resultado.
        background (background=True): lanza asyncio.Task, retorna task_id inmediatamente.
        """
        ...


_runner: SubagentRunnerProtocol | None = None


def set_runner(impl: SubagentRunnerProtocol) -> None:
    global _runner
    _runner = impl


def get_runner() -> SubagentRunnerProtocol:
    if _runner is None:
        raise RuntimeError(
            "SubagentRunner not initialized. Call set_runner() before using AgentTool."
        )
    return _runner
