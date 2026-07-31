# 15 · storage — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/15-storage.md`.
> Tracker de origen: `../15-storage.md` (543 LOC, leído ÍNTEGRO 1→EOF este ciclo). Esquema: `00-LEGEND.md §3`.
> PASO 0 (11 lecciones skill) ejecutado. Ensamblador y consumidores RE-ABIERTOS 1→EOF EN ESTE CICLO (L09/L11,
> NO heredados de la re-visita gate-11 del tracker 2026-07-20).

---

## 0. Tesis de separación (Filosofía B)

El tracker ya diagnostica la forma B correcta: el runtime **deliberadamente NO reifica el formato opinado** del
canónico (JSONL append-only + sidecars + cascada de config de 4 niveles + `~/.claude.json`). En su lugar ofrece un
**blob store k/v agnóstico**. La SEPARACION descompone eso en tres capas nítidas:

1. **Base = el seam del blob + su default de dev.** `StorageProtocol` (`upload/download/presign/delete/exists/
   list_prefix` + `copy`) = **T2-COSTURA** que el integrador rellena con MinIO/S3; `StorageRegistry` = mecanismo
   base pluggable (**T2-BASE**); `StorageKeys` = **taxonomía de claves determinista (T1-CONTRATO)**; `FilesystemStorage`
   = **backend nativo default** (dev/tests, T2-BASE). Es un **🔀 arquitectural correcto** (canónico single-user en
   terminal ↔ runtime multi-user sobre blob) — valor propio confirmado: `presign` (servir por URL) y `register` (MinIO)
   NO existen en el canónico.
2. **La FORMA de persistencia = BATTERIES opcionales** que se **componen sobre el seam del blob**. El sidecar meta,
   el config-store con cascada por scope, el catálogo/listado de sesiones y el motor de outputs son **shapes reusables
   por AMBOS integradores** (agentic_code y agentic_assistant) → paquetes estándar, no política de un solo producto.
   Reificar el shape como battery (no como gap del base) es el mismo criterio que 06 (el sistema typed-hooks
   configurable = `battery_hooks_config`, no CORE-GAP). **Anti-padding L10:** su ausencia = la battery a construir en
   Fase C, NO decenas de ❌ del base.
3. **El BACKEND, la POLÍTICA de scope y el TRANSPORTE = integrador.** Quién es MinIO, qué scopes de config existen
   (managed/user/project/local) y su modelo de confianza, el upsert coalescente del estado remoto (`WorkerStateUploader`),
   y quién consume el listado (BFF) = `00-INTEGRADORES.md`.

**La promesa del base está a MEDIO CUMPLIR (verificado por cableado este ciclo, no heredado):** de las **7 claves de
`StorageKeys` sólo `transcript_key` tiene consumidor de producción** (`_persist`, runtime.py:428); las otras 6 = **0
consumidores prod** (grep-de-ausencia este ciclo, legítimo para ausencia — §3.3). Peor: los stores que SÍ persisten
**ignoran la taxonomía** e inventan clave, con **scope inconsistente** y un **bug multi-usuario real** (tokens OAuth
de todos los usuarios colisionan bajo `mcp/mcp/<srv>`). Eso son **CORE-GAPs del base** (el base PROMETE la taxonomía
y no la cumple), distinto de las batteries ausentes.

### 0.1 DESAMBIGUACIÓN load-bearing — DOS seams de storage, NO fusionar (FIND-STOR6, cabo de 01)

Coexisten y **no deben fusionarse a ciegas** (verificado por el ensamblador este ciclo):
- **`StorageContract`** (`contracts/storage.py`: `real_path`/`ensure_local`/`commit`/`teardown`) = **path de archivo
  local para I/O de tools**, con ciclo ensure/commit. Lo consumen `fs_env` (09) y `plan_file` (14). Se cablea vía
  `ctx.storage`/`ctx.fs`. **T2-COSTURA** (home 01/09).
- **`StorageProtocol`** (`storage/protocol.py`: blob k/v) = **transcript/token/skills/mcp-config**. Se cablea vía
  `self._storage` del runtime. **T2-COSTURA** (home 15).

Son **dos roles distintos** (archivo-local-con-ciclo vs blob-k/v), pero **comparten backend físico** (un mismo MinIO).
Hoy la frontera es **implícita**: el ensamblador (`factory.py:226` `storage=` vs `:229` `fs=config.fs`) los pasa por
canales separados y **nada los puentea** en el standalone. Remediación = documentar los dos roles + ofrecer un
adaptador `StorageContract` que `commit`ee vía `StorageProtocol.upload` (StR6). **NO es CORE-GAP de forma** — es
clarificación de seam. Cierra el cabo 01·feat-10 (🔀 seam inventado, confirmado).

### 0.2 Eje transversal `persistencia` — multi-repo, NO god-store (anti-god-object)

La nota-identidad `persistencia` del `00-LEGEND §2.4` se realiza aquí con un patrón clave: el durable NO es un único
objeto global, son **VARIOS repos id-opaco+genérico coexistentes**, cada uno su seam:
- **transcript** → `StorageProtocol` (blob, `<uid>/<sid>/…` — `user_id`/`session_id` = componentes opacos de clave).
- **memoria** → `MemoryStore`/`FilesystemMemoryStore` (seam PROPIO, factory:166-172 — **NO** `StorageProtocol`,
  confirmado este ciclo; home 13).
- **sesión (registro/scope)** → `SessionRepo` (A2·S20, home 05/execution).
- **config/meta/catálogo** → batteries sobre el blob.

Todos siguen `id opaco + repo`, ninguno interpreta `userId`/`sessionId` como identidad — sólo como componentes de
clave. Un único "StorageManager" god-object sería el anti-patrón. Esto refuerza el `00-INTEGRADORES` (el integrador
compone N repos, no hereda uno).

