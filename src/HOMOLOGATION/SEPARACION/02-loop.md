# 02 · loop — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/02-loop.md`.
> **Ciclo A1.4** del PLAN §4. Fuente: tracker `../02-loop.md` (**60** features A1…G6, leído íntegro 1→365).
> **Reconciliado en `A-CIERRE-P4 §9`** (2026-07-28): 60/60 celdas · 0 INVENTADAS · 15 pérdidas remediadas
> (`P4-02-1..15`) · §Evidencia restituida (`§1.0`) · **5 veredictos invertidos aguas abajo → `§2.6`** ·
> conteo corregido **54→60** (el «54» era un error propio; el «46» del tracker, otro distinto).
> Esquema: `00-LEGEND.md`. Re-clasifica cada finding de fidelidad-de-capacidades bajo B (base↔costuras↔batteries↔integrador).
> **No es otra tabla de deuda:** es el reparto del **mecanismo del turno** entre el base (esqueleto loop) y las
> batteries/costuras que ese esqueleto dispara.

## Naturaleza de la categoría
El `AgentLoop` es **el mecanismo del turno**: el corazón `T2-BASE-MECANISMO` de la espina. La 2ª vuelta lo dejó
line-precisa: el runtime homologa fielmente el **esqueleto** (prompt → ensamblar pool → `complete()` → consumir stream
→ persistir assistant → dispatch de tools con gate + context_modifier/ends_turn → decidir continuar) y lo AUSENTE es
**sistémico y agrupable en cuatro motores no portados** + un accounting muerto. El eje de la re-clasificación bajo B es
exactamente ese corte: **el esqueleto es base-mecanismo; los cuatro motores son batteries (compactación, budget,
commands) o costuras que el loop dispara (hooks, motor-de-modelo), no lógica embebida.** El canónico los fusiona en
`query.ts` (1729 LOC); B los des-fusiona en un loop delgado que **invoca costuras** y baterías **componibles**.

Frontera heredada de la 2ª vuelta (se respeta aquí): las features **G** (`processUserInput`, `maxBudgetUsd`, structured
output, usage/coste, `interrupt`, persistencia de transcript) son el **driver de sesión** (`QueryEngine`/`ask`), que en
B vive en `execution/local/runtime.py` (`LocalAgentRuntime`) → se **auditan a fondo en 05·execution**; aquí se reparten
por su TIER pero su hogar de construcción es 05 (destino nombrado, no troceo — L07).

---

## 1. Tabla por finding

### 1.0 Criterio de aceptación heredado (restituido — `A-CIERRE-P4 §9.4 · P4-02-16`)

El tracker traía `## Evidencia ejecutada` (`../02-loop.md:25-35`) y el destilado **la perdió entera**, igual que
`05` (`P4-05-9`). Es el estado que la re-ingeniería debe reproducir, y el **único mecanismo del corpus que
detecta un doc rancio desde el código**:

- **Lint** de `loop/`: `ruff` ✅ · `mypy` ✅ (5 archivos) · `bandit` ✅.
- **Tests**: `test_basic_loop.py` (5) + `test_loop_homologation.py` → **`14 passed, 5 xfailed`**.
  - *Sintéticos*: inserción de prompt · multi-turno hasta agotar `tool_calls` · gate PreToolUse (deny +
    updatedInput) · `ends_turn` (HITL) · recall `<system-reminder>` con dedup · filtro de pool de subagente
    (background + `agent_allowed_tools`) · `system_override` · abort pre-inicio y entre turnos · techo `_MAX_TURNS`.
  - *e2e real* (dispatcher/pool/EventBus vía `create_runtime`): multi-turno con dispatch real y stream que
    surface `ToolCall→ToolResult→Token→Done`.
- **`xfail(strict)` = evidencia de gap** — 5, uno por motor ausente: `test_loop_accepts_configurable_max_turns`
  (GAP-L2, A5) · `test_loop_wires_compaction_engine` (GAP-L4, B6) · `test_loop_accepts_fallback_model`
  (**GAP-C4**, C4) · `test_loop_fires_stop_hook_at_turn_end` (GAP-L1, D5) · el 5º cubre GAP-L1b (D3).
- **Tests de la remediación** (§LR del tracker, aún no escritos): `test_loop_compacts_when_over_budget` (LR1) ·
  `test_loop_retries_then_fallbacks` (LR2) · `test_stop_hook_can_continue_loop` (LR3).

> ⚠ **`P4-02-17`** — la `§Evidencia` del tracker rotula ese tercer xfail como *«GAP-L3 fallback model»*. Es el
> **swap de GAP-IDs** que su propia `§Nota de honestidad` declaró corregido «en las 3 caras»: eran **4**, y ésta
> es la que no se revisó. GAP-L3 = token-budget (E1); el fallback = **GAP-C4**. Corregido arriba.

### A · Estructura del bucle de turnos
| ID | resumen (comportamiento observable) | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **A1** ✅ | inserta prompt user + bucle hasta turno sin tool-use | núcleo | **T2-BASE-MECANISMO** | módulo base `loop` | — | el esqueleto se queda tal cual (mecanismo del turno); `agent_loop.py:179/185/348` |
| **A2** 🔀 | estado mutado in-place vs `State` inmutable reducer-friendly | núcleo | **T2-BASE-MECANISMO** | módulo base `loop` | — | divergencia de forma; efecto equivalente. Opcional: extraer estado-de-turno si se quiere `step()` puro testeable |
| **A3** ⛔ | `queryTracking` (chainId/depth) para analítica de cadena | cáscara-CLI | **T3-INTEGRADOR** (observabilidad) | integrador (`00-INTEGRADORES`) | — | NO se descarta: observabilidad del árbol de queries → el integrador la deriva del stream de eventos (07); no core |
| **A4** 🟡 | terminación con **reason codes** estructurados — los **9** del canónico, restituidos (`P4-02-1`): `completed` · `aborted_*` · `max_turns` · `prompt_too_long` · `model_error` · `hook_stopped` · **`stop_hook_prevented`** · **`blocking_limit`** · **`image_error`**. Los tres últimos se habían perdido tras una elipsis, y **`blocking_limit` es la salida de B9 y `image_error` la de C10** ⇒ la elipsis cortaba el enlace del enum con dos gaps del propio doc | núcleo | **T2-BASE-MECANISMO** (`LoopOutcome`) | módulo base `loop` (+ consumo 05) | — | **CORE-GAP**: el loop retorna `None`; introducir `LoopOutcome`/reason para que 05 distinga fin/abort/límite/error (hoy colapsados). Home loop; consumo en 05 |
| **A5** ❌ | techo de turnos **configurable** por el consumidor + señal `max_turns_reached` | núcleo | **T1-CONTRATO** (campo, ya `RuntimeTask.max_turns` 01·CTR-14) + **T2-BASE-MECANISMO** (cablear) | contratos (campo) + base `loop` (cablear) → 05·FIND-EXEC5 | — | **CORE-GAP GAP-L2**: `_MAX_TURNS=50` fijo (`agent_loop.py:24/185`); inyectar `max_turns` al `AgentLoop` (cabling gap homed en 05) + señal de terminación por límite |

