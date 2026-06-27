from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ENTER_PLAN_MODE_TOOL_NAME = "EnterPlanMode"
EXIT_PLAN_MODE_TOOL_NAME = "ExitPlanMode"

_PLAN_MODE_KEY = "plan_mode"


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
            return c

        result = ToolResult(
            tool_name=self.name,
            output=f"Plan submitted for approval:\n\n{plan}",
        )
        result.context_modifier = modifier  # type: ignore[attr-defined]
        return result
