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
    defaults = {
        "parent_scope": "u1",
        "parent_session_id": "s1",
        "task_id": "t1",
        "status": "completed",
        "description": "task",
        "notification_text": "done",
        "final_text": "",
    }
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
    """La regresión que `AC-07` mide: el XML acaba en la lista que el loop le pasa al
    modelo, no en un objeto que se descarta al terminar el turno.

    **Reescrito (patrón `H-L4`).** La versión anterior aseveraba la FIRMA
    (`params[0] == "messages"`), que es forma: el día que alguien renombrara el primer
    parámetro sin tocar la conducta el test se pondría rojo sin que nada se rompiera, y
    —peor— el día que la conducta volviese al sumidero de copia manteniendo el nombre,
    seguiría verde. Lo que hace imposible el fallo silencioso no es cómo se llama el
    parámetro: es que la lista mutada sea la MISMA que viaja al modelo. Eso es lo que se
    asevera ahora, por identidad de objeto y por lo que el caller llega a leer.
    """
    historial_vivo: list = []
    apply_notification(historial_vivo, _notif(notification_text="el hijo terminó"))

    assert len(historial_vivo) == 1, "muta la lista recibida, no una copia"
    # Identidad: la mutación es in-place sobre el objeto del llamante.
    alias = historial_vivo
    apply_notification(historial_vivo, _notif(task_id="t2"))
    assert alias is historial_vivo and len(alias) == 2


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
# `_drain_notifications`: el CABLE del loop (`S21`/`H-5`)
#
# Lo de arriba prueba el canal y `apply_notification` por separado. Que el LOOP los una
# —que drene, que drene con la clave correcta, que sólo drene la raíz y que lo haga antes
# del mensaje del usuario— no lo aseveraba nadie salvo `E9` del gate, que necesita Azure.
# Sin esto, el runtime podía dejar de drenar y toda la batería barata seguía verde.
# ---------------------------------------------------------------------------

class _NotifyingCaller:
    """Registra el historial EXACTO que recibe el modelo en cada turno."""

    def __init__(self, turnos: int = 1) -> None:
        self._turnos = turnos
        self.historiales: list[list[dict]] = []

    async def complete(self, messages, tools, *, stop=None, model_id="", **kw):
        self.historiales.append([dict(m) for m in messages])
        n = len(self.historiales)

        async def _gen():
            from agentic_runtime.events import DoneEvent as _D
            yield _D(stop_reason="tool_calls" if n < self._turnos else "stop")

        return _gen()


def _loop_con_canal(caller, **kw):
    from agentic_runtime.execution.local.notification import InProcessNotificationSink
    from agentic_runtime.loop.agent_loop import AgentLoop
    return AgentLoop(model_caller=caller, notification_sink=InProcessNotificationSink(), **kw)


def _ctx_raiz(**kw):
    from agentic_runtime.context.tool_use import ToolUseContext
    from agentic_runtime.contracts.identity import Scope
    kw.setdefault("scope", Scope("u1"))
    return ToolUseContext(session_id="s1", **kw)


async def test_el_loop_drena_el_canal_y_el_XML_llega_al_MODELO():
    """El efecto que importa no es que el XML esté en `ctx.messages`: es que el modelo lo
    LEA. Se asevera sobre el historial que recibió el caller, no sobre el del final."""
    put_notification(_notif(notification_text="el hijo encontró 3 ficheros"))
    caller = _NotifyingCaller()
    ctx = _ctx_raiz()

    await _loop_con_canal(caller).run("¿qué hay?", ctx)

    assert caller.historiales, "el modelo fue llamado"
    contenidos = [m["content"] for m in caller.historiales[0]]
    assert any("el hijo encontró 3 ficheros" in c for c in contenidos), \
        "el XML de la notificación tiene que viajar al modelo, no quedarse en un sumidero"


async def test_el_drenaje_va_ANTES_del_mensaje_del_usuario():
    """Orden declarado en el docstring de `_drain_notifications`: son hechos ya ocurridos;
    el modelo debe leer que su subagente terminó **antes** de leer lo que se le pide
    ahora. El orden es conducta, no cosmética: invertido, el modelo interpreta la
    notificación como respuesta a la petición nueva."""
    put_notification(_notif(notification_text="ya terminé"))
    caller = _NotifyingCaller()

    await _loop_con_canal(caller).run("PROMPT-DEL-USUARIO", _ctx_raiz())

    contenidos = [m["content"] for m in caller.historiales[0]]
    i_notif = next(i for i, c in enumerate(contenidos) if "ya terminé" in c)
    i_user = next(i for i, c in enumerate(contenidos) if c == "PROMPT-DEL-USUARIO")
    assert i_notif < i_user, f"la notificación debe preceder al prompt (notif={i_notif}, user={i_user})"


