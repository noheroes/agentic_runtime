# 00 · INTEGRADORES — contrato base de obligaciones del integrador (lo que SALE del runtime)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/00-INTEGRADORES.md`.
> **ESTADO: SKELETON (creado en A0, definido 2026-07-21).** Secciones **VACÍAS a propósito**.
>
> **Razón de ser (definición del usuario 2026-07-21):** el runtime es **base framework agnóstico/headless**; lo que
> **deliberadamente NO hace** se convierte en **obligación del lado integrador**. El eje PRIMARIO de este doc es ese
> **contrato base común: el "must-be" que TODO integrador agéntico hereda** — los comportamientos base estándar de
> cualquier integrador (atribuir identidad al id opaco, rellenar las costuras, proveer los repos de persistencia,
> aportar capa de interfaz/transporte, componer batteries…). *No* es primordialmente "cosas de agentic_code vs
> agentic_assistant": es lo común a AMBOS por construcción de B.
>
> Las **necesidades específicas** de cada integrador (terminal en `agentic_code`; multi-tenant + front en
> `agentic_assistant`) son la **realización concreta** de esas obligaciones universales — una capa **secundaria**
> encima del contrato común (§2), no el eje principal.
>
> Gemelo de `00-BLUEPRINT.md` (que guía el base/runtime); aquí se guía lo que **todo** integrador debe construir.
> Alimenta las **Fases E (agentic_code)** y **F (agentic_assistant)** del PLAN §5. Se rellena incrementalmente:
> cada `SEPARACION/NN-<sub>.md` vierte su bucket "elementos de integrador" (síntesis §3.2 de `00-LEGEND.md`).
> Consolidación en **A-CIERRE**. Esquema/tiers: `00-LEGEND.md`. **No verter conclusiones no destiladas de un NN** (L00).

---

## 0. Leyenda de estado de llenado
`⬜ vacío (skeleton)` · `🟨 parcial (algún ciclo aportó)` · `✅ consolidado (A-CIERRE)`.

## 0.1 Detalle exigido por obligación (simetría con L05)
Cada obligación se desarrolla con el MISMO rigor que un finding que se queda en el base:
**capacidad observable** (qué debe lograr todo integrador, no la forma) · **origen** (de qué costura del base
delega / qué finding del tracker sale) · **firma que consume** (la interfaz T2/T1-MOTOR del base) · **cableado en el
integrador** (dónde se enchufa) · **orden** (dependencias) · **criterio de aceptación** (observable que lo valida).
Prohibido cerrar una obligación con "→ integrador" a secas.

---

## 1. CONTRATO BASE COMÚN — el "must-be" de TODO integrador agéntico (EJE PRIMARIO)
> Obligaciones universales que salen del runtime agnóstico. Todo integrador MUST cumplirlas para ser un sistema
> agéntico funcional. Cada una con detalle simétrico (§0.1). **Estado: ✅ espina consolidada (A1.7)** — vertidas las
> ~30 obligaciones `OI-*` de los 6 `SEPARACION/{01,16,07,02,05,09}.md`; se amplía en A3.
>
> **Trazabilidad de las obligaciones vertidas (A1.7):** 01→OI-1..5 · 16→OI-M1..M8 · 07→OI-EVT-1..4 · 02→OI-6..10 ·
> 05→OI-11..17 · 09→OI-18..23. Cada `OI-*` conserva su detalle L05 en su `SEPARACION/NN.md §2.5`; aquí se **agrupan por
> obligación universal** (no por categoría). Las costuras `S#` referencian `SEAMS.md`.

### 1.1 Atribución de identidad / sesión (rellenar el seam id-opaco + repo) — 【nido central】
> El runtime lleva ids opacos y NO los interpreta ⇒ todo integrador DEBE atribuir identidad y proveer los repos
> genéricos con su metadata. **Consolida: OI-1 (01) · OI-11 (05, central) · OI-M3 (16).**
- **capacidad:** poseer el grafo de identidad (single-session degenerado o multi-tenant) y hilarlo en un `SessionRepo`;
  el runtime sólo lleva `session.id` opaco y `metadata.user_id` (opaco) al model-call.
