"""Tests de los puertos de persistencia de capabilities (registro MCP + skills).

El runtime define el contrato; quien integra decide dónde se guarda (default sobre
StorageProtocol, inyectable). El runtime lee el store al arrancar (provider.startup).
"""
from agentic_runtime.capabilities.mcp import (
    McpProvider,
    StorageBackedMcpConfigStore,
)
from agentic_runtime.capabilities.skills import (
    SkillsProvider,
    StorageBackedSkillStore,
)
from agentic_runtime.context.tool_use import ToolUseContext


class _FakeStorage:
    def __init__(self):
        self._data: dict[str, bytes] = {}

    async def upload(self, key, data, content_type="application/octet-stream"):
        self._data[key] = data
        return key

    async def download(self, key):
        return self._data[key]

    async def exists(self, key):
        return key in self._data

    async def delete(self, key):
        return self._data.pop(key, None) is not None

    async def presign(self, key, ttl_seconds=3600):
        return key

    async def list_prefix(self, prefix):
        return [k for k in self._data if k.startswith(prefix)]


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


def _skill_md(name: str) -> str:
    return f"---\nname: {name}\ndescription: d {name}\nallowed-tools: echo_upper\n---\nUsa {name}."


# ---------------------------------------------------------------------------
# MCP config store
# ---------------------------------------------------------------------------

async def test_mcp_config_store_roundtrip():
    store = StorageBackedMcpConfigStore(_FakeStorage())
    assert await store.load() == {}

    await store.save("wiki", {"type": "http", "url": "https://x", "auth": "bearer", "token": "t"})
    await store.save("local", {"type": "stdio", "command": "run"})
    loaded = await store.load()
    assert set(loaded) == {"wiki", "local"}
    assert loaded["wiki"]["auth"] == "bearer"

    await store.remove("wiki")
    assert set(await store.load()) == {"local"}


async def test_provider_loads_registered_servers_from_store_on_startup():
    storage = _FakeStorage()
    store = StorageBackedMcpConfigStore(storage)
    # el integrador ya extrajo/mapeó su JSON al contrato y lo guardó
    await store.save("wiki", {"type": "http", "url": "https://x", "auth": "bearer", "token": "t"})

    # provider sin client real: factory fake para no conectar de verdad
    class _FakeClient:
        def __init__(self, config):
            self.config = config

        async def connect(self): ...
        async def list_tools(self): return [{"name": "wiki_search"}]
        async def list_resources(self): return []
        async def call(self, n, i): return "ok"
        async def aclose(self): ...

    provider = McpProvider(config_store=store, client_factory=_FakeClient)
    await provider.startup()  # debe ENCONTRAR el server persistido y conectarlo

    assert "wiki" in provider.state.servers
    assert provider.state.status("wiki").value == "connected"
    assert [t.name for t in provider.tools(_ctx())] == ["wiki_search"]
    await provider.shutdown()


async def test_register_server_persists_to_store():
    store = StorageBackedMcpConfigStore(_FakeStorage())
    provider = McpProvider(config_store=store)
    await provider.register_server("local", {"type": "stdio", "command": "run"})
    assert "local" in await store.load()


class _PersistFakeClient:
    def __init__(self, config):
        self.config = config

    async def connect(self): ...
    async def list_tools(self): return [{"name": f"{self.config.name}_t"}]
    async def list_resources(self): return []
    async def call(self, n, i): return "ok"
    async def aclose(self): ...


async def test_remove_server_unpersists_from_store():
    """Borrar un server lo quita del registro persistido (simétrico con register)."""
    store = StorageBackedMcpConfigStore(_FakeStorage())
    provider = McpProvider(config_store=store, client_factory=_PersistFakeClient)
    await provider.register_server("local", {"type": "stdio", "command": "run"})
    assert "local" in await store.load()

    await provider.remove_server("local")
    assert "local" not in await store.load()  # no reaparece en el próximo startup


async def test_startup_skips_disabled_servers():
    """Un server con enabled=False no se conecta en startup y no aporta tools."""
    storage = _FakeStorage()
    store = StorageBackedMcpConfigStore(storage)
    await store.save("on", {"type": "stdio", "command": "run"})
    await store.save("off", {"type": "stdio", "command": "run", "enabled": False})

    provider = McpProvider(config_store=store, client_factory=_PersistFakeClient)
    await provider.startup()

    assert provider.state.status("on").value == "connected"
    assert provider.state.status("off").value == "configured"  # registrado, no conectado
    assert [t.name for t in provider.tools(_ctx())] == ["on_t"]
    await provider.shutdown()


async def test_set_server_enabled_persists_and_survives_restart():
    """Deshabilitar persiste el flag: un nuevo startup respeta el estado deshabilitado."""
    storage = _FakeStorage()
    store = StorageBackedMcpConfigStore(storage)
    provider = McpProvider(config_store=store, client_factory=_PersistFakeClient)
    await provider.register_server("srv", {"type": "stdio", "command": "run"})
    await provider.connect_server("srv")

    connected = await provider.set_server_enabled("srv", False)
    assert connected is False
    assert provider.state.status("srv").value == "configured"
    assert (await store.load())["srv"]["enabled"] is False

    # reinicio: un provider nuevo lee el store y NO conecta el deshabilitado
    fresh = McpProvider(config_store=store, client_factory=_PersistFakeClient)
    await fresh.startup()
    assert fresh.state.status("srv").value == "configured"
    assert fresh.tools(_ctx()) == []

    # re-habilitar reconecta y vuelve a aportar tools
    reconnected = await fresh.set_server_enabled("srv", True)
    assert reconnected is True
    assert [t.name for t in fresh.tools(_ctx())] == ["srv_t"]
    assert (await store.load())["srv"]["enabled"] is True
    await fresh.shutdown()


# ---------------------------------------------------------------------------
# Skill store
# ---------------------------------------------------------------------------

async def test_skill_store_roundtrip_and_list():
    store = StorageBackedSkillStore(_FakeStorage())
    assert await store.list() == []

    await store.write("docx", _skill_md("docx"))
    await store.write("xlsx", _skill_md("xlsx"))
    assert await store.list() == ["docx", "xlsx"]
    assert "Usa docx." in (await store.read("docx"))

    await store.remove("docx")
    assert await store.list() == ["xlsx"]


async def test_skills_provider_loads_from_store_on_startup():
    storage = _FakeStorage()
    store = StorageBackedSkillStore(storage)
    await store.write("docx", _skill_md("docx"))

    provider = SkillsProvider(skill_store=store)
    await provider.startup()  # debe ENCONTRAR el skill persistido

    assert provider.state.get("docx") is not None
    assert "echo_upper" in provider.state.get("docx").allowed_tools
    assert [t.name for t in provider.tools(_ctx())] == ["Skill"]


async def test_register_skill_persists_content():
    store = StorageBackedSkillStore(_FakeStorage())
    provider = SkillsProvider(skill_store=store)
    await provider.register_skill("docx", _skill_md("docx"))
    assert await store.read("docx") is not None
    assert provider.state.get("docx") is not None
