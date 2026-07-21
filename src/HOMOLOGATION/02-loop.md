# 02 · loop

**Fase:** validación 2ª vuelta + **re-visita de completitud L09 (2026-07-18)** — C11/FIND-L1 reclasificado
🟡→🔀; código intacto.
**Runtime:** `src/agentic_runtime/loop/{agent_loop.py (352 LOC),basic.py,factory.py,protocol.py}`
**Canónico (leído ÍNTEGRO, no por hitos):**
`query.ts` (1729 LOC), `QueryEngine.ts` (1295 LOC), `query/config.ts` (46), `query/deps.ts` (40),
`query/stopHooks.ts` (473), `query/tokenBudget.ts` (93).

## Naturaleza del subsistema
El `AgentLoop` es el corazón del turno agente. El canónico lo reparte en DOS capas que hay que
separar para no misatribuir:
- **`query()`/`queryLoop()`** = el bucle de turnos (streaming del modelo → tool-use → recompactación
  → stop-hooks → continuación). Es el par directo de `AgentLoop.run`.
- **`QueryEngine.submitMessage()`/`ask()`** = el **driver de sesión** que envuelve `query()`
  (preproceso de input, usage/coste, maxBudgetUsd, structured output, persistencia, result codes).
  En el runtime, esa capa vive en **`execution/local/runtime.py` (`LocalAgentRuntime._run_loop`)**, NO
  en el loop. Se contrasta a fondo en **05·execution**; aquí solo se marca la frontera para clasificar
  correctamente cada feature (⇒05 = "el ajuste pertenece a execution").

Regla de lectura aplicada (política de exhaustividad): ambas contrapartes se leyeron completas.
Leer las cabeceras/helpers de `query.ts` (1-180) reveló `yieldMissingToolResultBlocks` — invariante de
API que una lectura "por hitos" habría omitido (ver FIND-L1).

## Evidencia ejecutada
- **Lint** (subsistema `loop/`): `ruff` ✅ · `mypy` ✅ (5 archivos, sin issues) · `bandit` ✅ (sin hallazgos).
- **Tests**: `test_basic_loop.py` (5) ✅ + nuevo `test_loop_homologation.py` → **14 passed, 5 xfailed**.
  - Sintéticos (fakes): inserción de prompt, multi-turno hasta agotar tool_calls, gate PreToolUse
    (deny + updatedInput), `ends_turn` (HITL), recall como `<system-reminder>` con dedup, filtro de pool
    de subagente (background + `agent_allowed_tools`), `system_override`, abort pre-inicio y entre turnos,
    techo `_MAX_TURNS`.
  - e2e real (dispatcher/pool/EventBus vía `create_runtime`): multi-turno con dispatch real + stream que
    surface `ToolCall→ToolResult→Token→Done`.
  - `xfail(strict)` = evidencia de gap (GAP-L1 Stop hook, GAP-L1b PostToolUse, GAP-L2 maxTurns
    configurable, GAP-L3 fallback model, GAP-L4 motor de compactación).

## Tabla feature-by-feature

### A · Estructura del bucle de turnos (`queryLoop`)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| A1 | Inserción del prompt como user y bucle hasta que un turno no pida tool-use | `run()`: append user + `for _turn in range(_MAX_TURNS)` | ✅ | `needsFollowUp` ≡ `done.stop_reason=="tool_calls"`/`tool_calls` presentes. Verificado e2e. |
| A2 | `State` inmutable-params vs struct mutable entre iteraciones (reducer-friendly) | `ctx` mutado in-place + locales por turno | 🔀 | Estructural. El canónico aísla `State`/`QueryConfig`/`deps` para un futuro `step()` puro; el runtime muta `ctx`. Comportamiento equivalente. **Ajuste**: opcional; si se busca testabilidad de reducer, extraer estado de turno. |
| A3 | `queryTracking` (chainId/depth) para analítica de cadena | — | ⛔ | Telemetría de árbol de queries. Fuera de core. |
| A4 | Terminal con **reason codes** (`completed`/`aborted_*`/`max_turns`/`prompt_too_long`/`model_error`/`hook_stopped`/`stop_hook_prevented`/`blocking_limit`/`image_error`) | `run()` retorna `None`; el status lo fija `execution` (completed/failed/killed) | 🟡 | El loop no devuelve una causa estructurada de terminación. **Ajuste (⇒05)**: introducir un `LoopOutcome`/reason para que `execution` distinga fin normal vs abort vs límite vs error del modelo, hoy colapsados. |
| A5 | Techo de turnos = `maxTurns` **configurable** por el consumidor + attachment `max_turns_reached` | `_MAX_TURNS=50` constante | ❌ | **GAP-L2**. Solo hay un techo de seguridad hardcodeado. **Ajuste**: `max_turns` inyectable (constructor/`RuntimeTask`) + señal de terminación por límite. xfail `test_loop_accepts_configurable_max_turns`. |

### B · Recompactación / presupuesto de contexto (pre-modelo)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| B1 | `getMessagesAfterCompactBoundary` (vista tras la última compactación) | — | ❌ | Sin fronteras de compactación no hay recorte de vista. Depende de B3-B6. |
| B2 | `applyToolResultBudget` (cap de tamaño agregado de tool results + `recordContentReplacement`) | — | ❌ | El loop no acota el tamaño de resultados de tools reingresados. **Ajuste**: presupuesto por-mensaje de tool_result (evita reventar el contexto con salidas gigantes). |
| B3 | `snipCompact` (HISTORY_SNIP) | — | ❌ | Poda de historia. |
| B4 | `microcompact` (deps, edición de caché + boundary diferido por `cache_deleted_input_tokens`) | — | ❌ | Microcompactación por tool_use_id. |
| B5 | `contextCollapse` (proyección + colapsos por turno) | — | ❌ | Colapso de contexto. |
| B6 | `autocompact` (deps + circuit-breaker `consecutiveFailures` + `AutoCompactTrackingState` + evento `tengu_auto_compact_succeeded`) | — | ❌ | **Motor de compactación ausente en el loop.** `CompactionProvider` (contracts, 01·feat 9 🟡) existe pero el loop NO lo consulta; `execution/local/summarizer.py` solo condensa el OUTPUT de un subagente background, no la historia del turno. **GAP-L4**. **Ajuste holístico**: cablear un motor de compactación (trigger por umbral/tokens + estrategia via `CompactionProvider`) en el loop pre-modelo. xfail `test_loop_wires_compaction_engine`. |
| B7 | `buildPostCompactMessages` + yield del boundary | — | ❌ | Depende de B6. |
| B8 | `task_budget.remaining` (carryover a través de compactaciones; beta API) | — | ⛔ | Feature de presupuesto server-side (beta `task-budgets-2026-03-13`). Fuera de core por ahora. |
| B9 | Blocking-limit preempt (`calculateTokenWarningState`/`isAtBlockingLimit` → error sintético PTL) | — | ❌ | Sin este guard, un contexto sobre-límite va directo a la API y falla sin reserva para `/compact`. Depende del contador de tokens (B10). |
| B10 | Contador de tokens con estimación (`tokenCountWithEstimation`, `finalContextTokensFromLastResponse`) | — | ❌ | El loop no contabiliza tokens de contexto. Prerrequisito de B2/B6/B9 y del token-budget (E1). |

