"""Homologación 10·tools-native — cada tool nativa (`tools/native/*.py`) vs su contraparte
canónica `tools/*Tool/` (uno a uno).

Los tests que PASAN codifican comportamiento YA homologado. Los `xfail(strict=True)` codifican
los gaps FIND-NATIVE-*: fallan HOY (comportamiento homologado ausente) y su fallo ES la evidencia
del gap. Si alguno empezara a pasar, el strict lo vuelve error → señal de reclasificar el estado
en `10-tools-native.md`.

⚠ **Reescrito 2026-08-02 por `H-L4`** (9ª ventana). Cuatro `xfail` de este fichero estaban
escritos sobre la **FIRMA** —`"replace_all" in FileEditTool.input_schema["properties"]`,
`"status" in TaskUpdateTool.input_schema["properties"]`, `EnterWorktreeTool.safe_for_background
is True`, `BashTool.name == "Bash"`— y **acreditaban en falso**: basta añadir la clave al schema
o flipar el bool para que el `strict` los vuelva XPASS y la deuda quede declarada pagada **sin
que la conducta exista**. Un `replace_all` en el schema que `execute()` ignora deja el gap intacto
y el tracker en verde. Los cuatro se reescriben a CONDUCTA: la aserción es ahora sobre el efecto
observable (el fichero reemplazado, el status que `TaskGet` devuelve, el filtro real del registry,
la resolución por nombre en el registry de producción). Se invirtió el sujeto de la aserción, no
se relajó el listón: los cuatro siguen ROJOS hoy y por el mismo gap.

Cobertura por `E10` (`test_tramo1_gate.py`): el efecto observable de **las 25** tools nativas
—incluidos `Edit`, `Config`, `TodoWrite`, las seis `Task*` y `bash`— se asevera allí con cableado
real y negativas. Este fichero NO lo duplica: cubre lo que `E10` deliberadamente no mira, que es
la **divergencia con el canónico** tool a tool.
"""
from __future__ import annotations

import asyncio

import pytest

from agentic_runtime.contracts.abort import AbortController

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry
from agentic_runtime.tools.factory import create_tools
from agentic_runtime.tools.fs_env import ConfinedFilesystem
from agentic_runtime.tools.native.ask_user import AskUserQuestionTool
from agentic_runtime.tools.native.bash import BashTool
from agentic_runtime.tools.native.config import ConfigTool
from agentic_runtime.tools.native.file_edit import FileEditTool
from agentic_runtime.tools.native.glob_tool import DEFAULT_GLOB_LIMIT, GlobTool
from agentic_runtime.tools.native.grep_tool import DEFAULT_HEAD_LIMIT
from agentic_runtime.tools.native.plan_mode import EnterPlanModeTool
from agentic_runtime.tools.native.read_file import ReadFileTool
from agentic_runtime.tools.native.task_tools import (
    TaskCreateTool,
    TaskGetTool,
    TaskUpdateTool,
)
from agentic_runtime.tools.native.todo_write import TodoWriteTool
from agentic_runtime.tools.native.worktree import EnterWorktreeTool
from agentic_runtime.tools.native.write_file import WriteFileTool


def _ctx(tmp_path=None, **kw) -> ToolUseContext:
    if tmp_path is not None:
        kw.setdefault("fs", ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]))
    return ToolUseContext(session_id="s1", stop=AbortController(), **kw)


# ===========================================================================
# HOMOLOGADO (PASA)
# ===========================================================================

def test_edit_is_resolvable_by_its_canonical_name():
    """`Edit` homologa el nombre canónico — aseverado por CONDUCTA, no por atributo.

    El nombre de una tool no es cosmético: es la clave por la que el modelo la invoca y por
    la que el registry la resuelve. Aseverar `FileEditTool.name == "Edit"` mide la FIRMA;
    lo que importa es que el registry **de producción** entregue la tool cuando llega una
    tool call llamada `Edit` (`H-L4`).
    """
    tool = create_tools().resolve("Edit")
    assert tool is not None, "el registry de producción no resuelve el nombre canónico `Edit`"
    assert type(tool) is FileEditTool


