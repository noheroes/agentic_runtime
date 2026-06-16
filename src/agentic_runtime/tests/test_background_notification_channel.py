"""
Tests de BackgroundNotificationChannel y process_background_notification (Fase 8).

Cubre:
- Canal acepta escritura por session_id y entrega notificaciones en orden
- Canal vacío al drenar devuelve lista vacía
- Canal con múltiples notificaciones: todas llegan en orden
- Notificación completed/failed/killed produce XML correcto
- process_background_notification actualiza BackgroundTaskRef e inyecta XML
- _run_loop no recibe ni referencia al objeto Session del padre
"""
from __future__ import annotations

import inspect

import pytest

from agentic_runtime.execution.local.notification import (
    BackgroundNotification,
    drain_notifications,
    process_background_notification,
    put_notification,
)
from agentic_runtime.execution.session import BackgroundTaskRef, Session


# ---------------------------------------------------------------------------
# Fixture: limpiar canal entre tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_channel():
    import agentic_runtime.execution.local.notification as _m
    _m._channel.clear()
    yield
    _m._channel.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _notif(**kw) -> BackgroundNotification:
    defaults = dict(
        parent_session_id="s1",
        task_id="t1",
        status="completed",
        description="task",
        notification_text="done",
        final_text="",
        parent_execution_id="",
    )
    defaults.update(kw)
    return BackgroundNotification(**defaults)


# ---------------------------------------------------------------------------
# Canal: comportamiento base
# ---------------------------------------------------------------------------

def test_drain_empty_returns_empty():
    assert drain_notifications("no-such-session") == []


def test_put_and_drain_single():
    n = _notif()
    put_notification(n)
    result = drain_notifications("s1")
    assert result == [n]


def test_drain_clears_channel():
    put_notification(_notif())
    drain_notifications("s1")
    assert drain_notifications("s1") == []


def test_drain_preserves_arrival_order():
    n1 = _notif(task_id="t1")
    n2 = _notif(task_id="t2")
    n3 = _notif(task_id="t3")
    put_notification(n1)
    put_notification(n2)
    put_notification(n3)
    result = drain_notifications("s1")
    assert [r.task_id for r in result] == ["t1", "t2", "t3"]


def test_channel_isolates_sessions():
    put_notification(_notif(parent_session_id="sA", task_id="tA"))
    put_notification(_notif(parent_session_id="sB", task_id="tB"))
    result_a = drain_notifications("sA")
    result_b = drain_notifications("sB")
    assert len(result_a) == 1 and result_a[0].task_id == "tA"
    assert len(result_b) == 1 and result_b[0].task_id == "tB"


# ---------------------------------------------------------------------------
# process_background_notification: inyección XML
# ---------------------------------------------------------------------------

def test_process_injects_completed_xml(monkeypatch):
    s = Session()
    process_background_notification(s, _notif(status="completed", notification_text="result ok"))
    xml = s.messages[-1]["content"]
    assert 'status="completed"' in xml
    assert "result ok" in xml
    assert "<task-notification" in xml


def test_process_injects_failed_xml(monkeypatch):
    s = Session()
    process_background_notification(s, _notif(status="failed", notification_text="Error: algo fallo"))
    xml = s.messages[-1]["content"]
    assert 'status="failed"' in xml
    assert "Error: algo fallo" in xml


def test_process_injects_killed_xml(monkeypatch):
    s = Session()
    process_background_notification(s, _notif(status="killed", notification_text="killed by timeout"))
    xml = s.messages[-1]["content"]
    assert 'status="killed"' in xml


def test_process_xml_message_has_user_role(monkeypatch):
    s = Session()
    process_background_notification(s, _notif())
    assert s.messages[-1]["role"] == "user"


def test_process_multiple_notifications_produce_multiple_messages(monkeypatch):
    s = Session()
    process_background_notification(s, _notif(task_id="t1", notification_text="first"))
    process_background_notification(s, _notif(task_id="t2", notification_text="second"))
    xmls = [m["content"] for m in s.messages]
    assert any("first" in x for x in xmls)
    assert any("second" in x for x in xmls)


# ---------------------------------------------------------------------------
# process_background_notification: BackgroundTaskRef
# ---------------------------------------------------------------------------

def test_process_updates_background_task_ref(monkeypatch):
    s = Session()
    s.metadata.background_tasks.append(BackgroundTaskRef(task_id="t1", description="d"))
    process_background_notification(s, _notif(task_id="t1", status="completed"))
    assert s.metadata.background_tasks[0].status == "completed"


def test_process_updates_failed_ref(monkeypatch):
    s = Session()
    s.metadata.background_tasks.append(BackgroundTaskRef(task_id="t1", description="d"))
    process_background_notification(s, _notif(task_id="t1", status="failed"))
    assert s.metadata.background_tasks[0].status == "failed"


def test_process_missing_task_ref_is_noop(monkeypatch):
    s = Session()
    process_background_notification(s, _notif(task_id="no-such-task", status="failed"))
    # No debe lanzar excepción


# Nota: display_messages y persistencia salieron de process_background_notification
# (G2/D4) — son proyección/persistencia del consumidor, no del runtime. Por eso ya
# no hay tests de display aquí.


# ---------------------------------------------------------------------------
# Acoplamiento: _run_loop no referencia Session del padre
# ---------------------------------------------------------------------------

def test_run_loop_does_not_receive_parent_session_object():
    """_run_loop no debe aceptar parent_session como parámetro tipado."""
    from agentic_runtime.execution.local.runtime import LocalAgentRuntime
    sig = inspect.signature(LocalAgentRuntime._run_loop)
    assert "parent_session" not in sig.parameters, (
        "_run_loop no debe recibir parent_session; debe recibir parent_session_id: str | None"
    )


def test_run_loop_does_not_mutate_parent_session_directly():
    """_run_loop no debe acceder a parent_session.messages ni parent_session.metadata."""
    from agentic_runtime.execution.local.runtime import LocalAgentRuntime
    src = inspect.getsource(LocalAgentRuntime._run_loop)
    assert "parent_session.messages" not in src, (
        "_run_loop no debe mutar parent_session.messages directamente"
    )
    assert "parent_session.metadata" not in src, (
        "_run_loop no debe acceder a parent_session.metadata directamente"
    )

