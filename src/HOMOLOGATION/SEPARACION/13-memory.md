# 13 · capabilities/memory — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/13-memory.md`.
> Tracker de origen: `../13-cap-memory.md` (635 LOC, leído ÍNTEGRO 1→EOF este ciclo). Esquema: `00-LEGEND.md §3`.
> PASO 0 (11 lecciones skill) ejecutado. B (5 `memory/*.py`) + ENSAMBLADOR (`factory.py`/`manager.py`/`agent_loop.py`/
> `runtime.py`/`fork/__init__.py`) RE-ABIERTOS 1→EOF EN ESTE CICLO (L09/L11, **NO** heredados de la re-visita gate-11
> del tracker 2026-07-20).

---

## 0. Tesis de separación (Filosofía B)

El tracker ya diagnostica la forma B correcta: la memoria **no es una tool ni una capability seleccionable** — es
**contexto + instrucciones** que se activan en el system prompt y por recall por turno, y el guardado lo hace el
modelo con `write_file` (sin tool `remember`). El runtime porta el **esqueleto honesto de la capa (1)** (auto-memory
del agente principal) y deja el resto por construir. La SEPARACION descompone eso en tres capas:

1. **Base = el MECANISMO de activación + el contrato + el seam del repo.** El `CapabilityProvider` (seam por el que
   la memoria enchufa, home 12/general, NO nuevo de 13) + su agregación per-turno en el manager + su consumo en el
   loop (`system_prompt_sections` loop:213 + `_inject_recall` loop:218) = **T2-BASE-MECANISMO**, COMPARTIDO con
   skills/mcp/plan (no memoria-específico). `MemoryHeader` (name/description/type/path/mtime) = **T1-CONTRATO**.
   `MemoryStore` = **T2-COSTURA, repo PROPIO** (§0.1).
2. **La memoria concreta (memdir) = BATTERY `battery_memory` opcional** que se compone sobre el `CapabilityProvider`
   seam: `FilesystemMemoryStore` (default dev) + `rank_memories`/`RecallStrategy` (recall) + `build_memory_activation`
   (prompt/taxonomía) + `MemoryExtractor` (auto-extracción por fork). Reificar el comportamiento como battery (no como
   maquinaria embebida del base) es el mismo criterio de 06 (`battery_hooks_config`) y 15 (`battery_persistence.*`).
   **Anti-padding L10:** un integrador puede NO querer memoria, o sustituir su implementación — por eso es battery.
   Que la battery esté **a medio construir** (extracción ausente, recall pobre, prompt recortado) = **CORE-GAPs que la
   battery estándar DEBE cerrar** para reproducir la capacidad del canónico (distinto de un shape opcional que nadie
   reclama; aquí el canónico SÍ tiene la capacidad).
3. **El ROOT/backend, el gate, el permiso de escritura, team-memory y la interfaz = integrador.** Quién siembra
   `caps.memory_root`/`memory_store`, el gate enable/disable, la siembra del permiso de escritura memory-scoped, la
   memoria de equipo multi-tenant (`TEAMMEM`), y las afordancias `#`/`/memory` = `00-INTEGRADORES.md`.

**La promesa está a MEDIO CUMPLIR (verificado por cableado este ciclo, no heredado):** el registro condicional del
provider funciona (`factory.py:166-172`, verificado 1→EOF) y el reensamblado per-turno del índice+recall es correcto
(loop:213/218, verificado). Pero la **battery está incompleta**: sin auto-extracción (la mayor brecha, MEM1), recall
sin `recentTools`/`alreadySurfaced`/frescura (MEM2a-c/MEM3), prompt de activación recortado (MEM7a-f), índice sin
truncar (MEM4), scan no-recursivo/sin cap (MEM5), frontmatter anidado sin validar (MEM6), memoria de subagente por
uuid volátil (MEM10), y — **seguridad** — clave de scope **sin sanitizar** (MEM9, traversal).

### 0.1 DESAMBIGUACIÓN load-bearing — la memoria es un REPO PROPIO, NO `StorageProtocol` (confirma 15·§0.2)

Verificado por el ensamblador ESTE ciclo: `factory._build_capability_manager` construye `MemoryProvider(store)`
(**factory.py:172**) donde `store = caps.memory_store` o `FilesystemMemoryStore(caps.memory_root)` (:169-171) —
**NUNCA** el parámetro `storage` (que `_build_local:194` pasa por separado a `McpProvider(storage=)` :152 para
TokenStorage OAuth y a `LocalAgentRuntime(storage=)` :226 para el transcript blob). Son **dos ejes de persistencia
distintos que comparten la nota-identidad `persistencia` pero NO el seam**: transcript → `StorageProtocol` (blob k/v);
memoria → `MemoryStore`/`FilesystemMemoryStore` (repo propio). Esto **confirma exactamente la §0.2 de 15** (persistencia
= multi-repo id-opaco+genérico, NO god-store) — el cabo de 15 a 13 se cierra sin discrepancia.

### 0.2 Eje transversal `persistencia` — id opaco + repo, clave SIN sanitizar (bug de seguridad)

La clave de scope de la memoria es `<user_id>/<agent>` (provider.py:52-63): `user = context.user_id or "anon"`;
`agent = context.agent_id if context.is_subagent else "main"`. Sigue el patrón `id opaco + repo` (el runtime NO
interpreta `user_id`/`agent_id` como identidad, sólo como componentes de clave) **PERO**:
- **MEM9 (seguridad):** los segmentos se unen crudos a `self._root` (store.py:106-110) **sin sanitizar** — un
  `user_id`/`agent_id` con `..` o ruta absoluta escapa del root (`Path / "/etc/…"`). El canónico sanitiza
  (`validateMemoryPath`/`sanitizePath`/team `sanitizePathKey`). Es el **espejo EXACTO de 15·CG-STOR-3**
  (`sanitizePathKey`) → **helper de guard-path UNIFICADO, no duplicado** (CG-MEM-1, keystone).
- **MEM10:** la raíz usa el slot ESTABLE `"main"` (correcto: su `agent_id` es un uuid distinto por despacho), pero el
  subagente se keyea por `context.agent_id` = **uuid volátil fresco por fork** (verificado `fork/__init__.py:69`
  `agent_id = f"agent_{uuid.uuid4().hex[:12]}"` + `_build_child` runtime.py:205) → la memoria del subagente-de-tipo-X
  **NO persiste entre despachos**. El canónico keya por `sanitizeAgentTypeForPath(agentType)` = ESTABLE (CG-MEM-3).

Ambos se consolidan en el rollup `DEUDA-A.md` (nota-identidad `persistencia`), no categoría-a-categoría.

---

## 1. Tabla por finding (grid del tracker · A1-A11 · B1-B13 · C1-C8 · D1-D10 · E1-E10 · F1-F5 = **57 filas**)

