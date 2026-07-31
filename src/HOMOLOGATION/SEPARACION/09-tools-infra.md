# 09 · tools-infra — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/09-tools-infra.md`.
> **Ciclo A1.6** del PLAN §4. Fuente: tracker `../09-tools-infra.md` (grid A1…G9, leído íntegro 1→492).
> Esquema: `00-LEGEND.md` (1→159). Re-clasifica cada celda de fidelidad-de-capacidades bajo B
> (base↔costuras↔batteries↔integrador). **No es otra tabla de deuda:** es el reparto de la **infraestructura de
> tools** (contrato de tool · registro · ensamblado del pool · dispatch · carga diferida/tool-search · backend de
> shell · confinamiento de fs) entre el mecanismo del base, las costuras que el integrador/battery rellena, y las
> batteries que la infra compone.

## Naturaleza de la categoría
El canónico **no reifica** una capa `tools/`: el "protocolo" es el tipo estructural `Tool` (~60 miembros, la mayoría
render React) construido por `buildTool`+`TOOL_DEFAULTS`; el registry es `getAllBaseTools()`; el pool es
`assembleToolPool()`; la ejecución vive dispersa (`StreamingToolExecutor`/`toolExecution`). El runtime **des-fusiona
cada rol** en clase/módulo (`ToolProtocol`, `ToolRegistry`, `ToolPool`, `ToolDispatcher`, `DeferredToolStrategy`) +
**AÑADE** dos costuras propias sin contraparte canónica: `ToolExecEnvironment` (backend de shell inyectable) y
`NativeDeferredStrategy` (defer_loading server-side gpt-5/Responses). Bajo B el des-fusionado es correcto de forma;
lo que aquí se destila es **qué del comportamiento canónico** (no del render) captura cada seam reificado.

El corte B de esta categoría (verificado abriendo B 1→EOF este ciclo):
- **El contrato mínimo de tool** (`ToolProtocol` 8 miembros + `ToolResult` + `ToolCategory`, `protocol.py`) es
  **T1-CONTRATO** (el shape de tool-schema/result que el modelo consume y donde enchufan AMBOS integradores). Sus
  omisiones de **comportamiento** (no de render) son los CORE-GAP: `is_concurrency_safe`, `interrupt_behavior`,
  `check_permissions`/`validate_input`/`is_read_only`/`is_destructive` (por-tool), `new_messages`, `output_schema`,
  `searchHint`, aliases, precedencia de deferral.
- **El ensamblado y el dispatch** (`assemble_tool_pool`, `ToolPool.find`, `ToolDispatcher`, `AgentLoop._build_tool_pool`)
  son **T2-BASE-MECANISMO**: el invariante del **pool único** (anuncio y ejecución resuelven del MISMO objeto ⇒
  deferred = visibilidad, no disponibilidad) es el corazón mecánico de la categoría, confirmado por lectura literal
  del ensamblador (`agent_loop.py:194-196` + `dispatcher.py:57`).
- **La carga diferida** (`DeferredToolStrategy` + Simulada/Nativa + delta + `ToolSearch`) es **T2-BASE-MECANISMO** con
  una rama **T1-MOTOR** (el flag `defer_loading` que `agentic_models` emite server-side). Es lo **propio de 09** que se
  desarrolla aquí (no se referencia fuera).
- **La política se saca del tool y se pone en costuras inyectables**: `ToolExecEnvironment` (backend shell),
  `ConfinedFilesystem`+`StorageContract` (token→path + roots), y el **PreToolUse hook del loop** (`agent_loop.py:300-313`,
  seam VIVO donde el integrador provee la política de permisos por-input). El gate propio del dispatcher es deny-por-nombre
  (mecanismo delgado); la política real es del integrador.

Frontera heredada (respetada, L07): muchos findings de 09 son el **aterrizaje de cabos transversales** de otras
categorías (SIG4/SIG10/SIG12→08, GAP-02→06, shell persistente/safety-fs→10, structured-output→16). Se clasifican
**aquí** por TIER+destino pero su remediación de campo se ancla en su home (referencia, no re-desarrollo — TiR1 del
tracker). Lo **propio de 09** (deferral, dos registries, auto-mode, exec/fs seams) se desarrolla aquí.

---

## 1. Tabla por finding

Leyenda tracker: ✅ homologado · 🟡 parcial · 🔀 diferente (deliberado) · ❌ no portado · ⛔ N/A core (render/UI).

### A · Contrato de tool — `ToolProtocol` (`protocol.py`, 8 miembros)
| ID | resumen (comportamiento) | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **A1** ✅ | `name`/`description`/`input_schema` (JSON-Schema, validado por `agentic_models`) | núcleo | **T1-CONTRATO** | paquete contratos (`tool-schema`) | — | Se queda. `protocol.py:53-55` + `dispatcher.py:71` |
| **A2** 🔀 | `description(input)` async + `prompt()` separado | núcleo | **T1-CONTRATO** | contratos + **→16** | — | Runtime colapsa a str fijo (`protocol.py:54`). `description(input)` (Bash renderiza cmd) diferido a 16 (TiR6-A2). Menor |
| **A3** ❌ | `isConcurrencySafe(input)` | núcleo | **T1-CONTRATO** (campo) | contratos + **Deuda B `B-concurrency`** | — | **FIND-TOOL1**. Ausente (`protocol.py:52-61`); prerequisito de dispatch paralelo (D6). Home concurrencia = Deuda B |
| **A4** ❌ | `interruptBehavior 'cancel'\|'block'` | núcleo | **T1-CONTRATO** (campo) | contratos + **Deuda B `B-signals`** | — | **FIND-TOOL3 = SIG4**. Ausente. Consumidor cuando crezca `ctx.stop` (08). Home 08 |
| **A5** 🟡 | `isEnabled()` (auto-gating por flag/env) | núcleo | **T2-COSTURA** (composición) | costura + **integrador** (OI-18) | — | Hoy el gating lo hace el integrador al elegir qué registrar (`create_tools(extras)`). `isEnabled()` opcional |
| **A6** ❌ | `isReadOnly(input)` | núcleo | **T2-COSTURA** (permisos) | **Deuda B `B-02`** (=GAP-02) | — | Parte del gate de permisos por-input. Liga A8/D3 |
| **A7** ❌ | `isDestructive(input)` (ops irreversibles) | núcleo | **T2-COSTURA** (permisos) | **Deuda B `B-02`** | — | Gate de confirmación (política "hard to reverse"). Liga A8 |
| **A8** ❌ | `checkPermissions(input,ctx)` **por-tool** (allow/ask/deny + updatedInput + suggestions) | núcleo | **T2-COSTURA** (permisos) + campo opcional en contrato | **Deuda B `B-02`** (=GAP-02) + **06** | — | **FIND-TOOL2**. El gate del dispatcher es deny-por-nombre (`dispatcher.py:62-65`, el input **no** llega). **Nuance B:** el loop SÍ dispara `PRE_TOOL_USE` con `tool_input` (`agent_loop.py:300-313`, honra `block`/`modified_input`) ⇒ el seam input-aware está **VIVO** (política del integrador vía 06); falta el `check_permissions` per-tool + modos |
| **A9** 🟡 | `validateInput(input,ctx)` (reglas semánticas + errorCode) | núcleo | **T1-CONTRATO** (método opcional) | contratos + base | — | Runtime sólo valida **schema** (`dispatcher.py:71`). CORE-GAP menor: input schema-válido pero semánticamente inválido llega a `execute()` |
| **A10** 🔀 | `getPath(input)` (path al gate central de permisos) | núcleo | **T2-BASE** (divergencia) | base (confinamiento en fs-tool) | — | Deliberado: el confinamiento se empuja a `ctx.fs.resolve(for_write=)` **dentro** de cada fs-tool (`fs_env.py:144`), no al gate central. Consecuencia: el gate central no ve el path (liga A8/G8) |
| **A11** ❌ | `aliases` + `toolMatchesName` | núcleo | **T1-CONTRATO** (campo) | contratos + base | — | `pool.find` compara `t.name==name` exacto (`pool.py:43`); sin aliases. Rompe compat al renombrar nativa. Menor |
| **A12** 🟡 | `searchHint` (frase 3-10 palabras, peso 4 en ToolSearch) | núcleo | **T1-CONTRATO** (campo) | contratos + base (liga E7) | — | Ausente; el keyword-search del runtime sólo matchea name+description (`tool_search.py:59`). Calidad de descubrimiento inferior |
| **A13** 🟡 | `shouldDefer`/`alwaysLoad`/`isMcp` (precedencia de deferral) | núcleo | **T2-BASE** (deferral) | base + **verificar 11** | — | **GAP-TOOL3**. `is_deferred_tool`=`getattr(deferred,False)` plano (`deferred.py:27`); falta precedencia. Ver E1/TiR5 |
| **A14** ❌ | `maxResultSizeChars` (persistir a disco si excede, preview+path) | núcleo | **T2-BASE** (budget) | **→02** (budget/`contentReplacementState`) | — | `ToolResult.output` es str sin cota (`protocol.py:32`). Evita reventar contexto. Cabo →02 |
| **A15** ❌ | `outputSchema` (structured output tipado) | núcleo | **T1-CONTRATO** (campo) | **Deuda B `B-structured-output`** (→05/16) | — | Liga A22 (result plano) + `SyntheticOutputTool`. Diferido |
| **A16** ❌/⛔ | `backfillObservableInput`/`toAutoClassifierInput` (❌ auto-mode) · `inputsEquivalent` (⛔ dedup UI) | mixto | **T3-INTEGRADOR** (auto-mode) / ⛔ | integrador (OI-23) / — | — | Observabilidad/clasificador de auto-mode = política del integrador; dedup UI ⛔ |
| **A17** ⛔ | `isSearchOrReadCommand`/`isOpenWorld`/`requiresUserInteraction`/`isLsp`/`isTransparentWrapper` | cáscara | **CLI-ONLY/INTERFAZ** | integrador (OI-22) | — | Clasificación para colapso de render. No al runtime headless |
| **A18** ⛔ | `render*` (~15 métodos: renderToolUse/Result/Grouped/Progress/Rejected/Error, getActivityDescription, getToolUseSummary…) | cáscara | **CLI-ONLY/INTERFAZ** | integrador (OI-22) | — | Todo React/ink/terminal. Runtime delega a `ctx.presentation` (D9) + integrador |
| **A19** 🔀 | `userFacingName(input)` (nombre para UI) | cáscara | **CLI-ONLY/INTERFAZ** | integrador (OI-22) | — | Runtime no lo modela; `ToolResult.tool_name` lleva el nombre. Menor |
| **A20** 🔀 | `preparePermissionMatcher(input)` (hook `if` de permission-rule) | núcleo | **T2-COSTURA** (permisos) | **→06** (matcher de condiciones) | — | Delegado a 06·hooks. No es del protocolo mínimo |
| **A21** 🔀 | `buildTool` + `TOOL_DEFAULTS` (fail-closed: concurrencySafe→false, readOnly→false, checkPermissions→**allow**, isEnabled→true) | núcleo | **T2-BASE** (builder) / BATTERY opcional | base (helper opcional) | — | Runtime sin builder; cada nativa implementa a mano (atributos de clase). Protocolo mínimo ⇒ bajo riesgo de drift. Nota: default canónico `checkPermissions→allow` explica por qué el gate del runtime (deny-por-nombre) es más restrictivo |

