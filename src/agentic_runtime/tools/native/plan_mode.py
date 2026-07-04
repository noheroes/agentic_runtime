from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ENTER_PLAN_MODE_TOOL_NAME = "EnterPlanMode"
EXIT_PLAN_MODE_TOOL_NAME = "ExitPlanMode"

_PLAN_MODE_KEY = "plan_mode"
# Plan aprobado persistido en `app_state.native` (espejo de `getPlan()` keyed por sesión;
# `app_state` es per-sesión). Lo consume `PlanModeProvider` en ejecución.
_PLAN_KEY = "plan"
# One-shot: marca que se acaba de salir de plan mode → el provider emite el recordatorio
# `plan_mode_exit` una vez (espejo de `needsPlanModeExitAttachment`).
_PLAN_EXIT_PENDING_KEY = "plan_mode_exit_pending"


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
            return c

        result = ToolResult(
            tool_name=self.name,
            output=(
                "Entered plan mode. Explore the codebase and design an implementation approach. "
                "DO NOT write or edit any files yet. "
                "When ready, use ExitPlanMode to present your plan for approval."
            ),
        )
        result.context_modifier = modifier  # type: ignore[attr-defined]
        return result


class ExitPlanModeTool:
    name = EXIT_PLAN_MODE_TOOL_NAME
    description = "Exit plan mode and present the implementation plan for approval."
    input_schema = {
        "type": "object",
        "properties": {
            "plan": {
                "type": "string",
                "description": "The implementation plan to present for approval.",
            }
        },
        "required": ["plan"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        plan = input.get("plan", "")
        if not plan:
            return ToolResult.error(self.name, "plan is required.")

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native.pop(_PLAN_MODE_KEY, None)
            # Persiste el plan aprobado (espejo de `getPlan()`) para que sea orientación
            # durable en ejecución, no un `tool_result` transitorio que el modelo pierde.
            c.app_state.native[_PLAN_KEY] = plan
            c.app_state.native[_PLAN_EXIT_PENDING_KEY] = True
            return c

        result = ToolResult(
            tool_name=self.name,
            output=f"Plan submitted for approval:\n\n{plan}",
        )
        result.context_modifier = modifier  # type: ignore[attr-defined]
        # Presentar el plan CIERRA el turno: el agente se detiene a esperar la aprobación del
        # usuario en vez de seguir generando (sin esto el modelo narra el plan como aprobado y
        # anuncia implementación). Espejo del canónico `requiresUserInteraction()->true`, que
        # detiene el turno en el gate de aprobación; mismo primitivo que `AskUserQuestion`.
        result.ends_turn = True  # type: ignore[attr-defined]
        return result