> Los findings-resumen `FIND-MEM1..12` = **capa de remediación** que reagrupa celdas del grid (MEM1→E1-E10, MEM2→D2-D6,
> MEM3→D5/D6, MEM4→B2, MEM5→C2-C4, MEM6→B11/C7, MEM7→B3-B10, MEM8→A8, MEM9→A4/A5, MEM10→A9/A10, MEM11→F4, MEM12→A6);
> los `MeR1-13` = §Plan desarrollado (6 campos L05) en el tracker — se **referencian** para la cara-base y se desarrolla
> la cara-integrador simétrica aquí (§2.5). **No se re-cuentan** (patrón 06/10/04/15). §G (deuda transversal), §H
> (session-memory→01), §I (team→integrador) = capas de handoff/cross-ref, no filas-grid (§2 las coloca con destino).

### A · Dónde vive / scoping (`store.py`/`provider._scope` vs `paths.ts`+`agentMemory.ts`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| A1 | Store en disco, sobrevive reinicio, **inyectable** | núcleo | T2-COSTURA + BATTERY | `MemoryStore` (seam propio) · `FilesystemMemoryStore` (default) | persistencia | ✅🔀 seam propio confirmado `factory:172` (≠ StorageProtocol, §0.1); habilita MinIO/multi-user |
| A2 | Auto-memory scopeada por **git-root** (worktrees comparten) | núcleo | 🔀 (nota-id) + BATTERY | `MemoryStore._scope` · política scope=integrador | persistencia | 🔀 **deliberado** L10: runtime scopea por `<user>/<agent>` (multi-tenant); mismo efecto (aislamiento), otro mecanismo — NO gap. Pero **sin sanitizar**=CG-MEM-1 |
| A3 | `getMemoryBaseDir` (env/config-home) + overrides Cowork/settings | núcleo/producto | T3-INTEGRADOR | `00-INTEGRADORES` (OI-MEM-A) | persistencia | 🔀 equivalente por inyección (`caps.memory_root`/`memory_store`, factory:169-171) |
| A4 | **`validateMemoryPath`** (rechaza relativa/root/UNC/drive/null-byte) | núcleo/seguridad | **CORE-GAP** | **CG-MEM-1** (`_safe_segment`, unificado 15·CG-STOR-3) | persistencia | ❌ **FIND-MEM9**: clave cruda → traversal (store:106-110) |
| A5 | `sanitizePath` del git-root para el nombre de carpeta | núcleo | **CORE-GAP** | **CG-MEM-1** | persistencia | ❌ FIND-MEM9 (mismo helper que A4) |
| A6 | **`isAutoMemPath`** → carve-out de escritura (bypassa deny-por-nombre) | núcleo | **CORE-GAP** + T2-COSTURA | **CG-MEM-9** → 06·GAP-02 + 09·fs_env | persistencia | 🟡 **FIND-MEM12**: seam actual `initial_allowed_tools` es COARSE (write global, no path-scoped al memory_dir) |
| A7 | `ensureMemoryDirExists` (mkdir recursivo idempotente) | núcleo | BATTERY | `FilesystemMemoryStore.ensure_dir` | — | ✅ `mkdir(parents, exist_ok)` store:112-115 |
| A8 | `isAutoMemoryEnabled` gate (env/setting/remote-sin-storage) | núcleo | **CORE-GAP** + T3-INTEGRADOR | **CG-MEM-10** (`__init__(enabled=)`) · integrador wire | — | 🟡 **FIND-MEM8**: provider siempre activo (`__init__(store)` sin flag) |
| A9 | Agent-memory por **tipo de agente**, 3 scopes `user\|project\|local` | núcleo | **CORE-GAP** | **CG-MEM-3** (keyed by `agent_type`; cabo→03/05) | persistencia | ❌ **FIND-MEM10**: keyed por `agent_id` uuid volátil (fork:69), no persiste entre despachos |
| A10 | **Snapshot-sync** de agent-memory (compartir por VCS) | núcleo/producto | T3-INTEGRADOR | `00-INTEGRADORES` (OI-MEM-F, diferido) | persistencia | ❌ FIND-MEM10: `agentMemorySnapshot` ausente; el integrador lo añade si comparte por VCS |
| A11 | Daily-log mode `KAIROS` (`logs/YYYY/MM/…`, /dream destila) | núcleo/producto | ⛔→05 | **05·EXEC10** (kairos, modo assistant) | — | ⛔ satélite de otra categoría (L07), nexo 05 |

### B · Índice `MEMORY.md` + activación en system prompt (`prompt.py` vs `memdir.ts`/`memoryTypes.ts`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| B1 | `MEMORY.md` excluido del recall/scan, inyectado como índice | núcleo | T2-BASE-MECANISMO + BATTERY | `system_prompt_section` (loop:213) · `read_index` | — | ✅ scan salta `ENTRYPOINT` (store:130), read_index (117), consumido per-turno |
| B2 | **`truncateEntrypointContent`** (200 líneas Y 25 000 bytes + warning) | núcleo | **CORE-GAP** | **CG-MEM-5** (`_truncate_entrypoint`) | — | ❌ **FIND-MEM4**: `read_index` devuelve crudo (store:117-122) |
| B3 | Guardado en 2 pasos + formato `- [Title](file.md) — hook`, "≤150 chars" | núcleo | BATTERY | **CG-MEM-8** (prompt) | — | 🟡 falta formato exacto + "≤200 se truncan" (prompt:37-42) |
| B4 | Taxonomía tipada detallada (description/when/how/examples/body_structure) | núcleo | **CORE-GAP** | **CG-MEM-8** | — | 🟡 **FIND-MEM7a**: 4 tipos con una línea (prompt:27-33) |
| B5 | `WHAT_NOT_TO_SAVE` + cláusula explicit-save ("aplica aunque el user lo pida") | núcleo | **CORE-GAP** | **CG-MEM-8** | — | 🟡 falta cláusula explicit-save (prompt:34-36) |
| B6 | `WHEN_TO_ACCESS`: **ignore-memory** + **drift caveat** | núcleo | **CORE-GAP** | **CG-MEM-8** | — | ❌ **FIND-MEM7b** |
| B7 | **`TRUSTING_RECALL`** "Before recommending": verificar file/func/flag antes de recomendar | núcleo | **CORE-GAP** | **CG-MEM-8** (nexo frescura CG-MEM-4) | — | ❌ **FIND-MEM7c** (la lección literal del recordatorio de memoria) |
| B8 | "Memory vs Plan/Tasks" | núcleo | **CORE-GAP** | **CG-MEM-8** | — | ❌ FIND-MEM7d |
| B9 | "Searching past context" (grep topic-files + transcript `.jsonl`) | núcleo | **CORE-GAP** | **CG-MEM-8** (+ cabo `transcript_glob` integrador) | — | ❌ FIND-MEM7e |
| B10 | "Build up over time / who the user is"; explicit save/forget inmediato | núcleo | **CORE-GAP** | **CG-MEM-8** | — | ❌ FIND-MEM7f |
| B11 | `MEMORY_FRONTMATTER_EXAMPLE` con `type:` **plano** | núcleo | **CORE-GAP** (T1) | **CG-MEM-7** (flat type + enum) | — | 🔀 **FIND-MEM6**: prompt pide `metadata.type` anidado (prompt:39) |
| B12 | Texto estable entre turnos (cache-friendly), sólo varía con el índice | núcleo | T2-BASE-MECANISMO | `build_memory_activation` | — | ✅ sólo varía con `index_block` (prompt:14-15) |
| B13 | `extraGuidelines` (Cowork memory-policy vía env) | producto | ⛔ | ⛔ (Cowork) | — | ⛔ N/A core |

