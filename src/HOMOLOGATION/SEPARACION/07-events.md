# 07 · events — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/07-events.md`.
> **Ciclo A1.3** del PLAN §4. Fuente: tracker `../07-events.md` (**44 filas** feature-by-feature A1–K5,
> leído íntegro 1→446; consolidadas en 9 `FIND-EVT*` + 5 `GAP-EVT*`). Esquema: `00-LEGEND.md`.
> Re-clasifica cada fila de fidelidad-de-capacidades bajo B (base↔costuras↔batteries↔integrador).
> **No es otra tabla de deuda:** es el reparto del subsistema de eventos/stream en sus destinos de construcción.

## Naturaleza de la categoría

El canónico **no tiene un bus de eventos**: tiene un **STREAM serializado** `AsyncIterable<SDKMessage>` (24 variantes)
que **ES el protocolo público** core↔consumidor (REPL / SDK / BFF-CCR). El runtime lo **parte en TRES canales**:
1. **`EventBus`** (tipado, in-proc, push): 5 eventos Token/ToolCall/ToolResult/Done/Error — observación en vivo.
2. **`registry.push_event`** (dicts sin tipar, per-task, **poll/drain** vía `rec.events`): espejo para subagentes.
3. **`ctx.messages`** (acumulación, NO emitido): el transcripto — el consumidor lo proyecta/persiste.

La homologación correcta es **del SEAM, no de la forma** (como en 06). Bajo B la categoría reparte así:
el **`Event` base + el `EventBus` + `stream()`** son **T2-BASE-MECANISMO** (+ el shape `Event`/`SDKMessage` = **T1**);
el **serializador `Event→SDKMessage` wire** es una **costura/battery del integrador** (el core sólo debe emitir puntos
suficientes); la **taxonomía de eventos core faltantes** (init, result terminal, session_state, tool_progress,
compact_boundary, api_retry) son **CORE-GAPs**; y las variantes de presentación/cuenta/transporte caen al integrador.

**Corrección de tier respecto al tracker (doble filo L10 — se aplica en este ciclo):** el tracker rotula
`FIND-EVT1`/usage → «**Deuda B `B-usage`**». Bajo el LEGEND eso es una **colisión de nombre**: el `usage` no acumulado
+ el `Usage` empobrecido es una **brecha de capacidad frente al canónico** (el canónico surface usage/cost;
el runtime no) ⇒ es **CORE-GAP** (→ DEUDA-A), **no** el tier **DEUDA-B** (higiene interna sin contraparte canónica).
El nombre de work-item `B-usage` se conserva, pero su **tier es CORE-GAP**. Lo único genuinamente **DEUDA-B** aquí es
**E4** (dos definiciones `Usage` divergentes → unificar), y su unificación apunta al shape canónico (E1).

---

## 0.1 Evidencia de origen — contrapartes canónicas y mapa de emisión/consumo *(restituido en A-CIERRE·P4″, `P4-07-2`)*

> **Por qué existe esta sección.** El tracker `../07-events.md` cita **5 archivos canónicos con LOC** y **≥9 anclas
> `.ts:línea`**; este destilado retenía **0** (patrón 3, retención 7→0). Sin ella, la columna canónica de la
> categoría desaparece del corpus y Fase B no puede volver al origen de ningún campo. Se restituye **tal como el
> tracker la acredita** (D-01: el insumo es el tracker, no una relectura del canónico).

**Contrapartes canónicas (con LOC, consumidas en fase 1):**

| archivo canónico | LOC | qué aporta |
|---|---|---|
| `sdk/coreSchemas.ts` | 1854 | la **unión de 24 variantes** `SDKMessage` (`1854-1881`) = el protocolo público; `init` (`1457-1494`); enum de error del assistant (`1256-1266`, `1352`); `SDKResultError` (`1428-1451`); `SDKRateLimitInfo` (`1305-1345`); `SDKSessionInfoSchema` (`1812-1852`); `priority` (`1280`); `ModelUsageSchema` (`17-28`) |
| `remote/sdkMessageAdapter.ts` | 303 | el adaptador wire→cliente (`convertSDKMessage`, K4) |
| `utils/hooks/hookEvents.ts` | 192 | el progreso de hooks fundido en el stream principal (I1) |
| `query.ts` | 1729 | el productor del `AsyncIterable<SDKMessage>` |
| `QueryEngine.ts` | 1295 | el motor que lo alimenta |

**Mapa de emisión/consumo del runtime (lado B, ≈128 LOC de `events/`):**
`events/protocol.py` (23) · `events/bus.py` (46) · `events/event_types.py` (44) · `events/__init__.py` (15).
**Emisores:** `models/caller.py:207-245` (traducción del stream del motor) · `loop/agent_loop.py` `_emit` **152**,
llamado en **247-258 / 312 / 324** · `execution/local/runtime.py:234-304` (`_wire_tts`, `_make_bus`, `_notify`) ·
`execution/tasks/registry.py:112` (`push_event`, canal 2).
**Consumidores/slots:** `execution/session/session.py:16,42` (`Usage`, `session.usage`).

---

## 1. Tabla por finding (44 filas A1–K5)