- **origen:** `SessionRepo` (05·E30 `SEAMS §S20`) + `TaskRegistry` repo (05·E9 `§S19`) + touchpoints opacos
  (05·E5/E7/E3/E8/E26; 16·B10; 09·G6/E5; 07·B3/K5). **Mímica a ripear:** autogen `sess_…`/`user_…` (05·`_build_child`, 01·CTR-05).
- **firma que consume:** `SessionRepo<TMetadata>` (create/open/list/delete/fork) + `RuntimeSessionProtocol` (lee `.id`) +
  `TaskRegistryProtocol` (scope = metadata) + `metadata` opaco en `StreamOptions` (S1).
- **cableado en el integrador:** implementa el repo con su metadata (cwd degenerado; user/tenant complejo); setea los ids
  antes de `dispatch`; el runtime nunca interpreta la identidad.
- **orden:** **funda el rollup transversal DEUDA-A** (A3.DA) + prerrequisito de persistencia (§1.3) + A2.4/A2.5.
- **aceptación:** el runtime corre un turno **sin conocer userId**; el integrador lista/scopea sesiones por su metadata;
  el complejo particiona affinity por tenant sin que el runtime vea el grafo; el degenerado omite (cero ceremonia).

### 1.2 Cableado de las costuras del motor y del loop
> model-caller → `agentic_models`; façade; input-processor; consumo del stream. Todo integrador DEBE poblarlas.
> **Consolida: OI-M1 (16, must-be) · OI-M2 (16 auth) · OI-2 (01 façade) · OI-5 (01 input) · OI-EVT-1 (07 stream).**
- **capacidad:** sin un `ModelCallerProtocol` cableado el loop **no ejecuta** (`agent_loop.py:181-183` avisa y retorna) ⇒
  todo integrador cablea el caller, puebla la façade `AgentRuntime`, consume el stream ordenado y (opcional) rellena el
  input-processor.
- **origen:** S1 `ModelCallerProtocol` (16·A-block) · S3 `AuthProvider` (16·D2/B17) · S4 `AgentRuntime` (01·CTR-01) ·
  S5 `EventBus`/`stream()` (07·A1/A2) · S11 `UserInputProcessor` (01·CTR-12).
- **firma que consume:** `complete(...)` enriquecido (`SEAMS §S1`) · `credential()` (`§S3`) · `dispatch`/`stream`
  (`§S4`) · `async for ev in runtime.stream(task)` **o** `dispatch(on_event=sink)` (`§S5`) · `process(input,ctx)` (`§S11`).
- **cableado en el integrador:** degenerado usa el **bridge `AgenticModelsCaller`** (battery) + `LocalAgentRuntime` +
  `async for`; complejo (openclaw-like) puede **embeber el motor** y dirigirlo por eventos + façade propia.
- **orden:** prerrequisito de **todo turno** (A2.2). **aceptación:** un turno real texto-solo end-to-end; un slash-command
  (si hay input-processor) corta el turno sin ir al modelo; una request OAuth con token caducado se refresca sin fallar.