### C · Scan de cabeceras (`store.scan`/`MemoryHeader` vs `memoryScan.ts`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| C1 | Scan `.md` del dir, excluye `MEMORY.md` | núcleo | BATTERY | `FilesystemMemoryStore.scan` | — | ✅ glob `*.md` salta ENTRYPOINT (store:129-131) |
| C2 | **Recursivo** (`readdir {recursive}`) | núcleo | **CORE-GAP** | **CG-MEM-6** (rglob) | — | 🔀 **FIND-MEM5a**: `glob("*.md")` sólo top-level (store:129) |
| C3 | Lee **sólo 30 líneas** (`FRONTMATTER_MAX_LINES`) vía readFileInRange | núcleo | **CORE-GAP** | **CG-MEM-6** | — | 🟡 **FIND-MEM5b**: `read_text` del fichero ENTERO (store:74) |
| C4 | **Cap `MAX_MEMORY_FILES=200`**, orden **newest-first** por mtime | núcleo | **CORE-GAP** | **CG-MEM-6** | — | 🟡 **FIND-MEM5c/d**: sin cap, `sorted(glob)` por nombre (store:129) |
| C5 | Aislamiento por-ítem (fichero roto no tumba el scan) | núcleo | BATTERY | `_parse_header` try/except | — | ✅ (store:68-91/:132-134) |
| C6 | `MemoryHeader`: filename/mtimeMs/description/type | núcleo | T1-CONTRATO | `MemoryHeader` (+`name`) | — | ✅🔀 (store:19-30; el runtime añade `name` para el ranker) |
| C7 | `parseMemoryType` valida contra el enum de 4 | núcleo | **CORE-GAP** | **CG-MEM-7** | — | 🟡 **FIND-MEM6**: lee `metadata.type` crudo sin validar (store:79-80) |
| C8 | `formatMemoryManifest`: `- [type] filename (ISO-ts): description` | núcleo | **CORE-GAP** | **CG-MEM-4** (manifiesto tipado) | — | 🟡 **FIND-MEM2c**: `_render_recall` sin type/timestamp (provider:31-34) |

### D · Recall (`recall.py`/`provider.active_context` vs `findRelevantMemories.ts`+`memoryAge.ts`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| D1 | Selección de ≤5 memorias relevantes, excluye `MEMORY.md` | núcleo | BATTERY | `rank_memories(limit=5)` | — | ✅ concepto (recall:16-37) |
| D2 | **Selector LLM** (`sideQuery` Sonnet, JSON-schema) | núcleo | BATTERY | `battery_memory` (`RecallStrategy` inyectable) | — | 🔀 **FIND-MEM2** declarado: keyword determinista; LLM=opinión inyectable futura (recall:21-26) |
| D3 | **`recentTools`** filter (no surfacear reference/API-docs de tools en uso) | núcleo | **CORE-GAP** | **CG-MEM-4** | — | ❌ **FIND-MEM2a** |
| D4 | **`alreadySurfaced`** (pre-selección antes del budget de 5) | núcleo | **CORE-GAP** | **CG-MEM-4** | — | 🟡 **FIND-MEM2b**: dedup en loop (loop:121-130), no pre-selección |
| D5 | **Frescura por memoria** (`memoryAge` + "verifica antes de afirmar") | núcleo | **CORE-GAP** | **CG-MEM-4** (nexo drift B7) | — | ❌ **FIND-MEM3**: `_render_recall` sin edad |
| D6 | `mtimeMs` threaded para frescura sin 2º stat | núcleo | **CORE-GAP** | **CG-MEM-4** | — | 🟡 FIND-MEM3: `MemoryHeader.mtime` presente, no usado en el render |
| D7 | Query = último texto real del user, ignorando `<system-reminder>` | núcleo | T2-BASE-MECANISMO | `_last_user_text` | — | ✅ (mejora explícita, provider:15-28) |
| D8 | Recall post-compactación (memorias sobreviven al recorte) | núcleo | T2-BASE-MECANISMO | `_inject_recall` per-turno (loop:218) | — | ✅ **PRECISIÓN**: la equivalencia la da el re-inject per-turno, **NO** `compact_context` (sin consumidor prod, §3.3) |
| D9 | Rendido como `role:"system"`/`user` en `<system-reminder>` | núcleo | T2-BASE-MECANISMO | loop `_as_reminder` | — | ✅🔀 (loop:27-33/:122-130; nexo 07·render) |
| D10 | Telemetría de shape del recall (`logMemoryRecallShape`) | producto | ⛔ | ⛔ (telemetría→16/07) | — | ⛔ N/A core |

### E · Auto-extracción por fork (AUSENTE — `services/extractMemories/*`) — toda la sección = **CG-MEM-2**
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| E1 | **Agente de extracción forkeado** al cierre del query-loop (Stop-hook) | núcleo | **CORE-GAP** | **CG-MEM-2** (`MemoryExtractor` + Stop 06 + fork 05) | — | ❌ **FIND-MEM1** (la mayor brecha) |
| E2 | `createAutoMemCanUseTool` (Read/Grep/Glob; Bash read-only; Write sólo `isAutoMemPath`) | núcleo | **CORE-GAP** | **CG-MEM-2** (usa CG-MEM-1 `is_mem_path` + CG-MEM-9) | — | ❌ **FIND-MEM1b** |
| E3 | **Cursor** `lastMemoryMessageUuid` (+ fallback si compactado) | núcleo | **CORE-GAP** | **CG-MEM-2** | — | ❌ FIND-MEM1c |
| E4 | **Exclusión mutua** `hasMemoryWritesSince` (skip si el agente ya escribió) | núcleo | **CORE-GAP** | **CG-MEM-2** | — | ❌ FIND-MEM1d |
| E5 | **Throttle** cada N turnos (`tengu_bramble_lintel`) | núcleo | **CORE-GAP** | **CG-MEM-2** | — | ❌ FIND-MEM1e |
| E6 | **Coalescing/trailing** (`pendingContext`) | núcleo | **CORE-GAP** | **CG-MEM-2** | — | ❌ FIND-MEM1f |
| E7 | Pre-inyecta manifiesto + prompt `buildExtractAutoOnly/Combined` (misma taxonomía) | núcleo | **CORE-GAP** | **CG-MEM-2** (reusa CG-MEM-8) | — | ❌ FIND-MEM1 |
| E8 | Sólo agente principal, skip-remote, drain-on-shutdown | núcleo | **CORE-GAP** | **CG-MEM-2** (drain→18/factory) | — | ❌ FIND-MEM1g/h |
| E9 | `createMemorySavedMessage` (notificación system al usuario) | núcleo | T2-COSTURA→07 | **07·events** (new_messages) + integrador render | — | ❌ nexo 07 (OI-MEM-G) |
| E10 | `initExtractMemories` estado closure-scoped (inFlight/turnsSince/pending) | núcleo | **CORE-GAP** | **CG-MEM-2** (estado por-sesión) | — | ❌ FIND-MEM1 |

