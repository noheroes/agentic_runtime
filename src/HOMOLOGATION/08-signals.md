# 08 · signals — homologación

Cancelación/abort del `agentic_runtime` contra la maquinaria `AbortController`/`AbortSignal`
del canónico (`/home/noheroes/python/claude-code/src`).

## Contrapartes leídas (íntegras / tramos abort)

**Runtime:**
- `signals/protocols.py` (14 LOC, íntegro) — `SignalType {ABORT,PAUSE,RESUME}`, `SignalHandler` (Protocol).
- `signals/bus.py` (96 LOC, íntegro) — `SignalBus`, `SignalHandle`, `_Node`, `register/unregister/get_signal/send(cascade)/register_handler`.
- `signals/__init__.py` (íntegro) — export surface.
- Mecanismo REAL de cancelación (el que sí se cablea): `context/tool_use.py:47` (`ToolUseContext.stop: asyncio.Event|None`),
  `loop/agent_loop.py:173,186,227` (checks + threading a `complete(stop=…)`),
  `models/caller.py:151,166,188-190` (`replace(opts, signal=stop)` → `agentic_models.StreamOptions.signal`),
  `models/protocol.py:17,33` (`stop` en `ModelRequest`), `tools/dispatcher.py:54` (`ToolResult.aborted`),
  `execution/fork/__init__.py:67,81-83` (`propagate_abort` → objeto Event compartido vs fresco),
  `tools/protocol.py:47-48` (`ToolResult.aborted` / `is_aborted`).

**Canónico:**
- `utils/abortController.ts` (99 LOC, **ÍNTEGRO**) — `createAbortController(maxListeners)`, `createChildAbortController(parent)`
  (propagación padre→hijo, hijo→padre NO, WeakRef GC-safe, fast-path si el padre ya abortó).
- `services/tools/StreamingToolExecutor.ts` (530 LOC, **ÍNTEGRO**) — árbol de controllers y semántica de cancelación en vuelo
  (detalle abajo).
- `hooks/useCancelRequest.ts` (276 LOC, **ÍNTEGRO**, ⛔ React — comportamiento extraído) — escalera de disparo del abort
  (detalle abajo).
- `Task.ts` (125 LOC, **ÍNTEGRO**; ya cubierto en 05) — `TaskContext.abortController` (39, un controller POR task),
  `totalPausedMs` (53, pausa a nivel de lifecycle), nota "abortController were dead weight" para kill (71: kill usa sólo setAppState).
- `services/tools/toolExecution.ts` (1745 LOC — tramos abort **íntegros** 400-469 y 1615-1714; el resto = infra de tool-exec → 09/10):
  check pre-exec `signal.aborted` (415) → `createToolResultStopMessage`+`CANCEL_MESSAGE`+`withMemoryCorrectionHint` (443-452, con `tool_use_id`),
  `logEvent('tengu_tool_use_cancelled')` (416); en catch: `isInterrupt = error instanceof AbortError` (1694), `AbortError` NO loguea
  `tengu_tool_use_error` (1631), `isInterrupt` se **pasa a `runPostToolUseFailureHooks`** (1700-1707).
- `Tool.ts` (792, ya ÍNTEGRO en 03/08): `ToolUseContext.abortController: AbortController` (180), `signal: AbortSignal` en `call` (201),
  `interruptBehavior?(): 'cancel'|'block'` (416); callbacks del ctx `setInProgressToolUseIDs`/`setHasInterruptibleToolInProgress`.
- `QueryEngine.ts` (1295, ya ÍNTEGRO en 02): `abortController` propio (187,203 `?? createAbortController()`),
  `interrupt(): void { this.abortController.abort() }` (1157-1159), threading a `query()` (368,516,1210,1241,1274).
- `query.ts` (1729, ya ÍNTEGRO en 02): checks pre-modelo (1015) y post-tools (1485) → `signal.reason !== 'interrupt'`
  (1046,1501) gatea `createUserInterruptionMessage`; `yieldMissingToolResultBlocks`/`getRemainingResults` en abort (1013-1024);
  retornos tipados `{reason:'aborted_streaming'}` / `{reason:'aborted_tools'}`.
- `services/tools/toolHooks.ts` (650, tramos abort): `signal` propagado a hooks (63,220,472,582).
- `services/api/claude.ts` (3419, tramos abort — capa modelo → verificación fina en 16): `signal→fetch/stream`, `APIUserAbortError`
  (114,744-745,876,2434-2453,2738,2796), `stream.controller.abort()` en cleanup (2906-2907).

