from __future__ import annotations

from typing import TYPE_CHECKING

from ..exec_env import LocalExecEnvironment
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class BashTool:
    name = "bash"
    description = "Execute a shell command and return stdout/stderr."
    input_schema = {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 30.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        command = input.get("command", "")
        exec_env = getattr(ctx, "exec_env", None) or LocalExecEnvironment()
        try:
            result = await exec_env.run_shell(command, timeout=self.timeout_seconds)
            return ToolResult(
                tool_name=self.name,
                output=result.output,
                is_error=result.returncode != 0,
            )
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
