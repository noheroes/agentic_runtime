from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .config import McpServerConfig

if TYPE_CHECKING:
    from ...tools.protocol import ToolProtocol
    from .client import McpClient


class ServerStatus(str, Enum):
    """Ciclo de vida de conexión de un server MCP (patrón `appState.mcp` del canónico)."""

    CONFIGURED = "configured"  # registrado, sin intentar conectar
    PENDING = "pending"        # conectando
    CONNECTED = "connected"    # sesión inicializada, tools descubiertas
    FAILED = "failed"          # conexión/inicialización falló (aislado, no tumba al resto)


class McpState:
    """Estado MCP propio — servers, clients, tools, resources y estado de conexión.

    Mantener este estado SEPARADo del registry nativo es el patrón del canónico
    (`appState.mcp.*`): el runtime no registra tools MCP como nativas. Los clients
    viven aquí (no en globals); el provider los gestiona por su ciclo de vida.
    """

    def __init__(self) -> None:
        self._servers: dict[str, McpServerConfig] = {}
        self._clients: dict[str, "McpClient"] = {}
        self._tools: dict[str, list["ToolProtocol"]] = {}
        self._resources: dict[str, list[dict]] = {}
        self._status: dict[str, ServerStatus] = {}
        self._errors: dict[str, str] = {}

    # --- servers ---
    def set_server(self, config: McpServerConfig) -> None:
        self._servers[config.name] = config
        self._status.setdefault(config.name, ServerStatus.CONFIGURED)

    def remove_server(self, name: str) -> None:
        self._servers.pop(name, None)
        self._clients.pop(name, None)
        self._tools.pop(name, None)
        self._resources.pop(name, None)
        self._status.pop(name, None)
        self._errors.pop(name, None)

    @property
    def servers(self) -> dict[str, McpServerConfig]:
        return dict(self._servers)

    # --- clients ---
    def set_client(self, server_name: str, client: "McpClient") -> None:
        self._clients[server_name] = client

    def get_client(self, server_name: str) -> "McpClient | None":
        return self._clients.get(server_name)

    def remove_client(self, server_name: str) -> None:
        self._clients.pop(server_name, None)

    @property
    def clients(self) -> dict[str, "McpClient"]:
        return dict(self._clients)

    # --- estado de conexión ---
    def set_status(self, server_name: str, status: ServerStatus, error: str = "") -> None:
        self._status[server_name] = status
        if status is ServerStatus.FAILED:
            self._errors[server_name] = error
        else:
            self._errors.pop(server_name, None)

    def status(self, server_name: str) -> ServerStatus | None:
        return self._status.get(server_name)

    def pending_servers(self) -> list[str]:
        return [n for n, s in self._status.items() if s is ServerStatus.PENDING]

    def failed_servers(self) -> dict[str, str]:
        return {n: self._errors.get(n, "") for n, s in self._status.items() if s is ServerStatus.FAILED}

    def connected_servers(self) -> list[str]:
        return [n for n, s in self._status.items() if s is ServerStatus.CONNECTED]

    # --- tools ---
    def set_tools(self, server_name: str, tools: list["ToolProtocol"]) -> None:
        self._tools[server_name] = list(tools)

    def all_tools(self) -> list["ToolProtocol"]:
        result: list["ToolProtocol"] = []
        for server in self._servers:  # orden de registro de servers
            result.extend(self._tools.get(server, []))
        return result

    # --- resources ---
    def set_resources(self, server_name: str, resources: list[dict]) -> None:
        self._resources[server_name] = list(resources)

    def all_resources(self) -> list[dict]:
        result: list[dict] = []
        for server in self._servers:
            for resource in self._resources.get(server, []):
                result.append({**resource, "server": server})
        return result

    def find_resource_server(self, uri: str) -> str | None:
        """Server al que pertenece un resource `uri` (para enrutar la lectura)."""
        for server, resources in self._resources.items():
            if any(r.get("uri") == uri for r in resources):
                return server
        return None


__all__ = ["McpState"]
