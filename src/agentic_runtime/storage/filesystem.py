from __future__ import annotations

import asyncio
import shutil
from concurrent.futures import Executor, ThreadPoolExecutor
from pathlib import Path


class FilesystemStorage:
    def __init__(self, *, root: Path, executor: Executor | None = None) -> None:
        self._root = root.resolve()
        self._owns_executor = executor is None
        self._executor: Executor | None = executor or ThreadPoolExecutor(
            thread_name_prefix="agentic-storage"
        )

    def _path(self, key: str) -> Path:
        p = (self._root / key).resolve()
        if not str(p).startswith(str(self._root)):
            raise ValueError(f"path traversal detected: {key!r}")
        return p

    def _run(self, fn, *args):
        if self._executor is None:
            raise RuntimeError("FilesystemStorage ya fue cerrado con teardown()")
        return asyncio.get_running_loop().run_in_executor(self._executor, fn, *args)

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        p = self._path(key)
        await self._run(self._write, p, data)
        return key

    async def download(self, key: str) -> bytes:
        p = self._path(key)
        return await self._run(p.read_bytes)

    async def presign(self, key: str, ttl_seconds: int = 3600) -> str:
        return self._path(key).as_uri()

    async def delete(self, key: str) -> bool:
        p = self._path(key)
        if not p.exists():
            return False
        await self._run(p.unlink)
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
        src_path = self._path(src)
        dst_path = self._path(dst)
        await self._run(self._copy, src_path, dst_path)

    async def teardown(self) -> None:
        executor = self._executor
        self._executor = None
        if executor is not None and self._owns_executor:
            executor.shutdown(wait=True)

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    @staticmethod
    def _copy(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
