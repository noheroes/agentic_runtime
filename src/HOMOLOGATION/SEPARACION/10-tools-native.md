# 10 · tools/native — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/10-tools-native.md`.
> **Ciclo A3·10·tools-native** del PLAN §4. Fuente: tracker `../10-tools-native.md` (leído íntegro 1→**794**
> —decía «1→793», corregido en `A-CIERRE·P4″`—:
> tesis + tablas A-H + I-naming + J-CORR09 + K-extras + §Hallazgos/cabos/gaps + recuento + ledger 2ª vuelta
> gate-11 + §Plan R0-R11 + §tools-no-portadas). Esquema: `00-LEGEND.md`.
> Costuras **ya validadas por A2** (`SKELETON-REPORT.md`: S16 `ToolPool`/`ToolDispatcher`, S26 estrategia,
> S9/S27 composición de battery, S20 repo id-opaco). Aquí se re-abre el runtime **real** (no el skeleton) para
> las afirmaciones de cableado (L09/L11), en ESTE ciclo.
>
> **Enumeración (Q2).** Unidad atómica = **celdas del grid comparativo** (igual que 03 contó celdas A-F, no las
> §Hallazgos): A(17: A1/A2/A3/A3b/A3c/A3d/A4-A14) + B(12) + C(5) + D(3) + E(4) + F(4) + G(5) + H(2) + **K(12
> extras)** = **64**. §I (`FIND-NATIVE-NAME`) es la vista transversal de **A1** (se pliega, cruzada en A1); §J
> (`CORR-09-CTXMOD`) es la corrección capturada en **D3** (se pliega, cruzada en D3); los `FIND-NATIVE-*` de
> §Hallazgos y el §Plan **R0-R11** son la **capa de remediación** que aterriza sobre estas celdas (referenciada en
> `acción`, no re-contada). Ni doble conteo ni celda huérfana.

## Naturaleza de la categoría
10 es la categoría **más BATTERY-intensa** de la SEPARACION: cada tool nativa es la **implementación estándar
OPCIONAL** de una capacidad del canónico (una tool concreta = definición de BATTERY en `00-LEGEND §2.2`). El *shape*
que todas comparten (`ToolProtocol` de 8 miembros) es **T1-CONTRATO** (propiedad de 01/09, no re-auditado aquí); lo
que 10 destila es **qué battery empaqueta cada tool + qué costura rellena + qué invariante debe reproducir**.

Tres divergencias estructurales del tracker gobiernan el reparto B:
1. **25 tools runtime vs ~44 canónicas.** El subconjunto núcleo (fs/shell/discovery/plan/worktree/agent/task/web) +
   una inventada (`clone_repository`) → **batteries**. Las ~19 ausentes se parten: capacidades reales no portadas
   (`NotebookEdit`/`LSP`/`Brief`/`SyntheticOutput`/`Cron*`/`RemoteTrigger`) → **battery o costura nueva**;
   swarm/teams (`SendMessage`/`Team*`) → **⛔-nombrado** (corte README); terminal (`PowerShell`/`REPL`) →
   **CLI-ONLY/INTERFAZ**; MCP → **→11**.
2. **La política sale del tool a costuras inyectables** (`ctx.fs` confina, PreToolUse gatea, `ctx.exec_env` backend):
   homologación **de comportamiento** (L10), el integrador aporta lo que el canónico lleva inline. La cara oscura:
   **los invariantes que el canónico impone DENTRO del tool** (read-before-edit, device-guard, línea-numerada) el
   runtime **no los tiene ni en el tool ni en un seam** → aterrizan aquí como **CORE-GAP reales** (10·R0-R9), no como
   delegación. Ésta es la **deuda A↔B propia** de 10.
3. **`context_modifier`/`ends_turn` SÍ se cablean** (corrección a 09·A24/D7; re-verificado ESTE ciclo en el
   ensamblador real, ver §3.2): el loop los aplica; 6 tools los producen. Pero **no están declarados en el
   protocolo** (attr dinámico `# type: ignore`) → DEUDA-B.

Convención de destino (como 03): `→NN` = homed en otra categoría con destino nombrado (L07); `battery_*` = paquete
battery concreto; `INTEGRADOR` = `00-INTEGRADORES.md`; `⛔-nombrado` = fuera de MVP de runtime **y** ambos
integradores, con satélite nombrado; `R0-R11` = entrada del §Plan de remediación del tracker (target codificado por
xfail).

---

## 1. Tabla por finding

### A · fs tools — `Read`/`Write`/`Edit`/`Glob`/`Grep` (`read_file`/`write_file`/`file_edit`/`glob`/`grep`)

| ID | resumen (comportamiento observable) | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **A1** naming 🔀 (=§I/`FIND-NATIVE-NAME`) | `read_file`/`write_file`/`glob`/`grep`/`bash` (snake) NO homologan `Read`/`Write`/`Glob`/`Grep`/`Bash`; `Edit` sí | núcleo | **BATTERY fs** + **T1-CONTRATO-adyacente** (el `name` es el boundary que matchean permission-rules/hooks) | `battery_fs_tools` (renombrar, **R1**) + OI-naming | — | **CORE-GAP (barato/alto-impacto):** renombrar los 5 `name`; el prompt/tool-schema emite el canónico; **las reglas del integrador migran en lockstep** (OI-naming) |
| **A2** `isReadOnly`/`isConcurrencySafe` ❌ | flags de readonly/concurrency por-tool | núcleo | **T1-CONTRATO** (protocolo, home 09) | **→09·tools-infra** (09·A3/A6) + `CG-TOOL-CONC` | — | **CORE-GAP (era 🔀 «sin consumidor», INVERTIDO por `D-08`):** en el canónico `isConcurrencySafe` **es el discriminador de la topología de ejecución** — `toolOrchestration.ts:91-116` particiona la tanda de `tool_use` por ese flag y `:19-82` corre cada lote **concurrentemente** (fan-out `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`, default 10, `:8-12`) **o serialmente**. Sin el flag **no hay ejecución paralela de tools**, que es comportamiento observable. Consumidor ya nombrado en el plan: `DEUDA-A §1.2(a):322` (`is_concurrency_safe` de `CG-MCP-3`). **No es divergencia `L10`, es capacidad ausente.** Acoplada a **D3**: ver `CG-TOOL-CONC` en §2.3 |
| **A3** Read imagen/PDF/notebook ❌ | salida tipada `text\|image\|notebook\|pdf` | núcleo | **BATTERY fs** (capacidad) **bloqueada por** canal `new_messages` | `battery_fs_tools` (image/pdf/notebook) **bloqueado→02/09** (`new_messages`, 09·A23) | — | **CORE-GAP con prerrequisito:** el canónico entrega imagen/pdf inyectando `newMessages`; sin ese canal (❌ 02/09) el runtime **no puede** portarlo. Cierra causa raíz; NotebookEdit = tool aparte (§K) |
| **A3b** números de línea ❌ | `addLineNumbers` (`{n}\t{línea}`) + cyber-reminder | núcleo | **BATTERY fs** (**R5**) | `battery_fs_tools` (helper `add_line_numbers`) | — | **CORE-GAP correctitud:** rompe el contrato del que dependen Edit/el modelo ("línea N"); prefijo de presentación (no rompe el match de Edit sobre `old_string` crudo) |
| **A3c** device/binary guards ❌ | `BLOCKED_DEVICE_PATHS` + rechazo de binarios | núcleo | **BATTERY fs** (**R6**) | `battery_fs_tools` (`BLOCKED_DEVICE_PATHS` + `_is_binary`) | — | **CORE-GAP disponibilidad (BUG REAL):** `read_file /dev/zero` **cuelga el proceso** (lectura infinita); binario→basura. No es ausencia estética |
| **A3d** dedup `file_unchanged` ❌ | stub si (path,rango,mtime) sin cambios (ahorra cache_creation) | núcleo | **BATTERY fs** (**R7**, depende R0) | `battery_fs_tools` (consulta `read_file_state`) | — | optimización de tokens; prioridad menor (sin xfail) |
| **A4** token/byte-cap 🟡 | `MaxFileReadTokenExceededError` + nudge a offset/limit | núcleo | **BATTERY fs** (**R7**) | `battery_fs_tools` (`MAX_READ_BYTES`) | — | **CORE-GAP cota:** hoy un archivo enorme vuelca todo al contexto; canónico corta por tokens |
| **A5** `readFileState` ❌ (`FIND-NATIVE-READSTATE`) | `{path→content,mtime,offset,limit}` que Edit/Write consultan | núcleo | **T2-BASE-MECANISMO** (estado de ctx) | **`ctx.read_file_state`** (**R0/GAP-NATIVE-1**) + `ForkSnapshot` copia (03·CtxR1) | — | **CORE-GAP arquitectural KEYSTONE:** prerrequisito duro de A7/A8 y de B9. Nuevo campo en `ToolUseContext`; `read_file` lo puebla; el fork lo copia (el hijo hereda lo leído por el padre) |
| **A6** `Edit.replace_all` ❌ | flag para reemplazar todas las ocurrencias | núcleo | **BATTERY fs** (**R4**) | `battery_fs_tools` (schema + `content.replace`) | — | **CORE-GAP paridad menor:** hoy `count>1`→error "Provide more context" |
| **A7** read-before-edit ❌ (`FIND-NATIVE-EDITGUARDS`, aterriza `FIND-CTX1`) | rechaza editar/escribir archivo existente no leído en la sesión (errorCode 6/2) | núcleo | **BATTERY fs** (**R2**, depende R0) | `battery_fs_tools` (`check_read_before_edit(ctx,path)` en Edit/Write) | — | **CORE-GAP correctitud/seguridad:** helper compartido consulta `ctx.read_file_state` (A5); Write sólo lo exige para archivos que YA existen |
| **A8** modified-since-read ❌ | `mtime>readTimestamp`→abort + re-chequeo atómico en `call` (`FILE_UNEXPECTEDLY_MODIFIED_ERROR`) | núcleo | **BATTERY fs** (**R2**) | `battery_fs_tools` (guard + re-chequeo pre-write) | — | **CORE-GAP:** hoy el runtime **pisa cambios silenciosamente** entre lectura y edición |
| **A9** safety/dangerous-files ❌ (aterriza `G8/FIND-TOOL9`) | settings.json / secretos / `.ipynb`-redirect / deny-rule / `MAX_EDIT_FILE_SIZE` | núcleo | **T2-COSTURA** (`FsSafetyPolicy`, **R3/GAP-NATIVE-2**) + **INTEGRADOR** (política) | costura **`ctx.fs_safety`** + default `DefaultFsSafety` + OI-fs-safety | — | **CORE-GAP (seam ausente):** el runtime **no expone el gancho**. GAP-NATIVE-2 = exponer el seam, no imponer política; `.ipynb`→NotebookEdit (§K) |
| **A10** quote-norm/encoding/line-endings/fileHistory/LSP/VSCode/skill-disc 🔀/⛔ | normalización de match + backup/undo + notify IDE | núcleo (fileHistory) | **🔀** (quote/encoding, L10) + **BATTERY fs** (fileHistory-undo = 03·B7) + **T2-COSTURA** (`ctx.lsp`) + **⛔** (VSCode) + **→12** (skill-disc) | `battery_fs_tools` (undo) + costura LSP (§K) + ⛔ IDE | — | quote/encoding/line-endings = 🔀 (edita bytes UTF-8 crudos; riesgo de fallo de match en comillas curvas/UTF-16); fileHistory = **CORE-GAP undo** (homed 10, =03·B7); LSP/VSCode = ⛔/costura; skill-disc→12 |
| **A11** `checkPermissions`/`getPath`/`backfillObservableInput`/`preparePermissionMatcher` ❌ | gate de escritura ve input+path (expandido) | núcleo | **T2-COSTURA** (home 06) | **→06·hooks/permissions** (GAP-02/GAP-TOOL1) | — | el gate del runtime es deny-por-nombre sin ver input/path; territorio GAP-02 |
| **A12** `outputSchema` tipado 🔀 | `{type:create\|update, structuredPatch, gitDiff}` | núcleo | **T1-CONTRATO** (protocolo, home 09) | **→09·tools-infra** (09·A15/A22) | — | runtime devuelve str plano (`"Edited {path}"`); structured-output = DEUDA-B/09. 🔀 (L10) |
| **A13** Glob `maxResults`=100 ✅/🟡 | cap + nota de truncado | núcleo | **BATTERY fs** | `battery_fs_tools` (`DEFAULT_GLOB_LIMIT=100`) | — | **homólogo fiel** (verificado 2ª vuelta `glob_tool.py:13,40-43`). 🟡 sólo por A2. Sort alfabético vs mtime = 🔀 menor (L10) |
| **A14** Grep 🟡 | head_limit/offset/VCS-exclude/max-cols, modos | núcleo | **BATTERY fs** | `battery_fs_tools` (`DEFAULT_HEAD_LIMIT=250`…) | — | **homólogo** (`re` de Python sobre `pathlib.glob`, no ripgrep; sin count/files-only/`-A/-B/-C`). Menos rico = 🔀 (L10), funcional |

