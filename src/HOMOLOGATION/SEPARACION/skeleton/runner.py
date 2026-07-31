"""S18 · `LocalSubagentRunner` — realización base default del `SubagentRunnerProtocol`.

Ciclo **A2.5**: cablea la costura CRÍTICA de la espina de ejecución. Es el adaptador
`SubagentSpec → RuntimeTask` que SEAMS §S18 nombra: recibe la spec del `AgentTool`, construye
un runtime HIJO (vía la fábrica `build_child` que el factory le inyecta), corre su turno, y
publica una `Notification` (S21) al completar. Devuelve el texto final (camino síncrono).

Por qué un `build_child` inyectado y no un `import LocalAgentRuntime` directo: mantener el
runner AGNÓSTICO de cómo se compone el hijo (qué caller, qué tools, qué system). El factory
—el ensamblador— decide la composición del hijo; el runner sólo la ORQUESTA. Así el mismo
runner sirve al integrador degenerado (hijo = mismo stack) y al complejo (hijo con política
propia), sin que el runner conozca ninguno (Filosofía B).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from skeleton.contracts import ResultEvent, RuntimeTask
from skeleton.seams import (
    AgentRuntime,
    Notification,
    NotificationSink,
    SubagentSpec,
)

# El factory inyecta una fábrica de runtime-hijo: dada la spec, devuelve un `AgentRuntime`
# listo para correr el subagente (caller/tools/system ya compuestos por el ensamblador).
ChildRuntimeFactory = Callable[[SubagentSpec], AgentRuntime]


class LocalSubagentRunner:
    """Realiza `SubagentRunnerProtocol` (S18). Único productor real: `AgentTool.execute`."""

    def __init__(
        self,
        *,
        build_child: ChildRuntimeFactory,
        notifier: NotificationSink,
    ) -> None:
        self._build_child = build_child
        self._notifier = notifier

    async def run(self, spec: SubagentSpec, *, background: bool = False) -> str | None:
        if background:
            # Camino fire-and-forget: registrar y devolver el id opaco sin bloquear; el
            # resultado se recoge luego por S4 `result()`. NO ejercitado en A2.5 (requiere
            # S22 force-async + el daemon del integrador complejo) ⇒ se declara explícito,
            # no se finge un camino muerto que "parece" funcionar (L09-inverso).
            raise NotImplementedError(
                "background subagent → S22 force-async + daemon del integrador (Fase F)"
            )

        subagent_id = f"sub_{uuid.uuid4().hex[:12]}"  # id opaco del subagente
        child = self._build_child(spec)
        child_task = RuntimeTask(
            prompt=spec.prompt,
            subagent_type=spec.subagent_type,
            model_override=spec.model_override,
            session_id=spec.parent_session_id,  # scope heredado, id opaco (S20)
        )

        final_text = ""
        async for event in child.stream(child_task):
            if isinstance(event, ResultEvent):
                final_text = event.text

        # S21: el child PUBLICA su notificación; el integrador la drena/presenta al padre.
        # (En la mímica el `put` existía pero nadie drenaba — LAT-EXEC2; aquí el par completo.)
        self._notifier.put(
            Notification(
                task_id=subagent_id,
                status="completed",
                summary=f"subagente {spec.subagent_type or 'default'} completó",
                result=final_text,
            )
        )
        return final_text
