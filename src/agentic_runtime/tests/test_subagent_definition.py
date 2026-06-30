"""Slice A — contrato de definición de subagente y resolución de modelo inherit-aware.

Homologación de `tools/AgentTool/loadAgentsDir.AgentDefinition` + `utils/model/agent.getAgentModel`
del canónico: el runtime es genérico y NO posee el catálogo; el host provee las definiciones por
`AgentDefinitionResolver`. El modelo del subagente se deriva de la definición, con herencia del
padre por defecto — el NOMBRE del agente nunca es el modelo.
"""
from __future__ import annotations

from agentic_runtime.execution.agents import (
    INHERIT,
    AgentDefinition,
    AgentDefinitionResolver,
    resolve_subagent_model,
)


def test_definition_defaults():
    d = AgentDefinition(subagent_type="researcher")
    assert d.model is None  # None = hereda
    assert d.system_prompt == ""  # "" = hereda el base del padre
    assert d.allowed_tools == ()  # () = todas


def test_model_override_wins():
    # Espejo: toolSpecifiedModel tiene prioridad sobre la def y sobre inherit.
    assert resolve_subagent_model("haiku", "gpt-5.4-mini", "gpt-4o-mini") == "gpt-4o-mini"


def test_none_model_inherits_parent():
    # Espejo getDefaultSubagentModel='inherit' → modelo del padre. NO el nombre del agente.
    assert resolve_subagent_model(None, "gpt-5.4-mini") == "gpt-5.4-mini"


def test_inherit_sentinel_inherits_parent():
    assert resolve_subagent_model(INHERIT, "gpt-5.4-mini") == "gpt-5.4-mini"


def test_explicit_definition_model():
    assert resolve_subagent_model("gpt-4o-mini", "gpt-5.4-mini") == "gpt-4o-mini"


def test_resolver_is_runtime_checkable():
    class _R:
        def resolve(self, subagent_type: str):
            return AgentDefinition(subagent_type=subagent_type) if subagent_type == "x" else None

    r = _R()
    assert isinstance(r, AgentDefinitionResolver)
    assert r.resolve("x").subagent_type == "x"
    assert r.resolve("nope") is None
