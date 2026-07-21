# 05 · execution

> **RE-AUDITORÍA 2026-07-12 (parte del mandato 04→07).** Contrapartes reabiertas
> ÍNTEGRAS (AgentTool.tsx 1397 · runAgent.ts 973 · agentToolUtils.ts 686 ·
> loadAgentsDir.ts 755 · forkSubagent.ts 210 · Task.ts · tasks.ts · types.ts ·
> stopTask.ts · LocalAgentTask.tsx 682 · prompt.ts 287 · agentSummary.ts 179) +
> runtime íntegro. **Veredicto: el doc original era mayormente fiable** — E1-E32 y
> FIND-EXEC1-5/8 + GAP-EXEC1-7 se verificaron línea a línea contra el código (no fue
> superficial como 08). Pero la lectura íntegra destapó **4 findings nuevos**
> (FIND-EXEC9/10/11/12), **1 corrección** (`initialPrompt` mal clasificado) y varios
> enriquecimientos (algoritmo de permisos E20, shape de `usage` G2, trailer E18/E19).
> Sin fuga `</content>`. Ver §Re-auditoría al final.

**Fase:** VALIDADA en 2ª vuelta con **gate 11 / L09** de ENTRADA · 2026-07-19 (ver §Re-visita de COMPLETITUD al
final: ✅/🔀 sostenidos abriendo B; +LAT-EXEC1/2 tech-debt B-interno; código intacto). Base: documentación
(1ª pasada) + re-audit 2026-07-12, sin ajustes al código del runtime.
**Runtime:** `src/agentic_runtime/execution/` (1132 LOC):
- `session/{session.py, protocol.py, __init__.py}` — `Session`, `SessionMetadata`, `Usage`,
  `BackgroundTaskRef`, `RuntimeSessionProtocol`.
- `agents.py` — `AgentDefinition` (mínima), `AgentDefinitionResolver`, `resolve_subagent_model`, `INHERIT`.
- `runner.py` — `SubagentRunnerProtocol`, `get_runner`/`set_runner`.
- `fork/__init__.py` — `ForkPolicy`, `ForkSnapshot`, `ForkContext`, `RuntimeContextForker`.
- `local/runtime.py` — `LocalAgentRuntime` (el motor; dispatch/stream/status/cancel/result, `_run_loop`).
- `local/notification.py` — `BackgroundNotification`, `put/drain/process_background_notification`.
- `local/summarizer.py` — `summarize_if_needed` (condensación del resultado FINAL antes de inyectarlo al padre).
- `tasks/registry.py` — `TaskRecord`, `TaskRegistryProtocol`, `InMemoryTaskRegistry`, `get/set_registry`.
- `tasks/status.py` — `TaskStatus`.
- `observer/{observer.py, events.py, __init__.py}` — `ExecutionObserverProtocol`, `SubagentStarted/Stopped`,
  `NoopObserver`, `get/set_observer`.

Contrato despachado: `contracts/runtime.py::RuntimeTask` (+ `AgentRuntime` Protocol).
Consumidor de subagentes: `tools/native/agent.py::AgentTool` (→ `get_runner().run(fork_ctx, background)`).

**Contrapartes canónicas (leídas ÍNTEGRAS, no por hitos):**
- `Task.ts` (125) — `TaskType` (7 tipos), `TaskStatus` (5), `isTerminalTaskStatus`, `generateTaskId`
  (prefijo por tipo + `randomBytes` 36⁸), `createTaskStateBase` (`outputFile`, `outputOffset`, `notified`),
  interfaz `Task { kill(taskId, setAppState) }` (dispatch polimórfico por tipo).
- `tasks.ts` (39) — `getAllTasks`/`getTaskByType` (registro de implementaciones por tipo).
- `tasks/types.ts` (46) — unión `TaskState`, `isBackgroundTask` (running/pending ∧ `isBackgrounded !== false`).
- `tasks/stopTask.ts` (100) — `stopTask` compartido (TaskStop + SDK), `StopTaskError`
  (`not_found`/`not_running`/`unsupported_type`), supresión `notified`, `emitTaskTerminatedSdk`.
- `tools/AgentTool/`:
  - `AgentTool.tsx` (1397) — `call()`: routing (teammate/remote/fork/normal), depth guard vía tag de fork
    (`isInForkChild`), decisión sync/async (`forceAsync`/`background`/coordinator), worktree, `assembleToolPool`
    del worker, trailer de resultado (`agentId` + `<usage>`), `checkPermissions` (auto-mode → passthrough).
  - `runAgent.ts` (973) — motor síncrono del subagente: `filterIncompleteToolCalls`, clone de `readFileState`,
    `getUserContext`/`getSystemContext` (con `omitClaudeMd`/omit-gitStatus para Explore/Plan), threading de
    permissionMode, `initializeAgentMcpServers`, hooks/skills de frontmatter, `maxTurns`, `recordSidechainTranscript`
    + `writeAgentMetadata`.
  - `forkSubagent.ts` (210) — `FORK_AGENT` sintético (`tools:['*']`, `model:'inherit'`, `permissionMode:'bubble'`,
    `maxTurns:200`), `buildForkedMessages` (prefijo **byte-idéntico** para prompt-cache), `buildChildMessage`
    (directiva STOP/RULES), `isInForkChild` (guard de recursión), `buildWorktreeNotice`.
  - `agentToolUtils.ts` (686) — `resolveAgentTools`/`filterToolsForAgent` (allow/deny, `ASYNC_AGENT_ALLOWED_TOOLS`),
    `finalizeAgentTool` (fallback a text-blocks previos), `extractPartialResult`, `runAsyncAgentLifecycle`
    (driver background: stream→progreso→complete-first→classifyHandoff→worktree→`enqueueAgentNotification`),
    `classifyHandoffIfNeeded` (classifier de seguridad del handoff).
  - `loadAgentsDir.ts` (755) — forma completa de `AgentDefinition` (ver §AgentDefinition).
  - `prompt.ts` (287) — descripción de la tool Agent (listado de agentes, secciones fork/when-not-to-use).
  - `constants.ts` (12) — `AGENT_TOOL_NAME='Agent'`, `LEGACY_AGENT_TOOL_NAME='Task'`, `ONE_SHOT_BUILTIN` (Explore/Plan).
  - `builtInAgents.ts` (72) — catálogo host-provided ⛔ (en el runtime lo aporta `agent_resolver`).
- `tasks/LocalAgentTask/LocalAgentTask.tsx` (682) — `LocalAgentTaskState` (`isBackgrounded`, `retain`, `messages`),
  `enqueueAgentNotification` (+ dedup atómico `notified`), `kill`/`killAsyncAgent`, `registerAsyncAgent`/
  `registerAgentForeground`/`backgroundAgentTask`, `updateAgentProgress`/`updateAgentSummary`, `completeAgentTask`/
  `failAgentTask`. **Es el registry real de tasks de agente** (sobre `AppState.tasks`).