### F · Provider / superficies de activación (`MemoryProvider` vs los seams del canónico)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| F1 | La memoria **no es capability seleccionable** (sin tools) | núcleo | T2-BASE-MECANISMO | `MemoryProvider.tools()==[]` | — | ✅ **tesis correcta**: `catalog()`/`tools()`==`[]` (provider:73-77); manager agrega vacío (manager:50-59) |
| F2 | Activación estable en system prompt (instrucciones+índice) por-scope | núcleo | T2-BASE-MECANISMO | `system_prompt_section` (loop:213) | — | ✅ (provider:79-84; contenido recortado=CG-MEM-8) |
| F3 | `startup` no-op (dir perezoso por turno; multi-tenant) | núcleo | BATTERY | `startup`/`shutdown` no-op | — | ✅🔀 razón multi-tenant (provider:65-71) |
| F4 | Quick-save `#` (input `# text` → guarda) | cáscara-CLI | CLI-ONLY/INTERFAZ | `00-INTEGRADORES` (OI-MEM-E, `UserInputProcessor`) | — | 🟡 **FIND-MEM11**: afordancia de input → integrador |
| F5 | `/memory` slash (editar fichero en editor) | cáscara-CLI | CLI-ONLY/INTERFAZ | `00-INTEGRADORES` (OI-MEM-E) | — | ⛔ UI → integrador |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`MemoryStore`** (T2-COSTURA, home 13, **repo PROPIO**) — dónde vive la memoria + lectura de índice/cabeceras.
  Productor: `MemoryProvider`. Consumidor: `FilesystemMemoryStore` (battery default) o backend inyectado (MinIO).
  Verificado `factory.py:172` (`MemoryProvider(store)`, `store` ≠ el `storage` blob — §0.1).
- **`CapabilityProvider`** (T2-COSTURA, home 12/general, **NO nuevo de 13**) — el seam por el que la memoria enchufa.
  Consumido per-turno por el manager (`system_prompt_sections` manager:81-96 + `active_context` :98-102) + el loop
  (agent_loop:213/218). Verificado 1→EOF este ciclo.
- **guard-path / sanitize de clave** (T2-COSTURA base, **UNIFICADO con 15·CG-STOR-3** `sanitizePathKey`) — CG-MEM-1.
  Productor: util base. Consumidor: `MemoryStore._scope` + `StorageKeys` (15) + el carve-out (CG-MEM-9). Seguridad.
- **carve-out de escritura memory-scoped** (T2-COSTURA) — `is_mem_path` reconocido por `PermissionContext` como
  allow-para-escritura. → **06·GAP-02** (semántica) + **09·fs_env** (confinamiento). CG-MEM-9.
- **`agent_type` en `ToolUseContext`** (T1-CONTRATO, extensión) — cabo a **03·context/05·fork**. Verificado ausente
  hoy (sólo `agent_id`/`is_subagent`/`subagent_depth`, tool_use.py:39-42). Lo requiere CG-MEM-3.
- **`MemoryExtractor`** (seam interno de `battery_memory`) — engancha Stop-hook (06·CG-HOOK-6) + fork (05·EXEC).
  CG-MEM-2.
- **`RecallStrategy`** (seam inyectable de `battery_memory`) — keyword determinista default; LLM = opinión inyectable
  (MEM2/D2). No es CORE-GAP (🔀 declarado).

### 2.2 Batteries que alimenta
- **`battery_memory`** — el comportamiento memdir concreto, componible por AMBOS integradores (catálogo → A3.CAT):
  `FilesystemMemoryStore` (default) + `rank_memories`/`RecallStrategy` (recall, CG-MEM-4) + `build_memory_activation`
  (prompt/taxonomía, CG-MEM-8) + `_truncate_entrypoint` (CG-MEM-5) + scan recursivo/cap (CG-MEM-6) + frontmatter
  plano+enum (CG-MEM-7) + `MemoryExtractor` (auto-extracción, CG-MEM-2). Su incompletitud = los CORE-GAPs §2.3, NO
  decenas de gaps del base (L10: la battery es el paquete a completar, el mecanismo base ya está).
- **team-memory NO es battery base** — es T3-INTEGRADOR (multi-tenant sync); su pieza guard-path pliega en CG-MEM-1,
  su secret-scan = seam OPCIONAL del integrador. → §2.5 (OI-MEM-D) / `00-INTEGRADORES`.

### 2.3 CORE-GAPs (brechas A↔B reales que `battery_memory`+base DEBEN cerrar → rollup `DEUDA-A.md`)
Keystone-first. Los 6 campos L05 ya desarrollados en el tracker (MeR1-12); aquí se anclan con su ID de rollup:
- **CG-MEM-1** (A4/A5, MEM9, **keystone seguridad**) — **sanitizar la clave de scope** (`_safe_segment`/`is_mem_path`).
  Segmentos `<user>/<agent>` unidos crudos → traversal (store:106-110). **UNIFICADO con 15·CG-STOR-3** (`sanitizePathKey`,
  mismo helper guard-path — verificado espejo exacto). **Gatea CG-MEM-2** (canUseTool) y **CG-MEM-9** (carve-out).
  Cruza 15/09/06. Base = MeR9.
- **CG-MEM-2** (E1-E10, MEM1, **la mayor brecha**) — **auto-extracción por fork al cierre del turno**. `MemoryExtractor`
  (battery-internal, estado por-sesión) + Stop-hook (**06·CG-HOOK-6**) + fork perfecto (**05·EXEC**, cache-safe) +
  canUseTool memory-scoped (usa CG-MEM-1 + CG-MEM-9) + cursor/exclusión-mutua/throttle/coalescing/drain (drain→
  **18/factory** shutdown). Sólo agente principal (`ctx.agent_id is None`... = raíz). Best-effort. Base = MeR1/1b.
- **CG-MEM-3** (A9, MEM10) — **agent-memory keyed por TIPO + scopes `user\|project\|local`**. Hoy uuid volátil
  (fork:69) → no persiste. **El tipo YA existe en la frontera** (`RuntimeTask.subagent_type`, `execution/agents.py:26`,
  consumido `runtime.py:342`) pero **NO se hilvana al `ToolUseContext` ni al `_scope`** (`ToolUseContext` sólo tiene
  `agent_id`/`is_subagent`, tool_use.py:39-42, verificado por grep) → el cabo a **03/05** es "propagar el
  `subagent_type` existente al ctx y a la clave de scope", no inventar un campo de cero. Snapshot-sync VCS → integrador
  (OI-MEM-F, ❌ diferido). Base = MeR10.
