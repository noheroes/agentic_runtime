"""Tests para runtime/models/caller.py — ModelCallerProtocol, ModelRequest."""
import inspect
import pytest

from agentic_runtime.models import ModelCallerProtocol, ModelRequest
from agentic_runtime.events import DoneEvent, TokenEvent


# ---------------------------------------------------------------------------
# ModelRequest es frozen
# ---------------------------------------------------------------------------

def test_model_request_is_frozen():
    req = ModelRequest(messages=[{"role": "user", "content": "hi"}], tools=[], model_id="gpt-4.1")
    with pytest.raises(Exception):
        req.model_id = "other"  # type: ignore


def test_model_request_defaults():
    req = ModelRequest(messages=[], tools=[], model_id="gpt-4.1")
    assert req.stop is None
    assert req.thinking_budget is None


# ---------------------------------------------------------------------------
# Stub satisface ModelCallerProtocol
# ---------------------------------------------------------------------------

def test_stub_satisfies_model_caller_protocol():
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                yield TokenEvent(content="hello")
                yield DoneEvent(stop_reason="stop")
            return _gen()

    assert isinstance(StubCaller(), ModelCallerProtocol)


def test_incomplete_stub_does_not_satisfy_protocol():
    class IncompleteCaller:
        pass  # sin método complete

    assert not isinstance(IncompleteCaller(), ModelCallerProtocol)


# ---------------------------------------------------------------------------
# ModelCallerProtocol no importa LLM concreto
# ---------------------------------------------------------------------------

def test_model_caller_protocol_does_not_import_concrete_llm():
    import agentic_runtime.models.protocol as caller_module
    source = inspect.getsource(caller_module)
    forbidden = ["openai", "anthropic", "agent_core.llm", "AsyncOpenAI", "LLMClient"]
    for token in forbidden:
        assert token not in source, f"caller.py importa '{token}' — no debe"