### A · `ToolResult` (`protocol.py:18-48`) vs `ToolResult<T>` canónico
| ID | resumen | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **A22** 🔀 | `output:str` + `is_error/is_timeout/is_aborted` + `metadata` vs `data:T` tipado + `mapToolResultToToolResultBlockParam` | núcleo | **T1-CONTRATO** (result shape) | contratos + liga A15 | — | Runtime aplana a str en la tool (`protocol.py:18-36`). Equivalente para el modelo; pierde dato tipado |
| **A23** ❌ | `newMessages?: Message[]` (la tool inyecta mensajes a la conversación) | núcleo | **T1-CONTRATO** (campo) + **T2-BASE** (aplicar) | **Deuda B `B-new_messages`** | — | **FIND-TOOL4**. Sin canal: `execute()` sólo devuelve `output`; el loop sólo appendea `result.output` (`agent_loop.py:319-323`). Motor "tool inyecta mensajes" no portado |
| **A24** 🟡 | `contextModifier?: (ctx)=>ctx` (sólo tools NO concurrency-safe) | núcleo | **T2-BASE** (aplicado) + declarar campo | **Deuda B `B-new_messages`** (declarar) | — | **CORR 10·J**: el loop SÍ lo aplica vía `getattr` (`agent_loop.py:332-337`), consumido por plan_mode/worktree/config/todo_write. **Confirmado por lectura propia.** Falta declararlo en `ToolResult` + gating por `is_concurrency_safe==False`. **+ `ends_turn` (`agent_loop.py:338-339`, consumido por ask_user/exit_plan) — mismo canal resultado→control-del-loop, también sin declarar; restituido del tracker `:82` por `A-CIERRE-P4 §2.2·P4-09-4`, de modo que `B-new_messages` se diseñe para los TRES portadores, no dos** |
| **A25** ❌ | `mcpMeta` (`_meta`/`structuredContent` passthrough) | núcleo | **T1-CONTRATO** (MCP) | **→11** | — | Metadatos MCP para consumidores SDK |
| **A26** 🟡 | `ToolResult.aborted(name)` sintético | núcleo | **T1-CONTRATO** (reason) | **Deuda B `B-signals`** (=SIG10) | — | **FIND-TOOL5**. `aborted()`=`"aborted: <name>"` sin reason/tool_use_id/withMemoryCorrectionHint (`protocol.py:47-48`). Canónico: 3 sintéticos distintos. Home 08 |

### B · Registry + factory (`registry.py`/`native_registry.py`/`factory.py`)
| ID | resumen | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **B1** 🔀 | `create_tools(extras)` → 25 nativas incondicional vs `getAllBaseTools()` con gating masivo | núcleo | **composición** (BATTERY/integrador) | integrador (OI-18) + batteries (→10) | — | Runtime registra TODO (`factory.py:41-67`); el gating lo hace el integrador vía `extras`/no-registrar. Deliberado (provider-agnostic). Las 25 nativas = batteries, detalle en **10** |
| **B2** 🟡 | **Dos registries**: `ToolRegistry` (usado) vs `NativeToolRegistry` (hot-plug MCP, sin usar) | núcleo | **DEUDA-B** (huérfano) | **borrar** `native_registry.py` \| decidir en 11 | — | **FIND-TOOL10**. `factory.py:69` devuelve `ToolRegistry`; `NativeToolRegistry` NO lo cablea la factory (confirmado leyendo `factory.py` 1→EOF). Tech-debt B-interno (extensión sin contraparte), NO deuda A↔B. Decisión ligada a 11 (MCP hot-plug) |
| **B3** 🔀 | `list_available(mode)` filtra `safe_for_background` en background | núcleo | **T2-BASE-MECANISMO** (registry) | base + **reconciliar 10** | — | **GAP-TOOL2 = GAP-MODE2**. `registry.py:32-33`, cableado `agent_loop.py:91-92`. `worktree.safe_for_background=False` vs `ASYNC_AGENT_ALLOWED_TOOLS` canónico que lo incluye → reconciliar tool-por-tool en 10 |
| **B4** 🟡 | `filterToolsByDenyRules` (MCP server-prefix strip pre-anuncio) | núcleo | **T2-BASE** (deny) | base + **→11** | — | `assemble_tool_pool` deny por nombre **EXACTO** (`pool.py:64/70`); canónico matchea `mcp__server` prefix (deniega server entero). CORE-GAP. Liga 06/11 |
| **B5** ❌/⛔ | modo `CLAUDE_CODE_SIMPLE` (solo Bash/Read/Edit) | cáscara | **T3-INTEGRADOR** | integrador (OI-18) | — | Env-gated; el integrador lo replica filtrando `extras`. Bajo impacto core |
| **B6** ⛔/❌ | `REPL_ONLY_TOOLS` / `parseToolPreset`/`TOOL_PRESETS` | cáscara | **CLI-ONLY/INTERFAZ** | integrador (OI-18/OI-22) | — | REPL ⛔ (terminal); presets `--tools` = entrypoint del integrador. Menor |
| **B7** 🔀 | `getMergedTools` (builtins+mcp SIN dedup, para conteo de tokens) | núcleo | **T1-MOTOR** (token count) | **→16** | — | Runtime no cuenta tokens de tool-defs (delega en capability del provider). Liga E9/16 |

### C · Pool assembly (`pool.py::ToolPool`/`assemble_tool_pool`)
| ID | resumen | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **C1** ✅ | `assemble_tool_pool`: native-precede, sort-by-name per-partición, dedup (`uniqBy`) | núcleo | **T2-BASE-MECANISMO** | base (`pool`) | — | `pool.py:48-75` homólogo fiel; sort per-partición = estabilidad de prompt-cache. **Confirmado por lectura propia** |
| **C2** ✅ | `ToolPool.find(name)` resuelve del MISMO pool ensamblado | núcleo | **T2-BASE-MECANISMO** (invariante) | base (`pool`) | — | `pool.py:42-45`; anuncio (`agent_loop.py:196`) y ejecución (`dispatcher.py:57`) del mismo objeto ⇒ **deferred=visibilidad, no disponibilidad**. Invariante clave CONFIRMADO leyendo el ensamblador |
| **C3** 🟡 | `find` sin alias-matching | núcleo | **T1-CONTRATO** (=A11) | contratos + base | — | `pool.py:43` exacto. = A11 |
| **C4** ✅ | partición `native_tools`/`capability_tools` | núcleo | **T2-BASE-MECANISMO** | base (`pool`) | — | `pool.py:19-20`, cableado `agent_loop.py:93-94` (`capability_manager.build_tool_pool`). Espejo builtin+MCP provider-agnostic |

