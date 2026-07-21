# 09 · tools (infra) — homologación

Contrasta la **infraestructura de tools** del runtime (`tools/{protocol,registry,native_registry,
factory,pool,dispatcher,deferred*,exec_env,fs_env}.py`) contra el core canónico de tools:
`Tool.ts` (792, el tipo `Tool` + `ToolResult` + `ToolUseContext` + `buildTool`/`TOOL_DEFAULTS`),
`tools.ts` (389, `getAllBaseTools`/`getTools`/`assembleToolPool`/`filterToolsByDenyRules`),
`tools/utils.ts`, `utils/toolSearch.ts` (757) + `tools/ToolSearchTool/{ToolSearchTool.ts(471),prompt.ts}`
(deferred/tool-search), `utils/permissions/filesystem.ts` (1778) + `utils/path.ts` (155)
(path guards), y la costura de sandbox (`utils/sandbox/sandbox-adapter.ts` → paquete externo
`@anthropic-ai/sandbox-runtime`, `utils/Shell.ts`).

**Contrapartes leídas ÍNTEGRAS**: `Tool.ts` (792 — releído por los campos de INFRA de la tool,
no sólo `ToolUseContext` como en 03/08), `tools.ts` (389), `tools/utils.ts` (40), `utils/toolSearch.ts`
(757), `ToolSearchTool.ts` (471), `ToolSearchTool/prompt.ts` (122), `utils/path.ts` (155),
`utils/permissions/filesystem.ts` (1778, path-guards + safety layer), cabecera de `sandbox-adapter.ts`.
Runtime: los 12 archivos infra ÍNTEGROS + cableado en `loop/agent_loop.py:85-234` +
`tools/native/tool_search.py`.

## Tesis arquitectural

El canónico **no tiene una capa `tools/` reificada**: el "protocolo" de tool es el enorme tipo
estructural `Tool` (~60 campos/métodos, la mayoría de RENDER React) construido por `buildTool` con
`TOOL_DEFAULTS`; el "registry" es la función `getAllBaseTools()` (lista con gating por
`feature()`/`USER_TYPE`/env); el "pool" es `assembleToolPool()` (uniqBy + sort per-partición); la
"ejecución" vive dispersa en `StreamingToolExecutor.ts`/`toolExecution.ts` (08). El runtime **reifica
cada uno de esos roles en una clase/módulo** (`ToolProtocol`, `ToolRegistry`, `ToolPool`,
`ToolDispatcher`) — decisión de desacople correcta. La homologación aquí es **del contrato mínimo**:
qué del comportamiento canónico (no del render) captura cada seam reificado.

Dos ejes de divergencia estructural, ambos por diseño y en general acertados:
1. **`ToolProtocol` es un subconjunto de 8 miembros** frente al `Tool` de ~60. Lo omitido se parte en:
   (a) render/UI → ⛔ correcto; (b) **comportamiento real omitido** → los ❌/🟡 de este doc
   (`isConcurrencySafe`, `interruptBehavior`, `checkPermissions` por-tool, `validateInput`,
   `newMessages`/`contextModifier` en el resultado, `getPath`, `maxResultSizeChars`, `outputSchema`,
   `aliases`, `searchHint`, `isDestructive`).
2. **La política se saca del tool y se pone en seams inyectables** (`ctx.fs` confinamiento,
   `ctx.exec_env` backend shell, `permission_context` deny/allow). Homologación **de comportamiento**,
   no de forma — el integrador (agentic_assistant server-side) provee la política.

El runtime **AÑADE** dos cosas que el canónico no tiene y que son valor propio: `NativeDeferredStrategy`
(defer_loading server-side para gpt-5/Responses, no sólo el `tool_reference` de Anthropic) y la costura
`ToolExecEnvironment` (backend de shell inyectable: local/bwrap/remoto).

## Leyenda

✅ homologado · 🟡 parcial · 🔀 diferente (deliberado o a revisar) · ❌ no portado · ⛔ N/A core (UI/terminal).

---

## A · Contrato de tool (`protocol.py::ToolProtocol`/`ToolResult`/`ToolCategory` vs `Tool.ts`)

| # | Feature canónica (`Tool.ts`) | Estado | Nota / diferencia / ajuste |
|---|---|---|---|
| A1 | `name` / `description` / `inputSchema` (zod) | ✅ | Runtime: `name`/`description` (str) + `input_schema` (dict JSON-Schema). Validado por `agentic_models.validate_tool_arguments` (≈ zod parse). Equivalente. |
| A2 | `description(input, opts)` **async, función del input** + `prompt(opts)` (schema-desc) | 🔀 | Runtime: `description` es **atributo str estático**, no función del input ni del permission-context. El canónico compone la descripción por-input (p.ej. Bash renderiza el comando) y separa `prompt()` (texto de schema) de `description()` (UI). El runtime colapsa ambos en un str fijo. Suficiente para anunciar el schema; pierde descripción dependiente de input. |
| A3 | `isConcurrencySafe(input)` | ❌ | **No existe en `ToolProtocol`.** El canónico lo usa para correr tools concurrency-safe **en paralelo** (`StreamingToolExecutor`). El runtime NO tiene modelo de concurrencia (D6) → el flag no tendría consumidor aún, pero es prerequisito. Ajuste: añadir `is_concurrency_safe: bool` (o método) al protocolo + honrarlo en el dispatcher. |
| A4 | `interruptBehavior(): 'cancel'\|'block'` (default `block`) | ❌ | **Aterriza FIND-SIG4.** No existe en `ToolProtocol`. Define qué pasa si el usuario manda mensaje mientras la tool corre: `cancel` (matar+descartar) vs `block` (seguir, mensaje espera). El runtime sólo tiene `ctx.stop` binario. Ajuste ARQUITECTURAL: añadir `interrupt_behavior()` al protocolo; consumirlo cuando exista pausa/interrupción in-turn (crecer `ctx.stop`, ver 08·SIG-recomendación). |
| A5 | `isEnabled()` | 🟡 | Runtime: no hay `isEnabled()` por-tool; el registry lista TODO. El canónico filtra `getAllBaseTools().filter(isEnabled)`. Sin él, un tool gated (env/flag) no puede autodeshabilitarse. Hoy el gating lo hace el integrador al elegir qué registrar (`create_tools(extras)`), no el tool. Ajuste: `isEnabled()` opcional en el protocolo. |
| A6 | `isReadOnly(input)` | ❌ | No existe. El canónico lo usa en permisos (read implica menos fricción) y en sandbox. El runtime deriva "requiere permiso" de `requires_permission` (bool grueso). Ajuste liga GAP-02. |
| A7 | `isDestructive(input)` (default false) | ❌ | No existe. Marca ops irreversibles (delete/overwrite/send) — justo lo que la política del harness (“hard to reverse”) confirmaría. Ajuste: `is_destructive()` opcional; lo consume el gate de permisos/confirmación. |
| A8 | `checkPermissions(input, ctx): PermissionResult` **por-tool** | ❌ | El canónico da a cada tool su lógica de permiso específica (devuelve allow/ask/deny + `updatedInput` + `suggestions`). El runtime tiene sólo `requires_permission: bool` + chequeo de nombre en el dispatcher (`allowed_names()`). **Gran gap, liga GAP-02 + FIND-HOOK3/5.** Ajuste: método `check_permissions(input, ctx) -> PermissionDecision` en el protocolo, o mantener la política fuera pero pasar `input` al gate (hoy el gate ni ve el input). |
| A9 | `validateInput(input, ctx): ValidationResult` | 🟡 | Runtime: sólo validación de **schema** (`validate_tool_arguments`). El canónico añade `validateInput` **específico del tool** (reglas semánticas: p.ej. path existe, rango válido) con `errorCode`. Ausente → un input schema-válido pero semánticamente inválido llega a `execute()`. Ajuste: `validate_input()` opcional. |
| A10 | `getPath(input)` | 🔀 | El canónico expone el path de la tool para los checks de permiso read/write. El runtime NO; en su lugar empuja el confinamiento a `ctx.fs.resolve(token, for_write=)` **dentro** de cada fs-tool (G). Decisión deliberada (política fuera del permiso central). Consecuencia: el gate central no conoce el path → no puede aplicar reglas allow/deny por-ruta antes de ejecutar. |
| A11 | `aliases` + `toolMatchesName`/`findToolByName` | ❌ | Runtime: `pool.find`/`registry.resolve` comparan `t.name == name` exacto; **sin aliases**. El canónico permite renombrar una tool conservando el nombre viejo. Menor, pero rompe compat si se renombra una nativa. Ajuste: `aliases` opcional + comparación vía helper. |
| A12 | `searchHint` (frase 3-10 palabras para ToolSearch) | 🟡 | No existe. El canónico lo puntúa alto en `searchToolsWithKeywords` (peso 4). Sin él, el keyword-search del runtime (E) sólo matchea nombre+description. Calidad de descubrimiento inferior. |
| A13 | `shouldDefer` / `alwaysLoad` / `isMcp` (deferral) | 🟡 | Ver E1. Runtime: `is_deferred_tool` = `getattr(tool,'deferred',False)` + ToolSearch nunca. Falta `alwaysLoad` (opt-out), falta `isMcp`-siempre-diferida (el adaptador MCP debe setear `deferred=True` a mano → verificar en 11), faltan carve-outs Agent/Brief. |
| A14 | `maxResultSizeChars` (persistir a disco si excede) | ❌ | No existe. El canónico persiste resultados grandes a disco y devuelve preview+path (evita reventar el contexto). Liga 02·budget/`contentReplacementState`. Ajuste: fuera del protocolo mínimo o como metadato; hoy `ToolResult.output` es str sin cota. |
| A15 | `outputSchema` (structured output) | ❌ | No existe. Liga G3 (structured output, 05/09/16) + `SyntheticOutputTool`. Ajuste diferido. |
| A16 | `backfillObservableInput` / `toAutoClassifierInput` / `inputsEquivalent` | ❌/⛔ | `backfill` (mutar copia observable del input) y `toAutoClassifierInput` (input para el clasificador de auto-mode) no existen → ❌ pero ligados a auto-mode/observabilidad (política). `inputsEquivalent` ⛔ (dedup UI). |
| A17 | `isSearchOrReadCommand`/`isOpenWorld`/`requiresUserInteraction`/`isLsp`/`isTransparentWrapper` | ⛔ | Clasificación para UI/colapso de render. Fuera de alcance core. |
| A18 | `render*` (≈15 métodos: `renderToolUseMessage`, `renderToolResultMessage`, `renderGroupedToolUse`, `renderToolUseProgressMessage`, `renderToolUseRejected/ErrorMessage`, `renderToolUseTag`, `getActivityDescription`, `userFacingNameBackgroundColor`, `getToolUseSummary`, `extractSearchText`, `isResultTruncated`…) | ⛔ | Todo React/ink/terminal. El runtime delega presentación a `ctx.presentation` (sanitize_output) + al integrador. Correctamente omitido. |
| A19 | `userFacingName(input)` | 🔀 | Canónico: nombre para UI (default = `name`). Runtime: no lo modela; `ToolResult.tool_name` lleva el nombre. Menor. |
| A20 | `preparePermissionMatcher(input)` (hook `if`) | 🔀 | Delegado a 06·hooks (matcher de condiciones `if` de permission-rule). No es del protocolo mínimo. |
| A21 | `buildTool` + `TOOL_DEFAULTS` (fail-closed: `isConcurrencySafe→false`, `isReadOnly→false`, `checkPermissions→allow`, `isEnabled→true`) | 🔀 | El runtime no tiene builder con defaults; cada nativa implementa el `ToolProtocol` a mano (atributos de clase). Sin defaults centralizados, pero el protocolo mínimo es tan chico que el riesgo de drift es bajo. Nota: el default canónico `checkPermissions→allow` explica por qué el gate del runtime (deny-por-nombre) es más restrictivo que el canónico por defecto. |

