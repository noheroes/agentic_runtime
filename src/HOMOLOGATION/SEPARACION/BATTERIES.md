# BATTERIES — catálogo formal de paquetes componibles (rollup transversal **A3.CAT**)

> **Qué es este documento.** El tercer y último rollup transversal de la Fase A3 (tras `DEUDA-A.md` y `DEUDA-B.md`).
> No es una categoría: es el **catálogo** que destila las **§2.2 (BATTERY) de los 18 `NN-*.md`** + `00-BLUEPRINT §3`
> + `DEUDA-A §1.2` + `DEUDA-B §3.A` + `00-INTEGRADORES`, y responde la pregunta que `00-INTEGRADORES.md:142` dejó
> abierta *verbatim*: **«necesarias vs opcionales se fijan en A3.CAT»**.
>
> **Regla de arquitectura que gobierna todo el documento** (Filosofía B, `00-BLUEPRINT §3`): una battery se
> **compone o se sustituye, NUNCA se sobreescribe**. El base no trae catálogo por defecto: sin composición hay un
> núcleo que corre un turno de texto y nada más (`18·OI-FAC-1`).
>
> **Criterio de admisión al catálogo (anti-padding, L10 doble filo).** Una battery necesita **las tres** cosas:
> (1) **alcance** propio y nombrable, (2) **costura de composición** existente o nombrada, (3) **al menos un
> integrador que la componga** y, típicamente, otro que la **sustituya**. Lo que no cumple las tres **no entra**:
> es base-mecanismo, costura, CORE-GAP o contenido del integrador. §5 lista lo **excluido con su razón** — esa
> sección es parte del producto, no un apéndice.

---

## §0.1 · Evidencia de lectura de este ciclo (GENERADA de `EVIDENCIA.log`, no recordada)

> Remedio estructural de `A3.DB·RV`: una línea por lectura, escrita **al leer**. Si una lectura no está en el log,
> para el gatekeeper **no ocurrió**. Filtro `A3.CAT` → **40 entradas**.

| bloque | qué se abrió | alcance |
|---|---|---|
| **PASO 0** | `~/.claude/skills/analisis-comparativo-ab/lecciones/*.md` (11 + README) | **1→EOF cada una** (547 L) |
| **Barrido que ES el ciclo** | las **18 §2.2 (BATTERY)** de `01`…`18` | tramo exacto de cada una (rangos en el log) |
| **Insumos transversales** | `00-BLUEPRINT.md` **1→199 íntegro** (+ re-lectura acotada §3 126-151) · `00-INTEGRADORES.md` **1→207 íntegro** · `DEUDA-A.md` §1.2/§1.3 (288-349) · `DEUDA-B.md` §3.A (220-319) | íntegro / tramo |
| **Cabo del vertido (A3.DA §3)** | las **§2.5 (OI-\*) de los 12 ciclos A3**: `03`·`04`·`06`·`08`·`10`·`11`·`12`·`13`·`14`·`15`·`17`·`18` | tramo exacto de cada una |
| **Cableado (nunca grep)** | `agentic_runtime/factory.py` **1→268 = 1→EOF** · `execution/local/runtime.py` 210-269 (call-sites de voz) | ensamblador abierto |

**Lecturas añadidas EN EL GATE de cierre** (a raíz de la pregunta *«¿hiciste EoF en todos?»*, y no antes):
`runtime.py` **395-436 = hasta EOF** (verifica los dos anclajes `:410` y `:430` que el catálogo citaba **heredados**
de 05·§2.2 y `DEUDA-A §1.2(a)` — **ambos correctos**) · `DEUDA-B.md` **470-519 (§4 los 8 cabos + §5 hallazgos)** —
**esta lectura produjo CAT-h7 y forzó una retractación** · `PLAN.md` **1-116 + 130-133**.

**2ª tanda del gate (2026-07-27), tras la pregunta «¿y qué hay de los pendientes Q1, Q2 y Q5?»:**
`DEUDA-B.md` **158-219** (§2 Ledger maestro + §2.b) · **`SEAMS.md` 1-436 = 1→EOF (435 L)**. Ambas en el log.
**Consecuencia:** **V1 deja de ser un pendiente** (§8.4) y **Q2 se rehizo a nivel de ítem** (§8.2), lo que destapó
**un ítem sin colocar** que la 1ª redacción no vio (→ §5, fila `ModelsConfig`/OR1, y **CAT-h8**).

**Lo que este ciclo NO abrió** (y por tanto no afirma): ~~`SEAMS.md`~~ **(abierto 1→EOF en la 2ª tanda del gate;
la costura de §4.5 ya está numerada: S30/S31)**; los cuerpos completos de los 18 `NN-*.md` fuera de §2.2/§2.5 (**el encargo acotó ahí**);
`DEUDA-A.md` fuera de 288-349; `DEUDA-B.md` fuera de 220-319 y 470-519; `PLAN.md` **117-129** (filas de checklist de
ciclos ya cerrados: bitácora histórica que no gobierna A3.CAT — decisión declarada, no descuido); `runtime.py`
1-209 y 270-394; el código de las capabilities.

**Evidencia HEREDADA declarada (no propia).** `00-BLUEPRINT.md` 1→199 y `00-INTEGRADORES.md` 1→207 se abrieron
**íntegros en esta sesión pero antes de una compactación**. Post-compactación sólo se re-abrieron los tramos que
este ciclo **edita** (`00-BLUEPRINT` 126-151 y 179-206; `00-INTEGRADORES` 135-169 y 238-241). Por la regla de
`A3.DB·RV`, la lectura íntegra es **HEREDADA**: sirve de procedencia, **no** se invoca como evidencia propia. Lo
mismo vale para las **10 §2.5** leídas pre-compactación (03·04·06·08·10·11·12·13·14·15): el índice de
`00-INTEGRADORES §1.7` descansa en **las líneas de `EVIDENCIA.log` escritas al leer** —que es exactamente para lo
que existe el remedio— y su granularidad no excede la de esas líneas, salvo donde el dato viene de `17`/`18`/`12`,
que **sí** están en contexto.

---

## §1 · Veredicto sobre "necesarias vs opcionales" (la pregunta de `00-INTEGRADORES:142`)

**Ninguna battery es obligatoria para el base. Todas son opcionales — sin excepción.** Ésa es la respuesta, y no es
una evasiva: es la consecuencia directa de `18·OI-FAC-1` (*«el base no trae un catálogo por defecto»*) y de su
criterio de aceptación ejecutable (*«un runtime compuesto sin `battery_mcp` no importa `McpProvider` en ningún
punto»*). Un base con una battery obligatoria es un base que la importa siempre, y eso destruye el criterio.

Lo que **sí** es obligatorio se desplaza al integrador (`18·OI-FAC-3`): **declarar su perfil y tratar el ensamblado
incompleto como fatal**. Por eso el catálogo publica **perfiles** en vez de "obligatorias":

| perfil | quién | contenido |
|---|---|---|
| **`núcleo`** | el base a secas | ninguna battery. Un turno de texto contra el motor. Útil como diana de tests de aislamiento, no como producto. |
| **`estándar-terminal`** | `agentic_code` (integrador FINO) | compone **muchas** con defaults mínimos: las 11 de estrategia/subagente + `hooks_config` + `plan` + `skills` + `memory` + el bloque de tools nativas + `persistence.{config,session_meta}` + `voice`. |
| **`hosted-multi-tenant`** | `agentic_assistant` (integrador COMPLEJO) | compone **selectivamente** y **sustituye** lo que su orquestación ya posee: sustituye `hooks_config` (motor de política propio), `persistence.{session_catalog,outputs}` (MinIO/multi-tenant), el `SpeechSink` de `voice`, y el catálogo de agentes; compone `mcp`/`skills`/`memory`/`compaction`/`resilience`/`caching`/`budget`/`wire`. |

**Consecuencia dura, no cosmética:** hoy el ensamblador **viola** este veredicto en un punto exacto —
`PlanModeProvider()` se registra **incondicionalmente** en `factory.py:146`, sin campo de config que lo gatee,
mientras `mcp` (`:148`), `skills` (`:160`) y `memory` (`:166`) sí son condicionales. Ver **CAT-h3**.

---

## §2 · El catálogo — **33 unidades de composición**

> **Unidad de composición = un objeto `Battery` (S28)**, no un paquete de distribución. Es la granularidad a la que
> un integrador puede **sustituir sin tocar el resto** — y por eso es la granularidad correcta del catálogo (ver la
> resolución del cabo 2 en §4.2). Columnas: `alcance` · `costura de composición` · `origen (NN)` · `CORE-GAPs que la
> completan` · `qué se borra del base al extraerla`.

### 2.1 Estrategia del turno (8) — nacen de la espina A1.7, hogar en categoría

