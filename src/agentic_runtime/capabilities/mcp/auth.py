from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .config import McpServerConfig

# Modos de auth MCP — extensible. La spec (2025-11-25) no es solo bearer: define un
# flujo OAuth 2.1 completo. Aquí cada modo es una ESTRATEGIA registrable; añadir uno
# nuevo no toca el client ni el provider, solo registra un builder.


@dataclass
class AuthArtifacts:
    """Lo que un modo de auth aporta al transporte HTTP del client.

    - `headers`: cabeceras a fusionar (p.ej. `Authorization: Bearer ...`).
    - `httpx_auth`: un `httpx.Auth` (p.ej. el `OAuthClientProvider` del SDK, que hace
      descubrimiento + PKCE + refresh + resource indicator) aplicado en cada request.
    """

    headers: dict[str, str] = field(default_factory=dict)
    httpx_auth: Any | None = None


@dataclass
class AuthDeps:
    """Dependencias que un modo puede requerir, inyectadas por el integrador.

    El runtime es autónomo/headless: no abre navegador. Por eso el handler de
    redirección y el de callback del flujo `authorization_code` se inyectan; el
    `token_storage` persiste tokens (sobre `StorageProtocol` por defecto)."""

    token_storage: Any | None = None       # mcp.client.auth.TokenStorage
    redirect_handler: Any | None = None     # Callable[[str], Awaitable[None]]
    callback_handler: Any | None = None     # Callable[[], Awaitable[tuple[str, str|None]]]


AuthBuilder = Callable[["McpServerConfig", str, AuthDeps], AuthArtifacts]

_STRATEGIES: dict[str, AuthBuilder] = {}


def register_auth_strategy(name: str, builder: AuthBuilder) -> None:
    """Registra (o reemplaza) un modo de auth. Punto de extensión: nuevos modos de
    la spec u otros propietarios se añaden sin tocar client/provider."""
    _STRATEGIES[name.lower().strip()] = builder


def available_auth_strategies() -> list[str]:
    return sorted(_STRATEGIES)


def build_auth(config: "McpServerConfig", *, server_url: str, deps: AuthDeps | None = None) -> AuthArtifacts:
    """Resuelve los artefactos de auth para un server según su modo (`config.auth`)."""
    name = (config.auth or "none").lower().strip() or "none"
    builder = _STRATEGIES.get(name)
    if builder is None:
        raise ValueError(
            f"MCP server {config.name!r}: modo de auth desconocido {config.auth!r} "
            f"(registrados: {available_auth_strategies()})"
        )
    return builder(config, server_url, deps or AuthDeps())


# --- modos integrados --------------------------------------------------------

def _build_none(config: "McpServerConfig", server_url: str, deps: AuthDeps) -> AuthArtifacts:
    return AuthArtifacts()


def _build_bearer(config: "McpServerConfig", server_url: str, deps: AuthDeps) -> AuthArtifacts:
    # Token estático pre-obtenido (caso 'pre-registro/credencial estática' de la spec).
    return AuthArtifacts(headers={"Authorization": f"Bearer {config.token}"})


def _build_oauth(config: "McpServerConfig", server_url: str, deps: AuthDeps) -> AuthArtifacts:
    """OAuth 2.1 completo vía el SDK `mcp` (NO se reimplementa el flujo).

    `OAuthClientProvider` (un `httpx.Auth`) hace descubrimiento (RFC 9728 + RFC 8414/
    OIDC), PKCE S256, DCR/Client ID Metadata, refresh y resource indicator (RFC 8707).
    """
    if deps.token_storage is None:
        raise ValueError(f"MCP server {config.name!r}: auth='oauth' requiere token_storage")

    from mcp.client.auth import OAuthClientProvider
    from mcp.shared.auth import OAuthClientMetadata

    metadata = OAuthClientMetadata(
        client_name=config.client_name or "agentic-runtime",
        redirect_uris=list(config.redirect_uris) or ["http://localhost:8765/callback"],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope=config.scope,
        token_endpoint_auth_method="none",
    )
    provider = OAuthClientProvider(
        server_url=server_url,
        client_metadata=metadata,
        storage=deps.token_storage,
        redirect_handler=deps.redirect_handler,
        callback_handler=deps.callback_handler,
    )
    return AuthArtifacts(httpx_auth=provider)


register_auth_strategy("none", _build_none)
register_auth_strategy("bearer", _build_bearer)
register_auth_strategy("oauth", _build_oauth)


__all__ = [
    "AuthArtifacts",
    "AuthDeps",
    "available_auth_strategies",
    "build_auth",
    "register_auth_strategy",
]
