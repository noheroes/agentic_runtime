from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, model_validator

logger = logging.getLogger(__name__)


class McpServerConfig(BaseModel):
    """Config de un server MCP — schema abierto, estricta en identidad.

    Robustez ante terceros (ver plan §"Robustez Ante Skills/MCP De Terceros"):
    - `extra="allow"`: props operativas que NO son del estándar MCP (p.ej. props
      propias de un registro de terceros) se conservan sin romper el parseo.
    - identidad/transporte (`command` xor `url`) es un borde de seguridad: se valida
      y se RECHAZA si es inválida. La tolerancia es para lo operativo, no para esto.
    """

    model_config = ConfigDict(extra="allow")

    name: str
    # Transporte stdio
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] = {}
    # Transporte http/sse
    url: str | None = None
    headers: dict[str, str] = {}
    # Operativo (opcional, con default — no del estándar MCP)
    timeout_seconds: float | None = None
    model: str | None = None

    @model_validator(mode="after")
    def _exactly_one_transport(self) -> "McpServerConfig":
        has_command = bool(self.command)
        has_url = bool(self.url)
        if has_command == has_url:  # ambos o ninguno
            raise ValueError(
                f"MCP server {self.name!r}: debe especificar exactamente uno de "
                f"'command' (stdio) o 'url' (http/sse)"
            )
        return self


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