### D · Dispatcher (`dispatcher.py::ToolDispatcher`)
| ID | resumen | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **D1** ✅ | resolución por nombre desde `ctx.tool_pool` (no registry aparte) | núcleo | **T2-BASE-MECANISMO** | base (`dispatcher`) | — | `dispatcher.py:57`. Punto de integración único loop↔tool. **Confirmado** |
| **D2** 🟡 | abort check antes de trabajo (`ctx.stop.is_set()`→`aborted`) | núcleo | **T2-BASE** (abort) | base + **→08** (`B-signals`) | — | `dispatcher.py:54`; binario, sin reason ni árbol (SIG2/3). Sin cancelación EN VUELO (sólo pre-ejecución + timeout) |
| **D3** ❌ | chequeo de permiso: `requires_permission` + `allowed_names()` | núcleo | **T2-COSTURA** (permisos) | **Deuda B `B-02`** + **06** | — | **FIND-TOOL2 = GAP-02**. `dispatcher.py:62-65` deny-por-nombre; el `tool_input` **nunca** llega al gate del dispatcher. Seam input-aware VIVO en `agent_loop.py:300` (PRE_TOOL_USE, política del integrador). Falta modos + `check_permissions` per-tool (A8) |
| **D4** ✅ | validación de schema (`agentic_models.validate_tool_arguments`) | núcleo | **T2-BASE** + **T1-MOTOR** | base + costura motor | — | `dispatcher.py:71` ≈ zod parse. Devuelve `ToolResult.error` con el mensaje |
| **D5** 🔀 | timeout **global** (`asyncio.wait_for(effective_timeout)`) | núcleo | **T2-BASE-MECANISMO** | base (`dispatcher`) | — | `dispatcher.py:68/76` envuelve TODA tool (override-call > override-dispatcher > `tool.timeout_seconds`). Canónico sin timeout global. Divergencia deliberada server-side; puede matar tools legítimamente lentas |
| **D6** ❌ | ejecución **concurrente** de tools concurrency-safe (siblingAbortController) | núcleo | **T2-BASE-MECANISMO** | **Deuda B `B-concurrency`** | — | **FIND-TOOL1**. `agent_loop.py:287` `for tc in tool_calls:` despacha **secuencial** (confirmado). Sin A3 (flag) ni cascada sibling (08·SIG3b) |
| **D7** ❌ | aplicar `newMessages`/`contextModifier` del resultado | núcleo | **T2-BASE** | **Deuda B `B-new_messages`** | — | = A23(❌)/A24(🟡). El loop aplica `context_modifier` (`agent_loop.py:332-337`) **y `ends_turn` (`:338-339`)** pero **NO** `new_messages`. Los tres son el mismo canal resultado→control-del-loop; sólo `new_messages` falta, los otros dos faltan **declarados** (P4-09-4) |
| **D8** 🟡 | `except Exception → error` (aplana AbortError) | núcleo | **T2-BASE** | **Deuda B `B-signals`** | — | **Precisión (L11):** `dispatcher.py:83` `except Exception` **NO** captura `asyncio.CancelledError` (es `BaseException`). "aplana AbortError" es **impreciso**; sólo A26 (aborted genérico) se sostiene 🟡. Cancel EN VUELO propaga a `_run_loop` (08) |
| **D9** 🔀/✅ | choke point de presentación (`ctx.presentation.sanitize_output`) | núcleo | **T2-COSTURA** (presentación) | base (choke) + costura `presentation` | eje persist. (scope por identidad) | `dispatcher.py:42` todo `output` pasa por `sanitize_output` antes de `ctx.messages` Y EventBus. Bajo identidad = no-op. Correcto server-side |
| **D10** ❌ | `onProgress`/`tool_progress` heartbeat intra-tool | núcleo | **T1-CONTRATO** (evento) | **→07** (EVT6) | — | El dispatcher no emite progreso intra-tool. Shape → 07 |

### E · Deferred loading / tool-search (`deferred*.py`/`native/tool_search.py`)
| ID | resumen | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **E1** 🟡 | `is_deferred_tool` (getattr `deferred`) sin precedencia canónica | núcleo | **T2-BASE** (deferral) | base + **verificar 11** | — | **GAP-TOOL3**. `deferred.py:17-27`: falta `alwaysLoad`→false primero, `isMcp`→true, carve-outs **`FORK_SUBAGENT`(Agent) / `Brief` / `SendUserFile`** (los **tres**; `SendUserFile` restituido del tracker `:134` por `A-CIERRE-P4 §2.2·P4-09-3` — el `TiR5` del propio tracker ya lo había perdido, y con 2 de 3 la tool quedaría diferida donde el canónico la carga siempre). El adaptador MCP debe setear `deferred=True` a mano. Ver TiR5 |
| **E2** ✅/🟡 | `SimulatedDeferredStrategy` (fallback client-side): oculta diferidas no descubiertas, anuncia NOMBRES, `owns_search_dispatch=True` | núcleo | **T2-BASE-MECANISMO** | base (`deferred_strategy`) | — | `deferred_strategy.py:54-79`. Comportamiento vigente encapsulado. **Confirmado** (filtra schema `:67`). 🟡 por E4/E5 |
| **E3** 🔀 (AÑADIDO) | `NativeDeferredStrategy` (defer_loading server-side gpt-5/Responses) | núcleo | **T2-BASE-MECANISMO** + **T1-MOTOR** | base + costura motor (`agentic_models`) | — | **Sin contraparte canónica** (valor propio multi-provider). `deferred_strategy.py:82-97` marca `defer_loading=True`; seleccionada por `supports_native_tool_search` (`agent_loop.py:143-148`, **confirmado leyendo el ensamblador**) |
| **E4** 🔀 | `deferred_delta` compute/render/scan de altas-bajas | núcleo | **T2-BASE-MECANISMO** | base (mejorar a canal tipado) | — | **FIND-TOOL7**. Homólogo de `getDeferredToolsDelta` PERO escanea **texto rendido** de `<system-reminder>` por frase-centinela (`deferred_delta.py:26/52-88`, confirmado) vs attachments tipados del canónico. Parseo string-frágil. Ver TiR3 |
| **E5** 🔀 | `extractDiscoveredToolNames` (set descubierto) | núcleo | **T2-BASE-MECANISMO** | base | ~~eje ejecución (set por `agent_id`, opaco)~~ → **NO toca el eje de identidad** (ver ⚠ abajo) | **FIND-TOOL7**. Canónico DERIVA de la historia; runtime MATERIALIZA en `ctx.app_state.capabilities["discovered_tools"]` (`deferred.py:31`). (a) sobrevive a compactación sin carry (bien); (b) `fork` copia shallow + `mark` REEMPLAZA la clave (`deferred.py:37`) ⇒ **copy-safe, sin aliasing** (confirmado). Verificar poblado de `ForkSnapshot` en 05/11 |
| **E6** ❌ | `ToolSearchTool.call` `select:` **multi** (coma-separado) | núcleo | **T2-BASE** (deferral) | base (TiR2, xfail) | — | **FIND-TOOL6**. `tool_search.py:53-55` toma **un solo** nombre (`query[len("select:"):].strip()`, sin split coma). El announce del runtime promete `select:<tool_name>` **singular** (`deferred_delta.py:39`) ⇒ internamente consistente; el gap es de **paridad** vs A (un modelo entrenado sobre CC puede emitir `select:A,B`), no una promesa auto-incumplida |
| **E7** 🟡 | `searchToolsWithKeywords` (word-boundary, searchHint peso 4, MCP-prefix, `+required`, fast-path) | núcleo | **T2-BASE** (deferral) | base (liga A12) | — | `tool_search.py:57-63` scoring por **substring count** simple, sin word-boundary/searchHint/`+required`/fast-path. Descubrimiento funcional de menor calidad |
| **E8** 🔀 | resultado = `tool_reference` blocks + `pending_mcp_servers` | núcleo | **T2-BASE** (deferral) | base + **→11** (pending mcp) | — | `tool_search.py:69-78` devuelve JSON con schemas inline (coherente con "simulada": el modelo lee el schema del output). No `tool_reference` (eso es la ruta nativa E3). `pending_mcp_servers` → 11 |
| **E9** 🔀 | `isToolSearchEnabled` (umbral auto:N, token/char threshold, model support) | núcleo | **T2-BASE** (deferral) | base + **→16** (conteo tokens) | — | **No portado como umbral.** Runtime difiere **incondicionalmente** si hay diferidas; no calcula peso. Simplificación deliberada (pierde auto-mode). `should_defer_turn(pool, model_id)` en la estrategia depende de 16. Ver TiR6 |
| **E10** ✅ | `mark_tools_discovered` cableado en `ToolSearchTool.execute` (no en dispatcher) | núcleo | **T2-BASE-MECANISMO** | base | — | `tool_search.py:67` dentro del `execute` de la propia tool (confirmado); `owns_search_dispatch()` sólo decide si el runtime ejecuta client-side |

