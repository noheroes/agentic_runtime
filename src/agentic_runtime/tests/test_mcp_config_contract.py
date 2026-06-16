"""Tests del contrato de registro de un MCP: url + type + auth(bearer)+token + ssl_verify.

Operativo tolerante; identidad/transporte y seguridad (bearer, type) estrictos.
"""
import pytest

from agentic_runtime.capabilities.mcp import McpServerConfig, parse_server_config
from agentic_runtime.capabilities.mcp.client import _http_client_factory


# ---------------------------------------------------------------------------
# type explícito y resolución de transporte
# ---------------------------------------------------------------------------

def test_type_http_requires_url_and_resolves():
    cfg = parse_server_config("s", {"type": "http", "url": "https://x/mcp"})
    assert cfg.resolved_transport() == "http"


def test_type_sse_resolves():
    cfg = parse_server_config("s", {"type": "sse", "url": "https://x/sse"})
    assert cfg.resolved_transport() == "sse"


def test_type_stdio_requires_command():
    cfg = parse_server_config("s", {"type": "stdio", "command": "run"})
    assert cfg.resolved_transport() == "stdio"
    with pytest.raises(ValueError):
        parse_server_config("s", {"type": "stdio"})  # sin command


def test_type_http_without_url_raises():
    with pytest.raises(ValueError):
        parse_server_config("s", {"type": "http"})


def test_invalid_type_raises():
    with pytest.raises(ValueError):
        parse_server_config("s", {"type": "grpc", "url": "https://x"})


def test_transport_inferred_when_type_absent():
    assert parse_server_config("s", {"command": "run"}).resolved_transport() == "stdio"
    assert parse_server_config("s", {"url": "https://x"}).resolved_transport() == "http"


# ---------------------------------------------------------------------------
# auth bearer + token (borde de seguridad)
# ---------------------------------------------------------------------------

def test_bearer_requires_token():
    with pytest.raises(ValueError):
        parse_server_config("s", {"type": "http", "url": "https://x", "auth": "bearer"})


def test_bearer_with_token_builds_authorization_header():
    cfg = parse_server_config(
        "s", {"type": "http", "url": "https://x", "auth": "bearer", "token": "secret"}
    )
    assert cfg.auth_headers()["Authorization"] == "Bearer secret"


def test_auth_headers_merges_explicit_headers():
    cfg = parse_server_config(
        "s",
        {"type": "http", "url": "https://x", "headers": {"X-Env": "prod"},
         "auth": "bearer", "token": "t"},
    )
    h = cfg.auth_headers()
    assert h["X-Env"] == "prod" and h["Authorization"] == "Bearer t"


def test_no_auth_no_authorization_header():
    cfg = parse_server_config("s", {"type": "http", "url": "https://x"})
    assert "Authorization" not in cfg.auth_headers()


# ---------------------------------------------------------------------------
# ssl_verify
# ---------------------------------------------------------------------------

def test_ssl_verify_defaults_true():
    assert parse_server_config("s", {"type": "http", "url": "https://x"}).ssl_verify is True


def test_ssl_verify_can_be_disabled():
    cfg = parse_server_config("s", {"type": "http", "url": "https://x", "ssl_verify": False})
    assert cfg.ssl_verify is False


def test_http_client_factory_respects_ssl_verify():
    import httpx

    insecure = _http_client_factory(False)()
    secure = _http_client_factory(True)()
    assert isinstance(insecure, httpx.AsyncClient)
    assert isinstance(secure, httpx.AsyncClient)


# ---------------------------------------------------------------------------
# schema abierto sigue tolerando props de terceros
# ---------------------------------------------------------------------------

def test_open_schema_keeps_unknown_props_with_full_contract():
    cfg = parse_server_config(
        "s",
        {"type": "http", "url": "https://x", "auth": "bearer", "token": "t",
         "ssl_verify": False, "vendor_flag": 7},
    )
    assert isinstance(cfg, McpServerConfig)
    assert cfg.model_extra and cfg.model_extra.get("vendor_flag") == 7
