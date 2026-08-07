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
    # `searchHint` del canónico, grafía literal. Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "get or set runtime settings (theme, model)"
    # Homologada contra `ConfigTool/prompt.ts:50-76` (`generatePrompt()`), `GAP-PROMPT-1`.
    #
    # ⚠ OMITIDO Y DECLARADO — y esta omisión es la mitad del prompt canónico: A enumera
    # los ajustes configurables (`## Configurable settings list`, `:59-66`, generados
    # recorriendo `SUPPORTED_SETTINGS`, `:18-46`) y las opciones de modelo (`:79-93`).
    # **B no tiene registro de ajustes**: su `execute` acepta cualquier clave y la guarda
    # en `app_state.native["config"]`, así que no hay nada que enumerar. No se inventa
    # una lista: sería fabricar un dominio que la tool no valida. Queda registrado como
    # `FIND-CFG-2` (el modelo no puede saber qué claves existen ni qué valores admiten),
    # que es carencia ESTRUCTURAL y no se paga con una descripción.
    # Los ejemplos de A (`:69-75`) se conservan sólo en los dos casos genéricos; los que
    # citan ajustes concretos de Claude Code (`editorMode`, `permissions.defaultMode`)
    # se retiran porque en B nombrarían claves inexistentes.
    description = """Get or set runtime configuration settings.

View or change settings. Use when the user requests configuration changes, asks about current \
settings, or when adjusting a setting would benefit them.

## Usage
- **Get current value:** Omit the "value" parameter
- **Set new value:** Include the "value" parameter

## Examples
- Get theme: { "setting": "theme" }
- Set dark theme: { "setting": "theme", "value": "dark" }
"""
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
