from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..contracts import CapabilitySummary
from .loader import (
    SkillDefinition,
    default_is_enabled,
    load_skill_text,
    load_skills_dir,
)
from .state import SkillsState

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ...tools.protocol import ToolProtocol
    from .store import SkillStore

logger = logging.getLogger(__name__)


class SkillsProvider:
    name = "skills"

    def __init__(
        self,
        state: SkillsState | None = None,
        *,
        skill_store: SkillStore | None = None,
        is_enabled: Callable[[SkillDefinition], bool] | None = None,
    ) -> None:
        self._state = state or SkillsState()
        self._skill_store = skill_store
        self._is_enabled = is_enabled or default_is_enabled

    @property
    def state(self) -> SkillsState:
        return self._state

    def load_dir(self, root: str | Path) -> list[SkillDefinition]:
        skills = load_skills_dir(Path(root))
        self._state.add_skills(skills)
        return skills

    def add_skill_text(
        self, name: str, text: str, *, source_path: str = ""
    ) -> SkillDefinition:
        skill = load_skill_text(name, text, source_path=source_path)
        self._state.set_skill(skill)
        return skill

    def process_slash_command(self, text: str, context: ToolUseContext) -> str | None:
        from .commands import process_slash_command

        return process_slash_command(text, self._state, context, is_enabled=self._is_enabled)

    async def register_skill(self, name: str, content: str) -> SkillDefinition:
        if self._skill_store is not None:
            await self._skill_store.write(name, content)
        return self.add_skill_text(name, content)

    async def unregister(self, name: str) -> bool:
        if self._skill_store is not None:
            try:
                await self._skill_store.remove(name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("skills: no se pudo borrar %r del store: %s", name, exc)
        return self._state.remove(name)

    async def startup(self) -> None:
        if self._skill_store is None:
            return
        try:
            names = await self._skill_store.list()
        except Exception as exc:  # noqa: BLE001
            logger.warning("skills: no se pudo listar el store: %s", exc)
            return
        for name in names:
            try:
                content = await self._skill_store.read(name)
                if content is not None:
                    self.add_skill_text(name, content)
            except Exception as exc:  # noqa: BLE001
                logger.warning("skills: no se pudo cargar %r del store: %s", name, exc)
        return

    async def shutdown(self) -> None:
        return None

    def catalog(self, context: ToolUseContext) -> list[CapabilitySummary]:
        return [
            CapabilitySummary(
                name=skill.name,
                kind="skill",
                description=skill.description,
                when_to_use=skill.when_to_use,
                provider=self.name,
                source=skill.source,
            )
            for skill in self._state.all_skills()
            if self._is_enabled(skill) and not skill.disable_model_invocation
        ]

    def tools(self, context: ToolUseContext) -> list[ToolProtocol]:
        if not any(self._is_enabled(s) for s in self._state.all_skills()):
            return []
        from .skill_tool import SkillTool

        return [SkillTool(self._state, is_enabled=self._is_enabled)]

    def active_context(self, context: ToolUseContext) -> list[dict[str, Any]]:
        return []

    def compact_context(self, context: ToolUseContext) -> list[dict[str, Any]]:
        active = context.app_state.capabilities.get("active_skills", {})
        messages: list[dict[str, Any]] = []
        for name, info in active.items():
            base = info.get("base_dir") or ""
            base_line = f"Base directory for this skill: {base}\n\n" if base else ""
            messages.append({
                "role": "system",
                "content": (
                    f"Skill activa '{name}': continúa siguiendo sus instrucciones.\n\n"
                    f"{base_line}{info.get('content', '').strip()}"
                ),
            })
        return messages


__all__ = ["SkillsProvider"]