async def test_un_SUBAGENTE_no_drena_y_la_notificacion_sigue_disponible_para_el_padre():
    """Sólo la raíz drena. Padre e hijo comparten la clave `(scope, session_id)` porque el
    fork hereda ambas, así que un subagente que drenase **se comería la notificación de su
    hermano** y el padre no se enteraría nunca.

    La aserción fuerte no es «el hijo no la ve»: es que tras correr el hijo la
    notificación **sigue en el canal** — si el hijo la hubiera drenado, el drain
    destructivo la habría consumido y el padre encontraría el canal vacío.
    """
    put_notification(_notif(notification_text="del hermano"))
    caller = _NotifyingCaller()

    ctx_hijo = _ctx_raiz(is_subagent=True)
    await _loop_con_canal(caller).run("trabajo del hijo", ctx_hijo)

    assert all("del hermano" not in m["content"] for m in caller.historiales[0])
    # …y el padre la recibe entera después.
    caller_padre = _NotifyingCaller()
    await _loop_con_canal(caller_padre).run("¿y bien?", _ctx_raiz())
    assert any("del hermano" in m["content"] for m in caller_padre.historiales[0])


async def test_el_loop_drena_con_la_clave_del_ctx_no_con_otra():
    """La clave es el par `(scope, session_id)` (`C9`/`ID-3`). Un loop cuyo ctx tiene otro
    scope no debe llevarse la notificación ajena — es la frontera de aislamiento."""
    put_notification(_notif(parent_scope="u1", parent_session_id="s1", notification_text="de u1"))

    from agentic_runtime.contracts.identity import Scope
    caller_ajeno = _NotifyingCaller()
    ctx_ajeno = _ctx_raiz(scope=Scope("OTRO-SCOPE"))
    await _loop_con_canal(caller_ajeno).run("hola", ctx_ajeno)
    assert all("de u1" not in m["content"] for m in caller_ajeno.historiales[0]), \
        "un scope distinto NO puede leer la notificación de otro"

    # Control positivo: con la clave correcta sí llega ⇒ lo que corta arriba es el scope.
    caller_propio = _NotifyingCaller()
    await _loop_con_canal(caller_propio).run("hola", _ctx_raiz())
    assert any("de u1" in m["content"] for m in caller_propio.historiales[0])


async def test_se_drena_una_vez_por_run_no_una_por_turno():
    """Frecuencia declarada: una por `run()` = una por prompt de usuario (el canónico las
    mete como *attachment* del input), no una por turno de modelo. Con dos turnos el XML
    debe aparecer UNA sola vez en el historial que ve el modelo."""
    put_notification(_notif(notification_text="una sola vez"))
    caller = _NotifyingCaller(turnos=2)

    await _loop_con_canal(caller).run("hola", _ctx_raiz())

    assert len(caller.historiales) == 2, "hicieron falta dos turnos para que la prueba mida algo"
    apariciones = [c for c in (m["content"] for m in caller.historiales[-1]) if "una sola vez" in c]
    assert len(apariciones) == 1


async def test_sin_canal_inyectado_el_loop_se_comporta_como_antes_de_existir_la_costura():
    """Control negativo del default: `notification_sink=None` ⇒ ni drena ni consume nada
    del canal global (el runtime sin la costura no puede robar notificaciones ajenas)."""
    from agentic_runtime.loop.agent_loop import AgentLoop

    put_notification(_notif(notification_text="intacta"))
    caller = _NotifyingCaller()
    await AgentLoop(model_caller=caller).run("hola", _ctx_raiz())

    assert all("intacta" not in m["content"] for m in caller.historiales[0])
    assert len(drain_notifications("u1", "s1")) == 1, "la notificación sigue en el canal"


# ---------------------------------------------------------------------------
# Acoplamiento: _run_loop no referencia Session del padre
#
# Los dos de abajo son ESTRUCTURALES (introspección de firma / de fuente): necesarios,
# **no suficientes**. Su contraparte funcional es el bloque de `_drain_notifications` de
# arriba, que mide el efecto; se conservan como guarda barata del patrón de regresión.
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