> ⚠ **CORRECCIÓN EN SITU (A-CIERRE·P4″, 2026-07-27) — `E5` no está keyado por `agent_id`.** La columna de
> identidad de `E5` decía *«set por `agent_id`, opaco»* y la §3.3 lo repetía. **Es una invención de este
> documento:** el tracker `../09-tools-infra.md:138` dice *«estado de capability scopeado por agente»* —frase
> tomada a su vez del docstring `tools/deferred.py:11-13`— y **nunca nombra `agent_id`** (0 ocurrencias en sus
> 492 líneas). El código: `deferred.py` (44 L, 1→EOF) **no lee `agent_id` en ninguna línea**; la clave es
> `_DISCOVERED_KEY = "discovered_tools"`, literal y única, sin componente de identidad.
> **Consecuencia de la invención:** `DEUDA-A §2.8·H-4` la tomó por mecanismo y emitió un gap de cableado
> («son dos consumidores del mismo `agent_id` inestable», touchpoint 8 de `00-BLUEPRINT §2.1`), refutado en
> `A-CIERRE-P1 §AC-h6` abriendo el código. **`E5` sale del eje de identidad**; los dos gaps reales
> (derivar-vs-almacenar, y `inherit_capabilities=True` con `inherit_messages=False`) están en
> `A-CIERRE-P1 §AC-06`. **RV-5 en su forma más cara: un docstring no es evidencia de mecanismo — y aquí
> atravesó tres capas de destilación antes de que alguien abriera el archivo.**

