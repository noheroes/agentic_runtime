from __future__ import annotations

from typing import Any

from .agent_loop import AgentLoop
from .protocol import LoopProtocol


def create_loop(
    *,
    model_caller: Any = None,
    capabilities_resolver: Any = None,
    tool_dispatcher: Any = None,
    model_id: str = "",
) -> LoopProtocol:
    """
    Factory de loops.

    Helper opcional para componer un AgentLoop a partir de las primitivas; el runtime
    construye su loop directamente, así que esta factory es para uso del consumidor (D5c).
    """
    return AgentLoop(
        model_caller=model_caller,
        capabilities_resolver=capabilities_resolver,
        tool_dispatcher=tool_dispatcher,
        model_id=model_id,
    )
