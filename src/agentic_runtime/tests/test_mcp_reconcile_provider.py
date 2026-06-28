"""Tests de integración: provider cableado al store scope-aware + reconcile + watcher.

Cubre los vectores de recarga dinámica:
- Vector 1 (mutación in-process): register/remove/toggle persisten en el scope y
  convergen el estado vivo.
- Vector 2 (fuente externa): un watcher inyectado dispara `reconcile()`, que converge
  el estado vivo a la fuente sin reiniciar.
Más el gate de mutabilidad (managed no removible/toggleable) y la exclusividad en vivo.
"""
from agentic_runtime.capabilities.mcp import (
    McpProvider,
    McpScope,
    McpServerConfig,
    ScopedMcpConfigStore,
    ServerStatus,
)
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


class _FakeClient:
    def __init__(self, config: McpServerConfig) -> None:
        self.config = config
        self.closed = False

    async def connect(self): ...
    async def list_tools(self): return [{"name": f"{self.config.name}_t"}]
    async def list_resources(self): return []
    async def call(self, n, i): return "ok"
    async def aclose(self): self.closed = True


class _FakeProducer:
    """Productor en memoria mutable (simula la fuente externa: MinIO/archivo)."""

    def __init__(self, data: dict | None = None) -> None:
        self.data: dict[str, dict] = dict(data or {})

    async def load(self) -> dict[str, dict]:
        return dict(self.data)

    async def save(self, name: str, raw: dict) -> None:
        self.data[name] = raw

    async def remove(self, name: str) -> None:
        self.data.pop(name, None)


class _FakeWatcher:
    """Watcher inyectable: guarda el callback para que el test lo dispare."""

    def __init__(self) -> None:
        self.on_change = None
        self.stopped = False

    async def start(self, on_change) -> None:
        self.on_change = on_change

    async def stop(self) -> None:
        self.stopped = True


# ---------------------------------------------------------------------------
# startup con store scope-aware
# ---------------------------------------------------------------------------

async def test_startup_loads_scoped_registry_and_connects_enabled():
    store = ScopedMcpConfigStore({
        McpScope.USER: _FakeProducer({
            "on": {"command": "run"},
            "off": {"command": "run", "enabled": False},
        }),
    })
    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.startup()

    assert provider.state.status("on") is ServerStatus.CONNECTED
    assert provider.state.status("off") is ServerStatus.CONFIGURED
    assert [t.name for t in provider.tools(_ctx())] == ["on_t"]
    await provider.shutdown()


async def test_managed_present_suppresses_user_servers_live():
    store = ScopedMcpConfigStore({
        McpScope.USER: _FakeProducer({"u": {"command": "run"}}),
        McpScope.MANAGED: _FakeProducer({"m": {"command": "run"}}),
    })
    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.startup()

    assert provider.state.connected_servers() == ["m"]
    assert "u" not in provider.state.servers  # exclusividad aplicada en el merge
    await provider.shutdown()


# ---------------------------------------------------------------------------
# Vector 2 — reconcile contra fuente externa
# ---------------------------------------------------------------------------

async def test_reconcile_connects_externally_added_server():
    producer = _FakeProducer()
    store = ScopedMcpConfigStore({McpScope.USER: producer})
    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.startup()
    assert provider.state.connected_servers() == []

    producer.data["new"] = {"command": "run"}  # cambio externo de la fuente
    plan = await provider.reconcile()

    assert plan.to_connect == ("new",)
    assert provider.state.status("new") is ServerStatus.CONNECTED
    await provider.shutdown()


async def test_reconcile_disconnects_externally_removed_server():
    producer = _FakeProducer({"gone": {"command": "run"}})
    store = ScopedMcpConfigStore({McpScope.USER: producer})
    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.startup()
    assert provider.state.connected_servers() == ["gone"]

    del producer.data["gone"]  # desaparece de la fuente
    plan = await provider.reconcile()

    assert plan.to_disconnect == ("gone",)
    assert "gone" not in provider.state.servers
    await provider.shutdown()


# ---------------------------------------------------------------------------
# watcher inyectable
# ---------------------------------------------------------------------------

async def test_watcher_started_on_startup_and_drives_reconcile():
    producer = _FakeProducer()
    store = ScopedMcpConfigStore({McpScope.USER: producer})
    watcher = _FakeWatcher()
    provider = McpProvider(
        config_store=store, client_factory=_FakeClient, config_watcher=watcher
    )
    await provider.startup()
    assert watcher.on_change is not None  # el provider lo arrancó con su callback

    producer.data["w"] = {"command": "run"}
    await watcher.on_change()  # el integrador dispararía esto al detectar el cambio

    assert provider.state.status("w") is ServerStatus.CONNECTED
    await provider.shutdown()
    assert watcher.stopped is True


# ---------------------------------------------------------------------------
# gate de mutabilidad a nivel provider
# ---------------------------------------------------------------------------

async def test_managed_server_not_removable():
    store = ScopedMcpConfigStore({
        McpScope.MANAGED: _FakeProducer({"m": {"command": "run"}}),
    })
    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.startup()

    try:
        await provider.remove_server("m")
        assert False, "remove de un server managed debería fallar"
    except ValueError:
        pass
    assert "m" in provider.state.servers  # sigue vivo, gate lo protegió
    await provider.shutdown()


async def test_managed_server_not_toggleable():
    store = ScopedMcpConfigStore({
        McpScope.MANAGED: _FakeProducer({"m": {"command": "run"}}),
    })
    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.startup()

    try:
        await provider.set_server_enabled("m", False)
        assert False, "toggle de un server managed debería fallar"
    except ValueError:
        pass
    assert provider.state.status("m") is ServerStatus.CONNECTED
    await provider.shutdown()


async def test_register_server_defaults_to_user_scope():
    user = _FakeProducer()
    store = ScopedMcpConfigStore({McpScope.USER: user})
    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.register_server("local", {"command": "run"})
    assert "local" in user.data  # persistió en el productor user
