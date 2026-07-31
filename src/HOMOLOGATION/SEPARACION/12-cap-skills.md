# 12 · capabilities/skills — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/12-cap-skills.md`.
> Tracker de origen: `../12-cap-skills.md` (611 LOC, leído ÍNTEGRO 1→EOF este ciclo). Esquema: `00-LEGEND.md §3`.
> PASO 0 (11 lecciones skill) ejecutado. B (8 `skills/*.py`) + ENSAMBLADOR (`factory.py`/`manager.py`/`agent_loop.py`)
> RE-ABIERTOS 1→EOF EN ESTE CICLO (L09/L11, **NO** heredados de la re-visita gate-11 del tracker 2026-07-20).

---

## 0. Tesis de separación (Filosofía B)

El tracker ya diagnostica la forma B correcta y es idéntica en ESQUELETO a la de 13·memory / 11·mcp: una skill **no
es una capability nueva de plumbing** — es **un `Command` de tipo `prompt`** (misma abstracción que /commands, bundled,
plugin, MCP) que se **activa** en el contexto del turno. La tool `Skill` no "ejecuta": expande el `SKILL.md` en un
prompt (con substitución de `$args`/`${CLAUDE_SKILL_DIR}`/`${CLAUDE_SESSION_ID}` + bash-injection `!\`…\``) y lo entrega
como `newMessages` transitorios + un `contextModifier` que aplica allowed-tools/model/effort; el catálogo llega al
modelo como **system-reminder incremental por-agente** con budget. La SEPARACION descompone eso en tres capas:

1. **Base = el MECANISMO de activación + los contratos + los seams.** El `CapabilityProvider` (seam por el que las
   skills enchufan, home 12/general — COMPARTIDO con memoria/mcp/plan, no skill-específico) + su agregación per-turno
   en el `CapabilityManager` (`tools`/`active_context`, manager:50-59/98-102) + su consumo en el loop
   (`_build_tool_pool` loop:194-196 DENTRO del `for _turn`, `_inject_recall` loop:218, `context_modifier` aplicado
   loop:332-337) = **T2-BASE-MECANISMO**. `SkillDefinition`/`SkillFrontmatter` = **T1-CONTRATO**. `SkillStore` =
   **T2-COSTURA, repo PROPIO** (§0.1). La tool `Skill` usa el `ToolProtocol` (T1, home 01/09).
   **Asimetría con 13·memory (nota del SIGUIENTE, verificada este ciclo):** a diferencia de `MemoryProvider`
   (`tools()==[]`, `catalog()==[]`), `SkillsProvider` SÍ rinde **una tool viva** (`tools()`→`[SkillTool]` sii ≥1
   enabled, provider:144-151) reensamblada per-turno, y `catalog()` NO vacío (provider:131-142). El modelo activa
   skills LLAMANDO la tool; la activación (S3) sobrevive por `active_context`. Es el mismo mecanismo base que memoria
   **más** una tool en el pool.
2. **La skill concreta (loader/frontmatter/render/listing/fork/permisos/dinámicas/hooks/ranking/bundled/mcp) =
   BATTERY `battery_skills` opcional** que se compone sobre el `CapabilityProvider` seam. Reificar el comportamiento
   como battery (no como maquinaria embebida del base) es el mismo criterio de 06 (`battery_hooks_config`),
   15 (`battery_persistence.*`) y 13 (`battery_memory`). **Anti-padding L10:** un integrador puede NO querer skills, o
   sustituir su implementación. Que la battery esté **a medio construir** (una sola fuente, frontmatter de 6 campos,
   sin substitución/bash, sin gate de permisos, sin listing incremental, sin fork-en-tool, sin condicionales/dinámicas/
   hooks/ranking/bundled/mcp) = **CORE-GAPs que la battery estándar DEBE cerrar** para reproducir la capacidad del
   canónico (distinto de un shape opcional que nadie reclama; aquí el canónico SÍ tiene la capacidad).
3. **Las raíces/store, el gate enable, las reglas de permiso, el surface del listing, MCP-skills, el hot-reload y la
   interfaz `/skills` = integrador.** Quién siembra `caps.skill_dirs`/`skill_store`, el `is_enabled` (feature flags),
   las deny/allow-rules + auto-mode, la inyección del skill_listing como system-reminder por turno, el bridge MCP→skill,
   el watcher FS + ConfigChange, y el diálogo `/skills` = `00-INTEGRADORES.md`.

**La promesa está a MEDIO CUMPLIR (verificado por cableado ESTE ciclo, no heredado):** el registro condicional del
provider funciona (`factory.py:160-164`, verificado 1→EOF), la tool `Skill` se reensambla per-turno
(`agent_loop.py:194-196` DENTRO del `for _turn in range(_MAX_TURNS):185`, hermano EXACTO de MCP/memoria) y el
`context_modifier` (allowed-tools→allow + mark_discovered) se APLICA en el loop (`agent_loop.py:332-337`, no sólo
atributo) + `active_skills`→`active_context` se re-inyecta per-turno (`_inject_recall` loop:218). Pero la **battery
está incompleta**: los 13 CORE-GAPs de §2.3.

### 0.1 DESAMBIGUACIÓN load-bearing — el store de skills es un REPO PROPIO, NO auto-cableado (cierra cabo 15·B8)

Verificado por el ensamblador ESTE ciclo (`factory.py:160-164` 1→EOF): `SkillsProvider(skill_store=caps.skill_store)`
recibe el store **inyectado por el integrador** (`caps.skill_store`, default **None**) — el factory **NO auto-construye**
un `StorageBackedSkillStore` ni le pasa el `storage` blob (**contraste con MCP** `factory:152` `McpProvider(storage=)`
que SÍ auto-cablea el TokenStorage). ⇒ **en el standalone las skills vienen SÓLO de `caps.skill_dirs`** (`load_dir(root)`
factory:162-163); sin store, no hay persistencia de skills. Esto **confirma exactamente el cabo 15·B8**
(`battery_session_catalog` / skills store `prefix="skills"` sin scope, "factory sin auto-cablear") — el store es un
**seam de integrador OPCIONAL**, no una ruta viva del base. El `StorageBackedSkillStore` default (`store.py:28-68`) es
hermano del de MCP/memoria: usable, inyectable — pero su clave `<prefix="skills">/<name>/SKILL.md` **sin scope de
usuario/sesión y con `name` sin sanitizar** (§0.2) hereda el mismo bug de familia (15·CG-STOR-1 + 13·CG-MEM-1). Como
NO está auto-cableado, el bug sólo aflora cuando el integrador lo inyecta ⇒ obligación del integrador (OI-SKILL-A) +
helper guard-path unificado.

### 0.2 Eje transversal `persistencia` — id opaco + repo, dos touchpoints (scope + guard-path)

Dos superficies tocan scope/persistencia, ambas del `StorageBackedSkillStore` (sólo vivas si el integrador lo inyecta):
- **Scope ausente:** `_key(name) = f"{prefix}/{name}/SKILL.md"` con `prefix="skills"` fijo (store.py:35-40), **sin
  componente de `user_id`/`session`** → dos usuarios colisionarían bajo la MISMA clave `skills/<name>/SKILL.md`
  (mismo modo de fallo que 15·CG-STOR-1 `mcp/mcp/<srv>` y el `user_id="mcp"` de token_storage). Patrón obligado
  **id opaco + repo genérico**: el runtime NO interpreta identidad; el integrador scopea la clave. → **15·CG-STOR-1**.
- **Guard-path ausente:** `name` se une crudo a la clave (`f"{prefix}/{name}{SUFFIX}"`) **sin sanitizar** — un `name`
  con `..`/ruta escaparía del prefijo (mismo traversal que 13·MEM9 `<user>/<agent>` crudo). → helper **UNIFICADO con
  15·CG-STOR-3 / 13·CG-MEM-1** (`sanitizePathKey`, mismo guard, no duplicado).

Además la **battery** persiste `skill_usage` (ranking CG-SKILL-11, `getSkillUsageScore` half-life 7d) sobre
`StorageProtocol` — mismo eje `persistencia`, patrón id-opaco+repo. Los tres se consolidan en el rollup `DEUDA-A.md`
(nota-identidad `persistencia`), no categoría-a-categoría.

---

## 1. Tabla por finding

