from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ...tools.protocol import ToolCategory, ToolResult
from .state import McpState

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

LIST_MCP_RESOURCES_TOOL_NAME = "ListMcpResources"
READ_MCP_RESOURCE_TOOL_NAME = "ReadMcpResource"


class ListMcpResourcesTool:
    """Lista los resources MCP descubiertos (de todos los servers conectados).

    Tool del provider (no nativa, no MCP-named): accede al `McpState`, no a un loader
    global. Read-only → no requiere permiso y es safe_for_background.
    """

    name = LIST_MCP_RESOURCES_TOOL_NAME
    description = "List available MCP resources across connected servers."
    input_schema = {
        "type": "object",
        "properties": {
            "server": {"type": "string", "description": "Optional server name to filter by."},
        },
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 15.0

    def __init__(self, state: McpState) -> None:
        self._state = state

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        server = input.get("server")
        resources = self._state.all_resources()
        if server:
            resources = [r for r in resources if r.get("server") == server]
        return ToolResult(tool_name=self.name, output=json.dumps({"resources": resources}))


class ReadMcpResourceTool:
    """Lee un resource MCP por `uri`, enrutando al client del server dueño.

    Resuelve el server desde el estado (o el `server` dado) — sin loader global.
    """

    name = READ_MCP_RESOURCE_TOOL_NAME
    description = "Read the contents of an MCP resource by uri."
    input_schema = {
        "type": "object",
        "properties": {
            "uri": {"type": "string", "description": "Resource uri to read."},
            "server": {"type": "string", "description": "Optional server name owning the resource."},
        },
        "required": ["uri"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 30.0

    def __init__(self, state: McpState) -> None:
        self._state = state

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        uri = input.get("uri", "")
        server = input.get("server") or self._state.find_resource_server(uri)
        if not server:
            return ToolResult.error(self.name, f"resource {uri!r} no pertenece a ningún server conocido")
        client = self._state.get_client(server)
        if client is None:
            return ToolResult.error(self.name, f"server {server!r} no está conectado")
        try:
            contents = await client.read_resource(uri)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, f"read_resource falló: {exc}")
        return ToolResult(tool_name=self.name, output=contents)


__all__ = [
    "LIST_MCP_RESOURCES_TOOL_NAME",
    "READ_MCP_RESOURCE_TOOL_NAME",
    "ListMcpResourcesTool",
    "ReadMcpResourceTool",
]