---

## 1. Tabla por finding (grid del tracker · A1-A8 · B1-B13 · C1-C3 · D1-D3 · E1-E3 · F1-F3 = **33 filas**)

> Los findings-resumen `FIND-STOR1..13` = **capa de remediación** que reafirma celdas del grid (STOR1→F2/A2, STOR2→B1,
> STOR3→B4/B10, STOR4→A2-A7, STOR5→B8, STOR6→C1, STOR7→B13/C2, STOR8→B12, STOR9→C3, STOR10→D2, STOR11→E2, STOR12→
> `_persist`, STOR13→A8); **no se re-cuentan** (patrón 06/10/04). `StR1-8` = §Plan desarrollado (6 campos L05) en el
> tracker — se **referencian** para la cara-base y se desarrolla la cara-integrador simétrica aquí (§2.5).

### A · Persistencia de CONFIG (`config.ts` 1817 · `settings.ts` 1015 · `env{,Utils}.ts`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| A1 | config-home `$CLAUDE_CONFIG_DIR ?? ~/.claude` (memo, NFC) | cáscara/producto | T3-INTEGRADOR | `00-INTEGRADORES` (backend pone el home) | persistencia | 🔀 runtime usa claves user-scoped `<uid>/…`; el "home" = bucket/root del backend |
| A2 | `~/.claude.json` = GlobalConfig (~180 campos) + `projects[path]` | núcleo | BATTERY | `battery_config` (`config_key`) | persistencia | ❌ `config_key` declarada SIN consumidor prod (0, este ciclo); la persiste la battery |
| A3 | `getConfig`: read+merge-defaults+stripBOM+corrupción→backup+restore-prompt | núcleo | BATTERY | `battery_config` (load) | — | ❌ lógica de lectura tolerante de la battery (StR4) |
| A4 | `saveConfigWithLock`: lock+backup keep-5+guard-anti-pérdida-auth #3117+atómico 0600+strip | núcleo | BATTERY | `battery_config` (write) | — | ❌ write-path de la battery; `lockfile.ts` en sí = ⛔ (lib `proper-lockfile`, no core) |
| A5 | caché en-mem + `fs.watchFile` freshness-watcher (relee escrituras de otros procesos) | núcleo+cáscara | BATTERY + T2-COSTURA | `battery_config` (caché) · `ConfigWatcher` (integrador) | — | ❌ caché=battery; el watcher externo = seam del integrador (espejo `McpConfigWatcher`) |
| A6 | `ProjectConfig` keyed por git-root + cascada de **trust** (sube por padres) | núcleo+producto | BATTERY + T3-INTEGRADOR | `battery_config` (scope project) · `00-INTEGRADORES` (modelo trust) | — | ❌ el scope project=battery; la política de confianza=integrador (=FIND-STOR13 invariante) |
| A7 | Migraciones (`migrateConfigFields`/`removeProjectHistory`/`migrationVersion`) | núcleo | BATTERY | `battery_config` (migraciones) | — | ❌ hooks de migración de la battery |
| A8 | cascada settings.json 4+ niveles `plugin→user→project→local→flag→policy` + policy sub-cascada + zod + caché (=**FIND-STOR13**) | núcleo+producto | BATTERY + T3-INTEGRADOR | `battery_config` (`ScopedConfigStore`) · `00-INTEGRADORES` (qué scopes + trust) | — | 🔀→❌ maquinaria de merge/precedencia/mutabilidad = battery (generaliza `ScopedMcpConfigStore`); qué-scopes + **invariante seguridad project-no-privilegio** cruza a integrador+13/06 |