- `services/AgentSummary/agentSummary.ts` (179) — summary **periódico** (~30 s) de progreso para subagentes de
  coordinator, vía `runForkedAgent`. **Distinto** del `summarize_if_needed` del runtime (final-only).

**Descartes / delegaciones tras leerlos:**
- `utils/tasks.ts` (862) — **NO es el registry de ejecución**: es el sistema **TODO/tasklist**
  (`TASK_STATUSES = pending/in_progress/completed`, `createTask`/`claimTask`/`TeamMember`, `getTaskListId` por
  sesión). Mapea a **10** (`task_tools`/`todo_write`), no a `execution/tasks/registry.py`.
- `tasks/RemoteAgentTask/` (855), `teleportToRemote`, CCR — **18** (RemoteAgentRuntime `NotImplementedError`);
  homologación **de comportamiento**.
- `tasks/LocalShellTask/` (522+guards+kill) — bash background → **10**.
- `tasks/InProcessTeammateTask/`, `spawnTeammate`, teams, AgentSummary periódico — ⛔ coordinator/swarm (no gap).
- `tasks/DreamTask/`, `LocalWorkflowTask`, `MonitorMcpTask` — feature-gated, fuera de inventario core.
- `AgentTool/UI.tsx`, `agentDisplay.ts`, `agentColorManager.ts`, `pillLabel.ts` — ⛔ UI/terminal.
- `agentMemory.ts`, `agentMemorySnapshot.ts` — **13** (memory).
- `initializeAgentMcpServers` (MCP de frontmatter del agente) — **11**; hooks/skills de frontmatter — **06/12**;
  `thinkingConfig` — **16**.

---

## Naturaleza del subsistema

El canónico **no separa** "runtime de ejecución" de "tool que spawnea": `AgentTool.call()` ejecuta
`runAgent()`/`runAsyncAgentLifecycle()` **directamente**. El runtime, en cambio, factoriza la ejecución
en un **seam de tres piezas**: `AgentTool` (native) → `SubagentRunnerProtocol` (get_runner) →
`LocalAgentRuntime.dispatch`. Es un desacople legítimo (permite backends remote/local) **pero está roto en
producción** (FIND-EXEC1). Además, `Session` es una entidad nueva del runtime (el canónico es single-user sin
sesiones): su homologación es **de comportamiento** — debe reproducir lo que el canónico mantiene en `AppState`
por-turno, no la forma.

El eje **backgrounding** (mutable, `is_backgrounded`) y el **KIND** (fija el toolset) ya se documentaron en
03·E/B3 y 04. Aquí se contrasta el **ciclo de vida de ejecución** (spawn→stream→terminal→notificación→persistencia)
y el **fork**.

---

## Tabla feature-by-feature

