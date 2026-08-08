"""Tests para runtime/tools/ — ToolProtocol, ToolRegistry, ToolDispatcher."""
import asyncio

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.abort import AbortController
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.tools import (
    ToolCategory,
    ToolDispatcher,
    ToolProtocol,
    ToolRegistry,
    ToolResult,
)
from agentic_runtime.tools.pool import ToolPool

# ---------------------------------------------------------------------------
# Helpers — stubs de tools
# ---------------------------------------------------------------------------

class FastTool:
    name = "fast_tool"
    description = "Does nothing quickly"
    input_schema: dict = {}  # noqa: RUF012
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        return ToolResult(tool_name=self.name, output="done")


class SlowTool:
    name = "slow_tool"
    description = "Sleeps forever"
    input_schema: dict = {}  # noqa: RUF012
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 0.05  # muy corto para el test

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        await asyncio.sleep(10)
        return ToolResult(tool_name=self.name, output="never")


class PermissionedTool:
    name = "permissioned_tool"
    description = "Requires explicit permission"
    input_schema: dict = {}  # noqa: RUF012
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        return ToolResult(tool_name=self.name, output="secret")


def _ctx(*tools: ToolProtocol, stop: AbortController | None = None) -> ToolUseContext:
    # El dispatcher resuelve desde ctx.tool_pool (alineado al canónico): las tools
    # del turno se siembran en el pool, no en un registry aparte.
    return ToolUseContext(
        session_id="s1",
        stop=stop,
        tool_pool=ToolPool(native_tools=list(tools)),
    )


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------

def test_registry_resolve_registered_tool():
    reg = ToolRegistry()
    reg.register(FastTool())
    tool = reg.resolve("fast_tool")
    assert tool is not None
    assert tool.name == "fast_tool"


def test_registry_resolve_unknown_returns_none():
    reg = ToolRegistry()
    assert reg.resolve("nonexistent") is None


def test_registry_list_available_excludes_unsafe_in_background():
    reg = ToolRegistry()
    reg.register(FastTool())   # safe_for_background=True
    reg.register(SlowTool())   # safe_for_background=False
    available = reg.list_available(mode="background")
    names = [t.name for t in available]
    assert "fast_tool" in names
    assert "slow_tool" not in names


def test_registry_list_available_includes_all_in_foreground():
    reg = ToolRegistry()
    reg.register(FastTool())
    reg.register(SlowTool())
    available = reg.list_available(mode="foreground")
    names = [t.name for t in available]
    assert "fast_tool" in names
    assert "slow_tool" in names


# ---------------------------------------------------------------------------
# ToolDispatcher — dispatch básico
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_resolves_and_executes():
    disp = ToolDispatcher()

    result = await disp.dispatch(tool_name="fast_tool", tool_input={}, ctx=_ctx(FastTool()))
    assert result.output == "done"
    assert not result.is_error


@pytest.mark.asyncio
async def test_dispatcher_unknown_tool_returns_error():
    disp = ToolDispatcher()

    result = await disp.dispatch(tool_name="ghost", tool_input={}, ctx=_ctx())
    assert result.is_error
    assert "ghost" in result.output


# ---------------------------------------------------------------------------
# ToolDispatcher — timeout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_applies_timeout():
    disp = ToolDispatcher()

    result = await disp.dispatch(tool_name="slow_tool", tool_input={}, ctx=_ctx(SlowTool()))
    assert result.is_timeout


# ---------------------------------------------------------------------------
# ToolDispatcher — abort
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_aborts_if_event_set():
    disp = ToolDispatcher()

    stop = AbortController()
    stop.abort()
    result = await disp.dispatch(tool_name="fast_tool", tool_input={}, ctx=_ctx(FastTool(), stop=stop))
    assert result.is_aborted


# ---------------------------------------------------------------------------
# ToolDispatcher — permisos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_checks_permission_denied():
    disp = ToolDispatcher()

    # PermissionContext por defecto no tiene permisos
    result = await disp.dispatch(tool_name="permissioned_tool", tool_input={}, ctx=_ctx(PermissionedTool()))
    assert result.is_error


@pytest.mark.asyncio
async def test_dispatcher_allows_permissioned_tool_when_granted():
    from agentic_runtime.context.tool_use import AppState

    disp = ToolDispatcher()

    perms = PermissionContext(always_allow_command=["permissioned_tool"])
    ctx = ToolUseContext(
        session_id="s1",
        app_state=AppState(permissions=perms),
        tool_pool=ToolPool(native_tools=[PermissionedTool()]),
    )
    result = await disp.dispatch(tool_name="permissioned_tool", tool_input={}, ctx=ctx)
    assert not result.is_error
    assert result.output == "secret"