### C · Llamada al modelo y streaming
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| C1 | Consumo del stream: tokens / tool_use / done + persistir assistant | `async for event in stream`: Token/ToolCall/Done/Error | ✅ | Abstracción por `Event` (runtime) vs SDK-messages (canónico). Verificado e2e. |
| C2 | Superficie de opciones a `callModel` (thinkingConfig, fastMode, effortValue, advisorModel, mcpTools, agents, fallbackModel, taskBudget, maxOutputTokensOverride, queryTracking) | `complete(messages,tools,stop,model_id,system_sections?,system_override?)` | 🟡 | El loop plumbe una superficie mucho menor. `thinking`/`fastMode`/`effort`/`advisor`/`mcpTools` no pasan por el loop. **Ajuste**: decidir cuáles son core (thinking/effort probablemente sí) y ampliar `ModelCallerProtocol`/plumbing; el resto delegado al caller (`agentic_models`). Se cruza con 16·models. |
| C3 | `getRuntimeMainLoopModel` (plan-mode + `>200k` ⇒ cambio de modelo) | modelo fijo `model_id` por loop | 🟡 | El loop no reevalúa modelo por turno según modo/tamaño. El modelo de subagente SÍ se resuelve, pero en `execution` (`resolve_subagent_model`), no aquí. **Ajuste (⇒05/16)**: resolución de modelo por turno (plan-mode/200k) o documentar que el caller lo absorbe. |
| C4 | `fallbackModel` + `FallbackTriggeredError` ⇒ cambiar modelo y **reintentar** el request (`attemptWithFallback`) + tombstones de mensajes huérfanos + `stripSignatureBlocks` | ErrorEvent ⇒ append `[error]` + break | ❌ | **GAP-C4** (corregido en 2ª vuelta; antes decía GAP-L3, que es el token-budget de E1). Sin fallback ni reintento; un fallo del primario termina el turno. Canónico verificado 2ª vuelta: `query.ts:650-655` `attemptWithFallback` loop, `894-897` `FallbackTriggeredError`→`currentModel=fallbackModel`. **Ajuste**: soporte de modelo(s) de fallback con reintento limpio (descartar parciales). xfail `test_loop_accepts_fallback_model`. |
| C5 | Streaming fallback (`onStreamingFallback`) ⇒ tombstone + reset de executor | — | ❌ | Depende de C4. |
| C6 | `backfillObservableInput` (clonar msg, añadir campos derivados para transcript/SDK) | — | ⛔ | Presentación/transcript; no afecta lo que va a la API. |
| C7 | Withhold de errores recuperables (PTL/media/max_output) hasta saber si hay recuperación | — | ❌ | Depende de las rutas de recuperación (D). Sin ellas el error se surface directo. |
| C8 | `createDumpPromptsFetch` (debug ant) | — | ⛔ | Debug interno. |
| C9 | `pendingCacheEdits` (boundary de microcompact con `cache_deleted_input_tokens` reales) | — | ❌ | Depende de B4. |
| C10 | `ImageSizeError`/`ImageResizeError` ⇒ `image_error` | — | ❌ | Manejo de errores de imagen. Se cruza con tools multimodales. |
| C11 | `yieldMissingToolResultBlocks` — **garantiza que TODO `tool_use` reciba un `tool_result`** aun en error/abort (invariante de la API) | El invariante se garantiza por **buffer-then-commit**: la rama `ErrorEvent` hace `break` en 267-270 **ANTES** de persistir (272-281); todo `tool_calls` que sí se persiste se parea 1-a-1 en 287-344 | 🔀 | **FIND-L1 RECLASIFICADO 🟡→🔀 (re-visita de completitud L09, 2026-07-18).** La 1ª/2ª pasada lo marcó 🟡 (riesgo de assistant con `tool_calls` sin parear ⇒ API-400) asumiendo *persist-then-error*. Al **abrir el código y seguir el dato**: el error-mid-stream hace `break` en **267-270 ANTES** del bloque de persistencia (272-281) ⇒ los `tool_calls` buffered se **descartan** (solo se appendea `[error]`), nunca se persiste un assistant con `tool_calls` colgante. Y cuando SÍ se persisten (281), el bucle 287-344 appendea un `tool` message por CADA call (rama no-dispatcher 289 / block 311 / dispatch 319) y el dispatcher **nunca lanza** (envuelve todo en `ToolResult.aborted/error/timeout`, dispatcher.py:54-84). ⇒ el invariante se **reproduce por diseño**, con mecanismo distinto al canónico (`yieldMissingToolResultBlocks` *sintetiza*; B *evita la situación descartando*). Abort cubierto (dispatcher `aborted`, 54-55). **No requiere remediación** — la recuperación de error del modelo (retry/fallback) es harina aparte: GAP-C4/LR2. |
| C12 | Acumulación de **usage/tokens** (`updateUsage`/`accumulateUsage`, `message_delta` stop_reason) | `DoneEvent.usage` existe pero el loop NO lo lee; `session.usage` queda en 0 | 🟡 | **FIND-L2**. `LocalAgentRuntime.complete(... input_tokens=session.usage.input_tokens)` reporta siempre 0 porque nada propaga `DoneEvent.usage` a la sesión. **Ajuste (loop⇄execution)**: el loop debe acumular `DoneEvent.usage` en `ctx`/sesión para que el accounting no sea nulo. |

