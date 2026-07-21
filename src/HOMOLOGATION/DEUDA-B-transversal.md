# Deuda B · remediación transversal (sin hogar por subsistema)

**Qué es Deuda B.** El tablero maestro (01-18) alberga la **Deuda A**: gaps que pertenecen a UN
subsistema y se remedian en su doc (p.ej. los `FIND-NATIVE-*` viven en `10-tools-native.md`). Pero el
esfuerzo destapó gaps **transversales**: no son de un subsistema, son de la **forma en que los
subsistemas se conectan** (el protocolo de tool, la primitiva de cancelación, el canal de mensajes, el
gate de permisos). Esos gaps quedaban **sin hogar** — citados en 06/08/09/10 pero remediables sólo de
forma coordinada. Este doc es su hogar.

**Regla de esta pasada.** Diseño, no código (1ª pasada). Cada ítem: **síntesis del gap** (con sus IDs de
origen) · **remediación desarrollada** (comportamiento · seam · firma/campos · cableado · orden) ·
**dueño** (subsistemas que tocan) · **test** (xfail que lo codifica, si existe). Los `xfail(strict=True)`
de las suites de homologación ya fijan los targets; cuando uno empiece a pasar, es la señal de
reclasificar la celda de origen.

**Grafo entre ítems de Deuda B.**
`B-new_messages` desbloquea Read-image/pdf (10·A3) y Brief (10·K). `B-signals` absorbe a `B-orphans`
(SignalBus es uno de los tres huérfanos). `B-structured-output` habilita SyntheticOutput (10·K). `B-02`
(permisos) y `B-concurrency` son independientes. `B-usage` es autocontenido.

Orden sugerido: **B-orphans → B-signals → B-new_messages → B-structured-output → B-concurrency → B-02 → B-usage**
(los primeros limpian/unifican primitivas; los últimos enriquecen).

---

## B-02 · GAP-02 / GAP-TOOL1 — `check_permissions` por-tool + modos + input al gate

- **Síntesis**: el gate del runtime es **deny-por-nombre** (`dispatcher.py:62-65`: `tool_name in
  allowed_names()`), sin ver el **input** ni el path, sin **modos** (default/acceptEdits/plan/bypass), sin
  el `checkPermissions(input)` por-tool que el canónico lleva inline (Bash: la torre `bashPermissions`/
  `bashSecurity`/`readOnlyValidation`, ~9K LOC; Edit/Write: `checkWritePermissionForTool` +
  `preparePermissionMatcher` + `backfillObservableInput`). El **PreToolUse** del loop (§J de 10;
  `agent_loop.py:300-313`) transporta `block`/`modified_input` → **matiza** GAP-02 pero **no lo cierra**:
  no hay decisión tipada por-tool con modos ni el input entra al gate del dispatcher. Origen:
  09·TOOL2/GAP-02, 06·HOOK3 (gate lossy), 10·A11/B4/B7.
- **Remediación**:
  - **Comportamiento**: cada tool puede aportar `check_permissions(input, ctx) -> PermissionDecision`
    (`allow`/`deny`/`ask`, con `matcher`/`reason`); el dispatcher lo invoca **con el input completo**
    ANTES de `execute`, y respeta el **modo** activo (acceptEdits salta el ask de Edit/Write; plan bloquea
    escrituras; bypass salta todo). Bash deriva `is_read_only(input)` y sólo escala permiso en comandos no
    read-only (parseo/prefix-rules como **política inyectable**, no re-implementada en cada tool).
  - **Seam**: (a) miembro **opcional** en `ToolProtocol` — `check_permissions: Callable | None` (las tools
    que no lo definen conservan el deny-por-nombre actual, backward-compatible). (b) `PermissionContext`
    (contracts) gana `mode: PermissionMode` + resolución `decide(tool, input, mode) -> PermissionDecision`.
    (c) para Bash, seam `ctx.command_policy: CommandPolicy | None` (la torre de seguridad como valor
    inyectable — el integrador aporta el AST-parse/prefix-rules; el runtime no la re-implementa, Regla 1).
  - **Firma**: `@dataclass PermissionDecision(behavior: Literal["allow","deny","ask"], reason: str="",
    matcher: str="")`; `PermissionMode = Literal["default","acceptEdits","plan","bypassPermissions"]`.
  - **Cableado**: `dispatcher._run`, tras resolver la tool y ANTES de `execute`: si la tool define
    `check_permissions`, invocarlo con `(validated_input, ctx)`; combinar con el modo; `deny`→
    `ToolResult.error`, `ask`→ (server-side) ceder a HITL vía `ends_turn`/evento. El PreToolUse del loop
    sigue como **segundo** gate (hook del integrador), no se sustituye.
  - **Orden**: tras `B-structured-output` no requerido; independiente. Grande — dividir en (1) el miembro
    opcional + modos, (2) el `command_policy` de Bash.