def test_glob_caps_results_at_the_canonical_limit(tmp_path):
    """Caps espejo (§A13/A14) por CONDUCTA: glob trunca a 100 y lo DICE.

    La constante en sí (`DEFAULT_GLOB_LIMIT == 100`) es FIRMA: no prueba que el cap se
    aplique. Se siembran 130 ficheros y se cuenta lo que sale, más el aviso de truncado que
    el canónico emite para que el modelo sepa que la lista está incompleta.
    """
    for i in range(130):
        (tmp_path / f"f{i:03d}.txt").write_text("x")
    ctx = _ctx(tmp_path)
    r = await_(GlobTool().execute({"pattern": "*.txt"}, ctx))
    assert not r.is_error, r.output
    lineas = [ln for ln in r.output.splitlines() if ln.endswith(".txt")]
    assert len(lineas) == DEFAULT_GLOB_LIMIT == 100, f"salieron {len(lineas)} matches"
    assert "truncated" in r.output.lower(), "trunca en silencio: el modelo no sabe que falta"
    # CONTROL POSITIVO: por debajo del cap no trunca ni avisa.
    r2 = await_(GlobTool().execute({"pattern": "f00*.txt"}, ctx))
    assert len([ln for ln in r2.output.splitlines() if ln.endswith(".txt")]) == 10
    assert "truncated" not in r2.output.lower()


def test_grep_head_limit_mirrors_canonical():
    """`DEFAULT_HEAD_LIMIT == 250` (§A14).

    Se queda como FIRMA **declarado**: el cap de grep se ejerce en `E10` (`_e10_grep`), y
    duplicar aquí la siembra de 250+ líneas no añade grado probatorio, sólo tiempo.
    """
    assert DEFAULT_HEAD_LIMIT == 250


def test_context_modifier_attached_and_applicable():
    """CORR a 09·A24/D7: plan/worktree/config/todo adjuntan `context_modifier` al ToolResult
    y el loop lo aplica (agent_loop.py:329-337). Verifica que el modifier existe y muta app_state."""
    ctx = _ctx()
    r = await_(TodoWriteTool().execute({"todos": []}, ctx))
    modifier = getattr(r, "context_modifier", None)
    assert modifier is not None
    modifier(ctx)
    assert ctx.app_state.native.get("todos") == []


def test_ends_turn_signalled_by_hitl_tools():
    """AskUserQuestion/ExitPlanMode ceden el turno con `ends_turn` (homólogo de
    requiresUserInteraction canónico, §C4/D2)."""
    ctx = _ctx()
    r = await_(AskUserQuestionTool().execute(
        {"questions": [{"question": "¿q?", "header": "h", "options": [{"label": "a"}, {"label": "b"}]}]},
        ctx,
    ))
    assert getattr(r, "ends_turn", False) is True


def test_enter_plan_mode_is_root_only():
    """EnterPlanMode canónico es main-thread-only; el runtime lo rechaza en subagente (§D1)."""
    ctx = _ctx(is_subagent=True)
    r = await_(EnterPlanModeTool().execute({}, ctx))
    assert r.is_error


def test_worktree_rejects_a_bad_slug_through_execute(tmp_path):
    """Slug validado (§E1) por CONDUCTA: la tool rechaza el nombre, no sólo el helper.

    El test anterior llamaba a `_validate_slug` directamente —función privada, unidad, no
    conducta de la tool—: no probaba que `execute()` la CONSULTE. Se asevera el rechazo por
    la puerta pública, con control positivo (un slug legal no muere en la validación: pasa
    de ella y sólo falla más adelante, al no haber repo git).
    """
    ctx = _ctx(tmp_path)
    r = await_(EnterWorktreeTool().execute({"name": "bad name!"}, ctx))
    assert r.is_error, "aceptó un slug con espacio y signo de admiración"
    assert "not a git repository" not in r.output.lower(), (
        "murió por no haber repo, no por el slug: la validación no se consultó"
    )
    # CONTROL POSITIVO: un slug legal supera la validación (falla después, por no ser repo git).
    r2 = await_(EnterWorktreeTool().execute({"name": "feature-x"}, ctx))
    assert r2.is_error and "not a git repository" in r2.output.lower(), r2.output


