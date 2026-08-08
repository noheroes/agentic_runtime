from __future__ import annotations

import logging
from pathlib import Path

from .loader import SkillDefinition

logger = logging.getLogger(__name__)


def _file_identity(source_path: str) -> tuple[int, int] | str | None:
    """Identidad del FICHERO, no de la ruta — espejo de `getFileIdentity` (realpath).

    Devuelve `None` para una skill sin fichero (registrada por texto): entonces no hay
    nada que deduplicar, y dos skills sin ruta no son «el mismo fichero» por serlo
    ambas (`loadSkillsDir.ts:748-751`). `(st_dev, st_ino)` cuando el fichero existe —
    caza symlinks y bind mounts; si no se puede estatear, la ruta resuelta, que al
    menos caza el directorio padre duplicado.
    """
    if not source_path:
        return None
    path = Path(source_path)
    try:
        stat = path.stat()
    except OSError:
        return str(path.resolve()) if path.parent.exists() else source_path
    return (stat.st_dev, stat.st_ino)


class SkillsState:
    """Estado propio de skills — catálogo cargado, separado del registry nativo.

    Patrón del canónico (`appState`): el catálogo de skills vive fuera del runtime
    y se expone por el provider. En S0 es el catálogo cargado; el estado de skills
    *invocadas* (scopeado por `agent_id`) llega con la invocación en S1.

    **Dos vías de entrada, con reglas distintas a propósito** (`FIND-SKILL-21`):

    - `add_skills` es la vía de CARGA. Es **first-wins** por identidad y deduplica por
      identidad de fichero real, exactamente como `loadSkillsDir` (`:725-763`). La
      precedencia la expresa el host llamando en orden (managed → user → project → …),
      que es como la expresa A: por el orden de concatenación, no por un rango que
      alguien tenga que declarar. Antes esta vía era `self._skills[name] = skill`, o sea
      **last-wins**: el directorio de MENOS precedencia, por cargarse el último, pisaba
      al de más.
    - `set_skill` es la vía de ESCRITURA (registro en caliente). Mantiene last-wins,
      porque su homólogo en A es reescribir el fichero y recargar, donde la versión
      nueva gana. Confundirlas haría que registrar una skill dos veces dejara la vieja.
    """

    def __init__(self) -> None:
        self._skills: dict[str, SkillDefinition] = {}
        # Identidades de fichero ya cargadas → nombre que se quedó con el sitio.
        self._file_ids: dict[tuple[int, int] | str, str] = {}

    def set_skill(self, skill: SkillDefinition) -> None:
        """Registra (o reemplaza) una skill. Vía de ESCRITURA: last-wins."""
        previa = self._skills.get(skill.name)
        if previa is not None:
            previo_id = _file_identity(previa.source_path)
            if previo_id is not None and self._file_ids.get(previo_id) == previa.name:
                del self._file_ids[previo_id]
        self._skills[skill.name] = skill
        file_id = _file_identity(skill.source_path)
        if file_id is not None:
            self._file_ids[file_id] = skill.name

    def add_skills(self, skills: list[SkillDefinition]) -> None:
        """Añade un lote CARGADO. Vía de carga: first-wins + dedup por fichero real."""
        for skill in skills:
            file_id = _file_identity(skill.source_path)
            if file_id is not None and file_id in self._file_ids:
                logger.debug(
                    "skills: %r omitida — el mismo fichero ya se cargó como %r",
                    skill.name, self._file_ids[file_id],
                )
                continue
            if skill.name in self._skills:
                logger.debug(
                    "skills: %r omitida — ya cargada desde %r (gana la primera carga)",
                    skill.name, self._skills[skill.name].source or "?",
                )
                continue
            self._skills[skill.name] = skill
            if file_id is not None:
                self._file_ids[file_id] = skill.name

    def get(self, name: str) -> SkillDefinition | None:
        """Resuelve por IDENTIDAD y, si no, por nombre de presentación.

        Las dos vías son las de `findCommand` (`commands.ts:691-696`). La identidad va
        primero: si una skill se declara con el `name:` de otra, no puede interceptarla.
        """
        skill = self._skills.get(name)
        if skill is not None:
            return skill
        return next(
            (s for s in self._skills.values() if s.display_name and s.user_facing_name == name),
            None,
        )

    def remove(self, name: str) -> bool:
        """Quita una skill del catálogo vivo. Devuelve si estaba presente."""
        skill = self._skills.pop(name, None)
        if skill is None:
            return False
        file_id = _file_identity(skill.source_path)
        if file_id is not None and self._file_ids.get(file_id) == name:
            del self._file_ids[file_id]
        return True

    @property
    def skills(self) -> dict[str, SkillDefinition]:
        return dict(self._skills)

    def all_skills(self) -> list[SkillDefinition]:
        return list(self._skills.values())  # orden de registro


__all__ = ["SkillsState"]
