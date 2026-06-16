"""M2 — AgenticModelsCaller resuelve el modelo por request (model_id).

El modelo del constructor es el default; cada complete(..., model_id=...) puede
sobreescribirlo. Se espía el modelo que llega a agentic_models.stream para no
depender de red.
"""
from __future__ import annotations

import agentic_models
from agentic_models import get_model, register_builtins

from agentic_runtime.models.caller import AgenticModelsCaller

register_builtins()


async def _drain(agen):
    async for _ in agen:
        pass


def _empty_stream():
    async def _gen():
        return
        yield  # pragma: no cover — marca _gen como async generator
    return _gen()


async def test_caller_resolves_model_per_request(monkeypatch):
    default_model = get_model("claude-sonnet-4-6")
    caller = AgenticModelsCaller(model=default_model)

    captured = []

    def fake_stream(model, context, opts):
        captured.append(model)
        return _empty_stream()

    monkeypatch.setattr(agentic_models, "stream", fake_stream)

    msgs = [{"role": "user", "content": "hi"}]

    # sin model_id → default del constructor
    await _drain(await caller.complete(msgs, [], model_id=""))
    # con model_id distinto → resuelve ese modelo
    await _drain(await caller.complete(msgs, [], model_id="gpt-4.1"))

    assert len(captured) == 2
    assert captured[0].id == "claude-sonnet-4-6"
    assert captured[1].id == "gpt-4.1"


async def test_caller_unknown_model_id_raises(monkeypatch):
    import pytest
    from agentic_models.models.registry import ModelNotFoundError

    caller = AgenticModelsCaller(model=get_model("claude-sonnet-4-6"))
    monkeypatch.setattr(agentic_models, "stream", lambda m, c, o: _empty_stream())

    # model_id desconocido → error explícito, no fallback silencioso al default
    with pytest.raises(ModelNotFoundError):
        await _drain(await caller.complete([{"role": "user", "content": "hi"}], [], model_id="no-such-model"))
