# 07 · events

Runtime: `events/{protocol.py (23), bus.py (46), event_types.py (44), __init__.py (15)}` — **~128 LOC**.
Emisión/consumo reales (el bus no vive solo — su semántica está en quién emite y quién escucha):
- `models/caller.py:207-245` — traduce el stream del provider (`agentic_models`) a `TokenEvent` /
  `ToolCallEvent` / `DoneEvent(usage)` / `ErrorEvent` (async generator; NO emite `ToolResultEvent`).
- `loop/agent_loop.py` — `_emit` (152), consumo del stream (247-258), emisión de `ToolResultEvent`
  tras dispatch (312, 324). `run()` **retorna `None`**: `done`/`done.usage` sólo deciden continuación (348).
- `execution/local/runtime.py:234-304` — `_wire_tts` (Token/Done→TTS), `_make_bus`
  (ToolCall/ToolResult → `registry.push_event`; `subscribe_all(on_event)`), `_fire_stop`
  (SubagentStop, 06), `_notify` (BackgroundNotification).
- `execution/tasks/registry.py:112` — `push_event(task_id, dict)` → `rec.events.append` (buffer poll/drain).
- `execution/session/session.py:16,42` — `Usage(input/output)` + `Session.usage`/`turn_count` (slots).

Contrapartes canónicas **leídas íntegras**:
- `entrypoints/sdk/coreSchemas.ts` — `SDKMessageSchema` (**unión de 24 variantes**, 1854-1881) + cada
  variante campo-a-campo (1290-1806): `SDKAssistantMessage`, `SDKUserMessage`(+Replay),
  `SDKResultMessage`(success/error, 1407-1455), `SDKSystemMessage`(init), `SDKPartialAssistantMessage`
  (stream_event), `SDKCompactBoundaryMessage`, `SDKStatusMessage`, `SDKAPIRetryMessage`,
  `SDKLocalCommandOutputMessage`, `SDKHookStarted/Progress/ResponseMessage`, `SDKToolProgressMessage`,
  `SDKAuthStatusMessage`, `SDKTaskNotification/Started/ProgressMessage`, `SDKSessionStateChangedMessage`,
  `SDKFilesPersistedEvent`, `SDKToolUseSummaryMessage`, `SDKRateLimitEvent`,
  `SDKElicitationCompleteMessage`, `SDKPromptSuggestionMessage`; + no-unión pero definidos:
  `SDKStreamlinedText/ToolUseSummary`, `SDKPostTurnSummaryMessage`. `ModelUsageSchema` (17-28).
- `remote/sdkMessageAdapter.ts` (303) — `convertSDKMessage` (switch sobre TODAS las variantes → Message/StreamEvent/ignored), `isSessionEndMessage` (`type==='result'`), `getResultText`.
- `utils/hooks/hookEvents.ts` (192, leído en 06) — bus de progreso de EJECUCIÓN de hook (⛔ como sistema separado; el canónico lo **funde en el stream** vía `hook_started/progress/response`).
- `query.ts`/`QueryEngine.ts` (leídos íntegros en 02) — releídos con lente "qué mensajes SDK emite": el
  agente **serializa** todo su progreso como un ÚNICO `AsyncIterable<SDKMessage>`.

## RE-AUDITORÍA (2026-07-12) — lectura íntegra campo-a-campo de `coreSchemas.ts` (1256-1852)

**Conteo duro VERIFICADO**: la unión `SDKMessageSchema` (1854-1881) tiene **exactamente 24 variantes**
(contadas una a una) → la cabecera EVT2 **era correcta** (a diferencia de HOOK_EVENTS 27≠28). Sitios de
emisión del runtime **re-verificados línea-a-línea** (caller.py 210-243 · agent_loop.py _emit 152 / consumo
247-258 / ErrorEvent emitido en vivo ANTES del break / ToolResult 312·324 / run()→None break sin return ·
runtime.py _wire_tts/_make_bus/_fire_stop/_notify 234-304 · registry.push_event 112 · session.py Usage/turn_count)
→ **todos exactos**. `sdkMessageAdapter.ts` releído íntegro (302): 4 exports — `convertSDKMessage`,
`isSessionEndMessage`, **`isSuccessResult`** (el doc omitía este), `getResultText`.

**Pero la enumeración de variantes SUBCUBRÍA schemas** (mismo modo de fallo que 06, donde el archivo grande
se glosó). Correcciones aplicadas abajo:
- **`SDKSystemMessage` init (1457-1494) NO tenía fila** — el frame de apertura del stream (handshake de
  sesión). → nueva fila **F0** + **FIND-EVT9** (❌).
- **Enum de error de assistant (7 valores, 1256-1266)** — `authentication_failed·billing_error·rate_limit·
  invalid_request·server_error·unknown·max_output_tokens` — inline en `assistant.error` (1352), taxonomía
  tipada DISTINTA del `subtype` terminal del result. → nueva fila **D5** (🟡).
- **`SDKUserMessageContent.priority ['now','next','later']`** (1280) + `isSynthetic`/`tool_use_result`/
  `timestamp` — el `priority` liga **05·FIND-EXEC12** (pendingMessages/SendMessage-a-vivo). → enriquece K2.
- **`SDKSessionInfoSchema` (1812-1852)** — no-unión (listSessions/getSessionInfo): sessionId/summary/
  lastModified/customTitle/firstPrompt/gitBranch/cwd/tag/createdAt. → nueva fila **K5** (🔀 → 15 storage).
- Menores: `workflow_name` en task_started (local_workflow, enriquece G1); shape rico de rate-limit/overage
  (`SDKRateLimitInfo` 1305-1345: rateLimitType five_hour/seven_day*/overage + overageDisabledReason ×12 +
  isUsingOverage; enriquece J1); `fast_mode_state` (off/cooldown/on) en result/init/status (⛔ UX, nota F2);
  el error result ALSO lleva usage/modelUsage/total_cost_usd/permission_denials (accounting completo, no solo
  el success — precisa D2).

**Veredicto**: doc de 07 MAYORMENTE fiable y line-preciso en emisión; la re-audit añade 1 ❌ (init/EVT9) +
2 filas nuevas (D5/K5) + enriquecimientos. NO fue superficial como 08. Sin cambios de código (solo-doc).

## Tesis arquitectural

El runtime `events/` **NO es** el "sistema de eventos" del canónico, porque **el canónico no tiene un
bus de eventos**: tiene un **STREAM de mensajes serializado** — un `AsyncIterable<SDKMessage>` que **ES el
protocolo público** entre el core del agente y TODO consumidor (REPL, cliente SDK, backend remoto CCR por
WebSocket). Un solo canal, ordenado, ~24 variantes, que abarca transcripto (assistant/user), streaming
(stream_event), resultado terminal (result), ciclo de subagentes (task_*), progreso de hooks
(hook_*), compactación (compact_boundary), rate limits, estado de sesión, artefactos, elicitación.

