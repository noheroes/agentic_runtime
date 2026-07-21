# 10 · tools/native — homologación

> **Estado (2ª vuelta · gate 11 · 2026-07-19)**: **VALIDADA sin discrepancia** — cada fila ✅/🔀 re-verificada
> abriendo la implementación de B (los 19 `tools/native/*.py`) y siguiendo el dato hasta el **ensamblador**
> del loop (`agent_loop.py:283-352`), no aceptando la tabla. **Cero cambios de estado, código intacto, suite
> no re-ejecutada.** Detalle en §"Re-visita de COMPLETITUD (2ª vuelta · gate 11 / L09)" al pie.

Contrasta las **tools nativas** del runtime (`tools/native/*.py`, 25 tools en 20 archivos) contra
las contrapartes canónicas `tools/*Tool/` (uno a uno). Mientras 09 homologó la **infra** (protocolo,
registry, pool, dispatcher, deferred, exec/fs env), este doc baja a **cada tool concreta**: su schema,
su `execute`/`call`, y los invariantes de comportamiento que porta o no.

**Delimitación de alcance (heredada de 09 y del README).** El núcleo de cada tool es
**def + schema + `execute` + prompt**. Quedan FUERA y se cruzan a su subsistema, NO se re-auditan aquí:
- La **capa de permiso/seguridad** por-tool (`bashPermissions.ts` 2621, `bashSecurity.ts` 2592,
  `readOnlyValidation.ts` 1990, `pathValidation.ts` 1303, `sedValidation.ts` 684, `checkPermissions`,
  `checkWritePermissionForTool`/`checkReadPermissionForTool`) → **06/GAP-02** (exactamente como 09
  dejó `filesystem.ts` reglas allow/deny/ask fuera de su ledger).
- El **render** (`UI.tsx`, `render*`, `classifyForCollapse.ts` 604) → ⛔ terminal/ink.
- La **ejecución** de subagentes/tasks (`runAgent.ts` 973, `spawnMultiAgent.ts` 1093, `LocalShellTask`)
  → **05·execution**. Aquí sólo la **superficie de tool** de `AgentTool`.
- Las **tools MCP** (`MCPTool`, `McpAuthTool`, `*McpResource*`) → **11·cap-mcp**.
- Plan mode / worktree / config / todos como **capabilities** → 14/12/…; aquí sólo la tool.

**Contrapartes leídas ÍNTEGRAS**: `BashTool.tsx` (1144, **íntegro** — def+schema+flags+`validateInput`+
`checkPermissions`+`call`+`runShellCommand`+`applySedEdit`+render/UI hooks + motor de background/progress/
persistencia), `FileEditTool.ts` (625, íntegro), `FileWriteTool.ts` (434, íntegro), `FileReadTool.ts`
(1183, **íntegro** — guards/device/binary + dedup `file_unchanged` + `callInner` con handlers text/image/
pdf/notebook + `readImageWithTokenBudget` + `addLineNumbers`/`CYBER_RISK_MITIGATION_REMINDER`),
`TaskCreateTool.ts` (138, íntegro), `utils/tasks.ts` (862, **íntegro** — persistencia por-archivo +
high-water-mark + file-locking swarm + createTask/getTask/updateTask/deleteTask-cascada + blockTask-DAG +
claimTask/claimTaskWithBusyCheck + getAgentStatuses/readTeamMembers/unassignTeammateTasks),
`constants/tools.ts` (`ASYNC_AGENT_ALLOWED_TOOLS` + `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`, íntegro). Flags
`buildTool` (name/searchHint/maxResultSizeChars/isConcurrencySafe/isReadOnly/isEnabled/isDestructive/
requiresUserInteraction/checkPermissions) extraídos de los 17 `*Tool.ts` con contraparte + los
`*/constants.ts`/`prompt.ts` de los 40 dirs. **Runtime**: los 20 archivos de `native/` ÍNTEGROS +
`protocol.py` (ToolResult) + el tramo del loop que aplica `context_modifier`/`ends_turn`/PreToolUse
(`agent_loop.py:283-352`). **Nota de corrección**: la 1ª versión de este doc leyó `BashTool.tsx`/
`FileReadTool.ts`/`utils/tasks.ts` sólo por su "núcleo" y declaró el resto fuera de alcance — mal aplicada
la cláusula de la puerta de cierre (que es para archivos-satélite enteros de OTRO subsistema, p.ej.
`bashPermissions.ts`→06, no para trocear un archivo que ES de 10). Se releyeron ÍNTEGROS y aparecieron
A3b (números de línea), A3c (device/binary guards), A3d (dedup), B9-B12 (sed-edit/progress/preventCwd/
interpretCommandResult) que el núcleo ocultaba. La superficialidad es el modo de fallo #1 del esfuerzo.

## Tesis arquitectural

Tres divergencias estructurales dominan el mapa 1:1:

1. **El runtime tiene 25 tools; el canónico ~44.** Las 25 del runtime son un **subconjunto núcleo**
   (fs, shell, discovery, plan, worktree, agent, task, web) + una **inventada** (`clone_repository`).
   Las ~19 canónicas ausentes se parten en: capacidades reales no portadas (`NotebookEdit`, `LSP`,
   `SendUserMessage`/Brief, `SyntheticOutput`, `Cron*`, `RemoteTrigger`) → ❌; multi-agente/swarm
   (`SendMessage`, `TeamCreate`/`TeamDelete`) → ⛔ por el corte coordinator/swarm del README; terminal
   (`PowerShell`, `REPL`) → ⛔; MCP (`MCPTool`/`McpAuth`/`*McpResource*`) → 11.

2. **Cada tool canónica es un objeto `buildTool({...})` con ~15-40 miembros** (schema + `call` +
   `checkPermissions` + `validateInput` + `isConcurrencySafe`/`isReadOnly`/`isDestructive`/`isEnabled`/
   `requiresUserInteraction` + `getPath`/`backfillObservableInput`/`preparePermissionMatcher` +
   `searchHint`/`maxResultSizeChars`/`outputSchema` + ~15 `render*`). **Cada tool del runtime implementa
   el `ToolProtocol` de 8 miembros** (09·A): `name`/`description`/`input_schema`/`category`/
   `requires_permission`/`safe_for_background`/`timeout_seconds` + `execute`. Todo lo demás (concurrency,
   readonly, destructive, permiso por-tool, validateInput, getPath, searchHint, output schema) **no
   existe a nivel de tool** → los ❌ de 09·A se materializan aquí tool por tool.

3. **La política sale del tool a seams inyectables** (`ctx.fs` confina, `ctx.permission_context`
   deny/allow, el gate PreToolUse del hook-runner, `ctx.exec_env` backend shell). Homologación **de
   comportamiento**: el integrador server-side aporta la política que el canónico lleva inline. La cara
   oscura: **los invariantes de fs-tool que el canónico impone DENTRO del tool** (read-before-edit,
   modified-since-read, dangerous-files, secret-guard, `.ipynb`-redirect) **el runtime no los tiene ni
   en el tool ni en un seam** → FIND-CTX1 y G8 aterrizan aquí como ❌ reales, no como delegación.

**Corrección a 09.** 09·A24/D7 marcó `context_modifier` como "no portado / el loop sólo appendea
output". **Es incorrecto**: el loop SÍ aplica `context_modifier` y `ends_turn` vía `getattr`
(`agent_loop.py:329-348`), y 6 tools nativas los usan (plan_mode/worktree/config/todo_write →
`context_modifier`; ask_user/exit_plan → `ends_turn`). Se corrige abajo (§J) y se re-clasifica.

## Leyenda

✅ homologado · 🟡 parcial · 🔀 diferente (deliberado o a revisar) · ❌ no portado · ⛔ N/A core.

---

## A · fs tools — `read_file`/`write_file`/`file_edit`/`glob`/`grep` vs `Read`/`Write`/`Edit`/`Glob`/`Grep`