> **REFINAMIENTO A2.2 (ganado corriendo un turno OAuth real; cierra el "→ integrador a secas" del punto 4 §3.3).**
> El turno real destapó que la obligación de auth **NO es sólo "proveer una credencial"** (S3 `credential()`): el
> integrador **construye/parametriza el cliente del motor** según el modo de auth, y esa elección tiene consecuencias
> aguas abajo. Desarrollo (6 campos):
> - **comportamiento:** producir requests que el proveedor ACEPTE según el tipo de credencial (api-key vs OAuth-CC).
> - **seam:** S3 `AuthProvider` **ampliada** = credencial **+ modo de construcción del cliente** (`api_key` directo, o
>   cliente pre-construido `options.client`).
> - **firma:** además de `credential() -> Credential`, el integrador decide `client: MotorClient | None` (pre-construido)
>   ó `api_key: str`. El bridge `AgenticModelsCaller(model, *, api_key | client)` recibe una u otra (validado A2.2).
> - **cableado en el integrador (concreto, OAuth-CC):** (1) construir `AsyncAnthropic(auth_token=token)` **sin** `api_key`
>   (con `api_key="dummy"` el sdk 0.109.1 filtra `x-api-key: dummy` ⇒ 401 — HALLAZGO A2.2); (2) `default_headers` con las
>   betas `claude-code-20250219,oauth-2025-04-20` + `user-agent: claude-cli` + `x-app: cli`; (3) **inyectar la identidad
>   "You are Claude Code…" en el system-prompt** (bajo `options.client` el motor no la antepone: `is_oauth=False`); (4)
>   **consecuencia:** `is_oauth=False` desactiva el mapeo `_to_cc_name` de nombres de tool (anthropic.py:200/248/643).
>   **RESUELTO A2.3** (leído `_convert_messages`/`_convert_tools`/emisión 1→EOF + turno real): con `is_oauth=False` los
>   nombres viajan **verbatim** en ambos sentidos (`_to_cc_name`/`_from_cc_name` bypassed) ⇒ una tool de **nombre propio**
>   (no-CC, p.ej. `add_numbers`) round-trippea sin canonicalizar — probado en `skeleton/_tools.py`. La obligación de
>   canonicalizar **sólo** aplica si el integrador/battery expone **builtins de nombre CC** (Bash/Read/…): ahí debe mapear
>   `nombre_propio ⇄ nombre_CC` porque el proveedor podría esperar el canónico. Cara **integrador/battery** (no del base):
>   destino = battery `tools-native`/adaptador CC. No es cabo abierto: es una regla condicional cerrada.
> - **orden:** antes del turno; el refresh es pre-request (S3). **criterio:** turno OAuth real end-to-end (✅ A2.2:
>   `skeleton/_motor.py` texto+Usage; ✅ A2.3: `skeleton/_tools.py` tool round-trip, `claude-haiku-4-5`).
> - **reparto de caras:** la **necesidad** (auth correcto) es universal (OI-M2, aquí); la **identidad-CC** concreta es del
>   integrador CC-like (`agentic_code`) — un integrador con identidad propia (openclaw-like) la sustituye por la suya; el
>   arreglo de raíz de la rama OAuth rota vive en **Fase D** (`agentic_models`), no en el integrador.

### 1.3 Persistencia (repos que el base delega)
> proveer los repos de session/transcript/memoria/storage (el base sólo define la costura). **Consolida: OI-3 (01
> StorageContract) · OI-14 (05 resume) + touchpoints de persistencia de §1.1.**
- **capacidad:** resolver rutas y persistir artefactos (transcript de sesión/subagente, plan, fs, memoria) sobre un
  backend durable; reabrir (resume) un subagente terminado desde su transcript.
- **origen:** S13 `StorageContract` (01·CTR-10, 05·E7, 09·G6, →15) + costura `resume` (05·E26, diferida 11/15).
- **firma que consume:** `StorageContract.real_path/ensure_local/commit` (`SEAMS §S13`) + clave = **repo genérico** sobre
  metadata (transcript_key opaco) + `LocalAgentRuntime.resume(agent_id, message)` + `writeAgentMetadata`.
- **cableado en el integrador:** FS local (degenerado, token≡path) / adaptador MinIO (complejo, token→path por-tenant);
  persiste metadata de agente para resume.
- **orden:** con §1.1 (la clave es id-opaco). **aceptación:** plan_file/fs_env/`_persist` operan sobre el adaptador; una
  regla/transcript sobrevive entre sesiones del mismo scope; un agente terminado retoma desde su transcript persistido.