### B · Persistencia de SESIÓN / transcript (`sessionStorage.ts` 5105 · `sessionStoragePortable.ts` 793)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| B1 | JSONL **append-only** bufferizado (writeQueues/drain/flush/MAX_CHUNK) | núcleo | T2-BASE-MECANISMO | `execution/local/runtime._persist` + **CG-STOR-2** | persistencia | 🔀→❌ el base persiste el MODELO reconstruido por snapshot (no el log crudo → B6/B7/B9 N/A por diseño); pero **falta durabilidad incremental mid-turn** (StR2) = CORE-GAP |
| B2 | Layout `<projectsDir>/<cwd>/<sid>.jsonl` + subagentes `…/<sid>/subagents/` | núcleo | T1-CONTRATO | `StorageKeys` (taxonomía) | persistencia | 🔀 `transcript_key`=`<uid>/<sid>/session.json` user-scoped + subtree anidado = MEJORA multi-user; blob único vs jsonl |
| B3 | Materialización lazy + `shouldSkipPersistence` gate (test/`--no-session-persistence`/`cleanupPeriodDays=0`) | núcleo | T2-BASE-MECANISMO | `_persist` (gate) | — | 🟡 sin gate de persistencia; minor — el integrador puede querer suprimir persistencia (política) |
| B4 | Sidecars meta EN jsonl: title/tag/mode/worktree/pr/agent-name+color/last-prompt/summary + `reAppendSessionMetadata` | núcleo | BATTERY | `battery_session_meta` (`meta_key`) | persistencia | ❌ **FIND-STOR3**: `meta_key` declarada SIN consumidor (0, este ciclo); sidecar mutable = battery |
| B5 | Persistencia remota: `sessionIngress` v1 + CCR v2 event writer/reader + hydrate/epoch | producto | T3-INTEGRADOR | `00-INTEGRADORES` (transporte) | — | 🔀 el propio `StorageProtocol` ES lo remoto (MinIO); un `upload`. Sin ingress/hydrate por diseño |
| B6 | Load: `loadTranscriptFile` (chunked/skip-precompact/walkChain/relinks/snip/leaves) | núcleo | T2-BASE-MECANISMO | `download`+parse | — | 🔀 el runtime persiste el modelo ya-reconstruido → gran parte N/A por diseño |
| B7 | `buildConversationChain`+`recoverOrphanedParallelToolResults`+`checkResumeConsistency` (DAG) | núcleo | — | N/A por diseño | — | 🔀 la `Session` YA es la cadena; sin reconstrucción de log crudo |
| B8 | Listado/enriquecimiento: `getSessionFilesLite`+`readLiteMetadata`(head/tail 64KB)+`enrichLogs`+search-by-title | núcleo | BATTERY | `battery_session_catalog` | persistencia | ❌ **FIND-STOR5**: `list_prefix` da keys crudas; el BFF necesita título/última-actividad/primer-prompt sin descargar transcripts |
| B9 | Tombstone `removeMessageByUuid` (splice + slow-path rewrite ≤50MB) | núcleo | — | N/A por diseño | — | 🔀 el overwrite del blob lo hace N/A |
| B10 | Sidecar de agente `writeAgentMetadata` (agentType/worktreePath/description) + `RemoteAgentMetadata` per-task sobrevive-wipe | núcleo | BATTERY | `battery_session_meta` (agent-meta) | persistencia | ❌ sin clave agent-meta; **liga 05·GAP-EXEC3 resume** (el resume la lee) |
| B11 | `file-history-snapshot`/`attribution-snapshot`/`content-replacement`/`marble-origami` (context-collapse) | núcleo | BATTERY | `battery_compaction` (02) / 03·context | — | ❌ persistencia del colapso de contexto; cruza a la battery de compactación (02·LR1/A2.4) + 03 |
| B12 | Perms dirs 0o700 / files 0o600 (secreto por defecto) | núcleo | **CORE-GAP** | **CG-STOR-3** (`filesystem.py`) | — | 🟡 **FIND-STOR8**: `_write` hereda umask; el backend FS de dev filtra transcripts/tokens con perms laxas (N/A MinIO=ACL) |
| B13 | `sanitizePath`(no-alfanum→`-`, cap200+hash) + `resolveSessionFilePath`(canonicaliza+worktree+hash) | núcleo | **CORE-GAP** | **CG-STOR-3** (key-sanitize) | persistencia | 🟡 guard `_path` prefix-startswith débil; sanitizar clave antes de resolver (espejo 13·MEM9) |

### C · Seam de FS + guards de path (`fsOperations.ts` 770)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| C1 | `FsOperations` (~50 métodos) + `get/setFsImplementation` (mock/virtual injectable) | núcleo | T2-COSTURA (×2) | `StorageContract` (01/09) + `StorageProtocol` (15) | — | 🔀 **FIND-STOR6**: DOS seams por diseño (§0.1); frontera a documentar, no fusionar (StR6) |
| C2 | `getPathsForPermissionCheck`/`safeResolvePath` (symlink chain, UNC-block, FIFO/socket/device-block) | núcleo | 🔀→09 + CORE-GAP | `fs_env.ConfinedFilesystem` (09) · **CG-STOR-3** | — | 🔀 el confinamiento de tools lo homologa 09; `FilesystemStorage._path` es un guard SEPARADO y más débil (StR7) |
| C3 | `readFileRange`/`tailFile`/`readLinesReverse` (ventanas de archivos GB) | núcleo | **CORE-GAP** | **CG-STOR-4** (`StorageProtocol.download_range`) | — | ❌ **FIND-STOR9**: `download` es todo-o-nada; el lite-scan de `battery_session_catalog` lo prerrequiere |

### D · Cache / logs / work (`cachePaths.ts` 38 · `filePersistence/` 287+126)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| D1 | `CACHE_PATHS`=`envPaths('claude-cli').cache/<proj>/{errors,messages,mcp-logs}` (djb2 estable) | cáscara/producto | DEUDA-B + T3-INTEGRADOR | `log_key` slot muerto (borrar/cablear) · `00-INTEGRADORES` (cache=deployment) | — | ❌ `log_key` declarada SIN consumidor (0, este ciclo); la ruta de cache/logs = efímera del deployment |
| D2 | Outputs: `runFilePersistence` (BYOC scan-modified + `uploadSessionFiles` + `FILE_COUNT_LIMIT`) + `outputsScanner`(skip-symlink+guard-TOCTOU) | núcleo | BATTERY | `battery_outputs` (`work_key`) | persistencia | 🔀 **FIND-STOR10**: `work_key`+`copy` esbozados; el MOTOR (scan-modified+skip-symlink+TOCTOU) ausente = battery |
| D3 | `history.jsonl` (historial de prompts del proyecto) | cáscara/producto | BATTERY + CLI-ONLY | `battery_outputs` (history append) · `00-INTEGRADORES` (REPL history) | — | ❌ prompt-history = afordancia de terminal; primitiva append en battery, consumo en integrador |

### E · Config-file-path / estado remoto / session-state (`env.ts` · `WorkerStateUploader.ts` 131 · `sessionState.ts` 150)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| E1 | `getGlobalClaudeFile` (memo, fallback legacy `.config.json`) | núcleo | BATTERY | `battery_config` (=A2) | persistencia | ❌ cubierto por A2/`config_key` muerta; sin re-contar remediación |
| E2 | `WorkerStateUploader`: PUT /worker coalescente (1 in-flight+1 pending, merge RFC7396, backoff exp) | producto | T3-INTEGRADOR | `00-INTEGRADORES` (18/transporte) | — | 🔀 **FIND-STOR11**: patrón de upsert del sidecar meta sobre MinIO; hogar = transporte del integrador, referencia-fuente de `battery_session_meta` |
| E3 | `sessionState` (idle/running/requires_action + external_metadata + listeners) | núcleo | ⛔→07 | **07·FIND-EVT7** (`session_state_changed`) | — | ⛔-para-15: satélite de eventos (07) + external_metadata (persistencia CCR→18) |

