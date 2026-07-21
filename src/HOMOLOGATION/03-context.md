# 03 · context

**Fase:** documentación (primera pasada, sin ajustes al código).
**Runtime:** `src/agentic_runtime/context/{tool_use.py (70 LOC), presentation.py (25), adapters.py (85), __init__.py (11)}`
**Canónico (leído ÍNTEGRO, no por hitos):**
- `Tool.ts` (792 LOC) — tipo **`ToolUseContext`** (158-300), `ToolPermissionContext` (123-148),
  `ToolResult.contextModifier` (330), `getEmptyToolPermissionContext` (140).
- `context.ts` (189) — `getSystemContext`/`getUserContext`/`getGitStatus` (contexto prepend).
- `state/AppStateStore.ts` (570) — el **tipo real `AppState`** (89-452) + `getDefaultAppState` (456-569).
  (`state/AppState.tsx` (199) es sólo el wrapper React del store: `AppStateProvider`/`useAppState`/
  `useSyncExternalStore` ⇒ ⛔ UI; el tipo vive en `AppStateStore.ts`, contraparte real.)
- `utils/forkedAgent.ts::createSubagentContext` (345-462) — derivación del ctx hijo (isolación/herencia).

Se descartaron como contrapartes de ESTE subsistema (leídas para confirmarlo):
- `utils/context.ts` (221) = ventana de contexto / max-output-tokens / 1M-context ⇒ pertenece a
  **02·loop (B/E1)** y **16·models**, no al `ToolUseContext`.
- `src/context/*.tsx` (notifications, mailbox, voice, overlay, stats, modal, …) = React UI contexts ⇒ ⛔.

## Naturaleza del subsistema
El `ToolUseContext` es el **contexto operativo de un turno**: lo que cada tool recibe para ejecutarse.
Dos diferencias estructurales gobiernan toda la homologación:

1. **El canónico opera single-user en terminal; el runtime tiene usuarios y sesiones.** Por eso el
   `ToolUseContext` del runtime **añade** campos que el canónico no necesita (`user_id`, `is_subagent`,
   `storage`, `presentation`, `exec_env`, `fs`, `git_credentials`, `event_queue`) — homologación *de
   comportamiento*, no de forma. Ver [[architecture-layers]].
2. **El canónico mete TODO en dos bolsas gigantes** (`ToolUseContext` ~45 campos + `AppState` ~80
   campos) porque vive en un solo proceso REPL con React. El runtime parte eso en: (a) campos core del
   ctx, (b) `AppState` = **3 bolsas** (`permissions`/`capabilities`/`native`), (c) el resto delegado al
   integrador vía `capabilities`/`native` + seams (`root_context_modifier`, `presentation`, `ForkSnapshot`).
   La mayoría de campos del canónico son **callbacks de UI/REPL** (setToolJSX, addNotification,
   setStreamMode, openMessageSelector…) ⇒ ⛔.

## Evidencia ejecutada
- **Lint** (`context/`): `ruff` ✅ · `mypy` ✅ (4 archivos, sin issues) · `bandit` ✅ (0 hallazgos).
- **Tests**: nuevo `test_context_homologation.py` → **11 passed, 3 xfailed**. Junto a los previos que
  cubren 03 (`test_context_identity.py`, `test_path_presentation.py`, `test_root_context_modifier.py`):
  **33 passed, 3 xfailed**. Suite global tras 03: **559 passed · 3 skipped · 10 xfailed**.
  - Sintéticos: forma núcleo del ctx; `AppState` 3-bolsas; `permission_context`+`with_permissions`
    (copia inmutable); `ContextModifier` ≡ `ToolResult.contextModifier`; adapters
    (from_session mapea grants+skills, prefiere `get_messages_for_llm`, sync escribe grants de vuelta,
    compat con modifier ctx-aware y con modifier legacy de sesión); derivación de subagente
    (aísla messages / hereda permissions+tool_pool+capabilities / nuevo agent_id / propaga abort).
  - `xfail(strict)` = evidencia de gap: **FIND-CTX1** (read-file-state ausente), **GAP-02**
    (permission mode ausente en AppState), **FIND-CTX2** (agent_type no threadeado al ctx).

## Tabla feature-by-feature

