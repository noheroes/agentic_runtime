from __future__ import annotations

import asyncio
import contextlib
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


#: Read timeout de los streams SSE, en segundos. Es el default del propio SDK
#: (`sse_read_timeout=300` en `sse_client`, que es quien aún lo expone) y NO
#: se puede confundir con el timeout de una petición: el canal GET de streamable-HTTP es
#: de larga duración y con el timeout de request se corta cada pocos segundos.
SSE_READ_TIMEOUT_SECONDS = 300.0


def _sdk_httpx() -> Any:
    """El módulo httpx que usa ESTE SDK: `httpx2` en `mcp` 2.x, `httpx` en 1.26/1.27.

    No es un detalle de empaquetado. En `mcp` 2.0 el transporte streamable-HTTP abre el
    canal GET con `client.sse(...)` (`streamable_http.py:213,256,504`), un método que
    sólo existe en `httpx2`. Pasarle un `httpx.AsyncClient` normal conecta y deja pasar
    las tool calls (que son POST) pero revienta el canal GET con
    `AttributeError: 'AsyncClient' object has no attribute 'sse'` **dentro del task
    group**: el server no puede volver a hablar —notificaciones, `resources/updated`,
    progreso— y desde fuera parece que todo va bien. Medido contra el server real.

    Por eso el flavor NO se elige por lo que haya instalado, sino leyéndolo del propio
    SDK: `mcp.shared._httpx_utils` importa exactamente uno de los dos, y ése es el que
    sus transportes van a recibir.
    """
    try:
        from mcp.shared import _httpx_utils
    except ImportError:  # pragma: no cover — SDK sin ese módulo interno
        import httpx

        return httpx
    module = getattr(_httpx_utils, "httpx2", None) or getattr(_httpx_utils, "httpx", None)
    if module is None:  # pragma: no cover — reorganización futura del SDK
        import httpx

        return httpx
    return module


def _http_client_factory(ssl_verify: bool) -> Callable[..., httpx.AsyncClient]:
    """Factory de cliente httpx para los transportes http/sse, respetando `ssl_verify`.

    Cumple `McpHttpClientFactory(headers, timeout, auth) -> httpx.AsyncClient`. Con
    `ssl_verify=False` desactiva la validación de certificados TLS (útil contra
    servidores corporativos con CA propia o entornos de prueba). Borde de seguridad:
    es una decisión explícita del que registra el server, nunca un default silencioso.

    El `verify` NO se pasa crudo: va por `tls.httpx_verify`, que es donde entra la CA
    extra del proceso (`AGENTIC_EXTRA_CA_CERTS`, homóloga de `NODE_EXTRA_CA_CERTS`). En A
    el transporte MCP no configura TLS porque Node ya aplicó la CA extra a todo el
    proceso; en B hay que llevarla al cliente, y las DOS ramas (sse aquí, http en
    `connect`) tienen que pasar por el mismo punto o la que se olvide queda con el
    almacén por defecto y falla sólo contra el server con CA propia.
    """
    from ...tls import httpx_verify

    httpx_impl = _sdk_httpx()

    def factory(
        headers: Any = None, timeout: Any = None, auth: Any = None
    ) -> httpx.AsyncClient:
        kwargs: dict[str, Any] = {"follow_redirects": True, "verify": httpx_verify(ssl_verify)}
        if headers is not None:
            kwargs["headers"] = headers
        if timeout is not None:
            kwargs["timeout"] = timeout
        if auth is not None:
            kwargs["auth"] = auth
        client: httpx.AsyncClient = httpx_impl.AsyncClient(**kwargs)
        return client

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


def describe_exception(exc: BaseException) -> str:
    """Mensaje legible de una excepción, APLANANDO los `ExceptionGroup`.

    `str()` sobre un grupo devuelve «unhandled errors in a TaskGroup (1 sub-exception)»
    y **borra la causa**: es literalmente lo que veía el usuario en `/mcp` en lugar del
    error real. Los transportes del SDK corren dentro de un `anyio.TaskGroup`, así que
    aquí el grupo es la forma NORMAL de fallar, no un caso raro. Se recorre en
    profundidad, se conserva el tipo de cada hoja y se unen con `; ` cuando hay varias
    —perder las hermanas sería cambiar un mensaje pobre por otro—.
    """
    subs = getattr(exc, "exceptions", None)
    if subs:
        base = "; ".join(describe_exception(sub) for sub in subs)
    else:
        texto = str(exc).strip()
        base = f"{type(exc).__name__}: {texto}" if texto else type(exc).__name__
    # `__notes__` es el mecanismo de la stdlib (PEP 678) para enriquecer una excepción
    # con contexto que sólo conoce quien la deja pasar; `str()` no las incluye, así que
    # aplanarlas aquí es la única forma de que lleguen a quien lee el mensaje.
    notas = getattr(exc, "__notes__", None)
    if notas:
        return " · ".join([base, *(str(nota) for nota in notas)])
    return base