> **Unidad de conteo (declarada):** el tracker `../12-cap-skills.md` organiza tablas de features A-I **sin ID por
> celda**; su §Recuento fija el unit vinculante: **"20 findings … Lo vinculante son los IDs FIND-SKILL/GAP-SKILL y los
> cabos"** = **FIND-SKILL1..19 (19) + FIND-MCP16 (1) = 20**. `GAP-SKILL1`=FIND-SKILL5, `GAP-SKILL3`=FIND-SKILL12
> (alias, no separados); `GAP-SKILL2` = coherencia `is_deferred` **resuelta de diseño** (SkillTool no-diferida; se
> coloca como nota, no gap). Los `SkR1-17` = §Plan desarrollado (6 campos L05) en el tracker — se **referencian** para
> la cara-base y se desarrolla la cara-integrador simétrica (§2.5), **no se re-cuentan** (patrón 06/10/04/15/13). Para
> que "sin colocar = 0" se sostenga bajo la lectura más estricta, además de los 20 FIND-* se colocan las **capacidades
> homologadas** (`SK-OK-*`, ✅/🟡/🔀 sin ID en el tracker) y los **⛔/interfaz** (`SK-NA-*`).

### A · CORE-GAPs (findings ❌/🟡 que `battery_skills`+base DEBEN cerrar) — mapeados a CG-SKILL-*
| ID tracker | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| FIND-SKILL2 | `when_to_use`≠desc + `argument-hint`/`arguments`/`hooks`/`context`/`agent`/`effort`/`shell`/`paths` (frontmatter de 6 vs 16) | núcleo | **CORE-GAP** (T1 + BATTERY) | **CG-SKILL-1** (`SkillFrontmatter`+`SkillDefinition`) | — | ❌ `frontmatter.py:27-32` = **exactamente 6 campos** (verificado 1→EOF). Base=SkR1 |
| FIND-SKILL3 | Dos ejes ORTOGONALES `user-invocable` (typeable) ≠ `disable-model-invocation` (invocable por modelo) | núcleo | **CORE-GAP** (T1) | **CG-SKILL-1** (`is_hidden`+2 ejes) | — | ❌ un solo `enabled` los conflaciona (`loader.py:35`, `default_is_enabled:46`). Base=SkR1 |
| FIND-SKILL4 | Substitución `$ARGUMENTS`/`$N`/`$NAME` + `${CLAUDE_SKILL_DIR}`/`${CLAUDE_SESSION_ID}` + bash-injection `!\`…\`` (gate anti-MCP) | núcleo/seguridad | **CORE-GAP** | **CG-SKILL-2** (`substitution.py`+shell-exec inyectado) | — | ❌ **grep-ausencia 0** este ciclo; `render_skill` ignora args (skill_tool.py:18). Base=SkR3 |
| FIND-SKILL19 | El prompt lo produce un **callable async ctx-aware** (`getPromptForCommand(args,ctx)`), no markdown estático | núcleo | **CORE-GAP** | **CG-SKILL-2** (`prompt_provider: Callable`) | — | ❌ `render_skill` estático (skill_tool.py:18-35). Base=SkR3 |
| FIND-SKILL5 (=GAP-SKILL1) | Gate de permisos: deny/allow-rules `:*`-prefix + auto-allow-safe-properties + ask+suggestions | núcleo/seguridad | **CORE-GAP** + T2-COSTURA | **CG-SKILL-3** → 06·GAP-02 + 09·dispatcher | — | ❌ `requires_permission=False` (skill_tool.py:92, único hit). Base=SkR4 |
| FIND-SKILL9 | `skill_listing` incremental por-agente (delta `sentSkillNames`) + budget (1%/250char/bundled-sin-truncar) + skip-si-no-tool + reset/suppress | núcleo | **CORE-GAP** | **CG-SKILL-4** (`listing.py`+`provider.skill_listing`) | — | ❌ **el standalone NO surface NINGÚN listing al modelo** (§3.3 Q3; gap MAYOR, no "re-emite todo"). Base=SkR7 |
| FIND-SKILL17 | Elegibilidad `getSkillToolCommands` (excluye sin-descripción-explícita + `disableModelInvocation`/builtin) | núcleo | **CORE-GAP** | **CG-SKILL-4** | — | 🟡 `catalog` lista toda `is_enabled` + `when_to_use=description` (provider.py:137-142). Base=SkR7 |
| FIND-SKILL8 | Entrega vía `newMessages` transitorios + tool_result mínimo ("Launching skill: X") | núcleo | **CORE-GAP** | **CG-SKILL-5** (`ToolResult.new_messages`=B-new_messages) | — | 🔀 mete el render completo como `output` (skill_tool.py:118→loop:319-323). Base=SkR6 |
| FIND-SKILL18 | Prompt de la tool BLOCKING/never-mention/already-loaded/not-builtin | núcleo | **CORE-GAP** | **CG-SKILL-5** (description larga) | — | 🟡 description one-liner (skill_tool.py:79-82). Base=SkR6 |
| FIND-SKILL7 | `context_modifier` model-override (carry `[1m]`) + effort-override | núcleo | **CORE-GAP** | **CG-SKILL-6** (`resolve_skill_model_override`) | — | ❌ `skill.model` ALMACENADO (skill_tool.py:56) pero ningún prod lo aplica (§2.4). Base=SkR5 |
| FIND-SKILL1 | Fuentes múltiples con precedencia (managed/user/project-up-to-home/additional/legacy/plugin/bundled/mcp) + dedup realpath | núcleo | **CORE-GAP** | **CG-SKILL-7** (`load_skills_sources`+`_dedup_by_realpath`) | persistencia | ❌ una sola fuente `load_dir` (loader.py:97-114); **grep-ausencia realpath=0**. Base=SkR2 |
| FIND-SKILL6 | La tool `Skill` despacha a **fork** si `context==='fork'` (`runAgent`) | núcleo | **CORE-GAP** | **CG-SKILL-8** → 05·SubagentRunnerProtocol | — | ❌ `execute` inline sin rama fork (skill_tool.py:107-120). Base=SkR9 |
| FIND-SKILL11 | Skill hooks (frontmatter `hooks`→session hooks, `once:true`, `CLAUDE_PLUGIN_ROOT`) | núcleo | **CORE-GAP** | **CG-SKILL-9** → 06·HookSink | — | ❌ hooks no se parsean (frontmatter.py, grep-ausencia 0). Base=SkR11 |
| FIND-SKILL12 (=GAP-SKILL3) | Skills condicionales (`paths`) + descubrimiento dinámico (walk-up desde archivos tocados, gitignore, deepest-wins) | núcleo | **CORE-GAP** | **CG-SKILL-10** (`dynamic.py`) + evento file-op 10/07 | — | ❌ grep-ausencia (conditional/discover=0). Base=SkR12 |
| FIND-SKILL14 | Ranking de uso (`recordSkillUsage` debounce 60s → `getSkillUsageScore` half-life 7d, piso 0.1) | núcleo | **CORE-GAP** | **CG-SKILL-11** (`usage.py` sobre StorageProtocol) | persistencia | ❌ grep-ausencia 0. **Cabo de 13 aterriza AQUÍ** (§2.6). Base=SkR14 |
| FIND-SKILL15 | Bundled programáticos (`registerBundledSkill`) + extracción `files` con guardas (O_NOFOLLOW/EXCL/0o600/anti-traversal) | núcleo | **CORE-GAP** (mecanismo) | **CG-SKILL-12** (`bundled.py`) | — | ❌ grep-ausencia 0; contenido de los 15 = ⛔ (SK-NA-3). Base=SkR13 |
| FIND-SKILL16 | Resolución: aliases + namespaced (`ns:cmd`) + strip-leading-slash | núcleo | **CORE-GAP** | **CG-SKILL-13** (`find_skill` extendido) | — | ❌ `state.get` exacto (state.py:24). Base=SkR10 |
| FIND-SKILL10 | invoked_skills: `skillPath` + cleanup selectivo por agent (`clearInvokedSkills(preserved)`) | núcleo | ✅🔀 concepto + **CORE-GAP-menor** | **CG-SKILL-14** → 05·ExR6/08·SR3 | — | ✅🔀 `active_skills` homologa el concepto (skill_tool.py:53-58); falta `path`/`invoked_at`+cleanup selectivo. Base=SkR8 |
| FIND-SKILL13 | Hot-reload FS (`skillChangeDetector` + ConfigChange hook + `skillsChanged` signal) | núcleo | 🔀 + BATTERY + T3 | `provider.refresh()` (SkR16) + OI-SKILL-H | — | 🔀 el long-running refresca por API (register/unregister vivos); watcher FS=CLI-forma. Falta `refresh()`+ConfigChange (06) |
| FIND-MCP16 | MCP prompts (`mcp__srv__prompt`, isMcp, diferidos) + MCP skills (`srv:skill`, `loadedFrom='mcp'`, invocables por SkillTool, resources-backed) | núcleo | BATTERY (bridge) + T3 | **CG-SKILL-15**/`merge_mcp_skills` → 11 + OI-SKILL-G | — | ❌ grep-ausencia `loaded_from`=0; builder `mcpSkills.ts` **no vendorizado** (⛔ no-leíble). Base=SkR15 |