### A · `ToolUseContext` — campos (enumeración ÍNTEGRA de Tool.ts:158-300)
| # | Campo canónico | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| A1 | `messages: Message[]` | `messages: list[Any]` | ✅ | Vista de conversación del turno. Verificado. |
| A2 | `abortController: AbortController` | `stop: asyncio.Event \| None` | ✅ | Cancelación cooperativa. El dispatcher/loop chequean `stop`. Homologación de comportamiento (=G5 de 02). |
| A3 | `agentId?` (sólo subagentes; hooks distinguen) | `agent_id: str \| None` | ✅ | Espejo directo; lo genera el forker (`agent_...`). |
| A4 | `agentType?` (nombre del tipo de subagente; hooks lo leen) | — (existe `ForkContext.subagent_type`, no baja al ctx) | 🟡 | **FIND-CTX2**. El tipo de subagente no viaja en el ctx ejecutor, sólo en el descriptor de fork. **Ajuste**: threadear `agent_type` al `ToolUseContext` para que hooks/telemetría distingan el tipo. xfail `test_toolusecontext_carries_agent_type`. |
| A5 | `readFileState: FileStateCache` (LRU {path→{content,mtime}}) | — | ❌ | **FIND-CTX1 (correctitud).** El canónico usa esto para (a) el **guard de frescura de Edit/Write** (bloquea si el fichero cambió desde la última lectura / exige read-before-edit) y (b) dedup de nested-memory. `FileEditTool` del runtime NO tiene ese guard (lee y reemplaza sin verificar lectura previa ni mtime). **Ajuste**: cache de estado de lectura en el ctx + guard en Edit/Write. Se cruza con 10·tools-native. xfail `test_toolusecontext_tracks_read_file_state`. |
| A6 | `getAppState()` / `setAppState(f)` (store funcional React) | `app_state: AppState` (campo mutable directo) | 🔀 | El canónico lee/escribe vía store con selectores (`useSyncExternalStore`); el runtime muta el objeto in-place. Comportamiento equivalente fuera de React. **Nota**: el `setAppState` del canónico es **no-op para subagentes async** (aislamiento) — el runtime logra el mismo aislamiento por `ForkSnapshot` (ver E). |
| A7 | `setAppStateForTasks?` (siempre alcanza el store raíz aun en subagentes) | — | 🟡 | Registro/kill de infra session-scoped (bash background) que sobrevive al turno debe llegar a la raíz aun cuando `setAppState` es no-op. El runtime lo resuelve distinto: el registro de tasks vive en `execution` (`InMemoryTaskRegistry`), no en AppState. **Ajuste (⇒05)**: confirmar que el kill de tasks de subagentes async alcanza el registro raíz. |
| A8 | `abortController` hijo enlazado al padre (createChildAbortController) | `ForkPolicy.propagate_abort` ⇒ comparte `stop` del padre | ✅ | Propagación de abort padre→hijo. Verificado (forker). |
| A9 | `options.tools: Tools` / `options.refreshTools?()` | `tool_pool: ToolPool` (reensamblado por turno en el loop) | ✅ | El pool de tools viaja en el ctx. `refreshTools` ≡ el reensamblado por-turno del loop (=F11 de 02). |
| A10 | `options.commands: Command[]` | — | ❌ | Slash-commands en el ctx. Se cruza con 12·skills/commands + G1 (input processing). |
| A11 | `options.mainLoopModel` | — (modelo fijo por loop/caller) | 🔀 | Ver 02·C3 (resolución de modelo por turno). No vive en el ctx del runtime. |
| A12 | `options.thinkingConfig` / (AppState) `fastMode`/`effortValue`/`advisorModel` | — | ❌ | Superficie de sampling del modelo. Ver 02·C2. **Ajuste**: decidir cuáles son core (thinking/effort) y por dónde viajan (ctx vs caller). |
| A13 | `options.mcpClients` / `options.mcpResources` | `app_state.capabilities` (bolsa del integrador) + `event_queue` | 🔀 | El canónico threadea clientes/recursos MCP en `options`; el runtime los expone por la bolsa `capabilities` (delegador per-tenant) — el `ForkSnapshot` la hereda al hijo (espejo de `runAgent.ts` threadeando `options.mcpClients`). Se cruza con 11·mcp. |
| A14 | `options.agentDefinitions` | — (viven en `execution/agents.py`) | 🔀 | Definiciones de subagentes. En el runtime las resuelve `execution`, no viajan en el ctx. ⇒05. |
| A15 | `options.maxBudgetUsd` | — | ❌ | Ver 02·G2 (resuelto: en alcance de 05·execution). |
| A16 | `options.{customSystemPrompt,appendSystemPrompt}` | `presentation`/caller `system_sections`/`system_override` | 🔀 | Override/append de system prompt. El runtime lo maneja en el caller (`_compose_system_prompt`, ver 16·models) y por `system_override` del loop, no como campo del ctx. |
| A17 | `options.{debug,verbose,isNonInteractiveSession,querySource}` | — | ⛔ | Flags de UI/analítica/interactividad de terminal. Fuera de core. |
| A18 | `toolUseId?` | — | 🟡 | El id de la tool-call vive en el `ToolCallEvent`/dispatch, no en el ctx. Suficiente para el pareo; **ajuste**: exponerlo en el ctx si un hook/tool lo necesita. |
| A19 | `fileReadingLimits?` / `globLimits?` | — (límites en cada tool) | 🔀 | El canónico permite acotar read/glob por-contexto; el runtime los fija en la tool (read_file/glob). **Ajuste**: si el integrador debe ajustarlos por sesión, subirlos al ctx. Se cruza con 10. |
| A20 | `toolDecisions?` (accept/reject por tool) | — | ❌ | Historial de decisiones de permiso por tool. Se cruza con 06·hooks/permissions. |
| A21 | `localDenialTracking?` (contador de denials para subagentes async) | — | ❌ | Sin esto, el umbral fallback-a-prompting nunca se alcanza en subagentes. Se cruza con 06·permissions. |
| A22 | `contentReplacementState?` (presupuesto agregado de tool results) | — | ❌ | Ver 02·B2 (tool-result budget). Vive en el ctx en el canónico; el runtime no lo tiene. |
| A23 | `renderedSystemPrompt?` (bytes del system prompt del padre, congelados al inicio del turno, para cache-share del fork) | — | 🟡 | El fork del runtime comparte tool_pool/permissions/capabilities, pero NO congela el system prompt renderizado. Riesgo de cache-miss si el prompt del padre diverge al re-renderizar en el hijo. **Ajuste (⇒05/16)**: capturar el system prompt renderizado en `ForkSnapshot` para el prefijo byte-idéntico. |
| A24 | `nestedMemoryAttachmentTriggers?` / `loadedNestedMemoryPaths?` | — | ❌ | Dedup de inyección de CLAUDE.md anidado. Depende de A5 (readFileState) y se cruza con 13·memory. |
| A25 | `dynamicSkillDirTriggers?` / `discoveredSkillNames?` | — | ❌ | Triggers/telemetría de descubrimiento de skills. Se cruza con 12·skills (=F10 de 02). |
| A26 | `requireCanUseTool?` | — | ❌ | Forzar `canUseTool` aun con auto-approve (speculation). Se cruza con 06. |
| A27 | `preserveToolUseResults?` | — | ⛔ | Para teammates in-process (transcript visible al usuario). Fuera de core (ver 02·E3 teams ⛔). |
| A28 | `criticalSystemReminder_EXPERIMENTAL?` | — | ⛔ | Recordatorio experimental. Fuera de core. |
| A29 | `queryTracking?` (chainId/depth) | `subagent_depth` (sí) ; chainId — | 🟡/⛔ | La **profundidad** sí (runtime la usa como tope de anidamiento); el chainId de analítica de cadena ⇒ ⛔ (=A3 de 02). |
| A30 | `userModified?` | — | ⛔ | Flag de edición manual del input (UI). Fuera de core. |
| A31 | `handleElicitation?` (URL elicitation de MCP) | — | ❌ | Elicitación OAuth/URL de MCP. Se cruza con 11·mcp. |
| A32 | `requestPrompt?` (prompts interactivos al usuario) | tool `AskUserQuestion` (`ends_turn`) | 🔀 | HITL. El runtime lo hace por una tool que cierra el turno (=F4 de 02), no por un callback del ctx. Equivalente funcional para el asistente con sesiones. |
| A33 | Callbacks UI/REPL: `setToolJSX`, `addNotification`, `appendSystemMessage`, `sendOSNotification`, `setInProgressToolUseIDs`, `setHasInterruptibleToolInProgress`, `setResponseLength`, `pushApiMetricsEntry`, `setStreamMode`, `onCompactProgress`, `setSDKStatus`, `openMessageSelector`, `updateFileHistoryState`, `updateAttributionState`, `setConversationId` | — | ⛔ | Toda la superficie de render/estado de terminal (ink/React), métricas OTPS ant, notificaciones OS, JSX de tools, file-history/attribution de UI. Fuera de core. **Nota**: `updateFileHistoryState`/`updateAttributionState` tienen fondo de comportamiento (undo de edits, co-autoría de commits) — se re-evalúan en 10·tools-native / 05 si el asistente los necesita. |
| A+ | *(runtime añade)* `user_id`, `is_subagent`, `turn_count`, `storage`, `presentation`, `exec_env`, `fs`, `git_credentials`, `event_queue` | presentes | ✅ | Extensiones por usuarios/sesiones + FS de infra. `user_id`/`is_subagent` verificados en `test_context_identity`; `fs`/`presentation` en `test_fs_confinement`/`test_path_presentation`. No tienen contraparte canónica (el canónico es single-user/terminal). |

