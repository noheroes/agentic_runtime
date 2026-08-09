"""Homologación 09·tools-infra — contrato/registry/pool/dispatcher/deferred/exec/fs
vs el core de tools canónico (`Tool.ts`, `tools.ts`, `toolSearch.ts`, `filesystem.ts`, `path.ts`).

Los tests que PASAN codifican el comportamiento YA homologado (contrato mínimo, pool assembly,
resolución del mismo pool, path-guards). Los `xfail(strict=True)` codifican los gaps FIND-TOOL/
GAP-TOOL: fallan HOY (comportamiento homologado ausente) y su fallo ES la evidencia del gap.
Si alguno empezara a pasar, el strict lo vuelve error → señal de reclasificar el estado en 09-tools-infra.md.
"""
from __future__ import annotations

import asyncio

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.abort import AbortController
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.tools.deferred import is_deferred_tool
from agentic_runtime.tools.deferred_strategy import (
    NativeDeferredStrategy,
    SimulatedDeferredStrategy,
)
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.tools.factory import create_tools
from agentic_runtime.tools.fs_env import (
    ConfinedFilesystem,
    PathOutsideWorkspace,
    contains_path_traversal,
)
from agentic_runtime.tools.native.tool_search import TOOL_SEARCH_TOOL_NAME
from agentic_runtime.tools.pool import ToolPool, assemble_tool_pool
from agentic_runtime.tools.protocol import ToolCategory, ToolProtocol, ToolResult

# ---------------------------------------------------------------------------
# Fake tool mínima (implementa ToolProtocol estructural)
# ---------------------------------------------------------------------------

class _FakeTool:
    def __init__(self, name: str, *, deferred: bool = False, output: str = "ok") -> None:
        self.name = name
        self.description = f"desc-{name}"
        self.input_schema: dict = {"type": "object", "properties": {}}
        self.category = ToolCategory.UTILITY
        self.requires_permission = False
        self.safe_for_background = True
        self.timeout_seconds = 5.0
        self.deferred = deferred
        self._output = output

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        return ToolResult(tool_name=self.name, output=self._output)


def _ctx(**kw) -> ToolUseContext:
    return ToolUseContext(session_id="s1", stop=AbortController(), **kw)


# ===========================================================================
# A · Contrato — lo homologado (PASA)
# ===========================================================================

def test_fake_tool_satisfies_protocol_minimal_surface():
    """ToolProtocol es un subconjunto de 8 miembros del `Tool` canónico (~60). Verifica
    que la superficie mínima es la esperada (runtime_checkable)."""
    t = _FakeTool("Bash")
    assert isinstance(t, ToolProtocol)


def test_tool_result_flags_ok_error_timeout_aborted():
    """ToolResult lleva output+flags (A22). Espejo aplanado del ToolResult<T> canónico."""
    assert ToolResult.error("x", "boom").is_error
    assert ToolResult.timeout("x").is_timeout
    assert ToolResult.aborted("x").is_aborted


# ===========================================================================
# B/C · Registry + pool assembly — lo homologado (PASA)
# ===========================================================================

def test_create_tools_registers_native_and_extras():
    """create_tools = getAllBaseTools (B1): nativas + extras del integrador."""
    extra = _FakeTool("MyCustom")
    reg = create_tools(extras=[extra])
    assert reg.resolve("MyCustom") is extra
    assert reg.resolve("bash") is not None


def test_assemble_pool_native_precedence_and_sorted():
    """assemble_tool_pool = assembleToolPool (C1): native gana en colisión, sort per-partición,
    dedup. Estabilidad de prompt-cache."""
    native = [_FakeTool("Zeta"), _FakeTool("Alpha")]
    cap = [_FakeTool("Alpha", output="CAP"), _FakeTool("Beta")]
    out = assemble_tool_pool(native, cap, PermissionContext())
    names = [t.name for t in out]
    # sort per-PARTICIÓN (native contiguo primero: Alpha,Zeta), luego capability (Beta;
    # Alpha ya visto → dedup). NO es un sort global — el prefijo native contiguo es el
    # invariante de cache-breakpoint del canónico (assembleToolPool).
    assert names == ["Alpha", "Zeta", "Beta"]
    alpha = next(t for t in out if t.name == "Alpha")
    assert alpha._output == "ok"  # native gana (no la capability con output="CAP")