### B · Capacidades homologadas (✅/🟡/🔀 sin ID en el tracker — colocadas para "sin colocar=0")
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| SK-OK-1 | Formato `skill-name/SKILL.md` (glob dir) | núcleo | BATTERY | `load_skills_dir` | — | ✅ `loader.py:97-114` (glob `*/SKILL.md`) |
| SK-OK-2 | Aislamiento por-ítem (SKILL.md roto no tumba) + orden estable | núcleo | BATTERY | `load_skills_dir` try/except + `sorted` | — | ✅ `loader.py:106-113` |
| SK-OK-3 | Frontmatter tolerante (`extra="allow"`, coerción por campo, nunca lanza) | núcleo | BATTERY | `SkillFrontmatter` | — | ✅ `frontmatter.py:25/34-77` (paridad de robustez ante terceros) |
| SK-OK-4 | `base_dir`/`skillRoot` (localizar archivos bundled) | núcleo | BATTERY | `SkillDefinition.base_dir` | — | ✅ `loader.py:29-32/94` |
| SK-OK-5 | `allowed-tools`→allow + mark_discovered (context_modifier APLICADO en el loop) | núcleo | T2-BASE-MECANISMO | `build_skill_context_modifier` (skill_tool.py:47-64) | — | ✅ APLICADO `agent_loop.py:332-337` (+mejora: anuncia MCP diferidas, mark_tools_discovered:63) |
| SK-OK-6 | `active_skills`→`active_context` per-turno (concepto invoked_skills, S3) | núcleo | T2-BASE-MECANISMO | `_inject_recall` (loop:218) · `provider.active_context` | — | ✅🔀 provider.py:153-171 → `_inject_recall` (=FIND-SKILL10 concepto) |
| SK-OK-7 | Slash-command desacoplado del loop (activa inline, devuelve instrucciones) | núcleo | T2-COSTURA (integrador) | `process_slash_command` (commands.py:32-64) | — | ✅ el loop NO lo importa (provider.py:80-85); seam S4 del integrador |
| SK-OK-8 | Store inyectable + `startup()` rehidrata (habilita MinIO/sesiones) | núcleo | T2-COSTURA (repo propio) | `SkillStore` · `StorageBackedSkillStore` | persistencia | ✅🔀 `store.py` + `provider.startup:110-126`; **no auto-cableado** (§0.1, cabo 15·B8) |
| SK-OK-9 | `unregister`/`remove` en vivo (server long-running) | núcleo | BATTERY | `provider.unregister` (95-106) | — | ✅ mejora sobre canónico (`state.remove` state.py:27) |
| SK-OK-10 | Tool `Skill` NO diferida (el modelo la necesita para activar) — GAP-SKILL2 resuelto | núcleo | T2-BASE + coherencia 09 | `SkillTool` en pool per-turno | — | ✅ `provider.tools:144-151` (coherente con 09·TiR5; MCP-prompts SÍ diferidas) |
| SK-OK-11 | `version` passthrough (trazabilidad, runtime no interpreta) | núcleo | T1-CONTRATO | `SkillDefinition.version` | — | ✅ `loader.py:36-38` |
| SK-OK-12 | `SkillsProvider` con `tools()`/`catalog()` no-vacíos + name/desc derivation | núcleo | T2-BASE-MECANISMO | `provider.tools`/`catalog` · `load_skill_text` | — | ✅ provider:131-151 / loader:49-81 (**precisión**: `catalog()` NO cableado al modelo, §2.4) |

### C · ⛔ / capa de interfaz (colocadas con destino, no descartadas — L07/L02)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| SK-NA-1 | `tools/SkillTool/UI.tsx` (render ink use/result/progress) | cáscara-CLI | CLI-ONLY/INTERFAZ | `00-INTEGRADORES` (OI-SKILL-E) | — | ⛔ abierto y confirmado (tracker); render → integrador |
| SK-NA-2 | `/skills` slash + `SkillsMenu.tsx` + `useSkillsChange` (diálogo + refresco React) | cáscara-CLI | CLI-ONLY/INTERFAZ | `00-INTEGRADORES` (OI-SKILL-E) | — | ⛔ abiertos y confirmados; afordancia de interfaz → integrador |
| SK-NA-3 | Los 15 `bundled/*.ts` **como contenido** (simplify/verify/loop/remember/…) | producto | ⛔ (contenido) | ⛔ producto (el mecanismo=CG-SKILL-12) | — | ⛔ N/A core (abiertos 1→EOF tras reproche; el que integra registra los suyos, OI-SKILL-F) |
| SK-NA-4 | `skillImprovement.ts` (auto-mejora por LLM, gated `SKILL_IMPROVEMENT`) | producto | ⛔ | ⛔ producto | — | ⛔ N/A core (gated) |
| SK-NA-5 | `EXPERIMENTAL_SKILL_SEARCH` / remote-skill (búsqueda semántica remota ant-only) | producto | ⛔ | ⛔ experimental | — | ⛔ N/A core; **nexo cabo 13·B9 searching-past-context** = skill-search ⛔ (no aterriza como CORE-GAP) |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`CapabilityProvider`** (T2-COSTURA, home 12/general, **NO nuevo de 12**) — el seam por el que las skills enchufan.
  Consumido per-turno por el manager (`tools:50-59`/`active_context:98-102`) + el loop (`_build_tool_pool:194-196`/
  `_inject_recall:218`). Verificado 1→EOF este ciclo. **SkillsProvider es su realización más rica** (única con
  `tools()` no vacío entre skills/memory/plan → tool `Skill` viva).
- **`SkillStore`** (T2-COSTURA, home 12, **repo PROPIO**) — dónde se registra/persiste el `SKILL.md`. Productor:
  `SkillsProvider` (`register_skill`/`startup`). Consumidor: `StorageBackedSkillStore` (default) o backend inyectado.
  **No auto-cableado** por el factory (§0.1, cabo 15·B8) — seam del integrador; su clave sin scope/sanitize → §0.2.
- **`SkillDefinition`/`SkillFrontmatter`** (T1-CONTRATO) — shape tipado de la skill; hoy 6 campos, crece a 16 (CG-SKILL-1).
- **`prompt_provider` + shell-exec inyectado** (seam de `battery_skills`) — el callable ctx-aware (FIND-SKILL19) +
  el ejecutor de bash-injection (reusa el de 10·Bash / `ToolExecEnvironment`). CG-SKILL-2. Gate anti-MCP = `if`.
- **`PermissionGate` para SkillTool** (T2-COSTURA) — la tool entra al gate por-input como cualquier tool nativa
  (09·dispatcher). → **06·GAP-02** (semántica de reglas) + `SAFE_SKILL_PROPERTIES`. CG-SKILL-3.
- **`SubagentRunnerProtocol`** (T2-COSTURA, home 05, S18) — la tool despacha fork si `context=='fork'`. CG-SKILL-8.
- **`ToolResult.new_messages`** (T1-CONTRATO extensión = DEUDA-B `B-new_messages` transversal) — entrega transitoria.
  CG-SKILL-5. Cabo → 07·EVT/loop.
- **`HookSinkProtocol`** (T2-COSTURA, home 06) — skill hooks → session hooks. CG-SKILL-9.
- **evento file-op post-Read/Write/Edit** (seam base, home 10·native + 07·events) — dispara condicionales/dinámicas.
  CG-SKILL-10. Cabo → 10/07.
- **`skill_listing(ctx)`** (seam de `battery_skills`, consumido por el integrador) — listing incremental+budget
  por-agente; el integrador lo surface como system-reminder por turno (OI-SKILL-D). CG-SKILL-4. Distinto de
  `catalog()` (introspección, §2.4).