### `ToolResult` (runtime) vs `ToolResult<T>` (canónico, `Tool.ts:321`)

| # | Feature | Estado | Nota |
|---|---|---|---|
| A22 | `output: str` + `is_error`/`is_timeout`/`is_aborted` + `metadata` | 🔀 | Runtime: resultado plano de texto + flags. Canónico: `data: T` **tipado** + `mapToolResultToToolResultBlockParam` que serializa a `tool_result` block. El runtime aplana a str en la tool. Equivalente para el modelo, pierde el dato tipado (liga A15 output schema). |
| A23 | `newMessages?: Message[]` (la tool inyecta mensajes a la conversación) | ❌ | **No portado.** El canónico deja que una tool empuje `user/assistant/attachment/system` messages al historial (p.ej. attachments, recordatorios). El runtime no tiene canal: `execute()` sólo devuelve `output`. Ajuste: `ToolResult.new_messages: list[dict]` aplicado por el dispatcher/loop. |
| A24 | `contextModifier?: (ctx)=>ctx` (sólo tools NO concurrency-safe) | 🟡 (**CORR en 10·J**) | **Corregido**: el loop SÍ aplica `context_modifier` vía `getattr` (`agent_loop.py:329-337`), consumido por plan_mode/worktree/config/todo_write; y `ends_turn` (338-339) por ask_user/exit_plan. El campo NO está declarado en `ToolResult` (se adjunta dinámico `# type: ignore`), sin gating por `is_concurrency_safe==False`. Sigue ❌ sólo `new_messages` (A23). Ver 10·J. |
| A25 | `mcpMeta` (`_meta`/`structuredContent` passthrough) | ❌ | No portado. Metadatos MCP para consumidores SDK. Liga 11. |
| A26 | `ToolResult.aborted(name)` sintético | 🟡 | **SIG10 aterriza.** Runtime: `aborted()` produce `"aborted: <name>"` + `is_aborted=True`. Canónico: 3 sintéticos distintos (`CANCEL_MESSAGE`/`REJECT_MESSAGE`/sibling) con `tool_use_id` + `withMemoryCorrectionHint`. El runtime aplana a un str genérico sin razón ni pareo. Ajuste liga 08·SIG10 + FIND-L1. |

---

## B · Registry + factory (`registry.py`/`native_registry.py`/`factory.py` vs `tools.ts`)

| # | Feature | Estado | Nota |
|---|---|---|---|
| B1 | `create_tools(extras)` → lista fija de 25 nativas | 🔀 | Canónico `getAllBaseTools()`: lista con **gating** masivo (`feature('KAIROS'/'COORDINATOR_MODE'/…)`, `USER_TYPE==='ant'`, env). El runtime registra TODO incondicionalmente; el gating lo hace el integrador vía `extras`/no-registrar. Deliberado (provider-agnostic). Consecuencia: sin `isEnabled()` (A5), no hay auto-gating por flags. |
| B2 | **Dos registries**: `ToolRegistry` (factory/loop) vs `NativeToolRegistry` (con `unregister_by_prefix`) | 🟡 | Solapamiento estructural (hermano de 01·StorageContract vs StorageProtocol, 05·runner). `factory.create_tools` devuelve `ToolRegistry`; el loop usa `_tool_registry.list_available`. `NativeToolRegistry` (con `unregister`/`unregister_by_prefix`, pensado para MCP hot-plug) parece la evolución pero NO lo usa el factory. Ajuste: unificar en uno (el de MCP-aware gana) o documentar el reparto de roles. |
| B3 | `list_available(mode)` filtra `safe_for_background` en background | 🔀 | **GAP-MODE2 aterriza.** Canónico: el filtrado de background NO es un bool por-tool — es el allowlist `ASYNC_AGENT_ALLOWED_TOOLS` + `filterToolsForAgent` (05). El runtime lo modela como `safe_for_background: bool` por-tool. `worktree` tiene `safe_for_background=False` pero el canónico lo INCLUYE en `ASYNC_AGENT_ALLOWED_TOOLS` → discrepancia a reconciliar en 10. Ajuste: reconciliar el bool contra el allowlist canónico tool-por-tool. |
| B4 | `filterToolsByDenyRules` (strip de tools blanket-denied antes del modelo, MCP server-prefix) | 🟡 | Runtime: `assemble_tool_pool` filtra por `permission_context.denied_names()` — **deny por nombre EXACTO**. El canónico usa `getDenyRuleForTool` que matchea reglas MCP server-prefix (`mcp__server` strippea todas las tools del server). Sin eso, no se puede denegar un server MCP entero pre-anuncio. Liga 06/11. |
| B5 | `getTools` modo `CLAUDE_CODE_SIMPLE` (sólo Bash/Read/Edit) | ❌/⛔ | Runtime: sin modo simple. Env-gated del canónico; el integrador lo replicaría filtrando `extras`. Bajo impacto core. |
| B6 | `REPL_ONLY_TOOLS` / `parseToolPreset`/`TOOL_PRESETS` | ⛔/❌ | REPL ⛔ (terminal). Presets `--tools` ❌ menor (entrypoint). |
| B7 | `getMergedTools` (builtins + mcp SIN dedup, para conteo de tokens) | 🔀 | Runtime: sólo el pool ensamblado (dedup). El conteo de tokens para el umbral de tool-search (E) el runtime no lo hace (delega en capability del provider). Liga 16. |

