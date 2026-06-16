from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.permissions import PermissionContext
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


def assemble_tool_pool(
    native_tools: list[ToolProtocol],
    capability_tools: list[ToolProtocol],
    permission_context: PermissionContext,
) -> list[ToolProtocol]:
    """Combine native and capability tools deterministically.

    Native tools take precedence on name collisions. Each partition is sorted
    by name for prompt-cache stability before deduplication — matching the
    canonical's mergeAndFilterTools behavior.
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

    return result


__all__ = ["ToolPool", "assemble_tool_pool"]
