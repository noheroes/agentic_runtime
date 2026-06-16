"""Tests para runtime/signals/ — SignalBus con árbol de cascada."""
import pytest

from agentic_runtime.signals import SignalBus, SignalType


# ---------------------------------------------------------------------------
# Registro y árbol
# ---------------------------------------------------------------------------

def test_register_root_node():
    bus = SignalBus()
    handle = bus.register(execution_id="root", parent_id=None)
    assert handle.execution_id == "root"
    assert handle.parent_id is None


def test_register_child_node():
    bus = SignalBus()
    bus.register(execution_id="root", parent_id=None)
    child = bus.register(execution_id="child", parent_id="root")
    assert child.parent_id == "root"


def test_unregister_removes_node():
    bus = SignalBus()
    bus.register(execution_id="root", parent_id=None)
    bus.unregister("root")
    # Registrar de nuevo debe funcionar sin error
    handle = bus.register(execution_id="root", parent_id=None)
    assert handle.execution_id == "root"


# ---------------------------------------------------------------------------
# Señales directas (sin cascada)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_abort_to_single_node():
    bus = SignalBus()
    bus.register(execution_id="e1", parent_id=None)
    await bus.send(execution_id="e1", signal=SignalType.ABORT)
    assert bus.get_signal("e1") == SignalType.ABORT


@pytest.mark.asyncio
async def test_send_pause_to_single_node():
    bus = SignalBus()
    bus.register(execution_id="e1", parent_id=None)
    await bus.send(execution_id="e1", signal=SignalType.PAUSE)
    assert bus.get_signal("e1") == SignalType.PAUSE


@pytest.mark.asyncio
async def test_send_resume_clears_pause():
    bus = SignalBus()
    bus.register(execution_id="e1", parent_id=None)
    await bus.send(execution_id="e1", signal=SignalType.PAUSE)
    await bus.send(execution_id="e1", signal=SignalType.RESUME)
    assert bus.get_signal("e1") is None


def test_get_signal_unknown_node_returns_none():
    bus = SignalBus()
    assert bus.get_signal("nonexistent") is None


# ---------------------------------------------------------------------------
# Cascada parent → children
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_abort_cascades_to_children():
    bus = SignalBus()
    bus.register(execution_id="parent", parent_id=None)
    bus.register(execution_id="child1", parent_id="parent")
    bus.register(execution_id="child2", parent_id="parent")

    await bus.send(execution_id="parent", signal=SignalType.ABORT, cascade=True)

    assert bus.get_signal("parent") == SignalType.ABORT
    assert bus.get_signal("child1") == SignalType.ABORT
    assert bus.get_signal("child2") == SignalType.ABORT


@pytest.mark.asyncio
async def test_abort_cascades_deep():
    bus = SignalBus()
    bus.register(execution_id="root", parent_id=None)
    bus.register(execution_id="mid", parent_id="root")
    bus.register(execution_id="leaf", parent_id="mid")

    await bus.send(execution_id="root", signal=SignalType.ABORT, cascade=True)

    assert bus.get_signal("leaf") == SignalType.ABORT


@pytest.mark.asyncio
async def test_abort_no_cascade_does_not_affect_children():
    bus = SignalBus()
    bus.register(execution_id="parent", parent_id=None)
    bus.register(execution_id="child", parent_id="parent")

    await bus.send(execution_id="parent", signal=SignalType.ABORT, cascade=False)

    assert bus.get_signal("parent") == SignalType.ABORT
    assert bus.get_signal("child") is None


# ---------------------------------------------------------------------------
# Limpieza al unregister
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unregister_clears_signal():
    bus = SignalBus()
    bus.register(execution_id="e1", parent_id=None)
    await bus.send(execution_id="e1", signal=SignalType.ABORT)
    bus.unregister("e1")
    assert bus.get_signal("e1") is None


# ---------------------------------------------------------------------------
# SignalHandle.check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_check_returns_current_signal():
    bus = SignalBus()
    handle = bus.register(execution_id="e1", parent_id=None)
    assert handle.check() is None

    await bus.send(execution_id="e1", signal=SignalType.ABORT)
    assert handle.check() == SignalType.ABORT
