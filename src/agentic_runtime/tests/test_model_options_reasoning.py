"""`B5` — la costura `S1` deja de ser una tubería vacía: razonamiento de ida y de vuelta.

Tres hallazgos se cierran aquí, y cada prueba mide uno:

* `FIND-RT-REASON-1` — los items de razonamiento no volvían NUNCA al motor. El propio
  fabricante lo dice: «we highly recommend you pass back any reasoning items returned
  with the last function call … this allows the model to continue its reasoning process».
  Sin ellos el modelo re-razona desde cero en cada tool call.
* `FIND-MODELS-OFF-1` — `thinking.enabled=False` era un no-op: `clamp_thinking_level`
  ESCALA lo no soportado, así que un `off` mudo se volvía `minimal` (o el default
  `medium` del motor) sin una sola señal.
* `FIND-MODELS-BUDGET-1` — `thinking_budgets` viaja en `SimpleStreamOptions` pero sólo
  lo leen cuatro APIs; en `azure-openai-responses` el provider re-adjunta el nivel y
  tira el presupuesto **callando**.

El criterio que ordena las tres: lo que no se puede expresar se RECHAZA. Un puente que
recibe una opción y la descarta en silencio es exactamente el defecto que el contrato
`ModelOptions` existe para eliminar.
"""
from __future__ import annotations

import agentic_models
import pytest
from agentic_models import get_registry, register_builtins

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.events import DoneEvent, ThinkingEvent, TokenEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.models.caller import AgenticModelsCaller, _dict_messages_to_context
from agentic_runtime.models.protocol import (
    Effort,
    ModelOptions,
    ThinkingConfig,
    UnsupportedModelOptionError,
)
from agentic_runtime.tools import ToolRegistry
from agentic_runtime.tools.dispatcher import ToolDispatcher

register_builtins()

#: El de producción: `reasoning=True` y `thinking_level_map={'off': None, …}` — es decir,
#: sabe razonar y NO sabe apagarse. Las dos caras que hacen falta aquí.
_AZURE = ("azure-openai-responses", "gpt-5.4-mini")


def _caller(**kwargs):
    return AgenticModelsCaller(model=get_registry().get_by_provider(*_AZURE), **kwargs)


def _empty_stream():
    async def _gen():
        return
        yield  # pragma: no cover — marca _gen como async generator
    return _gen()


async def _drain(agen):
    return [event async for event in agen]


# ---------------------------------------------------------------------------
# El nivel llega al motor — y sólo cuando alguien lo pidió
# ---------------------------------------------------------------------------

async def test_effort_reaches_the_engine_as_a_reasoning_level(monkeypatch):
    seen: list[object] = []
    monkeypatch.setattr(agentic_models, "stream_simple", lambda m, c, o: seen.append(o) or _empty_stream())
    monkeypatch.setattr(agentic_models, "stream", lambda m, c, o: pytest.fail("con effort se usa stream_simple"))

    await _drain(await _caller().complete([{"role": "user", "content": "hi"}], [], effort=Effort.HIGH))

    assert len(seen) == 1
    assert seen[0].reasoning == "high"


async def test_without_options_nothing_is_invented(monkeypatch):
    """Sin petición no hay `reasoning`: el motor aplica su default y nadie lo suplanta."""
    seen: list[object] = []
    monkeypatch.setattr(agentic_models, "stream", lambda m, c, o: seen.append(o) or _empty_stream())
    monkeypatch.setattr(
        agentic_models, "stream_simple",
        lambda m, c, o: pytest.fail("sin opciones no se pasa por el camino `simple`"),
    )

    await _drain(await _caller().complete([{"role": "user", "content": "hi"}], []))

    assert len(seen) == 1
    assert getattr(seen[0], "reasoning", None) is None


# ---------------------------------------------------------------------------
# Lo inexpresable se rechaza, no se descarta
# ---------------------------------------------------------------------------

async def test_turning_thinking_off_is_refused_when_the_provider_blocks_it(monkeypatch):
    monkeypatch.setattr(agentic_models, "stream_simple", lambda m, c, o: _empty_stream())
    monkeypatch.setattr(agentic_models, "stream", lambda m, c, o: _empty_stream())

    with pytest.raises(UnsupportedModelOptionError, match="off"):
        await _drain(
            await _caller().complete(
                [{"role": "user", "content": "hi"}], [],
                thinking=ThinkingConfig(enabled=False),
            )
        )


