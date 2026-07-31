# 03 · context — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/03-context.md`.
> **Ciclo A3·03·context** del PLAN §4. Fuente: tracker `../03-context.md` (**64 findings**: A1-A33 + A+ + B1-B12 + C1-C3 + D1-D2 + E1-E8 + F1-F5, leído íntegro 1→313).
> Esquema: `00-LEGEND.md`. Re-clasifica cada finding de fidelidad-de-capacidades bajo B (base↔costuras↔batteries↔integrador).
> Costuras **ya validadas por A2** (`SKELETON-REPORT.md`: S4 dispatch, S18 fork/runner, S9/S27 composición, S20 repo id-opaco). Aquí se re-abre el runtime **real** (no el skeleton) para las afirmaciones de cableado (L09/L11).

## Naturaleza de la categoría
El `ToolUseContext` es el **contexto operativo de un turno**: la estructura que el base ensambla y pasa a cada tool.
Bajo B, 03 es una categoría **de mecanismo base + costuras**, no de contrato puro: el *shape* del ctx lo **posee el
base** (`context/tool_use.py`), pero la mayoría de sus ~45 campos canónicos son **callbacks de UI/REPL** (single-user
en terminal) que bajo B **no viajan en el ctx** — se reparten en tres direcciones:
1. **Base ctx** — los campos núcleo del turno (messages, stop, tool_pool, app_state, agent_id, ids opacos).
2. **Otros subsistemas** — campos que el canónico mete en el ctx pero que B **coloca por diseño** en 05/06/10/11/12/13/16 (🔀 "vive en otro subsistema", L10 — no gap si el destino está nombrado).
3. **Integrador** — la superficie de render/terminal (CLI-ONLY/INTERFAZ) y la política de producto (T3).

Dos ejes gobiernan la homologación (tracker §Naturaleza): (a) el canónico es single-user/terminal, el runtime tiene
**usuarios/sesiones** → el ctx **añade** `user_id`/`is_subagent`/`storage`/`fs`/`presentation`/`git_credentials` (A+,
sin contraparte canónica → **extensión B, no deuda**, L10); (b) el canónico mete todo en dos bolsas gigantes
(`ToolUseContext` ~45 + `AppState` ~80), el runtime parte `AppState` en **3 bolsas** (`permissions`/`capabilities`/`native`).

---

## 1. Tabla por finding

Convención de destino: `context/tool_use.py` = módulo base del ctx (`ToolUseContext`/`AppState`); `→NN` = 🔀/gap
homed en otra categoría (destino nombrado, L07); `INTEGRADOR` = `00-INTEGRADORES.md`; `⛔-nombrado` = fuera de
alcance de runtime **y** de ambos integradores en su MVP, con satélite nombrado (L07).

### 1.0 Criterio de aceptación heredado y anclas canónicas *(restituidos por `A-CIERRE·P4″`, par 03)*

Dos bloques del tracker que el destilado **no tenía ranura para recibir** — los dos agujeros estructurales del
esquema de SEPARACION (`A-CIERRE-P4 §9.7·11-12`). Restituidos aquí porque son el **6º campo de L05** (prueba) y
el **7º campo del ancla** (`D-02`).

**(a) §Evidencia ejecutada** (tracker `../03-context.md:34-46`) — criterio de aceptación vigente de 03:
- lint `context/`: `ruff` ✅ · `mypy` ✅ (4 archivos) · `bandit` ✅ (0).
- `test_context_homologation.py` → **11 passed, 3 xfailed**; con los previos de 03
  (`test_context_identity.py`, `test_path_presentation.py`, `test_root_context_modifier.py`) = **33 passed, 3 xfailed**.
- **3 `xfail(strict)` = los gaps vivos, con su ancla canónica exacta:**
  `test_toolusecontext_tracks_read_file_state` (**`Tool.ts:181`**, FIND-CTX1) ·
  `test_appstate_permissions_carry_mode` (**`AppStateStore.ts:109` + `Tool.ts:124`**, GAP-CTX2) ·
  `test_toolusecontext_carries_agent_type` (**`Tool.ts:246`**, FIND-CTX2).
  *`xfail(strict)` es el único mecanismo del corpus que detecta un doc rancio desde el código* — que es justo
  el defecto que §2.6 tabula.
- **Tests que codifican los targets aún no escritos** (§Plan del tracker): `test_fork_inherits_read_file_state`
  (CtxR1) · `test_context_prepends_git_and_claudemd` (CtxR3) · `test_fork_preserves_rendered_system_prompt`
  (CtxR4) · `test_ctx_carries_agent_type` (CtxR5) · `test_no_legacy_session_modifier` (grep-guard, CtxR6).
- Verificados por lectura en la 2ª vuelta, no por ejecución (los conteos de suite son artefactos de la 1ª pasada).

**(b) Anclas canónicas verificadas EXACTAS** (tracker §Ledger 2ª vuelta, `:263-266`) — la columna que esta tabla
no tiene (`P4-01-1`, 4ª confirmación; citas `.ts` **30 → 4**):

| ancla | qué fija | ficha |
|---|---|---|
| `Tool.ts:158-300` (1→EOF del archivo, 792 L) | los ~45 campos del `ToolUseContext` | A1-A33 |
| `Tool.ts:181` | `readFileState` | A5 / FIND-CTX1 |
| `Tool.ts:246` | `agentType` | A4 / FIND-CTX2 |
| `Tool.ts:123-138` + `getEmptyToolPermissionContext` `:140-148` (`:124`) | `ToolPermissionContext` | B2 / GAP-CTX2 |
| `Tool.ts:330` | `ToolResult.contextModifier` | C3 |
| `AppStateStore.ts:89-452` (1→EOF, 569 L) | el tipo real `AppState` | B1-B12 |
| `AppStateStore.ts:109` · `getDefaultAppState:500-503` | `mode: PermissionMode` **sí existe en el canónico** | B2 / K1 |
| `context.ts:1-189` (íntegro) | `getGitStatus`/`getSystemContext`/`getUserContext`/`setSystemPromptInjection`/memoize | F1-F5 |
| `utils/forkedAgent.ts::createSubagentContext:345-462` (+doc `320-344`) | derivación del ctx hijo | E1-E8 |
| ⛔ abierto y descartado: `state/AppState.tsx` (199, wrapper React) · `utils/context.ts` (221, ventana de contexto ⇒ 02/16) · `src/context/*.tsx` (React UI) | — | L02: `íntegro → ⛔` |

*Son **punteros acreditados por el tracker**, no la tabla de comportamientos que `D-02` exige; tabularlos es P6″/T-A.*

### A · `ToolUseContext` — campos (Tool.ts:158-300)