- **CG-MEM-4** (C8/D3/D4/D5/D6, MEM2a-c+MEM3) — **recall enriquecido**: `recentTools` filter + `alreadySurfaced`
  pre-selección + manifiesto tipado (`[type]` + ISO-ts) + **caveat de frescura** por memoria (edad + "verifica
  code:line antes de afirmar"; nexo drift CG-MEM-8·B7). Base = MeR2/MeR3.
- **CG-MEM-5** (B2, MEM4) — **truncado del índice** `MEMORY.md` (200 líneas / 25 000 bytes, corta en `\n`, warning que
  nombra el cap). Base = MeR4.
- **CG-MEM-6** (C2/C3/C4, MEM5a-d) — **higiene del scan**: recursivo (`rglob`) + lee sólo cabecera (~30 líneas) +
  cap `MAX_MEMORY_FILES=200` + newest-first por mtime. Base = MeR5.
- **CG-MEM-7** (B11/C7, MEM6) — **frontmatter `type:` plano + validación de enum** (`{user,feedback,project,reference}`;
  unknown/legacy→`""`), manteniendo compat con `metadata.type` anidado. Base = MeR6.
- **CG-MEM-8** (B3-B10, MEM7a-f) — **prompt de activación completo**: taxonomía detallada + explicit-save +
  ignore-memory + drift caveat + `TRUSTING_RECALL` ("before recommending" verificar file/func/flag) + Memory-vs-Plan/
  Tasks + searching-past-context (grep topic-files + transcript) + framing "build up over time". Base = MeR7.
- **CG-MEM-9** (A6, MEM12 = **GAP-02**) — **carve-out de escritura memory-scoped** → **06·GAP-02** (semántica) +
  **09·fs_env**. El seam actual `initial_allowed_tools` (runtime.py:214-217, factory.py:98) es **COARSE**: concede
  `write_file` en bloque vía `always_allow_command`, NO path-scoped al `memory_dir`. Remediación: `PermissionContext`
  reconoce `store.is_mem_path` (CG-MEM-1) como allow-para-escritura. Base = MeR12.
- **CG-MEM-10** (A8, MEM8) — **gate enable/disable** (`MemoryProvider.__init__(enabled=Callable)`; desactivado ⇒
  system_prompt_section/active_context vacíos + extractor no corre). El integrador lo cablea (env/setting), la battery
  lo respeta. Base = MeR8.

### 2.4 DEUDA-B (higiene interna — L10, NO A↔B)
- **NINGUNA propia de 13** (anti-padding L10, como 04·modes). Verificado leyendo B 1→EOF:
  - **`compact_context` sin consumidor prod** (provider:97-99, manager:104-108) — **NO es B-orphan nuevo**: es la cara
    aguas-abajo del **motor de compactación NO portado** (01·CompactionProvider / 02·GAP-L4), transversal a TODOS los
    providers (plan/skills/mcp/memory). La equivalencia post-compactación la entrega el re-inject per-turno de
    `active_context` (loop:218), no este hook. Ya implícito en "motor de compactación ausente" (01/02) → **no se
    re-cuenta ni se registra como B-orphan** (L10, precisión heredada del gate-11 del tracker, re-confirmada este
    ciclo por grep: `compact_context` prod-consumers = sólo los agregadores, cero caller de loop/runtime).
  - **`"anon"` en `_scope`** (provider:61, `context.user_id or "anon"`) — **reachable** legítimamente cuando `user_id`
    es None (standalone sin identidad sembrada); NO muerto, NO defensivo-inalcanzable. (Contrasta con el `"anon"` de
    `runtime._persist:424`, ése sí inalcanzable — pero ése es de 15, no de 13.)
  - Cero costuras latentes NUEVAS tipo `to_llm`/LAT-*.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05/§1.1)

**Must-be universal (CONTRATO BASE COMÚN — obligación de TODO integrador con memoria):**
- **OI-MEM-A · Proveer el ROOT/backend del store de memoria.** Capacidad: dónde viven las memorias (dev=FS, prod=
  MinIO). Costura: `RuntimeConfig.capabilities.{memory_root, memory_store}` → registro condicional `factory:166-172`.
  Firma: `Path` (default `FilesystemMemoryStore`) o un `MemoryStore` inyectado. Realización: agentic_code = FS local
  scopeado (equivalente al git-root del canónico); agentic_assistant = backend por `user_id` (multi-tenant). Criterio:
  `system_prompt_section` lee el índice del scope correcto y el recall lo scopea por usuario. (A1/A3.)
- **OI-MEM-B · Sembrar el permiso de escritura memory-scoped.** Capacidad: el modelo puede `write_file` en el
  `memory_dir` sin que el gate deny-por-nombre lo bloquee. Costura: `RuntimeConfig.initial_allowed_tools` (hoy COARSE)
  → refinar a `PermissionContext` que reconoce `store.is_mem_path` (CG-MEM-9). Firma: MeR12. Realización: agentic_code
  = carve-out local; agentic_assistant = política per-tenant. Criterio: `test_model_can_write_memory_dir` +
  `_cannot_write_outside`. **La memoria NO se auto-concede el permiso** — es decisión del integrador (verificado
  comentario factory.py:95-98). (A6, cruza 06·GAP-02 semántica + 09·fs_env.)
- **OI-MEM-C · Cablear el gate enable/disable.** Capacidad: activar/desactivar la memoria por deployment/usuario.
  Costura: `MemoryProvider(enabled=Callable)` (CG-MEM-10). Realización: agentic_code = env `DISABLE_AUTO_MEMORY`;
  agentic_assistant = setting per-user. Criterio: `test_disabled_provider_no_prompt_no_recall`. (A8, MEM8.)

**Específicos (realización concreta de un integrador):**
- **OI-MEM-D · Team-memory** (§I del tracker, `TEAMMEM`) — T3-INTEGRADOR, inherentemente multi-tenant/backend.
  Capacidad: memoria de equipo sincronizada al servidor por-repo. Costura+firma (detalle simétrico): sync server-backed
  (`GET/PUT /team_memory?repo=`, ETag/304, per-key `entryChecksums sha256`, **delta upload**, **412 conflict**
  probe→recompute→retry local-wins, batching `MAX_PUT_BODY_BYTES` bin-packing, aprendizaje `max_entries` desde 413) +
  watcher (`fs.watch recursive` debounced 2s → push, pull inicial, sólo github.com, flush en shutdown) + **secret-scan**
  (reglas gitleaks, `scanForSecrets`/`redactSecrets`, guard en `validateInput` que **bloquea** escribir secretos =
  **seam OPCIONAL del base** si el integrador comparte) + paths (`sanitizePathKey`/`realpathDeepestExisting`/
  `validateTeamMemKey` — su guard-path **pliega en CG-MEM-1**). Realización: ⛔ N/A agentic_code (single-user);
  agentic_assistant = el sistema completo. Criterio: dos clientes convergen sin filtrar secretos ni escapar del prefijo
  de repo. (§I.)
- **OI-MEM-E · Afordancias de interfaz** — quick-save `#` (F4, `input "# text"` → dispara un guardado sobre ese texto,
  posible `UserInputProcessor`) + `/memory` slash (F5, editar fichero en editor). Realización: agentic_code = terminal;
  agentic_assistant = capa front. Criterio: `# hecho` persiste una memoria; `/memory` abre el editor. (F4/F5, MEM11.)