| # | Feature (canónico) | Runtime | Estado | Nota |
|---|---|---|---|---|
| E1 | `TaskStatus` (pending/running/completed/failed/killed) + `isTerminalTaskStatus` | `tasks/status.py::TaskStatus` + `is_terminal` | ✅ | Paridad exacta. |
| E2 | `getAgentModel` (override > agente > herencia; `inherit` sentinel; nombre ≠ modelo) | `resolve_subagent_model` + `INHERIT` | ✅ | Precedencia idéntica (sin specifics Bedrock). |
| E3 | Snapshot inmutable del estado del padre al forkear | `ForkSnapshot` (frozen) | ✅ | Concepto homologado; **mejora**: añade `capabilities` (delegador MCP per-tenant). |
| E4 | Política de herencia del hijo (messages/permissions/tools/abort) | `ForkPolicy` + `RuntimeContextForker` | 🟡 | Flags ✅; pero `inherit_messages` **incompleto** → FIND-EXEC2. |
| E5 | Canal `<task-notification>` desacoplado del objeto Session del padre | `local/notification.py` (put/drain/process) | ✅ | **Mejora**: escopado por `(user_id, session_id)` — multi-usuario (el canónico es single-user). |
| E6 | complete-first, luego embellecer (notificación no bloquea la transición) | `_run_loop`: `registry.complete()` antes de `summarize`/`_notify` | ✅ | Análogo a `completeAsyncAgent` antes de handoff/worktree (gh-20236). |
| E7 | Persistencia de transcript del subagente | `_persist` → `StorageKeys.transcript_key(user, session, agent)` | 🟡 | Persiste transcript; **sin** `writeAgentMetadata` (agentType/worktree/description) ⇒ sin resume (GAP-EXEC3). |
| E8 | Tope de anidamiento de subagentes | `AgentTool._MAX_SUBAGENT_DEPTH=5` | ✅ | **Mejora**: tope de profundidad explícito (el canónico topa vía maxTurns/recursion-tag). |
| E9 | Registro de tasks de agente (AppState.tasks + LocalAgentTask) | `execution/tasks/registry.py` (`TaskRecord`/`InMemoryTaskRegistry`) | 🟡 | Estructura homologada; faltan `type` (GAP-EXEC2) y `notified` (GAP-EXEC1), `outputFile`/`outputOffset`. |
| E10 | `stopTask` compartido (TaskStop + SDK), `StopTaskError` con códigos | `registry.kill` + `cancel` | 🔀 | Kill genérico; sin códigos de error (`not_found`/`not_running`/`unsupported_type`) ni `emitTaskTerminatedSdk`. |
| E11 | Driver background (`runAsyncAgentLifecycle`): stream→progreso→terminal | `_run_loop` + `_make_bus` (push_event) | 🟡 | Progreso vía EventBus (tool_start/result); sin `emitTaskProgress` SDK, sin activity-resolver, sin `retain`/append de messages a AppState. |
| E12 | `filterIncompleteToolCalls` al heredar mensajes de fork | — | ❌ | **FIND-EXEC2**: invariante API tool_use↔tool_result no impuesto en el fork. |
| E13 | `buildForkedMessages` (prefijo byte-idéntico prompt-cache) + `buildChildMessage` (directiva) | — | ❌ | El fork del runtime hereda mensajes crudos; sin placeholder byte-idéntico ni directiva de fork. Liga GAP-CTX4 (`renderedSystemPrompt`). |
| E14 | `isInForkChild` (guard de recursión de fork por tag) | — | ❌ | Sin boilerplate-tag; el runtime topa por profundidad (E8), no por fork-en-fork. |
| E15 | `extractPartialResult` en la notificación de kill | `_notify(...,'killed','...',final_text='')` | ❌ | **FIND-EXEC3**: descarta el trabajo parcial pese a tener `ctx.messages`. |
| E16 | `maxTurns ?? agentDefinition.maxTurns` → `query()` | `AgentLoop` con `_MAX_TURNS=50` fijo | ❌ | **FIND-EXEC5**: `RuntimeTask.max_turns`/`ForkContext.max_turns` inertes; `AgentLoop.__init__` no acepta `max_turns`. |
| E17 | `finalizeAgentTool`: fallback a text-blocks de assistant previos | `_last_assistant_text` (último assistant, asume `content` str) | 🟡 | **FIND-EXEC8**: sin fallback si el último assistant es puro tool_use. Menor. |
| E18 | Trailer de resultado síncrono: `agentId` (SendMessage hint) + `<usage>` + marcador no-output; skip one-shot | `AgentTool` devuelve `output=result` | 🔀 | **GAP-EXEC7a**: sin usage/hint/marcador. `usage` lo consume el modelo padre ⇒ homologar. |
| E19 | Formato `<task-notification>`: `<task-id><tool-use-id><output-file><status><summary><result><usage><worktree>` | `process_background_notification`: attrs `task_id/status` + `<description><result>` | 🔀 | **GAP-EXEC7b**: faltan output-file/summary/usage/worktree; description vs summary. |
| E20 | Override de permissionMode del agente + scoping `allowedTools` (no fuga del padre) | Hijo hereda `snap.permissions` crudo | 🔀 | **GAP-EXEC6**: sin scoping ni override (bubble/plan/acceptEdits). Liga GAP-02. |
| E21 | Prepend user/system context al subagente (git status, CLAUDE.md, fecha) | system_prompt sólo de `agent_def.system_prompt` | 🟡 | **GAP-EXEC5** = cross-ref 03·GAP-CTX3 (prepend no portado). |
| E22 | `background:true` de la definición fuerza async | Async sólo por param `run_in_background` | 🟡 | **GAP-EXEC4**: `agent_def.background` no consultado. |
| E23 | Clone de `readFileState`/`FileStateCache` al forkear | — | ❌ | Cross-ref **FIND-CTX1** (el ctx no tiene readFileState). |
| E24 | Seam runner ↔ runtime cableado | `factory` no llama `set_runner()` | ❌ | **FIND-EXEC1** (crítico): AgentTool→`get_runner()` reventaría en prod. |
| E25 | Observabilidad de subagentes (updateAgentProgress/logEvent/emitTaskProgress) | `execution/observer/` | ❌ | **FIND-EXEC4**: `observer/` huérfano (nadie llama `on_subagent_*`); el eje real lo cubren EventBus + hook SUBAGENT_STOP. |
| E26 | Resume de subagente (`resumeAgent.ts` + SendMessage + metadata) | — | ❌ | **GAP-EXEC3**: no portado (depende de SendMessage tool [deferred] + writeAgentMetadata). |
| E27 | `classifyHandoffIfNeeded` (classifier de seguridad del output del subagente) | — | ❌ | Feature-gated; nota de seguridad (liga 06/permissions). |
| E28 | `AgentDefinition` completa (loadAgentsDir) | `AgentDefinition` (5 campos) | 🟡 | **GAP-EXEC4** (ver §AgentDefinition). |
| E29 | Summary **periódico** de progreso (AgentSummary, ~30 s, coordinator) | `summarize_if_needed` (final-only) | 🔀 | Propósito distinto; el periódico es coordinator ⛔. El final-only ✅ para su uso. |
| E30 | `Session` (behavior homolog; el canónico no tiene sesiones) | `execution/session/` | 🔀 | Deliberado/mejora: `Session`/`Usage`/`SessionMetadata` satisfacen `RuntimeSessionProtocol`. |
| E31 | `RemoteAgentTask`/CCR/teleport | `RemoteAgentRuntime` (futuro) | ❌ | → 18 (comportamiento). |
| E32 | `getTaskByType(type).kill()` (dispatch polimórfico por tipo) | kill genérico | 🔀 | Ligado a GAP-EXEC2; relevante al entrar bash-bg (10)/remote (18). |
| E33 | Promoción foreground→background de un subagente sync en vuelo (`registerAgentForeground`+`backgroundSignal`+`autoBackgroundMs` 120s+`backgroundAgentTask`) | Async sólo decidido en spawn; `is_backgrounded` mutable pero sin promoción | ❌ | **FIND-EXEC9** (re-audit). |
| E34 | `shouldRunAsync` multi-motor: `run_in_background‖background‖coordinator‖forceAsync(fork)‖assistantForceAsync(kairos)‖proactive` | AgentTool decide async sólo por `run_in_background` | 🔀 | **FIND-EXEC10** (re-audit): falta seam force-async del integrador assistant. |
| E35 | Cascada de limpieza al terminar el subagente (`killShellTasksForAgent`, libera `todos[agentId]`, `clearSessionHooks`, `mcpCleanup`, `killMonitorMcpTasksForAgent`) | `_run_loop` sin `finally` ni reaping por `agent_id` | ❌ | **FIND-EXEC11** (re-audit); aterriza en 10/11/12. |
| E36 | Inyección de mensajes a un local_agent VIVO (`pendingMessages`+`queue/drainPendingMessages`, drenados en límite de ronda) = SendMessage-continue | — | ❌ | **FIND-EXEC12** (re-audit); ≠ resume (GAP-EXEC3); aterriza FIND-SIG13 (dos abort controllers). |

**Recuento:** ✅8 · 🟡9 · 🔀9 · ❌9 (re-audit: +E34 🔀, +E33/E35/E36 ❌).

---

## AgentDefinition — subconjunto mínimo (GAP-EXEC4 / E28)

El runtime porta `{subagent_type, description, model, system_prompt, allowed_tools}`. La canónica
(`BaseAgentDefinition`) añade campos que **el motor de ejecución debe consumir** y otros delegados:

| Campo canónico | Dónde aterriza | Estado |
|---|---|---|
| `maxTurns` | execución (loop) | ❌ FIND-EXEC5 |
| `background` (force-async) | execución | 🟡 GAP-EXEC4/E22 |
| `disallowedTools` (resta) | execución (runtime sólo tiene allowlist) | ❌ |
| `permissionMode` | permisos | 🔀 GAP-02/E20 |
| `initialPrompt` (prepend al 1er turno) | **NO es de subagente** → entrypoint/persona de sesión | 🔀 (corr. re-audit) |
| `requiredMcpServers` / `mcpServers` | 11 | ⛔→11 |
| `skills` / `hooks` (frontmatter) | 12 / 06 | ⛔→12/06 |
| `effort` | 16 | ⛔→16 |
| `memory` | 13 | ⛔→13 |
| `isolation` (worktree/remote) | GAP-MODE2 / 10 / 18 | ❌ |
| `omitClaudeMd` / `criticalSystemReminder` | 03 (context) | ⛔→03 |
| `color` / `filename` / `baseDir` | UI | ⛔ |

**Ajuste arquitectural:** los de ejecución (`maxTurns`, `background`, `disallowedTools`, `permissionMode`)
deben poder consumirse por el motor (extender `AgentDefinition` + threadearlos en `_run_loop`/`AgentLoop`).
El resto se documenta como delegado; confirmar cobertura al documentar su subsistema.

