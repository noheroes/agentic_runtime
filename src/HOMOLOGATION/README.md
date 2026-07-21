# Homologación `agentic_runtime` ← canónico (`claude-code/src`)

Documento vivo. Contrasta **característica por característica** lo que `agentic_runtime`
ya porta contra el proyecto canónico (TypeScript/JavaScript, `/home/noheroes/python/claude-code/src`),
del cual `agentic_runtime` extrae el *core* desacoplado.

> **Alcance**: solo el **core** (loop, contexto, tools, capabilities, storage, modos, hooks,
> events, execution, models, voice, contratos). UI/TUI/ink, entrypoints CLI, componentes React
> y todo lo ligado a la terminal quedan **fuera** — el canónico opera en terminal sin usuarios ni
> sesiones; el runtime debe soportar usuarios y sesiones, así que ahí la homologación es *de comportamiento*,
> no de forma.

## Metodología

1. **Top-down por subsistema** (no por el bundle `main.tsx`). Cada subsistema que el runtime ya declara
   se compara contra su(s) contraparte(s) canónica(s).
2. Por subsistema, un archivo propio (`<subsistema>.md`) con una tabla feature-by-feature.
3. Cada feature lleva un **estado** y, si no está homologado, la **diferencia** y el **ajuste** que lo llevaría a ✅.
4. **Exhaustividad (obligatoria)**: las contrapartes canónicas se leen **íntegras**, sin saltarse tramos por
   "tamaño". El grep orienta pero NO sustituye la lectura completa. Se enumera **cada** feature de la
   contraparte, no una muestra. La lectura parcial ya costó omisiones (p. ej. `yieldMissingToolResultBlocks`
   en 02·loop, un invariante de API que la lectura "por hitos" pasó por alto). La superficialidad es el modo
   de fallo #1 de este esfuerzo.

## Leyenda de estados

| Estado | Símbolo | Significado |
|---|---|---|
| Homologado | ✅ | Comportamiento equivalente al canónico verificado. |
| Parcial | 🟡 | Existe pero incompleto (faltan casos, flags, ramas). |
| Diferente | 🔀 | Existe pero opera distinto (decisión deliberada o divergencia a revisar). |
| No homologado | ❌ | No portado. |
| Pendiente | ⬜ | Inventariado; comparación contra canónico aún no realizada. |
| N/A core | ⛔ | Fuera de alcance (UI/terminal) — se documenta por qué. |

## Fase actual: **2ª VUELTA (validación · gate 11/L09) COMPLETA — 01→18 VALIDADOS**

> **2ª vuelta de validación (gate 11 / L09) — COMPLETA 2026-07-20.** Los **18 subsistemas** quedaron re-verificados
> abriendo el código de B de cada ✅/🔀 (no confirmando el doc) y re-leyendo el lado A 1→EOF esta ronda; **18·factory
> (categoría de CIERRE)** cerró la vuelta confirmando por lectura del ensamblador que el núcleo se cablea en ruta real
> y que **el factory nunca consume ningún §B-orphan** (incl. el más fresco `config.models`/LAT-MODELS1 de 16). El
> saldo de la vuelta: **CERO cambios de estado de código**; sólo precisiones de mecanismo/observable y costuras
> latentes B-internas (to_llm/timeout_seconds/category/LAT-EXEC1/LAT-HOOK1/LAT-MCP1/LAT-SKILL1/LAT-MODELS1) homed en
> `DEUDA-B §B-orphans`. Detalle por categoría en `PROGRESS.md`. **Siguiente (fuera del bucle 01→18): re-visita de
> 2ª pasada de `DEUDA-B-transversal.md` si aplica** (los §B-orphans ya quedaron confirmados-convergentes en 18).

## Fase (1ª pasada): **COMPARACIÓN COMPLETA (01-18) + Deuda B homed**

Los **18 subsistemas** tienen doc con estado, §Plan de remediación desarrollada (por finding:
comportamiento·seam·firma·cableado·orden·test) y ledger honesto con columna "Lectura"; la **Deuda B**
transversal tiene sus 7 hogares con diseño listo. La **§Síntesis final del tablero** vive en `18-factory.md`
(todos los cabos verificados con hogar). Siguiente fase (no iniciada): **implementación** de las remediaciones
diseñadas (hoy codificadas como `xfail(strict)` en los `test_*_homologation.py` — passing = homologado).
Este README sigue siendo el mapa de verificación: enumera lo que el runtime declara y dónde está su contraparte.

## Tablero maestro