- **OI-MEM-F · Snapshot-sync VCS de agent-memory** (A10) — compartir la memoria de un agent-type por control de
  versiones (`agentMemorySnapshot`: project-snapshot→local, `.snapshot-synced.json`, init/replace/mark). Diferido; el
  integrador que ofrezca subagentes con memoria compartida lo añade sobre CG-MEM-3. Realización: agentic_assistant si
  aplica. Criterio: la memoria de agent-type X es idéntica tras `git pull`.
- **OI-MEM-G · Render de la notificación memory-saved** (E9, `createMemorySavedMessage`) → **07·events** new_messages:
  un system message tras guardar. Realización: integrador con superficie de mensajería. Criterio: el usuario ve "memoria
  guardada". (E9.)

**Cabos que aterrizan aquí (cerrados con destino):**
- **15·CG-STOR-3 (`sanitizePathKey`)** → **UNIFICADO con CG-MEM-1** (mismo helper guard-path, espejo exacto verificado).
- **15·§0.2 (memoria = repo propio, no `StorageProtocol`)** → **confirmado este ciclo** (factory:172 ≠ storage, §0.1).
- **06·OI-HOOK-C (persistir permisos)** — no es de 13; la persistencia = 15·battery_config, la semántica del carve-out
  de memoria = CG-MEM-9→06·GAP-02. Cruce, no re-desarrollo.
- **§H session-memory** → **01/compact** (satélite de otra categoría, L07 fuera-de-alcance-con-destino;
  `trySessionMemoryCompaction`/`calculateMessagesToKeepIndex`/`adjustIndexToPreserveAPIInvariants`).
