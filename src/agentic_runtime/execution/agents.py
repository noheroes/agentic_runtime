"""Reexport del contrato T1 de definiciones de subagente (`contracts.agents`)."""
from __future__ import annotations

from ..contracts.agents import (
    INHERIT,
    AgentDefinition,
    AgentDefinitionCatalog,
    AgentDefinitionResolver,
    enumerate_agent_definitions,
    resolve_subagent_model,
)

__all__ = [
    "INHERIT",
    "AgentDefinition",
    "AgentDefinitionCatalog",
    "AgentDefinitionResolver",
    "enumerate_agent_definitions",
    "resolve_subagent_model",
]