- **Dueño**: 06 (hooks/permission), 09 (protocol/dispatcher), 10 (Bash/Edit/Write). GAP-02 sigue abierto
  hasta cerrar (1)+(2).
- **Test**: sin xfail dedicado hoy; se codificaría `test_dispatch_consults_check_permissions` +
  `test_bash_readonly_skips_permission`.

## B-orphans · seams huérfanos — `modes/` (FIND-MODE1), `observer/` (FIND-EXEC4), `SignalBus` (FIND-SIG1), `tasks.get/set_registry` (LAT-EXEC1), `NativeToolRegistry` (FIND-TOOL10), `ToolProtocol.category` (LAT-TOOL1), `HookRunner.run additional_context` (LAT-HOOK1), `McpServerConfig.auth_headers()` (LAT-MCP1), `SkillTool.input_schema.args` (LAT-SKILL1), `ModelsConfig.extras`/`ModelRequest` (LAT-MODELS1)

> **Convergencia confirmada en 18 (2ª vuelta · gate 11/L09, 2026-07-20):** el ensamblador `factory.py` 267 se leyó
> **1→EOF** y se comprobó por lectura + AUSENCIA que **`_build_local` NO consume ninguno de estos seams**
> (`config.models`/LAT-MODELS1 grep `\.models`=0 lecturas; `observer`/`modes`/`SignalBus`/`NativeToolRegistry`/
> `get_registry` grep en factory.py=vacío; `task_registry` por inyección de instancia :224). Es la prueba de que
> son huérfanos/costuras B-internas, no cableado A↔B pendiente — anti-padding L10. Las decisiones de abajo
> (borrar/cablear) siguen vigentes.

