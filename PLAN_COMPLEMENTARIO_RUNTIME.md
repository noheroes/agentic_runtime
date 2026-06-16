# Plan Complementario — Enmienda del Runtime Agentico y Models

Estado general: `[ ] no iniciado` `[~] en progreso` `[x] completado`
Estado actual: `[ ] no iniciado`

Complementa `PLAN_RUNTIME_AGENTICO.md`. Ese plan marca todo `[x] completado`; la
auditoría 2026-06-13 (ver más abajo) demuestra que **no lo está**. Este plan enmienda
las dos brechas reales: el runtime no está integrado ni desacoplado, y `agentic_models`
no tiene verificación de providers.

No reescribe lo que ya funciona. No re-litiga decisiones. Cada fase tiene criterio de
cierre verificable por comando. **No mezclar fases.**

---

## 1. Hallazgos verificados (línea base de la auditoría)

Evidencia recogida el 2026-06-13, reproducible:

**agentic_runtime**
- Suite: `162 passed, 3 failed, 1 collection error` (no los "511 passed" del plan — esos
  eran de la ubicación vieja bajo `agent_core/`, pre-move).
- Falsa completitud: las primitivas de Fases 9-20 (`signals`, `modes`, `storage`,
  `tools/dispatcher`, `capabilities/resolver`, `events`, `models/caller`, `loop/agent_loop`,
  `factory`) pasan unitarios **en aislamiento** pero **no están integradas**.
- `factory.py:93` cuelga las primitivas como **atributos muertos** sobre un
  `LocalAgentRuntime` que sigue corriendo el `LoopFactory` viejo de `agent_core`.
- `execution/local/runtime.py`, `execution/local/notification.py`, `contracts/runtime.py`
  importan `agent_core.*` (Session, TaskRegistry, HookBus, SessionStore, display_types,
  config, models.events). **El desacople, objetivo central del plan original, no existe.**
- El único cableado real de las primitivas nuevas vive en `scripts/e2e_runtime_test.py`
  (a mano), no en `create_runtime()`.
- Tests rotos por el move de Fase 8: `test_background_notification_channel.py`
  (importa `agentic_runtime.notification`, inexistente) y `test_fork_skill.py` (3 fallos:
  importa `agentic_runtime.local` y `agent_core.skills.executor`).

**agentic_models**
- Port fiel de `pi/packages/ai`. Catálogo (939 modelos), registry y costeo: sólidos y
  probados. 9 providers registrados en `register_builtins()`. Sin falsa completitud.
- `types.py` hace shadow del stdlib `types`: `pytest` desde el paquete revienta en
  `import enum`. Como dependencia instalada importa OK.
- **Cero tests de providers**: ~4.900 LOC de traducción de APIs sin un solo test.
- `faux.py` (492 LOC) es infraestructura de test muerta — no registrada, no usada.
- `AgenticModelsCaller` (`agentic_runtime/models/caller.py:114`) ignora `model_id` por
  request — el modelo queda fijo en el constructor.

---

## 2. Decisiones ya tomadas (usuario, 2026-06-13)

- **D1.** Reescribir `LocalAgentRuntime` sobre `AgentLoop` — desacople total de
  `agent_core` en la capa de ejecución. [Aprobado explícitamente — cumple Regla 4.]
- **D2.** Auditar `agentic_models` a fondo antes de planificar. [Hecho.]
- **D3.** Construir `LocalAgentRuntime` **de cero** sobre las primitivas nuevas, no
  refactorizar el actual incrementalmente. El actual (`execution/local/runtime.py`) queda
  como **referencia de comportamiento** hasta lograr paridad; luego se elimina. Razón: su
  acople a `agent_core` es total y la red de tests que justificaría un strangler (tests de
  integración con `agent_core`) se excluye del paquete standalone en R0 — el incrementalismo
  arrastraría el lastre sin comprar seguridad. [Usuario, 2026-06-14.]
- **D4.** `agent_core` queda **fuera del diseño**. No es un consumidor para el cual abstraer:
  es código que se rehará tras Plan 2 (capabilities/mcp/skills) y nada de lo actual sirve.
  `agentic_runtime` debe ser **auto-completo, ejecutable por sí solo** (primitivas + protocolos
  + defaults), con **cero referencias a `agent_core`**. Dirección de dependencia, sin excepción:
  `consumidor ──▶ agentic_runtime ──▶ agentic_models`, nunca al revés. Quien se integre
  construye sus propias implementaciones a partir de las primitivas. Los `import agent_core`
  actuales dentro de `agentic_runtime/` son **bugs a borrar**, no fronteras a preservar.
  [Usuario, 2026-06-14.]
- **D5.** Modelo de extensión de capacidades. Tras lograr estabilidad, `agentic_runtime` debe
  **brindar capacidades** que el consumidor pueda: (a) **tomar tal cual** (defaults del runtime);
  (b) **implementar las suyas vía las fábricas** (`register_backend`/`register`/`register_source`/
  `register_execution_mode`); o (c) **componer las primitivas** directamente para conectarlas a
  su propósito. Las tres vías son ciudadanas de primera clase; ninguna obliga a modificar el
  runtime. [Usuario, 2026-06-14.]

---

## 3. Decisiones de frontera [Regla 4]

La reescritura de D1 obliga a re-decidir dónde vive cada responsabilidad que hoy
`LocalAgentRuntime` toma de `agent_core`. **G1-G3 resueltas (usuario, 2026-06-14).**

### G1 — Persistencia → RESUELTA: responsabilidad del runtime
La persistencia es responsabilidad del runtime porque la ejecución lo es. El runtime obtiene
una instancia de storage de la **fábrica** (`StorageRegistry.create(...)`); el único backend
implementado es `filesystem.py` (`FilesystemStorage`). El runtime persiste vía
`StorageProtocol` + `StorageKeys` (Fase 11), no vía `agent_core.core.store.SessionStore`.

### G2 — `execution/` → RESUELTA: pertenece al runtime, auto-completo, cero agent_core
Todo lo que vive en `execution/` (background tasks, `TaskRegistry`, `BackgroundNotification`,
summarizer, fork) son implementaciones base del runtime genérico. **`agent_core` no es parte
del diseño** (D4): no se abstrae para él, se elimina por completo.

Cada `import agent_core` dentro de `execution/local/runtime.py` se borra y su función se
re-expresa con lo que el runtime ya tiene o debe tener:

| Hoy importa de agent_core | Pasa a ser (genérico, nativo) |
|---|---|
| `agents.task_registry.get_registry` | `execution/tasks/registry.py` (ya existe en el runtime) |
| `models.events.{DoneEvent,…}` | `events/` (Fase 18, ya existe) |
| `core.store.SessionStore` | `StorageProtocol` vía `StorageRegistry` (G1) |
| `core.session.Session` | `Session` concreto nativo del runtime (default) + `SessionProtocol` |
| `hooks.bus`/`hooks.types` | `HookRunner` + taxonomía canónica (G3) |
| `api.session_context.get_user_id` | `RuntimeTask.owner_id` opaco, seteado por el consumidor |
| `core.display_types`/`display_messages` | nada en el runtime; el consumidor proyecta UI desde `EventBus` |
| `core.config.background_result_max_chars` | `RuntimeConfig` del runtime |