### F · Backend de shell (`exec_env.py` — costura AÑADIDA por el runtime)
| ID | resumen | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **F1** 🔀 (AÑADIDO) | `ToolExecEnvironment` protocolo + inyección vía `ctx.exec_env` | núcleo | **T2-COSTURA** (exec backend) | costura `ToolExecEnvironment` + integrador (OI-20) | — | Sin contraparte canónica (BashTool habla directo con `Shell.ts`). Runtime lo hace inyectable (local/bwrap/remoto). **Seam VIVO** (confirmado): `bash.py:27-29` `exec_env.run_shell` ← `factory` → `ctx.exec_env`. Valor propio server-side |
| **F2** ❌ | `LocalExecEnvironment.run_shell` = subproceso **fresco** por llamada (sin shell persistente) | núcleo | **T2-COSTURA** (impl) | **→10·R8** | — | **FIND-TOOL8**. `exec_env.py:38-48` `create_subprocess_shell` nuevo cada vez ⇒ `cd`/env NO persisten entre llamadas Bash (diverge de `Shell.ts`). Aterriza en 10·bash; el seam es infra de 09 |
| **F3** 🔀 | `BwrapExecEnvironment` (aislamiento grueso) vs `sandbox-adapter.ts` (red/fs-rules/violation-store/hardening/wrapWithSandbox) | núcleo | **T2-COSTURA** + **T3-INTEGRADOR** (política sandbox) | integrador (OI-20) | — | `exec_env.py:51-97` monta workspace + ro-binds, **sin** (a) restricción de red (`allowedDomains`/`deniedDomains` derivados de `WebFetch(domain:*)`, unix-sockets, proxy, `SandboxAskCallback` por-host), (b) fs allow/deny **derivados de las reglas de permiso** `Edit`/`Read` por-source, (c) `SandboxViolationStore`+`annotateStderrWithSandboxFailures`, (d) hardening anti-escape (deny-write a `settings.json`/`.claude/skills`, `scrubBareGitRepoFiles` #29316, write al main-repo en worktrees), **(e) la capa operativa: `wrapWithSandbox(command)` + `excludedCommands` + `autoAllowBashIfSandboxed` + gating por plataforma/deps + refresh dinámico al cambiar settings** *(bloque (e) restituido del tracker `:156` por `A-CIERRE-P4 §2.2·P4-09-2`: es el **cómo se aplica**, y sin él OI-20 pedía una política sin decir dónde se engancha)*. El motor real está VENDORIZADO (`@anthropic-ai/sandbox-runtime`). Si se quiere paridad, el integrador envuelve un motor real |
| **F4** 🔀 | `ShellResult` (`output` combinado + `returncode`) vs stdout/stderr separados + `interrupted` + `backgroundTaskId` | núcleo | **T1-CONTRATO** (shell result) | base + **→10** (bg task-id) | — | `exec_env.py:20-26` combina stdout+stderr, sólo returncode. El background de Bash (10) no tiene dónde colgar el task-id |

### G · Confinamiento de filesystem (`fs_env.py`)
| ID | resumen | núcleo \| cáscara | TIER | destino | id | acción |
|---|---|---|---|---|---|---|
| **G1** ✅ | `contains_path_traversal` (regex byte-idéntico) | núcleo | **T2-BASE-MECANISMO** | base (`fs` confinamiento) | — | `fs_env.py:37/40` byte-idéntico a `containsPathTraversal`. **Confirmado** |
| **G2** 🟡 | `expand_path` (`~`, relativo→abs, colapsa `.`/`..`, null-byte) | núcleo | **T2-BASE-MECANISMO** | base | — | `fs_env.py:44-57`. **Omite** normalización Unicode NFC (afecta macOS) + conversión Windows (⛔). Menor |
| **G3** ✅ | `paths_for_permission_check` (original + realpath, anti-symlink) | núcleo | **T2-BASE-MECANISMO** | base | — | `fs_env.py:60-70`. **Confirmado** |
| **G4** 🟡 | `path_in_working_path` | núcleo | **T2-BASE-MECANISMO** | base (**FIND-TOOL9**) | — | `fs_env.py:73-82`. **Omite** macOS `/private/*`→`/var`,`/tmp` + case-fold (macOS/Windows case-insensitive). Linux server-side case-sensitive ⇒ bajo impacto; divergencia de seguridad si corre en macOS |
| **G5** ✅ | `path_in_allowed_working_path` (cada forma dentro de ALGÚN root) | núcleo | **T2-BASE-MECANISMO** | base | — | `fs_env.py:85-101` simetría de resolución path↔roots. **Confirmado** |
| **G6** 🔀/✅ | `ConfinedFilesystem.resolve(token,for_write)` — token→host vía `StorageContract` + confina | núcleo | **T2-BASE** (confina) + **T2-COSTURA** (`StorageContract`) | base + costura storage (→15) | eje persistencia (id opaco + repo) | `fs_env.py:144-152`. Traducción token→path = política del consumidor; confinamiento = mecanismo homologado. Bien desacoplado. Consumido por read/write/edit/glob/grep |
| **G7** 🔀 | split read-roots vs write-roots (`roots`/`write_roots`) | núcleo | **T2-BASE-MECANISMO** | base | — | `fs_env.py:128-131/146` separa allow-set por **conjuntos de roots**; canónico por **reglas**. Misma intención (write más estrecho), distinta forma. 🔀 razonable |
| **G8** ❌ | capa de safety AUSENTE (`DANGEROUS_FILES`/`DIRECTORIES`, `hasSuspiciousWindowsPathPattern`, `checkPathSafetyForAutoEdit`) | núcleo | **T2-COSTURA** (safety hook) | **→10·R3** + **Deuda B `B-02`** + integrador (OI-21) | — | **FIND-TOOL9**. `ConfinedFilesystem` es confinamiento de workspace **puro** (`fs_env.py:107-152`): un Edit/Write dentro del workspace puede tocar `.bashrc`/`.git/config`/`.claude/settings.json`. **Es política de permisos** (acceptEdits) → integrador; el runtime hoy no expone el gancho. Liga FIND-CTX1 (read-before-edit) |
| **G9** ❌/🔀 | internal editable/readable paths allow sin permiso (plan-file/scratchpad/job-dir/agent-memory/project-dir…) | núcleo | (cross **13/14/15**) | **→13/14/15** (NO gap de 09) | eje persistencia | El runtime NO los modela aquí; plan-file (14), memoria (13), storage (15) gestionan su acceso vía `StorageContract`. Cabo con destino; NO re-abrir como gap de 09. **↓ las 17 rutas nominales, restituidas del tracker `:173` (P4-09-1)** |

> **G9 · las 17 rutas internas auto-permitidas** *(restituidas por `A-CIERRE-P4 §2.2·P4-09-1`; el destino sin
> la lista era un puntero, no un requisito — 13/14/15 no podían implementar nada con él)*. Canónico
> `filesystem.ts:1510-1777`:
> - **WRITE sin permiso** (`checkEditableInternalPath`) — plan-file de sesión **[→14]** · scratchpad **[→15]** ·
>   job-dir (`CLAUDE_JOB_DIR`) **[→15]** · agent-memory **[→13]** · memdir (auto-mem) **[→13]** ·
>   `.claude/launch.json` **[→integrador]**.
> - **READ sin permiso** (`checkReadableInternalPath`) — session-memory **[→13]** · project-dir
>   (`~/.claude/projects/…`) **[→15]** · plan-file **[→14]** · tool-results-dir **[→15]** · scratchpad **[→15]** ·
>   project-temp-dir **[→15]** · agent-memory **[→13]** · memdir **[→13]** · tasks-dir **[→15]** · teams-dir
>   **[→15]** · bundled-skills-root **con nonce** **[→12]**.
> ⇒ **criterio para 13/14/15:** cada una debe declarar cuáles de estas rutas auto-permite y por qué eje
> (lectura/escritura). Lo que hoy sólo dice «lo gestiona `StorageContract`» no acredita ninguna.

**Total celdas: A×26 · B×7 · C×4 · D×10 · E×10 · F×4 · G×9 = 70.**

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`ToolProtocol` / contrato de tool** (T1-CONTRATO, `protocol.py`) — productor: `create_tools`/`registry.register` (batteries, MCP, skills registran) · consumidor: cada tool concreta + adaptador MCP (11) + el integrador (extras). El **contrato** (name/description/input_schema + result shape) → paquete contratos. Miembros de **comportamiento** faltantes (A3/A4/A6/A7/A8/A9/A11/A12/A13/A15/A23/A26) = crecer el contrato o costura de permisos.
- **`PermissionGate` / `check_permissions(input,ctx)`** (T2-COSTURA, home **06**/GAP-02) — productor: el loop dispara `PRE_TOOL_USE` **con `tool_input`** (`agent_loop.py:300-313`, honra `block`/`modified_input`) + el dispatcher chequea (`dispatcher.py:62`) · consumidor: el **integrador** provee la política (modos default/acceptEdits/plan/bypass, deny/allow rules, suggestions). **Seam input-aware VIVO** (descubierto abriendo B — el 09-tracker, centrado en el gate del dispatcher, lo subdeclaraba); falta el `check_permissions` per-tool + modos. Findings A6/A7/A8/A9/A20/D3/G8.
- **`ToolExecEnvironment`** (T2-COSTURA AÑADIDA, `exec_env.py`) — productor: `BashTool.execute` (`bash.py:27` `exec_env.run_shell`) · consumidor: `LocalExecEnvironment` (default) / integrador (bwrap/remoto/sandbox real). Findings F1/F2/F3/F4. Cableado factory→runtime→`ctx.exec_env`.
- **`ConfinedFilesystem` + `StorageContract`** (T2-BASE mecanismo + T2-COSTURA token→path, `fs_env.py`) — productor: fs-tools (read/write/edit/glob/grep, `fs_env.py:144`) · consumidor: `StorageContract` del integrador (roots + traducción token→path). Findings G1-G8. **eje persistencia** (id opaco + repo). El **safety-hook** (G8) es sub-costura de escritura → 10/integrador.
- **`DeferredToolStrategy`** (T2-BASE-MECANISMO con 2 impls + rama T1-MOTOR, `deferred_strategy.py`) — productor: `AgentLoop._resolve_deferred_strategy` (`agent_loop.py:132-150`) · consumidor: la capability del `model_caller` (`supports_native_tool_search`) elige Simulada (client-side) vs Nativa (`defer_loading`→`agentic_models`). Findings E1-E10. Lo **propio de 09**.
- **`presentation` (sanitize choke)** (T2-COSTURA, `dispatcher.py:42`) — productor: dispatcher · consumidor: `ctx.presentation` del integrador (sanitización por-identidad). Finding D9.

### 2.2 Batteries que alimenta (nombre · alcance)
- **Nativas (tool-provider)** — las 25 tools de `create_tools` (`factory.py:41-67`) son **batteries** concretas; su detalle es **10·tools-native** (Bash/Read/Edit/Glob/Grep/Web…) + 11 (MCP) + 12 (skills). 09 **compone** el pool, no define las tools. Nota: `ToolSearch` NO es battery — es **infra base** (necesaria para el mecanismo de deferral).
- **`tool-builder` (opcional)** — helper `build_tool`+defaults fail-closed (A21). Componible; hoy cada nativa implementa a mano (bajo riesgo por protocolo mínimo).
- **`structured-output`** — `output_schema` (A15) + `ToolResult.structured` (A22) → **Deuda B `B-structured-output`** (→05/16), no battery pura.
- **Nota:** el **ensamblado/dispatch/deferral/confinamiento** NO son batteries: son **base-mecanismo/costura**. Sólo el conjunto de tools concretas (10/11/12) y el builder opcional son componibles.

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
- **Gate de permisos por-tool input-aware + modos** — A6/A7/A8/A9/D3 (**FIND-TOOL2 = GAP-02**). El seam input-aware VIVE en el loop (`PRE_TOOL_USE`); falta `check_permissions` per-tool + modos default/acceptEdits/plan/bypass + `updatedInput`/suggestions. Home costura permisos (06) + `B-02`. **El mayor gap de 09.**
- **Concurrencia** — A3/D6 (**FIND-TOOL1**): dispatch secuencial, sin `is_concurrency_safe` ni cascada sibling. Prerequisito de 08·SIG3b. Home `B-concurrency`.
- **Señales de tool** — A4 (**FIND-TOOL3=SIG4** interrupt_behavior), A26/D8 (**FIND-TOOL5=SIG10** aborted con reason). Home 08/`B-signals`.
- **Motor de mensajes/contexto desde la tool** — A23/A24/D7 (**FIND-TOOL4**): `new_messages` no portado; `context_modifier` aplicado pero sin declarar/gating. Home `B-new_messages`.
- **Deferral: precedencia + multi-select + delta tipado + auto-mode + keyword-quality** — A13/E1 (**GAP-TOOL3**), E6 (**FIND-TOOL6**), E4/E5 (**FIND-TOOL7**), E9 (auto-mode→16), E7/A12 (searchHint). Home base (TiR2/3/5) + 16 + verificar 11.
- **Path-guards + safety-fs** — G2 (NFC), G4 (**FIND-TOOL9**: /private + case-fold), G8 (safety layer ausente). Home base + 10·R3.
- **MCP server-prefix deny** — B4. Home base + 11.
- **Shape/budget** — A14 (maxResultSizeChars→02), A15/A22 (structured→05/16), F4 (shell result / bg task-id→10), D10 (tool_progress→07·EVT6), A25 (mcpMeta→11).
- **Cabos con destino (no home aquí):** A2/E9/B7→16; A14→02; A20/A8/G8→06; F2/F4/B3/G8→10; A25/E8/E1/B2→11; G9→13/14/15; D2/D8/A4/A26→08; A15/A22→05/16; D10→07.

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10 anti-padding)
- **`B-orphans` (B2/FIND-TOOL10 + LAT-TOOL1)** — `NativeToolRegistry` (`native_registry.py`) tiene **0 consumidores de producción** (el factory devuelve `ToolRegistry`, `factory.py:69`; confirmado leyendo `factory.py` 1→EOF — `NativeToolRegistry` no aparece). + `ToolProtocol.category`/`ToolCategory` (`protocol.py:56`) es campo **requerido** que las 25 nativas setean pero **ningún código de producción lee** (slot muerto). El canónico no tiene ni `NativeToolRegistry` ni el enum de 5 valores como driver ⇒ **tech-debt B-interno** (extensión sin contraparte), hermano de `observer/`·`SignalBus`·`LAT-EXEC1`. **Borrar** o (si 11 necesita hot-plug MCP) unificar en `NativeToolRegistry` y retirar `ToolRegistry`.
- **`B-02` (parte)** — el gate deny-por-nombre del dispatcher (`dispatcher.py:62-65`) queda como mecanismo delgado tras portar el algoritmo de permisos; ripear si duplica al PRE_TOOL_USE. Cross 06.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05; vertido formal en A1.7)
Con **capacidad observable · origen (costura/battery del base) · firma que consume · cableado en el integrador · orden · criterio de aceptación**:

