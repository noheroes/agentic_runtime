from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

SLEEP_TOOL_NAME = "Sleep"


class SleepTool:
    name = SLEEP_TOOL_NAME
    # Homologada contra `SLEEP_TOOL_PROMPT` (`SleepTool/prompt.ts:7-17`) — `GAP-PROMPT-1`.
    # La línea PORTANTE es «prefer this over Bash(sleep ...)»: sin ella el modelo gasta el
    # slot de shell en una espera. OMITIDAS las de `<tick>` y el coste de caché por wake-up,
    # que describen el bucle del integrador de A y no el de B.
    description = """Wait for a specified duration, in seconds (max 60).

Use this when you are waiting for something and have nothing else to do.

Prefer this over running `sleep` through the bash tool — it doesn't hold a shell process.
Do not use it to poll: if there is a check you can run, run the check instead."""
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
