from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Any

from .config import McpServerConfig

if TYPE_CHECKING:
    import httpx

    from .auth import AuthDeps

logger = logging.getLogger(__name__)


class McpToolError(Exception):
    """Una tool MCP devolvió `isError=True`. Lleva el texto del server.

    Se propaga como excepción para que `McpTool.execute` la envuelva en un
    `ToolResult.error` SIN hacer una segunda llamada al server.
    """


def _http_client_factory(ssl_verify: bool) -> Callable[..., httpx.AsyncClient]:
    """Factory de cliente httpx para los transportes http/sse, respetando `ssl_verify`.

    Cumple `McpHttpClientFactory(headers, timeout, auth) -> httpx.AsyncClient`. Con
    `ssl_verify=False` desactiva la validación de certificados TLS (útil contra
    servidores corporativos con CA propia o entornos de prueba). Borde de seguridad:
    es una decisión explícita del que registra el server, nunca un default silencioso.
    """
    import httpx

    def factory(
        headers: Any = None, timeout: Any = None, auth: Any = None
    ) -> httpx.AsyncClient:
        kwargs: dict[str, Any] = {"follow_redirects": True, "verify": ssl_verify}
        if headers is not None:
            kwargs["headers"] = headers
        if timeout is not None:
            kwargs["timeout"] = timeout
        if auth is not None:
            kwargs["auth"] = auth
        return httpx.AsyncClient(**kwargs)

    return factory


def _read(obj: Any, *names: str, default: Any = None) -> Any:
    """Lee el PRIMER atributo presente de `names` — tolerante a la grafía del SDK.

    Los modelos de `mcp.types` son pydantic con `alias_generator=to_camel`: el campo se
    llama `input_schema` y su alias de protocolo `inputSchema`. Cuál de los dos es el
    ATRIBUTO de Python ha cambiado entre versiones del SDK (1.x expone `inputSchema`;
    2.x expone `input_schema`), y el runtime declara `mcp>=1.26.0`, o sea que ambas caen
    dentro de lo soportado. Leer una sola grafía no rompe ruidosamente: degrada EN
    SILENCIO —schema vacío, `isError` que se pierde— y por eso se lee por lista.
    Detectado por el consumidor real (`D-15`): la suite del runtime corre con 1.27.2 y
    estaba verde y ciega.
    """
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return value
    return default


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

    def __init__(self, config: McpServerConfig, *, auth_deps: AuthDeps | None = None) -> None:
        self._config = config
        self._auth_deps = auth_deps
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

        transport = self._config.resolved_transport()
        stack = AsyncExitStack()
        try:
            if transport == "stdio":
                if self._config.command is None:
                    raise ValueError(f"MCP server {self._config.name!r}: transport stdio requiere 'command'")
                params = StdioServerParameters(
                    command=self._config.command,
                    args=list(self._config.args),
                    env=dict(self._config.env) or None,
                )
                read, write = await stack.enter_async_context(stdio_client(params))
            else:
                import httpx

                from .auth import build_auth

                url = self._config.url or ""
                artifacts = build_auth(self._config, server_url=url, deps=self._auth_deps)
                headers = {**dict(self._config.headers), **artifacts.headers} or None
                httpx_auth = artifacts.httpx_auth
                if transport == "sse":
                    from mcp.client.sse import sse_client

                    streams = await stack.enter_async_context(
                        sse_client(
                            url, headers=headers,
                            httpx_client_factory=_http_client_factory(self._config.ssl_verify),
                            auth=httpx_auth,
                        )
                    )
                else:  # http (Streamable HTTP) — API nueva: recibe un httpx.AsyncClient
                    from mcp.client.streamable_http import streamable_http_client

                    # El timeout DEBE venir del config (espejo del default operativo del
                    # provider, 30s): sin pasarlo, httpx aplica su default de 5s y toda tool
                    # que tarde más da ReadTimeout. La rama SSE ya lo respeta vía el factory.
                    http_client = await stack.enter_async_context(
                        httpx.AsyncClient(
                            headers=headers, auth=httpx_auth,
                            verify=self._config.ssl_verify, follow_redirects=True,
                            timeout=self._config.timeout_seconds or 30.0,
                        )
                    )
                    streams = await stack.enter_async_context(
                        streamable_http_client(url, http_client=http_client)
                    )
                read, write = streams[0], streams[1]

            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
        except BaseException:
            await stack.aclose()
            raise

        self._stack = stack
        self._session = session

    async def list_tools(self) -> list[dict[str, Any]]:
        """Specs crudos de tools (name/description/inputSchema/annotations) para `build_mcp_tool`."""
        result = await self._session.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": _read(t, "inputSchema", "input_schema", default={}) or {},
                "annotations": _annotations_dict(t),
                # `_meta` del server: es de donde `build_mcp_tool` saca el `searchHint`
                # (`services/mcp/client.ts:1778-1784`), la única pista curada de una tool
                # MCP y +4 en el ranking de ToolSearch. El adapter llevaba leyéndolo desde
                # que existe, pero NADIE se lo ponía en el spec: el cable estaba muerto en
                # producción y ningún test lo veía porque todos fabrican el spec a mano.
                "_meta": _read(t, "meta", "_meta", default={}) or {},
            }
            for t in result.tools
        ]

    async def list_resources(self) -> list[dict[str, Any]]:
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
                "mimeType": _read(r, "mimeType", "mime_type", default="") or "",
            }
            for r in result.resources
        ]

    async def call(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Implementa el contrato `McpCall`. `isError` → `McpToolError` (sin re-llamar)."""
        result = await self._session.call_tool(tool_name, tool_input)
        text = _text_from_content(getattr(result, "content", None))
        # Leer una sola grafía aquí es peor que un fallo: con la que no existe, un error
        # del server se le entrega al modelo como SALIDA CORRECTA («Error executing
        # tool …» en el hueco del resultado), que es exactamente lo que `isError` existe
        # para impedir. Medido contra un server real bajo SDK 2.x.
        if _read(result, "isError", "is_error", default=False):
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


def _annotations_dict(tool: Any) -> dict[str, Any]:
    ann = getattr(tool, "annotations", None)
    if ann is None:
        return {}
    if isinstance(ann, dict):
        return ann
    # Pydantic model (mcp.types.ToolAnnotations) → dict tolerante
    dump = getattr(ann, "model_dump", None)
    return dump() if callable(dump) else {}


__all__ = ["McpClient", "McpToolError"]