### B · Recompactación / presupuesto de contexto (pre-modelo) — motor #1
| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **B1** ❌ | `getMessagesAfterCompactBoundary` (vista tras última compactación) | núcleo | **BATTERY compaction** | battery `compaction` | eje **persistencia** (scope = sesión) | CORE-GAP; depende del motor B6 |
| **B2** ❌ | `applyToolResultBudget` (cap de tamaño agregado de tool results) | núcleo | **BATTERY compaction** | battery `compaction` | — | CORE-GAP: presupuesto por-mensaje de tool_result (evita reventar contexto con salidas gigantes) |
| **B3** ❌ | `snipCompact` (poda de historia) | núcleo | **BATTERY compaction** | battery `compaction` | eje **persistencia** | CORE-GAP |
| **B4** ❌ | `microcompact` (edición de caché por `tool_use_id` + boundary diferido) | núcleo | **BATTERY compaction** | battery `compaction` | — | CORE-GAP |
| **B5** ❌ | `contextCollapse` (proyección + colapsos por turno) | núcleo | **BATTERY compaction** | battery `compaction` | — | CORE-GAP; prerequisito de la recuperación PTL (D1) |
| **B6** ❌ | `autocompact` (**el motor**) — mecanismo restituido (`P4-02-2`): trigger por umbral + **circuit-breaker `consecutiveFailures`** + **`AutoCompactTrackingState`** + evento canónico **`tengu_auto_compact_succeeded`** (que **no** es `compact_boundary`/07·H1: uno es telemetría de éxito, el otro la emisión de frontera — el destilado los había sustituido). **Carve-out que no puede perderse:** `execution/local/summarizer.py` sólo condensa el **OUTPUT de un subagente background**, NO la historia del turno ⇒ no es el motor ni puede reusarse como tal | núcleo | **BATTERY compaction** (motor) + **T2-COSTURA** `CompactionProvider` (01·CTR-09) | battery `compaction` + costura providers + emite 07·H1 | eje **persistencia** (scope = sesión) | **CORE-GAP GAP-L4**: `CompactionProvider` (aporte de providers) existe; falta EL MOTOR. El loop expone el **trigger** (LR1, base-mecanismo); la estrategia es battery |
| **B7** ❌ | `buildPostCompactMessages` + yield del boundary | núcleo | **BATTERY compaction** | battery `compaction` | — | CORE-GAP; depende B6 |
| **B8** ⛔ | `task_budget.remaining` (carryover, beta API server-side) | núcleo | **T1-MOTOR** (futuro) | costura motor (→16) / fuera hoy | — | feature beta `task-budgets-2026-03-13`: costura al motor de modelo si se adopta; hoy fuera de alcance |
| **B9** ❌ | blocking-limit preempt (PTL sintético con reserva para `/compact`) | núcleo | **BATTERY compaction** (guard) | battery `compaction` | — | CORE-GAP; depende del contador de tokens (B10) |
| **B10** ❌ | contador de tokens — **dos** caminos, restituido el barato (`P4-02-3`): `tokenCountWithEstimation` (estimar) **y `finalContextTokensFromLastResponse`** (tomar el conteo real de la última respuesta) | núcleo | **T1-MOTOR** (usage del modelo) + **T2-BASE-MECANISMO** (loop acumula) | costura motor (usage) + base `loop` | — | **CORE-GAP** (prerequisito de B2/B6/B9 y del budget E1). La parte "el loop no acumula usage" **también es CORE-GAP**, no DEUDA-B (§2.6·I2); agregación **asimétrica**, ver C12 |

### C · Llamada al modelo y streaming — motor #2 (error recovery)
| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **C1** ✅ | consumir stream (tokens/tool_use/done) + persistir assistant | núcleo | **T2-BASE-MECANISMO** (consume T1 event/stream de 07) | módulo base `loop` | — | `agent_loop.py:247-281`; verificado e2e. Shape del stream = 07·events |
| **C2** 🟡 | superficie de opciones a `callModel` — las **10** canónicas, restituidas (`P4-02-4`): `thinkingConfig` · `fastMode` · `effortValue` · **`advisorModel`** · `mcpTools` · `agents` · `fallbackModel` · `taskBudget` · **`maxOutputTokensOverride`** · **`queryTracking`**. La firma **viva** (punto de partida de la ampliación, también perdida): `complete(messages, tools, stop, model_id, system_sections?, system_override?)`. ⚠ `maxOutputTokensOverride` es **el mando que ejecuta D2** (escalar 8k→64k): sin él, D2 queda descrita sin el parámetro que la hace posible | núcleo | **T1-MOTOR** (ampliar `ModelCallerProtocol`) | costura motor (→16) | — | ampliar la costura del motor; decidir core (thinking/effort probablemente sí) vs delegado al caller (`agentic_models`) |
| **C3** 🟡 | `getRuntimeMainLoopModel` (plan-mode + `>200k` ⇒ cambio de modelo por turno) | núcleo | **T1-MOTOR** (resolución por turno) | costura motor (→16/05) | — | resolución de modelo por turno o documentar que el caller la absorbe; el modelo de subagente ya se resuelve en 05 (`resolve_subagent_model`) |
| **C4** ❌ | `fallbackModel` + `FallbackTriggeredError` ⇒ cambiar modelo y **reintentar** limpiando parciales | núcleo | **T2-BASE-MECANISMO** (retry wrapper) + **T1-MOTOR** (fallback id) | base `loop` + costura motor + emite 07·J3 (`api_retry`) | — | **CORE-GAP GAP-C4**: hoy `ErrorEvent`⇒`[error]`+break (`agent_loop.py:267-270`). Envolver `complete()` en retry/fallback (LR2), descartando parciales (respeta C11). **Cómo se descartan, restituido (`P4-02-5`): tombstones de mensajes huérfanos + `stripSignatureBlocks`** — no basta con «no persistir». Anclas canónicas del tracker (`:270`): `attemptWithFallback` `query.ts:650-655` · `FallbackTriggeredError`→`currentModel=fallbackModel` `:894-897` |
| **C5** ❌ | streaming fallback (`onStreamingFallback` ⇒ tombstone + reset de executor) | núcleo | **T2-BASE-MECANISMO** (error recovery) | base `loop` | — | CORE-GAP; depende C4 |
| **C6** ⛔ | `backfillObservableInput` (clonar msg, campos derivados para transcript/SDK) | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (`00-INTEGRADORES`) | — | presentación de transcript; NO afecta lo que va a la API. Capa de interfaz del integrador |
| **C7** ❌ | withhold de errores recuperables (PTL/media/max_output) hasta saber si hay recuperación | núcleo | **T2-BASE-MECANISMO** (error recovery) | base `loop` | — | CORE-GAP; depende de las rutas de recuperación (D1/D2). Sin ellas el error se surface directo |
| **C8** ⛔ | `createDumpPromptsFetch` (debug interno ant) | cáscara-CLI | **CLI-ONLY / INTERFAZ** (dev tooling) | integrador (dev tooling) / fuera | — | herramienta de depuración; no core. Un integrador puede exponerla como dev tooling |
| **C9** ❌ | `pendingCacheEdits` (boundary de microcompact con tokens de caché reales) | núcleo | **BATTERY compaction** | battery `compaction` | — | CORE-GAP; depende B4 |
| **C10** ❌ | `ImageSizeError`/`ImageResizeError` ⇒ `image_error` | núcleo | **T1-CONTRATO** (shape image) + **BATTERY** (handling) | contratos (image content) + battery/handling (cross 09·tools) | — | CORE-GAP multimodal: shape de imagen + manejo de error. Se cruza con tools multimodales |
| **C11** 🔀 | `yieldMissingToolResultBlocks` — todo `tool_use` recibe `tool_result` aun en error/abort | núcleo | **T2-BASE-MECANISMO** (buffer-then-commit) | módulo base `loop` | — | invariante reproducido **por diseño** (distinto mecanismo). `break` 267-270 ANTES de persistir 272-281; dispatcher nunca lanza (`dispatcher.py:54-84`). **Sin remediación** (L10) |
| **C12** 🟡 | acumulación de **usage/tokens** (`updateUsage` / **`accumulateUsage`**, `message_delta` stop_reason) | núcleo | **T1-MOTOR** (usage en `DoneEvent`) + **T2-BASE-MECANISMO** (el loop acumula) | costura motor + **CORE-GAP** (`B-usage` recalificado, §2.6·I2 → residual `DB-14`/`DB-15`) | — | **FIND-L2**: `agent_loop.py:253-254` nunca lee `done.usage` ⇒ `session.usage`=0. **Regla de agregación restituida** (`P4-02-6`, cruce `A-CIERRE-P4 §8·P4-05-6`): es **ASIMÉTRICA** — `latestInputTokens` **se queda con el último** (el input ya es acumulativo), `cumulativeOutputTokens` **se suma**. Sumar el input es el bug natural y produce doble conteo por turno, con `maxBudgetUsd` (G2) colgando de ahí |