- **OI-18 · Componer y gatear el conjunto de tools** *(CONTRATO BASE COMÚN §1 — el "must-be" central)* — **capacidad:** todo integrador **elige y compone** su tool-provider set (qué nativas/MCP/skills registrar + gating por flag/env/usuario); el runtime registra TODO incondicionalmente. **origen:** B1/A5/B5 (`create_tools(extras)`, sin `isEnabled()` auto-gating). **firma:** `create_tools(extras)` + `registry.register` + `ToolRegistry` inyectado. **cableado:** el integrador arma el registry con su selección; el runtime lo ensambla en el pool sin conocer la política. **orden:** funda A2.1 (skeleton). **aceptación:** el runtime corre un turno con el pool que el integrador compuso; ninguna tool auto-gatea. *(realización: `agentic_code` = compone batteries + presets `--tools`; `agentic_assistant` = gating multi-tenant + modo simple.)*
- **OI-19 · Proveer la política de permisos por-input** *(CONTRATO BASE COMÚN §1 — obligación universal)* — **capacidad:** todo integrador **DEBE** proveer la política de permisos (modos default/acceptEdits/plan/bypass, deny/allow rules, ask/confirm de ops destructivas); el runtime sólo **dispara el punto** (`PRE_TOOL_USE`) y hace un deny-por-nombre delgado. **origen:** A6/A7/A8/A9/A20/D3/G8 (FIND-TOOL2=GAP-02). **firma:** hook `PRE_TOOL_USE(tool_name, tool_input, call_id, ctx)` → decisión `block`/`modified_input` (`agent_loop.py:300-313`, **seam VIVO**) + `check_permissions(input,ctx)` per-tool (a crecer en el contrato) + `PermissionContext` con modos. **cableado:** el integrador registra el hook y resuelve allow/ask/deny leyendo `app_state`; muta `app_state.permissions` para HITL. **orden:** tras A2.3 (tools) — es el nido de GAP-02. **aceptación:** una escritura peligrosa (`.bashrc`) o un input no permitido se deniega **por input**, no sólo por nombre. *(realización: `agentic_code` = prompt de aprobación en terminal + modos; `agentic_assistant` = reglas server-side + acceptEdits autónomo.)*
- **OI-20 · Elegir el backend de ejecución de shell + sandbox** *(CONTRATO BASE COMÚN + específico hosted)* — **capacidad:** todo integrador con ejecución de shell **DEBE** elegir un `ToolExecEnvironment` (local/bwrap/remoto) y su política de sandbox (red, fs allow/deny, hardening anti-escape, violation-store). **origen:** F1/F2/F3/F4. **firma:** `ToolExecEnvironment` protocol (`run_shell(command,*,timeout)->ShellResult`) inyectado en `ctx.exec_env`; para paridad de sandbox, envolver un motor real (equivalente a `@anthropic-ai/sandbox-runtime`). **cableado:** el integrador construye el backend y lo pasa a la factory (`config.exec_env`). **orden:** tras A2.3. **aceptación:** un comando corre aislado según la política del integrador **y, además (P4-09-2): el integrador ENVUELVE el comando (`wrapWithSandbox`), mantiene su lista de `excludedCommands`, decide si auto-permite Bash por estar sandboxeado, y RE-EVALÚA la política cuando cambian los settings** — un criterio que sólo compruebe «corre aislado» pasa sin nada de esto; el shell persistente (F2) y el bg task-id (F4) los aporta el integrador/10. *(realización: `agentic_code` = local/host; `agentic_assistant` hosted = bwrap/remoto + adaptador de sandbox con reglas de red/fs.)*
- **OI-21 · Proveer roots de confinamiento + traducción token→path + safety-fs** *(CONTRATO BASE COMÚN §1)* — **capacidad:** todo integrador provee el `StorageContract` (roots de lectura/escritura + `real_path(token)`) y la política de archivos peligrosos; el runtime aporta el **mecanismo** de confinamiento homologado (traversal/symlink/allow-set) pero no la política. **origen:** G6/G8/G9 (+ G2/G4 normalizaciones si corre en macOS). **firma:** `ConfinedFilesystem(roots, storage, write_roots)` + `StorageContract.real_path` + hook de safety en el gate de escritura. **cableado:** el integrador instancia el fs con sus roots y su `StorageContract`; el runtime confina. **orden:** con OI-19 (safety-fs es política de permisos). **aceptación:** un path fuera del allow-set o un archivo peligroso se rechaza; el token multi-tenant resuelve al path correcto. **id:** eje persistencia (id opaco + repo). *(realización: `agentic_code` = roots=cwd, token≡path; `agentic_assistant` = roots por-tenant sobre MinIO, token→path.)*
- **OI-22 · Renderizar tool-use / tool-result** *(CONTRATO BASE COMÚN — capa de interfaz/transporte §1)* — **capacidad:** todo integrador con interfaz **DEBE** presentar el uso y resultado de tools (los ~15 `render*` + activity-description + userFacingName + clasificación de colapso). **origen:** A17/A18/A19/B6 (CLI-ONLY/INTERFAZ). **firma:** el runtime entrega texto sanitizado (`ctx.presentation`, D9) + eventos (07); el integrador renderiza. **cableado:** el integrador se suscribe al stream/EventBus y pinta. **orden:** capa de interfaz, tras el motor. **aceptación:** el integrador muestra cada tool-use/result de forma legible. *(realización: `agentic_code` = React/ink terminal; `agentic_assistant` = capa front separada.)*
- **OI-23 · Observabilidad de auto-mode del tool** *(específico — política de producto, opcional)* — **capacidad:** proveer el input observable/clasificable para auto-mode (backfillObservableInput/toAutoClassifierInput). **origen:** A16. **firma:** hooks de observabilidad sobre el input del tool. **cableado:** el integrador hosted con auto-mode los consume. **aceptación:** un tool-use se clasifica para auto-aprobación. *(realización: `agentic_assistant` hosted; `agentic_code` off.)*

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por celda (70)
Evidencia abierta **este ciclo** 1→EOF (lectura propia, no heredada): `protocol.py` (62), `dispatcher.py` (85),
`pool.py` (79), `tools/factory.py` (76), `registry.py` (38), `native_registry.py` (42), `exec_env.py` (106),
`fs_env.py` (164), `deferred.py` (45), `deferred_strategy.py` (106), `deferred_delta.py` (117),
`native/tool_search.py` (79), `native/bash.py` (37) + ensamblador `loop/agent_loop.py` (352, **1→EOF, L09**).