- **Síntesis**: varios seams implementan maquinaria que **ninguna ruta real consulta** — sólo sus propios
  tests los tocan:
  1. `modes/ModeManager` (`register/get_mode/set_mode/unregister`) — 04·D3: ni loop, ni
     `LocalAgentRuntime`, ni resolver, ni factory lo instancian. El "modo" real es un flag del ctx
     (foreground/background/fork resuelto en 04/05).
  2. `execution/observer/` (`on_subagent_*`) — 05·EXEC4: nadie llama `on_subagent_started/stopped`; el eje
     real de observabilidad es **EventBus + hook SUBAGENT_STOP**.
  3. `signals/SignalBus`/`SignalType`/`SignalHandle` — 08·SIG1: implementa el árbol de cascada
     (`ABORT/PAUSE/RESUME`, `send(cascade=True)`) pero la cancelación real es `ctx.stop` (`asyncio.Event`);
     además **conflaciona** dos cascadas distintas (árbol de controllers in-turn vs kill de tasks).
  4. `execution/tasks/registry.py::get_registry/set_registry` (singleton de módulo) — **LAT-EXEC1**
     (05·re-visita gate 11, 2026-07-19): ni productor ni consumidor en producción; `LocalAgentRuntime`
     toma su registry por **inyección de instancia** (`__init__(task_registry=…)` runtime.py:86, default
     `InMemoryTaskRegistry`), nunca por el global. Hermano exacto de `observer/`. *(Distinto del global
     `get_runner`/`set_runner`, que SÍ tiene consumidor — agent.py:105 — y cuyo productor falta = FIND-EXEC1,
     un seam roto, no un huérfano.)*
  5. `tools/native_registry.py::NativeToolRegistry` — **FIND-TOOL10** (09·re-visita gate 11, 2026-07-19):
     cero consumidores de producción (grep: sólo `tools/__init__.py` export + `test_runtime_contracts.py`);
     el registry cableado es `ToolRegistry` (`factory.py:189`→`runtime._tool_registry`→`loop:92`
     `list_available` + `resolver.py:46`). Sus métodos `unregister`/`unregister_by_prefix` (pensados para
     hot-plug MCP) no los usa nadie: el hot-plug real es por **reensamblado del pool por turno** (11). El
     canónico no tiene `NativeToolRegistry` ⇒ extensión sin contraparte. Hermano exacto de `observer/`.
  6. `tools/protocol.py::ToolProtocol.category` (enum `ToolCategory` 5 valores) — **LAT-TOOL1** (09·re-visita
     gate 11, 2026-07-19): campo **requerido** que las 25 tools nativas **setean**, pero **ningún código de
     prod lo LEE** (grep de lectura = 0). Slot de clasificación muerto. El canónico no usa este enum como
     driver de comportamiento (sus clasificadores `isReadOnly`/`isDestructive` SÍ se consumen, pero son otra
     cosa y ya están en A6/A7 ❌ = deuda A↔B distinta). No es deuda A↔B: tech-debt B-interno.
  7. `capabilities/mcp/config.py::McpServerConfig.auth_headers()` — **LAT-MCP1** (11·re-visita gate 11,
     2026-07-19): construye el header `Authorization: Bearer …` pero **ningún código de prod lo LEE** (grep:
     sólo `test_cap_mcp_homologation.py` + `test_mcp_config_contract.py`). La ruta VIVA del bearer es la
     estrategia de auth `_build_bearer` (auth.py:73-75) → `AuthArtifacts.headers` → merge en `client.connect`
     (client.py:106). `auth_headers()` es un **duplicado muerto** de esa lógica. El canónico no usa este método
     como driver de headers ⇒ tech-debt B-interno, NO deuda A↔B. *(Primos menores no elevados: `McpServerConfig.
     model` per-server 0 lectores de prod; `McpState.pending_servers()` accesor integrator-facing — slots
     pasivos / superficie de API, no maquinaria duplicada.)*
  8. `capabilities/skills/skill_tool.py::SkillTool.input_schema.args` — **LAT-SKILL1** (12·re-visita gate 11,
     2026-07-20): el `input_schema` **anuncia** la propiedad `args` (skill_tool.py:83-89) pero `execute()` lee
     **sólo** `input.get("command")` (:108) y `render_skill(skill)` no acepta args (:18) — el `args` anunciado se
     **descarta en silencio**. Costura a medio cablear: la tool promete en su PROPIO schema un manejo de args que
     no entrega. Es la superficie **B-interna** de FIND-SKILL4 (el gap A↔B — sin substitución `$ARGS`/`$N`/vars ni
     bash-injection — se sostiene ❌ como deuda A↔B). Gemela del announce singular de 09·FIND-TOOL6. **Distinto de
     los otros huérfanos: NO se borra** — se **cablea** vía SkR3 (`render_skill(skill, args, ctx)` + substitución),
     que es justo la remediación de FIND-SKILL4. Es "a medio cablear", no "duplicado muerto".
  9. `factory.ModelsConfig.extras` + `RuntimeConfig.models` (+ `models/protocol.py::ModelRequest`/`thinking_budget`) —
     **LAT-MODELS1** (16·re-visita gate 11, 2026-07-20): dos slots muertos de la misma familia. (a) `ModelsConfig.extras`
     (factory.py:59-60) + el campo `RuntimeConfig.models` (:83) están **declarados** pero `_build_local` (178-240,
     leído 1→EOF) **NUNCA los consume** (grep prod = 0; el `get_model`/`register_builtins` de `caller.py:110-113` está
     dentro del docstring). El integrador arma su `model_caller`/`Model` directamente; el factory nunca registra los
     modelos extra en el registro de `agentic_models`. (b) `ModelRequest`/`ModelRequest.thinking_budget` (protocol.py:12-18)
     = **tipo muerto** (0 consumidores prod, sólo def + re-export `__init__.py`); el loop llama `complete(messages, tools,
     stop, model_id, system_sections, system_override)` directo, nunca construye un `ModelRequest`. `ModelRequest` es además
     la **cara B-interna de FIND-MODELS1** (thinking no cableado, deuda A↔B que se sostiene). El canónico no tiene ni
     `ModelsConfig` (su registro de modelos es `utils/model/*`) ni `ModelRequest` ⇒ extensión sin contraparte = tech-debt
     B-interno, NO deuda A↔B. Hermano exacto de LAT-EXEC1/`NativeToolRegistry`/`category`.
  10. `hooks/runner.py::HookRunner.run` — agregación de `additional_context` sin consumidor — **LAT-HOOK1**
     (06·re-visita gate 11, 2026-07-19): `run()` **agrega** el `additional_context` de todos los handlers
     (`runner.py:54-55/59`) pero **ningún código de prod lo LEE** — el gate PreToolUse del loop
     (`agent_loop.py:307-313`) sólo honra `modified_input`+`block`, y `_fire_stop` descarta la `HookDecision`.
     Maquinaria a medio cablear: la agregación existe muerta. Es la **cara B-interna de FIND-HOOK3** (el gate lossy
     = deuda A↔B que se sostiene ❌). **Gemelo exacto de LAT-SKILL1** (item 8): NO se borra — se **cablea** vía
     **HR5** (que hace al gate consumir `additional_context` + `behavior` allow/ask/deny), la remediación de
     FIND-HOOK3. "A medio cablear", no "duplicado muerto". *(Primo menor no elevado, misma familia:
     `context/presentation.py::PathPresentation.to_llm` — sin call site de prod (01/03), `sanitize_output` SÍ
     cableado; slot pasivo homed en 03, no requiere decisión transversal.)*
