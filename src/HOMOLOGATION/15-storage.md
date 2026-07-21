# 15 · storage

> **Estado (2ª vuelta · MODO VALIDACIÓN con gate 11/L09) — ✅ VALIDADA 2026-07-20.** B (`storage/*` +
> consumidores + ENSAMBLADOR `factory.py`) leída 1→EOF; A in-scope RE-LEÍDA 1→EOF esta ronda (no apoyada en
> la 1ª pasada — L11). **CERO cambios de estado** (✅3·🟡7·🔀9·❌15·⛔2 intactos), código intacto. 2
> precisiones de cableado (FIND-STOR1 / FIND-STOR12), sin B-orphans nuevos. Ver §"Re-visita de COMPLETITUD
> (gate 11/L09)" al pie.

Homologación de la capa de persistencia del runtime (`storage/{protocol,filesystem,factory}.py`
+ los consumidores que persisten sobre ella) contra la persistencia del canónico, que **no vive en un
módulo único** sino dispersa: `utils/config.ts` (config `~/.claude.json`), `utils/sessionStorage.ts`
(transcript JSONL + sidecars + listado), `utils/sessionStoragePortable.ts` (primitivos portables),
`utils/fsOperations.ts` (seam de FS + guards de path), `utils/env{,Utils}.ts` (config-home + config-file),
`utils/cachePaths.ts` (cache), `utils/filePersistence/` (outputs/work), `cli/transports/WorkerStateUploader.ts`
(estado remoto), `utils/sessionState.ts` (session-state), `bootstrap/state.ts` (identidad de sesión).

## Tesis

El runtime **deliberadamente NO reifica** el formato opinado del canónico (JSONL append-only con sidecars
de metadatos + cascada de config de 4 niveles + `~/.claude.json`). En su lugar ofrece un **blob store
k/v agnóstico** (`StorageProtocol`: `upload/download/presign/delete/exists/list_prefix`) + un **registry
pluggable** (`StorageRegistry` — habilita MinIO en `agentic_assistant`) + una **taxonomía de claves
canónicas** (`StorageKeys`). El "equivalente directo de la persistencia FS" (`filesystem.py`) es sólo el
backend de desarrollo/tests; la persistencia **de forma** la pone el integrador sobre el blob store.

**Esto es un 🔀 arquitectural correcto** (el canónico es single-user en terminal; el runtime es multi-user
sobre blob). Pero la homologación destapa que la **promesa de la capa está a medio cumplir**: de las 7
claves de `StorageKeys` **sólo `transcript_key` está cableada**; la config, el plano meta mutable, el
listado de sesiones y los guards de forma NO existen — y el propio implementador (`agentic_assistant`
sobre MinIO) los necesita. Además hay **DOS abstracciones de storage solapadas** (`StorageContract` de
01/09 vs `StorageProtocol` de 15) cuya frontera es implícita (cabo de 01, resuelto aquí).

Recuento: **✅3 · 🟡7 · 🔀9 · ❌15 · ⛔2** (tras re-auditoría 2026-07-14 — ver §honestidad).

---

## Tabla feature-by-feature

### A · Persistencia de CONFIG (`config.ts` 1817 · `env{,Utils}.ts`)