### 2.2 Batteries que alimenta
- **`battery_skills`** — el comportamiento concreto, componible por AMBOS integradores (catálogo → A3.CAT):
  loader multi-fuente+precedencia+dedup (CG-SKILL-7) + frontmatter de 16 campos + 2 ejes (CG-SKILL-1) +
  `render_skill`/`prompt_provider`+substitución+bash (CG-SKILL-2) + gate de permisos (CG-SKILL-3) + `skill_listing`
  incremental+budget+elegibilidad (CG-SKILL-4) + entrega new_messages+prompt (CG-SKILL-5) + model/effort override
  (CG-SKILL-6) + fork-dispatch (CG-SKILL-8) + skill-hooks (CG-SKILL-9) + condicionales/dinámicas (CG-SKILL-10) +
  ranking de uso (CG-SKILL-11) + bundled programáticos (CG-SKILL-12) + resolución aliases/namespaced (CG-SKILL-13) +
  invoked cleanup+path (CG-SKILL-14) + refresh/hot-reload (SkR16). Su incompletitud = los CORE-GAPs §2.3, NO decenas
  de gaps del base (L10: la battery es el paquete a completar, el mecanismo base ya está).
- **`battery_mcp_skills` (sub-battery / bridge)** — MCP prompts→slash + MCP skills→SkillTool (CG-SKILL-15/FIND-MCP16),
  gated `MCP_SKILLS && supportsResources`; el builder real `mcpSkills.ts` no vendorizado. Compone 11↔12.
- **bundled de producto NO es battery base** — el mecanismo `registerBundledSkill` (CG-SKILL-12) SÍ; los 15 skills
  de Claude Code = contenido de producto (⛔ SK-NA-3); cada integrador registra los suyos (OI-SKILL-F).

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
Keystone-first; los 6 campos L05 ya desarrollados en el tracker (SkR1-17); aquí se anclan con su ID de rollup:
- **CG-SKILL-1** (FIND-SKILL2/3, **keystone**) — **frontmatter completo (16 campos) + dos ejes ortogonales**
  (`user_invocable` typeable ≠ `disable_model_invocation` invocable-por-modelo; `is_hidden`) + `when_to_use`≠desc.
  Base para CG-3/4/5/6/8/9. Base = SkR1.
- **CG-SKILL-2** (FIND-SKILL4/19, **keystone funcional+seguridad**) — **prompt-provider callable ctx-aware** +
  substitución `$ARGUMENTS`/`$N`/`$NAME`/`${CLAUDE_SKILL_DIR}`/`${CLAUDE_SESSION_ID}` + **bash-injection** `!\`…\`` con
  `allowed_tools` como allow-rules efímeras **y gate `if loaded_from != 'mcp'`** (seguridad). LAT-SKILL1 es su cara
  B-interna (§2.4). Base = SkR3.
- **CG-SKILL-3** (FIND-SKILL5=GAP-SKILL1, **seguridad**) — **gate de permisos de SkillTool**: deny/allow-rules
  (exact + `:*`-prefix), auto-allow sólo si `_skill_has_only_safe_properties` (`SAFE_SKILL_PROPERTIES`), si no `ask`
  con suggestions + metadata `{command}`. `requires_permission=True`. → **06·GAP-02** (semántica) + 09·dispatcher
  (ya consulta el gate por-input). Base = SkR4.
- **CG-SKILL-4** (FIND-SKILL9/17) — **`skill_listing` incremental por-agente + budget + elegibilidad**: delta
  `sent_skill_names` por `agent_id`, budget 1%/250char/bundled-sin-truncar/fallback names-only, skip-si-no-tool-Skill,
  filtro elegibilidad (`not disable_model_invocation && auto-descrita|when_to_use`), `reset_sent_skill_names`.
  **El standalone NO surface listing** (§2.4/§3.3) → gap MAYOR. Base = SkR7. Reemplaza el uso de `catalog()` como
  entrega (catalog queda introspección/UI).
- **CG-SKILL-5** (FIND-SKILL8/18) — **entrega vía `new_messages` transitorios** (SKILL.md expandido, tagged
  tool_use_id) + tool_result mínimo + **prompt de la tool** BLOCKING/never-mention/already-loaded/not-builtin.
  Depende de `B-new_messages` (DEUDA-B transversal / 07·EVT). Base = SkR6.
- **CG-SKILL-6** (FIND-SKILL7) — **model + effort override** en el `context_modifier` (resolver alias, carry `[1m]`).
  Base = SkR5.
- **CG-SKILL-7** (FIND-SKILL1) — **fuentes múltiples + precedencia + dedup por realpath**. El integrador provee las
  raíces (nota-identidad); setting-source/plugin-only gating = integrador. Base = SkR2.
- **CG-SKILL-8** (FIND-SKILL6) — **fork-dispatch en la tool** (`context=='fork'` → `SubagentRunnerProtocol` de 05,
  merge effort/model/agent, output `{status:'forked'}`, cleanup en `finally`). Base = SkR9. Cross 05.
- **CG-SKILL-9** (FIND-SKILL11) — **skill hooks** (frontmatter `hooks`→session hooks, `once:true` auto-remove,
  `CLAUDE_PLUGIN_ROOT`=base_dir) vía HookSink de 06. Base = SkR11. Cross 06.
- **CG-SKILL-10** (FIND-SKILL12=GAP-SKILL3) — **skills condicionales (`paths`) + descubrimiento dinámico** (walk-up
  desde archivos tocados hasta cwd, gitignore, deepest-wins). **Necesita el evento file-op** (10·native+07). Base = SkR12.
- **CG-SKILL-11** (FIND-SKILL14) — **ranking de uso** (`record_skill_usage` debounce + `skill_usage_score` half-life
  7d, piso 0.1) sobre `StorageProtocol` (mismo patrón que 13·memory pero persiste `skill_usage`; nota-identidad
  `persistencia`). **Cabo de 13 aterriza AQUÍ** (§2.6). Base = SkR14.
- **CG-SKILL-12** (FIND-SKILL15) — **bundled programáticos** (`register_bundled_skill(defn)` con `is_enabled` callable/
  `files`/`context`/`agent`) + extracción de `files` con guardas (O_NOFOLLOW/EXCL/0o600/anti-traversal). Base = SkR13.
- **CG-SKILL-13** (FIND-SKILL16) — **resolución extendida** (aliases + namespaced `ns:cmd` + strip-leading-slash).
  Base = SkR10.
- **CG-SKILL-14** (FIND-SKILL10, menor) — **invoked_skills con `path`/`invoked_at` + cleanup selectivo por agent**
  (`clear_invoked_skills(preserved)` al cerrar fork/compactación). Concepto YA homologado (✅🔀 SK-OK-6); falta el
  matiz. → 05·ExR6/08·SR3. Base = SkR8.
- **CG-SKILL-15** (FIND-MCP16) — **bridge MCP-skills/prompts** (`loaded_from='mcp'`, `merge_mcp_skills`, gate
  `MCP_SKILLS && supportsResources`, anti-bash). Base = SkR15. Cross 11; builder `mcpSkills.ts` no-leíble (⛔).

*(FIND-SKILL13 hot-reload = 🔀 + `provider.refresh()` menor (SkR16) + OI-SKILL-H; no CORE-GAP duro — el comportamiento
observable "catálogo fresco tras cambio" ya lo cubre la API register/unregister viva; falta el ConfigChange hook (06).)*