- **Remediación** (decisión, no sólo diseño): los **duplicados-muertos se ELIMINAN**, absorbiendo lo poco
  recuperable; los **seams a-medio-cablear (LAT-SKILL1→SkR3, LAT-HOOK1→HR5) se CABLEAN** vía su remediación de
  categoría, NO se borran:
  - `ModeManager` → **borrar**; el modo es un campo/enum del ctx resuelto por 04/05. No hay comportamiento
    canónico que reproduzca.
  - `observer/` → **borrar**; su superficie la cubren EventBus (07) + hook `SUBAGENT_STOP` (06). Si se
    quiere un observer tipado, que sea un **suscriptor del EventBus**, no un registry paralelo.
  - `execution/tasks/registry.py::get_registry/set_registry` (LAT-EXEC1) → **borrar** el par global; el
    registry ya viaja por inyección de instancia (`RuntimeConfig.task_registry` → `LocalAgentRuntime.__init__`).
    El `TaskRecord`/`InMemoryTaskRegistry`/`TaskRegistryProtocol` **se conservan** (sí se usan); sólo se retira
    el singleton `_registry` + sus `get/set`.
  - `SignalBus` → **fusionar** en la primitiva única de `B-signals` (abajo). Lo recuperable (la idea de
    árbol con direccionalidad) se realiza allí como `AbortScope`; el `SignalBus` como clase se borra.
  - `NativeToolRegistry` (LAT-TOOL1-hermano) → **DECISIÓN RESUELTA CON 11 (gate 11, 2026-07-19): borrar.**
    El hot-plug MCP se confirmó **por reensamblado del pool por turno** (leyendo el ensamblador: `factory.
    _build_capability_manager` → `capability_manager` compartido → `agent_loop.py:194-195` re-arma el pool cada
    turno → `McpProvider.tools()` re-lee `McpState`), **NO** por registro dinámico. `NativeToolRegistry` (0
    consumidores de prod) queda huérfano ⇒ **borrar**. ÚNICA excepción: si se implementa el swap push-based del
    auth-tool de FIND-MCP4/McR2 (needs-auth), `NativeToolRegistry.unregister_by_prefix(f"mcp__{srv}__")` sería
    su seam — sólo entonces se cablea; mientras tanto, huérfano a borrar. NO mantener los dos registries.
  - `ToolProtocol.category` (LAT-TOOL1) → **borrar el campo** (o darle un consumidor real si el integrador
    lo necesita para filtrado/telemetría). Hoy es peso muerto en el contrato mínimo de 8 miembros.
  - `McpServerConfig.auth_headers()` (LAT-MCP1) → **borrar el método** (duplicado muerto del bearer): la ruta
    viva es la estrategia `_build_bearer`→`AuthArtifacts`. Los tests que lo ejercitan se re-apuntan a
    `build_auth`/`_build_bearer` o se borran con él. (Primos `model`/`pending_servers()`: dejar como superficie
    de API o limpiar en el mismo barrido.)
  - `ModelsConfig.extras`/`RuntimeConfig.models` + `ModelRequest` (LAT-MODELS1) → **borrar** ambos (o dar a
    `ModelsConfig.extras` un consumidor real en `_build_local`: `register_builtins()` + registrar cada `Model` extra en
    el registro de `agentic_models` antes de construir el runtime, si el integrador lo necesita). Hoy son peso muerto:
    el `model_caller` se inyecta ya armado (con su `Model`), y el loop llama `complete()` directo sin `ModelRequest`.
    Los tests que ejercitan `ModelRequest` se re-apuntan a `complete()` o se borran con él.
  - `SkillTool.input_schema.args` (LAT-SKILL1) y `HookRunner.run additional_context` (LAT-HOOK1) → **NO borrar,
    CABLEAR**: son seams a-medio-cablear cuya agregación/announce ya existe pero sin consumidor; se completan vía la
    remediación de su categoría (**SkR3** = `render_skill(skill, args, ctx)`+substitución; **HR5** = gate PreToolUse
    que consume `additional_context`+`behavior`). Distintos de los duplicados-muertos de arriba: aquí completar el
    cableado ES cerrar el ❌ A↔B del que son la cara B (FIND-SKILL4 / FIND-HOOK3).
  - **Por qué borrar (los duplicados-muertos) y no cablear**: cablear un huérfano-muerto añade un segundo mecanismo
    que hay que mantener coherente con el real (el mismo modo de fallo que ya sufre 08 con dos cascadas). La
    homologación es de **comportamiento observable**, y el comportamiento ya lo dan las rutas reales. *(No aplica a
    LAT-SKILL1/LAT-HOOK1: allí NO hay mecanismo real duplicado — la ruta está incompleta, y cablearla es la
    remediación.)*