### D · Recuperación post-stream (rama sin tool-use) — motores #2 y #3
| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **D1** ❌ | recuperación PTL: collapse-drain ⇒ reactive-compact, **single-shot cada uno** (`P4-02-7`: guarda anti-bucle, cada ruta se intenta UNA vez por turno) | núcleo | **BATTERY compaction** | battery `compaction` | — | CORE-GAP; depende B5/B6 |
| **D2** ❌ | recuperación `max_output_tokens`: escalar 8k→64k + "resume" multi-turno (límite 3) | núcleo | **T2-BASE-MECANISMO** (error recovery) | base `loop` | — | CORE-GAP: detectar truncamiento por tokens de salida y reintentar/continuar |
| **D3** ❌ | `executePostSamplingHooks` tras respuesta del modelo | núcleo | **T2-COSTURA** `HookRunner` (fire point) | costura hooks (→06) + base fire point | — | **CORE-GAP GAP-L1b**: post-sampling/post-tool hooks no cableados pese al enum `HookEvent` |
| **D4** ⛔ | skip stop-hooks si el último mensaje es API-error (anti death-spiral) | núcleo | (parte de LR3) | base `loop` (con D5) | — | consecuencia de no tener stop-hooks; se resuelve con D5 |
| **D5** ❌ | `handleStopHooks` (Stop/SubagentStop + blocking errors + `preventContinuation` + retry con **`stopHookActive`**, `P4-02-8`: la guarda de re-entrada, lo único que impide que `preventContinuation` haga girar el loop indefinidamente) | núcleo | **T2-BASE-MECANISMO** (fire point) + **T2-COSTURA** `HookRunner` | base `loop` (disparar) + costura hooks (→06) | — | **CORE-GAP GAP-L1**: el fin de turno no corre Stop hooks (`HookEvent.STOP` definido, jamás disparado); `SUBAGENT_STOP` sí (execution, post-loop). Disparar al cerrar turno con `preventContinuation` (LR3) |
| **D6** ❌ | token budget (+500k auto-continue) — ver E1 | núcleo | **BATTERY budget** | battery `budget` | — | CORE-GAP GAP-L3 (= E1) |
| **D7** ✅ | `return completed` en fin de turno normal | núcleo | **T2-BASE-MECANISMO** | módulo base `loop` | — | `agent_loop.py:348-349` (`break` del `for`); equivalente observable (salvedad A4) |

### E · Stop-hooks, token-budget, config, deps (auxiliares)
| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **E1** ❌ | `checkTokenBudget` (+500k con nudge, diminishing returns, completion event) | núcleo | **BATTERY budget** | battery `budget` | — | **CORE-GAP GAP-L3**: motor de budget con `BudgetTracker` + mensaje de continuación (requiere C12/B10) |
| **E2** ❌ | `executeExtractMemories` en fin de turno | núcleo | **BATTERY memory** (→13) + **T2-COSTURA** `HookRunner` | battery `memory` (13) + costura hooks | eje **persistencia** (scope memoria → 13) | CORE-GAP: extracción de memorias al cerrar turno; hoy el loop no lo dispara. Cross 13·memory |
| **E3** ⛔ | `executeTaskCompletedHooks` + `executeTeammateIdleHooks` (teammates coordinator/swarm) | núcleo | **T3-INTEGRADOR** (subsistema nuevo) | integrador (multi-agente, subsistema nuevo) | — | topología coordinator/swarm **gateada/experimental**: `feature('COORDINATOR_MODE')` + env `CLAUDE_CODE_COORDINATOR_MODE`, en `coordinator/coordinatorMode.ts` + `utils/swarm/inProcessRunner.ts`; las INTERNAL_WORKER_TOOLS son **cuatro** — `SendMessage` · `TeamCreate` · **`TeamDelete`** · **`SyntheticOutput`** (`P4-02-9`: sin los gates, el ⛔ pierde su justificación verificable). El runtime modela padre→subagente, NO pares (grep = 0). Si un integrador la adopta ⇒ **subsistema nuevo**, no gap del loop |
| **E4** ⛔ | `executePromptSuggestion`/`executeAutoDream`/job classifier/notifications/summary **+ `saveCacheSafeParams` + `cleanupComputerUseAfterTurn`** (`P4-02-10`) | cáscara-CLI | **CLI-ONLY / INTERFAZ** + fuera | integrador (UI/bookkeeping) / fuera (dogfooding) | — | background bookkeeping / UI / dogfooding (chicago MCP); no core. ⚠ **doble filo abierto (L10)**: los dos restituidos **no son UI** — son limpieza de **estado real** al cerrar turno (parámetros de caché, computer-use) ⇒ el ⛔ de la fila puede estar sobre-extendido. **Marcado, no resuelto**: decidir en el ciclo de hooks (06) si son fire-point de fin de turno |
| **E5** 🔀 | `buildQueryConfig`: **snapshot de `sessionId`** + gates statsig/env (`streamingToolExecution`, **`emitToolUseSummaries`**, `isAnt`, `fastMode`) | núcleo | **T2-COSTURA** (flags de capacidad del caller) | costura motor / flags de construcción | **eje identidad** — el config del turno **congela el `sessionId`** al construirse (`P4-02-11`) ⇒ toca K4/ID-5: quién es el portador de identidad del turno y cuándo se fija | gates de infra expresados como flags de construcción/capability (`supports_native_tool_search`, `agent_loop.py:143-146`). Equivalente de intención **para los gates**; el snapshot de identidad **no tiene contraparte** y no estaba declarado. ⚠ Es la especie de `09·E5` invertida: allí la columna de identidad inventó, aquí **omitió** |
| **E6** 🔀 | `productionDeps` (DI de `callModel`/`microcompact`/`autocompact`/`uuid` para tests) | núcleo | **T2-COSTURA** (deps seam) | módulo base `loop` (patrón DI) | — | mismo patrón (DI por constructor, `agent_loop.py:49-63`). Al portar B/battery, reusar el seam de deps para inyectar los motores en tests |

### F · Tool-use dispatch y fin de turno con tools
| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **F1** ✅ | ejecutar tool calls y reingresar resultados como contexto | núcleo | **T2-BASE-MECANISMO** (dispatch) + **T1-CONTRATO** (tool/tool_result shape) | base `loop`/`dispatcher` + contratos (01/09) | — | `agent_loop.py:287-323` + `dispatcher.py:36/76-77`; verificado e2e |
| **F2** 🟡 | gate `canUseTool` (allow/deny/**ask**/updatedInput) + **permission modes** | núcleo | **T2-COSTURA** (gate/hook) + **T1-CONTRATO** (`PermissionMode`, 01·CTR-08) | costura hooks (06·HOOK3) + contratos (mode) + **CORE-GAP K1** (§2.6·I3) | — | **CORE-GAP** (parte modes/ask): gate cablea `block`/`modified_input` (`agent_loop.py:300-313`); falta `ask`/HITL + modos. **`B-02` fue recalificado: es CORE-GAP = GAP-02/K1**, no deuda interna; lo único que sigue siendo DEUDA-B es el **canal no tipado** `app_state.native["plan_mode"]`, renombrado **`DB-19`** y secuenciado **tras** K1 |
| **F3** 🔀 | `StreamingToolExecutor` (ejecución concurrente DURANTE el stream) **+ su fallback `runTools`** (`P4-02-12`) | núcleo | **T2-BASE-MECANISMO** | base `loop` | — | divergencia de rendimiento: dispatch secuencial post-stream (`agent_loop.py:287-344`). ⚠ La restitución **cambia la lectura de la fila**: el secuencial de B no es sólo «correcto pero más lento», es **el mismo modo que el canónico conserva como fallback** ⇒ el concurrente es optimización tras el gate `streamingToolExecution`, no una deuda de fidelidad |
| **F4** 🔀 | `hook_stopped_continuation` desde una tool ⇒ cerrar turno | núcleo | **T2-BASE-MECANISMO** | base `loop` | — | mecanismo `ends_turn` equivalente (`agent_loop.py:338-339/348`); productores reales `native/ask_user.py`, `native/plan_mode.py`. Documentado |
| **F5** ⛔ | `generateToolUseSummary` (Haiku, para UI móvil) | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (UI móvil) | — | resumen para interfaz; capa de presentación del integrador con UI |
| **F6** 🟡 | abort durante tools ⇒ interrupción + `aborted_tools` + check maxTurns | núcleo | **T2-BASE-MECANISMO** | base `loop` | — | el dispatcher honra `ctx.stop` por-call (`dispatcher.py:54-55`); el loop no re-chequea entre tools ni corta el batch. Chequear `ctx.stop` entre tool calls y mid-stream. **⚠ Causa restituida (`A-CIERRE-P4 §14.8`):** el «ni mid-stream» **no es un olvido del loop** — es que el mid-stream **no es alcanzable desde el loop**: el corte tiene que ocurrir dentro del provider y el contrato de la señal está roto (`08·CG-SIG-10`). Chequear `ctx.stop` entre tool calls es arreglo de este loop; el mid-stream **no lo es**, y listarlos juntos hacía parecer local un arreglo que vive en `16`/`agentic_models` |
| **F7** 🟡 | `getAttachmentMessages` (edited-file diffs, comandos en cola, memory/skill prefetch) fin de turno | núcleo | **BATTERY** (attachments) + cross 03/13 | battery attachments (cross 03·context/13·memory) | — | el runtime rinde recall al INICIO (`_inject_recall`); falta el pipeline de attachments de fin de turno. Cubrir en 03/13 qué es core |
| **F8** ❌ | drain de comandos en cola: **`getCommandsByMaxPriority`** (prioridad), prompt/task-notification, **exclusión de slash**, scoping por agente (`P4-02-13`: se conservó *qué* se drena y se perdieron **la prioridad y el filtro**) | núcleo | **T2-BASE-MECANISMO** (drain point) + **BATTERY commands** | base `loop` (punto) + battery `commands` | — | **VEREDICTO INVERTIDO — era 🔀 «consumidor real», es CORE-GAP `H-5`** (§2.6·I1). En el base **nadie drena**: `_turn_start_hooks` nace vacío (`agent_loop.py:83`) y el único registrador es `runtime.py:371-374`, que sólo re-emite hooks **del integrador**; `drain_notifications` no tiene caller. Y el hook corre en `:176`, **antes** del `for` de `:185` ⇒ **una vez por `run()`, no por turno**. Home del arreglo = **este loop** (`AC-07`). Alinear además semántica de cola (cross 04/05) |
| **F9** 🔀 | memory prefetch consume (`startRelevantMemoryPrefetch`/`filterDuplicate`) | núcleo | **BATTERY memory** (→13) | battery `memory` (13) | eje **persistencia** (scope memoria → 13) | recall **síncrono** con dedup (`agent_loop.py:112-130/218`) vs prefetch asíncrono canónico. ⚠ **`P4-02-14`**: el criterio del dedup canónico es **`filterDuplicateMemoryAttachments` contra `readFileState`** (ficheros ya leídos); el de B es contra **la historia de mensajes**. **No es el mismo criterio**, y el «efecto cercano» se había concluido tras borrar justamente aquello en lo que difieren ⇒ doble filo abierto, a resolver en 13·memory |
| **F10** ❌ | skill discovery prefetch inject | núcleo | **BATTERY skills** (→12) | battery `skills` (12) | — | CORE-GAP: prefetch de descubrimiento de skills; cross 12·skills |
| **F11** 🟡 | `refreshTools` entre turnos (MCP recién conectado disponible) | núcleo | **T2-BASE-MECANISMO** | base `loop` (cross 11·mcp) | — | el pool se re-arma CADA turno (`agent_loop.py:195`, no cacheado); falta confirmar que ve MCP conectados a mitad de sesión (cross 11) |
| **F12** ✅ | `context_modifier`/`newContext` tras una tool (skills⇒allowed-tools, worktree/plan⇒estado) | núcleo | **T2-BASE-MECANISMO** (seam invocado) | base `loop` | — | `agent_loop.py:332-337` (`ctx = modifier(ctx) or ctx`); 5 productores reales. Cableado real, no costura muerta |
| **F13** ⛔ | `taskSummary` periódico (`claude ps`) | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (`agentic_code` terminal) | — | resumen de sesión para CLI `ps`; capa de interfaz de terminal |
| **F14** ⛔/❌ | `consumedCommandUuids` + `notifyCommandLifecycle` (started/completed) | núcleo | **BATTERY commands** + **CLI-ONLY** (notify) | battery `commands` + integrador (notify lifecycle) | — | lifecycle de comandos encolados; depende F8. El tracking = battery; la notificación al usuario = interfaz |