**Corrección re-audit (`initialPrompt`):** el doc original lo listaba como gap ❌ de ejecución de
subagente. Es incorrecto — `initialPrompt` se consume **sólo** para el agente de main-thread
(`mainThreadAgentDefinition`) en el entrypoint (`main.tsx:2097`, `cli/print.ts:4417`: se antepone al
`inputPrompt` de la sesión), **nunca** en `runAgent` para subagentes spawneados. Es una feature de
**adopción de persona por la sesión** (la sesión entera corre como un agente), no del motor de ejecución de
subagentes. Para el subagente es 🔀: el canónico tampoco lo antepone. Homólogo en el integrador/entrypoint
(agentic_assistant, que SÍ tiene sesiones), no en `execution/`.

---

## Hallazgos (ajustes arquitecturales, NO parches)

- **FIND-EXEC1 (❌ crítico — seam roto).** `factory._build_local` nunca llama `set_runner()`; hay además
  desajuste de firma (`SubagentRunnerProtocol.run(fork_ctx: ForkContext, *, background)->str|None` vs
  `LocalAgentRuntime.dispatch(task: RuntimeTask, parent_snapshot, *, on_event)->str`). **Ajuste:** el factory
  construye un adaptador `ForkContext→RuntimeTask` (deriva `RuntimeTask` desde `fork_ctx.prompt`/`subagent_type`/
  `model_override`/`max_turns`, y `parent_snapshot` desde `fork_ctx.parent_snapshot`), implementa
  `SubagentRunnerProtocol.run` delegando a `dispatch` (background) o esperando el resultado (foreground vía
  `stream`/`result`), y llama `set_runner()`. Alternativa: AgentTool obtiene el runtime por `ctx`.
- **FIND-EXEC2 (❌ correctitud — fork sin filtrado).** `RuntimeContextForker.fork` copia `tuple(snap.messages)`
  crudo. **Ajuste:** al heredar mensajes, aplicar el equivalente de `filterIncompleteToolCalls` (eliminar
  assistant-msgs con `tool_use` sin `tool_result`) — misma familia que FIND-L1/`yieldMissingToolResultBlocks`.
  Extensión: portar `buildForkedMessages` (prefijo byte-idéntico) + directiva de fork (E13) si se adopta el
  modelo de fork implícito con prompt-cache.
- **FIND-EXEC3 (❌ pérdida de trabajo).** La rama `CancelledError` de `_run_loop` notifica `final_text=''`.
  **Ajuste:** rescatar `_last_assistant_text(ctx.messages)` (o `extractPartialResult`) y pasarlo como
  `notification_text`/`final_text` en el kill.
- **FIND-EXEC4 (❌ código muerto).** `execution/observer/` no lo invoca ninguna ruta. **Ajuste:** cablear
  (emitir `SubagentStarted` en `dispatch`, `SubagentStopped` en las ramas terminales de `_run_loop`) **o
  eliminar** — recomendado eliminar salvo que se quiera un canal de observabilidad separado del EventBus, que hoy
  ya cubre el eje (push_event) + hook SUBAGENT_STOP. Hermano de FIND-MODE1.
- **FIND-EXEC5 (❌ max_turns inerte).** `AgentLoop.__init__` no acepta `max_turns`; usa `_MAX_TURNS=50` fijo.
  **Ajuste:** añadir `max_turns` a `AgentLoop` (default 50) y threadear `task.max_turns` / `agent_def.maxTurns` /
  `fork.max_turns` desde `_run_loop`.
- **FIND-EXEC8 (🟡 menor).** `_last_assistant_text` sin fallback a text-blocks previos. **Ajuste:** replicar el
  retroceso de `finalizeAgentTool` cuando el último assistant es puro `tool_use`.
- **GAP-EXEC1 (❌ dedup).** `TaskRecord` sin `notified`. **Ajuste:** añadir flag y gatear `put_notification`
  (marcar atómicamente, como `enqueueAgentNotification`/`stopTask`) para evitar doble notificación.
- **GAP-EXEC2 (🔀 = GAP-MODE1).** `TaskRecord` sin discriminante `type`. **Ajuste:** añadir `TaskType` cuando
  entren bash-bg (10) / remote (18) / teammate; habilita dispatch polimórfico (E32) y prefijo de id.
- **GAP-EXEC3 (❌ resume).** Sin `resumeAgent`/`writeAgentMetadata`. **Ajuste:** subsistema de resume
  (persistir metadata de agente + reanudar con contexto vía SendMessage tool [deferred]). Depende de 10.
- **GAP-EXEC4 (🟡 AgentDefinition).** Ver §AgentDefinition.
- **GAP-EXEC5 (🟡 = 03·GAP-CTX3).** Prepend user/system context no llega al subagente.
- **GAP-EXEC6 (🔀 permisos).** Fuga de permisos del padre al hijo; sin override de permissionMode. Liga GAP-02.
- **GAP-EXEC7 (🔀 formato).** Trailer de resultado (a) y notificación (b) divergen; `usage`/`output-file` son
  señales que el modelo padre consume ⇒ homologar (no es sólo proyección del integrador).

