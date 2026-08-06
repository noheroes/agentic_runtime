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

# Claves de `_meta` de las que se lee el search hint, EN ORDEN de precedencia. El `_meta`
# de MCP es un espacio namespaced por vendor (`<vendor>/<campo>`) y el runtime es
# multi-modelo: no ancla ninguna marca en su default. La clave genérica va de serie; un
# integrador que hable el dialecto namespaced de un vendor concreto pasa la suya por
# `search_hint_meta_keys` — elegir dialecto es política del integrador (Filosofía B),
# igual que elegir modelo.
DEFAULT_SEARCH_HINT_META_KEYS: tuple[str, ...] = ("searchHint",)


class McpTool:
    """Adapter de una tool MCP a `ToolProtocol` — tolerante con campos opcionales.

    Robustez ante terceros: `annotations` es del estándar MCP pero opcional; cada
    hint ausente degrada a un default seguro (espejo de `?? false` del canónico).
    Default conservador para tools de terceros no anotadas: requiere permiso y no
    es safe_for_background hasta que un `readOnlyHint` lo afirme explícitamente.
    """

    category = ToolCategory.SYSTEM
    # Las tools MCP son diferidas (workflow-specific): no se anuncian hasta que
    # ToolSearch las descubre. Siguen ejecutables desde el pool (M3).
    deferred = True

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
        search_hint: str = "",
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema
        # `searchHint` del `_meta` del server (`services/mcp/client.ts:1778-1784`). Es la
        # única pista curada que tiene una tool MCP y puntúa +4 en ToolSearch, por encima
        # del +2 de la descripción — que para una tool diferida es la diferencia entre que
        # el modelo la encuentre por keyword o no la encuentre.
        self.search_hint = search_hint
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
    search_hint_meta_keys: tuple[str, ...] = DEFAULT_SEARCH_HINT_META_KEYS,
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

    # Search hint del `_meta` del server (homólogo de `client.ts:1778-1784`, cuya clave
    # namespaced la aporta el integrador vía `search_hint_meta_keys`). El COLAPSO DE
    # ESPACIOS no es cosmético y el canónico lo explica: `_meta` lo escribe un server de
    # terceros, y un salto de línea ahí inyecta líneas huérfanas en la lista de diferidas,
    # que se une por '\n'. Lo que no sea `str` degrada a vacío, como el resto del adapter.
    meta = spec.get("_meta")
    search_hint = ""
    if isinstance(meta, dict):
        for key in search_hint_meta_keys:
            raw_hint = meta.get(key)
            if isinstance(raw_hint, str) and raw_hint.strip():
                search_hint = " ".join(raw_hint.split())
                break

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
        search_hint=search_hint,
    )


__all__ = ["McpCall", "McpTool", "build_mcp_tool"]