| # | Feature canónica | Estado | Nota / diferencia / ajuste |
|---|---|---|---|
| A1 | **Nombres** `Read`/`Write`/`Glob`/`Grep`/`Bash` (capitalizados) | 🔀 | Runtime usa `read_file`/`write_file`/`glob`/`grep`/`bash` (snake/minúscula). PERO `Edit` sí coincide (`FILE_EDIT_TOOL_NAME='Edit'`). **Homologación de naming inconsistente**: la familia fs está a medias. Impacto real: CLAUDE.md/hooks/permission-rules y el prompt del modelo referencian `Bash(...)`, `Read`, `Write`, `Glob`, `Grep` — con los nombres del runtime, una regla `Bash(git *)` o un hook `Read` no matchea. Ver §I. |
| A2 | `Read`: `isReadOnly()→true`, `isConcurrencySafe()→true` | ❌ | Runtime `read_file`: `requires_permission=False`, `safe_for_background=True`, pero **sin** `is_read_only`/`is_concurrency_safe` en el protocolo (09·A3/A6). El dispatcher es secuencial (09·D6) → el flag no tendría consumidor. |
| A3 | `Read`: **imágenes** (base64+resize/compresión a token-budget), **PDF** (extracción de páginas/`pages`), **notebooks** (celdas), salida tipada (unión `text\|image\|notebook\|pdf\|parts\|file_unchanged`) | ❌ | Runtime `read_file`: **sólo texto** (`read_text`+splitlines+offset/limit). Sin imagen/PDF/notebook. **Nexo causal con A23/`new_messages`**: el canónico entrega imagen/PDF **inyectando `newMessages`** (`createUserMessage` con bloques `image`/`document`, líneas 883-1016) — el runtime NO tiene ese canal (09·A23 ❌), por eso NO PUEDE portar image/pdf aunque quisiera. Cierra la causa raíz. |
| A3b | `Read`: **prefijo de números de línea** (`addLineNumbers`, estilo `cat -n`) | ❌ | **Gap nuevo (lectura íntegra).** El `Read` canónico numera cada línea (`formatFileLines`→`addLineNumbers`) + `CYBER_RISK_MITIGATION_REMINDER` (recordatorio anti-malware en CADA lectura). El `read_file.py` devuelve **texto crudo** (`"\n".join(selected)`), SIN numerar. Rompe el contrato del que depende `Edit`/el modelo (referenciar líneas por número) y la UX de todo el harness. Ajuste: portar la numeración. |
| A3c | `Read`: **guards de entrada** — `BLOCKED_DEVICE_PATHS` (rechaza `/dev/zero`,`/dev/random`,`/proc/*/fd/{0,1,2}`… que colgarían), rechazo de **binarios** (`hasBinaryExtension`), `getAlternateScreenshotPath` (macOS thin-space) + `findSimilarFile`/`suggestPathUnderCwd` ("Did you mean?") en ENOENT | ❌ | Runtime `read_file`: **ninguno**. Un `read_file /dev/zero`/`/dev/urandom` **colgaría el proceso** (lee infinito); un binario devuelve basura. Ajuste: portar el device-guard (bug de disponibilidad real) + rechazo de binarios. |
| A3d | `Read`: **dedup `file_unchanged`** (si el rango ya se leyó y el mtime no cambió, devuelve stub en vez de re-enviar el contenido — ahorra cache_creation tokens) + `registerFileReadListener` (servicios notificados) | ❌ | Ausente. Runtime re-envía el contenido completo cada vez. Optimización de tokens no portada. |
| A4 | `Read`: **token-cap** (`validateContentTokens`/`MaxFileReadTokenExceededError` → "exceeds maximum allowed tokens, use offset/limit") + `getDefaultFileReadingLimits` (maxSizeBytes/maxTokens) | 🟡 | Runtime: sin cota de tokens ni de bytes; `offset`/`limit` existen pero por **líneas**, sin default. Un `read_file` de un archivo enorme vuelca todo al contexto. Canónico corta por tokens (con estimación rápida + `countTokensWithAPI`). Ajuste: cota de tamaño + nudge a offset/limit. |
| A5 | `Read`: **setea `readFileState`** (`readFileState.set(path,{content,timestamp,offset,limit})`, líneas 842/1032) | ❌ | **Base de FIND-CTX1.** El canónico registra en `ToolUseContext.readFileState` cada lectura; ese estado es el que `Edit`/`Write` consultan para exigir read-before-edit. Runtime `read_file` **no registra nada** → aunque se añadiera el check en Edit, no habría estado que consultar. Ajuste ARQUITECTURAL: portar `read_file_state` al `ToolUseContext` (03) + poblarlo en `read_file`. |
| A6 | `Edit`: parámetro **`replace_all`** | ❌ | Runtime `file_edit.py`: si `count>1` → error "Provide more context". Sin `replace_all`. Ajuste menor: añadir el flag + `replaceAll` en el replace. |
| A7 | `Edit`/`Write`: **read-before-edit** (`validateInput`: `readFileState.get(path)` vacío o `isPartialView` → "File has not been read yet. Read it first", errorCode 6/2) | ❌ | **FIND-CTX1 aterriza CONFIRMADO.** El canónico **rechaza** editar/escribir un archivo existente que no se leyó antes en la sesión. Runtime `file_edit.py`/`write_file.py`: **no lo imponen** (editan/escriben directo). Invariante de seguridad/consistencia ausente. Ajuste: `validate_input` en Edit/Write consultando el `read_file_state` de A5. |
| A8 | `Edit`/`Write`: **modified-since-read** (`getFileModificationTime > readTimestamp.timestamp` → "File has been modified since read… Read it again", errorCode 7/3) + re-chequeo atómico en `call` (`FILE_UNEXPECTEDLY_MODIFIED_ERROR`) | ❌ | Ausente en runtime. El canónico detecta que el usuario/linter tocó el archivo entre la lectura y la edición y **aborta** (con fallback content-compare para full-reads). Runtime pisa cambios silenciosamente. Ajuste ligado a A5/A7. |
| A9 | `Edit`/`Write`: **safety / dangerous-files** — `validateInputForSettingsFileEdit` (settings.json), `checkTeamMemSecrets` (rechaza secretos en team-mem), `.ipynb`→`NotebookEdit` redirect, deny-rule `matchingRuleForInput`, UNC-path skip, `MAX_EDIT_FILE_SIZE` 1 GiB | ❌ | **G8/FIND-TOOL9 aterriza CONFIRMADO.** El canónico bloquea escrituras a settings, secretos, notebooks-por-la-tool-equivocada, paths denegados, archivos gigantes. Runtime: **nada** (sólo confinamiento de workspace vía `ctx.fs.resolve`, 09·G8). Un `Edit`/`write_file` dentro del workspace puede tocar `.claude/settings.json`/`.bashrc`/`.git/config` sin fricción. Es **política de permisos** (delegable al integrador) PERO el runtime no expone el gancho. Ajuste: hook de safety en el gate de escritura. |
| A10 | `Edit`/`Write`: quote-normalization (`findActualString`/`preserveQuoteStyle`), encoding-detect (utf16le BOM), line-endings preserve, fileHistory backup, LSP `didChange`/`didSave`, VSCode notify, skill-discovery-por-path | 🔀/⛔ | Quote/encoding/line-endings = 🔀 (runtime edita bytes crudos UTF-8, `content.replace`; sin normalización de comillas ni BOM — puede fallar match en archivos con comillas curvas o UTF-16). fileHistory/LSP/VSCode/skill-discovery = ⛔ (IDE/harness) salvo skill-discovery que liga 12. |
| A11 | `Edit`/`Write`: `checkPermissions`=`checkWritePermissionForTool`, `getPath`, `backfillObservableInput` (expandPath para que hooks no se evadan por `~`/relativo), `preparePermissionMatcher` | ❌ | = 09·A8/A10/A16. El gate del runtime es deny-por-nombre sin ver input ni path (09·D3). Territorio GAP-02. |
| A12 | `Edit`/`Write`: `outputSchema` tipado (`type: create\|update`, `structuredPatch`, `originalFile`, `gitDiff`) + `mapToolResultToToolResultBlockParam` | 🔀 | Runtime devuelve str plano (`"Edited {path}"`, `str(path)`). Sin patch estructurado ni diff. = 09·A15/A22. |
| A13 | `Glob`: `maxResults` 100 + trunc-note, `isReadOnly`/`isConcurrencySafe` | ✅/🟡 | Runtime `glob.py`: `DEFAULT_GLOB_LIMIT=100` (espejo explícito citado) + nota de truncado. **Homólogo fiel** del cap. 🟡 sólo por A2 (sin flags readonly/concurrency). Divergencia menor: canónico usa ripgrep/fast-glob con sort por mtime; runtime `pathlib.glob` + sort alfabético. |
| A14 | `Grep`: ripgrep, `head_limit`/`offset`, `--max-columns`, VCS-exclude, `maxResultSizeChars` 20K, modos (files/count/content) | 🟡 | Runtime `grep.py`: `DEFAULT_HEAD_LIMIT=250`, `MAX_LINE_LEN=500`, `_VCS_DIRS` exclude, `offset`, `head_limit=0`=ilimitado — **espejos explícitos** del canónico. PERO usa `re` de Python sobre `pathlib.glob`+`read_text` línea a línea (no ripgrep) → sin modos count/files-only, sin `-A/-B/-C` context, regex Python≠PCRE2, más lento. Funcional, menos rico. |

---

## B · shell — `bash` vs `Bash`; y `clone_repository` (inventada)

| # | Feature canónica (`BashTool.tsx`) | Estado | Nota |
|---|---|---|---|
| B1 | Schema: `command` + **`timeout`** (semanticNumber, max configurable) + **`run_in_background`** (semanticBoolean) + `description` | 🟡 | Runtime `bash.py`: **sólo `command`**. Sin `timeout` por-input (usa `timeout_seconds=30` de clase, envuelto por el dispatcher 09·D5), sin `run_in_background`, sin `description`. |
| B2 | **Shell persistente** (`exec(command, signal, 'bash', …)` vía `utils/Shell.ts`, UN shell vivo: `cwd`/env persisten entre llamadas) | ❌ | **FIND-TOOL8 aterriza CONFIRMADO.** `bash.py` → `ctx.exec_env.run_shell` → `LocalExecEnvironment` = `create_subprocess_shell` **fresco cada vez** (09·F2). Un `cd`/`export` en una llamada NO afecta a la siguiente. Divergencia de comportamiento observable. Ajuste ARQUITECTURAL: backend con shell persistente (seam `ToolExecEnvironment` ya existe, falta la impl viva). |
| B3 | **Background tasks**: `run_in_background`→`backgroundTaskId`, auto-backgrounding en timeout, `ASSISTANT_BLOCKING_BUDGET_MS` (15s), Kairos force-async, sugerencia de `Monitor`/`sleep`-bloqueante, output a `getTaskOutputPath` | ❌ | Runtime `bash.py`: bloqueante puro, sin background, sin auto-bg, sin task-id. `ShellResult` no tiene dónde colgar un `backgroundTaskId` (09·F4). Liga 05·EXEC9/10 (promoción fg→bg, force-async kairos) y `Monitor`/`Sleep` (no portados). |
| B4 | `isConcurrencySafe(input)=isReadOnly(input)`, `isReadOnly`=`checkReadOnlyConstraints`, `checkPermissions`=`bashToolHasPermission` (la torre `bashPermissions`/`bashSecurity`/`readOnlyValidation`, ~9K LOC) | ❌ | Runtime: `requires_permission=True` grueso; sin readonly-derivation ni la torre de seguridad. **GAP-02** (parseo AST del comando, prefix-rules, wildcard, compound-command splitting). El runtime confía todo al gate deny-por-nombre + `ctx.exec_env` (bwrap). Divergencia mayor de seguridad, delegada al integrador. |
| B5 | `maxResultSizeChars` 30K (persist a disco), `outputSchema` (stdout/stderr/`returnCodeInterpretation`/`backgroundTaskId`), `interpretCommandResult`, image-output, sed-in-place-edit render, git-op tracking (`trackGitOperations`) | 🔀 | Runtime: `ShellResult` combina stdout+stderr, sólo `returncode` (09·F4); sin persistencia, sin interpretación, sin git-tracking (`gitOperationTracking.ts` declarado 05/10, no portado). `is_error = returncode != 0`. |
| B6 | `sandbox` (`shouldUseSandbox` + `SandboxManager`) | 🔀 | Runtime: `BwrapExecEnvironment` (09·F3), aislamiento grueso vs el adaptador rico del canónico. Divergencia conocida. |
| B7 | `preparePermissionMatcher` (split compound-command para que `ls && git push` dispare hook `Bash(git *)`), `isSearchOrReadCommand`, `toAutoClassifierInput` | ❌ | Ausentes. Ligan 06 (hook `if`) + auto-mode (política). |
| B8 | **`clone_repository`** (runtime) — sin contraparte canónica | 🔀 (AÑADIDO) | El canónico clona por `Bash` con red normal + credenciales del host. El runtime NO puede (bash en bwrap `--unshare-all` sin red; token en el MCP, no en env). `clone_repository` es **valor propio**: git clone FUERA del sandbox (subproceso privilegiado con red), credencial vía seam `ctx.git_credentials` (credential-helper efímero, token nunca en argv ni `.git/config` ni expuesto al modelo), destino confinado con `ctx.fs.resolve`. Cubre el hueco del MCP de GitHub (API sí, clone no). Bien diseñado. |
| B9 | **`_simulatedSedEdit`/`applySedEdit`** — Bash puede aplicar un sed-in-place **preview-aprobado** que escribe el fichero Y **actualiza `readFileState`** (líneas 360-419) | ❌ | Runtime `bash.py` no lo tiene. Nota transversal: incluso Bash participa del invariante `readFileState` (A5) — refuerza que la ausencia de read-state en el runtime es sistémica (afecta a Read, Edit, Write y Bash-sed). |
| B10 | **`onProgress` heartbeat** (generador `runShellCommand` emite `bash_progress` cada ~1s: output parcial/líneas/bytes/elapsed vía `TaskOutput.startPolling`) | ❌ | = 07·EVT6 / 09·D10. Runtime bloquea sin progreso intra-tool. El dispatcher del runtime ni siquiera transporta `onProgress`. |
| B11 | **`preventCwdChanges = !isMainThread`** | 🔀 | **Matiz de FIND-TOOL8.** Aun con shell persistente, el canónico **bloquea `cd`** para subagentes (no-main-thread): un worker no puede mover el cwd del shell compartido. El runtime (sin shell persistente) el punto es moot, pero al portar F2 hay que replicar esta restricción por-thread. |
| B12 | **`dangerouslyDisableSandbox`** (input) + `interpretCommandResult` (exit-codes semánticos: p.ej. grep=1 "sin match" no es error) + `trackGitOperations` + `extractClaudeCodeHints` (side-channel `<claude-code-hint/>` stripped) + persistencia de output grande a tool-results-dir (link/copy, truncado 64 MB) + image-output (resize) | ❌/🔀 | Todo ausente en `bash.py`. `dangerouslyDisableSandbox` = escape explícito del sandbox (el runtime lo tapa a nivel `ctx.exec_env`). `interpretCommandResult` importa: el runtime marca `is_error = returncode != 0` a secas → un `grep` sin match (rc=1) se reporta como error. Ajuste al menos para exit-codes semánticos. |

---

## C · discovery / meta — `config`/`todo_write`/`sleep`/`ask_user`/`tool_search`