### G · Frontera con el driver de sesión (`QueryEngine`/`ask`) — hogar de construcción = 05·execution
| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **G1** ❌ | `processUserInput` (slash commands, `allowedTools`, override de modelo, **`resultText` de comandos locales**) antes del bucle — `P4-02-15`: el **camino de retorno** perdido; un comando local no sólo intercepta el turno, **produce texto** que lo alimenta. Es lo que da contenido al «si devuelve resultado terminal, cortar el turno» de `01·CR2` | núcleo | **T2-COSTURA** `UserInputProcessor` (01·CTR-12) + **T2-BASE-MECANISMO** (cablear) | costura + cablear loop (01·CR2) + battery `commands` (12) | — (arg `session` roza identidad) | **CORE-GAP GAP-G1**: seam existe, ningún consumidor lo invoca; el loop base debe invocarlo pre-turno (homed 01·CR2) |
| **G2** ❌ | `maxBudgetUsd` ⇒ `error_max_budget_usd` | núcleo | **T3-INTEGRADOR** (política de coste) o **BATTERY budget** | integrador (hosted multi-tenant) / 05 | eje **persistencia** (coste por sesión/tenant) | cap de coste por request: política de producto del integrador hosted. Requiere usage accounting (C12) + coste por modelo (16). Home 05 |
| **G3** ❌ | structured output (`jsonSchema` + `SyntheticOutputTool`) + límite de reintentos | núcleo | **BATTERY structured-output** (→09) | battery + cablear driver (05) | — | endpoints tipados del BFF (clasificar/extraer): portar `SyntheticOutputTool` (09) + plumbing de `jsonSchema` en el driver (05) |
| **G4** 🟡 | usage/coste (`totalUsage`, `getTotalCost`, `getModelUsage`) + `lastStopReason` | núcleo | **T1-MOTOR** (usage) + **CORE-GAP** (no se llena) | costura motor + **CORE-GAP `B-usage`** (§2.6·I2) | — | estructura existe, no se llena (= C12/FIND-L2). Home 05 (driver) + costura motor. La agregación es **asimétrica** (ver C12) |
| **G5** ~~✅~~ **🟡** | `interrupt()` ⇒ `abortController.abort()` | núcleo | **T2-BASE-MECANISMO** (abort) | base `loop` + 05 (cancel externo) | — | vía cooperativa abierta aquí (`ctx.stop`, `agent_loop.py:173/186` + `dispatcher.py:54`); el cancel externo `runtime.cancel` vive en 05 (verificado 2ª vuelta: `runtime.py:187`→`registry.kill:117-124`). **⚠ CAMBIO DE ESTADO `✅→🟡` (`A-CIERRE-P4 §14.8`, 2026-07-29, `D-06·1`).** El canónico `abortController.abort()` **corta la petición HTTP en vuelo**; B **no puede**: `08·CG-SIG-10` prueba que el `asyncio.Event` viaja como `StreamOptions.signal` (`caller.py:188-190`) y **todos** los providers gatean con `getattr(signal, "aborted", False)` ⇒ el corte nunca dispara. La vía cooperativa **sí** existe y es real, pero sólo actúa **en la frontera del turno y entre tool calls**: un abort durante la generación del modelo se ignora hasta que el stream termina solo. El ✅ homologaba la llamada `interrupt()`, no su **efecto observable**. Queda 🟡 hasta que `16` cierre el contrato de `CG-SIG-10` |
| **G6** ⛔/🟡 | persistencia de transcript (`recordTranscript`/`flush`), system-init, file-history, replay, partial | núcleo (persist) / cáscara-CLI (replay) | **T2-COSTURA** storage (→15) + **CLI-ONLY / INTERFAZ** | costura storage (15) + integrador (replay/partial/system-init) | eje **persistencia** | persistencia ⇒ 15·storage/05; replay/partial/system-init/file-history = capa de interfaz del integrador |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`ModelCallerProtocol`** (T1-MOTOR, ya existe; **ampliar superficie**) — productor: el loop en `complete(...)` (`agent_loop.py:235-239`) · consumidor: `agentic_models`. Findings C2/C3/C4(fallback)/B8/B10(usage). *Ampliación (thinking/effort/fallback/usage) se diseña en **16·models**.*
- **`CompactionProvider`** (T2-COSTURA, ya en 01·CTR-09) — productor: el **motor de compactación** (battery) vía `collect_compaction_context` · consumidor: providers concretos. El **loop** invoca el **trigger** (`should_compact`/`compact`, LR1) = base-mecanismo. Findings B1-B7/B9/C9/D1.
- **`HookRunner`** (T2-COSTURA, hogar **06·hooks**) — productor: el loop en las fronteras del turno. Hoy cablea **`PRE_TOOL_USE`** (`agent_loop.py:300-306`); faltan los **fire points** de `STOP`/`SUBAGENT_STOP`/`POST_TOOL_USE`/post-sampling (D3/D5/E2). Findings D3/D5/E2/F2.
- **`RetryPolicy` + fallback** (T2-COSTURA + T1-MOTOR) — productor: el loop envolviendo `complete()` en `_attempt_with_fallback` (LR2) · consumidor: config del integrador/caller. Findings C4/C5/C7/D2. Emite `api_retry` (07·J3).
- **`UserInputProcessor`** (T2-COSTURA, ya en 01·CTR-12) — productor (a cablear): el loop pre-turno (01·CR2) · consumidor: battery `commands`. Findings G1/F8/F14.
- **usage/token-counter** (T1-MOTOR) — productor: `DoneEvent.usage` del caller · consumidor: el loop acumula en `ctx`/sesión (hoy no lo hace, `agent_loop.py:253-254`). Findings C12/B10/G4 → **CORE-GAP `B-usage`** (recalificado, §2.6·I2). **La acumulación es asimétrica**: input = último valor, output = suma.
- **canal de notificación background** (T2-COSTURA, hoy sin drenador) — productor: el subagente al terminar (`put_notification`) · consumidor: **nadie** (`drain_notifications` sin caller; `_turn_start_hooks` vacío salvo aporte del integrador). Finding **F8 → CORE-GAP `H-5`**, cuyo punto de arreglo es este loop (§2.6·I1). Cross `SEAMS §S21` · `04`/`05`.
- **deps DI seam** (E6, ya existe por constructor `agent_loop.py:49-63`) — reusar para inyectar los motores (compaction/budget) en tests.