El runtime `EventBus` es una primitiva distinta y más chica: un **bus tipado en-proceso** de
observación de EJECUCIÓN (`subscribe(Type,h)` / `subscribe_all(h)` / `emit`), con 5 eventos
(Token/ToolCall/ToolResult/Done/Error) que viajan modelo→loop→consumidor **dentro del mismo proceso**.

**La homologación correcta es del SEAM, no de forma** (como en 06): el runtime **parte en TRES canales**
lo que el canónico **unifica en UNO**:

1. **`EventBus`** (tipado, in-proc, push): Token/ToolCall/ToolResult/Done/Error — observación en vivo.
2. **`registry.push_event`** (dicts sin tipar, per-task, **poll/drain** vía `rec.events`): espejo
   tool_start/tool_result para el streaming de subagentes + notificación de fin (`_notify`).
3. **`ctx.messages`** (acumulación, NO emitido): el transcripto — el consumidor lo proyecta/persiste.

Bajo esa lente, **muchas variantes SDK = 🔀 delegadas** (viven en otro subsistema o en la capa de
serialización del integrador que mapearía EventBus→wire). Los gaps REALES de 07 son:

1. **Sin resultado terminal con accounting** — el seam no puede reconstruir `SDKResultMessage`
   (usage/cost/num_turns/denials). **Aquí aterriza FIND-L2**: `DoneEvent.usage` existe por-turno pero
   **ni se acumula ni se surface**; **`Session.usage` (tokens) es slot muerto** — `run()→None`, y nada
   suma `done.usage`. **Corrección gate 11 (2ª vuelta): `Session.turn_count` NO es slot muerto** — se
   alimenta en `runtime.py:398` (`session.turn_count = ctx.turn_count`, incrementado en `agent_loop.py:189`)
   y se surface a `TaskRecord.turn_count` vía `complete()` (402→registry.py:148); `duration_ms` ídem. El
   gap real es **usage(tokens)+cost**, no turn_count.
2. **Taxonomía incompleta** (5 vs 24) — faltan puntos que el integrador necesitaría oír para
   reconstruir el stream canónico (tool_progress, task_*, session_state_changed, compact_boundary…).
3. **Tres canales sin costura de serialización** — no hay `EventBus→SDKMessage` wire; el BFF/transporte
   remoto lo necesitaría. `subscribe_all` es el gancho, pero no hay forma canónica que produzca.
4. **`Usage` empobrecido y duplicado** — dos definiciones divergentes, sin cache-tokens ni costUSD.

## Tabla feature-by-feature

### A · Modelo del subsistema (bus in-proc vs stream serializado)

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste arquitectural |
|---|---|---|---|---|
| A1 | Protocolo público = `AsyncIterable<SDKMessage>` (un canal ordenado core↔consumidor) | `EventBus` in-proc + **`LocalAgentRuntime.stream()`** + 2 canales laterales | 🔀 | Decisión deliberada: bus tipado in-proc en vez de stream serializado. **Precisión gate 11 (2ª vuelta)**: el productor de canal único ordenado **SÍ existe** — `runtime.py:153-181` `stream()` construye un `AsyncIterator[Event]` sobre `subscribe_all`→`asyncio.Queue`→sentinela, con **orden de emisión garantizado** y sin pérdida (docstring 158-163). Lo que falta es SÓLO la serialización `Event→SDKMessage` **wire** (dict de 24 variantes) encima de ese productor (GAP-EVT5); un consumidor in-proc YA puede iterar el stream ordenado, un cliente remoto CCR necesita además el wire. |
| A2 | Ordenamiento total de eventos (un solo stream) | 3 canales (bus push, registry poll, messages) | 🔀 | El orden relativo entre `push_event` (poll) y `emit` (push) no está garantizado para el consumidor; el canónico lo garantiza por construcción (un iterable). |
| A3 | `Event` base inmutable / extensible por el consumidor | `Event` frozen + `subscribe(MyType,…)` | ✅ | El bus permite tipos propios sin tocar el runtime (primitiva de extensión). El canónico no tiene equivalente (unión cerrada Zod). Mejora del runtime en extensibilidad in-proc. |
| A4 | Aislamiento de errores de handler | `emit` captura+loguea por handler (bus.py:42-45) | ✅ | Un handler que lanza no rompe el stream. El canónico depende del consumidor del iterable. |

### B · Streaming incremental de texto/thinking

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| B1 | `stream_event` (`SDKPartialAssistantMessage.event: RawMessageStreamEvent`) — deltas crudos del SDK | `TokenEvent(content=str)` | 🟡 | El runtime aplana a texto: sólo `text_delta` → `TokenEvent`; `thinking_*`, `content_block_start/stop`, `message_start` se **descartan** (caller.py:245). El canónico reenvía el evento crudo (thinking, signatures, índices de bloque). Ajuste: preservar thinking deltas como evento propio (necesario para `thinking_tokens`, hoy hardcode 0). |
| B2 | `parent_tool_use_id` en cada partial (atribución a subagente) | ausente en `TokenEvent` | 🔀 | El runtime atribuye por `task_id` en el canal registry, no en el evento. El bus in-proc es per-task (un bus por tarea, `_make_bus(task_id)`), así que la atribución es implícita al bus. |
| B3 | `session_id`/`uuid` por mensaje | ausente | 🔀 | Metadatos de correlación del wire; en in-proc el bus ya está scoped. Los añadiría el serializador A1. |

### C · Ciclo de tool-use

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| C1 | tool_use como bloque dentro de `assistant` message (no evento aparte) | `ToolCallEvent(name,input,call_id)` | 🔀 | El runtime emite un evento dedicado **y** acumula el tool_call en `ctx.messages` (agent_loop.py:277). Dualidad correcta: evento para observar, mensaje para persistir. |
| C2 | tool_result como bloque `user` message | `ToolResultEvent(call_id,result,is_error)` | ✅ | Emitido por el loop tras dispatch (312/324), también acumulado en messages. Equivalente. |
| C3 | `tool_progress` (heartbeat cada N s: `elapsed_time_seconds`, `tool_use_id`, `task_id`) | — | ❌ | **FIND-EVT6**. No hay progreso de tools largas. El canónico lo emite para observabilidad/HITL. Ajuste: evento `ToolProgressEvent` emitido por el dispatcher para tools que excedan un umbral. |
| C4 | `tool_use_summary` (resumen acumulado "Read 2 files, wrote 1") | — | 🔀 | Streamlining de salida (UX) → presentación/⛔. No es gap del core. |
| C5 | `registry.push_event({tool_start/tool_result})` dicts per-task | canal 2 | 🔀 | **FIND-EVT8**: espejo untyped de C1/C2 para el streaming de subagentes; buffer poll (`rec.events`), no push. Sin `usage`/`summary`. Contraparte de `task_progress`. |

