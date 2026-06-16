from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .protocol import CapabilitySource, ResolvedCapabilities, SkillCatalogProtocol
from ..context.tool_use import ToolUseContext
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class CapabilitiesResolver:
    """
    Combina ToolRegistry y SkillCatalog (inyectado) para responder qué puede hacer un agente.

    El loop no sabe si algo es un tool nativo, MCP o skill.

    Extension primitive: register_source(source) agrega fuentes adicionales (MCP dinámico,
    skills remotos, herramientas propietarias) sin modificar este resolver.
    """

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        skill_catalog: Optional[SkillCatalogProtocol] = None,
        resolve_timeout_seconds: float = 5.0,
    ) -> None:
        self._tool_registry = tool_registry
        self._skill_catalog = skill_catalog
        self._extra_sources: list[CapabilitySource] = []
        self.resolve_timeout_seconds = resolve_timeout_seconds

    def register_source(self, source: CapabilitySource) -> None:
        self._extra_sources.append(source)

    async def resolve(self, ctx: ToolUseContext) -> ResolvedCapabilities:
        allowed = ctx.permission_context.allowed_names()
        denied = ctx.permission_context.denied_names()

        # Filtro por KIND (no por el flag mutable is_backgrounded): un subagente es
        # unattended, así que solo recibe tools safe_for_background (sin ask_user/
        # plan_mode/worktree). El main recibe todas. Promover a background no re-filtra.
        candidate_tools = (
            self._tool_registry.list_available(mode="background")
            if ctx.is_subagent
            else self._tool_registry.all_tools()
        )

        # Tools nativas — sin timeout externo
        native_schemas = [
            {"name": t.name, "description": t.description, "parameters": t.input_schema}
            for t in candidate_tools
            if not t.requires_permission or (t.name in allowed and t.name not in denied)
        ]

        # Fuentes externas con timeout parcial — si tardan, se devuelve lo disponible
        external_schemas: list[dict] = []

        sources: list[SkillCatalogProtocol | CapabilitySource] = []
        if self._skill_catalog is not None:
            sources.append(self._skill_catalog)
        sources.extend(self._extra_sources)

        for source in sources:
            try:
                schemas = await asyncio.wait_for(
                    source.list_schemas(ctx),
                    timeout=self.resolve_timeout_seconds,
                )
                external_schemas.extend(schemas)
            except asyncio.TimeoutError:
                logger.warning("capabilities: timeout resolving source %r — returning partial", source)
            except Exception:
                logger.exception("capabilities: error resolving source %r — skipped", source)

        return ResolvedCapabilities(tool_schemas=native_schemas + external_schemas)