**Detalle `StreamingToolExecutor.ts` (íntegro)** — la maquinaria de cancelación en vuelo que el grep me había ocultado:
- Tres `ToolStatus` (queued/executing/completed/yielded) + control de concurrencia (`isConcurrencySafe`): safe corren en paralelo, no-safe en exclusiva.
- `siblingAbortController` = hijo del `abortController` del query (constructor:59). Un error de **Bash** (sólo Bash, 359) lo aborta con `'sibling_error'` (362) → mata subprocesos hermanos en vuelo, SIN abortar al padre (no termina el turno).
- `toolAbortController` per-tool = hijo del sibling (301). Su listener de abort **bubblea al query controller** SÓLO si `reason !== 'sibling_error'` AND el padre no estaba abortado AND no hay `discard` (307-315) — necesario para que el rechazo de permiso (`PermissionContext.cancelAndAbort`) termine el turno (regresión #21056, ExitPlanMode).
- `getAbortReason` (210-231) devuelve **tres** razones: `'streaming_fallback'` (si `discard()` — fallback de streaming, 213), `'sibling_error'` (216), `'user_interrupted'` (219-228). En interrupción de usuario (`reason==='interrupt'`) sólo cancela tools con `interruptBehavior()==='cancel'`; las `'block'` no se abortan (223-227, `getToolInterruptBehavior` default 'block').
- `createSyntheticErrorMessage` (153-205): **tres mensajes sintéticos distintos** por `tool_use_id` — `user_interrupted`→`REJECT_MESSAGE` ("User rejected tool use", 160-172), `streaming_fallback`→"discarded" (174-188), `sibling_error`→"Cancelled: parallel tool call … errored" (189-204). Garantiza pairing `tool_use↔tool_result` para cada tool abortada (queued o en vuelo).
- `updateInterruptibleState`→`setHasInterruptibleToolInProgress` (254-260): reporta al ctx si TODAS las tools en ejecución son interrumpibles ('cancel') — señal que gobierna si Ctrl+C puede interrumpir el turno. `setInProgressToolUseIDs`/`markToolUseAsComplete` (267,435,521) trackean qué IDs están en vuelo.

**Detalle `useCancelRequest.ts` (íntegro, ⛔ React → comportamiento)** — el disparo del abort:
- **Escalera de prioridad** (`handleCancel` 87-122): (1) hay task activa (`abortSignal && !aborted`) → cancelarla (abort + vaciar `toolUseConfirmQueue`); (2) idle con cola → pop de cola; (3) fallback cancel. `logEvent('tengu_cancel')`.
- **Ctrl+C (`app:interrupt`) vs Escape (`chat:cancel`)**: Ctrl+C siempre cancela; Escape cede a mode-exit en modos especiales con input vacío y a la navegación de teammate.
- **`chat:killAgents`** (Ctrl+X Ctrl+K, dos pulsaciones en ventana de 3s, 225-266): mata TODOS los agentes background.
- **`killAllAgentsAndNotify`** (172-195): `killAllRunningAgentTasks` + por cada uno `markAgentsNotified` + `emitTaskTerminatedSdk(taskId,'stopped')` + una notificación agregada al modelo. **Este es el análogo conductual REAL de `SignalBus.send(cascade=True)` para agentes en background** — la cascada a hijos NO va por el árbol de `AbortController` (eso es para tools/subquery del MISMO turno), sino por **kill de tasks**.

## Tesis arquitectural

El canónico **no tiene un "SignalBus"**: su primitiva de cancelación es el `AbortController`/`AbortSignal`
nativo, que **vive dentro del `ToolUseContext`** (`abortController`) y se threadea por TODO el core (167 archivos
lo tocan). La señal lleva **`reason`** (`'interrupt'`, `'sibling_error'`, `'streaming_fallback'`, user) que gobierna
el comportamiento posterior, y es **one-shot irreversible**.

**Hay DOS mecanismos de cascada distintos, no uno** (matiz que la lectura íntegra reveló):
1. **Árbol de `AbortController`** (`createChildAbortController`) — para tools/subquery del **mismo turno**. Cada tool
   deriva un hijo del controller del padre, con **direccionalidad estricta** (padre→hijo propaga; hijo→padre NO, salvo
   el bubble explícito de rechazo de permiso, StreamingToolExecutor:307-315). Incluye un nivel intermedio
   `siblingAbortController` para que un error de Bash mate hermanos sin terminar el turno.
2. **Kill de tasks** (`killAllRunningAgentTasks` + `emitTaskTerminatedSdk`) — para **agentes en background** (hijos de
   OTRO turno/sesión). No usa el árbol de controllers; cada agente es un task con su propio `TaskContext.abortController`
   (Task.ts:39) y se cancela por su registry (subsistema 05).

El `SignalBus` del runtime, con su cascada `send(cascade=True)` sobre un árbol `parent→children`, **conflaciona los
dos** en una sola abstracción — y encima está desconectado de ambos.

Además, **pausa SÍ existe en el canónico**, pero a nivel de **lifecycle de task** (`totalPausedMs`, Task.ts:53, para
contabilidad de tiempo en backgrounding), NO como estado del signal de abort. `PAUSE`/`RESUME` sobre un signal de
cancelación no tiene contraparte (el abort es irreversible); si el runtime los quiere, su hogar es el lifecycle de
task (04/05), no `signals/`.

El runtime tiene **DOS mecanismos paralelos y desconectados**:
1. **`ctx.stop` (`asyncio.Event`)** — el REAL: cableado end-to-end (loop→caller→`agentic_models` signal; dispatcher;
   fork). Es la homologación de facto del `AbortController`, pero **degradada**: binaria (set/clear), **sin `reason`**,
   sin árbol de derivación (el fork comparte el MISMO objeto Event o lo aísla), sin `interruptBehavior`.
2. **`SignalBus`/`SignalType`/`SignalHandle`** — **HUÉRFANO**: implementa el árbol de cascada
   (`ABORT/PAUSE/RESUME`, `send(cascade=True)`) que sería la contraparte conceptual del árbol de controllers,
   pero **NINGUNA ruta lo consulta** — sólo lo tocan sus propios tests. Hermano exacto de FIND-MODE1 (`modes/`
   huérfano) y FIND-EXEC4 (`observer/` huérfano).

**La homologación de 08 es del SEAM de cancelación**: el runtime debe (a) reconciliar los dos mecanismos en UNO,
(b) que esa primitiva lleve `reason` y sea un ÁRBOL con direccionalidad (espejo `createChildAbortController`), y
(c) exponer un `interrupt()` público. El disparo del abort (quién llama `.set()`/`.abort()`) es del integrador
(como HITL) — eso es correcto y ✅ de comportamiento.

## Tabla feature-by-feature

| # | Feature (canónico) | Runtime | Estado | Nota |
|---|---|---|---|---|
| S1 | Primitiva de cancelación en el ctx (`abortController` en `ToolUseContext`) | `ctx.stop: asyncio.Event` | 🟡 | Existe y vive en el ctx, pero degradada (ver S3/S4/S5). |
| S2 | Propagación a la llamada al modelo (`signal`→fetch/stream) | `complete(stop=…)`→`replace(opts, signal=stop)`→`agentic_models` | ✅ | Seam cableado (loop→caller→models). Verificación fina del corte HTTP = 16. |
| S3 | Abort **reason** (`signal.reason`: `'interrupt'`/`'sibling_error'`/user) | `asyncio.Event` binario, sin reason | ❌ | **FIND-SIG2**. |
| S4 | Árbol de controllers con direccionalidad (`createChildAbortController`) | `fork.propagate_abort`: Event compartido (True) / fresco (False) | ❌ | **FIND-SIG3**: objeto compartido = sin direccionalidad; hijo abortaría al padre. |
| S5 | `interruptBehavior()` per-tool (`'cancel'`/`'block'`) | — | ❌ | **FIND-SIG4**: el runtime aborta toda tool indiscriminadamente. |
| S6 | Check pre-modelo de abort | `agent_loop.py:173,186` | ✅ | Homologa `query.ts:1015` (a nivel de turno). |
| S7 | Check pre/post ejecución de tool | `dispatcher.py:54` → `ToolResult.aborted` | 🟡 | Corta antes de ejecutar; falta `getRemainingResults`/pairing sintético completo (S9). |
| S8 | Cancelación de tools EN VUELO (sibling/per-tool child, `sibling_error` sólo Bash, bubble permiso) | — | ❌ | **FIND-SIG3b**: sin `siblingAbortController`/`toolAbortController`; el dispatcher no aborta subprocesos en curso ni cascada Bash→hermanos. |
| S9 | Invariante tool_use↔tool_result en abort (`yieldMissingToolResultBlocks`/`getRemainingResults`) | `dispatcher` devuelve `ToolResult.aborted` por tool; loop parea por `call_id` | 🟡 | **FIND-SIG7** (familia FIND-L1): pairing se mantiene si el break es a nivel dispatch; abort mid-stream con tool_calls parciales sin verificar. |
| S21 | **Tres** mensajes sintéticos por tool abortada (`CANCEL_MESSAGE` pre-exec · `REJECT_MESSAGE` rechazo permiso · sibling-error), con `withMemoryCorrectionHint` | `ToolResult.aborted` = string plano `"aborted: {name}"` | ❌ | **FIND-SIG10**: un único texto plano; sin distinguir interrupción vs rechazo-permiso vs sibling, sin memory-correction hint. |
| S22 | `interruptBehavior==='cancel'` para todas las en-vuelo ⇒ turno interrumpible (`setHasInterruptibleToolInProgress`) | — | ❌ | **FIND-SIG11**: el runtime no computa ni expone si el turno es interrumpible; Ctrl+C no puede gatearse. |
| S23 | Tracking de tool_use IDs en vuelo (`setInProgressToolUseIDs`/`markToolUseAsComplete`) | — | ❌ | Necesario para el pairing sintético (S9) y para la señal de S22. |
| S24 | `discard()` + razón `'streaming_fallback'` (abandonar tools del intento fallido de streaming) | — | ❌ | Sin equivalente; liga a la recuperación de streaming (motor #2 de 02, aún ❌). |
| S25 | `isInterrupt = error instanceof AbortError` pasado a `PostToolUseFailure` hooks; `AbortError` no loguea error | — | ❌ | **FIND-SIG12** (concreta GAP-SIG2): los hooks del runtime no distinguen fallo-por-abort de error real. |
| S10 | Mensaje de interrupción al usuario, gateado por `reason!=='interrupt'` | — | ❌ | **FIND-SIG2b**: sin `createUserInterruptionMessage` ni distinción submit-interrupt. |
| S11 | Resultado terminal tipado (`{reason:'aborted_streaming'\|'aborted_tools'}`) | `run()→None` | ❌ | **FIND-SIG8** (liga 07·FIND-EVT1: sin `SDKResultMessage`). |
| S12 | Error de abort a nivel API (`APIUserAbortError`, `stream.controller.abort()` cleanup) | delegado a `agentic_models` | 🔀 | Delegado; verificar en 16 que `StreamOptions.signal` corta y surface el error tipado. |
| S13 | `interrupt()` público (QueryEngine.interrupt → abort) | — | ❌ | **GAP-SIG1**: no hay método `interrupt()` en loop/runtime; el integrador debe setear `ctx.stop` a mano. |
| S14 | Disparo del abort (keybinding Ctrl+C/Escape, prioridad cancel-task-then-pop) | integrador (UI ⛔) | ⛔ | `useCancelRequest.ts` = React/terminal. El **comportamiento** (quién dispara) es del integrador; el runtime sólo expone el seam. |
| S15 | Cleanup on abort (cleanupComputerUseAfterTurn, chicago MCP unhide/lock release) | — | 🔀/❌ | **FIND-SIG9**: computerUse ⛔; el patrón "liberar locks/recursos al abortar mid-turn" (MCP) sí es core → GAP. |
| S16 | `SignalBus` árbol de cascada (`send(cascade=True)`, parent→children DFS) | `signals/bus.py` | 🔀 | **FIND-SIG1**: HUÉRFANO — no lo consulta ninguna ruta; además conflaciona los DOS mecanismos de cascada (árbol controllers in-turn vs kill de tasks). |
| S17 | `SignalBus.register_handler` (extensión: handlers externos) | almacena, nunca invoca | ❌ | **FIND-SIG5**: `send()` no llama `handle_signal` → extension point muerto; `SignalHandler` Protocol sin uso. |
| S18 | `PAUSE`/`RESUME` | `SignalType.PAUSE/RESUME`, `RESUME` limpia la señal | 🔀 | **FIND-SIG6**: sin contraparte — `AbortSignal` es one-shot IRREVERSIBLE; `RESUME` la contradice. Invención (¿UX BFF futura? = subsistema nuevo). |
| S19 | Cancelación en hooks (`signal` a Pre/PostToolUse hooks) | — | ❌ | El runtime no threadea `stop` a `HookRunner.run` (liga 06). |
| S20 | Ownership: nadie setea abort internamente (lo dispara el usuario/integrador) | igual — nadie setea `ctx.stop` en el runtime | ✅ | Comportamiento correcto: el disparo es externo (como HITL). |

**Recuento**: ✅3 · 🟡3 · 🔀4 · ❌14 · ⛔1 (25 filas; S15 doble marca 🔀/❌, contada 🔀). Las S21–S25
son features que la lectura íntegra de `StreamingToolExecutor.ts`/`toolExecution.ts` reveló y que el grep inicial había
omitido — la razón por la que este subsistema pasó de ~8 a 14 ❌.

## Hallazgos

- **FIND-SIG1** (❌ CRÍTICO, arquitectura — código muerto): `SignalBus`/`SignalType`/`SignalHandle` es una
  **abstracción HUÉRFANA**. Implementa un árbol de cascada `ABORT/PAUSE/RESUME`, pero **ninguna ruta la consulta** —
  el loop, el dispatcher y el fork miran `ctx.stop`, nunca el bus; sólo lo tocan sus propios tests. Hermano de
  **FIND-MODE1** (`modes/`) y **FIND-EXEC4** (`observer/`). **Agravante detectado en la lectura íntegra**: el canónico
  NO tiene un único árbol de cascada — tiene **dos mecanismos distintos** (árbol de `AbortController` para tools/subquery
  del mismo turno · kill de tasks `killAllRunningAgentTasks`+`emitTaskTerminatedSdk` para agentes en background). El
  `SignalBus` los **conflaciona** en una sola cascada `send(cascade=True)`, y encima está desconectado de ambos.
  **Ajuste**: ELIMINAR `SignalBus` (recomendado) y (a) hacer que `ctx.stop` crezca a la primitiva in-turn completa
  (reason + árbol direccional, SIG2/SIG3), y (b) dejar la cascada a agentes background donde ya vive de facto — el
  registry de tasks (05). No fabricar un tercer canal que unifique lo que el canónico separa a propósito.

- **FIND-SIG2** (❌ semántica/correctitud): `ctx.stop` (`asyncio.Event`) es **binario, sin `reason`**. El canónico
  usa `AbortSignal.reason` (`'interrupt'` submit-interrupt · `'sibling_error'` · user) para decidir comportamiento —
  p. ej. **omitir** `createUserInterruptionMessage` cuando `reason==='interrupt'` (query.ts:1046,1501), porque el
  mensaje de usuario encolado ya da contexto. El runtime no puede distinguir → o siempre emite o nunca. **Ajuste**:
  la primitiva de abort debe portar un `reason` (enum/str). Liga S10.

- **FIND-SIG3** (🔀→❌ direccionalidad): `fork.propagate_abort=True` comparte el **MISMO objeto** `asyncio.Event`
  entre padre e hijo (`fork/__init__.py:81`); `False` los aísla del todo. Un objeto compartido **no tiene
  direccionalidad**: si el hijo hiciera `stop.set()` (p. ej. su propia tool aborta) **abortaría también al padre** —
  VIOLA la invariante canónica (`createChildAbortController`: padre→hijo SÍ, hijo→padre NO, salvo el bubble explícito
  de rechazo de permiso). Hoy es inocuo (nadie setea `stop` en el hijo), pero es incorrecto en cuanto exista un setter
  interno. **Ajuste**: portar `createChildAbortController` (derivación unidireccional + WeakRef GC-safe + fast-path
  padre-ya-abortado). **FIND-SIG3b**: falta la capa `siblingAbortController`/`toolAbortController` de
  `StreamingToolExecutor` (cancelación de tools en vuelo, `sibling_error` sólo desde Bash, bubble del rechazo de
  permiso) → el dispatcher del runtime no aborta subprocesos ya lanzados.

- **FIND-SIG4** (❌): sin `interruptBehavior()` per-tool (`'cancel'`/`'block'`). El canónico, ante interrupción de
  usuario, **NO aborta** las tools `'block'` (StreamingToolExecutor.ts:221-233); el runtime corta cualquier tool en
  `dispatcher.py:54`. **Ajuste**: añadir `interrupt_behavior` al `ToolProtocol` y consultarlo antes de abortar.

- **FIND-SIG5** (❌ código muerto): `SignalBus.register_handler` (bus.py:89-96) almacena handlers en `_handlers` pero
  `send()`/`_apply()` **nunca invocan `handle_signal`** → extension point muerto; el `SignalHandler` Protocol
  (protocols.py:11) no lo usa nadie. Hermano de FIND-HOOK2 (eventos que no se disparan). **Ajuste**: si se conserva
  el bus, `send()` debe await-ear los handlers; si se elimina (recomendado con SIG1), cae con él.

- **FIND-SIG6** (🔀 invención mal ubicada): `SignalType.PAUSE`/`RESUME` sobre el signal de cancelación no tienen
  contraparte — `AbortSignal` es **one-shot irreversible** (el fast-path de `createChildAbortController` lo asume) y
  `RESUME`, que **limpia** la señal (bus.py:68-69), contradice esa irreversibilidad. **Matiz de la lectura íntegra**:
  la pausa SÍ existe en el canónico, pero a nivel de **lifecycle de task** (`Task.ts:53 totalPausedMs`, contabilidad de
  tiempo pausado en backgrounding), no como estado del abort. **Ajuste**: separar `ABORT` (irreversible, en la primitiva
  de cancelación) de la pausa (que, si se quiere, va en el lifecycle de task — 04/05 backgrounding — con `totalPausedMs`
  como espejo), NO en `signals/`.

- **FIND-SIG10** (❌): `ToolResult.aborted` produce un string plano `"aborted: {name}"`. El canónico emite **tres**
  mensajes sintéticos distintos, todos con `tool_use_id` y `withMemoryCorrectionHint`: `CANCEL_MESSAGE` (abort pre-exec,
  toolExecution.ts:443), `REJECT_MESSAGE` (rechazo de permiso, StreamingToolExecutor:160), y "Cancelled: parallel tool
  call … errored" (sibling_error). **Ajuste**: `ToolResult.aborted` debe portar la razón y renderizar el mensaje
  correcto (interrupción vs rechazo vs sibling) con hint de corrección de memoria.

- **FIND-SIG11** (❌): el canónico computa `setHasInterruptibleToolInProgress` = TODAS las tools en vuelo son
  `interruptBehavior()==='cancel'` (StreamingToolExecutor:254-260) → señal que gobierna si Ctrl+C puede interrumpir el
  turno. El runtime no la computa ni la expone (liga FIND-SIG4). **Ajuste**: derivarla del `interrupt_behavior` de las
  tools activas y exponerla en el ctx/eventos (liga 07·session_state_changed FIND-EVT7).

- **FIND-SIG13** (❌, granularidad — detectado en la re-auditoría de 04·modes): un task del canónico tiene DOS abort
  controllers con alcances distintos — `currentWorkAbortController` (aborta SOLO el turno actual; el agente sigue vivo,
  lo que habilita `SendMessage`-continue) vs `abortController` (mata el agente entero). Referencia:
  `useBackgroundTaskNavigation.ts:156-158` (Escape sobre teammate running → aborta el turno, NO mata). El runtime tiene
  un único `ctx.stop`/`SignalType.ABORT` de un solo nivel → no distingue "para el turno" de "mata el agente".
  **Ajuste**: dos niveles de cancelación (turn-abort vs task-kill); liga 05·GAP-EXEC3 (resume/continue) y
  `TaskStopTool`/`emitTaskTerminatedSdk('stopped')`. (Aunque el fichero es ⛔ swarm, la granularidad aplica a subagentes.)

- **FIND-SIG12** (❌, concreta GAP-SIG2): en el canónico, un fallo de tool por abort se marca `isInterrupt = error
  instanceof AbortError` y se **pasa a `runPostToolUseFailureHooks`** (toolExecution.ts:1694-1707); además `AbortError`
  NO se loguea como `tengu_tool_use_error`. El runtime ni threadea `stop` a los hooks ni distingue abort de error real.
  **Ajuste**: propagar `stop`/reason a `HookRunner.run` y marcar el fallo-por-abort (liga 06).

- **FIND-SIG7** (🟡 invariante, familia FIND-L1): en abort mid-turn el canónico **genera tool_results sintéticos**
  para todo `tool_use` pendiente (`getRemainingResults`/`yieldMissingToolResultBlocks`/`CANCEL_MESSAGE`) — invariante
  API `tool_use↔tool_result`. En el runtime el pairing SE MANTIENE mientras el corte sea a nivel de dispatch (cada
  tool devuelve `ToolResult.aborted`), pero: (a) el check de `agent_loop.py:186` rompe al TOPE del turno; (b) si
  `stop` se setea **mid-stream** con `tool_calls` parciales, no está verificado que cada `tool_use` reciba su
  resultado. **Ajuste**: verificar/forzar el pairing sintético en la ruta de abort (mismo motor que FIND-L1/EXEC2).

- **FIND-SIG8** (❌, liga 07·FIND-EVT1): el abort rompe el loop pero `run()→None` no surface un **resultado terminal
  tipado** (`{reason:'aborted_streaming'|'aborted_tools'}` del canónico). Sin `SDKResultMessage` no hay señal de
  cancelación observable aguas arriba (BFF/CCR). **Ajuste**: junto con FIND-EVT1, `run()` debe emitir un resultado
  terminal con `subtype`/reason de abort.

- **FIND-SIG9** (🔀/❌): cleanup on abort no portado. `cleanupComputerUseAfterTurn`/chicago MCP unhide+lock release =
  computerUse UI ⛔, pero el **patrón** "liberar locks/recursos al abortar mid-turn" (MCP, worktrees) sí es core.
  **Ajuste**: hook de cleanup en la ruta de abort (liga 06·Stop/SubagentStop y 11·mcp).

## Gaps

- **GAP-SIG1** (S13): sin `interrupt()` público en loop/runtime; el integrador setea `ctx.stop` a mano. Portar el
  espejo de `QueryEngine.interrupt()`.
- **GAP-SIG2** (S19): `stop`/abort no se threadea a `HookRunner.run` → los hooks no son abort-aware (liga 06).
- **GAP-SIG3** (S3/S4/S5): la primitiva de abort del runtime carece de `reason`, árbol direccional e
  `interruptBehavior` — los tres ejes que el canónico expresa con `AbortController`+`AbortSignal.reason`+`interruptBehavior()`.

## Cabos que aterrizan / relaciones

- **`ctx.stop` (cabo de 02/05)**: confirmado como la primitiva REAL de cancelación; homologa el `abortController` del
  canónico pero degradada (SIG2/SIG3/SIG4). El `fork.propagate_abort` es su cascada, pero por objeto compartido
  (SIG3), no por árbol de controllers.
- **SignalBus (08) vs EventBus (07) vs ctx.stop**: tres cosas distintas. EventBus = observación in-proc (07,
  documentado). `ctx.stop` = cancelación real. SignalBus = árbol de cascada HUÉRFANO (SIG1). El canónico unifica
  observación en el stream `SDKMessage` y cancelación en `AbortSignal`; el runtime las tiene separadas, con SignalBus
  como tercer canal muerto.
- **FIND-L1 / FIND-EXEC2** (pairing tool_use↔tool_result): reaparece en la ruta de abort (SIG7).
- **FIND-EVT1** (usage/resultado terminal): el abort necesita un `SDKResultMessage`-equivalente (SIG8).
- **FIND-MODE1 / FIND-EXEC4**: SIG1 es el tercer huérfano del mismo patrón — recomendación coherente: eliminar los
  tres o cablearlos, no dejar abstracciones muertas.

## Estado

**DOCUMENTADO** (1ª pasada, sin ajustes al código del runtime) · **VALIDADO 2ª vuelta con gate 11 (2026-07-19)**
— cada ✅/🔀 re-verificada abriendo el código de B (ver bloque "Re-visita de COMPLETITUD (gate 11 / L09)" abajo);
cero cambios de estado, 1 precisión de cableado (arming integrador vs standalone), código intacto. Evidencia:
`test_signals_homologation.py` (6 passed + 7 xfailed strict; los xfail codifican SIG1/2/3/4/5/6/10). Suite global
**582 passed·3 skipped·40 xfailed**. Lint verde (ruff/mypy/bandit).

**Nota de método**: la 1ª versión de este doc se apoyó en grep + ventanas de contexto para
`StreamingToolExecutor.ts`/`toolExecution.ts`/`useCancelRequest.ts` (superficialidad — corrección del usuario). Tras la
lectura ÍNTEGRA aparecieron S21–S25 y FIND-SIG10/11/12, y se corrigió la tesis (dos mecanismos de cascada, no uno; la
pausa vive en el lifecycle de task). Reconfirma la política: el grep ORIENTA, no sustituye la lectura completa.

---

## Plan de homologación / remediación desarrollada

Diseño por finding. Seams: `signals/protocols.py` (`SignalType{ABORT,PAUSE,RESUME}`, `SignalHandler`),
`signals/bus.py` (`SignalBus` árbol parent→children + `SignalHandle` + `register_handler` muerto),
`context/tool_use.py` (`ctx.stop: asyncio.Event`, el mecanismo REAL). **La homologación de 08 es del SEAM
de cancelación**: unificar los dos mecanismos en UNO con reason + árbol direccional + interruptBehavior.
El grueso se desarrolla en **`DEUDA-B-transversal.md §B-signals`** (`AbortScope`); aquí se ancla lo propio
de 08 y se DESARROLLAN los cabos que faltaban en Deuda B: **SIG9** (cleanup/lock-release on abort) y
**SIG13** (dos niveles currentWork/abort).

### SR1 · FIND-SIG1 + SIG5 + SIG6 — `SignalBus` huérfano → Deuda B (`B-signals`/`B-orphans`)
- **Decisión**: `SignalBus` no lo consulta ninguna ruta (sólo sus tests) y conflaciona dos cascadas (árbol
  de controllers in-turn vs kill de tasks); `register_handler` es código muerto (nunca se invoca
  `handle_signal`, protocols.py:11); PAUSE/RESUME está mal ubicada (la pausa canónica vive en el lifecycle
  de task, `totalPausedMs`, no en el signal — `AbortSignal` es irreversible). **Remediación**: borrar
  `SignalBus`/`SignalType`/`SignalHandle`/`SignalHandler` y **fusionar** en `AbortScope`
  (`DEUDA-B §B-signals`): `ctx.stop` crecido a `ctx.abort: AbortScope` con reason + árbol + `interrupt()`.
  La cascada de background queda en el registry (05·kill). **Test**: `test_no_orphan_signalbus_in_real_path`.

### SR2 · SIG2/3/4/10/11 — la primitiva única → Deuda B (`B-signals`)
- `reason` (SIG2), árbol child-abort direccional (SIG3, hoy el fork comparte el MISMO Event → hijo
  abortaría al padre), `interrupt_behavior` per-tool cancel/block (SIG4), `aborted` con reason+tool_use_id
  (SIG10), `has_interruptible_tool_in_progress` (SIG11) — todos son `AbortScope` en `DEUDA-B §B-signals`.
  Aquí se referencian; no se re-desarrollan.

### SR3 · SIG9 (NUEVO en Deuda B) — cleanup / liberación de recursos al abortar mid-turn
- **Comportamiento**: al abortar en medio de un turno, el canónico libera recursos
  (`cleanupComputerUseAfterTurn` ⛔; **MCP unhide + release de locks** = core). El runtime no tiene el
  gancho → un abort mid-turn puede dejar locks MCP tomados / recursos colgando.
- **Seam/firma**: `AbortScope` (Deuda B) expone `on_abort(callback)`; los subsistemas que toman recursos
  (11·mcp: locks/hide) registran un cleanup. Al `interrupt()`, el scope corre los callbacks en LIFO.
  Alternativa: el loop, en el path de abort, invoca un `ctx.on_turn_cleanup` list.
- **Cableado**: 11·mcp registra su release; el loop/dispatcher lo dispara al detectar abort. **Orden**: tras
  `AbortScope` (Deuda B) y junto a 11. **Test**: `test_abort_runs_cleanup_callbacks`.
- **Nota**: este finding NO estaba en el `DEUDA-B §B-signals` original → **se añade allí** como sub-ítem de
  `B-signals` (cerrando el hueco que la auditoría detectó).

### SR4 · SIG13 (NUEVO en Deuda B) — dos niveles de abort (`currentWork` vs `abort`)
- **Comportamiento**: un task canónico tiene DOS controllers — `currentWorkAbortController` (corta el TURNO
  pero el agente sigue vivo → puede recibir `SendMessage`-continue) vs `abortController` (mata al agente).
  El `ctx.stop`/`AbortScope` de UN nivel no modela esa granularidad → no se puede "interrumpir el trabajo
  actual sin matar al agente" (necesario para 05·EXEC12 pendingMessages + `TaskStop`).
- **Seam/firma**: `AbortScope` gana dos niveles: `AbortScope.work` (turno) y `AbortScope.agent` (vida). El
  loop chequea `abort.work.is_aborted()` para cortar el turno; el registry `kill` usa `abort.agent`.
  `interrupt(level="work"|"agent", reason=...)`.
- **Cableado**: loop (chequeos 173/186 pasan a `abort.work`), registry.kill (`abort.agent`), 05·EXEC12
  (drain pendingMessages tras `work`-abort sin matar). **Orden**: junto a `B-signals` + 05·ExR6. **Test**:
  `test_work_abort_keeps_agent_alive`.
- **Nota**: también se **añade** a `DEUDA-B §B-signals` como sub-ítem (cerraba el hueco de la auditoría).

### SR5 · SIG7/SIG8 — cabos a otro subsistema (referencia)
- **SIG7 pairing tool_use↔tool_result en abort** = familia 02·FIND-L1 → helper compartido de 02·LR5.
- **SIG8 resultado terminal 'aborted_*'** → 07·EvR4 (`ResultEvent` con subtype) + `B-usage`.
- **SIG12 distinguir abort de error en PostToolUseFailure** → 06·HR2 (el hook recibe `is_interrupt`).

---

## Re-visita de COMPLETITUD (gate 11 / L09) · 2ª vuelta · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** (cada fila ✅/🔀 re-verificada abriendo el código de B y siguiendo el dato
de punta a punta, no la tabla; las ❌ convergen por lectura directa). **Resultado**: la tesis (canónico =
`AbortController`/`AbortSignal` DENTRO del `ToolUseContext` + `reason` + one-shot; DOS cascadas separadas; el
runtime tiene `ctx.stop` REAL degradado + `SignalBus` HUÉRFANO) y **todas** las filas ✅/🔀 **se sostienen
sobre base correcta**; **1 precisión de cableado** (el arming de `ctx.stop` es del integrador, no del ensamblador
standalone — hermana de `stream()` 07 / `HookRunner` 06); **cero cambios de estado** (✅3·🟡3·🔀4·❌14·⛔1
intactos); **código intacto**; tests no re-ejecutados (sin cambio de código); **sin costuras latentes NUEVAS**
(el `SignalBus` entero YA es la costura huérfana, FIND-SIG1).

### Mini-ledger de consumidores (✅/🔀 seguidos punta a punta en B)
| Fila | Estado | Consumidor real abierto en B | Veredicto |
|---|---|---|---|
| S1 | 🟡 | `context/tool_use.py:47` (`stop: asyncio.Event\|None`) | Existe en el ctx, binario sin reason — degradado confirmado. |
| S2 | ✅ | `loop/agent_loop.py:227` (`complete_kwargs={"stop": ctx.stop,…}`, **incondicional**) → `models/caller.py:188-190` (`replace(opts, signal=stop)` si `stop is not None`) → `agentic_models.StreamOptions.signal` | Plumbing cableado en la ruta real del loop. ✅. |
| S6 | ✅ | `loop/agent_loop.py:173` (`return` pre-turno) + `:186` (`break` por turno), ambos `if ctx.stop and ctx.stop.is_set()` | Homologa `query.ts:1015` a nivel de turno. ✅. |
| S7 | 🟡 | `tools/dispatcher.py:54-55` (`if ctx.stop and ctx.stop.is_set(): return ToolResult.aborted(name)`) | Corta pre-exec; falta cascada en-vuelo (S8). 🟡. |
| S9 | 🟡 | `agent_loop.py:319-323` (parea `role:"tool"` por `call_id` 1-a-1 por cada `tool_call`) | Pairing a nivel dispatch; mid-stream sin verificar (FIND-SIG7). 🟡. |
| S12 | 🔀 | `caller.py:188-190` delega el corte a `agentic_models.StreamOptions.signal` | Seam delegado; verificación fina del corte HTTP + error tipado = 16. 🔀. |
| S16 | 🔀 | `signals/bus.py` (`SignalBus` completo) | **HUÉRFANO** — grep repo-wide: importado SÓLO por `tests/test_signal_bus.py` + `test_signals_homologation.py` (+ 1 comentario en `test_runtime_e2e.py`); **cero producción**. FIND-SIG1 confirmado por cableado. 🔀. |
| S18 | 🔀 | `signals/bus.py:68-69` (`if signal == SignalType.RESUME: node.signal = None`) | `RESUME` limpia la señal → contradice la irreversibilidad del abort; invención mal ubicada (FIND-SIG6). 🔀. |
| S20 | ✅ | grep `\.set()` / `\.stop\.set` en prod (excl. tests) = **0** | Nadie dispara `ctx.stop` internamente; disparo 100% externo (integrador/HITL). ✅. |

**❌ convergen por lectura directa de B** (ausencia = ausencia): S3 (`asyncio.Event` binario, sin `reason`),
S4/FIND-SIG3 (`fork/__init__.py:80-83`: `propagate_abort=True`→`stop=parent_stop` = **MISMO objeto**; `False`→
`asyncio.Event()` fresco — sin direccionalidad), S5/FIND-SIG4 (`tools/protocol.py:51-61` `ToolProtocol` sin
`interrupt_behavior`), S8/FIND-SIG3b (dispatcher corta pre-exec, sin `siblingAbortController`/`toolAbortController`),
S10/FIND-SIG10 (`tools/protocol.py:47-48` `aborted` = string plano `f"aborted: {name}"`), S11/S22/S23/S24/S25
(sin `has_interruptible_tool_in_progress`, sin tracking de IDs en vuelo, sin `discard`, sin `isInterrupt` a hooks),
S13/GAP-SIG1 (sin `interrupt()` público en loop/runtime), S17/FIND-SIG5 (`signals/bus.py:89-96` `register_handler`
guarda en `_handlers` pero `send()`/`_apply()` **nunca invocan `handle_signal`** — extension point muerto),
S19/GAP-SIG2 (`agent_loop.py:301-306` payload de `PRE_TOOL_USE` sin `stop`/reason → hooks no abort-aware).

### PRECISIÓN DE CABLEADO (el arming de `ctx.stop` es del integrador, no del ensamblador standalone)
El plumbing de `ctx.stop` (S2/S6/S7) es real e **incondicional** en el loop, PERO **ningún path de producción del
runtime standalone lo ARMA con un `asyncio.Event` vivo**:
- **Root**: `execution/local/runtime.py:210` (`_build_child`) construye `ToolUseContext(session_id,user_id,agent_id)`
  **sin `stop=`** → `ctx.stop` queda `None` (default `tool_use.py:47`).
- **Fork**: `execution/local/runtime.py:201` llama `RuntimeContextForker().fork(ForkContext(...))` **sin
  `parent_stop`** → con `propagate_abort=True` (default) el hijo recibe `stop = parent_stop = None`
  (`fork/__init__.py:80-81`). La tool Agent (`tools/native/agent.py:89-105`) arma el `ForkContext(propagate_abort=
  True)` pero **tampoco** threadea un `parent_stop` (y su `get_runner()` es FIND-EXEC1, ya roto/05).
- **Seams de arming del integrador SÍ existen** (dos): `execution/local/runtime.py:329-330`
  (`root_context_modifier(ctx, task)` — autoría per-request del ctx raíz, default `None`, puede sembrar `ctx.stop`)
  y `context/adapters.py:11-48` (`tool_use_context_from_session(*, stop: asyncio.Event | None = None, …)` →
  `ToolUseContext(…, stop=stop)`, línea 15→44). Solo los tests arman `stop=asyncio.Event()`.

**Alcance de la latencia — NO es "no hay cancelación"** (corrección de honestidad, leyendo `_run_loop`
runtime.py:306-416 1→EOF): la cancelación de **task** SÍ funciona en el standalone, por **otra vía** que
`ctx.stop` — `runtime.cancel(task_id)`→`registry.kill`→`asyncio_task.cancel()`→**`asyncio.CancelledError`**
capturado en `runtime.py:381-384` → `kill`+`_fire_stop`(SubagentStop)+`_notify`. Es el homólogo del **kill de
tasks** canónico (`killAllRunningAgentTasks`+`emitTaskTerminatedSdk`), el **nivel "agent-kill"** de FIND-SIG13
(ya visto en 02·G5). ⇒ Lo latente-en-standalone es **solo `ctx.stop`** (la señal cooperativa **in-turn**: checks
173/186, threading 227, dispatcher 54, `replace(signal=stop)` en caller), **NO** la cancelación de task. Coincide
EXACTO con la tesis de las DOS cascadas: el runtime tiene la de **kill de tasks** cableada y funcionando
(CancelledError), y le falta ARMAR la de **árbol in-turn** (`ctx.stop`) en el standalone. El `ctx.stop` in-turn es
**costura de consumo del integrador por diseño** (hermana de `stream()`/`subscribe_all` de 07 y `HookRunner`/
`register` de 06), **NO** un huérfano tipo `SignalBus`/`observer/`, **NO** bug, y **NO** deuda A-vs-B (el
`abortController` canónico también se arma externamente — UI `useCancelRequest`). **Refuerza S20 ✅** (disparo
externo) y **afina la tesis**: el plumbing in-turn está homologado pero el standalone no lo arma (mientras el
kill-de-task sí opera). **Corolario sobre FIND-SIG3**: el peligro
"objeto compartido → hijo aborta al padre" es hoy **doblemente inocuo** — no solo nadie setea `stop` en el hijo,
sino que en prod el fork ni recibe un `parent_stop` vivo (queda `None`); el riesgo solo se materializa cuando el
integrador threadee un `parent_stop` real Y exista un setter en el hijo. El estado ❌ de S4 se sostiene (la
API `fork(parent_stop=…)` comparte el objeto cuando se usa, como prueban `test_fork_primitives.py:198-206`).

### Ledger de lectura — 2ª vuelta (gate 11)
**B (runtime) — leído 1→EOF esta vuelta:**
| Archivo | LOC | Lectura |
|---|---|---|
| `signals/bus.py` | 96 | íntegro (el más grande de `signals/`, L08) |
| `signals/protocols.py` | 14 | íntegro |
| `signals/__init__.py` | 4 | íntegro |
| `context/tool_use.py` | 70 | íntegro (`stop` field 47) |
| `loop/agent_loop.py` | 352 | íntegro 1→EOF (checks 173/186, threading 227, pairing 319-323) |
| `models/caller.py` | 245 | íntegro (`complete(stop=)` 146-159, `replace(signal=stop)` 188-190) |
| `models/protocol.py` | 37 | íntegro (`stop` en `ModelRequest` 17 + `complete` 33) |
| `tools/dispatcher.py` | 84 | íntegro (abort check 54) |
| `tools/protocol.py` | 61 | íntegro (`ToolResult.aborted` 47-48; `ToolProtocol` sin `interrupt_behavior` 51-61) |
| `execution/fork/__init__.py` | 96 | íntegro (`propagate_abort` 80-83, `parent_stop` 67) |
| `execution/local/runtime.py` | 435 | **íntegro 1→EOF esta vuelta** (1-129 init/seams, 130-259 dispatch/stream/cancel/_build_child, 260-435 _make_bus/_fire_stop/_notify/**_run_loop 306-416**/_persist) — el `_run_loop` destapó la vía de cancelación real por `CancelledError` 381-384 |
| `context/adapters.py` | 86 | íntegro (seam de arming `stop=` 15/44) |
| `tools/native/agent.py` | 119 | tramos: fork build 78-105 (ya íntegro en 05) |

+ **grep de completitud por símbolo** (`SignalBus`/`SignalType`/`SignalHandle`/`SignalHandler` prod-vs-test = solo
tests; `\.set()`/`stop.set` en prod = 0; `.fork(`/`parent_stop` en prod = solo `runtime.py:201` sin `parent_stop`).

**A (canónico) — releído por anclas** (ya íntegros en 1ª vuelta, L08; SIGUIENTE: "releer anclas, no re-derivar"):
`utils/abortController.ts` (99, direccionalidad padre→hijo), `StreamingToolExecutor.ts` (530, árbol
sibling/toolAbortController + 3 razones + 3 sintéticos + interruptibleState), `toolExecution.ts` (tramos abort
400-469/1615-1714), `useCancelRequest.ts` (276, escalera de disparo + killAllAgents), `Task.ts` (125,
`abortController` por task + `totalPausedMs`), `Tool.ts:180/201/416` (`abortController`/`signal`/`interruptBehavior`),
`query.ts:1015/1046/1485/1501` (checks + `reason!=='interrupt'`).

### §Nota de honestidad
- La 1ª ronda de esta 2ª vuelta NO existía (08 se cierra directo con gate 11 de entrada). La **1ª pasada** (1ª
  vuelta) fue la categoría genuinamente superficial (grep+ventanas → lectura íntegra añadió S21-25/SIG10-12); esta
  re-visita **abrió el código de B** para cada ✅/🔀 y lo siguió punta a punta — no confirmación-de-doc.
- **Precisión añadida sobre la 1ª pasada**: el doc trataba "`ctx.stop` cableado end-to-end" y "`fork.propagate_abort`
  es su cascada" sin distinguir **plumbing** (real, incondicional en el loop) de **arming** (que el standalone NO
  hace para `ctx.stop`: `runtime.py:210/201` nunca puebla `stop`/`parent_stop`; los seams de arming del integrador
  son `root_context_modifier` runtime.py:329 y `adapters.py:15`). No es sobre-declaración de estado (S2/S6/S20
  siguen ✅ como homologación del SEAM), pero la 1ª redacción no lo hacía explícito. Corregido aquí, sin tocar la tabla.
