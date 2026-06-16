from __future__ import annotations

from typing import Any, Type

from .filesystem import FilesystemStorage
from .protocol import StorageProtocol


class StorageRegistry:
    """
    Registry de backends de storage.

    Extensión: proyectos llaman `StorageRegistry.register("s3", MyS3Backend)`
    y luego `StorageRegistry.create("s3", bucket="...")` sin modificar el runtime.
    """

    _backends: dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, backend_cls: Type) -> None:
        cls._backends[name] = backend_cls

    @classmethod
    def create(cls, backend: str, **cfg: Any) -> StorageProtocol:
        """Retorna una instancia fresca cada vez — no es singleton."""
        backend_cls = cls._backends.get(backend)
        if backend_cls is None:
            raise KeyError(f"storage backend '{backend}' no registrado")
        return backend_cls(**cfg)


# Registrar el backend nativo
StorageRegistry.register("filesystem", FilesystemStorage)
