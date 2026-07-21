# 13 · capabilities/memory — homologación

> **Estado**: 1ª pasada DOCUMENTADO + re-audit 2026-07-14 · **✅ VALIDADA (2ª vuelta · gate 11/L09) 2026-07-20** —
> lado B 1→EOF (5 `memory/*.py`) + **ENSAMBLADOR** (`factory.py` 1→EOF + `manager.py` 1→EOF + `loop/agent_loop.py:85-234`)
> + los **10 archivos A in-scope RE-LEÍDOS 1→EOF esta ronda** (extractMemories 615/memdir 507/memoryTypes 271/paths 278/
> memoryScan 94/findRelevantMemories 141/memoryAge 53/agentMemory 177 + prompts.ts 154 + agentMemorySnapshot.ts 197,
> estos 2 tras el gate auto-adversarial) → **CERO discrepancias, cero cambios de estado, código intacto**.
> Ver bloque "Re-visita de COMPLETITUD (gate 11/L09)" al final.

Contrasta `agentic_runtime/src/agentic_runtime/capabilities/memory/*` (5 archivos, 347 LOC) contra el subsistema
de **memoria persistente entre-sesiones** del canónico: el core `memdir/*` (`memdir.ts`, `memoryTypes.ts`,
`memoryScan.ts`, `findRelevantMemories.ts`, `paths.ts`, `memoryAge.ts`), el pipeline de **auto-extracción**
`services/extractMemories/*`, la **memoria de subagente** `tools/AgentTool/{agentMemory,agentMemorySnapshot}.ts`,
y los seams de detección/permisos (`utils/memoryFileDetection.ts`, el carve-out de escritura de `paths.ts`).

**Alcance**: comportamiento del *core* de la memoria tipada persistente — dónde vive y cómo se scopea, scan/recall,
activación en el system prompt (taxonomía + instrucciones), auto-extracción por fork al cierre del turno, memoria
de subagente, y el gate de escritura a la carpeta de memoria. El runtime soporta usuarios/sesiones y es
long-running; el canónico es single-user en terminal y scopea por **git-root del proyecto**, así que la
homologación del *scoping* es **de comportamiento** (el runtime scopea por `user_id/agent`, decisión deliberada
del multi-tenant).

**Fuera de alcance de 13 — con destino a OTRO subsistema numerado (abiertos y confirmados, lección 07)**:
- **SessionMemory + SM-compaction** → **subsistema de compactación (01 `contracts/compaction` / `services/compact`)**.
  `services/SessionMemory/{sessionMemory,sessionMemoryUtils,prompts}.ts` + `services/compact/sessionMemoryCompact.ts`
  NO son la memoria transversal: son el **resumen de la conversación ACTUAL** (`~/.claude/session-memory/<id>.md`,
  plantilla de secciones fijas) que un fork periódico mantiene para **cebar el contexto post-compactación**
  (ligado a `isAutoCompactEnabled`). Leídos íntegros y confirmados como concern de compactación — se auditan allí,
  NO se re-enumeran feature-by-feature aquí. Cabo abierto a 01: `trySessionMemoryCompaction`, `calculateMessagesToKeepIndex`,
  `adjustIndexToPreserveAPIInvariants` (invariante tool_use↔tool_result en el recorte).

**Fuera del core del runtime → territorio del IMPLEMENTADOR (`agentic_assistant`), abiertos y enumerados**:
- **Team memory (feature `TEAMMEM`)**: `memdir/{teamMemPaths,teamMemPrompts}.ts` + `services/teamMemorySync/*`
  (index/watcher/secretScanner/secretGuard/types) + `utils/teamMemoryOps.ts`. Es memoria **inherentemente
  multi-tenant/backend** (sync server-backed GET/PUT con ETag/version/checksums, delta upload, resolución de
  conflicto 412, watcher fs + push debounced, secret-scanning gitleaks antes de compartir). El runtime es
  **agnóstico**; team-sync pertenece al implementador que SÍ tiene usuarios/equipos — análogo a cómo todo el
  esfuerzo trata *usuarios/sesiones*. Se enumera abajo (§I) como spec para el implementador. **Transferible al
  core**: la sanitización de la clave de scope (**FIND-MEM9**) y el seam de secret-scan (si el implementador
  sincroniza).

**⛔ N/A core (UI/terminal/telemetría — abiertos y confirmados, nunca ⛔ por título)**:
`commands/memory/memory.tsx` (diálogo `/memory`→editor), `components/memory/{MemoryFileSelector,MemoryUpdateNotification}.tsx`,
`components/messages/UserMemoryInputMessage.tsx` (render del quick-save `#`), `components/agents/…/MemoryStep.tsx`
(wizard de scope de agent-memory), `components/FeedbackSurvey/useMemorySurvey.tsx` (encuesta de feedback),
`utils/memory/{types,versions}.ts` (clasificación de instruction-files tipo CLAUDE.md + `projectIsInGitRepo`),
y — **falso positivo de nombre** — `components/MemoryUsageIndicator.tsx` + `hooks/useMemoryUsage.ts`, que son
**monitoreo de RAM del proceso** (`process.memoryUsage().heapUsed`, `/heapdump`), nada que ver con `memdir`.
`utils/memoryFileDetection.ts` es sobre todo detección para el **collapse/badge del transcript** (UI) — sus
predicados load-bearing (`isAutoMemPath`/`isAgentMemoryPath`) viven en `paths.ts`/`agentMemory.ts` (sí core).

## Tesis arquitectural
El canónico tiene una **topología de memoria de cuatro capas**, todas ficheros `.md` con frontmatter tipado
(`type: user|feedback|project|reference`) e índice `MEMORY.md` inyectado al system prompt:
1. **auto-memory** (agente principal): `<base>/projects/<sanitized-git-root>/memory/` — scopeada por **proyecto**.
2. **agent-memory** (subagentes con memoria activada): keyed por **tipo de agente** (persistente entre despachos),
   3 scopes `user|project|local` + **snapshot sync** (compartir memoria de agent-type por VCS).
3. **team-memory** (`TEAMMEM`): subdir `…/memory/team/`, sincronizada al servidor por-repo.
4. **session-memory**: resumen de la conversación actual para compactación (→ subsistema 01/compact).

Y **NO usa una tool de memoria**: el modelo guarda con `Write`/`Edit` (carve-out de permisos sobre la carpeta),
y hay un **agente de extracción forkeado** que corre al final de cada query-loop (stop-hook) — si el agente
principal no escribió memorias él mismo, el fork lee los últimos ~N mensajes y las escribe, con un `canUseTool`
restringido (Read/Grep/Glob libres, Bash read-only, Write/Edit **sólo dentro de la carpeta de memoria**). El
recall por turno es un **selector LLM** (Sonnet vía `sideQuery`, JSON-schema, ≤5) sobre el manifiesto de cabeceras,
con filtrado de `recentTools` y dedup de `alreadySurfaced`, y cada memoria recallada lleva un **caveat de
frescura** ("hace N días… verifica antes de afirmar").

