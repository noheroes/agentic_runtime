from __future__ import annotations

import inspect
import json
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ...contracts.tools import PermissionDecision
from ...storage.config_store import ConfigStore
from ..protocol import ToolCategory, ToolResult
from .supported_settings import SUPPORTED_SETTINGS, SettingDescriptor

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

CONFIG_TOOL_NAME = "Config"

_MISSING = object()


class ConfigRegistry:
    def __init__(
        self,
        settings: Mapping[str, SettingDescriptor] | None = None,
        stores: Mapping[str, ConfigStore] | None = None,
        source_labels: Mapping[str, str] | None = None,
    ) -> None:
        settings = SUPPORTED_SETTINGS if settings is None else settings
        stores = stores or {}
        self._settings = dict(settings)
        self._stores = dict(stores)
        self._source_labels = dict(source_labels or {})

    def label_for(self, source: str) -> str:
        label = self._source_labels.get(source)
        if label:
            return label
        return f"{source[:1].upper()}{source[1:]} Settings"

    def is_supported(self, key: str) -> bool:
        return key in self._settings

    def get(self, key: str) -> SettingDescriptor | None:
        return self._settings.get(key)

    def all_keys(self) -> list[str]:
        return list(self._settings)

    def items(self) -> list[tuple[str, SettingDescriptor]]:
        return list(self._settings.items())

    def options_for(self, key: str) -> list[str] | None:
        descriptor = self._settings.get(key)
        if descriptor is None or descriptor.options is None:
            return None
        options = descriptor.options
        resolved = options() if callable(options) else options
        return [str(option) for option in resolved]

    def path_for(self, key: str) -> list[str]:
        descriptor = self._settings.get(key)
        if descriptor is not None and descriptor.path is not None:
            return list(descriptor.path)
        return key.split(".")

    def store_for(self, source: str) -> ConfigStore | None:
        return self._stores.get(source)


DEFAULT_REGISTRY = ConfigRegistry()


def _stringify(value: Any) -> str:
    if value is _MISSING:
        return "undefined"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _read_path(store: ConfigStore, path: Sequence[str]) -> Any:
    current: Any = store.read()
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return _MISSING
    return current


def _assign(payload: dict[str, Any], path: Sequence[str], value: Any) -> dict[str, Any]:
    key = path[0]
    if len(path) == 1:
        if key in payload and payload[key] == value:
            return payload
        return {**payload, key: value}
    nested = payload.get(key)
    branch = dict(nested) if isinstance(nested, dict) else {}
    updated = _assign(branch, path[1:], value)
    if updated is branch and isinstance(nested, dict):
        return payload
    return {**payload, key: updated}


def _example_value(registry: ConfigRegistry, key: str, descriptor: SettingDescriptor) -> Any:
    options = registry.options_for(key)
    if options:
        for option in options:
            if option != "default":
                return option
        return options[0]
    if descriptor.type == "boolean":
        return True
    return _MISSING


def generate_description(registry: ConfigRegistry) -> str:
    grouped: dict[str, list[str]] = {}
    examples: list[str] = []
    for key, descriptor in registry.items():
        options = registry.options_for(key)
        line = f"- {key}"
        if options:
            line += ": " + ", ".join(f'"{option}"' for option in options)
        elif descriptor.type == "boolean":
            line += ": true/false"
        line += f" - {descriptor.description}"
        grouped.setdefault(descriptor.source, []).append(line)

        examples.append(f'- Get {key}: {{ "setting": "{key}" }}')
        example_value = _example_value(registry, key, descriptor)
        if example_value is not _MISSING:
            examples.append(
                f'- Set {key}: {{ "setting": "{key}", "value": {_stringify(example_value)} }}'
            )

    sections = ""
    for source in sorted(grouped):
        sections += f"\n### {registry.label_for(source)}\n" + "\n".join(grouped[source]) + "\n"

    listing = (
        f"""
## Configurable settings list
The following settings are available for you to change:
{sections}"""
        if sections
        else ""
    )
    examples_block = "\n## Examples\n" + "\n".join(examples) + "\n" if examples else ""

    return f"""Get or set runtime configuration settings.

View or change settings. Use when the user requests configuration changes, asks about current \
settings, or when adjusting a setting would benefit them.

## Usage
- **Get current value:** Omit the "value" parameter
- **Set new value:** Include the "value" parameter
{listing}{examples_block}"""


