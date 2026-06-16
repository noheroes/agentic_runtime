from __future__ import annotations

from typing import TYPE_CHECKING

from .config import McpServerConfig

if TYPE_CHECKING:
    from ...tools.protocol import ToolProtocol


class McpState:
    """Estado MCP propio — servers, tools y resources, scopeado por server.

    Mantener este estado SEPARADo del registry nativo es el patrón del canónico
    (`appState.mcp.*`): el runtime no registra tools MCP como nativas. En M0 es un
    contenedor; el ciclo de vida de clientes/transporte llega en M1.
    """

    def __init__(self) -> None:
        self._servers: dict[str, McpServerConfig] = {}
        self._tools: dict[str, list["ToolProtocol"]] = {}
        self._resources: dict[str, list[dict]] = {}

    # --- servers ---
    def set_server(self, config: McpServerConfig) -> None:
        self._servers[config.name] = config

    def remove_server(self, name: str) -> None:
        self._servers.pop(name, None)
        self._tools.pop(name, None)
        self._resources.pop(name, None)

    @property
    def servers(self) -> dict[str, McpServerConfig]:
        return dict(self._servers)

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
            result.extend(self._resources.get(server, []))
        return result


__all__ = ["McpState"]