El runtime porta el **esqueleto correcto y honesto de la capa (1)**: `MemoryStore` inyectable (habilita MinIO),
`FilesystemMemoryStore` en disco, `MemoryHeader` (name/description/type/path/mtime), scan tolerante, índice
`MEMORY.md` excluido del recall, `MemoryProvider` **sin tools** (activación en system prompt + recall por turno +
recall post-compactación), y guardado por `write_file` (2 pasos, sin tool `remember`). Pero: **sin auto-extracción**
(el modelo debe decidir escribir — la mayor brecha), **recall determinista por keywords** (no LLM; decisión
declarada, pero sin `recentTools`/`alreadySurfaced`/frescura), **prompt de activación recortado** (falta la
taxonomía detallada, "Before recommending"/verificar, drift-caveat, ignore-memory, plan/tasks, "Searching past
context"), **índice sin truncar**, **scan no-recursivo/sin cap**, **frontmatter anidado `metadata.type` vs plano
`type` y sin validar el enum**, **memoria de subagente keyed por `agent_id` (uuid por-despacho, NO persiste entre
despachos del mismo tipo)**, y **clave de scope sin sanitizar** (traversal).

## Leyenda
✅ homologado · 🟡 parcial · 🔀 distinto (deliberado o a revisar) · ❌ no portado · ⛔ N/A core (UI/producto).

---

## A · Dónde vive / scoping (`store.py`/`provider._scope` vs `paths.ts` + `agentMemory.ts`)

| Feature canónica | Runtime | Estado |
|---|---|---|
| Store en disco, sobrevive reinicio; **inyectable** | `MemoryStore` Protocol + `FilesystemMemoryStore` | ✅ 🔀 (seam propio, habilita MinIO/sesiones) |
| Auto-memory scopeada por **git-root del proyecto** (`getAutoMemBase`=`findCanonicalGitRoot`; worktrees comparten) | scope `<user_id>/<agent>` (multi-tenant) | 🔀 **deliberado** (el runtime tiene usuarios; el canónico no) |
| `getMemoryBaseDir` (`CLAUDE_CODE_REMOTE_MEMORY_DIR` \|\| config-home), overrides Cowork/settings `autoMemoryDirectory` | `root` inyectado por el integrador | 🔀 (equivalente por inyección) |
| **`validateMemoryPath`**: rechaza relativa/root/near-root/UNC/drive-root/null-byte; una sola `sep` final; NFC | store hace `self._root / scope`, **sin validar la clave** | ❌ **FIND-MEM9** (traversal por `user_id`/`agent_id`) |
| `sanitizePath` del git-root para el nombre de carpeta | `_scope` = `user or "anon"` / (`agent_id`\|`"main"`) **crudo** | ❌ FIND-MEM9 |
| `isAutoMemPath` → **carve-out de escritura** (bypassa DANGEROUS_DIRECTORIES para que el modelo pueda guardar) | escritura vía `write_file`/`ConfinedFilesystem`: la carpeta debe estar en el working-allowlist | 🟡 **FIND-MEM12** (=GAP-02/Deuda-B; cross-09) |
| `ensureMemoryDirExists` (mkdir recursivo, idempotente, no bloquea; el prompt dice "ya existe, no mkdir") | `ensure_dir` (mkdir parents exist_ok) + prompt dice "ya existe" | ✅ |
| `isAutoMemoryEnabled` gate (env `CLAUDE_CODE_DISABLE_AUTO_MEMORY`/SIMPLE/remote-sin-storage/setting) | siempre activa | 🟡 **FIND-MEM8** (implementer wire) |
| Agent-memory por **tipo de agente**, 3 scopes `user`/`project`/`local`, `sanitizeAgentTypeForPath` | subagente scopeado por **`agent_id`** (uuid por-despacho) | ❌ **FIND-MEM10** (no persiste entre despachos del mismo tipo; sin scopes) |
| **Snapshot sync** de agent-memory (`agentMemorySnapshot`: project-snapshot→local, `.snapshot-synced.json`, init/replace/mark, compartir por VCS) | ausente | ❌ FIND-MEM10 (agentMemorySnapshot) |
| Daily-log mode `KAIROS` (`logs/YYYY/MM/YYYY-MM-DD.md`, append-only, /dream destila) | ausente | ⛔/❌ (modo assistant; nexo 05·EXEC10 kairos) |

## B · Índice `MEMORY.md` + activación en el system prompt (`prompt.py` vs `memdir.ts`/`memoryTypes.ts`)

| Feature canónica | Runtime | Estado |
|---|---|---|
| `MEMORY.md` excluido del recall/scan, inyectado como índice | `ENTRYPOINT="MEMORY.md"`, `scan` lo salta, va en system prompt | ✅ |
| **`truncateEntrypointContent`**: cap 200 líneas **Y** 25 000 bytes, con warning que nombra qué cap disparó | `read_index` devuelve crudo | ❌ **FIND-MEM4** (índice sin acotar → bloat) |
| Guardado en **2 pasos** (fichero + puntero en índice), "índice ≠ memoria, 1 línea <~150 chars, sin frontmatter" | prompt dice 2 pasos (`<slug>.md` + puntero) | 🟡 (falta el "≤200 líneas se truncan", el formato `- [Title](file.md) — hook`) |
| Taxonomía tipada `user/feedback/project/reference` con `<description>/<when_to_save>/<how_to_use>/<examples>/<body_structure>` (individual **y** combined con `<scope>`) | 4 tipos con una línea cada uno | 🟡 **FIND-MEM7a** (taxonomía recortada) |
| `WHAT_NOT_TO_SAVE` + regla "aplica aunque el user lo pida; pregunta qué fue *sorprendente*" | "Qué NO guardar" (código/git/conversación) | 🟡 (falta la cláusula explicit-save) |
| `WHEN_TO_ACCESS`: relevancia, MUST al pedir, **ignore-memory** (proceder como MEMORY.md vacío), **drift caveat** | "Cuándo usarla" (encaje + guardar duradero) | ❌ **FIND-MEM7b** (falta ignore + drift) |
| **`TRUSTING_RECALL`/"Before recommending from memory"**: memoria nombra file/func/flag ⇒ verificar (existe/grep) antes de recomendar; "X existía cuando se escribió" ≠ "X existe ahora"; snapshots congelados → git log | ausente | ❌ **FIND-MEM7c** (la lección literal del recordatorio de memoria) |
| "Memory and other forms of persistence": cuándo Plan vs memoria, cuándo Tasks vs memoria | ausente | ❌ FIND-MEM7d |
| "Searching past context": grep de topic-files + transcript-logs (`.jsonl`) con términos estrechos | ausente | ❌ FIND-MEM7e |
| "Build up over time / who the user is"; explicit save/forget inmediato | ausente | ❌ FIND-MEM7f |
| `MEMORY_FRONTMATTER_EXAMPLE` con `type: {{user,feedback,project,reference}}` **plano** | prompt pide `metadata.type` **anidado** | 🔀 **FIND-MEM6** (schema divergente) |
| Texto estable entre turnos (cache-friendly), sólo varía con el índice | idem (docstring lo declara) | ✅ |
| `extraGuidelines` (Cowork memory-policy vía env) | ausente | ⛔ (Cowork) |

## C · Scan de cabeceras (`store.scan`/`MemoryHeader` vs `memoryScan.ts`)

| Feature canónica | Runtime | Estado |
|---|---|---|
| Scan `.md` del dir, excluye `MEMORY.md` | `scan` glob `*.md`, salta `ENTRYPOINT` | ✅ |
| **Recursivo** (`readdir {recursive:true}`; team soporta subdirs) | `glob("*.md")` **sólo top-level** | 🔀 **FIND-MEM5a** (no recursivo) |
| Lee **sólo 30 líneas** (`FRONTMATTER_MAX_LINES`) vía `readFileInRange` (stat+read 1 syscall) | `read_text` del **fichero entero** para parsear frontmatter | 🟡 **FIND-MEM5b** (ineficiente) |
| **Cap `MAX_MEMORY_FILES=200`**, orden **newest-first** por `mtimeMs` | sin cap; `sorted(glob)` por nombre (mtime se usa luego en ranking) | 🟡 **FIND-MEM5c/d** |
| Aislamiento por-ítem (`Promise.allSettled`; fichero roto no tumba el scan) | `_parse_header` try/except por path; `None`→se omite | ✅ |
| `MemoryHeader`: `filename/filePath/mtimeMs/description/type` | `name/description/type/path/mtime` (+ `name`, usado por el ranker) | ✅ 🔀 (el runtime añade `name`) |
| `parseMemoryType` valida contra el enum de 4 (unknown/legacy→undefined) | lee `metadata.type` crudo, **sin validar** | 🟡 FIND-MEM6 |
| `formatMemoryManifest`: `- [type] filename (ISO-ts): description` (compartido con extracción) | `_render_recall` sin type/timestamp | 🟡 **FIND-MEM2c** |

## D · Recall (`recall.py`/`provider.active_context` vs `findRelevantMemories.ts` + `memoryAge.ts`)

| Feature canónica | Runtime | Estado |
|---|---|---|
| Selección de ≤5 memorias relevantes a la query, excluye `MEMORY.md` | `rank_memories(…, limit=5)`; scan ya excluye índice | ✅ (concepto) |
| **Selector LLM** (`sideQuery` Sonnet, JSON-schema `selected_memories`, `max_tokens:256`, valida contra filenames) | **overlap de keywords** determinista sobre `name`+`description`, desempate por `mtime` | 🔀 **FIND-MEM2** (el runtime lo declara: "ranker LLM = opinión inyectable futura") |
| **`recentTools` filter**: no surfacear reference/API-docs de tools en uso activo; SÍ warnings/gotchas | ausente | ❌ **FIND-MEM2a** |
| **`alreadySurfaced`**: filtra paths mostrados en turnos previos antes de gastar el budget de 5 | el loop dedup por `path`; el provider re-emite todo el ranking cada turno | 🟡 **FIND-MEM2b** (dedup en loop, no pre-selección) |
| **Frescura por memoria**: `memoryAge` ("hoy/ayer/N days ago") + `memoryFreshnessText`/`Note` (>1 día: "verifica code:line antes de afirmar") | `_render_recall` sin edad/frescura | ❌ **FIND-MEM3** (nexo drift-caveat FIND-MEM7c) |
| `mtimeMs` threaded al caller para frescura sin 2º stat | `MemoryHeader.mtime` disponible, no usado en el render | 🟡 FIND-MEM3 |
| Query = último texto real del user, ignorando `<system-reminder>` inyectados | `_last_user_text` salta reminders | ✅ (mejora explícita) |
| Recall post-compactación (memorias sobreviven al recorte) | `compact_context` = `active_context` | ✅ (canónico: session-start hooks restauran; equivalente observable) |
| Rendido como `role:"system"`/`user` en `<system-reminder>` | dicts `role:"system"`; el loop los envuelve | ✅ 🔀 (nexo 07·events render) |
| Telemetría de shape del recall (`logMemoryRecallShape`) | N/A | ⛔ (telemetría) |

## E · Auto-extracción por fork (AUSENTE en runtime — `services/extractMemories/*`)

| Feature canónica | Runtime | Estado |
|---|---|---|
| **Agente de extracción forkeado** al cierre de cada query-loop (stop-hook `handleStopHooks`), fork perfecto que comparte prompt-cache | el modelo guarda a mano con `write_file`; **no hay extracción** | ❌ **FIND-MEM1** (la mayor brecha) |
| `createAutoMemCanUseTool`: Read/Grep/Glob libres, **Bash read-only** (`isReadOnly`), Write/Edit **sólo `isAutoMemPath`**, REPL passthrough; todo lo demás denegado | ausente | ❌ **FIND-MEM1b** (gate de escritura memory-scoped; nexo 06·hooks + B-02) |
| **Cursor** `lastMemoryMessageUuid`: sólo mensajes nuevos desde la última extracción; fallback si el uuid fue compactado | ausente | ❌ **FIND-MEM1c** |
| **Exclusión mutua** `hasMemoryWritesSince`: si el agente principal ya escribió memorias, se salta el fork y avanza el cursor | ausente | ❌ **FIND-MEM1d** |
| **Throttle** cada N turnos (`tengu_bramble_lintel`, default 1); trailing runs lo saltan | ausente | ❌ **FIND-MEM1e** |
| **Coalescing/trailing**: si llega llamada durante un run en curso, se stashea `pendingContext` y se corre una extracción trailing tras la actual | ausente | ❌ **FIND-MEM1f** |
| Pre-inyecta el manifiesto de memorias (reusa `scanMemoryFiles`), prompt `buildExtractAutoOnly/Combined` (misma taxonomía; estrategia read-en-paralelo turno-1, write-en-paralelo turno-2; `maxTurns:5`, `skipTranscript`) | ausente | ❌ FIND-MEM1 |
| **Sólo agente principal** (no subagentes), skip remote-mode; drain-on-shutdown (`drainPendingExtraction`, race con timeout) | ausente | ❌ **FIND-MEM1g/h** |
| `createMemorySavedMessage` (notificación system al usuario tras guardar) | ausente | ⛔/❌ (nexo 07·events) |
| `initExtractMemories` estado closure-scoped (inFlight/inProgress/turnsSince/pending) | ausente | ❌ FIND-MEM1 |

## F · Provider / superficies de activación (`MemoryProvider` vs los seams del canónico)

| Feature canónica | Runtime | Estado |
|---|---|---|
| La memoria **no es capability seleccionable**: es contexto+instrucciones (sin tools) | `catalog()`/`tools()` = `[]`; sólo `system_prompt_section`+`active_context`+`compact_context` | ✅ (tesis correcta) |
| Activación estable en system prompt (instrucciones+índice) por-scope | `system_prompt_section` → `build_memory_activation` | ✅ (contenido recortado: §B) |
| `startup` no-op (dir perezoso por turno; multi-tenant no conoce users al arrancar) | `startup`/`shutdown` no-op documentado | ✅ 🔀 (razón multi-tenant) |
| Quick-save `#` (input `# text` → `user-memory-input` → guarda) | ausente | ⛔/🟡 **FIND-MEM11** (afordancia; posible `UserInputProcessor`) |
| `/memory` slash (editar fichero en editor) | ausente | ⛔ (UI) |

## G · Deuda transversal que toca 13

| Concern | Detalle | Destino |
|---|---|---|
| **Permisos de escritura a memoria** | carve-out `isAutoMemPath` (canónico) vs working-allowlist del `ConfinedFilesystem` (runtime): la carpeta de memoria debe ser escribible sin que el gate deny-por-nombre la bloquee | **FIND-MEM12** = GAP-02 / `DEUDA-B-transversal` (B-02 permisos) + 09·fs_env |
| **Sanitización de clave de scope** | `<user_id>/<agent>` crudo → traversal; el canónico sanitiza (git-root `sanitizePath`, team `sanitizePathKey`, `validateMemoryPath`) | **FIND-MEM9** (core; ver §Plan MeR9) |
| **new_messages / notificación** | `createMemorySavedMessage` (extracción) como system message | nexo 07·events / B-new_messages |
| **Fork** | la extracción usa `runForkedAgent` (fork perfecto, cache-safe, canUseTool restringido, maxTurns) | nexo 05·execution/fork (EXEC*) |

## H · Session-memory (fuera de 13 → compactación) — resumen de handoff
Confirmado por lectura íntegra: `SessionMemory` mantiene un **único `.md` de la conversación actual** (plantilla
de secciones: Title/Current State/Task spec/Files/Workflow/Errors/Docs/Learnings/Key results/Worklog) que un fork
periódico actualiza (thresholds de tokens/tool-calls, `shouldExtractMemory`), gated por `isAutoCompactEnabled`.
`sessionMemoryCompact.ts` lo usa como **summary de compactación** (recorte desde `lastSummarizedMessageId`,
expandiendo a mínimos de tokens/text-blocks, respetando el invariante tool_use↔tool_result y el compact-boundary).
**No es la memoria transversal** — se audita en 01/compact. Cabo abierto a 01 con estos nombres.

## I · Team memory (fuera del core runtime → implementador `agentic_assistant`) — spec enumerada
Enumerada por lectura íntegra para que el implementador la porte si ofrece equipos:
- **Paths + seguridad** (`teamMemPaths.ts`): subdir `…/memory/team/`, `isTeamMemoryEnabled` (requiere auto-mem),
  y **validación fuerte** — `sanitizePathKey` (rechaza null-byte, traversal URL-encoded `%2e%2e`, unicode NFKC
  `．．／`, backslash, absoluta), `validateTeamMemWritePath`/`validateTeamMemKey` con `realpathDeepestExisting`
  (resuelve symlinks del ancestro existente; detecta dangling-symlink/ELOOP; falla-cerrado en EACCES).
- **Sync server-backed** (`index.ts`): `GET/PUT /api/claude_code/team_memory?repo=`, ETag `If-None-Match`/304,
  `version`, per-key `entryChecksums` (`sha256:`), **delta upload** (sólo keys cuyo hash difiere), **412 conflict
  resolution** (probe `?view=hashes` → recomputa delta → retry, local-wins), **batching** por `MAX_PUT_BODY_BYTES`
  (bin-packing determinista), aprendizaje de `max_entries` desde un 413 estructurado, upsert (deletes no propagan).
- **Watcher** (`watcher.ts`): `fs.watch({recursive})` debounced 2 s → push; pull inicial; sólo repos github.com;
  suppression de retry en fallo permanente; flush en shutdown.
- **Secret-scan** (`secretScanner.ts` + `teamMemSecretGuard.ts`): reglas gitleaks (AWS/GCP/Anthropic/OpenAI/
  GitHub/Slack/Stripe/private-key/…), `scanForSecrets`/`redactSecrets`; guard en `FileWrite/Edit.validateInput`
  que **bloquea** escribir secretos a team-memory. **Transferible al core** como seam opcional si el implementador
  comparte memoria.
- **Prompt** (`teamMemPrompts.ts`): `buildCombinedMemoryPrompt` (dos dirs private/team, `<scope>` por tipo,
  "nunca guardes secretos en team").
- **UI/telemetría** (`teamMemoryOps.ts`): detección de search/write a team + texto de resumen del transcript.

---

## Hallazgos (IDs para retoma)
- **FIND-MEM1** — auto-extracción por fork ausente (❌ mayor): fork en stop-hook + canUseTool memory-scoped
  (**1b**) + cursor (**1c**) + exclusión-mutua con escritura directa (**1d**) + throttle (**1e**) + coalescing/
  trailing (**1f**) + drain-on-shutdown (**1g**) + main-agent-only/skip-remote (**1h**).
- **FIND-MEM2** — recall determinista vs selector LLM (🔀 declarado); sub: `recentTools` (**2a**) + `alreadySurfaced`
  pre-selección (**2b**) + manifiesto con type/timestamp (**2c**).
- **FIND-MEM3** — recall sin caveat de frescura por-memoria (edad + "verifica antes de afirmar").
- **FIND-MEM4** — índice `MEMORY.md` sin truncar (200 líneas / 25 000 bytes + warning).
- **FIND-MEM5** — scan divergente: no-recursivo (**5a**) + lee fichero entero vs 30 líneas (**5b**) + sin cap 200 (**5c**) + orden (**5d**).
- **FIND-MEM6** — frontmatter `metadata.type` anidado vs `type` plano, y sin validar el enum de 4 tipos.
- **FIND-MEM7** — prompt de activación recortado: taxonomía detallada (**7a**), ignore+drift (**7b**),
  "Before recommending"/verificar (**7c**), plan/tasks (**7d**), "Searching past context" (**7e**), framing/explicit-save (**7f**).
- **FIND-MEM8** — sin gate enable/disable (`isAutoMemoryEnabled`).
- **FIND-MEM9** — clave de scope `<user_id>/<agent>` sin sanitizar (traversal). **Core, seguridad.**
- **FIND-MEM10** — memoria de subagente keyed por `agent_id` (uuid por-despacho, no persiste entre despachos del
  mismo tipo) vs por tipo+3 scopes; snapshot-sync ausente.
- **FIND-MEM11** — quick-save `#` ausente (afordancia de input; posible `UserInputProcessor`).
- **FIND-MEM12** — escritura a memoria: carve-out de permisos (=GAP-02/Deuda-B-02, cross-09).

### Cabos que ENTRARON / se abren a otros subsistemas
- **A 01/compact**: SessionMemory + `trySessionMemoryCompaction`/`calculateMessagesToKeepIndex`/`adjustIndexToPreserveAPIInvariants` (invariante tool_use↔tool_result en el recorte).
- **A 05/fork**: la extracción usa `runForkedAgent` (fork perfecto cache-safe, canUseTool restringido, maxTurns) — MeR1 depende de EXEC*.
- **A 06/hooks**: la extracción se dispara en `handleStopHooks` (Stop event) — nexo HOOK6.
- **A 07/events**: `createMemorySavedMessage` (new_messages/notificación).
- **A DEUDA-B**: FIND-MEM9 (sanitización de scope, comparte forma con 09·fs_env) + FIND-MEM12 (B-02 permisos).

## Recuento
✅ **~11** (store inyectable, MEMORY.md-como-índice-excluido, ensure_dir, aislamiento por-ítem del scan, MemoryHeader,
provider-sin-tools, activación estable cache-friendly, recall ≤5 concepto, query=último-user-real, compact_context,
startup-lazy multi-tenant) · 🟡 **~9** (guardado-2-pasos parcial, taxonomía-recortada, WHAT_NOT parcial, scan
lee-entero/sin-cap, parseMemoryType sin validar, manifiesto sin type/ts, alreadySurfaced en-loop, frescura mtime
sin usar, carve-out permisos) · 🔀 **~6** (scoping user/agent vs git-root, baseDir por inyección, recall keyword
vs LLM, scan no-recursivo, frontmatter anidado, memoria como seam propio) · ❌ **~7 findings mayores**
(FIND-MEM1/2a/3/4/7b-f/9/10 + sub-ítems) · ⛔ **~10** (memoria=RAM indicator+useMemoryUsage falso-positivo,
`/memory` slash, MemoryFileSelector, MemoryUpdateNotification, UserMemoryInputMessage, MemoryStep, useMemorySurvey,
utils/memory/{types,versions}, KAIROS daily-log, Cowork extraGuidelines). **12 findings** (FIND-MEM1…12). Lo
vinculante son los IDs FIND-MEM y los cabos.

---

## Ledger de archivos (auditoría de cierre — protocolo obligatorio)

> **Nota de honestidad.** Se abrió **TODO** el árbol de memoria del canónico (26 archivos), incluidos los que
> "parecen" UI/team/session, **antes** de clasificar — precisamente donde 02/07/08 avisan que se esconde el core.
> El payoff apareció: `useMemoryUsage`/`MemoryUsageIndicator` resultaron ser **monitoreo de RAM del proceso**
> (falso positivo de nombre — habría sido erróneo asumir que eran memdir por el nombre); `teamMemPaths.ts` destapó
> la **validación anti-traversal** que el runtime NO tiene (**FIND-MEM9**), y `agentMemory.ts` destapó que el
> keying por **tipo de agente** (no por uuid) es lo homologado (**FIND-MEM10**). Los cuatro archivos grandes
> (`sessionMemoryCompact.ts` 630, `extractMemories.ts` 615, `memdir.ts` 507, `sessionMemory.ts` 495, y el mayor
> del cluster team `teamMemorySync/index.ts` 1256) se leyeron **íntegros 1→EOF**, no por hitos. `useMemorySurvey.tsx`
> se leyó 1-180 de 213 (el tail 181-213 es continuación de la misma lógica de probabilidad/efecto del hook; ⛔
> encuesta) — **la única lectura parcial**, declarada. Ninguna ⛔ se puso por título: cada UI se **abrió** y se
> confirmó presentacional.

### Canónico (`/home/noheroes/python/claude-code/src`) — TODOS abiertos (26)
| Archivo | LOC | Lectura |
|---|---|---|
| **— core memdir (in-scope) —** | | |
| `memdir/memdir.ts` | 507 | **íntegro** (truncateEntrypoint, ensureMemoryDirExists, buildMemoryLines/Prompt, loadMemoryPrompt, buildSearchingPastContext, KAIROS daily-log) |
| `memdir/memoryTypes.ts` | 271 | **íntegro** (4-type taxonomy individual+combined, WHAT_NOT, WHEN_TO_ACCESS, DRIFT, TRUSTING_RECALL, FRONTMATTER_EXAMPLE, parseMemoryType) |
| `memdir/memoryScan.ts` | 94 | íntegro (scanMemoryFiles recursivo/30-líneas/cap-200/newest-first, formatMemoryManifest) |
| `memdir/findRelevantMemories.ts` | 141 | íntegro (selector LLM sideQuery, recentTools, alreadySurfaced, JSON-schema, telemetría) |
| `memdir/paths.ts` | 278 | íntegro (isAutoMemoryEnabled, isExtractModeActive, getMemoryBaseDir, validateMemoryPath, getAutoMemPath/base, daily-log, isAutoMemPath) |
| `memdir/memoryAge.ts` | 53 | íntegro (memoryAgeDays/Age, memoryFreshnessText/Note) |
| **— auto-extracción (in-scope) —** | | |
| `services/extractMemories/extractMemories.ts` | 615 | **íntegro** (createAutoMemCanUseTool, cursor, hasMemoryWritesSince, throttle, coalescing/trailing, runForkedAgent, drain) |
| `services/extractMemories/prompts.ts` | 154 | íntegro (opener + buildExtractAutoOnly/Combined) |
| **— agent-memory (in-scope) —** | | |
| `tools/AgentTool/agentMemory.ts` | 177 | íntegro (getAgentMemoryDir 3 scopes, isAgentMemoryPath, loadAgentMemoryPrompt) |
| `tools/AgentTool/agentMemorySnapshot.ts` | 197 | íntegro (check/initialize/replace/mark snapshot sync) |
| **— team (→ implementador, enumerado) —** | | |
| `services/teamMemorySync/index.ts` | 1256 | **íntegro** (fetch/hashes, upload, batchDeltaByBytes, readLocal+secret-scan, writeRemote, pull/push/sync, 412) |
| `services/teamMemorySync/watcher.ts` | 387 | íntegro (fs.watch debounced, pull inicial, suppression, flush) |
| `services/teamMemorySync/secretScanner.ts` | 324 | íntegro (reglas gitleaks, scanForSecrets, redactSecrets) |
| `services/teamMemorySync/types.ts` | 156 | íntegro (schemas API, SkippedSecret, resultados) |
| `services/teamMemorySync/teamMemSecretGuard.ts` | 44 | íntegro (checkTeamMemSecrets en validateInput) |
| `memdir/teamMemPaths.ts` | 292 | íntegro (sanitizePathKey, realpathDeepestExisting, validate*, isTeamMem*) |
| `memdir/teamMemPrompts.ts` | 100 | íntegro (buildCombinedMemoryPrompt) |
| `utils/teamMemoryOps.ts` | 88 | íntegro (isTeamMemorySearch/WriteOrEdit, appendTeamMemorySummaryParts) |
| **— session-memory (→ 01/compact, confirmado) —** | | |
| `services/compact/sessionMemoryCompact.ts` | 630 | **íntegro → handoff 01** (calculateMessagesToKeepIndex, adjustIndexToPreserveAPIInvariants, trySessionMemoryCompaction) |
| `services/SessionMemory/sessionMemory.ts` | 495 | íntegro → handoff 01 (shouldExtractMemory, setup, extractSessionMemory fork, manual) |
| `services/SessionMemory/prompts.ts` | 324 | íntegro → handoff 01 (template + update prompt + section budgeting) |
| `services/SessionMemory/sessionMemoryUtils.ts` | 207 | íntegro → handoff 01 (config/thresholds/estado) |
| **— detección/UI (⛔ abierto y confirmado) —** | | |
| `utils/memoryFileDetection.ts` | 289 | íntegro (detectSession*, isAutoMem/AgentFile, memoryScopeForPath, isMemoryDirectory, isShellCommandTargetingMemory — mayormente collapse UI) |
| `commands/memory/memory.tsx` | 89 | íntegro → ⛔ (`/memory`→editor) |
| `components/memory/MemoryFileSelector.tsx` | 437 | 1-120 → ⛔ (picker; el resto es render de opciones/folders — confirmado UI) |
| `components/memory/MemoryUpdateNotification.tsx` | 44 | íntegro → ⛔ (+ getRelativeMemoryPath) |
| `components/messages/UserMemoryInputMessage.tsx` | 74 | íntegro → ⛔ (render quick-save `#`) |
| `components/agents/…/wizard-steps/MemoryStep.tsx` | 112 | íntegro → ⛔ (wizard scope agent-memory) |
| `components/MemoryUsageIndicator.tsx` | 36 | íntegro → ⛔ (**RAM**, no memdir) |
| `hooks/useMemoryUsage.ts` | 39 | íntegro → ⛔ (**RAM** heap polling) |
| `components/FeedbackSurvey/useMemorySurvey.tsx` | 213 | 1-180 → ⛔ (encuesta; tail = misma lógica, declarado) |
| `utils/memory/types.ts` | 12 | íntegro → ⛔ (MEMORY_TYPE_VALUES de instruction-files) |
| `utils/memory/versions.ts` | 8 | íntegro → ⛔ (projectIsInGitRepo) |

### Runtime (`…/capabilities/memory`)
| Archivo | LOC | ¿Leído íntegro? |
|---|---|---|
| `__init__.py` | 19 | sí |
| `store.py` | 138 | sí |
| `recall.py` | 40 | sí |
| `provider.py` | 102 | sí |
| `prompt.py` | 48 | sí |

### Preguntas de cierre
- ¿Se revisó **todo** cada archivo **canónico** listado? **sí.** Los 26 abiertos; los 5 mayores (index.ts 1256,
  sessionMemoryCompact 630, extractMemories 615, memdir 507, sessionMemory 495) íntegros 1→EOF. Únicas parciales
  declaradas: `MemoryFileSelector.tsx` (1-120, resto render de opciones) y `useMemorySurvey.tsx` (1-180/213, tail
  = continuación del hook) — ambas ⛔ UI, no core. Ningún ⛔ por título: cada UI abierta y confirmada.
- ¿Se revisó **todo** cada archivo **runtime** listado? **sí** (los 5 archivos ÍNTEGROS, 347 LOC).
- ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **sí.** Se enumeran las 6 sub-piezas de la
  auto-extracción (fork/canUseTool/cursor/exclusión/throttle/coalescing), las 6 secciones de prompt que faltan,
  las 4 divergencias de scan, la validación anti-traversal ausente (FIND-MEM9, destapada al abrir `teamMemPaths`),
  el keying por-tipo vs uuid (FIND-MEM10, al abrir `agentMemory`), y el falso positivo RAM (al abrir `useMemoryUsage`).
- ¿Quedó **todo cubierto (nada pendiente)**? **sí** — SessionMemory/SM-compact delegado a **01/compact** con
  nombres; team-memory enumerado como spec del **implementador**; los cabos de fork (05), stop-hook (06),
  new_messages (07) y permisos/scope-sanitize (DEUDA-B) anotados con destino.

**Cierre habilitado: las 4 respuestas = sí.**

---

## Plan de homologación / remediación desarrollada (Deuda A de 13)

> 1ª pasada = diseño. Cada MeR desarrolla la remediación de una vez: comportamiento · seam · firma · cableado ·
> orden · test. Los xfail(strict) codifican targets; passing = homologado.

### MeR1 · FIND-MEM1 — auto-extracción por fork al cierre del turno
- **Comportamiento**: al terminar un query-loop sin tool-calls (Stop), si el agente principal NO escribió memorias
  en el rango nuevo, un fork lee los últimos ~N mensajes y escribe/actualiza ficheros de memoria; con cursor,
  exclusión-mutua, throttle y coalescing. Best-effort (errores no rompen el turno).
- **Seam**: nuevo `capabilities/memory/extractor.py` (`MemoryExtractor` con estado por-sesión) + enganche en el
  runner de stop-hooks (06) que ya existe; usa el fork de 05 (`RuntimeContextForker`/runner) con un `canUseTool`
  restringido (MeR1b) y `PermissionContext` propio.
- **Firma**: `class MemoryExtractor: async def run(self, ctx: ToolUseContext, *, is_trailing=False) -> None`;
  `def _model_visible_since(msgs, cursor) -> int`; `def _has_memory_writes_since(msgs, cursor, is_mem_path) -> bool`.
  Estado: `_cursor: str|None`, `_in_progress: bool`, `_turns_since: int`, `_pending: ctx|None`, `_inflight: set`.
- **Cableado**: el `MemoryProvider` expone `extractor` y el factory lo cablea al Stop del `HookRunner`; `drain()`
  se llama en el shutdown del runtime (18/factory). Sólo agente principal (`ctx.agent_id is None`), skip si un
  flag/parametro `auto_extract` está off.
- **Orden**: tras MeR1b (gate), MeR9 (is_mem_path sanitizado); depende de 05·fork y 06·stop-hook.
- **Test**: `test_extract_runs_on_stop_when_no_direct_write`, `test_extract_skipped_when_agent_wrote (FIND-MEM1d)`,
  `test_cursor_advances_only_on_success`, `test_throttle_every_n_turns`, `test_trailing_run_after_inflight`,
  `test_extract_main_agent_only` — xfail(strict) hasta portar.

### MeR1b · FIND-MEM1b — `canUseTool` memory-scoped para el fork de extracción
- **Comportamiento**: Read/Grep/Glob permitidos; Bash sólo read-only; Write/Edit sólo si el `file_path` está bajo
  la carpeta de memoria del scope; todo lo demás denegado con razón.
- **Seam**: `capabilities/memory/permissions.py::memory_scoped_permission(memory_dir)` → `PermissionContext`.
- **Firma**: `def memory_scoped_permission(memory_dir: Path, is_read_only_bash: Callable) -> PermissionContext`.
- **Cableado**: lo consume MeR1 al forkear; reusa `is_mem_path` de MeR9 y el clasificador read-only de Bash (10·bash).
- **Orden**: antes de MeR1. **Test**: `test_mem_perm_allows_read`, `_denies_write_outside_memdir`, `_bash_readonly_only`.

### MeR2 · FIND-MEM2a/b/c — recall: recentTools + alreadySurfaced + manifiesto tipado
- **Comportamiento**: `rank_memories` acepta `recent_tools` (excluye memorias cuya descripción es reference/API-doc
  de una tool en uso, salvo warnings/gotchas) y `already_surfaced` (excluye paths ya mostrados antes de aplicar el
  límite de 5); `_render_recall`/manifiesto incluyen `[type]` y timestamp ISO. (El selector LLM queda como
  `RecallStrategy` inyectable — MeR2-opt, no core.)
- **Seam**: `recall.py` (params nuevos + filtro), `provider.active_context` (pasa `recent_tools` desde `ctx`,
  `already_surfaced` desde estado del provider por-agente).
- **Firma**: `rank_memories(headers, query, limit=5, recent_tools: list[str]=[], already_surfaced: set[str]=set())`.
- **Cableado**: el provider mantiene `_surfaced: dict[agent, set[str]]`; el loop sigue dedup por path (redundante-seguro).
- **Orden**: independiente. **Test**: `test_recall_excludes_recent_tool_refs`, `test_recall_skips_already_surfaced`,
  `test_manifest_has_type_and_ts`.

### MeR3 · FIND-MEM3 — caveat de frescura por memoria recallada
- **Comportamiento**: cada memoria recallada >1 día lleva "hace N días… verifica code:line antes de afirmar";
  hoy/ayer sin ruido.
- **Seam**: `recall.py::memory_freshness(mtime)` + `_render_recall` lo antepone.
- **Firma**: `def memory_age_days(mtime: float) -> int`; `def memory_freshness_text(mtime: float) -> str`.
- **Orden**: independiente (usa `MemoryHeader.mtime` ya presente). **Test**: `test_freshness_over_1_day`, `_today_empty`.

### MeR4 · FIND-MEM4 — truncado del índice `MEMORY.md`
- **Comportamiento**: `read_index` acota a 200 líneas / 25 000 bytes, corta en salto de línea, añade warning que
  nombra qué cap disparó.
- **Seam**: `store.py::_truncate_entrypoint(raw) -> str` usado por `read_index`.
- **Firma**: `def _truncate_entrypoint(raw: str, max_lines=200, max_bytes=25_000) -> str`.
- **Orden**: independiente. **Test**: `test_index_line_cap`, `_byte_cap`, `_warning_names_cap`.

### MeR5 · FIND-MEM5 — scan recursivo, 30-líneas, cap 200, newest-first
- **Comportamiento**: `scan` recorre subdirs (`rglob("*.md")`), lee sólo la cabecera (primeras ~30 líneas) para
  el frontmatter, ordena newest-first por mtime y corta a 200.
- **Seam**: `store.py::scan` + `_parse_header` (lee rango).
- **Firma**: `scan(agent_id) -> list[MemoryHeader]` (recursivo, cap `MAX_MEMORY_FILES=200`).
- **Orden**: independiente. **Test**: `test_scan_recursive`, `_reads_only_header`, `_cap_200_newest_first`.

### MeR6 · FIND-MEM6 — frontmatter tipado (plano) + validación de enum
- **Comportamiento**: aceptar `type:` **plano** (homologar el canónico) manteniendo compat con `metadata.type`
  anidado; validar contra `{user,feedback,project,reference}` (unknown/legacy → `""`).
- **Seam**: `store.py::_parse_header` (`front.get("type") or (front.get("metadata") or {}).get("type")`, luego
  `_parse_memory_type`). El prompt (MeR7) migra el ejemplo a `type:` plano.
- **Firma**: `MEMORY_TYPES=("user","feedback","project","reference")`; `def _parse_memory_type(raw)->str`.
- **Orden**: junto a MeR7. **Test**: `test_flat_type`, `test_nested_metadata_type_compat`, `test_unknown_type_degrades`.

### MeR7 · FIND-MEM7 — prompt de activación completo
- **Comportamiento**: `build_memory_activation` gana: taxonomía detallada por tipo (description/when/how/examples/
  body_structure), "Qué NO guardar" con cláusula explicit-save, "Cuándo acceder" (+ ignore-memory + drift-caveat),
  "Antes de recomendar desde memoria" (verificar file/func/flag), "Memoria vs Plan/Tasks", "Buscar contexto pasado"
  (grep de topic-files + transcript), framing "constrúyela con el tiempo / quién es el user", save/forget inmediato.
- **Seam**: `prompt.py` (constantes de sección reutilizables, espejo de `memoryTypes.ts`; el índice sigue inyectado).
- **Firma**: `build_memory_activation(memory_dir, index_content, *, transcript_glob=None) -> str`.
- **Orden**: junto a MeR6 (formato de frontmatter en el ejemplo). **Test**: `test_prompt_has_trusting_recall`,
  `_has_ignore_and_drift`, `_has_searching_past_context`, `_frontmatter_example_flat_type`.

### MeR8 · FIND-MEM8 — gate enable/disable
- **Comportamiento**: `MemoryProvider` respeta un flag de habilitación (config del runtime / env del implementador);
  desactivado ⇒ `system_prompt_section`/`active_context` devuelven vacío y el extractor no corre.
- **Seam**: `provider.__init__(store, *, enabled: Callable[[], bool] = lambda: True)`.
- **Orden**: independiente. **Test**: `test_disabled_provider_no_prompt_no_recall`.

### MeR9 · FIND-MEM9 — sanitización de la clave de scope (**seguridad, core**)
- **Comportamiento**: la clave `<user_id>/<agent>` se sanitiza por-segmento (rechaza null-byte, `..`, separadores,
  URL-encoded/unicode-traversal, absoluto) antes de unirla al root; `memory_dir` nunca escapa del root. `is_mem_path`
  (para MeR1b) compara contra el `memory_dir` normalizado.
- **Seam**: `store.py::_safe_segment(s)` aplicado en `_scope`/`memory_dir`; `store.is_mem_path(path, agent)`.
- **Firma**: `def _safe_segment(s: str) -> str` (raise/replace); `def is_mem_path(self, path, agent_id) -> bool`.
- **Cableado**: lo consume MeR1b y el carve-out de permisos (MeR12). Comparte forma con 09·fs_env (`ConfinedFilesystem`).
- **Orden**: antes de MeR1b. **Test**: `test_scope_rejects_dotdot`, `_rejects_null_byte`, `_rejects_absolute`,
  `test_is_mem_path_true_inside_false_outside`.

### MeR10 · FIND-MEM10 — memoria de subagente por tipo + scopes
- **Comportamiento**: los subagentes con memoria activada se keyean por **tipo de agente** (estable entre despachos),
  no por `agent_id` uuid; soportar scopes `user|project|local`. (Snapshot-sync VCS → ❌ diferido, se documenta como
  no-portado; el implementador puede añadirlo.)
- **Seam**: `provider._scope` usa `ctx.agent_type` (nuevo en `ToolUseContext`, cabo a 03·context) para subagentes;
  `store` gana un eje de scope opcional.
- **Firma**: `_scope(ctx)`: subagente → `f"{user}/agent/{sanitize(agent_type)}"`; scope configurable.
- **Cableado**: requiere que `ToolUseContext` exponga `agent_type` (cabo a 03/05). Corrige la divergencia observable
  "la memoria del subagente no sobrevive al siguiente despacho del mismo tipo".
- **Orden**: tras MeR9 (sanitize). **Test**: `test_subagent_memory_keyed_by_type_persists_across_dispatch`.

### MeR11 · FIND-MEM11 — quick-save `#` (afordancia)
- **Comportamiento**: input `# text` se interpreta como "guarda esto" (el implementador puede mapearlo a un
  `UserInputProcessor` que dispare MeR1 sobre ese texto). Diferido al implementador; se documenta el contrato.
- **Seam**: `contracts/user_input.py::UserInputProcessor` (ya existe) — nota de diseño, no core-obligatorio.
- **Orden**: opcional. **Test**: (implementador) `test_hash_prefix_triggers_save`.

### MeR12 · FIND-MEM12 (=GAP-02 / Deuda-B-02) — carve-out de escritura a memoria
- **Comportamiento**: `write_file`/`file_edit` deben poder escribir la carpeta de memoria del scope sin que el gate
  deny-por-nombre ni el `ConfinedFilesystem` lo bloqueen — el equivalente al carve-out `isAutoMemPath` del canónico.
- **Seam**: se resuelve en `DEUDA-B-transversal` (B-02 permisos) + 09·fs_env: el `PermissionContext` reconoce
  `store.is_mem_path` (MeR9) como allow-para-escritura.
- **Orden**: junto a B-02. **Test**: `test_model_can_write_memory_dir`, `_cannot_write_outside`.

### MeR13 · Referencias (no se re-desarrollan aquí)
- SessionMemory + SM-compact → **01/compact** (con `trySessionMemoryCompaction`/`calculateMessagesToKeepIndex`/
  `adjustIndexToPreserveAPIInvariants`). Team-memory → **implementador** (§I: sync/watcher/secret-scan/paths).
  Fork → **05**. Stop-hook → **06**. new_messages → **07**. KAIROS daily-log → modo assistant (05·EXEC10).

## Nota metodológica
El árbol de "memoria" del canónico mezcla **cuatro sistemas distintos** que comparten prefijo de nombre: la
memoria transversal (memdir, in-scope), la memoria de sesión-para-compactación (→01), la team-sync
(→implementador), y **dos falsos positivos** (RAM `useMemoryUsage`/`MemoryUsageIndicator`, e instruction-files
`utils/memory/*`). Separarlos exigió **abrir cada archivo** (lección 02): el juicio por título habría (a) mandado
la validación anti-traversal de `teamMemPaths` al olvido, (b) confundido el monitor de RAM con memdir, y (c)
perdido que el keying de agent-memory es por tipo, no por uuid. Los cinco findings core reales (MEM1/3/4/9/10) y
las seis secciones de prompt (MEM7) son el trabajo vinculante; team/session se enumeran con destino, no se difieren
a "ningún sitio".

### RE-AUDITORÍA 2026-07-14 (belt-and-suspenders, ordenada por el usuario) — **CONFIRMADO sin cambios**
Re-leídos ÍNTEGROS 1→EOF de cero, diff contra este doc: `services/teamMemorySync/index.ts` (1256, el más grande) y
`memdir/memdir.ts` (507). **Todo coincide con el ledger**: teamMemorySync (fetch+retry / fetchHashes view=hashes /
upload+If-Match ETag / batchDeltaByBytes bin-packing / readLocalTeamMemory walk+secret-scan+oversize+maxEntries-truncate /
writeRemoteEntriesToLocal validateTeamMemKey-traversal+skip-if-matches / pull server-wins / push local-wins-delta +
412-conflict-loop+probe / 413-structured serverMaxEntries — team→implementador); memdir (truncateEntrypointContent
200-líneas/25KB = MEM4, ensureMemoryDirExists, buildMemoryLines/buildMemoryPrompt = MEM7, buildSearchingPastContextSection,
buildAssistantDailyLogPrompt KAIROS = ⛔, extraGuidelines Cowork = ⛔, loadMemoryPrompt dispatch auto/team/KAIROS).
`extractMemories.ts` (615) ya se había re-verificado íntegro en el paso previo. **Cero findings nuevos, cero
sobre-declaración.** Ledger de 13 confirmado honesto.

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09) — 2026-07-20 · **VALIDADA sin cambios de estado**

