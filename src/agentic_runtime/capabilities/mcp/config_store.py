from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Protocol, runtime_checkable

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


__all__ = ["McpConfigStore", "StorageBackedMcpConfigStore"]
