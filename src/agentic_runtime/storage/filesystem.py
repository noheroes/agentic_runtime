from __future__ import annotations

import asyncio
import shutil
from pathlib import Path


class FilesystemStorage:
    """Backend de filesystem — implementación nativa del runtime para desarrollo y tests."""

    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    def _path(self, key: str) -> Path:
        p = (self._root / key).resolve()
        if not str(p).startswith(str(self._root)):
            raise ValueError(f"path traversal detected: {key!r}")
        return p

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        p = self._path(key)
        await asyncio.get_event_loop().run_in_executor(None, self._write, p, data)
        return key

    async def download(self, key: str) -> bytes:
        p = self._path(key)
        return await asyncio.get_event_loop().run_in_executor(None, p.read_bytes)

    async def presign(self, key: str, ttl_seconds: int = 3600) -> str:
        return self._path(key).as_uri()

    async def delete(self, key: str) -> bool:
        p = self._path(key)
        if not p.exists():
            return False
        await asyncio.get_event_loop().run_in_executor(None, p.unlink)
        return True

    async def exists(self, key: str) -> bool:
        return self._path(key).exists()

    async def list_prefix(self, prefix: str) -> list[str]:
        base = self._path(prefix)
        if not base.exists():
            return []
        return [
            str(p.relative_to(self._root)).replace("\\", "/")
            for p in base.rglob("*")
            if p.is_file()
        ]

    async def copy(self, src: str, dst: str) -> None:
        """Copia sin pasar por upload/download — usa shutil.copy2 directamente."""
        src_path = self._path(src)
        dst_path = self._path(dst)
        await asyncio.get_event_loop().run_in_executor(None, self._copy, src_path, dst_path)

    # ------------------------------------------------------------------
    # Sync helpers for executor
    # ------------------------------------------------------------------

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    @staticmethod
    def _copy(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