### D · Recuperación post-stream (rama sin tool-use)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| D1 | Recuperación PTL: collapse-drain ⇒ reactive-compact (single-shot cada uno) | — | ❌ | Depende de B5/B6. Sin recuperación, PTL termina el turno. |
| D2 | Recuperación `max_output_tokens`: escalar 8k→64k, luego mensajes de "resume" multi-turno (límite 3) | — | ❌ | El runtime no distingue truncamiento por tokens de salida. **Ajuste**: detectar la causa y reintentar/continuar. |
| D3 | `executePostSamplingHooks` tras respuesta del modelo | — | ❌ | Ver GAP-L1b (hooks post-muestreo/post-tool no cableados). |
| D4 | Skip stop-hooks si el último mensaje es API-error (anti death-spiral) | N/A | ⛔ | Consecuencia de no tener stop-hooks (D5). |
| D5 | `handleStopHooks` (Stop/SubagentStop) + blocking errors + `preventContinuation` + `stopHookActive` retry | Loop: nada. `SUBAGENT_STOP` se dispara en `execution` tras el loop (solo subagentes) | ❌ | **GAP-L1**. El fin de turno del loop no corre Stop hooks. El `HookEvent.STOP` está DEFINIDO pero jamás se dispara; `SUBAGENT_STOP` sí (execution, post-loop) ⇒ homologación parcial solo para subagentes. **Ajuste holístico**: disparar Stop/SubagentStop al cerrar el turno, con soporte de `preventContinuation` (re-entrar) y blocking errors. xfail `test_loop_fires_stop_hook_at_turn_end`. |
| D6 | Token budget (+500k auto-continue) — ver E1 | — | ❌ | GAP-L3 (tokenBudget). |
| D7 | `return completed` en fin de turno normal | `break` del for | ✅ | Comportamiento observable equivalente (con la salvedad de A4). |

### E · Stop-hooks, token-budget, config, deps (archivos auxiliares)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| E1 | `checkTokenBudget` (tokenBudget.ts): continuación +500k con nudge, `diminishingReturns`, completion event | — | ❌ | **GAP-L3**. Sin auto-continuación por presupuesto de tokens. **Ajuste**: motor de budget con `BudgetTracker` + mensaje de continuación (requiere C12/B10). |
| E2 | stopHooks: `executeExtractMemories` en fin de turno | — | ❌ | Extracción de memorias al cerrar turno. Se cruza con 13·memory; hoy no lo dispara el loop. |
| E3 | stopHooks: `executeTaskCompletedHooks` + `executeTeammateIdleHooks` (teammates) | — | ⛔ | **RESUELTO (decisión 2026-07-11).** Estos hooks solo se disparan bajo la topología **coordinator/swarm** (`coordinator/coordinatorMode.ts` + `utils/swarm/inProcessRunner.ts`): teammates líder/worker in-process que se mensajean vía `SendMessageTool` y notifican idle al líder. En el canónico va gateada tras `feature('COORDINATOR_MODE')` + env `CLAUDE_CODE_COORDINATOR_MODE` (opt-in/experimental). El runtime modela padre→subagente (fork/background/tasks), NO pares-teammates (grep = 0). **Fuera de alcance del core como gap del loop**: si `agentic_assistant` adopta colaboración multi-agente, será un **subsistema nuevo** (coordinator/swarm + `SendMessage`/`TeamCreate`/`TeamDelete`/`SyntheticOutput` como INTERNAL_WORKER_TOOLS), no un feature pendiente de 02·loop. |
| E4 | stopHooks: `executePromptSuggestion`, `executeAutoDream`, job classifier, `saveCacheSafeParams`, `cleanupComputerUseAfterTurn`, summary+notifications | — | ⛔ | Background bookkeeping / UI / dogfooding (chicago MCP). Fuera de core. |
| E5 | `buildQueryConfig` (config.ts): snapshot `sessionId` + gates statsig/env (`streamingToolExecution`,`emitToolUseSummaries`,`isAnt`,`fastMode`) | flags por constructor del `AgentLoop` | 🔀 | Gates de infraestructura (statsig/env). El runtime los expresa como flags de construcción/capacidad del caller (`supports_native_tool_search`). Equivalente de intención. |
| E6 | `productionDeps` (deps.ts): DI de `callModel`/`microcompact`/`autocompact`/`uuid` para tests | DI por constructor de `model_caller`/`tool_dispatcher` | 🔀 | Mismo patrón (inyección de I/O para tests). El runtime no tiene `microcompact`/`autocompact` que inyectar (ausentes, B4/B6). Al portar B, replicar el seam de deps. |