### 1.4 Capa de interfaz / transporte
> el base es headless ⇒ todo integrador DEBE aportar SU interfaz. Obligación universal; la forma es específica (§2). Por
> **completitud de capacidad, no forma verbatim**. **Consolida: OI-EVT-2 (07 wire) · OI-EVT-3 (07 init) · OI-6 (02
> transcript) · OI-7 (02 observabilidad-queries) · OI-13 (05 notificaciones) · OI-17 (05 progreso-subagente) · OI-22 (09
> render tool) · OI-M4 (16 syscall-prefix) · OI-M5 (16 telemetría) · OI-M7 (16 diag conexión).**
- **capacidad:** consumir el stream de eventos del turno y **renderizarlo, serializarlo y/o persistirlo** — transcript,
  render de tool-use/result, wire `Event→SDKMessage` para transporte remoto, bootstrap de la vista de sesión desde el
  `init`, entrega de notificaciones de background, observabilidad del árbol de queries/subagentes, telemetría/diagnóstico.
- **origen (todos ex-`CLI-ONLY`/costuras de consumo):** S6 wire (07·GAP-EVT5/K4) · `InitEvent` (07·F0) · S12
  presentación (01·CTR-11/09·D9) · S21 `NotificationSink` (05·E5/E19) · EventBus para progreso (05·E11/E25, **NO** el
  `observer/` huérfano) · render tools (09·A17/A18/A19) · atribución/`getCLISyspromptPrefix` (16·A1) · sink de
  observabilidad (16·E) · diagnóstico conexión/SSL (16·C4). Los ex-CLI-ONLY del loop: transcript/replay/`claude ps`
  (02·C6/F5/F13/G6), prompt_suggestion/streamlined (07·C4/F4/K3/J6).
- **firma que consume:** `to_sdk_message(event)->dict` sobre `subscribe_all` (`§S6`) · `InitEvent` · `sanitize_output`
  (`§S12`) · `drain()` + shape XML `<task-notification>` (`§S21`) · suscripción al `EventBus`/stream (07) + ids opacos.
- **cableado en el integrador:** se suscribe al stream y pinta/escribe/serializa; el runtime **no** persiste transcript ni
  renderiza ni se auto-drena. **orden:** tras 07 (stream) + 15 (storage).
- **aceptación:** un turno end-to-end deja transcript reproducible; un cliente remoto reconstruye el stream (init→…→
  result) desde el wire; la vista de sesión se puebla del `init` (no de lectura directa de `ToolUseContext`); un
  subagente background completado notifica al padre en el siguiente límite de turno.

### 1.5 Composición de batteries requeridas
> qué batteries del catálogo son **necesarias** para un agente funcional (vs opcionales). **Consolida: OI-18 (09,
> must-be central) · OI-20 (09 backend shell).**
- **capacidad:** todo integrador **elige y compone** su tool-provider set (qué nativas/MCP/skills registrar + gating por
  flag/env/usuario) y elige el backend de ejecución de shell; el runtime registra TODO incondicionalmente y no gatea.
- **origen:** `create_tools(extras)` + `ToolRegistry` inyectado (09·B1/A5/B5, `SEAMS §S16`) + `ToolExecEnvironment`
  (09·F1/F2/F3, `§S15`). Batteries de la espina: `compaction`/`resilience`/`caching`/`budget`/`commands`/`wire`/
  `structured-output`/`voice`/`result-summary` (`00-BLUEPRINT.md §3`); necesarias vs opcionales se fijan en A3.CAT.
- **RESUELTO por A3.CAT (`BATTERIES.md §1`):** **ninguna battery es obligatoria** — consecuencia directa del criterio
  ejecutable de `18·OI-FAC-1` (*un runtime compuesto sin `battery_mcp` no importa `McpProvider` en ningún punto*). Lo
  obligatorio se desplaza al integrador: **declarar su perfil** y tratar el ensamblado incompleto como fatal
  (`OI-FAC-3`). El catálogo publica **3 perfiles** —`núcleo` (0 batteries) · `estándar-terminal` (`agentic_code`) ·
  `hosted-multi-tenant` (`agentic_assistant`, que **sustituye** hooks-config, persistence.{session_catalog,outputs},
  el `SpeechSink` de voz y el catálogo de agentes)— sobre **33 unidades de composición**. Deuda que esto destapa:
  `PlanModeProvider()` se registra **incondicionalmente** en `factory.py:146` ⇒ `BATTERIES.md §6·CAT-h3`.
