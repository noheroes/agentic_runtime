"""El caller honra `system_override`: el system prompt del subagente REEMPLAZA el base
del constructor (homologación getAgentSystemPrompt → [agentPrompt]). Sin override, base intacto.

Se espía `agentic_models.stream` para capturar el Context sin depender de red.
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
        yield  # pragma: no cover

    return _gen()


async def test_system_override_replaces_base(monkeypatch):
    model = get_registry().get_by_provider("azure-openai-responses", "gpt-4.1")
    caller = AgenticModelsCaller(model=model, system_prompt="BASE")

    captured = []

    def fake_stream(model, context, opts):
        captured.append(context)
        return _empty_stream()

    monkeypatch.setattr(agentic_models, "stream", fake_stream)
    msgs = [{"role": "user", "content": "hi"}]

    await _drain(await caller.complete(msgs, [], system_override=None))
    await _drain(await caller.complete(msgs, [], system_override="AGENTE"))

    assert captured[0].system_prompt == "BASE"          # sin override → base del constructor
    assert captured[1].system_prompt == "AGENTE"        # override → reemplaza el base


async def test_system_override_still_appends_sections(monkeypatch):
    model = get_registry().get_by_provider("azure-openai-responses", "gpt-4.1")
    caller = AgenticModelsCaller(model=model, system_prompt="BASE")

    captured = []

    def fake_stream(model, context, opts):
        captured.append(context)
        return _empty_stream()

    monkeypatch.setattr(agentic_models, "stream", fake_stream)

    await _drain(await caller.complete(
        [{"role": "user", "content": "hi"}], [],
        system_override="AGENTE", system_sections=["SECCION"],
    ))
    # El override reemplaza el base; las secciones del runtime se concatenan igual.
    assert captured[0].system_prompt == "AGENTE\n\nSECCION"
