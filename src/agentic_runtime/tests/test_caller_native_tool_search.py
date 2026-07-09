"""Sub-contrato runtime↔models: capability native_tool_search + propagación de defer_loading."""
from __future__ import annotations

from agentic_models import get_registry, register_builtins

from agentic_runtime.models.caller import AgenticModelsCaller, _dict_messages_to_context

register_builtins()


def _azure(model_id: str):
    return get_registry().get_by_provider("azure-openai-responses", model_id)


def test_capability_true_for_gpt5_responses_false_for_gpt4():
    caller = AgenticModelsCaller(model=_azure("gpt-4.1"))
    # default (gpt-4.1) no soporta; gpt-5.4-mini sí (capability del wheel 0.2.0)
    assert caller.supports_native_tool_search() is False
    assert caller.supports_native_tool_search("gpt-5.4-mini") is True


def test_capability_unknown_model_falls_back_to_default():
    caller = AgenticModelsCaller(model=_azure("gpt-4.1"))
    # id inexistente en el provider → cae al default (gpt-4.1 → False), sin romper
    assert caller.supports_native_tool_search("no-such-model") is False


def test_defer_loading_flag_propagates_dict_to_typed_tool():
    tools = [
        {"name": "plain", "description": "d", "parameters": {}},
        {"name": "mcp_x", "description": "d", "parameters": {}, "defer_loading": True},
    ]
    ctx = _dict_messages_to_context([], tools, None)
    by_name = {t.name: t for t in ctx.tools}
    assert by_name["plain"].defer_loading is False
    assert by_name["mcp_x"].defer_loading is True