### D · Resultado terminal y errores

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| D1 | `SDKResultMessage` (success) — `result`, `num_turns`, `duration_ms/api_ms`, `total_cost_usd`, `usage`, `modelUsage`, `permission_denials`, `structured_output`, `stop_reason` | `DoneEvent(stop_reason, usage?)` + `run()→None` | ❌ | **FIND-EVT1/GAP-EVT2**. `DoneEvent` es **per-turno**, no terminal: sin num_turns, cost, denials, duración, structured_output. No hay mensaje "fin de la ejecución" que el consumidor pueda distinguir de un corte por tool_calls (salvo `stop_reason != 'tool_calls'`). Ajuste: emitir un `ResultEvent` terminal al salir del loop, agregando lo acumulado. |
| D2 | `SDKResultMessage` (error) — `subtype ∈ {error_during_execution, error_max_turns, error_max_budget_usd, error_max_structured_output_retries}`, `errors[]`, `num_turns`, `usage` | `ErrorEvent(message)` emitido al bus en vivo (agent_loop.py:248) + loop añade `"[error:…]"` a messages y `break` (267-270) | 🟡 | **FIND-EVT4**. El error del modelo **sí se observa en vivo** (emitido al bus antes de clasificar) — eso está homologado. Falta el **resultado terminal** de error: sin `subtype` ni accounting, el loop lo entierra en el transcripto. `error_max_turns` no existe (el límite de 50 turnos sólo loguea warning, agent_loop.py:352 — liga FIND-EXEC5). `error_max_budget_usd` bloqueado por accounting (F). **Re-audit**: el `SDKResultError` (1428-1451) lleva accounting COMPLETO igual que el success — `usage`, `modelUsage` (por modelo), `total_cost_usd`, `num_turns`, `permission_denials`, `errors[]` — no sólo el subtype; el resultado terminal de error del runtime debería agregar todo eso, no sólo un string. |
| D3 | `isSessionEndMessage` = `type==='result'` (señal de fin de sesión) | — | ❌ | Sin evento que marque fin de sesión; el consumidor infiere por ausencia de más eventos. |
| D4 | `stop_reason` mapeado (`toolUse`→`tool_calls`) | caller.py:227 | ✅ | Mapea `toolUse→tool_calls`, resto passthrough. Equivalente al `stop_reason` del result. |
| D5 | `SDKAssistantMessage.error` — enum **tipado de 7 valores** (`authentication_failed`, `billing_error`, `rate_limit`, `invalid_request`, `server_error`, `unknown`, `max_output_tokens`) inline en CADA mensaje assistant (1256-1266/1352) | `ErrorEvent(message: str)` (texto plano) | 🟡 | **Re-audit**. La taxonomía de error del canónico vive en DOS niveles: (a) inline por-mensaje-assistant (este enum de 7, correlacionable a reintento/billing/auth) y (b) el `subtype` terminal del result (D2). El runtime aplana ambos a un `message` string sin clasificar → un consumidor no puede distinguir `rate_limit` (reintentable, liga J3/api_retry) de `billing_error` (fatal) ni `max_output_tokens` (truncado). Ajuste: `ErrorEvent` debería llevar un `code` = este enum. |

### E · Usage / accounting  *(hogar de FIND-L2)*

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| E1 | `ModelUsage`: inputTokens, outputTokens, **cacheReadInputTokens**, **cacheCreationInputTokens**, **webSearchRequests**, **costUSD**, **contextWindow**, **maxOutputTokens** | `events/Usage(input,output,thinking)` | 🟡 | **FIND-EVT5**. Faltan cache-tokens (clave para coste real con prompt-cache — recordar prefijo byte-idéntico del fork, 05), webSearchRequests, costUSD, contextWindow, maxOutputTokens. `thinking_tokens` existe pero **hardcode 0** en caller.py:231. |
| E2 | `result.usage` agregado + `result.modelUsage` (record **por modelo**) | — | ❌ | **FIND-EVT1**. `DoneEvent.usage` es per-turno y **no se acumula**; no hay agregado por-sesión ni breakdown por-modelo. |
| E3 | Acumulación a lo largo de turnos → `Session.usage` | `Session.usage` existe pero **nadie lo alimenta** (turn_count SÍ) | ❌ | **FIND-L2 físico**: el slot de acumulación de tokens EXISTE (session.py:42) y el dato per-turno EXISTE (`DoneEvent.usage`), pero **falta el cable** que sume `done.usage` en `Session.usage` al consumir el `DoneEvent` — `complete()` recibe `input_tokens/output_tokens=0` SIEMPRE (runtime.py:403-404). `run()→None` no devuelve accounting. **Precisión gate 11**: `Session.turn_count` SÍ se alimenta (runtime.py:398 desde `ctx.turn_count`) y surface a `TaskRecord.turn_count` (402→registry.py:148); el slot muerto es SÓLO `usage` (tokens). |
| E4 | Dos `Usage` divergentes | `events/Usage(i,o,thinking)` ≠ `session/Usage(i,o)` | ❌ | **FIND-EVT5**. Definiciones incompatibles en dos módulos; ninguna con cache/cost. Ajuste: un único `Usage` canónico (= ModelUsage) compartido. |
| E5 | `total_cost_usd` (coste $) | — | ❌ | **Bloquea G2 maxBudgetUsd (05) y coste/modelo (16)**. Requiere E1(costUSD) que requiere tarifa por modelo (16). |

