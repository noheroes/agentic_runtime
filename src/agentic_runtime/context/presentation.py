"""
Default `PathPresentation` implementation.

Identity presentation = canonical CLI/IDE behaviour: the user's filesystem IS
the agent's filesystem, so real paths are shown verbatim and tool output passes
through untouched. Consumers that run on infra filesystems (container/cloud)
inject their own implementation that maps host paths to fake tokens; see
``contracts/storage.py::PathPresentation``.
"""
from __future__ import annotations

from pathlib import Path


class IdentityPresentation:
    """No-op presentation — real paths shown as-is, output unchanged."""

    def to_llm(self, host_path: Path) -> str:
        return str(host_path)

    def sanitize_output(self, text: str) -> str:
        return text


__all__ = ["IdentityPresentation"]