> Método (L11): el objeto a validar es la **homologación A↔B**, NO el documento. Para cada fila **✅/🔀** se abrió la
> **implementación de B** que produce el comportamiento y se siguió el dato de punta a punta; para las **❌** (ausencia
> total) confirmación-de-doc y verificación-de-completitud CONVERGEN. Lección reforzada de 11/12: **cableado = leer el
> ENSAMBLADOR 1→EOF (nunca grep)** + **re-leer A 1→EOF ESTA ronda** (no apoyarse en "leído en la 1ª pasada").

### Cableado confirmado abriendo el ENSAMBLADOR (L09), no por grep
- **Registro condicional (seam de integrador)**: `factory._build_capability_manager` (leído 1→EOF) registra
  `MemoryProvider(store)` **sólo si** `caps.memory_store is not None or caps.memory_root is not None` (factory.py:166-172);
  si el integrador no siembra `memory_root`/`memory_store`, **no hay provider de memoria en absoluto** — hermano del
  seam condicional de MCP/Skills (mismo `_build_capability_manager`). El `capability_manager` resultante es la MISMA
  instancia para raíz y subagentes (pasada a `LocalAgentRuntime`, factory:218-221; compartida a los subagentes
  runtime.py:358, ya visto 11/12).
- **Reensamblado PER-TURNO (confirmado leyendo `agent_loop.py:185-218` dentro del `for _turn in range(_MAX_TURNS)`)**,
  hermano EXACTO de MCP/Skills:
  - `build_tool_pool` (loop:94-95): memoria aporta `tools()==[]` → no toca el pool (provider-sin-tools ✅).
  - `system_prompt_sections(ctx)` (loop:213 → manager:81-96 → `MemoryProvider.system_prompt_section` provider.py:79-84):
    cada turno hace `ensure_dir` + `read_index` + `build_memory_activation` → **el índice se RE-LEE de disco cada turno**
    (una memoria escrita en el turno N aparece en el prompt del turno N+1). Texto estable salvo el índice = cache-friendly ✅.
  - `_inject_recall(ctx)` (loop:218 → `active_context` → `MemoryProvider.active_context` provider.py:86-95 → `scan` +
    `rank_memories`): recall ≤5 rendido como `<system-reminder>` `role:"user"` con dedup por contenido (loop:121-130).
  - El test `test_memory_provider.py:139-144` asegura que el loop/runtime **NUNCA importa `capabilities.memory`** —
    consumo polimórfico vía el manager, no acoplamiento directo (arquitectura correcta).