### B · shell — `Bash` (`bash`) + `clone_repository` (inventada)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **B1** schema `timeout`/`run_in_background`/`description` 🟡 | superficie de entrada del Bash | núcleo | **BATTERY shell** (schema, **R9**) + **→05** (background) | `battery_shell` (schema) + →05·execution (bg) | — | hoy sólo `command`; `timeout` de clase 30s; `run_in_background` liga el motor de background (05·EXEC9/10) |
| **B2** shell persistente ❌ (`FIND-NATIVE-BASH`=`FIND-TOOL8`) | `cd`/`export` persisten entre llamadas de la sesión | núcleo | **T2-COSTURA** (`ToolExecEnvironment` impl viva, **R8**) | costura **`exec_env`** (`PersistentShellExecEnvironment`) | eje ejecución | **CORE-GAP comportamiento:** `bash.py`→`LocalExecEnvironment` **fresco cada vez** (verificado `bash.py`); el seam existe, falta la impl viva por-ctx |
| **B3** background tasks ❌ | `run_in_background`→task-id, auto-bg en timeout, budget Kairos | núcleo | **T2-BASE-MECANISMO** (home 05) | **→05·execution** (EXEC9/10) + Monitor/Sleep | eje ejecución | bloqueante puro; `ShellResult` sin dónde colgar `backgroundTaskId`. Home 05 |
| **B4** `bashToolHasPermission` (torre ~9K LOC) ❌ | AST del comando, prefix-rules, readonly-derivation | núcleo | **T2-COSTURA** (home 06) | **→06·permissions** (GAP-02) + **INTEGRADOR** | — | el runtime confía al gate deny-por-nombre + `ctx.exec_env` (bwrap); torre de seguridad = GAP-02, política del integrador |
| **B5** `maxResultSizeChars`/`outputSchema`/`interpretCommandResult`/git-track 🔀 | resultado rico + interpretación de exit-codes | núcleo | **BATTERY shell** (`interpret`, **R9**) + **→09** (outputSchema) + **⛔** (git-track) | `battery_shell` (R9) + →09 + ⛔ `gitOperationTracking` | — | `interpret`→R9 (CORE-GAP, ver B12); output plano/git-track = 🔀/⛔ (L10) |
| **B6** sandbox (`SandboxManager`) 🔀 | aislamiento por-comando | núcleo | **T2-COSTURA** (home 09) | **→09·tools-infra** (F3, `BwrapExecEnvironment`) | — | `BwrapExecEnvironment` grueso vs adaptador rico. Divergencia conocida (L10). Home 09 |
| **B7** `preparePermissionMatcher` (split compound) ❌ | `ls && git push` dispara hook `Bash(git *)` | núcleo | **T2-COSTURA** (home 06) | **→06·hooks** + auto-mode | — | ligan 06 (hook `if`) + política de auto-mode |
| **B8** `clone_repository` 🔀 AÑADIDO | git clone FUERA del sandbox con red + credencial efímera | núcleo | **BATTERY clone** (extensión B, **NO deuda** L10) + **T2-COSTURA** (`git_credentials`) | `battery_clone` + costura **`ctx.git_credentials`** + OI-git-cred | eje ejecución (subproceso privilegiado) | **valor propio de B:** token vía credential-helper efímero (env, **no** en argv ni `.git/config`), destino confinado `ctx.fs.resolve`. Diseño íntegro (verificado 2ª vuelta `clone_repository.py:120-128`). Cubre el hueco del MCP-GitHub (API sí, clone no) |
| **B9** sed-edit que actualiza `readFileState` ❌ | `applySedEdit` escribe + refresca read-state | núcleo | **BATTERY shell** (depende R8+R0) | `battery_shell` (liga R0) | — | refuerza que la ausencia de read-state es **sistémica** (Read/Edit/Write/Bash-sed). Depende de R0/R8 |
| **B10** `onProgress` heartbeat ❌ | `bash_progress` cada ~1s (output parcial/elapsed) | núcleo | **T2-COSTURA** (home 07) | **→07·events** (EVT6) + 09·D10 | — | el dispatcher del runtime ni transporta `onProgress`. Home 07 |
| **B11** `preventCwdChanges = !isMainThread` 🔀 | worker no mueve el cwd del shell compartido | núcleo | **BATTERY shell** (depende R8) | `battery_shell` (`preventCwd = ctx.is_subagent`, **R8**) | eje ejecución | matiz de FIND-TOOL8: al portar el shell persistente (R8), replicar la restricción por-thread |
| **B12** `dangerouslyDisableSandbox`/`interpretCommandResult`/hints/persist/image ❌/🔀 | escapes + exit-codes semánticos + persistencia de output | núcleo | **BATTERY shell** (`interpret`, **R9**) + **⛔/→09** (resto) | `battery_shell` (R9) + ⛔ satélites | — | **CORE-GAP correctitud (R9):** `is_error = returncode!=0` a secas (verificado `bash.py:33`) ⇒ **`grep` sin match (rc=1) se reporta ERROR**. `dangerouslyDisableSandbox`/hints/persist/image = ⛔/🔀 |

### C · discovery / meta — `Config`/`TodoWrite`/`Sleep`/`AskUserQuestion`/`ToolSearch`

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **C1** Config 🟡 | get/set settings vía `context_modifier` | núcleo | **BATTERY meta** | `battery_meta` (`ConfigTool`) | — | **homólogo funcional** (verificado ESTE ciclo `config.py:62-75`: `context_modifier` muta `app_state.native["config"]`). **CORE-GAP menor:** sin `supportedSettings` allow-list; store efímero vs settings.json (→15·storage) |
| **C2** TodoWrite ✅/🟡 | checklist de sesión `{id,content,status,priority}` | núcleo | **BATTERY meta** (= B4 `todos`) | `battery_meta` (`native["todos"]`; **`battery_todos` NO existe** en `BATTERIES §2.5` — TodoWrite vive DENTRO de `B25 battery_meta`) | — | **homólogo fiel** (enums espejo, `context_modifier`). 🟡: sin `isEnabled`, sin hook verification-agent. Nombre coincide |
| **C3** Sleep 🟡 | `asyncio.sleep(clamp(0,60))` | núcleo | **BATTERY meta** | `battery_meta` (`SleepTool`) | — | homólogo plausible (max 60s). Canónico gatea por feature + auto-bg sleeps largos (→05·Monitor). Nombre coincide |
| **C4** AskUserQuestion ✅/🟡 (=03·A32) | 1-4 preguntas × 2-4 opciones, HITL | núcleo | **BATTERY tool** (`AskUserQuestion`) | `battery_meta` (`ends_turn`) | — | **homólogo de comportamiento** (verificado ESTE ciclo `ask_user.py:97` `result.ends_turn=True`; schema idéntico): en vez de `requiresUserInteraction` cede el turno; el consumidor reinyecta la respuesta (HITL multi-turno server-side). 🟡: sin `isEnabled` |
| **C5** ToolSearch — | — | núcleo | **→09·tools-infra** | **→09·E** (E6 select singular = FIND-TOOL6; E7 scoring) | — | homed 09; no se re-audita en 10 (verificado 2ª vuelta `tool_search.py:53-55` `select:` singular) |

### D · plan mode — `EnterPlanMode`/`ExitPlanMode`

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **D1** EnterPlanMode ✅/🟡 | root-only; setea `native["plan_mode"]=True` vía `context_modifier` | núcleo | **BATTERY plan** (superficie de tool; capacidad home 14) | `battery_plan` (tool) + **→14·plan** | — | **homólogo** (verificado 2ª vuelta `plan_mode.py:40,45-49`). La tool vive en el battery de plan; el gate de plan-mode = **`04·B2`**/GAP-CTX2 (mode contract, →01·CTR-08). ⚠ **Colisión de auto-referencia corregida:** este «B2» **NO es `10·B2`** (que es el shell persistente / `FIND-NATIVE-BASH`/`R8`). La colisión ya se propagó: **`DEUDA-A §1.1·K1:187` cita «`10·B2`» como el gap de modo de permiso** — es incorrecto, y hay que corregirlo allí |
| **D2** ExitPlanMode ✅/🟡 | schema vacío, plan leído de disco, `ends_turn` | núcleo | **BATTERY plan** | `battery_plan` (tool) + **→14·plan** | — | **homólogo fiel** del V2 (verificado 2ª vuelta `plan_mode.py:79,106`). 🟡: sin enganche auto-mode/classifier (política) |
| **D3** `context_modifier` muta `plan_mode` 🟡 (=§J/`CORR-09-CTXMOD`) | el loop transporta y aplica `context_modifier`/`ends_turn` | núcleo | **T2-BASE-MECANISMO** (loop) + **DEUDA-B** (no declarado en protocolo) | mecanismo en `agent_loop.py` + **DEUDA-B** (declarar en `ToolResult`) + `CG-TOOL-CONC` | — | **CORR a 09·A24/D7** (❌→**🟡**, no ✅): re-verificado ESTE ciclo `agent_loop.py:332-337` (modifier) + 338-339/348 (ends_turn) + 300-313 (PreToolUse). **El tracker `§J:221-222` re-clasificó a 🟡 por DOS razones y aquí sólo se conservó una.** (a) **`DEUDA-B`:** `protocol.py` no declara los campos (`# type: ignore[attr-defined]` en `config.py:75`/`ask_user.py:97`). (b) **`CG-TOOL-CONC` (recuperada):** *«sin gating por `is_concurrency_safe==False` que el canónico exige»*. Leído el canónico (`D-08`, `toolOrchestration.ts` 1→EOF): la rama **concurrente NO aplica los modifiers al vuelo** — los **encola** por `toolUseID` (`:42-48`) y los aplica **al terminar el lote** (`:54-62`); sólo la rama **serial** los aplica inmediatamente (`:140-142`); `StreamingToolExecutor.ts:391` lo confirma. ⇒ **este ✅ era correcto SÓLO porque el dispatcher del runtime es secuencial**: es un estado **condicionado a que `A2` siga ausente**. Con `R10`/09 dando concurrencia, pasa a **incorrecto en silencio** |