### F · Estado de sesión / turno

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| F0 | `SDKSystemMessage` **init** (frame de apertura del stream: `agents[]`, `apiKeySource`, `betas`, `claude_code_version`, `cwd`, `tools[]`, `mcp_servers[]{name,status}`, `model`, `permissionMode`, `slash_commands[]`, `output_style`, `skills[]`, `plugins[]`, `fast_mode_state`) | — | ❌ | **FIND-EVT9** (re-audit). El PRIMER mensaje del stream = handshake que anuncia las capacidades de la sesión. El runtime NO emite ningún evento init/handshake; esa info vive dispersa en `ToolUseContext`/`AppState`/`factory` y el consumidor la leería directo. Para un consumidor remoto al modo CCR (el **BFF de agentic_assistant gestiona sesiones**) es el frame que bootstrapea la vista de sesión (tools/model/mcp/skills/slash_commands/permissionMode disponibles). Ajuste: el serializador de GAP-EVT5 debe producir un `init` a partir del contexto ensamblado al arrancar la sesión. Liga 18 (factory) + GAP-02 (permissionMode). |
| F1 | `session_state_changed` (`idle`/`running`/`requires_action`) — señal AUTORITATIVA de turn-over | — | ❌ | **FIND-EVT7**. El runtime infiere fin por `DoneEvent.stop_reason != 'tool_calls'` (o `_ends_turn`, agent_loop.py:348), pero no emite estado de sesión. `requires_action` es justo la señal HITL de `_ends_turn` (AskUserQuestion, 02) — homologarla desbloquea observabilidad HITL. |
| F2 | `status` (`SDKStatusMessage`: `status`∈{compacting, null}, `permissionMode`) | — | ❌ | Sin eventos de estado transitorio. Liga compactación (I) y permission mode (GAP-02). **Re-audit**: `fast_mode_state` (off/cooldown/on) aparece en result/init/status = feature de Fast mode (⛔ UX/config de sesión, fuera de alcance del core). |
| F3 | `post_turn_summary` (resumen background por turno: status_category, needs_action, artifact_urls) | — | 🔀 | Feature de agentes background/coordinator → 05/13. No gap del core del bus. |
| F4 | `prompt_suggestion` (predicción del siguiente prompt) | — | ⛔ | UX. Fuera de alcance. |

### G · Ciclo de vida de subagentes / tasks

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| G1 | `task_started` (task_id, tool_use_id, description, task_type, **workflow_name** `local_workflow`, prompt) | `registry.push_event`? — **no emitido** | ❌ | El registry bufferiza tool_start/result pero **no** un evento de inicio de task. Liga `TaskRecord` (05). **Re-audit**: `workflow_name` sólo se setea cuando `task_type==='local_workflow'` (meta.name del script de workflow) — concepto de workflows/scripts fuera del alcance actual del runtime (⛔ salvo que se adopten). |
| G2 | `task_progress` (usage{total_tokens,tool_uses,duration_ms}, last_tool_name, summary) | `push_event(tool_start/result)` dicts | 🟡 | **FIND-EVT8**. Espejo parcial: hay tool_start/result por task pero sin `usage`/`tool_uses`/`duration`/`last_tool_name`/`summary` agregados. Depende de E (accounting). |
| G3 | `task_notification` (status completed/failed/stopped, output_file, summary, usage) | `_notify`→`BackgroundNotification` (runtime.py:294) | 🟡 | Contraparte real de la notificación de fin (05·GAP-EXEC1 dedup). Falta `output_file`/`usage`. `_notify` gateado sólo por `parent_session_id`; `final_text` puede ir vacío (05·FIND-EXEC3). |
| G4 | Todo esto viaja en el MISMO stream que el agente padre | canal 2 separado (poll) | 🔀 | El canónico intercala task_* en el stream principal (atribución por `parent_tool_use_id`); el runtime los aísla en `rec.events`. |