| # | Feature canónica | Estado | Nota |
|---|---|---|---|
| C1 | `Config` (`Config`): get/set settings, `isReadOnly(input)` (read si no hay value), `checkPermissions`, `supportedSettings` (211 LOC allow-list de claves válidas), voice-gating (`feature('VOICE_MODE')`) | 🟡 | Runtime `config.py`: get/set sobre `app_state.native['config']` (dict en memoria) vía `context_modifier`. **Homólogo funcional** PERO: (a) sin `supportedSettings` → acepta cualquier clave; (b) el store canónico persiste a settings.json (15·storage), el runtime lo deja en app_state efímero; (c) sin gating de claves. Nombre coincide (`Config`). |
| C2 | `TodoWrite` (`TodoWrite`): checklist de sesión, `isEnabled()` gated, `checkPermissions`, verification-agent hook | ✅/🟡 | Runtime `todo_write.py`: schema `{id,content,status,priority}` con enums espejo, guarda en `app_state.native['todos']` vía `context_modifier`, devuelve `{old_todos,new_todos}`. **Homólogo fiel**. 🟡: sin `isEnabled` (09·A5), sin el hook de verification-agent. Nombre coincide. |
| C3 | `Sleep` (`Sleep`): feature-gated (`require` condicional en `tools.ts:25-27`); impl **no está en el árbol legible** (sólo `prompt.ts` 17 LOC) | 🟡 | Runtime `sleep.py`: `asyncio.sleep(clamp(duration,0,60))`, cap 60s. Homólogo plausible (el prompt canónico también dice max 60), pero el canónico lo gatea por feature y auto-backgroundea sleeps largos vía `Monitor` (B3). Nombre coincide. |
| C4 | `AskUserQuestion` (`AskUserQuestion`): `requiresUserInteraction()→true` (para en `interactiveHandler`), `isConcurrencySafe/isReadOnly→false`, `isEnabled` gated, `checkPermissions`, schema 1-4 preguntas × 2-4 opciones + `multiSelect` | ✅/🟡 | Runtime `ask_user.py`: schema **idéntico** (1-4 preguntas, 2-4 opciones, `header`≤12, `multiSelect`, no-'Other'). En vez de `requiresUserInteraction` usa **`ends_turn=True`**: emite las preguntas y cede el turno; el consumidor reinyecta la respuesta como tool_result al inicio del turno siguiente (HITL multi-turno). **Homólogo de comportamiento** (server-side users/sessions). 🟡 por `isEnabled`. Nombre coincide. |
| C5 | `ToolSearch` | — | Cubierto en **09·E** (E6 select: sin multi = FIND-TOOL6; E7 scoring pobre). No se re-audita. |

---

## D · plan mode — `EnterPlanMode`/`ExitPlanMode` vs `EnterPlanModeTool`/`ExitPlanModeV2Tool`

| # | Feature canónica | Estado | Nota |
|---|---|---|---|
| D1 | `EnterPlanMode`: `isEnabled()` (main-thread/Kairos-gated), `isConcurrencySafe/isReadOnly` | ✅/🟡 | Runtime `EnterPlanModeTool`: **root-only** (`if ctx.is_subagent → error`; el canónico también es main-thread-only — no está en `ASYNC_AGENT_ALLOWED_TOOLS`). Setea `app_state.native['plan_mode']=True` vía `context_modifier` + resetea la cadencia del reminder. Homólogo. 🟡 sin `isEnabled` como método. |
| D2 | `ExitPlanModeV2Tool` (nombre `ExitPlanMode`): `requiresUserInteraction()→true`, schema interno **sin `plan`** (plan leído de disco vía `getPlan`), rechazo pre-permiso, auto-mode/permission-setup (TRANSCRIPT_CLASSIFIER) | ✅/🟡 | Runtime `ExitPlanModeTool`: schema **vacío** (plan leído del plan-file vía `get_plan(ctx)` — mismo diseño "fuente de verdad en disco"), cachea el plan para el one-shot del provider, `ends_turn=True` (homólogo de `requiresUserInteraction` — presentar el plan CIERRA el turno a esperar aprobación). **Homólogo fiel** del V2. Nombre coincide. 🟡: sin el enganche de auto-mode/classifier (política). |
| D3 | Ambos: `context_modifier` para mutar `plan_mode` state | ✅ | **CORR a 09**: el runtime SÍ transporta y aplica `context_modifier` (§J). Plan mode entra/sale mutando `app_state.native` en el loop. |

---

## E · worktree — `EnterWorktree`/`ExitWorktree`  · **resuelve GAP-TOOL2/GAP-MODE2**

| # | Feature canónica | Estado | Nota |
|---|---|---|---|
| E1 | `EnterWorktree`/`ExitWorktree`: crear/salir worktree git aislado, schema (`name` / `action keep\|remove` + `discard_changes`), output tipado (`worktreePath`/`worktreeBranch`/`discardedFiles`/`discardedCommits`) | ✅/🟡 | Runtime `worktree.py`: `git worktree add -b worktree/<name> <root>/../.worktrees/<name>` con slug-validation (`_SLUG_RE`), guard de "ya en worktree", exit con `keep`/`remove`+`discard_changes` (refuse si hay cambios sin `discard`), muta `app_state.native['worktree_session']` vía `context_modifier`. **Homólogo de comportamiento fiel**. 🟡: output str plano vs tipado; `ExitWorktree` canónico marca `isDestructive(input)` (runtime no, 09·A7). |
| E2 | **`safe_for_background`**: `EnterWorktree`/`ExitWorktree` ∈ `ASYNC_AGENT_ALLOWED_TOOLS` | 🔀 | **GAP-TOOL2/GAP-MODE2 RESUELTO.** El canónico **SÍ permite** worktree en agentes async (`constants/tools.ts:69-70`). El runtime marca `worktree.safe_for_background=False` (09·B3) → **es más restrictivo de lo debido**. Ajuste: `safe_for_background=True` para worktree, o —mejor— reemplazar el bool por la allowlist (E3). |
| E3 | **Modelo de gating de background**: DOS allowlists **positivas por nombre**, no un bool por-tool | 🔀 | **Hallazgo transversal (FIND-NATIVE-BG).** El canónico tiene: `ASYNC_AGENT_ALLOWED_TOOLS` = {Read, WebSearch, TodoWrite, Grep, WebFetch, Glob, Bash/PowerShell (`SHELL_TOOL_NAMES`), Edit, Write, NotebookEdit, Skill, SyntheticOutput, ToolSearch, EnterWorktree, ExitWorktree} — lo que un **subagente async** puede usar; y `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS` = {TaskCreate/Get/List/Update, SendMessage, (+Cron*)} — lo que un **teammate** puede usar. El runtime usa un **bool `safe_for_background` por-tool** que hay que reconciliar celda a celda (E4). |
| E4 | Reconciliación `safe_for_background` (runtime) vs allowlists (canónico) | 🔀 | **worktree** F→debe T (E2). **Agent** runtime=T pero **NO** ∈ async-allowlist → el canónico NO deja a un async spawnear otro async; el runtime sí (con depth≤5) — divergencia. **Sleep/Config** runtime=T, **NO** ∈ allowlist → divergencia (menor). **Task\*** runtime=T pero son `IN_PROCESS_TEAMMATE`, no async (y `TaskStop` explícitamente excluido: "requires main-thread task state") → divergencia. **Bash/Edit/Write/Read/Glob/Grep/WebFetch/WebSearch/TodoWrite/ToolSearch** runtime=T ∈ allowlist → ✅. **AskUserQuestion/EnterPlanMode/ExitPlanMode** runtime=F, NO ∈ allowlist → ✅. `clone_repository`=T (inventada, sin contraparte). Ajuste: sustituir el bool por las dos allowlists nombradas. |

---

## F · agent — `Agent` vs `AgentTool` (superficie de tool; ejecución = 05)

| # | Feature canónica | Estado | Nota |
|---|---|---|---|
| F1 | Nombre `Agent` (+ legacy `Task`), spawn de subagente | ✅ | Runtime `AgentTool` nombre `Agent`. Homólogo. Depth-limit 5 (`_MAX_SUBAGENT_DEPTH`). |
| F2 | Schema: `prompt`/`description` + `subagent_type` + `run_in_background` + (KAIROS) `name` (addressable vía SendMessage), `team_name`, `model_override`-equiv | 🔀 | Runtime: `prompt`/`description`/`run_in_background`/`subagent_type`/`model_override`/`inherit_messages`. Sin `name`/`team_name` (swarm ⛔). `inherit_messages` es propio del runtime (fork con/sin historia). |
| F3 | `filterDeniedAgents`, `filterToolsForAgent` (async→allowlist), `ONE_SHOT_BUILTIN_AGENT_TYPES`, coordinator-mode gating, `agentMemory`/`agentMemorySnapshot`, `builtInAgents` | 🔀/❌ | Territorio **05·execution** (runner/fork/registry) — aquí sólo se constata que la **tool** delega en `get_runner().run(fork_ctx, background=)`. `ForkSnapshot`/`ForkPolicy`/`ForkContext` = 05. La memoria de agente = 13. |
| F4 | `run_in_background`→task-id; fg→resultado directo | ✅ | Runtime: `background=True` → "Task ID: …"; si no, output directo o `(no output)`. Homólogo del patrón. |

---

## G · task tools — `TaskCreate`/`Get`/`List`/`Update`/`Stop`/`Output`  · **resuelve el cabo task_tools**