El runtime debe quedar **ejecutable por sí solo** con estos defaults (R7 corre con
`FauxProvider`, sin ningún consumidor presente).

### G3 — Hooks ≠ EventBus → RESUELTA: dos contratos distintos
Son cosas diferentes y conviven:
- **`EventBus` (`events/`, Fase 18)** = primitiva de *emisión* unidireccional de progreso:
  `TokenEvent`, `ToolCallEvent`, `ToolResultEvent`, `DoneEvent`, `ErrorEvent`. Ya existe.
- **Hooks** = puntos de *intercepción* del ciclo de vida con poder de decisión (bloquear,
  modificar input, denegar permiso, inyectar contexto, detener). Contrato separado.

Taxonomía tomada del canónico (`claude-code/src/entrypoints/sdk/coreSchemas.ts:355`):
`PreToolUse, PostToolUse, PostToolUseFailure, Notification, UserPromptSubmit, SessionStart,
SessionEnd, Stop, StopFailure, SubagentStop, PreCompact`.

Decisión: el runtime define un `HookRunner`/`HookSink` genérico con esta taxonomía y dispara
los hooks en sus puntos de ciclo (antes/después de `ToolDispatcher`, al terminar subagente →
`SubagentStop`, antes de compactar → `PreCompact`). Cualquier **consumidor registra handlers**;
el runtime no importa hooks de nadie. Sin defaults que asuman un consumidor concreto.

### G4 — Shadow de `types.py` → RESUELTA (M0): renombrar
Evidencia nueva en M0: el crash ocurre en el **bootstrap de `python -m pytest`** (cwd en
`sys.path[0]` shadea el `types` de stdlib), ANTES de que cargue cualquier `conftest.py` → la vía
"config/conftest" queda descartada; la única "config" que mantiene el comando literal exigiría
`PYTHONSAFEPATH=1`/`-P`, que `uv run` no auto-inyecta. Decisión del usuario (2026-06-15):
**renombrar** `types.py` → `model_types.py`. Elimina el footgun de forma permanente (cualquier
invocación, cualquier cwd, sin env).

Con G1-G3 resueltas, **R1 y R2 quedan destrabadas**.

---

## 3.5 Inventario de necesidades tomadas de `agent_core`

Identificar primero qué necesidad representa cada `import agent_core`, implementarla nativa, y
recién entonces erradicar `agent_core` de una pasada y **reconstruir los tests** para probar la
reconexión. No se conserva ningún test "verde apoyado en agent_core" como muleta.

Verificado 2026-06-14 (grep exhaustivo de source). Necesidades reales del runtime:

| # | Hoy (agent_core) | Necesidad | Solución nativa | Fase |
|---|---|---|---|---|
| 1 | `core.session.{Session,SessionMetadata,BackgroundTaskRef}` | estado de sesión concreto | `Session` nativo + `SessionProtocol` | R1 |
| 2 | `agents.task_registry.{TaskStatus,get_registry}` | ciclo de vida de task | `execution/tasks/{status,registry}.py` (ya existe) | R1 |
| 3 | `hooks.{bus,types}` (`get_bus`, `HookEvent`, `SubagentStart/StopContext`) | intercepción de ciclo | `HookRunner` + taxonomía canónica (G3) | R1 |
| 4 | `models.events.{DoneEvent,ToolStartEvent,ToolResultEvent}` | eventos del loop | `events/` (Fase 18); `ToolStartEvent`→`ToolCallEvent` | R2 |
| 5 | `core.store.SessionStore.{save,save_background,save_fork}` | persistencia | `StorageProtocol`+`StorageKeys` (G1), `FilesystemStorage` | R2 |
| 6 | `api.session_context.get_user_id` | identidad del owner | `RuntimeTask.owner_id` opaco | R1 |
| 7 | `core.config.get_config().background_result_max_chars` | configuración | `RuntimeConfig` (campo nuevo) | R1 |
| 8 | `display_types.make_agent_result_dm` + `metadata.display_messages` | presentación | **fuera del runtime** — proyección del consumidor por `EventBus` | — |
| 9 | `loop.factory.LoopFactory` | construcción del loop | `AgentLoop` + `create_runtime` | R2 |

