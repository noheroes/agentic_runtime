from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from ..contracts import CapabilitySummary
from .client import McpClient
from .config import McpServerConfig, load_server_configs, parse_server_config
from .config_store import ScopedMcpConfigStore
from .reconcile import ReconcilePlan, apply_reconcile, plan_reconcile
from .scope import McpScope
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
        config_store: "Any | None" = None,
        config_watcher: "Any | None" = None,
        storage: "Any | None" = None,
        redirect_handler: "Any | None" = None,
        callback_handler: "Any | None" = None,
        user_id: str = "mcp",
    ) -> None:
        self._state = state or McpState()
        # Puerto de persistencia del registro de servers, scope-aware. El integrador
        # registra un productor por scope; un store plano (legacy) se envuelve como el
        # productor del scope `user`. Se lee (mergeado por precedencia) en startup().
        self._scoped: "ScopedMcpConfigStore | None" = self._normalize_store(config_store)
        # Procedencia (scope) resuelta de cada server tras el merge — gobierna el gate
        # de mutabilidad (managed/enterprise no mutables por el usuario).
        self._scope_of: dict[str, McpScope] = {}
        # Watcher de fuente externa (vector 2). Lo arranca startup() con `reconcile`.
        self._watcher = config_watcher
        # Inyección para auth OAuth: storage para TokenStorage por defecto; handlers
        # interactivos los provee QUIEN INTEGRA el runtime (headless no abre navegador).
        self._storage = storage
        self._redirect_handler = redirect_handler
        self._callback_handler = callback_handler
        self._user_id = user_id
        self._client_factory = client_factory or self._default_client

    @staticmethod
    def _normalize_store(config_store: "Any | None") -> "ScopedMcpConfigStore | None":
        """Acepta un store scope-aware o uno plano (legacy → productor del scope user)."""
        if config_store is None:
            return None
        if isinstance(config_store, ScopedMcpConfigStore):
            return config_store
        return ScopedMcpConfigStore.from_flat(config_store, scope=McpScope.USER)

    def _default_client(self, config: McpServerConfig) -> McpClient:
        """Factory por defecto: arma `AuthDeps` para oauth (TokenStorage sobre storage)."""
        from .auth import AuthDeps
        from .token_storage import StorageBackedTokenStorage

        deps = None
        if (config.auth or "").lower().strip() == "oauth":
            token_storage = (
                StorageBackedTokenStorage(self._storage, config.name, user_id=self._user_id)
                if self._storage is not None
                else None
            )
            deps = AuthDeps(
                token_storage=token_storage,
                redirect_handler=self._redirect_handler,
                callback_handler=self._callback_handler,
            )
        return McpClient(config, auth_deps=deps)

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
            except Exception as close_exc:  # noqa: BLE001
                logger.debug("mcp: aclose tras fallo de %r también falló: %s", name, close_exc)
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
        """Desconecta y elimina el server por completo: estado vivo Y registro persistido.

        Simétrico con `register_server` (que persiste): borrar un server lo quita también
        del store, igual que `removeMcpConfig` del canónico borra del archivo de config.
        El gate de mutabilidad se aplica ANTES de tocar el estado vivo: un server managed/
        enterprise no es removible por el usuario (el store lanza `ValueError`)."""
        if self._scoped is not None:
            scope = self._scope_of.get(name, McpScope.USER)
            await self._scoped.remove(scope, name)  # gate: lanza para scopes no mutables
        await self.disconnect_server(name)
        self._state.remove_server(name)
        self._scope_of.pop(name, None)

    async def reconnect_server(self, name: str) -> bool:
        """Reconecta un server (toggle/refresh). El pool se reensambla solo por turno."""
        await self.disconnect_server(name)
        return await self.connect_server(name)

    async def set_server_enabled(self, name: str, enabled: bool) -> bool:
        """Habilita/deshabilita un server y lo deja consistente en estado, persistencia y
        conexión (espejo del toggle del canónico, que escribe la config y reconcilia).

        Persiste el flag (sobrevive a reinicios: `startup()` lo respeta), reconecta si se
        habilita o desconecta si se deshabilita. Devuelve el estado de conexión resultante."""
        config = self._state.servers.get(name)
        if config is None:
            return False
        updated = config.model_copy(update={"enabled": enabled})
        # Persiste primero: el gate de mutabilidad rechaza managed/enterprise antes de
        # alterar el estado vivo (un toggle fallido no deja el server inconsistente).
        if self._scoped is not None:
            scope = self._scope_of.get(name, McpScope.USER)
            await self._scoped.save(scope, name, updated.model_dump(exclude={"name"}))
        self._state.set_server(updated)
        if enabled:
            return await self.reconnect_server(name)
        await self.disconnect_server(name)
        return False

    # --- contrato CapabilityProvider -------------------------------------

    async def startup(self) -> None:
        """Carga el registro persistido (mergeado por scope) y conecta los HABILITADOS.

        Un server deshabilitado (`enabled=False`) no se conecta y no aporta tools (espejo
        de `isMcpServerDisabled` del canónico). Un server caído no aborta el resto. Si hay
        watcher de fuente externa, se arranca con `reconcile` como callback (vector 2)."""
        if self._scoped is not None:
            try:
                merged = await self._scoped.load()  # {name: ScopedConfig} con precedencia
                self._scope_of.update({n: sc.scope for n, sc in merged.items()})
                self.load_servers({n: sc.raw for n, sc in merged.items()})  # tolerante
            except Exception as exc:  # noqa: BLE001
                logger.warning("mcp: no se pudo cargar el registro persistido: %s", exc)
        for name, config in list(self._state.servers.items()):
            if not config.enabled:
                logger.info("mcp: server %r deshabilitado — no se conecta en startup", name)
                continue
            await self.connect_server(name)
        if self._watcher is not None:
            await self._watcher.start(self.reconcile)

    async def reconcile(self) -> ReconcilePlan:
        """Converge el estado vivo al registro deseado de la fuente (vectores 1 y 2).

        Lee el store mergeado, actualiza la procedencia y el registro, y aplica el plan
        diff (connect/disconnect/refresh) sobre los clients. Lo consumen el watcher
        externo y cualquier recarga in-process. Sin store: no-op."""
        if self._scoped is None:
            return ReconcilePlan((), (), ())
        merged = await self._scoped.load()
        desired: dict[str, McpServerConfig] = {}
        for name, scoped in merged.items():
            try:
                desired[name] = parse_server_config(name, scoped.raw)
            except Exception as exc:  # noqa: BLE001 — tolerante: salta inválidos
                logger.warning("mcp: config inválida para %r en reconcile — omitido: %s", name, exc)
        # Snapshot del estado vivo ANTES de mutar el registro.
        live = {
            n: self._state.servers[n]
            for n in self._state.connected_servers()
            if n in self._state.servers
        }
        self._scope_of = {n: merged[n].scope for n in desired}
        for name, config in desired.items():
            self._state.set_server(config)
        plan = plan_reconcile(desired, live)
        await apply_reconcile(plan, self)
        # Los servers que ya no se desean quedaron desconectados por el plan: se sacan
        # del registro para que no reaparezcan.
        for name in list(self._state.servers):
            if name not in desired:
                self._state.remove_server(name)
                self._scope_of.pop(name, None)
        return plan

    async def register_server(
        self, name: str, raw: dict, *, scope: McpScope = McpScope.USER
    ) -> McpServerConfig:
        """Registra un server EN runtime: valida, persiste en el scope (default user) y
        deja listo para conectar. El gate rechaza scopes no mutables (managed/enterprise).
        La config `raw` ya viene en el contrato (el integrador la mapeó)."""
        config = self.add_server(name, raw)  # estricto: valida identidad/seguridad
        if self._scoped is not None:
            await self._scoped.save(scope, name, raw)  # gate de mutabilidad
        self._scope_of[name] = scope
        return config

    async def shutdown(self) -> None:
        if self._watcher is not None:
            try:
                await self._watcher.stop()
            except Exception as exc:  # noqa: BLE001
                logger.warning("mcp: error deteniendo watcher: %s", exc)
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
