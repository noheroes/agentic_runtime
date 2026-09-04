"""`FIND-TODO-REMINDER-1` — el recordatorio 10/10 de la lista de tareas.

Lo que se mide no es que exista una función que sepa contar turnos: es que, corriendo el
loop, el modelo RECIBA el recordatorio cuando lleva diez turnos sin tocar la lista. Por eso
casi todo se afirma sobre `ScriptedCaller.seen_messages` —lo que el modelo vio— y no sobre
el retorno de un auxiliar; un test sobre `render_todo_reminder` seguiría verde con el loop
sin cablear, que es el modo de fallo de `L09`.

Canónico: `utils/attachments.ts:254-257` (la config 10/10), `:482-486` (el attachment),
`:893-897` (cableado en `allThreadAttachments` — hilo entero, subagentes incluidos),
`:3212-3264` (`getTodoReminderTurnCounts`), `:3266-3317` (`getTodoReminderAttachments`) y
`utils/messages.ts:3663-3679` (el render literal).
"""
from __future__ import annotations

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.tools.native.todo_write import TodoWriteTool
from agentic_runtime.tools.registry import ToolRegistry
from agentic_runtime.tools.todo_reminder import (
    TODO_REMINDER_CONFIG,
    TODO_REMINDER_KEY,
    compute_todo_reminder,
    count_todo_reminder_turns,
)

from .test_loop_homologation import RecordingTool, ScriptedCaller

_MARCA = "The TodoWrite tool hasn't been used recently."
_CABECERA_LISTA = "Here are the existing contents of your todo list:"


def _habla() -> list:
    """Un turno de modelo con contenido. Sin él no hay mensaje de asistente
    (`loop/agent_loop.py:115-137`) y no habría turnos que contar: el andamio, no el
    módulo, sería quien decidiera que nunca se recuerda."""
    return [TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]


def _loop(*, con_todo_write: bool = True, script=None) -> tuple[AgentLoop, ScriptedCaller]:
    reg = ToolRegistry()
    reg.register(TodoWriteTool() if con_todo_write else RecordingTool("echo"))
    caller = ScriptedCaller(script or [_habla() for _ in range(40)])
    return (
        AgentLoop(
            model_caller=caller,
            tool_registry=reg,
            tool_dispatcher=ToolDispatcher(),
        ),
        caller,
    )


def _recordatorio(caller: ScriptedCaller, llamada: int) -> str:
    """Recordatorio inyectado ANTES de esa llamada al modelo — no el que arrastra
    la historia, que es acumulativa y reencontraría siempre el primero."""
    vistos = caller.seen_messages
    idx = llamada if llamada >= 0 else len(vistos) + llamada
    previos = len(vistos[idx - 1]) if idx > 0 else 0
    nuevos = vistos[idx][previos:]
    bloques = [
        m.get("content", "")
        for m in nuevos
        if m.get("role") == "user" and _MARCA in m.get("content", "")
    ]
    return bloques[0] if bloques else ""


async def _correr(loop: AgentLoop, ctx: ToolUseContext, veces: int) -> None:
    for i in range(veces):
        await loop.run(f"turno {i}", ctx)


# ──────────────────────────────────────────────────────────────────────────────
# La conducta: el recordatorio llega al modelo, y cuándo
# ──────────────────────────────────────────────────────────────────────────────

async def test_no_se_recuerda_antes_de_los_diez_turnos():
    """`attachments.ts:3305-3311`: por debajo del umbral no se emite. Un recordatorio
    en cada turno sería ruido permanente en el contexto, no un recordatorio."""
    loop, caller = _loop()
    ctx = ToolUseContext(session_id="s")
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"])

    assert all(
        _recordatorio(caller, i) == "" for i in range(len(caller.seen_messages))
    ), "se recordó antes de tiempo"


async def test_el_recordatorio_llega_al_modelo_al_cumplirse_el_umbral():
    """El hueco entero, medido por su efecto: sin esto, un modelo que abandona su lista
    de tareas no vuelve a ella nunca."""
    loop, caller = _loop()
    ctx = ToolUseContext(session_id="s")
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 1)

    texto = _recordatorio(caller, -1)
    assert texto, "el modelo no recibió NINGÚN recordatorio tras diez turnos"
    assert "<system-reminder>" in texto
    assert "consider using the TodoWrite tool to track progress" in texto
    assert "NEVER mention this reminder to the user" in texto


async def test_sin_todo_write_publicada_no_se_recuerda():
    """Guarda del canónico (`attachments.ts:3277-3283`): sin la tool el aviso es
    inaccionable. Mira el pool PUBLICADO, no el registro — `FIND-POOL-1`."""
    loop, caller = _loop(con_todo_write=False)
    ctx = ToolUseContext(session_id="s")
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 2)

    assert all(_recordatorio(caller, i) == "" for i in range(len(caller.seen_messages)))


async def test_el_subagente_tambien_lo_recibe():
    """A lo cablea en `allThreadAttachments` (`:893-897`), no en los del hilo principal:
    el subagente que lleva su propia lista necesita el mismo recordatorio."""
    loop, caller = _loop()
    ctx = ToolUseContext(session_id="s", subagent_depth=1, is_subagent=True)
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 1)

    assert _recordatorio(caller, -1) != ""