- **Dueño**: 04 (modes), 05 (observer + `tasks.get/set_registry` LAT-EXEC1), 06 (`HookRunner.run additional_context`
  LAT-HOOK1 → cablear vía HR5), 08 (SignalBus), 09 (`NativeToolRegistry` FIND-TOOL10 — **decisión resuelta con 11:
  borrar** — + `ToolProtocol.category` LAT-TOOL1), 11 (`McpServerConfig.auth_headers()` LAT-MCP1), 12
  (`SkillTool.input_schema.args` LAT-SKILL1 → cablear vía SkR3), 16 (`ModelsConfig.extras`/`ModelRequest` LAT-MODELS1).
  Son "hermanos exactos del mismo patrón" (08·SIG1 lo nombra).
- **Test**: `test_no_orphan_modemanager_in_real_path` / `..._observer` / `..._signalbus` —
  asserts de que ninguna ruta de producción importa/instancia estos módulos (guard anti-regresión), o su
  eliminación (los tests unitarios de los huérfanos se borran con ellos).

## B-signals · unificar `ctx.stop` + `SignalBus` en UN `AbortScope` (reason + árbol + interruptBehavior)

- **Síntesis**: DOS mecanismos paralelos y desconectados (08): `ctx.stop` (`asyncio.Event`, el REAL,
  cableado end-to-end pero **degradado**: binario, sin `reason`, sin árbol, sin `interruptBehavior`) y el
  `SignalBus` huérfano. Origen: FIND-SIG1/2/3/3b/4/5/6/7/10/11/12, 09·TOOL3/TOOL5.
- **Remediación**:
  - **Comportamiento**: una primitiva única de cancelación en el ctx que (a) lleve `reason`
    (`'interrupt'`/`'sibling_error'`/`'user'`), (b) sea un **árbol con direccionalidad** (el hijo aborta
    sin abortar al padre; espejo `createChildAbortController`), (c) exponga `interrupt()` público, (d)
    consulte `interrupt_behavior()` por-tool (`'cancel'` mata en vuelo / `'block'` espera).
  - **Seam**: sustituir `ctx.stop: asyncio.Event | None` por `ctx.abort: AbortScope`. `AbortScope` en
    `signals/scope.py` (reemplaza `signals/bus.py`).
  - **Firma**: `class AbortScope: reason: str | None; def is_aborted() -> bool; def interrupt(reason:str);
    def child() -> AbortScope (direccional: aborta hacia abajo, no hacia arriba); def wait() (compat con
    el await de `asyncio.Event`)`. `ToolProtocol.interrupt_behavior: Literal["cancel","block"] = "cancel"`.
  - **Cableado**: `agent_loop` (checks pre-modelo 173/186 y pre-tool), `caller`/`agentic_models`
    (propaga `abort.reason` a la señal HTTP), `dispatcher` (`ToolResult.aborted(reason=…)`; hoy 08·SIG10 lo
    da sin razón), `fork` (usa `abort.child()` en vez de compartir el Event — cierra FIND-SIG3). El
    **disparo** del abort (quién llama `interrupt()`) sigue siendo del integrador (HITL) — correcto.
  - **Orden**: tras `B-orphans` (absorbe el SignalBus). Prerrequisito de nada más, pero mejora la calidad
    del abort que consumen dispatcher/fork.
