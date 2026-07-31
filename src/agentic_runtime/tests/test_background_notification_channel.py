"""
Tests del canal de notificaciones background y de `apply_notification` (`S21`).

**Reescritos en `C8`.** Antes ejercitaban `process_background_notification(session, n)`,
que `AC-07` retiró: escribía en `session.messages` mientras `_run_loop` reasigna
`session.messages = list(ctx.messages)` al terminar ⇒ el XML se descartaba en silencio.
Estos 7 tests pasaban verificando **la función**, no el comportamiento — el ejemplo
exacto de `L09`. La firma vigente es `apply_notification(messages, n)` sobre el
historial VIVO, y el comportamiento de punta a punta lo asevera `E9` del gate.

Cubre:
- Canal: escritura escopada por (scope, session_id), entrega en orden, drain destructivo
- `apply_notification`: XML completed/failed/killed, rol `user`, acumulación
- `_run_loop` no recibe ni referencia al objeto Session del padre
"""
from __future__ import annotations

import inspect

import pytest

from agentic_runtime.contracts.notifications import apply_notification
from agentic_runtime.execution.local.notification import (
    BackgroundNotification,
    drain_notifications,
    put_notification,
)


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
        parent_scope="u1",
        parent_session_id="s1",
        task_id="t1",
        status="completed",
        description="task",
        notification_text="done",
        final_text="",
    )
    defaults.update(kw)
    return BackgroundNotification(**defaults)


# ---------------------------------------------------------------------------
# Canal: comportamiento base
# ---------------------------------------------------------------------------

def test_drain_empty_returns_empty():
    assert drain_notifications("u1", "no-such-session") == []


def test_put_and_drain_single():
    n = _notif()
    put_notification(n)
    result = drain_notifications("u1", "s1")
    assert result == [n]


def test_drain_clears_channel():
    put_notification(_notif())
    drain_notifications("u1", "s1")
    assert drain_notifications("u1", "s1") == []


def test_drain_preserves_arrival_order():
    n1 = _notif(task_id="t1")
    n2 = _notif(task_id="t2")
    n3 = _notif(task_id="t3")
    put_notification(n1)
    put_notification(n2)
    put_notification(n3)
    result = drain_notifications("u1", "s1")
    assert [r.task_id for r in result] == ["t1", "t2", "t3"]


def test_channel_isolates_sessions():
    put_notification(_notif(parent_session_id="sA", task_id="tA"))
    put_notification(_notif(parent_session_id="sB", task_id="tB"))
    result_a = drain_notifications("u1", "sA")
    result_b = drain_notifications("u1", "sB")
    assert len(result_a) == 1 and result_a[0].task_id == "tA"
    assert len(result_b) == 1 and result_b[0].task_id == "tB"


# ---------------------------------------------------------------------------
# apply_notification: inyección XML sobre el HISTORIAL VIVO
# ---------------------------------------------------------------------------

def test_apply_injects_completed_xml():
    messages: list = []
    apply_notification(messages, _notif(status="completed", notification_text="result ok"))
    xml = messages[-1]["content"]
    assert 'status="completed"' in xml
    assert "result ok" in xml
    assert "<task-notification" in xml


def test_apply_injects_failed_xml():
    messages: list = []
    apply_notification(messages, _notif(status="failed", notification_text="Error: algo fallo"))
    xml = messages[-1]["content"]
    assert 'status="failed"' in xml
    assert "Error: algo fallo" in xml


def test_apply_injects_killed_xml():
    messages: list = []
    apply_notification(messages, _notif(status="killed", notification_text="killed by timeout"))
    assert 'status="killed"' in messages[-1]["content"]


def test_apply_xml_message_has_user_role():
    messages: list = []
    apply_notification(messages, _notif())
    assert messages[-1]["role"] == "user"


def test_apply_multiple_notifications_produce_multiple_messages():
    messages: list = []
    apply_notification(messages, _notif(task_id="t1", notification_text="first"))
    apply_notification(messages, _notif(task_id="t2", notification_text="second"))
    xmls = [m["content"] for m in messages]
    assert any("first" in x for x in xmls)
    assert any("second" in x for x in xmls)


def test_apply_operates_on_the_live_history_not_on_a_session():
    """La regresión que `AC-07` mide: la firma NO toma `Session`.

    Con `process_background_notification(session, n)` el XML acababa en un objeto que
    `_run_loop` sobreescribe al terminar el turno; con `apply_notification(messages, n)`
    acaba en la MISMA lista que el loop le pasa al modelo. Que la firma tome la lista es
    lo que hace imposible volver al fallo silencioso.
    """
    import inspect

    params = list(inspect.signature(apply_notification).parameters)
    assert params[0] == "messages"


# Nota honesta de `C8`: `process_background_notification` también recorría
# `session.metadata.background_tasks` para actualizar el `status` del ref. Ese recorrido
# **no se ha portado**, y no es una omisión disimulada: `background_tasks` no lo puebla
# NADIE en producción (sólo lo hacía el test que lo aseveraba), luego era un bucle sobre
# una lista siempre vacía. Reponerlo exige primero un productor del ref — unidad
# diferida ENTERA y nombrada (`L07`), no troceada aquí.
#
# display_messages y persistencia salieron ya antes (G2/D4): son proyección del
# consumidor, no del runtime.


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