### E · worktree — `EnterWorktree`/`ExitWorktree`

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **E1** Enter/Exit worktree ✅/🟡 | crear/salir worktree git aislado vía `context_modifier` | núcleo | **BATTERY worktree** | `battery_worktree` (`native["worktree_session"]`) | — | **homólogo fiel** (verificado 2ª vuelta `worktree.py:65,73-88,144-149`). 🟡: output str plano vs tipado; sin `isDestructive` |
| **E2** `safe_for_background` F→T 🔀 (`GAP-TOOL2`=`GAP-MODE2` RESUELTO) | worktree permitido en agente async | núcleo | **T2-BASE-MECANISMO** (bg-gating, **R10**) | `battery_worktree` (`safe_for_background=True`) + costura allowlist | eje ejecución | **CORE-GAP-restrictividad:** el canónico lo incluye en `ASYNC_AGENT_ALLOWED_TOOLS`; runtime `=False` (verificado 2ª vuelta `worktree.py:61,129`) ⇒ **más restrictivo de lo debido** |
| **E3** modelo de bg-gating 🔀 (`FIND-NATIVE-BG`) | DOS allowlists nombradas vs bool por-tool | núcleo | **T2-BASE-MECANISMO** (filtro toolset, **R10**) | costura **allowlist** (`ASYNC_AGENT_ALLOWED_TOOLS`/`IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`) + **→05** | eje ejecución | sustituir el bool `safe_for_background` por dos `frozenset[str]`; el filtro de toolset para subagentes consulta membresía (=03·E5, `resolver.py:45-48`) |
| **E4** reconciliación celda a celda 🔀 | Agent/Sleep/Config/Task* mal incluidos; worktree mal excluido | núcleo | **T2-BASE-MECANISMO** (**R10**) | costura allowlist (reconciliar E4) | eje ejecución | verificado 2ª vuelta celda a celda; **cabo 04·GAP-MODE2 (worktree+Agent+TaskStop+TaskOutput) cubierto** |

### F · agent — `Agent` (superficie de tool; ejecución = 05)

> ⛔ **PRECONDICIÓN QUE INVALIDA EL «✅ de comportamiento» DE TODA ESTA SECCIÓN Y DE LA G** (regla (32): el
> consumidor vive en otro paquete ⇒ el estado exige abrirlo; incorporado en esta pasada). **`DEUDA-B §5·DB-27`:
> el factory nunca llama `set_runner()` ⇒ TODO spawn de subagente falla hoy.** **`DB-h1`/`RV-8`:
> `create_runtime` nunca llama `set_registry()` ⇒ las 6 tools `Task*` levantan `RuntimeError` → `ToolResult.error`
> **silenciosamente en cada llamada**.** Y **`BATTERIES §6·CAT-h5:339-341`** lo confirma desde el catálogo:
> `battery_agent`/`battery_task` tienen *«alcance hoy inoperante»* y **su composición no es verificable hasta
> `K7`**. ⇒ Los ✅/🟡 de F1-F4 y G1-G5 son **✅ de superficie de tool (schema/delegación leídos en fuente)**,
> **NO** ✅ de comportamiento observable. No se re-clasifican las celdas —el defecto está en el cableado del
> factory, no en la tool— pero **queda escrito aquí**, que es donde faltaba.

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **F1** nombre `Agent` + spawn ✅ | spawn de subagente, depth-cap 5 | núcleo (id opaco) | **BATTERY agent-tool** (superficie; ejecución home 05) | `battery_agent` (tool) + **→05·execution** | eje ejecución | homólogo (verificado 2ª vuelta `agent.py:73` `_MAX_SUBAGENT_DEPTH=5`) |
| **F2** schema `subagent_type`/`run_in_background`/`inherit_messages` 🔀 | superficie de spawn | núcleo | **BATTERY agent-tool** | `battery_agent` (tool) | eje ejecución | sin `name`/`team_name` (swarm ⛔); `inherit_messages` = **extensión B** (fork con/sin historia, no deuda L10) |
| **F3** `filterDeniedAgents`/fork/`agentMemory`/`builtInAgents` 🔀/❌ | runner/fork/registry/memoria | núcleo | **T2-BASE-MECANISMO/COSTURA** (home 05) + **BATTERY memory** (13) | **→05·execution** (fork/runner) + **→13·memory** | eje ejecución | 10 sólo constata que la **tool** delega en `get_runner().run(fork_ctx, background=)` (verificado 2ª vuelta `agent.py:105`) |
| **F4** `run_in_background`→task-id ✅ | fg→resultado directo | núcleo | **BATTERY agent-tool** | `battery_agent` + →05 | eje ejecución | homólogo del patrón |

### G · task tools — `TaskCreate`/`Get`/`List`/`Update`/`Stop`/`Output`

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **G1** store: conflación tasklist↔registry 🔀 (`FIND-NATIVE-TASK`) | `task_tools.py` opera sobre `execution.tasks.registry`, no una tasklist persistida | núcleo | **DEUDA-B** (conflación de stores) + **→05** | **DEUDA-B (separar stores)** + →05·execution | eje ejecución | **cabo task_tools RESUELTO:** el canónico `Task*` es tablero TODO persistido; el runtime lo mapeó AL registry de ejecución = conflación (verificado 2ª vuelta `task_tools.py:10,54`). Separar = DEUDA-B (dim. team/swarm ⛔) |
| **G2** TaskCreate campos 🟡 | `subject`/`description` → `register(...)` | núcleo | **BATTERY task-tool** (superficie) | `battery_task` (surface) | eje ejecución | sin `activeForm`/`metadata`/`owner`/`blocks`/`shouldDefer`/gating/hooks |
| **G3** `TaskUpdate.status` ❌ | transiciones pending/in_progress/completed/deleted + owner + DAG | núcleo | **BATTERY task-tool** (**R11**) + **DEUDA-B** (conflación) | `battery_task` (schema `status`, **R11**) + DEUDA-B (stores) | eje ejecución | **CORE-GAP superficie:** hoy `TaskUpdate` sólo `task_id`+`description` (verificado 2ª vuelta `task_tools.py:137-142`). Fix mínimo = `status` al schema→registry; separación real = DEUDA-B |
| **G4** `claimTask`/`blockTask`/`TeamMembers` ⛔/❌ | dimensión team/swarm de la tasklist | — | **⛔-nombrado** (teams/swarm) | ⛔ **corte README** (coordinator/swarm) | — | el runtime no tiene teammates; razón de que `Task*` sea wrapper fino |
| **G5** TaskGet/List/Output/Stop 🟡 | read-only + kill, scopeado por `session_id` | núcleo | **BATTERY task-tool** | `battery_task` (`_scoped_get` por `session_id`) | eje persistencia (scope por sesión) | scoping espejo de `getTaskListId()` (verificado 2ª vuelta `task_tools.py:17-32,187`); leen del registry de ejecución (G1). `TaskStop`→`registry.kill` |

### H · web — `WebFetch`/`WebSearch`

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **H1** WebFetch 🔀 (`FIND-NATIVE-WEB`) | `urllib` crudo, sólo http/https, cap 100K | núcleo | **BATTERY web** (mínimo viable, L10) + **INTEGRADOR** (domain-rules) | `battery_web` + OI-web-policy | — | sin markdown/cache/domain-rules (verificado 2ª vuelta `web_fetch.py:44`, CWE-22 mitigado). La política de dominio = integrador/sandbox-adapter (09·F3). Divergencia deliberada |
| **H2** WebSearch 🔀 | Serper.dev (`SERPER_API_KEY`), filtros `site:` | núcleo | **BATTERY web** (provider adaptado) + **INTEGRADOR** (elección de provider) | `battery_web` + OI-web-policy | — | mecanismo **distinto** (provider externo, no el web_search nativo del modelo; verificado 2ª vuelta `web_search.py:74-95`). Valor: funciona sin el tool nativo del proveedor. Sin `isEnabled` |

### K · extras canónicos sin contraparte nativa (§K del tracker)