| # | Feature canónica (`utils/tasks.ts` + `Task*Tool`) | Estado | Nota |
|---|---|---|---|
| G1 | **Sobre qué store operan**: la **tasklist** persistida `utils/tasks.ts` (`createTask(getTaskListId(), …)`, `getTasksDir`/`getTaskPath`, high-water-mark de IDs en disco), NO el registry de ejecución | 🔀 | **CABO task_tools RESUELTO (= FIND-NATIVE-TASK).** El canónico `Task*` es un **tablero TODO colaborativo** (persistido, team-scopeado). El runtime `task_tools.py` opera sobre **`execution.tasks.registry.get_registry()`** — el **MISMO registry de ejecución** donde aterrizan los subagentes background (05). **Conflación**: el runtime funde dos conceptos canónicos distintos (tasklist-tool ≠ registry-de-ejecución). Consecuencia: `TaskCreate` inyecta un record fantasma sin ejecución detrás; `TaskList` mezcla TODOs con tareas de subagente reales. La aclaración de 05 lo anticipó: "NO es el registry de ejecución". |
| G2 | `TaskCreate`: `subject`/`description`/`activeForm`/`metadata`, `status:'pending'`, `owner`/`blocks`/`blockedBy`, `shouldDefer:true`, `isEnabled:isTodoV2Enabled()`, dispara **hooks TaskCreated** (rollback si blocking) | 🟡 | Runtime: `subject`/`description` → `register(description=f"{subject}: {description}")`. Sin `activeForm`/`metadata`/`owner`/`blocks`/`blockedBy`, sin `shouldDefer`, sin gating, sin hooks. |
| G3 | `TaskUpdate`: `taskId`/`subject`/`description`/**`status`**(pending/in_progress/completed/**deleted**)/`blocks`/`blockedBy`/**`owner`** + auto-set-owner al marcar in_progress | ❌ | Runtime `TaskUpdate`: **sólo `description`**. Sin transiciones de status, sin owner, sin DAG de bloqueo. El status del runtime lo maneja el runtime de ejecución, no el modelo. |
| G4 | **`claimTask`** (agente reclama tarea → owner, con busy-check anti-deadlock), **`blockTask`** (DAG), `getAgentStatuses`/`readTeamMembers` (`TeamMember`, coordinación de equipo) | ⛔/❌ | Dimensión **team/swarm** de la tasklist → ⛔ por el corte del README (coordinator/swarm). El runtime no tiene teammates. Se documenta como la razón de que `Task*` del runtime sea un wrapper fino. |
| G5 | `TaskGet`/`TaskList`/`TaskOutput`: read-only sobre la tasklist, scopeado por `getTaskListId()` (sesión o team-name del leader) | 🟡 | Runtime: `TaskGet`/`TaskList`/`TaskOutput`/`TaskStop` scopean por `session_id` (`_scoped_get`: un task de otra sesión es invisible — espejo correcto de `getTaskListId()→getSessionId()`). PERO leen del registry de ejecución (G1). `TaskStop` mata vía `registry.kill` (coherente con "kill running task", pero el canónico excluye TaskStop de async — main-thread). |

---

## H · web — `web_fetch`/`web_search` vs `WebFetch`/`WebSearch`

| # | Feature canónica | Estado | Nota |
|---|---|---|---|
| H1 | `WebFetch`: HTML→markdown, cache 15min, `preapproved` domains (166 LOC), `checkPermissions` con reglas `WebFetch(domain:*)`, `maxResultSizeChars` 100K | 🔀 | Runtime `web_fetch.py`: `urllib.urlopen` crudo, **sólo http/https** (cierra `file:`/custom, mitiga CWE-22), cap 100K chars, `User-Agent` fijo. **Sin** conversión a markdown, sin cache, sin reglas de dominio (la política de dominio la aporta el integrador/sandbox-adapter 09·F3). Nombre coincide. Divergencia deliberada (mínimo viable). |
| H2 | `WebSearch`: **web_search server-side** (via modelo, `toolChoice` Haiku), `isEnabled()` gated, `allowed/blocked_domains` | 🔀 | Runtime `web_search.py`: **Serper.dev** (`SERPER_API_KEY` requerido), construye `site:`/`-site:` filters, cap 20 resultados. Mecanismo **distinto** (provider externo adaptado, no el web_search nativo del modelo). Nombre coincide. Sin `isEnabled`. Valor: funciona sin depender del tool nativo del proveedor. |

---

## I · Homologación de naming (transversal)

| Runtime | Canónico | ¿Coincide? |
|---|---|---|
| `read_file` / `write_file` / `glob` / `grep` / `bash` | `Read` / `Write` / `Glob` / `Grep` / `Bash` | ❌ (snake vs Capitalized) |
| `Edit` / `Config` / `Sleep` / `TodoWrite` / `AskUserQuestion` / `ToolSearch` | idem | ✅ |
| `Agent` / `WebFetch` / `WebSearch` | idem (Agent + legacy `Task`) | ✅ |
| `EnterPlanMode` / `ExitPlanMode` / `EnterWorktree` / `ExitWorktree` | idem | ✅ |
| `TaskCreate/Get/List/Update/Stop/Output` | idem | ✅ (nombre; store diverge, G1) |
| `clone_repository` | — (inventada) | n/a |

**FIND-NATIVE-NAME**: 5 de las tools núcleo (`read_file`/`write_file`/`glob`/`grep`/`bash`) NO homologan el
nombre canónico, mientras `Edit` (su hermano fs) SÍ. Rompe: (a) permission-rules `Bash(git *)`/`Read`/`Write`;
(b) hooks matcher por `tool_name`; (c) referencias en CLAUDE.md/skills; (d) el prompt del modelo, entrenado en
los nombres canónicos. Ajuste barato y alto-impacto: renombrar a `Bash`/`Read`/`Write`/`Glob`/`Grep`.

---

## J · CORRECCIÓN a 09 — `context_modifier`/`ends_turn` SÍ se aplican

09·A24/D7 marcó `context_modifier` como ❌ ("el loop sólo appendea output"). **Verificación in situ
(`agent_loop.py:283-352`) lo desmiente**:
- `modifier = getattr(result, "context_modifier", None); if modifier: ctx = modifier(ctx) or ctx`
  (líneas 329-337) — **aplicado**, con try/except que loguea si falla.
- `if getattr(result, "ends_turn", False): _ends_turn = True` (338-339) → corta el turno (348).
- **Consumidores reales**: `plan_mode`/`worktree`/`config`/`todo_write` usan `context_modifier` para mutar
  `app_state.native`; `ask_user`/`exit_plan` usan `ends_turn` para el HITL multi-turno.
- El campo NO está declarado en `ToolResult` (`protocol.py`): se adjunta dinámicamente (`# type:
  ignore[attr-defined]`). Frágil (sin tipo), pero **funciona**.

**Re-clasificación**: 09·A24 (`contextModifier`) ❌ → **🟡** (aplicado vía attr dinámico, sin gating por
`is_concurrency_safe==False` que el canónico exige, y sin declararlo en el protocolo). 09·D7-context_modifier
❌ → **🟡**. Lo que **sigue** ❌ es 09·A23/D7-**`new_messages`**: el loop sólo appendea `result.output`
(línea 319-323), no hay canal para que una tool inyecte mensajes tipados al historial.

**Además — gate PreToolUse en el loop (aclaración a 09·D3):** el loop dispara `HookEvent.PRE_TOOL_USE`
(`agent_loop.py:300-313`) y honra `block` (deny sin ejecutar) + `modified_input` (reemplaza el input) del
hook-runner. Es un segundo gate, distinto del `requires_permission`/`allowed_names` del dispatcher (09·D3):
la política vive en el hook del integrador. NO consume `stop`/`additional_context`. Esto **matiza** GAP-02:
el punto PreToolUse existe y transporta block/modified_input; lo que falta es el `checkPermissions` **por-tool**
con modos + el input al gate del dispatcher (sigue GAP-02).

---

## K · Extras canónicos sin contraparte en runtime (clasificación)

| Tool canónica | Nombre | Clasif. | Razón |
|---|---|---|---|
| `BriefTool` | `SendUserMessage` (legacy `Brief`) | ❌ | Canal de **entrega al usuario** (markdown + attachments + `status: normal\|proactive`). El runtime entrega vía texto assistant + EventBus (server-side). Capacidad real no portada como tool; liga A23 `new_messages` + entrega proactiva. |
| `SyntheticOutputTool` | (interno) | ❌ | **Structured/synthetic final output** (liga 09·A15 `outputSchema` + G3). Diferido. |
| `NotebookEditTool` | `NotebookEdit` | ❌ | Editar celdas Jupyter. Capacidad fs real no portada. `Edit` canónico **redirige** `.ipynb` aquí (A9); el runtime ni redirige ni edita notebooks. ∈ async-allowlist. |
| `LSPTool` | `LSP` | ❌ | Code-intelligence (goToDefinition/findReferences/hover/symbols/callHierarchy). Capacidad real, pesada, IDE-acoplada. No portada. |
| `ScheduleCronTool` | `CronCreate`/`Delete`/`List` | ❌ | Scheduling de agentes (feature `AGENT_TRIGGERS`/Kairos + GrowthBook). Subsistema de cron no portado. |
| `RemoteTriggerTool` | `RemoteTrigger` | ❌/⛔ | Gestiona agentes remotos vía **claude.ai CCR API** (OAuth in-process). Producto-específico (claude.ai). |
| `SendMessageTool` | `SendMessage` | ⛔ | Mensajería **inter-agente** (teams/UDS/bridge). Swarm/coordinator → corte del README. Liga 05·EXEC12 (pendingMessages). |
| `TeamCreateTool` / `TeamDeleteTool` | `TeamCreate`/`TeamDelete` | ⛔ | Ciclo de vida de **equipos/swarm** (`~/.claude/teams/`). Corte del README. |
| `PowerShellTool` | `PowerShell` | ⛔ | Shell de Windows (∈ `SHELL_TOOL_NAMES`). Runtime = Linux server-side. Terminal/OS. |
| `REPLTool` | `REPL` | ⛔ | REPL de terminal. |
| `MCPTool` / `McpAuthTool` | (dinámicos) | →11 | Wrapper de tools MCP + OAuth. **11·cap-mcp**. |
| `ListMcpResourcesTool` / `ReadMcpResourceTool` | idem | →11 | El runtime **sí** tiene `resource_tools.py` (README 11). Contraste en **11**. |

---

## Hallazgos (IDs para retoma)

- **FIND-NATIVE-NAME** (🔀 §A1/I): `read_file`/`write_file`/`glob`/`grep`/`bash` no homologan el nombre
  canónico (`Read`/`Write`/`Glob`/`Grep`/`Bash`), mientras `Edit` sí. Rompe permission-rules, hooks,
  CLAUDE.md y el prior del modelo. Ajuste barato/alto-impacto.
- **FIND-NATIVE-READSTATE** (❌ A5): `read_file` no puebla `readFileState` (ni existe en el `ToolUseContext`).
  Es la **base ausente** de read-before-edit. = raíz de FIND-CTX1.
- **FIND-NATIVE-EDITGUARDS** (❌ A7/A8/A9): `file_edit.py`/`write_file.py` no imponen read-before-edit,
  ni modified-since-read, ni safety (settings/secrets/`.ipynb`/deny-rule/tamaño). **Aterrizan FIND-CTX1 + G8/FIND-TOOL9.**
- **FIND-NATIVE-READ** (❌ A3/A3b/A3c/A3d/A4): `read_file` sólo texto (sin imagen/PDF/notebook — el nexo
  causal es A23/`new_messages`, el canal por el que el canónico entrega imagen/pdf), **sin numeración de
  línea** (`addLineNumbers`; rompe el contrato del que depende Edit/el modelo), **sin device-guard**
  (`read_file /dev/zero` colgaría el proceso), sin rechazo de binarios, sin dedup `file_unchanged`, sin
  token/byte-cap. Varios de estos son **bugs de disponibilidad/correctitud reales**, no sólo ausencias.
- **FIND-NATIVE-BASH-DEPTH** (❌ B9-B12, hallazgo de la RE-LECTURA íntegra): el "núcleo" de Bash ocultaba
  un motor real — sed-edit que actualiza `readFileState` (B9), heartbeat `onProgress` (B10=07·EVT6),
  `preventCwdChanges` por-thread (B11, matiz de FIND-TOOL8), `interpretCommandResult` exit-codes semánticos
  (B12: el runtime marca `grep` sin-match rc=1 como error), `dangerouslyDisableSandbox`, persistencia de
  output grande. El auto-backgrounding (timeout→bg, Kairos budget, Ctrl+B fg↔bg) refuerza B3.
- **FIND-NATIVE-BASH** (❌ B2/B3): sin shell persistente (**FIND-TOOL8**) y sin background/auto-bg/task-id.
- **FIND-NATIVE-BG** (🔀 E2/E3/E4): el bool `safe_for_background` diverge del modelo canónico de DOS
  allowlists nombradas; worktree mal excluido (**GAP-TOOL2/GAP-MODE2 resuelto**), Agent/Sleep/Config/Task*
  mal incluidos.
- **FIND-NATIVE-TASK** (🔀 G1): `task_tools.py` **conflaciona** la tasklist-tool (canónico `utils/tasks.ts`,
  TODO colaborativo con owner/DAG/status/teams) con el **registry de ejecución** (05). Wrapper fino:
  sin status/owner/blocks/activeForm/metadata/hooks.
- **FIND-NATIVE-WEB** (🔀 H1/H2): `WebFetch` sin markdown/cache/domain-rules; `WebSearch` sobre Serper.dev
  (no el web_search nativo del modelo). Mínimos viables deliberados.
- **CORR-09-CTXMOD** (§J): 09·A24/D7 `context_modifier` ❌ → **🟡** (el loop SÍ lo aplica, 329-348).
  Sigue ❌ sólo `new_messages` (A23). Y el gate **PreToolUse** existe en el loop (matiza GAP-02/09·D3).

### Cabos que ENTRARON y su resolución
- **FIND-TOOL8** (bash sin shell persistente) → CONFIRMADO en `bash.py`→`LocalExecEnvironment` (fresco por
  llamada) vs `exec`/`Shell.ts` (persistente). ❌ = FIND-NATIVE-BASH.
- **GAP-TOOL2 = GAP-MODE2** (worktree bg) → RESUELTO: canónico lo permite (`ASYNC_AGENT_ALLOWED_TOOLS`);
  runtime `safe_for_background=False` es erróneamente restrictivo. 🔀 = FIND-NATIVE-BG/E2.
- **FIND-CTX1** (FileEdit sin read-before-edit/modified-since-read) → CONFIRMADO: el canónico lo impone en
  `validateInput` de `Edit` **y** `Write` (+ re-chequeo atómico en `call`); el runtime no. ❌ = FIND-NATIVE-EDITGUARDS.
- **FIND-TOOL9 / G8** (dangerous-files no protegidos) → CONFIRMADO: canónico `validateInputForSettingsFileEdit`
  + `checkTeamMemSecrets` + `.ipynb`-redirect + deny-rule + MAX_EDIT_FILE_SIZE; runtime nada. ❌ = FIND-NATIVE-EDITGUARDS.
- **task_tools = tasklist canónico (utils/tasks.ts, claimTask/TeamMembers; NO el registry de ejecución)** →
  RESUELTO: el runtime lo mapeó AL registry de ejecución = conflación. 🔀 = FIND-NATIVE-TASK.

### Gaps con ID (heredados / que salen)
- **GAP-02 / GAP-TOOL1** sigue abierto: `checkPermissions` por-tool + modos + input al gate. El PreToolUse del
  loop lo matiza pero no lo cierra (§J).
- **GAP-NATIVE-1** (nuevo): portar `read_file_state` al `ToolUseContext` (03) + poblarlo en `read_file` +
  consumirlo en `Edit`/`Write` (cierra FIND-CTX1). Prerrequisito de FIND-NATIVE-EDITGUARDS.
- **GAP-NATIVE-2** (nuevo): exponer un hook de **safety fs** (dangerous-files/settings/secrets) en el gate de
  escritura (cierra G8) — o declararlo responsabilidad explícita del integrador server-side.

## Recuento
Tools con contraparte: 25 runtime vs ~44 canónico. Estados de las celdas de comportamiento (recuento
actualizado tras la re-lectura íntegra de Bash/FileRead/tasks):
✅/homólogo-fiel **~10** (glob-cap, grep-cap, todo_write, ask_user, plan enter/exit, worktree enter/exit,
Agent spawn, config funcional, context_modifier aplicado) ·
🟡 **~12** (bash schema, read token-cap, config/sleep/todo gating, task read-scoping, edit sin replace_all…) ·
🔀 **~14** (naming, output plano, web providers, bg-allowlist, task-store, clone_repository añadido, preventCwd…) ·
❌ **~20** (read-state, edit-guards read-before-edit/modified/safety, read image/pdf/notebook + **números de
línea** + **device/binary guards** + **dedup**, bash persistent/bg + **sed-edit/readState** + **onProgress** +
**interpretCommandResult**, new_messages, Brief/SyntheticOutput/Notebook/LSP/Cron/RemoteTrigger) ·
⛔ **~8** (SendMessage/Team*/PowerShell/REPL + render + claim/team dimension). Lo vinculante son los IDs
FIND-NATIVE-* y los cabos resueltos. **La re-lectura íntegra subió los ❌ de ~15 a ~20** (A3b/A3c/A3d/B9/B10/B12).