**Cabos del enunciado resueltos aquí:**
- **AgentMode.FORK ⇒ execution/fork/**: el fork del runtime existe (E3/E4) pero es una herencia superficial de
  mensajes; le faltan las tres piezas del fork canónico (filtrado E12, prefijo byte-idéntico E13, guard E14).
- **FIND-MODE1**: la notificación incondicional vive en `_run_loop::_notify` (gateada sólo por
  `parent_session_id`). Confirmado que `modes/` no la gobierna; **recomendación: eliminar `modes/`** (y de paso
  `observer/`, FIND-EXEC4) — el eje real es `TaskRecord.is_backgrounded` + `is_subagent` + el canal de notificación.
- **GAP-MODE1**: = GAP-EXEC2 (discriminante de tipo en `TaskRecord`).
- **G2 maxBudgetUsd**: sigue ❌ y **bloqueado** por FIND-L2 (usage accounting: `DoneEvent.usage` no se propaga →
  `input_tokens/output_tokens` del `TaskRecord` llegan en 0) + coste por modelo (16). El cap de coste hosted no se
  puede implementar hasta que el accounting sea real. Prereq documentado, no resuelto en 05.
- **G3 structured output**: ❌; `SyntheticOutputTool`/`jsonSchema` no portados. → 09/16 (probable necesidad del BFF).
- **coordinator/swarm** ⛔ (no gap), confirmado.

---

## Re-auditoría (2026-07-12) — findings nuevos + enriquecimientos

**FIND-EXEC9 (❌ promoción foreground→background no modelada).** El canónico convierte un subagente
**síncrono** a background **a mitad de ejecución**: `registerAgentForeground` devuelve un `backgroundSignal`
(promise) + `autoBackgroundMs` (auto-bg tras 120s, env/GB); `AgentTool.tsx` corre `Promise.race(next-message,
background-signal)` y, al dispararse (usuario o timer), llama `agentIterator.return()`, sigue en un closure
`void runWithAgentContext(...)` detached, re-notifica vía `enqueueAgentNotification` y retorna `async_launched`.
El runtime decide async **sólo en el spawn** (`run_in_background`); `TaskRecord.is_backgrounded` es mutable
(`set_backgrounded`) pero no hay primitiva que interrumpa el `await` del padre, desenganche el loop y
re-notifique. **Distinto de E22/GAP-EXEC4** (que es `background:true` force-async en spawn). **Ajuste:** una
primitiva de promoción (señal de background + detach del stream + re-notificación), o declarar el modelo
binario spawn-time como divergencia deliberada del integrador. Liga 04·B (backgrounding de sesión) pero es
por-task.

**FIND-EXEC10 (🔀 seam force-async del integrador ausente).** `shouldRunAsync` del canónico se deriva de
**varios motores**, no del param: `run_in_background ‖ selectedAgent.background ‖ isCoordinator ‖
forceAsync(=isForkSubagentEnabled) ‖ assistantForceAsync(=appState.kairosEnabled) ‖ proactive`, gateado por
`!isBackgroundTasksDisabled`. **`assistantForceAsync` es directamente relevante a agentic_assistant**: en modo
assistant TODOS los subagentes se fuerzan async porque un subagente síncrono mantiene abierto el turno del
main-loop del daemon y atasca el `inputQueue`. El `AgentTool` del runtime decide async sólo por
`run_in_background`. **Ajuste:** un seam de política force-async que el integrador assistant fije (p.ej. en
`RuntimeConfig`/ctx), no un flag por-call.

**FIND-EXEC11 (❌ cascada de limpieza de recursos hijos al terminar el agente).** El `finally` de
`runAgent.ts` (816-859) reap-ea, al terminar el subagente (normal/abort/error), los recursos que **el
subagente spawneó**: `killShellTasksForAgent` (mata los bash `run_in_background` que lanzó — si no, quedan
zombies PPID=1), libera `AppState.todos[agentId]` (leak: cada subagente que llamó TodoWrite deja una clave),
`clearSessionHooks`, `mcpCleanup` (servers MCP inline del frontmatter), `cleanupAgentTracking`,
`killMonitorMcpTasksForAgent`. `_run_loop` del runtime **no tiene `finally`** ni reaping por `agent_id`. La
limpieza de MCP del runtime es a nivel-runtime (`capability_manager.shutdown`), no por-subagente. **Ajuste:**
`finally` en `_run_loop` que reap-ee los recursos por `agent_id` cuando entren bash-bg (10) / MCP de agente
(11) / skills (12). Es responsabilidad de **ejecución** (el agente es dueño de sus hijos), aunque los recursos
concretos vivan en otros subsistemas.

**FIND-EXEC12 (❌ inyección de mensajes a un subagente EN EJECUCIÓN).** `LocalAgentTaskState.pendingMessages`
+ `queuePendingMessage`/`drainPendingMessages` (drenados en los límites de ronda de tools) +
`appendMessageToLocalAgent`: un `local_agent` **vivo** recibe mensajes nuevos vía SendMessage, encolados y
consumidos entre rondas. Es el mecanismo **SendMessage-continue** y es **DISTINTO de GAP-EXEC3** (resume de un
agente ya TERMINADO vía `resumeAgent`+`writeAgentMetadata`). **Aterriza FIND-SIG13**: un task canónico tiene
DOS abort controllers — `currentWorkAbortController` (corta el turno actual; el agente **sobrevive** para
recibir SendMessage) vs `abortController` (mata el agente). `TaskRecord` no tiene cola `pending_messages` ni
ese doble nivel; `ctx.stop` (asyncio.Event) del runtime es un único nivel binario (08·SIG2/3). **Ajuste:**
cola `pending_messages` en `TaskRecord` + drenado en el límite de ronda del `AgentLoop`, y separar el abort de
turno del abort de agente (coordina con 08·GAP-SIG3 + GAP-EXEC3).

**Enriquecimientos (targets concretos de homologación descubiertos en la lectura íntegra):**
- **E20/GAP-EXEC6 (algoritmo de permisos del hijo).** `runAgent.ts::agentGetAppState` es el algoritmo canónico:
  (a) override de `permissionMode` del agente **salvo** que el padre sea `bypassPermissions`/`acceptEdits`/`auto`
  (esos ganan); (b) `shouldAvoidPermissionPrompts` — async ⇒ auto-deny (sin UI), `bubble` ⇒ siempre muestra
  (bubblea al padre), sync ⇒ muestra; (c) async+puede-mostrar ⇒ `awaitAutomatedChecksBeforeDialog`; (d)
  scoping `allowedTools`: **reemplaza** las reglas `session` pero **preserva** `cliArg` (anti-fuga del padre);
  (e) override de `effort`. Además el worker pool se ensambla con `mode: selectedAgent.permissionMode ??
  'acceptEdits'` (default del worker = `acceptEdits`). Ése es el target de GAP-EXEC6/GAP-02, no sólo "sin scoping".
- **G2 (shape de `usage`).** El accounting canónico es concreto: `AgentToolResult.usage` = usage completa de
  Anthropic (`input/output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `server_tool_use`,
  `service_tier`, `cache_creation.ephemeral_1h/5m_input_tokens`) tomada de `lastAssistantMessage.message.usage`;
  y `ProgressTracker` computa `latestInputTokens` (se **queda** con el último — es acumulativo en la API, incluye
  cache tokens) + `cumulativeOutputTokens` (se **suma**), `getTokenCountFromTracker = suma`. El runtime tiene
  `Session.usage={input:0,output:0}` y `TaskRecord.input/output_tokens=0` (FIND-EVT1/FIND-L2). Ése es el shape a
  homologar para desbloquear G2 maxBudgetUsd + coste/modelo (16).
- **E18/E19 (trailer).** Confirmado + matices: el resultado `async_launched` tiene su PROPIO mapeo (hint
  SendMessage + `output_file` + `canReadOutputFile` + guía "no dupliques el trabajo"); el `<usage>` de la
  `<task-notification>` XML usa sub-tags `<total_tokens><tool_uses><duration_ms>`; los one-shot builtins saltan
  el trailer sólo si no hay worktree; y la completación de un sync foreground emite un `task_notification` SDK
  (`enqueueSdkEvent`, distinto del canal del LLM-loop) → 07.
- **`filterToolsForAgent` (denylists).** Además de `ASYNC_AGENT_ALLOWED_TOOLS`: `ALL_AGENT_DISALLOWED_TOOLS`
  (todo agente), `CUSTOM_AGENT_DISALLOWED_TOOLS` (sólo no-builtin), `ExitPlanMode` permitido en `plan` mode,
  MCP siempre permitido → cruzar con 09/10 al documentar el pool.
- **`TaskStateBase` extra.** También `endTime` y `totalPausedMs` (la pausa vive en el lifecycle del task, no en
  el signal → confirma 08·SIG6).

---

## Evidencia

- `tests/test_execution_homologation.py`: **7 passed** (homologado: E1/E2/E4-defaults/E3/E5/E8 + smoke registry) +
  **11 xfailed(strict)** — original: FIND-EXEC1/2/3/4/5, GAP-EXEC1, GAP-EXEC2; **re-audit +4**:
  FIND-EXEC9 (promoción fg→bg), FIND-EXEC10 (seam force-async), FIND-EXEC11 (reaping de recursos hijos),
  FIND-EXEC12 (pendingMessages / SendMessage-a-agente-vivo). Los xfail codifican el gap: si el runtime lo
  homologa, el xfail-strict falla y obliga a revisitar el doc.
- Cobertura previa que toca 05: `test_fork_primitives.py`, `test_task_registry_list_all.py`,
  `test_task_registry_session_scope.py`, `test_modes_background.py`, `test_runtime_e2e*.py`.
- Suite global tras re-audit 05: **582 passed · 3 skipped · 44 xfailed**. Lint verde (ruff).

**Sin ajustes al código del runtime en esta pasada (paso 6 del DoD).**

---

## Plan de homologación / remediación desarrollada

Eleva los "Hallazgos (ajustes arquitecturales)" a diseño por finding. Seams: `execution/runner.py`
(`SubagentRunnerProtocol` + `set_runner`/`get_runner`), `execution/tasks/registry.py` (`TaskRecord` +
`TaskRegistryProtocol` + `set_registry`/`get_registry`), `execution/fork/__init__.py` (`ForkSnapshot`/
`ForkPolicy`/`ForkContext.build`), `execution/local/runtime.py` (`LocalAgentRuntime`), `loop/agent_loop.py`
(`_MAX_TURNS=50` fijo). Los cabos de permisos (GAP-EXEC6) y structured-output (G3) son **Deuda B**.

### ExR1 · FIND-EXEC1 (CRÍTICO) — seam runner sin cablear + mismatch de firma
- **Comportamiento**: la factory nunca llama `set_runner()`; `AgentTool → get_runner().run(fork_ctx,
  background=)` reventaría (RuntimeError "runner not initialized"), y hay mismatch: `run(fork_ctx,
  background)` vs `LocalAgentRuntime.dispatch(task, parent_snapshot)`. Falta el adaptador
  `ForkContext → RuntimeTask` que puentee `AgentTool ↔ LocalAgentRuntime`.
- **Seam/firma**: (a) `RuntimeFactory.create_runtime` llama `set_runner(adapter)` al ensamblar; (b) nuevo
  `execution/local/runner_adapter.py::LocalSubagentRunner(SubagentRunnerProtocol)` con `async def
  run(fork_ctx, *, background) -> str` que traduce `ForkContext → RuntimeTask` (prompt/subagent_type/
  model_override/max_turns/fork_context) y delega en `LocalAgentRuntime.dispatch(task,
  parent_snapshot=fork_ctx.snapshot, on_event=...)`.
- **Cableado**: factory (18) invoca `set_runner`; `AgentTool` sigue llamando `get_runner().run(...)`.
- **Orden**: **primero** de 05 (sin esto, spawnear subagente falla). **Test**:
  `test_agent_tool_spawns_via_wired_runner` (xfail existente).

### ExR2 · FIND-EXEC2 — fork con `inherit_messages` sin `filterIncompleteToolCalls`
- **Comportamiento**: `ForkContext.build` copia `tuple(snap.messages)` crudo (fork/__init__:73); si el
  padre tenía un `tool_use` sin su `tool_result`, el hijo arranca con un mensaje colgante → error de API
  (misma familia que 02·FIND-L1).
- **Seam/firma**: `ForkContext.build`, al materializar `messages` con `inherit_messages`, pasa por
  `filter_incomplete_tool_calls(messages)` (helper compartido con 02·LR5 —
  `loop/_message_invariants.py`): descarta el último assistant con `tool_calls` sin sus `tool_result`
  pareados.
- **Cableado**: fork/__init__:73 `messages = filter_incomplete_tool_calls(list(snap.messages)) if
  policy.inherit_messages else []`. **Orden**: tras 02·LR5 (comparten helper). **Test**:
  `test_fork_filters_incomplete_tool_calls`.

### ExR3 · FIND-EXEC3 — kill descarta el resultado parcial
- **Comportamiento**: al matar un subagente, `_notify` manda `final_text=''` descartando el parcial pese a
  que `ctx.messages` lo tiene; el canónico usa `extractPartialResult`.
- **Seam/firma**: `execution/local/runtime.py` gana `_extract_partial(ctx) -> str` (último texto de
  assistant / concatenación de bloques text). En el path de kill, `final_text = _extract_partial(ctx)`.
- **Cableado**: `LocalAgentRuntime` (kill/notify). Liga 08 (abort con parcial). **Orden**: independiente.
  **Test**: `test_kill_surfaces_partial_result`.

### ExR4 · FIND-EXEC4 — `observer/` huérfano → Deuda B (`B-orphans`)
- **Decisión**: `execution/observer/` (`on_subagent_*`) no lo llama nadie; el eje real es EventBus +
  hook `SUBAGENT_STOP`. **Eliminar** (desarrollado en `DEUDA-B-transversal.md §B-orphans`). Si se quiere
  un observer tipado, que sea un **suscriptor del EventBus**, no un registry paralelo. **Test**:
  `test_no_orphan_observer_in_real_path`.

### ExR5 · FIND-EXEC5 — `max_turns` inerte
- **Comportamiento**: `AgentLoop` usa `_MAX_TURNS=50` fijo (`agent_loop.py:24,185`); `RuntimeTask.max_turns`
  / `Fork.max_turns` se ignoran.
- **Seam/firma**: `AgentLoop.__init__(..., max_turns: int = 50)`; `run()` itera `range(self._max_turns)`.
  El runner (ExR1) pasa `max_turns=task.max_turns or 50` al construir el loop del subagente.
- **Cableado**: factory/runner. **Orden**: junto a ExR1. **Test**: `test_agent_respects_max_turns`.

### ExR6 · FIND-EXEC9/10/11/12 — lifecycle de subagente (los 4 de la re-audit)
- **EXEC9 promoción fg→bg**: un subagente sync que excede `autoBackgroundMs` (120s) se promueve a
  background. Seam: `LocalAgentRuntime.dispatch` arma un `asyncio.wait_for`-equivalente con timer que, al
  vencer, marca `registry.set_backgrounded(task_id, True)` y devuelve el task-id en vez de bloquear.
- **EXEC10 seam force-async**: `should_run_async(task, ctx)` = `run_in_background ‖ background ‖ fork ‖
  **assistant_force_async(integrador)**`. Seam inyectable `ctx.force_async_policy` (MUY relevante a
  `agentic_assistant`: evita que un subagente sync atasque el inputQueue del daemon).
- **EXEC11 reaping**: `run()` gana un `finally` que reap-ea por `agent_id` (kill shell-tasks del agente,
  limpiar todos/hooks/mcp del agente). Liga 10/11/12. Seam: `on_agent_teardown(agent_id)` callback.
- **EXEC12 pendingMessages**: cola por-agente drenada en el límite de ronda (`SendMessage`-a-vivo). Seam:
  `TaskRecord.pending_messages: list` + `drain_pending(agent_id)` en el loop del subagente. Liga 08·SIG13
  (dos niveles currentWork/abort) — desarrollado en `DEUDA-B §B-signals`.
- **Orden**: tras ExR1. **Tests**: `test_sync_agent_promotes_to_background`,
  `test_force_async_seam_honored`, `test_agent_teardown_reaps`, `test_pending_messages_drained`.

### ExR7 · GAP-EXEC1/2/3/4/7 — enriquecer registry y AgentDefinition
- **GAP-EXEC1 dedup `notified`**: `TaskRecord` gana `notified: bool` para no notificar dos veces (espejo
  `LocalAgentTask.notified`). Cableado: `_notify` chequea/setea. **Test**: `test_notify_deduped`.
- **GAP-EXEC2 = GAP-MODE1** → `TaskRecord.kind` (04·MR2).
- **GAP-EXEC3 resume**: `resumeAgent` + `writeAgentMetadata` no portados; depende de `SendMessage`
  (deferred) + persistencia (15). Seam: `LocalAgentRuntime.resume(agent_id, message)`. **Diferido a 11/15**
  por dependencia; anotado. **Test**: `test_agent_resume` (xfail).
- **GAP-EXEC4 AgentDefinition**: hoy 5 campos mínimos; consumir `maxTurns`/`background`/`disallowedTools`/
  `permissionMode`/`initialPrompt`. Seam: ampliar `AgentDefinition` + que el runner los aplique. **Test**:
  `test_agent_definition_consumes_all_fields`.
- **GAP-EXEC7 trailer**: resultado + notificación divergen; homologar el trailer `async_launched` +
  `<usage>` sub-tags que el modelo padre consume. Liga 07. **Test**: `test_agent_trailer_shape`.

### ExR8 · Cabos a Deuda B / otro subsistema (referencia)
- **GAP-EXEC5 prepend** = 03·CtxR3 (que el subagente reciba git/CLAUDE.md/fecha).
- **GAP-EXEC6 fuga de permisos padre→hijo** (sin scoping/override permMode; worker default `acceptEdits`) →
  **Deuda B `B-02`** (el algoritmo `agentGetAppState` es el target).
- **G3 structured output** → **Deuda B `B-structured-output`** + `SyntheticOutputTool` (10).
- **model_override / fork byte-identidad** = 01·feat3/feat4 + 03·CtxR4 (rendered_system_prompt en snapshot).

---

## Re-visita de COMPLETITUD (gate 11 / L09) · 2026-07-19 — MODO VALIDACIÓN

**gate 11 de ENTRADA** — cada fila ✅/🔀 se re-verificó **abriendo el código de B** que produce el
comportamiento y siguiendo el dato de punta a punta (no por la tabla). Las ❌ convergen (ausente = ausente),
pero los ❌ **críticos** se confirmaron por cableado. **Resultado**: el doc (ya re-auditado 2026-07-12 línea a
línea) **se sostiene sobre la base correcta**; **2 costuras latentes NUEVAS** (tech-debt B-interno, NO deuda
A-vs-B — anti-padding L10) + 1 docstring obsoleto. **Código intacto**; tests no re-ejecutados (sin cambio de código).

### Verificación por cableado (B abierta 1→EOF)
- **✅ sostenidos abriendo B**: E1 (`tasks/status.py` TaskStatus×5 + `is_terminal`), E2 (`agents.py:46-58`
  `resolve_subagent_model` precedencia override>agente>inherit, **cableado** runtime.py:345), E3 (`fork/__init__.py:31-46`
  `ForkSnapshot` frozen + `capabilities`, construido en agent.py:79-87), E6 (**complete-first**: runtime.py:400
  `complete()` **antes** de `summarize`/`_notify` 408-414), E8 (`_MAX_SUBAGENT_DEPTH=5` agent.py:14, chequeado
  agent.py:73, `ctx.subagent_depth` sembrado runtime.py:316).
- **🔀 sostenidos**: E10/E32 (kill genérico `registry.py:117-124`, sin códigos ni dispatch por tipo — `TaskRecord`
  **sin** `kind`/`type`, registry.py:17-35 ⇒ confirma GAP-EXEC2/GAP-MODE1), E18 (agent.py:111-119 output plano,
  sin usage/hint), E19 (`notification.py:62-67` XML task_id/status/description/result, sin output-file/summary/
  usage/worktree), E20 (`fork/__init__.py:74` hereda `snap.permissions` crudo; agent.py:91 `inherit_permissions=True`,
  sin scoping/override), E29 (`summarizer.py` final-only, **cableado** runtime.py:410), E30 (`session/session.py`),
  E34 (agent.py:65 async sólo por `run_in_background`).
- **🟡 sostenidos**: E4 (`fork/__init__.py:73` copia cruda `list(snap.messages)`, sin `filter_incomplete_tool_calls`
  ⇒ FIND-EXEC2), E17 (`_last_assistant_text` runtime.py:45-49 `m.get("content") or ""` — si el último assistant es
  puro tool_use, `content` es lista y se devuelve la lista, no texto ⇒ FIND-EXEC8), E22 (`AgentDefinition` sin campo
  `background`, agents.py:22-33), E28 (5 campos exactos).
- **❌ críticos confirmados por cableado (factory.py + agent_loop.py 1→EOF)**:
  - **E24/FIND-EXEC1** (seam roto): `RuntimeFactory._build_local` (factory.py:178-240) construye y devuelve
    `LocalAgentRuntime` pero **nunca llama `set_runner()`** → `get_runner()` (agent.py:105) lanza `RuntimeError` en
    **todo** spawn de subagente. `set_runner` sólo aparece en tests (`test_context_identity.py`). Converge con 18·C1.
  - **E16/FIND-EXEC5** (`max_turns` inerte): `_MAX_TURNS=50` es **constante de módulo** (agent_loop.py:24, usada en
    `range` línea 185 + warning 352); `AgentLoop.__init__` (49-63) **no acepta** `max_turns`; runtime.py:355 lo
    construye sin pasarlo; `_build_child` arma `ForkContext` sin `max_turns` (runtime.py:198-204) ⇒ `RuntimeTask.max_turns`
    / `ForkContext.max_turns` **doblemente** inertes.
  - **E25/FIND-EXEC4** (observer huérfano): `get_observer` **nunca** se llama en producción (runtime.py leída 1→EOF,
    cero referencias); sólo defs + exports + tests. Confirmado huérfano.

### Costuras latentes NUEVAS (tech-debt B-interno — L10 anti-padding, NO deuda A-vs-B)
- **LAT-EXEC1 · `get_registry`/`set_registry` de `execution/tasks/registry.py` huérfano.** El singleton de módulo
  (`_registry` + `get_registry`/`set_registry`, registry.py:153-166) **no tiene ni productor ni consumidor en
  producción**: el runtime toma su registry por **inyección de instancia** (`__init__(task_registry=...)`
  runtime.py:63/86, default `InMemoryTaskRegistry`), nunca por el global. *(Los `get_registry` que aparecen en el
  grep son de `agentic_models`, otro símbolo.)* **Hermano de `observer/`** (FIND-EXEC4): seam provisto-pero-no-usado.
  Clasificación: tech-debt B-interno (extensión sin contraparte canónica) → candidato al mismo trato "cablear o
  eliminar" en `DEUDA-B-transversal.md §B-orphans`. **NO** cuenta como deuda A-vs-B.
- **LAT-EXEC2 · precisión sobre E5 — drain/process de notificación son integrator-delegated.** `put_notification`
  **sí** está cableado (el child escribe, runtime.py:299), pero `drain_notifications`/`process_background_notification`
  **no tienen consumidor runtime-interno** (sólo exports + tests). El **drenado** se delega al integrador vía el seam
  `root_turn_start_hooks` (factory.py:106-112 → registrado en el loop runtime.py:372-374 → ejecutado en
  `agent_loop.py:176` `_run_turn_start_hooks`). Es **🔀/delegación** (como el sistema de hooks configurable de 06),
  no un bug — pero E5 se leía como si el ciclo put/drain/process operara **dentro** del runtime. Matiz honesto: el
  runtime **standalone escribe** notificaciones y **no se auto-drena**; quien las sube al padre es el integrador.
  *(Sub-matiz cross-ref 02/07: el hook de turn-start se dispara una vez por `run()`, no una por turno como el drain
  canónico in-loop — no se remedia aquí, se ancla en 07·events.)* **NO** es deuda A-vs-B.
- **Docstring obsoleto (menor, refuerza FIND-EXEC4).** `observer.py:5` afirma "LocalAgentRuntime emite eventos vía
  `get_observer()`" — **falso** (no lo hace). Se corrige al ejecutar la remediación de FIND-EXEC4 (eliminar `observer/`).

### Ledger de lectura (columna Lectura real — L03)

| Archivo (B) | LOC | Lectura |
|---|---|---|
| `execution/local/runtime.py` | 435 | íntegro 1→EOF (el más grande, L08; ya leído en 01·re-visita, huecos cerrados) |
| `loop/agent_loop.py` | 352 | íntegro 1→EOF (E16/max_turns + PreToolUse + context_modifier/ends_turn) |
| `factory.py` | 267 | íntegro 1→EOF (E24/set_runner — confirmó el seam roto) |
| `execution/tasks/registry.py` | 166 | íntegro 1→EOF (TaskRecord sin kind/notified; LAT-EXEC1) |
| `tools/native/agent.py` | 119 | íntegro 1→EOF (get_runner/depth/snapshot/async-por-flag) |
| `execution/fork/__init__.py` | 96 | íntegro 1→EOF (ForkPolicy/Snapshot/Context/Forker) |
| `execution/local/notification.py` | 72 | íntegro 1→EOF (LAT-EXEC2: put cableado, drain/process delegados) |
| `execution/agents.py` | 66 | íntegro 1→EOF (AgentDefinition 5 campos + resolve_subagent_model) |
| `execution/session/session.py` | 59 | íntegro 1→EOF (Session/Usage/SessionMetadata) |
| `execution/local/summarizer.py` | 49 | íntegro 1→EOF (final-only, cableado runtime.py:410) |
| `execution/runner.py` | 41 | íntegro 1→EOF (get_runner lanza si !set; set sólo en tests = FIND-EXEC1) |
| `execution/observer/observer.py` | 37 | íntegro 1→EOF (huérfano; docstring obsoleto) |
| `execution/tasks/status.py` | 14 | íntegro 1→EOF (TaskStatus×5) |
| Grep cableado | — | `set_runner`/`get_registry`/`set_registry`/`get_observer`/`drain_notifications`/`process_background_notification`/`summarize_if_needed`/`put_notification`/`arm_watchdog` (producción vs test) |

**A (canónico)**: releído íntegro en la re-audit 2026-07-12 (AgentTool.tsx 1397 · runAgent.ts 973 · agentToolUtils.ts
686 · loadAgentsDir.ts 755 · forkSubagent.ts 210 · Task.ts · LocalAgentTask.tsx 682 …). Esta re-visita gate 11 se
centró en **abrir B** (el eje que la re-audit estructural no cubría), no en re-releer A.

### §Nota de honestidad
- La **1ª pasada + re-audit 2026-07-12** verificaron A↔B **línea a línea** contra el código (no fue superficial como
  08), pero fueron **confirmación estructural**; esta re-visita aplicó **gate 11** abriendo la implementación de B de
  cada fila ✅/🔀 y **siguiendo el dato**. Los ✅/🔀 **se sostienen sobre la base correcta**.
- Lo NUEVO que sólo aparece al abrir B siguiendo el dato: **LAT-EXEC1** (registry-global huérfano) y **LAT-EXEC2**
  (drain de notificación delegado al integrador). Ambos **tech-debt B-interno** (L10), **no** deuda A-vs-B — no se
  infla el ledger. FIND-EXEC1/4/5 se **re-confirmaron por cableado** (factory + agent_loop + runtime 1→EOF), no por
  la tabla.
- Código del runtime **intacto** (MODO VALIDACIÓN). Suite **no** re-ejecutada (sin cambio de código); los xfail(strict)
  siguen codificando los gaps.

### Las 4 preguntas de cierre
1. **¿Se revisó todo A?** Sí — A se releyó íntegro en la re-audit 2026-07-12 (registrado); esta re-visita no re-abrió A
   sino B (el foco del gate 11).
2. **¿Se revisó todo B?** Sí — los 13 archivos de B del subsistema leídos **íntegros 1→EOF** (ledger arriba) + grep de
   cableado producción-vs-test. **Tras la re-visita** (en la re-audit estructural previa B se había leído pero NO se
   había seguido el dato de los ✅/🔀).
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí — gate 11 destapó 2 costuras latentes que la confirmación
   estructural no veía (LAT-EXEC1/2) + docstring obsoleto; los ❌ críticos re-confirmados por cableado.
4. **¿Todo cubierto (nada pendiente)?** Sí — LAT-EXEC1/2 clasificados y homed (DEUDA-B §B-orphans / 07); FIND/GAP
   previos intactos con sus destinos; código intacto por diseño (MODO VALIDACIÓN).