### B · `AppState` (par de AppStateStore.ts:89-452)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| B1 | `AppState` = store monolítico DeepImmutable (~80 campos) | `AppState` = 3 bolsas (`permissions`, `capabilities`, `native`) | 🔀 | Divergencia deliberada. El runtime NO porta el store REPL; expone lo core y delega el resto al integrador por bolsa. Verificado (`test_appstate_is_three_bag_seam`). |
| B2 | `toolPermissionContext` = `{ mode: PermissionMode, alwaysAllow/Deny/AskRules, additionalWorkingDirectories, isBypassPermissionsModeAvailable, prePlanMode, … }` | `AppState.permissions: PermissionContext` = `{ always_allow_command, always_allow_session, always_deny }` | 🟡 | El runtime tiene reglas allow/deny pero **falta `mode` (PermissionMode: default/plan/acceptEdits/bypass)** y `additionalWorkingDirectories`/`prePlanMode`. **= GAP-02** de 01·contracts. Hoy el plan-mode se lee de `app_state.native["plan_mode"]` (hack del integrador). **Ajuste**: modelar el modo de permisos como estado de primera clase. xfail `test_appstate_permissions_carry_mode`. |
| B3 | `mcp: { clients, tools, commands, resources, pluginReconnectKey }` | `app_state.capabilities` (bolsa) | 🔀 | Estado MCP. El runtime lo mete en `capabilities` (provider per-tenant del integrador). ⇒11. |
| B4 | `todos: { [agentId]: TodoList }` | `app_state.native`/tool `todo_write` | 🔀 | Estado de todos por agente. El runtime lo maneja en la tool nativa. ⇒10. |
| B5 | `tasks` / `agentNameRegistry` / `foregroundedTaskId` / `viewingAgentTaskId` | `execution` (`InMemoryTaskRegistry`, observer) | 🔀 | Registro de subagentes/tasks. En el runtime vive en `execution`, no en AppState. ⇒05. |
| B6 | `sessionHooks: SessionHooksState` | `hooks/` (HookRunner) | 🔀 | Estado de hooks de sesión. ⇒06. |
| B7 | `fileHistory` / `attribution` | — | ❌/⛔ | Snapshots de undo de ficheros + co-autoría de commits. `fileHistory` tiene fondo de comportamiento (undo); `attribution` roza política de commits (ver memoria [[no-claude-coauthorship]]). Re-evaluar en 10/05. |
| B8 | `agentDefinitions` | `execution/agents.py` | 🔀 | ⇒05. |
| B9 | `notifications` / `elicitation` / `inbox` | `execution/local/notification.py` (canal con clave user+session) | 🔀 | Notificaciones de background. El runtime tiene canal keyed por (user_id, session_id); elicitation ⇒11; inbox (teammates) ⇒⛔. |
| B10 | `mainLoopModel*` / `thinkingEnabled` / `fastMode` / `effortValue` / `advisorModel` / `promptSuggestionEnabled` | — | ❌/🔀 | Opciones de modelo/turno. ⇒02·C2 / 16·models. |
| B11 | `initialMessage` (mensaje inicial a procesar) | — | ❌ | Mensaje inicial (CLI args / salida de plan mode). Se cruza con G1 (input processing) y 14·plan. |
| B12 | UI/REPL/bridge/teams/tmux/bagel/computer-use/speculation/plugins/companion/ultraplan/worker-sandbox/pending*Request/skillImprovement/promptSuggestion/activeOverlays/footer*/expandedView/statusLineText/remote*/verbose/isBriefOnly/spinnerTip/authVersion | — | ⛔ | El grueso del store (~55 campos): estado de terminal/REPL, bridge a claude.ai, swarm/teams (⛔ ver 02·E3), tmux, WebBrowser, computer-use (chicago MCP), speculation, plugins, companion. Fuera de core. |

