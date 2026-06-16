from __future__ import annotations

from .loader import SkillDefinition


class SkillsState:
    """Estado propio de skills — catálogo cargado, separado del registry nativo.

    Patrón del canónico (`appState`): el catálogo de skills vive fuera del runtime
    y se expone por el provider. En S0 es el catálogo cargado; el estado de skills
    *invocadas* (scopeado por `agent_id`) llega con la invocación en S1.
    """

    def __init__(self) -> None:
        self._skills: dict[str, SkillDefinition] = {}

    def set_skill(self, skill: SkillDefinition) -> None:
        self._skills[skill.name] = skill

    def add_skills(self, skills: list[SkillDefinition]) -> None:
        for skill in skills:
            self.set_skill(skill)

    def get(self, name: str) -> SkillDefinition | None:
        return self._skills.get(name)

    @property
    def skills(self) -> dict[str, SkillDefinition]:
        return dict(self._skills)

    def all_skills(self) -> list[SkillDefinition]:
        return list(self._skills.values())  # orden de registro


__all__ = ["SkillsState"]
