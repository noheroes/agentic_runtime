from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Awaitable, Callable

from ...tools.protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

logger = logging.getLogger(__name__)

# El transporte real lo inyecta quien embebe el runtime: dado (tool_name, input)
# devuelve el texto de salida del server MCP. El shell no implementa transporte.
McpCall = Callable[[str, dict], Awaitable[str]]


class McpTool:
    """Adapter de una tool MCP a `ToolProtocol` — tolerante con campos opcionales.

    Robustez ante terceros: `annotations` es del estándar MCP pero opcional; cada
    hint ausente degrada a un default seguro (espejo de `?? false` del canónico).
    Default conservador para tools de terceros no anotadas: requiere permiso y no
    es safe_for_background hasta que un `readOnlyHint` lo afirme explícitamente.
    """

    category = ToolCategory.SYSTEM

    def __init__(
        self,
        *,
        name: str,
        description: str,
        input_schema: dict,
        call: McpCall,
        read_only: bool = False,
        timeout_seconds: float = 30.0,
        server_name: str = "",
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self._call = call
        # Tools MCP de terceros son no confiables: requieren permiso siempre.
        self.requires_permission = True
        # Solo las read-only se consideran seguras en background (unattended).
        self.safe_for_background = read_only
        self.timeout_seconds = timeout_seconds
        self.server_name = server_name

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        from .client import McpToolError

        try:
            output = await self._call(self.name, input)  # una sola llamada al server
        except McpToolError as exc:
            # El server respondió isError=True: error de la tool, no del transporte.
            return ToolResult.error(self.name, str(exc))
        except Exception as exc:
            return ToolResult.error(self.name, f"mcp call failed: {exc}")
        return ToolResult(tool_name=self.name, output=output)


def build_mcp_tool(
    spec: dict,
    call: McpCall,
    *,
    timeout_seconds: float = 30.0,
    server_name: str = "",
) -> McpTool | None:
    """Construye un `McpTool` desde el spec crudo del server, tolerante.

    Solo `name` es obligatorio (identidad). Sin nombre → se omite con log
    (aislamiento por ítem). `description`/`inputSchema`/`annotations` degradan
    a defaults seguros si faltan o vienen malformados.
    """
    name = spec.get("name")
    if not name or not isinstance(name, str):
        logger.warning("mcp: tool sin 'name' válido en server %r — omitida", server_name)
        return None

    description = spec.get("description")
    if not isinstance(description, str):
        description = ""

    input_schema = spec.get("inputSchema")
    if not isinstance(input_schema, dict):
        input_schema = {}

    annotations = spec.get("annotations")
    read_only = False
    if isinstance(annotations, dict):
        read_only = annotations.get("readOnlyHint") is True

    return McpTool(
        name=name,
        description=description,
        input_schema=input_schema,
        call=call,
        read_only=read_only,
        timeout_seconds=timeout_seconds,
        server_name=server_name,
    )


__all__ = ["McpCall", "McpTool", "build_mcp_tool"]