### C · Adapters (`context/adapters.py`) — Session ⇄ ToolUseContext
| # | Feature | Runtime | Estado | Nota |
|---|---|---|---|---|
| C1 | `tool_use_context_from_session` mapea grants→permissions, invoked_skills→capabilities, messages (prefiere `get_messages_for_llm`) | ✅ | ✅ | Seam de transición Session→ctx. No tiene contraparte canónica (el canónico no tiene sesión); es homologación *de comportamiento*. Verificado. |
| C2 | `sync_session_from_tool_use_context` escribe `always_allow_session`→`metadata.permission_grants` | ✅ | ✅ | Sincronización inversa. Verificado. **Nota**: sólo sincroniza grants; si el ctx gana estado que la sesión debe persistir (p. ej. modo de permisos tras B2), ampliar. |
| C3 | `apply_context_modifier_compat` (modifier ctx-aware con fallback a modifier de sesión legacy) | ✅ | 🟡 | Puente durante la transición a `ToolUseContext`. Verificado ambos caminos. **Ajuste**: es andamiaje de migración; retirar cuando todos los modifiers sean ctx-aware. |

### D · Presentation (`context/presentation.py`)
| # | Feature | Runtime | Estado | Nota |
|---|---|---|---|---|
| D1 | `IdentityPresentation` (no-op: FS del usuario = FS del agente, rutas verbatim) | ✅ | ✅ | Comportamiento canónico por defecto (terminal). Verificado. |
| D2 | `PathPresentation` como seam (FS de infra ⇒ mapea rutas host→tokens fake en el choke point único del ToolResult) | ✅ (mecanismo `sanitize_output`) | ✅ | **Extensión del runtime** (no existe en el canónico: éste no confina FS ⇒ **no hay comportamiento de A que reproducir aquí; N/A al eje A-vs-B**). El ocultamiento REAL se logra por `sanitize_output` en el choke point único del dispatcher (`tools/dispatcher.py:42`, todo `ToolResult.output`) + `runtime.py:244` (stream TTS) — verificado por cableado (2ª vuelta) y por `test_path_presentation::test_choke_point_covers_messages_and_bus` (alimenta `ctx.messages` Y el bus). **Cabo latente B-interno (no deuda A-vs-B, L10):** el 2º método del protocolo `PathPresentation.to_llm(host_path)→token` (mapeo de ruta en origen) **no tiene NINGÚN call site de producción** (`grep to_llm` = sólo la def del protocolo/IdentityPresentation + fakes de test); ninguna tool que emite rutas lo invoca. Bajo identidad es no-op (invisible); para un consumidor de infra el ocultamiento depende SÓLO del scrubbing de texto de `sanitize_output` (no del mapeo estructurado en origen). Se registra como tech-debt de la extensión propia de B, no se cuenta como ❌/🟡 de homologación. Contrato en `contracts/storage.py::PathPresentation`. |

### E · Derivación de subagente (par de `createSubagentContext`, forkedAgent.ts:345-462)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| E1 | Aísla por defecto: `readFileState` clonado, colecciones frescas, callbacks de mutación no-op | `RuntimeContextForker.fork`: messages aislados, nuevo agent_id, callbacks N/A (sin store React) | ✅ | Aislamiento equivalente. El runtime no tiene callbacks de UI que "no-opear"; el aislamiento es por construcción del ctx hijo. Verificado. |
| E2 | Hereda del padre lo que el modelo necesita: `options` (tools, mcpClients), `messages` (override) | `ForkPolicy`: `inherit_{permissions,tool_pool,capabilities,messages}` | ✅ | El runtime lo hace declarativo por política (el canónico por overrides imperativos). `capabilities` hereda el provider MCP per-tenant (espejo de `options.mcpClients`). Verificado (`test_subagent_context_isolation_defaults_mirror_canonical`). |
| E3 | `agentId` nuevo por subagente (`createAgentId`) | `agent_{uuid}` en el forker | ✅ | Verificado. |
| E4 | abort hijo enlazado al padre (`createChildAbortController`); `shareAbortController` para agentes interactivos | `ForkPolicy.propagate_abort` (comparte `stop`) o `stop` fresco | ✅ | Verificado (`test_context_identity` + forker). |
| E5 | `getAppState` envuelto para `shouldAvoidPermissionPrompts=true` en subagentes async (no pueden mostrar UI) | `is_subagent`/background ⇒ toolset filtrado a `safe_for_background`; sin prompts | 🔀 | Mismo objetivo (subagente unattended no pide permiso interactivo), mecanismo distinto: el canónico fuerza `shouldAvoidPermissionPrompts`; el runtime filtra el toolset y no tiene UI de prompt. Se cruza con GAP-02 (permission modes) y 05. |
| E6 | `contentReplacementState` clonado (decisiones idénticas ⇒ cache-hit del fork) | — | ❌ | Ver A22/02·B2. El fork del runtime no clona presupuesto de tool-results (no existe). |
| E7 | `renderedSystemPrompt` congelado del padre (prefijo byte-idéntico prompt-cache) | — | 🟡 | Ver A23. **Ajuste (⇒05/16)**: capturarlo en `ForkSnapshot`. |
| E8 | `queryTracking` con `depth+1` | `ForkSnapshot.subagent_depth` (+ tope en la tool Agent) | ✅ | Profundidad de anidamiento. chainId ⇒ ⛔. |

