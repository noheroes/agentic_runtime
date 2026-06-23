from __future__ import annotations

import logging

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

    name: str | None = None
    description: str | None = None
    allowed_tools: list[str] = Field(default_factory=list, alias="allowed-tools")
    model: str | None = None
    enabled: bool = True
    version: str = ""

    @field_validator("name", "description", "model", mode="before")
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
    def from_raw(cls, raw: dict) -> "SkillFrontmatter":
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
    if body.startswith("\n"):
        body = body[1:]

    try:
        loaded = yaml.safe_load(raw_block)
    except yaml.YAMLError as exc:
        logger.warning("skills: YAML de frontmatter inválido — ignorado: %s", exc)
        loaded = None

    if not isinstance(loaded, dict):
        loaded = {}

    return SkillFrontmatter.from_raw(loaded), body


__all__ = ["SkillFrontmatter", "parse_frontmatter"]
