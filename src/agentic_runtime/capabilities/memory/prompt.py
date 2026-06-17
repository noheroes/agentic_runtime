from __future__ import annotations

from .store import ENTRYPOINT


def build_memory_activation(memory_dir: str, index_content: str) -> str:
    """Bloque de activación de la memoria para el system prompt (model-facing, español).

    Espejo recortado de `memdir.ts::buildMemoryPrompt`: instrucciones permanentes +
    taxonomía tipada + qué NO guardar + cómo guardar (2 pasos, sin tool propia) +
    cuándo acceder + el índice `MEMORY.md` inyectado. Texto estable entre turnos
    (cache-friendly): solo varía con el índice.
    """
    index = index_content.strip()
    index_block = index if index else "(índice vacío — aún no hay memorias guardadas)"

    return (
        f"# Memoria persistente\n\n"
        f"Dispones de una memoria persistente basada en ficheros en `{memory_dir}`. "
        f"Sobrevive entre sesiones. No hay una tool de memoria: guardas escribiendo "
        f"ficheros con `write_file` y consultas con `read_file`.\n\n"
        f"## Cuándo usarla\n"
        f"Recupera memoria cuando el contexto actual encaje con algo que recuerdes "
        f"haber guardado (mira el índice de abajo y los recordatorios que recibas). "
        f"Guarda cuando aparezca un hecho duradero que no sea derivable del propio "
        f"repositorio ni del historial de git.\n\n"
        f"## Qué guardar (un hecho por fichero)\n"
        f"- `user`: quién es el usuario (rol, experiencia, preferencias).\n"
        f"- `feedback`: cómo debes trabajar (correcciones o enfoques confirmados); "
        f"incluye el porqué.\n"
        f"- `project`: trabajo en curso, objetivos o restricciones no derivables del "
        f"código; convierte fechas relativas en absolutas.\n"
        f"- `reference`: punteros a recursos externos (URLs, tickets, paneles).\n\n"
        f"## Qué NO guardar\n"
        f"Lo que el repositorio ya registra (estructura del código, fixes pasados, "
        f"historial de git) o lo que solo importa en esta conversación.\n\n"
        f"## Cómo guardar (2 pasos)\n"
        f"1. Escribe el hecho en `{memory_dir}/<slug>.md` con frontmatter "
        f"`name`/`description`/`metadata.type`.\n"
        f"2. Añade un puntero de una línea en `{memory_dir}/{ENTRYPOINT}` (el índice).\n\n"
        f"Antes de guardar, revisa si ya existe un fichero que cubra el hecho y "
        f"actualízalo en vez de duplicar.\n\n"
        f"## Índice ({ENTRYPOINT})\n"
        f"{index_block}"
    )


__all__ = ["build_memory_activation"]
