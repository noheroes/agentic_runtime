from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

SLEEP_TOOL_NAME = "Sleep"


class SleepTool:
    name = SLEEP_TOOL_NAME
    description = "Pause execution for a specified number of seconds."
    input_schema = {
        "type": "object",
        "properties": {
            "duration": {
                "type": "number",
                "description": "Number of seconds to sleep (max 60).",
            }
        },
        "required": ["duration"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 90.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        duration = float(input.get("duration", 0))
        duration = max(0.0, min(duration, 60.0))
        await asyncio.sleep(duration)
        return ToolResult(
            tool_name=self.name,
            output=f"Slept for {duration} seconds.",
        )
