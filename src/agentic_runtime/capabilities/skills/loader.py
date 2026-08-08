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

    #: IDENTIDAD. La fija la ESTRUCTURA (el nombre del directorio), nunca el contenido
    #: del fichero — `FIND-SKILL-20`, espejo de `const skillName = entry.name`
    #: (`loadSkillsDir.ts:452`). Antes era `front.name or name_hint`, así que un
    #: `SKILL.md` de terceros podía declararse con el nombre de otra skill y quedarse
    #: con su sitio en el catálogo, que indexa por este campo.
    name: str
    #: PRESENTACIÓN (`displayName` del canónico, `:238-239`). `""` = no declarado.
    #: Sólo lo lee `user_facing_name`; no participa en la identidad.
    display_name: str = ""
    description: str = ""
    #: CUÁNDO usar la skill (`whenToUse`, `:252`). Se concatena a la descripción en el
    #: listado; vacío = no aporta.
    when_to_use: str = ""
    instructions: str = ""
    allowed_tools: list[str] = Field(default_factory=list)
    #: Nombres POSICIONALES de los argumentos (`argNames` del canónico, `:324`): habilitan
    #: los placeholders `$nombre` además de `$ARGUMENTS`/`$0`. Vacío = sólo indexados.
    argument_names: list[str] = Field(default_factory=list)
    model: str | None = None
    source_path: str = ""
    # Directorio de la skill (`skillRoot`/`baseDir` del canónico): permite al modelo
    # localizar archivos bundled (scripts/, templates/) por ruta. Vacío si la skill se
    # registró solo como contenido (sin directorio en disco).
    base_dir: str = ""
    # Enablement declarativa (frontmatter `enabled`, default true). La consume el
    # predicado por defecto del provider; deshabilitada → fuera del catálogo y no invocable.
    enabled: bool = True
    # Versión declarada (frontmatter `version`): passthrough de trazabilidad para el
    # integrador (p.ej. manifest de sesión). El runtime no la interpreta.
    version: str = ""
    # `disable-model-invocation`: la skill sigue siendo del usuario (`/nombre`) pero el
    # MODELO no la ve en el listado ni puede invocarla por la tool (`SkillTool.ts:412-418`).
    disable_model_invocation: bool = False

    # --- ORIGEN (`FIND-SKILL-21`) ----------------------------------------------
    # Dos ejes, como en el canónico: `source` = de qué ámbito de settings viene
    # (`SettingSource`: managed/user/project/…) y `loaded_from` = por qué vía se cargó
    # (`LoadedFrom`: skills/plugin/bundled/mcp/…, `loadSkillsDir.ts:67-73`).
    # Passthrough OPACO: la taxonomía es política del host y el runtime no la interpreta
    # ni la valida — la PRECEDENCIA la expresa el host por el ORDEN en que carga, igual
    # que A la expresa por el orden de concatenación (`:717-723`). El único uso que el
    # runtime hace de estos campos es el que hace A: exentar a las `bundled` del recorte
    # del listado (`SkillTool/prompt.ts:97`).
    source: str = ""
    loaded_from: str = ""

    @property
    def user_facing_name(self) -> str:
        """Nombre para MOSTRAR — espejo de `userFacingName()` (`:337-339`).

        Es lo contrario de la identidad y por eso vive aparte: se puede resolver por él
        (`findCommand`, `commands.ts:691-696`), pero no indexa el catálogo."""
        return self.display_name or self.name


def default_is_enabled(skill: SkillDefinition) -> bool:
    """Predicado de enablement por defecto: la skill declara su estado en el frontmatter.

    Espejo del `isEnabled` canónico (un predicado de código, no un toggle persistido).
    El integrador puede inyectar otro predicado (p.ej. feature flags) en el provider."""
    return skill.enabled


def _first_paragraph(body: str) -> str:
    for block in body.split("\n\n"):
        text = block.strip()
        if text:
            return " ".join(text.split())
    return ""


def load_skill_text(
    name_hint: str,
    text: str,
    *,
    source_path: str = "",
    base_dir: str = "",
    source: str = "",
    loaded_from: str = "",
) -> SkillDefinition:
    """Construye una `SkillDefinition` desde el texto de un `SKILL.md`, TOLERANTE.

    `name_hint` (nombre del directorio) **es** la identidad, la declare o no el
    frontmatter: un `name:` declarado va a `display_name` y no desplaza a nadie
    (`FIND-SKILL-20`). `description` ausente se deriva del cuerpo; `model`
    ausente/`inherit` → `None` (hereda el del padre); `allowed-tools` ausente → `[]`
    (no activa nada). `base_dir` es el directorio de la skill (para localizar archivos
    bundled); `source`/`loaded_from` los pone quien carga (ver `SkillDefinition`).
    """
    front, body = parse_frontmatter(text)
    description = front.description or _first_paragraph(body)
    model = None if front.model in _INHERIT else front.model
    return SkillDefinition(
        name=name_hint,
        display_name=front.name or "",
        description=description,
        when_to_use=front.when_to_use or "",
        instructions=body,
        allowed_tools=front.allowed_tools,
        argument_names=front.arguments,
        model=model,
        source_path=source_path,
        base_dir=base_dir,
        enabled=front.enabled,
        version=front.version,
        disable_model_invocation=front.disable_model_invocation,
        source=source,
        loaded_from=loaded_from,
    )


def load_skill_file(
    path: Path, *, source: str = "", loaded_from: str = ""
) -> SkillDefinition | None:
    """Carga una skill desde un archivo `SKILL.md`. IO ilegible → log + None.

    `base_dir` = el directorio de la skill (donde viven scripts/, templates/, …)."""
    name_hint = path.parent.name if path.name == "SKILL.md" else path.stem
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("skills: no se pudo leer %s — omitida: %s", path, exc)
        return None
    return load_skill_text(
        name_hint,
        text,
        source_path=str(path),
        base_dir=str(path.parent),
        source=source,
        loaded_from=loaded_from,
    )


def load_skills_dir(
    root: Path, *, source: str = "", loaded_from: str = ""
) -> list[SkillDefinition]:
    """Carga TOLERANTE de un directorio de skills (`<root>/<skill>/SKILL.md`).

    Aislamiento por ítem: un `SKILL.md` que falle al cargar se salta con log; el
    resto carga. Orden estable por ruta para que el catálogo sea determinista.

    `source`/`loaded_from` rotulan TODO lo que sale de este directorio: es el host
    quien sabe si este `root` es el ámbito gestionado, el del usuario o el del
    proyecto, y el runtime no lo adivina de la ruta.
    """
    skills: list[SkillDefinition] = []
    if not root.is_dir():
        return skills
    for path in sorted(root.glob("*/SKILL.md")):
        try:
            skill = load_skill_file(path, source=source, loaded_from=loaded_from)
        except Exception as exc:  # noqa: BLE001 — aislamiento por ítem
            logger.warning("skills: fallo al cargar %s — omitida: %s", path, exc)
            continue
        if skill is not None:
            skills.append(skill)
    return skills


__all__ = [
    "SkillDefinition",
    "default_is_enabled",
    "load_skill_file",
    "load_skill_text",
    "load_skills_dir",
]