### 2.2 Batteries que alimenta (nombre · **ID de `BATTERIES.md`** · alcance)

> **Reconciliado con el catálogo (§2.6·I4).** `BATTERIES.md:166` asigna a 02 los IDs **B01 · B04 · B05 · B07**
> y clasifica `memory` como **alimentada** (hogar 13). Y `DEUDA-A:349` da a **`B02 resilience`** hogar
> **02·loop** — que la «Nota» de abajo negaba. Corte exacto (`BATTERIES.md:279`): **el esqueleto resiliente es
> base-mecanismo; la *estrategia* de reintento sí es battery componible (B02)**.

- **compaction** (**B01**, el MOTOR) — EL motor de compactación/presupuesto de contexto: trigger por umbral (B6), microcompact (B4), collapse (B5), snip (B3), tool-result budget (B2), boundary/vista (B1/B7), blocking-limit guard (B9), recuperación PTL (D1), cache-edits (C9). Consume `CompactionProvider`; emite `compact_boundary` (07·H1) para re-surface de 13·memory. **Motor origen aquí; el seam nació en 01.**
- **budget** (**B04**) — token-budget auto-continue +500k con nudge/diminishing-returns (E1/D6) + cost-cap por request (G2). Consume usage accounting (C12/B10).
- **commands** (**B05**) — drain de comandos encolados **por prioridad** (`getCommandsByMaxPriority`, con exclusión de slash) + lifecycle (F8/F14) + preproceso slash/inline (G1). Rellena `UserInputProcessor`. *Cross 12·skills.*
- **structured-output** (**B07**) — `SyntheticOutputTool` + `jsonSchema` con reintentos (G3). *Cross 09·tools; consumidor BFF.*
- **resilience** (**B02**, hogar 02 — `DEUDA-A:349`) — **sólo la política**: retry/backoff+jitter/retry-after · 529→fallback-de-modelo · streaming→non-streaming · idle-watchdog. Emite `api_retry` (07·J3). Findings C4/C5/C7/D2 + `16·B1-B4`.
- **memory** (alimentada, hogar 13) — prefetch (F9) / extract-memories fin de turno (E2) / skill prefetch (F10, hogar 12).
- **Nota (corregida).** La **recuperación de errores del modelo** (C4/C5/C7/D2) se parte en dos: el **wrapper** que envuelve `complete()` y descarta parciales es **base-mecanismo** del loop; la **estrategia** (cuántos reintentos, qué es reintentable, cuándo saltar al fallback) es la battery **B02**. La redacción previa —«NO es battery separada»— era media verdad y contradecía el catálogo. Se acopla a compaction sólo en las rutas PTL/max_output (D1).

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
Los **cuatro motores no portados** + los ❌ satélite:
- **GAP-L4 (motor compactación)** — battery `compaction` sin motor; `CompactionProvider` sin consumidor. Home **02·loop** (trigger) + battery. Findings B1-B7/B9/C9/D1.
- **GAP-L3 (token-budget)** — battery `budget` ausente + contador de tokens (B10). Findings E1/D6/B9/B10.
- **GAP-L1/L1b (stop/post-tool/post-sampling hooks)** — el loop no dispara `STOP`/`SUBAGENT_STOP`(main)/`POST_TOOL_USE`; fire points ausentes. Cross **06·hooks**. Findings D3/D5/E2.
- **GAP-C4 (fallback/retry)** — sin recuperación de error del modelo; un fallo del primario termina el turno. Base-mecanismo + costura motor. Findings C4/C5/C7/D2.
- **GAP-L2 (maxTurns configurable)** — A5; cabling gap homed **05·FIND-EXEC5** (+ contrato 01·CTR-14).
- **GAP-G1 (input preproc)** — G1; cabling homed **01·CR2**.
- **A4 (LoopOutcome reason codes)** — terminación estructurada; home loop, consumo 05.
- **C10 (image errors / multimodal)** — shape image (contrato) + handling; cross 09·tools.
- **F10 (skill prefetch)** — cross 12·skills. **F2 (modes/ask)** — contrato `PermissionMode` (01·CTR-08) + gate; **el ítem es CORE-GAP K1**, sólo el canal no tipado queda como DEUDA-B (`DB-19`).
- **`H-5` (F8 · drenaje de notificaciones background)** — *añadido por la reconciliación (§2.6·I1)*. El canal tiene productor (`put_notification`) y **ningún consumidor**: el padre nunca sabe que su subagente terminó. **El punto de arreglo es este loop** (`AC-07`: drenar en `run()`), por eso la brecha entra en la lista de 02 aunque el canal viva en `execution/local/notification.py`. Cross `RV-7`/`DB-29`/`SEAMS §S21`/`05·§2.6·R1`.
- **`B-usage` (FIND-L2 / C12 / B10 / G4)** — *recalificado a CORE-GAP* (§2.6·I2, por `07·§2.4` y `DEUDA-B §·fila 6`). El loop no acumula `DoneEvent.usage`; `session.usage`=0 (`agent_loop.py:253-254`). Residual DEUDA-B → `DB-14`/`DB-15`.

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10)

> **Esta sección se vació casi entera en la reconciliación.** De sus 3 ítems, **2 fueron recalificados a
> CORE-GAP** por rollups posteriores (§2.6·I2/I3) y ya no viven aquí. Queda **uno**, y con acople nuevo.

- **path legacy `capabilities_resolver`** (`agent_loop.py:201-205`, sólo anuncia schemas, no ejecuta) — cableado muerto; homed **18·FaR2** (`B-dead-resolver`). ⚠ **acople `18·N1` restituido**: borrarlo **rompe `create_loop`** (`loop/factory.py`), cuyo único camino es ese `elif` — la remediación del tracker no lo decía. Decidir juntos: re-firmar `create_loop` sobre `tool_registry`/`capability_manager`, o borrar el helper.
- *(residuales de los recalificados, no propios de 02: `DB-14`/`DB-15` por usage · `DB-19` por el canal `app_state.native["plan_mode"]`, secuenciado tras K1.)*

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05; vertido formal en A1.7)
Con **capacidad observable · origen (costura/battery del base) · firma que consume · cableado en el integrador · orden · criterio de aceptación**:

- **OI-6 · Renderizar/persistir el transcript del turno** *(contrato base común — capa de interfaz §1)* — **capacidad:** todo integrador con interfaz consume el stream de eventos del turno y lo **renderiza y/o persiste** (transcript, replay, system-init, file-history, partial messages). **origen:** G6/C6/F5/F13 (CLI-ONLY) + costura `StorageContract` (15). **firma:** subscripción al `EventBus`/stream (07) + `StorageContract` para durabilidad. **cableado:** el integrador se suscribe al stream y escribe/pinta; el runtime **no** persiste transcript ni renderiza. **orden:** tras 07 (stream) + 15 (storage). **aceptación:** un turno end-to-end deja transcript reproducible. *(realización: `agentic_code` = render a terminal + `claude ps` (F13) + resumen tool-use (F5); `agentic_assistant` = capa front + persistencia MinIO.)*
- **OI-7 · Observabilidad del árbol de queries/turnos** *(contrato base común §1)* — **capacidad:** correlacionar turnos/queries para analítica (chainId/depth). **origen:** A3 (`queryTracking`). **firma:** derivada del stream de eventos (07) + ids opacos. **cableado:** el integrador correlaciona por sus propios ids; el runtime no lleva telemetría de árbol. **aceptación:** el integrador puede reconstruir la cadena padre→subagente desde los eventos. *(realización: métricas en `agentic_assistant`; spinner/estado en `agentic_code`.)*
- **OI-8 · Cap de coste por request** *(específico — política de producto hosted)* — **capacidad:** abortar un request que supera un presupuesto en USD. **origen:** G2 (`maxBudgetUsd`). **firma:** parámetro del driver de sesión (05) + battery `budget`. **cableado:** el integrador hosted setea el cap; el driver compara `getTotalCost()` y emite `error_max_budget_usd`. **orden:** tras usage accounting (`B-usage`) + coste por modelo (16). **aceptación:** un request que excede el cap termina con el código de coste. *(realización: `agentic_assistant`/BFF multi-tenant; `agentic_code` degenerado no lo usa.)*
- **OI-9 · Salida estructurada tipada** *(específico — BFF)* — **capacidad:** forzar la respuesta a un `jsonSchema`. **origen:** G3. **firma:** battery `structured-output` (`SyntheticOutputTool`, 09) + plumbing `jsonSchema` en el driver (05). **cableado:** el integrador pasa el schema; el driver reintenta hasta conformar. **aceptación:** un endpoint tipado devuelve JSON conforme o agota reintentos. *(realización: `agentic_assistant`/BFF; `agentic_code` no lo usa.)*
- **OI-10 · Colaboración multi-agente de pares** *(específico — subsistema nuevo, futuro)* — **capacidad:** líder/worker in-process que se mensajean y notifican idle. **origen:** E3 (coordinator/swarm). **firma:** subsistema nuevo (`SendMessage`/`TeamCreate`/idle→líder), NO gap del loop. **cableado:** un integrador que adopte colaboración lo construye sobre el runtime. **aceptación:** N/A hoy (fuera de la espina). *(realización: futura, sólo si un integrador la adopta.)*

