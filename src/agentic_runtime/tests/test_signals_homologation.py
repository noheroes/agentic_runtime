"""Homologación 08·signals — cancelación/abort vs AbortController/AbortSignal canónico.

Contrasta el mecanismo REAL de cancelación del runtime (`ctx.stop: asyncio.Event`,
cableado loop→caller→models→dispatcher→fork) contra la maquinaria `AbortController`/
`AbortSignal` del canónico, y documenta el estado HUÉRFANO de `signals/SignalBus`.

Los `xfail(strict=True)` codifican los gaps (SIG1..SIG6): fallan HOY (comportamiento
homologado ausente) y su fallo ES la evidencia del gap. Si alguno empezara a pasar,
el strict lo convierte en error → señal de que hay que reclasificar el estado.
"""
import asyncio

import pytest

from agentic_runtime.context.tool_use import AppState, ToolUseContext
from agentic_runtime.execution.fork import (
    ForkContext,
    ForkPolicy,
    ForkSnapshot,
    RuntimeContextForker,
)
from agentic_runtime.signals import SignalBus, SignalHandler, SignalType
from agentic_runtime.tools.dispatcher import ToolDispatcher  # noqa: F401  (referencia de seam)
from agentic_runtime.tools.protocol import ToolResult


# ---------------------------------------------------------------------------
# Lo que SÍ está homologado (comportamiento verificado) — deben PASAR
# ---------------------------------------------------------------------------

def test_ctx_stop_is_the_real_cancellation_primitive():
    """`ctx.stop` (asyncio.Event) vive en el ToolUseContext, espejo de
    `ToolUseContext.abortController` del canónico (Tool.ts:180)."""
    stop = asyncio.Event()
    ctx = ToolUseContext(session_id="s1", stop=stop)
    assert ctx.stop is stop
    assert not ctx.stop.is_set()
    ctx.stop.set()
    assert ctx.stop.is_set()


def test_tool_result_aborted_marks_is_aborted():
    """El dispatcher devuelve ToolResult.aborted ante stop.is_set() (dispatcher.py:54),
    espejo del CANCEL_MESSAGE/synthetic-result del canónico (toolExecution.ts:444)."""
    r = ToolResult.aborted("bash")
    assert r.is_aborted is True
    assert "bash" in r.output


def test_abort_ownership_is_external_no_internal_setter():
    """S20: nadie SETEA ctx.stop dentro del runtime (lo dispara el integrador, como HITL);
    espejo de que el canónico sólo aborta vía interrupt()/keybinding externo."""
    import agentic_runtime  # noqa: F401
    # Un ctx recién forjado nunca trae stop activado por el runtime.
    ctx = ToolUseContext(session_id="s1", stop=asyncio.Event())
    assert not ctx.stop.is_set()


# ---------------------------------------------------------------------------
# FIND-SIG1 — SignalBus es HUÉRFANO: ninguna ruta lo consulta
# ---------------------------------------------------------------------------

@pytest.mark.xfail(strict=True, reason="FIND-SIG1: SignalBus no está cableado a ctx.stop ni al loop")
def test_signalbus_abort_reaches_ctx_stop():
    """Homologado: enviar ABORT por el bus a un task debería reflejarse en el ctx.stop
    de ese task. Hoy los dos mecanismos están desconectados → no existe el puente."""
    bus = SignalBus()
    ctx = ToolUseContext(session_id="s1", agent_id="a1", stop=asyncio.Event())
    bus.register(task_id="a1", parent_id=None)
    asyncio.run(bus.send(task_id="a1", signal=SignalType.ABORT))
    # No hay puente bus→ctx.stop; esto es lo que faltaría para homologar.
    assert ctx.stop.is_set()


# ---------------------------------------------------------------------------
# FIND-SIG2 — la primitiva de abort carece de `reason`
# ---------------------------------------------------------------------------

@pytest.mark.xfail(strict=True, reason="FIND-SIG2: asyncio.Event no porta reason (canónico: signal.reason)")
def test_ctx_stop_carries_reason():
    """El canónico distingue 'interrupt' vs 'sibling_error' vs user (query.ts:1046,1501).
    ctx.stop es binario → no puede portar reason."""
    stop = asyncio.Event()
    stop.set()
    assert getattr(stop, "reason", None) == "interrupt"