def test_assemble_pool_applies_deny_by_name():
    """B4: deny por NOMBRE exacto (denied_names). Nota: sin MCP server-prefix (gap documentado)."""
    native = [_FakeTool("Bash"), _FakeTool("Danger")]
    pc = PermissionContext(always_deny=["Danger"])
    out = assemble_tool_pool(native, [], pc)
    assert [t.name for t in out] == ["Bash"]


def test_pool_find_resolves_from_same_assembled_pool():
    """C2/D1: ejecución y anuncio resuelven del MISMO pool (findToolByName). Invariante clave."""
    pool = ToolPool(native_tools=[_FakeTool("Bash")], capability_tools=[_FakeTool("mcp__x__y", deferred=True)])
    assert pool.find("Bash") is not None
    # deferred = visibilidad, no disponibilidad: sigue resoluble desde el pool
    assert pool.find("mcp__x__y") is not None


# ===========================================================================
# D · Dispatcher — lo homologado (PASA)
# ===========================================================================

def test_dispatch_resolves_and_runs_from_ctx_pool():
    """D1/D4: el dispatcher resuelve de ctx.tool_pool y ejecuta."""
    ctx = _ctx(tool_pool=ToolPool(native_tools=[_FakeTool("Echo", output="hi")]))
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Echo", tool_input={}, ctx=ctx))
    assert r.output == "hi" and not r.is_error


def test_dispatch_aborts_before_work_when_stop_set():
    """D2: abort-check pre-ejecución (ctx.stop).

    ⚠ El rótulo anterior («Binario, sin reason (gap SIG2)») era **falso desde que existe
    `contracts/abort.py`**: `AbortController` transporta `AbortReason` y deriva `aborted`
    de ella precisamente para cerrar `SIG2`. Lo que sigue sin razón es el **resultado**
    (`ToolResult.aborted`), no la señal — ver `test_abort_reason_reaches_the_result`.
    Un rótulo caducado en un test verde es lo que hace diagnosticar mal el gap.
    """
    ctx = _ctx(tool_pool=ToolPool(native_tools=[_FakeTool("Echo")]))
    ctx.stop.abort()
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Echo", tool_input={}, ctx=ctx))
    assert r.is_aborted


def test_dispatch_unknown_tool_is_error():
    ctx = _ctx(tool_pool=ToolPool(native_tools=[]))
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Nope", tool_input={}, ctx=ctx))
    assert r.is_error


# ===========================================================================
# E · Deferred — lo homologado (PASA)
# ===========================================================================

def test_tool_search_never_deferred_and_flag_defers():
    """E1 (parcial): ToolSearch nunca diferida; `deferred=True` sí. (Sin alwaysLoad/isMcp: gap.)"""
    assert is_deferred_tool(_FakeTool(TOOL_SEARCH_TOOL_NAME, deferred=True)) is False
    assert is_deferred_tool(_FakeTool("mcp__x__y", deferred=True)) is True
    assert is_deferred_tool(_FakeTool("Bash")) is False


def test_simulated_strategy_hides_undiscovered_deferred():
    """E2: la simulada oculta diferidas no descubiertas y muestra ToolSearch si hay diferidas."""
    pool = [_FakeTool("Bash"), _FakeTool("mcp__x__y", deferred=True), _FakeTool(TOOL_SEARCH_TOOL_NAME)]
    ctx = _ctx()
    plan = SimulatedDeferredStrategy().prepare_turn(ctx, pool)
    names = {s["name"] for s in plan.tool_schemas}
    assert "Bash" in names
    assert TOOL_SEARCH_TOOL_NAME in names  # hay diferidas → visible
    assert "mcp__x__y" not in names  # oculta hasta ToolSearch