### F · Registry / primitivas de blob (`factory.py` · `StorageRegistry` · `StorageKeys` · `FilesystemStorage`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| F1 | `StorageRegistry.register`/`create` (instancia fresca, no singleton); factory instancia+comparte | núcleo | T2-BASE-MECANISMO | `storage/factory.py` | — | ✅ valor propio (pluggable MinIO); el canónico no tiene registry. Verificado `factory.py:186` 1→EOF |
| F2 | `StorageKeys` (config/agent_md/ltm/transcript/meta/work/log) — taxonomía determinista | núcleo | T1-CONTRATO | `StorageKeys` + **CG-STOR-1** | persistencia | ❌ **FIND-STOR1 CRÍTICO**: sólo `transcript_key` cableada (1 prod); las otras 6=0 prod (este ciclo); stores inventan clave, scope inconsistente |
| F3 | `upload/download/presign/delete/exists/list_prefix`+`copy`; `presign` FS=`file://`, MinIO=URL firmada | núcleo | T2-COSTURA | `StorageProtocol` | — | ✅ valor propio (`presign` sirve blobs por URL); seam base del blob |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`StorageProtocol`** (T2-COSTURA, home 15) — blob k/v. Productor: `_persist` + los stores de battery. Consumidor:
  `FilesystemStorage` (default base) o el backend MinIO del integrador (vía `StorageRegistry.register`). Verificado
  cableado este ciclo: `factory.py:186` crea UNA instancia y la reparte a `runtime` (:226) + `McpProvider` (:194→:152).
- **`StorageContract`** (T2-COSTURA, home 01/09) — path-de-archivo para tools. Productor: `plan_file`/`fs_env`.
  Consumidor: `ConfinedFilesystem` (default) o `BlobBackedStorageContract` (StR6). **SEPARADO de `StorageProtocol`**
  (§0.1); verificado: `ctx.storage` NUNCA se liga en `runtime.py` (306-416) → `plan_file` inerte en standalone.
- **`StorageKeys`** (T1-CONTRATO) — taxonomía determinista. La rellena el base; hoy sólo `transcript_key` cableada.
- **`ConfigWatcher`** (T2-COSTURA NUEVA, A5) — detección de escrituras externas de config (espejo exacto de
  `McpConfigWatcher` de 11); la provee el integrador (poll MinIO / inotify). Consumidor: `battery_config`.
- **`SessionCatalog`** (seam de `battery_session_catalog`, StR5) — `list_sessions(user_id)` sobre `list_prefix`+meta.
- **Backend perms** (integrador) — MinIO ACL vs FS 0600 (B12/CG-STOR-3 es sólo el default FS de dev).

### 2.2 Batteries que alimenta (shapes de persistencia opcionales sobre el blob)
Familia `battery_persistence.*` — cada shape es un paquete estándar componible por AMBOS integradores (catálogo →
A3.CAT). Su ausencia = trabajo de Fase C, **no** CORE-GAP del base (L10):
- **`battery_session_meta`** (B4/B10, FIND-STOR3) — sidecar `session.meta.json` mutable `{title, tag, mode, worktree,
  pr, is_backgrounded, agent_type, description, updated_at}`; upsert merge RFC-7396 (patrón `WorkerStateUploader`
  E2/STOR11). **Habilita 04·backgrounding-persistido + 05·GAP-EXEC3 resume.** Base-6-campos = StR3.
- **`battery_config`** (A2-A8/E1, FIND-STOR4+STOR13) — `ConfigStore` (read-merge-defaults+write-atómico) +
  `ScopedConfigStore` (cascada managed/user/project/local/flag + merge por precedencia + gate de mutabilidad +
  arrays-concat-dedup) generalizando `ScopedMcpConfigStore`. Base-6-campos = StR4.
- **`battery_session_catalog`** (B8, FIND-STOR5) — `list_sessions`/enrich/search leyendo sólo el meta-sidecar,
  paginado; **depende de `battery_session_meta` + CG-STOR-4 (`download_range`)** para el lite-scan. Base = StR5.
- **`battery_outputs`** (D2/D3, FIND-STOR10) — `persist_outputs` (scan-modified + skip-symlink + guard-TOCTOU +
  `FILE_COUNT_LIMIT`) reusando `copy` + `history` append. Base = StR8-part.

### 2.3 CORE-GAPs (brechas A↔B reales del BASE → rollup `DEUDA-A.md`)
El base PROMETE estas capacidades (seam/taxonomía declarados) y NO las cumple — distinto de las batteries ausentes.
Los 6 campos L05 ya desarrollados en el tracker (StR1/2/6/7/8); aquí se anclan con su ID de rollup:
- **CG-STOR-1** (F2/A2, FIND-STOR1) — **cablear la taxonomía completa + scope uniforme**. Hoy 6/7 claves muertas +
  stores inventan clave. Incluye el **bug multi-usuario**: `McpProvider` recibe `user_id="mcp"` por default y el
  factory NUNCA pasa el real (`provider.py:50/87` + `factory.py:149-155`, verificado) → tokens OAuth de TODOS los
  usuarios colisionan bajo `mcp/mcp/<srv>/oauth_tokens.json`. **Cruza a 11·mcp** (el fix del user_id vive en el
  cableado del provider). Base = StR1.
