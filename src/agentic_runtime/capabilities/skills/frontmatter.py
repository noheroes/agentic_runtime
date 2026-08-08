from __future__ import annotations

import logging
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

_DELIM = "---"


class SkillFrontmatter(BaseModel):
    """Frontmatter de un `SKILL.md` — schema abierto, tolerante por campo.

    Robustez ante terceros (ver plan §"Robustez Ante Skills/MCP De Terceros"):
    - `extra="allow"`: directivas que NO son del estándar de Agent Skills (las
      consolidadas por registros de terceros) se conservan sin romper el parseo.
    - Cada campo operativo es `Optional`/con default y degrada a un comportamiento
      definido, nunca a error: ver la tabla en `SkillsProvider`.
    - No hay borde de seguridad aquí: la identidad (`name`) la garantiza el loader
      desde el nombre del directorio aunque el frontmatter la omita o la malforme.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    #: Nombre de PRESENTACIÓN, nunca identidad (`FIND-SKILL-20`): el canónico lo mete en
    #: `displayName` y sólo lo lee `userFacingName()` (`loadSkillsDir.ts:238-239`,
    #: `:337-339`). La identidad es el nombre del directorio (`:452`).
    name: str | None = None
    description: str | None = None
    #: `when_to_use` del canónico (`loadSkillsDir.ts:252`): CUÁNDO usar la skill. Se
    #: concatena a la descripción en el listado (`SkillTool/prompt.ts:43-50`).
    when_to_use: str | None = None
    allowed_tools: list[str] = Field(default_factory=list, alias="allowed-tools")
    model: str | None = None
    enabled: bool = True
    #: `disable-model-invocation` (`loadSkillsDir.ts:255-257`): la skill sigue siendo del
    #: usuario (`/nombre`) pero el MODELO no la ve ni puede invocarla. Distinto de
    #: `enabled: false`, que la retira para todos.
    disable_model_invocation: bool = Field(default=False, alias="disable-model-invocation")
    #: `arguments` (`loadSkillsDir.ts:249-251`): nombres POSICIONALES para los placeholders
    #: `$nombre` del cuerpo. Lista o cadena separada por espacios; vacío = sólo indexados.
    arguments: list[str] = Field(default_factory=list)
    version: str = ""

    @field_validator("name", "description", "when_to_use", "model", mode="before")
    @classmethod
    def _coerce_optional_str(cls, value: object) -> str | None:
        # Un valor no-string (p.ej. `name: [x]`) degrada a None, no a error de tipo.
        return value if isinstance(value, str) else None

    @field_validator("enabled", mode="before")
    @classmethod
    def _coerce_enabled(cls, value: object) -> bool:
        # Enablement como predicado declarativo (espejo del `isEnabled` canónico). Solo
        # `false` literal (bool o string) deshabilita; ausente o corrupto → habilitado
        # (default seguro: un frontmatter malformado no debe silenciar una skill).
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in {"false", "0", "no"}
        return True

    @field_validator("disable_model_invocation", mode="before")
    @classmethod
    def _coerce_disable_model_invocation(cls, value: object) -> bool:
        # Espejo EXACTO de `parseBooleanFrontmatter` (`frontmatterParser.ts:332-334`):
        # sólo `true` literal (bool o string) activa. La asimetría con `enabled` —que
        # degrada a habilitado— es deliberada y es la misma que la de A: el default
        # seguro de una RESTRICCIÓN es no restringir, el de una PUBLICACIÓN es publicar.
        return value is True or (isinstance(value, str) and value.strip().lower() == "true")

    @field_validator("arguments", mode="before")
    @classmethod
    def _coerce_arguments(cls, value: object) -> list[str]:
        # Delegado en el mismo parser que usa A (`parseArgumentNames`), para que el
        # descarte de vacíos y numéricos puros viva en UN sitio y no en dos.
        from .arguments import parse_argument_names

        if isinstance(value, str):
            return parse_argument_names(value)
        if isinstance(value, list):
            return parse_argument_names([str(v) for v in value])
        return []

    @field_validator("version", mode="before")
    @classmethod
    def _coerce_version(cls, value: object) -> str:
        # Passthrough de trazabilidad: YAML puede dar float/int (`version: 1.0`) →
        # str; ausente/None → "". No es campo de seguridad; nunca lanza.
        return "" if value is None else str(value)

    @field_validator("allowed_tools", mode="before")
    @classmethod
    def _coerce_allowed_tools(cls, value: object) -> list[str]:
        # El canónico acepta lista o string separado por comas; cualquier otra
        # cosa (o ausencia) → lista vacía = "no activa tools extra".
        if isinstance(value, str):
            return [t.strip() for t in value.split(",") if t.strip()]
        if isinstance(value, list):
            return [str(t).strip() for t in value if str(t).strip()]
        return []

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> SkillFrontmatter:
        """Construcción TOTAL — nunca lanza. Frontmatter corrupto → defaults."""
        try:
            return cls.model_validate(raw)
        except Exception as exc:  # noqa: BLE001 — tolerancia por contrato
            logger.warning("skills: frontmatter inválido — usando defaults: %s", exc)
            return cls()


def parse_frontmatter(text: str) -> tuple[SkillFrontmatter, str]:
    """Separa frontmatter YAML del cuerpo de un `SKILL.md`, de forma TOLERANTE.

    Espejo del parser del canónico: sin frontmatter → `{}`; YAML inválido o que no
    produce un mapping → log + `{}`. Nunca lanza. Devuelve `(frontmatter, body)`.
    """
    stripped = text.lstrip("﻿")  # tolera BOM al inicio
    if not stripped.startswith(_DELIM):
        return SkillFrontmatter.from_raw({}), text

    # Busca el delimitador de cierre tras la primera línea `---`.
    rest = stripped[len(_DELIM):]
    end = rest.find(f"\n{_DELIM}")
    if end == -1:
        # Apertura sin cierre → no es frontmatter válido; todo es cuerpo.
        return SkillFrontmatter.from_raw({}), text

    raw_block = rest[:end]
    body_start = end + 1 + len(_DELIM)
    body = rest[body_start:]
    body = body.removeprefix("\n")

    try:
        loaded = yaml.safe_load(raw_block)
    except yaml.YAMLError as exc:
        logger.warning("skills: YAML de frontmatter inválido — ignorado: %s", exc)
        loaded = None

    if not isinstance(loaded, dict):
        loaded = {}

    return SkillFrontmatter.from_raw(loaded), body


__all__ = ["SkillFrontmatter", "parse_frontmatter"]
