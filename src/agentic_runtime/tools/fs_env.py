from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..contracts.storage import StorageContract


class PathOutsideWorkspace(Exception):
    pass


_TRAVERSAL_RE = re.compile(r"(?:^|[\\/])\.\.(?:[\\/]|$)")


def contains_path_traversal(path: str) -> bool:
    return bool(_TRAVERSAL_RE.search(path))


def expand_path(path: str, base_dir: str) -> str:
    if "\0" in path or "\0" in base_dir:
        raise ValueError("Path contains null bytes")
    trimmed = path.strip()
    if not trimmed:
        return os.path.normpath(base_dir)
    expanded = os.path.expanduser(trimmed)
    if not os.path.isabs(expanded):
        expanded = os.path.join(base_dir, expanded)
    return os.path.normpath(expanded)


def paths_for_permission_check(path: str, base_dir: str) -> list[str]:
    expanded = expand_path(path, base_dir)
    resolved = os.path.realpath(expanded)
    if resolved == expanded:
        return [expanded]
    return [expanded, resolved]


def path_in_working_path(path: str, working_path: str, base_dir: str) -> bool:
    abs_path = expand_path(path, base_dir)
    abs_working = expand_path(working_path, base_dir)
    relative = os.path.relpath(abs_path, abs_working)
    if relative == ".":
        return True
    if contains_path_traversal(relative):
        return False
    return not os.path.isabs(relative)


def path_in_allowed_working_path(path: str, roots: list[str], base_dir: str) -> bool:
    checks = paths_for_permission_check(path, base_dir)
    working_paths: list[str] = []
    for root in roots:
        expanded = expand_path(root, base_dir)
        working_paths.append(expanded)
        resolved = os.path.realpath(expanded)
        if resolved != expanded:
            working_paths.append(resolved)
    return all(
        any(path_in_working_path(check, wp, base_dir) for wp in working_paths)
        for check in checks
    )


class ConfinedFilesystem:
    def __init__(
        self,
        roots: list[Path] | None = None,
        storage: StorageContract | None = None,
        *,
        write_roots: list[Path] | None = None,
    ) -> None:
        self._roots = [Path(r) for r in roots] if roots else [Path.cwd()]
        self._write_roots = (
            [Path(r) for r in write_roots] if write_roots is not None else self._roots
        )
        self._storage = storage

    @property
    def _base_dir(self) -> str:
        return str(self._roots[0])

    @property
    def write_root(self) -> Path:
        return self._write_roots[0]

    def resolve(self, token: str, *, for_write: bool, cwd: str | None) -> Path:
        host = self._storage.real_path(token) if self._storage is not None else Path(token)
        allow = self._write_roots if for_write else self._roots
        base = cwd or self._base_dir

        from ..capabilities.plan.plan_file import is_session_plan_file

        if is_session_plan_file(token) and not contains_path_traversal(token):
            return Path(expand_path(str(host), base))
        if not path_in_allowed_working_path(str(host), [str(r) for r in allow], base):
            raise PathOutsideWorkspace(
                f"path {token!r} resolves outside the allowed "
                f"{'write ' if for_write else ''}workspace"
            )
        return Path(expand_path(str(host), base))


__all__ = [
    "ConfinedFilesystem",
    "PathOutsideWorkspace",
    "contains_path_traversal",
    "expand_path",
    "path_in_allowed_working_path",
    "path_in_working_path",
    "paths_for_permission_check",
]