### F · Tool-use dispatch y fin de turno con tools
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| F1 | Ejecutar tool calls y reingresar resultados como contexto | `for tc in tool_calls`: dispatch ⇒ append role:tool | ✅ | Verificado e2e (multi-turno). |
| F2 | Gate `canUseTool` (allow/deny/ask + updatedInput) integrado en el executor | Hook `PRE_TOOL_USE`: `block`⇒deny, `modified_input`⇒updatedInput | 🟡 | Cubre deny + updatedInput. **Falta**: `ask`/HITL como comportamiento del gate y los **permission modes** (acorde a GAP-02 de 01·contracts: hoy plan-mode se lee de `app_state.native["plan_mode"]` dentro del hook del integrador). **Ajuste**: el gate del loop debe consultar modo+reglas (ver GAP-02), no solo block/modified. |
| F3 | `StreamingToolExecutor` (ejecución **concurrente** y en streaming DURANTE el stream del modelo) + fallback `runTools` | Dispatch **secuencial** post-stream | 🔀 | Divergencia de rendimiento/latencia: el runtime no ejecuta tools mientras el modelo aún transmite ni en paralelo. **Ajuste**: evaluar un executor concurrente (gate `streamingToolExecution`); hoy el modelo secuencial es correcto pero más lento. |
| F4 | `hook_stopped_continuation` desde una tool ⇒ `shouldPreventContinuation` ⇒ `hook_stopped` | `ends_turn` en el `ToolResult` ⇒ cerrar turno | 🔀 | Mecanismos distintos para "una tool cierra el turno". El runtime usa `ends_turn` (AskUserQuestion/plan_mode); el canónico un attachment de hook. Equivalente funcional; documentado. |
| F5 | `generateToolUseSummary` (Haiku, IDs, para UI móvil) | — | ⛔ | Resumen para UI móvil. Fuera de core. |
| F6 | Abort durante tools ⇒ interrupción + `aborted_tools` + check maxTurns | dispatcher chequea `ctx.stop` (devuelve aborted); el loop no reevalúa abort entre tools | 🟡 | El abort se honra a nivel dispatcher (cada call), pero el loop no corta el batch a mitad ni emite interrupción estructurada. **Ajuste**: chequear `ctx.stop` entre tool calls y en mid-stream (hoy solo en fronteras de turno). |
| F7 | `getAttachmentMessages` (cambios de fichero, comandos en cola, memory prefetch, skill prefetch) al final del turno | Recall inyectado al INICIO del turno (`_inject_recall`) | 🟡 | El runtime rinde recall/secciones al inicio vía `capability_manager`; NO tiene el pipeline de attachments de fin de turno (edited-file diffs, prefetch de memoria/skills consumidos post-tools). **Ajuste**: cubrir en 03·context/13·memory qué attachments son core. |
| F8 | Drain de comandos en cola (`getCommandsByMaxPriority`, prompt/task-notification, exclusión de slash) con scoping por agente | `register_turn_start_hook` drena `BackgroundNotificationChannel` al INICIO del turno | 🔀 | Placement (inicio vs fin) y alcance distintos. El runtime drena notificaciones de subagentes; el canónico además inyecta prompts encolados del usuario y notifica lifecycle. **Ajuste (⇒04/05)**: alinear semántica de cola (qué se drena, cuándo, scoping main/subagente). |
| F9 | Memory prefetch consume (`startRelevantMemoryPrefetch`/`filterDuplicateMemoryAttachments`) | Recall síncrono por `capability_manager.active_context` | 🔀 | El canónico hace prefetch asíncrono (arranca en turno-0, consume cuando resuelve) filtrando por `readFileState`; el runtime lo hace síncrono con dedup contra la historia. Comportamiento cercano, mecanismo distinto. Se cruza con 13·memory. |
| F10 | Skill discovery prefetch inject | — | ❌ | Prefetch de descubrimiento de skills. Se cruza con 12·skills. |
| F11 | `refreshTools` entre turnos (MCP recién conectado disponible) | `_build_tool_pool` reensambla el pool CADA turno (native+capability) | 🟡 | El runtime reensambla por turno, lo que puede recoger MCP nuevas si el `capability_manager` las expone; falta verificar que la reconciliación MCP (11) refresca el pool. **Ajuste (⇒11)**: confirmar que el reensamblado ve servidores MCP conectados a mitad de sesión. |
| F12 | `context_modifier`/`newContext` tras una tool (skills⇒allowed-tools, worktree/plan⇒estado) | `result.context_modifier(ctx)` in-place | ✅ | Espejo directo. Verificado en tests de skills/plan (subsistemas 12/14). |
| F13 | `taskSummary` periódico (`claude ps`) | — | ⛔ | Resumen de sesión para `claude ps`. Fuera de core. |
| F14 | `consumedCommandUuids` + `notifyCommandLifecycle` (started/completed) | — | ⛔/❌ | Lifecycle de comandos encolados. Depende de F8. |

### G · Frontera con el driver de sesión (`QueryEngine`/`ask`) — pertenece a 05·execution
| # | Feature canónica | Runtime (`LocalAgentRuntime`) | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| G1 | `processUserInput` (slash commands, `allowedTools`, override de modelo, `resultText` de comandos locales) antes del bucle | — | ❌ | **GAP-01** (de 01·contracts): `UserInputProcessor` existe pero ni el loop ni `execution` lo invocan. **Ajuste**: cablear el preproceso de input (slash/inline) antes del turno. |
| G2 | `maxBudgetUsd` ⇒ `error_max_budget_usd` | — | ❌ | **RESUELTO (2026-07-11): EN ALCANCE de 05·execution** (no ⛔). Parámetro de entrada del driver de sesión (`QueryEngine`, líneas 147/972-990), expuesto por `entrypoints/sdk/coreSchemas.ts` + `cli/print.ts`; compara `getTotalCost()` y emite `error_max_budget_usd`. Un cap de coste por request tiene sentido para un asistente hosted multi-tenant. **Prerrequisitos**: accounting de usage (FIND-L2/C12, hoy 0) + tabla de coste por modelo (⇒16·models). **Ajuste (⇒05)**: cap de coste en el driver de sesión, no en el loop. |
| G3 | Structured output (`jsonSchema`+`SyntheticOutputTool`) + límite de reintentos | — | ❌ | **RESUELTO (2026-07-11): EN ALCANCE de 05·execution/09·tools** (no ⛔). Parámetro de entrada del driver (`QueryEngine` líneas 149/331/662-671/1149): fuerza resultado conforme a `jsonSchema` vía `SyntheticOutputTool`. Plausiblemente necesario para el **BFF** (endpoints tipados: clasificar/extraer). **Ajuste (⇒09)**: portar `SyntheticOutputTool` + (⇒05) plumbing de `jsonSchema` y límite de reintentos en el driver de sesión. |
| G4 | Usage/coste (`totalUsage`, `getTotalCost`, `getModelUsage`) + `lastStopReason` | `session.usage` (hoy 0 — ver FIND-L2/C12) | 🟡 | Estructura existe, no se llena. **Ajuste**: ver C12. |
| G5 | `interrupt()` ⇒ `abortController.abort()` | `runtime.cancel(task_id)` ⇒ cancela el `asyncio.Task` | ✅ | Homologación de comportamiento (cancelación). Verificado en `test_runtime_e2e`. |
| G6 | Persistencia de transcript (`recordTranscript`/`flushSessionStorage`), system-init msg, file-history, replay, partial messages | `_persist` (execution) / — | ⛔/🟡 | Persistencia ⇒ 15·storage/05. Replay/partial/system-init/file-history = SDK/UI ⇒ ⛔. |

## Resumen de estados
Sobre 46 features enumeradas:
- ✅ **7** (A1, C1, D7, F1, F12, G5, y el equivalente de terminación normal).
- 🟡 **11** (A4, C2, C3, C12/FIND-L2, F2, F6, F7, F11, G4; + B-parciales dependientes). *(C11/FIND-L1 reclasificado 🟡→🔀 en la re-visita L09 2026-07-18.)*
- 🔀 **8** (A2, E5, E6, F3, F4, F8, F9, C11/FIND-L1).
- ❌ **~15** (A5, B1-B7·B9·B10, C4, C5, C7, C9, D1, D2, D3, D5, E1, E2, F10, G1, G2, G3).
- ⛔ **~11** (A3, B8, C6, C8, C10?, E3, E4, F5, F13, F14, G6-parcial). *(E3 reclasificado ⛔ el 2026-07-11.)*

