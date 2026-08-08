"""Homologación 07·events — runtime `events/` vs el stream de mensajes SDK del canónico.

Contrapartes canónicas leídas ÍNTEGRAS: `entrypoints/sdk/coreSchemas.ts`
(`SDKMessageSchema`, unión de 24 variantes 1854-1881, cada variante campo-a-campo
1290-1806; `ModelUsageSchema` 17-28), `remote/sdkMessageAdapter.ts` (303,
`convertSDKMessage`/`isSessionEndMessage`/`getResultText`), `utils/hooks/hookEvents.ts`
(192, progreso de hook — el canónico lo funde en el stream), `query.ts`/`QueryEngine.ts`
(releídos: el agente serializa TODO su progreso como un `AsyncIterable<SDKMessage>`).

Tesis: el canónico NO tiene bus de eventos — tiene un STREAM serializado (`AsyncIterable
<SDKMessage>`) que ES el protocolo público core↔consumidor (REPL/SDK/CCR), un solo canal
ordenado con ~24 variantes. El runtime `EventBus` es un bus tipado in-proc (5 eventos) y
PARTE en 3 canales lo que el canónico unifica en 1 (EventBus push · registry.push_event
poll · ctx.messages). La homologación es del SEAM. Los gaps reales: (1) sin resultado
terminal con accounting — FIND-L2 aterriza aquí (DoneEvent.usage no se acumula ni se
surface; Session.usage/turn_count muertos; run()->None), (2) taxonomía 5 vs 24, (3) tres
canales sin serializador EventBus->SDKMessage, (4) Usage empobrecido y duplicado.

Los xfail(strict) codifican esos gaps: fallan HOY (evidencia del gap); al homologar,
pasan y se retira el marcador.
"""
from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import (
    DoneEvent,
    ErrorEvent,
    Event,
    EventBus,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from agentic_runtime.events.event_types import Usage as EventsUsage
from agentic_runtime.execution.session.session import Usage as SessionUsage
from agentic_runtime.loop import AgentLoop
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher

# --- Contraparte canónica: la unión SDKMessageSchema (coreSchemas.ts:1854) ---
# 24 variantes; el runtime declara 5 eventos. Enumeradas para el gap de taxonomía.
CANONICAL_SDK_MESSAGE_TYPES = {
    "assistant", "user", "user_replay", "result", "system_init", "stream_event",
    "compact_boundary", "status", "api_retry", "local_command_output",
    "hook_started", "hook_progress", "hook_response", "tool_progress",
    "auth_status", "task_notification", "task_started", "task_progress",
    "session_state_changed", "files_persisted", "tool_use_summary",
    "rate_limit_event", "elicitation_complete", "prompt_suggestion",
}

# Campos de ModelUsage (coreSchemas.ts:17) — el accounting canónico completo.
CANONICAL_MODEL_USAGE_FIELDS = {
    "inputTokens", "outputTokens", "cacheReadInputTokens",
    "cacheCreationInputTokens", "webSearchRequests", "costUSD",
    "contextWindow", "maxOutputTokens",
}


# --------------------------------------------------------------------------- #
# Helpers (espejo de test_hooks_homologation.py)
# --------------------------------------------------------------------------- #
def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id="", **kw):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


class RecordingTool:
    name = "echo"
    description = "Echoes input"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}  # noqa: RUF012
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(input)
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


def _make_registry(*tools) -> ToolRegistry:
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


def _loop(caller, reg, bus):
    return AgentLoop(
        model_caller=caller,
        tool_registry=reg,
        tool_dispatcher=ToolDispatcher(),
        event_bus=bus,
    )


def _one_tool_call(text="mundo"):
    return _make_caller(
        ToolCallEvent(tool_name="echo", tool_input={"text": text}, call_id="c1"),
        DoneEvent(stop_reason="stop", usage=EventsUsage(input_tokens=10, output_tokens=5)),
    )


# ========================================================================== #
# HOMOLOGADO (✅) — el bus tipado in-proc como primitiva de observación
# ========================================================================== #
@pytest.mark.asyncio
async def test_eventbus_delivers_typed_events_in_order():
    """✅ subscribe_all recibe el stream completo en orden de emisión (primitiva de
    consumo en vivo — el gancho del serializador a un wire tipo SSE/CCR)."""
    seen: list[str] = []

    async def sink(ev: Event) -> None:
        seen.append(type(ev).__name__)

    bus = EventBus()
    bus.subscribe_all(sink)
    for ev in (TokenEvent(content="h"), ToolCallEvent(tool_name="t", call_id="c"),
               ToolResultEvent(call_id="c", result="ok"), DoneEvent(stop_reason="stop")):
        await bus.emit(ev)

    assert seen == ["TokenEvent", "ToolCallEvent", "ToolResultEvent", "DoneEvent"]