- **CG-STOR-2** (B1, FIND-STOR2) — **durabilidad incremental del transcript**. `_persist` snapshot-overwrite por
  completion (runtime.py:430) → crash mid-turn pierde el turno; sin persistencia de subagente hasta terminar. Un
  daemon multi-sesión lo necesita. Base = StR2 (`StorageProtocol.append` opcional + `persist_incremental` en el
  límite de ronda del loop). **Cruza a 02·loop** (el disparo por-ronda).
- **CG-STOR-3** (B12/B13/C2, FIND-STOR7/8/12) — **guard de path robusto + sanitización de clave + perms**.
  `FilesystemStorage._path` usa `startswith` → vulnerable a hermano-prefijo (`/data/root-evil`); sin sanitizar
  `\0`/`..`/absolutos/backslashes; `_write` hereda umask. **Espejo exacto de 13·MEM9** (`sanitizePathKey`) → helper
  unificado. Seguridad, alta prioridad. Base = StR7.
- **CG-STOR-4** (C3, FIND-STOR9) — **`StorageProtocol.download_range`** (default: download+slice; MinIO Range
  header). Prerreq del lite-scan de `battery_session_catalog`. Base = StR8-part.
- **CG-STOR-5** (C1, FIND-STOR6) — **frontera `StorageContract`↔`StorageProtocol`** documentada + adaptador
  `BlobBackedStorageContract` (StR6). No es gap de forma; es clarificación de seam (§0.1). Cierra cabo 01.

### 2.4 DEUDA-B (higiene interna del runtime — L10, NO A↔B)
- **`log_key` slot muerto** (D1) — declarada en `protocol.py:86`, 0 consumidores prod (este ciclo). O se cablea (si
  el runtime quiere log durable) o se borra. Análogo a los slots `config_key`/`meta_key`/`work_key`, pero ésos tienen
  battery-dueño (CG-STOR-1 los cablea); `log_key` no tiene battery ⇒ decisión borrar-vs-cablear en A3.DB.
- **`"anon"` muerto defensivo** (`_persist`, runtime.py:424) — `ctx.user_id or "anon"`, pero `_build_child:209`
  SIEMPRE fija `user_id = task.owner_id or f"user_{uuid}"` (verificado 1→EOF) → nunca None; la rama `"anon"` es
  inalcanzable. NO es maquinaria a-medio-cablear (a diferencia de LAT-*): es fallback defensivo → limpiar al pasar
  StR7 (que valida componentes de clave). Cero B-orphans nuevos, cero LAT-* nuevas (§3.3).

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05/§1.1)

**Must-be universal (CONTRATO BASE COMÚN — obligación de TODO integrador con persistencia durable):**
- **OI-STOR-A · Proveer el BACKEND del blob.** Capacidad: el durable físico (dev=FS, prod=MinIO/S3). Costura:
  `StorageRegistry.register("<backend>", Cls)` + `RuntimeConfig.storage.{backend,root,extra_kwargs}`. Firma:
  clase que satisface `StorageProtocol` (6 métodos +`copy`). Realización: agentic_code = `FilesystemStorage` (default,
  sobre el FS del usuario); agentic_assistant = backend MinIO (register + presign real). Criterio: `_persist` sube el
  transcript y `download` lo recupera; `presign` da URL servible. (F1/F3.)
- **OI-STOR-B · Componer las batteries de shape que el producto necesita.** Capacidad: el integrador ELIGE y cablea
  `battery_session_meta`/`battery_config`/`battery_session_catalog`/`battery_outputs` sobre el mismo backend. Costura:
  inyección por `RuntimeConfig`/factory (los stores reciben `user_id` real — cerrando CG-STOR-1). Firma: `caps.*_store`
  + los seams de battery (§2.2). Realización: agentic_code = config+meta local; agentic_assistant = las 4 sobre MinIO
  + BFF que consume `list_sessions`. Criterio: la clave de cada store deriva de `StorageKeys`, scope uniforme, sin
  colisión `"mcp"`. (A2-A8/B4/B8/B10/D2.)
- **OI-STOR-C · Ligar el `StorageContract` de tools al mismo backend.** Capacidad: `ctx.storage`/`ctx.fs` para que
  `plan_file`/`fs_env` operen (hoy `ctx.storage` inerte). Costura: `ctx.storage = BlobBackedStorageContract(storage,
  workdir)` vía `root_context_modifier` (o el `PathStorage` del integrador). Firma: StR6. Realización: agentic_code =
  identidad local; agentic_assistant = materializa MinIO→workspace del contenedor. Criterio: `get_plan`/`plan_file_exists`
  dejan de retornar None/False. (C1, cabo 14·FIND-PLAN4.)
- **OI-STOR-D · Política de scope + confianza de la cascada de config.** Capacidad: QUÉ scopes existen (managed←
  plataforma, user←MinIO, project←repo, local, flag) y el **invariante de seguridad: el scope `project` NO concede
  privilegio** (excluido de lecturas trust-sensibles — espejo de `hasSkipDangerousModePermissionPrompt`/13·
  `getAutoMemPathSetting`; "un proyecto malicioso podría auto-bypassear el diálogo / inyectar reglas RCE"). Costura:
  `ScopedConfigStore.set_producer(scope, store)` + `assert_mutable`. Realización: agentic_code = user local +
  project repo (untrusted); agentic_assistant = managed plataforma + user MinIO. Criterio: una regla de permiso de
  scope-project NO altera `defaultMode`/dangerous-skip. (A6/A8, FIND-STOR13; **cruza 06·GAP-02 semántica de permisos**,
  aquí sólo la PERSISTENCIA/cascada.)
