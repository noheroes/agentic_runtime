"""Definiciones de subagente — homologación de `loadAgentsDir.AgentDefinition` +
`utils/model/agent.getAgentModel` del canónico.

El runtime es genérico: NO posee el catálogo de agentes. El host (integrador) provee las
definiciones implementando `AgentDefinitionResolver`, inyectado por `RuntimeConfig` (espejo de
`toolUseContext.options.agentDefinitions` del canónico). Una `AgentDefinition` identifica por
`subagent_type` el modelo, el system prompt y el subconjunto de tools del subagente especializado.

Punto crítico de homologación: el NOMBRE del agente (`subagent_type`) es la LLAVE de la
definición, nunca el `model_id`. El modelo se deriva de `AgentDefinition.model` con herencia del
padre por defecto, como `getAgentModel` (cuyo default `getDefaultSubagentModel()` es `'inherit'`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

#: Sentinela de herencia de modelo (espejo de getDefaultSubagentModel() == 'inherit').
INHERIT = "inherit"


@dataclass(frozen=True)
class AgentDefinition:
    """Definición de un tipo de subagente (espejo de la `AgentDefinition` canónica)."""

    subagent_type: str
    description: str = ""
    #: `None` o `"inherit"` → hereda el modelo del padre (espejo getAgentModel).
    model: str | None = None
    #: Cuerpo del `.md`: system prompt del subagente. `""` → hereda el base del padre.
    system_prompt: str = ""
    #: Subconjunto de tools por nombre. Vacío o `("*",)` → todas (espejo resolveAgentTools).
    allowed_tools: tuple[str, ...] = ()


@runtime_checkable
class AgentDefinitionResolver(Protocol):
    """Resuelve un `subagent_type` a su `AgentDefinition`, o `None` si no existe.

    Lo implementa el host (espejo de `options.agentDefinitions.activeAgents.find(
    a => a.agentType === subagent_type)`)."""

    def resolve(self, subagent_type: str) -> "AgentDefinition | None": ...


def resolve_subagent_model(
    agent_model: str | None, parent_model: str, model_override: str | None = None
) -> str:
    """Modelo efectivo de un subagente — espejo de `getAgentModel` (sin specifics de Bedrock).

    Precedencia: `model_override` explícito de la tool > `agent_model` de la definición >
    herencia del padre. `None`/`"inherit"` significan heredar. El nombre del agente NO
    participa: si nadie declara modelo, se usa el del padre."""
    if model_override:
        return model_override
    if not agent_model or agent_model == INHERIT:
        return parent_model
    return agent_model


__all__ = [
    "INHERIT",
    "AgentDefinition",
    "AgentDefinitionResolver",
    "resolve_subagent_model",
]