- **firma que consume:** `create_tools(extras)` + `registry.register` + `config.exec_env` a la factory.
- **cableado en el integrador:** arma el registry con su selección + construye el backend shell y lo pasa a la factory;
  el runtime lo ensambla en el **pool único** sin conocer la política.
- **orden:** funda A2.1/A2.4. **aceptación:** el runtime corre un turno con el pool que el integrador compuso; ninguna
  tool auto-gatea; un comando corre aislado según la política del integrador.

### 1.6 Política / hooks / gates que el base no hornea
> permisos, aprobación, safety-fs, sinks de hooks — el base define el mecanismo; el integrador aporta la política.
> **Consolida: OI-19 (09 permisos-por-input, universal) · OI-4 (01 permisos scope+modo) · OI-21 (09 roots+safety-fs) ·
> OI-16 (05 handoff) · OI-23 (09 auto-mode).**
- **capacidad:** proveer la política de permisos (modos `default`/`acceptEdits`/`plan`/`bypass`, deny/allow rules, ask/
  HITL de ops destructivas, safety de archivos peligrosos, scope de persistencia de reglas); el runtime sólo **dispara el
  punto** (`PRE_TOOL_USE` vivo) y hace un deny-por-nombre delgado.
- **origen:** S17 `PermissionGate` (09·A6-A9/D3/G8, 02·F2, 01·CTR-07/CTR-08) + hook `PRE_TOOL_USE` (`agent_loop.py:300-313`,
  **seam VIVO**) + safety-fs (09·G8→10·R3) + roots/token→path (09·G6/G9, `§S13`) + handoff-classifier (05·E27) +
  auto-mode (09·A16). **CORE-GAP: `PermissionMode` falta en el contrato** (01·CTR-08/GAP-02); hack `app_state.native["plan_mode"]` = DEUDA-B `B-02`.
- **firma que consume:** hook `PRE_TOOL_USE(tool_name, tool_input, call_id, ctx) -> block|modified_input` (`§S8/§S17`) +
  `check_permissions(input,ctx)` per-tool + `PermissionContext(mode, rules)`.
- **cableado en el integrador:** registra el hook y resuelve allow/ask/deny leyendo `app_state`; muta `app_state.permissions`
  para HITL; persiste el scope de reglas (project/user/local); provee el safety-hook de escritura.
- **orden:** tras §1.5 (tools). **aceptación:** una escritura peligrosa (`.bashrc`) o un input no permitido se deniega **por
  input**, no sólo por nombre; una regla `always_allow` de scope `project` sobrevive entre sesiones del mismo proyecto.

### 1.7 Obligaciones aportadas por los 12 ciclos A3 (vertido del cabo `A3.DA §3`) — ✅ A3.CAT
> §1.1-§1.6 sólo contenían la **espina A1.7** (OI-1..23 · OI-M1..8 · OI-EVT-1..4). Los OI-\* que los 12 ciclos A3
> emitieron en su **§2.5** no estaban vertidos aquí; `A3.DA §3` lo dejó como cabo explícito y **A3.CAT lo cierra**.
> Esto es un **índice consolidado por familia**: el detalle L05 de 6 campos (capacidad · origen · firma · cableado ·
> orden · aceptación) **vive en el `NN-*.md` dueño y no se duplica** — duplicarlo crearía dos verdades.