- **Auto-corrección de honestidad (leer el ensamblador, no glosar)**: mi PRIMERA redacción de esta re-visita
  escribió "toda la maquinaria de abort está latente" — **imprecisión por no haber leído `_run_loop`
  (runtime.py:306-416) 1→EOF en el 1er intento**. Al leerlo apareció que la cancelación de **task** SÍ opera vía
  `CancelledError` (381-384, kill de tasks); lo latente-en-standalone es SOLO `ctx.stop` (in-turn). Corregido antes
  de cerrar (L00: leer el ensamblador 1→EOF es necesario; glosar `_build_child` sin `_run_loop` era el atajo).
- **Sin costuras latentes NUEVAS** tipo `to_llm`/`timeout_seconds` (01) / LAT-EXEC1-2 (05) / LAT-HOOK1 (06): el
  `SignalBus` completo (con `register_handler` muerto) YA es la costura huérfana registrada (FIND-SIG1/SIG5); el
  `parent_stop`-no-threadeado es **delegación por diseño** (no huérfano, no deuda A-vs-B, anti-padding L10).
- Los 3 huérfanos del mismo patrón (`SignalBus`/`modes/`/`observer/`) siguen coherentes → Deuda B `B-orphans`.

### 4 preguntas de cierre (2ª vuelta)
1. **¿Se revisó todo A?** Sí — anclas de las contrapartes canónicas (ya íntegras 1→EOF en 1ª vuelta) re-confirmadas;
   no se re-derivó (per SIGUIENTE). Convergencia de las ❌ verificada.
