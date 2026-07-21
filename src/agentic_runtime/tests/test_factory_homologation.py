"""Homologación 18 · factory / ensamblado — `factory.py::create_runtime`.

18 es el punto de CONVERGENCIA: donde se cablean los seams que los §Plan previos
citan. Estos tests codifican (lección 05):
  - los targets PROPIOS de 18 como xfail(strict) (FaR1 fail-fast, FaR2 resolver muerto);
  - la convergencia OBSERVABLE de C1=FIND-EXEC1 (el xfail source-grep vive en 05,
    aquí se prueba el efecto observable: tras create_runtime el runner sigue sin cablear);
  - el ensamblado ya homologado como passing (storage/tools/voice/presentation/lifecycle/mode).
"""
import pytest

from agentic_runtime import execution
from agentic_runtime.execution.local import LocalAgentRuntime
from agentic_runtime.factory import (
    RuntimeConfig,
    StorageConfig,
    VoiceConfig,
    create_runtime,
)


@pytest.fixture
def _reset_runner():
    """Aísla el `_runner` global de execution/runner.py (evita filtrado entre tests)."""
    import agentic_runtime.execution.runner as runner_mod

    prev = runner_mod._runner
    runner_mod._runner = None
    try:
        yield runner_mod
    finally:
        runner_mod._runner = prev


# --------------------------------------------------------------------------
# Deuda A propia de 18
# --------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="FaR1: create_runtime() no valida inyecciones requeridas. Con model_caller=None "
    "ensambla un runtime silenciosamente no funcional (el loop hace warning+return, no-op) "
    "en vez de fallar rápido como el canónico (init.ts::enableConfigs → ConfigParseError). "
    "Passing = fail-fast al ensamblar (RuntimeConfigError).",
)
def test_create_runtime_fails_fast_without_model_caller(tmp_path):
    from agentic_runtime.factory import RuntimeConfigError  # aún no existe → parte del target

    with pytest.raises(RuntimeConfigError):
        create_runtime(config=RuntimeConfig(
            storage=StorageConfig(backend="filesystem", root=tmp_path),
            # model_caller ausente a propósito
        ))


@pytest.mark.xfail(
    strict=True,
    reason="FaR2: el factory teje un CapabilitiesResolver legacy (factory.py:197) que es "
    "camino MUERTO en el loop (agent_loop.py:194 el if pool siempre gana porque el factory "
    "siempre construye tool_registry+capability_manager). Passing = el factory no cablea el "
    "camino muerto (runtime._capabilities_resolver is None). Coordinar con 09·B2.",
)
def test_create_runtime_does_not_wire_dead_resolver(tmp_path):
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
    ))
    assert runtime._capabilities_resolver is None


# --------------------------------------------------------------------------
# C1 = FIND-EXEC1 — convergencia observable (el xfail source-grep vive en 05)
# --------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="C1=FIND-EXEC1 (converge en 18): create_runtime NO llama set_runner(), así que "
    "get_runner() sigue lanzando RuntimeError tras ensamblar → todo spawn de subagente "
    "(AgentTool→get_runner().run) revienta. Passing = el factory registra el runner "
    "(remediación real en 05·ExR1). Prueba el efecto observable, no el source.",
)
def test_create_runtime_wires_runner_so_subagents_spawn(tmp_path, _reset_runner):
    create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
    ))
    # Tras ensamblar, el runner DEBERÍA estar registrado (sin set_runner manual):
    runner = execution.get_runner()  # hoy lanza RuntimeError → el xfail
    assert runner is not None


# --------------------------------------------------------------------------
# Ensamblado ya homologado (passing) — el núcleo SÍ está cableado
# --------------------------------------------------------------------------

def test_local_mode_returns_local_runtime(tmp_path):
    """D1: execution_mode='local' → LocalAgentRuntime."""
    rt = create_runtime(execution_mode="local", config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
    ))
    assert isinstance(rt, LocalAgentRuntime)


def test_unknown_execution_mode_raises(tmp_path):
    """D1: modos no implementados fallan explícitamente (no silenciosamente)."""
    with pytest.raises(NotImplementedError):
        create_runtime(execution_mode="remote", config=RuntimeConfig(
            storage=StorageConfig(backend="filesystem", root=tmp_path),
        ))
    with pytest.raises(NotImplementedError):
        create_runtime(execution_mode="does-not-exist", config=RuntimeConfig(
            storage=StorageConfig(backend="filesystem", root=tmp_path),
        ))


def test_lifecycle_startup_shutdown_present(tmp_path):
    """E1: el lifecycle de capabilities EXISTE (no inflar un gap inexistente)."""
    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
    ))
    assert hasattr(rt, "startup") and callable(rt.startup)
    assert hasattr(rt, "shutdown") and callable(rt.shutdown)


def test_presentation_default_is_identity(tmp_path):
    """B4/C10: sin presentation inyectada, default IdentityPresentation cableado."""
    from agentic_runtime.context.presentation import IdentityPresentation

    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
    ))
    assert isinstance(rt._presentation, IdentityPresentation)


def test_voice_gate_off_when_flag_disabled(tmp_path):
    """B7/17·C1: canal activo sii primitiva inyectada Y flag on. Gate en el factory."""
    class _STT:
        async def transcribe(self, audio, ctx):  # pragma: no cover
            return ""

    stt = _STT()
    # primitiva presente + flag off → canal inactivo (None en el runtime)
    rt_off = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        voice=VoiceConfig(stt=stt, stt_enabled=False),
    ))
    assert rt_off._stt is None
    # primitiva presente + flag on → canal activo
    rt_on = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        voice=VoiceConfig(stt=stt, stt_enabled=True),
    ))
    assert rt_on._stt is stt


def test_single_registry_no_native_registry_wired(tmp_path):
    """C8/09·B2: el factory usa create_tools→ToolRegistry; el hot-plug MCP es por
    reensamblado del pool por-turno, NO por NativeToolRegistry en el factory."""
    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
    ))
    # el registry cableado responde list_available (contrato de ToolRegistry)
    assert hasattr(rt._tool_registry, "list_available")