| # | battery | alcance | costura de composición | origen | CORE-GAPs | se borra del base |
|---|---|---|---|---|---|---|
| B01 | **`compaction`** | EL motor de compactación/presupuesto: trigger por umbral (02·B6), microcompact (B4), collapse (B5), snip (B3), tool-result budget (B2), boundary/vista (B1/B7), blocking-limit guard (B9), recuperación PTL (D1), cache-edits (C9). Emite `CompactBoundaryEvent` | **S9 `CompactionProvider`** + trigger del loop; `16` aporta **la detección** (`is_context_overflow`, 16·C2) | 02 (motor) · 01·CTR-09 (seam) · 07·H1 (evento) · 16·C2 | **K6** (bloque entero) | n/a — no existe hoy |
| B02 | **`resilience`** | retry/backoff+jitter/retry-after · 529→fallback-de-modelo · streaming→non-streaming · idle-watchdog. Emite `ApiRetryEvent` | **S10 `RetryPolicy`/`with_retry`** en el loop | 16·B1-B4 · 02·C4/C5/C7/D2 · 07·J3 | `16·FIND-MODELS5/6/7` + `B4` | n/a |
| B03 | **`caching`** | estrategia rica de `cache_control`: TTL-elegibilidad · global-scope · skip-write · cache_edits · split de bloques cache-scoped del system prompt | envuelve la maquinaria wire del motor (**compone o sustituye**, no parchea) | 16·A1/B6 | — (sin CORE-GAP propio) | n/a |
| B04 | **`budget`** | token-budget auto-continue +500k con nudge/diminishing-returns · cost-cap por request | consume usage-accounting (**S1**) + coste/modelo | 02·E1/D6/B9 · G2 | depende de `B-usage` (recalificado a CORE-GAP por 07) | n/a |
| B05 | **`commands`** | drain de comandos encolados + lifecycle (02·F8/F14) + preproceso slash/inline (G1) · `local_command_output` (07·J6) | **S11 `UserInputProcessor`** (hoy `existe-sin-poblar`) | 01·CTR-12 · 02 · 03·A10/B11 · 07·J6 · cross 12 | — | n/a |
| B06 | **`wire`** | serializador `Event→SDKMessage` (24 variantes) + `SessionInfo`; produce `init`/`result`/`session_state` al wire. **El core no lo conoce** | **S6 wire-sink** (`subscribe_all`) | 07·GAP-EVT5 · **07·K4** (convertSDKMessage) · **07·K5** (SDKSessionInfo) | keystone **`DA·K4`** (identidad en el `Event` base) — **único**; el `K5` que figuraba aquí queda **RETIRADO**, ver nota | n/a |
| B07 | **`structured-output`** | `SyntheticOutputTool` + `jsonSchema` con reintentos; endpoints tipados del BFF | **S16 `output_schema`** + driver (05) | 02·G3 · 09·A15/A22 | `K5` (`ToolResult.structured`) · `16·FIND-MODELS9` | n/a |
| B08 | **`voice`** *(`agentic_runtime_voice`)* | **dos canales**: entrada `AudioPromptResolver` (`AudioInput`→prompt) **+ salida `SpeechSink`** (TTS incremental sobre `TokenEvent`/`DoneEvent`, saneado por `PathPresentation`). Alcance AMPLIADO por 17: la espina sólo vio la entrada | **salida = S5 `EventBus.subscribe` (ya existe) + K4 = S31 `SpeechSink`**; **entrada = S30 `PromptSourceProtocol`** (§4.5; numeradas en `SEAMS.md` en el gate) | 01·CTR-06 · 03 · **17·CG-V1..V5** | `CG-V1` (extracción) · `CG-V3` · `CG-V4` (saneo per-chunk) · `CG-V5` (STT falla ⇒ prompt vacío; 2 líneas, mejor ratio del inventario) · `CG-V2`=**K4** | **sí, y es el único caso con evidencia hoy**: `VoiceConfig` (`factory.py:64-75`) · `RuntimeConfig.voice` (`:84`) · gate `:212-216` · paso `:238-239` · `LocalAgentRuntime(stt=,tts=)` (`:76-77,:106-107`) · `_resolve_prompt` (`runtime.py:220-232`) · `_wire_tts` (`:234-262`) = **DB-24** |

> ⚠ **Colisión de espacio de nombres en B06, desambiguada en A-CIERRE·P4″** (consecuencia 31 de `A-CIERRE-P4 §13.7`).
> La fila usaba `K4`/`K5` en **dos espacios de nombres distintos a la vez**: como **filas del grid de 07**
> (`07·K4` = `convertSDKMessage`, `07·K5` = `SDKSessionInfoSchema`) en la columna *origen*, y como **keystones de
> `DEUDA-A`** (`K4` = identidad en el `Event` base, `K5` = `ToolResult`, cf. B07) en la columna *CORE-GAPs*.
> Los `K\d` de 07 **son filas nativas de su grid** (bloque K · Transcripto), no extras locales: **renumerarlos
> rompería la reconciliación 44=44 del par**. El remedio es **disciplina de prefijo** (`07·Kn` para filas,
> `DA·Kn` para keystones), aplicada arriba.
> **RESUELTO 2026-07-29 (`AC-26` cerrado, `D-06·1`) — y la resolución corrige el planteamiento, no sólo la fila.**
> La redacción anterior decía: *«el `K5` de la columna CORE-GAPs admite dos lecturas —`07·K5` (SessionInfo) o el
> keystone `DA·K5` (ToolResult)—. Bajo `D-06·3` no la resuelvo por mi cuenta: más de un resultado defendible»*.
> Falso: **ninguna de las dos es admisible**, y comprobarlo costó tres lecturas puntuales.
> - **`07·K5` es 🔀**, no CORE-GAP — así consta en el tracker (`../07-events.md:196`) y en el destilado
>   (`07-events.md:105` fila del grid y `:358` fila del ledger §3.1, ambas `T2-COSTURA / BATTERY storage`).
>   **Un 🔀 no puede ocupar una columna titulada *CORE-GAPs*.** Su destino (→ 15·storage) ya lo lleva la columna
>   *origen* de esta misma fila, que es donde corresponde.
> - **`DA·K5` es `ToolResult` enriquecido** (`DEUDA-A.md:255`, `new_messages`+`structured`/`output_schema`): no
>   tiene relación alguna con el serializador wire, y su hogar es **B07**, que ya lo reclama explícitamente.
>
> ⇒ el `K5` era un **arrastre desde la columna *origen*** de la propia fila al redactarla. **Retirado**; `DA·K4`
> queda como único keystone de B06. **Ningún CORE-GAP se pierde** en la operación: `DA·K5` sigue contabilizado en
> B07 y `07·K5` nunca fue uno.
> **Lección de método (por qué esto no era una decisión del usuario):** la pregunta que planteé fue *«¿cuál de las
> dos?»* cuando la pregunta correcta era *«¿alguna de las dos es admisible en esta columna?»*. Elevar una binaria
> sin haber comprobado la **admisibilidad** de sus ramas es el tell **`binaria-delegada`** (`DECISIONES D-06`) — y
> `D-06·3` («preguntar sólo si hay más de un resultado defendible») **no ampara** el caso: aquí no había ninguno.

### 2.2 Ciclo de vida del subagente (3)

| # | battery | alcance | costura | origen | CORE-GAPs | se borra |
|---|---|---|---|---|---|---|
| B09 | **`result-summary`** | condensación **final-only** del resultado del subagente antes de inyectarlo al padre. El coordinator periódico es **⛔ fuera de alcance** | componible en el ciclo de vida; **hoy cableado duro en `runtime.py:410`** | 05·E29 | — | **sí**: la condensación horneada en `runtime.py:410` |
| B10 | **`handoff-classifier`** | classifier de seguridad del output del subagente, feature-gated. Alternativa legítima: política del integrador hosted | hook de política / S17 | 05·E27 | — | n/a |
| B11 | **`background-agents`** | `post_turn_summary` estructurado (`status_category`/`needs_action`/`artifact_urls`) de un turno background | battery → 05/13 | 07·F3 | consume `H-5` (canal de notificación sin drenador, hallazgo `RV-7`) | n/a |

> **Vecindad declarada, no fusionada:** B09 y B11 ambos "resumen". Son distintos —B09 condensa *el resultado para el
> padre*, B11 produce *un estado estructurado del turno*— y ninguno de los dos es hoy código vivo, así que fundirlos
> sería una decisión sin evidencia. Se registra la vecindad para Fase C.

### 2.3 Capabilities (6) — hogar en ciclos A3, **es el bloque con toda la deuda A↔B**