| ID | resumen (comportamiento observable) | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **A1** messages ✅ | vista de conversación del turno | núcleo | **T2-BASE-MECANISMO** | `context/tool_use.py` (`messages`) | — | shape ya en base; el *item* de mensaje es T1 (07·events/01) |
| **A2** abort→`stop` ✅ | cancelación cooperativa | núcleo | **T2-BASE-MECANISMO** | `context/tool_use.py` (`stop`) + mecanismo en loop/dispatcher | eje ejecución | `stop: asyncio.Event`; cableado `agent_loop.py:173/186/227`+`dispatcher.py:54` (verificado) — cruza 08·signals |
| **A3** agentId ✅ | id de subagente en el ctx | núcleo (id opaco) | **T2-BASE-MECANISMO** | `context/tool_use.py` (`agent_id`) | eje ejecución · id opaco | lo genera el forker (`agent_{uuid}`) |
| **A4** agentType 🟡 **FIND-CTX2** | tipo de subagente para hooks/telemetría | núcleo | **T2-BASE-MECANISMO** (cableado-gap) | `context/tool_use.py` (+ poblar en 05) | eje ejecución | **CORE-GAP (CtxR5):** `ToolUseContext` gana `agent_type`; el runner lo puebla al construir el ctx hijo. Hoy sólo en `ForkContext.subagent_type`, no baja al ctx (verificado fork:55/85-93) |
| **A5** readFileState ❌ **FIND-CTX1** | LRU {path→content,mtime} → **dos consumidores**: (a) guard de frescura de Edit/Write (bloquea si el fichero cambió desde la última lectura / exige read-before-edit) y (b) **dedup de nested-memory** (A24) | núcleo | **T2-BASE-MECANISMO** (home 10) + fork-copy | **→10·tools-native (R0** = `FIND-NATIVE-READSTATE`, keystone de 10; battery `B22 fs_tools`**)** + `ForkSnapshot` copia (CtxR1) | — | **CORE-GAP correctitud:** el campo se desarrolla en 10·R0 (`ctx.read_file_state`); aquí sólo el **cableado del fork** (snapshot copia lo leído por el padre; firma `read_file_state: dict[str,Any] = {}` copiado como `dict(snap.read_file_state)`, mismo patrón que `messages`). **Estado de B, verificado:** `FileEditTool` **lee y reemplaza sin verificar lectura previa ni mtime** ⇒ el riesgo no es teórico (write-stale). Ancla canónica `Tool.ts:181` |
| **A6** getAppState/setAppState 🔀 | store funcional React vs mutación in-place | núcleo | **T2-BASE-MECANISMO** | `context/tool_use.py` (`app_state` mutable) | — | divergencia por diseño (headless, sin React); mismo efecto observable — **no deuda** (L10). ⚠ **invariante canónico restituido (`P4-03-2`):** en el canónico `setAppState` es **no-op para subagentes async** — así se logra el aislamiento. B obtiene el mismo aislamiento por `ForkSnapshot` (E1/E2). **Ese no-op es la razón de existir de A7**: sin él, `setAppStateForTasks` no tendría sentido |
| **A7** setAppStateForTasks 🟡 | registro session-scoped (bash bg) que sobrevive al turno alcanza la raíz | núcleo | **T2-COSTURA** (home 05) | **→05·execution** (`InMemoryTaskRegistry`) | eje ejecución | **registro Y kill** de infra session-scoped (bash background) que sobrevive al turno debe alcanzar la raíz **precisamente porque `setAppState` es no-op en el subagente async** (A6); el registro de tasks vive en execution, no en AppState; **ajuste**: confirmar en 05 que el kill de tasks de subagente async alcanza el registro raíz |
| **A8** child-abort enlazado ✅ | abort padre→hijo compartido | núcleo | **T2-COSTURA** (home 05·fork) | **→05·execution** (`ForkPolicy.propagate_abort`) | eje ejecución | `fork/__init__.py:80-83` comparte `parent_stop` (verificado) |
| **A9** tools/refreshTools ✅ | pool de tools reensamblado por turno | núcleo | **T2-BASE-MECANISMO** | `context/tool_use.py` (`tool_pool`) + reensamblado en loop | — | `refreshTools` ≡ `agent_loop.py:195-196` (`_build_tool_pool` por turno) — verificado (=F11 de 02) |
| **A10** commands ❌ | slash-commands en el ctx | núcleo | **T2-COSTURA** (`UserInputProcessor`) + **BATTERY commands** | **→12·skills** (battery commands) + costura 01·CTR-12 | — | ligado a **GAP-01** (01): el loop debe invocar `UserInputProcessor`; el contenido (comandos) es battery |
| **A11** mainLoopModel 🔀 | resolución de modelo por turno | núcleo | **T1-MOTOR** (home 16) | **→16·models** / 02·C3 | — | no vive en el ctx del runtime; resolución en el caller |
| **A12** thinkingConfig/fastMode/effortValue/**advisorModel** ❌ | superficie de sampling del modelo (`options.thinkingConfig` + los 4 de `AppState`) | núcleo | **T1-MOTOR** (home 16) | **→16·models** / 02·C2 | — | decidir cuáles son core (thinking/effort) y por dónde viajan (caller, no ctx) |
| **A13** mcpClients/resources 🔀 | clientes/recursos MCP threadeados | núcleo | **T2-COSTURA** (home 11) | **→11·mcp** (`app_state.capabilities` + `event_queue`) | — | el `ForkSnapshot` ya hereda la bolsa `capabilities` (verificado fork:46/78); desarrollo en 11 (CtxR7) |
| **A14** agentDefinitions 🔀 | defs de subagentes | núcleo | **T2-COSTURA** (home 05) | **→05·execution** (`agents.py`) | — | las resuelve execution, no viajan en el ctx |
| **A15** maxBudgetUsd ❌ | tope de gasto por task | núcleo | **T2-BASE-MECANISMO** (home 05) | **→05·execution** / 02·G2 | — | en alcance de 05 |
| **A16** custom/appendSystemPrompt 🔀 | override/append de system prompt | núcleo | **T1-MOTOR** (home 16) | **→16·models** (`_compose_system_prompt`) + `system_override` del loop | — | el runtime lo maneja en el caller (verificado seam `agent_loop.py:233-234`), no como campo del ctx |
| **A17** debug/verbose/isNonInteractive/querySource ⛔ | flags de UI/analítica/interactividad terminal | cáscara-CLI | **CLI-ONLY / INTERFAZ** | **INTEGRADOR** (flags de sesión/interfaz) | — | el integrador con interfaz decide interactividad; no al runtime headless |
| **A18** toolUseId 🟡 | id de la tool-call en el ctx | núcleo | **T2-BASE-MECANISMO** (ajuste diferido) | `context/tool_use.py` (opcional, si un hook lo pide) | — | hoy vive en `ToolCallEvent`/dispatch (suficiente para el pareo); exponer en ctx sólo si un consumidor lo exige |
| **A19** fileReadingLimits/globLimits 🔀 | acotar read/glob por-contexto | núcleo | **T2-COSTURA** (home 10) | **→10·tools-native** | — | límites hoy en cada tool; subir al ctx sólo si el integrador los ajusta por sesión |
| **A20** toolDecisions ❌ | historial accept/reject por tool | núcleo | **T2-COSTURA** (home 06) | **→06·hooks/permissions** | — | historial de decisiones de permiso |
| **A21** localDenialTracking ❌ | contador de denials para subagentes async | núcleo | **T2-COSTURA** (home 06) | **→06·permissions** | — | sin esto el umbral fallback-a-prompting nunca se alcanza en subagentes |
| **A22** contentReplacementState ❌ | presupuesto agregado de tool-results | núcleo | **T2-BASE-MECANISMO** (home 02) | **→02·loop (B2)** | — | tool-result budget; vive en el ctx del canónico, ausente en runtime |
| **A23** renderedSystemPrompt 🟡 **GAP-CTX4** | bytes del system prompt del padre congelados (cache-share del fork) | núcleo | **T2-BASE-MECANISMO** (fork) | `ForkSnapshot` (CtxR4) + **→16** (byte-identidad) | eje ejecución | **CORE-GAP:** `ForkSnapshot` gana `rendered_system_prompt`; sin él, riesgo de cache-miss si el prompt diverge al re-renderizar (verificado ausente fork:31-46) |
| **A24** `nestedMemoryAttachmentTriggers` + `loadedNestedMemoryPaths` ❌ | dedup de inyección de CLAUDE.md anidado (**dos campos**: los disparadores y el set de rutas ya cargadas) | núcleo | **BATTERY memory** (home 13) | **→13·memory** (depende de A5) | — | dedup de nested-memory; depende de readFileState |
| **A25** `dynamicSkillDirTriggers` + `discoveredSkillNames` ❌ | triggers/telemetría de descubrimiento de skills (**dos campos**: los disparadores y el **set de descubiertos**) | núcleo | **BATTERY skills** (home 12) | **→12·skills** | — | =F10 de 02. ⚠ `discoveredSkillNames` es el **discovered-set** — mismo eje que `DEUDA-A §2.8·H-4` (discovered-set sin cablear) y que `09·E5` (`_DISCOVERED_KEY`): al portarlo, la clave la fija 09/12, **no** un `agent_id` (`A-CIERRE-P4 §1`) |
| **A26** requireCanUseTool ❌ | forzar `canUseTool` aun con auto-approve | núcleo | **T2-COSTURA** (home 06) | **→06·permissions** | — | speculation gate |
| **A27** preserveToolUseResults ⛔ | transcript de teammates in-process visible al usuario | — | **⛔-nombrado** | ⛔ **teams (02·E3)** — fuera de core | — | satélite teams/swarm, decisión de producto (02·E3 ⛔) |
| **A28** criticalSystemReminder_EXPERIMENTAL ⛔ | recordatorio experimental | — | **⛔-nombrado** | ⛔ **ant-experimental** — fuera de core | — | flag experimental interno del canónico |
| **A29** queryTracking (depth/chainId) 🟡/⛔ | profundidad de anidamiento + chainId de analítica | núcleo (depth) | **T2-BASE-MECANISMO** (depth, home 05) + **⛔-nombrado** (chainId) | **→05** (`subagent_depth`) + ⛔ chainId (analítica, =A3 de 02) | eje ejecución | depth cableado (`runtime.py:204/316`, verificado); chainId de cadena ⇒ fuera de core |
| **A30** userModified ⛔ | flag de edición manual del input (UI) | cáscara-CLI | **CLI-ONLY / INTERFAZ** | **INTEGRADOR** | — | estado de edición del input en la UI |
| **A31** handleElicitation ❌ | elicitación OAuth/URL de MCP | núcleo | **T2-COSTURA** (home 11) | **→11·mcp** | — | elicitación de MCP |
| **A32** requestPrompt 🔀 | prompts interactivos al usuario (HITL) | núcleo | **BATTERY tool** (`AskUserQuestion`) | **→10·tools-native** (tool `ends_turn`) | — | HITL por tool que cierra el turno (=F4 de 02), no por callback del ctx; equivalente funcional |
| **A33** callbacks UI/REPL (15: setToolJSX, addNotification, appendSystemMessage, sendOSNotification, setInProgressToolUseIDs, setHasInterruptibleToolInProgress, setResponseLength, pushApiMetricsEntry, setStreamMode, onCompactProgress, setSDKStatus, openMessageSelector, updateFileHistoryState, updateAttributionState, setConversationId) ⛔ | render/estado de terminal (ink/React), métricas, notificaciones OS, JSX de tools | cáscara-CLI | **CLI-ONLY / INTERFAZ** (13) + **background-behavior** (2) | **INTEGRADOR** (render/notif/status/stream) · `updateFileHistoryState`→**10** (undo) · `updateAttributionState`→**INTEGRADOR-política** (co-autoría, [[no-claude-coauthorship]]) | — | la superficie de interfaz es obligación del integrador (OI-A); 2 con fondo de comportamiento se re-hogar (undo→10, attribution→política) |
| **A+** runtime añade: `user_id`, `is_subagent`, `turn_count`, `storage`, `presentation`, `exec_env`, `fs`, `git_credentials`, `event_queue` ✅ | extensiones por usuarios/sesiones + FS de infra | núcleo | **mixto** (extensión B, sin contraparte canónica → **no deuda**, L10) | `user_id`→**T3+repo** (transversal) · `is_subagent`/`turn_count`→**base** · `storage`/`fs`/`git_credentials`→**T2-COSTURA** (`StorageContract`/`ConfinedFilesystem`/`GitCredentialProvider`) · `presentation`→**T2-COSTURA** (`PathPresentation`) · `event_queue`→**T2-COSTURA** (event-sink, 07) | eje persist+ejec (user_id) · id opaco+repo | verificado poblado en `runtime.py:315-321`; `user_id` **ripear** el autogen `user_<hex>` (:209) → id opaco atribuido por el integrador (consolida A3.DA) |

### B · `AppState` (AppStateStore.ts:89-452)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **B1** AppState 3-bolsas 🔀 | store monolítico (~80) → 3 bolsas (permissions/capabilities/native) | núcleo | **T2-BASE-MECANISMO** | `context/tool_use.py` (`AppState`) | — | divergencia deliberada (L10); el base expone lo core y delega el resto por bolsa (verificado tool_use.py:23-30) |
| **B2** toolPermissionContext 🟡 **GAP-CTX2=GAP-02=K1** | **shape canónico entero** (`Tool.ts:123-138`, default en `AppStateStore.ts:500-503`): `{ mode: PermissionMode (default/plan/acceptEdits/bypass), alwaysAllowRules, alwaysDenyRules, alwaysAskRules, additionalWorkingDirectories, isBypassPermissionsModeAvailable, prePlanMode, … }` **vs** el de B: `PermissionContext = { always_allow_command, always_allow_session, always_deny }` (`contracts/permissions.py`, 33 L) | núcleo | **T1-CONTRATO** (faltan `mode`, `alwaysAskRules`, `additionalWorkingDirectories`, `isBypassPermissionsModeAvailable`, `prePlanMode`) + **DEUDA-B `DB-19`** (canal no tipado `native["plan_mode"]`) | **→01·contracts (CTR-08)** (`PermissionMode`) + gate + **`DEUDA-A·K1`** + `DB-19` | — | **CORE-GAP = keystone `K1`:** misma raíz que 01·CR1/CTR-08. **Faltan 5 campos, no uno**: sin `alwaysAskRules` no hay canal HITL; sin `additionalWorkingDirectories`/`prePlanMode` el gate no reproduce plan-mode (los 2 ya restituidos en `01·CTR-08` por `P4-01·§7.5`). En 03 el cableado es leer el modo de `app_state.permissions.mode`, no de `native["plan_mode"]` (CtxR2) — ver **§2.6·I3** para el estado vigente del hack |
| **B3** mcp state 🔀 | `{clients, tools, commands, resources, pluginReconnectKey}` — el 5º campo es la **clave de reconexión de plugins**, sin la cual no hay re-handshake tras caída | núcleo | **T2-COSTURA** (home 11) | **→11·mcp** (`capabilities`) | — | provider per-tenant del integrador |
| **B4** todos 🔀 | `{[agentId]: TodoList}` | núcleo | **BATTERY** (home 10) | **→10·tools-native** (`todo_write` + `native`) | — | estado de todos por agente en la tool nativa |
| **B5** `tasks`/`agentNameRegistry`/`foregroundedTaskId`/`viewingAgentTaskId` 🔀 | registro de subagentes/tasks (**4 campos**; los 2 últimos son *qué task está en primer plano* y *cuál se está viendo* — selección de foco, que en B es del integrador) | núcleo | **T2-BASE-MECANISMO** (home 05) | **→05·execution** (`InMemoryTaskRegistry`) | eje ejecución | vive en execution, no en AppState |
| **B6** sessionHooks 🔀 | estado de hooks de sesión | núcleo | **BATTERY hooks** (home 06) | **→06·hooks** (`HookRunner`) | — | estado de hooks |
| **B7** fileHistory / attribution ❌/⛔ | snapshots de undo de ficheros + co-autoría de commits | núcleo (fileHistory) | **T2-BASE-MECANISMO** (fileHistory undo, home 10) + **INTEGRADOR-política** (attribution) | **→10·tools-native** (undo) + **INTEGRADOR** (attribution, [[no-claude-coauthorship]]) | — | fileHistory = capacidad de undo (CORE-GAP homed 10); attribution = política de commits del integrador |
| **B8** agentDefinitions 🔀 | defs de subagentes | núcleo | **T2-COSTURA** (home 05) | **→05·execution** (`agents.py`) | — | =A14 |
| **B9** notifications/elicitation/inbox 🔀 | notificaciones de background / elicitación / bandeja teams | núcleo (notifications) | **T2-COSTURA** (`NotificationSink`, home 05) + **→11** (elicitation) + **⛔** (inbox) | **→05·execution** (`notification.py`, canal keyed user+session) + **→11·mcp** (elicitation) + ⛔ inbox (teams) | eje persist+ejec (canal keyed) | ⚠ **VEREDICTO INVERTIDO — ver §2.6·I1.** El canal tiene `put` (`runtime.py:299`) y **NO tiene drain**: `drain_notifications`/`process_background_notification` (`local/notification.py:45/49`) **no tienen caller** ⇒ **CORE-GAP `H-5`**, no delegación al integrador. `SEAMS §S21` lo rotula `existe-put-sin-drain`; el drenador es **el propio `AgentLoop`** (`AC-07`), no OI-B |
| **B10** mainLoopModel/thinking/fastMode/effort/advisor ❌/🔀 | opciones de modelo/turno | núcleo | **T1-MOTOR** (home 16) | **→16·models** / 02·C2 | — | =A11/A12 |
| **B11** initialMessage ❌ | mensaje inicial (CLI args / salida de plan mode) | núcleo | **T2-COSTURA** (`UserInputProcessor`) + **BATTERY plan** | **→14·plan** + costura commands (01·CTR-12) | — | se cruza con G1 (input processing) y 14·plan |
| **B12** UI/REPL/bridge/teams/tmux/bagel/computer-use/speculation/plugins/companion/ultraplan/worker-sandbox/… (~55 campos) ⛔ | grueso del store: terminal/REPL, bridge a claude.ai, swarm/teams, tmux, computer-use, speculation, plugins | cáscara-CLI (interfaz) + ⛔ (satélites) | **CLI-ONLY / INTERFAZ** (terminal/REPL/footer/overlay/statusLine) + **⛔-nombrado** (teams/bridge/computer-use/speculation/tmux) | **INTEGRADOR** (capa de interfaz) + ⛔ satélites nombrados (02·E3 teams; bridge/computer-use fuera de core) | — | separar: estado de **interfaz** → integrador (OI-A); satélites de producto (teams/bridge/computer-use) → ⛔ nombrado (L10, divergencia por arquitectura single-user) |

### C · Adapters (`context/adapters.py`) — Session ⇄ ctx

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **C1** `tool_use_context_from_session` ✅ | grants→permissions, invoked_skills→capabilities, prefiere `get_messages_for_llm` | núcleo | **T2-COSTURA** (adapter Session→ctx, extensión B) | `context/adapters.py` (sin contraparte canónica) | eje persistencia (lee metadata de sesión) | seam de transición; verificado adapters.py:11-48. Homologación *de comportamiento* — no deuda A↔B |
| **C2** `sync_session_from_tool_use_context` ✅ | escribe `always_allow_session`→`metadata.permission_grants` | núcleo | **T2-COSTURA** (adapter inverso) | `context/adapters.py` | eje persistencia | verificado adapters.py:51-57. **Ajuste**: si el ctx gana estado persistible (p.ej. modo tras B2), ampliar la sync |
| **C3** `apply_context_modifier_compat` 🟡 | modifier ctx-aware con fallback a modifier legacy de sesión | núcleo | **DEUDA-B** (andamiaje de migración) | **DEUDA-B (borrar)** cuando todo modifier sea ctx-aware | — | el loop ya usa `modifier(ctx)` directo (verificado `agent_loop.py:332-335`); retirar el `except AttributeError` (CtxR6). NO deuda A↔B |

### D · Presentation (`context/presentation.py`)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **D1** `IdentityPresentation` ✅ | no-op: FS del usuario = FS del agente, rutas verbatim | núcleo | **T2-COSTURA** (`PathPresentation`, default base) | costura **`PathPresentation`** (`contracts/storage.py`) + default `IdentityPresentation` | — | comportamiento canónico por defecto (terminal); verificado presentation.py:15-23 |
| **D2** `PathPresentation` seam + `to_llm` latente ✅/deuda-B | mapea rutas host→tokens fake en el choke point del ToolResult | núcleo | **T2-COSTURA** (`sanitize_output` cableado) + **DEUDA-B** (`to_llm` sin call site) | costura **`PathPresentation`** + **DEUDA-B (cablear\|borrar `to_llm`)** | — | `sanitize_output` cableado en **DOS choke points, no uno** (`P4-03-8`): `dispatcher.py:42` (todo `ToolResult.output`) **y `runtime.py:244` (stream TTS)** — quien implemente el saneo debe cubrir ambos; prueba que lo fija: `test_path_presentation::test_choke_point_covers_messages_and_bus` (alimenta `ctx.messages` **y** el bus). `to_llm(host_path)` sin consumidor de producción → **DEUDA-B interna** (`DB-28`), extensión sin contraparte canónica → **NO deuda A↔B** (L10). ⚠ **estado vigente ≠ «cablear o borrar»: ver §2.6·I5** |

### E · Derivación de subagente (`createSubagentContext`, forkedAgent.ts:345-462)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **E1** aísla por defecto ✅ | **`readFileState` clonado** (no compartido — de ahí CtxR1), colecciones frescas, callbacks de mutación no-op; en B: messages aislados | núcleo | **T2-BASE-MECANISMO** (fork, home 05) | **→05·execution** (`RuntimeContextForker.fork`) | eje ejecución | aislamiento por construcción del ctx hijo (verificado fork:64-93); sin callbacks React que "no-opear" |
| **E2** hereda del padre ✅ | options (tools/mcp), messages (override) | núcleo | **T2-BASE-MECANISMO** (fork, home 05) | **→05·execution** (`ForkPolicy.inherit_*`) | eje ejecución | declarativo por política; `capabilities` hereda el provider MCP per-tenant (verificado fork:78) |
| **E3** agentId nuevo ✅ | `createAgentId` por subagente | núcleo (id opaco) | **T2-BASE-MECANISMO** (fork, home 05) | **→05·execution** (`agent_{uuid}`) | eje ejecución · id opaco | verificado fork:69 |
| **E4** abort hijo enlazado ✅ | `createChildAbortController` / `shareAbortController` | núcleo | **T2-COSTURA** (fork, home 05) | **→05·execution** (`propagate_abort` o `stop` fresco) | eje ejecución | verificado fork:80-83 (=A8) |
| **E5** avoid-prompts en subagente async 🔀 | subagente unattended no pide permiso interactivo | núcleo | **T2-BASE-MECANISMO** (filtro toolset) | **→05·execution** + **→06** (permission) | eje ejecución | mecanismo distinto: `is_subagent`→toolset filtrado a `safe_for_background` (verificado `resolver.py:45-48`+`registry.py:32-33`), no `shouldAvoidPermissionPrompts`. Cruza GAP-02 |
| **E6** contentReplacementState clonado ❌ | decisiones idénticas ⇒ cache-hit del fork | núcleo | **T2-BASE-MECANISMO** (home 02) | **→02·loop (B2)** (=A22) | — | el fork no clona presupuesto de tool-results (no existe) |
| **E7** renderedSystemPrompt congelado 🟡 **GAP-CTX4** | prefijo byte-idéntico prompt-cache | núcleo | **T2-BASE-MECANISMO** (fork) | `ForkSnapshot` (CtxR4, =A23) + **→16** | eje ejecución | capturarlo en `ForkSnapshot` |
| **E8** queryTracking depth+1 ✅ | profundidad de anidamiento como tope | núcleo | **T2-BASE-MECANISMO** (home 05) | **→05·execution** (`subagent_depth`) | eje ejecución | verificado `runtime.py:204/316` + tope en tool Agent; chainId ⇒ ⛔ |

### F · `context.ts` — contexto prepend (system/user)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **F1** `getGitStatus` ❌ **GAP-CTX3** | branch/main/status-short/log-5/user.name (trunca 2k) al inicio | núcleo | **T2-BASE-MECANISMO** (prepend) + **T2-COSTURA** (git-status provider) + **INTEGRADOR** (fuente) | nuevo `context/session_context.py::build_prepend_context` → `system_sections` (CtxR3) + provider en el integrador | — | **CORE-GAP:** el seam `system_sections` existe (verificado `agent_loop.py:211-213/228-229`); falta el provider que aporta git-status. La **fuente** (¿opera sobre un checkout?) la decide el integrador (OI-C) |
| **F2** `getUserContext` (CLAUDE.md + fecha) 🟡 **GAP-CTX3** | memory files + `Today's date` inyectados y cacheados | núcleo (parcial) | **BATTERY memory** (home 13) + **T2-BASE** (fecha) | **→13·memory** (recall ya presente) + `session_context` (fecha) | — | recall de memoria ya inyectado (verificado `agent_loop.py:218` `_inject_recall`); falta **fecha actual** (core) y CLAUDE.md del repo (depende de si el integrador opera sobre checkout) |
| **F3** `getSystemContext` (git + cache-breaker) ❌/⛔ | git status = F1; cache-breaker ant | núcleo (git) | **=F1** + **⛔-nombrado** (cache-breaker) | =F1 + ⛔ `BREAK_CACHE_COMMAND` (ant-only debug) | — | git = F1; cache-breaker fuera de core |
| **F4** `setSystemPromptInjection` ⛔ | debug ant, cache breaking | — | **⛔-nombrado** | ⛔ **ant-debug** — fuera de core | — | debug interno del canónico |
| **F5** memoización por conversación 🟡 | contexto prepend computado una vez y cacheado | núcleo | **T2-BASE-MECANISMO** (home 16) | **→16·models** (cacheo por sesión) | eje persistencia (cache por sesión) | si el runtime porta F1/F2, replicar el cacheo por sesión |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`ToolUseContext` / `AppState` 3-bolsas** (T2-BASE-MECANISMO, **propiedad del base**) — productor: el runtime (`_build_child`, adapters) · consumidor: cada tool + hooks. Es el **shape núcleo del turno**; no es costura rellenable sino mecanismo base. *Ganancias de campo pendientes: `agent_type` (CtxR5), `read_file_state` (10·R0/CtxR1), `permissions.mode` (CtxR2).*
- **`PathPresentation`** (T2-COSTURA) — productor: **dos choke points** — `tools/dispatcher.py:42` (`sanitize_output` sobre `ToolResult.output`) **y `runtime.py:244`** (stream TTS) · consumidor: base default `IdentityPresentation` / integrador de infra. *`to_llm` → **`S31.sanitize` con estado ENTRE chunks** (A3.CAT/17), ya no «cablear o borrar» — ver §2.6·I5.* (Compartida con 01·CTR-11.)
- **`UserInputProcessor`** (T2-COSTURA, hoy sin productor = GAP-01) — productor (a cablear): el loop antes del turno LLM · consumidor: battery commands / integrador. Alimenta A10/B11. (Homed en 01·CTR-12.)
- **`NotificationSink`** (**S21**, keyed user+session) — productor: execution (`runtime.py:299`, `put`) · consumidor: ⚠ **NO EXISTE** — `drain_notifications`/`process_background_notification` (`local/notification.py:45/49`) **no tienen caller** en las 435 L de `runtime.py`. Estado real `existe-put-sin-drain` = **CORE-GAP `H-5`** (`SEAMS §S21`, `:381`/`:517`); el drenador correcto es **el propio `AgentLoop`** (`AC-07`), **no** el integrador. Lo que A2 validó fue el `put`, no el ciclo. Ver **§2.6·I1**.
- **git-status/prepend provider** (T2-COSTURA sobre `system_sections`) — productor: `agent_loop.py:211-213` (el loop concatena `system_sections`) · consumidor: un provider dedicado / `CapabilityManager` que aporte git-status+fecha+CLAUDE.md. **Hoy sin provider de prepend** = GAP-CTX3.
- **`RuntimeContextForker` / `ForkPolicy` / `ForkSnapshot`** (T2-BASE-MECANISMO + COSTURA de política) — productor: `runtime.py:_build_child` · consumidor: base default. **Ganancias de snapshot pendientes:** `read_file_state` (CtxR1), `rendered_system_prompt` (CtxR4), `agent_type` (CtxR5). *Home de la mecánica: 05·execution; 03 aporta los campos que el snapshot debe copiar.*
- **repo id-opaco de identidad/sesión** (T2-COSTURA transversal, SEAM-DE-IDENTIDAD) — productor: runtime (lee sólo `.id`; hoy autogen `user_<hex>` en `runtime.py:209` = mímica a ripear) · consumidor: integrador (atribuye + metadata). *Consolidación en A3.DA.*

### 2.2 Batteries que alimenta (nombre · alcance)
*(IDs canónicos según `BATTERIES.md:167` — «`03·context` **origina 0 propias**; alimenta B05/B15/B16/B08»)*

- **`B05` commands** — slash-commands / inline-invocations que rellenan **`S11 UserInputProcessor`** (estado `existe-sin-poblar`, `BATTERIES.md:97` cita `03·A10/B11`). Origen del seam en 01; contenido en 12.
- **`B15` memory** — recall + dedup de nested-memory (A24) + CLAUDE.md del prepend (F2). Home 13.
- **`B16` plan** — `initialMessage` como salida de plan mode (B11). Home 14. ⚠ es **battery OPCIONAL** y hoy se instancia incondicionalmente (`PlanModeProvider()`, `factory.py:146`) = `BATTERIES §6·CAT-h3`.
- **`B08` voice** — `audio_prompt`→prompt (verificado seam `runtime.py:220-224`, `_resolve_prompt`). Home 17 (=01·CTR-06). Costuras numeradas: **`S30 PromptSourceProtocol`** (entrada) / **`S31 SpeechSink`** (salida).
- Además **alimenta `B22 battery_fs_tools`** por la vía de `ctx.read_file_state` (`BATTERIES.md:141`), que sostiene el keystone `FIND-NATIVE-READSTATE` = FIND-CTX1 de 03.
- *(03 no origina batteries nuevas propias: todas nacen en otras categorías; 03 confirma que sus campos NO viajan en el ctx.)*

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
Findings que **originan en 03** (el ctx/fork base debe reproducir un comportamiento y hoy no):
- **FIND-CTX1 (A5/E6, ❌ correctitud)** — `read_file_state` ausente ⇒ sin guard read-before-edit / write-stale. Home **10·R0**; en 03 el cableado del fork (`ForkSnapshot` copia — CtxR1).
- **GAP-CTX2 (B2/GAP-02, 🟡)** — `AppState.permissions` sin `mode`; plan-mode hackeado por `native["plan_mode"]`. Raíz compartida con **01·CTR-08**; CtxR2.
- **FIND-CTX2 (A4, 🟡)** — `agent_type` no threadeado al ctx (sólo en `ForkContext.subagent_type`). CtxR5.
- **GAP-CTX3 (F1/F2, ❌)** — contexto prepend (git status + fecha + CLAUDE.md) no portado; el seam `system_sections` existe pero sin provider. CtxR3.
- **GAP-CTX4 (A23/E7, 🟡)** — `rendered_system_prompt` no capturado en `ForkSnapshot` ⇒ posible cache-miss del fork. CtxR4.

CORE-GAPs que 03 **detecta pero homea fuera** (destino nombrado): A22/E6 tool-result budget →02·B2; B7 fileHistory-undo →10; A10/B11 commands cabling →01·CTR-12/12·skills.

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10)
*(estado vigente tras los rollups A3.DB/A3.CAT — los 4 ítems fueron recalificados; ver §2.6)*

- **C3** `apply_context_modifier_compat` — andamiaje de migración; retirar el `except AttributeError` cuando ningún modifier use el path legacy (CtxR6). El loop ya usa `modifier(ctx)` directo. **Sigue vigente** (`DEUDA-B:212`, dentro de `DB-28` menores).
- **D2** `PathPresentation.to_llm` — ⚠ **ya NO es «cablear o borrar»**: A3.CAT/17 lo **decidió** → pasa a **`S31.sanitize` con estado ENTRE chunks** (fija `CG-V4`/`FIND-VOICE1`), y **`S12` quedó corregida a `existe-parcial`** (`BATTERIES.md:253`). Ver **§2.6·I5**.
- **B2 (parte hack)** — ⚠ el ítem se llama hoy **`DB-19`** y está **secuenciado tras `K1`** (`DEUDA-B:201`: *BORRAR, secuenciado tras K1*), no es una limpieza suelta. Ver **§2.6·I3**.
- **A+ (parte mímica)** — ⚠ **no es un barrido suelto**: `DEUDA-B:314` lo pliega **DENTRO de la remediación de `H-1`** (memoria rota por el autogen). Ver **§2.6·I4**.

### 2.3b Cambios de estado declarados *(patrón 4 — `A-CIERRE-P4 §7`)*
- **`A+` (autogen `user_<hex>`/`sess_<hex>`, `runtime.py:208-209`)** — el destilado lo endureció de *observación de mímica* a *ítem de DEUDA-B accionable*. **El endurecimiento resultó CIERTO y luego se quedó corto**: `DEUDA-A·H-1` demostró que el autogen **rompe la memoria** (la clave de scope cambia entre turnos) ⇒ no es higiene, es **CORE-GAP con remediación acoplada**. Misma especie que `01·CTR-05`: endurecer no es *per se* inventar. Registrado aquí, no como pérdida.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05)
Con **capacidad observable · origen (costura del base) · firma que consume · cableado en el integrador · orden · criterio de aceptación**:

- **OI-A · Renderizar el turno (capa de interfaz)** *(contrato base común: todo integrador con interfaz)* — **capacidad:** presentar progreso del turno, tool-use en curso, status, notificaciones, selección de mensaje, stream mode. **origen:** A33 (15 callbacks UI) + A17/A30 (flags de interactividad) + B12 (estado terminal/REPL/footer/overlay/statusLine). **firma:** el integrador consume el **stream de eventos** del runtime (07·events) — el runtime **NO** expone callbacks de render en el ctx; emite eventos que el integrador renderiza. **cableado:** `agentic_code` = render a terminal (ink-like); `agentic_assistant` = SSE/websocket → front (bff). **orden:** requiere el stream de eventos (07). **aceptación:** un turno con tool-calls se renderiza incrementalmente sin que el runtime conozca el medio (verificado en A2: el loop emite `ToolCallEvent`/`ToolResultEvent`; el integrador drena). *(realización: terminal vs front web)*
- **OI-B · Surtir al usuario las notificaciones de background** *(contrato base común)* — ⚠ **REESCRITO por §2.6·I1: el DRENAJE no es del integrador.** **capacidad (del integrador):** enrutar a su transporte las notificaciones que **el runtime ya le entrega** por el stream de eventos (OS notification en terminal; push/inbox en front). **origen:** B9/A33 (`addNotification`/`sendOSNotification`). **firma:** el integrador consume el evento; `NotificationSink.put/drain` es **interna del base**. **prerrequisito bloqueante:** `drain_notifications` **no tiene caller hoy** ⇒ **CORE-GAP `H-5` / `AC-07`**: el drenador es el propio `AgentLoop` (y el hook de turn-start **no** sirve — dispara una vez por `run()`, `SEAMS:408`, y su firma 0-arg no admite `(user_id, session_id)`). **orden:** después de `AC-07`; no antes. **aceptación (hoy IMPOSIBLE de pasar, por eso es CORE-GAP):** un subagente background que termina hace que el padre reciba la notificación en el siguiente límite de turno. Lo que A2 validó fue el `put`, no el ciclo.
- **OI-C · Aportar el contexto de sesión (prepend)** *(contrato base común, realización específica)* — **capacidad:** anteponer git-status + fecha + CLAUDE.md al system prompt. **origen:** F1/F2 (GAP-CTX3). **firma:** un provider que aporta a `system_sections` (`build_prepend_context(ctx) -> list[str]`); el loop ya los concatena (`agent_loop.py:211-213`). **cableado:** `agentic_code` = git-status del cwd local + CLAUDE.md del checkout; `agentic_assistant` = git-status del workspace per-tenant (o vacío si no hay checkout) + fecha siempre. **orden:** tras CtxR3 (definir el seam del provider). **aceptación:** un turno en un repo inyecta el bloque git-status; sin repo, sólo la fecha. **nota:** la fecha es **core** (siempre); el git-status/CLAUDE.md es realización por-integrador.
- **OI-D · Atribuir identidad/sesión al id opaco** *(contrato base común — transversal)* — **capacidad:** el integrador setea `user_id`/`session_id` opacos y provee el repo genérico; el runtime no interpreta. **origen:** A+/C1/C2 + `runtime.py:208-209` (autogen a ripear). **firma:** `RuntimeTask.owner_id/session_id` opacos + repo (validado A2·S20). **cableado:** `agentic_code` degenerado corre con defaults minimal; `agentic_assistant` particiona por tenant. **orden:** prerrequisito de persistencia. **aceptación:** el runtime corre sin ver el grafo de identidad (verificado A2: turno sin `user_id` interpretado). *(consolidación formal en A3.DA)*
- **OI-E · Política de attribution/co-autoría de commits** *(específico)* — **capacidad:** decidir la atribución de commits que el agente produce. **origen:** A33 `updateAttributionState` + B7 attribution. **firma:** política del integrador (no hay campo en el ctx). **cableado:** el integrador aplica su política; memoria [[no-claude-coauthorship]] es la del usuario actual (nunca añadir Co-Authored-By de Claude). **orden:** al construir tools de commit (10/05). **aceptación:** los commits siguen la política del integrador, no una embebida en el runtime.

### 2.6 Inversiones — fichas fieles a su tracker y FALSAS hoy *(patrón 4 severo, `A-CIERRE-P4 §9.3`)*

Ninguna de estas se caza comparando las dos caras del par (**coinciden**): sólo cruzando cada ficha contra
`DEUDA-A` / `DEUDA-B` / `BATTERIES` / `SEAMS` / `P0` / `P1`. **6 de 64 = 9,4 %** (en línea con el 8,3 % de 02 y el
11 % de 05).

| # | ficha | decía (fiel al tracker) | estado real hoy | fuente que lo invierte |
|---|---|---|---|---|
| **I1** | `B9` · §2.1 `NotificationSink` · `OI-B` | «el integrador **la drena** y renderiza»; validada en A2 | **`existe-put-sin-drain` = CORE-GAP `H-5`**: `drain_notifications` no tiene caller; el drenador es el `AgentLoop` (`AC-07`), no el integrador; el turn-start hook dispara **1 vez por `run()`**, no por turno | `SEAMS:54/:381/:404/:408/:517` |
| **I2** | `A4` · CtxR5 | `ToolUseContext` gana **`agent_type`**, poblado por el runner | la firma **decidida** es **`subagent_type: str \| None`** (`ID-5`), con **consumidor nombrado**: `MemoryStore._scope` → `subagent_type or ("main" if not is_subagent else agent_id)` — remedia `H-1` | `DEUDA-A:472-481` |
| **I3** | `B2` · §2.4 | «ripear el hack `native["plan_mode"]`» como higiene | es **`DB-19` · BORRAR secuenciado tras `K1`**; y la parte `PlanModeProvider()` incondicional (`factory.py:146`) se recategorizó a **decisión de composición**, no deuda | `DEUDA-B:201`, `:480`; `BATTERIES §6·CAT-h3` |
| **I4** | `A+` · §2.4 | «ripear el autogen» como barrido suelto | se **ejecuta DENTRO de la remediación de `H-1`**, no como barrido | `DEUDA-B:314` |
| **I5** | `D2` | «cablear `to_llm` o borrarlo» (pendiente abierto) | **decidido**: pasa a **`S31.sanitize` con estado ENTRE chunks** (fija `CG-V4`/`FIND-VOICE1`); **`S12` corregida a `existe-parcial`** | `BATTERIES:253` |
| **I6** (leve) | §2.2 | batteries nombradas sin ID | IDs canónicos **B05/B15/B16/B08 (+B22)**; y **03 origina 0 propias** | `BATTERIES:97/:100/:122/:141/:167` |

**Propagación aguas abajo — 3 defectos en la capa consolidadora `00-INTEGRADORES.md`** (destino: la pasada de
consolidación de `§1.x` que P4–P7 alimenta, con precedencia declarada *P4-P7 antes de consolidar*):

- **`P4-03-P1`** — `§1.7:181` resume los OI de 03 como *«poblar el contexto que el base no hornea (presentación,
  estado de ficheros, attachments)»*: **no corresponde a ninguna** de las cinco obligaciones reales
  (`OI-A` render · `OI-B` notificaciones · `OI-C` prepend · `OI-D` identidad · `OI-E` attribution). «estado de
  ficheros» y «attachments» son **inventados** en el resumen — el 3er salto de destilación también inventa.
- **`P4-03-P2`** — **colisión de IDs**: `OI-A`/`OI-B` se reusan en `§1.7:185` para `10·tools-native`. Los OI son
  per-categoría y el consolidador los mezcla sin prefijo ⇒ **prefijar `OI-03-A`…** en la consolidación.
- **`P4-03-P3`** — `§1.4` sigue afirmando que el runtime *«no se auto-drena»* con aceptación *«un subagente
  background completado notifica al padre en el siguiente límite de turno»* (rancio vs `H-5`, misma inversión I1),
  y `§1.6:165` sigue llamando `B-02` a lo que es `DB-19` (I3).

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (64)

| ID | TIER | destino | cara | evidencia | detalle | nota-identidad |
|---|---|---|---|---|---|---|
| A1 | T2-BASE-MECANISMO | `context/tool_use.py` | base | ensamblador `tool_use.py:44` abierto (`messages`) | sí (§1·A) | — |
| A2 | T2-BASE-MECANISMO | base + loop/dispatcher | base | ensamblador `agent_loop.py:173/186/227`+`dispatcher.py:54` abiertos | sí (§2.1) | eje ejecución |
| A3 | T2-BASE-MECANISMO | `context/tool_use.py` | base | ensamblador `fork/__init__.py:69` abierto (`agent_{uuid}`) | sí (§1·A) | eje ejecución · id opaco |
| A4 | T2-BASE-MECANISMO (cableado-gap) | base + 05 | ambas | ensamblador `fork:55/85-93`+`tool_use.py:33-55` abiertos (ausente) | sí (CtxR5/OI) | eje ejecución |
| A5 | T2-BASE-MECANISMO (home 10)+fork | →10·R0 + `ForkSnapshot` | base | ensamblador `tool_use.py`+`fork:31-46` abiertos (ausente) | sí (CtxR1/→10) | — |
| A6 | T2-BASE-MECANISMO | `context/tool_use.py` | base | ensamblador `tool_use.py:46/61-64` abierto (app_state mutable) | sí (§1·A, 🔀 L10) | — |
| A7 | T2-COSTURA (home 05) | →05·execution | base | tracker-leído | sí (→05) | eje ejecución |
| A8 | T2-COSTURA (home 05) | →05·fork | base | ensamblador `fork:80-83` abierto | sí (§1·A) | eje ejecución |
| A9 | T2-BASE-MECANISMO | base + loop | base | ensamblador `agent_loop.py:195-196` abierto (reensamblado) | sí (§1·A) | — |
| A10 | T2-COSTURA + BATTERY commands | →12 + 01·CTR-12 | ambas | tracker-leído (GAP-01 homed 01) | sí (→12/OI-A) | — |
| A11 | T1-MOTOR (home 16) | →16·models | base | tracker-leído | sí (→16, 🔀 L10) | — |
| A12 | T1-MOTOR (home 16) | →16·models | base | tracker-leído | sí (→16) | — |
| A13 | T2-COSTURA (home 11) | →11·mcp | base | ensamblador `fork:46/78` abierto (capabilities hereda) | sí (→11/CtxR7) | — |
| A14 | T2-COSTURA (home 05) | →05·execution | base | tracker-leído | sí (→05, 🔀 L10) | — |
| A15 | T2-BASE-MECANISMO (home 05) | →05·execution | base | tracker-leído | sí (→05) | — |
| A16 | T1-MOTOR (home 16) | →16·models | base | ensamblador `agent_loop.py:233-234` abierto (`system_override`) | sí (→16, 🔀 L10) | — |
| A17 | CLI-ONLY/INTERFAZ | INTEGRADOR | integrador | tracker-leído | sí (OI-A) | — |
| A18 | T2-BASE-MECANISMO (ajuste diferido) | base (opcional) | base | tracker-leído | sí (§1·A) | — |
| A19 | T2-COSTURA (home 10) | →10·tools-native | base | tracker-leído | sí (→10) | — |
| A20 | T2-COSTURA (home 06) | →06·permissions | base | tracker-leído | sí (→06) | — |
| A21 | T2-COSTURA (home 06) | →06·permissions | base | tracker-leído | sí (→06) | — |
| A22 | T2-BASE-MECANISMO (home 02) | →02·loop (B2) | base | tracker-leído | sí (→02) | — |
| A23 | T2-BASE-MECANISMO (fork) | `ForkSnapshot`(CtxR4)+16 | base | ensamblador `fork:31-46` abierto (ausente) | sí (CtxR4) | eje ejecución |
| A24 | BATTERY memory (home 13) | →13·memory | base | tracker-leído | sí (→13) | — |
| A25 | BATTERY skills (home 12) | →12·skills | base | tracker-leído | sí (→12) | — |
| A26 | T2-COSTURA (home 06) | →06·permissions | base | tracker-leído | sí (→06) | — |
| A27 | ⛔-nombrado (teams) | ⛔ 02·E3 | — | tracker-leído | N/A (⛔ nombrado) | — |
| A28 | ⛔-nombrado (ant-exp) | ⛔ fuera de core | — | tracker-leído | N/A (⛔ nombrado) | — |
| A29 | T2-BASE-MECANISMO (depth,05)+⛔(chainId) | →05 + ⛔ chainId | base | ensamblador `runtime.py:204/316` abierto (depth) | sí (→05) | eje ejecución |
| A30 | CLI-ONLY/INTERFAZ | INTEGRADOR | integrador | tracker-leído | sí (OI-A) | — |
| A31 | T2-COSTURA (home 11) | →11·mcp | base | tracker-leído | sí (→11) | — |
| A32 | BATTERY tool (`AskUserQuestion`) | →10·tools-native | ambas | tracker-leído | sí (→10, 🔀 L10) | — |
| A33 | CLI-ONLY/INTERFAZ (13)+behavior(2) | INTEGRADOR + 10(undo) + política(attr) | integrador | tracker-leído | sí (OI-A/OI-E) | — |
| A+ | mixto (extensión B, no deuda L10) | base + costuras + T3(user_id) | ambas | ensamblador `runtime.py:315-321` abierto (poblado) | sí (§1·A/OI-D) | **persist+ejec · id opaco+repo** (user_id) |
| B1 | T2-BASE-MECANISMO | `context/tool_use.py` | base | ensamblador `tool_use.py:23-30` abierto (3 bolsas) | sí (§1·B, 🔀 L10) | — |
| B2 | T1-CONTRATO (mode) + DEUDA-B | →01·CTR-08 + gate + DEUDA-B | ambas | tracker-leído (raíz 01·CR1) | sí (CtxR2) | — |
| B3 | T2-COSTURA (home 11) | →11·mcp | base | tracker-leído | sí (→11) | — |
| B4 | BATTERY (home 10) | →10·tools-native | base | tracker-leído | sí (→10) | — |
| B5 | T2-BASE-MECANISMO (home 05) | →05·execution | base | tracker-leído | sí (→05) | eje ejecución |
| B6 | BATTERY hooks (home 06) | →06·hooks | base | tracker-leído | sí (→06) | — |
| B7 | T2-BASE-MECANISMO (undo,10)+INTEGRADOR(attr) | →10 + INTEGRADOR | ambas | tracker-leído | sí (→10/OI-E) | — |
| B8 | T2-COSTURA (home 05) | →05·execution | base | tracker-leído | sí (→05) | — |
| B9 | T2-COSTURA (`NotificationSink`,05)+11+⛔ | →05 + →11 + ⛔ inbox | ambas | A2·S21 (canal validado) + tracker-leído | sí (OI-B) | eje persist+ejec (keyed) |
| B10 | T1-MOTOR (home 16) | →16·models | base | tracker-leído | sí (→16) | — |
| B11 | T2-COSTURA (commands)+BATTERY plan | →14·plan + 01·CTR-12 | ambas | tracker-leído | sí (→14/OI-A) | — |
| B12 | CLI-ONLY/INTERFAZ + ⛔-nombrado | INTEGRADOR + ⛔ satélites | integrador | tracker-leído | sí (OI-A, 🔀 L10) | — |
| C1 | T2-COSTURA (adapter, extensión B) | `context/adapters.py` | base | ensamblador `adapters.py:11-48` abierto | sí (§1·C) | eje persistencia |
| C2 | T2-COSTURA (adapter inverso) | `context/adapters.py` | base | ensamblador `adapters.py:51-57` abierto | sí (§1·C) | eje persistencia |
| C3 | DEUDA-B (andamiaje) | DEUDA-B (borrar) | base | ensamblador `adapters.py:60-78`+`agent_loop.py:332-335` abiertos | N/A (DEUDA-B/CtxR6) | — |
| D1 | T2-COSTURA (`PathPresentation` default) | costura + default | base | ensamblador `presentation.py:15-23` abierto | sí (§1·D) | — |
| D2 | T2-COSTURA + DEUDA-B (`to_llm`) | costura + DEUDA-B | base | ensamblador `dispatcher.py:42` abierto (`sanitize_output`) + `presentation.py:18` (`to_llm` def) | sí (§2.4, L10) | — |
| E1 | T2-BASE-MECANISMO (home 05) | →05·fork | base | ensamblador `fork:64-93` abierto | sí (→05) | eje ejecución |
| E2 | T2-BASE-MECANISMO (home 05) | →05·fork | base | ensamblador `fork:73-78` abierto (inherit) | sí (→05) | eje ejecución |
| E3 | T2-BASE-MECANISMO (home 05) | →05·fork | base | ensamblador `fork:69` abierto | sí (→05) | eje ejecución · id opaco |
| E4 | T2-COSTURA (home 05) | →05·fork | base | ensamblador `fork:80-83` abierto | sí (→05) | eje ejecución |
| E5 | T2-BASE-MECANISMO (filtro toolset) | →05 + →06 | base | ensamblador `resolver.py:45-48`+`registry.py:32-33` abiertos | sí (§1·E, 🔀 L10) | eje ejecución |
| E6 | T2-BASE-MECANISMO (home 02) | →02·loop (B2) | base | tracker-leído (=A22) | sí (→02) | — |
| E7 | T2-BASE-MECANISMO (fork) | `ForkSnapshot`(CtxR4)+16 | base | ensamblador `fork:31-46` abierto (ausente) | sí (CtxR4, =A23) | eje ejecución |
| E8 | T2-BASE-MECANISMO (home 05) | →05·execution | base | ensamblador `runtime.py:204/316` abierto | sí (→05) | eje ejecución |
| F1 | T2-BASE-MECANISMO (prepend)+T2-COSTURA+INTEGRADOR | `session_context`(CtxR3)+provider | ambas | ensamblador `agent_loop.py:211-213/228-229` abierto (seam existe, provider no) | sí (CtxR3/OI-C) | — |
| F2 | BATTERY memory (home 13)+T2-BASE (fecha) | →13 + `session_context` | ambas | ensamblador `agent_loop.py:218` abierto (`_inject_recall`) | sí (CtxR3/OI-C) | — |
| F3 | =F1 + ⛔-nombrado (cache-breaker) | =F1 + ⛔ ant-debug | base | tracker-leído | sí (=F1) | — |
| F4 | ⛔-nombrado (ant-debug) | ⛔ fuera de core | — | tracker-leído | N/A (⛔ nombrado) | — |
| F5 | T2-BASE-MECANISMO (home 16) | →16·models (cacheo) | base | tracker-leído | sí (→16) | eje persistencia |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../03-context.md`?** — **Sí**, líneas 1→313 (encabezado + naturaleza + evidencia + tablas A/B/C/D/E/F + resumen + gaps priorizados + notas 2/3 + §remediación CtxR1-CtxR7 + ledger de cierre 2ª vuelta + 4 preguntas).
2. **¿Reconcilia el conteo?** — findings en `../03-context.md` = **64** (A1-A33=33 + A+=1 + B1-B12=12 + C1-C3=3 + D1-D2=2 + E1-E8=8 + F1-F5=5); colocados = **64**; sin colocar = **0**. ✅
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, re-abierto en ESTE ciclo contra el runtime real:** A2 `agent_loop.py:173/186/227`+`dispatcher.py:54`; A9 `agent_loop.py:195-196`; A6/C3 `agent_loop.py:332-335`+`adapters.py:60-78`; A16 `agent_loop.py:233-234`; D1/D2 `dispatcher.py:42`+`presentation.py:15-23`; A+/E8/A29 `runtime.py:204/315-321`; E5 `resolver.py:45-48`+`registry.py:32-33`; E1-E4/A3/A8 `fork/__init__.py:64-93`; A13 `fork:46/78`; C1/C2 `adapters.py:11-57`; B1 `tool_use.py:23-30`; F1/F2 seam `agent_loop.py:211-218/228-229`. Las **ausencias** (A4/A5/A23/E7 = campos que NO existen) se confirmaron abriendo `tool_use.py`/`fork:31-46` (ausencia leída en fuente, no grep). Los homed-fuera puros (→05/06/10/11/12/13/16) se colocan con destino nombrado y `tracker-leído` — no afirman cableado de B **en 03**, sino que su cableado se verifica en su categoría-hogar (L07).
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla 5 obligaciones (OI-A render / OI-B notificaciones / OI-C prepend / OI-D identidad / OI-E attribution) con los 6 campos L05; ningún finding cerrado con "→ integrador" a secas.
5. **¿Doble filo (L10)?** — **Sí**: ningún ❌ disfrazado de 🔀 (FIND-CTX1/GAP-CTX3 se mantienen ❌/CORE-GAP; GAP-CTX2/CTX4/FIND-CTX2 son 🟡 reales con remediación). Ninguna deuda inflada: los ~55 campos de B12 y las 15 UI-callbacks de A33 **NO** se cuentan como deuda A↔B — son capa de interfaz (→INTEGRADOR) o satélites de producto (→⛔ nombrado), por arquitectura single-user del canónico. Las extensiones B sin contraparte (A+, C1/C2, D2·`to_llm`) → **NO deuda A↔B** (D2·`to_llm` = DEUDA-B interna).

### 3.2b Adenda de `A-CIERRE · P4″` (par 03, 2026-07-28) — lo que las 5 preguntas de arriba NO cubrían

1. **Q1 se sostiene, pero mal orientada.** La lectura 1→313 fue real; lo que faltaba era **PARA QUÉ**: se leyó
   para *repartir* findings, no para *reconciliar celda a celda*. En esta pasada el tracker se reabrió 1→313 y el
   destilado 1→256 con esa segunda pregunta ⇒ aparecieron **11 pérdidas** que la primera lectura no buscaba.
2. **Q2 era correcta y ahora está VERIFICADA sumando sus propios addendos** (consecuencia 11 de `§9.7`):
   33+1+12+3+2+8+5 = **64** ✅. A diferencia de `02` (declaraba 54, reales 60), aquí no hay error aritmético que
   propagar.
3. **Q3, releída como «¿abrió el tramo Y identificó al PRODUCTOR?»** — **falla en 1 de 6 costuras**: `B9`/§2.1
   afirmaba consumidor («el integrador drena») sin que exista **ningún caller** de `drain_notifications`. Abrir el
   punto de registro no acredita que alguien registre (I1). Las otras 5 mantienen productor identificado.
4. **Q4 se sostiene en detalle, pero `OI-B` tenía el criterio de aceptación INSATISFACIBLE** (I1) y `OI-A`/`OI-B`
   **colisionan de ID** con los de `10` en el consolidador (`P4-03-P2`).
5. **Q5 (doble filo) — FALSO NEGATIVO parcial, igual que en 02:** no detectó ninguna de las 6 inversiones, porque
   busca ❌-disfrazado-de-🔀 **dentro del par**, y las inversiones viven **fuera** (en los rollups posteriores).
6. **Agujero de esquema confirmado 3/3** (consecuencia 12): el tracker traía **§Evidencia ejecutada** con 3 nombres
   de `xfail(strict)` y anclas canónicas; el destilado tenía **0 nombres de test**. Restituido en **§1.0**.
7. **Patrón 3 confirmado 4/4** (`P4-01-1`): el tracker tiene columna *Campo canónico* sin sucesora en SEPARACION;
   citas `.ts` **30 → 4**. Anclas canónicas restituidas en **§1.0** como *punteros acreditados*, **no** como la
   tabla de comportamientos que exige `D-02` (eso es P6″).

### 3.3 VEREDICTO
**(veredicto original del ciclo A3, conservado)** **✅ NADA PENDIENTE → A3·10·tools-native (siguiente ciclo del checklist §7).**
Los 64 findings repartidos con TIER+destino; **5 CORE-GAPs originados en 03** para DEUDA-A (FIND-CTX1→10·R0+CtxR1, GAP-CTX2→01·CTR-08+CtxR2, FIND-CTX2→CtxR5, GAP-CTX3→CtxR3, GAP-CTX4→CtxR4); **4 DEUDA-B** (C3 andamiaje, D2·`to_llm`, B2·hack plan_mode, A+·autogen id); **6 costuras** nombradas con productor/consumidor; **5 obligaciones de integrador** con detalle simétrico. Cabos con destino explícito (05·execution: A7/A8/A14/A15/B5/B8/E1-E8; 06·permissions: A20/A21/A26/B6; 10·tools-native: A19/A32/B4/B7·undo; 11·mcp: A13/A31/B3; 12·skills: A10/A25; 13·memory: A24/F2; 14·plan: B11; 16·models: A11/A12/A16/B10/F5; 02·loop: A22/E6; transversal A3.DA: A+·user_id) — ninguno es pendiente de **verificación** (cada uno se verificará en su categoría-hogar; el cableado interno a 03 se re-abrió aquí, Q3).

**VEREDICTO VIGENTE tras `A-CIERRE · P4″` (2026-07-28):** el reparto se sostiene; **la caracterización de 6 fichas
no** (§2.6). Saldo de la reconciliación: **64/64 = 46 conservadas · 7 enriquecidas · 11 comprimidas-con-pérdida ·
0 INVENTADAS · 0 perdidas**; las 11 pérdidas **remediadas in situ** (`P4-03-1..11`), las 6 inversiones registradas
en §2.6, y **3 defectos de propagación emitidos contra `00-INTEGRADORES`** (`P4-03-P1..P3`, destino = la pasada de
consolidación de `§1.x`). Lo que **NO** queda verificado y no se disimula: la **tasa DR-2** de esta categoría
(comportamientos canónicos que nunca entraron ni al tracker) **sigue sin medir** — sólo es atacable en **P6″**
abriendo `Tool.ts`/`AppStateStore.ts`/`forkedAgent.ts`/`context.ts`, y **§1.0 son punteros, no la tabla `D-02`**.
