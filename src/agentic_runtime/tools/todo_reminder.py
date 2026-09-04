"""Recordatorio 10/10 de la lista de tareas — homólogo del attachment `todo_reminder`
canónico (`utils/attachments.ts:254-257` la config, `:482-486` el tipo, `:893-897` el
cableado, `:3212-3264` la cuenta de turnos, `:3266-3317` las guardas; render en
`utils/messages.ts:3663-3679`).

`FIND-TODO-REMINDER-1`. Sin esto, un modelo que abandona su lista de tareas no vuelve a
ella: la tool existe, se publica, y nada le recuerda que está ahí. La conducta observada
en la corrida contra el modelo local fue exactamente ésa —dos `TodoWrite` iniciales y
después la lista muerta— y es el efecto que este módulo mide.

**Lo que de A NO se porta, dicho y no disfrazado.**

1. `isThinkingMessage` (`attachments.ts:3222-3224`) no tiene qué saltar aquí. En A un
   mensaje de asistente puede ser SÓLO bloques de pensamiento y no cuenta como turno; en
   B eso no es construible: `_assistant_message` (`loop/agent_loop.py:115-137`) devuelve
   `None` si no hay ni contenido ni `tool_calls`, y el pensamiento viaja en `thinking_blocks`
   DENTRO del mismo mensaje que el texto. No hay filtro «simplificado»: no hay caso.
2. `BRIEF_TOOL_NAME` (`:3285-3287`) es catálogo de producto de A (modo brief) y no existe
   en B. Guarda declarada ausente.
3. `appState.todos[agentId ?? getSessionId()]` (`:3313`). B lee la MISMA ranura única que
   escribe `TodoWrite` (`tools/native/todo_write.py:12`, `_TODOS_KEY`), sin clave por
   agente ni por sesión. La consecuencia hay que decirla: un subagente ve la lista del
   padre. Es `FIND-TODO`, paso 9 del orden de ataque, y está bloqueado por la decisión del
   depósito de estado (paso 7); no se abre aquí. Lo que sí queda garantizado es la
   coherencia interna: el recordatorio lee lo mismo que la tool escribe.

**Reconstrucción de la recencia.** A encuentra el recordatorio anterior por el `type` del
attachment, no por su texto. B hace lo mismo con el sidecar `TODO_REMINDER_KEY`: el texto
rendido lleva contenido de usuario (las tareas), así que re-parsearlo sería frágil por
construcción — la enfermedad de `FIND-DEFER-1`. Un sidecar perdido degrada a RE-recordar,
nunca a callar. El caller sólo lee `role`/`content` (`models/caller.py:58-94`), así que el
sidecar no llega al modelo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .native.todo_write import TODO_WRITE_TOOL_NAME

#: Las dos ventanas del canónico (`attachments.ts:254-257`), con su nombre.
TODO_REMINDER_CONFIG = {
    "TURNS_SINCE_WRITE": 10,
    "TURNS_BETWEEN_REMINDERS": 10,
}

#: Clave sidecar del mensaje del recordatorio (homóloga del `type: 'todo_reminder'` del
#: attachment canónico). No la lee el modelo.
TODO_REMINDER_KEY = "todo_reminder"

_AVISO = (
    "The TodoWrite tool hasn't been used recently. If you're working on tasks that would "
    "benefit from tracking progress, consider using the TodoWrite tool to track progress. "
    "Also consider cleaning up the todo list if has become stale and no longer matches "
    "what you are working on. Only use it if it's relevant to the current work. This is "
    "just a gentle reminder - ignore if not applicable. Make sure that you NEVER mention "
    "this reminder to the user\n"
)
_CABECERA_LISTA = "Here are the existing contents of your todo list:"


@dataclass(frozen=True)
class TodoReminder:
    """Recordatorio a emitir: la lista tal cual está, y su tamaño como dato."""

    todos: tuple[dict[str, Any], ...]
    item_count: int


def _escribe_la_lista(message: dict[str, Any]) -> bool:
    calls = message.get("tool_calls")
    if not isinstance(calls, (list, tuple)):
        return False
    for call in calls:
        if not isinstance(call, dict):
            continue
        function = call.get("function")
        name = function.get("name") if isinstance(function, dict) else call.get("name")
        if name == TODO_WRITE_TOOL_NAME:
            return True
    return False


def count_todo_reminder_turns(messages: list[dict[str, Any]]) -> tuple[int, int]:
    """Turnos de ASISTENTE desde la última escritura y desde el último recordatorio.

    Espejo de `getTodoReminderTurnCounts` (`attachments.ts:3212-3264`): barrido hacia
    atrás, corte cuando se han encontrado los dos, y —esto importa— la comprobación de
    la escritura ANTES del incremento, de modo que el turno en que se llamó a la tool no
    cuenta como turno transcurrido. Contarlo desplazaría la ventana respecto de A.

    Que sólo incrementen los mensajes de asistente es deliberado en A: el recordatorio
    mide vueltas del modelo, no mensajes del historial (que en B incluyen los `role:tool`
    y las propias inyecciones del runtime)."""
    desde_escritura = 0
    desde_recordatorio = 0
    escritura_vista = False
    recordatorio_visto = False
    for message in reversed(messages):
        if message.get("role") == "assistant":
            if not escritura_vista and _escribe_la_lista(message):
                escritura_vista = True
            if not escritura_vista:
                desde_escritura += 1
            if not recordatorio_visto:
                desde_recordatorio += 1
        elif not recordatorio_visto and TODO_REMINDER_KEY in message:
            recordatorio_visto = True
        if escritura_vista and recordatorio_visto:
            break
    return desde_escritura, desde_recordatorio


def render_todo_reminder(reminder: TodoReminder) -> str:
    """Texto del recordatorio (sin el envoltorio `<system-reminder>`, que pone el loop).

    Literal de `messages.ts:3663-3679`, corchetes incluidos: la sección de la lista es
    condicional, el aviso no."""
    texto = _AVISO
    lineas = "\n".join(
        f"{i + 1}. [{todo.get('status', '')}] {todo.get('content', '')}"
        for i, todo in enumerate(reminder.todos)
    )
    if lineas:
        texto += f"\n\n{_CABECERA_LISTA}\n\n[{lineas}]"
    return texto


def compute_todo_reminder(
    messages: list[dict[str, Any]],
    todos: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    todo_tool_available: bool,
) -> TodoReminder | None:
    """El recordatorio a emitir este turno, o `None` si no toca.

    `todo_tool_available` es la guarda del canónico (`attachments.ts:3277-3283`): sin la
    tool publicada en el pool de este turno el aviso sería inaccionable. Mira el pool
    PUBLICADO, no el registro — desde `FIND-POOL-1` no son lo mismo."""
    if not todo_tool_available:
        return None
    if not messages:
        return None
    desde_escritura, desde_recordatorio = count_todo_reminder_turns(messages)
    if desde_escritura < TODO_REMINDER_CONFIG["TURNS_SINCE_WRITE"]:
        return None
    if desde_recordatorio < TODO_REMINDER_CONFIG["TURNS_BETWEEN_REMINDERS"]:
        return None
    lista = tuple(todos)
    return TodoReminder(todos=lista, item_count=len(lista))


__all__ = [
    "TODO_REMINDER_CONFIG",
    "TODO_REMINDER_KEY",
    "TodoReminder",
    "compute_todo_reminder",
    "count_todo_reminder_turns",
    "render_todo_reminder",
]