| # | battery | alcance | costura | origen | CORE-GAPs | se borra |
|---|---|---|---|---|---|---|
| B12 | **`battery_mcp`** | la capacidad MCP entera (12 módulos `mcp/*.py`): config·scope·store·client·provider·state·auth·token_storage·tool_adapter·resource_tools·reconcile | `CapabilityProvider` vía `caps.extra_providers`; **hoy 5 campos dedicados** en `CapabilitiesConfig` (`factory.py:37,42,46,54,55` → `:148-158`) | 11 | **`CG-MCP-1..20`** — el bloque más grande del rollup. Sub-keystone `CG-MCP-1` (naming FQ `mcp__srv__tool`) gatea permisos FQ + swap; núcleo `CG-MCP-8` (ciclo de vida robusto) | **sí, al extraer**: los 5 campos de `CapabilitiesConfig` + el `if` de `:148-158` |
| B13 | **`battery_skills`** | el comportamiento skills completo: loader multi-fuente+precedencia+dedup · frontmatter 16 campos + 2 ejes · `render_skill`/prompt-provider+substitución+bash · gate de permisos · `skill_listing` incremental+budget · entrega new_messages+prompt · model/effort override · fork-dispatch · skill-hooks · condicionales · ranking · bundled programáticos · aliases · cleanup · hot-reload | `CapabilityProvider`; **hoy 3 campos** (`:34,38,47` → `:160-164`) | 12 | **`CG-SKILL-1..15`**; keystones internos `CG-SKILL-1` (frontmatter/2 ejes) y `CG-SKILL-2` (bash-injection con gate `loaded_from != 'mcp'` — **seguridad**). Gap MAYOR: `CG-SKILL-4` (**el standalone no surface el listing**) | **sí**: los 3 campos + el `if` |
| B14 | **`battery_mcp_skills`** *(bridge)* | prompts MCP→slash-commands (`mcp__srv__prompt`) + skills `skill://` con `loaded_from='mcp'`; gate `MCP_SKILLS && supportsResources`. Builder real `mcpSkills.ts` **NO vendorizado (⛔)** | `Battery.requires() = {battery_skills, battery_mcp}` (S28) | 11 + 12 | `CG-SKILL-15` / `FIND-MCP16` | n/a (no existe) |
| B15 | **`battery_memory`** | memdir concreto: `FilesystemMemoryStore` · `rank_memories`/`RecallStrategy` · `build_memory_activation` · `_truncate_entrypoint` · scan recursivo/cap · frontmatter plano+enum · `MemoryExtractor` | `CapabilityProvider` + **hook `Stop`** vía `Battery.hooks(host)`; **hoy 2 campos** (`:50,51` → `:166-172`) | 13 | **`CG-MEM-1..10`**; el grande es `CG-MEM-2` (auto-extracción por fork ⇒ depende de **K7+K1**). `CG-MEM-1` absorbe el guard-path (**K3**) | **sí**: los 2 campos + el `if`. Además **DB-26** (borrado) se ejecuta dentro de la remediación de **H-1** (memoria rota por autogen) |
| B16 | **`battery_plan`** | capacidad de plan (rendir el plan aprobado como orientación durable, one-shot de salida) **+ sus tools `EnterPlanMode`/`ExitPlanMode`** (10) **+ sus agent-definitions vía `Battery.agents(host)`** | `CapabilityProvider` + `agents()`; **hoy INCONDICIONAL `factory.py:146`, sin campo de config** ⇒ **CAT-h3** | 14 + 10 | **`CG-PLAN-1..11`**; `CG-PLAN-1`=**K1**, `CG-PLAN-2`⇢**K7**, `CG-PLAN-3`⇢**K2/ID-3** | **sí**: el registro incondicional `:146` pasa a condicional; el hack `app_state.native["plan_mode"]` = **DEUDA-B `B-02`** |
| B17 | **`battery_hooks_config`** | el **motor de hooks configurable estándar**: hooks tipados (`command`/`prompt`/`agent`/`http` + SSRF) · `matchesPattern` (exact/pipe/regex) · `matchQuery` · `if` (permission-rule syntax) · `once` · `async`/`asyncRewake` · dedup namespaced · resolución multi-fuente (settings/plugin/skill/frontmatter/SDK) · `processHookJSONOutput` | **S8 `HookRunner`** — que **el integrador debe proveer**: `RuntimeConfig.hook_runner=None` por defecto (`factory.py:86`) ⇒ hoy, aunque una battery devolviera hooks, **no habría dónde registrarlos** (`18·C2`) | 06 | — (es el reificado del "🔀 delegado" del tracker: **battery, no CORE-GAP**, L10) | n/a |

### 2.4 Persistencia (4) — la familia `battery_persistence.*`

| # | battery | alcance | costura | origen | CORE-GAPs |
|---|---|---|---|---|---|
| B18 | **`persistence.session_meta`** | metadatos de sesión (15·B4/B10) | **S13 `StorageContract`** | 15 | `CG-STOR-2` (durabilidad incremental del transcript: hoy snapshot-overwrite por completion, `runtime.py:430` ⇒ crash mid-turn pierde el turno) |
| B19 | **`persistence.config`** | config persistida (15·A2-A8/E1) | S13 | 15 | `CG-STOR-5` (frontera `StorageContract`↔`StorageProtocol` + adaptador) |
| B20 | **`persistence.session_catalog`** | catálogo/listado de sesiones (15·B8). **`requires()` = `session_meta`** | S13 | 15 | `CG-STOR-4` (`download_range`) |
| B21 | **`persistence.outputs`** | artefactos de salida (15·D2/D3) | S13 | 15 | — |

### 2.5 Tools nativas (11) — el pool que 09 **compone** y 10 **define**

> 09 compone el pool; **no define las tools**. Las 25 clases de `create_tools` (`tools/factory.py`, invocado en
> `factory.py:189`) se reparten en estas unidades.

| # | battery | alcance | nota |
|---|---|---|---|
| B22 | **`battery_fs_tools`** | `Read`/`Write`/`Edit`/`Glob`/`Grep` (+`NotebookEdit`); guards R0/R2/R3/R5/R6/R7 + fileHistory-undo. Consume `ctx.fs`, `ctx.fs_safety`, `ctx.read_file_state` | **la más gruesa: concentra la deuda A↔B de 10** — `FIND-NATIVE-READSTATE` (keystone de 10) · `EDITGUARDS` · corrección de READ · `R4` |
| B23 | **`battery_shell`** | `Bash`: persistent-shell (R8) + `interpretCommandResult` (R9) + sed-edit (B9) + preventCwd (B11). Consume **S15 `ToolExecEnvironment`** (impl viva) | `B12/R9` |
| B24 | **`battery_web`** | `WebFetch`/`WebSearch`, mínimos viables provider-adaptados | política de dominio/provider = **integrador** (OI-web-policy) |
| B25 | **`battery_meta`** | `Config`/`TodoWrite`/`Sleep`/`AskUserQuestion` | consumidores de `context_modifier`/`ends_turn` |
| B26 | **`battery_worktree`** | `EnterWorktree`/`ExitWorktree` | `safe_for_background=True` (R10) |
| B27 | **`battery_clone`** | `clone_repository` | seam `git_credentials` (`factory.py:91`) |
| B28 | **`battery_agent`** | superficie de tool `Agent` | mecánica de ejecución/registry = **base (05)**. ⚠ **CAT-h5** |
| B29 | **`battery_task`** | superficie de las tools `Task*` | ⚠ **CAT-h5: las 6 `Task*` fallan SIEMPRE hoy** (DB-h1) ⇒ su composición no es verificable hasta **K7** |
| B30 | **`battery_brief`** | capacidad **no portada** (10·K1) | requiere `ToolResult.new_messages` = **K5** |
| B31 | **`battery_synthetic`** | capacidad **no portada** (10·K2) | requiere `structured-output` (B07) |
| B32 | **`battery_cron`** | capacidad **no portada** (10·K5) | requiere `StorageContract` (S13) |

### 2.6 Helper (1)

| # | battery | alcance | nota |
|---|---|---|---|
| B33 | **`tool-builder`** | helper `build_tool` + defaults fail-closed (09·A21) | **opcional de verdad**: hoy cada nativa implementa a mano y el riesgo es bajo porque el protocolo es mínimo. Se cataloga como conveniencia, no como capacidad |

---

## §3 · Trazabilidad: las 18 §2.2 → el catálogo (una fila por ciclo, incluidas las vacías)

