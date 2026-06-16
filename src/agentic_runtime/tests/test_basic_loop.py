"""Tests para runtime/loop/ — LoopProtocol, DrainableLoopProtocol, BasicLoop."""
import pytest

from agentic_runtime.loop import BasicLoop, DrainableLoopProtocol, LoopProtocol


# ---------------------------------------------------------------------------
# Protocol checks
# ---------------------------------------------------------------------------

def test_basic_loop_satisfies_loop_protocol():
    loop = BasicLoop(model_caller=None)
    assert isinstance(loop, LoopProtocol)


def test_basic_loop_satisfies_drainable_protocol():
    loop = BasicLoop(model_caller=None)
    assert isinstance(loop, DrainableLoopProtocol)


# ---------------------------------------------------------------------------
# register_turn_start_hook
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_turn_start_hook_called_before_turn():
    calls: list[str] = []

    async def hook():
        calls.append("hook")

    loop = BasicLoop(model_caller=None)
    loop.register_turn_start_hook(hook)
    await loop._run_turn_start_hooks()

    assert calls == ["hook"]


@pytest.mark.asyncio
async def test_multiple_hooks_called_in_order():
    order: list[int] = []

    async def h1():
        order.append(1)

    async def h2():
        order.append(2)

    loop = BasicLoop(model_caller=None)
    loop.register_turn_start_hook(h1)
    loop.register_turn_start_hook(h2)
    await loop._run_turn_start_hooks()

    assert order == [1, 2]


# ---------------------------------------------------------------------------
# non-drainable loop does not crash
# ---------------------------------------------------------------------------

def test_non_drainable_loop_is_still_valid_loop_protocol():
    class MinimalLoop:
        async def run(self, prompt, session, ctx):
            pass

    # No implementa DrainableLoopProtocol — está OK
    loop = MinimalLoop()
    assert isinstance(loop, LoopProtocol)
    assert not isinstance(loop, DrainableLoopProtocol)
