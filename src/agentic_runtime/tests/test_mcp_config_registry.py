"""Tests del store de config MCP scope-aware multi-productor (`ScopedMcpConfigStore`).

El runtime orquesta un productor por scope (cada uno un `McpConfigStore` plano),
mergea por precedencia y enruta las mutaciones al productor del scope, con gate de
mutabilidad. Homologado a `getMcpConfigsByScope`/`addMcpServerToScope` del canónico.
"""
import pytest

from agentic_runtime.capabilities.mcp.config_store import (
    ScopedMcpConfigStore,
    StorageBackedMcpConfigStore,
)
from agentic_runtime.capabilities.mcp.scope import McpScope, ScopedConfig


class _FakeProducer:
    """Productor en memoria que satisface el contrato `McpConfigStore`."""

    def __init__(self, data: dict | None = None, *, fail_load: bool = False) -> None:
        self.data: dict[str, dict] = dict(data or {})
        self._fail_load = fail_load

    async def load(self) -> dict[str, dict]:
        if self._fail_load:
            raise RuntimeError("boom")
        return dict(self.data)

    async def save(self, name: str, raw: dict) -> None:
        self.data[name] = raw

    async def remove(self, name: str) -> None:
        self.data.pop(name, None)


pytestmark = pytest.mark.asyncio


async def test_set_producer_and_scopes():
    store = ScopedMcpConfigStore()
    p = _FakeProducer()
    store.set_producer(McpScope.USER, p)
    assert store.scopes == {McpScope.USER}


async def test_load_scoped_returns_per_scope_dicts():
    store = ScopedMcpConfigStore({
        McpScope.USER: _FakeProducer({"a": {"url": "https://a"}}),
        McpScope.MANAGED: _FakeProducer({"m": {"url": "https://m"}}),
    })
    scoped = await store.load_scoped()
    assert scoped[McpScope.USER] == {"a": {"url": "https://a"}}
    assert scoped[McpScope.MANAGED] == {"m": {"url": "https://m"}}


async def test_load_merges_by_precedence():
    store = ScopedMcpConfigStore({
        McpScope.USER: _FakeProducer({"s": {"url": "https://user"}}),
        McpScope.LOCAL: _FakeProducer({"s": {"url": "https://local"}}),
    })
    merged = await store.load()
    assert isinstance(merged["s"], ScopedConfig)
    assert merged["s"].scope is McpScope.LOCAL


async def test_producer_failure_isolated():
    store = ScopedMcpConfigStore({
        McpScope.USER: _FakeProducer({"a": {"url": "https://a"}}),
        McpScope.LOCAL: _FakeProducer(fail_load=True),
    })
    merged = await store.load()
    assert set(merged) == {"a"}  # el productor caído no tumba a los demás


async def test_save_routes_to_scope_producer():
    user = _FakeProducer()
    store = ScopedMcpConfigStore({McpScope.USER: user})
    await store.save(McpScope.USER, "s", {"url": "https://s"})
    assert user.data["s"] == {"url": "https://s"}


async def test_save_to_managed_rejected_and_not_persisted():
    managed = _FakeProducer()
    store = ScopedMcpConfigStore({McpScope.MANAGED: managed})
    with pytest.raises(ValueError):
        await store.save(McpScope.MANAGED, "s", {"url": "https://s"})
    assert managed.data == {}  # gate: no persiste


async def test_remove_routes_to_scope_producer():
    user = _FakeProducer({"s": {"url": "https://s"}})
    store = ScopedMcpConfigStore({McpScope.USER: user})
    await store.remove(McpScope.USER, "s")
    assert "s" not in user.data


async def test_remove_from_non_mutable_rejected():
    managed = _FakeProducer({"s": {"url": "https://s"}})
    store = ScopedMcpConfigStore({McpScope.MANAGED: managed})
    with pytest.raises(ValueError):
        await store.remove(McpScope.MANAGED, "s")
    assert "s" in managed.data


async def test_mutate_scope_without_producer_raises():
    store = ScopedMcpConfigStore()
    with pytest.raises(ValueError):
        await store.save(McpScope.USER, "s", {"url": "https://s"})


async def test_from_flat_wraps_as_user_scope():
    flat = _FakeProducer({"s": {"url": "https://s"}})
    store = ScopedMcpConfigStore.from_flat(flat)
    merged = await store.load()
    assert merged["s"].scope is McpScope.USER


async def test_storage_backed_store_works_as_producer():
    # Retro-compat: el default plano sigue siendo un productor válido.
    class _Storage:
        def __init__(self) -> None:
            self.blobs: dict[str, bytes] = {}

        async def exists(self, key: str) -> bool:
            return key in self.blobs

        async def download(self, key: str) -> bytes:
            return self.blobs[key]

        async def upload(self, key: str, data: bytes, content_type: str) -> None:
            self.blobs[key] = data

    producer = StorageBackedMcpConfigStore(_Storage())
    store = ScopedMcpConfigStore({McpScope.USER: producer})
    await store.save(McpScope.USER, "s", {"url": "https://s"})
    merged = await store.load()
    assert merged["s"].scope is McpScope.USER
    assert merged["s"].raw == {"url": "https://s"}