| ID | TIER | destino | cara | evidencia (abierta este ciclo) | detalle | id |
|---|---|---|---|---|---|---|
| A1 | T1-CONTRATO | contratos | base | `protocol.py:53-55`+`dispatcher.py:71` | sí (§1) | — |
| A2 | T1-CONTRATO | contratos+16 | base | `protocol.py:54` (str fijo) | sí (TiR6) | — |
| A3 | T1-CONTRATO(campo) | `B-concurrency` | base | `protocol.py:52-61` (ausente) | sí (§2.3) | — |
| A4 | T1-CONTRATO(campo) | `B-signals`(SIG4) | base | `protocol.py:52-61` (ausente) | sí (§2.3→08) | — |
| A5 | T2-COSTURA | costura+integrador(OI-18) | ambas | `factory.py:69-73` (gating por extras) | sí (§2.5) | — |
| A6 | T2-COSTURA permisos | `B-02` | base | `dispatcher.py:62-65` (bool grueso) | sí (§2.3) | — |
| A7 | T2-COSTURA permisos | `B-02` | base | `protocol.py:57` (`requires_permission`) | sí (§2.3) | — |
| A8 | T2-COSTURA permisos | `B-02`+06 | ambas | `dispatcher.py:62-65` + `agent_loop.py:300-313` (PRE_TOOL_USE vivo) | sí (§2.5 OI-19) | — |
| A9 | T1-CONTRATO(método) | contratos+base | base | `dispatcher.py:71` (solo schema) | sí (§2.3) | — |
| A10 | T2-BASE (divergencia) | base | base | `fs_env.py:144` (confina en fs-tool) | sí (§1) | — |
| A11 | T1-CONTRATO(campo) | contratos+base | base | `pool.py:43` (name exacto) | sí (§1) | — |
| A12 | T1-CONTRATO(campo) | contratos+base | base | `tool_search.py:59` (sin searchHint) | sí (§2.3) | — |
| A13 | T2-BASE (deferral) | base+11 | base | `deferred.py:17-27` (sin precedencia) | sí (TiR5) | — |
| A14 | T2-BASE (budget) | →02 | base | `protocol.py:32` (str sin cota) | sí (§2.3) | — |
| A15 | T1-CONTRATO(campo) | `B-structured-output` | base | `protocol.py:18-36` (sin outputSchema) | sí (§2.3) | — |
| A16 | T3-INTEGRADOR/⛔ | integrador(OI-23)/— | integrador | tracker-leído (auto-mode policy) | sí (OI-23) | — |
| A17 | CLI-ONLY/INTERFAZ | integrador(OI-22) | integrador | tracker-leído (clasificación render) | sí (OI-22) | — |
| A18 | CLI-ONLY/INTERFAZ | integrador(OI-22) | integrador | tracker-leído (~15 render*) | sí (OI-22) | — |
| A19 | CLI-ONLY/INTERFAZ | integrador(OI-22) | integrador | `protocol.py` (sin userFacingName) | sí (OI-22) | — |
| A20 | T2-COSTURA permisos | →06 | base | tracker-leído (matcher `if`) | sí (§2.1) | — |
| A21 | T2-BASE (builder) | base (helper opc.) | base | `factory.py:41-67` (nativas a mano) | sí (§2.2) | — |
| A22 | T1-CONTRATO (result) | contratos+A15 | base | `protocol.py:18-36` (str plano) | sí (§1) | — |
| A23 | T1-CONTRATO+T2-BASE | `B-new_messages` | base | `agent_loop.py:319-323` (solo output) | sí (§2.3) | — |
| A24 | T2-BASE (aplicado) | `B-new_messages` (declarar) | base | `agent_loop.py:332-337` (getattr aplica) | sí (§1, CORR 10·J) | — |
| A25 | T1-CONTRATO (MCP) | →11 | base | tracker-leído (mcpMeta) | sí (§2.3) | — |
| A26 | T1-CONTRATO (reason) | `B-signals`(SIG10) | base | `protocol.py:47-48` (str genérico) | sí (§2.3→08) | — |
| B1 | composición | integrador(OI-18)+10 | integrador | `factory.py:41-67` (25 incond.) | sí (§2.5) | — |
| B2 | DEUDA-B (huérfano) | borrar\|11 | base | `factory.py:69` (devuelve ToolRegistry); `native_registry.py` no cableado (factory 1→EOF) | N/A (DEUDA-B) | — |
| B3 | T2-BASE-MECANISMO | base+reconciliar 10 | base | `registry.py:32-33`+`agent_loop.py:91-92` | sí (GAP-TOOL2) | — |
| B4 | T2-BASE (deny) | base+11 | base | `pool.py:64/70` (name exacto) | sí (§2.3) | — |
| B5 | T3-INTEGRADOR | integrador(OI-18) | integrador | tracker-leído (env-gated) | sí (OI-18) | — |
| B6 | CLI-ONLY/INTERFAZ | integrador(OI-18/22) | integrador | tracker-leído (REPL/presets) | sí (OI-18/22) | — |
| B7 | T1-MOTOR (token count) | →16 | base | tracker-leído (delega en provider) | sí (§2.3) | — |
| C1 | T2-BASE-MECANISMO | base (`pool`) | base | `pool.py:48-75` abierto 1→EOF | sí (§1) | — |
| C2 | T2-BASE-MECANISMO (invariante) | base (`pool`) | base | `pool.py:42-45`+`agent_loop.py:196`+`dispatcher.py:57` | sí (§1) | — |
| C3 | T1-CONTRATO (=A11) | contratos+base | base | `pool.py:43` (exacto) | sí (§1) | — |
| C4 | T2-BASE-MECANISMO | base (`pool`) | base | `pool.py:19-20`+`agent_loop.py:93-94` | sí (§1) | — |
| D1 | T2-BASE-MECANISMO | base (`dispatcher`) | base | `dispatcher.py:57` | sí (§1) | — |
| D2 | T2-BASE (abort) | base+08 | base | `dispatcher.py:54` (binario) | sí (§1) | — |
| D3 | T2-COSTURA permisos | `B-02`+06 | ambas | `dispatcher.py:62-65` + `agent_loop.py:300-313` | sí (§2.5 OI-19) | — |
| D4 | T2-BASE+T1-MOTOR | base+costura motor | base | `dispatcher.py:71` | sí (§1) | — |
| D5 | T2-BASE-MECANISMO | base (`dispatcher`) | base | `dispatcher.py:68/76` (timeout global) | sí (§1) | — |
| D6 | T2-BASE-MECANISMO | `B-concurrency` | base | `agent_loop.py:287` (for secuencial) | sí (§2.3) | — |
| D7 | T2-BASE | `B-new_messages` | base | `agent_loop.py:332-337` (ctx_mod sí, new_msg no) | sí (§2.3) | — |
| D8 | T2-BASE | `B-signals` | base | `dispatcher.py:83` (no captura CancelledError) | sí (§1 precisión L11) | — |
| D9 | T2-COSTURA presentación | base(choke)+costura | base | `dispatcher.py:42` (sanitize choke) | sí (§2.1) | eje persist. |
| D10 | T1-CONTRATO (evento) | →07 (EVT6) | base | tracker-leído (sin progreso intra-tool) | sí (§2.3) | — |
| E1 | T2-BASE (deferral) | base+11 | base | `deferred.py:17-27` | sí (GAP-TOOL3) | — |
| E2 | T2-BASE-MECANISMO | base (`deferred_strategy`) | base | `deferred_strategy.py:54-79` (filtra `:67`) | sí (§1) | — |
| E3 | T2-BASE-MECANISMO+T1-MOTOR | base+costura motor | base | `deferred_strategy.py:82-97`+`agent_loop.py:143-148` | sí (§1) | — |
| E4 | T2-BASE-MECANISMO | base (canal tipado) | base | `deferred_delta.py:26/52-88` (parseo texto) | sí (TiR3) | — |
| E5 | T2-BASE-MECANISMO | base | base | `deferred.py:31/34-37` (materializado, copy-safe) | sí (TiR3) | eje ejecución |
| E6 | T2-BASE (deferral) | base (TiR2) | base | `tool_search.py:53-55` (single) | sí (§2.3) | — |
| E7 | T2-BASE (deferral) | base | base | `tool_search.py:57-63` (substring) | sí (§2.3) | — |
| E8 | T2-BASE (deferral) | base+11 | base | `tool_search.py:69-78` (JSON inline) | sí (§1) | — |
| E9 | T2-BASE (deferral) | base+16 | base | tracker-leído (difiere incond.) | sí (TiR6) | — |
| E10 | T2-BASE-MECANISMO | base | base | `tool_search.py:67` (en execute) | sí (§1) | — |
| F1 | T2-COSTURA (exec) | costura+integrador(OI-20) | ambas | **ensamblador** `factory.py:210` (`config.exec_env or Local`) → `:228` → `runtime.py:90/318` (`ctx.exec_env=self._exec_env`) → `bash.py:27` (consumidor). Cadena 1→consumidor abierta este ciclo (L09) | sí (OI-20) | — |
| F2 | T2-COSTURA (impl) | →10·R8 | base | `exec_env.py:38-48` (subproc fresco) | sí (§2.3) | — |
| F3 | T2-COSTURA+T3-INTEGRADOR | integrador(OI-20) | integrador | `exec_env.py:51-97` (aislam. grueso) | sí (OI-20) | — |
| F4 | T1-CONTRATO (shell result) | base+10 | base | `exec_env.py:20-26` (combinado) | sí (§2.3) | — |
| G1 | T2-BASE-MECANISMO | base (`fs`) | base | `fs_env.py:37/40` (byte-idéntico) | sí (§1) | — |
| G2 | T2-BASE-MECANISMO | base | base | `fs_env.py:44-57` (sin NFC) | sí (§1) | — |
| G3 | T2-BASE-MECANISMO | base | base | `fs_env.py:60-70` | sí (§1) | — |
| G4 | T2-BASE-MECANISMO | base (FIND-TOOL9) | base | `fs_env.py:73-82` (sin /private+case-fold) | sí (§2.3) | — |
| G5 | T2-BASE-MECANISMO | base | base | `fs_env.py:85-101` | sí (§1) | — |
| G6 | T2-BASE+T2-COSTURA | base+costura storage(15) | ambas | `fs_env.py:144-152` (token→path) | sí (§2.1) | eje persistencia |
| G7 | T2-BASE-MECANISMO | base | base | `fs_env.py:128-131/146` (read/write roots) | sí (§1) | — |
| G8 | T2-COSTURA (safety) | →10·R3+`B-02`+integrador(OI-21) | ambas | `fs_env.py:107-152` (sin safety) | sí (OI-21) | — |
| G9 | (cross 13/14/15) | →13/14/15 | base | tracker-leído (StorageContract gestiona) | sí (§1 cabo) | eje persistencia |