| ID | tool canónica | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **K1** `BriefTool`/`SendUserMessage` ❌ | canal de **entrega al usuario** (markdown+attachments+`status`) | núcleo | **BATTERY tool** + **T2-COSTURA** (event-sink, bloqueado por `new_messages`) | `battery_brief` (emite `BriefEvent` al `ctx.event_queue`) + **→02/09** (`new_messages`) + OI-B | — | **CORE-GAP capacidad:** entrega proactiva + attachments requieren el canal de mensajes tipados (A23/`new_messages`, DEUDA-B); el integrador enruta al usuario (=OI-B) |
| **K2** `SyntheticOutputTool` ❌ | salida final estructurada/sintética | núcleo | **BATTERY tool** + **T1-CONTRATO** (structured-output, home 09) | `battery_synthetic` (`context_modifier`→`native["final_output"]`) + **→09** (`output_schema`) | — | **CORE-GAP:** depende del `output_schema` en `ToolProtocol` + `structured` en `ToolResult` (09·A15/DEUDA-B) |
| **K3** `NotebookEditTool`/`NotebookEdit` ❌ | editar celdas `.ipynb` (`edit_mode` replace/insert/delete) | núcleo | **BATTERY fs** (reusa seams de 10) | `battery_fs_tools` (nueva tool; **prereq R2/R3**) | — | **CORE-GAP capacidad fs:** reusa `ctx.fs.resolve` + `ctx.fs_safety` (R3) + read-state guard (R2); `safe_for_background=True` (∈ allowlist R10). Cierra el cabo "Edit redirige `.ipynb` pero el runtime ni redirige ni edita" |
| **K4** `LSPTool`/`LSP` ❌ | code-intelligence (definition/references/hover/symbols) | núcleo | **T2-COSTURA** (`ctx.lsp: LspProvider\|None`) + **INTEGRADOR** | costura **`ctx.lsp`** (default `None`→auto-deshabilita) + OI-lsp | — | **no se porta la impl** (pesada, IDE-acoplada); se ancla el **hueco inyectable** — el integrador cablea un language-server real. Candidata a doc de capability aparte |
| **K5** `ScheduleCronTool`/`Cron*` ❌ | scheduling de agentes (`{schedule,prompt,subagent_type}`) | núcleo | **BATTERY tool** + **T2-COSTURA** (`StorageContract`, 15) + **INTEGRADOR** (scheduler) | `battery_cron` (tools escriben/borran/listan vía storage) + **→15** + OI-cron | eje persistencia | subsistema de scheduling: el runtime aporta tools+store; el **disparo temporal** es del integrador (como el disparo de abort en 08). Feature-gated |
| **K6** `RemoteTriggerTool`/`RemoteTrigger` ❌/⛔ | agentes remotos vía claude.ai CCR API | — | **⛔** (claude.ai) + **T2-COSTURA opcional** (`ctx.remote_trigger`) | ⛔ producto-específico — **NO genera obligación de integrador** | — | mayormente ⛔ (acoplado a claude.ai). **Corregido:** antes daba destino «OI-remote (si genérico)», un OI-* **sin ficha en §2.5 y ausente de `00-INTEGRADORES §1.7`** — exactamente el «→ integrador a secas» que `Q4` dice no cometer. No es **contrato base común** (ningún integrador lo necesita para operar): si uno lo quisiera, la costura opcional `ctx.remote_trigger: RemoteAgentProvider \| None` es **realización específica suya**, no obligación del catálogo. El conteo de OI-* de 10 queda en **9**, coherente con `00-INTEGRADORES §1.7:185` y `BATTERIES §4.1:219-220` |
| **K7** `SendMessageTool`/`SendMessage` ⛔ | mensajería inter-agente (teams/UDS/bridge) | — | **⛔-nombrado** (swarm) | ⛔ **corte README** (05·EXEC12 pendingMessages) | — | swarm/coordinator fuera de core |
| **K8** `TeamCreateTool`/`TeamDeleteTool` ⛔ | ciclo de vida de equipos/swarm | — | **⛔-nombrado** (teams) | ⛔ **corte README** (`~/.claude/teams/`) | — | teams fuera de core |
| **K9** `PowerShellTool`/`PowerShell` ⛔ | shell de Windows | cáscara-CLI | **⛔-nombrado** (OS/terminal) | ⛔ Windows (runtime = Linux server-side) | — | terminal/OS fuera de runtime headless; si un integrador Windows lo quiere, es realización de interfaz |
| **K10** `REPLTool`/`REPL` ⛔ | REPL de terminal | cáscara-CLI | **CLI-ONLY / INTERFAZ** | **INTEGRADOR** (interfaz terminal) + ⛔ core | — | interfaz de terminal; realización específica de un integrador con REPL, no runtime |
| **K11** `MCPTool`/`McpAuthTool` →11 | wrapper de tools MCP + OAuth | núcleo | **T2-COSTURA** (home 11) | **→11·mcp** | — | contraste en 11·cap-mcp |
| **K12** `ListMcpResourcesTool`/`ReadMcpResourceTool` →11 | recursos MCP | núcleo | **T2-COSTURA** (home 11) | **→11·mcp** | — | el runtime SÍ tiene `resource_tools.py`; contraste en 11 |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica — **DOCE** (nombre · productor invoca · consumidor implementa)

> **Estado en `SEAMS.md` (sonda `c24/c29`, corregido en esta pasada).** `SEAMS:4` declara como fuentes las `§2.1`
> de **{01,16,07,02,05,09}**: **10 no es fuente del registro de costuras**, y por eso **CINCO de estas doce no
> tienen número `S`** — `ctx.read_file_state` (**el KEYSTONE del par**), `FsSafetyPolicy`, `ctx.git_credentials`,
> la allowlist de bg-gating y `ctx.lsp`. Hay que darles número en `SEAMS`, no renumerar nada aquí.
> En **sentido inverso**, `SEAMS` asigna a 10 dos consumos que este doc **no tiene como ficha**: **`§S23`**
> (`on_agent_teardown`) nombra *«10 (bash-bg)»* como consumidor del **reaping** — liga el `aclose()` de `R8` y
> `05·EXEC11`— y **`§S25`** delega ***«isolation→10/18»***. Ambos quedan **abiertos**, no cerrados.
- **`ctx.read_file_state`** (T2-BASE-MECANISMO, estado de ctx; **R0/GAP-NATIVE-1**, KEYSTONE) — productor:
  `read_file.execute` (puebla) + Bash-sed (B9) · consumidor: `Edit`/`Write` guard (R2). **Hoy ausente.** El
  `ForkSnapshot` debe **copiarlo** (03·CtxR1). Prerrequisito duro de R2/R7/B9.
- **`FsSafetyPolicy` / `ctx.fs_safety`** (T2-COSTURA; **R3/GAP-NATIVE-2**) — productor: `Edit`/`Write` llaman
  `check_write(path,content)` tras el confinamiento · consumidor: base `DefaultFsSafety` (settings/`.ipynb`/tamaño)
  o el integrador (deny-rules/secret-scan). **Seam ausente.**
- **`ToolExecEnvironment` (impl viva `PersistentShellExecEnvironment`)** (T2-COSTURA; **R8**) — productor:
  `bash.execute`→`run_shell` · consumidor: impl por-ctx que mantiene UN subproceso `bash` vivo (`cwd`/env
  persisten). **Seam existe** (`exec_env.py`), **impl viva ausente** (hoy `LocalExecEnvironment` fresco).
  `preventCwd = ctx.is_subagent` (B11). Ciclo de vida `aclose()` liga 05·EXEC11.
- **`GitCredentialProvider` / `ctx.git_credentials`** (T2-COSTURA, **existe**) — productor: `clone_repository` ·
  consumidor: el integrador aporta credential-helper efímero (token nunca en argv/`.git/config`). Extensión B.
- **`ConfinedFilesystem` / `ctx.fs`** (T2-COSTURA, **existe**) — productor: cada fs-tool (`resolve(...,for_write=)`)
  · consumidor: default de infra / integrador. Confinamiento de workspace verificado (09·G8).
- **allowlist de bg-gating** (T2-BASE-MECANISMO; **R10**) — productor: el ensamblado del pool para `is_subagent`
  filtra por membresía · consumidor: base con `ASYNC_AGENT_ALLOWED_TOOLS`/`IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`
  nombradas (reemplaza el bool `safe_for_background`). Cruza 05 (`resolver.py:45-48`, =03·E5).
- **PreToolUse hook-gate** (T2-COSTURA, **cableado** — verificado ESTE ciclo) — productor:
  `agent_loop.py:300-313` (dispara `HookEvent.PRE_TOOL_USE`, honra `block`+`modified_input`) · consumidor: el hook
  del integrador (política). **Lo que falta = `checkPermissions` por-tool con modos + input al gate del dispatcher**
  (GAP-02, home 06; el modo = 01·CTR-08).
- **`context_modifier`/`ends_turn` en `ToolResult`** (T2-BASE-MECANISMO del loop, **cableado** — verificado ESTE
  ciclo `agent_loop.py:332-339`) — productor: 6 tools (config/todo/plan-enter/plan-exit/worktree →
  `context_modifier`; ask_user/exit-plan → `ends_turn`) · consumidor: el loop. **DEUDA-B:** `protocol.py` no
  declara los campos (attr dinámico).
- **choke point de presentación** (T2-COSTURA `PathPresentation`, **cableado** — verificado ESTE ciclo
  `dispatcher.py:41-42` `sanitize_output`) — = 03·D2. Todo `ToolResult` pasa por aquí.
- **canal `new_messages`** (T1-CONTRATO/T2-COSTURA, **ausente ❌**) — habilitaría A3 (image/pdf) + K1 (Brief). Home
  **02/09** (09·A23). Prerrequisito de esas capacidades.
- **`ctx.lsp: LspProvider | None`** (T2-COSTURA, **ausente**) — K4/LSP. Default `None`→tool auto-deshabilitada.
- **`StorageContract`** para cron/tasklist (T2-COSTURA) — K5/G1. Cruza 15·storage.

### 2.2 Batteries que alimenta (nombre · alcance)
- **`battery_fs_tools`** — `Read`/`Write`/`Edit`/`Glob`/`Grep` (+ `NotebookEdit`). Alberga los guards R0/R2/R3/R5/
  R6/R7 + fileHistory-undo (A10=03·B7). Consume `ctx.fs`, `ctx.fs_safety`, `ctx.read_file_state`. **Battery más
  gruesa de 10** (concentra la deuda A↔B).
- **`battery_shell`** — `Bash`. Persistent-shell (R8) + `interpretCommandResult` (R9) + sed-edit (B9) + preventCwd
  (B11). Consume `ctx.exec_env` (impl viva).
- **`battery_web`** — `WebFetch`/`WebSearch`. Mínimos viables provider-adaptados; política de dominio/provider =
  integrador.
- **`battery_meta`** — `Config`/`TodoWrite`/`Sleep`/`AskUserQuestion`. Consumidores de `context_modifier`/`ends_turn`.
- **`battery_worktree`** — `EnterWorktree`/`ExitWorktree`. `safe_for_background=True` (R10).
- **`battery_clone`** — `clone_repository` (extensión B, git_credentials seam).
- **`battery_agent`** / **`battery_task`** — superficie de tool; la mecánica de ejecución/registry = **→05**.
- **`battery_plan`** — `EnterPlanMode`/`ExitPlanMode` (tools); la capacidad de plan = **→14**.
- **Batteries/tools nuevas por capacidad no portada:** `battery_brief` (K1, +`new_messages`), `battery_synthetic`
  (K2, +structured-output), `battery_cron` (K5, +`StorageContract`).
- **`tool_search`** → homed **09·E** (no origina battery en 10).

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
Findings que **originan/aterrizan en 10** (el battery/base debe reproducir un comportamiento y hoy no):
- **`FIND-NATIVE-READSTATE` (A5, R0/GAP-NATIVE-1, ❌ arquitectural KEYSTONE)** — `ctx.read_file_state` ausente ⇒ sin
  base para read-before-edit. Prerrequisito duro de R2/R7/B9 + fork-copy (03·CtxR1).
- **`FIND-NATIVE-EDITGUARDS` (A7/A8, R2, ❌ correctitud/seguridad)** — read-before-edit + modified-since-read; hoy el
  runtime **pisa cambios silenciosamente**. Aterriza `FIND-CTX1`.
- **`GAP-NATIVE-2` (A9, R3, ❌ seam)** — `FsSafetyPolicy` ausente; el runtime no expone el gancho de safety-fs.
  Aterriza `G8/FIND-TOOL9`. + OI-fs-safety (política).