---

## C · Pool assembly (`pool.py::ToolPool`/`assemble_tool_pool` vs `assembleToolPool` en `tools.ts:345`)

| # | Feature | Estado | Nota |
|---|---|---|---|
| C1 | `assemble_tool_pool`: native-precede, sort-by-name **per-partición**, dedup | ✅ | Homólogo fiel de `assembleToolPool` (`uniqBy` + sort per-partición para estabilidad de prompt-cache; builtins como prefijo contiguo). El comentario del runtime cita textual la razón del cache-breakpoint. Native gana en colisión de nombre = `uniqBy` preserva orden de inserción. **Verificado equivalente.** |
| C2 | `ToolPool.find(name)` resuelve del MISMO pool ensamblado | ✅ | Homólogo de `findToolByName(options.tools, name)`. **Confirma el invariante clave** (ver D1): no hay registry aparte para ejecutar; anuncio y ejecución resuelven del mismo pool → deferred = visibilidad, no disponibilidad. Cableado verificado en `agent_loop.py:195-196` (`ctx.tool_pool = build; dispatcher resuelve de ctx.tool_pool`). |
| C3 | `find` sin alias-matching | 🟡 | = A11. `find` compara `tool.name == name`; el canónico usa `toolMatchesName` (name + aliases). |
| C4 | Partición native/capability (`ToolPool(native_tools, capability_tools)`) | ✅ | Espejo del boundary builtin+MCP del canónico, manteniéndose provider-agnostic (las capability tools las aporta el `CapabilityManager`, no el pool). |

---

## D · Dispatcher (`dispatcher.py::ToolDispatcher` vs ejecución canónica `StreamingToolExecutor.ts`/`toolExecution.ts`)

| # | Feature | Estado | Nota |
|---|---|---|---|
| D1 | Resolución por nombre desde `ctx.tool_pool` (no registry aparte) | ✅ | Punto de integración único loop↔tool. Homólogo del modelo canónico. |
| D2 | Abort check antes de trabajo (`ctx.stop.is_set()` → `ToolResult.aborted`) | 🟡 | Existe, pero **binario, sin reason, sin árbol** (08·SIG2/SIG3). No hay cancelación de tool EN VUELO (sólo pre-ejecución + timeout). Liga FIND-SIG3b. |
| D3 | Chequeo de permiso: `requires_permission` + `allowed_names()` | ❌ | **Gran gap, liga GAP-02.** El canónico corre `canUseTool`/`checkPermissions` (PreToolUse hook + permission modes default/acceptEdits/plan/bypass + `updatedInput` + suggestions + clasificador). El runtime hace deny/allow por **nombre**, sin ver el input, sin modos, sin hook. El input ni llega al gate (A8/A10). Ajuste ARQUITECTURAL: cablear el gate a un `PermissionContext` con modos + pasar `input` + disparar PreToolUse (06·FIND-HOOK3). |
| D4 | Validación de schema (`agentic_models.validate_tool_arguments`) | ✅ | ≈ zod parse del canónico. Devuelve `ToolResult.error` con el mensaje de validación. |
| D5 | Timeout global (`asyncio.wait_for(effective_timeout)`) | 🔀 | Runtime: el dispatcher envuelve TODA tool en un timeout (override-call > override-dispatcher > `tool.timeout_seconds`). El canónico NO tiene timeout global — cada tool se autogestiona (Bash tiene el suyo; Read/Grep no timeoutean). Divergencia deliberada (server-side quiere cota dura), pero puede matar tools legítimamente lentas que el canónico deja correr. |
| D6 | **Ejecución concurrente de tools concurrency-safe** | ❌ | **No portado.** El canónico ejecuta en paralelo las tools `isConcurrencySafe` de un mismo assistant turn (`StreamingToolExecutor` con `siblingAbortController`: un error de Bash mata hermanos sin terminar el turno). El runtime dispatcha **una por una** (el loop llama `dispatch` secuencial). Consecuencia: sin A3 (flag) ni cascada sibling (08·SIG3b). Ajuste: modelar ejecución concurrente gateada por `is_concurrency_safe` + árbol de abort per-tool. |
| D7 | Aplicar `newMessages`/`contextModifier` del resultado | ❌ | = A23/A24. El dispatcher devuelve `ToolResult` y el loop sólo appendea `output` a `ctx.messages` (`agent_loop.py:314+`). Ni inyecta `new_messages` ni aplica `context_modifier`. |
| D8 | `except Exception → ToolResult.error` (aplana AbortError) | 🟡 | **SIG12 aterriza.** El canónico distingue `AbortError` (→ PostToolUseFailure con `isInterrupt=true`) de error real. El runtime captura todo en un `error` genérico → un abort en vuelo se reporta como error, no como aborted. Ajuste: detectar `asyncio.CancelledError`/abort y mapear a `ToolResult.aborted`. |
| D9 | Choke point de presentación (`ctx.presentation.sanitize_output`) | 🔀/✅ | Runtime-específico (users/sessions): todo `output` pasa por `sanitize_output` antes de `ctx.messages` Y el EventBus. Bajo identidad = no-op. Comportamiento correcto para el server-side; el canónico no lo necesita (single-user terminal). |
| D10 | `onProgress`/`tool_progress` heartbeat | ❌ | = 07·EVT6. El dispatcher no emite progreso intra-tool. |

---

## E · Deferred loading / tool-search (`deferred.py`/`deferred_strategy.py`/`deferred_delta.py`/`native/tool_search.py` vs `utils/toolSearch.ts` + `ToolSearchTool.ts` + `prompt.ts`)