@pytest.mark.xfail(strict=True, reason="FIND-CFG-1: la rama GET de Config escribe en app_state (config.py:44 `setdefault` antes de bifurcar); el canónico la tiene como lectura pura y la DECLARA read-only (ConfigTool.ts:90-92, :136-144)")
def test_config_get_does_not_write_state(tmp_path):
    """`FIND-CFG-1`: la rama GET de `Config` debería ser LECTURA PURA, como en el canónico.

    A tiene el GET como lectura pura **y lo declara**: `isReadOnly(input) { return
    input.value === undefined }` (`ConfigTool.ts:90-92`), y su `call()` en la rama GET sólo
    llama a `getValue()`, que lee de `getGlobalConfig()`/`getInitialSettings()` sin escribir
    (`ConfigTool.ts:136-144`, leído 1→EOF). B hacía
    `ctx.app_state.native.setdefault("config", {})` **antes de bifurcar** (`config.py:44`),
    así que una simple lectura dejaba la clave creada en el estado de la sesión: una
    escritura en la rama de lectura que nadie había aseverado nunca.

    El test anterior (`'"operation": "get"' in r.output`) era FORMA: miraba la cadena del
    output, no el efecto sobre el estado.
    """
    ctx = _ctx(tmp_path)
    antes = dict(ctx.app_state.native)
    r = await_(ConfigTool().execute({"setting": "model"}, ctx))
    assert not r.is_error, r.output
    assert ctx.app_state.native == antes, (
        f"el `get` escribió en app_state: {set(ctx.app_state.native) - set(antes)}"
    )
    # CONTROL POSITIVO: el SET sí deja efecto, y sólo a través de su `context_modifier`.
    r2 = await_(ConfigTool().execute({"setting": "model", "value": "opus"}, ctx))
    assert ctx.app_state.native == antes, "el `set` mutó el ctx fuera del context_modifier"
    r2.context_modifier(ctx)
    assert ctx.app_state.native["config"]["model"] == "opus"


def test_ask_user_announces_the_canonical_questionnaire():
    """Cuestionario 1-4 tal y como se ANUNCIA desde el registry de producción (§C4).

    La forma completa del schema (opciones 2-4, `required`, `multiSelect`, `annotations`/
    `answers`/`metadata`) se asevera en `test_ask_user.py::test_schema_es_cuestionario_1_a_4`
    y el anuncio es gate DURO en `E11` (`D-14`); aquí sólo se comprueba que lo que el
    **registry de producción** entrega es esa misma tool y no otra cosa.
    """
    tool = create_tools().resolve("AskUserQuestion")
    assert tool is not None
    q = tool.input_schema["properties"]["questions"]
    assert q["minItems"] == 1 and q["maxItems"] == 4


# ===========================================================================
# GAPS — xfail(strict): fallan HOY, su fallo ES la evidencia
# ===========================================================================