El loop del runtime homologa fielmente el **esqueleto** del turno (prompt → stream → tool-use → reingreso →
stop). Lo AUSENTE es sistémico y agrupable en cuatro motores no portados: **(1) compactación/presupuesto de
contexto** (B/E1), **(2) recuperación de errores del modelo** (C4/C5/C7/D1/D2), **(3) stop-hooks de fin de
turno** (D3/D5), **(4) preproceso de input** (G1). Más **un** hallazgo de correctitud de la lectura íntegra
que persiste: **FIND-L2** (usage a 0). *(FIND-L1 —pareo tool_use↔tool_result— quedó descartado como bug en la
re-visita L09 2026-07-18: el invariante se mantiene por diseño; reclasificado 🔀.)*

## Gaps priorizados (para fase de implementación)
- **GAP-L1 (❌)** Stop/SubagentStop hooks no se disparan al cerrar el turno (solo SUBAGENT_STOP en execution, subagentes). *Arquitectural.*
- **GAP-L1b (❌)** PostToolUse/post-sampling hooks no cableados pese a estar en el enum `HookEvent`.
- **GAP-L2 (❌)** `maxTurns` no configurable (solo techo `_MAX_TURNS=50`).
- **GAP-L3 (❌)** Sin token-budget (+500k auto-continue) ni contador de tokens (prerrequisito compartido con B).
- **GAP-L4 (❌)** Sin motor de compactación en el loop (`CompactionProvider` de contracts sin consumidor).
- **GAP-C4 (❌)** Sin fallback model / reintento ante fallo del primario.
- **GAP-G1 (❌ = GAP-01 de 01·contracts)** `UserInputProcessor` no cableado (slash/inline sin preproceso).

## Hallazgos de correctitud (de la lectura íntegra — NO simples ausencias)
- **FIND-L1 (🔀 — DESCARTADO como bug en la re-visita L09 2026-07-18)** ~~El pareo `tool_use ↔ tool_result` no
  está garantizado en la rama `ErrorEvent`~~. **Verificado abriendo B y siguiendo el dato**: el invariante SÍ se
  garantiza. El error-mid-stream hace `break` en `agent_loop.py:267-270` **ANTES** de persistir (272-281) ⇒ los
  `tool_calls` buffered se descartan, jamás se persiste un assistant con `tool_calls` colgante; y todo `tool_calls`
  que sí se persiste se parea 1-a-1 en 287-344 (el dispatcher nunca lanza, dispatcher.py:54-84). B reproduce el
  invariante por **buffer-then-commit** (mecanismo distinto al `yieldMissingToolResultBlocks` canónico, que
  sintetiza). La premisa "persist-then-error" de la pasada previa era un **misread** — además internamente
  inconsistente con LR2, que describe correctamente `error → [error] + break` en 267-270. **Sin remediación** (la
  recuperación de error del modelo es GAP-C4/LR2, otra cosa).
- **FIND-L2 (🟡)** `DoneEvent.usage` no se propaga: `session.usage` (y por ende
  `input_tokens/output_tokens` reportados por `LocalAgentRuntime.complete`) quedan en 0. Accounting nulo.

## Preguntas abiertas — RESUELTAS (2026-07-11)
- **Teammates/teams** (E3): **⛔ N/A core.** Topología coordinator/swarm (líder/worker in-process, `SendMessage`, idle→líder), gateada/experimental en el canónico; el runtime modela subagentes, no teammates-pares. Si se adopta ⇒ **subsistema nuevo**, no gap del loop.
- **maxBudgetUsd** (G2): **❌ EN ALCANCE de 05·execution.** Cap de coste por request (hosted multi-tenant). Prerrequisito: usage accounting (FIND-L2) + coste por modelo (16).
- **structured output** (G3): **❌ EN ALCANCE de 05·execution/09·tools.** Salida conforme a `jsonSchema` vía `SyntheticOutputTool`; probable necesidad del BFF (endpoints tipados).

## Notas para pasadas 2/3
- ~~Escribir el test de FIND-L1~~ (descartado en la re-visita L09 2026-07-18: no es un bug). Sí escribir el de
  FIND-L2 (assert usage>0) como xfail cuando se aborde la implementación.
- La compactación (B), el token-budget (E1) y el contador de tokens (B10) comparten prerrequisito
  (contabilidad de tokens) ⇒ portarlos juntos.
- Confirmar en 05·execution si el `LoopOutcome`/reason (A4) debe nacer en el loop o en execution.
- Al portar B, reusar el patrón `deps` (E6) para inyectar el motor de compactación en tests.

---

## Plan de homologación / remediación desarrollada

Diseño por finding. Lo AUSENTE de 02 se agrupa en **cuatro motores no portados** + el invariante de pareo
(FIND-L1) + cabos que aterrizan en otros subsistemas. Seam real: `loop/agent_loop.py` (`AgentLoop.run`
352 LOC, leído íntegro): turno = ensamblar pool → deferred → system_sections/recall → `complete()` →
consumir stream (Token/ToolCall/Done/Error) → persistir assistant → ejecutar tools (PreToolUse gate +
dispatch + context_modifier/ends_turn) → decidir continuar. **Nota de hogar**: FIND-L2/usage y el gate de
permisos (F2) son **Deuda B** (`B-usage`, `B-02`); aquí se desarrollan los 4 motores + FIND-L1, que SÍ
son Deuda A de 02 (su hogar es el loop).

### LR1 · Motor #1 — compactación / presupuesto de contexto (GAP-L4, B4 microcompact, E1 token-budget=GAP-L3)
- **Comportamiento**: cuando el historial se acerca al límite de la ventana, el loop **compacta** (resume
  segmentos viejos preservando head/anchor/tail) en vez de crecer sin cota; microcompact edita la caché por
  `tool_use_id`. Emite `compact_boundary` (07·H1) para que memoria (13) re-surface.
- **Seam/firma**: reutilizar el contrato ya existente `contracts/compaction.py`
  (`CompactionProvider.compact_context` + `collect_compaction_context`) — el **aporte** de providers ya
  está; falta el **motor**. Nuevo `loop/compaction.py::ContextBudget` con `should_compact(ctx,
  model_id) -> bool` (estimación de tokens vs % de ventana) + `compact(ctx, providers) -> ToolUseContext`
  (recorta `ctx.messages`, inserta el resumen de `collect_compaction_context`, marca boundary).