- **Sub-ítem SIG9 · cleanup / liberación de recursos al abortar mid-turn** (añadido tras la auditoría de
  deuda; desarrollado en 08·SR3): al abortar en medio de un turno hay que **liberar locks/recursos** (MCP
  unhide + release; `cleanupComputerUseAfterTurn` ⛔). Firma: `AbortScope.on_abort(callback)` que corre los
  callbacks en LIFO al `interrupt()`; los subsistemas que toman recursos (11·mcp) registran su release.
  Cableado: 11 registra el cleanup; el loop/dispatcher lo dispara al detectar abort. Test:
  `test_abort_runs_cleanup_callbacks`.
- **Sub-ítem SIG13 · dos niveles de abort (`work` vs `agent`)** (añadido tras la auditoría; desarrollado en
  08·SR4): un task tiene DOS controllers — `currentWorkAbortController` (corta el TURNO, el agente sigue
  vivo → recibe `SendMessage`-continue) vs `abortController` (mata al agente). El scope de un nivel no lo
  modela. Firma: `AbortScope.work` / `AbortScope.agent`; `interrupt(level="work"|"agent", reason=…)`. El
  loop chequea `abort.work`; el registry `kill` usa `abort.agent`. Habilita 05·EXEC12 (drenar
  pendingMessages tras `work`-abort SIN matar al agente). Test: `test_work_abort_keeps_agent_alive`.
- **Dueño**: 08 (primitiva), 09 (dispatcher/protocol `interrupt_behavior`), 02/05 (loop/fork), 11 (cleanup
  SIG9), 16 (corte HTTP).
- **Test**: `test_abort_carries_reason`, `test_child_scope_directional` (hijo aborta sin tocar al padre),
  `test_tool_interrupt_behavior_block` (una tool `'block'` no se mata en vuelo), + SIG9/SIG13 arriba.

## B-new_messages · canal de mensajes tipados tool→historial (`ToolResult.new_messages`)

- **Síntesis**: el loop **sólo appendea `result.output`** (texto, `agent_loop.py:319-323`); no hay canal
  para que una tool inyecte **mensajes tipados** (bloques `image`/`document`) al historial. Es la **causa
  raíz** de que Read no pueda portar image/pdf (10·A3: el canónico los entrega **inyectando `newMessages`**
  con `createUserMessage`) y de que Brief no tenga forma nativa. Origen: 09·A23/D7/TOOL4, 10·A3/K(Brief).
  **Nota**: `context_modifier`/`ends_turn` SÍ se aplican (CORR-09, §J de 10) — lo que sigue ❌ es SÓLO
  `new_messages`.
- **Remediación**:
  - **Comportamiento**: una tool puede devolver mensajes tipados que el loop **appendea al historial** tras
    el `output` (o en su lugar), con bloques `text`/`image`/`document`. Read los usa para image/pdf/notebook;
    Brief para la entrega proactiva.
  - **Seam**: **declarar** `new_messages` en `ToolResult` (`protocol.py`) — hoy incluso
    `context_modifier`/`ends_turn` se cuelgan por `getattr` dinámico (`# type: ignore`, frágil, §J de 10);
    esta es la ocasión de tipar los tres campos de extensión juntos.
  - **Campos**: `ToolResult(..., new_messages: list[Message] | None = None)` (+ formalizar
    `context_modifier`/`ends_turn` como campos tipados en vez de attrs dinámicos).
  - **Cableado**: `agent_loop` (283-352), tras leer `output`: si `result.new_messages` → `ctx.messages`
    los recibe con el rol/bloques correctos (invariante tool_use↔tool_result intacto, FIND-L1). Read
    construye `new_messages` con bloque `image`/`document`; el dispatcher/presentation los deja pasar.
  - **Orden**: temprano dentro de Deuda B (desbloquea 10·A3 y Brief).
