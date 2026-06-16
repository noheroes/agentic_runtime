"""Tests de R2: Session concreto nativo."""
from __future__ import annotations

from agentic_runtime.execution.session import (
    BackgroundTaskRef,
    RuntimeSessionProtocol,
    Session,
    SessionMetadata,
)


def test_session_satisfies_runtime_session_protocol():
    assert isinstance(Session(), RuntimeSessionProtocol)


def test_session_defaults_are_runnable_standalone():
    s = Session()
    assert s.session_id.startswith("sess_")
    assert s.messages == []
    assert s.turn_count == 0
    assert s.input_tokens == 0 and s.output_tokens == 0
    assert s.subagent_depth == 0


def test_flat_views_reflect_nested_state():
    s = Session()
    s.usage.input_tokens = 5
    s.usage.output_tokens = 7
    s.metadata.subagent_depth = 2
    assert s.input_tokens == 5
    assert s.output_tokens == 7
    assert s.subagent_depth == 2


def test_no_display_messages_in_runtime_session():
    """Presentación sale del runtime (G2/D4): el Session nativo no tiene display_messages."""
    assert not hasattr(SessionMetadata(), "display_messages")


def test_background_task_ref_defaults():
    ref = BackgroundTaskRef(task_id="t1")
    assert ref.status == "pending"
    assert ref.description == ""
