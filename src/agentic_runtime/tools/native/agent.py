from __future__ import annotations

from typing import TYPE_CHECKING

from ...execution.fork import ForkContext, ForkPolicy, ForkSnapshot
from ...execution.runner import get_runner
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
        model_override: str | None = input.get("model_override")
        inherit_messages: bool = bool(input.get("inherit_messages", False))

        if not prompt:
            return ToolResult.error(self.name, "prompt is required.")

        if ctx.subagent_depth >= _MAX_SUBAGENT_DEPTH:
            return ToolResult.error(
                self.name,
                f"Maximum subagent depth ({_MAX_SUBAGENT_DEPTH}) reached.",
            )

        snapshot = ForkSnapshot(
            session_id=ctx.session_id,
            user_id=ctx.user_id,
            subagent_depth=ctx.subagent_depth,
            messages=tuple(ctx.messages) if inherit_messages else (),
            permissions=ctx.permission_context,
            tool_pool=ctx.tool_pool,
        )

        policy = ForkPolicy(
            inherit_messages=inherit_messages,
            inherit_permissions=True,
            inherit_tool_pool=True,
            propagate_abort=True,
        )

        fork_ctx = ForkContext(
            prompt=prompt,
            policy=policy,
            parent_snapshot=snapshot,
            model_override=model_override,
        )

        try:
            result = await get_runner().run(fork_ctx, background=run_in_background)
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
