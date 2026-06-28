from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, model_validator

logger = logging.getLogger(__name__)

_TRANSPORTS = {"http", "sse", "stdio"}


class McpServerConfig(BaseModel):
    """Config de un server MCP — schema abierto, estricta en identidad/seguridad.

    Robustez ante terceros (ver plan §"Robustez Ante Skills/MCP De Terceros"):
    - `extra="allow"`: props operativas que NO son del estándar MCP (p.ej. props
      propias de un registro de terceros) se conservan sin romper el parseo.
    - identidad/transporte y seguridad son bordes ESTRICTOS: se validan y RECHAZAN.
      La tolerancia es para lo operativo, no para esto.

    Contrato de registro:
    - `type`: transporte explícito (`http`/`sse`/`stdio`). Si se omite, se infiere
      (`command` → stdio; `url` → http) por compatibilidad.
    - `url`: requerido para http/sse. `command`(+`args`/`env`): requerido para stdio.
    - `auth`: esquema de autenticación. `bearer` exige `token` (borde de seguridad).
    - `ssl_verify`: valida o no los certificados TLS (default True = valida).
    """

    model_config = ConfigDict(extra="allow")

    name: str
    type: str | None = None
    # Transporte stdio
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] = {}
    # Transporte http/sse
    url: str | None = None
    headers: dict[str, str] = {}
    # Auth y TLS (seguridad). `auth` nombra un modo extensible (none/bearer/oauth/...).
    auth: str | None = None
    token: str | None = None            # bearer: token estático
    scope: str | None = None            # oauth: scopes solicitados
    client_name: str | None = None      # oauth: nombre de cliente
    redirect_uris: list[str] = []       # oauth: redirect URIs registrados
    ssl_verify: bool = True
    # Operativo (opcional, con default — no del estándar MCP)
    timeout_seconds: float | None = None
    model: str | None = None
    # Enablement: un server deshabilitado no se conecta en `startup()` y no aporta tools
    # (espejo de `disabledMcpServers`/`isMcpServerDisabled` del canónico). Default habilitado.
    enabled: bool = True

    @model_validator(mode="after")
    def _validate_identity_and_auth(self) -> "McpServerConfig":
        kind = (self.type or "").lower().strip() or None
        if kind is not None and kind not in _TRANSPORTS:
            raise ValueError(
                f"MCP server {self.name!r}: 'type' inválido {self.type!r} "
                f"(debe ser uno de {sorted(_TRANSPORTS)})"
            )
        if kind is None:
            # Inferencia retro-compatible: exactamente uno de command/url.
            has_command, has_url = bool(self.command), bool(self.url)
            if has_command == has_url:  # ambos o ninguno → ambiguo
                raise ValueError(
                    f"MCP server {self.name!r}: especifica 'type', o exactamente uno "
                    f"de 'command' (stdio) o 'url' (http/sse)"
                )
        elif kind == "stdio":
            if not self.command:
                raise ValueError(f"MCP server {self.name!r}: type='stdio' requiere 'command'")
        else:  # http / sse
            if not self.url:
                raise ValueError(f"MCP server {self.name!r}: type={kind!r} requiere 'url'")

        # Bearer es borde de seguridad: sin token no se asume anónimo silenciosamente.
        auth = (self.auth or "").lower().strip()
        if auth == "bearer" and not self.token:
            raise ValueError(f"MCP server {self.name!r}: auth='bearer' requiere 'token'")
        # La auth HTTP (bearer/oauth) no aplica a stdio: la spec exige credenciales por
        # entorno para stdio. Evita configuraciones engañosas (borde de seguridad).
        if auth in ("bearer", "oauth") and self.resolved_transport() == "stdio":
            raise ValueError(
                f"MCP server {self.name!r}: auth={auth!r} no aplica a stdio "
                f"(usa variables de entorno en 'env' para credenciales stdio)"
            )
        return self

    def resolved_transport(self) -> str:
        """Transporte efectivo (`http`/`sse`/`stdio`), explícito o inferido."""
        kind = (self.type or "").lower().strip()
        if kind in _TRANSPORTS:
            return kind
        return "stdio" if self.command else "http"

    def auth_headers(self) -> dict[str, str]:
        """Headers de auth combinados con los explícitos (bearer → Authorization)."""
        headers = dict(self.headers)
        if (self.auth or "").lower().strip() == "bearer" and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def parse_server_config(name: str, raw: dict) -> McpServerConfig:
    """Parseo ESTRICTO — borde de seguridad (agregar un server explícitamente).

    Lanza `ValueError` si la config es inválida. Espejo del canónico, que hace
    `safeParse` y lanza al agregar un server (acción explícita del usuario).
    """
    return McpServerConfig(name=name, **raw)


def load_server_configs(raw: dict[str, dict]) -> list[McpServerConfig]:
    """Carga TOLERANTE en bloque — aislamiento por ítem.

    Un server con config inválida se salta con log; los demás cargan. Espejo del
    canónico al leer una lista de configs de archivo.
    """
    configs: list[McpServerConfig] = []
    for name, cfg in raw.items():
        try:
            configs.append(parse_server_config(name, cfg))
        except Exception as exc:
            logger.warning("mcp: config inválida para server %r — omitido: %s", name, exc)
    return configs


__all__ = ["McpServerConfig", "load_server_configs", "parse_server_config"]