**LAT-TOOL1** (`.category`/`ToolCategory` slot muerto, `protocol.py:10-15/56`) + **B2** (`NativeToolRegistry` huérfano) → **DEUDA-B `B-orphans`** (tech-debt B-interno, NO fila de la tabla A↔B).

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../09-tools-infra.md`?** — **Sí**, líneas 1→492 (encabezado + contrapartes · tesis arquitectural · leyenda · grid A1-G9 · §Hallazgos FIND-TOOL1-10/GAP-TOOL1-3 · cabos resueltos SIG4/SIG3b/SIG10/GAP-MODE2 · recuento · ledger de archivos · §Re-visita de COMPLETITUD 2ª vuelta con LAT-TOOL1 + 2 precisiones + refinamiento huérfano + auto-corrección de honestidad + 4 preguntas · §Plan de remediación TiR1-TiR6). Además `00-LEGEND.md` (1→159) y `SEPARACION/05-execution.md` como plantilla.
2. **¿Reconcilia el conteo?** — celdas en `../09-tools-infra.md` = **70** (A×26 · B×7 · C×4 · D×10 · E×10 · F×4 · G×9); colocadas = **70**; sin colocar = **0**. ✅ Los 10 `FIND-TOOL*` + 3 `GAP-TOOL*` + `LAT-TOOL1` (consolidaciones) mapean todos a celdas: FIND-TOOL1=A3/D6; FIND-TOOL2=A6/A7/A8/A9/D3(=GAP-TOOL1=GAP-02); FIND-TOOL3=A4; FIND-TOOL4=A23/A24/D7; FIND-TOOL5=A26/D8; FIND-TOOL6=E6; FIND-TOOL7=E4/E5; FIND-TOOL8=F2; FIND-TOOL9=G4/G8; FIND-TOOL10=B2; GAP-TOOL2(=GAP-MODE2)=B3; GAP-TOOL3=A13/E1; LAT-TOOL1=`.category` (→DEUDA-B). *(El «recuento» del tracker "✅9·🟡14·🔀16·❌18·⛔6" es su tally por-estado con sub-celdas mezcladas; el conteo real de **celdas del grid** es 70, todas repartidas — mismo fenómeno que 02·loop "~46 vs 54" y 05 "8/9/9 vs 36".)*
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, TODO abierto en ESTE ciclo 1→EOF** (14 archivos B; ninguna ancla heredada del tracker). Anclas ✅/🔀 confirmadas por lectura propia:
   - **Invariante del pool único (✅ C1/C2/C4/D1):** `agent_loop.py:194-196` (`ctx.tool_pool=_build_tool_pool` → `assemble` → schemas `:197-200`) + `_build_tool_pool:85-97` (native `list_available(mode)` + `capability_manager.build_tool_pool`) + `pool.py:42-75` (assemble+find) + `dispatcher.py:57` (`ctx.tool_pool.find`). La **ejecución resuelve del MISMO objeto** — leído literal, no por tabla.
   - **Deferral (✅ E2/E10 · 🔀 E3/E4/E5/E8):** `deferred_strategy.py:54-97` (Simulada filtra `:67`, Nativa `defer_loading` `:91`) seleccionada por `supports_native_tool_search` (`agent_loop.py:143-148`); `deferred_delta.py:26/52-88` (parseo texto); `deferred.py:31/34-37` (materializado, `mark` REEMPLAZA clave ⇒ copy-safe); `tool_search.py:67` (mark en execute).
   - **exec_env seam VIVO (🔀 F1) — cadena de población abierta este ciclo (L09):** `factory.py:210` `exec_env = config.exec_env or LocalExecEnvironment()` → `:228` al ctor → `runtime.py:90` `self._exec_env=exec_env` → `runtime.py:318` `ctx.exec_env = self._exec_env` → `bash.py:27` consumidor. La 1ª emisión sólo ancló consumidor+seam (heredaba la factory del tracker); **subsanado** abriendo `factory.py:203-234` + `runtime.py:67/90/318`.
   - **Orfandad B-orphans re-verificada por grep PROPIO este ciclo (no heredada):** `NativeToolRegistry` = 0 consumidores prod (sólo `tools/__init__.py`/`__init__.py` export + `test_runtime_contracts.py`/comentario en test + su definición); `.category` = 0 lectores en `src/agentic_runtime/**.py`. Corroborado por `factory.py:218-234` (return pasa sólo `tool_registry`=ToolRegistry; `NativeToolRegistry` no aparece).
   - **fs-guards (✅ G1/G3/G5 · 🔀 G6/G7):** `fs_env.py:37/60/85/128-152` leídos 1→EOF.
   - **dispatch/gate/timeout (✅ D4 · 🔀 D5/D9 · ❌ D3/D6):** `dispatcher.py:42/57/62-65/68/71/76/83` + `agent_loop.py:287/300-313/319-323/332-337` — **hallazgo nuevo al abrir B (L11):** el loop dispara `PRE_TOOL_USE` con `tool_input` (seam de permisos input-aware VIVO), que el 09-tracker —centrado en el gate del dispatcher— subdeclaraba; anotado en A8/D3/§2.1/OI-19.
   - **❌ de no-cableado** (B2 huérfano, D6 secuencial): `factory.py` **1→EOF** confirma que devuelve `ToolRegistry` y NO cablea `NativeToolRegistry`; `agent_loop.py:287` for-loop confirma dispatch secuencial — **por lectura del ensamblador**, no sólo grep.
   - **Cero contradicción al re-abrir:** todas las anclas ✅/🔀 confirmadas exactas; la única corrección es un **añadido** (el PRE_TOOL_USE vivo), no una sobre-declaración volteada.
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla 6 obligaciones (OI-18…OI-23) con los 6 campos L05. **Contrato base común** (must-be de todo integrador): OI-18 (componer/gatear tools), OI-19 (política de permisos por-input), OI-20 (backend shell+sandbox), OI-21 (roots+token→path+safety-fs), OI-22 (render tool-use/result). **Específico:** OI-23 (auto-mode hosted). Ninguno cerrado con "→ integrador" a secas. *(Vertido formal a `00-INTEGRADORES.md` en A1.7.)*
5. **¿Doble filo (L10)?** — **Sí.** Ningún ❌ disfrazado de 🔀: el gate de permisos (FIND-TOOL2), la concurrencia (FIND-TOOL1), interrupt/aborted (FIND-TOOL3/5), new_messages (FIND-TOOL4), multi-select (FIND-TOOL6), safety-fs (FIND-TOOL9/G8) siguen **CORE-GAP**, no degradados a 🔀. Ninguna deuda inflada: `NativeToolRegistry` (B2) + `.category` (LAT-TOOL1) son **DEUDA-B interna** (extensión sin contraparte canónica, 0 consumidores prod — confirmado leyendo `factory.py` 1→EOF), **NO** deuda A↔B; las costuras AÑADIDAS (`ToolExecEnvironment` F1, `NativeDeferredStrategy` E3) se mantienen **🔀-valor-propio**, no gap. Anti-padding: la precisión de D8 (`except Exception` no captura `CancelledError`) **restó** un supuesto gap ("aplana AbortError") que el tracker sobre-declaraba, dejando sólo A26 (🟡 real).

### 3.3 VEREDICTO
**✅ NADA PENDIENTE → A1.7 (síntesis de la ESPINA + `SEAMS.md`).**
Las 70 celdas (A1-G9) repartidas con TIER+destino: **T1-CONTRATO** del tool (schema+result, con miembros de comportamiento a crecer: concurrency/interrupt/permisos/validate/new_messages/output_schema/searchHint/aliases) + **T2-BASE-MECANISMO** (pool único `assemble`/`find`, dispatch, timeout global, deferral Simulada/Nativa, confinamiento fs homologado) + rama **T1-MOTOR** (`defer_loading`→`agentic_models`, validación de schema) + costuras **`ToolProtocol`** / **`PermissionGate`** (PRE_TOOL_USE vivo, 06/GAP-02) / **`ToolExecEnvironment`** (AÑADIDA) / **`ConfinedFilesystem`+`StorageContract`** / **`DeferredToolStrategy`** / **`presentation`** + batteries compuestas (nativas→10, MCP→11, skills→12; `tool-builder` opcional) + 6 obligaciones de integrador (OI-18…OI-23). CORE-GAPs para DEUDA-A: gate de permisos por-input (FIND-TOOL2=GAP-02, el mayor), concurrencia (FIND-TOOL1), señales de tool (FIND-TOOL3/5→08), new_messages (FIND-TOOL4), deferral (GAP-TOOL3/FIND-TOOL6/7 + auto-mode E9→16 + keyword E7), path-guards+safety (FIND-TOOL9→10), MCP-deny B4→11. DEUDA-B: `B-orphans` (`NativeToolRegistry` + `.category`). Hilo transversal de identidad (nota-identidad → rollup DEUDA-A): G6 (`StorageContract` token→path, eje persistencia), G9 (internal paths→13/14/15), ~~E5 (discovered-set por `agent_id`, eje ejecución)~~ **[RETIRADO — ver ⚠ tras la tabla E: `E5` no está keyado por identidad]**, D9 (sanitize por identidad). Cabos con destino explícito (16: A2/B7/E9/A15; 02: A14; 06: A8/A20/G8; 08: A4/A26/D2/D8; 10: F2/F4/B3/G8; 11: A25/E8/E1/B2/B4; 07: D10; 13/14/15: G9; 05/16: A15/A22) — ninguno es pendiente de **verificación**.
