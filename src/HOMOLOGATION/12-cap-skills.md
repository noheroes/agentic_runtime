# 12 · capabilities/skills — homologación

> **Estado (2ª vuelta · gate 11/L09 de ENTRADA — ✅ VALIDADA 2026-07-20).** Lado B (los 8
> `capabilities/skills/*.py`) + el **ENSAMBLADOR** (`factory._build_capability_manager:142-164`,
> `CapabilityManager`, `loop/agent_loop.py:85-352`) releídos 1→EOF esta ronda. Cada ✅/🔀 re-verificada
> **abriendo el código de B que la reproduce y siguiendo el cableado**, no la tabla. **CERO cambios de estado,
> código intacto, suite no re-ejecutada.** 2 precisiones de mecanismo (no voltean estado) + 1 costura latente
> nueva (LAT-SKILL1). Ver bloque "Re-visita de COMPLETITUD (gate 11/L09)" al pie del Recuento.

Contrasta `agentic_runtime/src/agentic_runtime/capabilities/skills/*` (8 archivos, 754 LOC) contra el
subsistema de skills del canónico: `skills/{loadSkillsDir,bundledSkills,mcpSkillBuilders}.ts` + `skills/bundled/*`,
`tools/SkillTool/*`, el motor de `commands.ts`, `commands/skills/*`, `utils/skills/*`, `utils/hooks/{registerSkillHooks,skillImprovement}.ts`,
`utils/suggestions/skillUsageTracking.ts`, `hooks/useSkillsChange.ts`, `components/skills/SkillsMenu.tsx`, y los
seams de entrega (`utils/attachments.ts` skill-listing/dynamic/invoked, `bootstrap/state.ts` invokedSkills,
`utils/messages.ts` renderers, `services/mcp/utils.ts` naming prompt-vs-skill).

**Alcance**: comportamiento del *core* de skills — carga, modelo, invocación (inline/fork), entrega al modelo,
resolución de slash-commands, permisos, descubrimiento dinámico/condicional, hooks de skill, MCP-skills. El
runtime soporta usuarios/sesiones y es long-running; el canónico es single-user en terminal, así que la
homologación de la entrega y del hot-reload es **de comportamiento observable**, no de forma (ink/React).

**Fuera de alcance (⛔, abiertos y confirmados — NO en el ledger de "core")**: `tools/SkillTool/UI.tsx` (render
ink del tool_use/result/progress), `components/skills/SkillsMenu.tsx` (diálogo del `/skills`), `commands/skills/{index,skills}.tsx`
(el slash `/skills` es `local-jsx`→`SkillsMenu`), `hooks/useSkillsChange.ts` (hook React que refresca la lista al
cambiar el watcher/growthbook), `skills/bundled/*.ts` **como contenido** (15 skills de producto de Claude Code —
`simplify`/`verify`/`loop`/`remember`/… — el *mecanismo* `registerBundledSkill` sí entra), `utils/hooks/skillImprovement.ts`
(auto-mejora de skills por LLM, gated `SKILL_IMPROVEMENT`+`copper_panda` — producto), y las 4 ramas
`EXPERIMENTAL_SKILL_SEARCH`/remote-skill de `SkillTool.ts` (búsqueda semántica remota ant-only).

## Tesis arquitectural
El canónico trata las skills como un caso de **`Command` de tipo `prompt`**: la misma abstracción cubre skills
de `/skills/`, comandos legacy de `/commands/`, bundled, plugin y MCP. La tool `Skill` **no ejecuta** la skill:
expande su `SKILL.md` en un prompt (con substitución de `$args`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_SESSION_ID}` y
bash-injection `!\`…\``) y lo entrega como **`newMessages` transitorios** + un `contextModifier` que aplica
allowed-tools/model/effort. El catálogo llega al modelo como **system-reminder incremental por-agente**
(`skill_listing`, sólo deltas, con budget del 1% de la ventana). La supervivencia a compactación es un estado
global `invokedSkills` keyed por `agentId` que se re-inyecta como "continue to follow".

El runtime porta el **esqueleto correcto** (loader tolerante, `SkillDefinition` tipada, `SkillsProvider` por
contrato, tool `Skill` con `context_modifier`, `active_skills` para compactación, slash-command desacoplado del
loop) pero **una sola fuente**, **frontmatter reducido**, **sin substitución de args ni variables ni bash**, **sin
gate de permisos**, **catálogo re-emitido entero cada turno** (no incremental/budget), **sin fork en la tool**,
**sin skills condicionales/dinámicas/hooks/ranking/bundled**, y **sin MCP-skills**.

## Leyenda
✅ homologado · 🟡 parcial · 🔀 distinto (deliberado o a revisar) · ❌ no portado · ⛔ N/A core (UI/producto).

---

## A · Carga, fuentes y ciclo de vida (`loader.py`/`store.py`/`provider.startup` vs `loadSkillsDir.ts` + `commands.ts::getSkills`)

| Feature canónica | Runtime | Estado |
|---|---|---|
| Formato `skill-name/SKILL.md` (glob dir); single `.md` **no** en `/skills/` | `load_skills_dir` glob `*/SKILL.md` | ✅ |
| Aislamiento por ítem (un SKILL.md roto no tumba el resto) + orden estable | `load_skills_dir` try/except por path, `sorted` | ✅ |
| **Fuentes múltiples con precedencia**: managed(policy)/user/project(up-to-home)/additional(`--add-dir`)/legacy `/commands/`/plugin/bundled/mcp | **una** fuente: `load_dir(root)` + `SkillStore` | ❌ **FIND-SKILL1** |
| **Dedup por realpath** (`getFileIdentity`, symlinks / parents solapados) | sin dedup (dict por nombre; último gana) | ❌ FIND-SKILL1 |
| Setting-source gating (`isSettingSourceEnabled`), plugin-only policy (`isRestrictedToPluginOnly`), `--bare` (sólo `--add-dir`), `CLAUDE_CODE_DISABLE_POLICY_SKILLS` | ninguno | ⛔/❌ (config de producto) |
| Legacy `/commands/`: `transformSkillFiles`, namespacing `ns:cmd`, SKILL.md toma nombre del dir padre | no portado | 🔀 (deprecado; ver FIND-SKILL16 namespacing) |
| Carga programática desde texto (tests) | `add_skill_text`/`register_skill` | ✅ |
| Persistencia inyectable (`SkillStore`/`StorageBackedSkillStore` en `<prefix>/<name>/SKILL.md`) + `startup()` que rehidrata | ✅ (no existe en canónico; habilita MinIO/sesiones) | ✅ 🔀 seam propio |
| `unregister`/`remove` en vivo (server long-running) | `SkillsProvider.unregister` (store + estado) | ✅ (mejora sobre canónico) |
| Memoización + `clearSkillCaches`/`clearCommandsCache` | N/A (sin memo por cwd) | 🔀 |
| `estimateSkillFrontmatterTokens` (name+desc+whenToUse) | no | ❌ (UI `/skills`; nexo budget FIND-SKILL9) |

## B · Modelo de skill (`SkillDefinition`/`SkillFrontmatter` vs `Command`/`parseSkillFrontmatterFields`)

| Campo/derivación canónica | Runtime | Estado |
|---|---|---|
| `name` ← frontmatter o **nombre del dir** (identidad garantizada) | ✅ `name_hint` | ✅ |
| `description` ← frontmatter o `extractDescriptionFromMarkdown`/primer párrafo | ✅ `_first_paragraph` | ✅ |
| `allowed-tools` (lista o CSV) | ✅ coerción lista/CSV | ✅ |
| `model` (`inherit`/None → hereda; si no `parseUserSpecifiedModel`) | ✅ (`_INHERIT` → None) | 🟡 (sin `parseUserSpecifiedModel`/alias `[1m]`) |
| `version` passthrough | ✅ | ✅ |
| **`when_to_use`** (SEPARADO de description; alimenta el listado `desc - whenToUse`) | ❌ (usa description como when_to_use en `catalog`) | ❌ **FIND-SKILL2** |
| **`argument-hint`** + **`arguments`/`argumentNames`** | ❌ | ❌ FIND-SKILL2 |
| **`disable-model-invocation`** (no invocable por el modelo vía SkillTool) | ❌ (sólo `enabled`) | ❌ **FIND-SKILL3** |
| **`user-invocable`** (typeable como slash; `isHidden=!userInvocable`) — ORTOGONAL a lo anterior | ❌ (conflado en `enabled`) | ❌ FIND-SKILL3 |
| **`hooks`** (HooksSchema) | ❌ (no se parsea) | ❌ **FIND-SKILL11** |
| **`context: fork`** | ❌ | ❌ **FIND-SKILL6** |
| **`agent`** (agentType para fork) | ❌ | ❌ FIND-SKILL6 |
| **`effort`** (`parseEffortValue`) | ❌ | ❌ **FIND-SKILL7** |
| **`shell`** (`parseShellFrontmatter`, para bash-injection) | ❌ | ❌ FIND-SKILL4 |
| **`paths`** (`splitPathInFrontmatter` → skills condicionales) | ❌ | ❌ **FIND-SKILL12** |
| `displayName` (`name` de frontmatter) vs `skillName` (dir) → `userFacingName()` | 🟡 (sólo `name`) | 🟡 |
| Frontmatter tolerante (`extra="allow"`, coerción por campo, nunca lanza) | ✅ pydantic `extra="allow"` + validators | ✅ (paridad de robustez ante terceros) |
| `base_dir`/`skillRoot` para localizar archivos bundled | ✅ | ✅ |

## C · Invocación inline (`SkillTool.execute`/`build_skill_context_modifier` vs `SkillTool.call` inline)