# ---------------------------------------------------------------------------
# ToolProtocol structural check
# ---------------------------------------------------------------------------

def test_fast_tool_satisfies_protocol():
    assert isinstance(FastTool(), ToolProtocol)


# ---------------------------------------------------------------------------
# GAP medido: el timeout del dispatcher NO acota a una tool que bloquea el loop
# ---------------------------------------------------------------------------

class _BlockingTool:
    """Tool que hace E/S SINCRONA dentro de `async def` — la forma real de
    `web_fetch.py:53` y `web_search.py:111` (`urllib.request.urlopen`)."""

    name = "blocking_tool"
    description = "bloquea el event loop"
    input_schema: dict = {}  # noqa: RUF012
    category = ToolCategory.NETWORK
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 0.2

    async def execute(self, input: dict, ctx=None) -> ToolResult:
        import time
        # Silenciado a propósito: el `time.sleep` síncrono dentro de `async def` ES el
        # defecto que este test demuestra. Arreglar el lint aquí borraría la prueba.
        time.sleep(1.0)  # noqa: ASYNC251
        return ToolResult(tool_name=self.name, output="termine igual")


@pytest.mark.asyncio
async def test_una_corrutina_que_no_cede_no_se_puede_acotar_y_esto_esta_medido():
    """El LÍMITE ESTRUCTURAL del cap, aseverado en vez de supuesto (`FIND-C6-2`, parte 1).

    `asyncio.wait_for` no puede preemptar una corrutina que nunca cede el control: no hay
    dónde entregarle la cancelación. **No es deuda de homologación** — A tiene exactamente
    la misma propiedad (un solo event loop en JS: una función síncrona larga congela el
    proceso), y de hecho A **ni siquiera tiene** un cap genérico por tool en su dispatcher;
    su único `timeout` es el de INPUT de `Bash` (`toolExecution.ts:1148-1149`), que honra el
    subproceso, aplicado justo donde hay algo genuinamente preemptable.

    Lo que sí era deuda —y se paga en el test siguiente— es que las tools de red de B
    **fueran** esa corrutina que no cede.

    El `xfail(strict=True)` que ocupaba este lugar ACREDITABA EN FALSO (`H-L4`): reventaba
    en `ToolUseContext(tool_pool=...)` con `ValidationError: session_id Field required`, o
    sea que nunca llegó a llamar a `dispatch` ni a medir un timeout, y el `strict` tampoco
    habría enrojecido al pagarse el gap, porque el fallo venía de otro sitio.
    """
    import time

    ctx = _ctx(_BlockingTool())
    t0 = time.monotonic()
    result = await ToolDispatcher().dispatch(
        tool_name="blocking_tool", tool_input={}, ctx=ctx
    )
    elapsed = time.monotonic() - t0

    # Se asevera el límite REAL, con su signo: el cap de 0.2 s no acota, la tool termina
    # entera y vuelve como ÉXITO. Si algún día esto cambiara, el test se pone rojo y obliga
    # a revisar el razonamiento de arriba en vez de dejarlo caducar en silencio.
    assert not result.is_error, "cambió la conducta: ahora sí acota una corrutina que no cede"
    assert elapsed >= 1.0, f"la tool no llegó a bloquear: {elapsed:.2f}s"

    # CONTROL POSITIVO: en cuanto la tool CEDE, el mismo cap sí acota.
    t0 = time.monotonic()
    lento = await ToolDispatcher().dispatch(
        tool_name="slow_tool", tool_input={}, ctx=_ctx(SlowTool())
    )
    assert lento.is_timeout and time.monotonic() - t0 < 1.0