def test_native_strategy_marks_defer_loading_and_drops_toolsearch():
    """E3 (AÑADIDO): la nativa marca defer_loading y deja el tool_search al provider."""
    pool = [_FakeTool("Bash"), _FakeTool("mcp__x__y", deferred=True), _FakeTool(TOOL_SEARCH_TOOL_NAME)]
    plan = NativeDeferredStrategy().prepare_turn(_ctx(), pool)
    by_name = {s["name"]: s for s in plan.tool_schemas}
    assert TOOL_SEARCH_TOOL_NAME not in by_name  # provider lo añade server-side
    assert by_name["mcp__x__y"].get("defer_loading") is True
    assert "defer_loading" not in by_name["Bash"]


#: El reparto de `shouldDefer` del canónico, censado sobre `claude-code/src/tools` 1→EOF
#: (`D-08`) y no de memoria. Cada nombre lleva su cita en la clase de B. Las 12 que A
#: difiere y B no tiene (`LSPTool`, `SendMessage`, `Team*`, `RemoteTrigger`, `Cron*`,
#: `NotebookEdit`) no entran; las dos de recursos MCP tampoco, porque son `FIND-MCP17`.
_A_DIFIERE = {
    "AskUserQuestion", "Config", "EnterPlanMode", "ExitPlanMode", "EnterWorktree",
    "ExitWorktree", "TaskCreate", "TaskGet", "TaskList", "TaskOutput", "TaskStop",
    "TaskUpdate", "TodoWrite", "WebFetch", "WebSearch",
}
#: Lo que A **no** difiere, y no es arbitrario: es el núcleo de exploración que el modelo
#: necesita en el turno 1, más `ToolSearch` (que nunca se difiere) y `clone_repository`,
#: que no existe en A (`L10`).
_A_NO_DIFIERE = {
    "Agent", "bash", "glob", "grep", "read_file", "write_file", "Edit", "Sleep",
    "clone_repository", "ToolSearch",
}


def test_gap_tool4_el_reparto_de_diferidas_es_el_del_canonico():
    """`GAP-TOOL4`: las 15 «meta» que A retira del turno 1 se difieren, y sólo ésas.

    Se mide sobre las clases de PRODUCCIÓN, no sobre un pool fabricado: el gate `E2g`
    monkeypatchea las suyas (`test_tramo1_gate.py:2357-2359`) y por eso no veía este
    hueco. La aserción va en las DOS direcciones a propósito — que falte una marca y que
    sobre una son el mismo defecto de reparto, y sólo la segunda mitad impide «arreglar»
    un rojo difiriendo `grep`, que es justo lo que el turno 1 no puede perder.
    """
    from agentic_runtime.tools.factory import create_tools

    por_nombre = {t.name: t for t in create_tools(interactive=True).all_tools()}
    assert _A_DIFIERE | _A_NO_DIFIERE == set(por_nombre), (
        f"el censo de nativas cambió: {set(por_nombre) ^ (_A_DIFIERE | _A_NO_DIFIERE)}"
    )
    diferidas = {n for n, t in por_nombre.items() if is_deferred_tool(t)}
    assert diferidas == _A_DIFIERE, (
        f"faltan={_A_DIFIERE - diferidas} sobran={diferidas - _A_DIFIERE}"
    )


# ===========================================================================
# G · Path guards / confinamiento — lo homologado (PASA)
# ===========================================================================

def test_contains_path_traversal_matches_canonical():
    """G1: byte-idéntico a containsPathTraversal (path.ts:133)."""
    assert contains_path_traversal("../etc/passwd")
    assert contains_path_traversal("a/../b")
    assert not contains_path_traversal("a/b/c")


def test_confined_fs_blocks_outside_workspace(tmp_path):
    """G5/G6: resolve() confina contra roots; fuera → PathOutsideWorkspace."""
    (tmp_path / "inside.txt").write_text("x")
    fs = ConfinedFilesystem(roots=[tmp_path])
    assert fs.resolve(str(tmp_path / "inside.txt"), for_write=False)
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve("/etc/passwd", for_write=False)


def test_write_roots_narrower_than_read_roots(tmp_path):
    """G7: split read/write roots — escritura más estrecha que lectura."""
    sub = tmp_path / "wr"
    sub.mkdir()
    fs = ConfinedFilesystem(roots=[tmp_path], write_roots=[sub])
    # lectura permitida en todo tmp_path
    assert fs.resolve(str(tmp_path / "a"), for_write=False)
    # escritura sólo en sub
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(tmp_path / "a"), for_write=True)
    assert fs.resolve(str(sub / "a"), for_write=True)