### F · `context.ts` — contexto prepend (system/user)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| F1 | `getGitStatus` (branch, main branch, `git status --short`, últimos 5 commits, user.name; trunca a 2k) inyectado al inicio de la conversación | — | ❌ | El runtime no inyecta git status como contexto de sistema. Útil para un asistente que opera sobre repos. **Ajuste**: proveer el bloque git-status como sección de sistema (probablemente vía `capability_manager`/system_sections del caller). Se cruza con 16·models (`_compose_system_prompt`). |
| F2 | `getUserContext`: CLAUDE.md (memory files) + `Today's date` inyectados y cacheados por conversación | Parcial: memoria vía 13·capabilities/memory (recall como `<system-reminder>`); fecha — | 🟡 | El runtime inyecta **memoria recuperada** (recall, 13), pero no el patrón `getUserContext` del canónico (CLAUDE.md del proyecto + fecha actual como contexto fijo cacheado). **Ajuste**: decidir qué del `getUserContext` es core para el asistente (fecha actual sí; CLAUDE.md del repo depende de si el asistente opera sobre un checkout). Se cruza con 13. |
| F3 | `getSystemContext`: git status + cache-breaker (ant) | ver F1 | ❌/⛔ | git status = F1; cache-breaker (BREAK_CACHE_COMMAND, ant-only debug) ⇒ ⛔. |
| F4 | `setSystemPromptInjection` (debug ant, cache breaking) | — | ⛔ | Debug interno ant. Fuera de core. |
| F5 | Memoización por conversación (`memoize` de getSystemContext/getUserContext) | — | 🟡 | El contexto prepend se computa una vez y se cachea. Si el runtime porta F1/F2, replicar el cacheo por sesión. **Ajuste (⇒16)**. |

## Resumen de estados
Sobre las features enumeradas (≈33 campos de `ToolUseContext` + 12 grupos de `AppState` + adapters/presentation/subagente/context.ts):
- ✅ **~14** — la forma núcleo del ctx (messages, abort, agent_id, tool_pool, app_state), los adapters,
  la presentation (identity + seam), y la derivación de subagente (aísla/hereda/abort/depth).
- 🟡 **~11** — agentType (FIND-CTX2), setAppStateForTasks, toolUseId, fileReadingLimits/globLimits,
  renderedSystemPrompt, permission rules sin `mode` (GAP-02), queryTracking-depth, apply_compat (andamiaje),
  getUserContext parcial, memoización de contexto.
- 🔀 **~10** — AppState 3-bolsas vs store, getAppState directo vs store, mainLoopModel/system-prompt/mcp/
  agentDefinitions/todos/tasks/sessionHooks fuera del ctx, requestPrompt vía tool, E5 (avoid-prompts).
- ❌ **~9** — **readFileState/freshness (FIND-CTX1)**, commands, thinking/effort/fastMode, maxBudgetUsd,
  toolDecisions, localDenialTracking, contentReplacementState, nested-memory dedup, skill-discovery
  triggers, initialMessage, git-status prepend (F1).
- ⛔ **~muchos** — toda la superficie UI/REPL/terminal (callbacks de render, bridge, teams/swarm, tmux,
  computer-use, speculation, plugins, analítica, debug ant).

El `ToolUseContext` del runtime homologa fielmente el **contexto operativo del turno** y **mejora**
sobre el canónico en dos ejes propios de su naturaleza (usuarios/sesiones + FS de infra): `user_id`/
`is_subagent`/`storage`/`presentation`/`fs`/`git_credentials`. Lo ausente se agrupa en: **(1)
seguimiento de estado de ficheros leídos** (readFileState → guard de frescura de Edit, FIND-CTX1);
**(2)** el **modo de permisos** como estado de primera clase (GAP-02, heredado de 01); **(3)** el
**contexto prepend** (`context.ts`: git status + CLAUDE.md + fecha, F1/F2); **(4)** campos que en el
canónico viajan por el ctx pero que el runtime **coloca en otros subsistemas** por diseño (modelo→16,
mcp→11, tasks/agents→05, hooks/permisos→06, skills→12, todos→10) — 🔀 esperado, no gaps.

## Gaps priorizados (para fase de implementación)
- **FIND-CTX1 (❌ correctitud)** Sin `readFileState`/FileStateCache en el ctx ⇒ `FileEditTool` no impone
  read-before-edit ni detecta modificación-desde-lectura (invariante del canónico). Riesgo de write-stale.
  *Arquitectural: cache de lectura en el ctx + guard en Edit/Write (⇒10).*