@pytest.mark.asyncio
async def test_eventbus_subscribe_by_type_is_selective():
    """✅ subscribe(Type, h) sólo recibe ese tipo (registro por tipo exacto)."""
    tokens: list[str] = []

    async def on_token(ev: TokenEvent) -> None:
        tokens.append(ev.content)

    bus = EventBus()
    bus.subscribe(TokenEvent, on_token)
    await bus.emit(TokenEvent(content="a"))
    await bus.emit(DoneEvent(stop_reason="stop"))
    await bus.emit(TokenEvent(content="b"))

    assert tokens == ["a", "b"]


def test_event_is_frozen_immutable():
    """✅ Event base frozen — inmutable post-construcción (invariante del bus)."""
    ev = TokenEvent(content="x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.content = "y"


@pytest.mark.asyncio
async def test_eventbus_isolates_handler_errors():
    """✅ Un handler que lanza no rompe el stream para los demás (bus.py:42-45)."""
    delivered: list[str] = []

    async def boom(ev: Event) -> None:
        raise RuntimeError("handler roto")

    async def good(ev: Event) -> None:
        delivered.append("ok")

    bus = EventBus()
    bus.subscribe_all(boom)
    bus.subscribe_all(good)
    await bus.emit(TokenEvent(content="x"))  # no propaga la excepción

    assert delivered == ["ok"]


@pytest.mark.asyncio
async def test_loop_emits_execution_events_onto_bus():
    """✅ El loop deriva la ejecución al bus: Token/ToolCall/ToolResult/Done en vivo
    (espejo del progreso serializado del canónico, pero in-proc y tipado)."""
    seen: list[str] = []

    async def sink(ev: Event) -> None:
        seen.append(type(ev).__name__)

    bus = EventBus()
    bus.subscribe_all(sink)
    caller = _make_caller(
        TokenEvent(content="hola"),
        ToolCallEvent(tool_name="echo", tool_input={"text": "y"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    await _loop(caller, _make_registry(RecordingTool()), bus).run(
        "usa echo", ToolUseContext(session_id="s1")
    )

    assert "ToolResultEvent" in seen  # el loop lo sintetiza tras el dispatch
    # `#10`: el canal abre por lo que el runtime le mete al modelo (el prompt del
    # usuario) y por la frontera de turno, no por el primer token del modelo.
    assert seen[:3] == ["MessageEvent", "TurnStartEvent", "TokenEvent"], seen


# ========================================================================== #
# GAPS (xfail strict) — evidencia de lo NO homologado
# ========================================================================== #
@pytest.mark.xfail(strict=True, reason="FIND-EVT2: taxonomía 5 vs 24 — no existe un "
                   "evento terminal 'result' (SDKResultMessage) que agregue num_turns/"
                   "usage/cost/permission_denials al fin de la ejecución")
def test_taxonomy_has_terminal_result_event():
    import agentic_runtime.events as ev
    assert hasattr(ev, "ResultEvent"), "falta un evento terminal tipo SDKResultMessage"


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="FIND-EVT1/GAP-EVT2 (=FIND-L2): run() no devuelve "
                   "un resultado con accounting agregado; DoneEvent.usage per-turno no se "
                   "acumula ni se surface")
async def test_run_returns_result_with_aggregated_usage():
    result = await _loop(
        _one_tool_call(), _make_registry(RecordingTool()), EventBus()
    ).run("x", ToolUseContext(session_id="s1"))
    assert result is not None and hasattr(result, "usage"), (
        "run() debería devolver un resultado terminal con usage agregado"
    )


@pytest.mark.xfail(strict=True, reason="FIND-EVT5: Usage empobrecido — sin cache_read/"
                   "cache_creation tokens, webSearchRequests, costUSD, contextWindow, "
                   "maxOutputTokens (ModelUsage canónico)")
def test_usage_has_canonical_model_usage_fields():
    fields = {f.name for f in dataclasses.fields(EventsUsage)}
    # Nombres snake_case equivalentes a ModelUsage.
    expected = {
        "cache_read_input_tokens", "cache_creation_input_tokens",
        "web_search_requests", "cost_usd", "context_window", "max_output_tokens",
    }
    missing = expected - fields
    assert not missing, f"campos de accounting ausentes: {missing}"


@pytest.mark.xfail(strict=True, reason="FIND-EVT5: dos Usage divergentes (events i/o/"
                   "thinking != session i/o) — deberían ser un único Usage canónico")
def test_events_and_session_usage_are_unified():
    ev_fields = {f.name for f in dataclasses.fields(EventsUsage)}
    ss_fields = set(SessionUsage.model_fields)  # pydantic
    assert ev_fields == ss_fields, (
        f"Usage divergentes: events={ev_fields} vs session={ss_fields}"
    )


@pytest.mark.xfail(strict=True, reason="FIND-EVT4: ErrorEvent sin subtype — el canónico "
                   "distingue error_during_execution/max_turns/max_budget_usd/"
                   "max_structured_output_retries")
def test_error_event_has_subtype():
    fields = {f.name for f in dataclasses.fields(ErrorEvent)}
    assert "subtype" in fields, "ErrorEvent debería llevar subtype (SDKResultError)"


@pytest.mark.xfail(strict=True, reason="FIND-EVT6: sin tool_progress — no hay heartbeat "
                   "de tools largas (elapsed_time_seconds)")
def test_taxonomy_has_tool_progress_event():
    import agentic_runtime.events as ev
    assert hasattr(ev, "ToolProgressEvent")


@pytest.mark.xfail(strict=True, reason="FIND-EVT7: sin session_state_changed (idle/"
                   "running/requires_action) — la señal HITL de _ends_turn no se surface")
def test_taxonomy_has_session_state_event():
    import agentic_runtime.events as ev
    assert hasattr(ev, "SessionStateEvent")


@pytest.mark.asyncio
async def test_model_error_surfaces_live_on_bus():
    """✅ El ErrorEvent del modelo SÍ se emite al bus en vivo (agent_loop.py:248 emite
    todo evento antes de clasificar). Lo que falta (FIND-EVT4) es un RESULTADO terminal
    de error con subtype/accounting — el loop además entierra un '[error:...]' en
    ctx.messages, pero la observación en vivo del error está homologada."""
    seen: list[str] = []

    async def sink(ev: Event) -> None:
        seen.append(type(ev).__name__)

    bus = EventBus()
    bus.subscribe_all(sink)
    caller = _make_caller(ErrorEvent(message="boom"))
    await _loop(caller, _make_registry(RecordingTool()), bus).run(
        "x", ToolUseContext(session_id="s1")
    )
    assert "ErrorEvent" in seen


# ========================================================================== #
# C3 · S5 EventBus — VERIFICACIÓN del canal único ordenado (tramo 1)
# ========================================================================== #
#
# `TRAMO-1 §C3` clasifica esta capacidad como `existe-fiel`: **no se reconstruye,
# se verifica**. Su prueba pedida es «orden total del canal en los 3 runners +
# test de handler que lanza».
#
# ⚠ **interpretación declarada, no inferida en silencio:** la expresión «los 3
# runners» aparece UNA sola vez en todo el corpus (`TRAMO-1.md:82`) y no está
# definida en ningún sitio. Se lee contra el campo *cableado* de la misma ficha
# —«caller/loop/runtime emiten»— como **los tres emisores del canal**, que es lo
# que sí está verificado leyendo la fuente 1→EOF en esta ventana:
#
#   1. el **caller** (`S1`) produce los eventos del stream del proveedor;
#   2. el **loop** los reemite en vivo (`agent_loop.py:312`) y añade los suyos
#      —`ToolResultEvent` tras cada dispatch (`:405`) y tras un bloqueo de hook
#      (`:393`)—;
#   3. el **runtime** suscribe sus propios sumideros al mismo bus
#      (`runtime.py:326-330`: registry por tipo, `on_event` global) .
#
# ⚠ **hallazgo de la verificación, escrito y no maquillado:** el orden real del
# canal **no** es el `Init→…→Result` que enuncia la ficha. No existen `InitEvent`
# ni `ResultEvent` (la taxonomía son 5, ver `FIND-EVT*` arriba), y el `DoneEvent`
# llega **antes** que los `ToolResultEvent` del mismo turno, porque `Done` cierra
# el mensaje del asistente y los resultados de tools se despachan después. Es
# coherente con el canónico —allí el mensaje del asistente con sus `tool_use`
# precede a los `tool_result`— pero **no** con la frase de la ficha, que describe
# un terminal que este canal no tiene. Queda aseverado abajo: si alguien añade un
# `ResultEvent` terminal, este test se pone rojo y obliga a revisar la ficha.

@pytest.mark.asyncio
async def test_c3_bus_channel_is_totally_ordered_across_the_three_emitters():
    """Orden TOTAL: los tres emisores comparten un único canal secuencial.

    Se observa por las dos vías de suscripción a la vez (`subscribe_all` y
    `subscribe` por tipo) porque son caminos distintos dentro de `emit`
    (`bus.py:40` concatena los tipados ANTES que los globales): si sólo se mirara
    uno, un reordenamiento entre ambos pasaría inadvertido.
    """
    order: list[str] = []
    tool_results_by_type: list[str] = []

    async def _all(ev: Event) -> None:
        order.append(type(ev).__name__)

    async def _typed(ev: ToolResultEvent) -> None:
        tool_results_by_type.append(ev.call_id)

    bus = EventBus()
    bus.subscribe(ToolResultEvent, _typed)
    bus.subscribe_all(_all)

    caller = _make_caller(
        TokenEvent(content="pen"),
        TokenEvent(content="sando"),
        ToolCallEvent(tool_name="echo", tool_input={"text": "hola"}, call_id="c1"),
        DoneEvent(stop_reason="stop", usage=EventsUsage(input_tokens=1, output_tokens=1)),
    )
    tool = RecordingTool()
    await _loop(caller, _make_registry(tool), bus).run("x", ToolUseContext(session_id="s1"))

    # 1. el turno corrió de verdad (si no, el orden de abajo sería el de la nada)
    assert tool.calls == [{"text": "hola"}]

    # 2. orden total, exacto y completo del canal — no «contiene», no «al menos».
    #    Ampliado al pagar `#10`/`FIND-STREAM-1`: el canal ya no empieza en el primer
    #    token. Lleva TAMBIÉN lo que el runtime inyecta —el prompt del usuario y el
    #    turno del asistente como mensajes— y la frontera de turno, que es la propiedad
    #    canónica de `query.ts` (se yieldea lo mismo que se persiste, `:1588`/`:1610`).
    assert order == [
        "MessageEvent",     # prompt del usuario, entrado a la historia
        "TurnStartEvent",   # frontera de turno + plan de tools como dato
        "TokenEvent", "TokenEvent", "ToolCallEvent", "DoneEvent",
        "MessageEvent",     # turno del asistente ya ensamblado
        "ToolResultEvent",  # el resultado NO duplica `MessageEvent`: ya viaja aquí
    ], order

    # 3. el `ToolResultEvent` del loop llegó a AMBAS vías, y a la tipada primero
    #    (es lo que `bus.py:40` promete: tipados, luego globales).
    assert tool_results_by_type == ["c1"]

    # 4. el terminal que la ficha enuncia NO existe: aseverado, no narrado.
    import agentic_runtime.events as _ev
    assert not hasattr(_ev, "ResultEvent") and not hasattr(_ev, "InitEvent"), (
        "apareció un evento terminal: `TRAMO-1 §C3` («Init→…→Result») ya no describe "
        "este canal y hay que reconciliar la ficha"
    )


@pytest.mark.asyncio
async def test_c3_a_throwing_handler_does_not_take_down_the_others():
    """Un handler que revienta no tumba a los demás **ni corta el canal**.

    Las dos mitades importan y sólo juntas prueban el aislamiento: que los otros
    handlers del MISMO evento sigan recibiéndolo, y que los eventos POSTERIORES
    sigan llegando (un `emit` que propagara mataría el turno entero).
    """
    survivors: list[str] = []
    late: list[str] = []

    async def _boom(ev: Event) -> None:
        raise RuntimeError("handler roto a propósito")

    async def _survivor(ev: Event) -> None:
        survivors.append(type(ev).__name__)

    async def _typed_late(ev: DoneEvent) -> None:
        late.append(ev.stop_reason)

    bus = EventBus()
    bus.subscribe(TokenEvent, _boom)      # revienta por tipo…
    bus.subscribe(DoneEvent, _typed_late)
    bus.subscribe_all(_boom)              # …y también en el canal global
    bus.subscribe_all(_survivor)

    caller = _make_caller(
        TokenEvent(content="a"),
        DoneEvent(stop_reason="stop", usage=EventsUsage(input_tokens=1, output_tokens=1)),
    )
    ctx = ToolUseContext(session_id="s1")
    await _loop(caller, _make_registry(RecordingTool()), bus).run("x", ctx)

    # 1. el handler sano recibió TODO, pese a que otro reventó en cada evento
    assert survivors == [
        "MessageEvent", "TurnStartEvent", "TokenEvent", "DoneEvent", "MessageEvent",
    ], survivors
    # 2. y el canal siguió vivo después de la excepción (evento posterior, vía tipada)
    assert late == ["stop"]
    # 3. el turno terminó normal: la excepción no escapó al loop
    assert ctx.turn_count == 1