# ===========================================================================
# GAPS — xfail(strict): fallan HOY, su fallo ES la evidencia
# ===========================================================================

@pytest.mark.xfail(strict=True, reason="FIND-TOOL3=FIND-SIG4: interruptBehavior 'cancel'|'block' ausente — el dispatcher cancela sin consultar la política de la tool NI la razón del abort")
def test_block_tool_survives_a_user_interrupt_but_not_other_aborts():
    """CONDUCTA, ajustada al canónico tras contrastarlo (`D-08`).

    Dos correcciones sobre mis propias versiones anteriores:

    1. La primera aseveraba `t.interrupt_behavior() in ("cancel","block")` **sobre
       `_FakeTool`, el DOBLE de este fichero**: añadirle el método al doble la habría
       puesto XPASS sin que el runtime cambiara una línea.
    2. La segunda exigía que una tool `block` sobreviviera a **cualquier** abort. Eso
       asevera MÁS que A y habría inventado deuda (`L10`). Leído
       `StreamingToolExecutor.ts:219-229` 1→EOF de esa zona: A consulta
       `interruptBehavior` **sólo si `signal.reason === 'interrupt'`** —usuario que teclea
       mientras las tools corren—; para cualquier otra razón cancela todo
       (`return 'user_interrupted'`). El default es `'block'` cuando la tool no lo
       implementa (`Tool.ts:414`, `:233-241`).

    Se asevera el espejo exacto, con las dos ramas: sobrevive a `USER_INTERRUPT`, muere
    con `AGENT_KILLED`.
    """
    from agentic_runtime.contracts.abort import AbortReason

    class _Block(_FakeTool):
        def __init__(self):
            super().__init__("Blocker", output="terminé")

        def interrupt_behavior(self):
            return "block"

    # RAMA 1 — interrupción del usuario: la tool `block` sigue y entrega su resultado.
    ctx = _ctx(tool_pool=ToolPool(native_tools=[_Block()]))
    ctx.stop.abort(AbortReason.USER_INTERRUPT)
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Blocker", tool_input={}, ctx=ctx))
    assert not r.is_aborted and r.output == "terminé", (
        "canceló una tool `block` ante una interrupción de usuario (política no consultada)"
    )

    # RAMA 2 — CONTROL NEGATIVO: con otra razón, `block` no protege de nada.
    ctx2 = _ctx(tool_pool=ToolPool(native_tools=[_Block()]))
    ctx2.stop.abort(AbortReason.AGENT_KILLED)
    r2 = asyncio.run(ToolDispatcher().dispatch(tool_name="Blocker", tool_input={}, ctx=ctx2))
    assert r2.is_aborted, "`block` no debe blindar contra un abort que no es interrupción"