- **GAP-CTX2 (🟡 = GAP-02 de 01·contracts)** `AppState.permissions` sin `mode` (PermissionMode) ni
  `additionalWorkingDirectories`; el plan-mode se hackea por `native["plan_mode"]`.
- **FIND-CTX2 (🟡)** `agent_type` no se threadea al `ToolUseContext` (sólo en `ForkContext.subagent_type`);
  hooks/telemetría no distinguen el tipo de subagente.
- **GAP-CTX3 (❌)** Contexto prepend de `context.ts` (git status + fecha + CLAUDE.md) no portado (F1/F2).
- **GAP-CTX4 (🟡)** `renderedSystemPrompt` no capturado en `ForkSnapshot` ⇒ posible cache-miss del fork (A23/E7).

## Hallazgos de correctitud (de la lectura íntegra — NO simples ausencias)
- **FIND-CTX1 (❌)** El guard de frescura de Edit/Write del canónico depende de `readFileState`, ausente
  en el runtime. Confirmar en pasada 2 con un test de comportamiento: leer→modificar externamente→Edit
  debe fallar con "modified since read" (hoy no puede expresarse; xfail a nivel de campo).

## Notas para pasadas 2/3
- FIND-CTX1 y GAP-CTX3 son los dos con impacto de comportamiento observable claro; priorizar.
- GAP-CTX2 comparte raíz con GAP-02 (01) y con 02·F2 (gate de permisos) y E5 (avoid-prompts en subagente):
  portar el modo de permisos resuelve los tres a la vez.
- Muchos 🔀 de A/B son "el campo vive en otro subsistema": al documentar 05/11/16 confirmar que el
  comportamiento se cubre allí (no re-abrir como gap de 03).
- Ver [[homologation-effort]] y [[architecture-layers]].

---

## Plan de homologación / remediación desarrollada

Diseño por finding. Seams: `context/tool_use.py` (`ToolUseContext` pydantic + `AppState` 3-bolsas),
`context/adapters.py` (`tool_use_context_from_session`/`sync_session_from_tool_use_context`/
`apply_context_modifier_compat`), `execution/fork/__init__.py` (`ForkSnapshot`/`ForkPolicy`:
`messages`/`permissions`/`capabilities`, `inherit_messages`/`inherit_permissions`).

### CtxR1 · FIND-CTX1 — read-file-state en el ctx → YA desarrollado en 10·R0
- El read-file-state (base de read-before-edit) se desarrolla en **10·R0** (`ctx.read_file_state` +
  `ReadFileEntry`). Aquí sólo el **cableado del fork**: `ForkSnapshot` debe **copiar** `read_file_state`
  (el hijo hereda lo leído por el padre; espejo del `readFileState`-clone de `runAgent.ts`). Firma:
  `ForkSnapshot` gana `read_file_state: dict[str, Any] = {}` y `ForkContext.build` lo copia como
  `dict(snap.read_file_state)` (mismo patrón que `messages` tupla→list). **Test**:
  `test_fork_inherits_read_file_state`.

### CtxR2 · GAP-CTX2 = GAP-02 (parte ctx) — `mode` en `AppState.permissions`
- Es la misma raíz que **01·CR1**: `PermissionContext.mode`. En 03 el cableado es que el `ToolUseContext`
  deje de exponer plan-mode por `app_state.native["plan_mode"]` y lo lea de `app_state.permissions.mode`.
  La **decisión** por modo → Deuda B `B-02`. **Test**: `test_appstate_permissions_carry_mode` (xfail existente).

### CtxR3 · GAP-CTX3 — prepend de contexto (git status + fecha + CLAUDE.md)
- **Comportamiento**: el canónico antepone al system prompt el contexto de sesión (git status, fecha,
  CLAUDE.md) vía `context.ts::getSystemContext`/`getUserContext`/`getGitStatus`. No portado.
- **Seam/firma**: nuevo `context/session_context.py::build_prepend_context(ctx) -> list[str]` (secciones de
  system prompt: git-status del `ctx.fs.write_root`, fecha, contenido de CLAUDE.md si existe). Se suma a
  `system_sections` que el loop ya ensambla y pasa al caller (`agent_loop.py:211-213`).
- **Cableado**: el `CapabilityManager.system_prompt_sections` o un provider dedicado lo aporta; el loop ya
  los concatena. Liga **05·GAP-EXEC5** (que el subagente también reciba el prepend).
- **Orden**: independiente. **Test**: `test_context_prepends_git_and_claudemd`.

### CtxR4 · GAP-CTX4 — `renderedSystemPrompt` en `ForkSnapshot` (cache-miss del fork)
- **Comportamiento**: el fork canónico captura el system prompt **renderizado** para que el hijo comparta
  prompt-cache byte-idéntico; el runtime no lo snapshotea → posible cache-miss. Liga 01·feat4 (byte-identidad).
- **Seam/firma**: `ForkSnapshot` gana `rendered_system_prompt: str = ""`; `ForkContext.build` lo pasa al
  hijo tal cual (no re-renderiza). Coordinar con 05 (dónde se arma el fork).
- **Orden**: junto a 05·fork. **Test**: `test_fork_preserves_rendered_system_prompt`.

### CtxR5 · FIND-CTX2 — `agent_type` threadeado al ctx
- **Comportamiento**: hoy el tipo de agente sólo vive en `ForkContext.subagent_type`, no en el
  `ToolUseContext`; algunas decisiones (gating de tools, prompt) lo necesitan en el ctx.