- **`FIND-NATIVE-READ` correctitud (A3b/A3c, R5/R6)** — números de línea (**rompe contrato Edit/modelo**) +
  device-guard (**BUG de disponibilidad: `read /dev/zero` cuelga**). A4/A3d (R7: token-cap + dedup) = cota/optim.
- **A6/R4** — `Edit.replace_all` (paridad menor).
- **`FIND-NATIVE-BASH` (B2, R8, ❌ comportamiento)** — shell persistente (`ToolExecEnvironment` impl viva). Habilita
  B9 (sed-edit+read-state) y B11 (preventCwd). = `FIND-TOOL8`.
- **B12/R9 `interpretCommandResult` (❌ correctitud)** — `is_error=returncode!=0` a secas ⇒ `grep` sin match reportado
  como error. Exit-codes semánticos.
- **`FIND-NATIVE-BG` (E2/E3/E4, R10, 🔀→CORE-GAP-restrictividad)** — bool `safe_for_background` diverge del modelo de
  DOS allowlists; **worktree mal excluido** (GAP-TOOL2/MODE2 resuelto). Cruza 05.
- **G3/R11 `TaskUpdate.status` (❌ superficie)** — status/owner/DAG ausentes en el schema. (La conflación de stores
  G1 = DEUDA-B, no CORE-GAP.)
- **`CG-TOOL-CONC` (A2+D3, NUEVO en `A-CIERRE·P4″`, resuelto por `D-08`)** — **una sola costura canónica que este
  doc tenía partida en dos celdas suavizadas.** `toolOrchestration.ts` (leído 1→EOF): `partitionToolCalls:91-116`
  particiona la tanda de `tool_use` por `isConcurrencySafe` y `runTools:19-82` corre cada lote **concurrente**
  (fan-out default **10**, `:8-12`) **o serial**; y el lote concurrente **encola** los `contextModifier` por
  `toolUseID` (`:42-48`) aplicándolos **al terminar el lote** (`:54-62`), no al vuelo como la rama serial
  (`:140-142`). ⇒ (1) `A2` **no es** «flag sin consumidor»: es el **discriminador de la topología**, y sin él el
  runtime no puede ejecutar tools en paralelo — capacidad canónica observable ausente, con consumidor ya
  nombrado en `DEUDA-A §1.2(a):322`; (2) el estado de `D3` está **condicionado a que `A2` siga ausente**: el
  dispatcher secuencial del runtime hace hoy lo mismo que la rama serial del canónico, pero **no hay encolado de
  modifiers**, así que el día que el dispatcher gane concurrencia (`R10`/09) `D3` se rompe **en silencio**.
  **Remediación:** al portar `is_concurrency_safe` (home 09), portar **con él** el encolado de `context_modifier`
  por lote; el orden es `09·A3/A6` → encolado → concurrencia del dispatcher, nunca al revés.
- **Capacidades no portadas (§K):** K1 Brief, K2 SyntheticOutput, K3 NotebookEdit, K4 LSP (seam), K5 Cron — ausencias
  con forma concreta (batteries/costuras), no ⛔.

CORE-GAPs que 10 **detecta pero homea fuera** (destino nombrado, L07): A3 image/pdf + K1/K2 → bloqueados por
`new_messages` **→02/09**; B3/B10 background+onProgress **→05·EXEC9/10 / 07·EVT6**; A11/B4/B7 `checkPermissions`
por-tool **→06/GAP-02**; A12/B5-outputSchema **→09**; B2-`mode` (plan-gate) **→01·CTR-08**; F3 fork/runner/memoria
**→05/13**.

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10)
- **`context_modifier`/`ends_turn` no declarados en `ToolResult`** (§J/D3) — se adjuntan por attr dinámico
  (`# type: ignore[attr-defined]`, verificado ESTE ciclo `config.py:75`/`ask_user.py:97`). **Confirmado abriendo
  `protocol.py:21-36` ESTE ciclo:** `ToolResult.__init__` sólo declara `tool_name/output/is_error/is_timeout/
  is_aborted/metadata`; los dos campos NO existen en el tipo. **Declararlos en `protocol.py`** (frágil sin tipo,
  pero funciona). Deuda de higiene, no A↔B.
- **`LAT-TOOL1` / `category` slot muerto — confirmado en fuente ESTE ciclo:** `ToolProtocol:56` **sí declara**
  `category: ToolCategory` (y cada nativo lo setea), pero ningún nativo lo lee (ya homed 09/DEUDA-B).
  Anti-padding (L10/L11): el canónico tampoco usa este enum como driver → **NO deuda A↔B** (sus
  `isReadOnly`/`isDestructive`, que sí consume, son A2/A6 — ésa sí es deuda, ver A2). *(Esta entrada estaba
  **duplicada literalmente** en esta misma sección; fusionadas en una, la sección tiene **4** entradas, no 5.)*
  ⚠ **`DB-06` (`DEUDA-B §3.A`) ordena BORRAR `ToolProtocol.category` y es «el radio de explosión más grande de
  las 12 entradas BORRAR»: ~25 productores, de los que **18 son tools nativas de ESTE par**, más
  `scripts/e2e_runtime_test.py:37,46` y 24 archivos de test. El coste de ejecución aterriza aquí, no en 09.
- **G1 conflación tasklist↔registry-de-ejecución** — `task_tools.py` funde dos conceptos canónicos distintos
  (`utils/tasks.ts` tablero TODO persistido ≠ `execution.tasks.registry`). Separar el store de tasklist = DEUDA-B
  (la dim. team/swarm está ⛔). No es deuda A↔B directa (el runtime opera, sólo conflaciona).
- **`clone_repository`** (B8) — inventada, **sin contraparte canónica** ⇒ **NO deuda A↔B** (anti-padding L10); es
  valor propio de B, bien diseñado. Sólo se registra la costura `git_credentials` que exige.
- **`inherit_messages`** (F2) — extensión B del schema de Agent (fork con/sin historia), sin contraparte → NO deuda.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05)
Con **capacidad observable · origen (costura del base) · firma que consume · cableado en el integrador · orden ·
criterio de aceptación**:

- **OI-fs-safety · Aportar la política de safety-fs** *(contrato base común: todo integrador decide qué escrituras
  bloquear)* — **capacidad:** rechazar escrituras peligrosas (settings.json, secretos, deny-rules, tamaño). **origen:**
  A9 (R3/GAP-NATIVE-2). **firma:** `FsSafetyPolicy.check_write(path,content) -> str | None`; el base provee
  `DefaultFsSafety` (settings/`.ipynb`/tamaño), el integrador **sustituye la instancia** en `ctx.fs_safety`. **cableado:**
  `agentic_code` = default minimal; `agentic_assistant` = deny-rules per-tenant + secret-scan server-side. **orden:**
  tras R3 (definir el seam). **aceptación:** un `Write` a `.claude/settings.json` → `is_error`; el integrador puede
  ampliar sin tocar el battery.
- **OI-perm · Aportar la política de permiso por-tool (GAP-02)** *(contrato base común)* — **capacidad:** decidir
  allow/deny/ask por-tool viendo input+path (`Bash(git *)`, `Write` a path denegado). **origen:** A11/B4/B7 + §J. **firma:**
  el hook **PreToolUse** (`HookEvent.PRE_TOOL_USE`, **cableado** `agent_loop.py:300-313`) que honra `block` +
  `modified_input`; falta el `checkPermissions` por-tool con modos + el input al gate del dispatcher (06/GAP-02) y el
  campo `mode` (01·CTR-08). **cableado:** el integrador implementa el hook-runner con su torre de reglas.
  **orden:** requiere el `mode` en el contrato (01) + el gate del dispatcher (06). **aceptación:** `ls && git push`
  dispara la regla `Bash(git *)`; una escritura en plan-mode se deniega. **nota:** el runtime dispara el punto; la
  **política** es del integrador (verificado ESTE ciclo: el gate existe y transporta block/modified_input).
- **OI-git-cred · Proveer credenciales de clonado** *(contrato base común para clone)* — **capacidad:** dar al
  `clone_repository` un token efímero sin exponerlo al modelo. **origen:** B8. **firma:** `GitCredentialProvider`
  (`ctx.git_credentials`) → credential-helper efímero (env `GIT_CLONE_TOKEN`, **no** argv/`.git/config`). **cableado:**
  `agentic_code` = token del host; `agentic_assistant` = token per-tenant del vault. **orden:** al construir el tool de
  clone. **aceptación:** un clone privado funciona con el token nunca visible en argv/config/modelo.
- **OI-web-policy · Aportar política de web** *(contrato base común, realización específica)* — **capacidad:** reglas de
  dominio (`WebFetch(domain:*)`) + elección de provider de búsqueda. **origen:** H1/H2 (`FIND-NATIVE-WEB`). **firma:**
  el sandbox-adapter/red del integrador (09·F3) + la config del provider (`SERPER_API_KEY` o web_search nativo).
  **cableado:** `agentic_code` = red del host + Serper opcional; `agentic_assistant` = allow/blocklist per-tenant +
  provider gestionado. **orden:** al construir el battery web. **aceptación:** un dominio bloqueado se rechaza; la
  búsqueda funciona con el provider configurado.
- **OI-naming · Migrar las reglas a los nombres canónicos** *(contrato base común — transversal a R1)* — **capacidad:**
  que permission-rules/hooks/CLAUDE.md matcheen tras el renombrado `read_file→Read` etc. **origen:** A1/§I
  (`FIND-NATIVE-NAME`, R1). **firma:** el runtime **emite** los nombres canónicos; las reglas del integrador se migran
  en lockstep. **cableado:** ambos integradores actualizan sus `allowed_names`/matchers. **orden:** junto a R1 (el
  runtime debe emitir el canónico para que las reglas puedan matchear). **aceptación:** `Bash(git *)` matchea la tool
  renombrada.
- **OI-B · Drenar y entregar Brief/notificaciones** *(contrato base común; =OI-B de 03)* — **capacidad:** entregar al
  usuario los `BriefEvent` (markdown+attachments+status) y las notificaciones de background. **origen:** K1 + B9/A33
  (03). **firma:** el battery Brief emite `BriefEvent` al `ctx.event_queue`; el integrador lo enruta (server-side
  users/sessions). **cableado:** `agentic_code` = render a terminal; `agentic_assistant` = push/inbox al front.
  **orden:** requiere `new_messages` para attachments/proactivo (02/09). **aceptación:** un `Brief` proactivo llega al
  transporte del integrador.
- **OI-lsp · Cablear un language-server** *(específico)* — **capacidad:** code-intelligence. **origen:** K4/LSP. **firma:**
  `ctx.lsp: LspProvider | None` (default `None`→tool auto-deshabilitada). **cableado:** el integrador con IDE enchufa un
  LSP real; sin él la tool no aparece. **orden:** al anclar el seam. **aceptación:** con provider, `LSP goToDefinition`
  responde; sin provider, la tool no se ofrece.