@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-NAME: bash/read_file/write_file/glob/grep no homologan el nombre canónico (Bash/Read/Write/Glob/Grep)")
def test_fs_shell_tools_resolvable_by_canonical_names():
    """CONDUCTA (`H-L4`): el registry de producción no resuelve los nombres canónicos.

    La versión anterior aseveraba `BashTool.name == "Bash"` —FIRMA—: renombrar el atributo
    la habría puesto verde aunque el registry siguiera indexando por otra clave. Lo que
    rompe de verdad es que una tool call `Bash` emitida por el modelo **no se resuelve**.
    """
    registry = create_tools()
    for canonico in ("Bash", "Read", "Write", "Glob", "Grep"):
        assert registry.resolve(canonico) is not None, f"el registry no resuelve `{canonico}`"


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READSTATE/A5: read_file no puebla un read_file_state en el ToolUseContext (base ausente de read-before-edit)")
def test_read_populates_read_file_state(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hola\nmundo\n")
    ctx = _ctx(tmp_path)
    await_(ReadFileTool().execute({"path": str(f)}, ctx))
    assert getattr(ctx, "read_file_state", None) and str(f) in ctx.read_file_state


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-EDITGUARDS=FIND-CTX1: file_edit no impone read-before-edit (canónico rechaza editar sin leer antes)")
def test_edit_requires_read_before_edit(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("alfa beta\n")
    ctx = _ctx(tmp_path)  # nunca se leyó f
    r = await_(FileEditTool().execute(
        {"file_path": str(f), "old_string": "alfa", "new_string": "gamma"}, ctx,
    ))
    assert r.is_error and "read it first" in r.output.lower()


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-EDITGUARDS=G8/FIND-TOOL9: write_file no bloquea dangerous-files (.claude/settings.json) dentro del workspace")
def test_write_blocks_dangerous_settings_file(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    ctx = _ctx(tmp_path)
    r = await_(WriteFileTool().execute({"path": str(settings), "content": "{}"}, ctx))
    assert r.is_error  # homologado: validateInputForSettingsFileEdit lo rechazaría


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READ/A6: Edit no soporta replace_all (canónico sí)")
def test_edit_replace_all_replaces_every_occurrence(tmp_path):
    """CONDUCTA (`H-L4`): con `replace_all`, las N ocurrencias quedan reemplazadas EN DISCO.

    La versión anterior aseveraba `"replace_all" in FileEditTool.input_schema["properties"]`
    —FIRMA—: añadir la clave al schema la habría puesto XPASS con `execute()` ignorando el
    parámetro por completo, declarando pagada una deuda inexistente en la conducta. Hoy B
    ni siquiera acepta el input: `count > 1` es error de ambigüedad (`file_edit.py:66-70`),
    así que el fichero queda intacto.
    """
    f = tmp_path / "a.txt"
    f.write_text("uno x dos\ntres x cuatro\ncinco x seis\n")
    ctx = _ctx(tmp_path)
    r = await_(FileEditTool().execute(
        {"file_path": str(f), "old_string": "x", "new_string": "Y", "replace_all": True}, ctx,
    ))
    assert not r.is_error, r.output
    assert f.read_text(encoding="utf-8") == "uno Y dos\ntres Y cuatro\ncinco Y seis\n"


@pytest.mark.xfail(strict=True, reason="GAP-TOOL2/GAP-MODE2: worktree.safe_for_background=False pero el canónico lo incluye en ASYNC_AGENT_ALLOWED_TOOLS")
def test_worktree_offered_to_a_background_agent():
    """CONDUCTA (`H-L4`): el filtro REAL por kind deja fuera `EnterWorktree`.

    La versión anterior aseveraba `EnterWorktreeTool.safe_for_background is True` —FIRMA—:
    flipar el bool la habría puesto XPASS sin que nadie comprobara que el filtro que lo
    consume (`registry.list_available(mode="background")`, `tools/registry.py:36`) entrega
    de verdad la tool al agente unattended. Se asevera el resultado del filtro.
    """
    ofrecidas = {t.name for t in create_tools().list_available(mode="background")}
    assert "EnterWorktree" in ofrecidas, (
        "el agente en background no recibe EnterWorktree; el canónico lo lista en "
        f"ASYNC_AGENT_ALLOWED_TOOLS. Ofrecidas: {sorted(ofrecidas)}"
    )


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-TASK/G3: TaskUpdate no modela transiciones de status (canónico: pending/in_progress/completed/deleted)")
def test_task_update_transitions_status_observably(tmp_path):
    """CONDUCTA (`H-L4`): el status pedido a `TaskUpdate` lo devuelve después `TaskGet`.

    La versión anterior aseveraba `"status" in TaskUpdateTool.input_schema["properties"]`
    —FIRMA—: añadir la clave al schema la habría puesto XPASS mientras `execute()` sigue
    ignorando el campo (`task_tools.py:179-181` sólo aplica `description`), o sea la deuda
    entera intacta. Se asevera la transición a través de la tool que la lee.
    """
    ctx = _ctx(tmp_path, task_registry=InMemoryTaskRegistry())
    creada = await_(TaskCreateTool().execute({"subject": "s", "description": "d"}, ctx))
    import json
    task_id = json.loads(creada.output)["task_id"]

    await_(TaskUpdateTool().execute({"task_id": task_id, "status": "completed"}, ctx))
    leida = await_(TaskGetTool().execute({"task_id": task_id}, ctx))
    assert json.loads(leida.output)["status"] == "completed", leida.output


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-BASH=FIND-TOOL8/F2: bash sin shell persistente — cd no persiste entre llamadas")
def test_bash_persistent_shell(tmp_path):
    ctx = _ctx()
    await_(BashTool().execute({"command": f"cd {tmp_path}"}, ctx))
    r = await_(BashTool().execute({"command": "pwd"}, ctx))
    assert str(tmp_path) in r.output


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READ/A3b: read_file no prefija números de línea (canónico addLineNumbers, cat -n)")
def test_read_adds_line_numbers(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("alfa\nbeta\n")
    ctx = _ctx(tmp_path)
    r = await_(ReadFileTool().execute({"path": str(f)}, ctx))
    # homologado: cada línea con su número (p.ej. "     1\talfa")
    assert "1\talfa" in r.output or r.output.lstrip().startswith("1")


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READ/A3c: read_file no rechaza binarios (canónico: 'cannot read binary files')")
def test_read_rejects_binary(tmp_path):
    png = tmp_path / "img.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\x00")
    ctx = _ctx(tmp_path)
    r = await_(ReadFileTool().execute({"path": str(png)}, ctx))
    assert r.is_error


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-BASH-DEPTH/B12: is_error=returncode!=0 a secas — grep sin match (rc=1) NO debería ser error (interpretCommandResult)")
def test_bash_grep_no_match_not_error(tmp_path):
    ctx = _ctx()
    r = await_(BashTool().execute({"command": "printf 'a\\nb\\n' | grep zzz"}, ctx))
    assert not r.is_error  # rc=1 semántico: "sin coincidencias", no fallo


@pytest.mark.xfail(strict=True, reason="FIND-READ-1: `read_file` no tiene NINGÚN cap; A corta por bytes (256 KB) y por tokens (25 000) y LANZA")
def test_read_file_refuses_a_file_over_the_canonical_size_cap(tmp_path):
    """`FIND-READ-1` — un `Read` sin cap vuelca el fichero entero al contexto.

    Contraste (`D-08`, leído 1→EOF en `FileReadTool/limits.ts`): A aplica **dos** topes
    —`maxSizeBytes` 256 KB sobre el tamaño TOTAL del fichero y `maxTokens` 25 000 sobre la
    salida— y en desbordamiento **lanza** en vez de truncar. La cabecera del fichero documenta
    que probaron truncar (#21841) y lo **revirtieron**: el throw devuelve ~100 bytes de error,
    truncar devolvía 25 K tokens de contenido en el tope. O sea: el corte es deliberado y
    medido, no un detalle.

    B (`read_file.py:38`) hace `limit = input.get("limit", len(lines))` — sin `limit`
    explícito se lee el fichero ENTERO. Un log de 50 MB entra al contexto tal cual y rompe
    al proveedor, que es el mismo modo de fallo que `grep_tool.py:12-15` sí documenta y
    previene con `DEFAULT_HEAD_LIMIT`. Es CORE-GAP: la protección existe en el hermano.

    Control positivo incluido: un fichero pequeño debe seguir leyéndose entero.
    """
    ctx = _ctx(tmp_path)
    pequeno = tmp_path / "ok.txt"
    pequeno.write_text("hola\n")
    assert "hola" in await_(ReadFileTool().execute({"path": str(pequeno)}, ctx)).output

    grande = tmp_path / "enorme.txt"
    grande.write_text("x" * 300_000)  # > 256 KB
    r = await_(ReadFileTool().execute({"path": str(grande)}, ctx))
    assert r.is_error, (
        f"el fichero de {grande.stat().st_size} B salió entero al contexto "
        f"({len(r.output)} chars de output)"
    )


@pytest.mark.xfail(strict=True, reason="FIND-READ-2: `offset` es 0-indexado y la salida no lleva números de línea; A usa offset=1 y addLineNumbers")
def test_read_file_offset_is_one_indexed_and_output_is_numbered(tmp_path):
    """`FIND-READ-2` — dos divergencias que se pagan juntas porque son el mismo contrato.

    Contraste (`D-08`): `FileReadTool.ts:497` desestructura `{ offset = 1 }` —**1-indexado**—
    y `:726` devuelve `addLineNumbers(file)`. B (`read_file.py:37-39`) usa `offset` como
    índice de lista Python (**0-indexado**) y emite las líneas desnudas.

    No es cosmético en ninguna de las dos mitades: `offset=1` pide la línea 1 en A y devuelve
    la línea 2 en B —**un off-by-one silencioso** en la herramienta que el modelo usa para
    citar código—, y sin numeración el modelo no puede referirse a `fichero:línea` sin
    contarlas a mano, que es justo lo que la numeración existe para evitar.
    """
    ctx = _ctx(tmp_path)
    f = tmp_path / "tres.txt"
    f.write_text("uno\ndos\ntres\n")

    r = await_(ReadFileTool().execute({"path": str(f), "offset": 1, "limit": 1}, ctx))
    assert "uno" in r.output, f"offset=1 debe dar la PRIMERA línea (1-indexado), dio {r.output!r}"

    entero = await_(ReadFileTool().execute({"path": str(f)}, ctx))
    assert "1" in entero.output.split("\n")[0], (
        f"la salida no lleva número de línea: {entero.output.splitlines()[:1]}"
    )


@pytest.mark.xfail(strict=True, reason="FIND-GLOB-1: orden alfabético; A ordena por mtime (--sort=modified), y con el cap de 100 el orden decide QUÉ se ve")
def test_glob_orders_by_mtime_not_alphabetically(tmp_path):
    """`FIND-GLOB-1` — el orden no es presentación cuando hay un cap: es SELECCIÓN.

    Contraste (`D-08`, leído en `utils/glob.ts:94-104`): A pasa `--sort=modified` con el
    comentario explícito «sort by modification time (oldest first)», y recorta DESPUÉS
    (`:127 slice(offset, offset + limit)`). B (`glob_tool.py:40-41`) hace `sorted(...)`
    alfabético y recorta igual.

    Con el mismo cap de 100 que ambos comparten, el orden decide **cuáles 100 de 130 ve el
    modelo**. Alfabéticamente eso es arbitrario; por mtime es «lo que se tocó», que es lo que
    hace útil un glob durante una sesión de trabajo. Por eso se levanta como hallazgo y no
    como divergencia cosmética.

    Se siembra con mtimes explícitos para que la medición no dependa de la velocidad del disco.
    """
    import os

    ctx = _ctx(tmp_path)
    # `zzz` es el MÁS ANTIGUO, `aaa` el más reciente: alfabético y mtime dan órdenes opuestos.
    for nombre, mtime in (("zzz.txt", 1_000_000), ("mmm.txt", 2_000_000), ("aaa.txt", 3_000_000)):
        p = tmp_path / nombre
        p.write_text("x")
        os.utime(p, (mtime, mtime))

    r = await_(GlobTool().execute({"pattern": "*.txt", "path": str(tmp_path)}, ctx))
    lineas = [line for line in r.output.splitlines() if line.strip()]
    assert len(lineas) == 3  # control positivo: los tres salen
    assert lineas[0].endswith("zzz.txt"), (
        f"A ordena por mtime (oldest first) ⇒ primero `zzz.txt`; B dio {lineas}"
    )


def await_(coro):
    """`asyncio.run` con nombre corto: estos tests son síncronos a propósito."""
    return asyncio.run(coro)
