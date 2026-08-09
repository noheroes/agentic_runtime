"""Tests para capabilities/mcp/ — ciclo de vida real de clients (Fase M1).

Foco: connect/discover/call/aclose, estado de conexión (pending/failed/connected),
aislamiento por ítem (un server caído no tumba al resto) y mapeo de isError.
El transporte se inyecta vía `client_factory` (cliente fake) — sin server real.
"""
from types import SimpleNamespace

import certifi
import httpx
import mcp
import mcp.client.streamable_http as _shttp
import pytest

from agentic_runtime.capabilities.mcp import (
    McpProvider,
    McpServerConfig,
    McpToolError,
    ServerStatus,
    build_mcp_tool,
)
from agentic_runtime.capabilities.mcp.client import McpClient
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


class _FakeClient:
    """Cliente MCP fake — implementa la misma superficie que McpClient sin transporte."""

    def __init__(
        self,
        config: McpServerConfig,
        *,
        tools: list[dict] | None = None,
        resources: list[dict] | None = None,
        fail_on_connect: bool = False,
        tool_error: str | None = None,
    ) -> None:
        self.config = config
        self._tools = tools or []
        self._resources = resources or []
        self._fail = fail_on_connect
        self._tool_error = tool_error
        self.connected = False
        self.closed = False
        self.call_count = 0

    async def connect(self) -> None:
        if self._fail:
            raise RuntimeError("transporte caído")
        self.connected = True

    async def list_tools(self) -> list[dict]:
        return self._tools

    async def list_resources(self) -> list[dict]:
        return self._resources

    async def call(self, tool_name: str, tool_input: dict) -> str:
        self.call_count += 1
        if self._tool_error is not None:
            raise McpToolError(self._tool_error)
        return f"{tool_name}:{tool_input}"

    async def aclose(self) -> None:
        self.closed = True


def _provider_with(**fake_kwargs) -> McpProvider:
    def factory(config: McpServerConfig) -> _FakeClient:
        return _FakeClient(config, **fake_kwargs)

    return McpProvider(client_factory=factory)


# ---------------------------------------------------------------------------
# connect: descubrimiento de tools/resources + estado
# ---------------------------------------------------------------------------

async def test_connect_discovers_tools_and_marks_connected():
    provider = _provider_with(
        tools=[{"name": "alpha", "description": "a"}, {"name": "beta"}],
        resources=[{"uri": "mcp://r"}],
    )
    provider.add_server("srv", {"command": "run"})
    ok = await provider.connect_server("srv")

    assert ok is True
    assert provider.state.status("srv") is ServerStatus.CONNECTED
    tool_names = [t.name for t in provider.tools(_ctx())]
    assert tool_names[:2] == ["mcp__srv__alpha", "mcp__srv__beta"]  # tools del server como prefijo
    # con resources presentes, el provider añade además las resource tools (M4)
    assert {"ListMcpResources", "ReadMcpResource"} <= set(tool_names)
    assert provider.resources(_ctx()) == [{"uri": "mcp://r", "server": "srv"}]
    assert provider.state.connected_servers() == ["srv"]


async def test_connect_unregistered_server_returns_false():
    provider = _provider_with()
    assert await provider.connect_server("ghost") is False


# ---------------------------------------------------------------------------
# aislamiento por ítem: un server caído no tumba al resto
# ---------------------------------------------------------------------------

async def test_failed_server_is_isolated_and_recorded():
    def factory(config: McpServerConfig) -> _FakeClient:
        fail = config.name == "bad"
        return _FakeClient(config, fail_on_connect=fail, tools=[{"name": f"{config.name}_t"}])

    provider = McpProvider(client_factory=factory)
    provider.add_server("good", {"command": "run"})
    provider.add_server("bad", {"command": "run"})

    await provider.startup()

    assert provider.state.status("good") is ServerStatus.CONNECTED
    assert provider.state.status("bad") is ServerStatus.FAILED
    assert "transporte caído" in provider.state.failed_servers()["bad"]
    # las tools del bueno siguen expuestas; ninguna del malo
    assert [t.name for t in provider.tools(_ctx())] == ["mcp__good__good_t"]


# ---------------------------------------------------------------------------
# call: transporte del client + mapeo de isError
# ---------------------------------------------------------------------------

