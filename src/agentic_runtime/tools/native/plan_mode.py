from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult
# La capa plan-file (token + lectura vía storage inyectado) vive en un módulo hoja para que tanto
# esta tool como el `PlanModeProvider` la importen sin ciclo. Re-exportados aquí por compat.
from ...capabilities.plan.plan_file import (  # noqa: F401
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_FULL_SHOWN_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    get_plan,
    get_plan_file_path,
)

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ENTER_PLAN_MODE_TOOL_NAME = "EnterPlanMode"
EXIT_PLAN_MODE_TOOL_NAME = "ExitPlanMode"


class EnterPlanModeTool:
    name = ENTER_PLAN_MODE_TOOL_NAME
    description = (
        "Requests permission to enter plan mode for complex tasks requiring "
        "exploration and design before implementation."
    )
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        # El discriminador de subagente es `is_subagent`, no `agent_id` (que también se
        # asigna al contexto raíz como identidad). Mismo criterio que el resto del runtime
        # (resolver/agent_loop/runtime). Canónico: EnterPlanMode es root-only.
        if ctx.is_subagent:
            return ToolResult.error(
                self.name, "EnterPlanMode cannot be used inside a subagent."
            )

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native[_PLAN_MODE_KEY] = True
            # Reinicia la cadencia: la primera iteración del nuevo plan mode rinde el reminder full.
            c.app_state.native.pop(_PLAN_FULL_SHOWN_KEY, None)
            return c

        return ToolResult(
            tool_name=self.name,
            output=(
                "Entered plan mode. Explore the codebase and design an implementation approach. "
                "DO NOT write or edit any files yet. "
                "When ready, use ExitPlanMode to present your plan for approval."
            ),
            context_modifier=modifier,
        )


class ExitPlanModeTool:
    name = EXIT_PLAN_MODE_TOOL_NAME
    description = (
        "Exit plan mode and present your plan for approval. The plan is read from the plan "
        "file you wrote during plan mode — call this with no arguments once the plan file is ready."
    )
    # Sin arg `plan`: el plan se lee del plan-file (fuente de verdad que el modelo escribió durante
    # plan mode). Homólogo de `ExitPlanModeV2Tool` (inputSchema interno sin `plan`, plan leído de
    # disco vía `getPlan`). Schema vacío = el modelo lo llama sin argumentos.
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        plan = await get_plan(ctx)
        if not plan or not plan.strip():
            return ToolResult.error(
                self.name,
                f"No plan found at {get_plan_file_path(ctx)}. Write your plan to the plan file "
                "before calling ExitPlanMode.",
            )
        plan = plan.strip()

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native.pop(_PLAN_MODE_KEY, None)
            c.app_state.native.pop(_PLAN_FULL_SHOWN_KEY, None)
            # Cachea el plan leído del plan-file para el one-shot de salida del provider (sync),
            # que no puede releer storage (async). La fuente de verdad sigue siendo el plan-file.
            c.app_state.native[_PLAN_KEY] = plan
            c.app_state.native[_PLAN_EXIT_PENDING_KEY] = True
            return c

        # Presentar el plan CIERRA el turno: el agente se detiene a esperar la aprobación del
        # usuario en vez de seguir generando (sin esto el modelo narra el plan como aprobado y
        # anuncia implementación).
        #
        # ⚠ Esto **no** es espejo del canónico, y la nota anterior que lo llamaba «espejo de
        # `requiresUserInteraction()->true`» sobre-afirmaba: `requiresUserInteraction()` existe
        # en A (`AskUserQuestionTool.tsx:155`) pero NO cierra el turno — marca que la tool
        # necesita al usuario para que el gate de permisos la resuelva por
        # `checkPermissions → behavior:'ask' + updatedInput`, y el turno **continúa**. `endsTurn`
        # no existe en A. Es cable propio de B mientras esa capa de interacción (`GAP-02`/`K1`)
        # esté por encima de la línea de corte. Ver `ToolResult.ends_turn`.
        return ToolResult(
            tool_name=self.name,
            output=f"Plan submitted for approval:\n\n{plan}",
            context_modifier=modifier,
            ends_turn=True,
        )
