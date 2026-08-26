from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .tool_use import AppState

READ_FILE_STATE_KEY = "read_file_state"


@dataclass(frozen=True)
class ReadFileEntry:
    path: str
    timestamp: float


def _deposit(app_state: AppState | Any) -> dict[str, Any] | None:
    native = getattr(app_state, "native", None)
    if not isinstance(native, dict):
        return None
    deposit = native.get(READ_FILE_STATE_KEY)
    if deposit is None:
        deposit = {}
        native[READ_FILE_STATE_KEY] = deposit
    return deposit if isinstance(deposit, dict) else None


def record_read_file(
    app_state: AppState | Any,
    path: str,
    *,
    timestamp: float | None = None,
) -> None:
    deposit = _deposit(app_state)
    if deposit is None or not path:
        return
    deposit[str(path)] = time.time() if timestamp is None else float(timestamp)


def read_file_state(app_state: AppState | Any) -> list[ReadFileEntry]:
    deposit = _deposit(app_state)
    if not deposit:
        return []
    entries: list[ReadFileEntry] = []
    for path, timestamp in deposit.items():
        try:
            entries.append(ReadFileEntry(path=str(path), timestamp=float(timestamp)))
        except (TypeError, ValueError):
            continue
    return entries


def clear_read_file_state(app_state: AppState | Any) -> None:
    deposit = _deposit(app_state)
    if deposit is not None:
        deposit.clear()


__all__ = [
    "READ_FILE_STATE_KEY",
    "ReadFileEntry",
    "clear_read_file_state",
    "read_file_state",
    "record_read_file",
]