async def test_tool_call_routes_through_connected_client():
    provider = _provider_with(tools=[{"name": "alpha"}])
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")

    tool = provider.tools(_ctx())[0]
    result = await tool.execute({"k": "v"}, _ctx())
    assert not result.is_error
    assert result.output.startswith("alpha:")


async def test_tool_is_error_maps_to_error_result_single_call():
    fake = _FakeClient(McpServerConfig(name="s", command="run"), tool_error="boom de tool")
    tool = build_mcp_tool({"name": "t"}, fake.call)

    result = await tool.execute({}, _ctx())
    assert result.is_error
    assert "boom de tool" in result.output
    assert fake.call_count == 1  # no doble llamada en error


# ---------------------------------------------------------------------------
# shutdown: cierra todos los clients
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# connect (streamable HTTP): el httpx.AsyncClient recibe el timeout configurado
# y NO el default de httpx (5s), que mata tools que tardan más (regresión real:
# create_drawio_diagram ~7s daba ReadTimeout en la 2ª llamada del turno).
# ---------------------------------------------------------------------------


class _FakeStreams:
    async def __aenter__(self):
        return (object(), object())

    async def __aexit__(self, *exc):
        return False


class _FakeSession:
    def __init__(self, *a, **k) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def initialize(self):
        return None


def _patch_streamable_transport(monkeypatch) -> dict:
    """Stub del transporte streamable-HTTP, sin server real.

    El stub declara la firma REAL (`url` + `http_client` keyword-only) en vez de tragar
    `**kwargs`: uno permisivo daría verde con cualquier forma de llamada y no probaría
    nada. Esa firma es la misma en todo el rango declarado (`mcp>=1.26.0`) — la variante
    con `headers=`/`timeout=`/`httpx_client_factory=` pertenece a `streamablehttp_client`,
    sin guion bajo, que es otra función y está deprecada.
    """
    captured: dict = {}

    class _CapturingClient:
        def __init__(self, **kwargs) -> None:
            captured["timeout"] = kwargs.get("timeout")
            captured["verify"] = kwargs.get("verify")
            captured["cliente"] = type(self).__name__

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    def transport(url, *, http_client=None, terminate_on_close=True):
        captured["url"] = url
        captured["http_client"] = http_client
        return _FakeStreams()

    monkeypatch.setattr(httpx, "AsyncClient", _CapturingClient)
    monkeypatch.setattr(_shttp, "streamable_http_client", transport)
    monkeypatch.setattr(mcp, "ClientSession", _FakeSession)
    return captured


async def test_streamable_http_uses_configured_timeout(monkeypatch):
    captured = _patch_streamable_transport(monkeypatch)
    cfg = McpServerConfig(name="s", url="http://x/mcp", type="http", timeout_seconds=42.0)
    await McpClient(cfg).connect()
    assert captured["timeout"].connect == 42.0


async def test_streamable_http_defaults_timeout_above_httpx_5s(monkeypatch):
    captured = _patch_streamable_transport(monkeypatch)
    cfg = McpServerConfig(name="s", url="http://x/mcp", type="http")  # timeout_seconds=None
    await McpClient(cfg).connect()
    # sin config explícita, debe usar el default operativo del provider (30s), nunca
    # quedarse con el default de httpx (5s) que regresa el bug.
    assert captured["timeout"].connect == 30.0


async def test_el_read_timeout_no_corta_el_canal_sse(monkeypatch):
    """Un timeout PLANO mata el canal GET, que es un stream de larga duración.

    El timeout de request y el de lectura del stream son ejes distintos: el SDK los
    separa (`sse_read_timeout=300`) y el runtime tiene que hacer lo mismo, o el server
    pierde la vía por la que envía notificaciones cada vez que pasan 30 s en silencio.
    """
    captured = _patch_streamable_transport(monkeypatch)
    cfg = McpServerConfig(name="s", url="http://x/mcp", type="http", timeout_seconds=42.0)
    await McpClient(cfg).connect()
    timeout = captured["timeout"]
    assert timeout.read == 300.0, timeout
    assert timeout.connect == 42.0 and timeout.write == 42.0, timeout


async def test_el_transporte_recibe_el_cliente_ya_construido(monkeypatch):
    """`streamable_http_client` no construye cliente: lo recibe.

    De ahí que TODO —timeouts y material TLS— tenga que ponerlo el llamante. El stub
    declara la firma real, así que una llamada con la forma deprecada (`headers=`,
    `timeout=`, `httpx_client_factory=`) muere aquí con `TypeError` en vez de pasar.
    """
    captured = _patch_streamable_transport(monkeypatch)
    cfg = McpServerConfig(name="s", url="http://x/mcp", type="http", timeout_seconds=42.0)
    await McpClient(cfg).connect()
    assert captured["http_client"] is not None, "el transporte se llamó sin cliente"