- **Cableado**: en `run()`, al inicio de cada iteración de turno (tras `ctx.turn_count += 1`,
  `agent_loop.py:189`): `if budget.should_compact(ctx, model_id): ctx = budget.compact(ctx, providers);
  emit(CompactBoundaryEvent)`. El trigger/presupuesto se inyecta por `deps` (E6) para tests.
- **Orden**: independiente; habilita 07·H1 y el re-surface de 13.
- **Test**: `test_loop_compacts_when_over_budget` (historial gigante → `len(ctx.messages)` cae + boundary emitido).

### LR2 · Motor #2 — recuperación de errores del modelo / fallback + retry (GAP-C4 fallback; api_retry 07·J3)
- **Comportamiento**: un `ErrorEvent` del modelo hoy **termina el turno** (`agent_loop.py:267-270`: append
  `[error]` + break). El canónico (a) **reintenta** con backoff (emite `api_retry`), y (b) ante
  `FallbackTriggeredError` cambia a `fallbackModel` y **reintenta** limpiando parciales (tombstones de
  mensajes huérfanos + `stripSignatureBlocks`).
- **Seam/firma**: `AgentLoop.__init__` acepta `fallback_model_id: str | None` + `retry_policy: RetryPolicy`
  (`max_retries`, `backoff_ms`, `retryable(error) -> bool`). El request al modelo (`complete`) se envuelve
  en `_attempt_with_fallback(...)` que reintenta y, si el error es de fallback, re-llama con
  `fallback_model_id` tras **descartar los tokens/tool_calls parciales del intento fallido** (no persistir el
  assistant a medias — respeta FIND-L1).
- **Cableado**: reemplazar el bloque `if error is not None: break` por el reintento; emitir `api_retry`
  (07·J3) por intento. La superficie de opciones del modelo (thinking/effort) es **16** (C2).
- **Orden**: independiente; toca 07 (evento `api_retry`) y 16 (fallback model id).
- **Test**: `test_loop_retries_then_fallbacks` (xfail `test_loop_accepts_fallback_model` ya existe).

### LR3 · Motor #3 — stop-hooks de fin de turno (GAP-L1/L1b, = 06·FIND-HOOK6/HOOK9)
- **Comportamiento**: al decidir terminar el turno, el canónico dispara `Stop`/`SubagentStop` hooks que
  pueden **preventContinuation** (re-loop: el agente sigue) o **blockingError** (mensaje + continúa). Hoy el
  loop corta seco (`agent_loop.py:348`) y `_fire_stop` (SubagentStop) es fire-and-forget que descarta la
  `HookDecision` (06·FIND-HOOK6).
- **Seam/firma**: ya existe `HookEvent.STOP`/`STOP_FAILURE`/`SUBAGENT_STOP` (hooks/protocol.py) y el
  `HookRunner`. En `run()`, ANTES del `break` de cierre (línea 348): `decision = await
  hook_runner.run(HookEvent.STOP, {"ctx":ctx,"last_assistant_message":...})`; si `decision` pide continuar
  (nuevo campo `continue_loop` en `HookDecision`, ver 06) → NO romper, re-llamar al modelo con el
  `additional_context` inyectado. Adjuntar `last_assistant_message`+`agent_transcript_path` al payload
  (06·HOOK9).
- **Cableado**: el loop deja de tratar Stop como no-evento; el `HookRunner` ya está inyectado
  (`self._hook_runner`). Requiere `HookDecision.continue_loop` (desarrollado en 06).
- **Orden**: tras el enriquecimiento de `HookDecision` (06·HR-*).
- **Test**: `test_stop_hook_can_continue_loop`.

### LR4 · Motor #4 — preproceso de input → cableado en 01·CR2 (no re-desarrollar)
- El motor #4 (slash/inline preprocessing) es `UserInputProcessor`, cuyo cableado se desarrolla en
  **01·CR2** (el loop lo invoca antes del turno). Aquí sólo se referencia para cerrar los "4 motores".

