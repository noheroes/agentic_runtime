from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ...tools.protocol import ToolCategory, ToolResult
from .arguments import substitute_arguments
from .loader import SkillDefinition, default_is_enabled
from .state import SkillsState

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

logger = logging.getLogger(__name__)

SKILL_TOOL_NAME = "Skill"


def render_skill(skill: SkillDefinition, args: str | None = None, *, session_id: str = "") -> str:
    """Renderiza la skill como mensaje meta (instrucciones + framing de 'continuar').

    El modelo recibe las instrucciones sin tener que reinvocar la skill (S1): el
    texto va como contenido del tool result (rol `tool`, no un `user` plano).

    Si la skill tiene `base_dir`, se antepone "Base directory for this skill: <dir>"
    (espejo del canónico): así el modelo localiza los archivos bundled (scripts/,
    templates/) por ruta y los ejecuta vía bash. Las subcarpetas no tienen manejo
    especial — son archivos del directorio que el modelo referencia desde el base_dir.

    `args` (`LAT-SKILL1`) se sustituye en el contenido de la SKILL —`base_dir` + cuerpo,
    exactamente el mismo texto sobre el que sustituye `getPromptForCommand`
    (`loadSkillsDir.ts:344-354`)— y **nunca sobre el marco** que pone el runtime: la
    cabecera y la coleta son instrucción del sistema, no del usuario, y dejarlas dentro
    del alcance haría que un dato del turno pudiera reescribirlas. `None` = no se pasaron
    argumentos y el contenido no se toca.

    Tras los args se sustituyen las dos variables del canónico (`loadSkillsDir.ts:356-369`),
    en ESE orden: `${CLAUDE_SKILL_DIR}` **sólo si la skill tiene directorio** —sin él no hay
    valor que poner y una cadena vacía fabricaría rutas absolutas falsas— y
    `${CLAUDE_SESSION_ID}`, siempre. Van después de los args igual que en A, así que un
    argumento que contenga la variable la ve expandida.
    """
    head = f"Skill '{skill.name}' activada."
    if skill.allowed_tools:
        head += f" Tools habilitadas: {', '.join(skill.allowed_tools)}."
    base = f"Base directory for this skill: {skill.base_dir}" if skill.base_dir else ""
    body = skill.instructions.strip()
    contenido = "\n\n".join(p for p in (base, body) if p)
    contenido = substitute_arguments(contenido, args, argument_names=skill.argument_names)
    if skill.base_dir:
        contenido = contenido.replace("${CLAUDE_SKILL_DIR}", skill.base_dir)
    contenido = contenido.replace("${CLAUDE_SESSION_ID}", session_id)
    tail = "Continúa siguiendo estas instrucciones durante la tarea (no reinvoques la skill)."
    return "\n\n".join(p for p in (head, contenido, tail) if p)


def build_skill_context_modifier(
    skill: SkillDefinition,
) -> Callable[[ToolUseContext], ToolUseContext]:
    """Construye el `context_modifier` de una skill invocada (S2).

    Muta ctx in-place (convención del runtime): registra la skill activa en
    `app_state.capabilities` (scoped por agente vía ctx) y añade sus `allowed_tools`
    al `PermissionContext`. Marca esas tools como descubiertas para que las MCP
    diferidas que la skill habilita se anuncien (cruce S2↔M3: 'Skill(x) habilita x__*').
    """

    def modifier(c: ToolUseContext) -> ToolUseContext:
        caps = c.app_state.capabilities
        invoked = caps.setdefault("invoked_skills", [])
        if skill.name not in invoked:
            invoked.append(skill.name)
        # Estado activo estructurado: contenido completo, no solo el nombre (S1).
        caps.setdefault("active_skills", {})[skill.name] = {
            "content": skill.instructions,
            "allowed_tools": list(skill.allowed_tools),
            "model": skill.model,
            "base_dir": skill.base_dir,
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
    # Homologada contra `SkillTool/prompt.ts:173-196` (`getPrompt()`). La frase del
    # listado sólo es legítima porque B lo EMITE de verdad desde `FIND-SKILL9/17`
    # (`capabilities/skill_listing_delta.py` + `AgentLoop._announce_skill_listing`); hay
    # test que se pone rojo si deja de emitirse.
    #
    # OMITIDO Y DECLARADO — describiría superficie que B no tiene:
    #   · el nombre cualificado de plugin (`ms-office-suite:pdf`, `:186`)
    #   · la guarda del `<command-name>` ya cargado (`:194`): B no marca así el turno
    #   · la lista de comandos de CLI built-in (`:193`): B no tiene ninguno
    description = """Execute a skill within the main conversation.

When users ask you to perform tasks, check if any of the available skills match. \
Skills provide specialized capabilities and domain knowledge.

When users reference a "slash command" or "/<something>" (e.g., "/commit", "/review-pr"), \
they are referring to a skill. Use this tool to invoke it.

How to invoke:
- Use this tool with the skill name as 'command' and optional 'args'
- Examples:
  - `command: "pdf"` - invoke the pdf skill
  - `command: "commit", args: "-m 'Fix bug'"` - invoke with arguments

Important:
- Available skills are listed in <system-reminder> messages in the conversation
- When a skill matches the user's request, this is a BLOCKING REQUIREMENT: invoke the \
relevant Skill tool BEFORE generating any other response about the task
- NEVER mention a skill without actually calling this tool
- Do not invoke a skill that is already running
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
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

    def __init__(
        self,
        state: SkillsState,
        *,
        is_enabled: Callable[[SkillDefinition], bool] | None = None,
    ) -> None:
        self._state = state
        # Predicado de enablement (espejo del `isEnabled` canónico): una skill
        # deshabilitada no es invocable ni aparece en la lista de disponibles.
        self._is_enabled = is_enabled or default_is_enabled

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        command = (input.get("command") or "").strip()
        skill = self._state.get(command)
        if skill is None or not self._is_enabled(skill):
            available = ", ".join(
                s.name
                for s in self._state.all_skills()
                if self._is_enabled(s) and not s.disable_model_invocation
            ) or "(ninguna)"
            return ToolResult.error(
                self.name, f"skill '{command}' no encontrada. Disponibles: {available}"
            )
        if skill.disable_model_invocation:
            # Espejo del errorCode 4 de `validateInput` (`SkillTool.ts:412-418`). Filtrar
            # sólo el listado no bastaría: el modelo puede nombrarla igual (la vio en un
            # `/comando` del usuario, o la adivinó). La skill sigue siendo del usuario.
            return ToolResult.error(
                self.name,
                f"skill '{command}' no puede invocarse desde la tool "
                f"{self.name} (disable-model-invocation).",
            )

        # `None` (ausente) y `""` (invocada sin args) NO son lo mismo — ver `render_skill`.
        # Un no-string se coerce en vez de descartarse: perder el dato en silencio es
        # justo el defecto que se está pagando.
        raw_args = input.get("args")
        args = raw_args if raw_args is None or isinstance(raw_args, str) else str(raw_args)

        return ToolResult(
            tool_name=self.name,
            output=render_skill(skill, args, session_id=ctx.session_id),
            context_modifier=build_skill_context_modifier(skill),
        )


__all__ = ["SKILL_TOOL_NAME", "SkillTool", "build_skill_context_modifier", "render_skill"]