### H · Compactación

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| H1 | `compact_boundary` (trigger manual/auto, pre_tokens, preserved_segment{head/anchor/tail_uuid}) | — | ❌ | **GAP-EVT3**. Depende de la compactación **no portada** (02 motor #1). Sin evento no hay marca de frontera para el resume/re-surface de memoria (13). |

### I · Progreso de hooks (funde 06 en el stream)

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| I1 | `hook_started` / `hook_progress` / `hook_response` (hook_id, hook_name, hook_event, stdout/stderr/output, outcome) | `hookEvents.ts` bus separado ⛔ en 06 | ❌ | **GAP-EVT4**. El canónico **funde el progreso de hooks en el stream principal**; el runtime ni lo tiene (06·FIND-HOOK). Para homologar el stream unificado, `HookRunner` debería emitir estos al EventBus. Reconciliar con 06. |

### J · Infra / transporte (mayormente delegado)

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| J1 | `rate_limit_event` (`SDKRateLimitInfo` 1305-1345: `status` allowed/warning/rejected, `resetsAt`, `rateLimitType` five_hour/seven_day/seven_day_opus/seven_day_sonnet/overage, `utilization`, `overageStatus`, `overageResetsAt`, `overageDisabledReason` ×12, `isUsingOverage`, `surpassedThreshold`) | — | 🔀 | Concern de transporte/cuenta (suscripción claude.ai + **overage**) → 16/18 o integrador. **Re-audit**: shape mucho más rico de lo anotado — el modelo de overage (créditos/tiers) es de la capa de cuenta, no del core del bus; el bus podría transportarlo si el caller lo emitiera. |
| J2 | `auth_status` (isAuthenticating, output, error) | — | 🔀 | Auth de sesión → 18/integrador. |
| J3 | `api_retry` (attempt, max_retries, retry_delay_ms, error_status, error) | — | ❌ | Liga 02 motor #2 (recuperación de errores del modelo, no portado). El caller no reintenta ni emite reintentos. |
| J4 | `files_persisted` (files/failed/processed_at) | — | 🔀 | Artefactos → 13. |
| J5 | `elicitation_complete` (mcp_server_name, elicitation_id) | — | 🔀 | MCP → 11. |
| J6 | `local_command_output` (slash command output) | — | ⛔ | Slash commands de terminal/UX → 12/⛔. |

### K · Transcripto (delegado por diseño)

| # | Feature (canónico) | Runtime | Estado | Diferencia / ajuste |
|---|---|---|---|---|
| K1 | `assistant` message (message, parent_tool_use_id, error, uuid) en el stream | `ctx.messages.append({assistant})` (no emitido como evento) | 🔀 | El canónico serializa el transcripto EN el stream (el consumidor lo renderiza); el runtime lo **acumula** en `ctx.messages` y delega proyección/persistencia al consumidor (01/03/15). Correcto: separar estado (messages) de observación (bus). |
| K2 | `user` message (+Replay, isReplay; `SDKUserMessageContent`: `isSynthetic`, `tool_use_result`, **`priority ['now','next','later']`**, `timestamp`) | `ctx.messages` | 🔀 | Ídem. `isReplay` (resume) → 15/storage. **Re-audit**: el campo `priority` = prioridad del mensaje en la cola de input → liga **05·FIND-EXEC12** (pendingMessages/drainPendingMessages = SendMessage-a-un-agente-vivo) y **FIND-SIG13** (dos niveles de abort). `isSynthetic`/`tool_use_result` = inyección de resultados de tool en el transcripto. Confirmar cobertura al documentar 05/10 (SendMessage). |
| K3 | `streamlined_text` / `streamlined_tool_use_summary` | — | ⛔ | Streamlining de salida (UX). |
| K4 | `convertSDKMessage` (adaptador stream→Message del REPL; +`isSessionEndMessage`/`isSuccessResult`/`getResultText`) | — | ⛔ | Capa de presentación del cliente CCR (deserializa el wire → Message del REPL, mayormente `→ignored`/SystemMessage plano); el runtime delega al integrador (sería el consumidor de `subscribe_all`). Es el CONSUMIDOR espejo del productor que falta (GAP-EVT5). |
| K5 | `SDKSessionInfoSchema` (no-unión, 1812-1852; `listSessions`/`getSessionInfo`: sessionId, summary, lastModified, fileSize, customTitle, firstPrompt, gitBranch, cwd, tag, createdAt) | — | 🔀 | **Re-audit**. NO es una variante del stream — es el índice/metadata de sesiones persistidas. En el runtime es concern de **15·storage** (índice de sesiones sobre FS/MinIO) + entrypoint de listado del BFF. Sin equivalente aún; se documenta aquí para no perderlo → reconciliar en 15. |

## Resumen de estados

✅5 · 🟡8 · 🔀15 · ❌16 · ⛔4  (sobre ~48 features de las 24 variantes SDK + mecánica del bus).
Re-audit 2026-07-12: +F0/EVT9 (❌ init handshake), +D5 (🟡 enum error assistant), +K5 (🔀 SDKSessionInfo→15).
Conteo de la unión **24 CONFIRMADO** contra la fuente (1854-1881).

## Hallazgos

- **FIND-EVT1** (❌ CRÍTICO, correctitud/accounting) — **FIND-L2 de 02 aterriza aquí**: `DoneEvent.usage`
  se emite por-turno pero **ni se acumula ni se surface como resultado terminal**; **`Session.usage`
  (tokens) es slot muerto** (nadie lo alimenta → `complete()` recibe 0/0 en runtime.py:403-404);
  `run()→None`. Sin usage agregado el runtime no puede emitir `SDKResultMessage` con coste ⇒ **bloquea
  G2 maxBudgetUsd (05) y coste/modelo (16)**. **Corrección gate 11 (2ª vuelta)**: la 1ª pasada declaraba
  `turn_count` también "slot muerto" — **inexacto**: `Session.turn_count` SÍ se alimenta (runtime.py:398 ←
  `ctx.turn_count`, agent_loop.py:189) y se surface a `TaskRecord.turn_count`/`duration_ms` (complete()
  400-405). El gap A-vs-B es **usage(tokens)+costUSD**, no el conteo de turnos.
- **FIND-EVT2** (❌ taxonomía) — 5 eventos (Token/ToolCall/ToolResult/Done/Error) vs **24 variantes** de
  `SDKMessage`. Faltan puntos core: resultado terminal, tool_progress, task_*, session_state_changed,
  compact_boundary, api_retry.
- **FIND-EVT3** (🔀 tres canales) — el canónico **unifica** todo en UN stream serializado (protocolo
  público REPL/SDK/CCR); el runtime lo **parte en 3** (EventBus push · registry poll · ctx.messages). Sin
  serializador `EventBus→SDKMessage` (GAP-EVT5) el runtime no es consumible por un cliente remoto.
- **FIND-EVT4** (🟡 resultado/error) — el `ErrorEvent` del modelo **sí se observa en vivo** (emitido al bus
  antes de clasificar, agent_loop.py:248) ⇒ observación homologada; falta el **resultado terminal** de error
  con `subtype` y accounting (el loop lo entierra en el transcripto como `"[error:…]"`). `error_max_turns`
  inexistente (liga FIND-EXEC5).
- **FIND-EVT5** (❌ Usage) — **dos `Usage` divergentes** (events i/o/thinking ≠ session i/o); **ninguno**
  con cache_read/cache_creation tokens, webSearchRequests, costUSD, contextWindow, maxOutputTokens;
  `thinking` hardcode 0. Unificar en un `Usage` = `ModelUsage` canónico.
- **FIND-EVT6** (❌ tool_progress) — sin heartbeat de tools largas.
- **FIND-EVT7** (❌ session_state) — sin `session_state_changed` (idle/running/**requires_action**); la
  señal HITL de `_ends_turn` (02) no se surface como estado observable.
- **FIND-EVT8** (🔀 push_event dicts) — canal 2 sin tipar (tool_start/result como dicts, buffer poll), sin
  usage/summary/last_tool_name; contraparte incompleta de task_progress/notification.
- **FIND-EVT9** (❌ init/handshake, **NUEVO en re-audit**) — el PRIMER mensaje del stream canónico,
  `SDKSystemMessage` subtype `init` (1457-1494), anuncia las capacidades de la sesión (tools, model,
  mcp_servers, permissionMode, skills, slash_commands, agents, plugins, output_style). El runtime NO emite
  ningún frame de apertura; esa info vive dispersa en `ToolUseContext`/`AppState`/`factory`. Un consumidor
  remoto al modo CCR — y el **BFF de agentic_assistant, que gestiona sesiones** — necesita este handshake
  para bootstrapear la vista de sesión. Ajuste: el serializador de GAP-EVT5 debe producir un `init` desde el
  contexto ensamblado. Liga 18 (factory) + GAP-02 (permissionMode). El doc original NO tenía fila para esto
  (omisión del mismo tipo que los ~15 ejecutores glosados en 06).

## Gaps

- **GAP-EVT1** = FIND-L2: seam de usage accounting (bloquea G2/16).
- **GAP-EVT2**: sin `SDKResultMessage` terminal (num_turns, cost, denials, structured_output; liga 05 max_turns/max_budget, 09 structured_output G3).
- **GAP-EVT3**: `compact_boundary` depende de compactación no portada (02 motor #1).
- **GAP-EVT4**: progreso de hooks (`hook_started/progress/response`) no surface — el canónico lo funde en el stream; reconciliar con 06.
- **GAP-EVT5**: serializador `EventBus→SDKMessage` wire (para BFF/transporte remoto CCR). **Precisión gate 11**: el **productor de canal único ordenado YA existe** (`LocalAgentRuntime.stream()` runtime.py:153-181, sobre `subscribe_all`); lo ausente es SÓLO el mapeo `Event→SDKMessage` (dict wire de 24 variantes) que se pondría encima de `stream()`, no el productor. Liga 18. La remediación EvR3 (`events/wire.py::to_sdk_message`) es exactamente ese mapeo — se cablea suscribiendo el serializador a `stream()`/`subscribe_all`, no creando el canal desde cero.

## Ajuste arquitectural recomendado (2ª pasada, NO implementar aún)

1. **Un `Usage` canónico** (= `ModelUsage`: input/output/cacheRead/cacheCreation/webSearch/costUSD/
   contextWindow/maxOutput) compartido por `events` y `session`; el caller lo puebla completo (incl.
   thinking y cache tokens del provider).
2. **Cablear la acumulación**: al consumir `DoneEvent`, sumar `done.usage` en `Session.usage` y `turn_count`
   (cierra FIND-L2/GAP-EVT1).
3. **`ResultEvent` terminal** emitido al salir del loop (success/error+subtype, num_turns, usage agregado,
   duración, permission_denials) — homologa `SDKResultMessage` y desbloquea `error_max_turns/budget`.
4. **`session_state_changed`** derivado de `_ends_turn`/DoneEvent (idle/running/requires_action).
5. **(Opcional, para consumo remoto)** serializador `EventBus→SDKMessage` en la capa del integrador/BFF —
   NO en el core; el core sólo debe emitir puntos suficientes (18).

Cabos que salen de aquí: E5/total_cost_usd → **16** (tarifa por modelo); `structured_output` en result →
**09** (G3, SyntheticOutputTool + jsonSchema); `compact_boundary` → **02** motor #1; hook_* en stream →
**06**; task_*/notification → **05**.

---

## Plan de homologación / remediación desarrollada

Diseño por finding. Seams: `events/protocol.py` (`Event` frozen base, `EventBusProtocol`,
`EventHandler`), `events/event_types.py` (`Usage`/`TokenEvent`/`ToolCallEvent`/`ToolResultEvent`/
`DoneEvent`/`ErrorEvent` — 5 tipos), `events/bus.py` (`EventBus`). **Tesis intacta**: el canónico serializa
UN stream `AsyncIterable<SDKMessage>` (24 variantes); el runtime parte en 3 canales (EventBus / registry
dicts / ctx.messages). La homologación es del SEAM serializador. `FIND-EVT1`/usage → **Deuda B `B-usage`**.

### EvR1 · FIND-EVT2 — taxonomía 5 → 24 variantes (los tipos core)
- **Comportamiento**: 5 event types vs 24 SDK variants. Añadir los tipos core que un consumidor remoto
  necesita: `InitEvent` (handshake, EvR2), `CompactBoundaryEvent` (H1/02·LR1), `ApiRetryEvent` (02·LR2),
  `ToolProgressEvent` (EVT6), `SessionStateEvent` (EVT7). Las variantes de terminal/UX → ⛔.
- **Seam/firma**: nuevos `@dataclass(frozen=True)` en `event_types.py`, subtipos de `Event`. **Orden**:
  primero (los demás los emiten). **Test**: `test_event_taxonomy_covers_core`.

### EvR2 · FIND-EVT9 (F0) — frame `init` de apertura del stream
- **Comportamiento**: el PRIMER mensaje del stream canónico (`SDKSystemMessage subtype:init`) anuncia
  `tools[]`/`model`/`mcp_servers[]`/`permissionMode`/`skills`/`slash_commands`/`agents`. El runtime no emite
  handshake → el **BFF de agentic_assistant** (gestiona sesiones) lo necesita para bootstrapear la vista.
- **Seam/firma**: `InitEvent(tools, model, mcp_servers, permission_mode, skills, slash_commands, agents)`
  emitido al arrancar la sesión, a partir del contexto ensamblado (pool + `ctx.app_state` + factory).
- **Cableado**: `AgentLoop.run` emite `InitEvent` ANTES del primer turno (tras ensamblar el pool). Liga 18
  (factory) + GAP-02 (permission_mode). **Orden**: tras EvR1. **Test**: `test_stream_starts_with_init`.

### EvR3 · GAP-EVT5 — serializador EventBus → SDKMessage (wire)
- **Comportamiento**: no hay serializador que convierta los eventos tipados del EventBus al formato wire
  `SDKMessage` que consume el BFF/CCR. Los 3 canales (bus/registry/messages) no se unifican en el borde.
- **Seam/firma**: `events/wire.py::to_sdk_message(event: Event) -> dict` (mapea cada `Event` a su variante
  SDK) + `SessionInfo` para listSessions (K5→15). Produce también el `init` (EvR2) y `result` terminal.
- **Cableado**: el BFF suscribe `subscribe_all(serializer)` y emite wire por SSE. **Orden**: tras EvR1/EvR2.
  **Test**: `test_wire_serializes_all_core_events`.

### EvR4 · FIND-EVT4 + D5 — resultado terminal + `code` tipado de error
- **Comportamiento**: (EVT4) falta un resultado terminal tipado (`SDKResultMessage` con
  subtype/accounting); `run()→None`. (D5) el error de assistant tiene enum de 7 valores
  (authentication_failed/billing_error/rate_limit/invalid_request/server_error/unknown/max_output_tokens)
  que `ErrorEvent(message:str)` aplana.
- **Seam/firma**: `ErrorEvent` gana `code: str | None`; nuevo `ResultEvent(subtype, usage, result_text)`
  emitido al cierre (liga `B-usage` para el accounting + 08·SIG8 para 'aborted_*'). `AgentLoop.run` puede
  devolver/emitir el `ResultEvent`.
- **Cableado**: loop cierre + caller (mapea el code). **Orden**: tras `B-usage`. **Test**:
  `test_result_event_carries_subtype_and_usage`, `test_error_event_has_code`.

### EvR5 · FIND-EVT6 — heartbeat `tool_progress`
- **Comportamiento**: sin `tool_progress` intra-tool (Bash largo no reporta avance). Liga 10·B10 (Bash
  `onProgress`).
- **Seam/firma**: `ToolProgressEvent(call_id, partial_output, elapsed_ms)`; el dispatcher/tool lo emite vía
  `ctx.event_queue` durante la ejecución (requiere que `ToolExecEnvironment.run_shell` sea un generador o
  acepte un callback `on_progress`). **Orden**: junto a 10·R8/R9 (Bash). **Test**: `test_bash_emits_progress`.

### EvR6 · FIND-EVT7 — `session_state_changed` (idle/running/requires_action)
- **Comportamiento**: sin señal de estado de sesión; la señal HITL de `_ends_turn` (10) no se surface
  como `requires_action`.
- **Seam/firma**: `SessionStateEvent(state: Literal["idle","running","requires_action"])`; el loop lo emite
  en transiciones (arranque→running; `_ends_turn`→requires_action; cierre→idle). **Orden**: tras EvR1.
  **Test**: `test_session_state_emitted_on_ends_turn`.

### EvR7 · Cabos a otro subsistema / Deuda B (referencia)
- **FIND-EVT1 / EVT5 usage** (usage no acumulado, dos Usage divergentes, sin cache-tokens) → **Deuda B
  `B-usage`** (extiende `Usage` + acumula en Session).
- **H1 compact_boundary** → depende del motor de compactación **02·LR1**; el `CompactBoundaryEvent` se
  define aquí (EvR1) y lo emite LR1.
- **J3 api_retry** → lo emite **02·LR2** (motor de recuperación de errores).
- **K5 SDKSessionInfo** → **15·storage** (listSessions).

---

## Re-visita de COMPLETITUD (gate 11 / L09) · 2ª vuelta · 2026-07-19

**Modo**: 2ª vuelta con **gate 11 de ENTRADA** — cada fila ✅/🔀 se re-verificó **abriendo el código de B
que produce el comportamiento y siguiendo el dato de punta a punta**, NO confirmando la tabla ni el nombre del
campo. **Resultado**: la tesis y la mayoría de filas **se sostienen sobre base correcta**; **1 discrepancia
real** (sobre-declaración: `turn_count` NO es slot muerto) + **1 refinamiento** (sub-crédito: el productor de
canal único ordenado `stream()` existe). **Cero cambios de estado** (los recuentos ✅5·🟡8·🔀15·❌16·⛔4 se
mantienen). **Código intacto**; tests no re-ejecutados (sin cambio de código). **Sin costuras latentes NUEVAS**
tipo `to_llm`/`timeout_seconds`/LAT-EXEC1/LAT-HOOK1 (el `Session.usage` no-alimentado NO es costura latente
B-interna sino la propia deuda A-vs-B FIND-EVT1).

**Precisión de cableado de `stream()`/`subscribe_all` (verificada leyendo el ENSAMBLADOR `factory.py`
1→EOF, L09 — no por grep)**: el ensamblador `RuntimeFactory._build_local` (factory.py:178-240) construye
`LocalAgentRuntime` inyectando model_caller/registries/dispatcher/hook_runner/storage/presentation/exec_env,
**pero NO cablea ningún consumidor de eventos**, y `RuntimeConfig` (79-117) **no tiene campo de sink/stream de
eventos**. El bus se crea per-task en `_make_bus` (runtime.py:264) y `subscribe_all(on_event)` sólo se ejecuta
**si `on_event is not None`** (runtime.py:281-282), lo que únicamente ocurre cuando un consumidor externo
invoca `stream()`/`dispatch(on_event=)`. Grep prod-vs-test lo corrobora (sólo tests los ejercitan:
`test_runtime_e2e`, `test_runtime_e2e_real_complex`, `test_root_*`, `test_loop_homologation`,
`test_events_homologation`), pero **la conclusión se apoya en el ensamblador leído íntegro**: la costura de
consumo es **genuinamente externa por diseño** (la conduce el integrador/BFF), hermana de `subscribe_all`/
`register` de hooks (06, "costura de extensión por diseño L10") y **NO** un huérfano tipo `observer/`/`modes/`.
Distinta de **FIND-EXEC1** (donde la ruta INTERNA `AgentTool→get_runner` SÍ está rota porque el factory nunca
llama `set_runner`): aquí no hay ruta interna rota — el runtime emite a un bus per-task y delega el consumo al
integrador (consistente con el canónico: el stream lo consume REPL/SDK/BFF, no el core) ⇒ 🔀 delegación por
diseño, no defecto. **Corrige mi caracterización previa "plenamente cableado y usado"**: el productor EXISTE y
es correcto, pero NO hay caller de producción interno (por diseño), y esa conclusión requería abrir el
ensamblador — no un grep (L01/L09).

### Mini-ledger de consumidores/productores abiertos (L09 — el dato seguido de punta a punta)
| Fila | Afirmación | B abierto (dato seguido) | Veredicto |
|---|---|---|---|
| A1/A2 🔀 | canal único ordenado ausente / no garantizado | `runtime.py:153-181` `stream()` = `AsyncIterator[Event]` sobre `subscribe_all`(bus.py:31-37)→queue→sentinela, orden de emisión garantizado (docstring 158-163) | **REFINADO**: productor ordenado EXISTE; falta sólo el wire `Event→SDKMessage` |
| A3/A4 ✅ | Event frozen extensible + aislamiento de handler | `protocol.py:9-11` `@dataclass(frozen=True)`; `bus.py:26-29` `subscribe(Type,…)`; `bus.py:39-45` `emit` try/except por handler | sostenido |
| B1 🟡 | thinking deltas descartados | `caller.py:210-212` sólo `text_delta`→`TokenEvent`; `caller.py:245` skip `thinking_*`; `caller.py:231` `thinking_tokens=0` | sostenido |
| B2 🔀 | atribución por task_id, no en el evento | `runtime.py:264` `_make_bus(task_id)` = un bus por task; `push_event(task_id,…)` 268/274 | sostenido |
| C1 🔀 | ToolCallEvent emitido **y** acumulado | `agent_loop.py:248` `_emit(event)` (emite ToolCall) + `274-281` acumula `tool_calls` en `ctx.messages` | sostenido |
| C2 ✅ | ToolResultEvent emitido por el loop | `agent_loop.py:312` (rama block) + `324` (dispatch normal); acumulado 319-323 | sostenido |
| C5/EVT8 🔀 | canal 2 = dicts untyped per-task | `runtime.py:267-277` `_on_tool_call`/`_on_tool_result`→`push_event` dicts `tool_start`/`tool_result` | sostenido |
| D4 ✅ | `stop_reason` `toolUse→tool_calls` | `caller.py:227` mapea, resto passthrough; consumido en loop 348 y `_on_done` runtime.py:254 | sostenido |
| E3/EVT1 ❌ | acumulación de usage ausente | `agent_loop.py:253-255` `done=event;break` — `done.usage` NUNCA leído/sumado; `run()→None` (171); `runtime.py:403-404` `complete()` recibe `session.usage.*`=0 (nunca escrito) | ❌ sostenido (usage) **pero** turn_count corregido ↓ |
| E3/EVT1 | `turn_count` "slot muerto" | `runtime.py:398` `session.turn_count = ctx.turn_count` (← `agent_loop.py:189` `+=1`) → `complete(turn_count=…)` 402 → `registry.py:148` `rec.turn_count=` | **DISCREPANCIA**: turn_count VIVO, no muerto |
| G3 🟡 | `_notify`→BackgroundNotification | `runtime.py:294-304`; gate `parent_session_id is None`(297); `final_text` puede ir `""` (386/392) | sostenido |
| K1/K2 🔀 | transcripto acumulado, no emitido | `agent_loop.py:179/199/269/275/281/289/311/319` append a `ctx.messages` | sostenido |

Las filas **❌** (D1/D2 terminal, D3, E2, E4, E5, C3, F0/EVT9 init, F1/EVT7, F2, G1, H1, I1, J3) **convergen**
(confirmación-de-doc = verificación-de-completitud, campo ausente = ausente): `event_types.py` define
**exactamente 5** tipos (Token/ToolCall/ToolResult/Done/Error), sin init/session_state/tool_progress/
compact_boundary/api_retry/result-terminal/usage-rica — confirmado por lectura directa 1→EOF. No re-hechas.

### Las 2 correcciones (código intacto)
1. **DISCREPANCIA REAL (sobre-declaración)** — E3/FIND-EVT1/tesis marcaban `Session.turn_count` como
   "slot muerto (nadie lo alimenta)" junto a `usage`. **Falso para turn_count**: está cableado de punta a
   punta (`ctx.turn_count` loop 189 → `session.turn_count` runtime 398 → `TaskRecord.turn_count` complete
   402/registry 148); `duration_ms` ídem. **Sólo `Session.usage` (tokens) es el slot muerto** — `complete()`
   recibe 0/0 siempre (runtime.py:403-404) porque nada acumula `DoneEvent.usage`. Corregido en E3, FIND-EVT1
   y tesis. El núcleo de FIND-L2 (usage=0, sin cost, `run()→None` sin `SDKResultMessage`) **SE SOSTIENE**.
2. **REFINAMIENTO (sub-crédito)** — A1/A2/GAP-EVT5 trataban `subscribe_all` como "gancho sin productor
   canónico". Abriendo B, **`LocalAgentRuntime.stream()` (runtime.py:153-181) ES el productor de canal
   único ordenado** (`AsyncIterator[Event]` con orden garantizado). Lo ausente es sólo la serialización
   `Event→SDKMessage` **wire** encima de él. Refinado A1 y GAP-EVT5 (EvR3 se cablea sobre `stream()`, no
   crea el canal). Sin voltear estado (wire serializer sigue ❌/GAP).

### Ledger de cierre (columna Lectura)
**A (canónico)** — leídos en 1ª pasada + re-audit 2026-07-12 (no re-abiertos en esta 2ª vuelta salvo anclas):
| Archivo A | LOC | Lectura |
|---|---|---|
| `entrypoints/sdk/coreSchemas.ts` | 1854 | íntegro (re-audit 2026-07-12, campo-a-campo 1256-1852; unión 24 confirmada 1854-1881) |
| `remote/sdkMessageAdapter.ts` | 303 | íntegro (re-audit; 4 exports) |
| `utils/hooks/hookEvents.ts` | 192 | íntegro (06) |
| `query.ts` / `QueryEngine.ts` | 1729/1295 | íntegro (02) — releídos con lente "qué SDKMessage emite" |

**B (runtime)** — abiertos/re-abiertos 1→EOF en ESTA 2ª vuelta (gate 11):
| Archivo B | LOC | Lectura |
|---|---|---|
| `events/protocol.py` | 22 | íntegro 1→EOF |
| `events/bus.py` | 45 | íntegro 1→EOF |
| `events/event_types.py` | 43 | íntegro 1→EOF (5 tipos + `Usage`) |
| `events/__init__.py` | 15 | íntegro 1→EOF |
| `models/caller.py` | 245 | íntegro 1→EOF (emisión Token/ToolCall/Done/Error; thinking=0; skip 245) |
| `execution/session/session.py` | 59 | íntegro 1→EOF (`Usage` i/o; `turn_count`/`usage` slots) |
| `loop/agent_loop.py` | 353 | íntegro 1→EOF (consumo stream 247-258, `done.usage` no sumado, `_emit`, ToolResult 312/324, `run()→None`) |
| `execution/local/runtime.py` | 435 | íntegro 1→EOF (`stream()` 153-181, `_make_bus`/`_wire_tts`/`_fire_stop`/`_notify`, `complete()` 400-405, `turn_count` 398) |
| `execution/tasks/registry.py` | 166 | íntegro 1→EOF (`push_event` 112, `TaskRecord` tokens/turn_count, `complete` 133-150) |
| `factory.py` | 267 | íntegro 1→EOF (ENSAMBLADOR, L09) — `_build_local` 178-240 no cablea consumidor de eventos; `RuntimeConfig` 79-117 sin campo de sink/stream ⇒ costura de consumo externa por diseño |

### §Nota de honestidad
- La **1ª pasada + re-audit 2026-07-12** de 07 fueron **line-precisas en emisión** (no superficiales como 08),
  pero en las filas ✅/🔀 de accounting **confirmaron el modelo del doc** sin seguir `session.turn_count`
  hasta `runtime.py:398` — de ahí la sobre-declaración de turn_count, destapada sólo al abrir el consumidor
  (`_run_loop`/`complete()`) en esta 2ª vuelta (gate 11). Es el modo de fallo que la L11 predice: un doc
  internamente coherente que no probó el cableado de B.
- El `stream()` estaba **sin mencionar** en el doc (grep `stream()` = 0) pese a ser el productor real del
  canal único — sub-crédito corregido.
- La unión 24 y la emisión line-a-line NO se re-verificaron contra A en esta pasada (ya íntegras en re-audit
  2026-07-12); esta 2ª vuelta se centró en **B** (gate 11), que es donde vivían las dos imprecisiones.

### Las 4 preguntas de cierre
1. ¿Se revisó **todo** cada archivo de **A**? → **Sí** (íntegros en 1ª pasada/re-audit 2026-07-12; anclas
   re-confirmadas). Esta 2ª vuelta no re-abrió A (MODO VALIDACIÓN centrado en B, gate 11).
2. ¿Se revisó **todo** cada archivo de **B**? → **Sí, 1→EOF en esta 2ª vuelta** (los 9 archivos del ledger B).
3. ¿Los hallazgos fueron **exhaustivos**? → **Sí**: cada ✅/🔀 se abrió en B y se siguió el dato; las 2
   imprecisiones (turn_count, `stream()`) salieron precisamente de no aceptar la tabla.
4. ¿Quedó **todo cubierto**? → **Sí**. Cabos con destino: FIND-EVT1/usage→**Deuda B `B-usage`**;
   `compact_boundary`→02·LR1; `api_retry`→02·LR2; `SDKSessionInfo`→15; wire serializer EvR3→18/BFF;
   `session_state`/`tool_progress`/`init` = remediación desarrollada (EvR2/5/6). Ningún pendiente de
   verificación abierto.

### VEREDICTO DE AVANCE
**✅ NADA PENDIENTE → avanzar a `08 · signals`.** 07 validada con gate 11; 2 correcciones de doc aplicadas
(código intacto, sin cambio de estado). No quedan filas ✅/🔀 sin re-verificar en B ni re-visitas diferidas.
