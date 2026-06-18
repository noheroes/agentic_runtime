"""MemoryProvider: activación (system prompt), recall por turno y scoping por agente."""
from pathlib import Path

from agentic_runtime.capabilities.memory import (
    ENTRYPOINT,
    FilesystemMemoryStore,
    MemoryProvider,
)
from agentic_runtime.context.tool_use import ToolUseContext


def _write_memory(directory: Path, slug: str, name: str, description: str, mtype: str = "project") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.md").write_text(
        f"---\nname: {name}\ndescription: {description}\nmetadata:\n  type: {mtype}\n---\n\ncuerpo.\n",
        encoding="utf-8",
    )


def _ctx(agent_id: str | None = None, user_text: str = "", is_subagent: bool = False) -> ToolUseContext:
    ctx = ToolUseContext(session_id="s1", agent_id=agent_id, is_subagent=is_subagent)
    if user_text:
        ctx.messages.append({"role": "user", "content": user_text})
    return ctx


def _provider(tmp_path: Path) -> MemoryProvider:
    return MemoryProvider(FilesystemMemoryStore(tmp_path))


# ---------------------------------------------------------------------------
# Activación (system_prompt_section)
# ---------------------------------------------------------------------------

def test_activation_contains_instructions_and_index(tmp_path: Path):
    main_dir = tmp_path / "main"
    main_dir.mkdir(parents=True)
    (main_dir / ENTRYPOINT).write_text("- [auth](auth.md) — login y tokens\n", encoding="utf-8")

    section = _provider(tmp_path).system_prompt_section(_ctx())
    assert section is not None
    assert "Memoria persistente" in section
    assert "write_file" in section  # guardado canónico, sin tool propia
    assert "- [auth](auth.md) — login y tokens" in section  # índice inyectado


def test_activation_empty_dir_says_empty(tmp_path: Path):
    section = _provider(tmp_path).system_prompt_section(_ctx())
    assert section is not None
    assert "índice vacío" in section


def test_activation_ensures_dir_exists(tmp_path: Path):
    _provider(tmp_path).system_prompt_section(_ctx())
    assert (tmp_path / "main").is_dir()  # destino de write_file existe


# ---------------------------------------------------------------------------
# Recall (active_context)
# ---------------------------------------------------------------------------

def test_recall_relevant_memory(tmp_path: Path):
    _write_memory(tmp_path / "main", "auth", "auth-flow", "login y tokens de sesión")
    msgs = _provider(tmp_path).active_context(_ctx(user_text="problema con el login de sesión"))
    assert len(msgs) == 1
    assert msgs[0]["role"] == "system"
    assert "auth-flow" in msgs[0]["content"]


def test_recall_irrelevant_query_empty(tmp_path: Path):
    _write_memory(tmp_path / "main", "auth", "auth-flow", "login y tokens")
    msgs = _provider(tmp_path).active_context(_ctx(user_text="receta de tarta de manzana"))
    assert msgs == []


def test_recall_excludes_index(tmp_path: Path):
    main_dir = tmp_path / "main"
    main_dir.mkdir(parents=True)
    (main_dir / ENTRYPOINT).write_text(
        "---\nname: MEMORY\ndescription: login token sesión\n---\nindex\n", encoding="utf-8"
    )
    msgs = _provider(tmp_path).active_context(_ctx(user_text="login token sesión"))
    assert msgs == []  # MEMORY.md nunca entra al recall


def test_recall_ignores_system_reminder_when_picking_query(tmp_path: Path):
    _write_memory(tmp_path / "main", "auth", "auth-flow", "login y tokens de sesión")
    ctx = _ctx(user_text="problema con el login de sesión")
    # El loop pudo inyectar un recordatorio como user; no debe usarse como query.
    ctx.messages.append({"role": "user", "content": "<system-reminder>\nrecordatorio\n</system-reminder>"})
    msgs = _provider(tmp_path).active_context(ctx)
    assert len(msgs) == 1 and "auth-flow" in msgs[0]["content"]


# ---------------------------------------------------------------------------
# Scoping por agente
# ---------------------------------------------------------------------------

def test_scoping_subagent_a_does_not_see_b(tmp_path: Path):
    # El aislamiento por agent_id aplica a SUBAGENTES (is_subagent=True); el agente
    # principal usa el scope estable 'main'.
    _write_memory(tmp_path / "agent_a", "x", "secreto-a", "login token de A")
    provider = _provider(tmp_path)
    seen_by_b = provider.active_context(_ctx(agent_id="agent_b", user_text="login token", is_subagent=True))
    seen_by_a = provider.active_context(_ctx(agent_id="agent_a", user_text="login token", is_subagent=True))
    assert seen_by_b == []
    assert [m["content"] for m in seen_by_a if "secreto-a" in m["content"]]


def test_main_agent_uses_stable_scope_regardless_of_agent_id(tmp_path: Path):
    # Dos despachos del agente principal con agent_id (uuid) distinto comparten 'main'.
    _write_memory(tmp_path / "main", "auth", "auth-flow", "login y tokens de sesión")
    provider = _provider(tmp_path)
    run1 = provider.active_context(_ctx(agent_id="agent_uuid_1", user_text="login de sesión"))
    run2 = provider.active_context(_ctx(agent_id="agent_uuid_2", user_text="login de sesión"))
    assert run1 and run1 == run2  # misma memoria, scope estable


# ---------------------------------------------------------------------------
# Compactación + tools/catalog vacíos
# ---------------------------------------------------------------------------

def test_compact_context_preserves_relevant(tmp_path: Path):
    _write_memory(tmp_path / "main", "auth", "auth-flow", "login y tokens de sesión")
    provider = _provider(tmp_path)
    ctx = _ctx(user_text="login de sesión")
    assert provider.compact_context(ctx) == provider.active_context(ctx)
    assert provider.compact_context(ctx)  # no vacío


def test_provider_has_no_tools_or_catalog(tmp_path: Path):
    provider = _provider(tmp_path)
    assert provider.tools(_ctx()) == []
    assert provider.catalog(_ctx()) == []


# ---------------------------------------------------------------------------
# Acoplamiento: el runtime/loop NO importa capabilities.memory
# ---------------------------------------------------------------------------

def test_loop_does_not_import_memory():
    loop_src = Path("src/agentic_runtime/loop/agent_loop.py").read_text(encoding="utf-8")
    assert "capabilities.memory" not in loop_src
    assert "import memory" not in loop_src