# ---------------------------------------------------------------------------
# El FLAVOR de httpx: en `mcp` 2.0 el transporte abre el canal GET con `client.sse(...)`,
# que sólo existe en `httpx2`. Con un `httpx.AsyncClient` normal la conexión se
# establece, las tool calls (POST) funcionan y el canal GET revienta DENTRO del task
# group con `AttributeError: 'AsyncClient' object has no attribute 'sse'` — o sea, el
# server se queda sin vía para hablar y desde fuera parece que todo va bien. Medido
# contra el server real (`D-15`); esta suite corre con 1.27.2 y estaba verde y ciega.
# ---------------------------------------------------------------------------


async def test_el_flavor_de_httpx_se_lee_del_sdk_no_se_supone(monkeypatch):
    from mcp.shared import _httpx_utils

    from agentic_runtime.capabilities.mcp.client import _sdk_httpx

    centinela = SimpleNamespace(AsyncClient=object, Timeout=object)
    monkeypatch.setattr(_httpx_utils, "httpx2", centinela, raising=False)
    assert _sdk_httpx() is centinela, "se ignoró el httpx que usa el propio SDK"

    monkeypatch.delattr(_httpx_utils, "httpx2", raising=False)
    assert _sdk_httpx() is httpx


async def test_el_cliente_del_transporte_se_construye_con_el_flavor_del_sdk(monkeypatch):
    """No basta con elegir bien el módulo: hay que CONSTRUIR el cliente con él."""
    from mcp.shared import _httpx_utils

    construidos: list[str] = []

    class _Httpx2Client:
        def __init__(self, **kwargs) -> None:
            construidos.append("httpx2")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    falso_httpx2 = SimpleNamespace(AsyncClient=_Httpx2Client, Timeout=httpx.Timeout)
    monkeypatch.setattr(_httpx_utils, "httpx2", falso_httpx2, raising=False)
    captured = _patch_streamable_transport(monkeypatch)

    await McpClient(McpServerConfig(name="s", url="http://x/mcp", type="http")).connect()

    assert construidos == ["httpx2"], "el cliente se construyó con el httpx equivocado"
    assert isinstance(captured["http_client"], _Httpx2Client)


# ---------------------------------------------------------------------------
# CA extra: el contexto TLS del proceso tiene que llegar a las DOS ramas (http y sse).
# La que se olvide se queda con el almacén por defecto y falla SÓLO contra el server con
# CA propia — que es justo el que motivó el arreglo.
# ---------------------------------------------------------------------------


async def test_la_ca_extra_llega_al_transporte_http(monkeypatch):
    import ssl as _ssl

    from agentic_runtime import tls

    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, certifi.where())
    tls.clear_tls_cache()
    captured = _patch_streamable_transport(monkeypatch)

    await McpClient(McpServerConfig(name="s", url="https://x/mcp", type="http")).connect()

    tls.clear_tls_cache()
    assert isinstance(captured["verify"], _ssl.SSLContext), captured["verify"]


async def test_la_ca_extra_llega_al_transporte_sse(monkeypatch):
    import ssl as _ssl

    from agentic_runtime import tls
    from agentic_runtime.capabilities.mcp.client import _http_client_factory

    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, certifi.where())
    tls.clear_tls_cache()
    capturado: dict = {}

    class _CapturingClient:
        def __init__(self, **kwargs) -> None:
            capturado.update(kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _CapturingClient)
    _http_client_factory(True)(headers=None, timeout=5, auth=None)

    tls.clear_tls_cache()
    assert isinstance(capturado["verify"], _ssl.SSLContext), capturado.get("verify")


async def test_ssl_verify_false_sigue_desactivando_la_validacion(monkeypatch):
    """El eje por-server manda sobre el del entorno: quien lo apaga no quiere contexto."""
    from agentic_runtime import tls

    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, certifi.where())
    tls.clear_tls_cache()
    captured = _patch_streamable_transport(monkeypatch)

    cfg = McpServerConfig(name="s", url="https://x/mcp", type="http", ssl_verify=False)
    await McpClient(cfg).connect()

    tls.clear_tls_cache()
    assert captured["verify"] is False


