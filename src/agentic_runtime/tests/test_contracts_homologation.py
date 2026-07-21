"""
Homologación · subsistema 01 · contracts.

Evidencia sintética + e2e de los seams de `contracts/` que NO cubría
`test_runtime_contracts.py` (que ya cubre PermissionContext allow/deny,
CompactionProvider y adapters):

  - AgentRuntime / RuntimeTask  (protocolo de la unidad coordinable)
  - StorageContract / PathPresentation  (conformidad estructural)
  - UserInputProcessor / NoopUserInputProcessor  (+ gap de cableado)

Los tests marcados `xfail(strict=True)` codifican el comportamiento HOMOLOGADO
esperado; su fallo ES la evidencia del gap documentada en HOMOLOGATION/01-contracts.md.
Primera pasada: solo documentar — no se ajusta el runtime para hacerlos pasar.
"""
from __future__ import annotations

import inspect

import pytest

from agentic_runtime.contracts.runtime import AgentRuntime, RuntimeTask
from agentic_runtime.contracts.storage import PathPresentation, StorageContract
from agentic_runtime.contracts.user_input import (
    NoopUserInputProcessor,
    UserInputProcessor,
)


# ---------------------------------------------------------------- AgentRuntime

def test_local_agent_runtime_satisfies_agent_runtime_protocol() -> None:
    """La implementación en-proceso conforma el contrato (dispatch/stream/…)."""
    from agentic_runtime.execution.local.runtime import LocalAgentRuntime

    rt = LocalAgentRuntime()
    assert isinstance(rt, AgentRuntime)
    for method in ("dispatch", "stream", "status", "cancel", "result"):
        assert callable(getattr(rt, method))
    assert isinstance(rt.runtime_id, str) and rt.runtime_id


def test_runtime_task_defaults_are_self_contained() -> None:
    """RuntimeTask es ejecutable sola: identidad de ciclo de vida opcional."""
    task = RuntimeTask(prompt="hola", description="saludo")
    assert task.owner_id is None
    assert task.session_id is None
    assert task.subagent_type is None
    assert task.model_override is None
    assert task.fork_context is False
    assert task.audio_prompt is None


def test_runtime_task_accepts_injected_lifecycle_identity() -> None:
    """El consumidor (BFF) puede inyectar user/session; el runtime los respeta."""
    task = RuntimeTask(
        prompt="p", description="d", owner_id="user_x", session_id="sess_y",
    )
    assert task.owner_id == "user_x"
    assert task.session_id == "sess_y"


# ------------------------------------------------ Storage / PathPresentation

def test_identity_presentation_conforms_to_path_presentation() -> None:
    from agentic_runtime.context.presentation import IdentityPresentation

    assert isinstance(IdentityPresentation(), PathPresentation)


def test_storage_contract_is_structurally_checkable() -> None:
    from pathlib import Path

    class _Blob:
        def real_path(self, token: str) -> Path:
            return Path(token)

        async def ensure_local(self, token: str) -> Path:
            return Path(token)

        async def commit(self, token: str, content: bytes, mime: str | None = None) -> str:
            return token

        async def teardown(self) -> None:
            return None

    assert isinstance(_Blob(), StorageContract)


# ----------------------------------------------------- UserInputProcessor

async def test_noop_user_input_processor_is_passthrough() -> None:
    proc = NoopUserInputProcessor()
    # NOTA: UserInputProcessor NO es @runtime_checkable (a diferencia de
    # AgentRuntime/StorageContract/PathPresentation) → conformidad por duck-typing.
    for m in ("process_slash_command", "expand_inline_invocation", "get_inline_name"):
        assert callable(getattr(proc, m))
    assert await proc.process_slash_command("/x", None, None, None, None) is None
    assert proc.expand_inline_invocation("texto") == "texto"
    assert proc.get_inline_name("texto") is None


def test_runtime_checkable_is_inconsistent_across_contracts() -> None:
    """Evidencia FIND-01: unos contratos son @runtime_checkable y otros no.
    Documenta el estado actual (no lo homologa)."""
    from agentic_runtime.contracts.compaction import CompactionProvider

    def is_rc(proto: object) -> bool:
        return bool(getattr(proto, "_is_runtime_protocol", False))

    assert is_rc(AgentRuntime) is True
    assert is_rc(StorageContract) is True
    assert is_rc(PathPresentation) is True
    # Inconsistentes: sin @runtime_checkable
    assert is_rc(UserInputProcessor) is False
    assert is_rc(CompactionProvider) is False


@pytest.mark.xfail(
    strict=True,
    reason="GAP-01: UserInputProcessor no está cableado en el loop; ningún "
    "consumidor invoca process_slash_command/expand_inline. Ver 01-contracts.md.",
)
def test_agent_loop_consumes_user_input_processor() -> None:
    """Homologado: el loop debe preprocesar slash/inline vía UserInputProcessor
    (canónico: commands.ts + query). Hoy el seam existe pero está muerto."""
    from agentic_runtime.loop import agent_loop

    src = inspect.getsource(agent_loop)
    assert "UserInputProcessor" in src or "process_slash_command" in src


@pytest.mark.xfail(
    strict=True,
    reason="GAP-02: PermissionContext no modela los permission modes del canónico "
    "(acceptEdits/bypassPermissions/plan/default). Ver 01-contracts.md.",
)
def test_permission_context_models_permission_modes() -> None:
    """Homologado: el canónico decide permisos por MODO además de allow/deny."""
    from agentic_runtime.contracts.permissions import PermissionContext

    ctx = PermissionContext()
    assert hasattr(ctx, "mode")