async def test_a_token_budget_is_refused_where_the_api_has_no_field_for_it(monkeypatch):
    monkeypatch.setattr(agentic_models, "stream_simple", lambda m, c, o: _empty_stream())
    monkeypatch.setattr(agentic_models, "stream", lambda m, c, o: _empty_stream())

    with pytest.raises(UnsupportedModelOptionError, match="budget_tokens"):
        await _drain(
            await _caller().complete(
                [{"role": "user", "content": "hi"}], [],
                effort=Effort.HIGH,
                thinking=ThinkingConfig(budget_tokens=4096),
            )
        )


async def test_a_budget_without_a_level_is_refused_even_where_the_api_reads_it(monkeypatch):
    """`anthropic-messages` SÍ lee `thinking_budgets`… pero sólo si hay nivel.

    Sin `reasoning` el puente ni siquiera entra en el camino `simple`, así que el
    presupuesto se perdería igual. Se rechaza en vez de fingir que se aplicó.
    """
    monkeypatch.setattr(agentic_models, "stream_simple", lambda m, c, o: _empty_stream())
    monkeypatch.setattr(agentic_models, "stream", lambda m, c, o: _empty_stream())
    caller = AgenticModelsCaller(
        model=get_registry().get_by_provider("anthropic", "claude-sonnet-4-5")
    )

    with pytest.raises(UnsupportedModelOptionError, match="sin `effort`"):
        await _drain(
            await caller.complete(
                [{"role": "user", "content": "hi"}], [],
                thinking=ThinkingConfig(budget_tokens=4096),
            )
        )


# ---------------------------------------------------------------------------
# El round-trip: el razonamiento vuelve, y sólo el que es reproducible
# ---------------------------------------------------------------------------

def _assistant_parts(message: dict[str, object], model_id: str = "gpt-5.4-mini"):
    context = _dict_messages_to_context([message], [], None, model_id)
    return context.messages[0].content


def test_reasoning_travels_back_with_its_signature_and_ahead_of_the_call():
    parts = _assistant_parts({
        "role": "assistant",
        "content": "voy a leerlo",
        "thinking_blocks": [
            {"thinking": "razoné", "signature": '{"id":"rs_1"}', "model_id": "gpt-5.4-mini"}
        ],
        "tool_calls": [
            {"id": "c1", "function": {"name": "read_file", "arguments": '{"path":"a"}'}}
        ],
    })

    assert [p.type for p in parts] == ["thinking", "text", "toolCall"]
    assert parts[0].thinking == "razoné"
    # La firma es el ITEM ENTERO, opaco: es lo que continúa la cadena, no el texto.
    assert parts[0].thinking_signature == '{"id":"rs_1"}'


def test_a_signature_from_another_model_is_dropped():
    """`query.ts:924` (`stripSignatureBlocks`): las firmas están ATADAS al modelo.

    Replicarlas contra otro modelo no es una degradación: es un 400.
    """
    parts = _assistant_parts({
        "role": "assistant",
        "content": "hola",
        "thinking_blocks": [
            {"thinking": "de otro", "signature": "s", "model_id": "gpt-4.1"}
        ],
    })

    assert [p.type for p in parts] == ["text"]


def test_history_written_before_this_lane_existed_is_not_thrown_away():
    """Un bloque sin `model_id` es historia previa, no un bloque ajeno: se conserva."""
    parts = _assistant_parts({
        "role": "assistant",
        "content": "hola",
        "thinking_blocks": [{"thinking": "sin etiqueta", "signature": "s"}],
    })

    assert [p.type for p in parts] == ["thinking", "text"]
    assert parts[0].thinking == "sin etiqueta"


# ---------------------------------------------------------------------------
# El razonamiento sale por el bus — en vivo y cerrado
# ---------------------------------------------------------------------------

class _Block:
    type = "thinking"

    def __init__(self, thinking: str, signature: str | None) -> None:
        self.thinking = thinking
        self.thinking_signature = signature


class _Usage:
    input = 1
    output = 2


class _Message:
    def __init__(self, content) -> None:
        self.content = content
        self.usage = _Usage()