### 2.4 DEUDA-B (higiene interna — L10, NO A↔B)
- **LAT-CAP1** (**NUEVA — destapada al abrir `capabilities/contracts.py` 1→EOF tras el gate auto-adversarial;
  home 12/general**) — `CapabilityActivation` (contracts.py:26-38: `tools_to_enable`/`messages_to_append`/
  `permission_rules`/`active_state`/`refresh_tool_pool`) es un **contrato de activación estructurada definido y
  exportado pero SIN productor NI consumidor de prod** (verificado grep este ciclo: sólo `contracts.py:26` + re-export
  `capabilities/__init__.py:1/8`; ningún provider lo retorna, nadie lo lee). `SkillsProvider` **lo bypasea**: activa
  vía el dict ad-hoc `active_skills` (skill_tool.py:53-58) + el atributo `context_modifier` (skill_tool.py:119) +
  (ausente) `new_messages`. Es la cara B-interna de que **los targets de varios CORE-GAPs son exactamente sus campos**
  — `messages_to_append`≈CG-SKILL-5 (new_messages), `permission_rules`≈CG-SKILL-3, `tools_to_enable`≈context_modifier
  ya vivo, `refresh_tool_pool`≈FIND-SKILL13 hot-reload. **Seam a medio cablear**, hermano de LAT-SKILL1/LAT-HOOK1;
  **decisión CABLEAR-vs-BORRAR diferida a A3.DB** (¿la remediación converge a `CapabilityActivation` como shape de
  retorno de `activate()`, o la supersede el `ToolResult.new_messages` de CG-SKILL-5 y se borra?). NO es deuda A↔B
  (el canónico no tiene este contrato) → `DEUDA-B.md §B-orphans` (home 12/general, no skills-específico). Nota:
  `CapabilitySummary.deferred` (contracts.py:23) SÍ existe pero skills lo deja default `False` (provider.py:133-139
  no lo setea) — coherente (MCP-prompts lo pondrían True, =FIND-MCP16), NO latente.
- **LAT-SKILL1** (**seam a medio cablear → CABLEAR, no borrar**) — `SkillTool.input_schema` anuncia la
  propiedad `args` (skill_tool.py:83-89) que `execute()` **descarta** (`input.get("command")` :108; `render_skill` sin
  args :18). Costura a medio cablear: la tool promete en su PROPIO schema un manejo de args que no entrega. Es la
  superficie B-interna de **FIND-SKILL4** (cuyo gap A↔B — sin substitución/vars/bash — **se sostiene ❌**); lo latente
  es la **inconsistencia interna** (announce vs execute), gemela del announce singular de 09·FIND-TOOL6. **Se CABLEA
  vía CG-SKILL-2/SkR3** (que introduce `render_skill(skill, args, ctx)`), NO se borra — hermana de LAT-HOOK1
  (06, "cablear vía HR5"), distinta de los huérfanos duplicados-muertos (SignalBus/observer/modes/NativeToolRegistry).
  → `DEUDA-B.md §B-orphans` (seams a medio cablear).
- **`compact_context` sin consumidor prod** (provider.py:173-179, manager.py:104-108) — **NO es B-orphan nuevo**: es
  la cara aguas-abajo del **motor de compactación NO portado** (01·CompactionProvider / 02·GAP-L4), transversal a
  TODOS los providers (plan/skills/mcp/memory). La equivalencia post-compactación la da el re-inject per-turno de
  `active_context` (loop:218). **Idéntico a 13·D8** (precisión heredada, re-confirmada este ciclo por grep:
  `compact_context` prod-consumer = sólo el agregador `manager.py:104`, cero caller de loop/runtime) → **no se
  re-cuenta ni se registra como B-orphan** (L10).
- **`catalog()` sin consumidor prod** (provider.py:131-142, manager.py:44-48) — **NO es B-orphan**: es un **seam de
  introspección del integrador** (hermano de `stream()`/`subscribe_all` 07, `HookRunner.register` 06). Verificado este
  ciclo: `grep '\.catalog('` = SÓLO `manager.py:47` (el agregador interno); ningún caller de loop/runtime; `grep
  catalog|skill_listing` en `agent_loop.py` = **0**. La ausencia de listing al modelo es la deuda A↔B FIND-SKILL9/
  CG-SKILL-4, no una costura B-interna. (La misma naturaleza que 13, donde `MemoryProvider.catalog()==[]`.)
- **`category = ToolCategory.SYSTEM`** (skill_tool.py:91) = LAT-TOOL1 (ya homed 09/10, slot muerto compartido, NO
  nuevo). `timeout_seconds=10.0` (skill_tool.py:94) **SÍ consumido** por el dispatcher (`wait_for`, =11·FIND-MCP8) →
  no latente. Cero costuras latentes NUEVAS tipo `to_llm`/LAT-* propias de 12 salvo LAT-SKILL1.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05/§1.1)

**Must-be universal (CONTRATO BASE COMÚN — obligación de TODO integrador con skills):**
- **OI-SKILL-A · Proveer las raíces/store de skills.** Capacidad: dónde viven las skills (dev=FS dirs, prod=store
  MinIO). Costura: `RuntimeConfig.capabilities.{skill_dirs, skill_store}` → registro condicional `factory:160-164`.
  Firma: `list[Path]` (`load_dir` por raíz) o un `SkillStore` inyectado (default `StorageBackedSkillStore`, **el
  factory NO lo auto-cablea** — el integrador lo inyecta y **lo scopea** por `user_id`, §0.1/§0.2). Realización:
  agentic_code = FS local (`~/.claude/skills` + project + `--add-dir`, equivalente a las 5 fuentes canónicas);
  agentic_assistant = store por `user_id` (multi-tenant). Criterio: `tools()` rinde `SkillTool` sobre el catálogo del
  scope correcto; el store no colisiona entre usuarios ni escapa del prefijo. (FIND-SKILL1, cruza 15·CG-STOR-1/3.)
- **OI-SKILL-B · Proveer las reglas de permiso + auto-mode de SkillTool.** Capacidad: qué skills se auto-conceden vs
  piden aprobación. Costura: `PermissionContext` (deny/allow-rules) + `SAFE_SKILL_PROPERTIES` (la battery implementa
  el `check_permission`; el integrador aporta las reglas + la política auto-mode). → **06·GAP-02**. Firma: SkR4.
  Realización: agentic_code = reglas locales; agentic_assistant = política per-tenant. Criterio:
  `test_skill_deny_rule` + `test_skill_safe_properties_autoallow`. (FIND-SKILL5.)
- **OI-SKILL-C · Cablear el gate enable/disable + `is_enabled`.** Capacidad: activar/desactivar skills por
  deployment/usuario/feature-flag. Costura: `SkillsProvider(is_enabled=Callable)` (**el factory hoy NO lo pasa** →
  `default_is_enabled` por frontmatter, verificado factory:161). Realización: agentic_code = env/setting;
  agentic_assistant = flags per-tenant. Criterio: una skill deshabilitada no se lista ni es invocable. (FIND-SKILL3
  es el eje de frontmatter; `is_enabled` es la inyección runtime.)
- **OI-SKILL-D · Inyectar el `skill_listing` como system-reminder por turno.** Capacidad: el modelo ve el catálogo de
  skills DISPONIBLES (no sólo las activas). Costura: la battery expone `provider.skill_listing(ctx)` (CG-SKILL-4); el
  integrador lo surface por turno (como el recall de memoria, `_inject_recall`) — **el loop standalone NO lo surface**
  (§2.4/§3.3 Q3). Realización: agentic_code = attachment terminal; agentic_assistant = BFF/system-reminder. Criterio:
  el modelo recibe el listing incremental con budget. (FIND-SKILL9.)

**Específicos (realización concreta de un integrador):**
- **OI-SKILL-E · Afordancias de interfaz** — `/skills` (SkillsMenu), `useSkillsChange` (refresco al cambiar el
  watcher). CLI-ONLY/INTERFAZ. Realización: agentic_code = terminal (diálogo ink); agentic_assistant = capa front
  (`new_core`). Criterio: el usuario lista/activa skills por la interfaz. (SK-NA-1/2.)
- **OI-SKILL-F · Bundled skills de producto** — cada integrador registra sus propios bundled vía `register_bundled_skill`
  (CG-SKILL-12); los 15 de Claude Code = producto (⛔ SK-NA-3). Realización: agentic_code/agentic_assistant registran
  su set al arrancar. Criterio: los bundled del integrador aparecen sin dir en disco. (FIND-SKILL15.)
- **OI-SKILL-G · MCP-skills wiring** — 11 emite los comandos MCP (`mcp__srv__prompt` diferido / `srv:skill`
  `loaded_from='mcp'`); 12 los mergea (`merge_mcp_skills`, gate `MCP_SKILLS && supportsResources`). El builder
  `mcpSkills.ts` no vendorizado (⛔ no-leíble). Realización: integrador con MCP habilitado. Criterio:
  `test_mcp_skill_invocable_via_skill_tool` + `test_mcp_prompt_is_deferred_not_skill`. (FIND-MCP16, cross 11.)