- **FIND-SKILL14 (ranking por uso)** → **NO aterriza** (el recall de memoria no usa señal de uso — ni runtime ni
  canónico; verificado en el gate-11 del tracker). Cabo cerrado sin finding.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor:** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda;
ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar
—o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (57 = A1-A11·11 + B1-B13·13 + C1-C8·8 + D1-D10·10 + E1-E10·10 + F1-F5·5)
| ID | TIER | destino | cara | evidencia | detalle | nota-id |
|---|---|---|---|---|---|---|
| A1 | T2-COSTURA + BATTERY | MemoryStore · FilesystemMemoryStore | base | `store.py` 1→EOF + `factory.py:166-172` 1→EOF (registro condicional, store≠storage) | sí (§2.1/§2.5 OI-A) | persistencia |
| A2 | 🔀 + BATTERY | MemoryStore._scope · scope=integrador | ambas | `provider.py:52-63` 1→EOF (`<user>/<agent>`, `main` estable) | sí (L10 + CG-MEM-1) | persistencia |
| A3 | T3-INTEGRADOR | 00-INTEGRADORES (OI-A) | integrador | `factory.py:48-51/169-171` 1→EOF | sí (§2.5 OI-A) | persistencia |
| A4 | CORE-GAP | CG-MEM-1 (unificado 15·CG-STOR-3) | base | `store.py:106-110` 1→EOF (crudo) + grep-ausencia sanitize=0 | sí (MeR9) | persistencia |
| A5 | CORE-GAP | CG-MEM-1 | base | =A4 (mismo helper) | sí (MeR9) | persistencia |
| A6 | CORE-GAP + T2-COSTURA | CG-MEM-9 → 06·GAP-02 + 09 | base+integrador | `runtime.py:214-217` 1→EOF (`initial_allowed_tools` coarse) + `factory.py:95-98` | sí (MeR12) | persistencia |
| A7 | BATTERY | FilesystemMemoryStore.ensure_dir | base | `store.py:112-115` 1→EOF | sí (§2.2) | — |
| A8 | CORE-GAP + T3-INTEGRADOR | CG-MEM-10 · integrador wire | ambas | `provider.py:49-50` (`__init__(store)` sin flag) | sí (MeR8+§2.5 OI-C) | — |
| A9 | CORE-GAP | CG-MEM-3 (cabo agent_type→03/05) | base | `fork/__init__.py:69` + `runtime.py:205` 1→EOF (uuid) + `tool_use.py:39-42` (sin agent_type) | sí (MeR10) | persistencia |
| A10 | T3-INTEGRADOR | 00-INTEGRADORES (OI-F) | integrador | tracker-leído (agentMemorySnapshot) | sí (§2.5 OI-F) | persistencia |
| A11 | ⛔→05 | 05·EXEC10 (kairos) | — | tracker-leído (satélite L07) | N/A (⛔) | — |
| B1 | T2-BASE-MECANISMO + BATTERY | system_prompt_section (loop:213) · read_index | base | `store.py:117-122/:130` + `agent_loop.py:212-213` 1→EOF | sí (§2.1) | — |
| B2 | CORE-GAP | CG-MEM-5 | base | `store.py:117-122` 1→EOF (crudo) | sí (MeR4) | — |
| B3 | BATTERY | CG-MEM-8 (prompt) | base | `prompt.py:37-42` 1→EOF | sí (MeR7) | — |
| B4 | CORE-GAP | CG-MEM-8 | base | `prompt.py:27-33` 1→EOF | sí (MeR7) | — |
| B5 | CORE-GAP | CG-MEM-8 | base | `prompt.py:34-36` 1→EOF | sí (MeR7) | — |
| B6 | CORE-GAP | CG-MEM-8 | base | `prompt.py:22-26` 1→EOF (sin ignore/drift) | sí (MeR7) | — |
| B7 | CORE-GAP | CG-MEM-8 (nexo CG-MEM-4) | base | `prompt.py` 1→EOF (sin TRUSTING_RECALL) | sí (MeR7) | — |
| B8 | CORE-GAP | CG-MEM-8 | base | `prompt.py` 1→EOF (ausente) | sí (MeR7) | — |
| B9 | CORE-GAP | CG-MEM-8 (+cabo transcript_glob) | base+integrador | `prompt.py` 1→EOF (ausente) | sí (MeR7) | — |
| B10 | CORE-GAP | CG-MEM-8 | base | `prompt.py` 1→EOF (ausente) | sí (MeR7) | — |
| B11 | CORE-GAP (T1) | CG-MEM-7 | base | `prompt.py:39` (`metadata.type` anidado) 1→EOF | sí (MeR6) | — |
| B12 | T2-BASE-MECANISMO | build_memory_activation | base | `prompt.py:14-15` 1→EOF | sí (§2.1) | — |
| B13 | ⛔ | ⛔ (Cowork) | — | tracker-leído | N/A (⛔) | — |
| C1 | BATTERY | FilesystemMemoryStore.scan | base | `store.py:124-135` 1→EOF | sí (§2.2) | — |
| C2 | CORE-GAP | CG-MEM-6 | base | `store.py:129` (`glob` top-level) 1→EOF | sí (MeR5) | — |
| C3 | CORE-GAP | CG-MEM-6 | base | `store.py:74` (fichero entero) 1→EOF | sí (MeR5) | — |
| C4 | CORE-GAP | CG-MEM-6 | base | `store.py:129` (`sorted` por nombre, sin cap) 1→EOF | sí (MeR5) | — |
| C5 | BATTERY | _parse_header try/except | base | `store.py:68-91/:132-134` 1→EOF | sí (§2.2) | — |
| C6 | T1-CONTRATO | MemoryHeader | base | `store.py:19-30` 1→EOF | sí (§2.1) | — |
| C7 | CORE-GAP | CG-MEM-7 | base | `store.py:79-80` (metadata.type sin validar) 1→EOF | sí (MeR6) | — |
| C8 | CORE-GAP | CG-MEM-4 | base | `provider.py:31-34` (`_render_recall` sin type/ts) 1→EOF | sí (MeR2) | — |
| D1 | BATTERY | rank_memories(limit=5) | base | `recall.py:16-37` 1→EOF | sí (§2.2) | — |
| D2 | BATTERY | battery_memory (RecallStrategy) | base | `recall.py:21-37` 1→EOF (keyword+mtime) | sí (🔀 declarado) | — |
| D3 | CORE-GAP | CG-MEM-4 | base | `recall.py` 1→EOF (sin recent_tools) | sí (MeR2) | — |
| D4 | CORE-GAP | CG-MEM-4 | base | `agent_loop.py:121-130` 1→EOF (dedup en loop) | sí (MeR2) | — |
| D5 | CORE-GAP | CG-MEM-4 (nexo B7) | base | `provider.py:31-34`/`recall.py` 1→EOF (sin edad) | sí (MeR3) | — |
| D6 | CORE-GAP | CG-MEM-4 | base | `store.py:30` (mtime presente) + `provider.py:34` (no usado) | sí (MeR3) | — |
| D7 | T2-BASE-MECANISMO | _last_user_text | base | `provider.py:15-28` 1→EOF | sí (mejora) | — |
| D8 | T2-BASE-MECANISMO | _inject_recall per-turno (loop:218) | base | `agent_loop.py:112-130/:218` 1→EOF + grep `compact_context` prod=0 | sí (PRECISIÓN §3.3) | — |
| D9 | T2-BASE-MECANISMO | loop `_as_reminder` (nexo 07) | base | `agent_loop.py:27-33/:122-130` 1→EOF | sí (§2.1) | — |
| D10 | ⛔ | ⛔ (telemetría→16/07) | — | tracker-leído | N/A (⛔) | — |
| E1 | CORE-GAP | CG-MEM-2 (extractor+Stop 06+fork 05) | base | grep-ausencia `MemoryExtractor`=0 prod (este ciclo) | sí (MeR1) | — |
| E2 | CORE-GAP | CG-MEM-2 (usa CG-MEM-1+9) | base | grep-ausencia (canUseTool memory-scoped=0) | sí (MeR1b) | — |
| E3 | CORE-GAP | CG-MEM-2 | base | grep-ausencia (cursor=0) | sí (MeR1) | — |
| E4 | CORE-GAP | CG-MEM-2 | base | grep-ausencia (hasMemoryWritesSince=0) | sí (MeR1) | — |
| E5 | CORE-GAP | CG-MEM-2 | base | grep-ausencia (throttle=0) | sí (MeR1) | — |
| E6 | CORE-GAP | CG-MEM-2 | base | grep-ausencia (coalescing=0) | sí (MeR1) | — |
| E7 | CORE-GAP | CG-MEM-2 (reusa CG-MEM-8) | base | tracker-leído (prompts.ts 1→EOF gate-11) | sí (MeR1) | — |
| E8 | CORE-GAP | CG-MEM-2 (drain→18) | base | grep-ausencia (drain=0) | sí (MeR1) | — |
| E9 | T2-COSTURA→07 | 07·events (new_messages) | base+integrador | tracker-leído; nexo 07 | sí (§2.5 OI-G) | — |
| E10 | CORE-GAP | CG-MEM-2 (estado por-sesión) | base | grep-ausencia (initExtractMemories=0) | sí (MeR1) | — |
| F1 | T2-BASE-MECANISMO | MemoryProvider.tools()==[] | base | `provider.py:73-77` + `manager.py:50-59` 1→EOF | sí (tesis §0) | — |
| F2 | T2-BASE-MECANISMO | system_prompt_section (loop:213) | base | `provider.py:79-84` + `agent_loop.py:212-213` 1→EOF | sí (§2.1) | — |
| F3 | BATTERY | startup/shutdown no-op | base | `provider.py:65-71` 1→EOF | sí (§2.2) | — |
| F4 | CLI-ONLY/INTERFAZ | 00-INTEGRADORES (OI-E) | integrador | tracker-leído (UserMemoryInputMessage) | sí (§2.5 OI-E) | — |
| F5 | CLI-ONLY/INTERFAZ | 00-INTEGRADORES (OI-E) | integrador | tracker-leído (`/memory` UI) | sí (§2.5 OI-E) | — |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../13-cap-memory.md`?** → **Sí**, 1→635: §Estado/alcance, §Fuera-de-alcance (session→01/team→
   integrador/⛔ UI), §Tesis (4 capas), tablas A/B/C/D/E/F/G, §H session-memory, §I team-memory, §Hallazgos FIND-MEM1-12,
   §Recuento, §Ledger de archivos (26 canónico + 5 runtime), §Plan MeR1-13, §Nota metodológica, §Re-audit 2026-07-14,
   §Re-visita COMPLETITUD gate-11 + mini-ledger + honestidad + 4 preguntas + VEREDICTO.
2. **¿Reconcilia el conteo?** findings-grid en `../13-cap-memory.md` = **57**; colocados = **57**; sin colocar = **0**.
   (A1-A11·11 + B1-B13·13 + C1-C8·8 + D1-D10·10 + E1-E10·10 + F1-F5·5 = 57. `FIND-MEM1-12` + `MeR1-13` = capa de
   remediación referenciada, no re-contada — patrón 06/10/04/15. §G transversal = cross-ref de A4-A6/E9; §H session→01
   + §I team→integrador = handoff-con-destino, colocados en §2.5, no filas-grid.)
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ENSAMBLADOR (sin apoyarse en grep)?** → Tramos ABIERTOS 1→EOF
   EN ESTE CICLO (no heredados del gate-11 2026-07-20):
   - **A1 ✅🔀 (registro condicional, memoria=repo propio)**: `factory.py` **1→267 ÍNTEGRO** — `_build_capability_manager:
     166-172` registra `MemoryProvider(store)` sólo si `memory_store/memory_root`; `store` = `caps.memory_store` o
     `FilesystemMemoryStore(memory_root)`, **NUNCA** el `storage` param (:194→:152 McpProvider, :226 runtime) → memoria
     = seam propio (§0.1, cierra cabo 15·§0.2).
   - **B1/B12/F1/F2 ✅ (consumo per-turno + provider-sin-tools)**: `agent_loop.py` **1→352 ÍNTEGRO** — `_build_tool_pool:
     85-97` (memoria `tools()==[]` no toca el pool), `system_prompt_sections:212-213` + `_inject_recall:218` DENTRO del
     `for _turn in range(_MAX_TURNS):185` → índice re-leído per-turno; `_as_reminder:27-33` + dedup :121-130. +
     `manager.py` **1→111 ÍNTEGRO** (agregación `system_prompt_sections:81-96`/`active_context:98-102`/`tools:50-59`
     dedup).
   - **A2/A9/D8 (scope, MEM10, post-compact)**: `runtime.py` **1→435 ÍNTEGRO** — `_build_child:198-218` mintea
     `agent_id=agent_<uuid>`(:205) + persiste bajo `"main"` estable para raíz (:427); `_run_loop:306-416` liga
     ctx.presentation/exec_env/fs pero cero ctx.memory; `initial_allowed_tools:214-217` (carve-out coarse, A6). +
     `fork/__init__.py` **1→96 ÍNTEGRO** — `fork:69` `agent_id=agent_<uuid>` FRESCO por despacho (MEM10).
   - **D8 PRECISIÓN (`compact_context` sin consumidor)**: **grep-de-ausencia ESTE CICLO** (legítimo para ausencia, L09):
     `compact_context` prod-consumers = sólo agregadores (`manager.py:104`, `contracts/compaction.py:23`) + defs de
     provider; **cero** caller de loop/runtime → la equivalencia post-compact la da `_inject_recall` per-turno, no el
     hook (confirmado leyendo el loop 1→EOF, no por tabla).
   - **CG-MEM-2/9 ausencia (load-bearing)**: **grep-de-ausencia POR-TÉRMINO ESTE CICLO** (8 greps individuales, no
     inferencia del conjunto): `MemoryExtractor`=0 · `cursor`=0 · `hasMemoryWritesSince/writes_since`=0 · `throttle/
     turns_since`=0 · `coalesc/trailing/pending`=0 · `initExtract/_in_progress/_inflight`=0 · `canUseTool/
     memory_scoped`=0 · `extractor`=0 (todos prod, `-Ev '(^|/)tests/'`); `sanitize`/`_safe_segment`/`validate.*path`
     en memory/storage = **0**. Confirmado por ausencia+lectura, no heredado del doc.
4. **¿La cara integrador quedó al MISMO detalle que la base?** → **Sí.** OI-MEM-A..G (root/backend · permiso
   memory-scoped · gate enable · team-memory [sync/watcher/secret-scan/paths, detalle simétrico] · afordancias `#`//memory ·
   snapshot-VCS · notificación) con capacidad·costura·firma·realización(code/assistant)·criterio (§2.5). Cabos 15/06/
   01/05 cerrados con destino. Ningún "→ integrador" a secas.
