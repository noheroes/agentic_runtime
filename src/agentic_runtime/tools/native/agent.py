from __future__ import annotations

from typing import TYPE_CHECKING

from ...execution.fork import ForkSnapshot
from ...execution.runner import SubagentSpec
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

AGENT_TOOL_NAME = "Agent"

_MAX_SUBAGENT_DEPTH = 5


class AgentTool:
    name = AGENT_TOOL_NAME
    description = (
        "Launch a subagent to handle a self-contained task. "
        "Use run_in_background=true for long tasks that should not block the current agent."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The task or question for the subagent.",
            },
            "description": {
                "type": "string",
                "description": "Short description of what the subagent will do.",
            },
            "run_in_background": {
                "type": "boolean",
                "description": (
                    "Set to true to run this agent in the background. "
                    "You will be notified when it completes."
                ),
                "default": False,
            },
            "subagent_type": {
                "type": "string",
                "description": "The type of specialized agent to use for this task.",
            },
            "model_override": {
                "type": "string",
                "description": "Optional model ID to use for the subagent.",
            },
            "inherit_messages": {
                "type": "boolean",
                "description": "Whether the subagent inherits the current conversation history.",
                "default": False,
            },
        },
        "required": ["prompt", "description"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 600.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        prompt = input.get("prompt", "")
        run_in_background: bool = bool(input.get("run_in_background", False))
        subagent_type: str | None = input.get("subagent_type")
        model_override: str | None = input.get("model_override")
        inherit_messages: bool = bool(input.get("inherit_messages", False))

        if not prompt:
            return ToolResult.error(self.name, "prompt is required.")

        if ctx.subagent_depth >= _MAX_SUBAGENT_DEPTH:
            return ToolResult.error(
                self.name,
                f"Maximum subagent depth ({_MAX_SUBAGENT_DEPTH}) reached.",
            )

        # `S18` por DI (`C8`): la costura llega en el `ctx`, puesta por el runtime que
        # la recibió del ensamblador. Con el singleton global esto era
        # `get_runner()`, que en producción **siempre** levantaba `RuntimeError` porque
        # `create_runtime` no llamaba a `set_runner` (`FIND-EXEC1`).
        runner = ctx.runner
        if runner is None:
            return ToolResult.error(
                self.name,
                "Subagent runner not wired: this runtime was assembled without `S18` "
                "(RuntimeConfig.subagent_runner_factory / LocalAgentRuntime(runner_factory=…)).",
            )

        snapshot = ForkSnapshot(
            session_id=ctx.session_id,
            scope=ctx.scope,
            subagent_depth=ctx.subagent_depth,
            messages=tuple(ctx.messages) if inherit_messages else (),
            permissions=ctx.permission_context,
            tool_pool=ctx.tool_pool,
            capabilities=ctx.app_state.capabilities,
        )

        spec = SubagentSpec(
            prompt=prompt,
            description=input.get("description", "") or prompt[:80],
            subagent_type=subagent_type,
            model_override=model_override,
            # Token OPACO heredado: el runtime lo transporta, no lo interpreta (`D-11`).
            parent_session_id=ctx.session_id,
            parent_snapshot=snapshot,
            inherit_messages=inherit_messages,
        )

        try:
            result = await runner.run(spec, background=run_in_background)
        except Exception as e:
            return ToolResult.error(self.name, f"Subagent failed: {e}")

        if run_in_background:
            task_id = result or "unknown"
            return ToolResult(
                tool_name=self.name,
                output=f"Subagent started in background. Task ID: {task_id}",
            )

        return ToolResult(
            tool_name=self.name,
            output=result or "(no output)",
        )