- **OI-cron · Consumir el store de cron y disparar** *(específico)* — **capacidad:** ejecutar los agentes programados.
  **origen:** K5/Cron*. **firma:** las tools escriben `{schedule,prompt,subagent_type}` vía `StorageContract` (15); un
  **scheduler externo** del integrador consume y dispara vía el runner (05). **cableado:** `agentic_assistant` = worker
  de scheduling; `agentic_code` = cron del host (opcional). **orden:** tras el store (15). **aceptación:** una entrada
  cron dispara un agente a la hora indicada.
- **OI-A · Renderizar tool-use / terminal / REPL** *(contrato base común; =OI-A de 03)* — **capacidad:** presentar la
  ejecución de tools. **origen:** K10 (REPL), K9 (PowerShell), render (`UI.tsx`). **firma:** el integrador consume el
  **stream de eventos** (`ToolCallEvent`/`ToolResultEvent`, 07); el runtime **no** expone callbacks de render.
  **cableado:** `agentic_code` = terminal (ink-like) + REPL/PowerShell si aplica; `agentic_assistant` = SSE→front.
  **orden:** requiere 07·events. **aceptación:** un turno con tool-calls se renderiza incrementalmente sin que el
  runtime conozca el medio (verificado A2: el loop emite los eventos; el integrador drena).

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (64)

| ID | TIER | destino | cara | evidencia | detalle | nota-identidad |
|---|---|---|---|---|---|---|
| A1 | BATTERY fs + T1-CONTRATO-adyacente | `battery_fs_tools` (R1) + OI-naming | ambas | tracker-leído (1ª+2ª vuelta, naming) | sí (§1·A/OI-naming) | — |
| A2 | T1-CONTRATO (home 09) | →09·tools-infra | base | tracker-leído | sí (→09, 🔀 L10 sin consumidor) | — |
| A3 | BATTERY fs (bloqueado) | `battery_fs_tools` + →02/09 (`new_messages`) | base | tracker-leído | sí (→02/09) | — |
| A3b | BATTERY fs (R5) | `battery_fs_tools` (R5) | base | tracker-leído | sí (§1·A) | — |
| A3c | BATTERY fs (R6) | `battery_fs_tools` (R6) | base | tracker-leído | sí (§1·A, BUG) | — |
| A3d | BATTERY fs (R7) | `battery_fs_tools` (R7, dep R0) | base | tracker-leído | sí (§1·A) | — |
| A4 | BATTERY fs (R7) | `battery_fs_tools` (R7) | base | tracker-leído | sí (§1·A) | — |
| A5 | T2-BASE-MECANISMO | `ctx.read_file_state` (R0) + fork-copy | base | ensamblador `dispatcher.py`+`agent_loop.py:319-323` abiertos (sin canal de estado) | sí (§2.1/R0/CtxR1) | — |
| A6 | BATTERY fs (R4) | `battery_fs_tools` (R4) | base | tracker-leído | sí (§1·A) | — |
| A7 | BATTERY fs (R2) | `battery_fs_tools` (R2, dep R0) | base | tracker-leído | sí (§1·A) | — |
| A8 | BATTERY fs (R2) | `battery_fs_tools` (R2) | base | tracker-leído | sí (§1·A) | — |
| A9 | T2-COSTURA (R3) + INTEGRADOR | `ctx.fs_safety` + OI-fs-safety | ambas | tracker-leído | sí (§2.1/§2.5/R3) | — |
| A10 | 🔀 + BATTERY fs (undo) + T2-COSTURA (LSP) + ⛔ | `battery_fs_tools` (undo) + LSP + ⛔ IDE | ambas | tracker-leído | sí (§1·A, 🔀/undo=03·B7) | — |
| A11 | T2-COSTURA (home 06) | →06·permissions (GAP-02) | ambas | tracker-leído | sí (→06/OI-perm) | — |
| A12 | T1-CONTRATO (home 09) | →09·tools-infra | base | tracker-leído | sí (→09, 🔀 L10) | — |
| A13 | BATTERY fs | `battery_fs_tools` | base | ensamblador `glob_tool.py:13,40-43` (2ª vuelta) | sí (§1·A, homólogo) | — |
| A14 | BATTERY fs | `battery_fs_tools` | base | ensamblador `grep_tool.py:15-19` (2ª vuelta) | sí (§1·A, 🔀 L10) | — |
| B1 | BATTERY shell (R9) + →05 | `battery_shell` + →05 (bg) | base | tracker-leído | sí (§1·B) | — |
| B2 | T2-COSTURA (`exec_env` R8) | `PersistentShellExecEnvironment` | base | ensamblador `bash.py` (2ª vuelta, `LocalExecEnvironment` fresco) | sí (§2.1/R8) | eje ejecución |
| B3 | T2-BASE-MECANISMO (home 05) | →05·execution (EXEC9/10) | base | tracker-leído | sí (→05) | eje ejecución |
| B4 | T2-COSTURA (home 06) | →06·permissions (GAP-02) | ambas | tracker-leído | sí (→06/OI-perm) | — |
| B5 | BATTERY shell (R9) + →09 + ⛔ | `battery_shell` + →09 + ⛔ | base | tracker-leído | sí (§1·B, 🔀 L10) | — |
| B6 | T2-COSTURA (home 09) | →09·tools-infra (F3) | base | tracker-leído | sí (→09, 🔀 L10) | — |
| B7 | T2-COSTURA (home 06) | →06·hooks | ambas | tracker-leído | sí (→06) | — |
| B8 | BATTERY clone (extensión B) + T2-COSTURA (git-cred) | `battery_clone` + `ctx.git_credentials` + OI-git-cred | ambas | ensamblador `clone_repository.py:120-128` (2ª vuelta) | sí (§2.4/§2.5, NO deuda L10) | eje ejecución |
| B9 | BATTERY shell (dep R8+R0) | `battery_shell` | base | tracker-leído | sí (§1·B) | — |
| B10 | T2-COSTURA (home 07) | →07·events (EVT6) | base | tracker-leído | sí (→07) | — |
| B11 | BATTERY shell (dep R8) | `battery_shell` (R8) | base | tracker-leído | sí (§1·B) | eje ejecución |
| B12 | BATTERY shell (R9) + ⛔/→09 | `battery_shell` (R9) + ⛔ | base | ensamblador `bash.py:33` (2ª vuelta, `is_error=rc!=0`) | sí (§1·B, BUG grep) | — |
| C1 | BATTERY meta | `battery_meta` (`ConfigTool`) | base | **ensamblador `config.py:62-75` abierto (ESTE ciclo)** | sí (§1·C) | — |
| C2 | BATTERY meta | `battery_meta` (no `battery_todos`) | base | ensamblador `todo_write.py:54-62` (2ª vuelta) | sí (§1·C, homólogo) | — |
| C3 | BATTERY meta | `battery_meta` (`SleepTool`) | base | ensamblador `sleep.py:34-35` (2ª vuelta) | sí (§1·C) | — |
| C4 | BATTERY tool (`AskUserQuestion`) | `battery_meta` (`ends_turn`) | base | **ensamblador `ask_user.py:97` abierto (ESTE ciclo)** | sí (§1·C, homólogo) | — |
| C5 | →09·tools-infra | →09·E | base | tracker-leído (2ª vuelta `tool_search.py:53-55`) | sí (→09) | — |
| D1 | BATTERY plan (tool; home 14) | `battery_plan` + →14 | base | ensamblador `plan_mode.py:40,45-49` (2ª vuelta) | sí (§1·D, homólogo) | — |
| D2 | BATTERY plan (tool; home 14) | `battery_plan` + →14 | base | ensamblador `plan_mode.py:79,106` (2ª vuelta) | sí (§1·D, homólogo) | — |
| D3 | T2-BASE-MECANISMO (loop) + DEUDA-B | `agent_loop.py` + DEUDA-B (protocolo) | base | **ensamblador `agent_loop.py:332-337/338-339/348/300-313` + `dispatcher.py:41-84` + productores `config.py:62-75`/`ask_user.py:97` + `protocol.py:21-36/51-61` abiertos (ESTE ciclo)** | sí (§2.4, CORR-09) | — |
| E1 | BATTERY worktree | `battery_worktree` | base | ensamblador `worktree.py:65,73-88,144-149` (2ª vuelta) | sí (§1·E, homólogo) | — |
| E2 | T2-BASE-MECANISMO (R10) | `battery_worktree` + allowlist | base | ensamblador `worktree.py:61,129` (2ª vuelta, `=False`) | sí (§1·E, GAP-TOOL2 resuelto) | eje ejecución |
| E3 | T2-BASE-MECANISMO (R10) | allowlist + →05 | base | ensamblador `resolver.py:45-48` (=03·E5) | sí (§2.1/R10) | eje ejecución |
| E4 | T2-BASE-MECANISMO (R10) | allowlist (reconciliar) | base | tracker-leído (2ª vuelta, celda a celda) | sí (§1·E) | eje ejecución |
| F1 | BATTERY agent-tool (home 05) | `battery_agent` + →05 | base | ensamblador `agent.py:73` (2ª vuelta) | sí (§1·F) | eje ejecución · id opaco |
| F2 | BATTERY agent-tool | `battery_agent` | base | ensamblador `agent.py:50-54` (2ª vuelta) | sí (§1·F, extensión B) | eje ejecución |
| F3 | T2-BASE-MECANISMO/COSTURA (home 05) + BATTERY memory (13) | →05 + →13 | base | ensamblador `agent.py:105` (2ª vuelta, delega runner) | sí (→05/13) | eje ejecución |
| F4 | BATTERY agent-tool | `battery_agent` + →05 | base | tracker-leído | sí (§1·F) | eje ejecución |
| G1 | DEUDA-B (conflación) + →05 | DEUDA-B (separar stores) + →05 | base | ensamblador `task_tools.py:10,54` (2ª vuelta) | sí (§2.4, 🔀) | eje ejecución |
| G2 | BATTERY task-tool | `battery_task` | base | tracker-leído | sí (§1·G) | eje ejecución |
| G3 | BATTERY task-tool (R11) + DEUDA-B | `battery_task` (R11) + DEUDA-B | base | ensamblador `task_tools.py:137-142` (2ª vuelta) | sí (§1·G/R11) | eje ejecución |
| G4 | ⛔-nombrado (teams/swarm) | ⛔ corte README | — | tracker-leído | N/A (⛔ nombrado) | — |
| G5 | BATTERY task-tool | `battery_task` | base | ensamblador `task_tools.py:17-32,187` (2ª vuelta) | sí (§1·G) | eje persistencia (scope sesión) |
| H1 | BATTERY web + INTEGRADOR | `battery_web` + OI-web-policy | ambas | ensamblador `web_fetch.py:44` (2ª vuelta) | sí (§1·H, 🔀 L10) | — |
| H2 | BATTERY web + INTEGRADOR | `battery_web` + OI-web-policy | ambas | ensamblador `web_search.py:74-95` (2ª vuelta) | sí (§1·H, 🔀 L10) | — |
| K1 | BATTERY tool + T2-COSTURA (bloqueado) | `battery_brief` + →02/09 + OI-B | ambas | tracker-leído (§K) | sí (§2.5/OI-B) | — |
| K2 | BATTERY tool + T1-CONTRATO (home 09) | `battery_synthetic` + →09 | base | tracker-leído (§K) | sí (§2.3, dep structured-output) | — |
| K3 | BATTERY fs | `battery_fs_tools` (NotebookEdit, prereq R2/R3) | base | tracker-leído (§K) | sí (§2.2) | — |
| K4 | T2-COSTURA (`ctx.lsp`) + INTEGRADOR | costura LSP + OI-lsp | ambas | tracker-leído (§K) | sí (§2.5/OI-lsp) | — |
| K5 | BATTERY tool + T2-COSTURA (15) + INTEGRADOR | `battery_cron` + →15 + OI-cron | ambas | tracker-leído (§K) | sí (§2.5/OI-cron) | eje persistencia |
| K6 | ⛔ (claude.ai) + T2-COSTURA opcional | ⛔ (sin OI-*; realización específica si un integrador lo quiere) | integrador | tracker-leído (§K) | sí (⛔/OI) | — |
| K7 | ⛔-nombrado (swarm) | ⛔ corte README | — | tracker-leído (§K) | N/A (⛔ nombrado) | — |
| K8 | ⛔-nombrado (teams) | ⛔ corte README | — | tracker-leído (§K) | N/A (⛔ nombrado) | — |
| K9 | ⛔-nombrado (OS/terminal) | ⛔ Windows | — | tracker-leído (§K) | N/A (⛔ nombrado) | — |
| K10 | CLI-ONLY/INTERFAZ | INTEGRADOR (terminal REPL) | integrador | tracker-leído (§K) | sí (OI-A) | — |
| K11 | T2-COSTURA (home 11) | →11·mcp | base | tracker-leído (§K) | sí (→11) | — |
| K12 | T2-COSTURA (home 11) | →11·mcp | base | tracker-leído (§K) | sí (→11) | — |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../10-tools-native.md`?** — **Sí**, líneas **1→794** (corregido en `A-CIERRE·P4″`: decía
   «1→793»; el tracker tiene **794** líneas) (encabezado + delimitación + tesis
   arquitectural + tablas A-H + I-naming + J-CORR09 + K-extras + §Hallazgos/cabos/gaps-con-ID + recuento + ledger de
   archivos + 4 preguntas 1ª vuelta + §Re-visita gate-11 2ª vuelta [mini-ledger de consumidores, §nota-honestidad,
   ledger de lectura, 4 preguntas, VEREDICTO] + §Plan R0-R11 + §Implementación de tools no portadas).
2. **¿Reconcilia el conteo?** — findings en `../10-tools-native.md` = **64** (celdas del grid: A=17 [A1/A2/A3/A3b/A3c/
   A3d/A4-A14] + B=12 + C=5 + D=3 + E=4 + F=4 + G=5 + H=2 = 52; + K-extras = 12); colocados = **64**; sin colocar =
   **0**. ✅ §I=`FIND-NATIVE-NAME` plegado en A1 (cruzado); §J=`CORR-09-CTXMOD` plegado en D3 (cruzado); §Hallazgos +
   §Plan R0-R11 = capa de remediación referenciada en `acción`, no re-contada.
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí. Load-bearing re-abierto en
   ESTE ciclo contra el runtime real** (el ensamblador de 10 = el loop que aplica `context_modifier`/`ends_turn`/
   PreToolUse + el choke point del dispatcher): **D3/§J** `agent_loop.py:300-313` (PreToolUse honra `block`+
   `modified_input`; `stop`/`additional_context` NO), `314-318` (dispatch→pool), `319-328` (output→messages +
   `ToolResultEvent`), `332-337` (`context_modifier` `getattr`+try/except), `338-339`/`348` (`ends_turn`→break);
   **choke point** `dispatcher.py:36/41-42` (`sanitize_output`=03·D2), `57/62-65/71/76-79` (resolve/perm/validate/
   execute); **productores** `config.py:62-75` (C1, `context_modifier`), `ask_user.py:97` (C4, `ends_turn`) — ambos
   `# type: ignore[attr-defined]`; **`protocol.py:21-36/51-61` abierto ESTE ciclo** confirma que `ToolResult` NO
   declara `context_modifier`/`ends_turn` (⇒ DEUDA-B) y que `category` sí se declara (`:56`) pero nadie lo lee
   (LAT-TOOL1); **A5/new_messages ausente** confirmado abriendo
   `agent_loop.py:319-323` (sólo appendea `result.output`, sin canal de estado ni de mensajes tipados). Los demás
   ✅/🔀 (A13/A14/B8/C2/C3/D1/D2/E1/E2/F1-F4/G1/G3/G5/H1/H2) se **re-abrieron 1→EOF ESTE ciclo en B** (ver
   §3.2-bis), NO heredados de la tabla: `read_file.py`/`file_edit.py`/`write_file.py`/`bash.py`/`glob_tool.py`/
   `grep_tool.py`/`clone_repository.py`/`agent.py`/`plan_mode.py`/`worktree.py`/`task_tools.py`/`todo_write.py`/
   `tool_search.py`/`web_fetch.py`/`web_search.py`/`sleep.py`/`__init__.py` (los 17 restantes) + los ya-abiertos
   `config.py`/`ask_user.py`/`protocol.py`/`dispatcher.py`. Cero cambios de estado: cada celda se sostiene sobre B
   leído, no sobre el tracker (L11). Los homed-fuera puros (→05/06/07/09/11/13/15) se colocan con destino nombrado
   (L07); su cableado se verifica en su categoría-hogar.
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí en detalle; el conteo estaba mal y se
   corrige.** §2.5 desarrolla **NUEVE** obligaciones con los 6 campos L05: OI-fs-safety · OI-perm · OI-git-cred ·
   OI-web-policy · OI-naming · OI-B · OI-lsp · OI-cron · **OI-A**. *(Decía «8 … + OI-A render», colgando el noveno
   tras un `+` fuera del recuento. Refutado **dos veces desde fuera y de forma independiente**:
   `00-INTEGRADORES §1.7:185` lista los nueve nombres y `BATTERIES §4.1:219-220` escribe «las **9** de tools
   nativas (10)». El descuadre era del emisor, no de los receptores.)* Sobre el *«ninguno a secas»*: **era falso**
   — `K6` daba destino `OI-remote` **sin ficha en §2.5 y ausente de `00-INTEGRADORES`**; resuelto en `K6`
   declarando que RemoteTrigger **no genera obligación de integrador** (no es contrato base común). Las ⛔
   (K7/K8/K9 swarm/teams/Windows, G4) llevan satélite nombrado (corte README), no "→ integrador" vacío.