| # | Feature | Estado | Nota |
|---|---|---|---|
| E1 | `is_deferred_tool` | 🟡 | Runtime: `getattr(tool,'deferred',False)` + ToolSearch nunca. Canónico `isDeferredTool` (prompt.ts:62) tiene precedencia: **`alwaysLoad`→false (primero)**, `isMcp`→true (MCP siempre diferida), ToolSearch→false, carve-outs `FORK_SUBAGENT`(Agent)/`Brief`/`SendUserFile`→false, luego `shouldDefer`. El runtime **no** implementa alwaysLoad, ni isMcp-siempre, ni carve-outs → **el adaptador MCP (11) debe setear `deferred=True` a mano** y no hay forma de opt-out. Ajuste: portar la precedencia a `is_deferred_tool` (leer `alwaysLoad`/`isMcp` de la tool). |
| E2 | `SimulatedDeferredStrategy` (fallback client-side): oculta diferidas no descubiertas, anuncia NOMBRES por `<system-reminder>`, ToolSearch client-side | ✅/🟡 | Homólogo del comportamiento default de `claude.ts` + el `<available-deferred-tools>`/DTD. `owns_search_dispatch()==True`. Comportamiento vigente encapsulado. 🟡 por E4/E5. |
| E3 | `NativeDeferredStrategy` (defer_loading server-side, gpt-5/Responses) | 🔀 (AÑADIDO) | **No tiene contraparte canónica** — el canónico sólo tiene el path Anthropic `tool_reference`. El runtime abstrae ambos tras `DeferredToolStrategy` y elige por `model_caller.supports_native_tool_search(model_id)` (`agent_loop.py:143`). Valor propio del runtime (multi-provider). |
| E4 | `deferred_delta` (compute/render/scan de altas-bajas) | 🔀 | Homólogo de `getDeferredToolsDelta`: reconstruye lo ya anunciado escaneando la historia. **PERO** el canónico escanea **attachments tipados** (`msg.attachment.type==='deferred_tools_delta'`, `addedNames`/`removedNames`) o el prepend `<available-deferred-tools>`, gateado por `isDeferredToolsDeltaEnabled`. El runtime escanea **texto renderizado** de `<system-reminder>` por frase-centinela (`_ADDED_HEADER`) → parseo string-frágil (contrato de parseo acoplado a `render_*`). Ajuste: preferir un attachment/mensaje tipado sobre re-parsear texto. |
| E5 | `extractDiscoveredToolNames` (set descubierto derivado de la HISTORIA: `tool_reference` blocks + `preCompactDiscoveredTools` en el compact-boundary) | 🔀 | **Divergencia de fondo.** El canónico DERIVA el set descubierto del historial (stateless respecto a la conversación). El runtime lo MATERIALIZA como estado de capability scopeado por agente (`ctx.app_state.capabilities['discovered_tools']`, `deferred.py:14`). Consecuencia: (a) sobrevive a compactación sin necesitar carry en el boundary (bien), pero (b) un fork/subagente que clona `ctx` arrastra o no el set según cómo se clone `app_state` (verificar en 05·fork + 11). El canónico carga `preCompactDiscoveredTools` explícito en el boundary; el runtime confía en la persistencia del state. |
| E6 | `ToolSearchTool.call` — `select:` **multi** (`select:A,B,C` coma-separado) | ❌ | Runtime (`native/tool_search.py`): `select:` toma **un solo nombre** (`query[len('select:'):].strip()`, sin split por coma). El canónico soporta multi-select coma-separado + parcial (found/missing). **El propio delta-announce del runtime le dice al modelo que use `"select:<tool_name>"`** — si el modelo pide `select:A,B` falla. Ajuste: portar el split por coma. |
| E7 | `searchToolsWithKeywords` (word-boundary regex, `searchHint` peso 4, MCP-prefix, exact-match fast-path a TODO el set, required `+term`, scoring MCP 12/no-MCP 10) | 🟡 | Runtime: scoring por **substring count** simple (`sum(term in haystack)`), sin word-boundary, sin searchHint (A12), sin prefijo MCP, sin `+required`, sin fast-path a tools ya cargadas. Descubrimiento funcional pero de menor calidad. |
| E8 | Resultado = `tool_reference` blocks (`mapToolResultToToolResultBlockParam`) que la API expande + `pending_mcp_servers` | 🔀 | Runtime: devuelve **JSON con schemas inline** (`{name,description,parameters}`) como texto — coherente con la naturaleza "simulada" (el modelo lee el schema del output). No hay `tool_reference` (eso es la ruta nativa server-side, E3). Sin `pending_mcp_servers` (MCP aún conectando → 11). |
| E9 | `isToolSearchEnabled` (umbral auto:N, `modelSupportsToolReference` haiku, token/char threshold, `isToolSearchToolAvailable`) | 🔀 | **No portado como umbral.** El canónico decide POR REQUEST si diferir según tamaño de las tool-defs vs % del context window (`tst`/`tst-auto`/`standard`), soporte del modelo, y disponibilidad de ToolSearch. El runtime NO calcula umbral: difiere incondicionalmente si hay diferidas, y elige mecanismo por la capability del provider. Simplificación deliberada; pierde el auto-mode (diferir sólo cuando pesa). Liga 16 (conteo de tokens). |
| E10 | `mark_tools_discovered` cableado en `ToolSearchTool.execute` (no en el dispatcher) | ✅ | El descubrimiento se marca dentro del `execute` de la propia tool (`native/tool_search.py`), no en el dispatcher — el `owns_search_dispatch()` sólo decide si el runtime ejecuta la tool client-side. Verificado: mecanismo activo (test_deferred_strategy + test_skill_invocation). |

---

## F · Entorno de ejecución shell (`exec_env.py::ToolExecEnvironment`/`LocalExecEnvironment`/`BwrapExecEnvironment`/`ShellResult`)

Costura **inventada por el runtime** (backend de shell inyectable). Contraparte canónica dispersa:
`utils/Shell.ts` (shell persistente) + `utils/sandbox/sandbox-adapter.ts` (→ `@anthropic-ai/sandbox-runtime`).

