"""Tests para runtime/context/execution.py — ExecutionContext con ContextVar."""
import asyncio
import pytest

from agentic_runtime.context.execution import (
    ExecutionContext,
    RuntimeState,
    get_execution_context,
    run_with_context,
    set_execution_context,
)


# ---------------------------------------------------------------------------
# ExecutionContext aislamiento
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_context_not_set_outside_run_with_context():
    assert get_execution_context() is None


@pytest.mark.asyncio
async def test_run_with_context_sets_context():
    ctx = ExecutionContext(execution_id="e1", session_id="s1")

    async def check():
        return get_execution_context()

    result = await run_with_context(ctx, check())
    assert result is ctx


@pytest.mark.asyncio
async def test_contexts_isolated_across_concurrent_tasks():
    ctx_a = ExecutionContext(execution_id="a", session_id="s1")
    ctx_b = ExecutionContext(execution_id="b", session_id="s1")

    seen: list[str | None] = []

    async def record(ctx: ExecutionContext, delay: float):
        await asyncio.sleep(delay)
        seen.append(get_execution_context().execution_id if get_execution_context() else None)

    await asyncio.gather(
        run_with_context(ctx_a, record(ctx_a, 0.01)),
        run_with_context(ctx_b, record(ctx_b, 0.0)),
    )

    assert set(seen) == {"a", "b"}


@pytest.mark.asyncio
async def test_child_context_does_not_leak_to_parent():
    parent_ctx = ExecutionContext(execution_id="parent", session_id="s1")

    async def child_task():
        child_ctx = ExecutionContext(execution_id="child", session_id="s1")
        await run_with_context(child_ctx, asyncio.sleep(0))
        # Después del run_with_context del hijo, el padre no debe ver el hijo
        return get_execution_context()

    result = await run_with_context(parent_ctx, child_task())
    assert result.execution_id == "parent"


@pytest.mark.asyncio
async def test_set_execution_context_persists_in_same_task():
    ctx = ExecutionContext(execution_id="manual", session_id="s1")
    token = set_execution_context(ctx)
    assert get_execution_context() is ctx
    # Restaurar
    token.var.reset(token)


# ---------------------------------------------------------------------------
# RuntimeState
# ---------------------------------------------------------------------------

def test_runtime_state_initial_no_foreground():
    state = RuntimeState()
    assert state.foreground_task_id is None


def test_runtime_state_set_foreground():
    state = RuntimeState()
    state.set_foreground("t1")
    assert state.foreground_task_id == "t1"


def test_runtime_state_clear_foreground():
    state = RuntimeState()
    state.set_foreground("t1")
    state.clear_foreground()
    assert state.foreground_task_id is None