@pytest.mark.xfail(strict=True, reason="FIND-TOOL1/A3: sin isConcurrencySafe — el fan-out del turno corre en SERIE (declarado en contracts/tools.py:6-9)")
async def test_concurrency_safe_tools_run_in_parallel_within_a_turn():
    """CONDUCTA (`H-L4`): dos tools concurrency-safe del mismo turno deben SOLAPARSE.

    La versión anterior era `isinstance(t.is_concurrency_safe, (bool, type(lambda: None)))`
    sobre el doble: aserción tan laxa que casi cualquier atributo la satisface, y encima
    medía `_FakeTool`. El canónico particiona el fan-out por `isConcurrencySafe` (default
    diez en paralelo, `CG-TOOL-CONC`); B corre en serie **declarado y no fingido**. Se mide
    el efecto: con dos llamadas de 0,20 s, en paralelo el turno cuesta ~0,2 s y en serie ~0,4 s.
    """
    import time

    from agentic_runtime.context.tool_use import AppState
    from agentic_runtime.events import DoneEvent, ToolCallEvent

    class _Lento(_FakeTool):
        def __init__(self):
            super().__init__("Lento")
            self.is_concurrency_safe = True

        async def execute(self, input, ctx):
            await asyncio.sleep(0.20)
            return ToolResult(tool_name=self.name, output="ok")

    from agentic_runtime.loop.agent_loop import AgentLoop
    from agentic_runtime.tools import ToolRegistry

    reg = ToolRegistry()
    reg.register(_Lento())

    class _DosLlamadas:
        def __init__(self):
            self.n = 0

        async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
            self.n += 1
            n = self.n

            async def _gen():
                if n == 1:
                    yield ToolCallEvent(call_id="c1", tool_name="Lento", tool_input={})
                    yield ToolCallEvent(call_id="c2", tool_name="Lento", tool_input={})
                    yield DoneEvent(stop_reason="tool_use")
                else:
                    yield DoneEvent(stop_reason="stop")

            return _gen()

    loop = AgentLoop(
        model_caller=_DosLlamadas(), tool_registry=reg, tool_dispatcher=ToolDispatcher(),
    )
    ctx = ToolUseContext(session_id="s1", app_state=AppState(permissions=PermissionContext()))
    t0 = time.monotonic()
    await loop.run("hola", ctx)
    transcurrido = time.monotonic() - t0
    assert transcurrido < 0.35, (
        f"las dos tools concurrency-safe corrieron en serie ({transcurrido:.2f}s ≈ 0,40s)"
    )


@pytest.mark.xfail(strict=True, reason="FIND-TOOL2=GAP-02: el gate de permisos no ve el input ni aplica check_permissions por-tool")
def test_dispatcher_calls_per_tool_check_permissions():
    """Homologado: una tool con checkPermissions que niega ciertos inputs debería bloquear.
    Hoy el gate sólo mira requires_permission + nombre en allowed_names, nunca el input."""
    class _Guarded(_FakeTool):
        def __init__(self):
            super().__init__("Guarded")
            self.requires_permission = True

        async def check_permissions(self, input, ctx):  # homologado esperado
            return {"behavior": "deny"} if input.get("danger") else {"behavior": "allow"}

    ctx = _ctx(tool_pool=ToolPool(native_tools=[_Guarded()]))
    # con allowed_names vacío pero check_permissions que permitiría → hoy el dispatcher deniega por nombre
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Guarded", tool_input={"danger": False}, ctx=ctx))
    assert not r.is_error  # homologado: check_permissions permite → ejecuta


@pytest.mark.xfail(strict=True, reason="FIND-TOOL4/A23: ToolResult no transporta new_messages — una tool no puede inyectar mensajes en la conversación")
async def test_new_messages_from_a_tool_reach_the_conversation():
    """CONDUCTA (`H-L4`): los mensajes que produce una tool deben APARECER en `ctx.messages`.

    La versión anterior era `isinstance(r.new_messages, list)` —FIRMA—: añadir el atributo
    con default `[]` la habría puesto XPASS mientras el loop lo ignora por completo, o sea
    la deuda entera intacta. El punto de `new_messages` es que el modelo LEA lo inyectado;
    eso es lo que se asevera.
    """
    from agentic_runtime.context.tool_use import AppState
    from agentic_runtime.events import DoneEvent, ToolCallEvent
    from agentic_runtime.loop.agent_loop import AgentLoop
    from agentic_runtime.tools import ToolRegistry

    marca = "INYECTADO-POR-LA-TOOL"

    class _Inyecta(_FakeTool):
        def __init__(self):
            super().__init__("Inyecta")

        async def execute(self, input, ctx):
            return ToolResult(
                tool_name=self.name,
                output="ok",
                new_messages=[{"role": "user", "content": marca}],
            )

    reg = ToolRegistry()
    reg.register(_Inyecta())

    class _UnaLlamada:
        def __init__(self):
            self.n = 0

        async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
            self.n += 1
            n = self.n

            async def _gen():
                if n == 1:
                    yield ToolCallEvent(call_id="c1", tool_name="Inyecta", tool_input={})
                    yield DoneEvent(stop_reason="tool_use")
                else:
                    yield DoneEvent(stop_reason="stop")

            return _gen()

    loop = AgentLoop(model_caller=_UnaLlamada(), tool_registry=reg, tool_dispatcher=ToolDispatcher())
    ctx = ToolUseContext(session_id="s1", app_state=AppState(permissions=PermissionContext()))
    await loop.run("hola", ctx)
    assert any(marca in str(m.get("content", "")) for m in ctx.messages), (
        "la tool produjo new_messages y no llegaron a la conversación"
    )