5. **¿Doble filo (L10)?** → **Sí, calibrado.** (a) Ningún ❌ disfrazado de 🔀: MEM1 (extracción, ❌ mayor)/MEM9
   (traversal, ❌ seguridad)/MEM10 (uuid, ❌) son CORE-GAP honestos, no "divergencia". (b) Sin deuda inflada: el
   scoping `<user>/<agent>` vs git-root = 🔀 **deliberado** (multi-tenant, mismo efecto de aislamiento) — NO ❌; el
   recall keyword vs LLM = 🔀 declarado (LLM=RecallStrategy inyectable); team-memory = T3-INTEGRADOR (multi-tenant), no
   se cuenta como deuda del base; `compact_context` = cara del ❌ de compactación YA conocido (01/02), NO B-orphan
   nuevo; session-memory→01, KAIROS→05, `/memory`+RAM-monitor = ⛔ (satélite/UI/falso-positivo, no troceo). Cero
   DEUDA-B propia (como 04).

### 3.3 §Honestidad
- **Leídos 1→EOF EN ESTE CICLO** (L08/L09, no heredados del gate-11): `capabilities/memory/{store.py 138, provider.py
  102, recall.py 40, prompt.py 48, __init__.py 19}`; **ENSAMBLADOR**: `factory.py` (267), `capabilities/manager.py`
  (111), `loop/agent_loop.py` (352), `execution/local/runtime.py` (435), `execution/fork/__init__.py` (96) + grep-de-
  ausencia (`MemoryExtractor`/canUseTool-memory-scoped/`ctx.agent_type`/sanitize = 0; `compact_context` prod-consumer =
  sólo agregadores).
- **A canónico NO re-leído esta ronda** (honesto): el tracker documenta la re-lectura 1→EOF de los 10 archivos A
  in-scope en su gate-11 (2026-07-20) + re-audit 2026-07-14 (con auto-corrección adversarial); esta SEPARACION es
  MEJORA DE FORMA sobre findings ya establecidos, no una 3ª validación A↔B. La re-verificación de este ciclo se centró
  en **B + ENSAMBLADOR** (donde vive la clasificación TIER/destino/cableado, que es lo nuevo de la SEPARACION).
- **Cero costuras latentes NUEVAS** tipo LAT-*: `compact_context`-sin-consumidor es cara del motor de compactación
  ausente (01/02, transversal), no B-orphan; `"anon"` de `provider:61` es reachable legítimo (≠ el `"anon"` muerto de
  15·runtime). Cero DEUDA-B propia de 13 (anti-padding L10).
- **NO verificado (honesto):** el diseño fino de `MemoryExtractor` (cursor/coalescing) + el enganche Stop-hook se
  desarrollan al construir `battery_memory` (Fase C) sobre 05·fork + 06·CG-HOOK-6; el `ctx.agent_type` para CG-MEM-3
  se cablea en **03·context/05·fork** (aquí sólo se ancla el cabo, verificado ausente hoy); la semántica del carve-out
  = **06·GAP-02** (aquí sólo la persistencia/path-scope); el helper unificado guard-path lo comparte **15·CG-STOR-3**;
  el catálogo definitivo `battery_memory` (¿1 paquete o submódulos recall/extract/prompt?) → **A3.CAT**. Suite NO
  re-ejecutada (fase de diseño, sin cambio de código — PLAN §1.6; el tracker reporta 18 passed intactos, targets
  MeR xfail siguen rojos = gaps vivos).

### 3.4 VEREDICTO
**✅ NADA PENDIENTE → A3·12·skills.**
Conteo 57=57=0. Las 5 preguntas: sí honestas (Q3 con ENSAMBLADOR `factory`/`manager`/`agent_loop`/`runtime`/`fork`
1→EOF ESTE ciclo + grep-de-ausencia; Q5 doble-filo calibrado). CORE-GAPs anclados con destino: CG-MEM-1 (seguridad,
**unificado 15·CG-STOR-3**)→MeR9+15/09/06 · CG-MEM-2 (mayor brecha)→MeR1+05/06/18 · CG-MEM-3→MeR10+03/05 · CG-MEM-4→
MeR2/3 · CG-MEM-5→MeR4 · CG-MEM-6→MeR5 · CG-MEM-7→MeR6 · CG-MEM-8→MeR7 · CG-MEM-9 (=GAP-02)→MeR12+06/09 · CG-MEM-10→
MeR8. Battery `battery_memory`→A3.CAT; DEUDA-B propia = ninguna (L10); OI-MEM-A..G→`00-INTEGRADORES`. Cabos 15·§0.2
(repo propio) + 15·CG-STOR-3 (guard unificado) cerrados/confirmados; session→01, team→integrador, FIND-SKILL14 no-aterriza.
Ningún pendiente de verificación (L04).
