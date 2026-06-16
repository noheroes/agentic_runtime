from __future__ import annotations

from pydantic import BaseModel, Field


class PermissionContext(BaseModel):
    """Runtime-level permission rules for assembling and executing tools.

    This is intentionally provider-agnostic. Skills, MCP, plugins, or project
    adapters may contribute rules, but the runtime only sees tool names.
    """

    always_allow_command: list[str] = Field(default_factory=list)
    always_allow_session: list[str] = Field(default_factory=list)
    always_deny: list[str] = Field(default_factory=list)

    def allowed_names(self) -> set[str]:
        return set(self.always_allow_command) | set(self.always_allow_session)

    def denied_names(self) -> set[str]:
        return set(self.always_deny)

    def with_command_allow(self, names: list[str]) -> "PermissionContext":
        merged = [*self.always_allow_command]
        seen = set(merged)
        for name in names:
            if name not in seen:
                merged.append(name)
                seen.add(name)
        return self.model_copy(update={"always_allow_command": merged})


__all__ = ["PermissionContext"]