def test_tool_result_carries_context_modifier():
    """`FIND-TOOL4/A24` PAGADO — `ToolResult` declara `context_modifier`.

    La aserción anterior (`... and r.context_modifier is not None` sobre un resultado
    desnudo) exigía algo que el canónico **no** hace: `Tool.ts:330` declara
    `contextModifier?: (context: ToolUseContext) => ToolUseContext`, opcional, luego
    ausente = `undefined`. Homologado = el miembro EXISTE, defaultea a `None`, y
    transporta el modifier cuando la tool lo produce.
    """
    assert ToolResult(tool_name="x", output="ok").context_modifier is None

    def modifier(c):
        return c

    r = ToolResult(tool_name="x", output="ok", context_modifier=modifier)
    assert r.context_modifier is modifier
    sentinel = object()
    assert r.context_modifier(sentinel) is sentinel  # aplicable, no sólo presente


def test_tool_result_carries_ends_turn_as_declared_b_extension():
    """`ends_turn` declarado en el contrato — **extensión de B, no espejo de A**.

    `endsTurn` no existe en el canónico: `AskUserQuestionTool.call()` devuelve sólo
    `data` y las respuestas vuelven en el MISMO turno vía
    `checkPermissions → behavior:'ask' + updatedInput`. Esa capa es `GAP-02`/`K1`,
    por encima de la línea de corte; hasta que entre, B cede el turno con este cable.
    """
    assert ToolResult(tool_name="x", output="ok").ends_turn is False
    assert ToolResult(tool_name="x", output="ok", ends_turn=True).ends_turn is True


def test_abort_reason_reaches_the_result():
    """`FIND-TOOL5/SIG10` **PAGADO** — CONDUCTA, con la CAUSA localizada y ajustada.

    Dije que el gap era «la señal de abort es binaria». **Falso**: `contracts/abort.py`
    define `AbortReason` y `AbortController` **deriva `aborted` de la razón** justamente
    para cerrar `SIG2`; la señal lleva el motivo desde que existe ese contrato. El gap real
    es un eslabón más abajo y es de una línea: `dispatcher.py:54-55` consulta
    `ctx.stop.aborted` y devuelve `ToolResult.aborted(tool_name)` **tirando el
    `ctx.stop.reason()` que tiene disponible en la línea anterior**.

    Contraste (`D-08`): A usa `signal.reason` como dato de primera clase — lo fija al
    abortar (`abort('interrupt')`, `abort('sibling_error')`, `abort('user-cancel')`,
    `abort('background')`) y lo lee para decidir qué cancelar y con qué motivo
    (`StreamingToolExecutor.ts:213-229`: `streaming_fallback` · `sibling_error` ·
    `user_interrupted` · `null`). Perder la razón en el resultado es CORE-GAP, no
    divergencia.

    **Ajuste aplicado** (`dispatcher.py` + `ToolResult.aborted`): la razón se propaga al
    resultado y al `output`, que es lo único que el modelo lee. `interrupt_behavior` NO se
    ajustó: `contracts/tools.py:3-6` lo declara **fuera del tramo 1**, y el contraste no
    autoriza a colarlo por la puerta de atrás.

    Se asevera con dos causas REALES y distintas, que es lo que hace la prueba honesta.
    """
    from agentic_runtime.contracts.abort import AbortReason

    def _abortar(razon):
        ctx = _ctx(tool_pool=ToolPool(native_tools=[_FakeTool("Bash")]))
        ctx.stop.abort(razon)
        r = asyncio.run(ToolDispatcher().dispatch(tool_name="Bash", tool_input={}, ctx=ctx))
        assert r.is_aborted
        return r

    interrumpido = _abortar(AbortReason.USER_INTERRUPT)
    matado = _abortar(AbortReason.AGENT_KILLED)

    # 1) la razón que la señal SÍ llevaba tiene que sobrevivir al resultado
    assert getattr(interrumpido, "reason", None) == AbortReason.USER_INTERRUPT, (
        f"el dispatcher tiró la razón: resultado sin `reason`, output={interrumpido.output!r}"
    )
    # 2) y dos causas distintas tienen que ser DISTINGUIBLES por el campo
    assert interrumpido.reason != matado.reason

    # 3) y también por el `output`, que es lo ÚNICO que el modelo lee. Sin esto la
    #    prueba es un falso negativo: comparar la tupla `(reason, output)` pasa en
    #    verde con el `output` idéntico, porque basta con que difiera el `reason`.
    #    Lo cazó INY-44' (vaciar el sufijo del `output` no ponía el test en rojo).
    assert AbortReason.USER_INTERRUPT.value in interrumpido.output, (
        f"la razón no llega al texto que ve el modelo: {interrumpido.output!r}"
    )
    assert AbortReason.AGENT_KILLED.value in matado.output
    assert interrumpido.output != matado.output