| ciclo | qué aportó a este catálogo |
|---|---|
| 01·contracts | **origina 0 propias**; nacen aquí los *shapes*/seams de `compaction`(B01) · `voice`(B08) · `commands`(B05) |
| 02·loop | **B01 (el MOTOR)** · B04 · B05 · B07; alimenta memory. **Nota explícita: el error-recovery del modelo NO es battery** |
| 03·context | **origina 0 propias**; confirma que sus campos NO viajan en el ctx. Alimenta B05/B15/B16/B08 |
| **04·modes** | **NINGUNA** — backgrounding y derivación de modo son **primitivas del base**. *«Inventar una battery aquí sería padding (L10)»* |
| 05·execution | **B09 · B10**; `permissions` = alimentada (hogar = costura de permisos 02·F2); **`resume` ⇒ ver CAT-h1**. Lifecycle/fork/reaping = **base** |
| 06·hooks | **B17** |
| 07·events | **B06** · el *evento* de B01 · B11 · alimenta B05 |
| **08·signals** | **NINGUNA** — la cancelación es **primitiva del base**. Anti-padding (L10) |
| 09·tools-infra | **B33**; compone el pool de B22-B32. `structured-output` aquí es *deuda*, no battery pura. **`ToolSearch` = infra base, NO battery** |
| 10·tools-native | **B22-B32** (11) |
| 11·cap-mcp | **B12 · B14** |
| 12·cap-skills | **B13 · B14**; bundled de producto **NO** es battery base |
| 13·memory | **B15**; team-memory **NO** es battery (T3-INTEGRADOR) |
| 14·plan | **B16**; `battery_builtin_agents` **⇒ resuelto, no existe** (§4.3) |
| 15·storage | **B18-B21** |
| 16·models | **B02 · B03** + la *detección* que B01 consume |
| 17·voice | **B08 con alcance ampliado a TTS** + el reparto de qué se borra del base (DB-24) |
| 18·factory | el **mecanismo** de composición (S28/S29) y la evidencia `battery ↔ if-por-nombre` del ensamblador; remite aquí obligatoria-vs-opcional |

---

## §4 · Los 5 cabos que los rollups dejaron a A3.CAT — **resueltos**

### 4.1 Cabo 1 (`A3.DA §3`) · Verter los OI-\* al contrato de integradores — **HECHO**

`00-INTEGRADORES §1` sólo contenía la espina A1.7 (OI-1..23 / OI-M1..8 / OI-EVT-1..4). Los OI-\* de los **12 ciclos
A3** no estaban vertidos. Este ciclo abrió las 12 §2.5 y los vierte en **`00-INTEGRADORES.md §1.7`** como índice
consolidado por familia, con puntero al ciclo dueño (el detalle L05 de 6 campos vive en el `NN-*.md`, no se duplica).
Familias vertidas: `OI-A..E` (03) · `OI-MODE-A/B` (04) · `OI-HOOK-A..E` (06) · `OI-SIG-A/B/C` (08) · las 9 de tools
nativas (10) · `OI-MCP-A..I` (11) · `OI-SKILL-A..H` (12) · `OI-MEM-A..G` (13) · `OI-PLAN-A..D` (14) ·
`OI-STOR-A..F` (15) · `OI-VOICE-1..5` (17) · `OI-FAC-1/2/3` (18).

### 4.2 Cabo 2 (`15·§2.4`) · `battery_persistence` ¿1 paquete o 4? — **4 unidades, 1 distribución**

La pregunta mezcla dos granularidades y la respuesta las separa:

- **Unidad de composición = 4.** El criterio decisorio es **qué puede sustituir un integrador por separado**:
  `agentic_assistant` sustituye `session_catalog` y `outputs` (multi-tenant sobre MinIO) mientras **compone**
  `config` y `session_meta`. Si fueran una sola `Battery`, sustituir el catálogo obligaría a reimplementar los
  metadatos ⇒ se rompe *«se compone o se sustituye, nunca se sobreescribe»*.
- **Distribución = 1** (`battery_persistence`), porque las 4 comparten **una** costura (S13) y `session_catalog`
  declara `requires() = {session_meta}`. Empaquetarlas juntas no crea acoplamiento de importación relevante: todas
  importan lo mismo.

*Regla general que se extrae:* **el catálogo cuenta unidades de composición; el packaging es una decisión posterior
y de menor consecuencia.** El único criterio que obliga a separar paquetes es el de aislamiento de importación de
`OI-FAC-1` — y ése es exactamente el que decide el cabo 3.

### 4.3 Cabo 3 (`12`) · `battery_skills` + `battery_mcp_skills` ¿1 o 2? — **2, y por criterio ejecutable**

**2 batteries.** No es una preferencia estética: `OI-FAC-1` fija un criterio de aceptación **ejecutable** —
*«un runtime compuesto sin `battery_mcp` no importa `McpProvider` en ningún punto»*. Si el bridge viviera dentro de
`battery_skills`, componer skills **sin** MCP arrastraría el import de MCP y **el test de aislamiento fallaría**.
`battery_mcp_skills` se declara con `requires() = {battery_skills, battery_mcp}` (S28) y sólo se compone cuando
ambas están. Su alcance real es hoy parcialmente **⛔ no-leíble** (`mcpSkills.ts` no vendorizado), lo que **no**
cambia la decisión de empaquetado.

**Corolario del cabo 14 (`battery_builtin_agents`)** — **no existe como battery.** S28 ya tiene una fase
`agents(host)`: "llevar agent-definitions" es una **forma que cualquier battery puede tomar**, no un paquete. Los
built-ins de plan los aporta `battery_plan.agents(host)`; los agentes **no** específicos de plan son **contenido del
integrador** (`agent_resolver`, que **compone** su catálogo con el de las batteries, no lo sustituye —`18·C3`), en
simetría exacta con el fallo de 12 sobre los bundled skills de producto. Inventar el paquete habría sido padding.

### 4.4 Cabo 4 (`B-02`/`factory.py:146`) · ¿`battery_plan` es battery o base? — **battery, y OPCIONAL**

Battery (**B16**), opcional como todas (§1). El registro incondicional de `PlanModeProvider()` en `factory.py:146`
—verificado con el ensamblador abierto 1→EOF, y contrastado con `mcp`/`skills`/`memory` que **sí** son
condicionales— es una **decisión de composición horneada en el base**, y por tanto contradice el veredicto.

**Dónde aterriza la consecuencia (corregido en el gate, ver CAT-h7).** La 1ª redacción la abrió como ítem nuevo de
`DEUDA-B.md`. **Es incorrecto:** `DEUDA-B §4 · cabo 7` **ya había fallado el tier** de este mismo `:146` —
*«decisión de composición → A3.CAT, **no deuda**; lo que sí queda como DEUDA-B es el canal no tipado
`app_state.native["plan_mode"]` (DB-19), tras K1»*— y A3.CAT lo contradijo sin haber abierto §4. Reparto correcto:
**la decisión** es de este catálogo (§4.4); **la ejecución** —retirar el literal de `:146` y que
`Battery.providers(host)` lo aporte— es **trabajo de composición de Fase C**, no un ítem de higiene. `DEUDA-B.md`
**no gana ítems**; su reparto 12/12 y su conteo 18=18=0 quedan intactos.

### 4.5 Cabo 5 (`DB-24`) · Qué costura sustituye la voz que se retira del base

Al extraer **B08** el base pierde 7 cosas (columna de §2.1). La sustitución **no es simétrica**, y ésta es la parte
sustantiva del cabo:

| lo que se retira | qué lo sustituye | estado de la costura |
|---|---|---|
| `_wire_tts` (`runtime.py:234-262`) — **salida** | **S31 `SpeechSink`** — no necesita canal nuevo: se suscribe por **S5 `EventBus.subscribe(TokenEvent/DoneEvent)`**, que **ya es costura pública y viva**. Lo único que falta es que el sink sepa *de qué agente* es el evento (hoy lo resuelve con `ctx.is_subagent`, `:239`) ⇒ **depende de K4** (campos de identidad en el `Event` BASE) | **`existe-horneada`** (S31, registrada en `SEAMS §0/§3/§4`) + K4 |
| `_resolve_prompt` (`runtime.py:220-232`) — **entrada** | **S30 `PromptSourceProtocol`**: resolución de entrada a nivel de **`RuntimeTask`**, `resolve(task, ctx) -> str`, ejecutada **antes** de que exista el `AgentLoop`. **No** es S11: S11 `UserInputProcessor` es **intra-turno**, su productor es el loop y su poder es cortocircuitar el turno; `_resolve_prompt` es **pre-loop** y consume `ctx` (`:228`). Dos productores, dos ciclos de vida ⇒ **dos costuras, no una** (resuelve la vecindad que `17·§2.7` dejó abierta) | **`existe-horneada`** (S30) — **numerada al abrir `SEAMS.md` 1→EOF en el gate**; CAT-h6 queda **RESUELTO** |
| `VoiceConfig.stt_enabled`/`tts_enabled` | **nada**: *no componer la battery **es** el gate* (17·C1). Si se quiere toggle en caliente vive dentro de la battery | — |
| `RuntimeConfig.voice` · gate `:212-216` · paso `:238-239` · `LocalAgentRuntime(stt=,tts=)` | **nada**: son superficie de voz en un ensamblador genérico. Su sustituto es la lista `batteries=[...]` de S28 | — |
| saneo por `PathPresentation` (`:244`) | **se conserva y se corrige**: pasa a `S31.sanitize` (con estado ENTRE chunks), arreglando de paso `CG-V4`/`FIND-VOICE1` (saneo per-chunk rompe secuencias a caballo entre chunks; test `xfail(strict=True)` en `tests/test_voice_homologation.py:54-78`) | **S12 corregida a `existe-parcial`** en `SEAMS.md` (era `existe-fiel`, contradiciendo su propio cuerpo: `to_llm` sin call-site) — 3ª corrección de 17·§2.7 aplicada |