- **OI-STOR-E · Transporte de upsert del estado remoto** (`WorkerStateUploader`: coalescing PUT + RFC7396 + backoff).
  Capacidad: empujar el meta-sidecar mutable a la fuente remota sin reescribir el blob grande. Costura: consume
  `battery_session_meta.patch`. Realización: ⛔ N/A agentic_code (local); agentic_assistant = 18/transporte. Criterio:
  N upserts concurrentes convergen a un merge coherente. (E2, FIND-STOR11.)
- **OI-STOR-F · Watcher de config externa** (A5) — espejo de `McpConfigWatcher` (11). Realización: agentic_code =
  inotify; agentic_assistant = poll/evento MinIO. Criterio: una escritura externa de config se relee sin reinicio.

**Cabos que aterrizan aquí (cerrados con destino):**
- **06·OI-HOOK-C (persistir permisos aprobados)** → **hogar: `battery_config` / `battery_session_meta`** — los
  `always_allow_command`/`always_allow_session` aprobados se persisten como config user-scoped (durable entre
  sesiones) o meta de sesión (efímera de la sesión). La PERSISTENCIA es de 15 (battery_config); la SEMÁNTICA
  (cuándo se pregunta) es 06·GAP-02. Cruce explícito, no re-desarrollo.
- **04·A2 (persistencia del modo-sesión coordinator)** → ⛔ N/A hoy; si un integrador adopta swarm, el modo-sesión
  reconciliable (`matchSessionMode`) se persiste sobre `StorageProtocol` como meta → `00-INTEGRADORES` (swarm
  hipotético, =04·A2). No es gap del base.
- **13·memory** → seam PROPIO `FilesystemMemoryStore` (factory:166-172, verificado), NO `StorageProtocol`; coherente
  con §0.2 (multi-repo). Sin discrepancia.
