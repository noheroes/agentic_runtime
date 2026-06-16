"""Tests para runtime/events/ — Event, tipos concretos, EventBus."""
import pytest

from agentic_runtime.events import (
    DoneEvent,
    ErrorEvent,
    Event,
    EventBus,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from agentic_runtime.events.event_types import Usage


# ---------------------------------------------------------------------------
# Event es frozen
# ---------------------------------------------------------------------------

def test_event_is_frozen():
    ev = TokenEvent(content="hello")
    with pytest.raises(Exception):  # FrozenInstanceError o AttributeError
        ev.content = "world"  # type: ignore


def test_token_event_fields():
    ev = TokenEvent(content="hi")
    assert ev.content == "hi"


def test_tool_call_event_fields():
    ev = ToolCallEvent(tool_name="bash", tool_input={"command": "ls"}, call_id="c1")
    assert ev.tool_name == "bash"
    assert ev.call_id == "c1"


def test_tool_result_event_fields():
    ev = ToolResultEvent(call_id="c1", result="output", is_error=False)
    assert ev.call_id == "c1"
    assert not ev.is_error


def test_done_event_carries_usage():
    usage = Usage(input_tokens=10, output_tokens=5)
    ev = DoneEvent(stop_reason="stop", usage=usage)
    assert ev.usage.input_tokens == 10


def test_done_event_usage_optional():
    ev = DoneEvent(stop_reason="stop")
    assert ev.usage is None


def test_error_event_fields():
    ev = ErrorEvent(message="boom")
    assert ev.message == "boom"


# ---------------------------------------------------------------------------
# Todos son subtipos de Event
# ---------------------------------------------------------------------------

def test_all_events_are_event_subtype():
    events = [
        TokenEvent(content="x"),
        ToolCallEvent(tool_name="t", tool_input={}, call_id="c"),
        ToolResultEvent(call_id="c", result="r", is_error=False),
        DoneEvent(stop_reason="stop"),
        ErrorEvent(message="err"),
    ]
    for ev in events:
        assert isinstance(ev, Event)


# ---------------------------------------------------------------------------
# EventBus — dispatch por tipo
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_emit_dispatches_to_correct_handler():
    bus = EventBus()
    received: list[Event] = []

    async def on_token(ev: TokenEvent):
        received.append(ev)

    bus.subscribe(TokenEvent, on_token)
    await bus.emit(TokenEvent(content="hello"))
    await bus.emit(DoneEvent(stop_reason="stop"))

    assert len(received) == 1
    assert isinstance(received[0], TokenEvent)


@pytest.mark.asyncio
async def test_emit_no_subscribers_does_not_raise():
    bus = EventBus()
    await bus.emit(TokenEvent(content="x"))  # no debe lanzar


@pytest.mark.asyncio
async def test_subscribe_multiple_handlers_same_type():
    bus = EventBus()
    calls: list[int] = []

    async def h1(ev): calls.append(1)
    async def h2(ev): calls.append(2)

    bus.subscribe(TokenEvent, h1)
    bus.subscribe(TokenEvent, h2)
    await bus.emit(TokenEvent(content="x"))

    assert calls == [1, 2]


@pytest.mark.asyncio
async def test_custom_event_type_works():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class MyEvent(Event):
        value: int

    bus = EventBus()
    received: list[MyEvent] = []

    async def on_my(ev: MyEvent):
        received.append(ev)

    bus.subscribe(MyEvent, on_my)
    await bus.emit(MyEvent(value=42))

    assert len(received) == 1
    assert received[0].value == 42


@pytest.mark.asyncio
async def test_emit_does_not_dispatch_parent_to_child_handler():
    """Emitir Event base no dispara handler de TokenEvent."""
    bus = EventBus()
    calls: list[Event] = []

    async def on_token(ev): calls.append(ev)

    bus.subscribe(TokenEvent, on_token)
    await bus.emit(DoneEvent(stop_reason="stop"))

    assert calls == []
