from __future__ import annotations

from .protocol import ToolProtocol
from .registry import ToolRegistry


def create_tools(
    extras: list[ToolProtocol] | None = None,
    *,
    interactive: bool = False,
) -> ToolRegistry:
    """
    Crea un ToolRegistry con todas las tools nativas del runtime.

    Proyectos pasan `extras` para agregar tools propias sin modificar el runtime.

    `interactive` declara si el host tiene un humano capaz de responder en mitad
    del turno. Sólo lo consumen las tools de PUERTA ÚNICA —las que ceden el turno
    esperando a una persona—, que en un host headless son un turno perdido:
    `FIND-TOOL-ENABLED-1`. Default `False`: el runtime es headless salvo que el
    integrador diga lo contrario.
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
        AskUserQuestionTool(interactive=interactive),
        BashTool(),
        CloneRepositoryTool(),
        ConfigTool(),
        EnterPlanModeTool(interactive=interactive),
        EnterWorktreeTool(),
        ExitPlanModeTool(interactive=interactive),
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