- **OI-SKILL-H · Hot-reload / ConfigChange** — el integrador provee el watcher FS (agentic_code inotify;
  agentic_assistant poll/evento MinIO) que llama `provider.refresh()` + dispara el ConfigChange hook (06) +
  `reset_sent_skill_names`. Realización: por integrador. Criterio: catálogo fresco tras cambio en disco. (FIND-SKILL13.)

**Cabos que aterrizan aquí (cerrados con destino):**
- **15·B8 (`battery_session_catalog` / skills store `prefix="skills"` sin scope, factory sin auto-cablear)** →
  **CONFIRMADO este ciclo** (factory:161 no auto-cablea; store.py:35-40 sin scope) → §0.1/§0.2 + OI-SKILL-A; el guard-
  path/scope pliega en **15·CG-STOR-1/CG-STOR-3** (helper unificado), no duplica.
- **13·D8 (`compact_context` sin consumidor)** → **mismo tratamiento** (§2.4): skills tiene el hook idéntico
  (provider:173-179), cara del motor-compactación NO portado (01/02), NO B-orphan nuevo. Cabo cerrado sin finding.
- **13·B9 (searching-past-context, nexo skills-search)** → **NO aterriza como CORE-GAP**: el equivalente skills es
  `EXPERIMENTAL_SKILL_SEARCH` (⛔ SK-NA-5, semántica remota ant-only); ni base ni battery lo requieren. Cabo cerrado.
- **FIND-SKILL14 (ranking-por-uso half-life)** → **aterriza AQUÍ** como CG-SKILL-11 (13 lo devolvió: el recall de
  memoria no usa señal de uso; el ranking es específico de skills). Nota-identidad `persistencia`.

