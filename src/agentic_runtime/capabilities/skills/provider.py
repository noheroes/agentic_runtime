from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ..contracts import CapabilitySummary
from .loader import SkillDefinition, load_skill_text, load_skills_dir
from .state import SkillsState

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ...tools.protocol import ToolProtocol

logger = logging.getLogger(__name__)


class SkillsProvider:
    """`CapabilityProvider` de Skills — catálogo conectado por contrato.

    El runtime no accede a `skills.loader`: pide el catálogo al `CapabilityManager`,
    que lo pide a este provider. S0 (shell): carga tolerante + catálogo. La
    invocación de skills (mensajes meta, allowed-tools al contexto, estado activo
    por `agent_id`) llega en S1–S3; la compactación en S5. Por eso `tools`,
    `active_context` y `compact_context` devuelven vacío hoy — declarado, no fingido.

    Robustez ante skills de terceros — directivas estándar vs. operativas:

    | directiva       | estándar | ausente/malformada → comportamiento          |
    |-----------------|----------|----------------------------------------------|
    | `name`          | sí       | identidad ← nombre del directorio            |
    | `description`   | sí       | se deriva del primer párrafo del cuerpo      |
    | `allowed-tools` | no       | `[]` → no activa tools extra                 |
    | `model`         | no       | `None`/`inherit` → hereda el modelo del padre|

    Estrictez reservada a seguridad/identidad: aquí no hay borde estricto porque la
    identidad siempre se resuelve desde el directorio; el aislamiento por ítem evita
    que un `SKILL.md` corrupto tumbe la carga del resto.
    """

    name = "skills"

    def __init__(self, state: SkillsState | None = None) -> None:
        self._state = state or SkillsState()

    @property
    def state(self) -> SkillsState:
        return self._state

    # --- carga (lo usa el integrador) ------------------------------------

    def load_dir(self, root: str | Path) -> list[SkillDefinition]:
        """Carga tolerante de un directorio de skills (aislamiento por ítem)."""
        skills = load_skills_dir(Path(root))
        self._state.add_skills(skills)
        return skills

    def add_skill_text(
        self, name: str, text: str, *, source_path: str = ""
    ) -> SkillDefinition:
        """Registra una skill desde texto (carga explícita, p.ej. tests)."""
        skill = load_skill_text(name, text, source_path=source_path)
        self._state.set_skill(skill)
        return skill

    def process_slash_command(self, text: str, context: "ToolUseContext") -> str | None:
        """Procesa `/<skill> args` (S4): activa la skill en el contexto y devuelve sus
        instrucciones, o None si no aplica. El loop NO importa esto — lo usa el integrador."""
        from .commands import process_slash_command

        return process_slash_command(text, self._state, context)

    # --- contrato CapabilityProvider -------------------------------------

    async def startup(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    def catalog(self, context: "ToolUseContext") -> list[CapabilitySummary]:
        return [
            CapabilitySummary(
                name=skill.name,
                kind="skill",
                description=skill.description,
                when_to_use=skill.description,
                provider=self.name,
            )
            for skill in self._state.all_skills()
        ]

    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]:
        # La tool `Skill` (invocación) solo si hay skills que invocar (S1).
        if not self._state.all_skills():
            return []
        from .skill_tool import SkillTool

        return [SkillTool(self._state)]

    def active_context(self, context: "ToolUseContext") -> list[dict]:
        """Skills activas en este contexto → mensajes 'continúa siguiendo' (S3).

        Scoped por agente: lee `app_state.capabilities['active_skills']` del ctx, que
        la invocación pobló. No reinyecta el catálogo como mandato de reinvocación.
        """
        active = context.app_state.capabilities.get("active_skills", {})
        messages: list[dict] = []
        for name, info in active.items():
            messages.append({
                "role": "system",
                "content": (
                    f"Skill activa '{name}': continúa siguiendo sus instrucciones.\n\n"
                    f"{info.get('content', '').strip()}"
                ),
            })
        return messages

    def compact_context(self, context: "ToolUseContext") -> list[dict]:
        """Tras compactación: preservar skills activas como 'continue to follow' (S5).

        Mismo aporte que `active_context` — el contenido de la skill sobrevive a la
        compactación (no solo el nombre), y NO induce reinvocación.
        """
        return self.active_context(context)


__all__ = ["SkillsProvider"]