### 2.6 Veredictos **invertidos aguas abajo** (`A-CIERRE-P4 §9.3` — patrón 4 severo)

Cinco fichas eran **fieles a su tracker** y son **falsas hoy**: un rollup posterior invirtió el veredicto sin
volver a tocar este documento. No se detectan comparando las dos caras del par —coinciden— sino **cruzando cada
ficha contra `DEUDA-A`/`DEUDA-B`/`BATTERIES`/`P0`/`P1`**.

| # | ficha | decía | dice hoy la evidencia | fuente |
|---|---|---|---|---|
| **I1** | `F8` | 🔀 «drain al INICIO del turno … **consumidor real**» | **CORE-GAP `H-5`**: `_turn_start_hooks` nace vacío (`agent_loop.py:83`); el único registrador del base, `runtime.py:371-374`, sólo re-emite hooks **del integrador** (`root_turn_start_hooks is not None`); `drain_notifications`/`process_background_notification` **sin caller**. Además `_run_turn_start_hooks()` corre en `:176`, **antes** del `for` de `:185` ⇒ **una vez por `run()`, no por turno**. La sobre-declaración nació en el tracker (`:322` L09), que no abrió quién suministra el hook. **Y el seam, tal como está tipado, no puede rellenarse genéricamente:** el hook es `Callable[[], Coroutine]` (0-arg) mientras `drain_notifications(user_id, session_id)` exige **identidad** ⇒ sólo un closure del integrador puede cerrarla — por eso el arreglo es un drenaje **en el propio `run()`**, no un hook más (`AC-07`, cruce `AC-h3`) | `RV-7` · `DB-29` · `AC-07` · `SEAMS §S21` · `05·§2.6·R1` |
| **I2** | `C12`·`B10`·`G4`·§2.1·§2.4 | «= DEUDA-B `B-usage`» | **CORE-GAP**; residual → `DB-14`/`DB-15` | `07·§2.4` · `DEUDA-B §·fila 6` |
| **I3** | `F2`·§2.3·§2.4 | «parte hack = DEUDA-B `B-02`» | **CORE-GAP = GAP-02/K1**; sólo el canal no tipado sigue siendo deuda, como **`DB-19`**, tras K1 | `DEUDA-B §·fila 1` · `DEUDA-A · K1` |
| **I4** | §2.2 | 5 batteries sin ID + «error-recovery NO es battery» | IDs **B01·B04·B05·B07**, `memory` alimentada, y **`B02 resilience` con hogar 02**: el esqueleto es base, **la política de reintento es battery** | `BATTERIES.md:166/279` · `DEUDA-A:349` |
| **I5** | §3.2·Q5 y §3.3 | «`B-usage`/`B-02`/path-legacy son DEUDA-B interna, **NO** deuda A↔B» | **falso para 2 de 3** ⇒ la pregunta de doble filo dio un **falso negativo**. Sólo `path-legacy` se sostiene (y gana el acople `18·N1`) | consecuencia de I2+I3 |
| **I6** | `G5` (+ causa de `F6`) | ✅ «`interrupt()` ⇒ abort; vía cooperativa abierta» | **🟡**: la vía cooperativa existe y corta **en frontera de turno y entre tool calls**, pero el corte **mid-stream del canónico no ocurre** — `caller.py:188-190` pasa un `asyncio.Event` como `StreamOptions.signal` y **todos** los providers gatean con `getattr(signal, "aborted", False)` ⇒ `False` siempre. Homologaba la **llamada**, no el **efecto observable** | **`08·CG-SIG-10`** (2026-07-29) · `SEAMS §S2` `existe-roto` · `DEUDA-A §1.2(a)`→`16·FIND-MODELS4` |

Tasa **6/60 = 10 %** (05 midió 11 %). *Lección: un doc de categoría no es la última palabra sobre sus propias
fichas; el estado puede haber cambiado **debajo** de él.*

> **`I6` es de especie distinta a `I1..I5` y conviene no fundirlo con ellos.** `I1..I5` los invirtió un **rollup**
> (un documento transversal escrito después). `I6` lo invierte **el par 08**, es decir **otra categoría hermana**,
> al abrir código que estaba en su lado de la frontera. ⇒ la vigilancia de rancidez no basta hacerla contra los 5
> rollups: **cada par cierra celdas de otros pares**, y nadie estaba mirando ese vector (`AC-31`).

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (**60**)