| Feature canónica | Runtime | Estado |
|---|---|---|
| `SKILL_TOOL_NAME='Skill'`; input `{skill, args}` | ✅ (`command`/`args` — nombre distinto: `command` vs `skill`) | 🟡 (nombre de campo) |
| `validateInput`: trim, **strip leading `/`**, `disableModelInvocation`→error, type prompt | 🟡 (existencia + enabled; sin strip-slash ni disable-model) | 🟡 **FIND-SKILL16/3** |
| **Substitución de `$1`/`$ARGUMENTS`/`$NAME`** (`substituteArguments` + argumentNames) | ❌ (`render_skill` ignora `args`) | ❌ **FIND-SKILL4** |
| **`${CLAUDE_SKILL_DIR}`** (normalizado win32) + **`${CLAUDE_SESSION_ID}`** | ❌ | ❌ FIND-SKILL4 |
| **`executeShellCommandsInPrompt`** (`!\`…\``) con allowed-tools como allow-rules; **prohibido si `loadedFrom==='mcp'`** | ❌ | ❌ FIND-SKILL4 (funcional + seguridad) |
| **`getPromptForCommand(args, ctx)` es un CALLABLE async, side-effecting, ctx-aware** (lee memoria/archivos/red, parsea args, ramifica por flags, habilita logging) — no un markdown estático | ❌ (`instructions` string + `render_skill`) | ❌ **FIND-SKILL19** |
| Prefijo `Base directory for this skill: <dir>` | ✅ (`render_skill`) | ✅ |
| `contextModifier`: allowed-tools → `alwaysAllowRules.command` | ✅ (`with_command_allow` + `mark_tools_discovered`) | ✅ (+ mejora: anuncia MCP diferidas) |
| `contextModifier`: **model override** (`resolveSkillModelOverride`, carry `[1m]`) | ❌ | ❌ **FIND-SKILL7** |
| `contextModifier`: **effort override** (`appState.effortValue`) | ❌ | ❌ FIND-SKILL7 |
| Estado activo estructurado (contenido completo, no sólo nombre) | ✅ (`active_skills` en `caps`) | ✅ |
| Tool `Skill` NO diferida, entra sin permiso por defecto | 🔀 (ver G · permisos) | 🔀 |
| `recordSkillUsage` al invocar | ❌ | ❌ **FIND-SKILL14** |

## D · Invocación forked (`executeForkedSkill` — ausente en runtime SkillTool)

| Feature canónica | Runtime | Estado |
|---|---|---|
| **`SkillTool.call` despacha a fork** si `command.context==='fork'** (`runAgent` sub-agente aislado) | ❌ (la tool sólo activa inline; el fork lo decide el runtime vía `RuntimeContextForker`) | ❌ **FIND-SKILL6** |
| `prepareForkedCommandContext` (baseAgent + promptMessages + modifiedGetAppState) | N/A (05·execution) | ❌ |
| Merge de `effort` de la skill en la `AgentDefinition` | N/A | ❌ FIND-SKILL6/7 |
| Progreso `skill_progress` (normaliza mensajes con tool-use/result) | N/A | ⛔/❌ |
| `clearInvokedSkillsForAgent(agentId)` en `finally` | 🟡 (runtime limpia por ctx, no hay cleanup por agent explícito) | 🟡 (nexo 05·ExR6/08·SR3) |
| Output `{status:'forked', agentId, result}` vs `{status:'inline'}` | ❌ (un solo shape) | ❌ |

## E · Entrega al modelo (render / newMessages / skill_listing / invoked_skills)

| Feature canónica | Runtime | Estado |
|---|---|---|
| Resultado de tool **mínimo** (`Launching skill: X`) + **`newMessages` transitorios** (tagged `toolUseID`) que portan el SKILL.md expandido | 🔀 (mete el render completo como `output` del `ToolResult`) | 🔀 **FIND-SKILL8** (nexo B-new_messages / 07·EVT) |
| **`skill_listing`** = system-reminder "The following skills are available…" **incremental por agentId** (`sentSkillNames` delta, `isInitial` vs dynamic) | ❌ (`catalog()` re-emite TODO como `CapabilitySummary`, cada turno) | ❌ **FIND-SKILL9** |
| **Budget** del listado: 1% de la ventana (`getCharBudget`), 250 char/entrada, bundled sin truncar, modos `names_only`/`description_trimmed` | ❌ | ❌ FIND-SKILL9 |
| Skip listado si el agente **no tiene la tool Skill** | ❌ | ❌ FIND-SKILL9 |
| `resetSentSkillNames` (al cambiar el set) / `suppressNextSkillListing` (resume) | ❌ | ❌ FIND-SKILL9 (nexo hot-reload FIND-SKILL13 / conversationRecovery) |
| `getSkillToolCommands` filtro de elegibilidad: `prompt && !disableModelInvocation && source!=builtin && (bundled|skills|commands_DEPRECATED|hasUserSpecifiedDescription|whenToUse)` | 🟡 (`catalog` lista toda skill `enabled`) | 🟡 **FIND-SKILL17** |
| **`invoked_skills`** (supervivencia a compactación): `STATE.invokedSkills` keyed `${agentId}:${name}` → "were invoked … Continue to follow" | ✅ **concepto homologado**: `active_skills` en `caps` (scoped por ctx) + `active_context`/`compact_context` "continúa siguiendo" | ✅ 🔀 **FIND-SKILL10** |
| `clearInvokedSkills(preservedAgentIds)` en compactación (preserva agentes vivos) | 🟡 (limpia por ctx; falta cleanup selectivo por agent + `skillPath`) | 🟡 (nexo 05·ExR6/08·SR3) |
| `dynamic_skill` attachment (informativo, render `[]`) | ❌ | ⛔/❌ (ver FIND-SKILL12) |
| Prompt de la tool (`BLOCKING REQUIREMENT`, "NEVER mention without calling", "already loaded via COMMAND_NAME", "not for built-in CLI") | 🟡 (description one-liner) | 🟡 **FIND-SKILL18** |

## F · Slash-commands + resolución (`commands.py` vs motor de `commands.ts` + `findCommand`)

| Feature canónica | Runtime | Estado |
|---|---|---|
| Parseo `/<cmd> [args]` tolerante | ✅ `parse_slash_command` | ✅ |
| Slash-command desacoplado del loop (activa inline en el ctx, devuelve instrucciones) | ✅ `process_slash_command` | ✅ (buen desacople) |
| **`findCommand` por `name` \| `getCommandName` (namespaced `ns:cmd`) \| `aliases`** | ❌ (`state.get(name)` exacto) | ❌ **FIND-SKILL16** |
| Fork/bg NO lo decide la skill sino el runtime (para slash) | ✅ (documentado en `commands.py`) — pero la **tool** SÍ forkea en canónico (D) | 🔀 |
| Motor `getCommands`/`loadAllCommands` (merge de fuentes + dynamic + dedup + orden) | 🟡 (catálogo plano por nombre) | 🟡 (subsume FIND-SKILL1) |
| `builtInCommandNames` / comandos `local`/`local-jsx` (101 defs UI) | N/A | ⛔ (TUI/producto) |
| `REMOTE_SAFE`/`BRIDGE_SAFE`/`isBridgeSafeCommand`/`meetsAvailabilityRequirement` | N/A | ⛔ (remote/bridge/auth de producto) |

## G · Permisos (Deuda-B) — **gate de SkillTool ausente**

| Feature canónica | Runtime | Estado |
|---|---|---|
| `checkPermissions`: **deny rules** por contenido (exact + `:*` prefix) | ❌ (`requires_permission=False`) | ❌ **FIND-SKILL5** (=GAP-SKILL1 / Deuda-B) |
| **allow rules** por contenido | ❌ | ❌ FIND-SKILL5 |
| **Auto-allow sólo si `skillHasOnlySafeProperties`** (allowlist `SAFE_SKILL_PROPERTIES`; propiedad no-safe con valor → pide permiso) | ❌ (auto-allow universal) | ❌ FIND-SKILL5 |
| Default **`ask`** con `suggestions` (exact + `:*`) + `metadata:{command}` | ❌ | ❌ FIND-SKILL5 |
| `is_deferred` de SkillTool = false (la necesita para activar skills); MCP-prompts SÍ diferidas | ✅ (`SkillTool` no diferida) | ✅ (coherente con 09·TiR5/GAP-TOOL3) |

## H · Descubrimiento dinámico / condicional / hot-reload / hooks / ranking / bundled

| Feature canónica | Runtime | Estado |
|---|---|---|
| **Skills condicionales por `paths`**: `conditionalSkills`, `activateConditionalSkillsForPaths` (`ignore`-lib, relativo a cwd), `activatedConditionalSkillNames` | ❌ | ❌ **FIND-SKILL12** |
| **Descubrimiento dinámico**: `discoverSkillDirsForPaths` (walk-up desde archivos tocados hasta cwd, gitignore guard), `addSkillDirectories` (deepest-wins), `dynamicSkills`, `getDynamicSkills` | ❌ | ❌ FIND-SKILL12 (=GAP-SKILL3: necesita hook post-Read/Write/Edit) |
| Señal `skillsLoaded`/`onDynamicSkillsLoaded` (invalidación de caché sin ciclos de import) | ❌ | ❌ (nexo 08·signals) |
| **Hot-reload FS**: `skillChangeDetector` (chokidar / polling-Bun, debounce 300ms, `awaitWriteFinish`), dispara **ConfigChange hook** (`executeConfigChangeHooks('skills')`) antes de limpiar cachés, `skillsChanged` signal, `resetSentSkillNames` | ❌ (register/unregister programático, sin watcher) | 🔀 **FIND-SKILL13** (el runtime long-running refresca por API; falta ConfigChange hook — nexo 06) |
| **Skill hooks** (`registerSkillHooks`): frontmatter `hooks` → session hooks (`addSessionHook`, `once:true` auto-remove, `CLAUDE_PLUGIN_ROOT`=skillRoot) | ❌ (no se parsean hooks) | ❌ **FIND-SKILL11** (nexo 06·hooks) |
| **Ranking de uso**: `recordSkillUsage` (debounce 60s → `globalConfig.skillUsage`), `getSkillUsageScore` (half-life 7d, piso 0.1) | ❌ | ❌ **FIND-SKILL14** (nexo 13·memory `rank_memories`) |
| **Bundled skills programáticos**: `registerBundledSkill` (name/desc/whenToUse/argHint/allowedTools/model/disableModelInvocation/userInvocable/`isEnabled()`/hooks/context/agent/`files`) | ❌ (no hay bundled) | ❌ **FIND-SKILL15** (mecanismo; contenido de los 15 = ⛔) |
| Extracción de `files` a disco (lazy, memo por proceso, `getBundledSkillExtractDir` nonce, `O_NOFOLLOW\|O_EXCL`, `0o600`, `resolveSkillFilePath` anti-traversal, `prependBaseDir`) | ❌ | ❌ FIND-SKILL15 |
| Auto-mejora de skills (`skillImprovement`: post-sampling cada 5 turnos, LLM reescribe SKILL.md) | ❌ | ⛔ (producto, gated `SKILL_IMPROVEMENT`+flag) |

## I · MCP skills / prompts (**FIND-MCP16 aterriza aquí**)

| Feature canónica | Runtime | Estado |
|---|---|---|
| **MCP prompts** → slash-commands `mcp__<server>__<prompt>` (`isMcp:true`, **diferidos**; no invocables por SkillTool salvo si adivina el nombre — bloqueado por el filtro) | ❌ | ❌ **FIND-MCP16** |
| **MCP skills** → comandos `<server>:<skill>` (`loadedFrom:'mcp'`, invocables por SkillTool) construidos vía `getMCPSkillBuilders().createSkillCommand` (registry write-once en `mcpSkillBuilders.ts`) | ❌ | ❌ FIND-MCP16 |
| `getMcpSkillCommands` = `prompt && loadedFrom==='mcp' && !disableModelInvocation` (gate `feature('MCP_SKILLS')`) | ❌ | ❌ FIND-MCP16 |
| `getAllCommands` (SkillTool) = local + `uniqBy([...local, ...mcpSkills],'name')` | ❌ | ❌ FIND-MCP16 |
| Distinción `commandBelongsToServer` (dos formas: `mcp__srv__prompt` vs `srv:skill`; distinguidor = `loadedFrom==='mcp'`) | ❌ | ❌ FIND-MCP16 |
| **Seguridad**: skills MCP nunca ejecutan bash-injection (`loadedFrom!=='mcp'` gate en `getPromptForCommand`) | N/A (runtime no ejecuta bash aún — FIND-SKILL4) | ❌ (a portar junto con FIND-SKILL4) |

---

## Hallazgos (IDs para retoma)

- **FIND-SKILL1** — Una sola fuente de skills. Falta: fuentes con precedencia (managed/user/project-up-to-home/additional/legacy/plugin/bundled/mcp), dedup por realpath, setting-source/plugin-only gating.
- **FIND-SKILL2** — Frontmatter reducido: faltan `when_to_use` (≠ description), `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `hooks`, `context`, `agent`, `effort`, `shell`, `paths`.
- **FIND-SKILL3** — Un solo eje `enabled` conflaciona `user-invocable` (typeable) y `disable-model-invocation` (invocable por el modelo), que son ortogonales; falta `isHidden`.
- **FIND-SKILL4** — `render_skill` ignora `args` y no substituye `$ARGUMENTS`/`$N`/`${CLAUDE_SKILL_DIR}`/`${CLAUDE_SESSION_ID}` ni ejecuta bash-injection `!\`…\`` (con su gate anti-MCP). Funcional + seguridad.
- **FIND-SKILL5** — SkillTool sin gate de permisos (`requires_permission=False`): auto-allow universal. Canónico = deny/allow-rules + auto-allow-safe-properties + ask-con-suggestions. **=GAP-SKILL1 / Deuda-B permisos.**
- **FIND-SKILL6** — La tool `Skill` no despacha a fork (`context:fork`→`runAgent`); el runtime delega todo fork al runtime. Nexo 05·execution / `agent`.
- **FIND-SKILL7** — `context_modifier` no aplica model-override (con carry `[1m]`) ni effort-override.
- **FIND-SKILL8** — Entrega vía `output` string en vez de `newMessages` transitorios + tool_result mínimo. Nexo B-new_messages / 07·EVT.
- **FIND-SKILL9** — `catalog()` re-emite TODO el catálogo cada turno; canónico = `skill_listing` incremental por-agente (delta `sentSkillNames`) + budget (1%/250char/bundled-sin-truncar) + skip-si-no-Skill-tool + reset/suppress.
- **FIND-SKILL10** — invoked_skills homologado en concepto (`active_skills`+`active_context`/`compact_context`); matiz: canónico usa estado global keyed por `agentId` con `skillPath` + cleanup selectivo (`clearInvokedSkills(preserved)`).
- **FIND-SKILL11** — Skill hooks del frontmatter (`hooks`→session hooks, `once:true`) no portados. Nexo 06·hooks.
- **FIND-SKILL12** — Sin skills condicionales (`paths`) ni descubrimiento dinámico (walk-up desde archivos tocados). **=GAP-SKILL3.**
- **FIND-SKILL13** — Sin hot-reload FS (`skillChangeDetector` + ConfigChange hook + `skillsChanged` signal). Comportamiento cubierto parcialmente por register/unregister API.
- **FIND-SKILL14** — Sin ranking de uso (`recordSkillUsage`/`getSkillUsageScore` half-life 7d). Nexo 13·memory.
- **FIND-SKILL15** — Sin bundled skills programáticos (`registerBundledSkill`) ni extracción de `files` a disco con guardas. Contenido de los 15 bundled = ⛔.
- **FIND-SKILL16** — Resolución de comando exacta por nombre: falta aliases, nombre namespaced (`ns:cmd`), strip-leading-slash.
- **FIND-SKILL17** — `catalog` lista toda skill `enabled`; canónico filtra por `getSkillToolCommands` (excluye sin descripción explícita salvo fuentes auto-descritas + excluye `disableModelInvocation`/`builtin`).
- **FIND-SKILL18** — Prompt de la tool `Skill` pobre vs el canónico (BLOCKING REQUIREMENT / never-mention / already-loaded / not-builtin).
- **FIND-SKILL19** — El prompt de una skill lo produce un **callable async con acceso al `ToolUseContext`** (`getPromptForCommand(args, ctx)`): lee session-memory (skillify), archivos+red (schedule/debug/claude-api), parsea args y ramifica (updateConfig `[hooks-only]`, loremIpsum), y tiene efectos secundarios (debug habilita logging). El runtime almacena `instructions` (markdown estático) y `render_skill` sólo antepone/anexa — no puede modelar un proveedor de prompt dinámico. **Destapado en la re-auditoría al ABRIR los bundled que la 1ª pasada marcó ⛔ por grep.**
- **FIND-MCP16** — MCP prompts (`mcp__srv__prompt`, isMcp, diferidos) y MCP skills (`srv:skill`, `loadedFrom:'mcp'`, invocables por SkillTool) no portados. Hogar confirmado en 12. **Integración leída en `client.ts:2171-2179`**: las MCP-skills se fetchean por-cliente (`fetchMcpSkillsForClient`) **sólo si `feature('MCP_SKILLS') && supportsResources`** — están respaldadas en *resources* del server — y se concatenan a `.mcp.commands` junto a los prompts (`commands=[...mcpCommands, ...mcpSkills]`). El módulo constructor `skills/mcpSkills.ts` **no está vendorizado en este checkout** (gated `MCP_SKILLS`, como el transporte SDK en 11) — se documenta como no-leíble, no se infiere su interior.