| familia | ciclo dueño (§2.5) | qué obliga al integrador, en una línea |
|---|---|---|
| `OI-A` … `OI-E` | **03·context** | poblar el contexto que el base no hornea (presentación, estado de ficheros, attachments) |
| `OI-MODE-A` · `OI-MODE-B` | **04·modes** | política de modo/backgrounding **encima** de la primitiva del base (04 no aporta battery). *Swarm = ⛔ fuera de alcance* |
| `OI-HOOK-A` … `OI-HOOK-E` | **06·hooks** | **proveer el `HookRunner`** — `RuntimeConfig.hook_runner=None` por defecto (`factory.py:86`) ⇒ sin él, ninguna battery puede registrar hooks (`18·C2`) |
| `OI-SIG-A/B/C` | **08·signals** | superficie de cancelación/interrupción hacia su UI, sobre la primitiva del base (08 no aporta battery) |
| `OI-fs-safety` · `OI-perm` · `OI-git-cred` · `OI-web-policy` · `OI-naming` · `OI-B` · `OI-lsp` · `OI-cron` · `OI-A` | **10·tools-native** | **las políticas** sobre las tools nativas: safety de escritura, permisos por input, credenciales git, política de dominio/provider web, naming, LSP y cron |
| `OI-MCP-A` … `OI-MCP-I` | **11·cap-mcp** | declarar servidores, scope, stores de config/token y los handlers OAuth interactivos (el runtime headless no abre navegador) |
| `OI-SKILL-A` … `OI-SKILL-H` | **12·cap-skills** | fuentes/precedencia de skills, gate de permisos y **registrar sus propios bundled** (`OI-SKILL-F`: el contenido de producto no es del base) |
| `OI-MEM-A` … `OI-MEM-G` | **13·memory** | raíz/store de memoria, guard-path, y **team-memory como T3** (sync multi-tenant + secret-scan = seam opcional del integrador) |
| `OI-PLAN-A` … `OI-PLAN-D` | **14·plan** | `agent_resolver` que **COMPONE** su catálogo con el de las batteries (`battery_plan.agents(host)`), no lo sustituye |
| `OI-STOR-A` … `OI-STOR-F` | **15·storage** | respaldar `StorageContract`/`StorageProtocol` y poseer el reparto de la familia `battery_persistence.*` que sustituya |
| `OI-VOICE-1` … `OI-VOICE-5` | **17·voice** | inyectar STT/TTS y, en el caso complejo, **sustituir el `SpeechSink`**; `OI-VOICE-2`: sin `PathPresentation` real el invariante de saneo queda vacuo |
| `OI-FAC-1` · `OI-FAC-2` · `OI-FAC-3` | **18·factory** | **componer el runtime** (elegir batteries y config) · **invocar `startup()`/`shutdown()`** (sin ellos hay capabilities registradas y **desconectadas**, sin error visible) · **declarar la completitud del perfil** y tratar el fallo de ensamblado como fatal |

> **Caras-factory con dueño en otra categoría** (`18·§2.5`): `C2` memoria (el compositor registra el hook que
> `battery_memory.hooks(host)` devuelve) · `C3` plan (agentes) · `C4` `RuntimeManifest` para el frame `init` ·
> `C5` `RuntimeHost.scope` (token **opaco**, no `user_id` interpretado — hoy `token_storage` usa `user_id="mcp"` por
> defecto = colisión multi-usuario) · `C6` `WorkerStateUploader` = `agentic_assistant` tras `StorageProtocol`.

---

## 2. REALIZACIONES ESPECÍFICAS POR INTEGRADOR (capa secundaria sobre §1)
> Cómo cada integrador **concreta/extiende** el contrato base. Más delgado que §1. **Estado: ⬜ vacío.**

### 2.1 `agentic_code` (CLc-like) — realización DEGENERADA + terminal — 🟨 sembrado A1.7
> identidad usuario-único/sesión-única (defaults minimal, cero ceremonia); interfaz = terminal; compone muchas batteries. NO es Claude Code.
> **Realización mínima de cada obligación §1** (el "grado cero" que valida que el contrato base es construible):

