from __future__ import annotations

import re

from .store import MemoryHeader

_WORD = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    # Tokens de >2 caracteres en minúscula — descarta conectores cortos sin valor de
    # relevancia (de, la, el, ...). Determinista: misma entrada → mismo conjunto.
    return {t.lower() for t in _WORD.findall(text) if len(t) > 2}


def rank_memories(
    headers: list[MemoryHeader],
    query: str,
    limit: int = 5,
) -> list[MemoryHeader]:
    """Selecciona ≤`limit` memorias relevantes a `query` de forma DETERMINISTA.

    Solapamiento de keywords sobre `name`+`description` (lo que el modelo guarda como
    metadatos de relevancia); desempate por recencia (`mtime` desc). Sin solapamiento
    → no se incluye (query irrelevante → `[]`). Mismo estado + misma query → mismo
    resultado. El ranker LLM del canónico queda como opinión inyectable futura.
    """
    tokens = _tokens(query)
    if not tokens:
        return []
    scored: list[tuple[int, float, MemoryHeader]] = []
    for header in headers:
        overlap = len(tokens & _tokens(f"{header.name} {header.description}"))
        if overlap > 0:
            scored.append((overlap, header.mtime, header))
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    return [header for _, _, header in scored[:limit]]


__all__ = ["rank_memories"]
