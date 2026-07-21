"""Homologación 15·storage — `storage/{protocol,filesystem,factory}.py` + los consumidores que
persisten sobre `StorageProtocol` (transcript en `execution/local/runtime.py::_persist`, token/mcp-config/
skills stores) vs la persistencia del canónico, dispersa en `utils/{config,sessionStorage,sessionStoragePortable,
fsOperations,env,envUtils,cachePaths}.ts`, `utils/filePersistence/`, `cli/transports/WorkerStateUploader.ts`.

Los tests que PASAN codifican lo YA homologado: registry pluggable (habilita MinIO), primitivas de blob
(upload/download/exists/delete/list_prefix/presign/copy), la forma de la taxonomía `StorageKeys` de las claves
cableadas, y el rechazo de traversal `..` directo.

Los `xfail(strict=True)` codifican los gaps FIND-STOR1..12 (§Plan StR1-8): fallan HOY (comportamiento/símbolo
ausente) y su fallo ES la evidencia del gap. Si alguno empezara a pasar, el strict lo vuelve error → señal de
reclasificar en `15-storage.md`. Los símbolos-target aún inexistentes se importan/consultan DENTRO de cada test.
"""
from __future__ import annotations

import pytest

from agentic_runtime.storage import (
    FilesystemStorage,
    StorageKeys,
    StorageProtocol,
    StorageRegistry,
)

# ---------------------------------------------------------------------------
# HOMOLOGADO (passing)
# ---------------------------------------------------------------------------


def test_registry_pluggable_backend_fresh_instance(tmp_path):
    """F1: `StorageRegistry.register/create` — extensión pluggable (MinIO) sin tocar el runtime;
    instancia fresca cada vez (no singleton). Homologa el valor-propio sobre el canónico (FS directo)."""

    class DummyBackend:
        def __init__(self, **cfg):
            self.cfg = cfg

    StorageRegistry.register("dummy15", DummyBackend)
    a = StorageRegistry.create("dummy15", x=1)
    b = StorageRegistry.create("dummy15", x=1)
    assert isinstance(a, DummyBackend)
    assert a is not b
    assert a.cfg == {"x": 1}


async def test_blob_primitives_roundtrip(tmp_path):
    """F3: upload/download/exists/delete/list_prefix/copy — el blob store k/v (StorageProtocol)."""
    store = FilesystemStorage(root=tmp_path)
    await store.upload("u1/s1/session.json", b'{"ok":1}', "application/json")
    assert await store.exists("u1/s1/session.json") is True
    assert await store.download("u1/s1/session.json") == b'{"ok":1}'
    await store.copy("u1/s1/session.json", "u1/s1/work/out.json")
    assert await store.download("u1/s1/work/out.json") == b'{"ok":1}'
    keys = await store.list_prefix("u1/s1/")
    assert "u1/s1/session.json" in keys and "u1/s1/work/out.json" in keys
    assert await store.delete("u1/s1/session.json") is True
    assert await store.exists("u1/s1/session.json") is False


async def test_presign_returns_locator(tmp_path):
    """F3: `presign` FS = `file://` URI (para MinIO = URL firmada) — el runtime añade servir-por-URL."""
    store = FilesystemStorage(root=tmp_path)
    await store.upload("u1/blob.bin", b"\x00\x01")
    uri = await store.presign("u1/blob.bin")
    assert uri.startswith("file://")


def test_storage_keys_wired_taxonomy_shape():
    """F2/B2: la clave CABLEADA (`transcript_key`) y las declaradas comparten el subtree user/session;
    subagente anidado. Codifica la forma acordada (el que esté muerta la mayoría es FIND-STOR1, abajo)."""
    assert StorageKeys.transcript_key("u", "s") == "u/s/session.json"
    assert StorageKeys.transcript_key("u", "s", "a1") == "u/s/subagents/a1/session.json"
    assert StorageKeys.meta_key("u", "s") == "u/s/session.meta.json"
    assert StorageKeys.work_key("u", "s", "r.csv") == "u/s/work/r.csv"


async def test_traversal_dotdot_direct_rejected(tmp_path):
    """B13: el guard `_path` rechaza el `..` que sale del root (caso directo)."""
    store = FilesystemStorage(root=tmp_path)
    with pytest.raises(ValueError):
        await store.upload("../escape.txt", b"bad")


def test_filesystem_satisfies_storage_protocol(tmp_path):
    """StorageProtocol es @runtime_checkable y FilesystemStorage lo satisface estructuralmente."""
    assert isinstance(FilesystemStorage(root=tmp_path), StorageProtocol)