| obligación §1 | realización degenerada `agentic_code` |
|---|---|
| **1.1 identidad** | `SessionRepo` default **single-session scope-por-cwd**; `TaskRegistry` in-memory; ids opacos autogenerados una vez. Cero multi-tenant. |
| **1.2 motor/loop** | caller = **bridge `AgenticModelsCaller`** (battery); `LocalAgentRuntime` default; consume el stream por `async for`; credencial = `api_key` estático (sin refresh). |
| **1.3 persistencia** | `StorageContract` FS local con **token≡path** (roots = cwd); transcript en disco; resume **opcional**. |
| **1.4 interfaz** | **terminal**: render tool-use/result (React/ink), transcript a terminal, `claude ps`, resumen tool-use; **sin wire** (consume directo, sin BFF-SSE); telemetría mínima/stdout. |
| **1.5 batteries** | compone **muchas** (compaction/resilience/caching/commands/…); backend shell = `LocalExecEnvironment` (host); sin sandbox hosted. |
| **1.6 política** | prompt de **aprobación en terminal** + modos (`plan`/`acceptEdits`); safety-fs local; scope de reglas en disco (project/user/local). |
| **específico** | **force-async OFF** (OI-12); **sin** cap-de-coste (OI-8), **sin** salida estructurada BFF (OI-9), **sin** backend remoto (OI-15), **sin** billing/cuenta (OI-M6), **sin** handoff-classifier (OI-16), **sin** auto-mode (OI-23). |

> Este perfil es el **grado cero** que A2.5 (walking skeleton integrador) ejercita end-to-end: si el contrato base común
> §1 se cumple con estos defaults minimal, la re-arquitectura B es construible por la cara del integrador. Detalle fino
> (costuras exactas, orden de construcción) se cierra en **A-CIERRE / Fase E**.

### 2.2 `agentic_assistant` (openclaw-like) — realización COMPLEJA + front (posterior) — 🟨 específicos identificados A1.7
> identidad multi-tenant/multi-sesión (posee el grafo por fuera; consume por protocolo message/tool/event/stream + motor);
> interfaz = capa front separada (`new_core/frontend`+`bff`+KrakenD+Keycloak+MinIO); compone selectivamente. NO es openclaw.
> **Obligaciones específicas ya identificadas por la espina** (detalle simétrico en su `SEPARACION/NN §2.5`; se desarrolla en A-CIERRE/Fase F):
> **OI-12** force-async ON (un subagente sync atasca el `inputQueue` del daemon, 05·E34) · **OI-8** cap-de-coste por
> request multi-tenant (02·G2) · **OI-9** salida estructurada tipada del BFF (`SyntheticOutputTool`, 02·G3) · **OI-15**
> backend remoto `RemoteAgentRuntime`/CCR (05·E31) · **OI-M6** endpoints cuenta/billing/attachments (bff/KrakenD/Keycloak/
> MinIO, 16·F) · **OI-M8** config transporte/deployment (16·D3) · **OI-EVT-4** capa de cuenta rate-limit/auth/overage
> (07·J1/J2) · `SessionRepo` multi-tenant sobre MinIO (05·E30) · wire SSE multi-tenant + índice de sesiones (07·K5/S6).
_(detalle simétrico completo → A-CIERRE / Fase F)_

---

## 3. Trazabilidad de llenado (bitácora del skeleton)
| sección | se llena en | fuente | estado |
|---|---|---|---|
| 1.x contrato base común | A1.x + A3 (bucket "elementos de integrador") → A-CIERRE | todas las categorías | ✅ espina (A1.7: OI-1..23); resto A3 |
| 1.5 composición de batteries | **A3.CAT** | `BATTERIES.md §1` | ✅ **A3.CAT** — ninguna obligatoria; 3 perfiles sobre 33 unidades |
| 1.7 vertido de los OI-\* de A3 | **A3.CAT** (cabo `A3.DA §3`) | las 12 §2.5 de los ciclos A3 | ✅ **A3.CAT** — índice por familia; detalle L05 en el `NN-*.md` dueño |
| 2.1 agentic_code específico | A1.7 (degenerado) + A-CIERRE | espina + todas | 🟨 grado-cero sembrado (A1.7) |
| 2.2 agentic_assistant específico | A-CIERRE / Fase F | diseño complejo | 🟨 específicos identificados (A1.7) |
