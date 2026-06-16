from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext


@dataclass
class ResolvedCapabilities:
    """Resultado opaco de la resolución — el loop no accede a tools/skills directamente."""
    tool_schemas: list[dict[str, Any]] = field(default_factory=list)


class SkillCatalogProtocol(Protocol):
    """Contrato que el proyecto inyecta — el resolver no importa skills.*"""

    async def list_schemas(self, ctx: "ToolUseContext") -> list[dict[str, Any]]: ...


class CapabilitySource(Protocol):
    """Fuente adicional de capacidades — primitiva de extensión."""

    async def list_schemas(self, ctx: "ToolUseContext") -> list[dict[str, Any]]: ...