# ---------------------------------------------------------------------------
# GAPS (xfail strict) — codifican los targets de §Plan StR1-8
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason="FIND-STOR1/StR1: taxonomía incompleta; los stores inventan claves fuera de StorageKeys")
def test_storage_keys_taxonomy_complete():
    # StR1: cada store sobre StorageProtocol debe derivar su clave de StorageKeys, user-scoped.
    assert hasattr(StorageKeys, "mcp_config_key"), "falta StorageKeys.mcp_config_key(uid)"
    assert hasattr(StorageKeys, "skill_key"), "falta StorageKeys.skill_key(uid, name)"
    assert hasattr(StorageKeys, "oauth_key"), "falta StorageKeys.oauth_key(uid, srv)"
    assert StorageKeys.mcp_config_key("u") == "u/mcp/servers.json"


@pytest.mark.xfail(strict=True, reason="FIND-STOR2/StR2: transcript = snapshot-overwrite; sin append incremental")
def test_storage_protocol_has_append(tmp_path):
    # StR2: escritura durable mid-turn — el snapshot por-completion pierde el turno en curso ante crash.
    store = FilesystemStorage(root=tmp_path)
    assert hasattr(store, "append"), "FilesystemStorage sin append() incremental"


@pytest.mark.xfail(strict=True, reason="FIND-STOR3/StR3: plano meta mutable (session.meta.json / is_backgrounded) no portado")
def test_session_meta_sidecar_store_exists():
    # StR3: MetaStore + SessionMeta con upsert RFC-7396 sobre meta_key.
    from agentic_runtime.storage import MetaStore  # noqa: F401  # target inexistente


@pytest.mark.xfail(strict=True, reason="FIND-STOR4/StR4: sin persistencia de config (config_key/agent_md/ltm muertos)")
def test_config_store_exists():
    # StR4: StorageBackedConfigStore (load/save-merge) sobre config_key.
    from agentic_runtime.storage import StorageBackedConfigStore  # noqa: F401  # target inexistente


@pytest.mark.xfail(strict=True, reason="FIND-STOR5/StR5: sin listado/enriquecimiento de sesiones (sólo list_prefix)")
def test_session_catalog_list_sessions_exists():
    # StR5: list_sessions(user_id) leyendo sólo el meta sidecar (no descarga transcripts).
    from agentic_runtime.storage import SessionCatalog  # noqa: F401  # target inexistente


@pytest.mark.xfail(strict=True, reason="FIND-STOR13/StR4: cascada de settings de 4+ niveles no portada (ScopedMcpConfigStore es sólo MCP)")
def test_scoped_config_store_generalized():
    # StR4/FIND-STOR13: `ScopedConfigStore` general (managed/user/project/local/flag) con merge por precedencia
    # + invariante de seguridad (scope `project` no concede privilegio). Hoy sólo existe `ScopedMcpConfigStore`.
    from agentic_runtime.storage import ScopedConfigStore  # noqa: F401  # target inexistente


@pytest.mark.xfail(strict=True, reason="FIND-STOR6/StR6: frontera StorageContract↔StorageProtocol implícita; sin adaptador")
def test_blob_backed_storage_contract_exists():
    # StR6: un StorageContract (01/09) que commitee vía StorageProtocol.upload — mismo MinIO para tools y blobs.
    from agentic_runtime.tools.fs_env import BlobBackedStorageContract  # noqa: F401  # target inexistente


@pytest.mark.xfail(strict=True, reason="FIND-STOR7/StR7: guard prefix-startswith admite hermano-prefijo")
async def test_path_traversal_sibling_prefix_rejected(tmp_path):
    # StR7: root=<tmp>/root; la clave que resuelve a <tmp>/root-evil/x debe RECHAZARSE.
    # Hoy `str(p).startswith(str(root))` la ADMITE (bug) → este bloque no lanza → xfail(strict).
    root = tmp_path / "root"
    root.mkdir()
    store = FilesystemStorage(root=root)
    with pytest.raises(ValueError):
        await store.upload("../root-evil/x.txt", b"escaped")


@pytest.mark.xfail(strict=True, reason="FIND-STOR7/StR7: sin sanitización de clave (null-byte/backslash/absoluta)")
def test_key_sanitization_helper_exists(tmp_path):
    # StR7: _key_is_safe espejo de teamMemPaths.sanitizePathKey (= 13·MEM9).
    store = FilesystemStorage(root=tmp_path)
    assert hasattr(store, "_key_is_safe"), "FilesystemStorage sin sanitización de clave"


@pytest.mark.xfail(strict=True, reason="FIND-STOR9/StR8: sin download_range/tail (download es todo-o-nada)")
async def test_download_range_exists(tmp_path):
    # StR8: lectura por ventana sobre blobs grandes (transcripts/history GB).
    store = FilesystemStorage(root=tmp_path)
    assert hasattr(store, "download_range"), "FilesystemStorage sin download_range()"
