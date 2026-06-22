"""M2 — AgenticModelsCaller resuelve el modelo por request (model_id).

El modelo del constructor es el default; cada complete(..., model_id=...) puede
sobreescribirlo. La resolución per-request se hace DENTRO del provider del modelo
del constructor: el puente es mono-provider por construcción (un solo api_key, un
solo provider), así que la identidad canónica de agentic_models es (provider, id).
Resolver solo por id es ambiguo —el mismo id existe en varios providers— y podría
devolver un Model de otro provider cuyo api_key no corresponde.

Se espía el modelo que llega a agentic_models.stream para no depender de red.
"""
from __future__ import annotations

import agentic_models
from agentic_models import get_registry, register_builtins

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


async def test_caller_resolves_model_within_constructor_provider(monkeypatch):
    # Provider del constructor = azure-openai-responses (el de prod). El mismo id
    # gpt-5.4-mini existe también en openai/opencode/github-copilot; con resolución
    # id-only "last-registered wins" caería en otro provider.
    default_model = get_registry().get_by_provider("azure-openai-responses", "gpt-4.1")
    caller = AgenticModelsCaller(model=default_model)

    captured = []

    def fake_stream(model, context, opts):
        captured.append(model)
        return _empty_stream()

    monkeypatch.setattr(agentic_models, "stream", fake_stream)

    msgs = [{"role": "user", "content": "hi"}]

    # sin model_id → default del constructor
    await _drain(await caller.complete(msgs, [], model_id=""))
    # con model_id distinto → resuelve ese id DENTRO del provider del constructor
    await _drain(await caller.complete(msgs, [], model_id="gpt-5.4-mini"))

    assert len(captured) == 2
    assert captured[0].id == "gpt-4.1"
    assert captured[0].provider == "azure-openai-responses"
    assert captured[1].id == "gpt-5.4-mini"
    # No cae en openai/opencode/github-copilot pese a que el id existe en ellos.
    assert captured[1].provider == "azure-openai-responses"


async def test_caller_unknown_model_in_provider_raises(monkeypatch):
    import pytest
    from agentic_models.models.registry import ModelNotFoundError

    # Caller mono-provider azure; gemini-2.5-pro existe en el catálogo (google) pero
    # NO en azure-openai-responses → error explícito, no fallback al otro provider.
    caller = AgenticModelsCaller(
        model=get_registry().get_by_provider("azure-openai-responses", "gpt-4.1")
    )
    monkeypatch.setattr(agentic_models, "stream", lambda m, c, o: _empty_stream())

    with pytest.raises(ModelNotFoundError):
        await _drain(
            await caller.complete(
                [{"role": "user", "content": "hi"}], [], model_id="gemini-2.5-pro"
            )
        )
