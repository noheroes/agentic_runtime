from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...tools.protocol import ToolCategory, ToolResult
from .loader import SkillDefinition
from .state import SkillsState

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

logger = logging.getLogger(__name__)

SKILL_TOOL_NAME = "Skill"


def render_skill(skill: SkillDefinition) -> str:
    """Renderiza la skill como mensaje meta (instrucciones + framing de 'continuar').

    El modelo recibe las instrucciones sin tener que reinvocar la skill (S1): el
    texto va como contenido del tool result (rol `tool`, no un `user` plano).
    """
    head = f"Skill '{skill.name}' activada."
    if skill.allowed_tools:
        head += f" Tools habilitadas: {', '.join(skill.allowed_tools)}."
    body = skill.instructions.strip()
    tail = "Continúa siguiendo estas instrucciones durante la tarea (no reinvoques la skill)."
    return "\n\n".join(p for p in (head, body, tail) if p)


def build_skill_context_modifier(skill: SkillDefinition):
    """Construye el `context_modifier` de una skill invocada (S2).

    Muta ctx in-place (convención del runtime): registra la skill activa en
    `app_state.capabilities` (scoped por agente vía ctx) y añade sus `allowed_tools`
    al `PermissionContext`. Marca esas tools como descubiertas para que las MCP
    diferidas que la skill habilita se anuncien (cruce S2↔M3: 'Skill(x) habilita x__*').
    """

    def modifier(c: "ToolUseContext") -> "ToolUseContext":
        caps = c.app_state.capabilities
        invoked = caps.setdefault("invoked_skills", [])
        if skill.name not in invoked:
            invoked.append(skill.name)
        # Estado activo estructurado: contenido completo, no solo el nombre (S1).
        caps.setdefault("active_skills", {})[skill.name] = {
            "content": skill.instructions,
            "allowed_tools": list(skill.allowed_tools),
            "model": skill.model,
        }
        if skill.allowed_tools:
            c.app_state.permissions = c.app_state.permissions.with_command_allow(skill.allowed_tools)
            from ...tools.deferred import mark_tools_discovered

            mark_tools_discovered(c, skill.allowed_tools)
        return c

    return modifier


class SkillTool:
    """Tool `Skill` — invoca una skill como comando procesado (S1/S2).

    No es diferida (el modelo la necesita para activar skills) y no requiere permiso.
    Al invocarse deja estado activo estructurado (`active_skills`) y habilita las
    `allowed_tools` de la skill vía `context_modifier`, sin que el runtime derive
    tools desde `invoked_skills`.
    """

    name = SKILL_TOOL_NAME
    description = (
        "Invoke an available skill by name to load its instructions and enable its tools. "
        "Pass the skill name as 'command'."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Name of the skill to invoke."},
            "args": {"type": "string", "description": "Optional arguments for the skill."},
        },
        "required": ["command"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self, state: SkillsState) -> None:
        self._state = state

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        command = (input.get("command") or "").strip()
        skill = self._state.get(command)
        if skill is None:
            available = ", ".join(s.name for s in self._state.all_skills()) or "(ninguna)"
            return ToolResult.error(
                self.name, f"skill '{command}' no encontrada. Disponibles: {available}"
            )

        result = ToolResult(tool_name=self.name, output=render_skill(skill))
        result.context_modifier = build_skill_context_modifier(skill)  # type: ignore[attr-defined]
        return result


__all__ = ["SKILL_TOOL_NAME", "SkillTool", "build_skill_context_modifier", "render_skill"]