class ConfigTool:
    name = CONFIG_TOOL_NAME
    deferred = True
    search_hint = "get or set runtime settings"
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "setting": {
                "type": "string",
                "description": 'The setting key (e.g., "permissions.defaultMode")',
            },
            "value": {
                "type": ["string", "boolean", "number"],
                "description": "The new value. Omit to get current value.",
            },
        },
        "required": ["setting"],
        "additionalProperties": False,
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    def __init__(self, registry: ConfigRegistry | None = None) -> None:
        self.registry = registry if registry is not None else DEFAULT_REGISTRY
        self.description = generate_description(self.registry)

    async def check_permissions(
        self, input: dict[str, Any], ctx: ToolUseContext
    ) -> PermissionDecision:
        if "value" not in input:
            return PermissionDecision.allow(input)
        return PermissionDecision.ask(
            f"Set {input.get('setting')} to {_stringify(input.get('value'))}"
        )

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        setting = input.get("setting", "")
        registry = self.registry

        if not registry.is_supported(setting):
            return self._error(f'Unknown setting: "{setting}"')

        descriptor = registry.get(setting)
        if descriptor is None:
            return self._error(f'Unknown setting: "{setting}"')
        path = registry.path_for(setting)
        store = registry.store_for(descriptor.source)
        if store is None:
            return self._error(f"Invalid setting source: {descriptor.source}")

        if "value" not in input:
            current = _read_path(store, path)
            if descriptor.format_on_read is not None and current is not _MISSING:
                current = descriptor.format_on_read(current)
            return ToolResult(
                tool_name=self.name,
                output=f"{setting} = {_stringify(current)}",
            )

        value = input["value"]
        final_value: Any = value

        if descriptor.type == "boolean":
            if isinstance(value, str):
                lowered = value.lower().strip()
                if lowered == "true":
                    final_value = True
                elif lowered == "false":
                    final_value = False
            if not isinstance(final_value, bool):
                return self._error(f"{setting} requires true or false.")

        options = registry.options_for(setting)
        if options is not None and _option_text(final_value) not in options:
            return self._error(
                f'Invalid value "{value}". Options: {", ".join(options)}'
            )

        if descriptor.validate_on_write is not None:
            outcome = descriptor.validate_on_write(final_value)
            if inspect.isawaitable(outcome):
                outcome = await outcome
            valid, error = outcome
            if not valid:
                return self._error(str(error))

        previous = _read_path(store, path)

        try:
            store.update(lambda payload: _assign(payload, path, final_value))
        except Exception as exc:  # noqa: BLE001
            return self._error(str(exc))

        return ToolResult(
            tool_name=self.name,
            output=f"Set {setting} to {_stringify(final_value)}",
            metadata={"previous_value": None if previous is _MISSING else previous},
            context_modifier=_app_state_sync(descriptor.app_state_key, final_value),
        )

    def _error(self, message: str) -> ToolResult:
        return ToolResult(tool_name=self.name, output=f"Error: {message}", is_error=True)


def _app_state_sync(
    app_state_key: str | None, value: Any
) -> Callable[[ToolUseContext], ToolUseContext] | None:
    if app_state_key is None:
        return None

    def modifier(ctx: ToolUseContext) -> ToolUseContext:
        ctx.app_state.native[app_state_key] = value
        return ctx

    return modifier


def _option_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = [
    "CONFIG_TOOL_NAME",
    "DEFAULT_REGISTRY",
    "SUPPORTED_SETTINGS",
    "ConfigRegistry",
    "ConfigTool",
    "SettingDescriptor",
    "generate_description",
]
