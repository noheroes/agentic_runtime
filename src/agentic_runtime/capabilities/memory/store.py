from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Índice de la memoria — va inyectado en el system prompt; se excluye del recall y
# del scan de cabeceras (espejo de `paths.ts`/`memoryScan.ts` del canónico).
ENTRYPOINT = "MEMORY.md"

_DELIM = "---"


class MemoryHeader(BaseModel):
    """Cabecera de una memoria (un `*.md` salvo `MEMORY.md`).

    No carga el cuerpo: el recall opera sobre `name`/`description` (lo que decide
    relevancia) y el modelo lee el fichero completo con `Read` si lo necesita.
    """

    name: str
    description: str = ""
    type: str = ""
    path: str  # ruta absoluta del fichero (marcador estable para dedup)
    mtime: float = 0.0  # desempate por recencia en el ranking


@runtime_checkable
class MemoryStore(Protocol):
    """Puerto de la memoria: dónde vive y cómo se lee su índice/cabeceras.

    El default `FilesystemMemoryStore` la pone en disco (sobrevive a reinicio), como
    `base_dir` de skills. Inyectable por quien integra el runtime.
    """

    def memory_dir(self, agent_id: str | None) -> Path: ...
    def ensure_dir(self, agent_id: str | None) -> Path: ...
    def read_index(self, agent_id: str | None) -> str: ...
    def scan(self, agent_id: str | None) -> list[MemoryHeader]: ...


def _parse_frontmatter(text: str) -> dict:
    """Parse mínimo y TOLERANTE del frontmatter YAML (nunca lanza).

    No reutiliza `SkillFrontmatter` — su schema es distinto (la memoria usa
    `metadata.type`, no `allowed-tools`). Solo se comparte el enfoque tolerante.
    """
    stripped = text.lstrip("﻿")  # tolera BOM
    if not stripped.startswith(_DELIM):
        return {}
    rest = stripped[len(_DELIM):]
    end = rest.find(f"\n{_DELIM}")
    if end == -1:
        return {}
    try:
        loaded = yaml.safe_load(rest[:end])
    except yaml.YAMLError as exc:
        logger.warning("memory: frontmatter YAML inválido — ignorado: %s", exc)
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _parse_header(path: Path) -> MemoryHeader | None:
    """Construye la cabecera de un fichero de memoria — aislamiento por ítem.

    Un fichero ilegible o sin frontmatter degrada a defaults (identidad ← nombre del
    fichero), nunca tumba el scan del resto."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("memory: no se pudo leer %s: %s", path, exc)
        return None
    front = _parse_frontmatter(text)
    meta = front.get("metadata")
    mtype = meta.get("type") if isinstance(meta, dict) else ""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return MemoryHeader(
        name=str(front.get("name") or path.stem),
        description=str(front.get("description") or ""),
        type=str(mtype or ""),
        path=str(path),
        mtime=mtime,
    )


class FilesystemMemoryStore:
    """Memoria en disco, scopeada por agente: `<root>/<agent_id|'main'>/`.

    El modelo escribe los ficheros con `Write` (guardado canónico, sin tool propia)
    y actualiza el índice `MEMORY.md`; este store solo lee índice + cabeceras.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _scope(self, agent_id: str | None) -> str:
        return agent_id or "main"

    def memory_dir(self, agent_id: str | None) -> Path:
        return self._root / self._scope(agent_id)

    def ensure_dir(self, agent_id: str | None) -> Path:
        directory = self.memory_dir(agent_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def read_index(self, agent_id: str | None) -> str:
        index = self.memory_dir(agent_id) / ENTRYPOINT
        try:
            return index.read_text(encoding="utf-8")
        except OSError:
            return ""

    def scan(self, agent_id: str | None) -> list[MemoryHeader]:
        directory = self.memory_dir(agent_id)
        if not directory.is_dir():
            return []
        headers: list[MemoryHeader] = []
        for path in sorted(directory.glob("*.md")):
            if path.name == ENTRYPOINT:
                continue  # el índice ya va en el system prompt
            header = _parse_header(path)
            if header is not None:
                headers.append(header)
        return headers


__all__ = ["ENTRYPOINT", "FilesystemMemoryStore", "MemoryHeader", "MemoryStore"]