Source acoplado a sustituir: `contracts/runtime.py` (#2), `execution/local/runtime.py`
(#1-9), `execution/local/notification.py` (#1,5,6,8).

Clasificación de tests acoplados:
- **Internals de agent_core (no son del runtime) → BORRAR, sin reconstruir:** `test_fork_skill`
  (skills.executor, Plan 2), caso `GPT54Runtime` de `test_runtime_contracts`, `test_contracts`
  (PathStorage/FakePathPresentation), `test_storage_hardening` (PathStorage/minio_keys).
- **Cobertura real del runtime, hoy acoplada → RECONSTRUIR contra nativos:**
  `test_fork_primitives`, `test_background_notification_channel` → `Session` nativo (R1);
  `test_background_result_summary` → `RuntimeConfig` (R1/R2).

---

## 4. Track RUNTIME

### Fase R0 — Lockear inventario y limpiar tests de internals de agent_core  [x] completado

Objetivo: dejar la línea base honesta: inventario (§3.5) fijo, suite que **colecta y queda
verde**, y fuera los tests que prueban internals de agent_core (no son del runtime). Los tests
de cobertura real acoplados los **borra-y-reconstruye su fase** (R1/R2) de forma atómica —
no se preservan "verdes apoyados en agent_core" más allá de su propósito.

Tareas:
- [ ] Corregir el error de colección: `tests/test_background_notification_channel.py` import
      `agentic_runtime.notification` → `agentic_runtime.execution.local.notification`.
- [ ] Borrar tests de internals de agent_core (sin reconstrucción — no son del runtime):
      `test_fork_skill.py`; `test_storage_hardening.py`; `test_contracts.py` (PathStorage/
      FakePathPresentation); el caso `GPT54Runtime` de `test_runtime_contracts.py`.
- [ ] Endurecer la aserción no-op de `test_capabilities_resolver.py:134`.
- [ ] No tocar `test_fork_primitives`/`test_background_notification_channel`/
      `test_background_result_summary`: los borra-y-reconstruye su fase (R1/R2) contra nativos,
      sin estado intermedio "verde contra agent_core" que sobreviva a la fase.

Verificar:
- `uv run python -m pytest tests/ -q` → sin collection errors y verde.
- (El `grep agent_core tests/` = 0 se verifica en R6, tras R1/R2.)

### Fase R1 — Contratos de frontera faltantes (sin migrar comportamiento)  [x] completado

Objetivo: declarar los protocolos que permiten sacar `agent_core` del execution layer.
No se cambia el flujo todavía; solo se introducen las interfaces. Concretado por G1-G3.

Depende de: G1, G2, G3 (resueltas).

Tareas:
- [x] `HookRunner` + `HookSinkProtocol` + `HookDecision` con la taxonomía canónica de G3
      (PreToolUse, PostToolUse, PostToolUseFailure, Notification, UserPromptSubmit, SessionStart,
      SessionEnd, Stop, StopFailure, SubagentStop, PreCompact) y decisión (block / stop /
      modified_input / additional_context). Nuevo módulo `hooks/`. Distinto del `EventBus`.
- [x] `contracts/runtime.py` desacoplado de agent_core: `TaskStatus` nativo (vía TYPE_CHECKING
      para evitar ciclo) + `RuntimeTask.owner_id` opaco.
- [x] `TaskSinkProtocol`: ya existe como `TaskRegistryProtocol` en `execution/tasks/registry.py`
      (register/start/complete/fail/kill/push_event). No se crea nada nuevo.
- [x] Persistencia (G1): `StorageProtocol`/`StorageRegistry` ya existen (Fase 11). Sin contrato nuevo.
- [x] `RuntimeConfig.background_result_max_chars` (reemplaza `config.get_config()` de agent_core).
- [x] Tests de fork (`test_fork_primitives`) y notification (`test_background_notification_channel`)
      hechos agent_core-free: removidos los conductuales de `AgentTool` (interno, no del runtime);
      `process_*` reescritos contra un `Session` falso nativo (forma mínima).

Refinamiento (decisión 2026-06-14): el **`Session` concreto nativo se mueve a R2**, donde su
forma la define el uso real del `LocalAgentRuntime`. Construirlo en R1 sin consumidor sería
especulativo (CLAUDE.md §2). `RuntimeSessionProtocol` (ya existe) cubre el contrato; el concreto
llega en R2.

Verificar:
- [x] `HookRunner` dispara la taxonomía y respeta block/stop de un handler stub; sink isinstance.
      `tests/test_hooks.py` — 8 tests.
- [x] `grep agent_core contracts/` → 0 (antes 1).
- [x] Suite: `uv run python -m pytest tests/ -q` → 155 passed.

### Fase R2 — Construir `LocalAgentRuntime` de cero sobre `AgentLoop` [núcleo de D1/D3]  [x] completado

Objetivo: un `LocalAgentRuntime` nuevo, escrito desde cero, que componga `AgentLoop` +
`AgenticModelsCaller` + `ToolDispatcher` + `CapabilitiesResolver` + los sinks de R1, sin
importar `agent_core`. El actual se conserva como referencia hasta R5, luego se elimina.

Depende de: R1, **G1+G2+G3 resueltas** (un build limpio decide sus fronteras al inicio).

Tareas:
- [ ] `Session` concreto nativo (movido desde R1) — forma definida por el uso real aquí:
      session_id, messages, turn_count, usage, metadata (subagent_depth, background_tasks).
      Implementa `RuntimeSessionProtocol`. Rebuild de los tests de notification contra él.
- [ ] Crear el nuevo `LocalAgentRuntime` (archivo nuevo, p.ej. `execution/local/runtime_v2.py`)
      que en `dispatch()` construye `ToolUseContext` y corre `AgentLoop.run(prompt, ctx)`.
- [ ] Consumo de eventos vía `runtime/events/` (nunca `agent_core.models.events`).
- [ ] Fork/identidad: reutilizar `RuntimeContextForker` (Fase 7) ya existente.
- [ ] Task lifecycle vía `TaskSinkProtocol` (R1); persistencia vía G1; hooks vía G3.
- [ ] Background subagents + notificaciones + summarizer: en el runtime genérico (G2).
- [ ] Mantener idéntico el contrato externo `dispatch()/status()/cancel()/result()`.
- [ ] Conservar `runtime.py` actual como `legacy_runtime.py` (referencia de paridad).
- [ ] Reescribir contra los nativos (purga de agent_core diferida desde R0):
      `test_runtime_storage.py` y `test_storage_hardening.py` → `FilesystemStorage`;
      `test_background_result_summary.py` → `RuntimeConfig`.

Verificar (sin red, con `FauxProvider`/stub caller y sinks stub):
- Nuevo `tests/test_local_runtime_v2.py`: dispatch de una task simple corre el ciclo
  completo, acumula mensajes, `result()` devuelve el texto final; caso sin tool calls y caso
  con un tool call vía `ToolDispatcher`; notificación background emitida; persistencia invocada.
- `grep -rn "agent_core" execution/local/runtime_v2.py` → 0.
- Paridad de comportamiento documentada contra `legacy_runtime.py` (qué se preserva, qué
  cambia a propósito).

### Fase R5 — `create_runtime()` ensambla el runtime nuevo y se elimina el legacy

Depende de: R2.

Tareas:
- [x] Eliminar los "atributos muertos" de `factory.py:93+`.
- [x] `create_runtime()` inyecta `model_caller`, `tool_dispatcher`, `capabilities_resolver`,
      task sink, persistencia y eventos en el `LocalAgentRuntime` nuevo (R2), sin cableado manual.
- [x] Promover `runtime_v2.py` a `runtime.py` y **eliminar** el legacy una vez
      verificada la paridad.

Verificar:
- [x] `tests/test_runtime_factory.py` ampliado: un runtime creado por `create_runtime()`
  ejecuta una task end-to-end sin tocar `agent_core`. (El `FauxProvider` de `agentic_models`
  no es usable aún —`register_faux_provider()` pasa un dict a `register_api_provider()`, que
  espera `.api`; bug del port que toca al Track M/M1—, así que el e2e usa un caller guionado
  determinista. Mismo valor de verificación: prueba el cableado real de la factory sin red.)
- [ ] El flujo de `scripts/e2e_runtime_test.py` se reduce a `create_runtime()` + un prompt. → R7.
- [x] El runtime legacy ya no existe.

### Fase R6 — Check de acoplamiento final

Tareas:
- [x] Test de acoplamiento estático: `agentic_runtime` (incluyendo `tests/`, `scripts/` y
      todo) no contiene ni un `import agent_core`. Cero absoluto, sin excepciones (D4).

Verificar:
- `grep -rEn "import agent_core|from agent_core" src/agentic_runtime --include=*.py` → 0.
  (Las menciones de la cadena `"agent_core"` que quedan son literales dentro de *guard tests*
  —`test_runtime_contracts`, `test_model_caller_protocol`— que afirman su ausencia en el source;
  borrarlas para forzar el grep literal a 0 reduciría verificación, prohibido por Regla 3.)
- `pyproject.toml` de `agentic_runtime` no declara `agent_core` (nunca lo declaró).
- Suite completa del paquete verde.

### Fase R7 — Evidencia de ejecución E2E + suite de integración completa

Depende de: R5 (todo pasa por `create_runtime()`).

Objetivo doble: (a) un script E2E que pruebe el recableado de punta a punta y deje
**evidencia de ejecución** reproducible; (b) tests de integración que ejerciten
`agentic_runtime` **completo** a través de `create_runtime()`, no por módulos aislados.

Decisión: el E2E se **construye de cero** (el actual `scripts/e2e_runtime_test.py` cablea a
mano `AgentLoop`/caller/tools, justo lo que R5 elimina). Dual-mode:
- **faux** (default): `FauxProvider` determinista — corre sin red, evidencia repetible/CI.
- **real** (opcional, flag/env): provider real vía `.env` — evidencia de ejecución con LLM real.

Tareas:
- [x] Reescribir `scripts/e2e_runtime_test.py`: arma el runtime con `create_runtime()`,
      corre un prompt que fuerza al menos un tool call (`echo` faux / `bash` real),
      imprime traza de turnos/eventos/tool dispatch y el texto final. Selección de modo
      faux/real por argumento o env. Salida apta para pegar como evidencia.
- [x] Caller faux guionado (`FauxScriptedCaller`): stream determinista (turno 1 ToolCall→Done,
      turno 2 Token→Done) para que el E2E faux sea reproducible bit a bit.
- [x] Crear `tests/test_runtime_e2e.py` — integración completa vía `create_runtime()` +
      faux, cubriendo el ciclo real del runtime ensamblado:
  - [x] turno único sin tools → texto final acumulado en `ctx`/sesión.
  - [x] bucle multi-turno con tool calls vía `ToolDispatcher` → resultados insertados, fin correcto.
  - [x] abort/cancelación vía `runtime.cancel()` → task cancelada (status KILLED, result None).
  - [x] background subagent → notificación emitida + persistencia invocada (según G1/G2).
  - [x] fork → aislamiento de mensajes del padre (`fork_context=False`).
  - [x] `CapabilitiesResolver` → tool con permiso no otorgado no aparece; timeout de fuente
        externa → resultado parcial (nativas presentes), loop no se rompe.
  - [x] **Extensión D5 (las tres vías):** (a) capacidad default usada tal cual; (b) backend propio
        registrado vía fábrica (`StorageRegistry.register`) y resuelto por el runtime; (c) primitivas
        compuestas a mano que producen un runtime funcional. Las tres sin modificar `agentic_runtime/`.
  - **Fuera de alcance (Regla 3 — no testear integración inexistente):** la *cascada* de abort
    (`SignalBus`) y la *transición de modo* (`ModeManager`) son primitivas independientes aún NO
    cableadas en `_run_loop` (track BORDES B1-B4). Su comportamiento se cubre en
    `test_signal_bus.py` / `test_mode_manager.py`; aquí no se simula integración de runtime.

Verificar:
- `uv run python scripts/e2e_runtime_test.py` (modo faux) corre sin red y termina 0, con
  traza de ejecución impresa. La salida se registra en §9 como evidencia.
- `uv run python -m pytest tests/test_runtime_e2e.py -q` → todo verde, sin red.
- Cada escenario del E2E ejercita el runtime **a través de `create_runtime()`**, no por
  cableado manual ni módulos sueltos.

---

## 5. Track MODELS

### Fase M0 — Resolver el shadow de `types.py`

Depende de: G4.

Tareas:
- [x] Según G4: renombrado `agentic_models/types.py` → `model_types.py` (la vía conftest quedó
      descartada por crash en bootstrap). 36 import sites en 30 archivos reapuntados por
      profundidad de puntos (`.`/`..`/`...`); `utils/oauth/types.py` y `agentic_runtime/events/types.py`
      son módulos propios distintos, intactos. Consumidor `agentic_runtime/models/caller.py` (ref
      absoluta) reapuntado.

Verificar:
- [x] `uv run python -m pytest tests/` corre desde el directorio del paquete sin ImportError
      (12 passed, sin env). `agentic_runtime` sigue verde (174 passed). E2E faux exit 0.

### Fase M1 — Tests de providers con `FauxProvider`

Objetivo: cubrir la lógica de traducción (lo más propenso a bugs) sin gastar red.

Tareas:
- [x] **Bug bloqueante corregido**: `register_faux_provider` pasaba un dict a
      `register_api_provider` (que hace `provider.api`); ahora envuelve las closures en un
      `SimpleNamespace` que cumple el Protocol `ApiProvider`. `tests/test_faux_provider.py`
      (4 tests): cumple-protocolo / round-trip de AssistantMessage encolado / stream con deltas
      hasta `done` / unregister. El faux queda usable como doble determinista.
- [x] Golden tests de `providers/transform_messages.py` — `tests/test_transform_messages.py`
      (14 tests): downgrade de imágenes (no-visión + colapso de consecutivas + passthrough visión),
      thinking/text same-model (verbatim) vs cross-model (rebuild sin firma / thinking→text /
      vacío dropeado / redacted dropeado cross pero kept same), strip de `thought_signature`,
      `normalize_tool_call_id` (remapeo de call + propagación a toolResult), skip de errored,
      síntesis de toolResult huérfano vs satisfecho.
- **Round-trip por provider real — enfoque decidido (patrón de `pi/packages/ai`).** El `faux`
  reemplaza el provider entero, así que NO ejercita build de request ni parseo de stream. El
  proyecto de referencia (del que esto es port) no fakea el cliente del vendor: **apunta
  `model.base_url` a un servidor HTTP local** que captura el body del request (asertar BUILD) y
  devuelve SSE guionado (ejercitar PARSEO real), dejando que el SDK del vendor serialice. No
  introduce ningún seam en el source de los providers. Helper compartido: `tests/_sse_server.py`
  (`LocalSSEServer` + `sse()`). Para bedrock el cable es event-stream binario de AWS, no SSE;
  `pi/ai` no hace wire-replay de bedrock → se cubre solo build-side (igual que `pi/ai`).
  - [x] **anthropic** — `tests/test_provider_roundtrip_anthropic.py` (texto + tool call; asserts de
        build y de parseo). **Bug de port corregido**: `providers/anthropic.py` usaba la API del SDK
        TS (`client.messages.create(...).as_response()`, `response.aiter_bytes()`, `response.status`),
        inexistente en el SDK Python → reescrito a `with_streaming_response` + `iter_bytes()` +
        `status_code` (patrón que `openai_responses.py` ya seguía). Nunca detectado por falta de tests
        de providers (auditoría §1). Provider antes inoperante contra la API real.
  - [x] **openai_completions / openai_responses** — `tests/test_provider_roundtrip_openai_*.py`
        (texto + tool call cada uno). completions parsea chunks `chat.completion.chunk` + `[DONE]`;
        responses parsea eventos `response.*` validados por los modelos pydantic del SDK.
  - [x] **google** — `tests/test_provider_roundtrip_google.py` (texto + tool call). **Bug de port
        corregido**: el provider tomaba el stream del cliente SÍNCRONO
        (`client.models.generate_content_stream`) e iteraba con `async for` → no enviaba request.
        Reescrito a `client.aio.models.generate_content_stream` con `await`.
  - [x] **bedrock / mistral build-side** — `tests/test_provider_build_bedrock_mistral.py`
        (`_convert_messages`/`_convert_tool_config` de bedrock; `_to_chat_messages`/`_to_function_tools`
        de mistral). bedrock por diseño (cable event-stream binario AWS, igual que `pi/ai`).
  - **BLOQUEADO (decisión del usuario 2026-06-15: dejar build-side) — round-trip de transporte de
    mistral.** El SDK instalado `mistralai` 2.4.9 reubicó `Mistral` a `mistralai.client` y dejó vacío
    el `__init__` top-level; el `from mistralai import Mistral` del provider (API v1) no resuelve →
    desajuste de dependencia, no bug del provider. mistral queda cubierto solo build-side; el round-trip
    de transporte se retoma cuando se resuelva el pin (pin v1.x vs adaptar import). El test
    `tests/test_provider_roundtrip_mistral.py` se escribió y removió por el bloqueo.

Verificar:
- [x] Suite verde sin variables de entorno de API: `pytest tests/ -q` → **44 passed**
      (30 previos + 8 round-trip [anthropic/openai×2/google] + 4 build-side bedrock/mistral +
      2 register_builtins).
- [x] Cobertura sobre `providers/*` real: round-trip (build+parseo) de 4 providers + build-side de
      bedrock/mistral. transporte de mistral diferido por dependencia.

### Fase M2 — `AgenticModelsCaller` respeta `model_id` por request — **COMPLETADA** (0544f2b)

- [x] `complete(..., model_id=...)` resuelve el modelo por request vía `get_model(model_id)`; el
      modelo del constructor es el default. `model_id` desconocido lanza `ModelNotFoundError` (error
      explícito, sin fallback silencioso — Regla 1/3).
- [x] Test (`test_caller_model_per_request.py`): dos `complete()` con `model_id` distintos resuelven
      modelos distintos; id desconocido propaga el error.

### Fase M3 — Providers no registrados — **COMPLETADA**

- [x] `cloudflare` **NO es un provider**: `providers/cloudflare.py` solo expone helpers de ruteo
      (`is_cloudflare_provider`, `resolve_cloudflare_base_url`) consumidos por anthropic/openai para
      modelos `cloudflare-ai-gateway`. La auditoría §1 que lo listó "sin registrar" lo malinterpretó.
- [x] Test (`test_register_builtins.py`): `register_builtins()` expone exactamente el set de 9 APIs
      esperado sin huérfanos; `cloudflare` no declara ninguna clase `*Provider`.

---

## 5.5 Track BORDES DE PROVISIONING (contrato de bordes, sesión 2026-06-14)

Decisiones de arquitectura cerradas con el usuario el 2026-06-14 (las 4 formas de consumidor:
CLI/IDE, container, cloud, asistente con cards; tmux como frontera despriorizada). Detalle y
justificación en la memoria `project_runtime_boundaries`. **Principio**: el runtime no hornea ninguna
pieza de despliegue; topología (in-process vs remoto = clase distinta) ≠ provisioning
(storage/presentation/transport = misma clase, distinta inyección). [Regla 4 — aprobado por el usuario.]

### Fase B1 — `PathPresentation` viva en el choke point  [x] completado

- [x] `PathPresentation` (ya es Protocol en `contracts/storage.py`) inyectada por el consumidor;
      default **identidad** (`context/presentation.py::IdentityPresentation`, canónico CLI/IDE).
- [x] Choke point **único** en la frontera del `ToolResult` (`dispatcher.dispatch`): `sanitize_output`
      sobre `result.output` en un único return point. Como el loop lee el mismo `result.output` para
      `ctx.messages` (`agent_loop.py:148`) Y para `ToolResultEvent` (`:152`), un solo punto cubre LLM
      y todos los canales. `to_llm` queda como helper per-path para las tools que construyen rutas.
- [x] `ctx.presentation` ya no está muerto; `factory.create_runtime()` lo cablea (default identidad,
      `RuntimeConfig.presentation` para inyectar) y el runtime lo fija en `ctx` en `_run_loop`.
Verificar: bajo identidad/None es no-op; bajo presentation fake, ninguna ruta real aparece en
`ctx.messages` ni en eventos emitidos (test a nivel de loop que captura ambos).

### Fase B2 — `ToolExecEnvironment` inyectable (sandbox)  [x] completado

- [x] Backend inyectable (`tools/exec_env.py`): `ToolExecEnvironment` Protocol + `ShellResult`;
      `LocalExecEnvironment` (default in-process), `BwrapExecEnvironment` (sandbox), remoto = D5c.
- [x] `BashTool` despacha a `ctx.exec_env` (cae a `LocalExecEnvironment()` si None); ya no llama
      `create_subprocess_shell` directo. Cableado `RuntimeConfig.exec_env` → factory → `ctx.exec_env`.
- [x] `BwrapExecEnvironment` monta `workspace_root` del host en `/workspace`, `--chdir /workspace`,
      comando verbatim a `sh -c` (sin reescritura, Regla 1).
Verificar: default in-process sin cambio (echo real); backend inyectado recibe el comando sin tocar
host; argv de bwrap build-side (workspace→/workspace + verbatim). **bwrap no instalado** → el run real
aislado se **skipea** (`pytest.mark.skipif`), no se finge (Regla 3) — análogo a bedrock build-side en M1.

### Fase B3 — Modos: `is_backgrounded` mutable + filtro por kind  [x] completado

- [x] `is_backgrounded: bool = False` MUTABLE en `TaskRecord`; el consumidor lo flipea vía
      `registry.set_backgrounded(task_id, value)` (en el Protocol y en `InMemoryTaskRegistry`).
      **No** va en `RuntimeTask`. `fork_context` intacto (eje aparte).
- [x] Hueco corregido: `resolver.resolve()` filtra por **kind**. `ToolUseContext.is_subagent` (lo fija
      el runtime en `_run_loop`: `parent_snapshot is not None`); si subagente → `list_available(
      mode="background")` (solo `safe_for_background`), si no → `all_tools()`. El filtro NO mira el flag
      mutable → promover a background no re-filtra.
Verificar: subagente no recibe tools con `safe_for_background=False` (ask_user/plan_mode/worktree);
main sí; `set_backgrounded` no participa en la resolución del toolset.

### Fase B4 — Taxonomía de `StorageKeys` + dos planos  [x] completado

- [x] **config** scope user: `config_key`/`agent_md_key`/`ltm_key` → `<uid>/config.json`, `<uid>/agent.md`,
      `<uid>/ltm/memories.json`. La **cascada de 4 niveles** (managed/user/project/local) queda como
      **decisión abierta** documentada en el docstring de `StorageKeys` — no se implementa especulativamente.
- [x] **session/log** scope user+session bajo `<uid>/<sid>/`; subagentes anidados en
      `<uid>/<sid>/subagents/<agent_id>/` vía `_agent_base` (main en raíz). El discriminador de subtree
      es el kind (`ctx.is_subagent`), no el `agent_id` aleatorio que ambas ramas asignan.
- [x] **Dos planos por clave**: conversación (`transcript_key`=`session.json` + sidecar mutable
      `meta_key`=`session.meta.json`, donde vivirá `is_backgrounded`) vs artefactos (`work_key`=`work/<f>`).
Verificar: claves deterministas por `agent_id`; transcript/meta/work en claves distintas; main en raíz,
subagente en subtree.

---

## 6. Criterios de cierre global

- [ ] `agentic_runtime` no importa `agent_core` fuera de adaptadores explícitos (R6).
- [ ] Un agente corre de forma autónoma vía `create_runtime()` con `FauxProvider`, sin
      cableado manual (R5).
- [ ] El `AgentLoop` real es el que ejecuta en producción, no el `loop_factory` viejo (R2).
- [ ] Existe evidencia de ejecución E2E reproducible (`scripts/e2e_runtime_test.py` modo
      faux) y suite de integración completa verde (`tests/test_runtime_e2e.py`) (R7).
- [ ] `agentic_models` corre su suite desde su propio directorio (M0) y tiene tests de
      providers (M1).
- [ ] Las tres vías de extensión de D5 (default / fábrica / primitivas) están demostradas y
      verdes sin modificar `agentic_runtime/` (R7).
- [ ] Ningún `[x]` se marca sin el comando de verificación ejecutado y su salida registrada
      en el Registro de Avance. [Regla 3 — sin alineación.]

## 7. Riesgos

- Romper el flujo de background subagents al mover persistencia/notificaciones (G1/G2).
- Diferencias sutiles entre el `AgentLoop` nuevo y el loop de `agent_core` (manejo de
  turnos, abort, tool results) que solo aparezcan con un LLM real — mitigar con `FauxProvider`
  determinista antes de probar con red.
- Renombrar `types.py` (si G4 elige esa vía) toca muchos imports — preferir config.

## 8. Regla de trabajo

Idéntica al plan original: antes de cada fase marcar `[~]`, listar archivos a tocar,
ejecutar tests base, documentar probado/no probado. Al cerrar, registrar evidencia con el
comando ejecutado. Las compuertas G1-G4 se aprueban con el usuario al llegar a su fase.

## 9. Registro de Avance

### 2026-06-14 — Creación del plan
- Auditoría de `agentic_runtime` y `agentic_models` completada y registrada (sección 1).
- Decisiones D1/D2 tomadas. Compuertas G1-G4 identificadas y pendientes de aprobación.
- Nada implementado aún.

### 2026-06-14 — D3: build de cero
- Decidido construir `LocalAgentRuntime` de cero (D3) en vez de refactor incremental.
- R3/R4 absorbidas en R2 (un build limpio decide sus fronteras al inicio). G1-G3 pasan a
  ser bloqueantes de R2. Track renumerado: R0, R1, R2, R5, R6.

### 2026-06-14 — G1-G3 resueltas
- G1: persistencia es del runtime; obtiene storage de `StorageRegistry.create(...)`
  (único backend `FilesystemStorage`); persiste vía `StorageProtocol`, no `SessionStore`.
- G2: `execution/` pertenece al runtime genérico. Salvedad: `get_user_id()` → `owner_id`
  opaco en `RuntimeTask`; `display_messages`/`make_agent_result_dm` → proyección del proyecto
  por eventos, no del runtime.
- G3: Hooks ≠ EventBus. `EventBus` (emisión) ya existe. `HookRunner` nuevo con taxonomía
  canónica (`coreSchemas.ts:355`) y decisiones (block/modify/deny/stop). Proyecto registra
  handlers; runtime no importa `agent_core.hooks`.
- R1 concretada, R2 destrabada. Solo G4 (shadow types.py) pendiente, en M0.

### 2026-06-14 — D4: agent_core fuera del diseño
- agent_core no es consumidor a abstraer: se rehará tras Plan 2; nada actual sirve.
- `agentic_runtime` debe ser auto-completo y ejecutable solo (primitivas+protocolos+defaults),
  cero referencias a agent_core. Dirección: consumidor ▶ agentic_runtime ▶ agentic_models.
- G2 reescrita con tabla de reemplazos (cada import agent_core → default nativo/protocolo).
- R0: tests acoplados a agent_core se borran (no cuarentena). R1: Session concreto nativo por
  default. R6: grep agent_core = 0 absoluto, sin tolerancia. No hay capa de adaptadores.

### 2026-06-14 — R7: E2E + integración completa
- Agregada Fase R7: reescribir `scripts/e2e_runtime_test.py` de cero (dual-mode faux/real)
  para evidencia de ejecución del recableado, + `tests/test_runtime_e2e.py` que ejercita el
  runtime completo vía `create_runtime()` (multi-turno, abort cascada, background+notif, fork,
  capabilities, modos). Depende de R5. Track runtime: R0, R1, R2, R5, R6, R7.

### 2026-06-14 — Inventario §3.5 + D5 + R0 COMPLETADA
- Inventario de necesidades agent_core levantado (§3.5, grep exhaustivo de source): 9 necesidades
  reales → solución nativa por fase. Corrección de secuencia aprobada: no preservar tests
  "verdes apoyados en agent_core"; cada fase borra-y-reconstruye su test contra el nativo.
- D5 agregada: modelo de extensión de capacidades (default / fábrica / primitivas), las tres
  vías de primera clase. Criterio de cierre y demo en R7.
- **R0 completada.** Borrados `test_fork_skill.py`, `test_storage_hardening.py`,
  `test_contracts.py` (internals de agent_core). Quitado caso `GPT54Runtime` de
  `test_runtime_contracts.py`. Removido `test_process_adds_display_message_when_completed_with_text`
  (probaba SessionStore→minio + display_messages, ambos salen del runtime; R1 lo reconstruye).
  Corregidos imports stale (`agentic_runtime.notification`/`.local` → rutas reales) y endurecida
  aserción no-op en `test_capabilities_resolver.py`.
  Evidencia: `uv run python -m pytest tests/ -q` → **154 passed** (antes: 162 passed, 3 failed,
  1 collection error).

### 2026-06-14 — R1 COMPLETADA
- Nuevo módulo `hooks/` (protocol.py, runner.py, __init__.py): `HookEvent` (11 eventos canónicos),
  `HookDecision` (block/stop/modified_input/additional_context), `HookSinkProtocol`, `HookRunner`
  (register/register_sink/run con corte en block-stop y agregación de contexto).
- `contracts/runtime.py` desacoplado de agent_core: `TaskStatus` nativo vía TYPE_CHECKING (evita
  import circular contracts↔execution), `RuntimeTask.owner_id` opaco.
- `RuntimeConfig.background_result_max_chars` añadido.
- Hallazgos: `TaskRegistryProtocol` ya cubría el `TaskSinkProtocol`; `StorageProtocol` ya existía.
- Tests agent_core-free: `test_fork_primitives` (removidos conductuales de AgentTool, quedan 15
  puros), `test_background_notification_channel` (process_* contra `_FakeSession` nativo).
- Refinamiento: `Session` concreto nativo movido a R2 (forma definida por uso real; no especular).
- `tests/test_hooks.py` (8 tests). Evidencia: `pytest tests/ -q` → **155 passed**.
  `grep agent_core contracts/` → 0.

### 2026-06-14 — R2 COMPLETADA (en 3 unidades sucesivas, commit c/u)
- `0e534fe`: `Session` concreto nativo (execution/session/session.py) sin display_messages;
  `process_background_notification` reescrito genérico (ref + XML, sin display/SessionStore) →
  `notification.py` agent_core-free. Tests contra Session nativo.
- `aab8401`: `AgentLoop` emite a `EventBus` inyectado (Token/ToolCall/ToolResult/Done); estado
  sigue en `ctx.messages`. Adapta el modelo del canónico (query() async-generator) separando
  estado de stream sobre la primitiva events/.
- `b58b0a2`: `LocalAgentRuntime` nuevo (`runtime_v2.py`) componiendo AgentLoop + EventBus +
  ToolDispatcher + CapabilitiesResolver + ModelCaller + TaskRegistry + HookRunner + Storage.
  `dispatch(task, parent_snapshot)` nativo (parent_session→ForkSnapshot, D4); SubagentStop por
  hook; notificación background con summarizer; persistencia por StorageKeys; owner_id opaco.
  `InMemoryTaskRegistry` concreto (no existía — el concreto era de agent_core). Legacy
  `runtime.py` intacto hasta R5.
- Source agent_core ahora SOLO en `runtime.py` (legacy) + comentario en `session/protocol.py`.
- Evidencia acumulada: `pytest tests/ -q` → **164 passed**.

### 2026-06-14 — Track BORDES DE PROVISIONING agregado (contrato de bordes)
- Sesión de diseño con el usuario: 4 formas de consumidor (CLI/IDE, container, cloud, asistente con
  cards) + tmux frontera. Cerrado el inventario de primitivas inyectables y los 3 ejes ortogonales de
  modos. Agregadas fases B1-B4 (PathPresentation, ToolExecEnvironment/bwrap, is_backgrounded+filtro,
  StorageKeys/planos). Detalle en memoria `project_runtime_boundaries`.
- Plan 2 (`PLAN_CAPABILITIES_SKILLS_MCP.md`) re-basado y ampliado con STT/TTS y MemoryProvider.

### 2026-06-14 — R5 COMPLETADA
- `factory.py`: `create_runtime()` arma `ToolDispatcher` desde el registry e inyecta
  `model_caller` / `capabilities_resolver` / `tool_dispatcher` / `task_registry` / `hook_runner` /
  `storage` / `small_llm` / `background_result_max_chars` / `model_id` por constructor del runtime
  nuevo. Eliminados los atributos muertos (`runtime._storage = …` etc.) y el `loop_factory`/
  `SignalBus` del cableado legacy. `RuntimeConfig` gana `model_caller`/`hook_runner`/`task_registry`
  (inyección D5b/c) y pierde `loop_factory`.
- `runtime_v2.py` promovido a `runtime.py`; **legacy eliminado**. `execution/local/__init__.py`
  ya apuntaba a `.runtime`. Imports de tests reapuntados (`test_runtime_v2`,
  `test_background_result_summary` al constructor nuevo).
- `test_runtime_factory.py`: e2e `create_runtime()` + caller guionado ejecuta una task hasta
  COMPLETED sin `agent_core`. (FauxProvider de `agentic_models` inutilizable aún: bug
  `register_faux_provider` → `register_api_provider` espera `.api` sobre un dict; Track M/M1.)
- `test_runtime_storage.py`: removido `test_local_backend_satisfies_storage_protocol` — importaba
  `agent_core.storage.local_backend` y solo "pasaba" por efecto colateral de import (el runtime
  legacy fijaba `AGENT_ROOT_PATH`). Cobertura del `StorageProtocol` ya la da
  `test_filesystem_satisfies_storage_protocol`. (D4: tests del runtime no importan agent_core.)
- **Source agent_core: 0 imports.** Solo queda un comentario aclaratorio en `session/protocol.py`.
  Pendiente R6 (tests/scripts) y R7 (e2e real).
- Evidencia: `pytest tests/ -q` → **164 passed**. `grep -rn "import agent_core" src` (source) → 0.

### 2026-06-14 — R6 COMPLETADA
- Último import real de `agent_core` removido: `test_background_result_summary.py::
  test_config_has_background_result_max_chars` afirmaba `AppConfig.from_env()` de agent_core;
  reescrito contra `RuntimeConfig()` propio (el campo `background_result_max_chars` vive en el
  runtime desde R1). Se eliminó el bloque de `os.environ.setdefault` de vars `AGENT_*` que solo
  existía para construir el `AppConfig` ajeno.
- **Acoplamiento de import: 0 absoluto** incluyendo `tests/` y `scripts/`.
  `grep -rEn "import agent_core|from agent_core" --include=*.py` → **0**. Las menciones restantes
  de la cadena `"agent_core"` (7) son literales dentro de *guard tests* (`test_runtime_contracts`,
  `test_model_caller_protocol`) que afirman su ausencia en el source — mantenerlas es verificación,
  no acoplamiento; borrarlas sería reducir cobertura (Regla 3).

### 2026-06-14 — R7 COMPLETADA
- `scripts/e2e_runtime_test.py` reescrito de cero sobre `create_runtime()` (se eliminó el cableado
  manual de `AgentLoop`/caller/tools). Dual-mode: **faux** (default, `FauxScriptedCaller` +
  `EchoTool`, sin red) / **real** (`--real` o `E2E_REAL=1`, `AgenticModelsCaller` + `OPENAI_API_KEY`,
  bash nativo). Imprime traza de tool dispatch + resultado y retorna exit code según completitud.
- `tests/test_runtime_e2e.py` (10 tests) — todos vía `create_runtime()`, runtime ensamblado:
  turno único, multi-turno con tool dispatch, cancelación (`runtime.cancel()` → KILLED),
  background subagent (notificación + persistencia por `StorageKeys`), aislamiento de fork,
  capabilities (tool sin permiso oculta + timeout de fuente externa → parcial), y las **tres vías
  D5** (default / `StorageRegistry.register` resuelto por fábrica / primitivas a mano).
- Alcance honesto (Regla 3): cascada de abort (`SignalBus`) y transición de modo (`ModeManager`)
  NO se testean "a través del runtime" porque aún no están cableadas en `_run_loop` (track B);
  su comportamiento ya vive en `test_signal_bus.py` / `test_mode_manager.py`.
- Evidencia faux (`uv run python scripts/e2e_runtime_test.py` → exit 0):
  `[tool_call] echo({"text": "ping"})` → `[tool_result] → echo:ping`; status COMPLETED;
  texto final `'Listo: la tool echo respondió correctamente.'`.
- Evidencia suite: `pytest tests/ -q` → **174 passed**. Track runtime R0–R7 cerrado.

### 2026-06-15 — M0 COMPLETADA (G4 resuelta: renombrar)
- Reproducido el shadow: `uv run python -m pytest tests/` desde `src/agentic_models` crashea en el
  bootstrap de `runpy` (`from types import MappingProxyType` resuelve al `types.py` local porque cwd
  está en `sys.path[0]`), ANTES de cargar conftest → vía config/conftest descartada empíricamente.
- Decisión del usuario: **renombrar** `types.py` → `model_types.py`. Reapuntados 36 imports en 30
  archivos por profundidad de puntos. Módulos homónimos propios (`utils/oauth/types.py`,
  `agentic_runtime/events/types.py`) intactos. Ref absoluta del consumidor (`caller.py`) reapuntada.
- Evidencia: desde `src/agentic_models`, `uv run python -m pytest tests/ -q` → **12 passed** sin env
  ni ImportError. `agentic_runtime`: **174 passed**. Smoke de import + e2e faux (exit 0) OK.

### 2026-06-15 — Normalización de taxonomía de `types` (hardening de M0)
- Decisión del usuario: **convención repo-wide `<dominio>_types.py`** para que el shadow de stdlib
  (que motivó M0) no vuelva a ocurrir. Alcance acordado: **solo paquetes nuevos** (agent_core es legacy
  en retiro, se deja intacto). Renombrados: `agentic_runtime/events/types.py` → `event_types.py` (refs:
  events/__init__, caller, agent_loop, runtime, test_events) y `agentic_models/utils/oauth/types.py` →
  `oauth_types.py` (4 refs). Junto con `model_types.py` (M0), ya no queda ningún `types.py` propio.
- Evidencia: `agentic_runtime` **174 passed**, `agentic_models` **30 passed**.

### 2026-06-15 — M1 PARCIAL (faux desbloqueado + transform_messages)
- Bug bloqueante del resume corregido: `register_faux_provider` registraba un dict; ahora
  `SimpleNamespace(api, stream, stream_simple)` cumple el Protocol `ApiProvider`. El faux es usable.
- `tests/test_faux_provider.py` (4) + `tests/test_transform_messages.py` (14 golden). Suite models:
  **30 passed** sin env de API.
- **Pendiente y por qué (Regla 3):** round-trip de providers REALES (anthropic/openai/google/
  bedrock/mistral) NO está cubierto — el faux reemplaza el provider entero y no toca la
  construcción de request ni el parseo de stream reales; requiere mockear el transporte HTTP/SSE
  por provider. Decisión de enfoque pendiente con el usuario antes de invertir el esfuerzo.

### 2026-06-15 — B1 COMPLETADA (PathPresentation en el choke point)
- `context/presentation.py::IdentityPresentation` (default no-op = canónico CLI/IDE: `to_llm`=str(path),
  `sanitize_output`=passthrough). Cumple el Protocol `PathPresentation` de `contracts/storage.py`.
- Choke point único en `ToolDispatcher.dispatch`: el cuerpo previo se movió a `_run`; `dispatch`
  aplica `presentation.sanitize_output(result.output)` en un solo return point (todo ToolResult —
  ok/error/timeout/aborted — pasa por ahí). Como `agent_loop.py` lee el mismo `result.output` para
  `ctx.messages` (:148) y para `ToolResultEvent` (:152), un único punto protege LLM y todos los canales.
- Cableado: `RuntimeConfig.presentation` (default `IdentityPresentation()` en `_build_local`),
  `LocalAgentRuntime(presentation=...)`, fijado en `ctx.presentation` en `_run_loop` (cubre ambas
  ramas de `_build_child`: main y fork). El campo `ctx.presentation` deja de estar muerto.
- `tests/test_path_presentation.py` (7): identidad/None no-op, presentation fake oculta ruta real,
  protocolo isinstance, y test a nivel de loop que captura `ctx.messages` (rol tool) Y el
  `ToolResultEvent` del bus — ambos sanitizados desde el único punto.
- Evidencia: `uv run python -m pytest tests/ -q` → **181 passed** (174 + 7). E2E faux exit 0.

### 2026-06-15 — Hygiene: context modules sin trackear (fix .gitignore)
- Destapado al añadir `context/presentation.py` (B1): la regla `context/` del `.gitignore` ignoraba
  `src/agentic_runtime/context/` y `src/agentic_runtime/execution/context/` enteros (whitelist solo
  para `agent_core/runtime/context/`). Ambos módulos (tool_use, adapters, execution, agent_context,
  __init__·) tenían 34 import sites pero **0 commits** — clone limpio no importaría. Añadidas las
  excepciones espejando el patrón existente; archivos rescatados al índice. Commit `4b824d9`.

### 2026-06-15 — B2 COMPLETADA (ToolExecEnvironment inyectable)
- `tools/exec_env.py`: `ToolExecEnvironment` Protocol + `ShellResult`; `LocalExecEnvironment` (default,
  in-process, mueve aquí la lógica que `BashTool` tenía inline) y `BwrapExecEnvironment` (sandbox:
  bind workspace_root→/workspace, --chdir /workspace, comando verbatim a sh -c; binds ro de sistema).
- `BashTool.execute` despacha a `getattr(ctx, "exec_env", None) or LocalExecEnvironment()`; eliminado
  el `import asyncio` huérfano. Cableado: `RuntimeConfig.exec_env` (default `LocalExecEnvironment()` en
  `_build_local`) → `LocalAgentRuntime(exec_env=...)` → `ctx.exec_env` en `_run_loop`.
- `tests/test_exec_env.py` (7, 1 skip): local ok/returncode≠0, isinstance del Protocol, BashTool
  despacha al env inyectado (no toca host) y cae a local con None, argv de bwrap (workspace→/workspace
  + verbatim), run real aislado skipeado por falta de bwrap.
- Evidencia: `uv run python -m pytest tests/ -q` → **187 passed, 1 skipped** (181 + 6 activos). E2E faux exit 0.

### 2026-06-15 — B3 COMPLETADA (is_backgrounded mutable + filtro por kind)
- `TaskRecord.is_backgrounded: bool = False` (mutable, relativo al observador, = isBackgrounded del
  canónico). `TaskRegistryProtocol.set_backgrounded(task_id, value)` + impl en `InMemoryTaskRegistry`.
  No está en `RuntimeTask`; `fork_context` intacto (los 3 ejes quedan ortogonales).
- Hueco del resume corregido: `CapabilitiesResolver.resolve` filtraba con `all_tools()` ignorando el
  modo. Ahora `ToolUseContext.is_subagent` (fijado por el runtime en `_run_loop` =
  `parent_snapshot is not None`) decide: subagente → `list_available(mode="background")` (predicado
  `safe_for_background`), main → `all_tools()`. El filtro es por KIND, no por el flag mutable →
  `set_backgrounded` no re-filtra el toolset.
- `tests/test_modes_background.py` (4): main ve todas, subagente filtrado a safe_for_background,
  is_backgrounded default-false-y-mutable, backgrounding no re-filtra ni muta estado.
- Evidencia: `uv run python -m pytest tests/ -q` → **191 passed, 1 skipped** (187 + 4). E2E faux exit 0.

### 2026-06-15 — B4 COMPLETADA (taxonomía StorageKeys + dos planos). Track BORDES B1–B4 CERRADO.
- `StorageKeys` rediseñado: `_agent_base` ubica el main en `<uid>/<sid>/` y cada subagente en
  `<uid>/<sid>/subagents/<agent_id>/`. config scope-user (`config_key`/`agent_md_key`/`ltm_key`).
  Dos planos por clave: conversación (`transcript_key`=session.json + sidecar `meta_key`=session.meta.json)
  vs artefactos (`work_key`=work/<f>). `log_key` por agente. Eliminados `session_key`/`agent_key` viejos.
- Cascada de 4 niveles del canónico: **decisión abierta** (documentada en el docstring), no implementada.
- `_persist` repuntado a `transcript_key`; el subtree de subagente se discrimina por `ctx.is_subagent`
  (B3), no por el `agent_id` aleatorio que `_build_child`/`fork()` asignan a todo agente.
- Rebuild de tests: `test_runtime_storage.py` (4 nuevos: main en raíz, subagente anidado, dos planos
  distintos, config scope-user) y assert de persistencia en `test_runtime_e2e.py` repuntado al nuevo prefijo.
- Evidencia: `uv run python -m pytest tests/ -q` → **192 passed, 1 skipped**. E2E faux exit 0.
  **Track BORDES B1–B4 cerrado.**