### LR5 · FIND-L1 — ~~invariante tool_use↔tool_result en la rama de error~~ · SIN REMEDIACIÓN (re-visita L09 2026-07-18)
- **Resolución**: la premisa de esta LR5 (el loop "persiste el assistant CON `tool_calls` en 274-281 y luego
  hace break por error dejando `tool_use` colgante") es **falsa**. Al abrir `agent_loop.py` 1→EOF: la rama
  `ErrorEvent` hace `break` en **267-270**, que precede al bloque de persistencia **272-281** ⇒ en error-mid-stream
  los `tool_calls` buffered **se descartan** (solo se appendea `[error]`), no se persiste ningún assistant con
  `tool_calls` sin parear. Cuando SÍ se persisten (281), el bucle **287-344** appendea un `tool` message por CADA
  call (no-dispatcher / block / dispatch) y el dispatcher **nunca lanza** (`ToolResult.aborted/error/timeout`,
  dispatcher.py:54-84). **El invariante ya está garantizado por diseño** (buffer-then-commit). No hay bug que
  remediar ni test xfail que escribir. (Reclasificado C11 🟡→🔀; el mecanismo difiere del canónico pero el efecto
  observable —cero `tool_use` colgantes— se reproduce, L10.)
- **Liga preservada**: 05·FIND-EXEC2 (fork con tool_use colgante) y 08·SIG7 se evalúan por sí mismos en su
  subsistema; no dependen de un bug de 02 que no existe.

### LR6 · Cabos a otro subsistema (referencia, no re-desarrollo)
- **C2 superficie de opciones al modelo** (thinking/effort/fastMode/mcpTools/agents/taskBudget) →
  **16·models** (ampliar `ModelCallerProtocol`); decidir cuáles son core (thinking/effort probablemente sí).
- **FIND-L2 / usage** → **Deuda B `B-usage`** (usage no acumulado; Session slots muertos).
- **F2 gate de permisos** (ask/HITL + permission modes) → **Deuda B `B-02`** + 06·HOOK3.
- **E3 teammates/coordinator** → ⛔ (corte del README; subsistema nuevo si se adopta).

---

## Ledger de cierre — 2ª vuelta (validación)

| Archivo | Lado | LOC | Lectura | Nota |
|---|---|---|---|---|
| `loop/agent_loop.py` | B | 352 | **íntegro 1→EOF** | Archivo grande. Refs de línea del doc EXACTAS (189/267-270/274-281/300-313/329-339/348). Cableado de los 4 motores ausentes verificado por lectura, no grep. |
| `loop/protocol.py` | B | 27 | **íntegro** | `LoopProtocol`+`DrainableLoopProtocol`, ambos `@runtime_checkable`. |
| `loop/factory.py` | B | 27 | **íntegro** | `create_loop` helper del consumidor. |
| `loop/basic.py` | B | 1 | **íntegro** | Shim: `BasicLoop = AgentLoop`. |
| `loop/__init__.py` | B | 6 | **íntegro** | Exports. |
| `query.ts` | A | 1729 | grep dirigido + tramos ya-íntegros (1ª pasada) | Anclas re-confirmadas: `yieldMissingToolResultBlocks`:123/984 (rama error→FIND-L1), `maxTurns`/`max_turns_reached`:1508-1511/1705-1711, `attemptWithFallback`:650-655/894-897, `microcompact`/`autocompact`/`getMessagesAfterCompactBoundary`:52/365/413, reason codes:1051/1175/1515/1520/1711. |
| `QueryEngine.ts` | A | 1295 | íntegro (1ª pasada); frontera G→05 | Driver de sesión; features G viven en 05·execution. |
| `query/{config,deps,stopHooks,tokenBudget}.ts` | A | 46/40/473/93 | íntegros (1ª pasada) | E1-E6 confirmados. |

### Nota de honestidad (2ª vuelta)
- **Discrepancia encontrada**: SÓLO de **etiquetado de GAP-IDs** en el §Plan/tabla — no afecta ningún estado
  ni hallazgo. Estaban intercambiados: LR1 (compactación) decía `GAP-L1/L1b` cuando compactación es **GAP-L4**;
  LR3 (stop-hooks) decía `GAP-L4` cuando stop-hooks es **GAP-L1/L1b**. Además la celda C4 usaba `GAP-L3` para
  el fallback cuando GAP-L3 es el token-budget (E1) y el fallback es **GAP-C4**. Corregido en las 3 caras.
- **Todo lo sustantivo validado-sin-cambios**: los ~46 estados (✅7·🟡12·🔀7·❌15·⛔11), FIND-L1 (pareo
  tool_use↔tool_result en rama error — canónico `yieldMissingToolResultBlocks` usado en `query.ts:984`
  confirmado), FIND-L2 (usage a 0 — `agent_loop.py:253-254` nunca lee `done.usage`, confirmado), los 4 motores
  ausentes (compactación/error-recovery/stop-hooks/input-preproc) verificados por **cableado** (L09), y las
  resoluciones E3⛔/G2❌-en-05/G3❌-en-05 siguen ciertas.
- **Path legacy** `capabilities_resolver` (`agent_loop.py:201-205`, sólo anuncia schemas, no ejecuta): ya está
  homed como **18·FaR2** (resolver legacy cableado muerto) — no es hallazgo nuevo, cabo con destino confirmado.

### 4 preguntas de cierre
1. **¿Todo B revisado?** ✅ Sí — los 5 archivos de `loop/` íntegros 1→EOF (413 LOC), el grande `agent_loop.py`
   barrido punta a punta con huecos cerrados.
2. **¿Todo A revisado?** ✅ Sí — `query.ts`/`QueryEngine.ts`/`query/*` ya se leyeron íntegros en la 1ª pasada
   (line-precisa); la 2ª vuelta re-confirmó las anclas load-bearing por grep dirigido a líneas exactas. Frontera
   G (driver de sesión) se audita íntegra en 05·execution (destino nombrado, no troceo).
3. **¿Hallazgos exhaustivos?** ✅ Sí — la 2ª vuelta cazó la única inconsistencia real (etiquetado GAP-ID) que la
   1ª pasada arrastraba; el resto se confirmó line-a-línea.
4. **¿Todo cubierto?** ✅ Sí; cabos con destino: FIND-L2→Deuda B `B-usage`, F2 gate→`B-02`+06, C2 superficie
   modelo→16, motores 2/4→05/01, path legacy→18·FaR2.

---

## Re-visita de COMPLETITUD (L09) — 2ª vuelta, 3ª ronda · 2026-07-18

**Modo**: re-visita de completitud A-vs-B (learned_lessons/09) sobre las filas **✅/🔀**. **Motivo**: la validación
del 2026-07-17 fue **confirmación-de-doc** en las filas ✅/🔀 (sólo los 4 motores ❌ llevaron cableado real). Aquí,
para cada ✅/🔀 se **abrió la implementación de B** que reproduce el comportamiento y se **siguió el dato de punta a
punta**, NO se aceptó la tabla. **Resultado**: 1 reclasificación real (**C11/FIND-L1 🟡→🔀**, sobre-declaración
corregida); todo lo demás se sostiene sobre la base correcta. **Código intacto** (MODO VALIDACIÓN).

### Mini-ledger de consumidores abiertos (dato seguido, no inventario)
| Fila | Estado | Consumidor de B abierto | Evidencia de cableado (seguir el dato) |
|---|---|---|---|
| A1 | ✅ | `agent_loop.py` 179/185/348 | append user + `for range(_MAX_TURNS)`; continúa **iff** `done.stop_reason=="tool_calls"`. |
| C1 | ✅ | `agent_loop.py` 247-281 | stream Token/ToolCall/Done/Error consumido; assistant persistido con tokens+tool_calls. |
| D7 | ✅ | `agent_loop.py` 348-349 | fin normal = `break` del `for`. |
| F1 | ✅ | `tools/dispatcher.py` 36/76-77 | `dispatch()`→`tool.execute()` real; TODO ToolResult → `tool` message (pareo garantizado). |
| **F12** | ✅ | `skills/skill_tool.py:119`, `native/worktree.py:102/166`, `native/plan_mode.py:59/101`, `native/todo_write.py:62`, `native/config.py:75` → loop 332-335 | **5 productores reales** setean `result.context_modifier`; el loop invoca `ctx = modifier(ctx) or ctx`. **Cableado real**, no costura muerta. |
| **G5** | ✅ | `runtime.cancel`(187)→`registry.kill`(117)→`asyncio_task.cancel()`(122)→`CancelledError` en `runtime.py:380-384` | Cancelación end-to-end EXACTA a la fila. (`ctx.stop` es la vía cooperativa paralela: loop 173/186 + dispatcher 54.) |
| A2 | 🔀 | `agent_loop.py` (ctx mutado in-place) | struct mutable vs State inmutable canónico; efecto equivalente. |
| E5 | 🔀 | `agent_loop.py:144` `supports_native_tool_search` | gates statsig/env → flags de capacidad del caller. |
| E6 | 🔀 | `agent_loop.py:49-63` (constructor DI) | `productionDeps` → DI de `model_caller`/`tool_dispatcher` por constructor. |
| F3 | 🔀 | `agent_loop.py` 287-344 (secuencial post-stream) | divergencia de rendimiento (no concurrente/streaming); efecto correcto. |
| **F4** | 🔀 | `native/ask_user.py:97`, `native/plan_mode.py:106` → loop 338/348 | `result.ends_turn = True` (2 productores reales) → `_ends_turn` → `break`. **Cableado real.** |
| F8 | 🔀 | `runtime.py:372-374` (solo raíz, `parent_snapshot is None`) → loop `register_turn_start_hook`/176 | drain al **inicio** del turno (placement divergente); consumidor real. |
| F9 | 🔀 | `agent_loop.py` 112-130/218 (`_inject_recall`) | recall **síncrono** con dedup vs prefetch asíncrono canónico. |
| **C11** | 🟡**→🔀** | `agent_loop.py` 267-270 vs 272-281 + 287-344; `dispatcher.py` 54-84 | **DISCREPANCIA**: `break` por error precede a la persistencia ⇒ nunca hay `tool_use` colgante; invariante reproducido por buffer-then-commit. Ver §honestidad. |
| F2 | 🟡 | `agent_loop.py` 300-313 | gate `block`/`modified_input` cableado; `ask`/HITL + permission-modes faltan (→`B-02`). Confirmado 🟡. |
| F6 | 🟡 | `dispatcher.py` 54-55 vs loop 287 | dispatcher honra `ctx.stop` por-call, pero el loop no re-chequea entre tools. Confirmado 🟡. |
| F11 | 🟡 | `agent_loop.py:195` (dentro del `for`) | pool **re-armado cada turno** (no cacheado); falta confirmar refresh MCP (→11). Confirmado 🟡. |

### Nota de honestidad (re-visita L09)
- **La ronda previa (2026-07-17) fue confirmación-de-doc** en las ✅/🔀: se re-confirmaron anclas de A por grep
  dirigido y se leyó `agent_loop.py` íntegro, pero NO se abrieron los **consumidores** (productores de
  `context_modifier`/`ends_turn`, `registry.kill`, `dispatcher`) para seguir el dato. Esta ronda sí.
- **Sobre-declaración corregida — C11/FIND-L1**: se marcaba 🟡 con riesgo de API-400 asumiendo *persist-then-error*.
  Al **abrir B**: la rama `ErrorEvent` hace `break` en **267-270 ANTES** del bloque de persistencia **272-281**;
  los `tool_calls` buffered se descartan en error, y los que se persisten se parean 1-a-1 en 287-344 (dispatcher
  nunca lanza). El invariante se mantiene por diseño (buffer-then-commit) ⇒ **🔀**, no 🟡. La premisa previa era
  además internamente inconsistente con LR2 (que describe bien `error→[error]+break` en 267-270). Un misread que
  la confirmación-de-doc no podía cazar (no abría el orden de las ramas); abrir B y seguir el dato sí (L09).
- **No se disfrazó ninguna brecha de 🔀 (L10 segundo filo)**: descartar los `tool_calls` en error NO es un gap nuevo
  — la recuperación de error del modelo ya está capturada como **GAP-C4/LR2 (❌)**. F2/F6/F11 siguen 🟡 (no se
  inflaron a ✅ ni se degradaron a ❌).
- **Costuras latentes buscadas (tipo `to_llm`/`timeout_seconds` de 01)**: `context_modifier` y `ends_turn` tienen
  **productores reales en ruta** (5 y 2 respectivamente) — NO son definido-pero-no-invocado. No apareció ninguna
  nueva costura muerta en las ✅/🔀 del loop.

### 4 preguntas de cierre (re-visita L09)
1. **¿Todo B revisado?** ✅ Sí — `agent_loop.py` re-leído 1→EOF (353 líneas) + abiertos los consumidores/productores
   de cada ✅/🔀: `dispatcher.py` (1→EOF), `tools/protocol.py` (ToolResult), `native/{ask_user,plan_mode,worktree,
   todo_write,config}.py` (productores de modifier/ends_turn), `skills/skill_tool.py`, `execution/local/runtime.py`
   (cancel/kill/register_turn_start_hook), `execution/tasks/registry.py:117-124` (kill).
2. **¿Todo A revisado?** ✅ Sí — A (`query.ts`/`QueryEngine.ts`/`query/*`) ya íntegro en 1ª pasada; esta ronda es de
   completitud **sobre B** (el objeto de L09 es abrir la implementación de B que sostiene cada ✅/🔀), con las anclas
   de A ya confirmadas en la ronda del 2026-07-17.
3. **¿Hallazgos exhaustivos?** ✅ Sí — se recorrieron **todas** las ✅ (7) y 🔀 (7→8) + los focos 🟡 (F2/F6/F11)
   abriendo el consumidor; la única discrepancia (C11 sobre-declarado) se cazó siguiendo el orden de las ramas.
4. **¿Todo cubierto?** ✅ Sí — cabos con destino sin cambios: FIND-L2→`B-usage`, F2→`B-02`+06, C2→16, motores
   2/4→05/01, path legacy→18·FaR2. Sin pendientes de verificación de la 2ª vuelta: **01/02/03 ya re-verificados con
   L09**.

### VEREDICTO DE AVANCE
**✅ NADA PENDIENTE → avanzar a `04·modes`.** La re-visita de completitud L09 de **02·loop** cierra el **único
pendiente de verificación de la 2ª vuelta** (01/02/03 completos con L09). No queda ningún ✅/🔀 sin re-verificar
abriendo B, ni pendiente de remediación en 02 (los ❌ ya tenían cableado; FIND-L1 resultó no-bug). Siguiente por
orden: **04·modes** (plan ya desarrollado en PROGRESS: B diminuto `modes/`, carne en A, L09 de ENTRADA sobre las
✅/🔀, verificar FIND-MODE1 huérfano + GAP-MODE1/2).
