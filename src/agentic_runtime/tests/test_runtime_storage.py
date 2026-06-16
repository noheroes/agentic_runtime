"""Tests para runtime/storage/ — StorageProtocol, FilesystemStorage, StorageRegistry."""
import pytest

from agentic_runtime.storage import StorageProtocol, StorageKeys, StorageRegistry
from agentic_runtime.storage.filesystem import FilesystemStorage


# ---------------------------------------------------------------------------
# FilesystemStorage roundtrip
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_filesystem_upload_download_roundtrip(tmp_path):
    store = FilesystemStorage(root=tmp_path)
    await store.upload("a/b/c.txt", b"hello")
    data = await store.download("a/b/c.txt")
    assert data == b"hello"


@pytest.mark.asyncio
async def test_filesystem_exists_false_before_upload(tmp_path):
    store = FilesystemStorage(root=tmp_path)
    assert await store.exists("not/here.txt") is False


@pytest.mark.asyncio
async def test_filesystem_exists_true_after_upload(tmp_path):
    store = FilesystemStorage(root=tmp_path)
    await store.upload("f.bin", b"\x00")
    assert await store.exists("f.bin") is True


@pytest.mark.asyncio
async def test_filesystem_delete_removes_file(tmp_path):
    store = FilesystemStorage(root=tmp_path)
    await store.upload("del.txt", b"x")
    result = await store.delete("del.txt")
    assert result is True
    assert await store.exists("del.txt") is False


@pytest.mark.asyncio
async def test_filesystem_list_prefix(tmp_path):
    store = FilesystemStorage(root=tmp_path)
    await store.upload("users/u1/a.txt", b"1")
    await store.upload("users/u1/b.txt", b"2")
    await store.upload("users/u2/c.txt", b"3")
    keys = await store.list_prefix("users/u1/")
    assert sorted(keys) == ["users/u1/a.txt", "users/u1/b.txt"]


@pytest.mark.asyncio
async def test_filesystem_copy_does_not_reupload(tmp_path, monkeypatch):
    store = FilesystemStorage(root=tmp_path)
    await store.upload("src.txt", b"payload")

    upload_calls = []
    original_upload = store.upload

    async def tracked_upload(key, data, *a, **kw):
        upload_calls.append(key)
        return await original_upload(key, data, *a, **kw)

    monkeypatch.setattr(store, "upload", tracked_upload)
    await store.copy("src.txt", "dst.txt")

    assert upload_calls == [], "copy no debe llamar upload"
    data = await store.download("dst.txt")
    assert data == b"payload"


@pytest.mark.asyncio
async def test_filesystem_path_traversal_rejected(tmp_path):
    store = FilesystemStorage(root=tmp_path)
    with pytest.raises(ValueError):
        await store.upload("../escape.txt", b"bad")


# ---------------------------------------------------------------------------
# StorageRegistry factory
# ---------------------------------------------------------------------------

def test_create_storage_returns_fresh_instance(tmp_path):
    a = StorageRegistry.create("filesystem", root=tmp_path)
    b = StorageRegistry.create("filesystem", root=tmp_path)
    assert a is not b


def test_create_storage_unknown_backend_raises():
    with pytest.raises(KeyError):
        StorageRegistry.create("nonexistent_backend")


def test_registry_register_custom_backend(tmp_path):
    class DummyStorage:
        def __init__(self, **cfg):
            self.cfg = cfg

    StorageRegistry.register("dummy", DummyStorage)
    instance = StorageRegistry.create("dummy", x=1)
    assert isinstance(instance, DummyStorage)
    assert instance.cfg == {"x": 1}


# ---------------------------------------------------------------------------
# StorageKeys
# ---------------------------------------------------------------------------

def test_storage_keys_main_transcript_at_session_root():
    assert StorageKeys.transcript_key("u1", "s1") == "u1/s1/session.json"
    assert StorageKeys.transcript_key("u1", "s1", "main") == "u1/s1/session.json"


def test_storage_keys_subagent_nested_subtree():
    assert StorageKeys.transcript_key("u1", "s1", "a1") == "u1/s1/subagents/a1/session.json"
    assert StorageKeys.work_key("u1", "s1", "out.csv", "a1") == "u1/s1/subagents/a1/work/out.csv"


def test_storage_keys_two_planes_distinct():
    """Conversación (transcript + sidecar meta) vs artefactos (work/) en claves distintas."""
    transcript = StorageKeys.transcript_key("u1", "s1")
    meta = StorageKeys.meta_key("u1", "s1")
    work = StorageKeys.work_key("u1", "s1", "report.xlsx")
    assert transcript == "u1/s1/session.json"
    assert meta == "u1/s1/session.meta.json"  # sidecar mutable (is_backgrounded)
    assert work == "u1/s1/work/report.xlsx"
    assert len({transcript, meta, work}) == 3
    assert "/work/" in work and "/work/" not in transcript and "/work/" not in meta


def test_storage_keys_config_scope_user():
    assert StorageKeys.config_key("u1") == "u1/config.json"
    assert StorageKeys.agent_md_key("u1") == "u1/agent.md"
    assert StorageKeys.ltm_key("u1") == "u1/ltm/memories.json"


# ---------------------------------------------------------------------------
# Structural protocol check (runtime_checkable)
# ---------------------------------------------------------------------------

def test_filesystem_satisfies_storage_protocol(tmp_path):
    store = FilesystemStorage(root=tmp_path)
    assert isinstance(store, StorageProtocol)
