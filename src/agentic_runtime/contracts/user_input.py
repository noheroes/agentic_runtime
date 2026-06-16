from __future__ import annotations

from typing import Any, Protocol


class UserInputProcessor(Protocol):
    """Provider hook for preprocessing user input before the LLM turn."""

    async def process_slash_command(
        self,
        message: str | list,
        registry: Any,
        session: Any,
        stop: Any,
        event_queue: Any,
    ) -> Any | None:
        ...

    def expand_inline_invocation(self, message: str | list) -> str | list:
        ...

    def get_inline_name(self, message: str | list) -> str | None:
        ...


class NoopUserInputProcessor:
    """Default processor for a runtime with no project-specific commands."""

    async def process_slash_command(
        self,
        message: str | list,
        registry: Any,
        session: Any,
        stop: Any,
        event_queue: Any,
    ) -> None:
        return None

    def expand_inline_invocation(self, message: str | list) -> str | list:
        return message

    def get_inline_name(self, message: str | list) -> str | None:
        return None


__all__ = ["NoopUserInputProcessor", "UserInputProcessor"]
