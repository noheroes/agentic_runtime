"""
`ConfinedFilesystem` — costura de confinamiento de paths para las fs-tools, inyectable.

Espejo de `ctx.exec_env` (ver `exec_env.py`): las tools que tocan el filesystem
(`write_file`, `read_file`, `Edit`, `glob`, `grep`) NO construyen `Path(input[...])` crudo;
resuelven vía ``ctx.fs.resolve(token, for_write=...)``, que traduce token→host path (política
del consumidor, vía `StorageContract`) y luego **confina** el path contra un allow-set de roots.

El chequeo de confinamiento es mecanismo genérico homologado del canónico
(`utils/permissions/filesystem.ts`: `pathInAllowedWorkingPath` / `pathInWorkingPath` +
`getPathsForPermissionCheck` + `containsPathTraversal`). Es un gate de permisos in-process en la
capa de tools, NO un sandbox de SO. Solo se inyecta el *valor* (roots) + la traducción token→path;
ningún consumidor re-implementa el chequeo (evita drift/heurística, Regla 1).

Divergencia por política del consumidor: el canónico single-user hace `ask` fuera del working-dir;
un consumidor server-side autónomo mapea fuera-del-allow-set a deny duro (`PathOutsideWorkspace`).
Misma maquinaria, distinto desenlace — decisión del integrador, no del runtime.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..contracts.storage import StorageContract


class PathOutsideWorkspace(Exception):
    """El path resuelto cae fuera del allow-set de roots (traversal / symlink-escape / fuera)."""


# ── Módulo de confinamiento homologado (mecanismo genérico, cero política) ──────────────

# Espejo de `containsPathTraversal` (path.ts:133): detecta un segmento `..` en el relativo.
_TRAVERSAL_RE = re.compile(r"(?:^|[\\/])\.\.(?:[\\/]|$)")


def contains_path_traversal(path: str) -> bool:
    return bool(_TRAVERSAL_RE.search(path))


def expand_path(path: str, base_dir: str) -> str:
    """
    Homólogo de `expandPath` (path.ts:32): expande `~`, resuelve relativo contra `base_dir`,
    y colapsa `.`/`..` lexicográficamente. NO resuelve symlinks (eso lo hace realpath aparte).
    """
    if "\0" in path or "\0" in base_dir:
        raise ValueError("Path contains null bytes")
    trimmed = path.strip()
    if not trimmed:
        return os.path.normpath(base_dir)
    expanded = os.path.expanduser(trimmed)
    if not os.path.isabs(expanded):
        expanded = os.path.join(base_dir, expanded)
    return os.path.normpath(expanded)


def paths_for_permission_check(path: str, base_dir: str) -> list[str]:
    """
    Homólogo de `getPathsForPermissionCheck` (fsOperations.ts:288): devuelve el path original
    expandido y su forma con symlinks resueltos, para no evadir el confinamiento por symlink.
    `realpath` resuelve la cadena completa; para un archivo nuevo resuelve el prefijo existente.
    """
    expanded = expand_path(path, base_dir)
    resolved = os.path.realpath(expanded)
    if resolved == expanded:
        return [expanded]
    return [expanded, resolved]


def path_in_working_path(path: str, working_path: str, base_dir: str) -> bool:
    """Homólogo de `pathInWorkingPath` (filesystem.ts:709): `path` cae dentro de `working_path`."""
    abs_path = expand_path(path, base_dir)
    abs_working = expand_path(working_path, base_dir)
    relative = os.path.relpath(abs_path, abs_working)
    if relative == ".":
        return True
    if contains_path_traversal(relative):
        return False
    return not os.path.isabs(relative)


def path_in_allowed_working_path(path: str, roots: list[str], base_dir: str) -> bool:
    """
    Homólogo de `pathInAllowedWorkingPath` (filesystem.ts:683): cada forma del path (original +
    symlink resuelto) debe caer dentro de ALGÚN root (resuelto igual, para simetría de comparación).
    """
    checks = paths_for_permission_check(path, base_dir)
    working_paths: list[str] = []
    for root in roots:
        expanded = expand_path(root, base_dir)
        working_paths.append(expanded)
        resolved = os.path.realpath(expanded)
        if resolved != expanded:
            working_paths.append(resolved)
    return all(
        any(path_in_working_path(check, wp, base_dir) for wp in working_paths)
        for check in checks
    )


# ── Costura fs (clase concreta del runtime, se cuelga en ctx.fs) ────────────────────────


class ConfinedFilesystem:
    """
    Traduce token→host path (vía `StorageContract`, política del consumidor) y confina el
    resultado contra `roots` (mecanismo homologado). Levanta `PathOutsideWorkspace` fuera.

    Default seguro: sin roots explícitos, confina a `cwd()` — nunca ilimitado (§3.5 del diseño).
    Los tokens relativos se expanden contra el primer root (cwd ≡ working-dir del canónico).

    Lectura vs escritura (homologado del canónico, que separa el check de escritura del de
    lectura): `roots` es el allow-set de LECTURA; `write_roots` el de ESCRITURA (subconjunto).
    `resolve(for_write=True)` confina contra `write_roots`; `for_write=False` contra `roots`.
    Omitir `write_roots` iguala escritura a lectura (comportamiento previo, backward-compatible).
    """

    def __init__(
        self,
        roots: list[Path] | None = None,
        storage: "StorageContract | None" = None,
        *,
        write_roots: list[Path] | None = None,
    ) -> None:
        self._roots = [Path(r) for r in roots] if roots else [Path.cwd()]
        self._write_roots = (
            [Path(r) for r in write_roots] if write_roots is not None else self._roots
        )
        self._storage = storage

    @property
    def _base_dir(self) -> str:
        return str(self._roots[0])

    @property
    def write_root(self) -> Path:
        """Root de escritura primario del workspace. Para tools que ubican un destino
        nuevo por nombre relativo (p.ej. `clone_repository`), no un path del modelo."""
        return self._write_roots[0]

    def resolve(self, token: str, *, for_write: bool) -> Path:
        host = self._storage.real_path(token) if self._storage is not None else Path(token)
        allow = self._write_roots if for_write else self._roots
        # `FIND-PLAN-FILE-1` — exención del plan-file de la sesión. El canónico la aplica en
        # este mismo punto (la capa de permisos de fs) y por partida doble:
        # `checkEditableInternalPath` (`filesystem.ts:1488`, *«Plan files for current session
        # are allowed for writing»*) y su gemelo de lectura (`:1645`). Sin ella, el plan-file
        # —que por definición vive FUERA del workspace— es inescribible, y la única
        # instrucción operativa de plan mode (`capabilities/plan/provider.py:40-42`, «create
        # your plan at {token}») es imposible de cumplir.
        #
        # Va DENTRO de `resolve` y no en un helper que las tools llamen, por el mismo criterio
        # que el cap de `FIND-DEFER-2`: un punto que ningún consumidor pueda esquivar. El
        # predicado es el homologado (`is_session_plan_file`), no una comparación ad-hoc, y se
        # aplica al TOKEN —que es lo que el modelo escribe— no al path host, que es privado
        # del consumidor. Import local: `plan_file` es hoja (sólo `TYPE_CHECKING`), pero
        # importarlo arriba ataría `tools/` a `capabilities/` en tiempo de carga.
        #
        # El guard de traversal NO es adorno: sin él `/plans/../../etc/passwd.md` satisface el
        # predicado (prefijo y sufijo correctos) y saldría del workspace por la puerta que
        # acabamos de abrir. A se defiende igual y lo dice en el propio comentario del
        # canónico: *«SECURITY: Normalize to prevent path traversal bypasses via .. segments»*
        # (`filesystem.ts:249`).
        from ..capabilities.plan.plan_file import is_session_plan_file

        if is_session_plan_file(token) and not contains_path_traversal(token):
            return Path(expand_path(str(host), self._base_dir))
        if not path_in_allowed_working_path(str(host), [str(r) for r in allow], self._base_dir):
            raise PathOutsideWorkspace(
                f"path {token!r} resolves outside the allowed "
                f"{'write ' if for_write else ''}workspace"
            )
        # `FIND-C6-1`: se devuelve el path **expandido**, que es el que se acaba de
        # autorizar — no el token crudo. Antes se validaba lo expandido y se devolvía
        # `Path(host)` sin expandir, así que un token RELATIVO pasaba el gate (expandido
        # contra `roots[0]`) y la tool lo abría contra el **cwd del proceso**: el archivo
        # caía fuera del workspace con `is_error=False`. Medido, no razonado: `write_file`
        # con `path="notas.txt"` escribía en `cwd()/notas.txt`. El confinamiento sólo vale
        # si lo autorizado y lo usado son el MISMO path.
        # Lexical a propósito (`expand_path` no resuelve symlinks): la forma con symlinks
        # resueltos es para el CHEQUEO (`paths_for_permission_check`), no para la E/S —
        # mismo reparto que el canónico. Para un token absoluto esto es un no-op.
        return Path(expand_path(str(host), self._base_dir))


__all__ = [
    "ConfinedFilesystem",
    "PathOutsideWorkspace",
    "contains_path_traversal",
    "expand_path",
    "path_in_allowed_working_path",
    "path_in_working_path",
    "paths_for_permission_check",
]
