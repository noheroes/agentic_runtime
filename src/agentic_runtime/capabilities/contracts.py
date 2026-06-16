from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext
    from ..tools.protocol import ToolProtocol


class CapabilitySummary(BaseModel):
    """Una capability visible al modelo (entrada de catálogo).

    Salida tipada: el catálogo que ve el modelo nunca es un dict suelto.
    """

    name: str
    kind: str  # "skill", "mcp_tool", "mcp_resource", ...
    description: str = ""
    when_to_use: str = ""
    provider: str = ""
    deferred: bool = False


class CapabilityActivation(BaseModel):
    """Resultado estructurado de activar una capability.

    No genera `agent_id` ni copia mensajes — el runtime decide herencia/fork.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    tools_to_enable: list[str] = Field(default_factory=list)
    messages_to_append: list[dict] = Field(default_factory=list)
    permission_rules: list[str] = Field(default_factory=list)
    active_state: dict[str, Any] = Field(default_factory=dict)
    refresh_tool_pool: bool = False


@runtime_checkable
class CapabilityProvider(Protocol):
    """Un proveedor de capacidades (Skills, MCP, ...) conectado por contrato.

    El runtime no sabe si una tool viene de un skill, MCP o plugin: habla con
    el `CapabilityManager`, que habla con providers que cumplen este protocolo.
    Las respuestas se scopean por `context.agent_id` (None = agente principal).
    """

    name: str

    async def startup(self) -> None: ...
    async def shutdown(self) -> None: ...

    def catalog(self, context: "ToolUseContext") -> list[CapabilitySummary]: ...
    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]: ...
    def active_context(self, context: "ToolUseContext") -> list[dict]: ...
    def compact_context(self, context: "ToolUseContext") -> list[dict]: ...


__all__ = [
    "CapabilityActivation",
    "CapabilityProvider",
    "CapabilitySummary",
]
