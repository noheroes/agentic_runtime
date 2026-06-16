from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from ..contracts import CapabilitySummary
from .client import McpClient
from .config import McpServerConfig, load_server_configs, parse_server_config
from .state import McpState, ServerStatus
from .tool_adapter import McpCall, build_mcp_tool

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ...tools.protocol import ToolProtocol

logger = logging.getLogger(__name__)


class McpProvider:
    """Primer `CapabilityProvider` concreto — MCP conectado por contrato.

    Quien embebe el runtime registra los servers; el provider abre los clients,
    descubre tools/resources y los expone por el contrato. El runtime no sabe que
    estas tools vienen de MCP: las recibe vía `CapabilityManager`.

    M0: estado + catálogo + tools + config robusta. M1: ciclo de vida real de
    clients (`startup`/`shutdown`, transporte stdio/http vía el SDK `mcp`),
    descubrimiento de tools/resources y estado de conexión (pending/failed/connected).
    El deferred loading (qué tools exponer según contexto) llega en M3.

    El transporte puede inyectarse para tests (`client_factory`); por defecto crea
    `McpClient` reales sobre el SDK `mcp`.
    """

    name = "mcp"

    def __init__(
        self,
        state: McpState | None = None,
        *,
        client_factory: "Callable[[McpServerConfig], McpClient] | None" = None,
    ) -> None:
        self._state = state or McpState()
        self._client_factory = client_factory or McpClient

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

    # --- ciclo de vida de clients (M1) -----------------------------------

    async def connect_server(self, name: str) -> bool:
        """Conecta un server, descubre tools/resources y los registra. Aísla fallos.

        Devuelve True si conectó. Un fallo se marca FAILED con el error y NO se
        propaga: el resto de servers sigue operando (aislamiento por ítem).
        """
        config = self._state.servers.get(name)
        if config is None:
            logger.warning("mcp: connect_server(%r) — server no registrado", name)
            return False

        self._state.set_status(name, ServerStatus.PENDING)
        client = self._client_factory(config)
        try:
            await client.connect()
            tool_specs = await client.list_tools()
            resources = await client.list_resources()
        except Exception as exc:  # noqa: BLE001 — aislamiento por ítem
            logger.warning("mcp: server %r falló al conectar — aislado: %s", name, exc)
            self._state.set_status(name, ServerStatus.FAILED, error=str(exc))
            try:
                await client.aclose()
            except Exception:  # noqa: BLE001
                pass
            return False

        self._state.set_client(name, client)
        self.register_tools_from_specs(name, tool_specs, client.call)
        self._state.set_resources(name, resources)
        self._state.set_status(name, ServerStatus.CONNECTED)
        return True

    # --- gestión en runtime (M5: la capa "service" que una API /mcp llamaría) ---

    async def disconnect_server(self, name: str) -> None:
        """Cierra el client de un server pero conserva su config (queda CONFIGURED)."""
        client = self._state.get_client(name)
        if client is not None:
            try:
                await client.aclose()
            except Exception as exc:  # noqa: BLE001
                logger.warning("mcp: error cerrando client %r: %s", name, exc)
        self._state.remove_client(name)
        self._state.set_tools(name, [])
        self._state.set_resources(name, [])
        if name in self._state.servers:
            self._state.set_status(name, ServerStatus.CONFIGURED)

    async def remove_server(self, name: str) -> None:
        """Desconecta y elimina el server por completo (config incluida)."""
        await self.disconnect_server(name)
        self._state.remove_server(name)

    async def reconnect_server(self, name: str) -> bool:
        """Reconecta un server (toggle/refresh). El pool se reensambla solo por turno."""
        await self.disconnect_server(name)
        return await self.connect_server(name)

    # --- contrato CapabilityProvider -------------------------------------

    async def startup(self) -> None:
        """Conecta todos los servers registrados. Un server caído no aborta el resto."""
        for name in list(self._state.servers):
            await self.connect_server(name)

    async def shutdown(self) -> None:
        for name, client in self._state.clients.items():
            try:
                await client.aclose()
            except Exception as exc:  # noqa: BLE001
                logger.warning("mcp: error cerrando client %r: %s", name, exc)

    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]:
        tools: list["ToolProtocol"] = list(self._state.all_tools())
        # M4: tools de acceso a resources, expuestas solo si hay resources descubiertos
        # (espejo del canónico, que añade las special tools condicionalmente).
        if self._state.all_resources():
            from .resource_tools import ListMcpResourcesTool, ReadMcpResourceTool

            tools.append(ListMcpResourcesTool(self._state))
            tools.append(ReadMcpResourceTool(self._state))
        return tools

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
