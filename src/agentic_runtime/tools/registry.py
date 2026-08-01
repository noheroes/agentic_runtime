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

    def list_available(self, *, mode: str = "foreground") -> list[ToolProtocol]:
        """Filtra SOLO por kind (`background` ⇒ `safe_for_background`).

        No lleva `permission_ctx`: el registry es "solo input" del turno
        (`agent_loop.py:121-133`) y el gate de permisos vive aguas abajo, en el
        ensamblador del pool (`assemble_tool_pool` + `resolver.py:40`
        `denied_names()`). El parámetro existía sin que ningún call-site lo pasara —
        un slot muerto que sugería un segundo lugar donde se filtra por permisos.
        """
        tools = list(self._tools.values())
        if mode == "background":
            tools = [t for t in tools if t.safe_for_background]
        return tools

    def all_tools(self) -> list[ToolProtocol]:
        return list(self._tools.values())