| ID | resumen (comportamiento observable) | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **A1** 🔀 protocolo público = stream | un canal ordenado core↔consumidor | núcleo | **T2-BASE-MECANISMO** (`stream()` productor ordenado existe) + cabo wire | módulo base `events/` + costura **wire** (GAP-EVT5) | — | mantener `EventBus`+`stream()` (verificado `runtime.py:153-181`); definir la costura serializadora `Event→SDKMessage` (battery/integrador), no el productor |
| **A2** 🔀 ordenamiento total | orden garantizado en el stream del consumidor | núcleo | **T2-BASE-MECANISMO** | módulo base `events/` | — | `stream()` garantiza orden de emisión **dentro de un canal**; el split 3-canales (push vs poll) es divergencia por-diseño para streaming de subagentes; el wire intercala. **Precisión restituida (`P4-07-10`): el orden RELATIVO entre `push_event` (canal 2, poll sobre `rec.events`) y `emit`/`stream()` (canal 1) NO está garantizado** — el canónico sí garantiza orden total sobre el stream único. Quien reconstruya el stream (OI-EVT-2) debe imponer el orden, no asumirlo |
| **A3** ✅ `Event` frozen extensible | tipos propios sin tocar el runtime | núcleo | **T1-CONTRATO** (`Event` base) + **T2-BASE-MECANISMO** (`subscribe`) | paquete contratos (`Event`) + módulo base `bus.py` | — | extraer `Event` frozen a contratos; el bus vive en base (mejora de extensibilidad in-proc vs unión Zod cerrada) |
| **A4** ✅ aislamiento de error de handler | un handler que lanza no rompe el stream | núcleo | **T2-BASE-MECANISMO** | módulo base `bus.py` (`emit` try/except 39-45) | — | conservar el patrón captura+log por handler |
| **B1** 🟡 stream_event deltas crudos | thinking deltas + índices de bloque preservados; **`message_start`, `content_block_start`/`content_block_stop`, y las `signatures` de los bloques thinking** | núcleo | **T1-CONTRATO** (evento) + **CORE-GAP** | paquete contratos (`ThinkingEvent`/`TokenEvent.kind`) + costura motor | — | **CORE-GAP**: `caller.py:245` descarta `thinking_*`; `thinking_tokens=0` hardcode (231). Preservar thinking como evento propio (necesario para `thinking_tokens`). **Restituido (`P4-07-8`):** el canónico reenvía el **raw stream event** completo — no sólo los deltas de texto: `message_start` (cabecera del mensaje), `content_block_start`/`content_block_stop` (los **índices de bloque**, sin los cuales un consumidor no puede reensamblar bloques concurrentes) y las **`signatures`** de los bloques de thinking (necesarias para re-enviar thinking firmado al proveedor en el turno siguiente). El `TokenEvent(text)` del runtime aplana los tres |
| **B2** ❌ `parent_tool_use_id` por partial | atribución explícita del partial a su subagente **en el propio evento** | núcleo | **CORE-GAP condicionado** (= K4/GAP-EVT5) + T2-BASE-MECANISMO (el bus per-task existe) | módulo base (`_make_bus(task_id)` per-task) + costura **wire** | eje **ejecución** (bus per-task) | **Inversión de veredicto en A-CIERRE·P4″ (`I1`): era 🔀 «divergencia por-diseño».** La atribución implícita por bus per-task (verificado `runtime.py:264`) **sólo funciona in-proc**: en cuanto los eventos se serializan a un canal único (OI-EVT-2 / `to_sdk_message`), la identidad del bus se pierde y **no hay campo que reconstruya la atribución**. Es el mismo condicionamiento que K4/GAP-EVT5: mientras el wire no exista es latente; en cuanto exista es una **capacidad ausente**, no una divergencia. **Acción:** el `Event` base lleva `parent_tool_use_id`/`task_id` poblado desde `_make_bus(task_id)` — **no un envelope**: `EventBus.emit` despacha por `type(event)` (`bus.py:40`) y envolver colapsaría el despacho tipado (forma fijada en `DEUDA-A §1.1·K4`, corregida en A-CIERRE·P0). ⚠ **`DEUDA-A §1.1·K4` YA registraba esta inversión** —«objeción formal registrada por 17, que este rollup ADOPTA: `07·B2` cerró `parent_tool_use_id` como 🔀 argumentando atribución implícita»— y la cerraba como **CORE-GAP condicionado**. La corrección se adoptó aguas arriba y **nunca bajó a este documento**: `I1` es la propagación que faltaba, no un hallazgo nuevo. Liga C3 (`task_id` en `ToolProgressEvent`) y G4 |
| **B3** 🔀 `session_id`/`uuid` por mensaje | correlación del wire | núcleo | **T1-CONTRATO** (campo wire) | cabo → costura **wire** (GAP-EVT5) | eje **ejecución** (id opaco) | metadatos de correlación que añade el serializador; el bus ya está scoped in-proc |
| **C1** 🔀 tool_use dual (evento + mensaje) | observar Y persistir el tool_call | núcleo | **T1-CONTRATO** (`ToolCallEvent`) + **T2-BASE-MECANISMO** | paquete contratos + módulo base loop | — | dualidad correcta: `_emit` (observa) + acumula en `ctx.messages` (`agent_loop.py:248/274-281`) |
| **C2** ✅ tool_result | resultado emitido y acumulado | núcleo | **T1-CONTRATO** (`ToolResultEvent`) + **T2-BASE-MECANISMO** | paquete contratos + módulo base loop | — | emitido por el loop tras dispatch (312/324) + acumulado (319-323) |
| **C3** ❌ **FIND-EVT6** tool_progress | heartbeat de tools largas (`tool_use_id`, **`task_id`**, `elapsed`/`elapsed_ms`, salida parcial) | núcleo | **T1-CONTRATO** (`ToolProgressEvent`) + **T2-COSTURA** (`on_progress`) + **CORE-GAP** | paquete contratos + costura **`on_progress`** + battery Bash (→10) | — | **CORE-GAP** (EvR5): el dispatcher/tool emite `ToolProgressEvent` para tools que excedan umbral; requiere `run_shell` generador/callback. **Restituido (`P4-07-9`):** el evento lleva **`task_id` además de `tool_use_id`** (una tool larga puede correr dentro de un subagente: sin `task_id` el progreso no es atribuible — liga B2) y se emite con **cadencia periódica mientras la tool siga viva**, no una sola vez al cruzar el umbral (es un *heartbeat*: su ausencia sostenida es la señal de cuelgue) |
| **C4** 🔀 tool_use_summary ("Read 2 files…") | resumen acumulado de salida | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (capa de interfaz) | — | streamlining de salida (UX) → presentación del integrador, no core |
| **C5** 🔀 **FIND-EVT8** `push_event` dicts | espejo untyped tool_start/result per-task | núcleo | **T2-BASE-MECANISMO** (canal 2 poll) | módulo base `execution/tasks` (buffer `rec.events`) | eje **ejecución** (per-task) | canal 2 por-diseño para streaming de subagentes (verificado `runtime.py:267-277`); enriquecer con agregados = G2 |
| **D1** ❌ **FIND-EVT1/GAP-EVT2** result success | `SDKResultMessage`: result/num_turns/**duration_ms**/**duration_api_ms**/cost/usage/modelUsage/denials/structured_output/stop_reason | núcleo | **T1-CONTRATO** (`ResultEvent`) + **T2-BASE-MECANISMO** (loop emite al cierre) + **CORE-GAP** | paquete contratos (`ResultEvent`) + módulo base loop | — | **CORE-GAP** (EvR4): `DoneEvent` es per-turno; `run()→None`. Emitir `ResultEvent` terminal agregando lo acumulado. Depende de usage (E). **Restituido (`P4-07-6`):** el result terminal lleva **dos relojes distintos** — `duration_ms` (pared, turno completo) y `duration_api_ms` (sólo tiempo en el proveedor). Su diferencia **es** el coste de las tools + el overhead del loop, y es la única métrica del corpus que permite atribuir latencia a herramientas vs modelo; el runtime no mide ninguno de los dos |
| **D2** 🟡 **FIND-EVT4** result error | `subtype ∈ {error_during_execution, error_max_turns, error_max_budget_usd, error_max_structured_output_retries}` + errors[]/usage | núcleo | **T1-CONTRATO** (`ResultEvent` error) + **CORE-GAP** | paquete contratos + módulo base loop | — | **CORE-GAP**: observación en vivo homologada (`ErrorEvent` al bus, `agent_loop.py:248`); falta el **resultado terminal** de error con subtype+accounting completo (el `SDKResultError` lleva usage/modelUsage/cost/denials). `error_max_turns`→05·FIND-EXEC5; `max_budget`→accounting. **Restituido (`P4-07-7`):** el runtime **sí tiene un límite de 50 turnos**, pero `agent_loop.py:352` **sólo emite un warning y sigue** — no corta el turno ni produce un terminal `error_max_turns`; y como no lleva `num_turns` en ningún resultado, el consumidor no puede ni detectar la condición a posteriori. No es «límite ausente»: es **límite sin efecto ni reporte** |
| **D3** ❌ isSessionEndMessage | señal de fin de sesión (`type==='result'`) | núcleo | **CORE-GAP** (subsumido por D1) | módulo base loop (`ResultEvent` = marca de fin) | — | el `ResultEvent` terminal (D1) ES la señal de fin de sesión; la remediación de D3 se pliega en D1 |
| **D4** ✅ stop_reason mapeado | `toolUse→tool_calls`, resto passthrough | núcleo | **T1-MOTOR** | costura **motor** (`caller.py:227`) | — | mapeo al nivel del caller (verificado `caller.py:227`); equivalente al stop_reason del result |
| **D5** 🟡 error assistant enum (7 valores) | `authentication_failed/billing_error/rate_limit/invalid_request/server_error/unknown/max_output_tokens` inline | núcleo | **T1-CONTRATO** (`ErrorEvent.code`) + **T1-MOTOR** (caller mapea) + **CORE-GAP** | paquete contratos (`ErrorEvent.code`) + costura motor | — | **CORE-GAP** (EvR4): `ErrorEvent(message:str)` aplana; un consumidor no distingue `rate_limit` (reintentable, liga J3) de `billing_error` (fatal). `ErrorEvent` gana `code` = enum; el caller lo mapea. **Restituido (`P4-07-5`):** la taxonomía canónica es de **dos niveles y no debe aplanarse a uno** — (i) el enum de **error del assistant** (`coreSchemas.ts:1256-1266`, 7 valores, error *dentro* de un turno que sigue vivo) y (ii) el **`subtype` del `SDKResultError`** (`1428-1451`, 4 valores, terminación del turno, ver D2). Un mismo incidente puede producir uno, el otro o ambos. Además **`max_output_tokens` NO es un fallo**: es terminación limpia por tope de salida, y colapsarlo con `server_error` hace que un consumidor reintente lo que debía continuar |
| **E1** 🟡 **FIND-EVT5** ModelUsage rico | input/output/**cacheRead/cacheCreation/webSearch/costUSD/contextWindow/maxOutput** | núcleo | **T1-CONTRATO** (`Usage`=ModelUsage) + **T1-MOTOR** (caller puebla) + **CORE-GAP** | paquete contratos (`Usage` unificado) + costura motor | — | **CORE-GAP**: faltan cache-tokens (coste real con prompt-cache), webSearch, costUSD, contextWindow, maxOutput; `thinking` hardcode 0. costUSD requiere tarifa/modelo →16. **Restituido (`P4-07-12`·E1):** `cacheRead`/`cacheCreation` no son dos contadores más — el **prompt-cache invierte la aritmética del coste** (leer de caché vale una fracción de `input`, crearla vale más), de modo que sin ellos `costUSD` no es aproximable a partir de `input`+`output`: es **incalculable**, no impreciso |
| **E2** ❌ **FIND-EVT1** usage agregado + modelUsage | agregado por-sesión + breakdown por-modelo | núcleo | **T2-BASE-MECANISMO** (acumula) + **T1-CONTRATO** (`ResultEvent.usage`) + **CORE-GAP** | módulo base (acumulación) + paquete contratos | eje **persistencia** (usage de sesión) | **CORE-GAP**: `DoneEvent.usage` per-turno, **no acumulado**; sin agregado por-sesión ni por-modelo |
| **E3** ❌ **FIND-L2 físico** acumulación→Session.usage | sumar `done.usage` en `Session.usage` al consumir DoneEvent | núcleo | **T2-BASE-MECANISMO** (cablear la suma) + **CORE-GAP** (+ faceta DEUDA-B: slot muerto) | módulo base loop/runtime (cablear) | eje **persistencia** (`Session.usage`) | **CORE-GAP `B-usage`** (NO tier DEUDA-B, ver §nota): slot existe (`session.py:42`) y dato existe (`DoneEvent.usage`) pero **falta el cable** — `agent_loop.py:253-255` `done;break` sin leer usage; `complete()` recibe 0/0 (`runtime.py:403-404`). **`turn_count` SÍ cableado** (398, verificado) — no muerto |
| **E4** ❌ **FIND-EVT5** dos `Usage` divergentes | `events/Usage(i,o,thinking)` ≠ `session/Usage(i,o)` | núcleo | **DEUDA-B** (higiene) | borrar/unificar → un `Usage` canónico (=E1) | — | **DEUDA-B interna** (L10): definiciones incompatibles en dos módulos; ninguna con cache/cost. Unificar en el `Usage`=ModelUsage de E1 |
| **E5** ❌ total_cost_usd | coste $ agregado | núcleo | **CORE-GAP** | paquete contratos (`ResultEvent.total_cost_usd`) + →16 (tarifa) | — | **CORE-GAP**: bloquea G2 maxBudgetUsd (05) y coste/modelo (16). Requiere E1(costUSD) que requiere tarifa/modelo (16) |
| **F0** ❌ **FIND-EVT9** init handshake | `SDKSystemMessage init` (`coreSchemas.ts:1457-1494`, **14 campos**): agents/tools/**mcp_servers[]{name,status}**/model/permissionMode/skills/slash_commands/plugins/output_style/**apiKeySource**/**betas**/**claude_code_version**/**cwd**/**fast_mode_state** | núcleo | **T1-CONTRATO** (`InitEvent`) + **T2-BASE-MECANISMO** (loop emite) + **CORE-GAP** | paquete contratos (`InitEvent`) + módulo base loop | eje **persistencia** (bootstrap de vista de sesión) | **CORE-GAP** (EvR2): PRIMER frame del stream que anuncia capacidades; el runtime no lo emite (info dispersa en `ToolUseContext`/`AppState`/factory). El **BFF de agentic_assistant** lo necesita para bootstrapear la vista. Liga 18 (factory) + GAP-02 (permissionMode). **Restituido (`P4-07-3`):** el destilado listaba 8 de los 14 campos. Los 6 omitidos no son decorativos: **`mcp_servers[]` es una lista de objetos `{name, status}`** —no de nombres— y ese `status` (connected/failed/pending) es **el único punto del protocolo donde un consumidor se entera de que un servidor MCP no levantó**; `apiKeySource` y `betas` determinan qué capacidades están activas en la sesión; `claude_code_version` es el discriminante de compatibilidad del wire; `cwd` ancla las rutas relativas de todo el transcripto; `fast_mode_state` viaja en el mismo frame (su UX es del integrador, F2, pero **el campo es del handshake**) |
| **F1** ❌ **FIND-EVT7** session_state_changed | `idle`/`running`/**`requires_action`** (señal autoritativa de turn-over) | núcleo | **T1-CONTRATO** (`SessionStateEvent`) + **T2-BASE-MECANISMO** (loop emite) + **CORE-GAP** | paquete contratos + módulo base loop | — | **CORE-GAP** (EvR6): el loop infiere fin por `stop_reason` (`agent_loop.py:348`) pero no emite estado. `requires_action` = la señal HITL de `_ends_turn` (02) → desbloquea observabilidad HITL |
| **F2** ❌ status transitorio | `SDKStatusMessage`: `status ∈ {compacting, null}`, permissionMode | núcleo | **CORE-GAP** (status) + **CLI-ONLY** (fast_mode_state) | paquete contratos (`StatusEvent`) + integrador (fast_mode UX) | — | **CORE-GAP** parcial: sin eventos de estado transitorio; liga compactación (I/H1) y permissionMode (GAP-02). `fast_mode_state` (off/cooldown/on) = UX de sesión → integrador |
| **F3** 🔀 post_turn_summary | resumen background por turno (status_category, needs_action, artifact_urls) | núcleo | **BATTERY** (background-agents) | battery **background-agents** → 05/13 | — | feature de agentes background/coordinator; no gap del core del bus |
| **F4** ⛔ prompt_suggestion | predicción del siguiente prompt | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (capa de interfaz) | — | UX; no se descarta — capa de interfaz del integrador (agentic_code terminal) |
| **G1** ❌ task_started | task_id/tool_use_id/description/task_type/**workflow_name**/prompt | núcleo | **T1-CONTRATO** (`TaskStartedEvent`) + **T2-BASE-MECANISMO** (registry/runtime emite) + **CORE-GAP** | paquete contratos + módulo base `execution/tasks` (→05) | eje **ejecución** (task) | **CORE-GAP**: el registry bufferiza tool_start/result pero no un evento de inicio de task. `workflow_name` sólo si `task_type==='local_workflow'` (workflows) = ⛔ fuera de alcance salvo adopción |
| **G2** 🟡 **FIND-EVT8** task_progress | usage{total_tokens,tool_uses,duration_ms}, last_tool_name, summary | núcleo | **T2-BASE-MECANISMO** (registry agrega) + **CORE-GAP** | módulo base `execution/tasks` + →E (accounting) | eje **ejecución** (task) | **CORE-GAP** parcial: hay tool_start/result por task sin agregados; depende de E (usage) |
| **G3** 🟡 task_notification | status completed/failed/stopped, **output_file**, summary, usage | núcleo | **T2-BASE-MECANISMO** (`_notify`) + **CORE-GAP** parcial | módulo base runtime (`_notify`) + →05 | eje **persistencia** (parent_session_id) | **CORE-GAP** parcial: `_notify`→`BackgroundNotification` (`runtime.py:294`) es la contraparte real; falta `output_file`/`usage`; gate `parent_session_id is None` (297); `final_text` puede ir `""` (05·FIND-EXEC3). **Restituido (`P4-07-11`):** liga **`05·GAP-EXEC1`** — la notificación **no está deduplicada**, de modo que un mismo `task_id` puede notificar más de una vez (retry/re-entrada) y el consumidor recibe estados terminales repetidos. La deduplicación pertenece a 05; se anota aquí porque el síntoma es observable **en este evento** |
| **G4** 🔀 task_* en el mismo stream | intercalado por `parent_tool_use_id` | núcleo | **T2-BASE-MECANISMO** (divergencia por-diseño) | módulo base + cabo wire | eje **ejecución** | el canónico intercala task_* en el stream principal; el runtime los aísla en `rec.events` (poll); el wire los intercala |
| **H1** ❌ **GAP-EVT3** compact_boundary | trigger manual/auto, pre_tokens, preserved_segment{head/anchor/tail_uuid} | núcleo | **T1-CONTRATO** (`CompactBoundaryEvent`) + **BATTERY compaction** + **CORE-GAP** | paquete contratos (evento, def. aquí) + battery **compaction** (motor→02·LR1) | eje **persistencia** (frontera de compactación) | **CORE-GAP**: depende de la compactación no portada (02 motor #1); sin el evento no hay marca de frontera para resume/re-surface de memoria (13) |
| **I1** ❌ **GAP-EVT4** progreso de hooks | `hook_started/progress/response` (hook_id, hook_name, hook_event, stdout/stderr, **output**, outcome) | núcleo | **T1-CONTRATO** (`Hook*Event`) + **T2-COSTURA** (HookRunner→EventBus) + **CORE-GAP** | paquete contratos + costura **hook-sink** (→06) | — | **CORE-GAP**: el canónico funde el progreso de hooks en el stream principal; el runtime tiene bus separado ⛔ (06·FIND-HOOK). `HookRunner` debe emitir al `EventBus`. Reconciliar con 06. **Restituido (`P4-07-12`·I1):** el evento lleva **`output` además de `stdout`/`stderr`** (`utils/hooks/hookEvents.ts`) — es el **resultado estructurado** que el hook devuelve al motor (el que puede bloquear/reescribir la acción), no la traza cruda; sin él, el consumidor ve la salida del hook pero no su **decisión** |
| **J1** 🔀 rate_limit_event | `SDKRateLimitInfo` rico (`coreSchemas.ts:1305-1345`): **`status ∈ {allowed, warning, rejected}`** · `resetsAt` · `utilization` · `overageStatus` · `overageResetsAt` · `surpassedThreshold` · ventanas `five_hour`/`seven_day`/**`seven_day_opus`**/**`seven_day_sonnet`** · `overage` ×12 reasons · `isUsingOverage` | núcleo (transporte) | **T3-INTEGRADOR** (cuenta) + cabo motor | integrador (cuenta/suscripción) + →16/18 | — | concern de transporte/cuenta (suscripción claude.ai + overage); el bus podría transportarlo si el caller lo emitiera → 16/18. **Restituido (`P4-07-4`):** el destilado había comprimido el shape a «rico (…)» y con ello **desapareció `status`, el único campo con semántica de control** (`rejected` = corta el turno; `warning` = avisa; `allowed` = sigue) junto con `resetsAt`/`overageResetsAt` (cuándo reintentar), `utilization`/`surpassedThreshold` (cuánto queda) y las ventanas **por modelo** (`seven_day_opus`/`seven_day_sonnet`, que son cuotas independientes). ⚠ El criterio de aceptación de **OI-EVT-4** (§2.5) cita `rejected` — es decir, **el corpus dependía de un valor que este documento había dejado de definir** |
| **J2** 🔀 auth_status | isAuthenticating, output, error | núcleo (transporte) | **T3-INTEGRADOR** | integrador (auth de sesión) → 18 | eje **persistencia** (auth) | auth de sesión → 18/integrador |
| **J3** ❌ api_retry | attempt, max_retries, retry_delay_ms, error_status, **error** | núcleo | **T1-CONTRATO** (`ApiRetryEvent`) + **CORE-GAP** | paquete contratos (evento, def. aquí) + motor recuperación →02·LR2 | — | **CORE-GAP**: liga 02 motor #2 (recuperación de errores del modelo, no portado); el caller no reintenta ni emite reintentos. **Restituido (`P4-07-12`·J3):** el evento lleva **`error` además de `error_status`** — el status HTTP dice *que* falló, el `error` dice *qué* falló (mensaje/tipo del proveedor), y es el que decide si el reintento tiene sentido (`overloaded` sí, `invalid_request` no) |
| **J4** 🔀 files_persisted | files/failed/processed_at | núcleo | **BATTERY memory/artifacts** | battery → 13 | eje **persistencia** (artefactos) | artefactos → 13 |
| **J5** 🔀 elicitation_complete | mcp_server_name, elicitation_id | núcleo | **BATTERY mcp** | battery → 11 | — | MCP → 11 |
| **J6** ⛔ local_command_output | salida de slash command | cáscara-CLI | **CLI-ONLY / INTERFAZ** + **BATTERY commands** | integrador (terminal) + battery commands (12) | — | slash commands de terminal/UX → capa de interfaz del integrador + battery commands (12) |
| **K1** 🔀 assistant message en stream | message, parent_tool_use_id, error, uuid | núcleo | **T1-CONTRATO** (shape=01) + **T2-BASE-MECANISMO** (acumula, no emite) | paquete contratos (message, →01) + módulo base | eje **persistencia** (transcripto) | el canónico serializa el transcripto EN el stream; el runtime lo **acumula** en `ctx.messages` (verificado) y delega proyección/persistencia (01/03/15). Correcto: separar estado de observación |
| **K2** 🔀 user message | +Replay/isReplay, isSynthetic, tool_use_result, **priority [now/next/later]**, timestamp | núcleo | **T1-CONTRATO** (shape=01) + cabos | paquete contratos + →05 (priority) + →15 (isReplay) | eje **persistencia** (transcripto/resume) | `priority` liga **05·FIND-EXEC12** (pendingMessages/SendMessage-a-vivo) + **FIND-SIG13** (dos niveles de abort); `isReplay`→15; `isSynthetic`/`tool_use_result` = inyección de resultados de tool |
| **K3** ⛔ streamlined_text/summary | streamlining de salida | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (capa de interfaz) | — | UX de salida → capa de interfaz del integrador |
| **K4** ⛔ convertSDKMessage | adaptador wire→Message del REPL (+isSessionEndMessage/isSuccessResult/getResultText) | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (consumidor de `subscribe_all`) | — | capa de presentación del cliente CCR: es el **CONSUMIDOR espejo** del productor wire que falta (GAP-EVT5). El integrador (BFF/REPL) lo implementa |
| **K5** 🔀 SDKSessionInfoSchema | listSessions/getSessionInfo (`coreSchemas.ts:1812-1852`): sessionId/summary/lastModified/customTitle/firstPrompt/gitBranch/cwd/tag/createdAt/**fileSize** | núcleo | **T2-COSTURA / BATTERY storage** | costura/battery **storage-index** → 15 + entrypoint BFF | eje **persistencia** (índice de sesiones) · patrón id opaco+repo | NO es variante del stream: índice/metadata de sesiones persistidas → concern de **15·storage** (índice sobre FS/MinIO) + listado del BFF. **Restituido (`P4-07-12`·K5):** el índice lleva **`fileSize`** — el listado debe poder ordenar/podar sin abrir cada transcripto, y es el campo que hace del índice un índice y no un directorio |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`Event` base + `EventBus`** (T1-CONTRATO + T2-BASE-MECANISMO) — productor: caller/loop/runtime (`emit`) · consumidor: `subscribe(Type,…)`/`subscribe_all` (base default + integrador). El `Event` frozen va a contratos; el bus al base.
- **`stream()` productor de canal único ordenado** (T2-BASE-MECANISMO) — productor: `LocalAgentRuntime.stream()` (`runtime.py:153-181`, verificado) · consumidor: integrador/BFF vía `async for`. **YA existe**; no se re-construye.
- **wire serializer `Event→SDKMessage`** (T2-COSTURA / battery `wire`, **GAP-EVT5**, hoy ausente) — productor: integrador que hace `subscribe_all(serializer)` (verificado que el factory NO lo cablea, `factory.py:178-240`) · consumidor: BFF por SSE / REPL. Produce también `init` (F0) y `result` terminal (D1). **Costura de consumo externa por diseño** (hermana de `register` de hooks 06, L10) — NO huérfano DEUDA-B.
- **model-caller (traducción de stream)** (T1-MOTOR) — productor: `agentic_models` (stream del provider) · consumidor: `caller.py:207-245` (verificado) → `Token/ToolCall/Done/Error`. Aquí se puebla `Usage` completo + `stop_reason` + `ErrorEvent.code`.
- **`on_progress` (tool progress)** (T2-COSTURA, C3/EVT6, ausente) — productor: dispatcher/tool durante la ejecución · consumidor: `EventBus` (`ToolProgressEvent`). Requiere `run_shell` generador/callback (→10·Bash).
- **hook-sink a EventBus** (T2-COSTURA, I1/GAP-EVT4, ausente) — productor: `HookRunner` · consumidor: `EventBus` (`Hook*Event`). Reconciliar con 06.
- **cable de usage-accounting** (T2-BASE-MECANISMO, E2/E3, ausente) — productor: el loop al consumir `DoneEvent` · consumidor: `Session.usage` (acumula). Hoy roto (`agent_loop.py:253-255` no lee `done.usage`). ⚠ **Sin número S en `SEAMS.md`** (sonda c24, A-CIERRE·P4″): las otras 6 costuras de esta lista tienen entrada en el índice de 29 (`Event`/`EventBus`→S5, `stream()`→S5, wire→S6, motor→S9, `on_progress`→S7, hook-sink→S8); ésta **no**, pese a que 07 **sí** fue documento de origen del rollup. Registrado como pendiente fuera del par (`I2`).

### 2.2 Batteries que alimenta (nombre · alcance)
- **wire** — serializador `Event→SDKMessage` (24 variantes) + `SessionInfo` (K5) sobre `stream()`/`subscribe_all`. OPCIONAL: sólo para consumo remoto/BFF-CCR. Produce init/result/session_state al wire. El core no lo conoce.
- **compaction** — emite `CompactBoundaryEvent` (H1); el **motor** (trigger/preserved_segment) nace en 02·LR1. El evento se **define aquí** (EvR1·a).
- **background-agents** — post_turn_summary (F3) → 05/13.
- **commands** — local_command_output (J6) → 12.

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`) — **20** *(eran 19; +B2 en A-CIERRE·P4″)*

> ⚠ **Recuento corregido.** `DEUDA-A §0.2` registra `| 07·events | 19 | …B1·C3·D1/D2/D3/D5·E1/E2/E3/E5·F0/F1/F2·G1/G2/G3·H1·I1·J3 |`
> — copiado de la versión previa de esta lista. Con la inversión `I1` de B2 la cifra correcta es **20** y la lista
> gana `B2`. `DEUDA-A` debe actualizarse (pendiente fuera del par).

- **B1** — thinking deltas descartados + `thinking_tokens=0` hardcode (caller.py:245/231); además `message_start`/`content_block_start|stop`/`signatures` aplanados.
- **B2** *(nuevo, inversión `I1`)* — sin `parent_tool_use_id`/`task_id` **en el evento**: la atribución por bus per-task no sobrevive a la serialización a canal único. **CORE-GAP condicionado** al wire (= K4/GAP-EVT5).
- **C3 / EVT6** — `tool_progress` inexistente (heartbeat de tools largas).
- **D1 / EVT1 / GAP-EVT2** — sin `ResultEvent` terminal success (num_turns/cost/usage/denials/structured_output); `run()→None`.
- **D2 / EVT4** — sin resultado terminal de error (subtype+accounting completo); `error_max_turns` inexistente (→05·FIND-EXEC5).
- **D3** — sin señal de fin de sesión (se pliega en D1: `ResultEvent`=fin).
- **D5** — `ErrorEvent` sin `code` tipado (7 valores); un consumidor no distingue reintentable de fatal.
- **E1 / EVT5** — `Usage` empobrecido (sin cache/webSearch/costUSD/contextWindow/maxOutput; thinking=0).
- **E2 / EVT1** — usage no acumulado; sin agregado por-sesión ni por-modelo.
- **E3 / FIND-L2** — el **cable** de acumulación (`done.usage`→`Session.usage`) falta; `complete()` recibe 0/0 (runtime.py:403-404). **Tier CORE-GAP `B-usage`** (con faceta DEUDA-B del slot muerto). `turn_count` SÍ cableado (398).
- **E5** — `total_cost_usd` ausente (bloquea 05·maxBudget + 16·coste/modelo).
- **F0 / EVT9** — sin `InitEvent` handshake (frame de apertura del stream).
- **F1 / EVT7** — sin `SessionStateEvent` (idle/running/requires_action); la señal HITL de `_ends_turn` no se surface.
- **F2** — sin `StatusEvent` transitorio (compacting).
- **G1** — sin `TaskStartedEvent`.
- **G2 / EVT8** — `task_progress` sin agregados de usage/tool_uses/duration/last_tool/summary (depende de E).
- **G3** — `task_notification` sin `output_file`/`usage`; `final_text` puede ir vacío (→05·FIND-EXEC3).
- **H1 / GAP-EVT3** — `compact_boundary` (evento aquí; motor→02·LR1).
- **I1 / GAP-EVT4** — progreso de hooks no fundido en el stream (→06).
- **J3** — `api_retry` (evento aquí; motor de recuperación→02·LR2).

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10)
- **E4** — dos `Usage` divergentes (`events/Usage(i,o,thinking)` ≠ `session/Usage(i,o)`) → unificar en un `Usage`=ModelUsage (target = shape de E1). Higiene, pero la unificación apunta al shape canónico.
- **E3 (faceta)** — el slot `session.usage` cableado a medias (nadie lo escribe) → se completa al cablear el CORE-GAP de E2/E3; la faceta de "seam a medias" es DEUDA-B, la capacidad ausente es CORE-GAP.

> **Aclaración de doble filo (L10):** el tracker rotuló `FIND-EVT1`/usage → «Deuda B `B-usage`». Bajo el LEGEND
> ese work-item es **CORE-GAP** (brecha de capacidad vs canónico), NO el **tier DEUDA-B**. Sólo **E4** (unificar dos
> `Usage`) es tier DEUDA-B puro. Se conserva el nombre `B-usage` pero con tier corregido a CORE-GAP.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05; vertido formal en A1.7)
Con **capacidad observable · origen (costura del base) · firma que consume · cableado en el integrador · orden · criterio de aceptación**.

**Eje PRIMARIO — CONTRATO BASE COMÚN (must-be de TODO integrador agéntico):**

- **OI-EVT-1 · Consumir el stream ordenado** *(contrato base común)* — **capacidad:** todo integrador consume los eventos del turno; el core delega la consumición (verificado: `factory.py:178-240` no cablea consumidor; `subscribe_all` sólo corre si el integrador pasa `on_event`). **origen:** A1/A2 (`stream()`/`subscribe_all`). **firma:** `async for ev in runtime.stream(task)` **o** `dispatch(on_event=sink)`. **cableado:** el integrador provee el sink/iterador. **orden:** prerrequisito de toda observación/UI. **aceptación:** un turno emite Token/ToolCall/ToolResult/Done en orden al consumidor sin pérdida.
- **OI-EVT-2 · Serializar `Event→SDKMessage` (wire)** *(contrato base común, para transporte remoto/UI)* — **capacidad:** todo integrador con transporte fuera-de-proceso (BFF-SSE / REPL) traduce los eventos tipados al wire de 24 variantes. **origen:** GAP-EVT5 (costura wire) + K4 (convertSDKMessage = el consumidor espejo). **firma:** `to_sdk_message(event: Event) -> dict` suscrito a `subscribe_all`; produce también `init`/`result`/`session_state`. **cableado:** el integrador suscribe el serializador y emite por su transporte. **orden:** tras que el core emita los puntos suficientes (EvR1/2/4/6). **aceptación:** un cliente remoto reconstruye el stream (init→…→result) desde el wire.
- **OI-EVT-3 · Bootstrapear la vista de sesión desde el `init`** *(contrato base común)* — **capacidad:** el integrador presenta capacidades de la sesión (tools/model/mcp/skills/slash_commands/permissionMode). **origen:** F0/EVT9 (`InitEvent`). **firma:** consume `InitEvent` (emitido por el loop desde el contexto ensamblado). **cableado:** el integrador renderiza/expone el handshake. **orden:** primer frame del stream. **aceptación:** la vista de sesión se puebla del `init`, no de lectura directa de `ToolUseContext`.
- **OI-EVT-4 · Capa de cuenta (rate-limit / auth / overage)** *(contrato base común, realización específica)* — **capacidad:** el integrador gestiona cuota/auth/overage. **origen:** J1/J2 (T3). **firma:** consume `rate_limit`/`auth_status` (si el caller los emite) → 16/18. **cableado:** el integrador atribuye a la cuenta. **orden:** ortogonal al turno. **aceptación:** un `rejected` de rate-limit corta el turno con mensaje de cuota.

**Realización específica por integrador (capa secundaria):**

- **agentic_code (terminal):** realiza OI-EVT-1/2 como **render a terminal** (K4 convertSDKMessage→REPL); implementa la capa de interfaz de **C4** (tool_use_summary), **F4** (prompt_suggestion), **J6** (local_command_output), **K3** (streamlined_text) — CLI-ONLY, por completitud de capacidad, no forma verbatim.
- **agentic_assistant (BFF + front):** realiza OI-EVT-2 como **serializador SSE** multi-tenant; consume el `init` (OI-EVT-3) para bootstrapear la **vista de sesión** del front; provee el **índice de sesiones** (K5·SDKSessionInfo → 15·storage) para `listSessions` del BFF; atribuye cuenta/overage (OI-EVT-4). *(nota-identidad: la sesión se identifica por id opaco + repo; el índice K5 es metadata que el integrador define — patrón repo genérico.)*

### 2.6 Plan de remediación del BASE — EvR1…EvR7 *(restituido en A-CIERRE·P4″, `P4-07-1`)*

> **Por qué existe esta sección.** El destilado citaba «(EvR2)», «(EvR4)», «(EvR5)», «(EvR6)» como punteros a un plan
> que **no había traído consigo**: las firmas, el cableado y las pruebas del tracker se habían perdido. La asimetría
> era además del tipo que L05 prohíbe **al revés de lo habitual**: la cara **integrador** tenía sus 6 campos
> desarrollados (§2.5, cuatro OI-EVT) y la cara **base** —20 CORE-GAPs— no tenía ninguno. Se restituye con los
> mismos 6 campos: **comportamiento · seam · firma · cableado · orden · prueba.**

- **EvR1 · taxonomía 5 → 24: los CINCO tipos core** *(rótulo corregido en `P4-07-13`; ver la nota de numeración)* —
  **comportamiento:** el bus expone 5 tipos (Token/ToolCall/ToolResult/Done/Error) frente a las 24 variantes del
  stream canónico; el tracker (`../07-events.md:276-281`) fija los **cinco** que un consumidor remoto necesita y que
  el base debe definir: **`InitEvent`** (→ EvR2) · **`CompactBoundaryEvent`** (→ EvR1·a) · **`ApiRetryEvent`**
  (→ EvR1·b) · **`ToolProgressEvent`** (→ EvR5) · **`SessionStateEvent`** (→ EvR6). El resto de variantes
  (terminal/UX) son ⛔. **seam:** paquete de contratos — todos son `@dataclass(frozen=True)` subtipos de `Event` en
  `event_types.py`, que hoy define **exactamente 5** (verificado 1→EOF). **orden: PRIMERO de todo el plan** — los
  demás ítems los *emiten*, así que ninguno puede cablearse antes de que el tipo exista. **prueba:**
  `test_event_taxonomy_covers_core`.

- **EvR1·b · `ApiRetryEvent` (J3)** *(**restituido en `P4-07-13`**: es el único de los cinco tipos core que se quedó
  **sin ficha** al colapsar EvR1 en un solo evento; la fila J3 lo marcaba ❌ y el plan del base no lo remediaba)* —
  **comportamiento:** cuando la llamada al proveedor falla de forma reintentable, el consumidor **ve el reintento en
  curso** en vez de un silencio indistinguible de un cuelgue; es la contraparte observable del motor de recuperación.
  **seam:** contratos (el evento se define aquí) + **T1-MOTOR** (lo emite el motor de reintentos, que **no está
  portado** — 02·LR2). **firma:** `ApiRetryEvent(attempt: int, max_retries: int, retry_delay_ms: int,
  error_status: int | None, error: str)` — **`error_status` (el HTTP) y `error` (el texto) son campos distintos y no
  se colapsan**: el consumidor decide por el status (429 ≠ 500), no por el string. Liga **D5**: el `code` del
  `ErrorEvent` (`rate_limit`) es lo que hace *reintentable* al incidente, y este evento es su traza. **cableado:**
  `models/caller.py` — hoy **no reintenta ni emite**: el error del proveedor sale una sola vez por `ErrorEvent`
  (`agent_loop.py:248`) y el loop rompe (`267-270`). **orden:** el **tipo** puede definirse ya con EvR1; la
  **emisión depende de 02·LR2** (mismo patrón que `CompactBoundaryEvent`/EvR1·a con 02·LR1). **prueba:** un
  proveedor que devuelve 429 dos veces y luego 200 produce exactamente 2 `ApiRetryEvent` con `attempt` 1 y 2 y
  `retry_delay_ms` creciente, y **un solo** turno completado (no tres).

- **EvR1·a · `CompactBoundaryEvent` (contrato del evento, motor→02·LR1)** — **comportamiento:** el stream marca la
  frontera de compactación para que resume/re-surface sepan qué tramo quedó fuera del contexto. **seam:** paquete de
  contratos (el evento **se define aquí**) + battery `compaction` (el trigger nace en 02·LR1). **firma:**
  `CompactBoundaryEvent(trigger: Literal["manual","auto"], pre_tokens: int, preserved_segment: dict)` con
  `preserved_segment{head, anchor, tail_uuid}`. **cableado:** lo emite quien ejecute la compactación (02), al bus.
  **orden:** el evento puede definirse ya; la emisión **depende** del motor de 02 (H1). **prueba:** una compactación
  forzada emite exactamente un `CompactBoundaryEvent` con `pre_tokens` > 0 y `tail_uuid` resoluble en el transcripto.
- **EvR2 · `InitEvent` (handshake de apertura, F0)** — **comportamiento:** el **primer** frame del stream anuncia las
  capacidades de la sesión. **seam:** contratos (`InitEvent`) + módulo base loop (lo emite). **firma:**
  `InitEvent(tools, model, mcp_servers, permission_mode, skills, slash_commands, agents)` — **⚠ la firma del tracker
  tiene 7 parámetros y la contraparte canónica 14** (`coreSchemas.ts:1457-1494`): faltan `apiKeySource`, `betas`,
  `claude_code_version`, `cwd`, `fast_mode_state`, `plugins`/`output_style`, y `mcp_servers` debe ser
  `list[{name, status}]`, no una lista de nombres (ver F0). La firma a implementar es la de **14 campos**.
  **cableado:** el loop lo emite al abrir el turno desde el contexto ya ensamblado (`ToolUseContext`/`AppState`/
  factory — hoy la info existe **dispersa**, `factory.py:178-240`, y nadie la publica). **orden:** antes de cualquier
  otro evento del turno; liga 18 (factory) + GAP-02 (permissionMode). **prueba:** el primer elemento de
  `stream()` es un `InitEvent`; un servidor MCP caído aparece como `{name, status:"failed"}` y no como ausencia.
- **EvR3 · wire serializer `Event→SDKMessage` (GAP-EVT5)** — **comportamiento:** un consumidor fuera de proceso
  reconstruye el stream completo (`init → … → result`). **seam:** costura **wire** / battery `wire` — **consumo
  externo por diseño** (el core no la cablea; hermana de `register` de hooks 06, L10). **firma:**
  `to_sdk_message(event: Event) -> dict`, suscrito vía `subscribe_all`. **cableado:** lo suscribe el **integrador**
  (BFF-SSE o REPL), no el factory (verificado: `factory.py:178-240` no cablea consumidor). **orden:** después de que
  el base emita los puntos suficientes (EvR1/2/4/6); es el espejo productor de K4 (`convertSDKMessage`).
  **prueba:** round-trip — un turno serializado y re-parseado por el consumidor espejo produce la misma secuencia,
  con la atribución de subagente preservada (**B2**: el sobre lleva `parent_tool_use_id`/`task_id`).
- **EvR4 · `ResultEvent` terminal + `ErrorEvent.code` (D1·D2·D3·D5)** — **comportamiento:** el turno termina con
  **un** frame que agrega todo lo contabilizado, y los errores llevan código tipado. **seam:** contratos + módulo
  base loop. **firma:** `ResultEvent(subtype, usage, result_text, num_turns, duration_ms, duration_api_ms,
  total_cost_usd, model_usage, denials, structured_output, stop_reason)` con
  `subtype ∈ {success, error_during_execution, error_max_turns, error_max_budget_usd,
  error_max_structured_output_retries}`; y **`ErrorEvent` gana `code`** = el enum de 7 valores del assistant
  (`authentication_failed`/`billing_error`/`rate_limit`/`invalid_request`/`server_error`/`unknown`/
  `max_output_tokens`) — **dos niveles distintos, no se aplanan** (ver D5). **cableado:** el loop lo emite al salir
  (hoy `run()→None`, `agent_loop.py:253-255`); el caller mapea el `code`. **orden:** depende de EvR7·a (usage) para
  poblar `usage`/`cost`; `error_max_turns` requiere que `agent_loop.py:352` **corte** en vez de sólo avisar.
  **prueba:** un turno normal termina en `ResultEvent(subtype="success")` y **ningún** `DoneEvent` posterior; un
  turno que agota los 50 turnos termina en `error_max_turns` con `num_turns == 50`.
- **EvR5 · `ToolProgressEvent` + costura `on_progress` (C3)** — **comportamiento:** una tool larga late mientras
  vive. **seam:** contratos + costura **`on_progress`** (dispatcher/tool → bus) + battery Bash (→10). **firma:**
  `ToolProgressEvent(call_id, partial_output, elapsed_ms, task_id)`. **cableado:** `run_shell` pasa a
  generador/callback y el dispatcher reemite al bus. **orden:** después de EvR3 sólo si se quiere en el wire; el
  evento in-proc no depende de nadie. **prueba:** una tool de >umbral emite ≥2 `ToolProgressEvent` con `elapsed_ms`
  creciente antes de su `ToolResultEvent`, y con `task_id` poblado si corre dentro de un subagente.
- **EvR6 · `SessionStateEvent` (F1)** — **comportamiento:** la sesión publica su estado en vez de obligar al
  consumidor a inferirlo del `stop_reason`. **seam:** contratos + módulo base loop. **firma:**
  `SessionStateEvent(state: Literal["idle","running","requires_action"])`. **cableado:** el loop lo emite en las
  transiciones; **`requires_action` es la señal HITL de `_ends_turn` (02)**, hoy inferida en `agent_loop.py:348` y
  nunca publicada. **orden:** independiente; desbloquea observabilidad HITL. **prueba:** un turno que requiere
  permiso emite `requires_action` **antes** de bloquearse, y `idle` al resolverse.
- **EvR7 · Cabos a otro subsistema / Deuda B** *(rótulo real del tracker, `:325-331`)* — el tracker cierra el plan
  remitiendo **cuatro** cabos, no desarrollándolos: **(i) usage** (FIND-EVT1/EVT5) → *Deuda B `B-usage`*;
  **(ii) `compact_boundary`** → motor **02·LR1**, con el evento definido aquí (EvR1·a); **(iii) `api_retry`** →
  motor **02·LR2**, con el evento definido aquí (EvR1·b); **(iv) `SDKSessionInfo`/K5** → **15·storage**
  (`listSessions`). Los cuatro conservan destino en §3.
  **⚠ DIVERGENCIA DELIBERADA Y DECLARADA sobre (i):** el tracker rutea usage a *Deuda B*, pero **`07·§2.4`
  recalificó `B-usage` de DEUDA-B a CORE-GAP** — precedente que `A3.DB §1` adoptó como el de todo el rollup
  (6 de 7 ítems salen a `DEUDA-A` por el mismo criterio) y que `DEUDA-A §1.2(a)` ya registra. Post-recalificación
  el usage **no es higiene interna sino brecha A↔B**, y por tanto **exige remediación desarrollada aquí**, no una
  remisión. Se desarrolla en **EvR7·a**. Esto es enriquecimiento sobre el tracker, no fidelidad a él: se dice para
  que nadie lo lea como si el tracker lo hubiera escrito.

- **EvR7·a · `Usage` unificado + cable de accounting (E1·E2·E3·E4·E5)** — **comportamiento:** el coste real de la
  sesión es consultable. **seam:** contratos (`Usage` = `ModelUsage`) + costura motor (el caller lo puebla) +
  **cable** base loop→`Session.usage`. **firma:** un único `Usage(input, output, cache_read, cache_creation,
  web_search, thinking, cost_usd, context_window, max_output)` — **se borra la segunda definición** (`session/Usage`,
  E4). **cableado:** `agent_loop.py:253-255` debe **leer `done.usage`** y acumular antes del `break`;
  `runtime.py:403-404` deja de pasar 0/0 a `complete()`. **orden:** `cost_usd` depende de tarifa/modelo (→16);
  todo lo demás es inmediato, y **EvR4 depende de esto**. **prueba:** dos turnos seguidos dejan
  `session.usage.input == t1.input + t2.input` (hoy queda en 0) y `cache_read` distinto de 0 en el segundo.

> **Nota de honestidad sobre la numeración — CORREGIDA 2026-07-29 (`P4-07-13`), y la corrección es el hallazgo.**
> La redacción anterior decía que `EvR1`…`EvR6` estaban «atestiguados literalmente» y que **`EvR7` se asignaba por
> eliminación**, cerrando con *«si al re-abrir `../07-events.md §Plan de remediación` el número resultara otro, se
> corrige el rótulo; el contenido de los siete ítems no depende de esa asignación»*. Al **re-abrir el tracker
> 1→EOF** (445 L) las tres afirmaciones resultan falsas:
> 1. **`EvR7` sí está atestiguado** (`:325`) — y es **«Cabos a otro subsistema / Deuda B (referencia)»**, no el
>    bloque de usage. No hacía falta deducirlo: hacía falta abrirlo.
> 2. **`EvR1` no era `CompactBoundaryEvent`** sino **«taxonomía 5 → 24: los tipos core»** (`:276-281`), un ítem
>    paraguas que enumera **cinco** tipos.
> 3. Por tanto **el contenido SÍ dependía de la asignación**, que es justo lo que la nota descartaba: al colapsar
>    `EvR1` en un solo evento, **`ApiRetryEvent` se quedó sin ficha de remediación** — el único de los cinco tipos
>    core sin desarrollar, con `J3` marcada ❌ en la grid y el plan del base sin remediarla. Restituido como
>    **EvR1·b**.
>
> **Contradicción interna que esto destapa:** el §Ledger de este mismo documento (pregunta 1) afirma *«¿Se leyó
> ÍNTEGRO `../07-events.md`? — **Sí**, líneas 1→446 … remediación **EvR1-7**»*. Esa respuesta y esta nota no podían
> ser ambas ciertas. La verdadera era la nota. **Una respuesta «sí, íntegro» en el ledger convivió con una hedge en
> el cuerpo del documento sin que ninguna de las dos disparara la relectura** — exactamente el modo de fallo que
> `lecciones/03` («nunca declarar íntegro lo leído por tramos») y `lecciones/08` («**abierto ≠ íntegro**») describen.
> **Regla operativa que queda escrita:** *una hedge del tipo «si al re-abrir X resultara otra cosa, se corrige» es
> una confesión de que X no se abrió; no se escribe la hedge — se abre X.* Coste medido de abrirlo: 445 líneas,
> una sola llamada.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (44)

| ID | TIER | destino | cara | evidencia | detalle | nota-identidad |
|---|---|---|---|---|---|---|
| A1 | T2-BASE-MECANISMO + cabo wire | base `events/` + costura wire | ambas | tracker-leído + ensamblador `runtime.py:153-181` (`stream()`) abierto | sí (§2.1/2.5 OI-EVT-1/2) | — |
| A2 | T2-BASE-MECANISMO | base `events/` | base | tracker-leído + `runtime.py:153-181` abierto | sí (§2.1) | — |
| A3 | T1-CONTRATO + T2-BASE | contratos (`Event`) + base `bus.py` | base | tracker-leído + `protocol.py:9-11` (Event frozen) + `bus.py:26-37` (subscribe/subscribe_all) abiertos 1→EOF este ciclo | sí (§2.1) | — |
| A4 | T2-BASE-MECANISMO | base `bus.py` | base | tracker-leído + `bus.py:39-45` (emit try/except por handler) abierto 1→EOF este ciclo | sí (§2.1) | — |
| B1 | T1-CONTRATO + CORE-GAP | contratos + costura motor | base | tracker-leído + ensamblador `caller.py:245/231` abierto | sí (§2.3) | — |
| B2 | **CORE-GAP condicionado** (=K4/GAP-EVT5) + T2-BASE-MECANISMO | base (`_make_bus` per-task) + costura wire | base | tracker-leído + `runtime.py:264` abierto | sí (§2.3, inversión `I1` en A-CIERRE·P4″) | eje ejecución |
| B3 | T1-CONTRATO | cabo → costura wire | ambas | tracker-leído | sí (→wire) | eje ejecución (id opaco) |
| C1 | T1-CONTRATO + T2-BASE | contratos + base loop | base | tracker-leído + `agent_loop.py:248/274-281` abierto | sí (§2.1) | — |
| C2 | T1-CONTRATO + T2-BASE | contratos + base loop | base | tracker-leído + ensamblador `agent_loop.py:312/324` (ToolResult block+dispatch) abierto este ciclo | sí (§2.1) | — |
| C3 | T1-CONTRATO + T2-COSTURA + CORE-GAP | contratos + `on_progress` + battery(→10) | ambas | tracker-leído + `event_types.py` 1→EOF (5 tipos, sin ToolProgress) abierto este ciclo | sí (§2.3 EvR5) | — |
| C4 | CLI-ONLY / INTERFAZ | integrador (interfaz) | integrador | tracker-leído | sí (§2.5 agentic_code) | — |
| C5 | T2-BASE-MECANISMO | base `execution/tasks` | base | tracker-leído + `runtime.py:267-277` abierto | sí (§2.1) | eje ejecución |
| D1 | T1-CONTRATO + T2-BASE + CORE-GAP | contratos (`ResultEvent`) + base loop | base | tracker-leído + `agent_loop.py:253-255` (`run()→None`) abierto | sí (§2.3 EvR4) | — |
| D2 | T1-CONTRATO + CORE-GAP | contratos + base loop | base | tracker-leído + `agent_loop.py:248/267-270` abierto | sí (§2.3 EvR4) | — |
| D3 | CORE-GAP (subsumido D1) | base loop (`ResultEvent`=fin) | base | tracker-leído | sí (§2.3, se pliega D1) | — |
| D4 | T1-MOTOR | costura motor | base | tracker-leído + ensamblador `caller.py:227` abierto | sí (§2.1) | — |
| D5 | T1-CONTRATO + T1-MOTOR + CORE-GAP | contratos (`ErrorEvent.code`) + costura motor | base | tracker-leído + `caller.py:236-242` abierto | sí (§2.3 EvR4) | — |
| E1 | T1-CONTRATO + T1-MOTOR + CORE-GAP | contratos (`Usage`) + costura motor | base | tracker-leído + `caller.py:226-233` (`thinking=0`) abierto | sí (§2.3) | — |
| E2 | T2-BASE + T1-CONTRATO + CORE-GAP | base (acumula) + contratos | base | tracker-leído + `agent_loop.py:253-255` abierto | sí (§2.3) | eje persistencia (usage sesión) |
| E3 | T2-BASE-MECANISMO + CORE-GAP (+faceta DEUDA-B) | base loop/runtime (cablear) | base | tracker-leído + ensamblador `runtime.py:398,403-404` + `session.py:16-19,42` abiertos | sí (§2.3/2.4) | **eje persistencia · `Session.usage`** |
| E4 | DEUDA-B | unificar `Usage` (=E1) | base | tracker-leído + `session.py:16-19` vs `events/Usage` abierto | N/A (DEUDA-B) | — |
| E5 | CORE-GAP | contratos + →16 (tarifa) | base | tracker-leído | sí (§2.3, →16) | — |
| F0 | T1-CONTRATO + T2-BASE + CORE-GAP | contratos (`InitEvent`) + base loop | ambas | tracker-leído + `factory.py:178-240` (info dispersa, sin frame) abierto | sí (§2.3/2.5 OI-EVT-3) | eje persistencia (bootstrap) |
| F1 | T1-CONTRATO + T2-BASE + CORE-GAP | contratos (`SessionStateEvent`) + base loop | base | tracker-leído + `agent_loop.py:348` abierto | sí (§2.3 EvR6) | — |
| F2 | CORE-GAP + CLI-ONLY (fast_mode) | contratos (`StatusEvent`) + integrador | ambas | tracker-leído | sí (§2.3) | — |
| F3 | BATTERY background-agents | battery → 05/13 | base | tracker-leído | sí (→05/13) | — |
| F4 | CLI-ONLY / INTERFAZ | integrador (interfaz) | integrador | tracker-leído | sí (§2.5 agentic_code) | — |
| G1 | T1-CONTRATO + T2-BASE + CORE-GAP | contratos (`TaskStartedEvent`) + base `execution/tasks`(→05) | base | tracker-leído + `registry.py:112 push_event` abierto | sí (§2.3) | eje ejecución (task) |
| G2 | T2-BASE + CORE-GAP | base `execution/tasks` + →E | base | tracker-leído + `runtime.py:267-277` abierto | sí (§2.3) | eje ejecución (task) |
| G3 | T2-BASE + CORE-GAP parcial | base runtime (`_notify`) + →05 | ambas | tracker-leído + ensamblador `runtime.py:294-304` abierto | sí (§2.3) | eje persistencia (parent_session_id) |
| G4 | T2-BASE-MECANISMO (divergencia) | base + cabo wire | base | tracker-leído | sí (§2.1) | eje ejecución |
| H1 | T1-CONTRATO + BATTERY compaction + CORE-GAP | contratos (evento) + battery(→02·LR1) | ambas | tracker-leído | sí (§2.2/2.3, →02) | eje persistencia (frontera) |
| I1 | T1-CONTRATO + T2-COSTURA + CORE-GAP | contratos + costura hook-sink(→06) | ambas | tracker-leído | sí (§2.1/2.3, →06) | — |
| J1 | T3-INTEGRADOR | integrador (cuenta) + →16/18 | integrador | tracker-leído | sí (§2.5 OI-EVT-4) | — |
| J2 | T3-INTEGRADOR | integrador (auth) → 18 | integrador | tracker-leído | sí (§2.5 OI-EVT-4) | eje persistencia (auth) |
| J3 | T1-CONTRATO + CORE-GAP | contratos (evento) + motor →02·LR2 | base | tracker-leído | sí (§2.3, →02) | — |
| J4 | BATTERY memory/artifacts | battery → 13 | base | tracker-leído | sí (→13) | eje persistencia (artefactos) |
| J5 | BATTERY mcp | battery → 11 | base | tracker-leído | sí (→11) | — |
| J6 | CLI-ONLY / INTERFAZ + BATTERY commands | integrador (terminal) + battery(12) | integrador | tracker-leído | sí (§2.5 agentic_code) | — |
| K1 | T1-CONTRATO(→01) + T2-BASE | contratos (message) + base | base | tracker-leído + `agent_loop.py` append a `ctx.messages` abierto | sí (§2.1, →01/03/15) | eje persistencia (transcripto) |
| K2 | T1-CONTRATO(→01) + cabos | contratos + →05 (priority) + →15 (isReplay) | ambas | tracker-leído | sí (→05/15) | eje persistencia (transcripto/resume) |
| K3 | CLI-ONLY / INTERFAZ | integrador (interfaz) | integrador | tracker-leído | sí (§2.5 agentic_code) | — |
| K4 | CLI-ONLY / INTERFAZ | integrador (consumidor wire) | integrador | tracker-leído | sí (§2.5 OI-EVT-2) | — |
| K5 | T2-COSTURA / BATTERY storage | costura storage-index → 15 + BFF | ambas | tracker-leído | sí (§2.5 agentic_assistant, →15) | **eje persistencia · id opaco+repo** |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../07-events.md`?** — **Sí tras la re-lectura del 2026-07-29, NO en la pasada que firmó
   este ledger** *(corrección de campo, `D-06·2` — la afirmación original se conserva citada para que el error
   siga siendo auditable: «**Sí**, líneas 1→446 (cabecera de emisión/consumo, re-audit 2026-07-12, tesis, tabla
   A1–K5, resumen de estados, hallazgos FIND-EVT1-9, gaps GAP-EVT1-5, ajuste arquitectural, **remediación
   EvR1-7**, re-visita gate 11 con mini-ledger + ledger de cierre + 4 preguntas + veredicto)»)*. **Por qué era
   falsa:** el propio §2.6 de este documento contenía, en la misma pasada, una nota declarando que el rótulo
   `EvR7` se asignaba **por eliminación** «si al re-abrir `../07-events.md §Plan de remediación`…» — es decir, el
   documento afirmaba en su ledger haber leído íntegro lo que en su cuerpo admitía no haber abierto. **Coste
   material del hueco:** `ApiRetryEvent` perdido del plan del base (`P4-07-13`, restituido como EvR1·b). **Estado
   real hoy:** tracker abierto **1→445 (EOF), una sola llamada, 2026-07-29**, con línea en `EVIDENCIA.log`;
   el inventario de secciones de la cita original es correcto salvo el rótulo de `EvR1`/`EvR7`.
2. **¿Reconcilia el conteo?** — findings en `../07-events.md` = **44 filas** discretas (A1–K5: A×4, B×3, C×5, D×5, E×5, F×5, G×4, H×1, I×1, J×6, K×5); colocados = **44**; sin colocar = **0** *(re-contado fila a fila en A-CIERRE·P4″, sonda c26: **✅4 · 🟡6 · 🔀16 · ❌14 · ⛔4 = 44**; tras la inversión `I1` de B2 el reparto pasa a **✅4 · 🟡6 · 🔀15 · ❌15 · ⛔4 = 44** — el total no cambia)*. ✅ Los 9 `FIND-EVT*` + 5 `GAP-EVT*` (consolidaciones) mapean todos a filas colocadas (EVT1=D1/E2/E3; EVT2=taxonomía A/§2.3; EVT3=A1/A2; EVT4=D2; EVT5=E1/E4; EVT6=C3; EVT7=F1; EVT8=C5/G2; EVT9=F0; GAP1=E3; GAP2=D1; GAP3=H1; GAP4=I1; GAP5=A1). *(El «resumen de estados» del tracker cuenta ~48 sub-features aprox.; las filas discretas colocables son 44 — ver §nota.)*
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, todos re-abiertos en ESTE ciclo con mis ojos** (ninguno heredado del tracker): A3/A4 `protocol.py:9-11` + `bus.py:26-45` (Event frozen, subscribe/subscribe_all, emit try/except) **1→EOF**; A1/A2 `runtime.py:153-181` (`stream()` productor ordenado); B2/C5/G2 `runtime.py:264-283` (`_make_bus`, `subscribe_all` sólo si `on_event`); C1 `agent_loop.py:248/274-281`; C2 `agent_loop.py:300-328` (ToolResult en 312 block-deny + 324 dispatch); D4 `caller.py:227`; D5/E1/B1 `caller.py:226-245` (`thinking=0`, skip, `ErrorEvent(str)`); E3/E2 `agent_loop.py:253-255` + `runtime.py:398,403-404` + `session.py:16-19,42` (1→EOF); G3 `runtime.py:294-304`; F0 `factory.py:178-240` (sin frame init, sin sink de eventos); K1 `agent_loop.py` append. Los **❌ por ausencia** (C3/D1/D2/D3/E5/F0/F1/F2/G1/H1/I1/J3) se apoyan en `event_types.py` **1→EOF abierto este ciclo** = **exactamente 5 tipos** (Token/ToolCall/ToolResult/Done/Error), sin init/session_state/tool_progress/compact_boundary/api_retry/result-terminal — ausencia probada por lectura directa, no afirmación de cableado (Q3 aplica a afirmar cableado). **Corrección de honestidad aplicada en el cierre:** la 1ª redacción de este ledger citó `bus.py`/`event_types.py`/`agent_loop.py:312/324` como evidencia sin haberlos abierto ESTE ciclo (los heredaba del gate 11 del tracker); re-abiertos 1→EOF/tramo antes de firmar (ver §nota).
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla 4 obligaciones universales (OI-EVT-1…4) con los 6 campos L05 + la realización específica por integrador (agentic_code terminal / agentic_assistant BFF+front), y los CLI-ONLY (C4/F4/J6/K3/K4) aterrizan en la capa de interfaz del integrador con destino nombrado. Ningún finding cerrado con "→ integrador" a secas.
5. **¿Doble filo (L10)?** — **Sí, con DOS correcciones aplicadas.** (a) Ningún ❌ disfrazado de 🔀 entre los que ya lo eran (D1/D2/E2/E3/F0/F1/G1/H1/I1/J3 se mantienen como CORE-GAP; los 🔀 A1/A2/G4/K1 son divergencias por-diseño con efecto observable reproducido vía `stream()`). (b) ⚠ **`B2` SÍ lo era y se corrige en A-CIERRE·P4″ (`I1`)**: estaba rotulado 🔀 «divergencia por-diseño» apoyándose en que el bus per-task atribuye implícitamente, pero esa atribución **no sobrevive a la serialización a canal único**; es una capacidad ausente condicionada al wire, exactamente como K4/GAP-EVT5. Su familia (`B2`/`G4`) ya no se cierra entera como divergencia: **`G4` sí** lo es (el aislamiento en `rec.events` es una decisión de canal), **`B2` no** (es un campo que falta). Este es el modo de fallo que L10 nombra en su filo caro: la divergencia rotulada correctamente en su nivel (in-proc) y **arrastrada sin condicionar** al nivel donde deja de valer. Ninguna deuda inflada: los CLI-ONLY (C4/F4/J6/K3/K4) y T3 (J1/J2) **NO** se cuentan como brecha del base (son capa de interfaz/cuenta del integrador). **Corrección de tier:** el `B-usage` del tracker se re-clasifica de «DEUDA-B» a **CORE-GAP** (E1/E2/E3/E5); sólo E4 (unificar dos `Usage`) queda como tier DEUDA-B puro.

### §Nota de honestidad
- **Conteo 44 vs "~48":** el «Resumen de estados» del tracker (✅5·🟡8·🔀15·❌16·⛔4=48) cuenta sub-features aproximadas de las 24 variantes; las **filas discretas colocables** de la tabla A1–K5 son **44** (recontadas fila a fila: ✅4·🟡6·🔀16·❌14·⛔4). La SEPARACION reconcilia sobre las 44 filas colocables — es lo enumerable y repartible (L01). **Diagnóstico corregido en A-CIERRE·P4″ (`T1`, sonda c26):** decir que «el delta con 48 es la fuzz de sub-features» era **blando y falso en la atribución**. El re-conteo fila a fila del grid da **✅4 · 🟡6 · 🔀16 · ❌14 · ⛔4 = 44**, contra el `✅5 · 🟡8 · 🔀15 · ❌16 · ⛔4 = 48` del §Resumen del tracker: **4 de las 5 cifras del tracker están mal** (sólo ⛔=4 coincide), y los signos van en direcciones opuestas (el tracker sobre-cuenta ✅🟡❌ y sub-cuenta 🔀). Eso no es granularidad distinta: es un **§Resumen desincronizado de su propio grid**. El grid manda; la cifra buena es 44 y el reparto el de arriba. *(Tras la inversión `I1` de B2: `🔀15 · ❌15`.)*
- **Verificación de B (gate 11 heredado + re-abierto) + auto-corrección de sobre-declaración:** el tracker ya re-verificó B 1→EOF en su 2ª vuelta (mini-ledger líneas 364-378). En la 1ª redacción de este cierre **sobre-declaré**: cité `events/bus.py`, `events/protocol.py`, `events/event_types.py` y `agent_loop.py:312/324` como evidencia de las ✅ A3/A4/C2 y de la prueba-de-ausencia "5 tipos" **sin haberlos abierto ESTE ciclo** — los heredaba de la palabra del tracker (justo lo que L11 y el gate auto-adversarial prohíben). **Corregido antes de firmar:** abrí `protocol.py` (1→23), `bus.py` (1→46), `event_types.py` (1→44) y `__init__.py` (1→16) **1→EOF**, y `agent_loop.py:300-328` — todos confirmaron lo declarado (Event frozen; subscribe/subscribe_all/emit-try-except; exactamente 5 tipos + `Usage` con thinking ≠ `session/Usage`; ToolResult en 312/324). Los tramos-bisagra de cableado (`stream()`, `_make_bus`/`subscribe_all`, usage/turn_count en `runtime.py`+`agent_loop.py`+`session.py`, `caller.py`, `factory.py`) sí se abrieron desde el principio. Ninguna ✅/🔀 queda apoyada en la palabra del tracker.
- **Cabos con destino** (no pendientes de verificación): E5/costUSD→**16**; `structured_output` en result→**09**(G3); `compact_boundary` motor→**02·LR1**; `api_retry` motor→**02·LR2**; hook_* en stream→**06**; K5·SDKSessionInfo→**15**; K2·priority→**05·FIND-EXEC12**; K2·isReplay→**15**; F3 post_turn_summary→**05/13**; J4→**13**; J5→**11**; J6→**12**. El **wire serializer** (GAP-EVT5/EvR3) y el `InitEvent` (EvR2) se vierten a `00-INTEGRADORES.md` en A1.7.

### 3.3 VEREDICTO

> **Reescrito en A-CIERRE·P4″ (2026-07-29).** El veredicto anterior era **«✅ NADA PENDIENTE → A1.4 (02·loop)»**.
> La reconciliación `tracker → SEPARACION` con la columna de cruce 1→EOF (D-05) encontró **12 pérdidas
> documentales** (`P4-07-1..13`, remediadas in situ arriba — la 13ª descubierta al pagar el pendiente 6) y **5 inversiones** (`I1`…`I5`), de las cuales una
> —`I1`— cambia un tier. Un ✅ que se sostenía sobre un plan de remediación que el documento había dejado de
> contener no era un cierre: era un cierre **no verificado**.

**⛔ PENDIENTE(S) — el par queda RECONCILIADO, no CERRADO.**

**Lo que sí queda firme (dentro del par):** las **44 filas** repartidas con TIER+destino (re-contadas fila a fila,
sonda c26); **20 CORE-GAPs** para DEUDA-A (B1, **B2**, C3, D1, D2, D3, D5, E1, E2, E3, E5, F0, F1, F2, G1, G2, G3,
H1, I1, J3); **1 DEUDA-B** (E4, +faceta de E3); **7 costuras** con productor/consumidor (`Event`+`EventBus`,
`stream()`, wire serializer, model-caller, `on_progress`, hook-sink, cable de usage); **4 batteries** (wire,
compaction, background-agents, commands); **4 obligaciones universales de integrador** (OI-EVT-1…4) + realización
por integrador; el **plan de remediación del base `EvR1`(+`·a`/`·b`)…`EvR7`(+`·a`)** con los 6 campos L05 (§2.6, restituido y **renumerado contra el tracker**); la
**cabecera de origen** con las 5 contrapartes canónicas y el mapa de emisión (§0.1, restituida). Corrección de
doble filo aplicada dos veces (`B-usage`: DEUDA-B→CORE-GAP; `B2`: divergencia→CORE-GAP condicionado).

**Los 6 puntos que vivían fuera del documento — estado real al 2026-07-29 (4 EJECUTADOS, 2 abiertos):**
1. ✅ **EJECUTADO** — `DEUDA-A §0.2:139`: `07·events | 19` → **20** con `B2` en la forma; inventario `≈152` → `≈153`.
2. ✅ **EJECUTADO** — `DEUDA-A §1.3:362`: rótulo caduco «K4 (sobre del evento)» → «K4 (identidad en el `Event`
   base…)»; era el **séptimo y último** sitio del `CAT-h10` (`I5` cerrado).
3. 🟡 **PARCIAL** — `SEAMS.md`: ✅ `:405` corregido (`07·E19` inexistente → **`05·E19`**, `I4` cerrado). ❌ Siguen
   abiertos **`I2`** (el cable de usage-accounting **sin número `S`** pese a que 07 fue documento de origen del
   rollup; sonda c24 = 6/7) y **`I3`** (las tres remisiones de `S21` al par 07 con dueño equivocado; el real es
   `H-5`/`DB-29`) — ambos exigen abrir `SEAMS` con su dueño delante, no sustituir una grafía. → `AC-23`/`AC-24`.
4. ✅ **EJECUTADO Y CERRADO** — `BATTERIES·B06`: aplicada la **disciplina de prefijo** (`07·Kn` filas del grid /
   `DA·Kn` keystones; los `K\d` de 07 son filas nativas y renumerarlos rompería la reconciliación 44=44), **y el
   `K5` de la columna CORE-GAPs RETIRADO** (`AC-26` cerrado): ninguna de sus dos lecturas era admisible —`07·K5`
   es 🔀 y `DA·K5` es `ToolResult`, cuyo hogar es B07—. Ver la nota resuelta en `BATTERIES.md`.
5. ❌ **ABIERTO** — `00-INTEGRADORES §1.4` sostiene un criterio de aceptación con **ENDURECIMIENTO** (prosa
   aproximada de este nivel citada como hecho estructural en el siguiente). → `AC-25`.
6. ✅ **CERRADO 2026-07-29 (`P4-07-13`)** re-abriendo el tracker **1→445 (EOF)**. No era un rótulo: `EvR1` y `EvR7`
   estaban **ambos** mal asignados, y el colapso de `EvR1` había dejado **`ApiRetryEvent` sin ficha de
   remediación** (pérdida nueva, restituida como **EvR1·b**). Ver la nota de numeración corregida en §2.6.
   **Lección: el ítem estaba catalogado como «confirmar un rótulo» —coste aparente cero— y el hallazgo real fue
   una pérdida de contenido.** Es la razón por la que un pendiente no se arrastra: su etiqueta no predice su peso.

El destino del flujo (**A1.4 · 02·loop**) no cambia. **El par sigue RECONCILIADO y no CERRADO**, ahora por
**3 ítems** (`I2`·`I3` de SEAMS y el ENDURECIMIENTO de `00-INTEGRADORES §1.4`), todos asentados en el ledger de
A-CIERRE como `AC-23`/`AC-24`/`AC-25`. Los pendientes de **verificación** del par están en **cero**: los tres
restantes son trabajo de **remediación** sobre documentos de otro dueño, no lecturas sin hacer.