2. **¿Se revisó todo B?** Sí — `signals/` íntegro + los consumidores reales de `ctx.stop` (loop/caller/dispatcher/
   fork/adapters) abiertos y seguidos punta a punta 1→EOF + grep de completitud prod-vs-test.
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí — cada ✅/🔀 verificada por cableado (mini-ledger), no por la
   tabla; 1 precisión de cableado destapada (arming integrador vs standalone) que la 1ª redacción no explicitaba.
4. **¿Nada pendiente?** Sí — sin discrepancia de estado; sin costura latente nueva; los cabos (SIG7→02·LR5,
   SIG8→07·EvR4, SIG12→06·HR2, SIG13→05·EXEC12, primitiva→Deuda B `B-signals`, huérfanos→`B-orphans`) ya homed.

**VEREDICTO DE AVANCE: ✅ NADA PENDIENTE → avanzar a 09 · tools-infra** (gate 11). 01→08 completos con gate 11;
NO quedan pendientes de verificación de la 2ª vuelta. En 09 (1ª pasada: ✅~9·🟡~14·🔀~16·❌~18·⛔~6; tesis "el
canónico NO reifica una capa `tools/` — el protocolo es el tipo estructural `Tool`; el runtime REIFICA cada rol
ToolProtocol/Registry/Pool/Dispatcher"): aplicar gate 11 a cada ✅/🔀 abriendo el consumidor real en B. Foco en
**FIND-TOOL1** (dispatcher SECUENCIAL, sin `isConcurrencySafe` — cazar si algo lo cablea), **FIND-TOOL10**
(`NativeToolRegistry` hot-plug-MCP sin usar por factory — hermano de los huérfanos: confirmar prod-vs-test),
**FIND-TOOL6/7** (ToolSearch select multi + delta parseado de reminders — seguir el dato). Archivo más grande A =
`utils/permissions/filesystem.ts` (1778, L08) — releer anclas de path-guards (ya íntegro en 1ª pasada). B: los 12
archivos infra + cableado loop `agent_loop.py:85-234` + `native/tool_search.py`.