# `FIND-TOOL6/E6` PAGADO (11ª ventana): `select:` multi-nombre homologado contra
# `ToolSearchTool.ts:363-406`. El `xfail(strict=True)` se retiró porque XPASSeó — que es
# exactamente para lo que estaba puesto.
def test_tool_search_select_multi():
    from agentic_runtime.tools.native.tool_search import ToolSearchTool

    tools = [_FakeTool("Read", deferred=True), _FakeTool("Edit", deferred=True), _FakeTool("Grep", deferred=True)]
    ctx = _ctx(tool_pool=ToolPool(capability_tools=tools))
    r = asyncio.run(ToolSearchTool().execute({"query": "select:Read,Edit,Grep"}, ctx))
    import json

    matched = {m["name"] for m in json.loads(r.output)["matches"]}
    assert matched == {"Read", "Edit", "Grep"}  # homologado: coma-separado


# ---------------------------------------------------------------------------
# `GAP-TOOLSEARCH-1` — lenguaje de consulta de A, homologado y medido por CONDUCTA.
# Canónico: `ToolSearchTool.ts:186-302` (keyword) y `:363-406` (select).
# ---------------------------------------------------------------------------

def _buscar(tools, query, **kw):
    """Ejecuta ToolSearch de verdad sobre un pool y devuelve los nombres hallados."""
    import json as _json

    ctx = _ctx(tool_pool=ToolPool(capability_tools=tools))
    from agentic_runtime.tools.native.tool_search import ToolSearchTool

    r = asyncio.run(ToolSearchTool().execute({"query": query, **kw}, ctx))
    return [m["name"] for m in _json.loads(r.output)["matches"]]


def test_tool_search_select_partial_success_and_dedupe():
    """`:383-405`: un nombre inexistente NO anula la selección, y los repetidos no duplican.
    Es lo que evita que un nombre alucinado tire abajo una selección buena."""
    tools = [_FakeTool("Read", deferred=True), _FakeTool("Edit", deferred=True)]
    assert _buscar(tools, "select:Read,NoExiste,Read,Edit") == ["Read", "Edit"]


def test_tool_search_select_falls_back_to_already_loaded_tool():
    """`:374-375`: si el nombre no está entre las diferidas pero SÍ en el pool completo, se
    devuelve igual — «a harmless no-op that lets the model proceed without retry churn»."""
    tools = [_FakeTool("Read", deferred=True), _FakeTool("Bash", deferred=False)]
    assert _buscar(tools, "select:Bash") == ["Bash"]


def test_tool_search_bare_name_without_select_prefix():
    """`:199-204`: nombre desnudo sin `select:` — atajo para modelos que lo omiten."""
    tools = [_FakeTool("Read", deferred=True), _FakeTool("Edit", deferred=True)]
    assert _buscar(tools, "read") == ["Read"]  # case-insensitive


