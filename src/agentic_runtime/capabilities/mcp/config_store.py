from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol, runtime_checkable

from .scope import McpScope, ScopedConfig, assert_mutable, merge_scoped

if TYPE_CHECKING:
    from ...storage.protocol import StorageProtocol

logger = logging.getLogger(__name__)


@runtime_checkable
class McpConfigStore(Protocol):
    """Puerto de persistencia del REGISTRO de servers MCP.

    Dónde se guarda la config al registrar un server es responsabilidad de quien
    integra el runtime: el runtime define este contrato; el integrador provee la
    implementación (o usa el default `StorageBackedMcpConfigStore`). El runtime lo
    lee al arrancar para encontrar los servers registrados.
    """

    async def load(self) -> dict[str, dict]: ...           # name -> raw server config
    async def save(self, name: str, raw: dict) -> None: ...
    async def remove(self, name: str) -> None: ...


class StorageBackedMcpConfigStore:
    """Default sobre `StorageProtocol` — registro como un JSON `{name: raw_config}`.

    Mismo patrón que `StorageBackedTokenStorage`: el runtime ofrece un default usable;
    el integrador puede inyectar el suyo (DB, archivo propio, etc.)."""

    def __init__(self, storage: "StorageProtocol", *, key: str = "mcp/servers.json") -> None:
        self._storage = storage
        self._key = key

    async def load(self) -> dict[str, dict]:
        try:
            if not await self._storage.exists(self._key):
                return {}
            raw = await self._storage.download(self._key)
            data = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("mcp config store: no se pudo leer %s: %s", self._key, exc)
            return {}
        return data if isinstance(data, dict) else {}

    async def _write(self, data: dict[str, dict]) -> None:
        await self._storage.upload(self._key, json.dumps(data).encode(), "application/json")

    async def save(self, name: str, raw: dict) -> None:
        data = await self.load()
        data[name] = raw
        await self._write(data)

    async def remove(self, name: str) -> None:
        data = await self.load()
        if data.pop(name, None) is not None:
            await self._write(data)


class ScopedMcpConfigStore:
    """Registro scope-aware: un productor (`McpConfigStore`) por scope.

    El runtime provee la maquinaria (merge por precedencia, gate de mutabilidad,
    aislamiento por productor); el integrador registra QUÉ scopes usa y con qué
    productor (agent_core: managed←plataforma, user←MinIO, dynamic←en-sesión).
    Homologado a `getMcpConfigsByScope`/`addMcpServerToScope` del canónico."""

    def __init__(
        self, producers: "dict[McpScope, McpConfigStore] | None" = None
    ) -> None:
        self._producers: dict[McpScope, McpConfigStore] = dict(producers or {})

    @classmethod
    def from_flat(
        cls, store: "McpConfigStore", *, scope: McpScope = McpScope.USER
    ) -> "ScopedMcpConfigStore":
        """Envuelve un store plano (legacy) como el productor de un único scope."""
        return cls({scope: store})

    def set_producer(self, scope: McpScope, store: "McpConfigStore") -> None:
        self._producers[scope] = store

    @property
    def scopes(self) -> set[McpScope]:
        return set(self._producers)

    def _producer(self, scope: McpScope) -> "McpConfigStore":
        store = self._producers.get(scope)
        if store is None:
            raise ValueError(f"no hay productor registrado para scope {scope.value!r}")
        return store

    async def load_scoped(self) -> dict[McpScope, dict[str, dict]]:
        """Carga cada productor de forma aislada (uno caído no tumba al resto)."""
        result: dict[McpScope, dict[str, dict]] = {}
        for scope, store in self._producers.items():
            try:
                result[scope] = await store.load()
            except Exception as exc:  # noqa: BLE001 — aislamiento por productor
                logger.warning(
                    "mcp scoped store: productor %r falló al cargar — aislado: %s",
                    scope.value, exc,
                )
                result[scope] = {}
        return result

    async def load(self) -> dict[str, ScopedConfig]:
        """Vista mergeada por nombre con precedencia/exclusividad."""
        return merge_scoped(await self.load_scoped())

    async def save(self, scope: McpScope, name: str, raw: dict) -> None:
        """Persiste en el productor del scope. Gate: solo scopes mutables."""
        assert_mutable(scope)
        await self._producer(scope).save(name, raw)

    async def remove(self, scope: McpScope, name: str) -> None:
        """Borra del productor del scope. Gate: solo scopes mutables."""
        assert_mutable(scope)
        await self._producer(scope).remove(name)


@runtime_checkable
class McpConfigWatcher(Protocol):
    """Puerto de detección de cambios EXTERNOS en la fuente de config (vector 2).

    El runtime provee el motor de reconciliación; el integrador provee el watcher
    concreto (agent_core: poll/evento MinIO; agentic_code: inotify del dir local,
    como `skillChangeDetector`). El provider lo arranca en `startup()` con su
    callback `reconcile` y lo apaga en `shutdown()`."""

    async def start(self, on_change: "Callable[[], Awaitable[Any]]") -> None: ...
    async def stop(self) -> None: ...


__all__ = [
    "McpConfigStore",
    "McpConfigWatcher",
    "ScopedMcpConfigStore",
    "StorageBackedMcpConfigStore",
]