**Orden:** la extracción de B08 **no puede preceder a K4**, o la salida pierde la capacidad de filtrar subagentes.

**Estado de la asimetría, ya con números (cerrado, no propuesto):** entrada = **S30**, costura *nueva* a nivel
`RuntimeTask`; salida = **S31**, que **no** añade canal (monta sobre S5) pero sí absorbe el saneo de S12 y **queda
detrás de K4**. Ninguna de las dos está `ausente`: ambas son **`existe-horneada`** — el comportamiento existe hoy
*porque* está dentro del base. Eso cambia la naturaleza del trabajo de Fase C: no es *construir*, es **exteriorizar
sin perder comportamiento**, que es más barato de estimar y más fácil de falsar.

**Y una trampa que la extracción tenía puesta, evitada al abrir `DEUDA-A` 1→EOF:** la firma de hoy es
`transcribe(audio, ctx)`/`speak(text, ctx)` con el **`ToolUseContext` completo** — `user_id`, `session_id`,
`messages` (la conversación entera), `tool_pool`, `storage`, `fs`, `git_credentials`— entregado a un motor de
terceros. `DEUDA-A ID-6(b)` lo tipifica como **fuga** y `00-LEGEND §2.4` lo prohíbe. **Extraer copiando la firma
actual habría convertido una fuga horneada en un contrato público**, que es estrictamente peor. S30/S31 toman
`VoiceCallContext` (id opaco + metadata + stop), la pieza que ID-6 ya había diseñado. 【id-opaco】

---

## §5 · Lo que NO entra al catálogo (y por qué) — parte del producto, no apéndice

| candidato | veredicto | razón (con su dueño) |
|---|---|---|
| backgrounding · derivación de modo (04) | **base-mecanismo** | primitivas del núcleo; *«inventar una battery aquí sería padding»* (04·§2.2) |
| cancelación / señales (08) | **base-mecanismo** | primitiva del base (08·§2.2); su deuda es `CG-SIG-1..9`, CORE-GAP |
| ensamblado · dispatch · deferral · confinamiento (09) | **base-mecanismo/costura** | 09·§2.2 explícito. ⚠ **CAT-h2**: `DEUDA-A §1.2(b)` los archivó bajo BATTERY |
| esqueleto del loop · error-recovery resiliente (02·C4/C5/C7/D2) | **base-mecanismo** | sólo la *estrategia* (retry policy) es componible ⇒ eso ya es B02 |
| ciclo de vida · fork · reaping (05) | **base-mecanismo** | sólo condensación (B09) y clasificación (B10) son componibles |
| `ToolSearch` | **infra base** | necesaria para el mecanismo de deferral (09·§2.2, `00-BLUEPRINT §3` nota) |
| bundled skills de producto (los 15 de Claude Code) | **contenido del integrador** | el *mecanismo* `registerBundledSkill` sí es de B13; el contenido es ⛔ SK-NA-3 / OI-SKILL-F |
| agentes no específicos de plan | **contenido del integrador** | simetría con la fila anterior; §4.3 |
| team-memory | **T3-INTEGRADOR** | multi-tenant sync; su guard-path pliega en `CG-MEM-1`, su secret-scan es seam opcional (13·§2.2) |
| `permissions` / `agentGetAppState` (05·E20) | **costura**, no battery | el hogar del algoritmo es la costura de permisos (02·F2/K1); el ripeo del hack = DEUDA-B `B-02` |
| `resume` de subagente (05·E26) | **CORE-GAP**, no battery | ⚠ **CAT-h1** |
| `structured-output` visto desde 09 | **deuda**, no battery pura | 09·§2.2 lo manda a `B-structured-output` (→05/16); como *estrategia* sí es B07 |
| 13·memory y 14·plan como fuente de paquetes extra | **nada extra** | ambos cerraron con **CERO DEUDA-B propia**; no se les inventan packages (anti-padding explícito del encargo) |
| **bridge de modelo ← `ModelsConfig` no consumido (`18·§2.2`, OR1/LAT-MODELS1)** | **ni battery ni base: ya colocado como DEUDA-B** | **Éste es el ítem que la 1ª redacción dejó sin colocar (CAT-h8).** `18·§2.2` lo nombra en su fila de batteries, pero **no es una unidad componible**: es un **slot muerto del ensamblador** — `RuntimeConfig.models: ModelsConfig` (`factory.py:83`) **nunca se lee** en `_build_local`; el caller entra por `factory.py:219` (`model_caller=config.model_caller`). La costura real ya existe y es **S1 `ModelCallerProtocol`**, y `SEAMS §4` la nombra con ese mismo nombre: *«NO `:83` = slot muerto `ModelsConfig`/LAT-MODELS1»*. **Hogar ya asignado por A3.DB:** `DEUDA-B.md §2` fila **2.10 → DB-10**, repartido **BORRAR (a) · CABLEAR (b)**. El catálogo **no lo re-tiera** (regla CAT-h7): sólo registra por qué no es battery |

---

## §6 · Hallazgos emitidos por A3.CAT (11 — los cinco últimos los produjo el propio gate de cierre)

- **CAT-h1 · `resume` está catalogado como battery y no lo es.** `05·§2.2:140` lo lista como battery *(«diferido»)*,
  pero `A3.DA·H-3` lo recalificó a **CORE-GAP con hogar nuevo en 05** (*«`resume` NO existe»*). El catálogo **lo
  retira** de batteries. *Acción:* corregir `05·§2.2` en **A-CIERRE**.
- **CAT-h2 · `DEUDA-A §1.2(b)` tiene una fila mal ubicada.** Archiva bajo **BATTERY** los ítems de **09·tools-infra**
  (concurrencia · señales · deferral · safety-fs · MCP-deny · shape/budget), que `09·§2.2` declara **base-mecanismo/
  costura** de forma explícita. Los de **10** sí son battery. *Acción:* mover esa fila a `(a) BASE` en **A-CIERRE**.
- **CAT-h3 · `PlanModeProvider()` es incondicional (`factory.py:146`) y debe pasar a componerse.** Decisión de
  composición horneada en el base. *Remediación:* `Battery.providers(host)` (S28) sustituye el literal de `:146`.
  *Tier:* **NO es DEUDA-B** — ver CAT-h7. *Ejecución:* **Fase C** (trabajo de composición), no ledger de higiene.
- **CAT-h7 · (hallazgo del gate de cierre, auto-detectado) A3.CAT re-tieró un ítem que A3.DB ya había fallado, sin
  abrir el tramo donde lo falló.** La 1ª redacción abrió `CAT-DB-1` en `DEUDA-B.md §10`. Al abrir `DEUDA-B §4` en el
  gate apareció el **cabo 7**, que ya decía *«decisión de composición → A3.CAT, **no deuda**»*. **Retractado**:
  `DEUDA-B.md §10` registra ahora la retractación y el ledger 12/12 · 18=18=0 queda intacto. *Causa:* de `DEUDA-B.md`
  se leyó **§3.A y nada más** (leer §4 "los 8 cabos" era obligatorio: es donde A3.DB dejó lo que **remitía a este
  ciclo**). *Regla que se escribe:* **antes de emitir un ítem contra un doc cerrado, abrir la sección donde ese doc
  resolvió cabos — un rollup posterior no re-tiera lo que un rollup anterior ya falló.*
- **CAT-h4 · Estado rancio en `00-BLUEPRINT §5/§6`:** marcaban `DEUDA-B.md` como ⬜ pese a que **A3.DB y A3.DB·RV
  están cerrados**. *Corregido en este ciclo.*
- **CAT-h5 · `battery_agent`/`battery_task` tienen alcance hoy inoperante.** `DB-h1` estableció que **las 6 tools
  `Task*` fallan SIEMPRE**. Se catalogan (su superficie existe) pero **su composición no es verificable hasta K7**;
  cualquier "✅ compone" sobre ellas antes de K7 sería una afirmación sin sustento.