- **Dueño**: 09 (protocol), 02 (loop), 10 (Read image/pdf, Brief).
- **Test**: `test_tool_result_new_messages_appended` (una tool que devuelve `new_messages` los ve en
  `ctx.messages`); habilitaría el des-xfail futuro de un `test_read_returns_image_block`.

## B-concurrency · dispatch paralelo de tools concurrency-safe (`is_concurrency_safe`)

- **Síntesis**: el dispatcher es **secuencial** (`dispatcher.py`: una tool por `dispatch`), sin
  `isConcurrencySafe`/`isReadOnly` a nivel de tool → el canónico corre en paralelo los tool_calls
  read-only de un mismo turno; el runtime no. Origen: 09·TOOL1/FIND-TOOL1, 10·A2/A13.
- **Remediación**:
  - **Comportamiento**: el loop, ante N `tool_calls` en un turno, agrupa los **consecutivos
    concurrency-safe** y los despacha con `asyncio.gather`; los no-safe (Edit/Write/Bash-mutante) van
    secuenciales, preservando el orden observable (homólogo de `runToolsConcurrently`/`runToolsSerially`).
  - **Seam**: (a) `ToolProtocol.is_concurrency_safe(input) -> bool` (default: `False`, salvo Read/Glob/
    Grep/WebFetch/WebSearch → `True`; derivable de `is_read_only`). (b) el dispatcher gana
    `dispatch_many(calls, ctx)` que particiona por safety y hace gather del bloque safe.
  - **Firma**: `is_concurrency_safe: Callable[[dict], bool] | bool`; `async def dispatch_many(...)
    -> list[ToolResult]`.
  - **Cableado**: `agent_loop` deja de iterar 1-a-1 y delega en `dispatch_many`; el pairing
    `call_id↔result` (FIND-L1) se mantiene por índice.
  - **Orden**: independiente; tras `B-signals` conviene (para que un abort mid-gather propague por
    `AbortScope`).
- **Dueño**: 09 (protocol/dispatcher), 02 (loop), 10 (flags per-tool Read/Glob/Grep).
- **Test**: `test_dispatch_many_runs_safe_in_parallel` (dos Read concurrentes solapan en el tiempo),
  `test_unsafe_tools_serialized`.

## B-usage · `Usage` con cache-tokens + acumulación cross-turn

- **Síntesis**: `events/event_types.py::Usage` sólo tiene `input_tokens`/`output_tokens`/`thinking_tokens`;
  **falta** `cache_creation_input_tokens`/`cache_read_input_tokens`, y **no se acumula** entre turnos
  (`DoneEvent.usage` es por-turno, sin agregado de sesión). Origen: 07·FIND-EVT1 = 02·FIND-L2, 07·EVT5
  (Usage duplicado/pobre).
- **Remediación**:
  - **Comportamiento**: `Usage` refleja los cinco campos de la API (input/output/thinking + cache_creation
    + cache_read); la `Session` (05) mantiene un **acumulado** que se incrementa por turno; `DoneEvent`
    puede llevar tanto el delta del turno como el acumulado.
  - **Seam**: extender el dataclass `Usage` (07) + un `Session.usage_total: Usage` (05) con `+=` (definir
    `__add__`). El caller (16) mapea los cinco campos del response de `agentic_models`.
  - **Campos**: `Usage(input_tokens, output_tokens, thinking_tokens, cache_creation_input_tokens=0,
    cache_read_input_tokens=0)` + `def __add__(self, other) -> Usage`.
  - **Cableado**: `caller` puebla los cinco; `agent_loop`/`Session` acumula al cerrar el turno; `DoneEvent`
    lo emite (07·EVT5 pide un único canal de Usage, no duplicado).
  - **Orden**: autocontenido; en cualquier momento.
- **Dueño**: 07 (Usage/DoneEvent), 05 (Session acumulado), 16 (mapeo del response).
- **Test**: `test_usage_has_cache_fields`, `test_session_accumulates_usage` (dos turnos → total = suma).

## B-structured-output · salida tipada de tool (`output_schema` + `ToolResult.structured`)