| # | Canónico | Runtime | Estado |
|---|---|---|---|
| A1 | `getClaudeConfigHomeDir` = `$CLAUDE_CONFIG_DIR ?? ~/.claude` (memo, NFC); `getTeamsDir`/`getUserClaudeRulesDir` cuelgan de ahí | Sin config-home; las claves son user-scoped (`<uid>/…`) — el "home" lo pone el backend (bucket MinIO / root FS) | 🔀 |
| A2 | `~/.claude.json` (`getGlobalClaudeFile`, con fallback legacy `.config.json`): **un** JSON con `GlobalConfig` (≈180 campos) + `projects[path]: ProjectConfig` anidado | `StorageKeys.config_key(uid)="<uid>/config.json"` **DECLARADA pero SIN consumidor** | ❌ |
| A3 | `getConfig`: read sync + merge-con-defaults + `stripBOM` + manejo de corrupción (`ConfigParseError` → backup del corrupto + restore-prompt en stderr + `tengu_config_parse_error`) | — | ❌ |
| A4 | `saveConfigWithLock`: `lockfile.lockSync` + detección de escritura-stale (mtime/size) + backups timestamped (keep-5, MIN_INTERVAL 60s) + **guard anti-pérdida-de-auth (#3117)** + escritura atómica `writeFileSyncAndFlush` mode 0600 + `pickBy` strip-defaults | `upload()` overwrite ingenuo: sin lock, sin backup, sin atomicidad declarada, sin strip, sin guard | ❌ |
| A5 | Caché en memoria + `fs.watchFile` freshness-watcher (relee escrituras de otros procesos) + write-through (mtime overshoot para saltarse el propio write) | `FilesystemStorage` es stateless per-op; sin caché ni watcher | ❌ |
| A6 | `ProjectConfig` keyed por git-root (`getProjectPathForConfig`→`findCanonicalGitRoot`) + cascada de trust (`checkHasTrustDialogAccepted` sube por padres) | Sin project-config ni trust | ❌ |
| A7 | Migraciones: `migrateConfigFields` (autoUpdaterStatus→installMethod), `removeProjectHistory`, `migrationVersion` gate | — | ❌ |
| A8 | Cascada de settings.json de 4+ niveles (`settings/settings.ts` 1015, ÍNTEGRO en re-audit): merge `plugin→user→project→local→flag→policy` (`mergeWith`/`settingsMergeCustomizer`); `policy` = sub-cascada first-source-wins (remote>MDM>`managed-settings.json`+`.d/*.json`>HKCU); write `updateSettingsForSource` (editables, `markInternalWrite`, atómico, auto-gitignore); zod+`filterInvalidPermissionRules`; caché parsed/per-source/session | `StorageKeys` lo declara PENDIENTE (nota B4); sólo nivel user. `ScopedMcpConfigStore` = análogo PARCIAL (sólo MCP) | 🔀→❌ (FIND-STOR13) |

### B · Persistencia de SESIÓN / transcript (`sessionStorage.ts` 5105 · `sessionStoragePortable.ts` 793)

| # | Canónico | Runtime | Estado |
|---|---|---|---|
| B1 | JSONL **append-only**, writer bufferizado (`Project`: `writeQueues` per-file, `drainWriteQueue`, `flush`, `MAX_CHUNK_BYTES`, `FLUSH_INTERVAL_MS`) | `_persist` (runtime.py:430) hace `upload(transcript_key, session.model_dump_json())` = **snapshot-overwrite del JSON entero por completion** | 🔀→❌ (ver FIND-STOR2) |
| B2 | Layout `<projectsDir>/<sanitized-cwd>/<sid>.jsonl`; subagentes `…/<sid>/subagents/agent-<id>.jsonl` | `StorageKeys.transcript_key` = `<uid>/<sid>/session.json`; subagente `<uid>/<sid>/subagents/<agent_id>/session.json` — **user-scoped + subtree anidado = MEJORA** para multi-user, pero blob único vs jsonl | 🔀 |
| B3 | Materialización lazy (buffer hasta primer user/assistant; `shouldSkipPersistence` gate test/`--no-session-persistence`/`cleanupPeriodDays=0`) | Persiste sólo al completar la task; sin gate de persistencia | 🟡 |
| B4 | **Sidecars de metadata DENTRO del jsonl**: `custom-title`/`ai-title`/`tag`/`agent-{name,color,setting}`/`mode`/`worktree-state`/`pr-link`/`last-prompt`/`summary`/`task-summary`; `reAppendSessionMetadata` los re-emite al tail (ventana 64KB) absorbiendo escrituras externas del SDK | `StorageKeys.meta_key`="<…>/session.meta.json" **DECLARADA pero SIN consumidor**; sin modelo de metadata | ❌ (FIND-STOR3) |
| B5 | Persistencia remota: `sessionIngress` (v1) + CCR v2 internal-event writer/reader + `hydrateRemoteSession`/`hydrateFromCCRv2InternalEvents` | El propio `StorageProtocol` ES lo remoto (MinIO); un solo `upload`. Sin ingress/hydrate/epoch | 🔀 |
| B6 | Load: `loadTranscriptFile` (chunked compact-boundary read, skip-precompact >5MB, `walkChainBeforeParse` excisión de ramas muertas, progress-bridge legacy, `applyPreservedSegmentRelinks`, `applySnipRemovals`, cómputo de leaves) | `download` del blob + parse del modelo | 🔀 (el runtime persiste el modelo ya reconstruido, no el log crudo → gran parte es N/A por diseño) |
| B7 | `buildConversationChain` + `recoverOrphanedParallelToolResults` (DAG tool_use↔tool_result) + `checkResumeConsistency` | Ninguno (la `Session` ya es la cadena) | 🔀 |
| B8 | Listado/enriquecimiento: `getSessionFilesLite` (stat-only) + `readLiteMetadata` (head/tail 64KB, sin full-parse) + `enrichLogs` (progresivo) + `loadMessageLogs`/`loadSameRepo`/`loadAllProjects` + `searchSessionsByCustomTitle` | Sólo `list_prefix` (keys); sin lite/enrich/metadata-scan/progresivo/búsqueda | ❌ (FIND-STOR5) |
| B9 | Tombstone `removeMessageByUuid` (tail positional splice + slow-path rewrite ≤50MB) | Ninguno (el overwrite del blob lo hace N/A) | 🔀 |
| B10 | Sidecar de agente: `writeAgentMetadata` (`agentType`/`worktreePath`/`description`) + `RemoteAgentMetadata` (per-task, sobrevive wipe) | Sin clave de agent-meta en `StorageKeys` | ❌ (liga 05·GAP-EXEC3 resume) |
| B11 | Entradas `file-history-snapshot`/`attribution-snapshot`/`content-replacement`/`marble-origami-{commit,snapshot}` (context-collapse) persistidas y reconstruidas | Ninguna | ❌ (liga 02 compactación / 03) |
| B12 | Perms: dirs 0o700, files 0o600 (secreto por defecto) | `FilesystemStorage._write` usa perms de umask | 🟡 (FIND-STOR8) |
| B13 | `sanitizePath` (no-alfanum→`-`, cap 200 + hash) + `resolveSessionFilePath` (canonicaliza + worktree fallback + hash Bun/Node) | Guard `_path` prefix-startswith (ver C2/FIND-STOR7) | 🟡 |

### C · Seam de FS + guards de path (`fsOperations.ts` 770)

| # | Canónico | Runtime | Estado |
|---|---|---|---|
| C1 | `FsOperations` (Protocol ~50 métodos sync+async) + `getFsImplementation`/`setFsImplementation`/`setOriginalFsImplementation` (mock/virtual injectable) | **DOS** seams: `StorageContract` (contracts, 01/09: `real_path`/`ensure_local`/`commit`/`teardown` — I/O de tools, usado por `fs_env`/`plan_file`) y `StorageProtocol` (15: blob k/v — transcript/token/skills/mcp-config) | 🔀 (FIND-STOR6, cabo 01) |
| C2 | `getPathsForPermissionCheck`/`safeResolvePath`/`resolveDeepestExistingAncestorSync` (cadena de symlinks, UNC-block, FIFO/socket/device-block) | `fs_env.ConfinedFilesystem` (09) homologa el confinamiento con separador; `FilesystemStorage._path` es un guard **separado y más débil** | 🔀→09 |
| C3 | `readFileRange`/`tailFile`/`readLinesReverse` (ventanas de archivos GB sin cargar todo) | `download` trae el blob entero; sin range/tail/reverse | ❌ (FIND-STOR9) |

### D · Cache / logs / work (`cachePaths.ts` 38 · `filePersistence/` 287)

| # | Canónico | Runtime | Estado |
|---|---|---|---|
| D1 | `CACHE_PATHS` = `envPaths('claude-cli').cache/<proj>/{errors,messages,mcp-logs-<srv>}` (djb2Hash estable) | `StorageKeys.log_key`="<…>/agent.log" **DECLARADA pero SIN consumidor** | ❌ |
| D2 | Persistencia de outputs (`runFilePersistence`: BYOC scan-modified + `uploadSessionFiles` Files-API + `FILE_COUNT_LIMIT` + skip-fuera-de-dir; 1P xattr TODO) | `StorageKeys.work_key`="<…>/work/<file>" DECLARADA sin consumidor; `FilesystemStorage.copy` existe (no re-upload) pero sin el orquestador scan+upload | 🔀 (plano declarado + `copy` primitivo; motor ausente — FIND-STOR10) |
| D3 | `history.jsonl` (historial de prompts del proyecto, migrado fuera de config vía `removeProjectHistory`) | Ninguno | ❌ |

### E · Config-file-path / estado remoto / session-state (`env.ts` · `WorkerStateUploader.ts` 131 · `sessionState.ts` 150)

| # | Canónico | Runtime | Estado |
|---|---|---|---|
| E1 | `getGlobalClaudeFile` (memo, fallback legacy `.config.json`) | Cubierto por A2 (config_key muerta) | ❌ |
| E2 | `WorkerStateUploader`: PUT /worker coalescente (1 in-flight + 1 pending, merge RFC 7396 de `external_metadata`/`internal_metadata`, backoff exp indefinido) | Ninguno; **es el patrón de upsert del sidecar meta** que el plano B4 necesitaría | 🔀→18/integrador (FIND-STOR11) |
| E3 | `sessionState` (`idle`/`running`/`requires_action` + `external_metadata` {permission_mode,model,pending_action} + listeners) | Satélite de **07** (`session_state_changed` = FIND-EVT7) + external_metadata (persistencia CCR) | ⛔-para-15 →07 |

### F · Registry / primitivas de blob (`factory.py` · `StorageRegistry` · `StorageKeys` · `FilesystemStorage`)

| # | Canónico | Runtime | Estado |
|---|---|---|---|
| F1 | — (el canónico no tiene registry de backends; FS directo) | `StorageRegistry.register("minio", …)`/`create(backend, **cfg)` (instancia fresca, no singleton); factory lo instancia con `config.storage.{backend,root,extra_kwargs}` y lo comparte a todos los stores | ✅ (valor propio: pluggable para MinIO) |
| F2 | — | `StorageKeys` (config/agent_md/ltm/transcript/meta/work/log) — taxonomía determinista | ❌ (FIND-STOR1: sólo `transcript_key` cableada; el resto muerto; los otros stores inventan sus claves) |
| F3 | — (FS local: read/write/append/copy directos) | `upload/download/presign/delete/exists/list_prefix` + `copy`; `presign` FS = `file://` URI (para MinIO = URL firmada) | ✅ (valor propio: `presign` para servir blobs por URL) |

⛔ (abiertos y confirmados fuera de forma-de-storage): `sessionState.ts`→07 (E3); cost/usage/model/duration
de `bootstrap/state.ts`→07/16 (leída la región de identidad de sesión, el resto es acumulación de coste/uso).

---

## Hallazgos

- **FIND-STOR1 (❌ CRÍTICO — taxonomía muerta)**: de las 7 claves de `StorageKeys` sólo `transcript_key`
  tiene consumidor (runtime.py:428). `config_key`/`agent_md_key`/`ltm_key`/`meta_key`/`work_key`/`log_key`
  son slots sin lector ni escritor. Peor: los stores que SÍ persisten **ignoran la taxonomía** e inventan
  su propio esquema — MCP `mcp/servers.json` (config_store.py:36), tokens `{uid}/mcp/<srv>/oauth_tokens.json`
  con `uid` default `"mcp"` (token_storage.py:25), skills `skills/<name>/SKILL.md` **sin scope de usuario**
  (store.py), plan `/plans/plan.md` vía **otro seam** (`StorageContract`, plan_file.py). La promesa
  "claves canónicas deterministas, sin dependencia de implementación" no se cumple, y el scope es
  inconsistente (transcript user-scoped; skills sin scope; tokens user="mcp").

- **FIND-STOR2 (🔀→❌ — snapshot vs append)**: el transcript se persiste como overwrite del `Session`
  entero serializado, por completion de task (runtime.py:430). Diverge del writer append-only bufferizado
  del canónico. Consecuencias reales: (a) **sin durabilidad incremental/mid-turn** — un crash antes de
  completar pierde el turno en curso (el canónico lo tiene en disco línea a línea); (b) sin tombstone/splice;
  (c) coste O(tamaño-sesión) por completion; (d) sin persistencia de subagente hasta que termina.
  Parcialmente deliberado (persiste el modelo reconstruido, no el log crudo → B6/B7/B9 son N/A por diseño),
  pero la pérdida de durabilidad incremental es un gap real para un daemon multi-sesión.

- **FIND-STOR3 (❌ — plano meta mutable ausente)**: el docstring de `StorageKeys` promete `session.meta.json`
  (`meta_key`) como sidecar mutable donde vive `is_backgrounded` "y demás meta de observación", pero
  **nunca se escribe**. El modelo de sidecar del canónico (title/tag/mode/worktree/pr-link/agent-name/color/
  last-prompt + backgrounded) no está portado. Liga 04/05 (backgrounding sin persistir), B10 (agent-meta →
  05·GAP-EXEC3 resume) y E2 (el `WorkerStateUploader` es el transporte de upsert que faltaría).

- **FIND-STOR4 (❌ — sin persistencia de config)**: no hay lector/escritor de `config_key`/`agent_md_key`/
  `ltm_key`. El canónico tiene toda la maquinaria (`getConfig`/`saveConfigWithLock`: lock, backups keep-5,
  guard anti-pérdida-de-auth #3117, atomicidad 0600, strip-defaults, freshness-watcher, migraciones).
  `agentic_assistant` sobre MinIO necesita settings de usuario persistidos → sin esto no hay dónde.

- **FIND-STOR5 (❌ — sin listado/enriquecimiento de sesiones)**: `list_prefix` devuelve keys crudas. El
  canónico tiene stat-only lite + scan head/tail 64KB de metadata sin full-parse + `enrichLogs` progresivo +
  búsqueda por título. El BFF de `agentic_assistant` que lista las sesiones de un usuario (con título/última-
  actividad/primer-prompt) no tiene primitiva.

- **FIND-STOR6 (🔀→01 RESUELVE el solapamiento)**: coexisten `StorageContract` (contracts/storage.py —
  `real_path`/`ensure_local`/`commit`/`teardown`, orientado a **path de archivo para tools**, usado por
  `fs_env`/09 y `plan_file`/14) y `StorageProtocol` (15 — **blob por clave**, usado por transcript/token/
  skills/mcp-config). **NO deben fusionarse a ciegas**: son dos roles distintos (archivo-local-para-tools con
  ciclo ensure/commit vs blob-k/v). Pero comparten backend físico (MinIO) y hoy la frontera es **implícita**:
  `fs_env` recibe un `StorageContract`, el runtime recibe un `StorageProtocol`, y nada documenta que uno se
  derive del otro o cómo un mismo MinIO sirve ambos. Ajuste: documentar la frontera + que el integrador
  construya ambos sobre el mismo bucket (un `StorageContract` que `commit`ee vía `StorageProtocol.upload`).

- **FIND-STOR7 (🟡 seguridad — guard de path débil)**: `FilesystemStorage._path` valida con
  `str(p).startswith(str(root))`. Es vulnerable a **hermano-prefijo**: con `root=/data/root`, la clave que
  resuelve a `/data/root-evil/x` pasa el guard. El canónico normaliza + resuelve la cadena de symlinks
  (`getPathsForPermissionCheck`) y `teamMemPaths.sanitizePathKey` rechaza null-byte/URL-enc/NFKC/backslash/
  absolutos (= MEM9). Ajuste: `Path.is_relative_to(root)` o comparar contra `str(root)+os.sep`, y sanitizar
  la clave (rechazar `\0`, `..`, absolutos, backslashes) antes de resolver. Mismo modo de fallo que 13·MEM9.

- **FIND-STOR8 (🟡 perms)**: `_write` no fija modo → los archivos del backend FS heredan umask; el canónico
  escribe dirs 0o700 / files 0o600. N/A para MinIO (ACL del bucket), pero el backend FS de dev filtra
  transcripts/tokens con perms laxas.

- **FIND-STOR9 (❌ — sin range/tail/reverse read)**: `readFileRange`/`tailFile`/`readLinesReverse` no tienen
  equivalente; `download` es todo-o-nada. Relevante para transcripts grandes e `history.jsonl` (lecturas de
  ventana sobre archivos GB).

- **FIND-STOR10 (🔀 — plano work/ sin motor)**: `work_key` declarado + `FilesystemStorage.copy` (copia sin
  re-upload) existen, pero falta el orquestador de outputs del canónico (`runFilePersistence` + `outputsScanner.ts`
  126, ÍNTEGRO en re-audit): `findModifiedFiles` = readdir recursivo + `lstat` paralelo con **skip-symlink +
  guard TOCTOU** (descarta si el entry se volvió symlink entre readdir y stat — seguridad), filtro por mtime ≥
  turn-start, `FILE_COUNT_LIMIT`, skip-fuera-de-dir. El motor del runtime debe replicar el skip-symlink y el
  guard de carrera, no sólo el scan. El plano de artefactos está esbozado, el motor no.

- **FIND-STOR13 (❌ — cascada de settings.json no portada · destapada en re-audit)**: `settings/settings.ts`
  (1015, ÍNTEGRO) es un subsistema de persistencia completo que la 1ª pasada difirió como "B4 sin abrir"
  (violación lección 02). Contiene: (a) la **cascada de 4+ niveles** `plugin(base)→user→project→local→flag→policy`
  (`getEnabledSettingSources` + `mergeWith`/`settingsMergeCustomizer`: arrays concat+dedup, `undefined`=borrado);
  (b) `policySettings` = **sub-cascada first-source-wins** (remote > MDM HKLM/plist > `managed-settings.json` +
  `managed-settings.d/*.json` estilo systemd drop-in > HKCU); (c) rutas por fuente (user `~/.claude/settings.json`
  o `cowork_settings.json`; project `.claude/settings.json`; local `.claude/settings.local.json`+auto-gitignore;
  policy `managed-settings.json`; flag `--settings`); (d) write `updateSettingsForSource` (sólo editables,
  `markInternalWrite` para que el change-detector distinga escritura propia de externa, atómico, `resetSettingsCache`);
  (e) validación zod + `filterInvalidPermissionRules` (una regla mala no tumba el archivo); (f) caché
  parsed-file/per-source/session. El runtime **no tiene cascada de settings** (`ScopedMcpConfigStore` es análogo
  PARCIAL, sólo MCP). **Invariante de seguridad transversal**: `projectSettings` se EXCLUYE de lecturas sensibles
  a confianza (`hasSkipDangerousModePermissionPrompt`/`hasAutoModeOptIn`/`getAutoModeConfig`) — "un proyecto
  malicioso podría auto-bypassear el diálogo / inyectar reglas del clasificador (RCE)"; **mismo patrón que
  `memdir/paths.getAutoMemPathSetting` (13, project excluido)** → invariante: **settings de scope-proyecto
  no-confiable NO conceden privilegio**. La semántica de permisos (allow/deny/ask/defaultMode) es GAP-02/06; la
  PERSISTENCIA/cascada/write/paths es 15. Generaliza StR4 (`ScopedConfigStore` para config, no sólo MCP).

- **FIND-STOR11 (🔀→18/integrador)**: `WorkerStateUploader` (coalescing PUT + RFC7396 merge + backoff) es el
  patrón de upsert del estado/meta remoto que el plano meta (FIND-STOR3) necesitaría sobre MinIO; su hogar es
  el transporte del integrador (18), no el core, pero se referencia como diseño-fuente.

- **FIND-STOR12 (🟡 — identidad de sesión con fallbacks silenciosos)**: `_persist` deriva la clave de
  `ctx.user_id or "anon"` + `ctx.session_id` + `(agent_id if is_subagent else "main") or "main"`. Coherente
  con el modelo atómico del canónico (CC-34: `sessionId`+`sessionProjectDir` nunca driftean), **pero** el
  fallback `"anon"` colisiona todas las sesiones sin `user_id` bajo el mismo subtree, y no hay validación de
  que `user_id`/`session_id` sean seguros como componentes de clave (liga FIND-STOR7).

**Cabos que aterrizan (cerrados aquí):**
- **01 · solapamiento `StorageContract` vs `StorageProtocol`** → **FIND-STOR6 RESUELTO**: dos roles, no
  fusionar; frontera a documentar + derivar sobre un mismo bucket. 01·feat-10 (`🔀 seam inventado`) confirmado.
- **14 · FIND-PLAN4** (`is_session_plan_file` sobre el StorageContract) → **confirmado**: `plan_file.py` usa
  `StorageContract` (`/plans/*.md`), NO `StorageProtocol`; el candado de plan mode exime `/plans/*.md`. Coherente.
- **14 · C4** (`settings.plansDirectory` override) → **confirmado NO portado**: `plan_file._PLAN_TOKEN_PREFIX`
  es `/plans` fijo; el override no existe (StR8 / cabo→14).
- **13 · MEM9** (clave-scope sin sanitizar = traversal) → **mismo modo de fallo que FIND-STOR7** en
  `FilesystemStorage._path`; `teamMemPaths.sanitizePathKey` es el modelo canónico robusto.
- **09 · fs_env** (`ConfinedFilesystem`/path-traversal) → es el `StorageContract` (C1/C2); separado del blob
  store; FIND-STOR6 documenta la relación.

---

## Plan de homologación / remediación desarrollada

> Regla 05: cada finding se DESARROLLA (comportamiento · seam · firma · cableado · orden · test). Sin código
> de runtime en esta 1ª pasada; los `xfail(strict)` de `test_storage_homologation.py` codifican los targets.

- **StR1 — cablear la taxonomía completa (FIND-STOR1)**.
  - *Comportamiento*: todo store que persista sobre `StorageProtocol` deriva su clave de `StorageKeys`, no
    de literales. Scope uniforme user-scoped (`<uid>/…`).
  - *Seam*: `StorageKeys` gana `mcp_config_key(uid)`, `skill_key(uid,name)`, `oauth_key(uid,srv)`; los stores
    (`StorageBackedMcpConfigStore`, `StorageBackedSkillStore`, `StorageBackedTokenStorage`) reciben `user_id`
    y llaman a `StorageKeys` en vez de a su literal.
  - *Firma*: `StorageKeys.mcp_config_key(user_id: str) -> str` (= `<uid>/mcp/servers.json`), etc.
  - *Cableado*: `factory._build_capability_manager` pasa `user_id` a cada store al construirlo.
  - *Orden*: primero `StorageKeys` (aditivo), luego migrar cada store (independientes).
  - *Test*: `test_storage_keys_taxonomy_complete` (xfail: los nuevos métodos no existen).

- **StR2 — persistencia incremental del transcript (FIND-STOR2)**.
  - *Comportamiento*: además del snapshot final, escritura durable mid-turn (al menos por-ronda) para que un
    crash no pierda el turno en curso; opción append para backends que lo soporten.
  - *Seam*: `StorageProtocol` gana `append(key, data)` opcional (default = download+concat+upload para
    backends sin append; MinIO multipart / FS `ab`); `_persist` gana una variante `_persist_incremental`
    llamada en el límite de ronda del loop (agent_loop) además del `_persist` final.
  - *Firma*: `async def append(self, key: str, data: bytes) -> None`.
  - *Cableado*: el loop invoca `runtime.persist_incremental(session)` tras cada ronda modelo↔tools.
  - *Orden*: tras StR1; independiente de StR3.
  - *Test*: `test_transcript_persisted_incrementally` (xfail).

- **StR3 — plano meta mutable (FIND-STOR3 + B10)**.
  - *Comportamiento*: sidecar `session.meta.json` con `{title, tag, mode, worktree, pr, is_backgrounded,
    agent_type, description, updated_at}`; upsert independiente del transcript (no reescribe el blob grande).
  - *Seam*: `SessionMeta` (pydantic) + `MetaStore` sobre `StorageProtocol` usando `StorageKeys.meta_key`;
    upsert con merge RFC-7396 (patrón `WorkerStateUploader`, FIND-STOR11).
  - *Firma*: `MetaStore.patch(user_id, session_id, patch: dict, agent_id="main")`.
  - *Cableado*: `LocalAgentRuntime._notify`/backgrounding escriben `is_backgrounded`; resume (05) lee agent-meta.
  - *Orden*: tras StR1; habilita 05·GAP-EXEC3 resume.
  - *Test*: `test_session_meta_sidecar_roundtrip` (xfail).

- **StR4 — persistencia de config (FIND-STOR4)**.
  - *Comportamiento*: `ConfigStore` sobre `StorageProtocol` (`config_key`) con read-merge-defaults + write
    atómico + (para FS) lock/backup; el integrador pone la política de cascada.
  - *Seam*: `StorageBackedConfigStore.load()/save(patch)`; `agent_md_key`/`ltm_key` análogos (texto/JSON).
  - *Firma*: `load() -> dict`, `save(patch: dict) -> None` (merge, no overwrite).
  - *Cableado*: `factory` lo expone en el runtime; `agentic_assistant` lo respalda en MinIO.
  - *Orden*: independiente; la cascada de 4+ niveles (A8/FIND-STOR13) se porta **generalizando
    `ScopedMcpConfigStore` a `ScopedConfigStore`** (productor por scope managed/user/project/local/flag +
    merge por precedencia + gate de mutabilidad + `settingsMergeCustomizer` arrays-concat-dedup), con el
    **invariante de seguridad**: el scope `project` NO concede privilegio (excluido de lecturas trust-sensibles),
    espejo de `hasSkipDangerousModePermissionPrompt`/13·`getAutoMemPathSetting`. La semántica de permisos → GAP-02/06.
  - *Test*: `test_config_store_load_save_merge` + `test_scoped_config_store_project_untrusted` (xfail).

- **StR5 — listado/enriquecimiento de sesiones (FIND-STOR5)**.
  - *Comportamiento*: `list_sessions(user_id)` → `[SessionInfo{sid, title, updated_at, first_prompt}]` leyendo
    sólo el sidecar meta (StR3), sin descargar transcripts; paginado.
  - *Seam*: método en un `SessionCatalog` que combina `list_prefix(<uid>/)` + `download(meta_key)` por sid.
  - *Firma*: `async def list_sessions(user_id, *, limit=None) -> list[SessionInfo]`.
  - *Cableado*: lo consume el BFF de `agentic_assistant`.
  - *Orden*: tras StR3 (necesita el meta sidecar).
  - *Test*: `test_list_sessions_from_meta` (xfail).

- **StR6 — frontera StorageContract↔StorageProtocol (FIND-STOR6, cabo 01)**.
  - *Comportamiento*: documentar los dos roles; ofrecer un adaptador `StorageContract` que `commit`ee vía
    `StorageProtocol.upload` para que un mismo MinIO sirva tools (fs_env) y blobs.
  - *Seam*: `BlobBackedStorageContract(storage: StorageProtocol, workdir)` en `tools/` (materializa a local en
    `ensure_local`, sube en `commit`, limpia en `teardown`).
  - *Firma*: implementa `real_path/ensure_local/commit/teardown` sobre `StorageProtocol`.
  - *Cableado*: `factory` construye ambos sobre el mismo backend; docstring de contracts/storage.py + protocol.py
    referencian mutuamente.
  - *Orden*: independiente; cierra el cabo 01 sin fusionar los protocolos.
  - *Test*: `test_storage_contract_over_protocol` (xfail).

- **StR7 — guard de path robusto + perms (FIND-STOR7/STOR8/STOR12)**.
  - *Comportamiento*: `_path` usa `resolved.is_relative_to(root)` (no `startswith`); `_key_is_safe` rechaza
    `\0`/`..`/absolutos/backslashes/URL-enc/NFKC (espejo `sanitizePathKey`); `_write` fija dir 0o700/file 0o600;
    `_persist` valida `user_id`/`session_id` como componentes seguros (no `"anon"` colisionable → error o uuid).
  - *Seam*: helpers en `filesystem.py` + validación en `StorageKeys._agent_base`.
  - *Firma*: `_key_is_safe(key: str) -> bool`.
  - *Orden*: independiente; alta prioridad (seguridad). Unifica con 13·MEM9 (mismo helper).
  - *Test*: `test_path_traversal_sibling_prefix_rejected`, `test_key_sanitization_rejects_dotdot` (xfail).

- **StR8 — range/tail read + work-engine + history (FIND-STOR9/STOR10 + D3 + 14·C4)**.
  - *Comportamiento*: `download_range(key, offset, length)` + `tail(key, n_bytes)`; orquestador `persist_outputs`
    (scan-modified + upload con límite); `history` como blob append; `plans_dir` override configurable.
  - *Seam*: `StorageProtocol.download_range` (default: download+slice; MinIO Range header); un `OutputsPersister`
    en `tools/` que reusa `copy`; `_PLAN_TOKEN_PREFIX` → configurable vía `StorageConfig`.
  - *Orden*: tras StR1; `download_range` prerreq de StR5 lite-scan eficiente.
  - *Test*: `test_download_range`, `test_persist_outputs_scan` (xfail).

**Deuda transversal referenciada** (no nueva; ya con hogar): B-signals/B-02 no aplican a 15; el upsert
coalescente (FIND-STOR11) y la cascada de 4 niveles (A8) son del **integrador/18**, no del core.

---

## Puerta de cierre 6b — ledger + honestidad

### Ledger de archivos (columna "Lectura")

**Canónico (in-scope, forma-de-storage):**

| Archivo | LOC | Lectura |
|---|---|---|
| `utils/sessionStorage.ts` | 5105 | **íntegro** 1→5105 (4 tramos: 1-540·540-1400·1400-2349·2349-3348·3348-4247·4247-5105) |
| `utils/config.ts` | 1817 | **íntegro** 1→1817 (2 tramos: 1-910·910-1817) |
| `utils/sessionStoragePortable.ts` | 793 | **íntegro** 1→793 |
| `utils/fsOperations.ts` | 770 | **íntegro** 1→770 |
| `utils/settings/settings.ts` | 1015 | **íntegro** 1→1015 (re-audit 2026-07-14 — la 1ª pasada la difirió `B4 sin abrir`; ver §honestidad) |
| `utils/filePersistence/filePersistence.ts` | 287 | **íntegro** 1→287 |
| `utils/filePersistence/outputsScanner.ts` | 126 | **íntegro** 1→126 (re-audit — motor de STOR10; skip-symlink+TOCTOU) |
| `utils/lockfile.ts` | 43 | **íntegro → ⛔** (re-audit — wrapper lazy de `proper-lockfile`; lib vendorizada, no core) |
| `utils/envUtils.ts` | 183 | **íntegro** 1→183 |
| `utils/sessionState.ts` | 150 | **íntegro** 1→150 → satélite ⛔ (07·session_state) |
| `cli/transports/WorkerStateUploader.ts` | 131 | **íntegro** 1→131 |
| `utils/cachePaths.ts` | 38 | **íntegro** 1→38 |
| `utils/env.ts` | 341 | **tramos 1-40** (`getGlobalClaudeFile`, única superficie storage); resto = find-executable/plataforma, satélite fuera de forma-de-storage |
| `bootstrap/state.ts` | 1758 | **tramos 420-540 + 1319-1331** (identidad de sesión: `getSessionId`/`switchSession`/`getSessionProjectDir`/`getOriginalCwd`/`isSessionPersistenceDisabled`/`getSessionTrustAccepted`) — el resto (cost/usage/duration/model, ~1600 LOC) es **07·events / 16·models**, subsistemas numerados concretos |

**Canónico (satélites de OTRO subsistema numerado, abiertos y confirmados — lección 02):**

| Archivo | LOC | Lectura → destino |
|---|---|---|
| `memdir/paths.ts` | 278 | **íntegro** 1→278 → **13·memory** (layout `<base>/projects/<git-root>/memory/`, `CLAUDE_CODE_REMOTE_MEMORY_DIR`, `validateMemoryPath`=MEM9) |
| `memdir/teamMemPaths.ts` | 292 | tramos 1-70 (`sanitizePathKey` = modelo del guard StR7) → **13·memory** (MEM9, abierto en 13) |
| `utils/plans.ts` | 397 | ya íntegro en **14** (`getPlansDirectory`/`getPlanSlug`) → confirmado cabo 14·C4/PLAN4 |

**Runtime (in-scope):**

| Archivo | LOC | Lectura |
|---|---|---|
| `storage/protocol.py` | 87 | **íntegro** (StorageProtocol + StorageKeys) |
| `storage/filesystem.py` | 70 | **íntegro** (FilesystemStorage + `copy` + guard `_path`) |
| `storage/factory.py` | 33 | **íntegro** (StorageRegistry) |
| `storage/__init__.py` | 5 | **íntegro** |
| `contracts/storage.py` | 40 | **íntegro** (StorageContract + PathPresentation) |
| `capabilities/mcp/token_storage.py` | 65 | **íntegro** (StorageBackedTokenStorage) |
| `capabilities/mcp/config_store.py` | 146 | **íntegro** (McpConfigStore + StorageBacked + ScopedMcpConfigStore + Watcher) |
| `capabilities/skills/store.py` | — | tramos (StorageBackedSkillStore `skills/<name>/SKILL.md`) |
| `capabilities/plan/plan_file.py` | — | tramos (token `/plans/*` vía StorageContract) — cruce con 14 |
| `execution/local/runtime.py` | — | tramos 415-435 (`_persist` = único consumidor de `transcript_key`) |
| `factory.py` | — | tramos 160-199 (wiring `StorageRegistry.create` + stores) |
| `tests/test_runtime_storage.py` | 143 | **íntegro** (roundtrip/registry/keys/traversal existentes) |

### §Honestidad (re-auditoría 2026-07-14, disparada por el usuario)

La **1ª pasada de 15 incurrió en el modo de fallo original de 11** (lección 02: marcar sin abrir) sobre los
satélites, aun habiendo leído los archivos grandes íntegros:
- `settings/settings.ts` (1015) — la cascada de config de 4+ niveles se difirió como "🔀/B4 sin mapear" **sin
  abrirla**. Al abrirla (re-audit) apareció un subsistema de persistencia completo → **FIND-STOR13** (nuevo ❌;
  recuento ❌14→15) + invariante de seguridad `projectSettings`-excluido (transversal con 13).
- `filePersistence/outputsScanner.ts` (126) — describí el motor de STOR10 **citando sus funciones sin leerlo**
  (troceo estilo 10). Al leerlo: skip-symlink + guard TOCTOU → enriquece FIND-STOR10.
- `lockfile.ts` (43) — descrito en A4/StR4 sin leer; al abrirlo se confirma ⛔ legítimo (wrapper `proper-lockfile`),
  legitimidad que **sólo es válida tras abrir** (lección 02).

Lección re-confirmada: leer los monstruos 1→EOF es necesario pero **no suficiente** — la superficialidad se movió
a los satélites pequeños marcados por título. La corrección se hizo **antes** de cerrar (lección 00: el ahorro era
ilusorio), no tras un reproche que forzara re-trabajo.

### 4 preguntas de cierre

1. **¿Se revisó todo cada archivo canónico listado?** — **Sí.** Los in-scope de forma-de-storage se leyeron
   íntegros (los tres grandes `sessionStorage.ts` 5105 / `config.ts` 1817 / `sessionStoragePortable.ts` 793 /
   `fsOperations.ts` 770 completos, cerrando huecos — lección 08). Los tramos declarados (`env.ts` 1-40,
   `bootstrap/state.ts` identidad-de-sesión) están justificados: el resto de esos archivos pertenece a
   subsistemas numerados concretos (07/16), no es troceo de un in-scope (lección 07). Satélites de 13/14
   abiertos y confirmados.
2. **¿Se revisó todo cada archivo runtime listado?** — **Sí.** La capa `storage/` completa + los consumidores
   sobre `StorageProtocol` (token/mcp-config/skills/plan/`_persist`) + el wiring de factory.
3. **¿Los hallazgos fueron exhaustivos (no superficiales)?** — **Sí, tras la re-auditoría 2026-07-14** (en la
   1ª pasada NO — ver §honestidad). El hallazgo raíz (FIND-STOR1: 6 de 7 claves muertas) salió al rastrear
   quién consume cada clave; FIND-STOR6 cerró el cabo de 01. Pero la 1ª pasada difirió `settings.ts`/`outputsScanner.ts`
   sin abrirlos; la re-audit los leyó íntegros → FIND-STOR13 + enriquecimiento de STOR10 + confirmación ⛔ de lockfile.
4. **¿Quedó todo cubierto (nada pendiente)?** — **Sí.** 12 findings con §Plan desarrollado (StR1-8); cabos de
   01/13/14/09 cerrados con destino; lo delegado (cascada 4-niveles A8, upsert coalescente) anotado →18/integrador,
   no como pendiente. E3/cost-usage anotados →07/16.

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09) — 2026-07-20

> **Objeto validado = la homologación A↔B, NO el documento (L11).** La 1ª pasada + re-audit 2026-07-14 leyeron
> A+B íntegros pero **no siguieron el cableado en el ENSAMBLADOR** para las filas ✅/🔀 (fue confirmación-de-doc
> en esas filas). El value-add del gate 11 fue **abrir `factory.py` 1→EOF** y seguir el dato desde `StorageRegistry.create`
> hasta cada consumidor real de B. **A in-scope RE-LEÍDO 1→EOF ESTA ronda** (reproche recurrente 11/12/13/14 — nunca
> apoyarse en la 1ª pasada; las anclas driftan): confirmado con `env.ts` **347** vs 341 del ledger previo (drift +6
> en la parte no-storage; la superficie storage `getGlobalClaudeFile:14-26` intacta).

### Cableado confirmado abriendo el ENSAMBLADOR (`factory._build_local` 1→EOF, L09)

`factory.py:186` crea **UNA** instancia `storage = StorageRegistry.create(backend, **kwargs)` y la reparte:
- **→ `LocalAgentRuntime(storage=storage)`** (factory:226 → runtime.py:88 `self._storage`) → **único productor** = `_persist`
  (runtime.py:418-432): `upload(StorageKeys.transcript_key(user_id, session_id, agent_id), session.model_dump_json())`.
  **transcript_key = la ÚNICA clave de `StorageKeys` cableada** (F2/FIND-STOR1 CONFIRMADO por cableado).
- **→ `_build_capability_manager(storage=storage)`** (factory:194 → :152 `McpProvider(storage=storage)`) → MCP TokenStorage.
- **`fs=config.fs`** (factory:229 → runtime.py:325 `ctx.fs`) = **StorageContract SEPARADO**; default `ConfinedFilesystem`
  (tool_use.py:52). **NO se deriva de `storage`** en el standalone → **FIND-STOR6 (dos seams) CONFIRMADO por el ensamblador**:
  `fs`/`ctx.fs` (StorageContract, tools/plan) y `storage` (StorageProtocol, blob) coexisten sin puente.

### 2 PRECISIONES de cableado (no voltean estado — refinan la justificación)

- **FIND-STOR1 (❌ · precisión de cableado, sigue ❌ CRÍTICO)** — al abrir el ensamblador, los 3 stores "que inventan
  clave" NO son homogéneos:
  1. **`StorageBackedTokenStorage` SÍ lo auto-cablea el factory** al MISMO `storage`, pero `McpProvider` recibe
     `user_id="mcp"` por **default** (provider.py:50/67; el factory **nunca** pasa el `user_id` real, factory:149-155)
     → todos los tokens OAuth de **todos los usuarios colisionan** bajo `mcp/mcp/<srv>/oauth_tokens.json`
     (token_storage.py:23-25). Es **peor** que "tokens user=mcp": es una **colisión multi-usuario real** para el propio
     implementador (agentic_assistant) que la tesis dice necesitar user-scope. Sólo se alcanza si `config.auth=="oauth"`
     (provider.py:85).
  2. **`StorageBackedMcpConfigStore` y `StorageBackedSkillStore` NO los auto-cablea el factory** — son inyección **pura**
     del integrador (`caps.mcp_config_store`/`caps.skill_store`, default None → provider recibe None; factory NO construye
     el default sobre `storage`). Sus claves inventadas (`mcp/servers.json` sin scope, config_store.py:36; `skills/<name>/SKILL.md`
     sin scope, store.py:40) **sólo corren si el integrador las inyecta**. ⇒ En el standalone las **únicas** claves que
     tocan `storage` son `transcript_key` (StorageKeys, cableada) + OAuth-MCP (inventada, scope `"mcp"`, si hay server oauth).
  El núcleo del ❌ (6 de 7 claves muertas + scope inconsistente) **SE SOSTIENE y se agrava** (colisión "mcp" confirmada por cableado).

- **FIND-STOR12 (🟡 · precisión, sigue 🟡)** — `_persist` deriva `ctx.user_id or "anon"` (runtime.py:424), PERO
  `_build_child` **siempre** fija `user_id = task.owner_id or f"user_{uuid...}"` (runtime.py:209) — nunca None/vacío
  (subagente: heredado del snapshot). ⇒ el fallback `"anon"` es **código muerto defensivo**; la "colisión de todas las
  sesiones sin user_id bajo el mismo subtree" **no puede ocurrir** en el standalone (cada sesión = uuid fresco). El
  **riesgo real que se sostiene** es la **falta de validación** de `user_id`/`session_id` como componentes de clave
  seguros (liga FIND-STOR7); la sub-justificación "anon colisiona" queda corregida.

### Cabos que aterrizan — CONFIRMADOS por cableado

- **11·token_storage MCP** → auto-cableado al MISMO `storage` con scope `"mcp"` (arriba). Confirmado abriendo
  `McpProvider._default_client` (provider.py:79-96).
- **14·plan_file / `is_session_plan_file`** → `plan_file.py` lee **`ctx.storage`** (StorageContract: `real_path`/`ensure_local`),
  pero el runtime **nunca asigna `ctx.storage`** (sólo `ctx.fs`, runtime.py:324-325; `ToolUseContext.storage` default None,
  tool_use.py:49) ⇒ `get_plan`/`plan_file_exists` **INERTES en el standalone** (retornan None/False) = **cara-B de 14·FIND-PLAN4**
  (candado de plan sólo-texto; el StorageContract de plan es seam del integrador vía `root_context_modifier`). **NO deuda nueva**
  (anti-padding L10) — ya homed en 14. FIND-STOR6/StR6 (frontera implícita) confirmado: son dos seams, no fusionar.
- **01·`StorageContract` vs `StorageProtocol`** → FIND-STOR6 confirmado por el ensamblador (dos roles, `fs` vs `storage`,
  no puenteados en standalone). RESUELTO como en la 1ª pasada.
- **13·SessionMemory→storage** → la memoria usa `FilesystemMemoryStore(memory_root)` (seam propio, factory:166-172),
  **NO** el blob `StorageProtocol` — seam separado (13), coherente; no toca `StorageKeys`. Sin discrepancia.

**Sin costuras latentes NUEVAS** tipo `to_llm`/`category`/LAT-EXEC1-2/LAT-HOOK1/LAT-TOOL1/LAT-MCP1/LAT-SKILL1: el `"anon"`
muerto es fallback defensivo inalcanzable (no maquinaria a-medio-cablear) y `ctx.storage`-no-bound es seam de integrador
por diseño (=fs default ConfinedFilesystem). Cero B-orphans nuevos, **CERO cambios de estado**.

### Ledger de lectura ESTA ronda (columna Lectura)

**Canónico (A) — RE-LEÍDO 1→EOF esta ronda (L11):**

| Archivo | LOC | Lectura (2ª vuelta) |
|---|---|---|
| `utils/sessionStorage.ts` | 5105 | **íntegro** 1→5105 (bloques contiguos 1-700·700-1449·1449-2248·2248-3097·3097-3947·3947-5105) — el más grande (L08) |
| `utils/config.ts` | 1817 | **íntegro** 1→1817 (2 bloques 1-910·910-1817) |
| `utils/settings/settings.ts` | 1015 | **íntegro** 1→1015 |
| `utils/sessionStoragePortable.ts` | 793 | **íntegro** 1→793 |
| `utils/fsOperations.ts` | 770 | **íntegro** 1→770 |
| `utils/filePersistence/filePersistence.ts` | 287 | **íntegro** 1→287 |
| `utils/envUtils.ts` | 183 | **íntegro** 1→183 |
| `utils/sessionState.ts` | 150 | **íntegro** 1→150 → satélite ⛔ (07·session_state) |
| `cli/transports/WorkerStateUploader.ts` | 131 | **íntegro** 1→131 |
| `utils/filePersistence/outputsScanner.ts` | 126 | **íntegro** 1→126 (skip-symlink+TOCTOU) |
| `utils/lockfile.ts` | 43 | **íntegro → ⛔** (wrapper `proper-lockfile`, lib vendorizada) |
| `utils/cachePaths.ts` | 38 | **íntegro** 1→38 |
| `utils/env.ts` | **347** | **íntegro 1→347** (`getGlobalClaudeFile:14-26` única superficie storage; **60-347 = `íntegro → ⛔`** detección runtime/terminal/deployment, abierto y confirmado sin storage — L02; drift +6 vs 341 en esa parte no-storage) |
| `bootstrap/state.ts` | 1758 | **tramos in-scope re-leídos esta ronda**: 420-544 (`getSessionId`/`switchSession`/`getSessionProjectDir`/`getOriginalCwd`, **atomicidad CC-34**) + 1315-1339 (`getSessionTrustAccepted`→A6, `isSessionPersistenceDisabled`→B3); resto (cost/usage/model, ~1600 LOC) = 07/16, no troceo de in-scope (L07) |
| `memdir/teamMemPaths.ts` | 292 | tramos 1-75 (`sanitizePathKey` = modelo de StR7/13·MEM9) — satélite de 13 |
| satélites de OTRA categoría enteros (`memdir/paths.ts`→13, `utils/plans.ts`→14) | — | ya íntegros en su categoría (L07); cabos re-confirmados por cableado |

**Runtime (B) — leído 1→EOF esta ronda:**

| Archivo | LOC | Lectura |
|---|---|---|
| `storage/protocol.py` | 87 | **íntegro** (StorageProtocol + StorageKeys) |
| `storage/filesystem.py` | 70 | **íntegro** (guard `_path` startswith, `copy`, umask) |
| `storage/factory.py` | 33 | **íntegro** (StorageRegistry) |
| `storage/__init__.py` | 5 | **íntegro** |
| `contracts/storage.py` | 40 | **íntegro** (StorageContract + PathPresentation) |
| `capabilities/mcp/token_storage.py` | 65 | **íntegro** (scope `"mcp"` default) |
| `capabilities/mcp/config_store.py` | 146 | **íntegro** (no auto-cableado) |
| `capabilities/skills/store.py` | 71 | **íntegro** (no auto-cableado) |
| `capabilities/skills/provider.py` | tramo 1-60 | `SkillsProvider.__init__(state, *, skill_store, is_enabled)` — **sin param `storage`** (leído, confirma no-auto-cableado) |
| `capabilities/plan/plan_file.py` | 108 | **íntegro** (`ctx.storage` nunca bound → inerte) |
| **`factory.py` (ENSAMBLADOR)** | 267 | **íntegro 1→EOF (L09)** — `_build_local`:186 create + reparto |
| `execution/local/runtime.py` | 435 | tramos 60-104·195-334·410-435 (`__init__` storage/fs, `_build_child`, `ctx.fs`, `_persist`) |
| `capabilities/mcp/provider.py` | — | tramos 40-99 (`__init__`+`_normalize_store`+`_default_client`) |
| `context/tool_use.py` | 70 | **íntegro** (`storage`/`fs` fields) |
| `tests/test_storage_homologation.py` | 163 | **íntegro** |
| `tests/test_runtime_storage.py` | 143 | **íntegro** |

**Evidencia:** `uv run pytest test_storage_homologation.py test_runtime_storage.py` = **21 passed, 10 xfailed**
(todos strict, ningún xpass) → los gaps FIND-STOR1..13 persisten, ninguno "pasó por sorpresa" (que indicaría gap cerrado
+ doc desfasado). Código intacto.

### §Honestidad (2ª vuelta)

La 1ª pasada + re-audit 2026-07-14 leyeron A+B íntegros y clasificaron bien, PERO las filas ✅/🔀 se validaron por
confirmación-de-doc, **sin seguir el cableado en el ENSAMBLADOR** (modo de fallo L09). El gate 11 abrió `factory.py`
1→EOF y siguió el dato → destapó que (a) sólo `transcript_key` toca `storage` por ruta interna; (b) el token_storage
auto-cableado colisiona bajo `"mcp"`; (c) skills/mcp-config NO los cablea el factory; (d) `ctx.storage` nunca se liga →
plan_file inerte. Ninguno voltea estado — refinan FIND-STOR1/STOR12/STOR6. **A RE-LEÍDO 1→EOF esta ronda** (no apoyado
en la 1ª pasada — L11): cero discrepancias en las filas documentadas, `env.ts` driftó 341→347 (parte no-storage), citas
exactas = evidencia de lectura real.

**⚠ Cierre en 2 iteraciones (gate auto-adversarial del usuario, reproche recurrente 11/12/13/14).** Mi 1er cierre dejó
**3 residuos** de superficialidad, cerrados al reproche ("¿sin grep como único mecanismo, cero superficialidad, A todo
EOF?"): (1) **`env.ts` 60-347 NO abierto** — declaré "no-storage" por el doc leyendo sólo 1-60 (fallo L02); al abrirlo
1→347: todo detección runtime/terminal/deployment, ⛔ ahora legítimo, cero storage. (2) **`bootstrap/state.ts` tramo de
identidad de sesión NO re-leído esta ronda** — me apoyé en la 1ª pasada (mismo fallo L11 que 14·F1-F8); re-leídos
420-544 (atomicidad CC-34) + 1315-1339 → confirman FIND-STOR12/A6/B3, cero discrepancia. (3) **`SkillsProvider.__init__`
verificado por GREP** — la conclusión "sin `storage`" descansaba en grep (viola "cableado=leer"); leído 1-60 → confirmado
`(state, *, skill_store, is_enabled)` sin `storage`. Además **grep de AUSENCIA esta ronda** (legítimo para ausencia):
`config_key`/`agent_md_key`/`ltm_key`/`meta_key`/`work_key`/`log_key` = **0 consumidores de prod** (sólo definidas en
`protocol.py`); sólo `transcript_key` cableada (`_persist`, por lectura) → **FIND-STOR1 confirmado ESTA ronda por
ausencia+lectura**, no heredado del doc. Los 3 residuos **confirmaron el doc** (cero cambios de estado); el cierre queda
GANADO, no asumido. Regla re-interiorizada: L07 acota el archivo satélite pero NO exime de re-leer el TRAMO in-scope esta
ronda (`bootstrap/state.ts`); ⛔ sólo tras abrir (`env.ts` 60-347); cableado = leer, nunca grep (`SkillsProvider`).

### 4 preguntas de cierre (2ª vuelta)

1. **¿Se revisó todo cada archivo canónico (A) listado?** — **Sí, RE-LEÍDO 1→EOF esta ronda.** Los grandes
   (`sessionStorage.ts` 5105 / `config.ts` 1817 / `settings.ts` 1015 / `sessionStoragePortable.ts` 793 / `fsOperations.ts` 770)
   íntegros en bloques contiguos cerrando huecos (L08); los medianos/pequeños íntegros; satélites 13/14 ya íntegros en su
   categoría (L07), cabos re-confirmados por cableado.
2. **¿Se revisó todo cada archivo runtime (B) listado?** — **Sí, 1→EOF esta ronda**, incluido el **ENSAMBLADOR
   `factory.py` 1→EOF** (L09) + los consumidores reales (`_persist`, `McpProvider._default_client`, `plan_file`, `ctx.storage`/`ctx.fs`).
3. **¿Los hallazgos fueron exhaustivos (no superficiales)?** — **Sí.** El gate 11 añadió el cableado del ensamblador
   (2 precisiones a FIND-STOR1/STOR12), confirmó FIND-STOR6 (dos seams) y el aterrizaje de los cabos 11/14/01/13 por lectura,
   no por tabla. Cero discrepancias de estado.
4. **¿Quedó todo cubierto (nada pendiente)?** — **Sí.** CERO cambios de estado (✅3·🟡7·🔀9·❌15·⛔2 intactos); §Plan
   StR1-8 intacto; cabos con destino; sin B-orphans nuevos (anti-padding L10); lo delegado (cascada A8, upsert coalescente)
   →18/integrador; E3/cost-usage →07/16. Código intacto; suite verde (21 passed/10 xfailed strict).

### VEREDICTO DE AVANCE

**✅ NADA PENDIENTE → avanzar a 16·models con gate 11.** (01→15 completos; no quedan pendientes de verificación de la
2ª vuelta.)