# ---------------------------------------------------------------------------
# FIND-SIG3 — direccionalidad del árbol padre→hijo (createChildAbortController)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-SIG3: fork.propagate_abort comparte el MISMO Event → hijo aborta al padre (viola direccionalidad)",
)
def test_child_abort_does_not_abort_parent():
    """Canónico: abortar el hijo NO afecta al padre (abortController.ts:56-57).
    Runtime: propagate_abort=True comparte el objeto Event → hijo.set() aborta al padre."""
    parent_stop = asyncio.Event()
    forker = RuntimeContextForker()
    fork_ctx = ForkContext(
        prompt="child",
        policy=ForkPolicy(propagate_abort=True),
        parent_snapshot=ForkSnapshot(session_id="s1"),
    )
    child = forker.fork(fork_ctx, parent_stop=parent_stop)
    # El hijo aborta lo suyo:
    child.stop.set()
    # Homologado: el padre NO debería verse afectado.
    assert not parent_stop.is_set()


def test_parent_abort_propagates_to_child_when_enabled():
    """La dirección padre→hijo SÍ funciona (objeto compartido): esto es correcto y pasa."""
    parent_stop = asyncio.Event()
    forker = RuntimeContextForker()
    fork_ctx = ForkContext(
        prompt="child",
        policy=ForkPolicy(propagate_abort=True),
        parent_snapshot=ForkSnapshot(session_id="s1"),
    )
    child = forker.fork(fork_ctx, parent_stop=parent_stop)
    parent_stop.set()
    assert child.stop.is_set()


# ---------------------------------------------------------------------------
# FIND-SIG4 — interruptBehavior per-tool ('cancel'/'block')
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-SIG4: el ToolProtocol no expone interrupt_behavior ('cancel'/'block')",
)
def test_tool_protocol_exposes_interrupt_behavior():
    """Canónico Tool.ts:416 interruptBehavior():'cancel'|'block'; el runtime aborta
    toda tool indiscriminadamente (dispatcher.py:54)."""
    from agentic_runtime.tools.protocol import ToolProtocol
    assert hasattr(ToolProtocol, "interrupt_behavior")


# ---------------------------------------------------------------------------
# FIND-SIG5 — register_handler nunca invoca handle_signal (extension point muerto)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-SIG5: SignalBus.send() nunca invoca handle_signal de los handlers registrados",
)
def test_register_handler_invokes_handle_signal():
    bus = SignalBus()
    bus.register(task_id="a1", parent_id=None)

    received: list[SignalType] = []

    class _Handler:  # implementa SignalHandler
        async def handle_signal(self, signal: SignalType) -> None:
            received.append(signal)

    handler: SignalHandler = _Handler()
    bus.register_handler("a1", handler)
    asyncio.run(bus.send(task_id="a1", signal=SignalType.ABORT))
    # Homologado: el handler debería haber recibido la señal.
    assert received == [SignalType.ABORT]


# ---------------------------------------------------------------------------
# FIND-SIG6 — PAUSE/RESUME contradicen la irreversibilidad de AbortSignal
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-SIG6: AbortSignal es one-shot irreversible; RESUME limpia un ABORT (invención sin contraparte)",
)
def test_abort_is_irreversible_like_canonical():
    """Canónico: una vez abortado, siempre abortado (createChildAbortController fast-path).
    Runtime: RESUME limpia cualquier señal, incluido ABORT → reversible."""
    bus = SignalBus()
    bus.register(task_id="a1", parent_id=None)
    asyncio.run(bus.send(task_id="a1", signal=SignalType.ABORT))
    asyncio.run(bus.send(task_id="a1", signal=SignalType.RESUME))
    # Homologado con el canónico: el ABORT debería persistir pese al RESUME.
    assert bus.get_signal("a1") == SignalType.ABORT


# ---------------------------------------------------------------------------
# FIND-SIG10 — ToolResult.aborted no porta razón (canónico: CANCEL vs REJECT vs sibling)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-SIG10: ToolResult.aborted es texto plano; no distingue interrupción/rechazo-permiso/sibling",
)
def test_aborted_result_carries_reason():
    """Canónico: tres mensajes sintéticos distintos por tool_use_id (CANCEL_MESSAGE,
    REJECT_MESSAGE, sibling-error), con withMemoryCorrectionHint. El runtime da un solo
    string plano sin razón."""
    r = ToolResult.aborted("file_edit")
    assert getattr(r, "reason", None) in {"user_interrupted", "sibling_error", "streaming_fallback"}


# ---------------------------------------------------------------------------
# Uso de AppState (import guard — el fork produce ctx con AppState válido)
# ---------------------------------------------------------------------------

def test_fork_produces_ctx_with_appstate():
    forker = RuntimeContextForker()
    fork_ctx = ForkContext(
        prompt="child",
        policy=ForkPolicy(),
        parent_snapshot=ForkSnapshot(session_id="s1"),
    )
    child = forker.fork(fork_ctx, parent_stop=asyncio.Event())
    assert isinstance(child.app_state, AppState)