async def test_no_se_repite_antes_de_otros_diez_turnos():
    """La segunda ventana (`TURNS_BETWEEN_REMINDERS`). Sin ella el recordatorio se
    emitiría en CADA turno posterior al décimo, porque el contador de escritura ya
    no baja nunca."""
    loop, caller = _loop()
    ctx = ToolUseContext(session_id="s")
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 3)

    emitidos = [
        i for i in range(len(caller.seen_messages)) if _recordatorio(caller, i) != ""
    ]
    assert emitidos == [TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"]], emitidos


async def test_una_escritura_de_la_lista_reinicia_la_cuenta():
    """`attachments.ts:3232-3241`: el contador mide turnos DESDE la última escritura.

    La escritura va en el turno 6 de doce: sin el reinicio, al duodécimo se habrían
    acumulado once turnos de asistente y el recordatorio habría salido —el hermano
    `test_el_recordatorio_llega_al_modelo_al_cumplirse_el_umbral` lo fija."""
    guion = [
        _habla(),
        _habla(),
        _habla(),
        _habla(),
        _habla(),
        [
            ToolCallEvent(
                tool_name="TodoWrite",
                tool_input={
                    "todos": [
                        {
                            "id": "1",
                            "content": "Homologar el recordatorio",
                            "status": "in_progress",
                            "priority": "high",
                        }
                    ]
                },
                call_id="c1",
            ),
            DoneEvent(stop_reason="tool_calls"),
        ],
    ] + [_habla() for _ in range(20)]
    loop, caller = _loop(script=guion)
    ctx = ToolUseContext(session_id="s")
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 2)

    assert all(
        _recordatorio(caller, i) == "" for i in range(len(caller.seen_messages))
    ), "recordó pese a haberse escrito la lista"


# ──────────────────────────────────────────────────────────────────────────────
# El texto: literal del canónico
# ──────────────────────────────────────────────────────────────────────────────

async def test_la_lista_viaja_con_el_formato_del_canonico():
    """`messages.ts:3667-3672`: `N. [estado] contenido`, y el bloque entre corchetes.
    El formato lo lee un modelo entrenado con el de A; no es uno propio."""
    loop, caller = _loop()
    ctx = ToolUseContext(session_id="s")
    ctx.app_state.native["todos"] = [
        {"id": "1", "content": "Leer el canónico", "status": "completed", "priority": "high"},
        {
            "id": "2",
            "content": "Pagar el recordatorio",
            "status": "in_progress",
            "priority": "high",
        },
    ]
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 1)

    texto = _recordatorio(caller, -1)
    assert _CABECERA_LISTA in texto
    assert "[1. [completed] Leer el canónico\n2. [in_progress] Pagar el recordatorio]" in texto


async def test_con_la_lista_vacia_se_avisa_sin_la_seccion_de_tareas():
    """`messages.ts:3673-3675`: la sección es condicional, el aviso no. Es justo el caso
    en que más falta hace: el modelo que nunca creó lista."""
    loop, caller = _loop()
    ctx = ToolUseContext(session_id="s")
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 1)

    texto = _recordatorio(caller, -1)
    assert _MARCA in texto
    assert _CABECERA_LISTA not in texto


# ──────────────────────────────────────────────────────────────────────────────
# El sidecar — la lección de `FIND-DEFER-1`
# ──────────────────────────────────────────────────────────────────────────────

async def test_el_sidecar_es_dato_y_no_lo_ve_el_modelo():
    """La recencia se reconstruye del DATO, como A la reconstruye del `type` del
    attachment. Re-parsear el texto sería frágil por construcción: lleva contenido
    de usuario (las tareas), que puede contener cualquier cosa."""
    loop, caller = _loop()
    ctx = ToolUseContext(session_id="s")
    await _correr(loop, ctx, TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"] + 1)

    portadores = [m for m in ctx.messages if TODO_REMINDER_KEY in m]
    assert len(portadores) == 1
    assert portadores[0][TODO_REMINDER_KEY] == {"item_count": 0}
    assert TODO_REMINDER_KEY not in _recordatorio(caller, -1)


def test_un_sidecar_perdido_degrada_a_re_recordar_nunca_a_callar():
    """Round-trip de persistencia que descarte claves desconocidas: se vuelve a
    recordar. La degradación segura es repetir, no omitir."""
    historia = [{"role": "assistant", "content": f"t{i}"} for i in range(10)]
    historia.append(
        {"role": "user", "content": f"<system-reminder>\n{_MARCA}\n</system-reminder>"}
    )
    reminder = compute_todo_reminder(historia, [], todo_tool_available=True)
    assert reminder is not None


def test_el_turno_de_la_escritura_no_cuenta_como_turno_transcurrido():
    """`attachments.ts:3232-3241`: la comprobación del `tool_use` va ANTES del
    incremento. Contarlo desplazaría la ventana un turno respecto de A."""
    historia: list[dict] = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "c1", "function": {"name": "TodoWrite", "arguments": "{}"}}
            ],
        }
    ]
    historia += [{"role": "assistant", "content": f"t{i}"} for i in range(9)]
    desde_escritura, _ = count_todo_reminder_turns(historia)
    assert desde_escritura == 9


def test_sin_mensajes_no_se_recuerda():
    """`attachments.ts:3288-3290`."""
    assert compute_todo_reminder([], [], todo_tool_available=True) is None
