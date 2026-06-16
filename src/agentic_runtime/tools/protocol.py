from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext


class ToolCategory(str, Enum):
    UTILITY = "utility"
    SYSTEM = "system"
    FILE = "file"
    NETWORK = "network"
    BACKGROUND = "background"


class ToolResult:
    """Resultado de la ejecución de un tool."""

    def __init__(
        self,
        *,
        tool_name: str,
        output: str,
        is_error: bool = False,
        is_timeout: bool = False,
        is_aborted: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.output = output
        self.is_error = is_error
        self.is_timeout = is_timeout
        self.is_aborted = is_aborted
        self.metadata = metadata or {}

    @classmethod
    def error(cls, tool_name: str, message: str) -> "ToolResult":
        return cls(tool_name=tool_name, output=message, is_error=True)

    @classmethod
    def timeout(cls, tool_name: str) -> "ToolResult":
        return cls(tool_name=tool_name, output=f"timeout: {tool_name}", is_timeout=True)

    @classmethod
    def aborted(cls, tool_name: str) -> "ToolResult":
        return cls(tool_name=tool_name, output=f"aborted: {tool_name}", is_aborted=True)


@runtime_checkable
class ToolProtocol(Protocol):
    name: str
    description: str
    input_schema: dict
    category: ToolCategory
    requires_permission: bool
    safe_for_background: bool
    timeout_seconds: float

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult: ...
