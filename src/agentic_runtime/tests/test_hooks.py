"""Tests de R1: HookRunner + taxonomía canónica de hooks."""
from __future__ import annotations

import pytest

from agentic_runtime.hooks import (
    HookDecision,
    HookEvent,
    HookRunner,
    HookSinkProtocol,
)


def test_taxonomy_matches_canonical():
    """Los 11 eventos canónicos (coreSchemas.ts:355) están presentes."""
    values = {e.value for e in HookEvent}
    assert values == {
        "PreToolUse", "PostToolUse", "PostToolUseFailure", "Notification",
        "UserPromptSubmit", "SessionStart", "SessionEnd", "Stop",
        "StopFailure", "SubagentStop", "PreCompact",
    }


@pytest.mark.asyncio
async def test_run_with_no_handlers_returns_allow():
    runner = HookRunner()
    decision = await runner.run(HookEvent.PRE_TOOL_USE, {"tool": "bash"})
    assert decision.block is False and decision.stop is False


@pytest.mark.asyncio
async def test_handler_block_short_circuits():
    runner = HookRunner()
    calls: list[str] = []

    async def blocker(event, payload):
        calls.append("blocker")
        return HookDecision.blocked("no permitido")

    async def after(event, payload):
        calls.append("after")
        return None

    runner.register(HookEvent.PRE_TOOL_USE, blocker)
    runner.register(HookEvent.PRE_TOOL_USE, after)
    decision = await runner.run(HookEvent.PRE_TOOL_USE, {})
    assert decision.block is True
    assert decision.message == "no permitido"
    assert calls == ["blocker"]  # corta antes del segundo handler


@pytest.mark.asyncio
async def test_handler_stop_short_circuits():
    runner = HookRunner()

    async def stopper(event, payload):
        return HookDecision.stopped("alto")

    runner.register(HookEvent.STOP, stopper)
    decision = await runner.run(HookEvent.STOP, {})
    assert decision.stop is True and decision.message == "alto"


@pytest.mark.asyncio
async def test_additional_context_is_aggregated():
    runner = HookRunner()

    async def h1(event, payload):
        return HookDecision(additional_context="a")

    async def h2(event, payload):
        return HookDecision(additional_context="b")

    runner.register(HookEvent.USER_PROMPT_SUBMIT, h1)
    runner.register(HookEvent.USER_PROMPT_SUBMIT, h2)
    decision = await runner.run(HookEvent.USER_PROMPT_SUBMIT, {})
    assert decision.additional_context == "a\nb"
    assert decision.block is False


@pytest.mark.asyncio
async def test_raising_handler_does_not_break_run():
    runner = HookRunner()

    async def boom(event, payload):
        raise RuntimeError("handler roto")

    async def ok(event, payload):
        return HookDecision(additional_context="sobrevivio")

    runner.register(HookEvent.SUBAGENT_STOP, boom)
    runner.register(HookEvent.SUBAGENT_STOP, ok)
    decision = await runner.run(HookEvent.SUBAGENT_STOP, {})
    assert decision.additional_context == "sobrevivio"


@pytest.mark.asyncio
async def test_handlers_isolated_per_event():
    runner = HookRunner()
    seen: list[str] = []

    async def only_pre(event, payload):
        seen.append("pre")
        return None

    runner.register(HookEvent.PRE_TOOL_USE, only_pre)
    await runner.run(HookEvent.POST_TOOL_USE, {})
    assert seen == []  # no se dispara para otro evento


@pytest.mark.asyncio
async def test_register_sink_receives_events():
    runner = HookRunner()
    received: list[HookEvent] = []

    class _Sink:
        async def handle(self, event, payload):
            received.append(event)
            return None

    sink = _Sink()
    assert isinstance(sink, HookSinkProtocol)
    runner.register_sink(sink, HookEvent.PRE_COMPACT)
    await runner.run(HookEvent.PRE_COMPACT, {})
    await runner.run(HookEvent.SESSION_START, {})  # no suscrito
    assert received == [HookEvent.PRE_COMPACT]
