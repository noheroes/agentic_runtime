"""
Path-related runtime contracts — protocols that consumers implement.

These are intentionally minimal Protocols, not abstract classes. Implementations
live with the consumer (new_core, agent-code, future deployments) because the
path / storage opinion depends on the deployment model:

- new_core: containerised + blob (MinIO/S3) — implements with caching + mirroring.
- agent-code: local CLI on user filesystem — implements as identity.

The runtime itself stays agnostic. Tools call into these via the
``ToolExecutionContext`` rather than touching path resolution or storage backends
directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageContract(Protocol):
    """Path resolution + durable persistence for tool I/O."""

    def real_path(self, token: str) -> Path: ...

    async def ensure_local(self, token: str) -> Path: ...

    async def commit(self, token: str, content: bytes, mime: str | None = None) -> str: ...

    async def teardown(self) -> None: ...


@runtime_checkable
class PathPresentation(Protocol):
    """LLM/UI-facing path translation."""

    def to_llm(self, host_path: Path) -> str: ...

    def sanitize_output(self, text: str) -> str: ...