### 2.6 Cabos que SALEN (con destino)
- `B-new_messages` (CG-SKILL-5) → DEUDA-B transversal / 07·EVT (dueño de la entrega transitoria).
- CG-SKILL-3 semántica de permisos → **06·GAP-02**; el gate por-input → 09·dispatcher.
- CG-SKILL-8 fork → **05·execution** (`SubagentRunnerProtocol` S18, cerrado en A2.5).
- CG-SKILL-9 hooks + FIND-SKILL13 ConfigChange → **06·hooks** (HookSink + CG-HOOK).
- CG-SKILL-10 evento file-op → **10·tools-native** (post-Read/Write/Edit) + **07·events**.
- CG-SKILL-15 (FIND-MCP16) → **11·mcp** (emite comandos MCP); builder `mcpSkills.ts` no-leíble.
- CG-SKILL-14 cleanup por-agent → **05·ExR6 / 08·SR3** (abort-scope/fork-close).
- Store scope/guard-path → **15·CG-STOR-1/CG-STOR-3** (unificado, no duplicar).

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor:** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda;
ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar
—o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — 20 FIND-* + 12 SK-OK + 5 SK-NA + 1 DEUDA-B (LAT-CAP1, destapada post-gate al abrir `contracts.py`) = 38
| ID | TIER | destino | cara | evidencia | detalle | nota-id |
|---|---|---|---|---|---|---|
| FIND-SKILL1 | CORE-GAP | CG-SKILL-7 | base+integrador | `loader.py:97-114` 1→EOF (una fuente) + grep-ausencia `realpath/load_sources`=0 | sí (SkR2 + §2.5 OI-A) | persistencia |
| FIND-SKILL2 | CORE-GAP (T1+BATTERY) | CG-SKILL-1 | base | `frontmatter.py:27-32` 1→EOF (6 campos) | sí (SkR1) | — |
| FIND-SKILL3 | CORE-GAP (T1) | CG-SKILL-1 | base+integrador | `loader.py:35/46` 1→EOF (`enabled` único) | sí (SkR1 + §2.5 OI-C) | — |
| FIND-SKILL4 | CORE-GAP (seguridad) | CG-SKILL-2 | base | `skill_tool.py:18-35` 1→EOF + grep-ausencia substitute/bash=0 | sí (SkR3) | — |
| FIND-SKILL5 | CORE-GAP + T2-COSTURA | CG-SKILL-3 → 06·GAP-02 + 09 | base+integrador | `skill_tool.py:92` 1→EOF (`requires_permission=False`, único hit) | sí (SkR4 + §2.5 OI-B) | — |
| FIND-SKILL6 | CORE-GAP | CG-SKILL-8 → 05 | base | `skill_tool.py:107-120` 1→EOF (execute inline sin fork) | sí (SkR9) | — |
| FIND-SKILL7 | CORE-GAP | CG-SKILL-6 | base | `skill_tool.py:47-64` 1→EOF (`model` almacenado :56, no aplicado) | sí (SkR5, §2.4) | — |
| FIND-SKILL8 | CORE-GAP | CG-SKILL-5 (B-new_messages) | base | `skill_tool.py:118` + `agent_loop.py:319-323` 1→EOF + grep-ausencia new_messages=0 | sí (SkR6) | — |
| FIND-SKILL9 | CORE-GAP | CG-SKILL-4 | base+integrador | `agent_loop.py:235-239` 1→EOF (call NO surface listing) + grep catalog/listing en loop=0 | sí (SkR7 + §2.5 OI-D, PRECISIÓN §3.3) | — |
| FIND-SKILL10 | ✅🔀 + CORE-GAP-menor | CG-SKILL-14 → 05·ExR6/08·SR3 | base | `skill_tool.py:53-58` 1→EOF (`active_skills` sin path/invoked_at) | sí (SkR8) | — |
| FIND-SKILL11 | CORE-GAP | CG-SKILL-9 → 06 | base | `frontmatter.py` 1→EOF (sin `hooks`) + grep-ausencia=0 | sí (SkR11) | — |
| FIND-SKILL12 | CORE-GAP | CG-SKILL-10 → 10/07 | base+integrador | grep-ausencia conditional/discover=0 (este ciclo) | sí (SkR12) | — |
| FIND-SKILL13 | 🔀 + BATTERY + T3 | `provider.refresh()` (SkR16) + OI-SKILL-H | base+integrador | `provider.py:87-106` 1→EOF (register/unregister vivos; sin watcher) | sí (SkR16 + §2.5 OI-H) | — |
| FIND-SKILL14 | CORE-GAP | CG-SKILL-11 | base | grep-ausencia record_usage/score=0 (cabo 13) | sí (SkR14) | persistencia |
| FIND-SKILL15 | CORE-GAP (mecanismo) | CG-SKILL-12 | base+integrador | grep-ausencia register_bundled=0 | sí (SkR13 + §2.5 OI-F) | — |
| FIND-SKILL16 | CORE-GAP | CG-SKILL-13 | base | `state.py:24` 1→EOF (`get` exacto) | sí (SkR10) | — |
| FIND-SKILL17 | CORE-GAP | CG-SKILL-4 | base | `provider.py:137-142` 1→EOF (`when_to_use=description`, sólo `is_enabled`) | sí (SkR7) | — |
| FIND-SKILL18 | CORE-GAP | CG-SKILL-5 | base | `skill_tool.py:79-82` 1→EOF (description one-liner) | sí (SkR6) | — |
| FIND-SKILL19 | CORE-GAP | CG-SKILL-2 (prompt_provider) | base | `skill_tool.py:18-35` 1→EOF (render estático) + grep getPromptForCommand=0 | sí (SkR3) | — |
| FIND-MCP16 | BATTERY (bridge) + T3 | CG-SKILL-15 → 11 | base+integrador | grep-ausencia loaded_from/merge_mcp=0; builder no-vendorizado | sí (SkR15 + §2.5 OI-G) | — |
| SK-OK-1 | BATTERY | load_skills_dir | base | `loader.py:97-114` 1→EOF | sí (§2.2) | — |
| SK-OK-2 | BATTERY | load_skills_dir try/except + sorted | base | `loader.py:106-113` 1→EOF | sí (§2.2) | — |
| SK-OK-3 | BATTERY | SkillFrontmatter (extra=allow) | base | `frontmatter.py:25/34-77` 1→EOF | sí (§2.2) | — |
| SK-OK-4 | BATTERY | SkillDefinition.base_dir | base | `loader.py:29-32/94` 1→EOF | sí (§2.2) | — |
| SK-OK-5 | T2-BASE-MECANISMO | build_skill_context_modifier (aplicado loop) | base | `skill_tool.py:47-64` + `agent_loop.py:332-337` 1→EOF | sí (§2.1) | — |
| SK-OK-6 | T2-BASE-MECANISMO | active_context per-turno (_inject_recall) | base | `provider.py:153-171` + `agent_loop.py:218/112-130` 1→EOF | sí (§2.1, =FIND-SKILL10) | — |
| SK-OK-7 | T2-COSTURA (integrador) | process_slash_command | base | `commands.py:32-64` + `provider.py:80-85` 1→EOF (loop no importa) | sí (§2.1) | — |
| SK-OK-8 | T2-COSTURA (repo propio) | SkillStore · StorageBackedSkillStore | base+integrador | `store.py` 1→EOF + `factory.py:160-164` 1→EOF (no auto-cablea) | sí (§0.1, cabo 15·B8) | persistencia |
| SK-OK-9 | BATTERY | provider.unregister | base | `provider.py:95-106` + `state.py:27` 1→EOF | sí (§2.2) | — |
| SK-OK-10 | T2-BASE + coherencia 09 | SkillTool en pool per-turno | base | `provider.py:144-151` 1→EOF (GAP-SKILL2 resuelto) | sí (§2.2) | — |
| SK-OK-11 | T1-CONTRATO | SkillDefinition.version | base | `loader.py:36-38` 1→EOF | sí (§2.1) | — |
| SK-OK-12 | T2-BASE-MECANISMO | provider.tools/catalog + load_skill_text | base | `provider.py:131-151` + `loader.py:49-81` 1→EOF | sí (§2.1, PRECISIÓN catalog §2.4) | — |
| SK-NA-1 | CLI-ONLY/INTERFAZ | 00-INTEGRADORES (OI-E) | integrador | tracker-leído (UI.tsx ⛔, abierto) | sí (§2.5 OI-E) | — |
| SK-NA-2 | CLI-ONLY/INTERFAZ | 00-INTEGRADORES (OI-E) | integrador | tracker-leído (SkillsMenu/`/skills`/useSkillsChange ⛔, abiertos) | sí (§2.5 OI-E) | — |
| SK-NA-3 | ⛔ (contenido) | ⛔ producto (mec.=CG-SKILL-12) | integrador | tracker-leído (15 bundled abiertos 1→EOF) | sí (§2.5 OI-F) | — |
| SK-NA-4 | ⛔ | ⛔ producto (gated) | — | tracker-leído (skillImprovement abierto) | N/A (⛔) | — |
| SK-NA-5 | ⛔ | ⛔ experimental | — | tracker-leído (skillSearch ⛔); nexo 13·B9 | N/A (⛔) | — |
| LAT-CAP1 | DEUDA-B (cablear\|borrar) | `DEUDA-B §B-orphans` (home 12/general) → A3.DB | base | `contracts.py:26-38` **1→EOF ESTE ciclo** + grep prod-consumers=0 (sólo def+re-export) | sí (§2.4) | — |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../12-cap-skills.md`?** → **Sí**, 1→611: §Estado gate-11, §Alcance/Fuera-de-alcance, §Tesis
   arquitectural, tablas A/B/C/D/E/F/G/H/I, §Hallazgos FIND-SKILL1-19 + FIND-MCP16 + GAP-SKILL1-3, §Cabos-que-entraron,
   §Recuento, §Re-visita COMPLETITUD gate-11 (mini-ledger + 2 precisiones + LAT-SKILL1 + ❌-convergen + §honestidad +
   4 preguntas + VEREDICTO), §Ledger de archivos, §Plan SkR1-17, §Nota metodológica, §Re-auditoría 2026-07-14.
2. **¿Reconcilia el conteo?** findings vinculantes en `../12-cap-skills.md` = **20** (FIND-SKILL1-19 + FIND-MCP16, per
   su §Recuento "20 findings … lo vinculante son los IDs FIND-SKILL/GAP-SKILL"); colocados = **20**; sin colocar =
   **0**. `GAP-SKILL1`=FIND-SKILL5, `GAP-SKILL3`=FIND-SKILL12 (alias); `GAP-SKILL2`=coherencia is_deferred resuelta
   (SK-OK-10). Además colocadas **12 capacidades homologadas** (SK-OK-1..12, ✅/🟡/🔀 sin ID) + **5 ⛔/interfaz**
   (SK-NA-1..5) + **1 DEUDA-B nueva LAT-CAP1** (destapada post-gate al abrir `contracts.py` 1→EOF) → ledger de
   **38 filas**, ninguna sin colocar bajo la lectura más estricta. `SkR1-17` = §Plan referenciado, no re-contado
   (patrón 06/10/04/15/13). LAT-CAP1 = hallazgo B-interno de la SEPARACION (como los LAT-* de rondas previas), no un
   FIND del tracker → no altera los 20 vinculantes.
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ENSAMBLADOR (sin apoyarse en grep)?** → Tramos ABIERTOS 1→EOF
   EN ESTE CICLO (no heredados del gate-11 2026-07-20):
   - **SK-OK-8/OI-A (registro condicional, store no auto-cableado)**: `factory.py` **1→267 ÍNTEGRO** —
     `_build_capability_manager:160-164` registra `SkillsProvider(skill_store=caps.skill_store)` + `load_dir(root)`
     sólo si `skill_dirs or skill_store`; **NO pasa `storage=` ni `is_enabled=`** (contraste MCP :152 `storage=`) →
     store inyectado por el integrador, default None (cierra cabo 15·B8).
   - **SK-OK-5/6/10, FIND-SKILL9 (tool per-turno, context_modifier aplicado, listing no-surfaced)**: `agent_loop.py`
     **1→353 ÍNTEGRO** — `_build_tool_pool:85-97` + `:194-196` DENTRO del `for _turn in range(_MAX_TURNS):185`
     (tool `Skill` reensamblada per-turno); `context_modifier` APLICADO `:332-337` (no sólo atributo); `_inject_recall
     :218/112-130` (active_skills→reminder, dedup); **la llamada al modelo `:235-239` NO surface `catalog()`/listing**
     (sólo `tool_schemas` del pool + `ctx.messages`). + `manager.py` **1→112 ÍNTEGRO** (`tools:50-59` dedup,
     `build_tool_pool:61-79`, `active_context:98-102`, `catalog:44-48` agregador).
   - **SK-OK-7 (slash desacoplado)**: `commands.py:32-64` 1→EOF + `provider.py:80-85` (el loop NO lo importa).
   - **Seam `CapabilityProvider`/`CapabilitySummary`/`CapabilityActivation` (tesis §0/§2.1)**: `capabilities/
     contracts.py` **1→EOF ESTE ciclo** (76 líneas — **abierto tras el gate auto-adversarial**; mi cierre inicial lo
     había INFERIDO del consumo en `manager.py` + la implementación en `provider.py`, sin abrir el contrato = fallo
     L08 que el gate cazó). Confirma: `CapabilityProvider` Protocol (startup/shutdown/catalog/tools/active_context/
     compact_context + `system_prompt_section` OPCIONAL vía getattr, :49-58); `CapabilitySummary` con campo `deferred`;
     y **destapa `CapabilityActivation` inerte** → LAT-CAP1 (§2.4).
   - **FIND-SKILL9 PRECISIÓN (`catalog()` no cableado al modelo)**: **grep-de-ausencia ESTE CICLO** (legítimo, L09):
     `grep '\.catalog('` = SÓLO `manager.py:47` (agregador interno); `grep catalog|skill_listing` en `agent_loop.py`
     = **0** → confirmado por LECTURA del tramo `:235-239` (call), no por tabla. El ❌ se sostiene (gap MAYOR).
   - **CORE-GAPs load-bearing (ausencia)**: **grep-de-ausencia POR-TÉRMINO ESTE CICLO** (`-Ev '(^|/)tests/'`):
     `substitute/ARGUMENTS/CLAUDE_SKILL_DIR/getPromptForCommand`=0 (CG-2) · `check_permission/SAFE_SKILL/deny_rule`=0
     (sólo `requires_permission=False`, CG-3) · `skill_listing/sent_skill/budget`=0 (CG-4) · `new_messages`=0 en
     skills+`tools/protocol.py` (CG-5/B-new_messages) · `realpath/load_sources/precedence`=0 (CG-7) ·
     `context.*fork/register_skill_hooks/conditional/discover`=0 (CG-8/9/10) · `record_skill_usage/register_bundled/
     aliases`=0 (CG-11/12/13) · `loaded_from/merge_mcp`=0 (FIND-MCP16). Confirmado por ausencia+lectura, no heredado.
4. **¿La cara integrador quedó al MISMO detalle que la base?** → **Sí.** OI-SKILL-A..H (raíces/store · reglas de
   permiso · gate enable · surface del listing · afordancias `/skills` · bundled de producto · MCP-skills wiring ·
   hot-reload) con capacidad·costura·firma·realización(code/assistant)·criterio (§2.5). Cabos 15·B8/13·D8/13·B9/
   FIND-SKILL14 cerrados con destino. Ningún "→ integrador" a secas.
5. **¿Doble filo (L10)?** → **Sí, calibrado.** (a) Ningún ❌ disfrazado de 🔀: FIND-SKILL4 (substitución+bash, ❌
   funcional+seguridad)/FIND-SKILL5 (gate permisos, ❌ seguridad)/FIND-SKILL9 (listing, ❌ **MAYOR** — el standalone
   no surface NADA, no "re-emite todo")/FIND-SKILL19 (callable) son CORE-GAP honestos. (b) Sin deuda inflada:
   entrega `output` vs new_messages = 🔀 hasta B-new_messages (transversal, no gap-base propio); hot-reload = 🔀
   deliberado (API viva cubre el observable, watcher=CLI-forma); invoked_skills = ✅🔀 concepto homologado +
   matiz-gap menor; `compact_context` = cara del motor-compact YA conocido (01/02), NO B-orphan nuevo; `catalog()`
   sin caller = seam de introspección del integrador, NO B-orphan; bundled-contenido/UI/skillSearch = ⛔
   (producto/interfaz/experimental, no troceo). **DEUDA-B propia = LAT-SKILL1** (seam a medio cablear → cablear vía
   SkR3) **+ LAT-CAP1** (`CapabilityActivation` inerte, home 12/general, cablear-o-borrar → A3.DB); ambas B-interno
   NO A↔B (el canónico no tiene ninguno). Store scope/guard-path NO se re-cuenta como deuda de 12 (pliega en
   15·CG-STOR-1/3, unificado).

### 3.3 §Honestidad
- **Leídos 1→EOF EN ESTE CICLO** (L08/L09, no heredados del gate-11): `capabilities/skills/{provider.py 182,
  skill_tool.py 123, loader.py 123, frontmatter.py 115, store.py 71, commands.py 67, state.py 39, __init__.py 34}`;
  **el contrato `capabilities/contracts.py` (76)** (abierto post-gate, ver auto-corrección abajo); **ENSAMBLADOR**:
  `factory.py` (267), `capabilities/manager.py` (111), `loop/agent_loop.py` (353) + grep-de-ausencia por-término
  (substitute/permisos/listing/new_messages/fuentes/fork/hooks/conditional/ranking/bundled/aliases/loaded_from = 0;
  `catalog()` prod-consumer = sólo `manager.py:47`; `catalog|skill_listing` en loop = 0; `CapabilityActivation`
  prod = 0 → LAT-CAP1).
- **AUTO-CORRECCIÓN (gate auto-adversarial del usuario, "¿EoF en todos los archivos?"):** mi 1er cierre afirmó
  implícitamente "todo 1→EOF" pero **NO había abierto `capabilities/contracts.py`** — inferí el shape del seam rector
  `CapabilityProvider` del consumo (`manager.py`) + la implementación (`provider.py`), sin abrir el contrato = **fallo
  L08 exacto** (la superficialidad se esconde en el archivo no abierto). Al reproche lo LEÍ 1→EOF y destapó
  **LAT-CAP1** (`CapabilityActivation` inerte) — un B-orphan que el cierre inicial habría enterrado. Añadido a §2.4 +
  ledger (38 filas) + Q2/Q5. Regla re-interiorizada (idéntica a 04·modes de este mismo lote): en un ciclo cuyo eje
  es un SEAM, el archivo del CONTRATO de ese seam se abre 1→EOF, no se infiere del consumo.
- **A canónico NO re-leído esta ronda** (honesto): el tracker documenta la re-lectura 1→EOF de los 10 archivos A
  in-scope en su gate-11 (2026-07-20, con 2 auto-correcciones adversariales: "ensamblador por tramos" y "no has
  vuelto a leer A") + belt-and-suspenders 2026-07-14 (SkillTool.ts 1108 + loadSkillsDir.ts 1086). Esta SEPARACION es
  MEJORA DE FORMA sobre findings ya establecidos, no una 3ª validación A↔B. La re-verificación de este ciclo se centró
  en **B + ENSAMBLADOR** (donde vive la clasificación TIER/destino/cableado, lo nuevo de la SEPARACION).
- **Value-add del ciclo (por qué NO fue confirmación-de-doc):** abrir el ENSAMBLADOR 1→EOF confirmó por CABLEADO
  (no tabla) la asimetría con memoria (SkillsProvider SÍ rinde tool viva per-turno + catalog no vacío) y re-confirmó
  la precisión FIND-SKILL9 (el loop `:235-239` no surface listing) leyendo el tramo, no por grep; y cerró el cabo
  15·B8 leyendo `factory:160-164` (store NO auto-cableado, sin `storage=`/`is_enabled=`).
- **DEUDA-B propia = LAT-SKILL1 + LAT-CAP1** (a diferencia de 13/04 que tienen NINGUNA): LAT-SKILL1 = seam a medio
  cablear (args announce/discard) → CABLEA vía CG-SKILL-2/SkR3, hermano de LAT-HOOK1; LAT-CAP1 = `CapabilityActivation`
  inerte (home 12/general, destapado post-gate) → cablear-o-borrar A3.DB. `compact_context`/`catalog()` sin caller =
  caras de gaps ya conocidos / seams de integrador, no B-orphans nuevos (L10 anti-padding).
- **NO verificado (honesto):** el diseño fino de `prompt_provider`/substitución/bash-injection (CG-SKILL-2) + el gate
  de permisos (CG-SKILL-3) se desarrollan al construir `battery_skills` (Fase C) sobre 06·GAP-02/09·dispatcher;
  el fork-dispatch (CG-SKILL-8) sobre 05·SubagentRunnerProtocol (cerrado A2.5); el evento file-op (CG-SKILL-10) sobre
  10/07; el bridge MCP (CG-SKILL-15) sobre 11 + el builder `mcpSkills.ts` (no vendorizado, ⛔). El catálogo definitivo
  `battery_skills` (¿1 paquete o submódulos loader/render/listing/dynamic/bundled/mcp?) → **A3.CAT**. Suite NO
  re-ejecutada (fase de diseño, sin cambio de código — PLAN §1.6; el tracker reporta 11 passed + 19 xfailed intactos,
  targets SkR xfail siguen rojos = gaps vivos).

### 3.4 VEREDICTO
**✅ NADA PENDIENTE → A3·11·mcp** (siguiente ciclo sin marcar del checklist PLAN §7 tras 12·skills — verificado
contra §7: 05·execution ya cerrado en A1.5, el orden A3 restante es 11·mcp → 14·plan → 17·voice → 18·factory).
Conteo 20=20=0 (vinculantes) + 12 SK-OK + 5 SK-NA + 1 LAT-CAP1 = 38 colocadas. Las 5 preguntas: sí honestas (Q3 con
ENSAMBLADOR `factory`/`manager`/`agent_loop` **+ el contrato `contracts.py`** 1→EOF ESTE ciclo + grep-de-ausencia
por-término; Q5 doble-filo calibrado). **Cierre en 2 iteraciones (gate auto-adversarial): el 1er cierre NO abrió
`contracts.py` (fallo L08); al reproche se abrió 1→EOF y destapó LAT-CAP1 — incorporado.** CORE-GAPs anclados con
destino: CG-SKILL-1..15 → SkR1-17 + 06/05/09/10/07/11. Battery `battery_skills` (+ bridge `battery_mcp_skills`) →
A3.CAT; DEUDA-B propia = LAT-SKILL1 (cablear vía SkR3) + LAT-CAP1 (A3.DB); OI-SKILL-A..H →
`00-INTEGRADORES`. Cabos 15·B8 (store no auto-cableado, confirmado) + 13·D8 (compact_context, mismo tratamiento) +
13·B9 (skill-search ⛔, no aterriza) + FIND-SKILL14 (aterriza como CG-SKILL-11) cerrados/confirmados. Ningún pendiente
de verificación (L04).
