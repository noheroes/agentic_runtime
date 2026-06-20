"""E2E de la memoria en el loop (scripted caller, siempre corre).

Demuestra el ciclo completo activación → recall → guardado → reinicio sin LLM real.
Lo único guionizado es la DECISIÓN del modelo (qué tool llamar); el fichero de memoria
y su persistencia en disco son reales:

  (a) activación — el caller recibe la sección de memoria en `system_sections`.
  (b) recall     — una memoria pre-sembrada relevante al prompt se inyecta como
                   `<system-reminder>` (role:"user").
  (c) guardado   — el modelo llama `write_file` (permitido vía initial_allowed_tools)
                   para crear `<dir>/feedback_estilo.md` y actualizar `MEMORY.md`.
  (d) reinicio   — un MemoryProvider nuevo sobre el mismo dir encuentra el fichero y el
                   índice (la memoria vive en disco, sobrevive al proceso).
"""
from __future__ import annotations

from pathlib import Path

from agentic_runtime.capabilities.memory import (
    ENTRYPOINT,
    FilesystemMemoryStore,
    MemoryProvider,
)
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.factory import (
    CapabilitiesConfig,
    RuntimeConfig,
    StorageConfig,
    create_runtime,
)

_PROMPT = "necesito arreglar el login de sesión otra vez"

_SEEDED_MEMORY = (
    "---\n"
    "name: auth-flow\n"
    "description: cómo funciona el login y los tokens de sesión\n"
    "metadata:\n  type: project\n"
    "---\n\nEl login usa tokens rotatorios.\n"
)
_SEEDED_INDEX = "- [auth-flow](auth.md) — login y tokens de sesión\n"

_FEEDBACK_MEMORY = (
    "---\n"
    "name: estilo-commits\n"
    "description: el usuario quiere commits en español sin referencias externas\n"
    "metadata:\n  type: feedback\n"
    "---\n\n**Why:** lo pidió explícitamente.\n"
)
_UPDATED_INDEX = _SEEDED_INDEX + "- [estilo-commits](feedback_estilo.md) — commits en español\n"


class _MemoryCaller:
    """Conduce el loop: turno1 guarda el fichero de memoria, turno2 actualiza el índice,
    turno3 termina. Captura `system_sections` (activación) y los recordatorios de recall."""

    def __init__(self, feedback_path: Path, index_path: Path) -> None:
        self._feedback_path = feedback_path
        self._index_path = index_path
        self.turns = 0
        self.tools_seen: list[list[str]] = []
        self.system_sections_seen: list[list[str] | None] = []
        self.recall_seen: list[str] = []

    async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
        self.turns += 1
        n = self.turns
        self.tools_seen.append([t["name"] for t in tools])
        self.system_sections_seen.append(system_sections)
        for m in messages:
            content = m.get("content") or ""
            if m.get("role") == "user" and "<system-reminder>" in content:
                self.recall_seen.append(content)

        async def gen():
            if n == 1:
                yield ToolCallEvent(
                    tool_name="write_file",
                    tool_input={"path": str(self._feedback_path), "content": _FEEDBACK_MEMORY},
                    call_id="w1",
                )
                yield DoneEvent(stop_reason="tool_calls")
            elif n == 2:
                yield ToolCallEvent(
                    tool_name="write_file",
                    tool_input={"path": str(self._index_path), "content": _UPDATED_INDEX},
                    call_id="w2",
                )
                yield DoneEvent(stop_reason="tool_calls")
            else:
                yield TokenEvent(content="memoria actualizada")
                yield DoneEvent(stop_reason="stop")

        return gen()


async def test_memory_activation_recall_save_and_restart(tmp_path):
    memory_root = tmp_path / "memory"
    # scope = <user_id>/<agente>; el principal usa el slot estable 'main' bajo su usuario.
    main_dir = memory_root / "u1" / "main"
    main_dir.mkdir(parents=True)
    (main_dir / "auth.md").write_text(_SEEDED_MEMORY, encoding="utf-8")
    (main_dir / ENTRYPOINT).write_text(_SEEDED_INDEX, encoding="utf-8")

    feedback_path = main_dir / "feedback_estilo.md"
    index_path = main_dir / ENTRYPOINT
    caller = _MemoryCaller(feedback_path, index_path)

    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        capabilities=CapabilitiesConfig(memory_root=memory_root),
        # El integrador permite write_file para que el modelo pueda guardar memorias.
        initial_allowed_tools=["write_file"],
    ))
    await runtime.startup()
    try:
        task_id = await runtime.dispatch(RuntimeTask(prompt=_PROMPT, description="memory-e2e", owner_id="u1"))
        rec = runtime._task_registry.get(task_id)
        await rec.asyncio_task
    finally:
        await runtime.shutdown()

    # (a) activación: la sección de memoria llega al caller en el primer turno.
    assert caller.system_sections_seen[0] is not None
    activation = "\n".join(caller.system_sections_seen[0])
    assert "Memoria persistente" in activation
    assert "auth-flow" in activation  # el índice pre-sembrado va inyectado

    # (b) recall: la memoria relevante se inyecta como <system-reminder> (role:"user").
    assert caller.recall_seen, "no se inyectó recall"
    assert any("auth-flow" in r for r in caller.recall_seen)

    # write_file quedó anunciado (seed de permisos), no oculto.
    assert "write_file" in caller.tools_seen[0]

    # (c) guardado: ficheros REALES en disco escritos por el modelo (guionizado).
    assert feedback_path.exists()
    assert "estilo-commits" in feedback_path.read_text(encoding="utf-8")
    assert "feedback_estilo.md" in index_path.read_text(encoding="utf-8")

    # (d) reinicio: un provider/store nuevo sobre el mismo dir encuentra lo guardado.
    fresh = MemoryProvider(FilesystemMemoryStore(memory_root))
    await fresh.startup()
    headers = {h.name for h in FilesystemMemoryStore(memory_root).scan("u1/main")}
    assert {"auth-flow", "estilo-commits"} <= headers

    fresh_ctx = ToolUseContext(session_id="s2", user_id="u1", agent_id="otro_uuid")  # main: scope estable
    section = fresh.system_prompt_section(fresh_ctx)
    assert section is not None and "feedback_estilo.md" in section  # índice actualizado visible