### ❌ críticos re-confirmados por CABLEADO / ABSENCIA (no por tabla)
- **FIND-MEM1 (auto-extracción ausente)** — grep de wiring de extracción en todo `src/` (fuera de tests) = **vacío**:
  no hay `MemoryExtractor`, ni fork de extracción, ni disparo en stop-hook. **Nada la dispara.** Lado A re-leído
  1→EOF esta ronda (`extractMemories.ts` 615): confirmadas las 8 sub-piezas (main-agent-only `if agentId return` :532,
  gate `isAutoMemoryEnabled` :545, skip-remote :550, coalescing/trailing :557-564/:510-521, cursor+fallback-compactado
  :307/:340/:103-108/:432-435, exclusión-mutua `hasMemoryWritesSince` :348-360, throttle N-turnos :377-386,
  `createAutoMemCanUseTool` memory-scoped :171-222, `runForkedAgent`+maxTurns:5+skipTranscript :415-427, drain 60s
  :579-586/:611-614). B: ninguna. ❌ se sostiene, la mayor brecha.
- **FIND-MEM10 (agent-memory por uuid vs por-TIPO)** — confirmado **leyendo el contexto del ensamblador** (no la línea
  de grep): en `_build_child` (runtime.py:198-218) la rama raíz mintea `agent_id = f"agent_{uuid.uuid4().hex[:12]}"`
  (:205) y `ToolUseContext(agent_id=…)` (:210); en `RuntimeContextForker.fork` (fork/__init__.py:61-93) cada subagente
  mintea `agent_id` uuid FRESCO (:69) y lo pone en el ctx hijo (:88) — en la ruta real de despacho/fork, no una línea
  suelta. `runtime.py:427` lo comenta ("el agent_id aleatorio discrimina el subtree"). `provider._scope`: subagente →
  `context.agent_id` (uuid volátil), raíz → `"main"` estable (vía `is_subagent`). ⇒ raíz OK (memoria persiste bajo
  `main`), pero subagente-de-tipo-X forkeado 2× = 2 uuids = 2 dirs → **la memoria del subagente NO persiste entre
  despachos**. Cross-confirmado en A (re-leído 1→EOF, `agentMemory.ts:52-65`): el canónico keya por
  `sanitizeAgentTypeForPath(agentType)` = **ESTABLE**, con 3 scopes `user|project|local`. ❌ se sostiene.