5. **¿Doble filo (L10)?** — **Sí**. Ningún ❌ disfrazado de 🔀: los CORE-GAP reales (A5/A7/A8/A9/A3b/A3c/B2/B12/G3 +
   K1/K2/K3) se mantienen como CORE-GAP con remediación desarrollada (R0-R11 + §K); los 🔀 son divergencias con efecto
   equivalente (A13/A14 menos-rico-pero-funcional; H1/H2 mínimo-viable; A6-quote/encoding bytes-crudos; E2 más-
   restrictivo). Ninguna deuda inflada: **`clone_repository`** (B8) e **`inherit_messages`** (F2) son extensiones B
   sin contraparte → **NO deuda A↔B**; **`category` slot muerto** (LAT-TOOL1) = DEUDA-B interna ya homed 09, **NO**
   deuda A↔B (el canónico tampoco lo usa como driver). La conflación G1 = DEUDA-B (el runtime opera), no ❌ A↔B.
   ⛔ **UN 🔀 DE ESTA LISTA SE CAYÓ (`D-08`, `A-CIERRE·P4″·§15.1`):** decía *«A2 (`isReadOnly`/`isConcurrencySafe`)
   **sin consumidor** hoy (dispatcher secuencial) ⇒ no gap activo, no se cuenta como deuda viva»*. **Falso.** El
   consumidor existe en el canónico y es estructural: `toolOrchestration.ts:91-116` (`partitionToolCalls`) usa
   `isConcurrencySafe` como **discriminador de la topología de ejecución**, y `:19-82` (`runTools`) bifurca en dos
   ramas con **semántica distinta de `context_modifier`** (encolado vs. al vuelo). El 🔀 se invirtió a **CORE-GAP**
   en `A2`, y arrastró `D3` (✅→🟡, `CG-TOOL-CONC`). **L10 aplicada mal**: se llamó «divergencia deliberada» a una
   capacidad ausente cuyo consumidor no se había ido a buscar al canónico (tell `elevar-en-vez-de-leer`). El resto
   de la lista sigue en pie; este ítem queda como el ejemplo de que la pregunta 5 puede fallar **en la dirección
   contraria** a la que vigila: no ❌-disfrazado-de-🔀, sino **❌-declarado-inerte**.