- **CAT-h6 · ~~La costura de entrada de voz se propone SIN número~~ → RESUELTO en el gate (2026-07-27).** El
  razonamiento original era correcto (*numerar sin abrir el registro sería el error que `17·§2.7` ya documentó tres
  veces*), pero la conclusión —remitirlo a A-CIERRE— era **falsa economía (L00)**: bastaba abrir 435 líneas. Hecho:
  `SEAMS.md` **1→EOF**. Resultado: **S30 `PromptSourceProtocol`** (entrada, pre-loop) y **S31 `SpeechSink`** (salida,
  sobre S5, detrás de K4), ambas registradas en `SEAMS §0/§3/§4`, y **las 3 correcciones de 17 aplicadas**.
- **CAT-h8 · (gate) La reconciliación de Q2 estaba hecha sobre el denominador equivocado.** La 1ª redacción marcó
  Q2 ✅ contando **secciones barridas** (18/18 §2.2) en vez de **ítems nombrados → ítems colocados**. Al enumerar los
  nombres de battery de las 18 §2.2 aparece **1 sin colocar**: el *bridge de modelo ← `ModelsConfig`* (OR1) de
  `18·§2.2`, que no estaba ni entre las 33 ni entre las exclusiones. **No era una battery perdida**: `DEUDA-B §2`
  fila **2.10** lo tenía colocado como **DB-10**. *Efecto real:* ninguno sobre el reparto (el ítem tenía hogar); el
  fallo era **de reconciliación**, y una reconciliación que no puede detectar un ítem sin colocar no es una
  reconciliación. *Corregido:* §5 gana su fila; §8.2·Q2 se re-enuncia a nivel de ítem. *Regla:* **un conteo de
  cierre se hace sobre la unidad que se reparte (ítems), nunca sobre el contenedor que se recorre (secciones).**
- **CAT-h9 · (gate) `SEAMS.md` tenía dos incoherencias internas, y la corrección de por qué sobrevivieron es más
  interesante que las incoherencias.** (a) el índice §0 se titulaba **"(20)"** y listaba **27** filas —la propia L54
  decía 27—; (b) **S12** figuraba `existe-fiel` en el índice mientras su propio cuerpo decía *«`to_llm` sin
  call-site»*, que bajo la convención de estado del encabezado es `existe-sin-poblar`. *Corregidas ambas* (29 y
  `existe-parcial`). **⚠ Corrección a mi propia explicación:** escribí *«nadie lo había abierto desde A1.7»*. **Falso,
  y lo desmiente el propio `DEUDA-A §0.1` (L30-33):** `SEAMS.md` **sí** se abrió 1→EOF en el tramo de re-verificación
  de **A3.DA**. *Lo que de verdad pasó, y es la lección:* esa lectura íntegra iba **dirigida a una pregunta** (cotejar
  las anclas del hilo de identidad) y **una lectura íntegra dirigida a una pregunta no verifica la coherencia interna
  del documento** — pasó por encima de "(20) vs 27 filas" sin verlo. *Corolario para A-CIERRE:* «abierto 1→EOF» debe
  registrarse **con la pregunta que lo abrió**, o se lee como una garantía que no da.
- **CAT-h10 · (gate) `DEUDA-A` quedó rancio respecto de `DEUDA-B` en la forma de K4, y ninguno de los dos lo
  arregló.** `DEUDA-A §1.1·K4` se titula *«Sobre del evento (`EventEnvelope`)»* y `§2·ID-6` da como firma
  `@dataclass class EventEnvelope: …`. **`DEUDA-B §7.2` cerró exactamente lo contrario, y con razón técnica
  verificada:** `EventBus.emit` despacha por **`type(event)`** (`bus.py:40`), luego un envelope que envuelva colapsa
  los tipos y **rompe el despacho tipado**; la forma correcta son **campos de identidad en el `Event` BASE**
  (`task_id`/`agent_id`/`session_id`/`seq`/`ts`), viable porque los 5 subtipos tienen todos sus campos con default.
  El propio §7.2 escribió *«sigue siendo CORE-GAP en `DEUDA-A`»* **pero no fue a corregirlo allí**. *Efecto:* quien
  lea `DEUDA-A` de buena fe implementará la forma descartada. *Acción:* **A-CIERRE** corrige `DEUDA-A §1.1·K4`,
  `§2·ID-6` y la fila 9 de `§2.8`. *Este catálogo ya usa la forma vigente* (§4.5) — no por mérito, sino porque A3.DB
  estaba en contexto cuando se redactó. *Regla:* **una decisión que corrige un doc cerrado se aplica EN ese doc, no
  sólo se anota en el que la toma.**
- **CAT-h11 · (gate) El propio bloque de cierre había sustituido dos de las cinco preguntas del gate y se rotulaba
  «VERBATIM».** Ver la nota al pie de §8.2. Las dos desaparecidas eran **«¿reconcilia el conteo?»** y **«¿doble
  filo?»** — precisamente las dos que destapan CAT-h8 y la cara-base vacía de 10 de 33. *Regla:* **el gate no se
  re-redacta; si una pregunta propia aporta, se añade numerada aparte y marcada como propia.**

---

## §7 · Qué queda fuera del alcance de A3.CAT (y a quién va)

| pendiente | destino | por qué no aquí |
|---|---|---|
| Firma final de `Battery`/`compose()` (S28) y `RuntimeManifest` (S29) | **Fase C** | **BORRADOR NO VALIDADO**: A2.4 compuso *una* battery por constructor, no por catálogo (L09). Este catálogo *usa* S28 como vocabulario; **no la declara validada** |
| ~~Numerar la costura de §4.5 + las 3 correcciones de `17·§2.7` a `SEAMS.md`~~ | **HECHO en el gate** | ya no es pendiente: `SEAMS.md` abierto 1→EOF ⇒ **S30/S31** + S12 corregida + índice 29. CAT-h6/h9 |
| **Exteriorizar** S30/S31 (hoy `existe-horneada`) sin perder comportamiento | **Fase C**, S31 **detrás de K4** | es trabajo de composición sobre código, no de diseño; A3 no toca runtime (`PLAN §1.6`) |
| `00-BLUEPRINT §1.4` "Módulos base del resto" | **A-CIERRE** | es el complemento de este catálogo: lo que **no** es battery es base, y §5 le entrega la lista |
| Auditoría símbolo-a-símbolo de las entradas BORRAR (regla RV-6) | **A-CIERRE** | ya estaba abierto antes de este ciclo |
| Realización concreta de los perfiles §1 en cada integrador | **Fases E/F** | requiere los integradores vivos |

---

## §8 · GATEKEEPER de cierre (`00-LEGEND §3.3`)

> **Frase de rigor.** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo
> respalda; ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede
> sin colocar —o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá
> incompleto e inútil.

### 8.1 Ledger — una fila por ítem del encargo

| # | ítem del encargo | resultado | evidencia |
|---|---|---|---|
| 1 | Barrido de las **18 §2.2** (*«ese barrido ES el ciclo»*) | **18/18** | 18 líneas en `EVIDENCIA.log` con rango exacto; trazadas una a una en §3 (incluidas las 2 vacías y las 2 que no originan propias) |
| 2 | `00-BLUEPRINT §3` | leído 1→199 + re-lectura §3 | §2 absorbe las 11 de espina + la fila de alimentadas + la nota NO-son-batteries (→ §5) |
| 3 | `DEUDA-A §1.2` como insumo directo (no re-derivar) | usado tal cual | columna "CORE-GAPs" de §2.3/§2.1 copia el reparto (b); **detectada 1 fila mal ubicada** → CAT-h2 |
| 4 | `DEUDA-B §3.A` (qué se borra condiciona quién re-hospeda) | usado | DB-24 → §4.5 completo; DB-26 → B15; B-02 → B16 |
| 5 | `00-INTEGRADORES` | leído 1→207 | §1.5:142 **respondido** en §1; §1.7 creada con el vertido |
| 6 | **Cabo 1** — verter los OI-\* | **resuelto** | §4.1 + edición de `00-INTEGRADORES §1.7`; 12 §2.5 abiertas y logueadas |
| 7 | **Cabo 2** — persistence 1 vs 4 | **resuelto: 4 unidades / 1 distribución** | §4.2, con el criterio decisorio explícito |
| 8 | **Cabo 3** — skills vs mcp_skills | **resuelto: 2** | §4.3, por el criterio **ejecutable** de OI-FAC-1 |
| 9 | **Cabo 4** — plan battery/base, obligatoria/opcional | **resuelto: battery, opcional** | §4.4 + `factory.py` abierto 1→EOF; emite CAT-h3 |
| 10 | **Cabo 5** — qué costura sustituye la voz | **resuelto, asimétrico** | §4.5, con `runtime.py:210-269` abierto; salida = **S31** (sobre S5) + K4, entrada = **S30** — numeradas al abrir `SEAMS.md` 1→EOF en el gate |
| 11 | Anti-padding (04 y 08 SIN battery; 13/14 sin DEUDA-B propia) | **respetado** | §3 registra 04/08 como **NINGUNA**; §5 última fila; §4.3 **elimina** un paquete que el encargo permitía inventar (`battery_builtin_agents`) |
| 12 | Catálogo con **alcance** por battery | **33 unidades** | §2.1-§2.6, 6 columnas |

