from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from typing import Any

from .config import McpServerConfig

logger = logging.getLogger(__name__)


class McpToolError(Exception):
    """Una tool MCP devolvió `isError=True`. Lleva el texto del server.

    Se propaga como excepción para que `McpTool.execute` la envuelva en un
    `ToolResult.error` SIN hacer una segunda llamada al server.
    """


def _text_from_content(content: Any) -> str:
    """Extrae texto de los content blocks de un `CallToolResult`/`ReadResourceResult`.

    Tolerante: cada bloque puede ser `TextContent` (tiene `.text`) u otro tipo;
    lo que no expone texto se serializa con `str` para no perder información.
    """
    parts: list[str] = []
    for block in content or []:
        text = getattr(block, "text", None)
        parts.append(text if isinstance(text, str) else str(block))
    return "\n".join(parts)


class McpClient:
    """Cliente de UN server MCP — encapsula transporte + sesión + ciclo de vida.

    Patrón del canónico (`appState.mcp` con clients por server): el provider posee
    los clients; no hay globals. El transporte se elige por la identidad ya validada
    de `McpServerConfig` (`command` → stdio; `url` → streamable HTTP). `connect()` y
    `aclose()` deben correr en el mismo contexto async (el integrador controla
    startup/shutdown del provider) — el SDK usa anyio cancel scopes por tarea.
    """

    def __init__(self, config: McpServerConfig) -> None:
        self._config = config
        self._stack: AsyncExitStack | None = None
        self._session: Any = None

    @property
    def config(self) -> McpServerConfig:
        return self._config

    @property
    def connected(self) -> bool:
        return self._session is not None

    async def connect(self) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        stack = AsyncExitStack()
        try:
            if self._config.command:
                params = StdioServerParameters(
                    command=self._config.command,
                    args=list(self._config.args),
                    env=dict(self._config.env) or None,
                )
                read, write = await stack.enter_async_context(stdio_client(params))
            else:
                from mcp.client.streamable_http import streamablehttp_client

                # streamablehttp_client cede (read, write, get_session_id)
                transport = await stack.enter_async_context(
                    streamablehttp_client(self._config.url, headers=dict(self._config.headers) or None)
                )
                read, write = transport[0], transport[1]

            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
        except BaseException:
            await stack.aclose()
            raise

        self._stack = stack
        self._session = session

    async def list_tools(self) -> list[dict]:
        """Specs crudos de tools (name/description/inputSchema/annotations) para `build_mcp_tool`."""
        result = await self._session.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": getattr(t, "inputSchema", None) or {},
                "annotations": _annotations_dict(t),
            }
            for t in result.tools
        ]

    async def list_resources(self) -> list[dict]:
        try:
            result = await self._session.list_resources()
        except Exception as exc:  # noqa: BLE001 — server sin resources es válido
            logger.debug("mcp: server %r no expone resources: %s", self._config.name, exc)
            return []
        return [
            {
                "uri": str(r.uri),
                "name": r.name or "",
                "description": r.description or "",
                "mimeType": getattr(r, "mimeType", None) or "",
            }
            for r in result.resources
        ]

    async def call(self, tool_name: str, tool_input: dict) -> str:
        """Implementa el contrato `McpCall`. `isError` → `McpToolError` (sin re-llamar)."""
        result = await self._session.call_tool(tool_name, tool_input)
        text = _text_from_content(getattr(result, "content", None))
        if getattr(result, "isError", False):
            raise McpToolError(text or f"mcp tool {tool_name!r} returned isError")
        return text

    async def read_resource(self, uri: str) -> str:
        result = await self._session.read_resource(uri)
        return _text_from_content(getattr(result, "contents", None))

    async def aclose(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = None
        self._session = None


def _annotations_dict(tool: Any) -> dict:
    ann = getattr(tool, "annotations", None)
    if ann is None:
        return {}
    if isinstance(ann, dict):
        return ann
    # Pydantic model (mcp.types.ToolAnnotations) → dict tolerante
    dump = getattr(ann, "model_dump", None)
    return dump() if callable(dump) else {}


__all__ = ["McpClient", "McpToolError"]
