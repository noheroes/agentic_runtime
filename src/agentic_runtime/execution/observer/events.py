from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SubagentStarted:
    task_id: str
    description: str
    foreground: bool
    model_override: str | None


@dataclass(frozen=True)
class SubagentStopped:
    task_id: str
    description: str
    status: str
    result: str | None
    duration_ms: int
    turn_count: int
    input_tokens: int
    output_tokens: int