| # | Feature | Estado | Nota |
|---|---|---|---|
| F1 | `ToolExecEnvironment` protocolo + inyección vía `ctx.exec_env` | 🔀 (AÑADIDO) | El canónico no abstrae el backend: BashTool habla directo con `Shell.ts`. El runtime lo hace inyectable (local/bwrap/remoto) — necesario para server-side/sandbox. Valor propio. |
| F2 | `LocalExecEnvironment.run_shell` = subproceso fresco por llamada | ❌ | **No hay shell persistente.** El canónico `Shell.ts` mantiene UN shell vivo: `cwd`, variables de entorno y estado de shell **persisten entre llamadas Bash**. `LocalExecEnvironment` hace `create_subprocess_shell` nuevo cada vez → un `cd` en una llamada NO afecta a la siguiente. Aterriza en 10·bash, pero el seam es infra. Ajuste ARQUITECTURAL: backend con shell persistente (o documentar la divergencia como límite conocido). |
| F3 | `BwrapExecEnvironment` (bubblewrap: monta workspace→`/workspace`, ro-binds sistema, `--unshare-all`) | 🔀 | **`sandbox-adapter.ts` (985) leído íntegro.** El canónico NO implementa el motor de sandbox: lo **vendoriza** en el paquete externo `@anthropic-ai/sandbox-runtime` (`BaseSandboxManager`, no está en el repo). `sandbox-adapter.ts` es el GLUE settings→`SandboxRuntimeConfig` + hardening CC-específico, y aporta un contrato MUY por encima del bwrap del runtime: (a) **restricción de red** (`allowedDomains`/`deniedDomains` derivados de reglas `WebFetch(domain:*)`, unix-sockets, proxy http/socks, `SandboxAskCallback` por-host); (b) **fs allow/deny read+write derivados de las reglas de permiso** `Edit`/`Read` por-source (no un allow-set plano); (c) **`SandboxViolationStore`** + `annotateStderrWithSandboxFailures`; (d) **hardening anti-escape**: deny-write a `settings.json`/`.claude/skills`, scrub de bare-git-repo plantado (`scrubBareGitRepoFiles`, #29316), write al main-repo en worktrees; (e) `wrapWithSandbox(command)` + `excludedCommands` + `autoAllowBashIfSandboxed` + gating por plataforma/deps + refresh dinámico en cambio de settings. El `BwrapExecEnvironment` del runtime es **aislamiento grueso** (mount workspace + ro-binds, sin nada de a–e). Divergencia conocida 🔀; si se necesita paridad, envolver un motor real. Nota: el motor bwrap/seatbelt no es contraparte del REPO — la contraparte de infra de 09 es el adaptador (política) + `exec_env.py` (mecanismo). |
| F4 | `ShellResult` (`output` combinado + `returncode`) | 🔀 | Canónico: stdout/stderr **separados** + `interrupted` + `backgroundTaskId` (Bash background). El runtime combina stdout+stderr y sólo lleva returncode. Menos rico; el background de Bash (10) no tiene dónde colgar el task-id. |

---

## G · Confinamiento de filesystem (`fs_env.py::ConfinedFilesystem` + path guards vs `utils/permissions/filesystem.ts` + `utils/path.ts`)

| # | Feature | Estado | Nota |
|---|---|---|---|
| G1 | `contains_path_traversal` (regex `(?:^|[\\/])\.\.(?:[\\/]|$)`) | ✅ | **Byte-idéntico** a `containsPathTraversal` (path.ts:133). |
| G2 | `expand_path(path, base_dir)` (`~`, relativo→abs, colapsa `.`/`..`, null-byte guard) | 🟡 | Homólogo de `expandPath` (path.ts:32). Runtime: correcto en POSIX + null-byte guard. **Omite**: normalización Unicode NFC (`.normalize('NFC')`), conversión POSIX→Windows (`/c/…`→`C:\`). ⛔ Windows fuera de alcance, pero la NFC afecta también macOS. Menor. |
| G3 | `paths_for_permission_check` (original + realpath resuelto) | ✅ | Homólogo de `getPathsForPermissionCheck` (fsOperations.ts:288): devuelve `[expanded]` o `[expanded, resolved]` para no evadir por symlink. |
| G4 | `path_in_working_path` | 🟡 | Homólogo de `pathInWorkingPath` (filesystem.ts:709). **Omite dos normalizaciones de seguridad canónicas**: (a) macOS `/private/var`→`/var`, `/private/tmp`→`/tmp`; (b) **case-normalization** (`toLowerCase`) para FS case-insensitive (macOS/Windows) — sin ella, `.CLAUDE/…` evade checks case-sensitive. En Linux server-side (case-sensitive, sin /private) el impacto es bajo, pero es divergencia de seguridad. Ajuste: portar ambas normalizaciones si el runtime corre en macOS. |
| G5 | `path_in_allowed_working_path` (cada forma del path dentro de ALGÚN root, roots resueltos igual) | ✅ | Homólogo de `pathInAllowedWorkingPath` (filesystem.ts:683): simetría de resolución path↔working-dirs. |
| G6 | `ConfinedFilesystem.resolve(token, for_write)` — token→host vía `StorageContract.real_path` + confina | 🔀/✅ | Seam runtime (users/sessions/MinIO): la traducción token→path es política del consumidor (`StorageContract`), el confinamiento es mecanismo homologado. Homologación **de comportamiento**. Bien desacoplado. |
| G7 | Split **read-roots vs write-roots** (`roots`/`write_roots`) | 🔀 | El runtime separa allow-set de lectura vs escritura por **conjuntos de roots**. El canónico separa read/write por **reglas** (`checkReadPermissionForTool` vs `checkWritePermissionForTool`: read permite en working-dirs, write exige acceptEdits/rule). Misma intención (write más estrecho que read), distinta forma. 🔀 razonable. |
| G8 | **Capa de safety AUSENTE**: `DANGEROUS_FILES`/`DANGEROUS_DIRECTORIES` (.git/.bashrc/.claude/settings.json…), `hasSuspiciousWindowsPathPattern` (ADS/8.3/UNC/DOS-devices), `isClaudeConfigFilePath`, `checkPathSafetyForAutoEdit` | ❌ | `ConfinedFilesystem` es **confinamiento de workspace puro**: no protege archivos peligrosos. Un `FileEdit`/`Write` dentro del workspace puede editar `.bashrc`/`.git/config`/`.claude/settings.json` sin fricción. El canónico lo bloquea en acceptEdits (`checkPathSafetyForAutoEdit`). **Es política de permisos** (acceptEdits/GAP-02) más que confinamiento → delegable al integrador, pero el runtime hoy no expone el gancho. Liga FIND-CTX1 (read-before-edit) — misma familia "invariantes de fs-tool no impuestos". Ajuste: exponer un hook de safety en el gate de escritura (o dejar explícito que es responsabilidad del integrador server-side). |
| G9 | Internal editable/readable paths allow sin permiso | ❌/🔀 | **`filesystem.ts` leído íntegro (1510-1777).** El canónico auto-permite paths internos del harness. WRITE (`checkEditableInternalPath`): plan-file de sesión, scratchpad, job-dir (`CLAUDE_JOB_DIR`), agent-memory, memdir (auto-mem), `.claude/launch.json`. READ (`checkReadableInternalPath`): session-memory, project-dir (`~/.claude/projects/...`), plan-file, tool-results-dir, scratchpad, project-temp-dir, agent-memory, memdir, tasks-dir, teams-dir, bundled-skills-root (nonce). El runtime NO los modela aquí — plan-file (14), memoria (13) y storage (15) gestionan su acceso vía `StorageContract`. Confirmar cobertura en 13/14/15; NO re-abrir como gap de 09. |

---

## Hallazgos (IDs para retoma)

- **FIND-TOOL1** (❌ D6/A3): sin ejecución concurrente de tools concurrency-safe (el dispatcher es
  secuencial; `isConcurrencySafe` no existe en `ToolProtocol`). Prerequisito de la cascada sibling
  (08·SIG3b). Ajuste: modelar concurrencia + árbol de abort per-tool.
- **FIND-TOOL2** (❌ D3/A8/A10): el gate de permisos es deny-por-nombre y **ni ve el input**; falta
  `check_permissions(input,ctx)` por-tool + modos + PreToolUse. **Es el aterrizaje de GAP-02 en tools.**
- **FIND-TOOL3** (❌ A4): `interruptBehavior 'cancel'|'block'` ausente del protocolo = **FIND-SIG4 aterriza aquí**.
- **FIND-TOOL4** (❌ A23/A24/D7): `ToolResult` no transporta `new_messages` ni `context_modifier`; el
  dispatcher/loop no los aplica. Motor de "tool que inyecta mensajes / muta contexto" no portado.
- **FIND-TOOL5** (🟡 A26/D8): `aborted` genérico sin reason/tool_use_id (SIG10) + `except Exception`
  aplana AbortError (SIG12). Familia FIND-L1/08.
- **FIND-TOOL6** (❌ E6): `ToolSearch select:` no soporta multi-select coma-separado que el propio
  delta-announce del runtime promete al modelo → `select:A,B` falla.
- **FIND-TOOL7** (🔀 E4/E5): el delta de diferidas se reconstruye **parseando texto** de reminders
  (frágil) en vez de attachments tipados; el set descubierto se materializa en state en vez de
  derivarse de la historia (verificar clonado en fork/subagente, 05/11).
- **FIND-TOOL8** (❌ F2): `LocalExecEnvironment` sin shell persistente → `cd`/env no persisten entre
  llamadas Bash (diverge de `Shell.ts`). Aterriza en 10·bash.
- **FIND-TOOL9** (🟡 G4/G8): path-guards omiten normalización macOS `/private/*` + case-fold, y NO hay
  capa de safety (dangerous files/dirs). Bajo impacto en Linux server-side case-sensitive; divergencia
  de seguridad si corre en macOS. G8 liga FIND-CTX1 + GAP-02.
- **FIND-TOOL10** (🟡 B2): dos registries (`ToolRegistry` usado / `NativeToolRegistry` con hot-plug MCP
  sin usar por el factory) — solapamiento a unificar (hermano de 01/05).

### Gaps con ID
- **GAP-TOOL1** = GAP-02: gate de permisos por-tool con modos + input (D3/A8).
- **GAP-TOOL2** = GAP-MODE2: `worktree.safe_for_background=False` vs `ASYNC_AGENT_ALLOWED_TOOLS`
  canónico que lo permite → reconciliar en 10 (B3).
- **GAP-TOOL3**: `is_deferred_tool` sin precedencia canónica (`alwaysLoad`/`isMcp`-siempre/carve-outs);
  MCP debe setear `deferred` a mano — verificar en 11 (E1).

### Cabos que ENTRARON y su resolución
- **FIND-SIG4** (interruptBehavior en ToolProtocol) → confirmado ausente = **FIND-TOOL3**. ❌.
- **FIND-SIG3b** (dispatcher no cancela tools en vuelo/sibling) → confirmado: dispatcher secuencial,
  sin concurrencia ni sibling-abort = **FIND-TOOL1**. ❌.
- **SIG10** (ToolResult.aborted string plano) → confirmado = **FIND-TOOL5** / A26. 🟡.
- **GAP-MODE2** (worktree background) → confirmado = **GAP-TOOL2** / B3. 🔀.
- **ToolPool↔dispatcher mismo pool** → confirmado ✅ (C2/D1); es un invariante bien homologado.

## Recuento
✅ **9** (A1,C1,C2,C4,D1,D4,E10,G1,G3,G5 — nota: 10 celdas ✅, algunas comparten fila) ·
🟡 **~14** · 🔀 **~16** · ❌ **~18** · ⛔ **~6**. Cómputo aproximado (varias filas mezclan
sub-estados); lo vinculante son los IDs FIND-TOOL/GAP-TOOL y los cabos resueltos.

## Ledger de archivos (auditoría de cierre — protocolo obligatorio)

### Canónico (`/home/noheroes/python/claude-code/src`)
| Archivo | LOC | ¿Leído íntegro? |
|---|---|---|
| `Tool.ts` | 792 | sí |
| `tools.ts` | 389 | sí |
| `tools/utils.ts` | 40 | sí |
| `utils/toolSearch.ts` | 757 | sí |
| `tools/ToolSearchTool/ToolSearchTool.ts` | 471 | sí |
| `tools/ToolSearchTool/prompt.ts` | 122 | sí |
| `utils/path.ts` | 155 | sí |
| `utils/permissions/filesystem.ts` | 1777 | sí |
| `utils/sandbox/sandbox-adapter.ts` | 985 | sí |

**Fuera de alcance de 09 (declarado, NO en el ledger de "leídos íntegros")**: `tools/shared/spawnMultiAgent.ts`
(1093 → spawn multi-agente = **05·execution**), `tools/shared/gitOperationTracking.ts` (277 → tracking de
ops git de Bash/commit = **10·bash**). El motor de sandbox real está VENDORIZADO
(`@anthropic-ai/sandbox-runtime`, fuera del repo) — no auditable aquí por diseño (ver F3).

### Runtime (`/home/noheroes/python/agentic_runtime/src/agentic_runtime/tools`)
| Archivo | LOC | ¿Leído íntegro? |
|---|---|---|
| `protocol.py` | 61 | sí |
| `registry.py` | 37 | sí |
| `native_registry.py` | 41 | sí |
| `factory.py` | 75 | sí |
| `pool.py` | 78 | sí |
| `dispatcher.py` | 84 | sí |
| `deferred.py` | 44 | sí |
| `deferred_strategy.py` | 105 | sí |
| `deferred_delta.py` | 116 | sí |
| `exec_env.py` | 105 | sí |
| `fs_env.py` | 163 | sí |
| `__init__.py` | 28 | sí |
| `native/tool_search.py` | ~80 | sí (relevante a deferred; el resto de `native/` es **10**) |
| `loop/agent_loop.py` (cableado infra) | 85-234 | sí (tramo de ensamblado pool/strategy/dispatch) |

### Preguntas de cierre
- ¿Se revisó **todo** cada archivo canónico listado? **sí**
- ¿Se revisó **todo** cada archivo runtime listado? **sí**
- ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **sí** (los ❌ de comportamiento se
  separaron de los ⛔ de render enumerando los ~60 miembros de `Tool`; los archivos grandes
  —`filesystem.ts` 1777, `toolSearch.ts` 757, `sandbox-adapter.ts` 985— se leyeron íntegros).
- ¿Quedó **todo cubierto (nada pendiente)**? **sí** (cabos FIND-SIG4/SIG3b/SIG10/GAP-MODE2
  resueltos; lo delegado —13/14/15/GAP-02— queda anotado con su destino, no pendiente en 09).

**Cierre habilitado: las 4 respuestas = sí.**

## Nota metodológica
`Tool.ts` se releyó ÍNTEGRO por los campos de INFRA (no sólo `ToolUseContext` como en 03/08):
enumerar los ~60 miembros del tipo `Tool` fue lo que separó los ❌ de comportamiento (A3/A4/A8/A9/A23/A24)
de los ⛔ de render (A17/A18). `filesystem.ts` (1778) se leyó hasta la capa de safety (G8) — el resto
(reglas allow/deny/ask, suggestions) es política de permisos → 06/GAP-02, no infra de tools. La lectura
íntegra de `toolSearch.ts` (757) destapó E9 (umbral auto:N) y E5 (set derivado de historia) que un grep
por `isDeferredTool` habría escondido.

---

## Re-visita de COMPLETITUD (gate 11 / L09) — 2ª vuelta, 2026-07-19

**Estado**: ✅ VALIDADA sin cambio de estado. Modo validación (L11): el objeto es la homologación A↔B,
NO confirmar este documento. Para cada fila **✅/🔀** se abrió la implementación de B (el consumidor real)
y se siguió el dato de punta a punta; las ❌ convergen (no re-hechas). B leída ÍNTEGRA 1→EOF esta vuelta:
los 12 archivos infra (`fs_env.py` 163 el más grande L08, `deferred_delta.py` 116, `exec_env.py` 105,
`deferred_strategy.py` 105, `dispatcher.py` 84, `pool.py` 78, `factory.py` 75, `protocol.py` 61,
`deferred.py` 44, `native_registry.py` 41, `registry.py` 37, `__init__.py` 28) + el **ensamblador**
`loop/agent_loop.py` (352, 1→EOF, L09) + `tools/native/tool_search.py` (79) + `execution/fork/__init__.py`
(96) + `context/tool_use.py` (70) + grep de cableado prod-vs-test.

### ✅/🔀 sostenidos ABRIENDO B (mini-ledger de consumidores)
- **C1/C2/D1 — invariante del pool único** ✅: `loop:195` `ctx.tool_pool = _build_tool_pool(ctx)` → `:196`
  `ctx.tool_pool.assemble(permission_context)` produce los schemas a anunciar (vía `prepare_turn`); la
  **ejecución** resuelve del MISMO objeto: `dispatcher.py:57` `ctx.tool_pool.find(tool_name, permission_context)`
  → `pool.py:42` `self.assemble(...)` + match por nombre; `tool_search.py:51` `ctx.tool_pool.assemble(...)`.
  Deferred = **visibilidad** (la `SimulatedDeferredStrategy` filtra el schema de la diferida-no-descubierta,
  `deferred_strategy.py:67`) **no disponibilidad** (sigue en `ctx.tool_pool` → `find` la resuelve). Invariante
  CONFIRMADO por lectura directa del ensamblador, no por tabla.
- **C1 `assemble_tool_pool`** ✅: `pool.py:48-75` native-sorted-by-name + dedup native-precede (`uniqBy`) +
  deny por nombre exacto + capability-sorted+dedup. Cableado: es la única fuente (announce + find + tool_search).
- **C4 partición native/capability** ✅: `_build_tool_pool` (`loop:85-97`) → `capability_manager.build_tool_pool(native, ctx)`.
- **B3 filtro background** 🔀: `registry.list_available(mode)` (`registry.py:32-33`) filtra `safe_for_background`;
  consumidor `loop:91-92` (`mode="background" if ctx.is_subagent`). Cableado confirmado.
- **D4** validación schema `dispatcher.py:71`; **E10** `mark_tools_discovered` dentro de `execute`
  (`tool_search.py:67`); **D9** `sanitize_output` choke-point `dispatcher.py:42`; **E3** `NativeDeferredStrategy`
  seleccionada por `supports_native_tool_search` (`loop:143-148`). Todos cableados en la ruta real.
- **G1/G3/G5 path-guards** ✅: `fs_env.py:37/60/85` (traversal byte-idéntico, `paths_for_permission_check`,
  `path_in_allowed_working_path`). **G6/G7** `ConfinedFilesystem.resolve(for_write=)` (`fs_env.py:144-152`,
  `roots` vs `write_roots`). Consumidos por las fs-tools reales: `read_file.py:31`, `write_file.py:30`,
  `file_edit.py:49`, `glob_tool.py:34`, `grep_tool.py:52`, `clone_repository.py:109`.
- **F1/F2/F4 exec_env** — **seam VIVO** (a diferencia del huérfano de abajo): `factory.py:210`
  `exec_env = config.exec_env or LocalExecEnvironment()` → `:228` al runtime → `runtime.py:318`
  `ctx.exec_env = self._exec_env` → `bash.py:27-33` `exec_env.run_shell(...)` lee `.output`/`.returncode`.

### ❌ foci re-confirmados por CABLEADO (no por tabla)
- **FIND-TOOL1** (D6/A3): `loop:287` `for tc in tool_calls:` despacha **secuencial** (await por tool);
  `protocol.py:52-61` `ToolProtocol` sin `is_concurrency_safe`. Concurrencia ausente CONFIRMADA.
- **FIND-TOOL2** (D3): `dispatcher.py:62-65` `requires_permission` + `permission_context.allowed_names()`;
  el `tool_input` **nunca** llega al gate (sólo se valida schema después). Deny-por-nombre confirmado.
- **FIND-TOOL8** (F2): `exec_env.py:38-48` `create_subprocess_shell` **fresco por llamada** → sin shell
  persistente. Confirmado. Aterriza 10.

### Precisiones (NO voltean estado; el doc previo sobre-declaraba la justificación)
- **FIND-TOOL6 / E6 — justificación corregida**: el ❌ (canónico soporta `select:A,B,C` coma-separado;
  el runtime toma **un solo** nombre, `tool_search.py:53-55` `query[len("select:"):].strip()`) **SE SOSTIENE**.
  PERO la justificación del doc ("el propio delta-announce del runtime le dice al modelo `select:A,B` y falla")
  es **INEXACTA**: el announce (`deferred_delta.py:39` `'call ToolSearch with "select:<tool_name>"'`) y la
  `ToolSearchTool.description` (`tool_search.py:17`) prometen **`select:<tool_name>` SINGULAR** — el runtime es
  internamente consistente con single-select. El gap real vs A es de **paridad** (un modelo entrenado sobre CC
  puede emitir `select:A,B` por su prior y no matchearía), no una promesa auto-incumplida.
- **FIND-TOOL5 / D8 (SIG12) — precisión**: `dispatcher.py:83` `except Exception` **NO** captura
  `asyncio.CancelledError` (es `BaseException` desde 3.8) → un cancel EN VUELO **no se aplana** a error
  genérico: propaga a `_run_loop` (manejado en 08 vía kill/`_fire_stop`). Además el runtime **no tiene
  AbortError dentro de `execute`**: el abort se pre-chequea (`dispatcher.py:54` → `ToolResult.aborted`) o llega
  como CancelledError de task-kill. Por tanto "except Exception aplana AbortError" es impreciso; sólo el lado
  **A26** (aborted = str genérico `"aborted: <name>"` sin reason/tool_use_id, `protocol.py:47-48`) se sostiene 🟡.

### Refinamiento de clasificación (L10/L11 anti-padding)
- **FIND-TOOL10** — `NativeToolRegistry` (`native_registry.py`) tiene **CERO consumidores de producción**
  (grep: sólo `tools/__init__.py` export + `test_runtime_contracts.py`); el registry cableado es `ToolRegistry`
  (`factory.py:189` → `runtime._tool_registry` → `loop:92` `list_available` + `resolver.py:46`). Por L10/L11
  esto es **tech-debt B-interno / módulo huérfano** (el canónico NO tiene `NativeToolRegistry` — extensión sin
  contraparte), hermano de `modes/`·`observer/`·`SignalBus`·`LAT-EXEC1`, **NO** deuda A↔B "dos registries a
  unificar". El 🟡 se afina a huérfano-B-interno (destino: DEUDA-B §B-orphans, junto al resto).

### Costura latente NUEVA (tech-debt B-interno, NO deuda A↔B; anti-padding L10/L11)
- **LAT-TOOL1**: `ToolProtocol.category: ToolCategory` (`protocol.py:56`, enum
  `UTILITY/SYSTEM/FILE/NETWORK/BACKGROUND`) es campo **requerido** y lo **setean las 25 tools nativas**, pero
  **NINGÚN código de producción lee `.category`** (grep de lectura = 0; sólo definición + asignaciones +
  import). Slot de clasificación muerto — maquinaria a medio cablear, hermana de `to_llm`/`timeout_seconds`/
  `LAT-EXEC1`/`LAT-HOOK1`/`NativeToolRegistry`. El canónico no tiene este enum de 5 valores como driver de
  comportamiento ⇒ **no es deuda A↔B**, es tech-debt B-interno (extensión sin contraparte y sin consumidor).
  (`ToolResult.metadata`, `protocol.py:36`, también sin poblar en la ruta real, pero es bolsa opcional → menor,
  no se cuenta como costura.)

### FIND-TOOL7 (E4/E5) 🔀 sostenido + mecanismo verificado copy-safe
- Delta parseado de texto CONFIRMADO (`deferred_delta.py`: `_announced_deferred_names` escanea `msg["content"]`
  por frase-centinela `_ADDED_HEADER`). Discovered-set MATERIALIZADO CONFIRMADO (`deferred.py:31`
  `ctx.app_state.capabilities["discovered_tools"]`). **Sub-concern (b) del doc resuelto en mecanismo**: el
  `fork()` copia `capabilities = dict(snap.capabilities)` (shallow, `fork/__init__.py:78`) y
  `mark_tools_discovered` **REEMPLAZA** la clave (`deferred.py:37` `= sorted(current)`, no muta in-place) → **sin
  aliasing/drift** entre padre e hijos. Que el hijo *vea* el set del padre depende de cómo `runtime.py` (05)
  puebla `ForkSnapshot.capabilities` — cabo con **destino 05/11**, NO bug del seam de 09. El materializar-vs-
  derivar es la 🔀 de diseño (sobrevive a compactación sin carry en el boundary).

### Ledger de LECTURA de esta vuelta (B, columna Lectura)
| Archivo B | LOC | Lectura |
|---|---|---|
| `tools/fs_env.py` | 163 | íntegro 1→EOF |
| `tools/deferred_delta.py` | 116 | íntegro 1→EOF |
| `tools/exec_env.py` | 105 | íntegro 1→EOF |
| `tools/deferred_strategy.py` | 105 | íntegro 1→EOF |
| `tools/dispatcher.py` | 84 | íntegro 1→EOF |
| `tools/pool.py` | 78 | íntegro 1→EOF |
| `tools/factory.py` | 75 | íntegro 1→EOF |
| `tools/protocol.py` | 61 | íntegro 1→EOF |
| `tools/deferred.py` | 44 | íntegro 1→EOF |
| `tools/native_registry.py` | 41 | íntegro 1→EOF |
| `tools/registry.py` | 37 | íntegro 1→EOF |
| `tools/__init__.py` | 28 | íntegro 1→EOF |
| `loop/agent_loop.py` (ensamblador) | 352 | íntegro 1→EOF (L09) |
| `tools/native/tool_search.py` | 79 | íntegro 1→EOF |
| `execution/fork/__init__.py` | 96 | íntegro 1→EOF |
| `context/tool_use.py` | 70 | íntegro 1→EOF |
| `factory.py` (ensamblador runtime) | 267 | íntegro 1→EOF (cierre — L09) |
| `execution/local/runtime.py` (wiring ctx) | 435 | tramos 308-331 (asignación `ctx.exec_env`/`fs`/`presentation`); resto ya íntegro en 05-08 |
| `tools/native/bash.py` (consumidor exec_env) | 37 | íntegro 1→EOF |

### §Honestidad (2ª vuelta)
La 1ª pasada de 09 (2026-07-13) fue rigurosa en la LECTURA (los grandes canónicos íntegros) pero sus filas
✅/🔀 se sostenían sobre la descripción del seam, no sobre abrir el ensamblador `loop/agent_loop.py` 1→EOF.
Esta 2ª vuelta ABRIÓ el consumidor real de cada ✅/🔀 y siguió el dato: los ✅ se sostienen sobre la base
correcta (el pool único es literal en `loop:195-196`+`dispatcher:57`), pero al hacerlo aparecieron (i) dos
**imprecisiones de justificación** que el doc sobre-declaraba (FIND-TOOL6 promesa `select:A,B` inexistente;
FIND-TOOL5 "except Exception aplana AbortError" — no captura `CancelledError`), (ii) una **costura latente
nueva** invisible a la confirmación-de-doc (`.category` slot muerto = LAT-TOOL1), y (iii) el refinamiento de
`NativeToolRegistry` de "dos registries a unificar" a **huérfano B-interno** (0 consumidores prod). Ningún
cambio de estado en la tabla; código intacto; suite no re-ejecutada (modo validación).

**Auto-corrección de honestidad (gate auto-adversarial del usuario, mismo reproche que en 07)**: mi 1ª
redacción de esta vuelta concluyó "seam `exec_env` VIVO / `ToolRegistry` cableado vía `factory:189`" a partir de
**líneas de grep** de `factory.py`/`runtime.py` **sin abrir el ensamblador `factory.py` 1→EOF**. Corregido en el
cierre: `factory.py` (267) leído **1→EOF** — `_build_local:189` `create_tools()`→`:220` a `LocalAgentRuntime`
(y `NativeToolRegistry` NO aparece en el ensamblador → huérfano confirmado por lectura, no sólo grep); `:210`
`exec_env = config.exec_env or LocalExecEnvironment()`→`:228`; + `runtime.py:314-318` `ctx.exec_env = self._exec_env`
+ `bash.py:27-33` `exec_env.run_shell` leídos. La conclusión de cableado ahora se apoya en el ensamblador leído,
no en grep. L09/L00 re-aplicadas: conclusión de cableado exige leer el ensamblador; grep sólo orienta o prueba
ausencia (los 0-consumidores de `NativeToolRegistry`/`.category` sí son legítimos por grep, y además corroborados
por `factory.py` 1→EOF que no los cablea).

### 4 preguntas de cierre (2ª vuelta)
1. ¿Se revisó **todo** cada archivo de **A**? **sí** — en la 1ª pasada los canónicos se leyeron íntegros
   (`Tool.ts` 792, `filesystem.ts` 1778, `toolSearch.ts` 757, `ToolSearchTool.ts` 471, `sandbox-adapter.ts` 985,
   `tools.ts` 389, `path.ts` 155); esta vuelta re-ancló las referencias, no re-derivó A (el objeto de L11 es B).
2. ¿Se revisó **todo** cada archivo de **B**? **sí** — los 12 infra + ensamblador + `tool_search` + fork +
   `tool_use` leídos 1→EOF esta vuelta (ledger arriba); cableado prod-vs-test por grep del ensamblador, no
   sustituto de la lectura.
3. ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **sí** — se abrió el consumidor real de cada
   ✅/🔀 (no la tabla); destapó LAT-TOOL1 + 2 imprecisiones + el refinamiento del huérfano.
4. ¿Quedó **todo cubierto (nada pendiente)**? **sí** — los cabos que aterrizan fuera de 09 quedan con destino
   (FIND-TOOL7-snapshot → 05/11; NativeToolRegistry+LAT-TOOL1 → DEUDA-B §B-orphans; FIND-TOOL8 → 10;
   FIND-TOOL2 → B-02); NO hay pendiente de **verificación** de 09.

**VEREDICTO DE AVANCE: ✅ NADA PENDIENTE → avanzar a 10·tools-native con gate 11.**

---

## Plan de homologación / remediación desarrollada

Diseño por finding. Seams: `tools/protocol.py` (`ToolProtocol` 8 miembros, `ToolResult`, `ToolCategory`),
`tools/dispatcher.py` (`ToolDispatcher.dispatch` secuencial + gate deny-por-nombre `allowed_names()`),
`tools/pool.py` (`ToolPool`/`assemble`), `tools/deferred*.py` (`is_deferred_tool`,
`NativeDeferredStrategy`/`SimulatedDeferredStrategy`), `tools/exec_env.py`/`tools/fs_env.py`. **Muchos
findings de 09 son el aterrizaje de cabos transversales** → se referencian a Deuda B / 10 y NO se
re-desarrollan. Lo propio de 09 (deferral, dos registries, auto-mode) se desarrolla aquí.

### TiR1 · Cabos que se desarrollan en Deuda B / 10 (referencia, no re-desarrollo)
- **FIND-TOOL1 concurrencia** (dispatcher secuencial, sin `is_concurrency_safe`) → **Deuda B `B-concurrency`**.
- **FIND-TOOL2 = GAP-02** (gate deny-por-nombre sin ver input + modos + PreToolUse) → **Deuda B `B-02`**;
  a nivel `ToolProtocol` = añadir `check_permissions(input, ctx)` opcional (A8) e `is_read_only(input)` (A6).
- **FIND-TOOL3 = SIG4** `interrupt_behavior` per-tool → **Deuda B `B-signals`** (miembro del `ToolProtocol`).
- **FIND-TOOL4** `ToolResult.new_messages` + `context_modifier` tipado → **Deuda B `B-new_messages`**
  (context_modifier YA se aplica, corregido en 10·J; falta declararlo + `new_messages`).
- **FIND-TOOL5 = SIG10** aborted con reason/tool_use_id → **Deuda B `B-signals`**.
- **FIND-TOOL8** shell persistente → **YA en 10·R8**. **FIND-TOOL9/G8** safety-fs → **YA en 10·R3**.
- **A15 `outputSchema`** → **Deuda B `B-structured-output`** (`ToolProtocol.output_schema` +
  `ToolResult.structured`).

### TiR2 · FIND-TOOL6 — `ToolSearch select:` sin multi-select
- **Comportamiento**: el propio delta-announce promete al modelo `select:A,B` (coma-separado), pero el
  runtime sólo procesa un nombre → `select:A,B` falla silenciosamente.
- **Seam/firma**: en `tools/deferred*.py` (la ruta que parsea `select:`), dividir por coma y resolver cada
  nombre: `names = [n.strip() for n in arg.split(",") if n.strip()]`; descubrir todos.
- **Cableado**: la estrategia deferred (`SimulatedDeferredStrategy`/`NativeDeferredStrategy`) que maneja el
  select. **Orden**: independiente, barato. **Test**: `test_tool_search_select_multi` (xfail existente).

### TiR3 · FIND-TOOL7 — delta de diferidas reconstruido parseando texto
- **Comportamiento**: el delta de tools descubiertas se reconstruye **parseando el texto** de los reminders
  (frágil) y el discovered-set se **materializa** en `app_state.capabilities` en vez de derivarse de la
  historia → riesgo de drift en fork/subagente (05/11).
- **Seam/firma**: reemplazar el parseo de texto por un canal tipado — el announcement lleva los nombres en
  un attachment/estructura (no en prose); `getDeferredToolsDelta` deriva el discovered-set de los
  announcements tipados en `ctx.messages`, no de un slot mutable. Verificar que el `ForkSnapshot` NO clona un
  discovered-set materializado (que se re-derive en el hijo).
- **Cableado**: deferred strategy + fork (05). **Orden**: tras `B-new_messages` (attachments tipados).
  **Test**: `test_deferred_delta_derived_not_parsed`, `test_fork_rederives_discovered_set`.

### TiR4 · FIND-TOOL10 — dos registries (`ToolRegistry` vs `NativeToolRegistry` hot-plug MCP)
- **Comportamiento**: `ToolRegistry` se usa; `NativeToolRegistry` (hot-plug de MCP) no lo usa la factory →
  hermano de los duplicados de 01/05.
- **Seam/firma**: decidir uno — si el hot-plug MCP es necesario (11), la factory debe usar
  `NativeToolRegistry` y `ToolRegistry` se retira; si no, borrar `NativeToolRegistry`. Verificar en **11**
  (el adaptador MCP setea `deferred=True` a mano → necesita el registro dinámico).
- **Orden**: junto a 11. **Test**: `test_single_tool_registry_wired`.

### TiR5 · GAP-TOOL3 — precedencia de `is_deferred_tool` (alwaysLoad/isMcp/carve-outs)
- **Comportamiento**: `is_deferred_tool` = `getattr(tool,'deferred',False)` plano; falta la precedencia
  canónica (`isDeferredTool`, prompt.ts:62): **`alwaysLoad`→false primero**, `isMcp`→true (MCP siempre
  diferida), ToolSearch→false, carve-outs `FORK_SUBAGENT`(Agent)/`Brief`→false, luego `shouldDefer`.
- **Seam/firma**: `is_deferred_tool(tool)` lee `getattr(tool,'always_load',False)` (opt-out primero),
  `getattr(tool,'is_mcp',False)` (siempre diferida), carve-outs por nombre, luego `deferred`.
- **Cableado**: verificar en **11** que el adaptador MCP setee `is_mcp=True` en vez de `deferred=True` a
  mano. **Orden**: junto a 11. **Test**: `test_is_deferred_precedence`.

### TiR6 · E9 / A2 — auto-mode (umbral) y `description(input)` → 16 (referencia)
- **E9 umbral de deferral** (diferir sólo cuando las tool-defs pesan vs % de la ventana; `tst`/`tst-auto`/
  `standard`) → depende del **conteo de tokens (16)**; el runtime hoy difiere incondicionalmente. Diseño en
  16 + un `should_defer_turn(pool, model_id)` en la estrategia. **Test**: `test_deferral_threshold`.
- **A2 `description(input)` async** (Bash renderiza el comando) → menor; el runtime colapsa a str fijo.
  Diferido, sin xfail.
