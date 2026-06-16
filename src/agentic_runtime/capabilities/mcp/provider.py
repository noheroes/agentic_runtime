from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..contracts import CapabilitySummary
from .config import McpServerConfig, load_server_configs, parse_server_config
from .state import McpState
from .tool_adapter import McpCall, build_mcp_tool

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ...tools.protocol import ToolProtocol

logger = logging.getLogger(__name__)


class McpProvider:
    """Primer `CapabilityProvider` concreto — MCP conectado por contrato.

    Quien embebe el runtime registra los servers y conecta el transporte; el
    provider solo mantiene el estado MCP y lo expone por el contrato. El runtime
    no sabe que estas tools vienen de MCP: las recibe vía `CapabilityManager`.

    M0 (shell): estado + catálogo + tools + config robusta. El ciclo de vida de
    clientes (startup/shutdown reales) y el deferred loading llegan en M1/M3.
    """

    name = "mcp"

    def __init__(self, state: McpState | None = None) -> None:
        self._state = state or McpState()

    @property
    def state(self) -> McpState:
        return self._state

    # --- registro (lo usa el integrador) ---------------------------------

    def add_server(self, name: str, raw: dict) -> McpServerConfig:
        """Estricto — borde de seguridad. Lanza si la config es inválida."""
        config = parse_server_config(name, raw)
        self._state.set_server(config)
        return config

    def load_servers(self, raw: dict[str, dict]) -> list[McpServerConfig]:
        """Tolerante — aislamiento por ítem. Un server inválido se salta con log."""
        configs = load_server_configs(raw)
        for config in configs:
            self._state.set_server(config)
        return configs

    def register_tools_from_specs(
        self,
        server_name: str,
        specs: list[dict],
        call: McpCall,
    ) -> None:
        """Adapta specs crudos de un server a tools tolerantes (omite las malformadas)."""
        config = self._state.servers.get(server_name)
        timeout = (config.timeout_seconds if config and config.timeout_seconds else 30.0)
        tools: list["ToolProtocol"] = []
        for spec in specs:
            tool = build_mcp_tool(spec, call, timeout_seconds=timeout, server_name=server_name)
            if tool is not None:
                tools.append(tool)
        self._state.set_tools(server_name, tools)

    def register_resources(self, server_name: str, resources: list[dict]) -> None:
        self._state.set_resources(server_name, resources)

    # --- contrato CapabilityProvider -------------------------------------

    async def startup(self) -> None:
        # El ciclo de vida del transporte/cliente es M1; el shell no abre conexiones.
        return None

    async def shutdown(self) -> None:
        return None

    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]:
        # Deferred loading (qué tools exponer según contexto) es M3.
        return self._state.all_tools()

    def catalog(self, context: "ToolUseContext") -> list[CapabilitySummary]:
        return [
            CapabilitySummary(
                name=tool.name,
                kind="mcp_tool",
                description=getattr(tool, "description", ""),
                provider=self.name,
            )
            for tool in self._state.all_tools()
        ]

    def resources(self, context: "ToolUseContext") -> list[dict]:
        return self._state.all_resources()

    def active_context(self, context: "ToolUseContext") -> list[dict]:
        return []

    def compact_context(self, context: "ToolUseContext") -> list[dict]:
        return []


__all__ = ["McpProvider"]
