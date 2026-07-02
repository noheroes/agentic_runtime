"""Tests para runtime/modes/ — ModeManager."""
import pytest

from agentic_runtime.modes import AgentMode, ModeManager


def test_background_on_complete_returns_true():
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.BACKGROUND)
    assert mgr.on_complete("t1") is True


def test_foreground_on_complete_returns_false():
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.FOREGROUND)
    assert mgr.on_complete("t1") is False


def test_mode_transition_to_foreground_suppresses_notification():
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.BACKGROUND)
    mgr.set_mode("t1", AgentMode.FOREGROUND)
    assert mgr.on_complete("t1") is False


def test_mode_transition_back_to_background_restores_notification():
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.FOREGROUND)
    mgr.set_mode("t1", AgentMode.BACKGROUND)
    assert mgr.on_complete("t1") is True


def test_fork_mode_is_immutable():
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.FORK)
    with pytest.raises(ValueError):
        mgr.set_mode("t1", AgentMode.FOREGROUND)


def test_unknown_task_on_complete_returns_false():
    mgr = ModeManager()
    assert mgr.on_complete("nonexistent") is False


def test_get_mode_returns_current_mode():
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.FOREGROUND)
    assert mgr.get_mode("t1") == AgentMode.FOREGROUND
    mgr.set_mode("t1", AgentMode.BACKGROUND)
    assert mgr.get_mode("t1") == AgentMode.BACKGROUND


def test_get_mode_unknown_returns_none():
    mgr = ModeManager()
    assert mgr.get_mode("nonexistent") is None


def test_unregister_removes_entry():
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.BACKGROUND)
    mgr.unregister("t1")
    assert mgr.get_mode("t1") is None
    assert mgr.on_complete("t1") is False
