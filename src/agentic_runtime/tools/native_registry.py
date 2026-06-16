from __future__ import annotations

from .protocol import ToolProtocol


class NativeToolRegistry:
    """Provider-agnostic registry for runtime-native tools.

    Intentionally excludes capability-specific filtering. Skills, MCP, and
    other providers contribute tools through the tool pool assembler, not here.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolProtocol] = {}

    def register(self, tool: ToolProtocol) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolProtocol:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found in registry")
        return tool

    def list_tools(self) -> list[ToolProtocol]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def unregister_by_prefix(self, prefix: str) -> int:
        names = [name for name in self._tools if name.startswith(prefix)]
        for name in names:
            del self._tools[name]
        return len(names)


__all__ = ["NativeToolRegistry"]