### 3.2-bis · §Nota de honestidad — re-lectura de B ESTE ciclo (20 de 21 archivos 1→EOF; `agent_loop.py` por tramo)
> ⚠ **Rótulo corregido en `A-CIERRE·P4″` (L08, «abierto ≠ íntegro» a nivel de etiqueta de sección).** Decía
> «re-lectura **íntegra** de B (1→EOF ESTE ciclo)» mientras la propia tabla de abajo declara `loop/agent_loop.py`
> | 352 | **tramo 280-352**. La excepción está justificada y **se mantiene** (1-279 es la tajada de `02·loop`, con
> EOF en su propia 2ª vuelta), pero el rótulo la borraba: quien lee sólo el título se lleva un grado probatorio
> que el cuerpo no sostiene. La regla es que **el titular no puede ser más fuerte que la celda más débil que
> resume**.
Tras el gate auto-adversarial del usuario ("¿EOF en todos los archivos? / si no recorres los archivos completos,
¿cómo aseguras que lo que se destile opere tal cual la expectativa?"), se **abrieron 1→EOF ESTE ciclo los 19 tools
nativos** (no sólo el ensamblador load-bearing), porque la clasificación de cada ✅/🔀 sólo vale abriendo el código
de B (L11), no heredando la tabla del tracker (que es hipótesis). Ledger de lectura de esta ronda:

| Archivo | LOC | Lectura ESTE ciclo |
|---|---|---|
| `tools/protocol.py` | 61 | **1→EOF** (`ToolResult` sin `context_modifier`/`ends_turn`; `ToolProtocol:56` declara `category`) |
| `tools/dispatcher.py` | 84 | **1→EOF** (choke `sanitize_output:41-42`; resolve/perm/validate/execute) |
| `loop/agent_loop.py` | 352 | **tramo 280-352** (tajada de aplicación de tool de 10; 1-279 = 02·loop, EOF'd en su 2ª-vuelta) |
| `native/config.py` | 76 | **1→EOF** (C1, `context_modifier:62-75`) |
| `native/ask_user.py` | 98 | **1→EOF** (C4, `ends_turn:97`) |
| `native/read_file.py` | 42 | **1→EOF** (A3/A3b/A3c/A3d/A4/A5 ❌ confirmados: `read_text`+`splitlines`+slice, nada más) |
| `native/file_edit.py` | 78 | **1→EOF** (A6/A7/A8/A9 ❌: `count>1`→error; edita si `path.exists`, sin read-state ni safety) |
| `native/write_file.py` | 38 | **1→EOF** (A7/A9 ❌: `mkdir`+`write_text` directo) |
| `native/bash.py` | 36 | **1→EOF** (B2/B12: `exec_env or LocalExecEnvironment()` fresco `:27`; `is_error=rc!=0` `:33`) |
| `native/glob_tool.py` | 46 | **1→EOF** (A13: `DEFAULT_GLOB_LIMIT=100`, sort alfabético, nota truncado) |
| `native/grep_tool.py` | 87 | **1→EOF** (A14: `DEFAULT_HEAD_LIMIT=250`/`MAX_LINE_LEN=500`/`_VCS_DIRS`, `re` sobre `pathlib.glob`) |
| `native/clone_repository.py` | 149 | **1→EOF** (B8: seam `GitCredentialProvider`, helper efímero `GIT_CLONE_TOKEN`, `ctx.fs.resolve`, git en host) |
| `native/agent.py` | 119 | **1→EOF** (F1-F4: `get_runner()` global `:105`=FIND-EXEC1→05; `ForkSnapshot:79-87` sin read_file_state/rendered_system_prompt) |
| `native/plan_mode.py` | 107 | **1→EOF** (D1/D2/D3: root-only `:40`, `context_modifier`+`ends_turn`; plan-file de `capabilities.plan`→14) |
| `native/worktree.py` | 167 | **1→EOF** (E1/E2: `safe_for_background=False` `:61,129`; git en host, no `exec_env`) |
| `native/task_tools.py` | 223 | **1→EOF** (G1/G3/G5: `get_registry()` global=LAT-EXEC1→05; `TaskUpdate` sin `status` `:137-144`; scope por `session_id`) |
| `native/todo_write.py` | 63 | **1→EOF** (C2/B4: enums espejo, `context_modifier`→`native["todos"]`) |
| `native/tool_search.py` | 79 | **1→EOF** (C5: `select:` singular `:53-55`=09·E6; usa `..deferred`→09) |
| `native/web_fetch.py` | 67 | **1→EOF** (H1: `urllib`, http/https `:44`, cap 100K, sin markdown/cache) |
| `native/web_search.py` | 128 | **1→EOF** (H2: Serper `:74`, **sí** implementa `allowed/blocked_domains` vía `site:` `:84-95`) |
| `native/sleep.py` | 39 | **1→EOF** (C3: `asyncio.sleep(clamp(0,60))` `:34-35`) |

**Resultado: cero cambios de clasificación.** Los 6 productores de `context_modifier`/`ends_turn` llevan **todos**
`# type: ignore[attr-defined]` (config/ask_user/plan_mode×3/worktree×2/todo) ⇒ DEUDA-B **sistémica**. Detalles nuevos
que refuerzan homing (ninguno mueve celda): `get_runner()`/`get_registry()` **globales** en agent/task (→05
FIND-EXEC1/LAT-EXEC1); `ForkSnapshot` omite read_file_state/rendered_system_prompt (re-confirma 03·A5/A23);
worktree/clone corren git en **host** (no `exec_env`); web_search **sí** trae domain-filters (un pelo más cerca del
canónico, sigue 🔀 por el provider Serper). **Honestidad de método:** en la 1ª entrega de este ciclo estos 17 se
marcaron "heredados de 2ª-vuelta gate-11" — atajo de falsa economía (L00/L11) que el usuario cazó; corregido leyendo
1→EOF ahora. `agent_loop.py` 1-279 es lo único no leído este ciclo, y es territorio de 02·loop (L07), EOF'd allí.

### 3.3 VEREDICTO
**🟡 REPARTO COMPLETO, CIERRE CONDICIONADO** *(era «✅ NADA PENDIENTE»; degradado en `A-CIERRE·P4″·§15`).*
El reparto de los 64 findings sí está completo y con destino nombrado — eso se sostiene. Lo que **no** se sostiene
es el «nada pendiente», por cuatro pendientes que existían y no estaban escritos:
1. **`CG-TOOL-CONC` (nueva, `D-08`):** `A2` invertido a CORE-GAP y `D3` degradado ✅→🟡. El ✅ de `D3` era correcto
   **sólo porque el dispatcher del runtime es secuencial**; pasa a incorrecto **en silencio** el día que gane
   concurrencia, porque el canónico **encola** los modifiers en la rama concurrente (`toolOrchestration.ts:42-48`,
   aplicación diferida `:54-62`) y los aplica al vuelo sólo en la serial (`:140-142`). Orden de remediación fijado
   en §2.3: `09·A3/A6` (flags declarados) → encolado → concurrencia del dispatcher, **nunca al revés**.
2. **Dos huecos de seam abiertos hacia fuera (`c24/c29`):** `SEAMS §S23` (reaping) nombra «10 (bash-bg)» y `§S25`
   (isolation) nombra «→10/18» como productores, pero ninguna celda de este doc los reconoce. Quedan **abiertos**,
   no adjudicados aquí.
3. **Precondición que invalida el «✅ de comportamiento» de §F y §G** (ya escrita en la cabecera de F): `DB-27` +
   `DB-h1`/`RV-8` + `CAT-h5` — hoy **todo spawn de subagente y las 6 `Task*` fallan**. Los ✅ de F/G son ✅ de
   *superficie de tool*, no de comportamiento observable.
4. **La capa de remediación no vive en este doc** (ver §Puntero al Plan, abajo): mientras eso siga así, «nada
   pendiente» describe el reparto, no la ejecutabilidad.
Con esos cuatro escritos, el paso a **A3·06·hooks** sigue siendo el siguiente ciclo del checklist §7 — pero se
pasa con la deuda **nombrada**, no con un ✅ que la tapaba.

Los 64 findings repartidos con TIER+destino; **CORE-GAPs originados/aterrizados en 10** para DEUDA-A: keystone
**R0** (`ctx.read_file_state`) → cascada R2 (edit-guards, aterriza FIND-CTX1) / R5 (línea-num, contrato) / R6
(device-guard, BUG) / R7 (cota+dedup); **R3** (`FsSafetyPolicy` seam, aterriza G8) ; **R4** (replace_all); **R8**
(shell persistente, FIND-TOOL8) → B9/B11; **R9** (interpretCommandResult, BUG grep); **R10** (bg-allowlist,
GAP-TOOL2/MODE2 resuelto); **R11** (TaskUpdate.status); + capacidades no portadas **K1-K5** (Brief/Synthetic/
NotebookEdit/LSP-seam/Cron). **DEUDA-B:** `context_modifier`/`ends_turn` sin declarar en `ToolResult` (§J), conflación
tasklist↔registry (G1), `category` slot muerto (LAT-TOOL1, ya homed 09). **12 costuras** nombradas con productor/
consumidor (*decía «11»; §2.1 enumera **doce** viñetas — descuadre interno del propio doc, corregido en
`A-CIERRE·P4″`*) (3 nuevas load-bearing ausentes: `read_file_state`/`fs_safety`/`exec_env`-vivo; 5 cableadas
verificadas: PreToolUse, `context_modifier`/`ends_turn`, `sanitize_output`, allowlist, git_credentials).
**9 obligaciones de integrador** con detalle simétrico (*decía «8»; §2.5 tiene **nueve** fichas y los dos
receptores externos —`00-INTEGRADORES §1.7:185` y `BATTERIES §4.1:219-220`— cuentan nueve*). Cabos con destino explícito (→02·loop: A3-image/K1-Brief-blocker `new_messages`;
→05·execution: B1-bg/B3/F1-F4/G1/G3; →06·permissions: A11/B4/B7 GAP-02; →07·events: B10; →09·tools-infra:
A2/A12/B5/B6/C5/K2; →11·mcp: K11/K12; →13·memory: F3; →14·plan: D1/D2; →15·storage: C1-persist/K5; →01·contracts:
B2-mode) — ninguno es pendiente de **verificación** (el cableado interno a 10 se re-abrió aquí, Q3; los homed-fuera se
verifican en su categoría-hogar). El siguiente ciclo del checklist §7 tras 03 y 10 es **06·hooks**.

### 3.4 Puntero al Plan de remediación (`c27/c32` — DEFECTO DE FORMA reconocido, no reparado aquí)
**El detalle L05 de `R0`-`R11` NO vive en este documento.** Vive en la cara A, `../10-tools-native.md`
**`:523-725`** (§Plan, doce entradas con los seis campos —comportamiento · seam · firma · cableado · orden ·
prueba— y grafo de dependencias explícito `R0 → R1 → {R2,R3,R4,R5,R6} → R7 → R8 → R9 → R10 → R11`), más
`:729-793` (§Implementación de las seis tools ❌ no portadas: NotebookEdit · Brief · SyntheticOutput · LSP-seam ·
Cron* · RemoteTrigger). Aquí sólo quedan **etiquetas** de esas entradas en la columna `acción`.

Esto **contradice la frase de rigor del propio corpus** («de lo que aquí se destile nace el código»): un
destilado del que nace código no puede delegar las firmas exactas —`check_read_before_edit(ctx, path) -> str |
None`, `FsSafetyPolicy.check_write(path: Path, content: str) -> str | None`, `add_line_numbers(text, start=1)
-> str`, `BLOCKED_DEVICE_PATHS: frozenset[str]`, `PersistentShellExecEnvironment.run_shell(command, *, timeout)
-> ShellResult` con centinela `command; printf "\n<sentinel>$?\n"`, `interpret_command_result(command, result)
-> bool`, `TaskUpdate.status`— al documento que el destilado viene a sustituir. Se deja **explícito y con rango
de líneas** en vez de disimulado: el que ejecute R0-R11 tiene que abrir la cara A. Reparación pendiente en el
ledger (`AC-36`).

### 3.5 Namespace `K*` — colisión, se resuelve por PREFIJO (`c25/c31`, `AC-30`)
`10·K1..K12` es el mayor namespace `K*` del corpus y **colisiona** con `DEUDA-A·K1..K8`. Ya hay una cita cruzada
mal resuelta por esto: `DEUDA-A §1.1·K1:187` cita «`10·B2`» refiriéndose a su propio `K1`. **Regla:** citar
siempre **con prefijo** —`10·Kn` vs `DA·Kn`—; **nunca renumerar** ninguna de las dos series (los IDs ya están
referenciados desde fuera y renumerar rompe las citas existentes en silencio).
