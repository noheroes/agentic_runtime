"""Delta de anuncio de tools diferidas — homólogo `deferred_tools_delta` canónico.

Cubre la lógica pura (`compute/render`, con round-trip de parseo) y la inyección en el
loop: correr un turno con un server MCP conectado anuncia el NOMBRE de la diferida al
modelo vía `<system-reminder>`, sin re-anunciarlo en iteraciones siguientes.
"""
from agentic_runtime.capabilities import CapabilityManager
from agentic_runtime.capabilities.mcp import McpProvider
from agentic_runtime.context.tool_use import AppState, ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.events import DoneEvent
from agentic_runtime.loop.agent_loop import AgentLoop, _as_reminder
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.tools.native import ToolSearchTool
from agentic_runtime.tools.deferred_delta import (
    compute_deferred_tools_delta,
    render_deferred_tools_delta,
)


class _Tool:
    """Stub mínimo con nombre + flag deferred (lo que lee `is_deferred_tool`)."""

    def __init__(self, name: str, deferred: bool = False) -> None:
        self.name = name
        self.deferred = deferred


def _reminder_msg(added, removed=()):
    """Simula un reminder ya presente en la conversación (como lo dejaría el loop)."""
    return {"role": "user", "content": _as_reminder(render_deferred_tools_delta(list(added), list(removed)))}


# --- lógica pura -----------------------------------------------------------

def test_added_when_nothing_announced():
    pool = [_Tool("drawio_create", deferred=True), _Tool("echo")]
    delta = compute_deferred_tools_delta(pool, messages=[])
    assert delta == (["drawio_create"], [])


def test_none_when_already_announced_roundtrip():
    """El parseo de reminders previos reconstruye lo anunciado → sin cambios = None."""
    pool = [_Tool("drawio_create", deferred=True)]
    messages = [_reminder_msg(added=["drawio_create"])]
    assert compute_deferred_tools_delta(pool, messages) is None


def test_new_server_midsession_is_added_only():
    """Con una diferida ya anunciada y otra nueva, solo se anuncia la nueva."""
    pool = [_Tool("drawio_create", deferred=True), _Tool("gmail_send", deferred=True)]
    messages = [_reminder_msg(added=["drawio_create"])]
    assert compute_deferred_tools_delta(pool, messages) == (["gmail_send"], [])


def test_removed_when_disconnected():
    """Anunciada pero ya no en el pool (server desconectado) → se reporta removida."""
    pool = [_Tool("echo")]
    messages = [_reminder_msg(added=["drawio_create"])]
    assert compute_deferred_tools_delta(pool, messages) == ([], ["drawio_create"])


def test_undeferred_but_in_pool_is_not_removed():
    """Anunciada, ya no diferida pero SIGUE en el pool (cargada directa) → silencio."""
    pool = [_Tool("drawio_create", deferred=False)]
    messages = [_reminder_msg(added=["drawio_create"])]
    assert compute_deferred_tools_delta(pool, messages) is None


def test_removed_line_stops_reannouncing():
    """Tras anunciar alta y luego baja, la diferida cuenta como no-anunciada de nuevo."""
    messages = [_reminder_msg(added=["drawio_create"]), _reminder_msg(added=[], removed=["drawio_create"])]
    pool = [_Tool("drawio_create", deferred=True)]
    # reconectada: vuelve a estar diferida y ya no figura como anunciada → se re-anuncia
    assert compute_deferred_tools_delta(pool, messages) == (["drawio_create"], [])


# --- inyección en el loop --------------------------------------------------

class _FakeMcpClient:
    def __init__(self, config):
        self.config = config

    async def connect(self):
        pass

    async def list_tools(self):
        return [{"name": "drawio_create", "description": "create a drawio diagram"}]

    async def list_resources(self):
        return []

    async def call(self, tool_name, tool_input):
        return "ok"

    async def aclose(self):
        pass


class _NativeEcho:
    name = "echo"
    description = "native echo"
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="ok")


def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
            async def _gen():
                for ev in events:
                    yield ev

            return _gen()

    return StubCaller()


async def _connected_provider():
    provider = McpProvider(client_factory=_FakeMcpClient)
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")
    return provider


def _loop(caller):
    reg = ToolRegistry()
    reg.register(_NativeEcho())
    reg.register(ToolSearchTool())
    return reg


async def test_loop_announces_deferred_tool_name_to_model():
    provider = await _connected_provider()
    manager = CapabilityManager([provider])
    reg = _loop(None)
    loop = AgentLoop(
        model_caller=_make_caller(DoneEvent(stop_reason="stop")),
        tool_registry=reg, capability_manager=manager, tool_dispatcher=ToolDispatcher(),
    )
    ctx = ToolUseContext(session_id="s1", app_state=AppState(permissions=PermissionContext()))
    await loop.run("hola", ctx)

    reminders = [m["content"] for m in ctx.messages if m.get("role") == "user"
                 and "now available via ToolSearch" in (m.get("content") or "")]
    assert len(reminders) == 1, "debe anunciarse exactamente una vez"
    assert "drawio_create" in reminders[0]
    assert "<system-reminder>" in reminders[0]


async def test_loop_does_not_reannounce_across_iterations():
    """Dos iteraciones del modelo en el mismo run: el reminder se inyecta solo la 1ª."""
    provider = await _connected_provider()
    manager = CapabilityManager([provider])
    reg = _loop(None)
    # El modelo pide una tool en la 1ª iteración (fuerza 2ª iteración), luego termina.
    from agentic_runtime.events import ToolCallEvent
    caller_events_first = ToolCallEvent(call_id="c1", tool_name="echo", tool_input={})
    class TwoTurnCaller:
        def __init__(self):
            self.n = 0
        async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
            self.n += 1
            n = self.n
            async def _gen():
                if n == 1:
                    yield caller_events_first
                    yield DoneEvent(stop_reason="tool_use")
                else:
                    yield DoneEvent(stop_reason="stop")
            return _gen()

    loop = AgentLoop(
        model_caller=TwoTurnCaller(), tool_registry=reg,
        capability_manager=manager, tool_dispatcher=ToolDispatcher(),
    )
    ctx = ToolUseContext(session_id="s1", app_state=AppState(permissions=PermissionContext()))
    await loop.run("hola", ctx)

    reminders = [m for m in ctx.messages if m.get("role") == "user"
                 and "now available via ToolSearch" in (m.get("content") or "")]
    assert len(reminders) == 1, "no debe re-anunciarse en la 2ª iteración"
