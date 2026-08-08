"""Tests para runtime/models/caller.py — ModelCallerProtocol, ModelRequest."""
import inspect
from dataclasses import FrozenInstanceError

import pytest

from agentic_runtime.events import DoneEvent, TokenEvent
from agentic_runtime.models import ModelCallerProtocol, ModelRequest
from agentic_runtime.models.protocol import ModelOptions

# ---------------------------------------------------------------------------
# ModelRequest es frozen
# ---------------------------------------------------------------------------

def test_model_request_is_frozen():
    req = ModelRequest(messages=[{"role": "user", "content": "hi"}], tools=[], model_id="gpt-4.1")
    # `FrozenInstanceError`, no `Exception`: ver la nota en `test_events.py`.
    with pytest.raises(FrozenInstanceError):
        req.model_id = "other"  # type: ignore


def test_model_request_defaults():
    req = ModelRequest(messages=[], tools=[], model_id="gpt-4.1")
    assert req.stop is None
    # `C2`: `thinking_budget: int | None` suelto se sustituye por el paquete de
    # opciones de `S1`. Vacío por defecto = el motor decide, como hasta ahora.
    assert req.options == ModelOptions()
    assert req.options.as_kwargs() == {}


# ---------------------------------------------------------------------------
# Stub satisface ModelCallerProtocol
# ---------------------------------------------------------------------------

def test_stub_satisfies_model_caller_protocol():
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id="", **kw):
            async def _gen():
                yield TokenEvent(content="hello")
                yield DoneEvent(stop_reason="stop")
            return _gen()

        def supports_native_tool_search(self, model_id=""):
            return False

    assert isinstance(StubCaller(), ModelCallerProtocol)


def test_incomplete_stub_does_not_satisfy_protocol():
    class IncompleteCaller:
        pass  # sin método complete

    assert not isinstance(IncompleteCaller(), ModelCallerProtocol)


def test_enriched_signature_carries_everything_the_engine_can_do():
    """`C2`/`SEAMS §S1`: la firma pide al motor TODO lo que el motor sabe hacer.

    Se asevera por firma y no por comentario porque el defecto que esto corrige era
    justamente una firma corta: lo que no se pide, no se echa de menos."""
    params = inspect.signature(ModelCallerProtocol.complete).parameters
    for name in ("stop", "model_id", "system_sections", "system_override",
                 "thinking", "effort", "temperature", "max_tokens",
                 "output_format", "tool_choice", "metadata"):
        assert name in params, f"la costura S1 no pide `{name}`"


# ---------------------------------------------------------------------------
# ModelCallerProtocol no importa LLM concreto
# ---------------------------------------------------------------------------

def test_model_caller_protocol_does_not_import_concrete_llm():
    import agentic_runtime.models.protocol as caller_module
    source = inspect.getsource(caller_module)
    forbidden = ["openai", "anthropic", "agent_core.llm", "AsyncOpenAI", "LLMClient"]
    for token in forbidden:
        assert token not in source, f"caller.py importa '{token}' — no debe"