### Gaps con ID
- **GAP-SKILL1** = FIND-SKILL5 = Deuda-B permisos (gate de SkillTool).
- **GAP-SKILL2** = coherencia `is_deferred` de SkillTool vs MCP-prompts (nexo 09·TiR5/GAP-TOOL3) — **resuelto de diseño**: SkillTool no diferida; MCP-prompts diferidas; MCP-skills invocables por SkillTool no diferidas.
- **GAP-SKILL3** = FIND-SKILL12 requiere el seam de **evento post-tool de file-ops** (Read/Write/Edit) para disparar descubrimiento/activación condicional (nexo 10·native + 06/07).

### Cabos que ENTRARON (de subsistemas previos) y su resolución
- **11·FIND-MCP16** (prompts MCP→slash-commands + skills `skill://`/`srv:skill`): **hogar confirmado aquí** (sección I). El seam es `mcpSkillBuilders.ts` (registry write-once de `createSkillCommand`/`parseSkillFrontmatterFields`) consumido por el discovery MCP; `getMcpSkillCommands`/`getAllCommands` los mergean.
- **Relación commands MCP** (`commandBelongsToServer`, dos formas): **resuelto** — `mcp__<server>__<prompt>` (`isMcp`) es un *prompt* (diferido, no-skill); `<server>:<skill>` (`loadedFrom==='mcp'`) es una *skill* (invocable por SkillTool). El distinguidor es `loadedFrom`.
- **Deferral/`is_deferred`/`always_load` que toca SkillTool** (09·TiR5/GAP-TOOL3): **resuelto** — la tool `Skill` NO es diferida (el modelo la necesita para activar skills). Las MCP-prompts sí. Coherente con la superficie `ToolProtocol.is_deferred`.
- **invoked_skills / cleanup por agent_id** (05·ExR6 / 08·SR3): **confirmado** — `clearInvokedSkills(preservedAgentIds)` es el mismo patrón de cleanup por `agent_id` que el de MCP (11·McR12); el runtime debe portarlo junto con el cierre de fork.

## Recuento
✅ **~13** (formato dir, aislamiento por-ítem, orden estable, frontmatter tolerante, base_dir, allowed-tools→allow+discovered, active_skills/compactación concepto, slash-command desacoplado, store inyectable+startup, unregister-en-vivo, SkillTool no-diferida, model=inherit→None, version) · 🟡 **~9** (validateInput parcial, getSkillToolCommands filtro, model sin parse/[1m], displayName, cleanup-por-agent, entrega, prompt, motor-plano, campo `command` vs `skill`) · 🔀 **~4** (entrega output-vs-newMessages, hot-reload, legacy-commands, fork-en-runtime-vs-tool) · ❌ **~20** (FIND-SKILL1,2,3,4,5,6,7,9,11,12,14,15,16,17,18,**19** + FIND-MCP16 + sub-ítems) · ⛔ **~7** (UI.tsx, SkillsMenu, `/skills` slash, useSkillsChange, bundled-como-contenido, skillImprovement, EXPERIMENTAL_SKILL_SEARCH). **20 findings** (19 en la 1ª pasada + **FIND-SKILL19 destapado en la re-auditoría** al abrir los bundled marcados ⛔ por grep). Lo vinculante son los IDs FIND-SKILL/GAP-SKILL y los cabos.

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09) · 2026-07-20

