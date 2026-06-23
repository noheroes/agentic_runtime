from __future__ import annotations

from typing import TYPE_CHECKING, Callable, NamedTuple

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from .loader import SkillDefinition
    from .state import SkillsState


class SlashCommand(NamedTuple):
    name: str
    args: str


def parse_slash_command(text: str) -> SlashCommand | None:
    """Parsea `/<skill> [args]`. Devuelve None si no es un slash command.

    No decide si la skill existe — solo separa nombre y args (la resolución la hace
    el provider). Tolerante: `/`, espacios sobrantes o vacío → None.
    """
    stripped = text.strip()
    if not stripped.startswith("/") or stripped == "/":
        return None
    body = stripped[1:]
    head, _, rest = body.partition(" ")
    if not head:
        return None
    return SlashCommand(name=head, args=rest.strip())


def process_slash_command(
    text: str,
    state: "SkillsState",
    ctx: "ToolUseContext",
    *,
    is_enabled: "Callable[[SkillDefinition], bool] | None" = None,
) -> str | None:
    """Procesa un slash command de skill (S4), desacoplado del loop.

    Si `text` es `/<skill> args` y `<skill>` existe (y está habilitada), activa la
    skill en `ctx` (mismo efecto que invocar la tool `Skill`: estado activo +
    allowed-tools) y devuelve sus instrucciones renderizadas. Devuelve None si no es un
    slash command, la skill no existe o está deshabilitada — el integrador lo trata
    como prompt normal.

    El fork/background NO lo decide la skill: si un slash command lanza un subagente,
    lo hace el runtime vía `RuntimeContextForker` (la capability solo activa inline).
    """
    parsed = parse_slash_command(text)
    if parsed is None:
        return None
    skill = state.get(parsed.name)
    if skill is None:
        return None
    from .loader import default_is_enabled

    if not (is_enabled or default_is_enabled)(skill):
        return None

    from .skill_tool import build_skill_context_modifier, render_skill

    build_skill_context_modifier(skill)(ctx)  # muta ctx in-place: activa la skill
    return render_skill(skill)


__all__ = ["SlashCommand", "parse_slash_command", "process_slash_command"]
