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
    """RuntimeTask es autocontenida: el DATACLASS no exige identidad — el que la exige
    es el runtime al arrancar la raíz (`C9`: no la inventa, la reclama)."""
    task = RuntimeTask(prompt="hola", description="saludo")
    assert task.owner_id is None
    assert task.session_id is None
    assert task.subagent_type is None
    assert task.model_override is None
    assert task.fork_context is False
    assert task.audio_prompt is None
    assert task.scope is None


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
    """`C4`: el default de `S11` tiene que ser identidad EXACTA.

    Es lo que sostiene que cablear la costura no cambió el comportamiento de
    ningún runtime que no inyecte procesador propio.
    """
    proc = NoopUserInputProcessor()
    # `C4` pagó `FIND-01` para esta costura: ya es @runtime_checkable, así que la
    # conformidad se comprueba, no se supone.
    assert isinstance(proc, UserInputProcessor)
    out = await proc.process("texto", None)  # type: ignore[arg-type]
    assert out.prompt == "texto"
    assert out.short_circuit is False
    assert out.result_text is None


def test_runtime_checkable_is_inconsistent_across_contracts() -> None:
    """Evidencia FIND-01: unos contratos son @runtime_checkable y otros no.
    Documenta el estado actual (no lo homologa)."""
    from agentic_runtime.contracts.compaction import CompactionProvider

    def is_rc(proto: object) -> bool:
        return bool(getattr(proto, "_is_runtime_protocol", False))

    assert is_rc(AgentRuntime) is True
    assert is_rc(StorageContract) is True
    assert is_rc(PathPresentation) is True
    # `UserInputProcessor` salió de esta lista con `C4`: al cablearlo se le puso
    # @runtime_checkable, porque un consumidor tiene que poder comprobar lo que
    # inyecta antes de un turno real, no descubrirlo con un AttributeError.
    assert is_rc(UserInputProcessor) is True
    # Sigue inconsistente (su ciclo dueño está bajo la línea de corte):
    assert is_rc(CompactionProvider) is False


# `GAP-01` PAGADO por `C4`. Aquí vivía un xfail que leía el **código fuente** del loop
# buscando la cadena "UserInputProcessor" — un test de grado `grep`, que habría pasado
# igual con la costura exportada y muerta (`L09`). Su sustituto prueba el
# comportamiento y vive donde vive el loop:
#   test_loop_homologation.py::test_loop_consumes_user_input_processor_and_honors_short_circuit
# (el processor corta, el modelo NO se llama, y el historial conserva ambos mensajes).


# GAP-02 (mitad de contrato) pagado por C1 del tramo 1. El motor = `K1`, sin tocar.
def test_permission_context_models_permission_modes() -> None:
    """Homologado: el canónico decide permisos por MODO además de allow/deny."""
    from agentic_runtime.contracts.permissions import PermissionContext

    ctx = PermissionContext()
    assert hasattr(ctx, "mode")
