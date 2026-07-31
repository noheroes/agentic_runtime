"""Costuras del hilo de identidad — `C9` · `SEAMS §S20` · `DEUDA-A ID-2`/`ID-3`.

Dos aserciones que el corpus pedía por escrito y que hasta ahora no existían:

  · **`ID-2`** — *«dos integradores con metadata **incompatible** componen el mismo
    núcleo sin tocarlo»*. Es el criterio de cierre literal de `DEUDA-A §2·ID-2`, y sólo
    se puede escribir cuando el repo es una costura de verdad: si el runtime leyera algo
    más que `.id`, la metadata del integrador entraría en el núcleo y estos dos repos no
    podrían coexistir.
  · **`ID-3`** — *«el token OAuth del usuario A no es legible bajo el scope de B»*, que
    `DEUDA-A` anotaba como **«hoy falla»**. Fallaba porque `StorageBackedTokenStorage`
    tenía `user_id: str = "mcp"` y el factory nunca pasaba el real: todos los tenants
    colisionaban en `mcp/mcp/<srv>`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from agentic_runtime.capabilities.mcp import StorageBackedTokenStorage
from agentic_runtime.contracts.identity import (
    RuntimeSessionProtocol,
    Scope,
    SessionId,
    SessionInfo,
)
from agentic_runtime.execution.local.runtime import LocalAgentRuntime

# ---------------------------------------------------------------------------
# ID-2 · dos integradores con metadata incompatible sobre el MISMO núcleo
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _TenantMeta:
    """Metadata del integrador complejo: multi-tenant, con proyecto."""

    tenant: str
    project: str


@dataclass(frozen=True)
class _CwdMeta:
    """Metadata del integrador degenerado: una sola sesión, scope por cwd."""

    cwd: str


class _Handle:
    def __init__(self, session_id: str) -> None:
        self._id = session_id

    @property
    def id(self) -> str:
        return self._id


class _TenantRepo:
    """Repo del integrador complejo. Su id opaco codifica SU metadata, no la del base."""

    def __init__(self) -> None:
        self._sessions: dict[str, _TenantMeta] = {}

    def create(self, metadata: _TenantMeta) -> SessionId:
        sid = SessionId(f"{metadata.tenant}:{metadata.project}:1")
        self._sessions[sid] = metadata
        return sid

    def open(self, session_id: SessionId) -> RuntimeSessionProtocol:
        if session_id not in self._sessions:
            raise KeyError(f"sesión desconocida para este tenant: {session_id}")
        return _Handle(session_id)

    def list(self, query: _TenantMeta) -> list[SessionInfo]:
        return [
            SessionInfo(id=SessionId(sid), metadata=meta)
            for sid, meta in self._sessions.items()
            if meta.tenant == query.tenant
        ]

    def delete(self, session_id: SessionId) -> None:
        self._sessions.pop(session_id, None)

    def fork(self, session_id: SessionId) -> SessionId:
        meta = self._sessions[session_id]
        sid = SessionId(f"{session_id}:fork")
        self._sessions[sid] = meta
        return sid


class _CwdRepo:
    """Repo del integrador degenerado. Metadata INCOMPATIBLE con la del anterior."""

    def __init__(self) -> None:
        self._sessions: dict[str, _CwdMeta] = {}

    def create(self, metadata: _CwdMeta) -> SessionId:
        sid = SessionId(metadata.cwd.replace("/", "_"))
        self._sessions[sid] = metadata
        return sid

    def open(self, session_id: SessionId) -> RuntimeSessionProtocol:
        if session_id not in self._sessions:
            raise KeyError(session_id)
        return _Handle(session_id)

    def list(self, query: _CwdMeta) -> list[SessionInfo]:
        return [SessionInfo(id=SessionId(s), metadata=m) for s, m in self._sessions.items()]

    def delete(self, session_id: SessionId) -> None:
        self._sessions.pop(session_id, None)

    def fork(self, session_id: SessionId) -> SessionId:
        return session_id


def test_two_integrators_with_incompatible_metadata_share_one_core():
    """El criterio de cierre de `ID-2`, escrito como aserción y no como prosa."""
    tenant_repo, cwd_repo = _TenantRepo(), _CwdRepo()
    sid_a = tenant_repo.create(_TenantMeta(tenant="acme", project="p1"))
    sid_b = cwd_repo.create(_CwdMeta(cwd="/home/x/proj"))

    rt_a = LocalAgentRuntime(session_repo=tenant_repo, scope=Scope("acme"))
    rt_b = LocalAgentRuntime(session_repo=cwd_repo, scope=Scope("local"))

    # El MISMO núcleo abre ambas sesiones y de cada handle lee sólo `.id` (`S20`).
    assert rt_a._open_session(sid_a).id == sid_a
    assert rt_b._open_session(sid_b).id == sid_b
    # ...y ninguna metadata del integrador entró en el núcleo: son tipos que el runtime
    # no importa, no menciona y no podría reconciliar entre sí.
    assert type(tenant_repo.list(_TenantMeta("acme", "p1"))[0].metadata) is _TenantMeta
    assert type(cwd_repo.list(_CwdMeta("/home/x/proj"))[0].metadata) is _CwdMeta


def test_session_repo_is_the_authority_on_which_sessions_exist():
    """Con repo inyectado, el runtime deja de ser el sitio donde una sesión «aparece»."""
    rt = LocalAgentRuntime(session_repo=_TenantRepo())
    with pytest.raises(KeyError):
        rt._open_session("no-existe")


def test_session_repo_is_optional_and_the_core_stays_runnable():
    """`S20` es costura OPCIONAL (precedente PI: el integrador complejo ni la usa)."""
    assert LocalAgentRuntime()._open_session("s-nativa").id == "s-nativa"


# ---------------------------------------------------------------------------
# ID-3 · aislamiento de los tokens OAuth entre scopes
# ---------------------------------------------------------------------------

class _FakeStorage:
    def __init__(self) -> None:
        self.data: dict[str, bytes] = {}

    async def upload(self, key: str, data: bytes, content_type: str = "") -> str:
        self.data[key] = data
        return key

    async def download(self, key: str) -> bytes:
        return self.data[key]

    async def exists(self, key: str) -> bool:
        return key in self.data

    async def delete(self, key: str) -> bool:
        return self.data.pop(key, None) is not None

    async def presign(self, key: str, ttl_seconds: int = 3600) -> str:
        return key

    async def list_prefix(self, prefix: str) -> list[str]:
        return [k for k in self.data if k.startswith(prefix)]


@pytest.mark.asyncio
async def test_oauth_token_of_one_scope_is_not_readable_under_another():
    """`DEUDA-A ID-3` lo daba por **fallando hoy**: `user_id="mcp"` por defecto hacía que
    todos los tenants compartieran `mcp/mcp/<srv>`. Con `Scope` obligatorio, no."""
    from mcp.shared.auth import OAuthToken

    storage = _FakeStorage()
    ts_a = StorageBackedTokenStorage(storage, "wiki", scope=Scope("tenant-a"))
    ts_b = StorageBackedTokenStorage(storage, "wiki", scope=Scope("tenant-b"))

    await ts_a.set_tokens(OAuthToken(access_token="SECRETO-DE-A", token_type="Bearer"))

    assert (await ts_b.get_tokens()) is None, "fuga entre tenants: B lee el token de A"
    loaded = await ts_a.get_tokens()
    assert loaded is not None and loaded.access_token == "SECRETO-DE-A"
    # cero claves compartidas entre los dos scopes
    keys_a = set(await storage.list_prefix("tenant-a/"))
    keys_b = set(await storage.list_prefix("tenant-b/"))
    assert keys_a and not (keys_a & keys_b)


def test_no_repo_of_the_runtime_accepts_a_bare_user_id() -> None:
    """`ID-3`, firma: *«cero repos que acepten `user_id: str` literal»*."""
    import inspect

    from agentic_runtime.capabilities.skills.store import StorageBackedSkillStore
    from agentic_runtime.storage.protocol import StorageKeys

    targets: list[Any] = [
        StorageBackedTokenStorage.__init__,
        StorageBackedSkillStore.__init__,
        StorageKeys.transcript_key,
        StorageKeys.config_key,
        StorageKeys.ltm_key,
        StorageKeys.work_key,
        StorageKeys.log_key,
        StorageKeys.meta_key,
        StorageKeys.agent_md_key,
    ]
    for fn in targets:
        params = inspect.signature(fn).parameters
        assert "user_id" not in params, f"{fn.__qualname__} sigue aceptando user_id"
        if "scope" in params:
            assert params["scope"].default is inspect.Parameter.empty, (
                f"{fn.__qualname__}: un `scope` con default es cómo volvió la fuga"
            )