- **FIND-MEM4/5/6/7/8/9/12** — re-confirmados abriendo B: `read_index` devuelve crudo sin truncar (store.py:117-122 =
  MEM4); `scan` `glob("*.md")` no-recursivo + `_parse_header` lee el fichero ENTERO + `sorted(glob)` por nombre sin cap
  (store.py:124-135/:68-91 = MEM5a-d); `_parse_header` lee sólo `metadata.type` anidado **sin** fallback a `type:` plano
  y **sin** validar el enum (store.py:79-80 = MEM6); `build_memory_activation` sin TRUSTING_RECALL/ignore/drift/plan-tasks/
  searching-past-context (prompt.py:6-45 = MEM7); provider siempre activo (`__init__(store)` sin flag = MEM8); `_scope`
  = `f"{user}/{agent}"` crudo unido a `self._root` **sin sanitizar** → traversal (provider.py:53-63 + store.py:106-110;
  si `user_id`/`agent_id` trae `..` o ruta absoluta, `Path / "/etc/…"` escapa = **MEM9 seguridad**); escritura por
  `write_file` bajo el `ConfinedFilesystem` sin carve-out `isAutoMemPath` (= MEM12/GAP-02). Lado A re-leído 1→EOF esta
  ronda confirma los anclas exactos: `truncateEntrypointContent` 200/25k (memdir.ts:57-103), `scanMemoryFiles`
  recursive+30-líneas+cap-200+newest-first (memoryScan.ts:35-77), `parseMemoryType`+`MEMORY_FRONTMATTER_EXAMPLE` flat
  `type:` (memoryTypes.ts:28-31/:266), las 6 secciones de prompt (memoryTypes.ts + memdir.ts:199-266), `isAutoMemoryEnabled`
  (paths.ts:30-55), **`sanitizePath(getAutoMemBase())`** = el sanitizador de clave-scope que el runtime NO tiene
  (paths.ts:231), `isAutoMemPath` carve-out (paths.ts:274-278). **CERO discrepancias, citas exactas.**

