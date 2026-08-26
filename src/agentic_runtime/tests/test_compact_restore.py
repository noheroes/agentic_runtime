"""Homologación K6·tramo-4 — restauración post-compactación y depósito de ficheros leídos.

Contrapartes canónicas leídas ÍNTEGRAS:
- `services/compact/compact.ts` (1706) — constantes `POST_COMPACT_*` (122-130), el
  volcado del estado de ficheros y su limpieza (517-521), el ensamblado de adjuntos
  (532-585), los hooks `PostCompact` (719-729) y el `userDisplayMessage` combinado
  (731-736), `truePostCompactTokenCount` contando adjuntos y hooks (637-642),
  `createPostCompactFileAttachments` (1415-1464), `collectReadToolFilePaths`
  (1610-1655), `truncateToTokens` (1666-1672) y
  `shouldExcludeFromPostCompactRestore` (1674-1705).
- `services/compact/postCompactCleanup.ts` (77) — reseteos de caché de módulo.

Divergencias DECLARADAS (`D-21`/`D-22`):
- **El depósito NO existía en B y se construye** (`D-22`): `context/file_state.py`,
  asentado en `app_state.native`. Diverge de A en dos cosas dichas: guarda sólo
  `ruta → marca de tiempo` (el contenido de A sirve a la guarda de relectura-antes-de-
  editar, que es del censo de tools y no de K6), y vive lo que vive el turno, mismo
  alcance que `AutoCompactTracking` (`D-44`), mientras que A lo tiene en sesión.
- La rama `FILE_UNCHANGED_STUB` de `collectReadToolFilePaths` (1610-1626) no se porta:
  B no tiene deduplicador de lecturas repetidas, así que no hay stub que saltar.
- La lista de exclusión de A (fichero de plan y los `claude.md`) es su catálogo de
  producto y no entra al núcleo: el núcleo publica la costura y el integrador pone el
  predicado en `app_state.native`, igual que ya hace con los validadores de edición.
- El presupuesto acumulado se mide con `rough_token_count_for_message` sobre el
  mensaje, no con `roughTokenCountEstimation(jsonStringify(result))` (1457): mide el
  mismo contenido sin el sobre de serialización de A.
- `runPostCompactCleanup` no tiene homólogo: sus reseteos son de cachés de módulo de A.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from agentic_runtime.context.compact import (
    collect_read_tool_file_paths,
    compact_conversation,
    create_post_compact_file_attachments,
    select_files_to_restore,
)
from agentic_runtime.context.compact.restore import (
    FILE_TRUNCATION_MARKER,
    POST_COMPACT_ATTACHMENT_KEY,
    POST_COMPACT_RESTORE_EXCLUSION_KEY,
)
from agentic_runtime.context.file_state import (
    READ_FILE_STATE_KEY,
    ReadFileEntry,
    read_file_state,
)
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.context.window import resolve_context_window_policy
from agentic_runtime.hooks.protocol import HookDecision, HookEvent
from agentic_runtime.tools.fs_env import ConfinedFilesystem
from agentic_runtime.tools.native.read_file import ReadFileTool

from .test_compact_engine import LONG_SUMMARY, FakeCaller, _history

LOCAL_BUDGET = resolve_context_window_policy("local").budget(32_768, 4_096)


def _ctx(tmp_path: Any) -> ToolUseContext:
    return ToolUseContext(
        session_id="s",
        cwd=str(tmp_path),
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
    )


def _read_call(path: str, *, tool_name: str = "read_file", raw: bool = True) -> dict[str, Any]:
    arguments = f'{{"path": "{path}"}}' if raw else {"path": path}
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"id": "c1", "function": {"name": tool_name, "arguments": arguments}}],
    }


# --- A · El depósito (lo que no está SE CREA, `D-22`) -----------------------


async def test_reading_a_file_deposits_its_resolved_path_and_when(tmp_path):
    """A lleva el estado en `context.readFileState` y lo vuelca antes de limpiarlo
    (compact.ts:517-521). En B no existía: sin depósito no hay recencia que ordenar,
    y la restauración se quedaría adivinando qué ficheros importaban."""
    target = tmp_path / "modulo.py"
    target.write_text("uno\ndos\n")
    ctx = _ctx(tmp_path)

    result = await ReadFileTool().execute({"path": "modulo.py"}, ctx)

    assert not result.is_error
    entries = read_file_state(ctx.app_state)
    assert [entry.path for entry in entries] == [str(target)]
    assert entries[0].timestamp > 0


async def test_a_failed_read_deposits_nothing(tmp_path):
    ctx = _ctx(tmp_path)
    result = await ReadFileTool().execute({"path": "no-existe.py"}, ctx)
    assert result.is_error
    assert read_file_state(ctx.app_state) == []


# --- B · Selección (par de compact.ts:1415-1432 y 1610-1655) ----------------


def test_the_visible_paths_come_from_the_assistants_read_calls_only():
    messages = [
        _read_call("/w/a.py"),
        _read_call("/w/b.py", raw=False),
        _read_call("/w/c.py", tool_name="file_edit"),
        {"role": "user", "content": "texto"},
        {"role": "assistant", "content": "sin tool_calls"},
    ]
    assert collect_read_tool_file_paths(messages) == {"/w/a.py", "/w/b.py"}


def test_selection_is_by_recency_capped_by_count_and_skips_what_is_already_visible():
    """A ordena `b.timestamp - a.timestamp` y corta con `slice(0, maxFiles)`
    (1431-1432); lo que ya se ve en la cola conservada se salta porque reinyectarlo
    es gasto puro (1404-1407)."""
    entries = [
        ReadFileEntry("/w/viejo.py", 1.0),
        ReadFileEntry("/w/medio.py", 2.0),
        ReadFileEntry("/w/nuevo.py", 3.0),
    ]
    assert select_files_to_restore(entries, max_files=2) == ["/w/nuevo.py", "/w/medio.py"]
    assert select_files_to_restore(
        entries, max_files=2, already_visible={"/w/nuevo.py"}
    ) == ["/w/medio.py", "/w/viejo.py"]
    assert select_files_to_restore(entries, max_files=0) == []


def test_the_exclusion_predicate_is_the_integrators_and_a_broken_one_does_not_decide():
    """La lista de A (plan y `claude.md`) es su catálogo de producto. El núcleo pone
    la costura; un predicado que revienta no puede excluir por accidente ni tumbar la
    compactación entera."""
    entries = [ReadFileEntry("/w/plan.md", 2.0), ReadFileEntry("/w/codigo.py", 1.0)]

    def excluir_planes(path: str) -> bool:
        return path.endswith("plan.md")

    def roto(path: str) -> bool:
        raise RuntimeError("predicado del integrador roto")

    assert select_files_to_restore(
        entries, max_files=5, exclusions=[excluir_planes]
    ) == ["/w/codigo.py"]
    assert select_files_to_restore(entries, max_files=5, exclusions=[roto]) == [
        "/w/plan.md",
        "/w/codigo.py",
    ]


# --- C · Adjuntos (par de compact.ts:1434-1464) -----------------------------


async def test_restoration_rereads_from_disk_instead_of_replaying_what_was_read(tmp_path):
    """A re-lee con `FileReadTool` (1436-1447), no reinyecta el contenido cacheado:
    entre la lectura y la compactación el fichero ha podido cambiar, y restaurar la
    versión vieja le miente al modelo sobre el disco."""
    target = tmp_path / "modulo.py"
    target.write_text("version vieja\n")
    ctx = _ctx(tmp_path)
    await ReadFileTool().execute({"path": "modulo.py"}, ctx)
    target.write_text("version nueva\n")

    attachments = await create_post_compact_file_attachments(ctx, LOCAL_BUDGET)

    assert len(attachments) == 1
    assert "version nueva" in attachments[0]["content"]
    assert "version vieja" not in attachments[0]["content"]
    assert attachments[0][POST_COMPACT_ATTACHMENT_KEY] == {"path": str(target)}
    assert attachments[0]["role"] == "user"


async def test_each_restored_file_is_truncated_to_its_share(tmp_path):
    target = tmp_path / "grande.py"
    target.write_text("linea\n" * 4_000)
    ctx = _ctx(tmp_path)
    await ReadFileTool().execute({"path": "grande.py"}, ctx)

    attachments = await create_post_compact_file_attachments(ctx, LOCAL_BUDGET)

    assert FILE_TRUNCATION_MARKER in attachments[0]["content"]
    assert len(attachments[0]["content"]) < len(target.read_text())


async def test_the_cumulative_budget_drops_what_does_not_fit_and_keeps_looking(tmp_path):
    """A filtra, no corta (1453-1463): un fichero enorme que no cabe no debe llevarse
    por delante a los pequeños que vienen detrás y sí caben."""
    (tmp_path / "grande.py").write_text("x" * 20_000)
    (tmp_path / "pequeno.py").write_text("y" * 40)
    ctx = _ctx(tmp_path)
    await ReadFileTool().execute({"path": "pequeno.py"}, ctx)
    await ReadFileTool().execute({"path": "grande.py"}, ctx)

    budget = replace(
        LOCAL_BUDGET,
        post_compact_max_files_to_restore=2,
        post_compact_token_budget=200,
        post_compact_max_tokens_per_file=100_000,
    )
    attachments = await create_post_compact_file_attachments(ctx, budget)

    restored = [a[POST_COMPACT_ATTACHMENT_KEY]["path"] for a in attachments]
    assert restored == [str(tmp_path / "pequeno.py")]


async def test_what_the_preserved_tail_already_shows_is_not_reinjected(tmp_path):
    (tmp_path / "visto.py").write_text("contenido\n")
    ctx = _ctx(tmp_path)
    await ReadFileTool().execute({"path": "visto.py"}, ctx)

    attachments = await create_post_compact_file_attachments(
        ctx, LOCAL_BUDGET, messages_to_keep=[_read_call("visto.py")]
    )

    assert attachments == []


async def test_the_deposit_is_emptied_and_only_what_got_restored_returns_to_it(tmp_path):
    """A limpia `readFileState` antes de montar los adjuntos (520-521); las relecturas
    vuelven a poblarlo, que es lo correcto: esos ficheros están en contexto otra vez."""
    (tmp_path / "restaurado.py").write_text("a\n")
    (tmp_path / "excluido.py").write_text("b\n")
    ctx = _ctx(tmp_path)
    await ReadFileTool().execute({"path": "excluido.py"}, ctx)
    await ReadFileTool().execute({"path": "restaurado.py"}, ctx)
    ctx.app_state.native[POST_COMPACT_RESTORE_EXCLUSION_KEY] = [
        lambda path: path.endswith("excluido.py")
    ]

    await create_post_compact_file_attachments(ctx, LOCAL_BUDGET)

    assert [entry.path for entry in read_file_state(ctx.app_state)] == [
        str(tmp_path / "restaurado.py")
    ]


async def test_without_a_deposit_there_is_nothing_to_restore(tmp_path):
    ctx = _ctx(tmp_path)
    assert await create_post_compact_file_attachments(ctx, LOCAL_BUDGET) == []
    assert ctx.app_state.native[READ_FILE_STATE_KEY] == {}


# --- D · El motor rinde la restauración (par de compact.ts:532-585, 637-642) -


async def test_the_engine_restores_files_and_counts_them_in_the_resulting_size(tmp_path):
    """`truePostCompactTokenCount` mide el contexto RESULTANTE (626-642). Sin contar
    los adjuntos, el freno de recompactación mide de menos y la vuelta siguiente
    vuelve a compactar creyendo que hay sitio."""
    (tmp_path / "modulo.py").write_text("contenido restaurado\n")
    ctx = _ctx(tmp_path)
    await ReadFileTool().execute({"path": "modulo.py"}, ctx)

    result = await compact_conversation(
        _history(), FakeCaller(LONG_SUMMARY), LOCAL_BUDGET, ctx=ctx
    )

    assert len(result.attachments) == 1
    sin_adjuntos = await compact_conversation(
        _history(), FakeCaller(LONG_SUMMARY), LOCAL_BUDGET
    )
    assert result.true_post_compact_token_count > sin_adjuntos.true_post_compact_token_count
    mensajes = [m.get("content") for m in result.attachments]
    assert any("contenido restaurado" in str(m) for m in mensajes)


async def test_the_providers_contribution_travels_after_the_restored_files(tmp_path):
    """`compact_context()` era una costura sin consumidor. El orden es el de A:
    primero los ficheros, después lo que aportan las capacidades (532-561)."""
    (tmp_path / "modulo.py").write_text("del disco\n")
    ctx = _ctx(tmp_path)
    await ReadFileTool().execute({"path": "modulo.py"}, ctx)

    result = await compact_conversation(
        _history(),
        FakeCaller(LONG_SUMMARY),
        LOCAL_BUDGET,
        ctx=ctx,
        provider_messages=[{"role": "user", "content": "aporte de una capacidad"}],
    )

    assert "del disco" in result.attachments[0]["content"]
    assert result.attachments[-1]["content"] == "aporte de una capacidad"


async def test_the_post_compact_hook_contributes_messages_and_its_notice_is_combined():
    """A ejecuta los hooks post-compactación y une los dos avisos con `\\n`
    (723-736). Sin la unión, el aviso del hook previo se pierde en silencio."""

    async def hooks(event: HookEvent, payload: dict[str, Any]) -> HookDecision | None:
        if event is HookEvent.PRE_COMPACT:
            return HookDecision(message="aviso previo")
        if event is HookEvent.POST_COMPACT:
            assert payload["compact_summary"] == LONG_SUMMARY
            return HookDecision(
                message="aviso posterior", additional_context="contexto del hook"
            )
        return None

    result = await compact_conversation(
        _history(), FakeCaller(LONG_SUMMARY), LOCAL_BUDGET, hooks=hooks
    )

    assert result.user_display_message == "aviso previo\naviso posterior"
    assert len(result.hook_results) == 1
    assert "contexto del hook" in result.hook_results[0]["content"]