# ---------------------------------------------------------------------------
# Grafía del SDK: los modelos de `mcp.types` son pydantic con alias camelCase, y cuál de
# las dos grafías es el ATRIBUTO de Python cambió entre 1.x (`inputSchema`) y 2.x
# (`input_schema`). El runtime declara `mcp>=1.26.0`, así que las dos están soportadas.
# Detectado por el consumidor real (`D-15`): `agentic_code` resolvió 2.0.0 y ahí el
# runtime degradaba EN SILENCIO. Esta suite corre con 1.27.2 y estaba verde y ciega, así
# que lo que se fija aquí no es «la versión X», es que la LECTURA sea por lista.
# ---------------------------------------------------------------------------


class _SessionWith:
    """Sesión MCP fake que devuelve los objetos tal cual se le den (sin transporte)."""

    def __init__(self, *, tools=(), resources=(), call_result=None) -> None:
        self._tools = list(tools)
        self._resources = list(resources)
        self._call_result = call_result

    async def list_tools(self):
        return SimpleNamespace(tools=self._tools)

    async def list_resources(self):
        return SimpleNamespace(resources=self._resources)

    async def call_tool(self, name, arguments):
        return self._call_result


def _client_with(session) -> McpClient:
    client = McpClient(McpServerConfig(name="s", command="run"))
    client._session = session
    return client


@pytest.mark.parametrize("field", ["inputSchema", "input_schema"])
async def test_the_tool_schema_survives_either_sdk_spelling(field):
    """Sin esto el modelo recibe la tool SIN parámetros y no puede invocarla bien.

    Medido contra un server real bajo SDK 2.x: las tres tools llegaban con `{}`.
    """
    schema = {"type": "object", "properties": {"text": {"type": "string"}}}
    tool = SimpleNamespace(name="echo", description="d", annotations=None, **{field: schema})

    specs = await _client_with(_SessionWith(tools=[tool])).list_tools()

    assert specs[0]["inputSchema"] == schema, specs


async def test_a_failing_tool_is_not_delivered_to_the_model_as_a_correct_answer():
    """`isError` con la grafía nueva: el fallo del server llegaba en el hueco del ÉXITO."""
    result = SimpleNamespace(
        content=[SimpleNamespace(text="el server rechaza 'x'")], is_error=True
    )

    with pytest.raises(McpToolError):
        await _client_with(_SessionWith(call_result=result)).call("always_fails", {})


@pytest.mark.parametrize("field", ["mimeType", "mime_type"])
async def test_the_resource_mime_type_survives_either_sdk_spelling(field):
    resource = SimpleNamespace(uri="mcp://r", name="r", description="", **{field: "text/plain"})

    resources = await _client_with(_SessionWith(resources=[resource])).list_resources()

    assert resources[0]["mimeType"] == "text/plain", resources


async def test_the_server_meta_reaches_the_adapter_so_the_search_hint_is_not_dead():
    """`searchHint` era un cable MUERTO: el adapter lo leía y el client no lo ponía nunca.

    Ningún test lo veía porque todos fabrican el spec a mano. Es la única pista curada de
    una tool MCP y puntúa +4 en ToolSearch — para una tool DIFERIDA, la diferencia entre
    que el modelo la encuentre por keyword o no la encuentre (`services/mcp/client.ts:1778-1784`).
    """
    tool = SimpleNamespace(
        name="echo", description="d", annotations=None, input_schema={},
        meta={"searchHint": "shout text loudly"},
    )

    specs = await _client_with(_SessionWith(tools=[tool])).list_tools()
    adapted = build_mcp_tool(specs[0], _SessionWith().call_tool)

    assert specs[0]["_meta"] == {"searchHint": "shout text loudly"}, specs
    assert adapted is not None and adapted.search_hint == "shout text loudly"


async def test_shutdown_closes_all_clients():
    clients: list[_FakeClient] = []

    def factory(config: McpServerConfig) -> _FakeClient:
        c = _FakeClient(config, tools=[{"name": "t"}])
        clients.append(c)
        return c

    provider = McpProvider(client_factory=factory)
    provider.add_server("a", {"command": "run"})
    provider.add_server("b", {"command": "run"})
    await provider.startup()
    await provider.shutdown()

    assert all(c.closed for c in clients)
    assert len(clients) == 2