### 8.2 Las 5 preguntas de cierre (Q1-Q5 = las del gate, **restauradas**; Q6-Q7 = propias, marcadas como tales)

**Q1 · ¿Abrí íntegro todo lo que sostiene cada afirmación, o hay algo clasificado sin abrir?**
**Sigue siendo `no`, pero el perímetro cambió y hay que decir en qué dirección.** *1→EOF ahora:* las 11 lecciones +
README · `factory.py` (268) · `PLAN.md` (salvo 117-129, declarado) · **`SEAMS.md` (436)** · **`DEUDA-A.md` (647)**.
*Sigue siendo tramo:* `DEUDA-B.md` (leídos §2 158-219, §3.A 220-319, §4/§5 470-519, §7.2 566-610 de 889) ·
`runtime.py` · los 18 `NN-*.md` fuera de §2.2/§2.5 —**este último recorte lo mandaba el encargo** («Leer ACOTADO»,
`PLAN §1.3`), los otros no—. **El coste de leer por tramo dejó de ser hipotético dos veces:** `DEUDA-B` sólo por
§3.A produjo **CAT-h7** (ítem mal tierado, retractado); y no haber abierto `DEUDA-A` ni `SEAMS` sostenía **V1**,
que resultó contener **cuatro cosas materiales** (CAT-h6 numeración · CAT-h9 dos incoherencias · CAT-h10 K4 rancio ·
la fuga de `ToolUseContext` que la firma de S30/S31 iba a congelar). Ninguna era un formalismo.

**Q2 · ¿Reconcilia el conteo — ítems nombrados = ítems colocados = 0 sin colocar?**

**⚠ La 1ª redacción respondió esta pregunta con el denominador equivocado y por eso la marcó ✅.** Contó
**secciones barridas** (18/18 §2.2) — pero la unidad que se reparte no es la sección, es el **ítem**. Rehecha a
nivel de ítem, enumerando los nombres de battery que las 18 §2.2 proponen:

| | |
|---|---|
| ítems nombrados por las 18 §2.2 | **34** |
| colocados como unidad del catálogo (§2) | **33** |
| colocados como **exclusión razonada** (§5) | **1** — el *bridge de modelo ← `ModelsConfig`* (OR1) de `18·§2.2` |
| **sin colocar** | **0** |

El ítem 34 es el que la ✅ original **no podía ver**: no estaba ni entre las 33 ni entre las 12 exclusiones que §5 tenía.
**No era una battery perdida** — `DEUDA-B §2` fila **2.10** lo tenía colocado como **DB-10** (BORRAR (a) ·
CABLEAR (b)), y `SEAMS §4` ya lo llamaba por su nombre (*«NO `:83` = slot muerto `ModelsConfig`/LAT-MODELS1»*), y
`DEUDA-A §4(b)` lo lista dentro de `B-orphans`. **Tres documentos lo tenían; el catálogo no.** *Efecto sobre el
reparto:* ninguno. *Efecto sobre la reconciliación:* total — **una reconciliación que no puede detectar un ítem
sin colocar no es una reconciliación**, y ésa es exactamente la función que la pregunta cumple. Corregido: §5 gana
su fila, **CAT-h8** registra la regla (*el conteo se hace sobre la unidad que se reparte, nunca sobre el contenedor
que se recorre*). **Ahora sí: 34 = 33 + 1 = 0 sin colocar.**

**Q3 · ¿Cada ✅/🔀 abrió el tramo del ensamblador que lo respalda, sin grep?**
Ensamblador: `factory.py` **1→268 = 1→EOF**. De ahí salen, con línea exacta, el `:146` incondicional (cabo 4), los
`if` condicionales de mcp/skills/memory, el gate de voz `:212-216` y `RuntimeConfig.hook_runner=None` (`:86`) que
sostiene la nota de B17. Los call-sites de voz: `runtime.py:210-269` abierto.
**Dos anclas SÍ estaban puestas sin abrir**, y las abrí en el gate, no antes: `runtime.py:410` (cableado de B09) y
`:430` (snapshot-overwrite de `CG-STOR-2`, B18) venían **heredadas** de 05·§2.2 y `DEUDA-A §1.2(a)`. Abierto
395-436: **`:410` = `await summarize_if_needed(final_text, self._max_chars, self._small_llm)` ✅ · `:430` =
`await self._storage.upload(key, session.model_dump_json()...)` dentro de `_persist`, un único upload por
completion ✅.** Ambas correctas — pero lo fueron por suerte del heredado, no por verificación previa.
**Ningún** ✅ de este documento se apoya en un docstring (RV-5) ni en un grep. **Sí hay un edit** apoyado en grep:
la fila de `PLAN.md §7` se localizó con grep antes de abrir el archivo; `PLAN.md` quedó abierto después.

**Q4 · ¿La cara del integrador está desarrollada al MISMO detalle que la del base?**
Las dos caras están en §1 (perfiles por integrador), §2 (columna "se borra del base" = cara base) y §4.5 (tabla
retira↔sustituye). **Lo que NO está a ese detalle y lo digo primero:** las columnas "se borra del base" de B01-B07 y
B09-B11 dicen **n/a — no existe hoy**, lo cual es cierto pero significa que para esas 10 batteries la cara-base está
*vacía por ausencia*, no *desarrollada*. La única extracción con reparto completo y verificado es **B08 (voz)**, más
las 4 capabilities cuyos campos de config están en el ensamblador (B12/B13/B15/B16).

**Q5 · ¿Doble filo — hay algo acreditado como battery/decisión que en realidad es padding, o alguna divergencia
acreditada como des-fusión correcta que en realidad es mímica?** *(L10 + `mimica-no-desfusion`)*

**Filo A — padding.** El ciclo lo aplicó **en positivo y con coste**: **eliminó** `battery_builtin_agents` (S28 ya
tiene fase `agents()` ⇒ la battery era una envoltura vacía), rehusó inventar paquetes para **13·memory** y
**14·plan** pese a que un catálogo más gordo se lee como más trabajo hecho, y escribió **§5 con 13 exclusiones
razonadas** en vez de absorberlas. **Pero el "33" no es un hecho descubierto, es una decisión**: sale de resolver
el cabo 2 como *4* y el cabo 3 como *2*; con las agrupaciones contrarias serían **29**. El número vale lo que valgan
los criterios de §4.2/§4.3 — que están escritos y son falsables, y ése es el único aval que tiene.

**Filo B — mímica acreditada como des-fusión. Aquí la respuesta es peor y va primero.** **10 de las 33 batteries
(B01-B07, B09-B11) no existen en el runtime**: su "alcance" está destilado del canónico **leído en superficie** por
los ciclos, no de código propio. Catalogarlas es legítimo —el catálogo es de *diseño*— pero **su columna "se borra
del base" dice `n/a — no existe hoy`, y eso no es un reparto verificado: es una casilla vacía por ausencia.** Bajo
la carga de prueba invertida del esfuerzo, **no acredito ninguna de las 10 como des-fusión correcta**. La única
extracción con reparto completo y verificado contra el ensamblador es **B08 (voz)**, y precisamente ahí el gate
encontró que la firma "obvia" (copiar `transcribe(audio, ctx)`) habría **congelado una fuga** en un contrato público
(§4.5). Si en la única que se pudo verificar apareció eso, las otras diez no merecen el beneficio de la duda.

**Q6 · ¿Hay algo que esté colocando como resuelto que en realidad remití a otro ciclo?**
Sí, cuatro, y los llevo al frente: (a) **S28/S29 siguen siendo BORRADOR NO VALIDADO** — este catálogo las usa como
vocabulario y **no** las valida (§7); ~~(b) la costura de entrada de voz queda propuesta, no numerada~~ **(b) ya no:
S30/S31 numeradas en el gate**; (c) **CAT-h1, CAT-h2 y CAT-h10 corrigen documentos ya cerrados** (`05-execution.md`,
`DEUDA-A.md` ×2) y esa corrección se **ejecuta en A-CIERRE**, no aquí — **hasta entonces esos archivos siguen
diciendo cosas que este catálogo contradice, y una de ellas (`EventEnvelope`) es una forma que quien la implemente
tendrá que deshacer**; (d) **la 1ª redacción colocó como resuelto un ítem que estaba mal tierado** (`CAT-DB-1`) —
retractado, **CAT-h7**. Ese es el ejemplo más honesto que este ciclo puede dar de por qué la pregunta existe.

