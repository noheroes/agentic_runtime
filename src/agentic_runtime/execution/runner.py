"""
`S18` · `SubagentRunnerProtocol` — la primitiva de ejecución de subagentes.

**`C8` retira el singleton global.** Hasta aquí esta costura era `existe-sin-poblar`
(`FIND-EXEC1`): el protocolo declaraba `set_runner`/`get_runner`, `AgentTool` llamaba
`get_runner()`, y `factory.create_runtime` —leído 1→EOF— **no llamaba `set_runner` jamás**,
de modo que en producción **todo** spawn de subagente reventaba. `set_runner` sólo se
invocaba desde los tests, que así probaban una costura que la producción no tenía
(`L09`: cablear ≠ existir).

El patrón correcto es DI (`SEAMS §S18`, corregido en A2.5): el runner se **inyecta** al
`LocalAgentRuntime`, éste lo threadea al `ctx`, y `AgentTool` lee `ctx.runner`. Con
`ctx.runner is None` la tool devuelve un `is_error` limpio en vez de levantar: la costura
es load-bearing y su ausencia se ve, que es justo lo que la negativa del gate asevera.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .fork import ForkSnapshot


@dataclass(frozen=True)
class SubagentSpec:
    """Qué subagente se pide. Frozen: es una petición, no estado mutable.

    ⚠ **Diverge del `SubagentSpec` mínimo del walking skeleton A2.5, y la razón se
    declara** (`L10`): allí el spec no llevaba `parent_snapshot` porque A2.5 **no
    ejercitaba el fork** —el hijo nacía con prompt propio y nada más—. Aquí el fork es
    real: el snapshot del padre es lo que transporta profundidad de anidamiento, `scope`,
    permisos y pool heredados. Sin él, el hijo perdería el aislamiento del padre y la
    tool `Agent` no podría topar la recursión.

    `parent_session_id` es un token **opaco** que se hereda: el runtime lo transporta y
    nunca lo interpreta ni lo compone (`00-LEGEND §2.4`, `D-11`).
    """

    prompt: str
    description: str = ""
    subagent_type: str | None = None
    model_override: str | None = None
    parent_session_id: str | None = None
    parent_snapshot: ForkSnapshot | None = None
    inherit_messages: bool = False


@runtime_checkable
class SubagentRunnerProtocol(Protocol):
    async def run(self, spec: SubagentSpec, *, background: bool = False) -> str | None:
        """Ejecuta un subagente.

        foreground (`background=False`): espera a que termine y devuelve su resultado.
        background (`background=True`): devuelve el `task_id` en cuanto queda despachado.
        """
        ...


# El runner necesita un runtime al que despachar al hijo. Quién lo compone es del
# ensamblador, no del runner: por eso recibe una FÁBRICA y no un import directo.
ChildRuntimeFactory = Callable[[SubagentSpec], Any]


class LocalSubagentRunner:
    """Adaptador `SubagentSpec` → `RuntimeTask`, despachado al runtime del hijo.

    Es la implementación por defecto que hace al runtime ejecutable por sí solo. El
    `background=True` **no se finge**: se apoya en que `AgentRuntime.dispatch` ya es
    fire-and-forget (registra la task, lanza el `asyncio.Task` y devuelve el `task_id`
    inmediatamente). Lo que sigue **ausente** es `S22` `ForceAsyncPolicy` —la POLÍTICA de
    promover a async un subagente que se pidió síncrono—, y eso se declara, no se simula.
    """

    def __init__(self, *, build_child: ChildRuntimeFactory) -> None:
        self._build_child = build_child

    def _to_task(self, spec: SubagentSpec) -> Any:
        from ..contracts.runtime import RuntimeTask

        return RuntimeTask(
            prompt=spec.prompt,
            description=spec.description or spec.prompt[:80],
            subagent_type=spec.subagent_type,
            model_override=spec.model_override,
            fork_context=spec.inherit_messages,
            # Token opaco heredado del padre: el hijo escribe bajo la misma sesión.
            session_id=spec.parent_session_id,
        )

    async def run(self, spec: SubagentSpec, *, background: bool = False) -> str | None:
        runtime = self._build_child(spec)
        task_id: str = await runtime.dispatch(self._to_task(spec), spec.parent_snapshot)

        if background:
            # El padre sigue su turno; se entera al terminar el hijo por el canal `S21`,
            # que su loop drena al arrancar el siguiente run.
            return task_id

        # Foreground = el padre BLOQUEA en el hijo. `join` es el miembro de `S4` que esto
        # exige y que la façade no tenía: con sólo `dispatch`/`status`/`result` la única
        # forma de esperar era hurgar en el `asyncio.Task` del registry, es decir, romper
        # la costura por dentro. Se declara como enriquecimiento de `S4` (ver `SEAMS`).
        try:
            joined: str | None = await runtime.join(task_id)
            return joined
        except asyncio.CancelledError:
            return None


__all__ = [
    "ChildRuntimeFactory",
    "LocalSubagentRunner",
    "SubagentRunnerProtocol",
    "SubagentSpec",
]
