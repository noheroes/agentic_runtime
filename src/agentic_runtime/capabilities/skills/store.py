from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ...storage.protocol import StorageProtocol

logger = logging.getLogger(__name__)


@runtime_checkable
class SkillStore(Protocol):
    """Puerto de persistencia de skills — dónde se registra y dónde se escribe el `SKILL.md`.

    Responsabilidad de quien integra el runtime: el runtime define el contrato; el
    integrador provee la implementación (o usa el default `StorageBackedSkillStore`).
    Registrar un skill = `write(name, contenido)`. El catálogo se deriva del store.
    El runtime lo lee al arrancar para encontrar los skills registrados.
    """

    async def list(self) -> list[str]: ...                 # nombres de skills
    async def read(self, name: str) -> str | None: ...     # contenido SKILL.md
    async def write(self, name: str, content: str) -> None: ...
    async def remove(self, name: str) -> None: ...


class StorageBackedSkillStore:
    """Default sobre `StorageProtocol` — cada skill en `<prefix>/<name>/SKILL.md`.

    Simétrico al store de MCP y a `StorageBackedTokenStorage`: default usable, inyectable."""

    _SUFFIX = "/SKILL.md"

    def __init__(self, storage: "StorageProtocol", *, prefix: str = "skills") -> None:
        self._storage = storage
        self._prefix = prefix.rstrip("/")

    def _key(self, name: str) -> str:
        return f"{self._prefix}/{name}{self._SUFFIX}"

    async def list(self) -> list[str]:
        try:
            keys = await self._storage.list_prefix(f"{self._prefix}/")
        except Exception as exc:  # noqa: BLE001
            logger.warning("skill store: no se pudo listar %s: %s", self._prefix, exc)
            return []
        names: list[str] = []
        for key in keys:
            if key.endswith(self._SUFFIX):
                names.append(key[len(self._prefix) + 1 : -len(self._SUFFIX)])
        return sorted(names)

    async def read(self, name: str) -> str | None:
        key = self._key(name)
        try:
            if not await self._storage.exists(key):
                return None
            return (await self._storage.download(key)).decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.warning("skill store: no se pudo leer %s: %s", key, exc)
            return None

    async def write(self, name: str, content: str) -> None:
        await self._storage.upload(self._key(name), content.encode("utf-8"), "text/markdown")

    async def remove(self, name: str) -> None:
        await self._storage.delete(self._key(name))


__all__ = ["SkillStore", "StorageBackedSkillStore"]