- **14·FIND-PLAN4 / `is_session_plan_file`** → `plan_file` sobre `StorageContract` (`/plans/*.md`), inerte en
  standalone (`ctx.storage` no-bound); cara-B ya homed en 14. Cerrado por OI-STOR-C.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor:** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda;
ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar
—o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (33 = A1-A8·8 + B1-B13·13 + C1-C3·3 + D1-D3·3 + E1-E3·3 + F1-F3·3)
| ID | TIER | destino | cara | evidencia | detalle | nota-id |
|---|---|---|---|---|---|---|
| A1 | T3-INTEGRADOR | 00-INTEGRADORES (backend home) | integrador | tracker-leído + `protocol.py` 1→EOF (claves user-scoped) | sí (§2.5 OI-A) | persistencia |
| A2 | BATTERY | battery_config (config_key) | ambas | `protocol.py:53` + grep-ausencia `config_key`=0 prod | sí (StR4+§2.5 OI-B) | persistencia |
| A3 | BATTERY | battery_config (load) | base | tracker-leído (`config.ts` íntegro) | sí (StR4) | — |
| A4 | BATTERY | battery_config (write) | base | tracker-leído; `lockfile.ts`=⛔ lib | sí (StR4) | — |
| A5 | BATTERY + T2-COSTURA | battery_config · ConfigWatcher | ambas | tracker-leído | sí (StR4+§2.1) | — |
| A6 | BATTERY + T3-INTEGRADOR | battery_config · 00-INTEGRADORES (trust) | ambas | tracker-leído | sí (§2.5 OI-D) | — |
| A7 | BATTERY | battery_config (migraciones) | base | tracker-leído | sí (StR4) | — |
| A8 | BATTERY + T3-INTEGRADOR | battery_config (ScopedConfigStore) · 00-INTEGRADORES | ambas | tracker-leído (`settings.ts` 1015 íntegro) + `config_store.py` 1→EOF (`ScopedMcpConfigStore` a generalizar) | sí (StR4+§2.5 OI-D) | — |
| B1 | T2-BASE-MECANISMO | _persist + CG-STOR-2 | base | `runtime.py:418-432` 1→EOF (snapshot por completion) | sí (StR2) | persistencia |
| B2 | T1-CONTRATO | StorageKeys | base | `protocol.py:67-73` 1→EOF | sí (§2.1) | persistencia |
| B3 | T2-BASE-MECANISMO | _persist (gate) | base | `runtime.py:416` (persist incondicional si storage) | sí (§1) | — |
| B4 | BATTERY | battery_session_meta (meta_key) | base | `protocol.py:72` + grep-ausencia `meta_key`=0 prod | sí (StR3) | persistencia |
| B5 | T3-INTEGRADOR | 00-INTEGRADORES (transporte) | integrador | tracker-leído | sí (§2.5) | — |
| B6 | T2-BASE-MECANISMO | download+parse | base | `runtime.py:430` (model_dump_json) | sí (N/A diseño) | — |
| B7 | — | N/A por diseño | base | tracker-leído (Session=cadena) | N/A (🔀) | — |
| B8 | BATTERY | battery_session_catalog | ambas | `filesystem.py:42-50` (`list_prefix` da keys crudas) 1→EOF | sí (StR5+§2.5 OI-B) | persistencia |
| B9 | — | N/A por diseño | base | tracker-leído | N/A (🔀) | — |
| B10 | BATTERY | battery_session_meta (agent-meta) | base | tracker-leído; liga 05·GAP-EXEC3 | sí (StR3) | persistencia |
| B11 | BATTERY | battery_compaction (02)/03 | base | tracker-leído; cruce 02·LR1 | sí (cross 02/03) | — |
| B12 | CORE-GAP | CG-STOR-3 | base | `filesystem.py:63-65` 1→EOF (`_write` sin modo) | sí (StR7) | — |
| B13 | CORE-GAP | CG-STOR-3 | base | `filesystem.py:14-18` 1→EOF (`_path` startswith) | sí (StR7) | persistencia |
| C1 | T2-COSTURA ×2 | StorageContract + StorageProtocol | base | `contracts/storage.py` 1→EOF + `protocol.py` 1→EOF + `factory.py:226/229` (dos canales) | sí (StR6+§0.1) | — |
| C2 | 🔀→09 + CORE-GAP | fs_env (09) · CG-STOR-3 | base | `filesystem.py:14-18` + `tool_use.py:52` (`fs`=ConfinedFilesystem default) 1→EOF | sí (StR7) | — |
| C3 | CORE-GAP | CG-STOR-4 (download_range) | base | `protocol.py:11` (`download` todo-o-nada) 1→EOF | sí (StR8) | — |
| D1 | DEUDA-B + T3-INTEGRADOR | log_key (borrar/cablear) · 00-INTEGRADORES | ambas | `protocol.py:86` + grep-ausencia `log_key`=0 prod | sí (§2.4) | — |
| D2 | BATTERY | battery_outputs (work_key) | base | `protocol.py:79` + `filesystem.py:52-56` (`copy`) + grep-ausencia `work_key`=0 prod | sí (StR8) | persistencia |
| D3 | BATTERY + CLI-ONLY | battery_outputs · 00-INTEGRADORES (REPL) | ambas | tracker-leído | sí (§2.5) | — |
| E1 | BATTERY | battery_config (=A2) | base | tracker-leído (=A2, no re-cuenta remediación) | sí (StR4) | persistencia |
| E2 | T3-INTEGRADOR | 00-INTEGRADORES (18) | integrador | tracker-leído (`WorkerStateUploader.ts` íntegro) | sí (§2.5 OI-E) | — |
| E3 | ⛔→07 | 07·FIND-EVT7 | — | tracker-leído (`sessionState.ts` íntegro→07) | N/A (⛔ satélite) | — |
| F1 | T2-BASE-MECANISMO | storage/factory.py | base | `storage/factory.py` 1→EOF + `factory.py:186` 1→EOF (create+reparto) | sí (§2.1) | — |
| F2 | T1-CONTRATO | StorageKeys + CG-STOR-1 | base | `protocol.py:42-88` 1→EOF + grep-ausencia (6 claves=0 prod, transcript=1) | sí (StR1) | persistencia |
| F3 | T2-COSTURA | StorageProtocol | base | `protocol.py:6-15` + `filesystem.py` 1→EOF (`presign` as_uri) | sí (§2.1) | — |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../15-storage.md`?** → **Sí**, 1→543: §Tesis, tablas A/B/C/D/E/F, §Hallazgos FIND-STOR1-13,
   §Cabos, §Plan StR1-8, §Puerta 6b + ledger + honestidad, §Re-visita COMPLETITUD gate-11 + 4 preguntas + VEREDICTO.
2. **¿Reconcilia el conteo?** findings-grid en `../15-storage.md` = **33**; colocados = **33**; sin colocar = **0**.
   (A1-A8·8 + B1-B13·13 + C1-C3·3 + D1-D3·3 + E1-E3·3 + F1-F3·3 = 33. `FIND-STOR1-13` + `StR1-8` = capa de
   remediación referenciada, no re-contada — patrón 06/10/04. El ⛔ `bootstrap/state.ts` cost/usage→07/16 = nota de
   ledger, no fila-grid.)
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ENSAMBLADOR (sin apoyarse en grep)?** → Tramos ABIERTOS 1→EOF
   EN ESTE CICLO (no heredados del gate-11 2026-07-20):
   - **F1/F3 ✅ · C1 🔀**: `storage/factory.py` 1→33 (`StorageRegistry.create` instancia fresca) + `factory.py`
     **1→267 ÍNTEGRO** (`_build_local:186` crea UNA `storage` y la reparte: `:194→:149-155` `McpProvider(storage=)`,
     `:226` `runtime(storage=)`, `:229` `fs=config.fs` SEPARADO) + `protocol.py` 1→88 + `filesystem.py` 1→71
     (`presign` as_uri, `copy`, `_path` startswith).
   - **B1/B6 🔀 · CG-STOR-2**: `runtime.py` **1→435 ÍNTEGRO** — `_persist:418-432` `upload(transcript_key,
     model_dump_json)` snapshot por completion; `_run_loop:306-416` liga `ctx.presentation/exec_env/git_credentials`
     (317-321) y `ctx.fs` condicional (324-325) pero **NUNCA `ctx.storage`** → `plan_file` inerte; `user_id or "anon"`
     (424) muerto porque `_build_child:209` siempre uuid.
   - **CG-STOR-1 (F2) bug user_id="mcp"**: `provider.py:40-96` 1→EOF (`__init__ user_id="mcp"` default :50;
     `_default_client:87` `StorageBackedTokenStorage(..., user_id=self._user_id)`) + `token_storage.py:22-25` 1→EOF
     (`user_id: str = "mcp"` → `mcp/mcp/<srv>`) + `factory.py:149-155` (McpProvider SIN pasar user_id) → colisión
     confirmada por cableado.
   - **A8 🔀→❌**: `config_store.py` 1→146 ÍNTEGRO (`ScopedMcpConfigStore` merge/precedencia/`assert_mutable` = lo a
     generalizar a `ScopedConfigStore`); **NO auto-cableado** (factory pasa `caps.mcp_config_store` default None).
   - **B8 ❌**: `filesystem.py:42-50` (`list_prefix` devuelve keys crudas relativas, sin meta).
   - **CG-STOR-1 ausencia (la load-bearing)**: **grep-de-ausencia ESTE CICLO** (legítimo para ausencia, L09):
     `config_key`/`agent_md_key`/`ltm_key`/`meta_key`/`work_key`/`log_key` = **0 consumidores prod**; sólo
     `transcript_key` = **1** (`_persist`). `ctx.storage` bound sites en prod = **0** (`plan_file` inerte). Confirmado
     ESTE ciclo por ausencia+lectura, no heredado del doc.
   - **Consumidores de battery no auto-cableados**: `skills/store.py` 1→71 (`StorageBackedSkillStore prefix="skills"`,
     sin scope) + `plan_file.py` 1→108 (`ctx.storage` leído :71/:86) + `tool_use.py` 1→70 (`storage=None`/`fs=
     ConfinedFilesystem` defaults) — todos abiertos 1→EOF.
4. **¿La cara integrador quedó al MISMO detalle que la base?** → **Sí.** OI-STOR-A..F (backend · componer batteries ·
   ligar StorageContract · política scope+trust · transporte upsert · watcher) con capacidad·costura·firma·
   realización(code/assistant)·criterio (§2.5). Cabos 06/04/13/14 cerrados con destino. Ningún "→ integrador" a secas.
5. **¿Doble filo (L10)?** → **Sí, calibrado.** (a) Ningún ❌ disfrazado de 🔀: FIND-STOR1 (taxonomía muerta) +
   bug `"mcp"` son CORE-GAP honestos (CG-STOR-1), no "divergencia". (b) Sin deuda inflada: B5/B6/B7/B9 = 🔀 N/A por
   diseño (el runtime persiste el modelo reconstruido, no el log crudo) — NO se contaron como ❌; el shape opinado =
   batteries (Fase C), no decenas de gaps del base; `log_key` = DEUDA-B, no CORE-GAP; E3/cost-usage → 07/16 (satélite,
   no troceo). El `StorageContract`↔`StorageProtocol` = dos seams por diseño (§0.1), no fusión forzada.

### 3.3 §Honestidad
- **Falsa alarma cazada y corregida DENTRO del ciclo (L00/L11):** mi primer grep de consumidores usó `grep -v
  '/tests/'` sobre rutas SIN `/` inicial (`tests/…`, no `./tests/`) → contó los tests como "consumidores prod" y
  aparentó una divergencia con el tracker (`meta_key:2`, `work_key:3`, etc.). Re-corrido con `grep -Ev '(^|/)tests/'`:
  **6 claves = 0 prod, transcript = 1**. El tracker (2026-07-20) se sostiene; **cero cambios de estado**. Lo dejo
  explícito en vez de esconder el tropiezo — el grep se re-verificó, no se asumió.
- **Leídos 1→EOF EN ESTE CICLO** (L08/L09, no heredados): `storage/protocol.py` (88), `storage/filesystem.py` (71),
  `storage/factory.py` (33), `contracts/storage.py` (40), `factory.py` **ENSAMBLADOR** (267), `execution/local/
  runtime.py` (435), `capabilities/mcp/token_storage.py` (65), `capabilities/mcp/config_store.py` (146),
  `capabilities/mcp/provider.py` (339), `capabilities/skills/store.py` (71), `capabilities/plan/plan_file.py` (108),
  `context/tool_use.py` (70) + grep-de-ausencia de las 7 claves y de `ctx.storage`.
- **Sin costuras latentes NUEVAS** tipo `to_llm`/LAT-EXEC1-2/LAT-HOOK1/LAT-TOOL1/LAT-SIG1: el `"anon"` muerto es
  fallback defensivo inalcanzable (no maquinaria a-medio-cablear) y `ctx.storage`-no-bound es seam de integrador por
  diseño (=`ctx.fs` default `ConfinedFilesystem`). Cero B-orphans nuevos. El `log_key` sin battery-dueño = DEUDA-B a
  decidir en A3.DB (borrar-vs-cablear).
- **NO verificado (honesto):** el diseño fino de `ScopedConfigStore` (generalización de `ScopedMcpConfigStore`) se
  desarrolla al construir `battery_config` (Fase C), no aquí; el fix del `user_id` real del token-storage se cablea en
  **11·mcp** (aquí sólo se ancla CG-STOR-1 cruzando allá); la semántica de permisos de la cascada = **06·GAP-02**
  (aquí sólo la persistencia); el catálogo definitivo de la familia `battery_persistence.*` (¿4 paquetes o 1 con
  submódulos?) lo decide **A3.CAT**. Suite NO re-ejecutada (fase de diseño, sin cambio de código — PLAN §1.6). El
  tracker ya reporta `21 passed / 10 xfailed strict` intactos (los targets StR1-8 siguen rojos = gaps vivos).
- **Corrección de la nota de retoma (no defensiva):** la memoria decía "06·OI-HOOK-C persistir permisos → storage"
  como cabo abierto; se **cierra con destino** en §2.5 (battery_config/meta), NO se deja como pendiente.

### 3.4 VEREDICTO
**✅ NADA PENDIENTE → A3·13·memory.**
Conteo 33=33=0. Las 5 preguntas: sí honestas (Q3 con ensamblador `factory.py`+`runtime.py` 1→EOF ESTE ciclo + grep-de-
ausencia re-corrido; Q5 doble-filo calibrado). CORE-GAPs anclados con destino concreto (CG-STOR-1→StR1+11·mcp,
CG-STOR-2→StR2+02·loop, CG-STOR-3→StR7+13·MEM9, CG-STOR-4→StR8, CG-STOR-5→StR6); batteries `battery_persistence.*`
→A3.CAT; DEUDA-B `log_key`→A3.DB; OI-STOR-A..F→`00-INTEGRADORES`. Ningún pendiente de verificación (L04).
</content>
</invoke>
