"""`create_runtime` — el ENSAMBLADOR del stack (ciclo A2.5).

Es el análogo clean-room de `factory.create_runtime` del canónico (18·C1). Su razón de ser
en A2.5 es la costura CRÍTICA S18: en la mímica el runner de subagentes NUNCA se poblaba en el
factory (`set_runner` sólo en tests, 05·E24) ⇒ todo spawn lanzaba en producción. AQUÍ el factory
es el ÚNICO punto que construye el `LocalSubagentRunner` y lo INYECTA al runtime del padre; el
turno end-to-end lo prueba siguiendo el dato de punta a punta (L09: cableado, no existencia).

Composición (Filosofía B — el base compone costuras, no las hereda):
- `parent_caller` (S1) + `parent_tools` (S16, default = `[AgentTool()]`) → runtime del PADRE.
- `child_caller_factory` (S1 por subagente) + `child_tools` (S16) → cómo se compone cada HIJO.
- `notifier` (S21) compartido padre↔runner: el child publica, el integrador drena.
El runner recibe una FÁBRICA de runtime-hijo (`build_child`), no un import directo: mantiene al
runner agnóstico de la composición del hijo (el factory decide; el runner orquesta).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from skeleton.runner import LocalSubagentRunner
from skeleton.runtime import LocalAgentRuntime
from skeleton.seams import (
    ModelCallerProtocol,
    NotificationSink,
    SubagentSpec,
    ToolProtocol,
)
from skeleton.stubs import InMemoryNotificationSink, PassthroughInputProcessor
from skeleton.tools import AgentTool, ToolPool


def create_runtime(
    *,
    parent_caller: ModelCallerProtocol,
    child_caller_factory: Callable[[SubagentSpec], ModelCallerProtocol],
    model_id: str = "stub-model",
    parent_system_prompt: str | None = None,
    child_system_prompt: str | None = None,
    parent_tools: list[ToolProtocol] | None = None,
    child_tools: Callable[[], list[ToolProtocol]] | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    metadata: Mapping[str, str] | None = None,
    notifier: NotificationSink | None = None,
) -> tuple[LocalAgentRuntime, NotificationSink]:
    """Devuelve (runtime del padre ya cableado, notifier compartido)."""
    sink: NotificationSink = notifier if notifier is not None else InMemoryNotificationSink()

    def build_child(spec: SubagentSpec) -> LocalAgentRuntime:
        # El factory compone el HIJO: caller propio por subagente + su pool de tools.
        return LocalAgentRuntime(
            caller=child_caller_factory(spec),
            input_processor=PassthroughInputProcessor(),
            model_id=spec.model_override or model_id,
            system_prompt=child_system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
            tool_pool=ToolPool(child_tools() if child_tools is not None else []),
        )

    # ── S18 POBLADO (el fix del bug mímica): el runner se CONSTRUYE en el factory ──
    runner = LocalSubagentRunner(build_child=build_child, notifier=sink)

    parent_pool = ToolPool(parent_tools if parent_tools is not None else [AgentTool()])
    parent = LocalAgentRuntime(
        caller=parent_caller,
        input_processor=PassthroughInputProcessor(),
        model_id=model_id,
        system_prompt=parent_system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        metadata=metadata,
        tool_pool=parent_pool,
        runner=runner,  # ← el factory INYECTA el runner al padre (18·C1). SIN esto: no hay spawn.
        notifier=sink,  # ← S21 compartido
    )
    return parent, sink
