from __future__ import annotations

from typing import Optional

from .protocol import ToolProtocol


class ToolRegistry:
    """
    Registro de tools del runtime.

    Extension primitive: proyectos llaman `registry.register(custom_tool)` para
    agregar tools propias sin modificar el runtime.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolProtocol] = {}

    def register(self, tool: ToolProtocol) -> None:
        self._tools[tool.name] = tool

    def resolve(self, name: str) -> Optional[ToolProtocol]:
        return self._tools.get(name)

    def list_available(
        self,
        *,
        mode: str = "foreground",
        permission_ctx=None,
    ) -> list[ToolProtocol]:
        tools = list(self._tools.values())
        if mode == "background":
            tools = [t for t in tools if t.safe_for_background]
        return tools

    def all_tools(self) -> list[ToolProtocol]:
        return list(self._tools.values())
