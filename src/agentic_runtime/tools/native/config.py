from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

CONFIG_TOOL_NAME = "Config"
_CONFIG_KEY = "config"


class ConfigTool:
    name = CONFIG_TOOL_NAME
    description = (
        "Read or write runtime configuration settings stored in the session. "
        "Omit value to read the current value."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "setting": {
                "type": "string",
                "description": "The setting key (e.g., 'model', 'theme').",
            },
            "value": {
                "description": "The new value. Omit to get the current value.",
            },
        },
        "required": ["setting"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        setting = input.get("setting", "")
        if not setting:
            return ToolResult.error(self.name, "setting is required.")

        config: dict[str, Any] = ctx.app_state.native.setdefault(_CONFIG_KEY, {})

        if "value" not in input:
            # Get
            current = config.get(setting)
            return ToolResult(
                tool_name=self.name,
                output=json.dumps({
                    "operation": "get",
                    "setting": setting,
                    "value": current,
                }),
            )

        # Set
        value = input["value"]
        previous = config.get(setting)

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native.setdefault(_CONFIG_KEY, {})[setting] = value
            return c

        result = ToolResult(
            tool_name=self.name,
            output=json.dumps({
                "operation": "set",
                "setting": setting,
                "previous_value": previous,
                "new_value": value,
            }),
        )
        result.context_modifier = modifier  # type: ignore[attr-defined]
        return result