### ✅/🔀 sostenidas abriendo B (mini-ledger de consumidores)
| Fila | Mecanismo B abierto | Veredicto |
|---|---|---|
| Store inyectable ✅🔀 | `MemoryStore` Protocol + `FilesystemMemoryStore` (store.py) + registro factory:166-172 | sostenida |
| MEMORY.md excluido/inyectado ✅ | `scan` salta `ENTRYPOINT` (store.py:130) + `read_index` (117) + `system_prompt_section` (provider:79-84) | sostenida |
| provider-sin-tools ✅ | `catalog()`/`tools()` == `[]` (provider:73-77); manager los agrega vacío | sostenida |
| activación estable cache-friendly ✅ | `build_memory_activation` sólo varía con `index_block` (prompt.py:14-15) | sostenida |
| recall ≤5 concepto / query=último-user ✅ | `rank_memories(limit=5)` (recall:16-37) + `_last_user_text` salta reminders (provider:15-28) | sostenida |
| aislamiento por-ítem del scan ✅ | `_parse_header` try/except → `None`→omite (store:68-91/:132-134) | sostenida |
| scoping user/agent 🔀 | `_scope` `<user>/<agent>` con `main` estable (provider:52-63) — deliberado multi-tenant | sostenida (pero **sin sanitizar** = MEM9) |
| recall keyword vs LLM 🔀 | `rank_memories` overlap determinista + `mtime` desc (recall:28-37) | sostenida |
| startup-lazy 🔀 | `startup`/`shutdown` no-op (provider:65-71); dir perezoso por turno | sostenida |

