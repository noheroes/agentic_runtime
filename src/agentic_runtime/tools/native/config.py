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

        # LECTURA, no `setdefault` (`FIND-CFG-1`): el `setdefault` corría antes de bifurcar,
        # así que un simple GET dejaba la clave creada en el estado de la sesión. A declara
        # el GET como puro —`isReadOnly(input) { return input.value === undefined }`
        # (`ConfigTool.ts:90-92`)— y su `call()` sólo llama a `getValue()` (`:136-144`).
        # Quien escribe es la rama SET, y lo hace por su `context_modifier`, que es el único
        # punto donde el runtime admite mutación de contexto desde una tool.
        config: dict[str, Any] = ctx.app_state.native.get(_CONFIG_KEY) or {}

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

        return ToolResult(
            tool_name=self.name,
            output=json.dumps({
                "operation": "set",
                "setting": setting,
                "previous_value": previous,
                "new_value": value,
            }),
            context_modifier=modifier,
        )