@pytest.mark.asyncio
async def test_las_tools_de_red_no_bloquean_el_event_loop_y_el_cap_las_acota(monkeypatch):
    """`FIND-C6-2` PAGADO (parte 2), contra un servidor HTTP REAL que tarda.

    Antes, `web_fetch.py`/`web_search.py` hacían `urlopen` síncrono dentro de su `async
    def`: eran literalmente la corrutina que no cede del test anterior, hasta 20 s cada
    una. Consecuencias medidas, las dos aseveradas aquí:

    1. el cap del dispatcher no valía nada sobre ellas — la afirmación firmada en
       `11-cap-mcp.md:656-658` («una tool que tarde >30 s FALLA») era falsa;
    2. y con un solo event loop, esos segundos congelaban stream, subagentes y
       notificaciones — por eso el LATIDO concurrente es la aserción que de verdad
       distingue «cede» de «no cede», y no el mero hecho de que devuelva timeout.

    A no tiene el problema porque su E/S de red es asíncrona de raíz y honra el `signal`
    además de su propio `FETCH_TIMEOUT_MS` (`WebFetchTool/utils.ts:262-282`).
    """
    import http.server
    import threading
    import time

    from agentic_runtime.tools.native import web_fetch as web_fetch_mod
    from agentic_runtime.tools.native.web_fetch import WebFetchTool

    class _Lento(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            time.sleep(2.0)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"tarde")

        def log_message(self, *args: object) -> None:
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), _Lento)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    try:
        from agentic_runtime.context.tool_use import AppState

        url = f"http://127.0.0.1:{srv.server_address[1]}/"
        tool = WebFetchTool()
        # `WebFetch` es `requires_permission = True`: sin concederlo el dispatcher corta
        # ANTES de la red y el test mediría el gate de permisos, no el bloqueo.
        ctx = ToolUseContext(
            session_id="s1",
            app_state=AppState(permissions=PermissionContext(always_allow_command=[tool.name])),
            tool_pool=ToolPool(native_tools=[tool]),
        )

        latidos = 0

        async def latir() -> None:
            nonlocal latidos
            while True:
                await asyncio.sleep(0.02)
                latidos += 1

        pulso = asyncio.create_task(latir())
        t0 = time.monotonic()
        # El upgrade http→https (`utils.ts:375-379`, homologado en la 11ª ventana) es
        # incondicional en A, así que contra un servidor de pruebas que sólo habla HTTP la
        # petición moriría al instante y no habría red que medir. Se neutraliza SÓLO ese
        # colaborador: la propiedad bajo prueba es que el event loop sigue latiendo
        # mientras la tool está en la red, y el upgrade tiene su propio test
        # (`test_web_fetch_upgrades_http_to_https`). No se relaja ninguna aserción.
        monkeypatch.setattr(web_fetch_mod, "_upgrade_scheme", lambda u: u)
        result = await ToolDispatcher(timeout_override=0.3).dispatch(
            tool_name=tool.name,
            tool_input={"url": url, "prompt": "qué dice"},  # `prompt` es requerido (A lo exige)
            ctx=ctx,
        )
        elapsed = time.monotonic() - t0
        pulso.cancel()

        assert result.is_timeout, f"el cap de 0.3s no acotó a WebFetch: {result.output!r}"
        assert elapsed < 1.5, f"el cap no cortó a tiempo: {elapsed:.2f}s"
        # LA ASERCIÓN QUE IMPORTA: el loop siguió vivo mientras la tool estaba en la red.
        # Con `urlopen` en el event loop esto sale 0 y no hay cap que lo disimule.
        assert latidos >= 5, f"el event loop estuvo congelado: {latidos} latidos"
    finally:
        srv.shutdown()
        srv.server_close()


@pytest.mark.asyncio
async def test_web_search_tampoco_bloquea_el_event_loop(monkeypatch):
    """`FIND-C6-2` PAGADO (parte 3): la hermana de `WebFetch` tenía el MISMO defecto.

    `WebSearch` no se puede apuntar a un servidor local —su endpoint es fijo
    (`https://google.serper.dev/search`)—, así que lo que se sustituye es la llamada
    bloqueante `_serper_search`, que es justamente la pieza que hacía `urlopen` síncrono
    (`web_search.py:111`). Si `execute` la invocara directamente en vez de por
    `asyncio.to_thread`, el latido se para: eso es lo que se mide.
    """
    import time

    from agentic_runtime.context.tool_use import AppState
    from agentic_runtime.tools.native import web_search as ws

    monkeypatch.setenv("SERPER_API_KEY", "clave-de-test")

    def _bloqueante(tool_name: str, query: str, n: int, api_key: str) -> ToolResult:
        time.sleep(0.5)
        return ToolResult(tool_name=tool_name, output=f"resultados de {query}")

    monkeypatch.setattr(ws, "_serper_search", _bloqueante)

    tool = ws.WebSearchTool()
    ctx = ToolUseContext(
        session_id="s1",
        app_state=AppState(permissions=PermissionContext(always_allow_command=[tool.name])),
        tool_pool=ToolPool(native_tools=[tool]),
    )

    latidos = 0

    async def latir() -> None:
        nonlocal latidos
        while True:
            await asyncio.sleep(0.02)
            latidos += 1

    pulso = asyncio.create_task(latir())
    result = await ToolDispatcher().dispatch(
        tool_name=tool.name, tool_input={"query": "qué"}, ctx=ctx
    )
    pulso.cancel()

    assert not result.is_error, result.output
    assert "resultados de" in result.output, result.output
    assert latidos >= 5, f"el event loop estuvo congelado: {latidos} latidos"
