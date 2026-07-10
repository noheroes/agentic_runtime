from __future__ import annotations

from .protocol import ToolProtocol
from .registry import ToolRegistry


def create_tools(extras: list[ToolProtocol] | None = None) -> ToolRegistry:
    """
    Crea un ToolRegistry con todas las tools nativas del runtime.

    Proyectos pasan `extras` para agregar tools propias sin modificar el runtime.
    """
    from .native import (
        AgentTool,
        AskUserQuestionTool,
        BashTool,
        CloneRepositoryTool,
        ConfigTool,
        EnterPlanModeTool,
        EnterWorktreeTool,
        ExitPlanModeTool,
        ExitWorktreeTool,
        FileEditTool,
        GlobTool,
        GrepTool,
        ReadFileTool,
        SleepTool,
        TaskCreateTool,
        TaskGetTool,
        TaskListTool,
        TaskOutputTool,
        TaskStopTool,
        TaskUpdateTool,
        TodoWriteTool,
        ToolSearchTool,
        WebFetchTool,
        WebSearchTool,
        WriteFileTool,
    )

    native: list[ToolProtocol] = [
        AgentTool(),
        AskUserQuestionTool(),
        BashTool(),
        CloneRepositoryTool(),
        ConfigTool(),
        EnterPlanModeTool(),
        EnterWorktreeTool(),
        ExitPlanModeTool(),
        ExitWorktreeTool(),
        FileEditTool(),
        GlobTool(),
        GrepTool(),
        ReadFileTool(),
        SleepTool(),
        TaskCreateTool(),
        TaskGetTool(),
        TaskListTool(),
        TaskOutputTool(),
        TaskStopTool(),
        TaskUpdateTool(),
        TodoWriteTool(),
        ToolSearchTool(),
        WebFetchTool(),
        WebSearchTool(),
        WriteFileTool(),
    ]

    reg = ToolRegistry()
    for tool in native:
        reg.register(tool)
    for extra in (extras or []):
        reg.register(extra)

    return reg