- **Seam/firma**: `ToolUseContext` gana `agent_type: str | None = None`; lo puebla el runner al construir el
  ctx del subagente (05). **Orden**: junto a 05. **Test**: `test_ctx_carries_agent_type`.

### CtxR6 · C3 `apply_context_modifier_compat` — retirar el andamiaje
- **Comportamiento**: `apply_context_modifier_compat` (adapters.py:60) es un puente durante la migración a
  `ToolUseContext` (soporta modifier ctx-aware Y modifier legacy de sesión). **Remediación = retirarlo**
  cuando todos los modifiers sean ctx-aware (hoy el loop ya usa `modifier(ctx)` directo,
  `agent_loop.py:332-335`). Deuda de limpieza, no de portado.
- **Orden**: al final (cuando ningún consumidor use el path legacy). **Test**: grep-guard `test_no_legacy_session_modifier`.

### CtxR7 · A13 mcpClients/resources → 11 (referencia)
- El threading de clientes/recursos MCP (`app_state.capabilities`) se contrasta y desarrolla en **11·mcp**;
  el `ForkSnapshot` ya hereda la bolsa `capabilities`. No re-desarrollo en 03.

---

## Ledger de cierre (2ª vuelta · MODO VALIDACIÓN) — 2026-07-17

**Resultado: VALIDADA SIN DISCREPANCIA SUSTANTIVA.** Código intacto; doc intacto en sustancia (sólo se
añade este bloque de cierre, que la 1ª pasada no llevaba, homologando el formato de 01/02).

### B (sujeto = runtime) — árbol de la categoría
| Archivo | LOC | Lectura | Veredicto |
|---|---|---|---|
| `context/tool_use.py` | 70 | íntegro 1→EOF | `ToolUseContext`(16 campos)+`AppState`(3 bolsas)+`permission_context`/`with_permissions`+`ContextModifier`. Sin `read_file_state` (⇒FIND-CTX1), sin `agent_type` (⇒FIND-CTX2). ✅ confirma A+/B1/A5/A4/A6. |
| `context/adapters.py` | 85 | íntegro 1→EOF | `tool_use_context_from_session` (grants→permissions, invoked_skills→capabilities, prefiere `get_messages_for_llm`), `sync_...` (grants de vuelta), `apply_context_modifier_compat` (ctx-aware con fallback legacy vía `AttributeError`). ✅ confirma C1/C2/C3. |
| `context/presentation.py` | 25 | íntegro 1→EOF | `IdentityPresentation` (`to_llm`/`sanitize_output` no-op). ✅ D1. PathPresentation = seam en `contracts/storage.py` (D2). |
| `context/__init__.py` | 11 | íntegro 1→EOF | re-export. |
| `contracts/permissions.py` | 33 | íntegro 1→EOF (cruce) | `PermissionContext`={always_allow_command, always_allow_session, always_deny}. **Sin `mode`** ⇒ confirma GAP-CTX2/GAP-02. |
| `execution/fork/__init__.py` | 96 | íntegro 1→EOF (cruce 05) | `ForkPolicy`(inherit_messages/permissions/tool_pool/capabilities+propagate_abort), `ForkSnapshot`(session_id,user_id,subagent_depth,messages,permissions,tool_pool,capabilities — **sin `read_file_state` ni `rendered_system_prompt`** ⇒ confirma CtxR1/CtxR4/GAP-CTX4), `RuntimeContextForker.fork` (agent_id nuevo, aísla/hereda por política). ✅ E2/E3/E4. |
| `execution/local/runtime.py` | tramos 204, 314-316, 332 | tramos-con-rango (cruce 05) | Cableado de `subagent_depth`+1 (204), `ctx.subagent_depth=`(316), `ctx.is_subagent=parent is not None`(315). Confirma E8/A29 ✅ y que `is_subagent` (A+) se **puebla** de verdad (L09). |
| `tests/test_context_homologation.py` | tramos 220-247 | tramos-con-rango | 3 xfail(strict) con anclas exactas: `..._tracks_read_file_state`(Tool.ts:181), `..._permissions_carry_mode`(AppStateStore.ts:109+Tool.ts:124), `..._carries_agent_type`(Tool.ts:246). Siguen xfail = gaps abiertos (L05). |

### A (referencia = canónico) — contrapartes
| Archivo | LOC | Lectura | Veredicto |
|---|---|---|---|
| `Tool.ts` | 792 | **íntegro 1→EOF** (archivo más grande, L08) | `ToolUseContext` (158-300): los ~45 campos enumerados A1-A33, incl. las 15 UI-callbacks de A33 — enumeración íntegra confirmada. `ToolPermissionContext`(123-138)+`getEmptyToolPermissionContext`(140-148), `ToolResult.contextModifier`(330), `Tool`/`buildTool` (302-792, fuera del ctx). Anclas de línea del doc/tests verificadas EXACTAS: :181, :246, :124, :330. |
| `state/AppStateStore.ts` | 569 | **íntegro 1→EOF** | `AppState`(89-452): B1-B12; `mode:PermissionMode` en `getDefaultAppState`(500-503) confirma que el canónico sí lleva modo. El grueso (~55 campos: bridge/teams/tmux/bagel/computer-use/speculation/plugins/remote/ultraplan/…) = superficie terminal/REPL ⇒ ⛔ catch-all B12 (L10, divergencia por arquitectura single-user). |
| `context.ts` | 189 | íntegro 1→EOF | `getGitStatus`(branch/main/status-short/log-5/user.name, trunca 2k), `getSystemContext`, `getUserContext`(CLAUDE.md+fecha), `setSystemPromptInjection` (debug ant), memoize. Confirma F1-F5 y GAP-CTX3 (no portado). |
| `utils/forkedAgent.ts::createSubagentContext` | 345-462 (+doc 320-344) | tramos-con-rango | Aísla (readFileState clonado, colecciones frescas, callbacks no-op), hereda options/messages, agentId nuevo, abort child/share, `shouldAvoidPermissionPrompts` wrap, `contentReplacementState` clonado, queryTracking depth+1. Confirma E1-E8. |