def _anotar_tls(exc: BaseException, transport: str) -> None:
    """Añade a un fallo de verificación TLS qué material de confianza se usó.

    Un `CERTIFICATE_VERIFY_FAILED` no dice si el CA extra estaba activo, y ésa es
    justo la pregunta que hay que responder para arreglarlo: sin el dato, «falla el
    TLS» y «no se cargó la CA» son indistinguibles desde fuera. La nota se cuelga con
    `add_note` (PEP 678), así que no cambia el tipo ni el mensaje de la excepción — sólo
    viaja con ella hasta `describe_exception`.
    """
    if transport == "stdio":
        return
    if "CERTIFICATE_VERIFY_FAILED" not in describe_exception(exc):
        return
    from ...tls import EXTRA_CA_CERTS_ENV, extra_ca_certs_path

    ruta = extra_ca_certs_path()
    exc.add_note(
        f"CA extra ({EXTRA_CA_CERTS_ENV}): {ruta}"
        if ruta
        else f"sin CA extra: {EXTRA_CA_CERTS_ENV} no está en el entorno"
    )


class McpClient:
    """Cliente de UN server MCP — encapsula transporte + sesión + ciclo de vida.

    Patrón del canónico (`appState.mcp` con clients por server): el provider posee
    los clients; no hay globals. El transporte se elige por la identidad ya validada
    de `McpServerConfig` (`command` → stdio; `url` → streamable HTTP).

    **El ciclo de vida vive en una TASK PROPIA (`FIND-MCP-LIFECYCLE-1`).** Los tres
    transportes del SDK (`streamable_http_client`, `sse_client`, `stdio_client`) abren
    por dentro un `anyio.TaskGroup`, y un cancel scope de anyio **sólo puede salirse en
    la misma task en la que se entró**. Aquí decía «`connect()` y `aclose()` deben correr
    en el mismo contexto async», y eso era declarar la restricción en vez de pagarla
    (`D-07`): ningún host real puede garantizarla. `agentic_code` es el contraejemplo —
    Textual corre cada comando en su propia task, así que al aprobar un server el
    `reconcile()` cierra, desde la task del comando, clientes abiertos en la del arranque;
    el cierre reventaba con `RuntimeError: Attempted to exit cancel scope in a different
    task than it was entered in`, que anyio envuelve y llega al usuario como
    `unhandled errors in a TaskGroup (1 sub-exception)` — y el server queda `failed`.

    La corrección no relaja nada del SDK: **respeta su regla confinando el stack**. Una
    task dueña abre el transporte, publica el resultado y se queda esperando la señal de
    cierre; `connect()`/`aclose()` pasan a ser mensajes hacia ella y pueden llamarse desde
    cualquier task. Las llamadas de datos (`list_tools`, `call`, …) sí son cross-task por
    diseño en anyio: lo que ata a una task es el cancel scope, no los streams.
    """

    def __init__(self, config: McpServerConfig, *, auth_deps: AuthDeps | None = None) -> None:
        self._config = config
        self._auth_deps = auth_deps
        self._stack: AsyncExitStack | None = None
        self._session: Any = None
        self._owner: asyncio.Task[None] | None = None
        self._closing: asyncio.Event | None = None

    @property
    def config(self) -> McpServerConfig:
        return self._config

    @property
    def connected(self) -> bool:
        return self._session is not None

    async def connect(self) -> None:
        """Abre transporte y sesión en una task DUEÑA, y espera a que esté lista.

        Los fallos de conexión se propagan tal cual al llamante — la task dueña muere
        con el stack ya cerrado, así que no queda nada abierto. Ese contrato es el que
        `McpProvider.connect_server` usa para aislar el server sin propagar.
        """
        if self._owner is not None:
            return
        listo: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._closing = asyncio.Event()
        self._owner = asyncio.create_task(
            self._own_session(listo), name=f"mcp-session:{self._config.name}"
        )
        try:
            await listo
        except BaseException:
            # La task dueña ya cerró su propio stack antes de publicar el fallo; sólo
            # queda esperarla para no dejarla huérfana y volver al estado desconectado.
            owner, self._owner = self._owner, None
            self._closing = None
            with contextlib.suppress(BaseException):
                await owner
            raise

    async def _own_session(self, listo: asyncio.Future[None]) -> None:
        """Dueña del `AsyncExitStack`: lo abre, publica el resultado y espera el cierre.

        Todo el ciclo del cancel scope ocurre DENTRO de esta task, que es la regla que
        anyio impone y que antes se le trasladaba al integrador (`FIND-MCP-LIFECYCLE-1`).
        """
        try:
            stack, session = await self._open()
        except BaseException as exc:  # noqa: BLE001 — la task dueña no puede dejar
            # escapar NADA: si el fallo no viaja al futuro, `connect()` espera para
            # siempre. Se publica y se vuelve al estado desconectado.
            #
            # La nota se pone AQUÍ y no dentro de `_open`: lo que allí se captura suele
            # ser el `CancelledError` del scope de anyio, y la causa real llega después,
            # dentro del grupo que lanza el propio `aclose()` del stack. Éste es el
            # único punto por el que pasa la excepción que de verdad se propaga.
            _anotar_tls(exc, self._config.resolved_transport())
            if not listo.done():
                listo.set_exception(exc)
            else:  # el llamante se fue antes; el fallo no puede perderse en silencio
                logger.warning("mcp: %r falló al conectar sin nadie esperando: %s",
                               self._config.name, exc)
            return
        self._stack = stack
        self._session = session
        if listo.done():  # `connect()` fue cancelado mientras abríamos: no dejar el stack
            await stack.aclose()
            self._stack = None
            self._session = None
            return
        listo.set_result(None)
        try:
            assert self._closing is not None
            await self._closing.wait()
        finally:
            self._session = None
            self._stack = None
            await stack.aclose()

    async def _open(self) -> tuple[AsyncExitStack, Any]:
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
                from ...tls import httpx_verify
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
                else:  # http (Streamable HTTP)
                    from mcp.client.streamable_http import streamable_http_client

                    request_timeout = self._config.timeout_seconds or 30.0
                    # `streamable_http_client` recibe el cliente YA CONSTRUIDO, así que el
                    # transporte no pone ni timeouts ni material TLS: lo que no se ponga
                    # aquí no lo pone nadie. (La firma con `headers=`/`timeout=` es de
                    # `streamablehttp_client`, sin guion bajo, que está DEPRECADA y es otra
                    # función; no hay dos firmas vivas de ésta en `mcp>=1.26.0`.)
                    #
                    # El timeout DEBE venir del config (espejo del default operativo del
                    # provider, 30s): sin pasarlo, httpx aplica su default de 5s y toda
                    # tool que tarde más da ReadTimeout. Pero un timeout PLANO tampoco
                    # vale: el canal GET de streamable-HTTP es un stream abierto y con
                    # `read=30` se corta solo; el propio SDK separa los dos ejes
                    # (`sse_read_timeout=300`) y aquí se hace igual.
                    httpx_impl = _sdk_httpx()
                    http_client = await stack.enter_async_context(
                        httpx_impl.AsyncClient(
                            headers=headers, auth=httpx_auth,
                            verify=httpx_verify(self._config.ssl_verify),
                            follow_redirects=True,
                            timeout=httpx_impl.Timeout(
                                request_timeout, read=SSE_READ_TIMEOUT_SECONDS
                            ),
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

        return stack, session

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
        """Pide el cierre a la task dueña y la espera. Idempotente y cross-task."""
        owner, self._owner = self._owner, None
        closing, self._closing = self._closing, None
        if owner is None:
            self._stack = None
            self._session = None
            return
        if closing is not None:
            closing.set()
        try:
            await owner
        except asyncio.CancelledError:
            # La dueña pudo ser cancelada por el cierre del host; eso no es un fallo del
            # cierre, y re-lanzarlo aquí abortaría el shutdown del resto de servers.
            if asyncio.current_task() is not None and getattr(
                asyncio.current_task(), "cancelling", lambda: 0
            )():
                raise
        finally:
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


__all__ = ["McpClient", "McpToolError", "describe_exception"]
