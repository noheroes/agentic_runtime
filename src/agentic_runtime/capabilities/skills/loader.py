from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, Field

from .frontmatter import parse_frontmatter

logger = logging.getLogger(__name__)

_INHERIT = {None, "", "inherit"}


class SkillDefinition(BaseModel):
    """Una skill cargada — salida tipada del loader (nunca un dict suelto).

    `model is None` significa **heredar el modelo del padre** (default operativo
    cuando el frontmatter omite `model` o dice `inherit`). `allowed_tools` vacío
    significa **no activa tools extra**.
    """

    name: str
    description: str = ""
    instructions: str = ""
    allowed_tools: list[str] = Field(default_factory=list)
    model: str | None = None
    source_path: str = ""


def _first_paragraph(body: str) -> str:
    for block in body.split("\n\n"):
        text = block.strip()
        if text:
            return " ".join(text.split())
    return ""


def load_skill_text(name_hint: str, text: str, *, source_path: str = "") -> SkillDefinition:
    """Construye una `SkillDefinition` desde el texto de un `SKILL.md`, TOLERANTE.

    `name_hint` (nombre del directorio) garantiza la identidad aunque el frontmatter
    omita `name`. `description` ausente se deriva del cuerpo; `model` ausente/`inherit`
    → `None` (hereda el del padre); `allowed-tools` ausente → `[]` (no activa nada).
    """
    front, body = parse_frontmatter(text)
    name = front.name or name_hint
    description = front.description or _first_paragraph(body)
    model = None if front.model in _INHERIT else front.model
    return SkillDefinition(
        name=name,
        description=description,
        instructions=body,
        allowed_tools=front.allowed_tools,
        model=model,
        source_path=source_path,
    )


def load_skill_file(path: Path) -> SkillDefinition | None:
    """Carga una skill desde un archivo `SKILL.md`. IO ilegible → log + None."""
    name_hint = path.parent.name if path.name == "SKILL.md" else path.stem
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("skills: no se pudo leer %s — omitida: %s", path, exc)
        return None
    return load_skill_text(name_hint, text, source_path=str(path))


def load_skills_dir(root: Path) -> list[SkillDefinition]:
    """Carga TOLERANTE de un directorio de skills (`<root>/<skill>/SKILL.md`).

    Aislamiento por ítem: un `SKILL.md` que falle al cargar se salta con log; el
    resto carga. Orden estable por ruta para que el catálogo sea determinista.
    """
    skills: list[SkillDefinition] = []
    if not root.is_dir():
        return skills
    for path in sorted(root.glob("*/SKILL.md")):
        try:
            skill = load_skill_file(path)
        except Exception as exc:  # noqa: BLE001 — aislamiento por ítem
            logger.warning("skills: fallo al cargar %s — omitida: %s", path, exc)
            continue
        if skill is not None:
            skills.append(skill)
    return skills


__all__ = ["SkillDefinition", "load_skill_file", "load_skill_text", "load_skills_dir"]
