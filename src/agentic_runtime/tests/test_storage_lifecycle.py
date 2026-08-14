from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from agentic_runtime.contracts.events import DoneEvent, TokenEvent
from agentic_runtime.contracts.identity import Scope
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.factory import RuntimeConfig, StorageConfig, create_runtime
from agentic_runtime.storage import FilesystemStorage, StorageKeys, StorageLifecycle
from agentic_runtime.storage.factory import StorageRegistry

_SCOPE = Scope("lifecycle")
_SESSION = "session-1"


class SilentCaller:
    def supports_native_tool_search(self, model_id: str = "") -> bool:
        return False

    async def complete(self, messages, tools, **kwargs):
        async def events():
            yield TokenEvent(content="listo")
            yield DoneEvent(stop_reason="stop")

        return events()


class SpyStorage:
    instances: list[SpyStorage] = []

    def __init__(self, *, root: Path) -> None:
        self.root = Path(root)
        self.uploads: list[str] = []
        self.teardowns = 0
        SpyStorage.instances.append(self)

    async def upload(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        self.uploads.append(key)
        return key

    async def download(self, key: str) -> bytes:
        return b""

    async def presign(self, key: str, ttl_seconds: int = 3600) -> str:
        return key

    async def delete(self, key: str) -> bool:
        return False

    async def exists(self, key: str) -> bool:
        return False

    async def list_prefix(self, prefix: str) -> list[str]:
        return []

    async def teardown(self) -> None:
        self.teardowns += 1


StorageRegistry.register("spy-lifecycle", SpyStorage)


def _runtime(storage: StorageConfig):
    return create_runtime(
        config=RuntimeConfig(
            model_caller=SilentCaller(),
            model_id="scripted",
            storage=storage,
            scope=_SCOPE,
        )
    )


async def _one_turn(runtime) -> None:
    await runtime.startup()
    task_id = await runtime.dispatch(
        RuntimeTask(prompt="hola", description="turno", session_id=_SESSION)
    )
    await runtime.join(task_id)
    await runtime.shutdown()
    await runtime.shutdown()


def _live_threads(prefix: str) -> list[str]:
    return [t.name for t in threading.enumerate() if t.name.startswith(prefix)]


def test_the_event_loop_closes_after_persisting_a_session(tmp_path: Path) -> None:
    root = tmp_path / "runtime"

    asyncio.run(_one_turn(_runtime(StorageConfig(backend="filesystem", root=root))))

    transcript = root / StorageKeys.transcript_key(_SCOPE, _SESSION)
    assert transcript.exists(), sorted(p.name for p in root.rglob("*"))
    assert _live_threads("asyncio_") == []
    assert _live_threads("agentic-storage") == []


def test_the_runtime_closes_the_storage_it_created(tmp_path: Path) -> None:
    SpyStorage.instances.clear()

    asyncio.run(_one_turn(_runtime(StorageConfig(backend="spy-lifecycle", root=tmp_path))))

    created = SpyStorage.instances[-1]
    assert created.uploads == [StorageKeys.transcript_key(_SCOPE, _SESSION)]
    assert created.teardowns >= 1


def test_the_runtime_does_not_close_an_injected_storage(tmp_path: Path) -> None:
    injected = SpyStorage(root=tmp_path)

    asyncio.run(_one_turn(_runtime(StorageConfig(instance=injected))))

    assert injected.uploads == [StorageKeys.transcript_key(_SCOPE, _SESSION)]
    assert injected.teardowns == 0


def test_the_filesystem_storage_owns_its_executor_and_closes_idempotently(tmp_path: Path) -> None:
    storage = FilesystemStorage(root=tmp_path)
    assert isinstance(storage, StorageLifecycle)

    async def exercise() -> bytes:
        await storage.upload("a/b.json", b"{}")
        payload = await storage.download("a/b.json")
        await storage.teardown()
        await storage.teardown()
        return payload

    assert asyncio.run(exercise()) == b"{}"
    assert _live_threads("asyncio_") == []
    assert _live_threads("agentic-storage") == []


def test_an_injected_executor_survives_the_teardown(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="integrator-pool")
    storage = FilesystemStorage(root=tmp_path, executor=executor)

    async def exercise() -> None:
        await storage.upload("c.json", b"{}")
        await storage.teardown()

    asyncio.run(exercise())
    assert executor.submit(lambda: 7).result() == 7
    executor.shutdown(wait=True)