> Método: para CADA fila **✅/🔀** se abrió la **implementación de B** que reproduce el comportamiento y se
> siguió el dato de punta a punta por el **ENSAMBLADOR** (no la tabla, L09/L11). Las ❌ convergen por lectura
> directa de B (campo ausente = ausente). Lado B leído 1→EOF esta ronda: `provider.py` 182 (el más grande, L08),
> `skill_tool.py` 123, `loader.py` 123, `frontmatter.py` 115, `store.py` 71, `commands.py` 67, `state.py` 39,
> `__init__.py` 34. **Ensamblador** leído esta ronda: `factory.py` **1→267 íntegro** (3 lecturas contiguas 1-119
> + 120-234 + 234-267), `capabilities/manager.py` **1→112 íntegro**, `loop/agent_loop.py` **cuerpo 85-352 contiguo**
> (`_build_tool_pool`/`_inject_recall`/`run` + turno + llamada al modelo 235-282 + tool-loop 283-352; el head 1-84
> —imports/`__init__`— íntegro en rondas 02/05/09/10). grep = sólo orientación / prueba de AUSENCIA.
>
> **RE-VERIFICACIÓN DE A 1→EOF (2ª corrección del cierre — reproche "no has vuelto a leer A", 2026-07-20).**
> Mi 1er cierre declaró "A NO re-abierto por diseño" apoyándose en "la 1ª vuelta lo leyó ×2" — **exactamente la
> racionalización que L11 prohíbe** (tratar el ledger previo como ancla fiable) y el mismo fallo que 11. Corregido:
> **re-leído TODO el árbol A in-scope 1→EOF ESTA ronda**, priorizando los grandes (L08), cotejando cada ✅/🔀/❌ y
> cada cita de línea del doc contra el código real de A:
> - `tools/SkillTool/SkillTool.ts` **1108 1→EOF** — `checkPermissions` deny/allow/`:*`-prefix/safe-properties/ask+
>   suggestions (432-577 → FIND-SKILL5), `SAFE_SKILL_PROPERTIES` (875-908, incluye `getPromptForCommand` → SKILL19),
>   `validateInput` strip-slash/disable-model/type-prompt (354-430 → SKILL16/3), `call` fork-dispatch `context===
>   'fork'` (622 → SKILL6), `processPromptSlashCommand(args)` (638), `contextModifier` allowedTools+model`[1m]`
>   (`resolveSkillModelOverride` 815)+effort (775-838 → SKILL4/7), `mapToolResult` "Launching skill:" mínimo +
>   `newMessages` transitorios `tagMessagesWithToolUseID` (735/843-862 → SKILL8), `getAllCommands` MCP-merge `uniqBy`
>   (81-94 → MCP16), `executeForkedSkill` `clearInvokedSkillsForAgent` en `finally` (287 → SKILL10). `executeRemoteSkill`
>   (969-1108) = ⛔ EXPERIMENTAL, abierto y confirmado (sustitución `${CLAUDE_SKILL_DIR}`/`${CLAUDE_SESSION_ID}` 1077-1081).
> - `skills/loadSkillsDir.ts` **1086 1→EOF** — `parseSkillFrontmatterFields` los 16 campos (185-265: when_to_use/
>   argument-hint/arguments/disable-model-invocation/user-invocable/hooks/context/agent/effort/shell → SKILL2/3/7),
>   `createSkillCommand.getPromptForCommand` **callable async ctx-aware** + `substituteArguments` + `${CLAUDE_SKILL_DIR}`
>   + `${CLAUDE_SESSION_ID}` + `executeShellCommandsInPrompt` gated `loadedFrom!=='mcp'` (344-399 → SKILL19/4), 5
>   fuentes+precedencia+gating (getSkillDirCommands 638-804 → SKILL1), dedup `getFileIdentity`/realpath (118-124/736-763),
>   condicionales `activateConditionalSkillsForPaths` + dinámicas `discoverSkillDirsForPaths` walk-up+gitignore + señal
>   `skillsLoaded` (861-1058 → SKILL12), `registerMCPSkillBuilders` write-once (1083 → MCP16).
> - `commands.ts` **754 1→EOF** — `getSkillToolCommands` filtro elegibilidad (563-581 → SKILL17), `getMcpSkillCommands`
>   `prompt&&loadedFrom==='mcp'&&!disableModelInvocation` (547-559 → MCP16), `findCommand` name|namespaced|aliases
>   (688-698 → SKILL16), motor `getCommands`/`loadAllCommands` merge+dynamic+dedup+orden (449-517 → SKILL1),
>   REMOTE/BRIDGE_SAFE ⛔ (619-686, abiertos).
> - `tools/SkillTool/prompt.ts` **241 1→EOF** — budget 1% (`SKILL_BUDGET_CONTEXT_PERCENT`)/`MAX_LISTING_DESC_CHARS`250/
>   bundled-nunca-truncado/modos names_only+description_trimmed (21-171 → SKILL9), prompt BLOCKING/never-mention/
>   already-loaded/not-builtin (173-196 → SKILL18), `desc - whenToUse` (44 → SKILL2).
> - `skills/bundledSkills.ts` **220 1→EOF** — `registerBundledSkill` + `BundledSkillDefinition` (isEnabled callable/
>   files/context/agent/getPromptForCommand) + extracción lazy memo `O_NOFOLLOW|O_EXCL`/0o600/0o700/`resolveSkillFilePath`
>   anti-traversal/`prependBaseDir` (15-220 → SKILL15).
> - `skills/mcpSkillBuilders.ts` **44 1→EOF** — registry write-once (→ MCP16). `utils/hooks/registerSkillHooks.ts`
>   **64 1→EOF** — hooks→session-hooks+`once:true`auto-remove+`CLAUDE_PLUGIN_ROOT` (→ SKILL11).
>   `utils/suggestions/skillUsageTracking.ts` **55 1→EOF** — debounce 60s+half-life 7d+piso 0.1 (→ SKILL14).
>   `utils/skills/skillChangeDetector.ts` **311 1→EOF** — chokidar/polling-Bun+debounce 300ms+`executeConfigChangeHooks
>   ('skills')`+`resetSentSkillNames` (→ SKILL13). `tools/SkillTool/constants.ts` 1 (`SKILL_TOOL_NAME='Skill'`).
> - **Satélites de OTRAS categorías (L07), NO re-leídos íntegros esta ronda** (porción-skill leída en 1ª vuelta+
>   belt-and-suspenders, con destino nombrado): `utils/attachments.ts` (skill_listing/sentSkillNames → 07·events),
>   `bootstrap/state.ts` (invokedSkills → 01/compact), `utils/messages.ts` (skill renderers → 07), `services/mcp/
>   client.ts` (2160-2199 fetch MCP-skills → 11, ya 1→EOF en 11), `services/mcp/utils.ts` (naming → 11), `bundled/*.ts`
>   (17, ⛔ contenido, abiertos 1ª vuelta), UI/SkillsMenu/`/skills`/useSkillsChange/skillImprovement (⛔, abiertos).
>
> **Resultado de la re-verificación de A: CERO discrepancias, ninguna ❌ falsa, ningún comportamiento A omitido; las
> citas de línea del doc coinciden EXACTAS con el código** — evidencia de lectura real (L11), no herencia del ledger.
>
> **Corrección de honestidad (gate auto-adversarial del usuario, 2026-07-20).** Mi 1er cierre de esta ronda
> **sobre-declaró "ensamblador 1→EOF"**: había leído `factory.py` por el tramo 120-234 y `agent_loop.py` por
> 85-234+283-352, dejando **sin leer `factory.py`:1-119/235-267 y `agent_loop.py`:235-282** — y la precisión
> FIND-SKILL9 ("`catalog()` no cableado al modelo") se apoyaba en un **grep de ausencia** + lectura parcial del
> loop. Al reproche, LEÍ los tramos faltantes: `agent_loop.py:235-282` **es la región de la llamada al modelo**
> (`complete(ctx.messages, tool_schemas, **complete_kwargs)` 235-239) y **NO inyecta `catalog()` ni skill_listing**
> — el modelo ve skills sólo por la tool `Skill` (en `tool_schemas`) + los recordatorios de skills activas ya
> insertados en `ctx.messages` por `_inject_recall` (218). ⇒ **la precisión FIND-SKILL9 se CONFIRMA por LECTURA
> del tramo antes omitido, no por grep** (grep sólo probó la ausencia de caller de `manager.catalog`, legítimo por
> L01/L09; la conclusión de cableado la da ahora la lectura de 235-282). Modo de fallo L08 reincidente ("abierto
> por tramos ≠ íntegro"); cerrado.

### Mini-ledger de consumidores (cómo se cablea cada ✅/🔀 al modelo)
| Comportamiento (✅/🔀) | Consumidor real en B (leído) | Veredicto |
|---|---|---|
| `SkillsProvider` ensamblado | `factory._build_capability_manager:160-164` (`if caps.skill_dirs or caps.skill_store` → `SkillsProvider(skill_store=…)` + `load_dir(root)` → `providers.append`) → `CapabilityManager(providers)` (:175) → `runtime._capability_manager` (`_build_local:194→221`) | ✅ cableado (MISMA instancia root+subagentes, `runtime.py:358`) |
| **Tool `Skill` por turno** | `agent_loop.py:194-200` `_build_tool_pool`→`manager.build_tool_pool`(manager.py:61-79)→`manager.tools`(50-59)→`SkillsProvider.tools`(provider.py:144-151)→`[SkillTool]` sii ≥1 enabled | ✅ **reensamblado per-turno** (hermano exacto de MCP 11: `for _turn in range(_MAX_TURNS)` → pool nuevo cada iteración) |
| `context_modifier`: allowed-tools→allow + mark_discovered | `skill_tool.py:119` set en `result.context_modifier` → **APLICADO en el loop** `agent_loop.py:332-337` (`modifier(ctx)`); `build_skill_context_modifier` (skill_tool.py:47-64) muta `permissions.with_command_allow` + `mark_tools_discovered` | ✅ cableado (no sólo atributo) |
| `active_skills` / invoked_skills (S3/S5) | `skill_tool.py:53-58` puebla `caps['active_skills']` → `_inject_recall` `agent_loop.py:218/112-130`→`manager.active_context`(manager.py:98-102)→`SkillsProvider.active_context`(provider.py:153-179) **cada turno**, dedup contra historia | ✅ cableado per-turno |
| slash-command desacoplado (S4) | `commands.py:32-64` `process_slash_command`→`build_skill_context_modifier(skill)(ctx)`+`render_skill` | ✅ (seam del integrador; el loop NO lo importa — provider.py:80-85) |
| store inyectable + `startup()` rehidrata | `store.py` + `provider.startup` (110-126) ← `manager.startup`(manager.py:36-38) ← `runtime.py:123-124` | ✅ cableado |
| unregister en vivo | `provider.unregister`(95-106)+`state.remove`(state.py:27) | ✅ (seam del integrador) |

### 2 PRECISIONES de mecanismo (leyendo el ensamblador — NO voltean estado)
1. **FIND-SKILL9 — el mecanismo del doc es IMPRECISO (código intacto, ❌ intacto).** El doc dice "`catalog()`
   **re-emite TODO el catálogo cada turno**". Al leer el ensamblador: el **único** consumidor de prod de
   `SkillsProvider.catalog()` es `CapabilityManager.catalog()` (manager.py:47) — y `manager.catalog()` **NO tiene
   ningún caller de producción** (grep `\.catalog(`: sólo `tests/*`). Lo que el loop SÍ rinde al modelo por turno
   es: (a) la **tool `Skill`** (vía `tools()`) y (b) los recordatorios de **skills activas** "continue to follow"
   (vía `active_context`/`_inject_recall`) — **nunca** el catálogo/listing. ⇒ `catalog()` es una **costura de
   consumo del integrador / introspección** (hermana de `stream()`/`subscribe_all` 07, `HookRunner.register` 06),
   **no** un surface per-turno al modelo. **El ❌ vs canónico SE SOSTIENE** (el canónico tiene `skill_listing`
   incremental+budget; el runtime **no surface ningún listing de skills al modelo en el standalone** — el modelo
   sólo ve la tool `Skill` + su description one-liner; el gap es, si acaso, **MAYOR** que "re-emite todo cada
   turno", no menor). Corrección de mecanismo: "catalog() no cableado al modelo en el standalone (seam de
   integrador)", NO "re-emitido cada turno". Hermana de las precisiones de cableado de 07/08/09/11 ("conclusión de
   cableado = leer el ensamblador, nunca grep para lo positivo").
2. **FIND-SKILL7 — `skill.model` se ALMACENA pero no se aplica.** `build_skill_context_modifier` guarda
   `skill.model` en `active_skills[name]['model']` (skill_tool.py:56) pero **ningún prod lo lee** para overridear
   el modelo/effort del turno (el modifier sólo toca `permissions`, no `app_state.model`/`effort`). Es la cara
   B-interna del ❌ FIND-SKILL7 (no override) — no lo voltea, lo precisa.

### 1 COSTURA LATENTE NUEVA — LAT-SKILL1 (tech-debt B-interno, NO deuda A↔B, anti-padding L10/L11)
- **`SkillTool.input_schema` anuncia `args` que `execute()` DESCARTA.** El schema declara la propiedad `args`
  (skill_tool.py:83-89) pero `execute()` lee **sólo** `input.get("command")` (skill_tool.py:108) y `render_skill`
  no acepta `args` (skill_tool.py:18) — el `args` anunciado se **descarta en silencio**. Costura a medio cablear:
  la tool promete en su PROPIO schema un manejo de args que no entrega. **Hermana de** `to_llm`/`category`/
  `timeout_seconds`/LAT-EXEC1/LAT-HOOK1/LAT-TOOL1/LAT-MCP1 → **DEUDA-B §B-orphans / seams a medio cablear**. Es la
  superficie B-interna de **FIND-SKILL4** (cuyo gap A↔B — sin substitución `$ARGS`/`$N`/vars ni bash-injection —
  **se sostiene ❌**); lo latente es la **inconsistencia interna** (el schema anuncia, `execute` ignora), gemela
  del announce singular de 09·FIND-TOOL6. Remediación = SkR3 (que introduce `render_skill(skill, args, ctx)`).

### ❌ que CONVERGEN por lectura directa de B (confirmadas, ninguna falsa)
`frontmatter.py` define **exactamente 6** campos (`name`/`description`/`allowed_tools`/`model`/`enabled`/`version`)
⇒ **FIND-SKILL2** (faltan `when_to_use`/`argument-hint`/`arguments`/`disable-model-invocation`/`user-invocable`/
`hooks`/`context`/`agent`/`effort`/`shell`/`paths`) + **FIND-SKILL3** (un solo eje `enabled` conflaciona los dos
ortogonales) confirmados. `render_skill` estático sin callable ⇒ **FIND-SKILL19**. `requires_permission=False`
(skill_tool.py:92) ⇒ **FIND-SKILL5**. `execute` inline sin rama fork ⇒ **FIND-SKILL6**. `state.get` exacto
(state.py:24) sin aliases/namespaced/strip-slash ⇒ **FIND-SKILL16**. `catalog` filtra sólo por `is_enabled`
(provider.py:140-142) y usa `when_to_use=description` (:137) ⇒ **FIND-SKILL17** + confirma la conflación de
FIND-SKILL2. Sin `record_skill_usage`/bundled/paths/hooks-parse ⇒ SKILL14/15/12/11. Sin `loaded_from`/merge MCP ⇒
**FIND-MCP16**. `result.output = render_skill(...)` completo (skill_tool.py:118) → `role:"tool"` message
(agent_loop.py:319-323), sin `new_messages` ⇒ **FIND-SKILL8** 🔀. `active_skills` dict sin `path`/`invoked_at`
(skill_tool.py:53-58) ⇒ **FIND-SKILL10** matiz. Ninguna ❌ resultó falsa.

### §Honestidad
- La 2ª pasada de la 1ª vuelta ya leyó A+B íntegros (post-reproche del troceo/grep; belt-and-suspenders 2026-07-14
  re-leyó `SkillTool.ts` 1108 + `loadSkillsDir.ts` 1086 1→EOF). El **value-add del gate 11 fue abrir el
  ENSAMBLADOR** (`factory`+`manager`+`loop`), invisible sin él — y ahí apareció la precisión de que `catalog()`
  **no está cableado al modelo** (la 1ª pasada asumió "re-emite cada turno" sin seguir el consumidor, exactamente
  el modo de fallo que L09 caza) + LAT-SKILL1.
- **El lado A SÍ se re-leyó 1→EOF esta ronda** (2ª corrección, reproche "no has vuelto a leer A"): mi 1er cierre
  dijo "A no re-abierto por diseño" apoyándose en el ledger previo = fallo L11 idéntico a 11. Corregido: los 10
  archivos A in-scope re-leídos 1→EOF ESTA ronda (los 3 grandes 1108/1086/754 + 6 satélites portadores de hallazgo
  + constants), cotejando cada cita de línea — CERO discrepancias, citas exactas (ver bloque "RE-VERIFICACIÓN DE A
  1→EOF"). Los satélites de OTRAS categorías (attachments/messages/state/client → 07/01/11) quedan L07 con destino.
- Auto-corrección de método interiorizada (idéntica a 07/09/11): conclusión de cableado = **leer el ensamblador
  1→EOF**; grep sólo orienta o prueba **ausencia** (los 0-consumidores de `catalog()`/`args` sí legítimos por grep,
  corroborados leyendo `factory`/`manager`/`loop`).
- **2ª auto-corrección (mismo reproche, 2026-07-20)**: mi 1er cierre de esta ronda dijo "ensamblador 1→EOF"
  habiéndolo leído **por tramos** (factory 120-234; loop 85-234+283-352) y apoyando FIND-SKILL9 en grep+lectura
  parcial. Cerrado leyendo los tramos omitidos (`factory` 1-119/235-267 + `agent_loop.py:235-282`): la región de la
  llamada al modelo **NO surface el catálogo** ⇒ FIND-SKILL9 confirmado por LECTURA, no grep. Ver el bloque de
  corrección al inicio de esta §. L08 ("abierto por tramos ≠ íntegro") reincidente.

### 4 preguntas de cierre (2ª vuelta)
1. ¿Se revisó **todo** cada archivo de **A**? **sí, y re-leído 1→EOF ESTA ronda tras el reproche** (los 10
   in-scope: SkillTool.ts 1108, loadSkillsDir.ts 1086, commands.ts 754, prompt.ts 241, bundledSkills.ts 220,
   skillChangeDetector.ts 311, registerSkillHooks.ts 64, skillUsageTracking.ts 55, mcpSkillBuilders.ts 44,
   constants.ts 1) — cero discrepancias, citas exactas. Satélites de otras categorías (attachments/messages/state/
   client/mcp-utils → 07/01/11; bundled/*.ts ⛔) L07 con destino. **El 1er cierre dijo "A no re-abierto por
   diseño" = fallo L11; corregido.**
2. ¿Se revisó **todo** cada archivo de **B**? **sí, esta ronda** (los 8 `skills/*.py` 1→EOF + ensamblador:
   `factory.py` 1→267 íntegro, `manager.py` 1→112 íntegro, `agent_loop.py` cuerpo 85→352 contiguo + head 1-84 de
   rondas previas). **Nota: el 1er cierre lo leyó por tramos y se corrigió tras el reproche** (ver bloque de
   corrección de honestidad); ahora íntegro.
3. ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **sí** — cada ✅/🔀 abierta en B por cableado; 2
   precisiones de mecanismo + LAT-SKILL1 destapados al leer el ensamblador; ninguna ❌ falsa.
4. ¿Quedó **todo cubierto (nada pendiente)**? **sí** — cabos (FIND-MCP16, cleanup-por-agent, is_deferred,
   new_messages) resueltos/anotados con destino; sin pendiente de verificación.

**VEREDICTO DE AVANCE: ✅ NADA PENDIENTE → avanzar a 13 · cap-memory.** (Código intacto, 0 cambios de estado;
LAT-SKILL1 → DEUDA-B §B-orphans; precisión FIND-SKILL9 = mecanismo, no estado.)

---

## Ledger de archivos (auditoría de cierre — protocolo obligatorio)

> **Nota de honestidad (re-auditoría tras reproche del usuario).** La **1ª pasada de este ledger fue superficial
> e incurrió en el modo de fallo #1** que 11 prohíbe: marcó **13 de los 15 `bundled/*.ts` como ⛔ por `grep`, sin
> abrirlos** (sólo leyó `index.ts` + 4), e **infirió el mecanismo de FIND-MCP16** sin leer el consumidor real.
> El usuario lo cuestionó con razón. La **2ª pasada ABRIÓ los 15 bundled** (register-blocks íntegros) y el
> consumidor MCP (`client.ts:2160-2199`). Resultado — exactamente el payoff de la re-auditoría:
> - **FIND-SKILL19 destapado**: `getPromptForCommand` es un **callable async, side-effecting, ctx-aware**
>   (skillify lee session-memory + mensajes post-compact; schedule hace red/auth; debug habilita logging y lee el
>   log; updateConfig/loremIpsum parsean args y ramifican). El grep-⛔ lo habría enviado como ausente.
> - **FIND-MCP16 refinado**: las MCP-skills están **respaldadas en resources** (`supportsResources` gate) y el
>   builder real `skills/mcpSkills.ts` **no está en el checkout** (gated) — antes se inferían.
>
> El ⛔ de contenido de los 15 bundled **resultó correcto** (no había coordinator/módulo oculto), pero el juicio
> sólo es legítimo **ahora que se abrieron**, no cuando se hizo por grep. Los dos archivos grandes
> (`loadSkillsDir.ts` 1086, `SkillTool.ts` 1108) sí se leyeron **íntegros de una** desde la 1ª pasada; de
> `attachments.ts`/`state.ts`/`messages.ts`/`commands.ts` se leyó íntegro lo relevante a skills (rango exacto).

### Canónico (`/home/noheroes/python/claude-code/src`) — TODOS abiertos
| Archivo | LOC | Lectura |
|---|---|---|
| `skills/loadSkillsDir.ts` | 1086 | **íntegro** (fuentes, frontmatter fields, createSkillCommand, dedup realpath, dynamic/conditional, señal) |
| `tools/SkillTool/SkillTool.ts` | 1108 | **íntegro** (getAllCommands, validate, checkPermissions, call inline+fork, safe-properties, remote⛔) |
| `tools/SkillTool/prompt.ts` | 241 | íntegro (budget/truncación, getPrompt, getSkillToolInfo) |
| `tools/SkillTool/constants.ts` | 1 | íntegro (`SKILL_TOOL_NAME='Skill'`) |
| `tools/SkillTool/UI.tsx` | 127 | íntegro → ⛔ (render ink result/use/progress/rejected/error) |
| `skills/mcpSkillBuilders.ts` | 44 | íntegro (registry write-once — hogar FIND-MCP16) |
| `skills/bundledSkills.ts` | 220 | íntegro (registerBundledSkill + extracción `files` con guardas) |
| `commands.ts` | 754 | íntegro (motor: getSkills/loadAllCommands/getCommands, getSkillToolCommands, getMcpSkillCommands, findCommand, dynamic merge) |
| `skills/bundled/index.ts` | 79 | íntegro (enumera las 15 registraciones) |
| `skills/bundled/{simplify,verify,loop,batch,remember,keybindings,updateConfig,skillify,scheduleRemoteAgents,debug,claudeInChrome,verifyContent,claudeApiContent,stuck,claudeApi,loremIpsum}.ts` | 13-475 | **íntegros / register-block íntegro → ⛔ contenido** (re-auditados abriéndolos tras el reproche del usuario; destaparon **FIND-SKILL19** = `getPromptForCommand` callable dinámico) |
| `services/mcp/client.ts` (integración MCP-skills) | 2160-2199 | comportamiento (fetch gated `MCP_SKILLS && supportsResources`, `commands=[...prompts, ...skills]`) |
| `skills/mcpSkills.ts` (builder MCP-skill real) | — | **no vendorizado** en el checkout (gated `MCP_SKILLS`) — documentado no-leíble, no inferido |
| `utils/skills/skillChangeDetector.ts` | 311 | íntegro (chokidar/polling, debounce, ConfigChange hook, signal) |
| `utils/hooks/registerSkillHooks.ts` | 64 | íntegro (frontmatter hooks → session hooks) |
| `utils/hooks/skillImprovement.ts` | 267 | íntegro → ⛔ (auto-mejora por LLM, gated) |
| `utils/suggestions/skillUsageTracking.ts` | 55 | íntegro (record/score half-life) |
| `hooks/useSkillsChange.ts` | 62 | íntegro → ⛔ (hook React de refresco) |
| `components/skills/SkillsMenu.tsx` | 236 | íntegro → ⛔ (diálogo `/skills`, agrupa por fuente + tokens) |
| `commands/skills/{index,skills.tsx}` | 7/7 | íntegros → ⛔ (`local-jsx` → SkillsMenu) |
| `utils/attachments.ts` (skill portions) | 2547-2751 + 82/86/271/525-539/646 | íntegro-comportamiento (getSkillListing/getDynamicSkill, sentSkillNames, filterToBundledAndMcp) |
| `bootstrap/state.ts` (invokedSkills) | 1502-1563 | íntegro (add/get/clear[ForAgent], InvokedSkillInfo) |
| `utils/messages.ts` (skill renderers) | 3644-3738 | íntegro (invoked_skills/dynamic_skill/skill_listing → system-reminder) |
| `services/mcp/utils.ts` (naming prompt-vs-skill) | 40-100 | comportamiento (distinción `mcp__srv__prompt` isMcp vs `srv:skill` loadedFrom mcp) |

**Genuinamente NO leídos (justificado, no por tamaño)**: `services/skillSearch/*` (EXPERIMENTAL_SKILL_SEARCH,
búsqueda semántica remota ant-only — ⛔ experimental; sus call-sites en `SkillTool.ts` sí leídos), `skills/bundled/{dream,hunter,runSkillGenerator}.ts` (registrados sólo bajo flags KAIROS/REVIEW_ARTIFACT/RUN_SKILL_GENERATOR — mismo patrón register-wrapper, ⛔ contenido), componentes ink de `components/*` (render puro).

### Runtime (`…/capabilities/skills`)
| Archivo | LOC | ¿Leído íntegro? |
|---|---|---|
| `__init__.py` | 34 | sí |
| `frontmatter.py` | 115 | sí |
| `loader.py` | 123 | sí |
| `state.py` | 39 | sí |
| `store.py` | 71 | sí |
| `commands.py` | 67 | sí |
| `skill_tool.py` | 123 | sí |
| `provider.py` | 182 | sí |

### Preguntas de cierre
- ¿Se revisó **todo** cada archivo canónico listado? **sí, tras la re-auditoría** (en la 1ª pasada NO: 13 bundled marcados ⛔ por grep + FIND-MCP16 inferido). La 2ª ABRIÓ los 15 bundled (register-blocks) + el consumidor MCP `client.ts:2160-2199`. Los dos grandes íntegros de una llamada; `commands.ts`/`prompt.ts`/`bundledSkills.ts`/`mcpSkillBuilders.ts`/`skillChangeDetector.ts`/`registerSkillHooks.ts`/`skillUsageTracking.ts`/`skillImprovement.ts` íntegros; `attachments.ts`/`state.ts`/`messages.ts`/`mcp/utils.ts` íntegros en su porción de skills (rango exacto); UI/SkillsMenu/`/skills`/useSkillsChange abiertos y confirmados ⛔. Lo genuinamente no-leíble: `skills/mcpSkills.ts` (no vendorizado, gated) + `services/skillSearch/*` (experimental) — justificado por producto/gating, no por tamaño.
- ¿Se revisó **todo** cada archivo runtime listado? **sí** (los 8 archivos ÍNTEGROS).
- ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **ahora sí** (la 1ª pasada NO — reconocido en la §honestidad). Se enumeran los 12 campos de frontmatter que faltan, el proveedor-de-prompt callable (**FIND-SKILL19, nuevo en la re-auditoría**), las substituciones + bash-injection, las 4 ramas del gate de permisos, el mecanismo incremental+budget del skill_listing (delta por agentId), las dos formas MCP (prompt vs skill) con su gate `supportsResources`, y el mecanismo de bundled+files. El ⛔ de bundled se evidenció **abriendo los 15**, no por grep.
- ¿Quedó **todo cubierto (nada pendiente)**? **sí** — cabos 11·FIND-MCP16, commandBelongsToServer, is_deferred/SkillTool, invoked_skills/cleanup-por-agent resueltos o confirmados; lo delegado (B-new_messages para la entrega, 06 para skill-hooks/ConfigChange, 05 para fork, 10/07 para el evento file-op de FIND-SKILL12, 13 para el patrón de ranking) anotado con destino.

**Cierre habilitado: las 4 respuestas = sí.**

---

## Plan de homologación / remediación desarrollada (Deuda A de 12)

> 1ª pasada = diseño. Cada SkR desarrolla la remediación de una vez: comportamiento · seam · firma · cableado ·
> orden · test. Los xfail(strict) codifican targets; passing = homologado.

### SkR1 · FIND-SKILL2 + FIND-SKILL3 — frontmatter completo + dos ejes de habilitación
- **Comportamiento**: `SkillFrontmatter` gana `when_to_use`, `argument-hint`, `arguments` (→`argument_names`), `disable-model-invocation`, `user-invocable`, `hooks` (dict crudo), `context` (`inline|fork`), `agent`, `effort`, `shell` (dict), `paths` (lista). `SkillDefinition` los propaga con defaults seguros. `enabled` se deriva: `user_invocable` (default true) y `disable_model_invocation` (default false) como ejes ortogonales; `is_hidden = not user_invocable`.
- **Seam**: `frontmatter.py` (campos + validators tolerantes por campo, coerción CSV/lista/bool), `loader.py` (`SkillDefinition` + `_parse_when_to_use`/`_parse_paths`).
- **Firma**: `SkillDefinition(..., when_to_use: str = "", argument_hint: str = "", argument_names: list[str] = [], disable_model_invocation: bool = False, user_invocable: bool = True, is_hidden: bool = False, hooks: dict | None = None, execution_context: str | None = None, agent: str | None = None, effort: str | None = None, shell: dict | None = None, paths: list[str] = [])`.
- **Cableado**: `default_is_enabled(skill)` = `not skill.disable_model_invocation` para la vía SkillTool (invocación del modelo); `user_invocable` gobierna la vía slash. `catalog`/`when_to_use` deja de reusar `description`.
- **Orden**: primero, base para SkR3/4/5/6/7/9/11.
- **Test**: `test_frontmatter_all_fields`, `test_user_invocable_vs_disable_model_invocation_orthogonal`, `test_when_to_use_separate_from_description`.

### SkR2 · FIND-SKILL1 — fuentes múltiples + precedencia + dedup
- **Comportamiento**: `load_sources([(root, source)…])` carga varias raíces con precedencia (policy < user < project(up-to-home) < additional < legacy), dedup por identidad de archivo (`os.path.realpath`) primero-gana, orden determinista.
- **Seam**: `loader.py::load_skills_sources` + `provider.load_dirs`. La precedencia por `source` es un enum ordenado.
- **Firma**: `load_skills_sources(sources: list[tuple[Path, SkillSource]]) -> list[SkillDefinition]`; `_dedup_by_realpath`.
- **Cableado**: el integrador provee las raíces (el runtime no asume `~/.claude`); el store sigue siendo una fuente más. Setting-source/plugin-only gating = responsabilidad del integrador (documentado).
- **Orden**: tras SkR1.
- **Test**: `test_source_precedence`, `test_dedup_symlinked_skill`, `test_isolation_per_item_multisource`.

### SkR3 · FIND-SKILL4 + FIND-SKILL19 — proveedor de prompt (callable) + substitución de args/vars + bash-injection
- **Comportamiento**: `SkillDefinition` gana un `prompt_provider: Callable[[str, ToolUseContext], Awaitable[str]] | None` (default = el markdown estático). `render_skill(skill, args, ctx)` invoca el provider (o usa `instructions`), luego substituye `$ARGUMENTS`/`$1..$N`/`$NAME` (con `argument_names`), `${CLAUDE_SKILL_DIR}` (normalizado), `${CLAUDE_SESSION_ID}`; luego, **si `skill.loaded_from != 'mcp'`**, ejecuta bash-injection `!\`…\`` / bloques ```! …``` con `allowed_tools` como allow-rules efímeras. El provider recibe el `ctx` (acceso a messages/memoria/mcp) y puede parsear args/ramificar/tener IO — el skill de disco usa el default estático; los bundled (SkR13) pueden inyectar un provider.
- **Seam**: nuevo `substitution.py` (`substitute_arguments`, `substitute_skill_vars`) + `skill_tool.render_skill` recibe `args`/`ctx`; el ejecutor de shell se inyecta por contrato (reusa el de 10·Bash / `promptShellExecution`).
- **Firma**: `render_skill(skill, args: str = "", ctx: ToolUseContext | None = None) -> str`; `substitute_arguments(text, args, argument_names) -> str`.
- **Cableado**: `SkillTool.execute` y `process_slash_command` pasan `args`+`ctx`. El gate MCP es un `if`.
- **Orden**: tras SkR1 (necesita `argument_names`); coordina con SkR8 (entrega).
- **Test**: `test_substitute_arguments`, `test_skill_dir_and_session_id_vars`, `test_bash_injection_gated_off_for_mcp`.

### SkR4 · FIND-SKILL5 (=GAP-SKILL1 / Deuda-B) — gate de permisos de SkillTool
- **Comportamiento**: `SkillTool` deja de auto-allow universal. `check_permission(input, ctx)` (contrato Deuda-B): deny-rules por contenido (exact + `:*` prefix), allow-rules, auto-allow sólo si `_skill_has_only_safe_properties`, si no `ask` con suggestions (exact + `:*`) + metadata `{command}`.
- **Seam**: `skill_tool.py` implementa el hook de permisos del contrato `PermissionContext` (mismo puerto que las tools nativas), + allowlist `SAFE_SKILL_PROPERTIES`.
- **Firma**: `SkillTool.requires_permission = True`; `async def check_permission(self, input, ctx) -> PermissionDecision`.
- **Cableado**: el dispatcher de tools (09) ya consulta el gate; SkillTool entra a él como cualquier tool. Ver DEUDA-B-transversal §B-02.
- **Orden**: independiente; alto valor (seguridad).
- **Test**: `test_skill_deny_rule`, `test_skill_allow_prefix_rule`, `test_skill_safe_properties_autoallow`, `test_skill_with_hooks_requires_permission`.

### SkR5 · FIND-SKILL7 — context_modifier: model + effort (+ carry [1m])
- **Comportamiento**: `build_skill_context_modifier` aplica, además de allowed-tools, override de `model` (resolviendo alias y preservando sufijo `[1m]`) y de `effort` en el `app_state`.
- **Seam**: `skill_tool.build_skill_context_modifier` + helper `resolve_skill_model_override(model, current)`.
- **Firma**: modifier muta `c.app_state` (model/effort) como ya hace con permissions.
- **Cableado**: consume `skill.model`/`skill.effort` de SkR1.
- **Orden**: tras SkR1.
- **Test**: `test_skill_model_override_carries_1m`, `test_skill_effort_override`.

### SkR6 · FIND-SKILL8 + FIND-SKILL18 — entrega vía new_messages + prompt de la tool
- **Comportamiento**: `SkillTool.execute` devuelve un `ToolResult` con `output` mínimo ("Launching skill: X") + `new_messages` transitorios (el SKILL.md expandido, tagged con el tool_use_id) en vez de meter el render como output. Prompt/description de la tool reescrito (BLOCKING REQUIREMENT / never-mention / already-loaded / not-builtin).
- **Seam**: `ToolResult.new_messages` (Deuda-B `B-new_messages`) + `skill_tool.py` description larga.
- **Firma**: `ToolResult(tool_name, output="Launching skill: …", new_messages=[…], context_modifier=…)`.
- **Cableado**: depende de que el loop consuma `new_messages` (B-new_messages / 07·EVT).
- **Orden**: tras B-new_messages; coordina con SkR3.
- **Test**: `test_skill_result_uses_new_messages`, `test_skill_tool_prompt_blocking_requirement` (xfail hasta B-new_messages).

### SkR7 · FIND-SKILL9 + FIND-SKILL17 — skill_listing incremental por-agente + budget + elegibilidad
- **Comportamiento**: el provider expone `skill_listing(ctx)` que emite **sólo skills nuevas** para el `agent_id` del ctx (estado `sent_skill_names` por agente), con `is_initial`, budget (1% de la ventana, 250 char/entrada, bundled sin truncar, fallback names-only), y **skip si el ctx no tiene la tool Skill**. Elegibilidad = `not disable_model_invocation && (auto-descrita | hasUserSpecifiedDescription | when_to_use)`. `reset_sent_skill_names` al cambiar el set.
- **Seam**: nuevo `listing.py` (`format_within_budget`, `SentSkillNames`) + `provider.skill_listing`. Reemplaza el uso de `catalog()` como entrega al modelo (catalog queda para introspección/UI).
- **Firma**: `skill_listing(ctx) -> list[dict]` (system-reminder incremental); `format_within_budget(skills, window_tokens) -> str`.
- **Cableado**: el integrador inyecta el listing como system-reminder por turno; `reset` se llama en register/unregister y en hot-reload.
- **Orden**: tras SkR1 (when_to_use/disable-model) y SkR2 (fuentes).
- **Test**: `test_skill_listing_delta_per_agent`, `test_skill_listing_budget_truncation`, `test_skill_listing_skipped_without_skill_tool`.

### SkR8 · FIND-SKILL10 — invoked_skills: skillPath + cleanup por agent
- **Comportamiento**: `active_skills` gana `path`/`invoked_at`; el runtime porta `clear_invoked_skills(preserved_agent_ids)` y `clear_invoked_skills_for_agent(agent_id)` (llamado al cerrar un fork y en compactación, preservando agentes vivos). `active_context`/`compact_context` incluyen el path.
- **Seam**: `skill_tool.build_skill_context_modifier` (añade path/invoked_at) + `provider` (cleanup selectivo). Nexo 05·ExR6/08·SR3.
- **Firma**: `caps['active_skills'][name] = {content, allowed_tools, model, base_dir, path, invoked_at}`.
- **Orden**: tras SkR6.
- **Test**: `test_invoked_skill_survives_compaction_with_path`, `test_clear_invoked_skills_preserves_live_agents`.

### SkR9 · FIND-SKILL6 — fork dispatch en la tool
- **Comportamiento**: `SkillTool.execute`, si `skill.execution_context == 'fork'`, no activa inline sino que lanza un sub-agente vía el `SubagentRunnerProtocol` (05), mergeando `effort`/`model`/`agent` de la skill, y devuelve `{status:'forked', agent_id, result}`; limpia invoked-skills del agente en `finally`.
- **Seam**: `skill_tool.py` + puente al runner de 05 (inyectado por contrato, no import directo).
- **Firma**: `execute` bifurca; nuevo output shape forked.
- **Cableado**: reusa `RuntimeContextForker`/runner de 05·execution; el prompt de la skill (SkR3) es el `initial_prompt` del sub-agente.
- **Orden**: tras SkR1/SkR3 y el cierre de 05.
- **Test**: `test_skill_context_fork_dispatches_subagent`, `test_forked_skill_clears_invoked_on_exit`.

### SkR10 · FIND-SKILL16 — resolución: aliases + namespaced + strip-slash
- **Comportamiento**: `find_skill(name)` resuelve por nombre exacto, `user_facing_name` (namespaced `ns:cmd`), o `aliases`; `parse_slash_command`/`SkillTool.execute` normalizan leading `/`.
- **Seam**: `state.py::get` gana resolución extendida (o `commands.py::find_skill`); `SkillDefinition.aliases: list[str]`.
- **Orden**: tras SkR1.
- **Test**: `test_find_skill_by_alias`, `test_find_skill_namespaced`, `test_skill_tool_strips_leading_slash`.

### SkR11 · FIND-SKILL11 — skill hooks (frontmatter `hooks`→session hooks)
- **Comportamiento**: al invocar una skill con `hooks`, se registran como session-hooks (con `once:true`→auto-remove tras primer éxito, `CLAUDE_PLUGIN_ROOT`=base_dir). Nexo 06·hooks.
- **Seam**: `skill_tool` llama a `register_skill_hooks(ctx, skill)` que delega en el `HookSinkProtocol` de 06.
- **Firma**: `register_skill_hooks(ctx, skill) -> None` (consume `skill.hooks` de SkR1).
- **Orden**: tras el cierre de 06 y SkR1.
- **Test**: `test_skill_hooks_registered_as_session_hooks`, `test_skill_once_hook_auto_removed` (xfail hasta 06).

### SkR12 · FIND-SKILL12 (=GAP-SKILL3) — skills condicionales (`paths`) + descubrimiento dinámico
- **Comportamiento**: skills con `paths` quedan "condicionales"; un evento post-file-op (Read/Write/Edit) las activa si algún path tocado matchea (gitignore-style). Descubrimiento: walk-up desde archivos tocados hasta cwd busca `<dir>/.claude/skills`, respeta gitignore, deepest-wins.
- **Seam**: nuevo `dynamic.py` (`activate_conditional_skills_for_paths`, `discover_skill_dirs_for_paths`) + un hook post-tool en el loop (10/07) que le pasa los paths.
- **Firma**: `activate_conditional_skills_for_paths(file_paths, cwd) -> list[str]`; `discover_skill_dirs_for_paths(file_paths, cwd) -> list[str]`.
- **Cableado**: el runtime debe emitir un evento con los file-paths de cada tool de fs; el provider lo consume y refresca el catálogo (dispara SkR7 reset).
- **Orden**: tras el seam de eventos file-op (10/07) y SkR2.
- **Test**: `test_conditional_skill_activates_on_matching_path`, `test_discover_nested_skill_dir` (xfail hasta el evento file-op).

### SkR13 · FIND-SKILL15 — bundled skills programáticos + extracción de files
- **Comportamiento**: API `register_bundled_skill(defn)` que añade una `SkillDefinition` de código (con `is_enabled` callable, `files`, `context`, etc.); los `files` se extraen a un dir por proceso (nonce) con guardas (no-follow, excl, 0o600, anti-traversal) en la primera invocación, prefijando el base_dir.
- **Seam**: nuevo `bundled.py` (`register_bundled_skill`, `extract_bundled_files`) + `provider` incluye bundled en `all_skills`.
- **Firma**: `register_bundled_skill(defn: BundledSkillDefinition) -> None`.
- **Cableado**: el integrador registra sus bundled al arrancar (el runtime no trae contenido — los 15 del canónico son de producto).
- **Orden**: independiente; bajo acoplamiento.
- **Test**: `test_register_bundled_skill`, `test_bundled_files_extraction_traversal_guard`.

### SkR14 · FIND-SKILL14 — ranking de uso
- **Comportamiento**: `record_skill_usage(name)` (debounce, persiste `skill_usage` vía storage) + `skill_usage_score(name)` (half-life 7d, piso 0.1); el listing/menu ordena por score.
- **Seam**: nuevo `usage.py` sobre `StorageProtocol` (mismo patrón que 13·memory); `SkillTool.execute` llama `record_skill_usage`.
- **Orden**: tras SkR7 (ordena el listing).
- **Test**: `test_record_and_score_usage_decay`.

### SkR15 · FIND-MCP16 — MCP skills/prompts como comandos
- **Comportamiento**: los prompts MCP se exponen como slash-commands diferidos `mcp__<server>__<prompt>` (`is_mcp`); las skills MCP como `<server>:<skill>` (`loaded_from='mcp'`, invocables por SkillTool, gate anti-bash de SkR3). `get_all_skills` mergea local + MCP (uniq por nombre); `get_mcp_skill_commands` filtra `prompt && loaded_from=='mcp' && !disable_model_invocation`.
- **Seam**: puente desde 11·capabilities/mcp — el discovery MCP construye `SkillDefinition` vía el loader (equivalente a `mcpSkillBuilders`), y el provider de skills los mergea al `catalog`/`skill_listing`.
- **Firma**: `SkillDefinition.loaded_from: str = 'skills'` (+ `'mcp'`); `SkillsProvider.merge_mcp_skills(mcp_commands)`.
- **Cableado**: 11 emite los comandos MCP; 12 los integra. Coherente con is_deferred (GAP-SKILL2).
- **Orden**: tras el cierre de 11 y SkR2/SkR3/SkR7.
- **Test**: `test_mcp_skill_invocable_via_skill_tool`, `test_mcp_prompt_is_deferred_not_skill`, `test_mcp_skill_bash_injection_blocked` (xfail hasta 11).

### SkR16 · FIND-SKILL13 — hot-reload / refresco de catálogo (comportamiento)
- **Comportamiento**: el runtime long-running refresca el catálogo por su API (`register`/`unregister` ya existen); se añade un `refresh()` que re-lee las fuentes y dispara `reset_sent_skill_names` + (si hay) el ConfigChange hook de 06. El watcher FS del canónico es ⛔ de forma (TUI); el comportamiento observable (catálogo fresco tras cambio) se cubre por API.
- **Seam**: `provider.refresh()` + señal opcional para el integrador.
- **Orden**: tras SkR2/SkR7 y 06 (ConfigChange).
- **Test**: `test_refresh_resets_sent_skill_names`.

### SkR17 · Referencias (no se re-desarrollan aquí)
- **FIND-SKILL10 cleanup por agent** ya en SkR8; su registro en abort-scope = 08·SR3 / 05·ExR6.
- **Entrega new_messages** = DEUDA-B `B-new_messages` (dueño transversal); SkR6 la consume.
- **Permisos** = DEUDA-B `B-02`; SkR4 la instancia para SkillTool.
- **Skill hooks / ConfigChange** = 06·hooks; SkR11/SkR16 los consumen.
- **Fork** = 05·execution; SkR9 lo consume.
- **Evento file-op** para condicionales/dinámicas = 10·native + 07·events; SkR12 lo consume.

---

## Nota metodológica
**Este doc se cerró en dos iteraciones; la 1ª fue superficial y el usuario la rechazó con razón** — el mismo
patrón que 11. La 1ª pasada leyó íntegros los dos grandes (`loadSkillsDir.ts`/`SkillTool.ts`) pero (a) marcó
**13 de los 15 bundled ⛔ por grep sin abrirlos** y (b) **infirió el mecanismo de FIND-MCP16** sin leer el
consumidor. La 2ª ABRIÓ los 15 bundled + `client.ts:2160-2199` y destapó **FIND-SKILL19** (`getPromptForCommand`
callable dinámico) + refinó FIND-MCP16 (resources-backed; builder `mcpSkills.ts` no vendorizado). UI.tsx/SkillsMenu/`/skills`/useSkillsChange/skillImprovement sí se **abrieron** antes de marcarse ⛔ en ambas pasadas.
**Lección reforzada (idéntica a 11): marcar ⛔ por grep/título es superficialidad; el ⛔ sólo es legítimo tras
abrir el archivo — aunque el veredicto final (contenido de producto) resulte correcto.**
El destape principal al leer lo que un grep habría escondido: (a) el `skill_listing` **incremental por-agente con
budget** (no un dump del catálogo) — clave para no quemar tokens cada turno; (b) los **dos ejes de habilitación**
(`user-invocable` ≠ `disable-model-invocation`) que el runtime conflaciona en `enabled`; (c) la **bash-injection**
en `getPromptForCommand` con su gate de seguridad anti-MCP; (d) que la **tool `Skill` misma despacha el fork**
(no lo delega); (e) que las **skills MCP** (`srv:skill`, loadedFrom mcp) son distintas de los **prompts MCP**
(`mcp__srv__prompt`, isMcp) — la resolución del cabo 11·FIND-MCP16.

### RE-AUDITORÍA 2026-07-14 (belt-and-suspenders, ordenada por el usuario) — **CONFIRMADO sin cambios**
Re-leídos ÍNTEGROS 1→EOF de cero, diff contra este doc: `SkillTool.ts` (1108) y `loadSkillsDir.ts` (1086) — los
dos archivos más grandes del subsistema. **Todo coincide con el ledger**: SkillTool (getAllCommands+MCP-merge,
validate, checkPermissions deny/allow/`:*`-prefix/safe-properties/ask+suggestions, call fork/inline+contextModifier
allowedTools/model[1m]/effort, executeForkedSkill, executeRemoteSkill=⛔EXPERIMENTAL, `${CLAUDE_SKILL_DIR}`/`${CLAUDE_SESSION_ID}`
subst, addInvokedSkill); loadSkillsDir (5 fuentes con gating por SettingSource/--bare/pluginOnly, parseSkillFrontmatterFields
todos los campos, createSkillCommand con `getPromptForCommand` callable dinámico = FIND-SKILL19, dedup por realpath,
skills condicionales `activateConditionalSkillsForPaths` + dinámicas + señal `skillsLoaded`, registerMCPSkillBuilders).
**Cero findings nuevos, cero sobre-declaración.** El `commands.ts` (754) ya se había re-verificado íntegro en el
paso previo. Ledger de 12 confirmado honesto.
