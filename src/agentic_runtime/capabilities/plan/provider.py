"""`PlanModeProvider` — orientación durable del plan aprobado en ejecución.

Espejo del `plan_mode_exit` del canónico (`utils/attachments.ts:getPlanModeExitAttachment`
+ `utils/messages.ts` `case 'plan_mode_exit'`): al salir de plan mode se emite UNA vez un
recordatorio que referencia el plan persistido. Cierra el defecto observado en vivo: el plan
sólo llegaba como `tool_result` transitorio de `ExitPlanMode` y, al empezar la ejecución, el
modelo lo perdía e improvisaba.

No tiene tools ni catálogo: es contexto puro, como `MemoryProvider`. El plan persiste en
`app_state.native` (per-sesión, espejo de `getPlan()` keyed por `getSessionId()`); este
provider sólo lo rinde. La cadencia recurrente `full/sparse` del canónico vive MIENTRAS
`mode==='plan'` (guía de planning), no en ejecución; aquí sólo se homologa el one-shot de
salida, que es lo que faltaba.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ...tools.native.plan_mode import _PLAN_EXIT_PENDING_KEY, _PLAN_KEY, _PLAN_MODE_KEY

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ..contracts import CapabilitySummary
    from ...tools.protocol import ToolProtocol


def _render_active_reminder() -> str:
    """Orientación durable MIENTRAS `mode==='plan'` (espejo de `messages.ts:3407`).

    Sin esto, entrar a plan mode por el flag del integrador siembra el candado de escritura pero
    NO le dice al modelo que está en plan mode → el modelo ejecuta el enunciado en vez de planear.
    El runtime no expone la capa de plan-file del canónico, así que se pide presentar el plan vía
    `ExitPlanMode`. Lenguaje del canónico: la restricción SUPERA cualquier otra instrucción."""
    return (
        "Plan mode is active. The user does not want you to execute yet -- you MUST NOT make any "
        "edits, run any non-readonly tools (including changing configs or making commits), or "
        "otherwise make any changes to the system. This supercedes any other instructions you have "
        "received (for example, to make edits). Instead, explore with READ-ONLY tools "
        "(read_file/glob/grep), and use AskUserQuestion if you need to clarify intent. When your "
        "plan is ready, call ExitPlanMode to present it for approval."
    )


def _render_exit_reminder(plan: str) -> str:
    """Texto espejo de `plan_mode_exit` (`messages.ts:3852`), con el plan inline.

    El canónico apunta a un archivo (`planFilePath`); el runtime no expone esa capa de
    archivos, así que el plan aprobado se rinde directamente. Lenguaje neutro y positivo
    (qué hacer), sin presión artificial — el plan ya está aprobado."""
    plan = plan.strip()
    body = (
        "## Exited Plan Mode\n\n"
        "You have exited plan mode. You can now make edits, run tools, and take actions. "
        "The approved plan is below — follow it."
    )
    if plan:
        body += f"\n\n{plan}"
    return body


class PlanModeProvider:
    """`CapabilityProvider` del plan — sin tools ni catálogo (contexto puro)."""

    name = "plan"

    async def startup(self) -> None: ...

    async def shutdown(self) -> None: ...

    def catalog(self, context: "ToolUseContext") -> list["CapabilitySummary"]:
        return []

    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]:
        return []

    def active_context(self, context: "ToolUseContext") -> list[dict]:
        """Orientación de plan mode:

        - MIENTRAS `plan_mode` activo: rinde la guía in-plan en CADA iteración (durable, no
          one-shot) para que el modelo sepa que no debe ejecutar. Espejo de la cadencia del
          canónico mientras `mode==='plan'`.
        - AL SALIR (`ExitPlanMode` armó el one-shot): rinde el plan aprobado UNA vez.

        Excluyentes por estado: `ExitPlanMode` hace `pop(plan_mode)` y arma el exit_pending en el
        mismo turno, así que nunca coinciden."""
        native = context.app_state.native
        if native.get(_PLAN_MODE_KEY):
            return [{"role": "system", "content": _render_active_reminder()}]
        if not native.pop(_PLAN_EXIT_PENDING_KEY, False):
            return []
        plan = native.get(_PLAN_KEY, "")
        return [{"role": "system", "content": _render_exit_reminder(plan)}]

    def compact_context(self, context: "ToolUseContext") -> list[dict]:
        # Tras compactación el flag ya se consumió; el plan sigue en `app_state.native`
        # y el modelo puede re-leerlo, pero no se re-emite el one-shot.
        return []


__all__ = ["PlanModeProvider"]