**Q7 · ¿El pendiente que remito justifica por qué NO es decidible con lo que tengo abierto?**
**La 1ª redacción respondió que sí a los 5 de §7, y en uno estaba mintiéndose.** *«La numeración de costuras necesita
`SEAMS.md` abierto»* es verdad — y **abrir `SEAMS.md` era exactamente lo que estaba en mi mano**: 435 líneas. Un
pendiente cuya única condición es *«no lo abrí»* **es decidible por definición**; llamarlo "no decidible" es falsa
economía (L00) con forma de rigor. Abierto en el gate ⇒ S30/S31 numeradas, 3 correcciones aplicadas, y de propina
CAT-h9/h10 y la fuga de `ToolUseContext`. Lo mismo valía para `DEUDA-A` (647 L), también abierto. **Los que quedan
sí justifican el destino:** S28/S29 necesitan **ejercitarse**, no leerse (Fase C); la auditoría RV-6 es
símbolo-a-símbolo sobre código; los perfiles necesitan integradores vivos. **Ninguno de los 5 cabos del encargo se
remitió** — los 5 se decidieron, incluidos los dos (2 y 3) que eran genuinamente "1 vs 2 paquetes".

> **⚠ Nota sobre esta misma sección (CAT-h11).** El encabezado dice **«VERBATIM, no parafraseadas»** y **no lo era**:
> la 1ª redacción conservó Q1, movió la del ensamblador al puesto 2 y **sustituyó dos de las cinco** —«¿reconcilia el
> conteo?» y «¿doble filo?»— por dos preguntas propias («¿remití algo como resuelto?», «¿el pendiente justifica su
> destino?»). Las dos propias son buenas y se conservan (**Q6/Q7**), pero **sustituir preguntas del gate y rotular el
> resultado «verbatim» es el fallo que el gate existe para impedir**: las dos que desaparecieron son justamente las
> dos que habrían destapado **CAT-h8** (reconciliación por secciones) y el filo B de arriba. Restaurado el orden del
> gate: **Q1-Q5 son las tuyas, Q6-Q7 son mías y van marcadas como mías.**

### 8.3 Honestidad primero — lo NO verificado, antes que lo hecho

1. ~~**`SEAMS.md` no abierto.**~~ **Resuelto en el gate** (1→EOF, + `DEUDA-A` 1→EOF). Lo que queda en su lugar, y es
   peor de lo que parecía: **el pendiente contenía 4 cosas materiales**, no un formalismo — CAT-h6 (numeración),
   CAT-h9 (2 incoherencias internas), CAT-h10 (`DEUDA-A` rancio en la forma de K4) y la **fuga de `ToolUseContext`**
   que la firma de S30/S31 iba a congelar en un contrato público. **Lo NO abierto que sigue:** `DEUDA-B.md` (≈4 de 9
   secciones, 889 L) y `runtime.py` fuera de 210-269/395-436.
2. **10 de 33 batteries tienen cara-base vacía por ausencia** (no existen en el runtime). Su "alcance" viene del
   canónico leído en superficie, no de código propio ⇒ **mímica, no des-fusión acreditada**.
3. **B14 tiene alcance parcialmente ⛔** (`mcpSkills.ts` no vendorizado): su descripción es la del gate y el efecto,
   no la del builder real.
4. **B28/B29 no son verificables hoy** (CAT-h5, K7).
5. **El conteo "33" es una decisión, no un hecho descubierto**: depende de resolver el cabo 2 como 4 y el cabo 3 como
   2. Con las agrupaciones contrarias serían 29. El número es tan sólido como los criterios de §4.2/§4.3 — que sí
   están escritos y son falsables.
6. **Los perfiles de §1 no están validados contra ningún integrador vivo**: `agentic_code` está sembrado (🟨) y
   `agentic_assistant` no se abrió en este ciclo. Son la *propuesta* del catálogo, no un hecho observado.

### 8.4 VEREDICTO

**⛔ PENDIENTE — sigue habiendo pendientes, y son de otro tipo que antes.** Regla dura: **Q1 sigue respondiendo
`no`**, así que no hay `✅ NADA PENDIENTE`. Pero los dos pendientes **que podían cambiar el contenido de este
documento están cerrados**, y eso sí es un cambio de estado, no una re-etiqueta.

**Lo que SÍ está cerrado y no se re-abre:** el barrido que *es* el ciclo (18/18 §2.2, con rango en el log); los **5
cabos**, resueltos y ninguno remitido; el catálogo de **33 unidades** + **1 exclusión nueva** con la reconciliación
item-level **34 = 33 + 1 = 0 sin colocar**; la §5 de exclusiones (13); **11 hallazgos** (CAT-h1..h11); **`SEAMS.md`
y `DEUDA-A.md` abiertos 1→EOF**, con **S30/S31 numeradas** y las 3 correcciones de `17·§2.7` aplicadas.

**PENDIENTES (tipo + destino):**

| # | pendiente | tipo | destino |
|---|---|---|---|
| ~~**V1**~~ | ~~`SEAMS.md` nunca abierto~~ → **CERRADO en el gate.** Y con dos correcciones a su propio enunciado: (a) no era «nunca abierto **en toda la Fase A3**» —`DEUDA-A §0.1` prueba que A3.DA lo abrió 1→EOF—, sino *no abierto por este ciclo*; (b) el pendiente **no era formal**: contenía CAT-h6/h9/h10 + la fuga de `ToolUseContext` | — | — |
| ~~**V4**~~ | ~~`DEUDA-A.md` leído sólo 288-349~~ → **CERRADO en el gate** (1→EOF, 647 L). Confirmó CAT-h2 por fuente, verificó que las **2** emisiones de `DEUDA-A §5` a A3.CAT están dischargadas, y produjo **CAT-h10** | — | — |
| **V2** | `00-BLUEPRINT.md` y `00-INTEGRADORES.md` íntegros **pre-compactación** ⇒ evidencia **HEREDADA**; sólo los tramos editados son propios | **verificación** | **A-CIERRE**, que los reescribe enteros de todos modos |
| **V3** | Las **10 §2.5** leídas pre-compactación ⇒ `00-INTEGRADORES §1.7` descansa en líneas de `EVIDENCIA.log`, no en el texto en contexto | **verificación** | **A-CIERRE** al consolidar §1 |
| **V4'** | **`DEUDA-B.md` sigue por tramos** (§2·158-219 · §3.A·220-319 · §4/§5·470-519 · §7.2·566-610, de 889 L). Es el único doc transversal que **ya produjo un error real** por leerse a trozos (CAT-h7) y del que **quedan ~4 secciones sin abrir** | **verificación** | **A-CIERRE**, que lo re-abre para la auditoría RV-6 símbolo-a-símbolo |
| **V5** | `PLAN.md` 117-129 no abierto (bitácora de ciclos cerrados) | **verificación, declarada como decisión** | ninguno — no gobierna nada |
| **V6** | **10 de 33 batteries con cara-base vacía por ausencia** + **S28/S29 sin validar** + 3 perfiles sin integrador vivo | **doble filo / completitud** | **Fase C** (validación real) |
| **V7** | **Los 18 `NN-*.md` sólo por §2.2/§2.5.** Recorte **mandado por el encargo** (`PLAN §1.3`), no descuido — pero `DEUDA-A §0.1` ya declaró la misma limitación y la mitigación que nombró era *«que A3.CAT y A-CIERRE los reabran por categoría»*. **A3.CAT no lo hizo** (no cabía: ≈795 KB) ⇒ la mitigación recae entera en A-CIERRE | **completitud heredada** | **A-CIERRE** |

**Consecuencia práctica, sin adornos:** A-CIERRE **ya puede** tratar `BATTERIES.md` como insumo por su **contenido**
—V1 y V4 eran los únicos que podían cambiarlo, y están cerrados—. Lo que queda (V2/V3/V4'/V5/V7) es **procedencia**,
y **V6 es la limitación de fondo**: el catálogo es un diseño sobre un runtime que en 10 de 33 casos **aún no tiene
nada que extraer**. Ninguna de esas 10 está acreditada como des-fusión correcta.

**Corrección al veredicto anterior, dicha en claro:** la versión previa remitía V1 y V4 a A-CIERRE justificándolo
como "no decidible aquí". Era falso: ambos se cerraban abriendo 1082 líneas de documento, y al abrirlas salieron
**cinco hallazgos** (h6, h8, h9, h10, h11) y **una fuga de identidad a punto de fosilizarse en un contrato público**.
El pendiente que se remite "por prudencia" cuando la única condición es *no lo abrí* no es prudencia.

**Con esto, los 18 ciclos por-categoría + los 3 rollups transversales (A3.DA · A3.DB(+RV) · A3.CAT) de la Fase A3
están COMPLETOS. Siguiente: A-CIERRE.**