def test_tool_search_bare_name_falls_back_to_already_loaded_tool():
    """`:200-201`: el atajo de nombre desnudo mira PRIMERO las diferidas y luego el pool
    completo. La primera versión de este test usaba una tool que ya era diferida, así que
    no medía la caída al set completo: INY-49 salió VERDE y ese fue el hallazgo."""
    tools = [_FakeTool("Read", deferred=True), _FakeTool("Bash", deferred=False)]
    assert _buscar(tools, "bash") == ["Bash"]


def test_tool_search_mcp_prefix_matches_server():
    """`:208-216`: `mcp__servidor` devuelve las tools de ese servidor."""
    tools = [
        _FakeTool("mcp__slack__send_message", deferred=True),
        _FakeTool("mcp__slack__list_channels", deferred=True),
        _FakeTool("mcp__github__create_issue", deferred=True),
    ]
    assert set(_buscar(tools, "mcp__slack")) == {
        "mcp__slack__send_message",
        "mcp__slack__list_channels",
    }


def test_tool_search_required_term_filters_out_non_matching():
    """`:220-257`: `+término` es REQUISITO, no peso. Sin él la consulta devolvía las dos."""
    tools = [
        _FakeTool("mcp__slack__send_message", deferred=True),
        _FakeTool("mcp__github__send_dispatch", deferred=True),
    ]
    assert _buscar(tools, "+slack send") == ["mcp__slack__send_message"]
    assert set(_buscar(tools, "slack send")) == {
        "mcp__slack__send_message",
        "mcp__github__send_dispatch",
    }


def test_tool_search_name_part_outranks_description_match():
    """`:271-290`: coincidir en el NOMBRE (10/12) pesa más que en la descripción (2)."""
    por_nombre = _FakeTool("NotebookEdit", deferred=True)
    por_descripcion = _FakeTool("Other", deferred=True)
    por_descripcion.description = "edits a notebook cell"
    assert _buscar([por_descripcion, por_nombre], "notebook") == ["NotebookEdit", "Other"]


def test_tool_search_hint_outranks_description():
    """`Tool.ts:373-378` + `:283-289`: el `search_hint` curado puntúa +4, la descripción +2.

    El hint se lee opcional (`getattr`): `contracts/tools.py:5` deja `search_hint` fuera del
    contrato T1 y esto NO lo asciende — homologa el mecanismo de ranking, no el miembro.
    """
    con_hint = _FakeTool("Alpha", deferred=True)
    con_hint.description = "generic tool"
    con_hint.search_hint = "jupyter notebook execution"
    con_desc = _FakeTool("Beta", deferred=True)
    con_desc.description = "works with jupyter files"
    assert _buscar([con_desc, con_hint], "jupyter") == ["Alpha", "Beta"]


def test_tool_search_description_match_uses_word_boundary():
    """`:171` + `:288`: frontera de palabra. Sin ella «read» puntúa dentro de «already» y la
    búsqueda devuelve ruido."""
    ruido = _FakeTool("Alpha", deferred=True)
    ruido.description = "this is already done"
    assert _buscar([ruido], "read") == []


@pytest.mark.xfail(strict=True, reason="GAP-TOOL3/E1: is_deferred_tool sin precedencia alwaysLoad (opt-out)")
def test_always_load_opts_out_of_deferral():
    t = _FakeTool("mcp__x__y", deferred=True)
    t.always_load = True  # homologado: alwaysLoad gana sobre isMcp/shouldDefer
    assert is_deferred_tool(t) is False


@pytest.mark.xfail(strict=True, reason="FIND-TOOL9/G8: ConfinedFilesystem no protege archivos peligrosos (.bashrc/.git/settings.json) dentro del workspace")
def test_confined_fs_blocks_dangerous_files_inside_workspace(tmp_path):
    (tmp_path / ".bashrc").write_text("x")
    fs = ConfinedFilesystem(roots=[tmp_path])
    # homologado (checkPathSafetyForAutoEdit): editar .bashrc dentro del workspace debería bloquearse
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(tmp_path / ".bashrc"), for_write=True)


# GAP-02 (mitad de contrato) pagado por C1 del tramo 1. El motor = `K1`, sin tocar.
def test_permission_context_has_mode():
    pc = PermissionContext()
    assert pc.mode in ("default", "acceptEdits", "plan", "bypassPermissions")
