from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.permissions import PermissionContext
from ..contracts.tools import tool_is_enabled
from .protocol import ToolProtocol


class ToolPool(BaseModel):
    """Partitioned tool pool used by the agentic runtime.

    Native tools remain separated from capability-provided tools until the
    final assembly point — mirroring the canonical's built-in + MCP pool
    boundary while keeping the runtime provider-agnostic.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    native_tools: list[ToolProtocol] = Field(default_factory=list)
    capability_tools: list[ToolProtocol] = Field(default_factory=list)

    def assemble(self, permission_context: PermissionContext | None = None) -> list[ToolProtocol]:
        return assemble_tool_pool(
            self.native_tools,
            self.capability_tools,
            permission_context or PermissionContext(),
        )

    def find(
        self,
        name: str,
        permission_context: PermissionContext | None = None,
    ) -> ToolProtocol | None:
        """Resuelve una tool por nombre desde el pool ensamblado.

        Análogo de `findToolByName(toolUseContext.options.tools, name)` del canónico:
        la ejecución resuelve desde el MISMO pool que se anuncia (native + capability,
        dedup native-gana, deny aplicado). No hay un registry aparte para ejecutar.
        Las tools diferidas (no anunciadas hasta activarse) siguen siendo ejecutables
        porque viven en el pool — deferred es visibilidad, no disponibilidad.
        """
        for tool in self.assemble(permission_context):
            if tool.name == name:
                return tool
        return None


def assemble_tool_pool(
    native_tools: list[ToolProtocol],
    capability_tools: list[ToolProtocol],
    permission_context: PermissionContext,
) -> list[ToolProtocol]:
    """Combine native and capability tools deterministically.

    Native tools take precedence on name collisions. Each partition is sorted
    by name for prompt-cache stability before deduplication — matching the
    canonical's mergeAndFilterTools behavior.

    Se aplican DOS filtros, y el ORDEN entre ellos es parte de la costura
    (`tools.ts:311-326`): primero deny + dedup, y `is_enabled` **al final**,
    sobre la lista ya deduplicada. No es cosmético — decide qué pasa cuando
    una capability trae el nombre de una nativa deshabilitada: como la nativa
    ya consumió el nombre en la deduplicación, el hueco NO lo rellena la
    capability. Aplicar el enabled antes invertiría eso y dejaría que una tool
    de terceros suplantara a una nativa apagada.

    El segundo filtro faltaba entero — `FIND-TOOL-ENABLED-1`: sin él, una tool
    que exige un humano se publica igual en un host sin humano, y el modelo la
    llama y pierde el turno. A lo dice en un comentario, sobre plan mode:
    *«Disable entry too so plan mode isn't a trap the model can enter but
    never leave»* (`EnterPlanModeTool.ts:56-67`).
    """
    denied = permission_context.denied_names()
    result: list[ToolProtocol] = []
    seen: set[str] = set()

    for tool in sorted(native_tools, key=lambda t: t.name):
        if tool.name in denied or tool.name in seen:
            continue
        result.append(tool)
        seen.add(tool.name)

    for tool in sorted(capability_tools, key=lambda t: t.name):
        if tool.name in denied or tool.name in seen:
            continue
        result.append(tool)
        seen.add(tool.name)

    return [tool for tool in result if tool_is_enabled(tool)]


__all__ = ["ToolPool", "assemble_tool_pool"]