async def test_the_bus_carries_live_deltas_and_the_closed_block_with_its_signature(monkeypatch):
    def fake_stream(model, context, opts):
        async def _gen():
            yield {"type": "thinking_delta", "delta": "pen"}
            yield {"type": "thinking_delta", "delta": "sando"}
            yield {
                "type": "done",
                "reason": "stop",
                "message": _Message([_Block("pensando", '{"id":"rs_1"}')]),
            }
        return _gen()

    monkeypatch.setattr(agentic_models, "stream", fake_stream)

    events = await _drain(await _caller().complete([{"role": "user", "content": "hi"}], []))
    thoughts = [e for e in events if isinstance(e, ThinkingEvent)]

    assert [(t.content, t.final) for t in thoughts] == [
        ("pen", False), ("sando", False), ("pensando", True),
    ]
    # Los deltas no llevan firma —el item sólo existe entero al cerrar— y el cierre sí.
    assert [t.signature for t in thoughts] == ["", "", '{"id":"rs_1"}']
    assert {t.model_id for t in thoughts} == {"gpt-5.4-mini"}
    # El cierre precede al `DoneEvent`: el loop corta al verlo, y esto tiene que
    # haber llegado antes para poder persistirse.
    assert isinstance(events[-2], ThinkingEvent) and events[-2].final


async def test_a_block_without_signature_is_still_shown_but_marked_final(monkeypatch):
    def fake_stream(model, context, opts):
        async def _gen():
            yield {"type": "done", "reason": "stop", "message": _Message([_Block("mudo", None)])}
        return _gen()

    monkeypatch.setattr(agentic_models, "stream", fake_stream)

    events = await _drain(await _caller().complete([{"role": "user", "content": "hi"}], []))
    thought = next(e for e in events if isinstance(e, ThinkingEvent))

    assert (thought.content, thought.final, thought.signature) == ("mudo", True, "")


# ---------------------------------------------------------------------------
# El loop lo persiste — y sólo colgado de un mensaje que ya existe
# ---------------------------------------------------------------------------

class _ReasoningCaller:
    """Caller que razona y responde, y que apunta lo que se le pasó."""

    def __init__(self, *, speak: bool = True) -> None:
        self.speak = speak
        self.kwargs: list[dict] = []
        self.messages: list[list[dict]] = []

    async def complete(self, messages, tools, **kwargs):
        self.kwargs.append(kwargs)
        self.messages.append([dict(m) for m in messages])
        speak = self.speak

        async def _gen():
            yield ThinkingEvent(content="en vivo", model_id="gpt-5.4-mini")
            yield ThinkingEvent(
                content="cerrado", signature='{"id":"rs_1"}', final=True, model_id="gpt-5.4-mini"
            )
            if speak:
                yield TokenEvent(content="respuesta")
            yield DoneEvent(stop_reason="stop")

        return _gen()


async def test_the_loop_persists_closed_blocks_and_ignores_the_live_deltas():
    caller = _ReasoningCaller()
    loop = AgentLoop(model_caller=caller, tool_registry=ToolRegistry(), tool_dispatcher=ToolDispatcher())
    ctx = ToolUseContext(session_id="s1")

    await loop.run("piensa", ctx)

    assistant = [m for m in ctx.messages if m.get("role") == "assistant"]
    assert len(assistant) == 1
    assert assistant[0]["content"] == "respuesta"
    # Un solo bloque: el delta es para mirar, no para persistir.
    assert assistant[0]["thinking_blocks"] == [
        {"thinking": "cerrado", "signature": '{"id":"rs_1"}', "model_id": "gpt-5.4-mini"}
    ]


async def test_a_turn_that_only_thinks_leaves_no_orphan_message():
    """`utils/messages.ts:2306-2310`: un assistant sólo-thinking es un 400 en el request siguiente.

    El razonamiento se CUELGA de un mensaje que ya existe; nunca crea uno.
    """
    caller = _ReasoningCaller(speak=False)
    loop = AgentLoop(model_caller=caller, tool_registry=ToolRegistry(), tool_dispatcher=ToolDispatcher())
    ctx = ToolUseContext(session_id="s1")

    await loop.run("piensa", ctx)

    assert [m for m in ctx.messages if m.get("role") == "assistant"] == []


async def test_the_options_of_the_seam_reach_the_caller():
    """`S1` deja de ser una tubería vacía: lo que se compone llega al puente."""
    caller = _ReasoningCaller()
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=ToolRegistry(),
        tool_dispatcher=ToolDispatcher(),
        model_options=ModelOptions(effort=Effort.XHIGH),
    )

    await loop.run("piensa", ToolUseContext(session_id="s1"))

    assert caller.kwargs[0]["effort"] is Effort.XHIGH
    # Sólo lo poblado: nadie inventa `thinking` porque nadie lo pidió.
    assert "thinking" not in caller.kwargs[0]