> **Dos deudas.** **Deuda A** = gaps que pertenecen a UN subsistema → se remedian en su doc (01-18).
> **Deuda B** = gaps **transversales** (tocan ≥2 subsistemas; son la *forma* en que se conectan: el
> `ToolResult`, la primitiva de abort, el gate de permisos) → hogar propio en `DEUDA-B-transversal.md`.
> El diseño de remediación (1ª pasada = diseño, no código) vive: Deuda A de **01-10** en cada
> `NN-<sub>.md` §"Plan de homologación / remediación desarrollada" (desarrollada por finding:
> comportamiento · seam · firma · cableado · orden · test); Deuda B en `DEUDA-B-transversal.md`.
> **Estado**: **01-18 COMPLETOS** con remediación desarrollada; Deuda B homed (incl. SIG9/SIG13 en B-signals tras la auditoría;
> FIND-MEM9 scope-sanitize + FIND-MEM12 carve-out-escritura aterrizan en B tras 13). Tras 14:
> FIND-PLAN4 (candado read-only plan mode + exención plan-file) aterriza en **B-02**; FIND-PLAN3
> (agentes built-in Explore/Plan) + FIND-PLAN7 (fork hereda plan) aterrizan en **05·execution**;
> FIND-PLAN-APPROVAL-CONTRACT (modo-resultante/clear-context/feedback/auto-name) → **front**. Tras 16
> (hogares verificados existentes): FIND-MODELS2 (Usage tira cache-tokens) → **B-usage**+07·EVT1;
> FIND-MODELS4 (abort roto asyncio.Event) → **B-signals**+08; FIND-MODELS5/6/7 (retry/fallback) →
> **02·loop** motor #2 (+07·J3 api_retry); FIND-MODELS10 (error-taxonomy colapsada a str) → **07·events D5**
> (`ErrorEvent.code`=enum-7-val); FIND-MODELS11 (overflow.py sin cablear) → **02·loop** ruteo + seam
> **01·contracts** `CompactionProvider`; FIND-MODELS8 (beta tool-search) → **09**. Tras 17 (voice, borde de
> I/O): core STT audio→prompt homologado; TTS = **superset** sin contraparte (canónico STT-only, verificado);
> motor STT → **integrador**, terminal/keybindings/`/voice`/gating → **front**; único gap **FIND-VOICE1**
> (saneo TTS per-chunk se evade en frontera de chunk) homable **dentro de 17** (VoR1, reusa `PathPresentation`
> de 01/03; sin cabo transversal nuevo). Tras 18 (factory/ensamblado, ÚLTIMO subsistema, **punto de convergencia**):
> el núcleo del ensamblado está cableado (verificado abriendo `factory.py`+`runtime.py` 1→EOF); el gap crítico
> **C1=FIND-EXEC1** (el factory nunca llama `set_runner()` → subagentes revientan) converge aquí con hogar en
> **05·ExR1**; las caras-factory pendientes **C2**(memoria→Stop)/**C3**(built-ins al resolver)/**C4**(frame `init`)
> tienen hogar en **13/14/07**; **C5**(user_id a stores)→15, **C6**(WorkerStateUploader)→18/integrador; Deuda A
> propia de 18 = **FaR1**(sin fail-fast de inyecciones) + **FaR2**(resolver legacy cableado muerto). El
> `18-factory.md` incluye la **§Síntesis final del tablero 01-18**: todos los cabos verificados con hogar.

| # | Subsistema (runtime) | Contraparte canónica (dónde buscar) | Estado | Archivo |
|---|---|---|---|---|
| 01 | `contracts` | seams inventados: `AgentTool`, `alwaysAllow`/`acceptEdits`, `services/compact`, `commands.ts` | 🟡 doc (**valid. 2ª vuelta + re-visita L09 ✅**) | `01-contracts.md` (✅4·🟡6·🔀3·❌1 · **re-visita completitud L09 2026-07-18: feat15 `timeout_seconds` NO inerte — cableado a `arm_watchdog` (runtime.py:149), default no-op ⇒ tech-debt B-interno L10; feat11 `to_llm` sin call site prod (=03·context) tech-debt B-interno, `sanitize_output` sí cableado; feat14 `max_turns` inerte→05·FIND-EXEC5; autogen user/sess runtime.py:208-209; +bloque L09+§honestidad ampliada**) |
| 02 | `loop` | `query.ts`, `QueryEngine.ts`, `query/{config,deps,stopHooks,tokenBudget}.ts` | 🟡 doc (**valid. 2ª vuelta ✅ + re-visita L09 ✅**) | `02-loop.md` (✅7·🟡**11**·🔀**8**·❌15·⛔11 · gaps L1-L4/C4/G1 + FIND-L2 · E3/G2/G3 resueltos · **re-visita completitud L09 2026-07-18: abiertos los consumidores de cada ✅/🔀 (dispatcher, productores de context_modifier/ends_turn, cancel→kill→asyncio_task); C11/FIND-L1 reclasificado 🟡→🔀 (invariante pareo garantizado por buffer-then-commit; break-por-error precede persistencia — no bug); mini-ledger de consumidores + §honestidad + 4 preguntas**) |
| 03 | `context` | `context.ts`, `Tool.ts` (ToolUseContext), `state/AppStateStore.ts`, `forkedAgent.ts` | 🟡 doc (**valid. 2ª vuelta ✅**) | `03-context.md` (✅~14·🟡~11·🔀~10·❌~9·⛔… · FIND-CTX1 read-file-state + GAP-CTX2/3/4 · **2ª vuelta: Tool.ts(792)+AppStateStore.ts(569)+context.ts(189) releídos 1→EOF; los 4 archivos de `context/` íntegros; `ToolUseContext` A1-A33 enumeración íntegra confirmada; `PermissionContext` sin `mode` y `ForkSnapshot` sin read_file_state/rendered_system_prompt verificados; cableado `subagent_depth`/`is_subagent` seguido a 05·runtime.py:204/315/316 (E8 ✅ no sobre-declarado); 3 xfail(strict) con anclas exactas; VALIDADA SIN DISCREPANCIA sustantiva; ledger+§honestidad+4 preguntas añadidos**) |
| 04 | `modes` | `coordinator/coordinatorMode.ts`, backgrounding (`tasks/`, `useSessionBackgrounding`) | 🟡 doc (**valid. 2ª vuelta + L09 de ENTRADA ✅**) | `04-modes.md` (A⛔5·B✅1/🔀3/🟡1/⛔2·C🔀1/🟡1/✅1·D❌4/🔀2 · FIND-MODE1 modes/ huérfano + GAP-MODE1/2 · **valid. L09 2026-07-19: abiertos los CONSUMIDORES reales del backgrounding (registry.py/notification.py/resolver.py íntegros); FIND-MODE1 confirmado por cableado — `modes/` importado sólo por 2 tests, `_notify` incondicional (runtime.py:294-304 sin `on_complete`); GAP-MODE1 `TaskRecord` sin `kind`; GAP-MODE2 sub-enumerada→4 ítems (worktree+AgentTool+TaskStop+TaskOutput) contra `ASYNC_AGENT_ALLOWED_TOOLS`+BLOCKED-block→10·R10; +mini-ledger de consumidores+§honestidad+4 preguntas**) |
| 05 | `execution` | `tasks/`, `Task.ts`, `tasks.ts`, `AgentTool`, `services/AgentSummary` | 🟡 doc (**valid. 2ª vuelta gate 11 ✅**) | `05-execution.md` (✅8·🟡9·🔀9·❌9 · FIND-EXEC1 runner sin cablear + EXEC2 fork sin filtrar + EXEC3/4/5/8 + GAP-EXEC1-7 · **re-audit +EXEC9** promoción fg→bg **+EXEC10** seam force-async(kairos) **+EXEC11** reaping recursos hijos **+EXEC12** pendingMessages/SendMessage-a-vivo · corr. initialPrompt · **re-visita gate 11 2026-07-19**: ✅/🔀 sostenidos abriendo B (E2/E6/E8/E10/E20/E29 cableados; E24/E16/E25 ❌ re-confirmados por factory+agent_loop 1→EOF); **+LAT-EXEC1** registry-global huérfano (hermano observer) **+LAT-EXEC2** drain notif. integrator-delegated (E5 matiz) — ambos tech-debt B-interno L10, NO deuda A-vs-B; código intacto) |
| 06 | `hooks` | `schemas/hooks.ts`, `hooks/toolPermission/`, `query/stopHooks.ts` | 🟡 doc (**valid. 2ª vuelta gate 11 ✅**) | `06-hooks.md` (✅6·🟡12·🔀14·❌20·⛔6 · FIND-HOOK1 taxonomía 11/**27** + HOOK2 2/11 disparados + HOOK3 gate lossy + HOOK6 Stop no portado + HOOK7 salida pobre · GAP-02 sigue abierto · **re-audit utils/hooks.ts íntegro: HOOK_EVENTS=27 no 28; +HOOK8 dos-motores executeHooks/OutsideREPL; +HOOK9/10/11; lista de ~15 ejecutores omitidos completada** · **re-visita gate 11 2026-07-19**: `hooks/{protocol,runner,__init__}.py` íntegros 1→EOF; **FIND-HOOK2 confirmado por cableado** — únicos `.run(HookEvent…)` de prod = PreToolUse `agent_loop.py:301` + SubagentStop `runtime.py:289` (`_fire_stop` invocado 384/391/406), los otros 9 = enum muerto; **FIND-HOOK3/6 re-confirmados**; `HookRunner` inyectado por consumidor (factory.py:86→225→runtime→362, NO huérfano); **+LAT-HOOK1** `run()` agrega `additional_context` sin consumidor de prod = tech-debt B-interno L10/L11 (pre-cablea HR5), NO deuda A-vs-B; código intacto) |
| 07 | `events` | `SDKMessageSchema` (24 variantes, `coreSchemas.ts`), `remote/sdkMessageAdapter.ts`, `ModelUsage` | 🟡 doc (**valid. 2ª vuelta gate 11 ✅**) | `07-events.md` (✅5·🟡8·🔀15·❌16·⛔4 · FIND-EVT1 usage no acumulado=FIND-L2 + EVT2 taxonomía 5/24 + EVT3 tres canales + EVT5 Usage duplicado/pobre + EVT6/EVT7 · GAP-EVT1-5 · re-audit: conteo 24 CONFIRMADO; +EVT9 init/handshake (F0 ❌); +D5 enum error 7-val; +K5 SDKSessionInfo→15 · **re-visita gate 11 2026-07-19**: los 9 archivos de B íntegros 1→EOF; tesis y ✅/🔀 sostenidos abriendo B; **2 correcciones de doc, código intacto** — (1) DISCREPANCIA: `Session.turn_count` NO es slot muerto (cableado ctx 189→session runtime.py:398→TaskRecord registry:148), SÓLO `usage`(tokens) lo es; FIND-L2 se sostiene; (2) REFINAMIENTO: `LocalAgentRuntime.stream()` runtime.py:153-181 ES el productor de canal único ordenado sobre `subscribe_all`, falta sólo el wire `Event→SDKMessage` (GAP-EVT5/EvR3); sin costuras latentes nuevas) |
| 08 | `signals` | abort/cancel (`AbortController`/`AbortSignal`, `createChildAbortController`, `StreamingToolExecutor`, `useCancelRequest`) | 🟡 doc (val 2ª vuelta gate 11 ✅) | `08-signals.md` (✅3·🟡3·🔀4·❌14·⛔1 · **gate 11 2026-07-19: ✅/🔀 sostenidos por cableado, 0 cambios de estado, precisión: arming de `ctx.stop` es del integrador `adapters.py:15`, NO del standalone `runtime.py:210/201`** · FIND-SIG1 SignalBus huérfano/conflaciona-2-cascadas + SIG2 sin reason + SIG3 fork sin direccionalidad + SIG4 sin interruptBehavior + SIG5 register_handler muerto + SIG6 PAUSE/RESUME mal ubicada + SIG10 aborted sin razón + SIG11 sin interruptible-state + SIG12 hooks no abort-aware · GAP-SIG1-3) |
| 09 | `tools` (infra) | `Tool.ts`, `tools.ts`, `tools/{shared,utils.ts}`, `ToolSearchTool` (deferred) | 🟡 doc (**valid. 2ª vuelta gate 11 ✅**) | `09-tools-infra.md` (✅~9·🟡~14·🔀~16·❌~18·⛔~6 · FIND-TOOL1 sin concurrencia/dispatcher secuencial + TOOL2=GAP-02 gate deny-por-nombre sin ver input + TOOL3=FIND-SIG4 interruptBehavior ausente + TOOL4 ToolResult sin new_messages/context_modifier + TOOL5 aborted sin reason(SIG10) + TOOL6 select: sin multi + TOOL7 delta parseando texto/discovered en state + TOOL8 exec sin shell persistente + TOOL9 sin safety-layer fs(G8) + TOOL10 dos registries · GAP-TOOL1=GAP-02 · GAP-TOOL2=GAP-MODE2 worktree bg · GAP-TOOL3 is_deferred sin alwaysLoad/isMcp · AÑADE NativeDeferredStrategy + ToolExecEnvironment) |
| 10 | `tools/native` | `tools/*Tool/` (uno a uno) | 🟡 doc (2ª vuelta ✅ gate 11) | `10-tools-native.md` (25 tools vs ~44 · ✅~10·🟡~12·🔀~14·❌~20·⛔~8 · **2ª vuelta gate 11 2026-07-19: VALIDADA sin discrepancia — 19 nativos + ensamblador `agent_loop.py:283-352` leídos 1→EOF, cada ✅/🔀 abierta en B, `context_modifier`/`ends_turn` confirmados CABLEADOS (no sólo atributo), E4 `safe_for_background` tabulado celda a celda, LAT-TOOL1(category) confirmado aterriza; cero cambios de estado/código** · **Bash/FileRead/tasks.ts releídos ÍNTEGROS tras reproche del usuario — el troceo ocultaba A3b números-de-línea/A3c device-guard(read /dev/zero colgaría)+binarios/A3d dedup/B9 sed-edit-readState/B10 onProgress/B11 preventCwd/B12 interpretCommandResult** · FIND-NATIVE-NAME 5 fs sin homologar nombre + READSTATE read_file no puebla readFileState + EDITGUARDS read-before-edit/modified/safety ausentes(=FIND-CTX1+G8) + READ sin img/pdf/notebook(nexo A23 new_messages) + BASH sin shell-persistente(=FIND-TOOL8)/bg + BG bool vs 2-allowlists(GAP-TOOL2 resuelto) + TASK conflación tasklist/registry-ejecución + WEB providers mínimos · **CORR-09: context_modifier/ends_turn SÍ se aplican(loop 329-348)** · GAP-NATIVE-1 read_file_state + GAP-NATIVE-2 safety-fs · Brief/SyntheticOutput/Notebook/LSP/Cron/RemoteTrigger ❌; SendMessage/Team*/PowerShell/REPL ⛔; MCP*→11 · **+§Plan de remediación desarrollada (Deuda A): R0 read_file_state→R11, cada FIND-NATIVE-* con comportamiento/seam/firma/cableado/orden/xfail; +§Implementación de tools no portadas Notebook/Brief/SyntheticOutput/LSP/Cron/RemoteTrigger**) |
| 11 | `capabilities/mcp` | `services/mcp`, `services/oauth`, `MCPTool`, `McpAuthTool`, `*McpResource*` | 🟡 doc (**valid. 2ª vuelta gate 11 ✅ — A+B re-verificados 1→EOF**) | `11-cap-mcp.md` (✅~11·🟡~6·🔀~4·❌~14·⛔~9 · **gate 11 2026-07-20 VALIDADA: lado B (12 mcp/*.py + ENSAMBLADOR factory/manager/dispatcher/fork) 1→EOF + lado A RE-VERIFICADO 1→EOF esta ronda (client.ts 3348 + config.ts 1578 + auth.ts 2465 + tratables) contra cada ❌/🔀 → CERO discrepancias, citas de línea de la 1ª pasada coinciden exactas, ⛔-de-forma confirmados por lectura L02; cero cambios de estado, código intacto; hot-plug per-turno CONFIRMADO por el ensamblador (loop:194-195→manager.tools→provider.tools cada turno; `NativeToolRegistry` 0-prod → RESUELVE "decidir con 11"=retirar); +LAT-MCP1 `auth_headers()` sin consumidor prod (dup muerto del bearer vivo `_build_bearer`→artifacts) = tech-debt B-interno→DEUDA-B §B-orphans; precisión: herencia MCP en fork por `capability_manager` compartido+`tool_pool` heredado, NO `app_state.capabilities`; FIND-MCP8 30s enforced por dispatcher:68+wait_for** · FIND-MCP1 naming `mcp__srv__tool`(=09·B4) + MCP2 `is_mcp` vs `deferred` a mano(=09·TiR5/GAP-TOOL3) + MCP3 annotations parciales + MCP4 needs-auth/pseudo-tool `authenticate`/caché + MCP5 transform image/audio/blob(=B-new_messages) + MCP6 solo `content`, sin structuredContent/mcpMeta(=09·A25/B-structured-output) + MCP7 large-output + MCP8 timeout 30s vs ~∞ + MCP9 sin reconexión/recuperación-sesión + MCP10 sin timeout-connect + MCP11 startup secuencial vs batched + MCP12 caps/instructions no capturados + MCP13 sin env-expansion + MCP14 sin política allow/deny + MCP15 sin aprobación-proyecto + MCP16 prompts→commands(→12) + MCP17 resource tools + MCP18 elicitation/roots + MCP19 cleanup por agent_id(=05·ExR6/08·SR3) + MCP20 keying-config-hash/revoke + **MCP21 sin `*_list_changed` refetch + MCP22 sin dedup-por-firma + MCP23 reconcile sobre-agresivo(vs scope dynamic) + MCP24 sin headersHelper** · cabos 09·TiR4 dos-registries **resuelto**(hot-plug por reensamblado per-turno) · 09·TiR3 fork **re-deriva**(provider vivo compartido) · 03·CtxR7/A13 **confirmado** · **+§Plan McR1-McR19** · +18 xfail · **RE-AUDITADO tras reproche de superficialidad: MCP21-24 destapados al ABRIR archivos antes marcados ⛔ sin leer (useManageMCPConnections/config:1-320/utils:185/headersHelper); ledger honesto con columna "Lectura"**) |
| 12 | `capabilities/skills` | `skills/{loadSkillsDir,bundledSkills,mcpSkillBuilders}`, `SkillTool`, motor `commands.ts`, `utils/skills/*`, `attachments`/`state` (skill_listing/invoked) | 🟡 doc (**valid. 2ª vuelta gate 11 ✅ — A+B re-verificados 1→EOF**) | `12-cap-skills.md` (✅~13·🟡~9·🔀~4·❌~19·⛔~7 · **gate 11 2026-07-20 VALIDADA (cierre en 3 iteraciones, 2 reproches del usuario): lado B 8 `skills/*.py` + ENSAMBLADOR (`factory.py` 1→267 + `manager` 1→112 + `loop:85-352`) 1→EOF; lado A los 10 in-scope RE-LEÍDOS 1→EOF esta ronda (SkillTool.ts 1108/loadSkillsDir.ts 1086/commands.ts 754/prompt.ts 241/bundledSkills.ts 220/skillChangeDetector.ts 311/registerSkillHooks 64/skillUsageTracking 55/mcpSkillBuilders 44/constants 1) → CERO discrepancias, citas exactas; cada ✅/🔀 abierta en B por cableado; 0 cambios de estado/código; SkillTool + `context_modifier`(loop:332) + `active_context`(loop:218) confirmados reensamblados per-turno (hermano MCP 11); PRECISIÓN FIND-SKILL9: `catalog()` 0-consumidores-prod (sólo tests) → seam de integrador, NO surface per-turno al modelo — ❌ vs canónico se sostiene (gap MAYOR); +LAT-SKILL1 `input_schema.args` anunciado y descartado por `execute` = tech-debt B-interno→DEUDA-B §B-orphans, a CABLEAR vía SkR3 no borrar** · FIND-SKILL1 fuente-única + SKILL2 frontmatter-reducido + SKILL3 dos-ejes(user-invocable≠disable-model) + SKILL4 sin substitución-args/vars/bash-injection + SKILL5 gate-permisos-ausente(=GAP-SKILL1/B-02) + SKILL6 fork-en-tool + SKILL7 modifier-sin-model/effort + SKILL8 output-vs-new_messages + SKILL9 catalog-re-emite-todo(vs skill_listing incremental+budget) + SKILL10 invoked_skills homologado(matiz cleanup-por-agent) + SKILL11 skill-hooks + SKILL12 condicionales/dinámicas(=GAP-SKILL3) + SKILL13 hot-reload + SKILL14 ranking + SKILL15 bundled + SKILL16 aliases/namespaced + SKILL17 filtro-elegibilidad + SKILL18 prompt + **SKILL19 getPromptForCommand=callable async ctx-aware** · **FIND-MCP16 aterriza aquí**(mcp__srv__prompt isMcp vs srv:skill loadedFrom mcp, resources-backed; builder mcpSkills.ts no-vendorizado) · +§Plan SkR1-SkR17 · +11 passing/19 xfail · **RE-AUDITADO tras reproche del usuario: la 1ª pasada marcó 13 bundled ⛔ por grep + infirió FIND-MCP16; al ABRIRLOS apareció SKILL19; ledger con §honestidad**) |
| 13 | `capabilities/memory` | `memdir/`, `services/extractMemories`, `tools/AgentTool/agentMemory*`; SessionMemory→01/compact; team→implementador | 🟡 doc (**valid. 2ª vuelta gate 11 ✅ — A+B re-verificados 1→EOF**) | `13-cap-memory.md` (✅~11·🟡~9·🔀~6·❌~7·⛔~10 · **gate 11 2026-07-20 VALIDADA: lado B (5 `memory/*.py`) + ENSAMBLADOR (`factory.py` 1→EOF + `manager.py` 1→EOF + `loop:85-234`) 1→EOF + lado A in-scope RE-LEÍDO 1→EOF esta ronda (extractMemories 615/memdir 507/memoryTypes 271/paths 278/memoryScan 94/findRelevantMemories 141/memoryAge 53/agentMemory 177) → CERO discrepancias, cero cambios de estado, código intacto; reensamblado PER-TURNO confirmado por el ensamblador (`system_prompt_section` re-lee índice + `_inject_recall`→`active_context` cada turno, hermano MCP/Skills); provider registrado CONDICIONAL (seam integrador factory:166-172); FIND-MEM10 confirmado por cableado (`agent_id`=uuid fresco por despacho runtime:205/fork:69 vs canónico `sanitizeAgentTypeForPath` estable); FIND-MEM1 por absencia (grep wiring extracción=vacío); FIND-MEM9 por seguir la clave cruda a `self._root/scope`; PRECISIÓN: fila-D `compact_context` 0-consumidores-prod → la equivalencia post-compact la da el recall PER-TURNO, no ese hook = cara aguas-abajo del motor-compactación ❌ ya conocido (01/02), NO nuevo B-orphan (anti-padding L10); cabos FIND-SKILL14/invoked-cleanup NO aterrizan; 18 passed** · FIND-MEM1 auto-extracción-por-fork ausente(canUseTool memory-scoped/cursor/exclusión-mutua/throttle/coalescing/drain) + MEM2 recall keyword vs LLM(recentTools/alreadySurfaced/manifiesto-tipado) + MEM3 sin caveat-frescura + MEM4 índice sin truncar(200/25k) + MEM5 scan no-recursivo/sin-cap/lee-entero + MEM6 frontmatter metadata.type-anidado vs plano+sin-validar-enum + MEM7 prompt recortado(taxonomía/ignore+drift/**Before-recommending-verificar**/plan-tasks/searching-past-context) + MEM8 sin gate + **MEM9 clave-scope sin-sanitizar=traversal(seguridad, destapado al abrir teamMemPaths)** + **MEM10 agent-memory keyed por agent_id-uuid vs por-TIPO(no persiste entre despachos)** + MEM11 quick-save `#` + MEM12 carve-out-escritura=GAP-02 · **SessionMemory+SM-compact→01/compact, team-sync→implementador(§I enumerado), ambos abiertos-íntegros y confirmados** · falso-positivo RAM(useMemoryUsage/MemoryUsageIndicator) descartado al abrirlo · +§Plan MeR1-MeR13 · 26 canónicos abiertos(5 mayores íntegros 1→EOF)) |
| 14 | `capabilities/plan` | `tools/{Enter,Exit}PlanModeTool`, `utils/{plans,planModeV2}.ts`, `built-in/{plan,explore}Agent.ts`, instrucciones/cadencia en `messages.ts`/`attachments.ts` | 🟡 doc (**valid. 2ª vuelta gate 11 ✅ — A+B re-verificados 1→EOF**) | `14-cap-plan.md` (**gate 11 2026-07-20 VALIDADA: lado B (3 `plan/*.py`+`plan_mode.py`) + ENSAMBLADOR (`factory.py`267/`manager.py`111/`agent_loop.py:85-234`/`execution/agents.py`66/`runtime.py:336-365`/`tools/factory.py`) 1→EOF + lado A in-scope RE-LEÍDO 1→EOF esta ronda (los 7 de código; el más grande `ExitPlanModeV2Tool.ts`493 + `plans.ts`397 íntegros; citas exactas=evidencia L11) → 1 DISCREPANCIA (FIND-PLAN1 sub-enumerado: `prompt()` ausente aplica a AMBAS tools, +fila B11+PlR1 ampliado) + 2 PRECISIONES (FIND-PLAN8 dedup `_inject_recall`:121-128 suprime sparse idéntico; FIND-PLAN6 `compact_context` 0-caller-prod=transversal-13); cero cambios de estado, código intacto; `PlanModeProvider` INCONDICIONAL factory:146, inyectado per-turno agent_loop:218 (hermano MCP/Skills/Memory); FIND-PLAN3 letra-muerta por cableado (`execution/agents.py` sin tabla built-ins + `agent_resolver=None`→fork genérico runtime:350-353, sin read-only); FIND-PLAN4 por ausencia (`is_session_plan_file` 0-consumidores-prod=cara-B-interna del ❌→B-02, no B-orphan)** · tabla A-H · FIND-PLAN1 prompt-no-portado + PLAN2 exit-sin-guard-de-modo + **PLAN3 agentes built-in Explore/Plan NO registrados → reminder 5-fases letra muerta(=05·agents)** + **PLAN4 candado read-only no-forzado, is_session_plan_file sin consumidor(→B-02)** + PLAN5 plan_mode_reentry no-portado + PLAN6 plan no-re-inyectado-tras-compact + PLAN7 fork no-hereda-plan(=05·fork) + PLAN8 cadencia sparse-cada-iter(sin throttle-5-turnos/full-cada-5ª) + PLAN9 interview-phase no-portado + PLAN10 counts-por-tier + PLAN11 exit tool_result empobrecido(sin isAgent/teamHint/edited/restore-modo) + PLAN12 subagent-reminder sin su plan-path + PLAN13 entrar-sin-aprobación + PLAN14 plan-tools no-diferidas · **CORR: A3 guard por is_subagent = MEJORA; B10 exit inlinea plan aprobado = enriquecido** · **FIND-PLAN-APPROVAL-CONTRACT**(modo-resultante/clear-context-and-implement/plan-feedback/auto-name → front+B-02) · ⛔-abiertos: /plan, /ultraplan(CCR ant-only), 2 permission-req + 3 msg-renderers ink · +§Plan PlR1-14 · 6 passing/6 xfail) |
| 15 | `storage` | `config.ts`(1817), `sessionStorage.ts`(5105)+`Portable`(793), `fsOperations.ts`(770), `settings/settings.ts`(1015), `env{,Utils}.ts`, `cachePaths.ts`, `filePersistence/`, `WorkerStateUploader.ts` | ✅ **VALIDADA (2ª vuelta · gate 11/L09) 2026-07-20** — B+ENSAMBLADOR `factory.py` 1→EOF, A RE-LEÍDA 1→EOF esta ronda (`env.ts` drift 341→347 parte no-storage), **CERO cambios de estado**, código intacto, 21 passed/10 xfailed; 2 precisiones cableado (STOR1: token_storage auto-cableado colisiona bajo scope `"mcp"` + skills/mcp-config NO auto-cableados; STOR12: `"anon"` = fallback muerto, `_build_child` siempre da uuid) + STOR6/plan_file-inerte(`ctx.storage` nunca bound=cara-B 14·FIND-PLAN4) confirmados por ensamblador; sin B-orphans nuevos | `15-storage.md` (✅3·🟡7·🔀9·**❌15**·⛔2 · **FIND-STOR1 taxonomía muerta: sólo `transcript_key` de 7 claves cableada; mcp/tokens/skills/plan inventan su esquema** + STOR2 snapshot-overwrite vs append-only(sin durabilidad mid-turn) + STOR3 plano meta mutable `session.meta.json` ausente(→05·resume/04·bg) + STOR4 sin persistencia de config(getConfig/saveConfigWithLock: lock/backups/#3117/atomic/watcher/migraciones) + STOR5 sin listado/enrich de sesiones(lite-stat/head-tail/progresivo) + **STOR6 solapamiento `StorageContract`(01/09) vs `StorageProtocol`(15) RESUELTO: dos roles, no fusionar, frontera+adaptador** + STOR7 guard `_path` prefix-startswith admite hermano-prefijo(=13·MEM9) + STOR8 perms umask vs 0700/0600 + STOR9 sin range/tail read + STOR10 work/ sin motor(scan+upload+skip-symlink/TOCTOU) + STOR11 upsert coalescente→18 + STOR12 fallbacks `anon`/`main` silenciosos + **STOR13 cascada settings.json 4+ niveles no portada(plugin→user→project→local→flag→policy; policy first-source-wins remote>MDM>managed>HKCU; invariante project-no-confiable=RCE, transversal 13)** · **cabos 01·solapamiento RESUELTO, 14·PLAN4/C4 confirmados, 09·fs_env, 13·MEM9** · +§Plan StR1-8 · 6 passing/10 xfail · **RE-AUDITADO 2026-07-14 (disparado por el usuario): la 1ª pasada difirió `settings.ts`(1015)/`outputsScanner.ts` sin abrirlos=fallo original de 11; al leerlos íntegros→STOR13 + enriq STOR10; §honestidad + ledger con Lectura**) |
| 16 | `models` | `services/api`, streaming/model call (delegado a `agentic_models`) | 🟡 doc (**valid. 2ª vuelta gate 11 ✅ — A+B re-verificados 1→EOF**) | `16-models.md` (✅6·🟡14·🔀3·❌11·⛔front · **gate 11 2026-07-20 VALIDADA: ENSAMBLADOR `factory.py` 1→EOF (cableado model_caller/small_llm/model_id; `config.models.extras` **NUNCA consumido**→LAT-MODELS1) + hilo usage seguido end-to-end (bridge caller:226→loop nunca lee done.usage→session.usage=0/0 runtime:403 = 07·FIND-EVT1) + lado A behavioral RE-LEÍDO 1→EOF ESTA ronda (claude.ts 3419+errors.ts 1207+withRetry.ts 822+client.ts 389+emptyUsage.ts 22) → CERO discrepancias, citas exactas; ✅/🔀 sostenidas abriendo B (A1/A7/A8 puente + B13 transform_messages + D1 superset); FIND-MODELS4 confirmado por lectura del provider (anthropic.py:450/717/732 `getattr(signal,"aborted")` vs `asyncio.Event`); cero cambios de estado, código intacto; +LAT-MODELS1 (`ModelsConfig.extras`+`ModelRequest` muertos)→DEUDA-B §B-orphans** · **puente `caller.py` no cablea thinking/usage/abort/error**: FIND-MODELS1 thinking muerto(ModelRequest/thinking_budget sin instanciar) + MODELS2 Usage tira cache-tokens(=07/B-usage) + MODELS3 thinking-events skip + MODELS4 abort roto(asyncio.Event vs `.aborted`→08/B-signals) + MODELS5/6/7 sin retry/fallback-529/fallback-non-streaming(→02·loop motor#2) + MODELS8 betas fijos(tool-search/effort ausentes→09) + MODELS9 sin structured-outputs + MODELS10 error-taxonomy colapsada a str(→07·D5 `ErrorEvent.code`) + MODELS11 overflow.py sin cablear(→02·loop+01·contracts CompactionProvider) · `agentic_models`=port de pi/ai multi-provider(939 modelos), superset sin contraparte canónica; provider Anthropic reproduce núcleo(SSE/betas/cache/thinking/usage+coste/pairing-repair/OAuth) ✅B13/14/17/A7 · +§Plan MoR1-8 · 8 xfail/4 passing · endpoints cuenta/billing/telemetría abiertos uno-a-uno→⛔front) |
| 17 | `voice` | `voice/`, `services/voice*`, `useVoice` | 🟡 doc (**valid. 2ª vuelta gate 11 ✅ — A+B re-verificados 1→EOF**) | `17-voice.md` (✅3·🔀5·❌1·⛔integrador+front · **gate 11 2026-07-20 VALIDADA: B (`voice/protocol.py`+cableado `_resolve_prompt`/`_wire_tts`+`test_voice_io.py`) 1→EOF + A re-leído 1→EOF ESTA ronda (useVoice.ts 1144+useVoiceIntegration.tsx 676→terminal/UI/motor, sin core oculto) + ausencia de TTS RE-VERIFICADA por barrido (0 hits); FIND-VOICE1 confirmado leyendo `_on_token` per-chunk; PRECISIÓN: FIND-VOICE1 es tech-debt B-interno/superset (no deuda A↔B — no hay TTS canónico), a CABLEAR vía VoR1 no borrar; cero cambios de estado, 0 costuras latentes nuevas, código intacto** · **core STT audio→prompt homologado**; canónico es **STT-only** (TTS del runtime = superset sin contraparte, verificado con grep) y **push-to-talk terminal** (motor STT=integrador, keybindings/prompt-input/`/voice`/gating=front, abiertos y clasificados) · **FIND-VOICE1** saneo TTS per-chunk se evade en frontera de chunk → **VoR1** buffer en límites seguros · 1 xfail/8 passing · Deuda A=1 ítem honesto, sin cabos transversales) |
| 18 | `factory` / ensamblado | `bootstrap/`, `setup.ts`, `entrypoints/` | ✅ **VALIDADA (2ª vuelta · gate 11/L09) 2026-07-20 — CIERRE de la 2ª vuelta** — ensamblador `factory.py` 267 releído **1→EOF esta ronda** seam por seam + **TODO el lado A del bootstrap RE-ABIERTO 1→EOF ESTA ronda** (`state.ts` 1758 · `setup.ts` 477 · `init.ts` 340 · `cli.tsx` 302 · `mcp.ts` 196), **CERO cambios de estado**, código intacto, **16 passed/3 xfailed(strict, sin xpass)**; **§B-orphans CONVERGEN — el factory NUNCA los consume** (confirmado por lectura + AUSENCIA: `config.models`/LAT-MODELS1 grep=0 lecturas · observer/modes/SignalBus/NativeToolRegistry/get_registry vacío); **precisión C1** (no voltea estado): el spawn no "revienta" — `agent.py:106` captura el `RuntimeError`→`ToolResult.error`, y `LocalAgentRuntime` no implementa `run(fork_ctx,*,background)` ⇒ C1 doblemente roto (sin `set_runner` + sin adaptador); FaR1/FaR2/FaR3 y C2/C3/C5 re-confirmados por lectura | `18-factory.md` (punto de **convergencia**, no features nuevas · ✅ núcleo cableado (storage/tools/capability-manager/presentation/exec_env/voice/lifecycle startup-shutdown/execution_mode) · **❌ C1=FIND-EXEC1 crítico**: `_build_local` nunca llama `set_runner()` → **todo spawn de subagente falla** (los tests lo llaman a mano); converge aquí, hogar 05·ExR1 · 🟡 C2 memoria→Stop(`setup.ts:294 initSessionMemory`) / C3 built-ins Explore-Plan al resolver / C4 frame `init` = caras-factory sin poblar (hogares 13/14/07) · C5 user_id a stores→15 · C6 WorkerStateUploader→18/integrador · C7-C10 **cerrados** · **§B-orphans convergen** (factory no consume ninguno; anti-padding L10)→`DEUDA-B §B-orphans` · **Deuda A propia = FaR1** sin fail-fast de inyecciones (canónico `enableConfigs:65`→`ConfigParseError:216`→`gracefulShutdownSync(1):224`) **+ FaR2** `CapabilitiesResolver` legacy cableado muerto (loop `agent_loop.py:194 if pool` siempre gana → `:201 elif` inalcanzable) + FaR3 ternario muerto cosmético · **factory.py 267 + runtime.py 435 + sub-factories + manager 1→EOF** · canónico `setup.ts` 477 + `init.ts` 340 + `state.ts` 1758 + `cli.tsx`/`mcp.ts` **RE-LEÍDOS 1→EOF esta ronda** (⛔-entrypoint/arquitectónico tras abrir L02) · **§Re-visita gate 11 + ledger + §honestidad + 4 preguntas + VEREDICTO** · **§Síntesis final del tablero 01-18**) |
| B | **deuda transversal** (sin hogar por subsistema) | forma compartida: `ToolResult`, primitiva de abort, gate de permisos, `Usage` | 🟡 diseño | `DEUDA-B-transversal.md` (B-02 permisos·B-orphans modes/observer/SignalBus→borrar/fusionar·B-signals AbortScope·B-new_messages·B-concurrency·B-usage cache-tokens·B-structured-output · cada uno con remediación desarrollada + dueño(s) + test) |

---

## Inventario detallado (mapa de verificación)

Para cada subsistema: features declaradas en el runtime → dónde comprobarlas en el canónico.

### 01 · contracts
Seams que el runtime *inventó* para desacoplar. La homologación aquí es **de comportamiento**: lo que el
contrato abstrae debe reproducir lo que el canónico hace inline.
- `contracts/runtime.py` → `RuntimeTask`, `AgentRuntime` (Protocol) — orquestación de una tarea de agente. Canónico: `query.ts`, `Task.ts`, `tasks/LocalMainSessionTask.ts`.
- `contracts/permissions.py` → `PermissionContext` — Canónico: `hooks/toolPermission/`, `useCanUseTool.tsx`, `canUseTool`.
- `contracts/compaction.py` → `CompactionProvider`, `collect_compaction_context` — Canónico: `services/compact`.
- `contracts/storage.py` → `StorageContract`, `PathPresentation` — Canónico: dispersa (escritura directa a FS/config).
- `contracts/user_input.py` → `UserInputProcessor`, `NoopUserInputProcessor` — Canónico: pre-proceso de input en `query`/commands.

### 02 · loop
- `loop/agent_loop.py` → `AgentLoop` (352 LOC, el corazón). Canónico: `query.ts` (68KB), `QueryEngine.ts` (46KB).
- `loop/basic.py`, `loop/factory.py` → `create_loop`.
- `loop/protocol.py` → `LoopProtocol`, `DrainableLoopProtocol`.
- Verificar contra: turno agente, streaming, tool-use dispatch, stop conditions (`query/stopHooks.ts`), token budget (`query/tokenBudget.ts`), config (`query/config.ts`), deps (`query/deps.ts`).

### 03 · context
- `context/tool_use.py` → `AppState`, `ToolUseContext`. Canónico: `Tool.ts` (tipo ToolUseContext), `context.ts`, `state/AppState.tsx`.
- `context/presentation.py` → `IdentityPresentation`.
- `context/adapters.py` → `tool_use_context_from_session`, `sync_session_from_tool_use_context`, `apply_context_modifier_compat`.

### 04 · modes
- `modes/protocols.py` → `AgentMode` (enum), `ModeManagerProtocol`.
- `modes/manager.py` → `ModeManager`.
- Modos declarados: foreground / background / fork. Canónico: `coordinator/coordinatorMode.ts`, backgrounding (`useSessionBackgrounding.ts`, `tasks/`).

### 05 · execution
- `execution/session/session.py` → `Session`, `SessionMetadata`, `Usage`, `BackgroundTaskRef`. Canónico: sesión no existe en canónico (sin usuarios) → **homologación de comportamiento**.
- `execution/agents.py` → `AgentDefinition`, `AgentDefinitionResolver`, `resolve_subagent_model`. Canónico: `AgentTool`, agent defs, `services/AgentSummary`.
- `execution/runner.py` → `SubagentRunnerProtocol`. Canónico: `tasks/LocalAgentTask`, `tasks/RemoteAgentTask`.
- `execution/local/runtime.py` → `LocalAgentRuntime` (435 LOC). Canónico: `Task.ts`, `tasks.ts`.
- `execution/local/notification.py` → `BackgroundNotification`, drain/process. Canónico: `hooks/notifs`, `services/notifier.ts`.
- `execution/local/summarizer.py` → `summarize_if_needed`. Canónico: `services/compact`, `services/AgentSummary`.
- `execution/fork/` → `ForkPolicy`, `ForkSnapshot`, `ForkContext`, `RuntimeContextForker`. **Fork existe en el canónico** — localizar su contraparte y contrastar (no es novedad del runtime).
- `execution/tasks/registry.py` → `TaskRecord`, `TaskRegistryProtocol`, `InMemoryTaskRegistry`. Canónico: `tasks/types.ts`, `Task.ts`.
- `execution/observer/` → `ExecutionObserverProtocol`, `SubagentStarted/Stopped`.

### 06 · hooks
- `hooks/protocol.py` → `HookEvent` (enum), `HookDecision`, `HookSinkProtocol`.
- `hooks/runner.py` → `HookRunner`.
- Canónico: `schemas/hooks.ts` (definición de eventos hook de settings.json), `hooks/toolPermission/`, `query/stopHooks.ts`. **Ojo**: el dir `hooks/` del canónico es mayormente React hooks (`useXxx`) — no confundir con el sistema de hooks configurables.

### 07 · events
- `events/protocol.py` → `Event`, `EventBusProtocol`.
- `events/bus.py` → `EventBus`.
- `events/event_types.py` → `Usage`, `TokenEvent`, `ToolCallEvent`, `ToolResultEvent`, `DoneEvent`, `ErrorEvent`.
- Canónico: eventos del stream de `query` (SDK messages), `remote/sdkMessageAdapter.ts`.

### 08 · signals
- `signals/protocols.py` → `SignalType` (enum), `SignalHandler`.
- `signals/bus.py` → `SignalBus`, `SignalHandle`, `_Node`.
- Canónico: cancelación/abort (`AbortController`, `useCancelRequest.ts`, `useCancelRequest`).

### 09 · tools (infra)
- `tools/protocol.py` → `ToolCategory`, `ToolResult`, `ToolProtocol`. Canónico: `Tool.ts` (29KB).
- `tools/registry.py` / `native_registry.py` / `factory.py` (`create_tools`). Canónico: `tools.ts` (17KB).
- `tools/pool.py` → `ToolPool`, `assemble_tool_pool`.
- `tools/dispatcher.py` → `ToolDispatcher`.
- `tools/deferred*.py` → deferred tools (`is_deferred_tool`, delta, `SimulatedDeferredStrategy`, `NativeDeferredStrategy`). Canónico: `ToolSearchTool`, mecanismo de deferred/tool-search.
- `tools/exec_env.py` → `ShellResult`, `LocalExecEnvironment`, `BwrapExecEnvironment`. Canónico: sandbox/bwrap, `tools/shared`.
- `tools/fs_env.py` → `ConfinedFilesystem`, path traversal, working-path checks. Canónico: `tools/utils.ts`, path guards.

### 10 · tools/native (uno a uno vs `tools/*Tool/` canónico)
Presentes en runtime: `agent`, `ask_user`, `bash`, `clone_repository`, `config`, `file_edit`, `glob`, `grep`,
`plan_mode` (enter/exit), `read_file`, `sleep`, `task_tools` (Create/Get/List/Update/Stop/Output), `todo_write`,
`tool_search`, `web_fetch`, `web_search`, `worktree` (enter/exit), `write_file`.

**Canónico tiene además (candidatos ❌/⛔ a clasificar):** `BriefTool`, `LSPTool`, `MCPTool`, `McpAuthTool`,
`NotebookEditTool`, `PowerShellTool`, `REPLTool`, `RemoteTriggerTool`, `ScheduleCronTool`, `SendMessageTool`,
`SyntheticOutputTool`, `TeamCreateTool`, `TeamDeleteTool`, `FileReadTool`/`FileWriteTool` (naming).

### 11 · capabilities/mcp
- `provider.py` (339), `client.py` (204), `config.py`/`config_store.py`/`scope.py`, `auth.py`, `token_storage.py`,
  `state.py`, `reconcile.py`, `tool_adapter.py`, `resource_tools.py` (`ListMcpResourcesTool`, `ReadMcpResourceTool`).
- Canónico: `services/mcp`, `services/oauth`, `services/mcpServerApproval.tsx`, `tools/MCPTool`, `tools/McpAuthTool`.

### 12 · capabilities/skills
- `loader.py`, `frontmatter.py`, `provider.py`, `skill_tool.py` (`SkillTool`), `commands.py` (slash commands), `store.py`, `state.py`.
- Canónico: `skills/{bundled,bundledSkills.ts,loadSkillsDir.ts,mcpSkillBuilders.ts}`, `tools/SkillTool`, `commands/`.

### 13 · capabilities/memory
- `store.py` (`FilesystemMemoryStore`, `MemoryHeader`), `recall.py` (`rank_memories`), `provider.py`, `prompt.py`.
- Canónico: `services/SessionMemory`, `services/extractMemories`, `services/teamMemorySync`, `memdir/`.

### 14 · capabilities/plan
- `plan_file.py` (get/exists/is_session), `provider.py` (`PlanModeProvider`, render full/sparse/reminders).
- Canónico: `EnterPlanModeTool`, `ExitPlanModeTool`, lógica de plan mode.

### 15 · storage
- `protocol.py` → `StorageProtocol`, `StorageKeys`. `filesystem.py` → `FilesystemStorage`. `factory.py` → `StorageRegistry`.
- `filesystem.py` **intenta ser el equivalente directo** de la persistencia FS del canónico → entra a contraste de homologación
  (cubrir todo lo que el canónico persiste: config, sesiones, history, todos, memoria, config MCP, estado skills).
  Además es el seam que habilita **MinIO** en `agentic_assistant`.

### 16 · models
- `caller.py` → `AgenticModelsCaller`, `_compose_system_prompt`. `protocol.py` → `ModelRequest`, `ModelCallerProtocol`.
- Delegado al paquete `agentic_models`. Canónico: `services/api`, streaming/model call.

### 17 · voice
- `protocol.py` → `AudioInput`, `SpeechToTextProtocol`, `TextToSpeechProtocol`.
- Canónico: `voice/`, `services/voice.ts`, `services/voiceStreamSTT.ts`, `hooks/useVoice.ts`.

### 18 · factory / ensamblado
- `factory.py` → `RuntimeConfig`, `RuntimeFactory`, `create_runtime`, y configs (`StorageConfig`, `ToolsConfig`,
  `CapabilitiesConfig`, `ModelsConfig`, `VoiceConfig`).
- Canónico: `bootstrap/`, `setup.ts`, `entrypoints/`.

---

## Notas de método (para no repetir el fracaso monolítico)
- El canónico incluye MUCHO fuera de alcance (UI/ink/terminal): se marca ⛔ con la razón, no se porta.
- El canónico **no tiene usuarios ni sesiones**; el runtime sí. Donde el canónico opera single-user en terminal,
  la homologación es *de comportamiento observable*, no de estructura 1:1.
- Cuando una feature del canónico dependa de la terminal (TUI, teclado, ink), se documenta como ⛔ y se anota qué
  parte del *comportamiento* (no de la UI) sí debe existir en el runtime.