## Ledger de archivos (auditoría de cierre — protocolo obligatorio)

### Canónico (`/home/noheroes/python/claude-code/src`)
| Archivo | LOC | ¿Leído íntegro? |
|---|---|---|
| `tools/FileEditTool/FileEditTool.ts` | 625 | **sí** |
| `tools/FileWriteTool/FileWriteTool.ts` | 434 | **sí** |
| `tools/FileReadTool/FileReadTool.ts` | 1183 | **sí** (íntegro; guards/dedup/`callInner`/handlers text-image-pdf-notebook/`addLineNumbers`/`readImageWithTokenBudget`) |
| `tools/BashTool/BashTool.tsx` | 1144 | **sí** (íntegro; def/schema/validateInput/checkPermissions-shim/call/`runShellCommand`/`applySedEdit`/motor de background) |
| `tools/TaskCreateTool/TaskCreateTool.ts` | 138 | **sí** |
| `utils/tasks.ts` | 862 | **sí** (íntegro; persistencia-por-archivo/lock/hwm/create/get/update/delete-cascada/block-DAG/claim/agentStatuses/unassign) |
| `constants/tools.ts` (allowlists) | ~100 | **sí** (`ASYNC_AGENT_ALLOWED_TOOLS` + `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`) |
| flags `buildTool` de 17 `*Tool.ts` con contraparte | — | **sí** (name/searchHint/maxResultSizeChars/isConcurrencySafe/isReadOnly/isEnabled/isDestructive/requiresUserInteraction/checkPermissions vía grep dirigido) |
| `*/constants.ts` + `*/prompt.ts` de los 40 dirs | — | **sí** (nombres canónicos + descripciones para clasificación) |

**Corrección de método (importante).** La 1ª versión de este ledger marcó `FileReadTool.ts`/`BashTool.tsx`/
`utils/tasks.ts` como "núcleo/superficie" y declaró el resto fuera de alcance — **mal aplicada** la cláusula
de cierre. Esa cláusula es para **archivos-satélite ENTEROS de OTRO subsistema**, NO para trocear un archivo
que ES la definición de una tool de 10 (no hay subsistema 11-18 donde "continuar" esos tramos → diferir era
diferir a ningún sitio). Se releyeron **ÍNTEGROS**; los tres ahora = **sí**. Aparecieron A3b/A3c/A3d y
B9-B12 que el troceo ocultaba.

**Archivos-satélite ENTEROS de OTRO subsistema (legítimamente fuera del ledger de 10, con destino real):**
- **Política de permiso/seguridad de comando** → **GAP-02** (cabo transversal, no subsistema numerado; el
  runtime la reemplaza por gate deny-por-nombre + `ctx.exec_env`): `BashTool/{bashPermissions.ts 2621,
  bashSecurity.ts 2592, readOnlyValidation.ts 1990, pathValidation.ts 1303, sedValidation.ts 684,
  modeValidation.ts, shouldUseSandbox.ts}`. **NO leídos** — su homologación es contenido de GAP-02; en 10
  sólo se constata que existen y qué los reemplaza (B4).
- **Ejecución de subagentes** → **05** (documentado): `AgentTool/{runAgent.ts 973, loadAgentsDir.ts 755,
  agentToolUtils.ts 686, resumeAgent.ts, agentMemory*.ts}`, `shared/spawnMultiAgent.ts 1093`.