### 1 PRECISIÓN de cableado (NO voltea estado — gate-11 value-add, leyendo el ensamblador L09)
- **Fila D "Recall post-compactación · `compact_context = active_context` ✅"** — el ❌/✅ observable se sostiene, PERO
  el **mecanismo citado no es el vivo**: `compact_context` **NO tiene NINGÚN consumidor de producción** (grep: sólo
  tests; los dos agregadores `manager.compact_context` manager.py:104-108 y el `CompactionProvider` de
  `contracts/compaction.py:11-23` tampoco tienen caller de prod). El loop consume **sólo** `active_context` +
  `system_prompt_sections`. La equivalencia observable ("las memorias sobreviven al recorte") la entrega el
  **re-inject PER-TURNO de `active_context`** (agent_loop.py:218; cuando la compactación recorta la historia, el dedup
  ya no casa y el recall se re-surface el turno siguiente — comentario loop:214-217), **no** `compact_context`.
  ⇒ `compact_context` es una **costura latente que espera al motor de compactación NO PORTADO** (motor #1 de 02·GAP-L4 /
  01·CompactionProvider) = **cara aguas-abajo de un ❌ A↔B YA conocido**, transversal a todos los providers
  (plan/skills/mcp/memory), **NO** una costura B-interna NUEVA tipo `to_llm`/`category`/LAT-*. Por anti-padding (L10)
  **no se registra como nuevo B-orphan** ni se re-cuenta: ya está implícito en "motor de compactación ausente" (01/02).
  Refina la justificación de la fila D; el ✅ se apoya ahora en el mecanismo correcto (recall per-turno).

