"""Tests del modelo de auth MCP extensible (none/bearer/oauth/...) + TokenStorage.

La auth es mutable: cada modo es una estrategia registrable. bearer = token estático;
oauth = OAuthClientProvider del SDK (full OAuth 2.1) con handlers inyectados por el
integrador y TokenStorage sobre StorageProtocol. stdio no usa auth HTTP (env).
"""
import pytest

from agentic_runtime.capabilities.mcp import (
    AuthArtifacts,
    AuthDeps,
    McpProvider,
    StorageBackedTokenStorage,
    available_auth_strategies,
    build_auth,
    parse_server_config,
    register_auth_strategy,
)


# ---------------------------------------------------------------------------
# Registro y extensibilidad
# ---------------------------------------------------------------------------

def test_builtin_strategies_registered():
    assert {"none", "bearer", "oauth"} <= set(available_auth_strategies())


def test_unknown_auth_mode_raises_on_build():
    cfg = parse_server_config("s", {"type": "http", "url": "https://x", "auth": "weird", "token": "t"})
    with pytest.raises(ValueError):
        build_auth(cfg, server_url="https://x")


def test_register_custom_auth_strategy():
    register_auth_strategy("apikey", lambda c, url, deps: AuthArtifacts(headers={"X-API-Key": c.token or ""}))
    cfg = parse_server_config("s", {"type": "http", "url": "https://x", "auth": "apikey", "token": "k"})
    art = build_auth(cfg, server_url="https://x")
    assert art.headers == {"X-API-Key": "k"}


# ---------------------------------------------------------------------------
# none / bearer
# ---------------------------------------------------------------------------

def test_none_auth_yields_no_headers():
    cfg = parse_server_config("s", {"type": "http", "url": "https://x"})
    art = build_auth(cfg, server_url="https://x")
    assert art.headers == {} and art.httpx_auth is None


def test_bearer_yields_authorization_header():
    cfg = parse_server_config("s", {"type": "http", "url": "https://x", "auth": "bearer", "token": "secret"})
    art = build_auth(cfg, server_url="https://x")
    assert art.headers["Authorization"] == "Bearer secret"
    assert art.httpx_auth is None


# ---------------------------------------------------------------------------
# oauth: wirea el OAuthClientProvider del SDK (httpx.Auth)
# ---------------------------------------------------------------------------

def test_oauth_requires_token_storage():
    cfg = parse_server_config("s", {"type": "http", "url": "https://x", "auth": "oauth"})
    with pytest.raises(ValueError):
        build_auth(cfg, server_url="https://x")  # sin deps.token_storage


def test_oauth_builds_httpx_auth_provider():
    import httpx
    from mcp.client.auth import OAuthClientProvider

    class _MemStore:
        async def get_tokens(self): return None
        async def set_tokens(self, t): pass
        async def get_client_info(self): return None
        async def set_client_info(self, c): pass

    cfg = parse_server_config(
        "s", {"type": "http", "url": "https://x/mcp", "auth": "oauth",
              "scope": "files:read", "client_name": "rt", "redirect_uris": ["http://localhost:9/cb"]},
    )
    art = build_auth(cfg, server_url="https://x/mcp", deps=AuthDeps(token_storage=_MemStore()))
    assert art.httpx_auth is not None
    assert isinstance(art.httpx_auth, OAuthClientProvider)
    assert isinstance(art.httpx_auth, httpx.Auth)


# ---------------------------------------------------------------------------
# Validación: auth HTTP no aplica a stdio (credenciales por env)
# ---------------------------------------------------------------------------

def test_bearer_on_stdio_rejected():
    with pytest.raises(ValueError):
        parse_server_config("s", {"type": "stdio", "command": "run", "auth": "bearer", "token": "t"})


def test_oauth_on_stdio_rejected():
    with pytest.raises(ValueError):
        parse_server_config("s", {"type": "stdio", "command": "run", "auth": "oauth"})


# ---------------------------------------------------------------------------
# TokenStorage sobre StorageProtocol
# ---------------------------------------------------------------------------

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


async def test_token_storage_roundtrip_over_storage_protocol():
    from mcp.shared.auth import OAuthToken

    storage = _FakeStorage()
    ts = StorageBackedTokenStorage(storage, "srv", user_id="u1")

    assert await ts.get_tokens() is None  # vacío → None, sin excepción
    tok = OAuthToken(access_token="abc", token_type="Bearer", refresh_token="r")
    await ts.set_tokens(tok)

    loaded = await ts.get_tokens()
    assert loaded is not None and loaded.access_token == "abc"
    # persistido bajo una clave scopeda por server
    assert any("mcp/srv" in k for k in storage._data)


# ---------------------------------------------------------------------------
# Provider arma AuthDeps con TokenStorage por defecto para oauth
# ---------------------------------------------------------------------------

def test_provider_default_client_builds_token_storage_for_oauth():
    provider = McpProvider(storage=_FakeStorage())
    provider.add_server("srv", {"type": "http", "url": "https://x", "auth": "oauth"})
    client = provider._default_client(provider.state.servers["srv"])
    assert client._auth_deps is not None
    assert isinstance(client._auth_deps.token_storage, StorageBackedTokenStorage)