- **Tools MCP** → **11** (siguiente): `MCPTool`, `McpAuthTool`, `*McpResource*`, `classifyForCollapse.ts 604`.
- **Render** (`*/UI.tsx`, `render*`) → ⛔. **PowerShellTool/** ⛔ Windows. **REPLTool** ⛔ terminal.
  `shared/gitOperationTracking.ts 277` = telemetría git que Bash llama (B12) ⛔. `SleepTool` impl fuera del
  árbol legible (feature-gated, sólo `prompt.ts` 17).

### Runtime (`/home/noheroes/python/agentic_runtime/src/agentic_runtime/tools/native`)
| Archivo | LOC | ¿Leído íntegro? |
|---|---|---|
| `__init__.py` | 55 | sí |
| `agent.py` | 120 | sí |
| `ask_user.py` | 99 | sí |
| `bash.py` | 37 | sí |
| `clone_repository.py` | 150 | sí |
| `config.py` | 77 | sí |
| `file_edit.py` | 79 | sí |
| `glob_tool.py` | 47 | sí |
| `grep_tool.py` | 88 | sí |
| `plan_mode.py` | 108 | sí |
| `read_file.py` | 43 | sí |
| `sleep.py` | 40 | sí |
| `task_tools.py` | 224 | sí |
| `todo_write.py` | 64 | sí |
| `tool_search.py` | 80 | sí (re-leído; homologación en 09·E) |
| `web_fetch.py` | 68 | sí |
| `web_search.py` | 129 | sí |
| `worktree.py` | 168 | sí |
| `write_file.py` | 39 | sí |
| `tools/protocol.py` (ToolResult) | 61 | sí (re-leído por §J) |
| `loop/agent_loop.py:283-352` (context_modifier/ends_turn/PreToolUse) | — | sí |

### Preguntas de cierre
- ¿Se revisó **todo** cada archivo runtime listado? **sí** (los 20 de `native/` íntegros).
- ¿Se revisó **todo** cada archivo canónico listado? **sí, ahora íntegros** — `BashTool.tsx` (1144),
  `FileReadTool.ts` (1183), `utils/tasks.ts` (862), `FileEditTool.ts`/`FileWriteTool.ts`/`TaskCreateTool.ts`
  todos leídos ENTEROS (la 1ª versión los troceó en "núcleo" y se corrigió tras el reproche del usuario —
  ver "Corrección de método" arriba). Los archivos-satélite ENTEROS de otro subsistema (permisos→GAP-02,
  spawnMultiAgent→05, MCP→11, render/PowerShell/REPL→⛔) quedan fuera del ledger con destino real, NO
  troceados.
- ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **sí** — la re-lectura íntegra de los 3 archivos
  troceados destapó A3b (números de línea), A3c (device/binary guards), A3d (dedup), B9-B12 (sed-edit/
  progress/preventCwd/interpretCommandResult) que el "núcleo" ocultaba; los invariantes fs se verificaron
  leyendo `Edit`/`Write` íntegros; el cabo task cerrando `TaskCreateTool` + `utils/tasks.ts` completo;
  el bg-gating contra `constants/tools.ts` real.
- ¿Quedó **todo cubierto (nada pendiente)**? **sí** — los 5 cabos que aterrizaban en 10 (FIND-TOOL8,
  GAP-TOOL2/MODE2, FIND-CTX1, G8/FIND-TOOL9, task_tools) resueltos; CORR-09-CTXMOD corrige a 09; lo delegado
  (05/06/11/GAP-02/13/14/15) anotado con destino, no pendiente.

**Cierre habilitado: las 4 respuestas = sí.**

## Nota metodológica
Leer `Edit`/`Write` **íntegros** (no por grep) fue lo que confirmó FIND-CTX1 y G8: el read-before-edit vive en
`validateInput` (errorCode 6/2) Y en el re-chequeo atómico de `call` (`FILE_UNEXPECTEDLY_MODIFIED_ERROR`) —
un grep por "read" no lo habría localizado con certeza. El cabo task se cerró sólo al ver que `TaskCreateTool`
llama `createTask(getTaskListId(), …)` de `utils/tasks.ts` (tasklist) mientras el runtime llama
`get_registry().register(...)` de `execution.tasks.registry` (ejecución) — la conflación no se ve sin abrir
ambos stores. Y **verificar el cableado del loop** (`agent_loop.py:283-352`) desmintió el ❌ de 09·A24/D7:
la lectura "por hitos" de 09 asumió que el loop ignora `context_modifier`; la lectura del tramo real mostró
que lo aplica. Lección repetida: el estado de una feature no se decide por el protocolo/tipo (donde
`ToolResult` no declara el campo) sino por el **consumidor** (donde el loop lo lee vía `getattr`).

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11 / L09) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** de ENTRADA (cada ✅/🔀 re-verificada abriendo el código de B que reproduce
el comportamiento y siguiendo el dato hasta el **consumidor/ensamblador**, NO confirmando la tabla; las ❌
convergen por lectura directa). **Resultado**: el doc (ya releído ÍNTEGRO en 1ª pasada tras el reproche de
troceo — A y B enteros) **se sostiene sobre base correcta**; **TODAS** las filas ✅/🔀 verificadas abriendo B;
**cero cambios de estado** (✅~10·🟡~12·🔀~14·❌~20·⛔~8 intactos); **código intacto**; suite no re-ejecutada;
**sin costuras latentes NUEVAS** (LAT-TOOL1 de 09 se confirma que **aterriza aquí**, ya registrada en DEUDA-B).

- **Leído íntegro (B) 1→EOF** (los 19 nativos in-scope, todos pequeños): `task_tools.py` (223, el más grande
  L08), `worktree.py` (167), `clone_repository.py` (149), `web_search.py` (128), `agent.py` (119),
  `plan_mode.py` (107), `ask_user.py` (98), `grep_tool.py` (87), `tool_search.py` (79, ya en 09),
  `file_edit.py` (78), `config.py` (76), `web_fetch.py` (67), `todo_write.py` (63), `glob_tool.py` (46),
  `read_file.py` (42), `sleep.py` (39), `write_file.py` (38), `bash.py` (36), `__init__.py` (54) +
  **ensamblador** `loop/agent_loop.py:283-352` (1→EOF del tramo, L09) + `tools/protocol.py` (61).

- **✅/🔀 sostenidos abriendo B** (mini-ledger de consumidores):
  - **A1/I (naming 🔀)**: `read_file.name="read_file"`, `write_file`, `glob`, `grep`, `bash` (minúscula) vs
    `Edit` (`FILE_EDIT_TOOL_NAME="Edit"`, `file_edit.py:12`). La familia fs a medias — confirmado literal.
  - **A13 (glob ✅/🟡)**: `DEFAULT_GLOB_LIMIT=100` + nota de truncado (`glob_tool.py:13,40-43`); sort
    alfabético (`sorted(str(p))`). **A14 (grep 🟡)**: `DEFAULT_HEAD_LIMIT=250`/`MAX_LINE_LEN=500`/`_VCS_DIRS`/
    `offset`/`head_limit=0`=ilimitado espejos explícitos (`grep_tool.py:15-19`), `re` de Python sobre
    `pathlib.glob`+`read_text` línea a línea (60-72), sin modos count/files-only ni `-A/-B/-C`.
  - **B1/B5/B12 (bash 🟡/🔀/❌)**: schema sólo `command` (`bash.py:15-19`); `ShellResult`→`result.output`;
    `is_error = result.returncode != 0` **literal** (`bash.py:33`) ⇒ `grep` sin-match rc=1 = error confirmado.
  - **B8 (clone_repository 🔀 AÑADIDO)**: git clone FUERA del sandbox (subproceso privilegiado con red),
    credencial vía seam `ctx.git_credentials` con credential-helper efímero (token en env `GIT_CLONE_TOKEN`,
    **no** en argv ni `.git/config`, `clone_repository.py:120-128`), destino confinado `ctx.fs.resolve(...,
    for_write=True)`. Diseño íntegro confirmado 1→EOF.
  - **C1/C2 (config/todo 🟡/✅)**: `context_modifier` que muta `app_state.native["config"|"todos"]`
    (`config.py:62-75`, `todo_write.py:54-62`); `Config`/`TodoWrite` nombres coinciden; sin `supportedSettings`.
  - **C3/C4 (sleep/ask_user 🟡/✅)**: `asyncio.sleep(clamp(0,60))` (`sleep.py:34-35`); `ask_user` schema
    1-4×2-4 + `multiSelect` + no-'Other' (`ask_user.py:69-81`), **`ends_turn=True`** (97) en vez de
    `requiresUserInteraction`.
  - **D1/D2/D3 (plan ✅/🟡)**: `EnterPlanMode` root-only (`if ctx.is_subagent → error`, `plan_mode.py:40`),
    `context_modifier` setea `_PLAN_MODE_KEY=True` + resetea cadencia (45-49); `ExitPlanMode` schema vacío,
    `plan = await get_plan(ctx)` (79), cachea plan + `_PLAN_EXIT_PENDING_KEY`, **`ends_turn=True`** (106).
  - **E1/E2 (worktree ✅/🟡/🔀)**: `git worktree add -b worktree/<name>` (`worktree.py:73-88`), slug-guard
    `_SLUG_RE`, guard "ya en worktree" (65), exit `keep`/`remove`+`discard_changes` refuse-si-cambios (144-149),
    `context_modifier` sobre `_WORKTREE_KEY`. `safe_for_background=False` en Enter/Exit (`61,129`) = GAP-MODE2.
  - **E3/E4 (bg-gating 🔀)**: los `safe_for_background` reales verificados **celda a celda** contra la tabla E4
    — T: bash/read/write/edit/glob/grep/web_fetch/web_search/todo/tool_search/**agent**/**sleep**/**config**/
    **clone**/**Task\*** (los 6); F: **worktree**(Enter/Exit)/ask_user/EnterPlanMode/ExitPlanMode. Coincide
    EXACTO con E4. **Cabo de 04·GAP-MODE2 (4 ítems: worktree + Agent + TaskStop + TaskOutput) CONFIRMADO
    cubierto**: worktree (F→debe T), Agent (T pero no ∈ async-allowlist), TaskStop (T, excluido main-thread),
    TaskOutput (T, bajo "Task*"); todos homed en R10 — el ruteo de 04 aterriza correcto.
  - **F1/F2/F4 (agent ✅/🔀)**: nombre `Agent`, depth-cap `_MAX_SUBAGENT_DEPTH=5` (`agent.py:73`), schema con
    `inherit_messages` propio (50-54), delega `get_runner().run(fork_ctx, background=)` (105), bg→"Task ID: …".
  - **G1/G2/G5 (task 🔀/🟡)**: `task_tools.py` opera sobre `execution.tasks.registry.get_registry()` (10,54) =
    conflación con el registry de EJECUCIÓN confirmada; `TaskCreate` → `register(description=f"{subject}:
    {description}")` (54-56); scoping por `session_id` (`_scoped_get`/`_session_of` 17-32, `owner_session_id`
    30), `TaskStop`→`registry.kill` (187). **G3 (TaskUpdate ❌)**: schema **sólo `task_id`+`description`**
    (137-142), sin `status`/owner/DAG — confirmado por lectura directa (target de R11).
  - **H1/H2 (web 🔀)**: `web_fetch` `urllib` crudo, sólo http/https (`web_fetch.py:44`, CWE-22), cap 100K,
    sin markdown/cache; `web_search` Serper.dev (`SERPER_API_KEY` requerido `web_search.py:74-79`), filtros
    `site:`/`-site:` (84-95), cap `_MAX_RESULTS_CAP=20` (default 5).

- **§J / CORR-09-CTXMOD confirmado en el ENSAMBLADOR (no sólo como atributo)**: el loop **realmente aplica**
  lo que las tools adjuntan dinámicamente — `context_modifier` en `agent_loop.py:332-337` (`getattr` + try/except
  que loguea), `ends_turn` en 338-339 (→ `_ends_turn=True` → `break` en 348), gate **PreToolUse** en 300-313
  (honra `modified_input` 307-308 + `block` 309-313; **no** consume `stop`/`additional_context`, comentario
  297-298). El **canal `new_messages` sigue ❌**: el loop sólo appendea `result.output` (319-323), no hay vía
  para inyectar mensajes tipados (A23). Los 6 productores reales confirmados abriendo cada tool (config/todo/
  plan_mode-enter+exit/worktree → `context_modifier`; ask_user/exit_plan → `ends_turn`). Reproduce la
  observación de 02·F12/F4 (5+2 productores) desde la cara de las tools.

- **LAT-TOOL1 (category) — confirmado que ATERRIZA aquí, sin novedad**: cada nativo setea `category`
  (`ToolCategory.FILE/SYSTEM/BACKGROUND/NETWORK`) pero **ningún nativo lee `.category`** (slot muerto); el
  canónico no usa este enum como driver (sus `isReadOnly`/`isDestructive` que sí consume son A2/A6/A7 ❌, otra
  deuda). Respuesta a la pregunta-guía de la 2ª vuelta ("¿alguna nativa debería leer category?"): **no** —
  sigue tech-debt B-interno (registrado en 09 + DEUDA-B §B-orphans), NO deuda A↔B (anti-padding L10/L11).

- **❌ convergen por lectura directa de B** (confirmación-de-doc = verificación-de-completitud para ausencias,
  L11): `read_file` sin numeración/device-guard/dedup/read_file_state (`read_file.py` entero: `read_text`+
  `splitlines`+slice, nada más); `file_edit`/`write_file` sin read-before-edit/modified-since-read/safety
  (`file_edit.py:52-78`, `write_file.py:28-38`); `bash` sin shell persistente (`LocalExecEnvironment` fresco
  `bash.py:27`) ni background/onProgress/sed-edit. Todos ya con §Plan (R0-R11) desarrollado.

**§Nota de honestidad (2ª vuelta)**. (1) La 1ª pasada de 10 **NO fue confirmación-de-doc** — ya leyó A y B
íntegros (tras el reproche de troceo), así que aquí no hubo el patrón "1ª ronda leyó sólo la tabla". El
value-add del gate 11 fue **abrir el ENSAMBLADOR** (`agent_loop.py:283-352`) y confirmar que `context_modifier`/
`ends_turn` están **cableados** (no sólo seteados como atributo en `ToolResult`, que `protocol.py` ni declara) y
verificar los `safe_for_background` **celda a celda** contra E4 (lo que la 1ª pasada afirmó pero no tabuló uno
a uno). (2) **NO releí las contrapartes canónicas** (`BashTool.tsx` 1144 / `FileReadTool.ts` 1183 /
`utils/tasks.ts` 862) esta vuelta — estaban ÍNTEGRAS en 1ª pasada (post-reproche); apliqué "releer anclas, no
re-derivar" (método 2ª vuelta 05-09). La cara nueva del gate 11 era **B + ensamblador**, cubierta 1→EOF.
(3) `category` como slot muerto es la única costura B-interna que toca 10, y **no es nueva** (09·LAT-TOOL1).
(4) **Auto-corrección de honestidad (gate auto-adversarial del usuario, MISMO patrón que 07/09)**: mi 1ª redacción del ledger de esta vuelta listó `__init__.py` (54) y `tool_search.py` (79) como "íntegro 1→EOF (esta vuelta)" cuando en realidad **NO los había abierto esta vuelta** — `__init__.py` no se leyó y `tool_search.py` sólo se **grepeó** una línea (`safe_for_background`); íntegro estaba en 09, no en esta ronda ("abierto ≠ íntegro", L08; sobre-declaración de ledger, L03). Corregido **tras la pregunta del usuario** leyéndolos **1→EOF** ahora: `__init__.py` = re-export de las **25 clases-tool** (confirma el recuento; `GitCredentialProvider` es Protocol, no tool; el registro real en el pool es `factory/create_tools`, 09 — sin cableado nuevo aquí); `tool_search.py` = `select:` **singular** (`query[len("select:"):]`, `t.name==name`, líneas 53-55) sin split por comas (FIND-TOOL6, =09·E), `safe_for_background=True` (41) ahora por LECTURA no grep. **Cero findings nuevos, cero cambios de estado** — la corrección es de método (ledger honesto), no de sustancia. Regla re-interiorizada: el ledger declara "íntegro" SÓLO lo abierto 1→EOF en ESTA ronda; lo heredado de otra ronda se marca como tal.

### Ledger de lectura (2ª vuelta)
| Lado | Archivos | Lectura |
|---|---|---|
| B (runtime) | los 19 `tools/native/*.py` | **íntegro 1→EOF** (esta vuelta) |
| B (ensamblador) | `loop/agent_loop.py:283-352` + `tools/protocol.py` (61) | **íntegro 1→EOF** (tramo/archivo) |
| A (canónico) | `BashTool.tsx` 1144, `FileReadTool.ts` 1183, `utils/tasks.ts` 862, `FileEditTool.ts` 625, `FileWriteTool.ts` 434, `TaskCreateTool.ts` 138, `constants/tools.ts` | íntegro en **1ª pasada** (post-reproche); esta vuelta = anclas, no re-derivado |

### 4 preguntas de cierre (2ª vuelta)
1. ¿Se revisó **todo** cada archivo de **A**? **sí** — íntegros en 1ª pasada (post-troceo); 2ª vuelta reusa
   anclas por método (05-09), sin re-derivar.
2. ¿Se revisó **todo** cada archivo de **B**? **sí** — los 19 nativos + ensamblador + protocol leídos 1→EOF
   ESTA vuelta.
3. ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **sí** — cada ✅/🔀 abierta en B y seguida al
   ensamblador; E4 tabulado celda a celda; `context_modifier`/`ends_turn` confirmados CABLEADOS, no sólo
   atributos; ❌ convergen por lectura directa.
4. ¿Quedó **todo cubierto (nada pendiente)**? **sí** — cero cambios de estado; LAT-TOOL1 confirmado (ya homed
   en 09/DEUDA-B); cabo 04·GAP-MODE2 (4 ítems) confirmado cubierto en E4/R10; lo delegado (05/06/11/GAP-02/13/
   14/15 + §Plan R0-R11) con destino.

**VEREDICTO DE AVANCE**: ✅ **NADA PENDIENTE de verificación en 10 → avanzar a 11 · cap-mcp** (01→10 completos
con gate 11).

---

# Plan de homologación / remediación desarrollada

Diseño de la remediación de **Deuda A** (los gaps de 10 que TIENEN hogar aquí: cada `FIND-NATIVE-*` +
`GAP-NATIVE-1/2`). **NO se toca código del runtime en esta pasada** (1ª pasada = sólo diseño; los
`xfail(strict=True)` de `test_tools_native_homologation.py` ya codifican los targets — cuando la
remediación se implemente, el xfail que empiece a pasar es la señal de reclasificar la celda). Cada
entrada lleva: **comportamiento** objetivo · **seam** que lo alberga · **firma/campos** · **cableado**
(quién lo puebla/consume) · **orden** de implementación · **test** (el xfail que lo verifica). Los seams
ya leídos y sobre los que se diseña: `tools/fs_env.py` (`ConfinedFilesystem.resolve/write_root/_base_dir`),
`tools/exec_env.py` (`ToolExecEnvironment.run_shell → ShellResult`), `context/tool_use.py`
(`ToolUseContext`/`AppState`, pydantic con `arbitrary_types_allowed`), `tools/protocol.py`
(`ToolResult`/`ToolProtocol`), `tools/dispatcher.py` (choke point secuencial).

**Grafo de dependencias.** `R0` (read_file_state) es prerrequisito duro de `R2`/`R7`. `R8` (shell
persistente) es prerrequisito de `B9` (sed-edit que actualiza read_file_state) y de `B11` (preventCwd).
El resto es independiente. Orden sugerido: **R0 → R1 → {R2,R3,R4,R5,R6} → R7 → R8 → R9 → R10 → R11**.

---

## R0 · GAP-NATIVE-1 — `read_file_state` en el `ToolUseContext` (prerrequisito arquitectural)

- **Comportamiento**: cada `read_file` exitoso registra `{content, timestamp(mtime), offset, limit}`
  indexado por el host-path resuelto; ese estado es el único lugar que `Edit`/`Write` consultan para
  exigir read-before-edit (A5→A7). Homólogo de `readFileState.set(path,…)` (canónico 842/1032).
- **Seam**: nuevo campo en `context/tool_use.py::ToolUseContext`. Es un `BaseModel` con
  `arbitrary_types_allowed=True` → añadir `read_file_state: dict[str, ReadFileEntry] = Field(default_factory=dict)`.
  Vive a nivel **ctx** (no `app_state.native`) porque es estado de sesión/turno consumido por tools, no
  estado de aplicación reinyectable por `context_modifier`. El loop ya enhebra el MISMO `ctx` entre
  llamadas del turno → persiste sin trabajo extra.
- **Firma**: `@dataclass ReadFileEntry(content: str, timestamp: float, offset: int, limit: int)` en
  `tools/native/_fs_state.py` (módulo compartido nuevo, cero política).
- **Cableado**: `read_file.execute`, tras leer con éxito, hace
  `ctx.read_file_state[str(path)] = ReadFileEntry(content, path.stat().st_mtime, offset, limit)`.
  **Fork**: `ForkSnapshot` (05) debe **copiar** el dict (el hijo hereda lo leído por el padre) — anotar el
  cabo en 05·EXEC2. **Bash-sed** (B9) también lo actualizaría (refuerza que la ausencia es sistémica, A5/B9).
- **Orden**: primero de todo (R2/R7 dependen).
- **Test**: `test_read_populates_read_file_state` (`ctx.read_file_state[str(f)]` poblado).

## R1 · FIND-NATIVE-NAME — renombrar `bash/read_file/write_file/glob/grep` a `Bash/Read/Write/Glob/Grep`

- **Comportamiento**: los nombres nativos homologan el canónico (como ya hace `Edit`). Rompe hoy:
  permission-rules `Bash(git *)`/`Read`/`Write`, hooks matcher por `tool_name`, refs de CLAUDE.md/skills,
  y el prior del modelo.
- **Seam**: atributo de clase `name` (no hay seam; es un renombrado). Cascada: (a) claves del
  `native_registry`/`create_tools`; (b) `allowed_names()` del `PermissionContext` (las reglas del
  integrador deben migrar en lockstep); (c) el prompt/tool-schema que ve el modelo; (d) cualquier
  `SHELL_TOOL_NAMES`-equivalente para el bg-gating (R10).
- **Firma/campos**: `BashTool.name="Bash"`, `ReadFileTool.name="Read"`, `WriteFileTool.name="Write"`,
  `GlobTool.name="Glob"`, `GrepTool.name="Grep"`.
- **Cableado**: renombrar los 5 `name` + actualizar el registry + grep dirigido de referencias
  internas. La migración de reglas del integrador (server-side) es responsabilidad del integrador, PERO
  el runtime debe emitir los nombres canónicos para que esas reglas puedan matchear.
- **Orden**: temprano (barato, alto-impacto, desbloquea que hooks/permission-rules se prueben con nombres reales).
- **Test**: `test_fs_shell_tools_match_canonical_names` (Bash/Read/Write).

## R2 · FIND-NATIVE-EDITGUARDS (parte 1) — read-before-edit + modified-since-read (Edit/Write)

- **Comportamiento**: `validate_input` de Edit/Write sobre un archivo **existente**: (a) si el path no
  está en `ctx.read_file_state` (o es vista parcial) → error `"File has not been read yet. Read it first"`
  (homólogo errorCode 6/2); (b) si `path.stat().st_mtime > entry.timestamp` → error `"File has been
  modified since read… Read it again"` (errorCode 7/3). `Write` sólo exige read-before para archivos que
  YA existen (crear nuevo no requiere lectura previa, homólogo del canónico). Re-chequeo atómico del mtime
  justo antes del `write_text` (homólogo `FILE_UNEXPECTEDLY_MODIFIED_ERROR`).
- **Seam**: `ctx.read_file_state` (R0). Helper compartido `_fs_state.check_read_before_edit(ctx, path)
  -> str | None` (mensaje de error o None) para no duplicar entre Edit y Write.
- **Cableado**: `FileEditTool.execute` y `WriteFileTool.execute` llaman el guard tras `ctx.fs.resolve` y
  antes de escribir. Al escribir con éxito, **refrescan** la entrada de read_file_state (mtime nuevo) para
  que una segunda edición en el mismo turno no falle el modified-since-read.
- **Orden**: tras R0.
- **Test**: `test_edit_requires_read_before_edit` (error + `"read it first"`).

## R3 · FIND-NATIVE-EDITGUARDS (parte 2) = GAP-NATIVE-2 — hook de safety-fs (dangerous-files)

- **Comportamiento**: bloquear escrituras a `.claude/settings.json` (homólogo
  `validateInputForSettingsFileEdit`), secretos en team-mem (`checkTeamMemSecrets`), redirigir `.ipynb`
  a `NotebookEdit` (A9; ver §"Implementación de tools no portadas"), deny-rule por path, y
  `MAX_EDIT_FILE_SIZE` (1 GiB). Es **política** (delegable al integrador) PERO hoy el runtime **no expone
  el gancho** → GAP-NATIVE-2 es exponer el seam, no imponer una política concreta.
- **Seam**: nuevo protocolo inyectable, espejo de `ctx.fs`/`ctx.exec_env`:
  `ctx.fs_safety: FsSafetyPolicy` en `ToolUseContext` (default `DefaultFsSafety`). `FsSafetyPolicy` en
  `tools/fs_safety.py`.
- **Firma**: `FsSafetyPolicy.check_write(path: Path, content: str) -> str | None` (mensaje de rechazo o
  None). `DefaultFsSafety` rechaza: basename `settings.json` bajo un dir `.claude`, extensión `.ipynb`
  (mensaje "use NotebookEdit"), tamaño `> MAX_EDIT_FILE_SIZE`. El integrador server-side sustituye la
  instancia por su política (deny-rules/secret-scan) — misma maquinaria que `ConfinedFilesystem`.
- **Cableado**: Edit/Write llaman `ctx.fs_safety.check_write(path, content)` tras el confinamiento
  (`ctx.fs.resolve`) y tras el read-state guard (R2), antes de `write_text`.
- **Orden**: independiente de R0 (paralelo a R2).
- **Test**: `test_write_blocks_dangerous_settings_file` (`.claude/settings.json` → `is_error`).

## R4 · A6 — `Edit.replace_all`

- **Comportamiento**: flag `replace_all` (bool, default False). True → reemplaza TODAS las ocurrencias
  (salta el guard `count>1`); False → comportamiento actual (error si `count>1`).
- **Seam**: ninguno (schema + lógica local en `file_edit.py`).
- **Campos**: añadir `"replace_all": {"type": "boolean"}` a `input_schema.properties`.
- **Cableado**: si `input.get("replace_all")` → `content.replace(old,new)` (sin límite) y reportar
  `n` reemplazos; si no, mantener el guard `count>1`.
- **Orden**: independiente.
- **Test**: `test_edit_supports_replace_all` (`"replace_all" in properties`).

## R5 · A3b — numeración de línea (`addLineNumbers`)

- **Comportamiento**: prefijar cada línea con su número 1-indexado estilo `cat -n` (`{n}\t{línea}`),
  arrancando en `offset+1` cuando hay offset. Opcional: `CYBER_RISK_MITIGATION_REMINDER` en cada lectura.
  El prefijo es **de presentación**: `Edit` matchea sobre `old_string` crudo, así que numerar no rompe el
  match — pero SÍ restaura el contrato del que dependen el modelo y las refs "línea N".
- **Seam**: helper `add_line_numbers(text: str, start: int = 1) -> str` en `tools/native/_fs_state.py`
  (mismo módulo util).
- **Cableado**: `read_file` formatea las líneas seleccionadas con `add_line_numbers(selected, offset+1)`
  antes de devolver.
- **Orden**: independiente.
- **Test**: `test_read_adds_line_numbers` (`"1\talfa"`).

## R6 · A3c — device-guard + rechazo de binarios

- **Comportamiento**: rechazar `BLOCKED_DEVICE_PATHS` (`/dev/zero`,`/dev/random`,`/dev/urandom`,
  `/proc/*/fd/{0,1,2}`…) — un `read_file /dev/zero` hoy **colgaría el proceso** (lectura infinita): es un
  **bug de disponibilidad real**, no una ausencia estética. Rechazar binarios (extensión conocida
  `hasBinaryExtension` + sniff de null-byte en los primeros ~8 KB) con `"cannot read binary files"`.
- **Seam**: guards locales en `read_file` (constante + helper); no requiere ctx-seam.
- **Firma**: `BLOCKED_DEVICE_PATHS: frozenset[str]` + `_is_binary(path: Path) -> bool` (extensión ∈
  set-de-binarios OR null-byte en el head).
- **Cableado**: `read_file.execute` tras `ctx.fs.resolve`, antes de `read_text`.
- **Orden**: independiente.
- **Test**: `test_read_rejects_binary` (`.png` → `is_error`).

## R7 · A3d + A4 — dedup `file_unchanged` + token/byte-cap

- **Comportamiento**: (A3d) si `(path,offset,limit)` ya está en `read_file_state` con mtime sin cambios →
  devolver stub `"<file unchanged; not re-sent>"` en vez del contenido (ahorra `cache_creation`). (A4)
  si `path.stat().st_size > MAX_READ_BYTES` (o estimación de tokens > cap) → error nudge
  `"exceeds maximum allowed tokens, use offset/limit"`.
- **Seam**: `ctx.read_file_state` (R0) para el dedup; constante `MAX_READ_BYTES` local para el cap.
- **Cableado**: `read_file.execute` consulta el estado + el tamaño antes de leer.
- **Orden**: tras R0. **Prioridad menor** (no hay xfail; optimización/cota, no bug). Documentado para
  no perder el cabo.
- **Test**: — (sin xfail; se añadiría al implementar).

## R8 · FIND-NATIVE-BASH = FIND-TOOL8 — shell persistente

- **Comportamiento**: `cd`/`export` persisten entre llamadas `bash` de la MISMA sesión (homólogo del
  único `exec`/`Shell.ts` vivo del canónico). `preventCwdChanges` para subagentes (B11): un worker no
  mueve el cwd del shell compartido.
- **Seam**: `tools/exec_env.py`. El `ToolExecEnvironment` (Protocol `run_shell`) ya existe; falta una
  **impl viva**: `PersistentShellExecEnvironment` que mantiene UN subproceso `bash` de larga vida y por
  cada `run_shell` escribe `command; printf "\n<sentinel>$?\n"` al stdin, lee stdout hasta el centinela y
  parsea el rc. `cwd`/env viven en ESE shell → persisten. Ciclo de vida (`aclose()`) para reaping (liga
  05·EXEC11).
- **Firma**: `class PersistentShellExecEnvironment: async def run_shell(command, *, timeout) -> ShellResult`
  (misma firma; intercambiable con `LocalExecEnvironment`). Estado interno: el proceso + un lock async
  (serializa comandos sobre el shell compartido).
- **Cableado**: el default de `ToolUseContext.exec_env` pasa a ser una instancia **por-ctx** de
  `PersistentShellExecEnvironment` (hoy `bash.py` cae a `LocalExecEnvironment()` fresco por llamada —
  ese es exactamente el bug). Como el test corre dos `bash` sobre el MISMO `ctx`, la persistencia debe
  colgar de `ctx.exec_env`. `preventCwdChanges = ctx.is_subagent` (B11): si subagente, rechazar/neutralizar `cd`.
- **Orden**: tras el bloque fs; prerrequisito de B9/B11.
- **Test**: `test_bash_persistent_shell` (`cd tmp` luego `pwd` → `tmp` en output).

## R9 · B12 — `interpretCommandResult` (exit-codes semánticos) + schema Bash (B1)

- **Comportamiento**: `is_error` deja de ser `returncode != 0` a secas. `interpret_command_result`
  reconoce códigos semánticos: `grep`/`find` rc=1 = "sin coincidencias" (NO error), etc. Además schema
  (B1): añadir `timeout` (per-input), `run_in_background`, `description`.
- **Seam**: helper `interpret_command_result(command: str, result: ShellResult) -> bool` en `bash.py`
  (o `tools/native/_shell.py`). El `run_in_background` liga el motor de background (B3 → 05·EXEC9/10) y
  queda como cabo de background, no de este ítem.
- **Cableado**: `bash.py` usa `is_error=interpret_command_result(command, result)` en vez de
  `result.returncode != 0`.
- **Orden**: tras R8.
- **Test**: `test_bash_grep_no_match_not_error` (rc=1 de grep-sin-match → `not is_error`).

## R10 · FIND-NATIVE-BG / GAP-TOOL2 = GAP-MODE2 — worktree en background + modelo de allowlists

- **Comportamiento**: (mínimo) `EnterWorktree`/`ExitWorktree` `safe_for_background=True` (el canónico los
  incluye en `ASYNC_AGENT_ALLOWED_TOOLS`; el runtime es erróneamente restrictivo). (Completo) sustituir el
  bool `safe_for_background` por-tool por **DOS allowlists nombradas** (E3): `ASYNC_AGENT_ALLOWED_TOOLS`
  (subagente async) e `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS` (teammate), reconciliando las divergencias de E4
  (Agent/Sleep/Config/Task* mal incluidos; worktree mal excluido).
- **Seam**: `tools/native/constants.py` (nuevo) con los dos `frozenset[str]`; el filtro de toolset para
  subagentes (05·filterToolsForAgent-equiv / `pool`) consulta membresía en vez del bool per-tool.
- **Cableado (mínimo)**: `EnterWorktreeTool.safe_for_background = True` (y Exit). **Cableado (completo)**:
  el ensamblado del pool para `is_subagent` filtra por `ASYNC_AGENT_ALLOWED_TOOLS`.
- **Orden**: independiente.
- **Test**: `test_worktree_allowed_in_background` (`safe_for_background is True`).

## R11 · FIND-NATIVE-TASK / G3 — `TaskUpdate.status` (+ el cabo de conflación)

- **Comportamiento**: `TaskUpdate` gana `status` (`pending`/`in_progress`/`completed`/`deleted`) +
  `owner` + `blocks`/`blockedBy`; auto-set de owner al marcar `in_progress` (homólogo del canónico).
- **Seam**: aquí aflora **G1** (conflación tasklist ↔ registry-de-ejecución). El fix **mínimo** (que hace
  pasar el xfail) es añadir `status` al schema y mapearlo a transiciones del `execution.tasks.registry`
  (`completed`→marcar done, `deleted`→`registry`-remove). El fix **completo** (homólogo real) exige
  **separar** un store de tasklist (homólogo `utils/tasks.ts`: persistencia por-archivo + high-water-mark
  de IDs + `claim`/`block` DAG) del registry de ejecución — eso es **Deuda B** (no vive en 10; ver
  `DEUDA-B-transversal.md`), porque la dimensión team/swarm (claim/TeamMembers) está ⛔ por el corte del
  README. En 10 se remedia la **superficie de tool** (status en el schema); la conflación de stores se
  eleva a Deuda B.
- **Campos**: `"status": {"enum":["pending","in_progress","completed","deleted"]}`, `"owner"`,
  `"blocks"`, `"blockedBy"` en `TaskUpdateTool.input_schema`.
- **Cableado**: `TaskUpdate.execute` traduce `status`→operación del registry (mínimo).
- **Orden**: independiente.
- **Test**: `test_task_update_has_status` (`"status" in properties`).

---

# Implementación de las tools ❌ no portadas

Diseño de las **capacidades reales** del canónico sin contraparte nativa (§K). NO son ⛔ (que se
descartan por corte de alcance): son ausencias que, de portarse, tienen forma concreta. Se ordenan por
acoplamiento (de menos a más externo).

## NotebookEdit (`NotebookEditTool`) — ∈ async-allowlist

- **Qué**: editar celdas de un `.ipynb` (JSON): `cell_id`/índice + `new_source` + `edit_mode`
  (`replace`/`insert`/`delete`). El `Edit` canónico **redirige** `.ipynb` aquí (R3).
- **Diseño**: native tool que carga el JSON del notebook, localiza la celda, aplica la mutación, y
  reescribe. **Reusa los seams de 10**: `ctx.fs.resolve(path, for_write=True)` (confinamiento) +
  `ctx.fs_safety.check_write` (R3) + el read_file_state guard (R2, el notebook debe leerse antes). Schema:
  `{path, cell_id?, cell_type?, new_source, edit_mode}`. `safe_for_background=True` (∈
  `ASYNC_AGENT_ALLOWED_TOOLS`, R10). Cierra el cabo de que `Edit` redirige pero el runtime "ni redirige ni
  edita notebooks".
- **Home**: 10 (es una fs-tool). Prerrequisitos: R2/R3.

## Brief (`BriefTool` / `SendUserMessage`)

- **Qué**: canal de **entrega al usuario** (markdown + attachments + `status: normal|proactive`), distinto
  de appendear texto al historial del modelo.
- **Diseño**: native tool que **emite un evento tipado** al `ctx.event_queue`/EventBus
  (`BriefEvent{markdown, attachments, status}`); el consumidor server-side lo enruta al usuario (server-side
  users/sessions, homólogo de comportamiento — no de la UI de terminal). Liga **A23 `new_messages`**
  (Deuda B): la entrega proactiva y los attachments requieren el canal de mensajes tipados. `ends_turn`
  opcional según `status`.
- **Home**: 10 (superficie de tool) + Deuda B (`new_messages` como habilitador).

## SyntheticOutput (`SyntheticOutputTool`)

- **Qué**: **salida final estructurada/sintética** del agente (liga `outputSchema` 09·A15 + G3).
- **Diseño**: tool que fija un resultado final estructurado validado contra un `output_schema`, vía
  `context_modifier` (que el loop YA aplica, §J) escribiendo en `app_state.native['final_output']`; el
  consumidor lo lee al cierre del turno. Depende del ítem **structured-output** de Deuda B (el
  `output_schema` en el `ToolProtocol` + `structured` en `ToolResult`).
- **Home**: Deuda B (structured-output) + 10 (la tool).

## LSP (`LSPTool`)

- **Qué**: code-intelligence (goToDefinition/findReferences/hover/symbols/callHierarchy). Pesada,
  IDE-acoplada.
- **Diseño**: exponer tras un seam `ctx.lsp: LspProvider | None` (Protocol con
  `definition/references/hover/symbols`); default `None` → la tool se auto-deshabilita (`is_enabled`
  gated). El integrador cablea un language-server real. **No se porta la impl**; se porta el **hueco
  inyectable** para que quien tenga un LSP lo enchufe.
- **Home**: capability aparte (candidata a un doc futuro); en 10 sólo se ancla el seam.

## Cron* (`ScheduleCronTool` → `CronCreate`/`CronDelete`/`CronList`)

- **Qué**: scheduling de agentes (feature `AGENT_TRIGGERS`/Kairos).
- **Diseño**: subsistema de scheduling nuevo. Las tools escriben/borran/listan entradas cron
  (`{schedule: cron-expr, prompt, subagent_type}`) vía `StorageContract` (persistencia homologada, 15);
  un **scheduler externo** (integrador) las consume y dispara agentes vía el runner (05). Feature-gated.
  El runtime aporta las tools + el store; el disparo temporal es del integrador (como el disparo de abort
  en 08).
- **Home**: subsistema de scheduling (no 10); en 10 se clasifica y se apunta el diseño.

## RemoteTrigger (`RemoteTriggerTool`)

- **Qué**: gestiona agentes remotos vía la **claude.ai CCR API** (OAuth in-process). Producto-específico.
- **Diseño**: mayormente ⛔ (acoplado a claude.ai). Si un integrador lo quiere genérico: seam
  `ctx.remote_trigger: RemoteAgentProvider | None` que el integrador implementa contra SU backend (no
  claude.ai). El runtime no porta la impl de claude.ai; expone el hueco.
- **Home**: ⛔/integrador; en 10 sólo se clasifica.