### §Nota de honestidad
- **Corrección de método (usuario, 2026-07-17):** la 1ª ronda de esta validación fue *confirmación de
  documentación* (leer A, comprobar que la tabla del doc enumera A y que B carece de lo que el doc dice) — NO es
  la tarea. La tarea es **verificación de completitud A vs B**: para cada comportamiento de A, abrir la
  **implementación de B** y confirmar que lo reproduce (L09, cablear ≠ existir). Se re-hizo así: las filas ✅/🔀
  se re-verificaron leyendo el **cableado real de B**, no la tabla:
  - **A2/A8 (abort ✅):** `ctx.stop` chequeado en `agent_loop.py:173/186`, pasado al modelo `:227`, y en
    `tools/dispatcher.py:54` antes de ejecutar la tool. Cancelación cooperativa cableada end-to-end. **Se sostiene.**
  - **E5 (avoid-prompts → filtro toolset 🔀):** `capabilities/resolver.py:42-47` llama `list_available(mode=
    "background")` cuando `ctx.is_subagent`; `tools/registry.py:33` filtra `t.safe_for_background`. Mecanismo real.
    **Se sostiene.**
  - **D1/D2 (presentation ✅):** `sanitize_output` invocado en el choke point del dispatcher (`:42`) + TTS
    (`runtime.py:244`). **Se sostiene el mecanismo** — pero se destapó la costura latente `to_llm` (ver D2), que la
    confirmación-de-doc no podía cazar.
  - **A+ `is_subagent` (✅):** poblado de verdad en `runtime.py:315`. **Se sostiene.**
- **Segundo filo de la honestidad (L10, anti-padding):** la costura latente `to_llm` es de la extensión
  PathPresentation, que **no tiene contraparte canónica** → **no es deuda A-vs-B** y NO se sumó al conteo de
  homologación. Inflarla sería tan deshonesto como ocultarla.
- Esta es una **validación de 2ª vuelta**: se re-abrieron A (Tool.ts/AppStateStore.ts/context.ts 1→EOF;
  forkedAgent.ts en su tramo) **y** B (los 4 archivos de `context/` íntegros + los cruces
  `permissions.py`/`fork/__init__.py`/`runtime.py` + el cableado de comportamiento en `dispatcher.py`/
  `resolver.py`/`registry.py`/`agent_loop.py`) — no me apoyé en el doc previo.
- **Un riesgo de sobre-declaración descartado tras verificar** (L10, doble filo): `RuntimeContextForker.fork`
  NO propaga `subagent_depth`/`is_subagent` al hijo — parecía que E8/A29 ✅ estaba sobre-declarado. Al abrir
  `execution/local/runtime.py` se confirmó que el cableado vive ahí (204/315/316) y que la tool `agent.py:73`
  lo usa como tope: E8 ✅ es **correcto**. El campo se cablea en 05 por diseño, no es gap de 03.
- **Imprecisión menor NO corregida** (no es discrepancia sustantiva): el encabezado cita
  "`ToolPermissionContext` (123-148)"; el tipo es 123-138 y `getEmptyToolPermissionContext` 140-148 (citado
  aparte justo después). Describe el bloque de permisos, cuyas internas 03 delega explícitamente a 06. Se deja
  como está y se declara aquí.
- **No re-ejecutado**: los conteos de suite de la §Evidencia ejecutada ("11 passed/3 xfailed", "559 passed…")
  son artefactos de la 1ª pasada; en MODO VALIDACIÓN no se implementa ni se corre la suite. Los 3 xfail(strict)
  se verificaron por lectura (marcadores + anclas exactas), no por ejecución.

### 4 preguntas de cierre
1. **¿Se revisó todo cada archivo de A listado?** — **Sí.** `Tool.ts`(792) y `AppStateStore.ts`(569) leídos
   1→EOF en esta 2ª vuelta; `context.ts`(189) íntegro; `createSubagentContext`(345-462) en su tramo íntegro.
2. **¿Se revisó todo cada archivo de B listado?** — **Sí.** Los 4 de `context/` íntegros + los cruces
   `permissions.py`/`fork/__init__.py` íntegros y `runtime.py` en los tramos del cableado.
3. **¿Los hallazgos fueron exhaustivos (no superficiales)?** — **Sí.** Los 4 findings (FIND-CTX1, GAP-CTX2/02,
   FIND-CTX2, GAP-CTX3/CTX4) confirmados por **ausencia/presencia leída en el fuente**, no por grep; enumeración
   íntegra de los ~45 campos del `ToolUseContext` y del store; cableado `subagent_depth`/`is_subagent` seguido
   de punta a punta (L09).
4. **¿Quedó todo cubierto (nada pendiente)?** — **Sí.** Los 🔀 "vive en otro subsistema" tienen destino
   nombrado (modelo→16, mcp→11, tasks/agents→05, hooks/permisos→06, skills→12, todos→10); FIND-CTX1→10·R0,
   CtxR1/CtxR4→05·fork, GAP-CTX2→Deuda B `B-02`, GAP-CTX3→05·GAP-EXEC5. Nada marcado ⛔ sin abrir.