| ID | TIER | destino | cara | evidencia | detalle | nota-identidad |
|---|---|---|---|---|---|---|
| A1 | T2-BASE-MECANISMO | base `loop` | base | ensamblador `agent_loop.py:179/185/348` abierto | sí (§2 esqueleto) | — |
| A2 | T2-BASE-MECANISMO (🔀) | base `loop` | base | ensamblador `agent_loop.py` (ctx in-place) abierto | sí (§2) | — |
| A3 | T3-INTEGRADOR (observabilidad) | integrador | integrador | tracker-leído | sí (OI-7) | — |
| A4 | T2-BASE-MECANISMO (`LoopOutcome`) | base `loop` + 05 | ambas | tracker-leído (retorna `None`, `agent_loop.py:171` firma) | sí (§2.3 + →05) | — |
| A5 | T1-CONTRATO + T2-BASE-MECANISMO | contratos + base (→05) | ambas | ensamblador `agent_loop.py:24/185` (`_MAX_TURNS` fijo) abierto | sí (§2.3 GAP-L2) | — |
| B1 | BATTERY compaction | battery `compaction` | base | tracker-leído | sí (§2.2) | eje persistencia |
| B2 | BATTERY compaction | battery `compaction` | base | tracker-leído | sí (§2.2) | — |
| B3 | BATTERY compaction | battery `compaction` | base | tracker-leído | sí (§2.2) | eje persistencia |
| B4 | BATTERY compaction | battery `compaction` | base | tracker-leído | sí (§2.2) | — |
| B5 | BATTERY compaction | battery `compaction` | base | tracker-leído | sí (§2.2) | — |
| B6 | BATTERY compaction (motor) + T2-COSTURA | battery + costura providers | base | tracker-leído + `agent_loop.py:189` (trigger point LR1) abierto | sí (§2.3 GAP-L4) | eje persistencia |
| B7 | BATTERY compaction | battery `compaction` | base | tracker-leído | sí (§2.2) | — |
| B8 | T1-MOTOR (futuro) | costura motor (→16) / fuera | base | tracker-leído (⛔ beta abierto) | N/A (⛔ fuera hoy) | — |
| B9 | BATTERY compaction (guard) | battery `compaction` | base | tracker-leído | sí (§2.2) | — |
| B10 | T1-MOTOR + T2-BASE-MECANISMO | costura motor + base | base | ensamblador `agent_loop.py:253-254` (no acumula) abierto | sí (§2.3 + `B-usage` **CORE-GAP**, §2.6·I2) | — |
| C1 | T2-BASE-MECANISMO | base `loop` | base | ensamblador `agent_loop.py:247-281` abierto | sí (§2) | — |
| C2 | T1-MOTOR | costura motor (→16) | base | tracker-leído + `agent_loop.py:227-239` (superficie `complete`) abierto | sí (→16) | — |
| C3 | T1-MOTOR | costura motor (→16/05) | base | tracker-leído | sí (→16/05) | — |
| C4 | T2-BASE-MECANISMO + T1-MOTOR | base + costura motor (→07·J3) | ambas | ensamblador `agent_loop.py:267-270` (error⇒break) abierto | sí (§2.3 GAP-C4, LR2) | — |
| C5 | T2-BASE-MECANISMO (error recovery) | base `loop` | base | tracker-leído (depende C4) | sí (§2.2 nota) | — |
| C6 | CLI-ONLY / INTERFAZ | integrador | integrador | tracker-leído (⛔ presentación abierto) | sí (OI-6) | — |
| C7 | T2-BASE-MECANISMO (error recovery) | base `loop` | base | tracker-leído | sí (§2.2 nota) | — |
| C8 | CLI-ONLY / INTERFAZ (dev) | integrador / fuera | integrador | tracker-leído (⛔ debug abierto) | N/A (⛔ dev tooling) | — |
| C9 | BATTERY compaction | battery `compaction` | base | tracker-leído (depende B4) | sí (§2.2) | — |
| C10 | T1-CONTRATO + BATTERY | contratos (image) + battery (09) | base | tracker-leído | sí (§2.3) | — |
| C11 | T2-BASE-MECANISMO (buffer-then-commit) | base `loop` | base | ensamblador `agent_loop.py:267-270 vs 272-281 + 287-344`; `dispatcher.py:54-84` abiertos | sí (🔀 sin remediación L10) | — |
| C12 | T1-MOTOR + T2-BASE-MECANISMO | costura motor + **CORE-GAP `B-usage`** | base | ensamblador `agent_loop.py:253-254` abierto | sí (FIND-L2 + §2.6·I2; agregación asimétrica) | — |
| D1 | BATTERY compaction | battery `compaction` | base | tracker-leído (depende B5/B6) | sí (§2.2) | — |
| D2 | T2-BASE-MECANISMO (error recovery) | base `loop` | base | tracker-leído | sí (§2.2 nota) | — |
| D3 | T2-COSTURA `HookRunner` | costura hooks (→06) | base | tracker-leído (enum def, sin fire point) | sí (§2.3 GAP-L1b) | — |
| D4 | (parte de LR3) | base `loop` (con D5) | base | tracker-leído (⛔ consecuencia abierto) | N/A (con D5) | — |
| D5 | T2-BASE-MECANISMO + T2-COSTURA | base (disparar) + costura hooks (→06) | base | ensamblador `agent_loop.py:348` (break seco, sin Stop) abierto | sí (§2.3 GAP-L1, LR3) | — |
| D6 | BATTERY budget | battery `budget` | base | tracker-leído (= E1) | sí (§2.2) | — |
| D7 | T2-BASE-MECANISMO | base `loop` | base | ensamblador `agent_loop.py:348-349` abierto | sí (§2) | — |
| E1 | BATTERY budget | battery `budget` | base | tracker-leído | sí (§2.3 GAP-L3) | — |
| E2 | BATTERY memory + T2-COSTURA | battery `memory` (13) + costura hooks | base | tracker-leído | sí (§2.3, →13) | eje persistencia |
| E3 | T3-INTEGRADOR (subsistema nuevo) | integrador (multi-agente) | integrador | tracker-leído (⛔ coordinator abierto) | sí (OI-10) | — |
| E4 | CLI-ONLY / INTERFAZ + fuera | integrador / fuera | integrador | tracker-leído (⛔ bookkeeping abierto) | N/A (⛔ dogfooding) | — |
| E5 | T2-COSTURA (flags caller) | costura motor / flags | base | ensamblador `agent_loop.py:143-146` abierto | sí (🔀 §2.1) | — |
| E6 | T2-COSTURA (deps seam) | base `loop` (DI) | base | ensamblador `agent_loop.py:49-63` abierto | sí (🔀 §2.1) | — |
| F1 | T2-BASE-MECANISMO + T1-CONTRATO | base + contratos (01/09) | base | ensamblador `agent_loop.py:287-323` + `dispatcher.py:36/76-77` abiertos | sí (§2) | — |
| F2 | T2-COSTURA + T1-CONTRATO | costura hooks (06) + contratos (mode) + **CORE-GAP K1** (residual `DB-19`) | ambas | ensamblador `agent_loop.py:300-313` abierto | sí (§2.3 + §2.6·I3, OI-4 de 01) | — |
| F3 | T2-BASE-MECANISMO (🔀) | base `loop` | base | ensamblador `agent_loop.py:287-344` (secuencial) abierto | sí (§2) | — |
| F4 | T2-BASE-MECANISMO (🔀) | base `loop` | base | ensamblador `agent_loop.py:338-339/348` (consumo) + productores `native/plan_mode.py:106`, `native/ask_user.py:97` (`ends_turn=True`) abiertos | sí (§2) | — |
| F5 | CLI-ONLY / INTERFAZ | integrador (UI móvil) | integrador | tracker-leído (⛔ UI abierto) | sí (OI-6) | — |
| F6 | T2-BASE-MECANISMO | base `loop` | base | ensamblador `dispatcher.py:54-55` vs `agent_loop.py:287` abiertos | sí (§2) | — |
| F7 | BATTERY attachments (cross 03/13) | battery (03/13) | base | tracker-leído | sí (→03/13) | — |
| F8 | T2-BASE-MECANISMO + BATTERY commands | base (punto) + battery + **CORE-GAP `H-5`** | base | ensamblador `agent_loop.py:83/160-165/176/185` + `runtime.py:371-374` + `execution/local/notification.py` abiertos 1→EOF (**ausencia de drenador verificada**) | sí (§2.3 `H-5` + §2.6·I1) | — |
| F9 | BATTERY memory (→13) | battery `memory` (13) | base | ensamblador `agent_loop.py:112-130/218` abierto | sí (🔀 §2.2) | eje persistencia |
| F10 | BATTERY skills (→12) | battery `skills` (12) | base | tracker-leído | sí (§2.3, →12) | — |
| F11 | T2-BASE-MECANISMO | base `loop` (cross 11) | base | ensamblador `agent_loop.py:195` (re-armado por turno) abierto | sí (→11) | — |
| F12 | T2-BASE-MECANISMO (seam invocado) | base `loop` | base | ensamblador `agent_loop.py:332-337` (call site) + productores abiertos `skills/skill_tool.py:119`, `native/todo_write.py:62`, `native/plan_mode.py:59/101`, `native/worktree.py:102/166`, `native/config.py:75` | sí (§2, 5 tools productores confirmados) | — |
| F13 | CLI-ONLY / INTERFAZ | integrador (`agentic_code`) | integrador | tracker-leído (⛔ CLI ps abierto) | sí (OI-6) | — |
| F14 | BATTERY commands + CLI-ONLY | battery + integrador (notify) | ambas | tracker-leído (depende F8) | sí (§2.2, OI-6) | — |
| G1 | T2-COSTURA + T2-BASE-MECANISMO | costura + cablear loop (01·CR2) + battery (12) | ambas | tracker-leído (seam sin consumidor, grep L09 de 01) | sí (§2.3 GAP-G1, →01) | (arg session roza id) |
| G2 | T3-INTEGRADOR / BATTERY budget | integrador (05) | ambas | tracker-leído | sí (OI-8) | eje persistencia (coste/tenant) |
| G3 | BATTERY structured-output (→09) | battery + driver (05) | ambas | tracker-leído | sí (OI-9, →09/05) | — |
| G4 | T1-MOTOR + T2-BASE-MECANISMO | costura motor + **CORE-GAP `B-usage`** (05) | base | ensamblador `agent_loop.py:253-254` abierto (= C12) | sí (§2.6·I2) | — |
| G5 ~~✅~~ **🟡** | T2-BASE-MECANISMO (abort) | base `loop` + 05 (cancel) + **corte real→16** | base | ensamblador `agent_loop.py:173/186` + `dispatcher.py:54` abiertos (cooperativo); cancel externo `runtime.py:187` homed 05; **`caller.py:188-190` + censo de providers abiertos en `08·CG-SIG-10` ⇒ el corte mid-stream NO ocurre** | sí (§2, →05, →`08·CG-SIG-10`) | — |
| G6 | T2-COSTURA storage (→15) + CLI-ONLY | costura storage (15) + integrador | ambas | tracker-leído | sí (OI-6, →15) | eje persistencia |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../02-loop.md`?** — **Sí**, líneas 1→365 (naturaleza, evidencia ejecutada, tablas A-G, resumen de estados, gaps priorizados, hallazgos de correctitud, §Plan de remediación LR1-LR6, ledger de cierre 2ª vuelta, re-visita L09). Además `00-LEGEND.md` (1→159) para el esquema.
2. **¿Reconcilia el conteo?** — features en `../02-loop.md` = **60** (A1-A5=5, B1-B10=10, C1-C12=12, D1-D7=7, E1-E6=6, F1-F14=14, G1-G6=6 ⇒ `5+10+12+7+6+14+6 = 60`); colocadas = **60**; sin colocar = **0**. ✅ *(**Corregido por `A-CIERRE-P4 §9.5·P4-02-18`**: esta pregunta declaraba **54** con los siete addendos correctos escritos al lado — nadie los sumó, y el «54» se propagó a `05·§3.2·Q2` como dato de apoyo. El tracker, por su parte, declara «46», con un tercer error propio: su tally por estado suma 52.)*
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, re-abierto en ESTE ciclo** (`agent_loop.py` 1→353 + `dispatcher.py` 1→85):
   - ✅: A1 `179/185/348` · C1 `247-281` · D7 `348-349` · F1 `287-323`+`dispatcher.py:36/76-77` · F12 `332-337` · ~~G5 `173/186`+`dispatcher.py:54`~~ (cancel externo `runtime.py:187` homed 05, no re-abierto aquí — es frontera G).
     **⚠ G5 retirada de esta lista (`A-CIERRE-P4 §14.8`, segundo caso de fallo de Q3 en este mismo doc, tras F8.)**
     Aquí Q3 falla por la **otra** punta que F8: en F8 el tramo abierto probaba el punto de registro pero no al
     productor; en G5 el tramo abierto prueba al **productor** de la señal (`agent_loop.py:173/186` sí la pone) y
     no al **consumidor efectivo** — el provider que debería cortar la lee con un atributo que el objeto no tiene.
     ⇒ **Regla de frontera de seam (consecuencia 32 de `§14.7`): cuando el consumidor de la costura vive en OTRO
     paquete, el ✅ exige abrir el consumidor, no el punto de entrega.** `08·CG-SIG-10` es el caso testigo y
     `02·G5` la segunda víctima. *Q3 debe leerse: «¿abrió el tramo, identificó al productor **y** abrió al
     consumidor cuando cruza paquete?»*
   - 🔀: A2 (ctx in-place) · C11 `267-270 vs 272-281 + 287-344`+`dispatcher.py:54-84` · E5 `143-146` · E6 `49-63` · F3 `287-344` · F4 `338-339/348` · ~~F8 `160-165/176`~~ · F9 `112-130/218`.
     **⚠ F8 retirada de esta lista (§2.6·I1).** Era el caso en que Q3 falla: abrir el tramo del ensamblador
     acredita que el **punto de registro** existe, **no** que alguien registre algo. El registrador real
     (`runtime.py:371-374`) sólo re-emite hooks del integrador ⇒ era **prueba de no-cableado** presentada como
     prueba de cableado. *Q3 debe leerse: «¿abrió el tramo **y** identificó al productor?»*
   - Los **ausentes-de-consumidor** (motores B/E1/D5 sin fire point, G1 seam sin invocar) se apoyan en la **ausencia** verificada por lectura del ensamblador (el `for` de turno 185-349 no llama compactación/budget/Stop; `HookEvent.STOP` no aparece en el fire path) — es prueba de **no-cableado**, no afirmación de cableado (Q3 aplica a afirmar cableado).
   - **⚠ Corrección de honestidad (auditada en el cierre, no en la 1ª emisión — el arnés debió forzarla en Q3, no un follow-up):** F12/F4 afirman seam-vivo por **dos puntas**; en la 1ª emisión sólo abrí el **call site** del loop y heredé los **productores** del tracker → por la regla dura eso era ⛔, no ✅. **Subsanado abriéndolos:** `context_modifier` = 5 tools (`skills/skill_tool.py:119`, `native/todo_write.py:62`, `native/plan_mode.py:59/101`, `native/worktree.py:102/166`, `native/config.py:75`); `ends_turn` = 2 tools (`native/plan_mode.py:106`, `native/ask_user.py:97`). La clasificación no cambia; la evidencia pasó de heredada a propia.
   - **Evidencia heredada declarada (no re-abierta, destino 05):** G5 cancel externo (`runtime.cancel`→`registry.kill`) y F8 drain raíz (`runtime.py:372-374`) — lado-loop abierto; lado-`runtime.py` se apoya en la 2ª vuelta. Frontera-G → **05·execution**.
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla 5 obligaciones (OI-6…OI-10) con los 6 campos L05; los CLI-ONLY (C6/C8/F5/F13/E4/G6-replay) y T3 (A3/E3/G2/G3) se vierten ahí, ninguno cerrado con "→ integrador" a secas. *(El vertido formal a `00-INTEGRADORES.md` se hace en A1.7, como en 01.)*
5. **¿Doble filo (L10)?** — **Parcialmente, y la respuesta original era un falso negativo (§2.6·I5).** Sostiene: los 4 motores siguen **CORE-GAP** sin degradarse; C11 se mantiene 🔀 (invariante por diseño, verificado en la re-visita L09); A3/C6/C8/F5/F13 son capa de interfaz/observabilidad del integrador. **No sostiene:** (a) `B-usage` y `B-02` **sí** eran deuda A↔B —recalificados a CORE-GAP, I2/I3—; sólo `path-legacy` es DEUDA-B pura. (b) **`F8` era un ❌ vestido de 🔀** (I1). **Dos dobles filos quedan ABIERTOS, no resueltos:** `E4` (⛔ posiblemente sobre-extendido: `saveCacheSafeParams`/`cleanupComputerUseAfterTurn` no son UI) y `F9` («efecto cercano» concluido tras borrar el criterio `readFileState` en que difieren).

### 3.3 VEREDICTO

> **⚠ Revisado por `A-CIERRE-P4 §9` (2026-07-28).** El «✅ nada pendiente» de abajo era correcto **como reparto**
> y falso **como estado**: 15 celdas venían comprimidas con pérdida, la §Evidencia se había perdido entera, el
> conteo estaba mal en 4 sitios y **5 veredictos habían sido invertidos aguas abajo** (§2.6). Todo ello queda
> remediado *in situ*; lo que sigue abierto y **no** se cierra aquí: los dos dobles filos de Q5 (`E4`, `F9`), la
> decisión `18·FaR2`↔`18·N1`, y el hecho de que la columna de contraparte canónica no existe en este esquema
> (`P4-01-1` ⇒ P6″).
>
> **⚠ Segunda revisión — `A-CIERRE-P4 §14.8` (2026-07-29), desde el par 08.** `G5` baja de **✅ a 🟡** (`§2.6·I6`)
> y `F6` recibe su causa real. **El «✅ REPARTO COMPLETO» de abajo se sostiene** —el reparto de las 60 features no
> cambia— pero la afirmación final *«ninguno es pendiente de verificación»* **deja de ser cierta**: el efecto
> observable del abort **depende de una decisión de contrato que no vive aquí** (`16`, `08·CG-SIG-10`, `D-06·3`).
> Se anota como **pendiente de verificación con dueño ajeno**, no como pendiente propio.

**✅ REPARTO COMPLETO (60/60) → A1.5 (05·execution).**
Las 60 features repartidas con TIER+destino (base-mecanismo del esqueleto + 4 batteries `compaction`/`budget`/`commands`/`structured-output` + costuras `ModelCallerProtocol`/`CompactionProvider`/`HookRunner`/`RetryPolicy`/`UserInputProcessor`/usage + 5 obligaciones de integrador). CORE-GAPs para DEUDA-A: GAP-L4/L3/L1-L1b/C4 (los 4 motores) + A4/C10/F10/F2(**K1**) + **`B-usage`** + **`H-5`** (drenaje, nuevo aquí) + los cabos GAP-L2→05 y GAP-G1→01. DEUDA-B: **sólo** path-legacy→18·FaR2 (acoplado a `18·N1`); residuales `DB-14`/`DB-15`/`DB-19`. Cabos con destino explícito (05·execution: A4/A5/C3/G1-G6 frontera del driver; 06·hooks: D3/D5/E2/F2 fire points; 16·models: C2/C3/C4-fallback/B8; 09·tools: C10/G3; 12·skills: F10/G1-commands; 13·memory: E2/F9; 11·mcp: F11; 15·storage: G6; 03·context: F7; 01·contracts: A5/G1 cabling ya desarrollado en CR1/CR2; A3·DA transversal: usage) — ninguno es pendiente de **verificación**.