- **Síntesis**: los `ToolResult` devuelven **str plano** (`"Edited {path}"`, `str(path)`, stdout crudo);
  el canónico tiene `outputSchema` por-tool + `structuredPatch`/`gitDiff`/`type:create|update`
  (Edit/Write), `stdout/stderr/returnCodeInterpretation/backgroundTaskId` (Bash), y el
  `SyntheticOutputTool` de salida final estructurada. Origen: 09·A15/A22, 10·A12/B5/K(SyntheticOutput), G3.
- **Remediación**:
  - **Comportamiento**: una tool puede declarar `output_schema` y devolver, además del `output` humano, un
    `structured` tipado (validado). SyntheticOutput fija el `final_output` estructurado del agente.
  - **Seam**: (a) `ToolProtocol.output_schema: dict | None`. (b) `ToolResult(..., structured: dict |
    None = None)`. (c) el mapeo a `tool_result` del provider (16) adjunta el structured cuando existe.
  - **Campos**: Edit/Write → `{type, structured_patch, git_diff}`; Bash → `{stdout, stderr,
    return_code_interpretation, background_task_id}` (liga B12 de 10 + el motor de background 05·EXEC9/10).
  - **Cableado**: cada tool rellena `structured`; el dispatcher/loop lo transportan sin aplanarlo;
    SyntheticOutput usa `context_modifier` (que YA se aplica, §J de 10) para el `final_output`.
  - **Orden**: tras `B-new_messages` (comparten la formalización del `ToolResult`); habilita SyntheticOutput.
- **Dueño**: 09 (protocol/ToolResult), 10 (Edit/Write/Bash structured, SyntheticOutput), 16 (mapeo provider).
- **Test**: `test_tool_result_carries_structured`, `test_synthetic_output_sets_final_output`.

---

## Recuento y cierre de Deuda B

| Ítem | IDs de origen | Dueño(s) | xfail hoy | Estado |
|---|---|---|---|---|
| B-02 permisos | GAP-02/TOOL1, HOOK3, A11/B4/B7 | 06·09·10 | no | abierto |
| B-orphans | FIND-MODE1·EXEC4·SIG1·LAT-EXEC1·FIND-TOOL10·LAT-TOOL1·**LAT-HOOK1**·LAT-MCP1·LAT-SKILL1·LAT-MODELS1 | 04·05·06·08·09·11·12·16 | no | decisión: **duplicados-muertos borrar/fusionar** (NativeToolRegistry resuelto con 11=borrar) · **seams a-medio-cablear CABLEAR** (LAT-SKILL1→SkR3, LAT-HOOK1→HR5) |
| B-signals | FIND-SIG1-12, TOOL3/5 | 08·09·02·05·16 | no | diseño listo |
| B-new_messages | A23/D7/TOOL4, 10·A3/Brief | 09·02·10 | no (habilita futuros) | diseño listo |
| B-concurrency | FIND-TOOL1, A2/A13 | 09·02·10 | no | diseño listo |
| B-usage | FIND-EVT1=L2, EVT5 | 07·05·16 | no | diseño listo |
| B-structured-output | A15/A22, A12/B5/G3, SyntheticOutput | 09·10·16 | no | diseño listo |

**Por qué "sin hogar" y no repartido en 01-18**: cada ítem toca ≥2 subsistemas y su remediación es una
**forma compartida** (el `ToolResult`, la primitiva de abort, el gate). Repartirlo por subsistema
fragmentaría el diseño y reintroduciría el modo de fallo de los tres huérfanos (mecanismos paralelos que
divergen). Deuda B es el contrato de coordinación; se implementa como una tanda, no celda a celda.

**Relación con Deuda A**: los `FIND-NATIVE-*` de 10 son Deuda A (hogar en `10-tools-native.md` §"Plan de
homologación / remediación desarrollada"). Deuda B los **habilita** donde hay dependencia:
`B-new_messages`→10·A3 (Read image/pdf) y 10·Brief; `B-structured-output`→10·SyntheticOutput y 10·A12/B5;
`B-02`→10·A11/B4 (Bash security). R11 de 10 **eleva** aquí la conflación tasklist/registry (G1), cuya
resolución completa (store de tasklist homólogo de `utils/tasks.ts`) es Deuda B-adyacente pero ⛔ en su
dimensión team/swarm por el corte del README.