### Cabos verificados (SIGUIENTE de la 2ª vuelta)
- **SessionMemory → 01/compact**: sigue fuera-de-alcance-con-destino (satélite de 01), enumerado en §H; re-audit
  2026-07-14 lo confirmó íntegro. NO re-leído esta ronda (satélite de otra categoría, L07).
- **FIND-SKILL14 (ranking por uso) — nexo con `rank_memories`**: **NO aterriza**. El ranking por frecuencia-de-uso
  con half-life (skillUsageTracking) es específico de SKILLS; el recall de memoria NO usa señal de uso — ni el runtime
  (keyword-overlap + `mtime` desc, recall.py) ni el canónico (selector LLM, findRelevantMemories). Sin nexo real; el
  cabo se cierra sin finding.
- **invoked/cleanup-por-agent (05·ExR6 / 08·SR3)**: la memoria **no tiene estado mutable por-agente** que limpiar — el
  provider re-escanea disco cada turno y scopea por `_scope(ctx)`; no hay `invoked_set` vivo (el `_surfaced: dict[agent,set]`
  del §Plan MeR2 es propuesta FUTURA, ausente en B). Sin concern de cleanup. Cabo cerrado.

### Ledger de lectura de esta ronda (gate 11)
**B (`capabilities/memory/`, 1→EOF esta ronda)**: `store.py` 138 · `provider.py` 102 · `recall.py` 40 · `prompt.py` 48
· `__init__.py` 19 — **todos íntegros**. **ENSAMBLADOR (1→EOF esta ronda)**: `factory.py` 267 íntegro · `manager.py`
112 íntegro · `agent_loop.py:85-234` (cuerpo de ensamblado per-turno) íntegro.
**A in-scope (RE-LEÍDO 1→EOF esta ronda, L11)**: `extractMemories.ts` 615 · `memdir.ts` 507 · `memoryTypes.ts` 271 ·
`paths.ts` 278 · `memoryScan.ts` 94 · `findRelevantMemories.ts` 141 · `memoryAge.ts` 53 · `agentMemory.ts` 177 —
**todos íntegros, citas exactas, cero discrepancias**.
**A ❌-por-ausencia — RE-LEÍDOS 1→EOF esta ronda tras el gate auto-adversarial del usuario** (ver §honestidad):
`services/extractMemories/prompts.ts` 154 (`opener` + `buildExtractAutoOnly/CombinedPrompt`: reutilizan
TYPES_SECTION_INDIVIDUAL/COMBINED + WHAT_NOT + MEMORY_FRONTMATTER_EXAMPLE + estrategia read-turno1/write-turno2 :39 +
anuncio memory-scoped :37 — todo el sistema de extracción ausente en B) y `tools/AgentTool/agentMemorySnapshot.ts` 197
(`getSnapshotDirForAgent` keyed por **agentType** + `checkAgentMemorySnapshot` none/initialize/prompt-update +
`initialize|replace|markSnapshotSynced` + `.snapshot-synced.json` — snapshot-sync VCS ausente en B, refuerza FIND-MEM10
keying-por-tipo). **CERO discrepancias, citas exactas.** ⇒ **los 10 archivos A in-scope leídos 1→EOF esta ronda**.
**Team/session/UI**: fuera-de-alcance-con-destino (§H/§I + ⛔), re-audit 2026-07-14 confirmó los grandes; no re-leídos.

### §Nota de honestidad
El value-add del gate 11 fue **abrir el ENSAMBLADOR 1→EOF** (`factory` + `manager` + el cuerpo per-turno del loop):
ahí apareció que (a) el `MemoryProvider` se registra **condicionalmente** (seam de integrador), (b) el reensamblado es
**per-turno** como skills/MCP (índice re-leído cada turno), y (c) `compact_context` **no tiene consumidor de prod** —
la equivalencia post-compactación la da el recall per-turno, no ese hook. La 1ª pasada (doc + re-audit) enumeró A a
fondo y clasificó B correctamente, pero **no había seguido el consumidor de `compact_context`** ni afirmado el
mecanismo per-turno por lectura del ensamblador — justo el modo de fallo que L09 caza. **NO se re-derivó la
enumeración de A** por hitos: se re-leyó 1→EOF esta ronda (L11), con citas exactas como evidencia. Suite de memoria
re-ejecutada esta ronda: **18 passed** (`test_memory_provider` + `test_memory_recall` + `test_memory_loop_e2e`).

**⚠ AUTO-CORRECCIÓN (gate auto-adversarial del usuario, 2026-07-20)**: mi 1er cierre declaró `prompts.ts` (154) y
`agentMemorySnapshot.ts` (197) **"NO re-leídos esta ronda"** apoyándome en el ledger de la 1ª pasada — y confirmé
FIND-MEM10 citando la **línea de grep** de `runtime.py:205`/`fork:69` sin abrir su contexto. Son **in-scope** (árbol
de memoria, no satélites de otra categoría), así que "apoyarse en la 1ª pasada" es **el mismo fallo L11 reprochado en
11 y 12**, y "cableado por grep" viola L09. Al reproche: **(1)** leí `prompts.ts` + `agentMemorySnapshot.ts` **1→EOF
esta ronda** → CERO discrepancias (extraction-prompt reutiliza la taxonomía; snapshot-sync keyed por agentType,
ausente en B — ambos refuerzan FIND-MEM1/MEM10, ningún finding nuevo); **(2)** leí el **contexto** de `_build_child`
(runtime.py:198-218) y `RuntimeContextForker.fork` (fork:61-93) → el uuid fresco por despacho está en la ruta real,
confirmado por LECTURA, no por la línea de grep. ⇒ **los 10 archivos A in-scope quedan leídos 1→EOF esta ronda**; el
cierre se GANA, no se asume. Regla re-interiorizada (idéntica 11/12): en validación, todo A in-scope se RE-ABRE 1→EOF
esta ronda y todo cableado se lee en su contexto — grep sólo orienta o prueba AUSENCIA.

### 4 preguntas de cierre
1. **¿Se revisó TODO cada archivo de A listado?** **Sí — los 10 in-scope RE-LEÍDOS 1→EOF esta ronda** (extractMemories
   615/memdir 507/memoryTypes 271/paths 278/memoryScan 94/findRelevantMemories 141/memoryAge 53/agentMemory 177
   **+ prompts.ts 154 + agentMemorySnapshot.ts 197**, estos dos tras el gate auto-adversarial — ver §honestidad),
   citas exactas. Team/session/UI (fuera-de-alcance-con-destino, re-audit 2026-07-14 los cubrió).
2. **¿Se revisó TODO cada archivo de B listado?** **Sí.** Los 5 `memory/*.py` 1→EOF **+ el ENSAMBLADOR** (`factory.py`
   267 + `manager.py` 112 + `agent_loop.py:85-234`) 1→EOF esta ronda.
3. **¿Los hallazgos fueron exhaustivos (no superficiales)?** **Sí.** Cada ✅/🔀 abierta en B por cableado; FIND-MEM1
   por absencia (grep de wiring = vacío) + A re-leído; FIND-MEM10 por cableado del uuid en runtime:205/fork:69; MEM9
   por seguir la clave cruda hasta `self._root / scope`. Una **precisión** (compact_context sin consumidor prod) que
   la 1ª pasada no había perseguido.
4. **¿Quedó TODO cubierto (nada pendiente)?** **Sí.** SessionMemory→01/compact y team→implementador con destino;
   cabos FIND-SKILL14 (no aterriza) e invoked/cleanup (sin estado por-agente) cerrados; `compact_context` refinado
   como cara del ❌ de compactación ya conocido (no nuevo). **CERO cambios de estado, código intacto.**

**VEREDICTO DE AVANCE: ✅ NADA PENDIENTE → avanzar a 14 · cap-plan** (01→13 completos con gate 11; ningún pendiente de
verificación de la 2ª vuelta). La homologación A↔B de 13 queda validada; código intacto (MODO VALIDACIÓN: sólo se
añadió este bloque + precisión de la fila D, sin tocar la sustancia del doc ni el runtime).
