from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from ...contracts.permissions import PermissionMode

MODEL_APP_STATE_KEY = "model"
THINKING_APP_STATE_KEY = "thinking_enabled"
EFFORT_APP_STATE_KEY = "effort"

OFF_EFFORT_LEVEL = "off"

MODEL_SETTING = "model"
PERMISSION_MODE_SETTING = "permissions.defaultMode"
THINKING_SETTING = "alwaysThinkingEnabled"
EFFORT_SETTING = "effortLevel"


@dataclass(frozen=True)
class SettingDescriptor:
    source: str
    type: str
    description: str
    path: tuple[str, ...] | None = None
    options: Sequence[str] | Callable[[], Sequence[str]] | None = None
    validate_on_write: Callable[[Any], Any] | None = None
    format_on_read: Callable[[Any], Any] | None = None
    app_state_key: str | None = None


SUPPORTED_SETTINGS: dict[str, SettingDescriptor] = {
    MODEL_SETTING: SettingDescriptor(
        source="project",
        type="string",
        description="Override the default model",
        app_state_key=MODEL_APP_STATE_KEY,
    ),
    THINKING_SETTING: SettingDescriptor(
        source="project",
        type="boolean",
        description="Enable extended thinking (false to disable)",
        app_state_key=THINKING_APP_STATE_KEY,
    ),
    EFFORT_SETTING: SettingDescriptor(
        source="global",
        type="string",
        description=f"Reasoning effort level ({OFF_EFFORT_LEVEL} to stop reasoning)",
        app_state_key=EFFORT_APP_STATE_KEY,
    ),
    PERMISSION_MODE_SETTING: SettingDescriptor(
        source="project",
        type="string",
        description="Default permission mode for tool usage",
        options=[mode.value for mode in PermissionMode],
    ),
}


def is_supported(key: str) -> bool:
    return key in SUPPORTED_SETTINGS


def get_config(key: str) -> SettingDescriptor | None:
    return SUPPORTED_SETTINGS.get(key)


def get_all_keys() -> list[str]:
    return list(SUPPORTED_SETTINGS)


def get_path(key: str) -> list[str]:
    descriptor = SUPPORTED_SETTINGS.get(key)
    if descriptor is not None and descriptor.path is not None:
        return list(descriptor.path)
    return key.split(".")


__all__ = [
    "EFFORT_APP_STATE_KEY",
    "EFFORT_SETTING",
    "MODEL_APP_STATE_KEY",
    "MODEL_SETTING",
    "OFF_EFFORT_LEVEL",
    "PERMISSION_MODE_SETTING",
    "SUPPORTED_SETTINGS",
    "THINKING_APP_STATE_KEY",
    "THINKING_SETTING",
    "SettingDescriptor",
    "get_all_keys",
    "get_config",
    "get_path",
    "is_supported",
]
