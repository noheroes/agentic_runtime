# 18 · factory / ensamblado — `agentic_runtime/factory.py` ← canónico (`bootstrap/`, `setup.ts`, `entrypoints/`)

> **Estado — ✅ VALIDADA en 2ª vuelta (gate 11 / L09), 2026-07-20.** Categoría de CIERRE de la 2ª vuelta
> (01→18 completos). El ensamblador `factory.py` (267) se releyó **1→EOF esta ronda** siguiendo el dato seam por
> seam (L09), y **todo el lado A del bootstrap se RE-ABRIÓ 1→EOF esta ronda** (L11, no apoyarse en la 1ª pasada):
> `bootstrap/state.ts` 1758, `setup.ts` 477, `entrypoints/init.ts` 340, `entrypoints/cli.tsx` 302,
> `entrypoints/mcp.ts` 196. **CERO cambios de estado; código intacto.** El value-add del gate 11: confirmar por
> cableado que (a) el núcleo del ensamblado se puebla en ruta real, (b) **C1=FIND-EXEC1** sigue roto (con matiz de
> observable), (c) el factory **NUNCA consume ningún §B-orphan** (incl. el más fresco `config.models`/LAT-MODELS1
> de 16). Bloque completo en **§Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09)** al pie. **Tras 18 → cierre de
> la 2ª vuelta completa.**

> **Forma del subsistema.** 18 es el **punto de convergencia**, no un subsistema de features nuevas. El factory
> es *donde se cablean* los seams que TODOS los §Plan anteriores citan (`create_runtime` como punto de inyección).
> Su homologación NO es "pegar dataclasses": es **verificar que el ensamblado CABLEA de verdad** lo que cada
> subsistema declaró — porque múltiples findings dicen "existe, pero el puente/factory no lo puebla". El archivo
> grande del subsistema (`factory.py`, 267 LOC) se leyó **1→EOF** con la lección 08 activa: *la omisión vive en el
> orden de ensamblado y en los defaults*, no en las funciones obvias.
>
> **La contraparte canónica es asimétrica por arquitectura.** El canónico ensambla un **singleton global de proceso**
> (`bootstrap/state.ts::STATE`, 1758 LOC) + un bootstrap **terminal** (`setup.ts` 477 → backups iTerm2/tmux/worktree;
> `entrypoints/init.ts` 340 → config/trust/telemetría; `entrypoints/cli.tsx` 302 → arranque CLI). El runtime **no
> tiene singleton global** — el estado vive **per-`ToolUseContext`** (`_build_child`) y **per-`Session`**
> (`_run_loop`), porque debe soportar **usuarios y sesiones** (README §Alcance). La homologación aquí es de
> **comportamiento de bootstrap**: orden de init, resolución de config, sembrado de estado, y —lo esencial de 18—
> **cableado real de los seams**.

**Estados:** ✅ ensamblado nuclear cableado (storage · tools · capability-manager · presentation · exec_env · voice ·
lifecycle startup/shutdown · execution_mode como extension primitive) · **❌1 crítico** (**C1=FIND-EXEC1** el factory
nunca llama `set_runner()` → **todo spawn de subagente revienta**) · 🟡3 cabos con hogar cuya cara-factory está sin
poblar (**C2** memoria→Stop, **C3** built-ins al resolver, **C4** frame `init`) · Deuda A propia de 18 = **FaR1**
(sin fail-fast de inyecciones) + **FaR2** (resolver legacy cableado muerto) + FaR3 (ternario muerto, cosmético) ·
⛔ singleton global / bootstrap terminal (`state.ts` accessors · `setup.ts` backups/tmux · `cli.tsx`) = por
divergencia arquitectónica per-ctx/session, **abiertos antes de clasificar** (lección 02).

---

## Hallazgo raíz de forma

El valor de 18 **no** es enumerar features nuevas (no las hay: el factory sólo ensambla). Es **verificar, seam por
seam, que lo que cada subsistema diseñó como "el factory lo cablea" está de verdad cableado** — y el resultado es
**honestamente mixto**:

- El **núcleo del ensamblado SÍ está cableado**: `_build_local` construye storage (`StorageRegistry.create`), tools
  (`create_tools`), el `CapabilityManager` con providers MCP/Skills/Plan/Memory, `presentation` (default
  `IdentityPresentation`), `exec_env` (default `LocalExecEnvironment`), el gate de voz por-canal, y expone
  `startup()`/`shutdown()` (lifecycle de capabilities). Todo esto se leyó y se confirmó **cableado real**, no
  declarado.
- Pero **el seam más crítico está roto**: `_build_local` retorna `LocalAgentRuntime(...)` y **nunca llama
  `set_runner()`**. `execution/runner.py` tiene un `_runner=None` module-level; `get_runner()` **lanza
  `RuntimeError("SubagentRunner not initialized")**; `tools/native/agent.py:105` lo llama. Como el factory **sí**
  mete `AgentTool` en el pool (vía `create_tools`), **cualquier spawn de subagente en un runtime de `create_runtime`
  revienta**. Prueba irrefutable: los tests que ejercitan subagentes (`test_context_identity.py:109/129`) llaman
  `set_runner()` **a mano** — porque el factory no lo hace. Esto es **C1 = FIND-EXEC1** (hogar 05·ExR1), y **18 es
  su punto de convergencia**.
- Tres cabos más tienen hogar en su subsistema pero su **cara-factory está sin poblar**: el extractor de memoria no
  se registra como hook `Stop` (**C2**, canónico lo hace en `setup.ts::initSessionMemory()`); el `agent_resolver` no
  se siembra con los built-ins Explore/Plan (**C3**); no se emite ningún frame `init`/handshake desde el contexto
  ensamblado (**C4**).
- La Deuda A **propia** de 18 es **delgada y honesta** (lección 00/03: no se inventa Deuda A ficticia para "parecer
  exhaustivo"): **FaR1** el factory no valida inyecciones requeridas (un runtime sin `model_caller` no falla al
  ensamblar — el loop hace `warning`+`return`, no-op silencioso; el canónico hace fail-fast con `ConfigParseError`),
  **FaR2** el factory teje un `CapabilitiesResolver` legacy que es **camino muerto** (el loop nunca lo alcanza), y
  FaR3 un ternario muerto cosmético.

---

## Tabla feature-by-feature

### A · Config dataclasses (`RuntimeConfig` + 5 sub-configs) — contrato de inyección

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| A1 | Contrato de config declarativo | `settings.json` cascada + flags CLI + `getInitialState()` (~90 campos sembrados) | `RuntimeConfig` (dataclass) + `StorageConfig`/`ToolsConfig`/`CapabilitiesConfig`/`ModelsConfig`/`VoiceConfig`; todo con defaults válidos (`RuntimeConfig()` instancia sin error) | ✅ (el integrador declara qué inyectar; el runtime da defaults) |
| A2 | Sembrado de identidad de sesión | `getInitialState`: `sessionId=randomUUID()`, `parentSessionId`, `originalCwd`/`projectRoot` en el singleton global | `_build_child`: `session_id`/`user_id`/`agent_id` **inyectables** por el consumidor, autogenerados si faltan (`sess_…`/`user_…`/`agent_…`); per-ctx, sin singleton | 🔀 (equivalente per-sesión; el runtime es multi-usuario, el canónico single-user global) |
| A3 | Seams de autoría per-request del ctx raíz | `ToolUseContext` monolítico (canUseTool/handleElicitation/app_state) reensamblado por turno | `root_context_modifier: (ctx, task)->ctx` (solo raíz) + `root_turn_start_hooks: (task)->[hooks]` sobre `app_state.native`+`presentation` | ✅ (espejo del ctx per-request sin replicar la bolsa monolítica; verificado `test_root_context_modifier`/`test_root_turn_start_hooks`) |
| A4 | Semilla de permisos del agente principal | `Write` disponible por defecto en CLI (single-user de confianza) | `initial_allowed_tools: list[str]` → `_build_child` siembra `PermissionContext.always_allow_command`; la memoria **no** se auto-concede `write_file` (decisión del integrador) | ✅ (espejo correcto: el permiso es del integrador, no auto-otorgado) |
| A5 | Resolver de subagentes | `options.agentDefinitions` | `agent_resolver: AgentDefinitionResolver` pasado tal cual a `LocalAgentRuntime` | 🟡 (**C3**: el factory NO siembra los built-ins Explore/Plan → el reminder de 5 fases es letra muerta; ver PlR/14) |

### B · Ensamblado local (`_build_local`) — el cableado real

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| B1 | Storage pluggable | FS directo (sin registry de backends) | `StorageRegistry.create(backend, root=…, **extra)` — instancia fresca compartida a todos los stores; habilita MinIO en `agentic_assistant` | ✅ (valor propio; verificado `test_runtime_factory`) |
| B2 | Tools nativas → pool | `getMergedTools`/`tools.ts` | `create_tools(extras)` → `ToolRegistry` (input al ensamblado del pool, no lookup de ejecución) | ✅ (**C8/09·B2 resuelto**: NativeToolRegistry NO lo usa el factory; hot-plug MCP por reensamblado del pool por-turno en el loop) |
| B3 | **Seam runner ↔ runtime** | `Task.ts`/`tasks.ts` cablean el runner inline | `_build_local` retorna `LocalAgentRuntime(...)` y **NUNCA llama `set_runner()`** | ❌ **C1=FIND-EXEC1 (crítico)**: `AgentTool→get_runner()` lanza `RuntimeError`; los tests llaman `set_runner()` a mano. Hogar 05·ExR1; converge aquí |
| B4 | Presentación de paths | inline (CLI/IDE) | `config.presentation or IdentityPresentation()` (L207) | ✅ (**C10/01·contracts** cableado real; `test_path_presentation`) |
| B5 | Entorno de ejecución de tools | sandbox/bwrap inline | `config.exec_env or LocalExecEnvironment()` (L210) | ✅ (default in-process; el integrador inyecta bwrap) |
| B6 | Confinamiento fs | path guards inline | `config.fs` → si None, el ctx conserva su default seguro `ConfinedFilesystem`-a-cwd (runtime.py:324, **nunca ilimitado**) | ✅ (default seguro; `test_fs_confinement`) |
| B7 | Gate de voz por-canal | `settings.voiceEnabled` (un flag) | `stt = voice.stt if (voice.stt and voice.stt_enabled) else None` (idem tts) (L214-216) | ✅ (**C10/17·C1**; más fino que el canónico; `test_voice_io`) |

### C · Ensamblado de capabilities (`_build_capability_manager`)

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| C-cap1 | Plan como capability nativa | `planModeV2`/attachments inline | `PlanModeProvider()` **siempre** presente (rinde el plan aprobado en ejecución) | ✅ (14; one-shot de salida de plan mode) |
| C-cap2 | MCP provider | `services/mcp` conecta en bootstrap | `McpProvider(config_store, config_watcher, storage, oauth handlers)`; `load_servers` **tolerante**; **conecta en `startup()`**, no en el factory (no abre red al ensamblar) | ✅ (11; separación ensamblado/conexión correcta) |
| C-cap3 | Skills provider | `loadSkillsDir`/`bundledSkills` en bootstrap | `SkillsProvider(skill_store)` + `load_dir(root)` por cada `skill_dirs` | ✅ (12) |
| C-cap4 | Memory provider | `initSessionMemory()` en `setup.ts` **registra el hook Stop** (extracción lazy) | `MemoryProvider(store)` se **registra como provider** si `memory_root`/`memory_store` presente — pero **NO se cablea el extractor al `Stop` del `HookRunner`, ni hay `drain()` explícito** | 🟡 **C2=13·MeR**: el auto-extract-por-fork no se dispara; `drain` depende de `MemoryProvider.shutdown` (vía `CapabilityManager.shutdown`). Canónico lo cablea en bootstrap; converge aquí |
| C-cap5 | Providers extra + user scoping | settings per-user (canónico single-user, N/A) | `caps.extra_providers` se extienden; **pero `user_id` NO se hila a los stores** (memory/mcp-config construidos una vez sin `user_id`) | 🟡 **C5=15·StR**: transcript persist SÍ usa `ctx.user_id` (runtime.py:424), pero los **stores** de capability no; multi-usuario comparte store |

### D · `execution_mode` + extension primitive (`RuntimeFactory`)

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| D1 | Modo de ejecución | `entrypoints/` distintos (cli/sdk/mcp) elegidos por flags | `create_runtime(execution_mode="local")` → `_build_local`; `remote`/`tmux`/`kubernetes`/`lambda` → `NotImplementedError` explícito | ✅ (04; **C7**; naming `execution_mode`≠`AgentMode` documentado en 04) |
| D2 | Registro de backends custom | — | `RuntimeFactory.register_execution_mode(name, cls)` + `_modes` dict; un proyecto registra su runtime remoto | ✅ (extension primitive; espejo `bootstrap`/`entrypoints`) |
| D3 | `RemoteAgentRuntime`/CCR/teleport | `RemoteAgentTask`/teleport | no implementado (`NotImplementedError`) | 🔀→18/integrador (05·E31; comportamiento futuro, con hogar nombrado) |
| D4 | Hygiene | — | L129 `cls._modes[name] = name if False else runtime_cls` — **ternario muerto** (≡ `runtime_cls`) | cosmético (**FaR3**; sin gap de comportamiento — hoy funciona) |

### E · Lifecycle + emisión de sesión

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| E1 | Startup / shutdown | `setupGracefulShutdown()` + `registerCleanup()` (LSP, teams) en `init.ts` | `LocalAgentRuntime.startup()` (conecta providers MCP) / `shutdown()` (`CapabilityManager.shutdown`→`provider.shutdown`) | ✅ (lifecycle **existe** — **no inflar** un gap inexistente; el integrador lo invoca) |
| E2 | Registry general de cleanups | `registerCleanup(fn)` acumulativo | shutdown provider-scoped, sin registry arbitrario | 🔀 (runtime más simple; cleanups no-provider = integrador) |
| E3 | Frame `init`/handshake del stream | `SDKSystemMessage` init (agents/tools/mcp/skills/model/permissionMode/betas) desde el estado sembrado (`registeredHooks`/`sdkBetas`/`initJsonSchema`) | **ninguno**: el estado que lo alimentaría vive disperso en `ctx`/`factory`; no se emite evento init | 🟡 **C4=07·EvR/EVT9**: converge aquí (serializador init desde el contexto ensamblado) + GAP-02 (permissionMode) |
| E4 | Validación de config / fail-fast | `enableConfigs()` → `ConfigParseError` → non-interactive stderr+`gracefulShutdownSync(1)`, interactive dialog | `create_runtime()` con `RuntimeConfig()` default ensambla **sin validar**: `model_caller=None` → el loop hace `warning`+`return` (no-op silencioso), `model_id=""` | ❌ **FaR1** (Deuda A propia de 18): sin fail-fast; runtime no funcional silencioso |

### F · Comportamiento de bootstrap canónico → mapeo (orden de init · resolución de config · sembrado)

| # | Comportamiento canónico | ¿Dónde vive en el runtime? | Estado |
|---|---|---|---|
| F1 | **Orden de init**: `setCwd()` antes de todo cwd-dep; `captureHooksConfigSnapshot()` **después** de setCwd (`setup.ts:160-166`) | `_build_local`: storage → tools → `capability_manager(storage=…)` → presentation → exec_env → voice → runtime. `capability_manager` recibe `storage` ya construido (TokenStorage OAuth) → orden respetado | ✅ (invariante de orden preservado; sin dependencia hacia adelante) |
| F2 | **Resolución de config en dos fases** alrededor del trust (`applySafeConfigEnvironmentVariables` antes, `applyConfigEnvironmentVariables` tras trust) | trust = responsabilidad del integrador (runtime headless); el factory recibe config ya resuelta | ⛔ integrador (el trust/env-vars viven en la capa que arranca el runtime) |
| F3 | **Sembrado de estado** (`getInitialState`: cwd/cost/tokens/model/session flags/registeredHooks/invokedSkills/sdkBetas) | per-ctx (`_build_child`) + per-session (`Session`: turn_count/usage/messages); flags de sesión → 04/06/12/16 respectivos | 🔀 (per-sesión, sin singleton global — divergencia deliberada) |
| F4 | **Gate de seguridad `bypassPermissions`** (root/sandbox/internet, `setup.ts:396-442`) | ausente en el factory | ⛔ integrador/B-02 (validación de entorno = capa que arranca; GAP-02 permisos) |
| F5 | `init` memoizado (una sola vez) | `create_runtime` no memoizado (factory llamado una vez por el integrador por diseño) | ✅ (N/A — semántica de factory, no de proceso) |

---

## §Convergencia de cabos — verificación de que TODOS tienen hogar (el control de calidad de 18)

> Esta tabla es el núcleo de 18: cada cabo que un §Plan previo mandó a "18/factory" se verifica **abriendo el
> código**, con su estado real de cableado **hoy** y su hogar de remediación. **Honestidad de doble filo**
> (lección 03): los cabos con hogar en OTRO subsistema **no** se re-cuentan como Deuda A de 18 (sería inflar);
> pero tampoco se subcubren — cada uno nombra su §Plan dueño y se confirma que el factory es su punto de cableado.

| Cabo | Origen (§Plan dueño) | Estado HOY en el factory | Hogar de remediación |
|---|---|---|---|
| **C1** set_runner | 05·ExR1 (xfail en `test_execution_homologation.py:113`) | ❌ **no cablea** — verificado: `_build_local` no llama `set_runner`; tests lo llaman a mano | 05·ExR1 (el factory llama `set_runner(adapter)` al ensamblar) |
| **C2** extractor memoria→Stop + drain | 13·MeR | 🟡 `MemoryProvider` registrado, extractor→`Stop` **sin cablear**; drain vía `shutdown` | 13·MeR (registrar extractor como hook `Stop` del `HookRunner` en el factory) |
| **C3** built-ins Explore/Plan al resolver | 14·PlR / FIND-PLAN3 | 🟡 `agent_resolver` pasado tal cual, **sin sembrar built-ins** | 14·PlR (el factory siembra el resolver con `EXPLORE_AGENT_TYPE`/`PLAN_AGENT_TYPE`) |
| **C4** frame `init`/handshake | 07·EvR / FIND-EVT9 | 🟡 **sin emisión** de init; estado disperso en ctx/factory | 07·EvR (serializador init desde el contexto ensamblado) + GAP-02 |
| **C5** `user_id` a los stores | 15·StR | 🟡 transcript persist usa `ctx.user_id`; **stores de capability no** | 15·StR (`_build_capability_manager` hila `user_id` a cada store) |
| **C6** `WorkerStateUploader` (upsert coalescente) | 15·STOR11 | ⛔ fuera del factory (patrón del sidecar meta) | 18/**integrador** (`agentic_assistant`/MinIO lo respalda) |
| **C7** `execution_mode` local/remote | 04 | ✅ homologado (extension primitive) + FaR3 (ternario muerto) | — (cerrado; FaR3 cosmético) |
| **C8** reensamblado del pool por-turno / dos registries | 02·F11 / 09·B2 | ✅ `create_tools`→`ToolRegistry`; hot-plug MCP por reensamblado en el loop | — (cerrado; **09·TiR4 resuelto**) |
| **C9** filtro `is_subagent` (`ASYNC_AGENT_ALLOWED_TOOLS`) | 10·A / 02 | ✅ vive en el loop (`_build_tool_pool` L91: `mode="background"` filtra `safe_for_background`) — **no** en el factory | 02/loop + 10/native_registry (cerrado; no era del factory) |
| **C10** PathPresentation / VoiceConfig gate | 01 / 17 | ✅ cableados en el factory (L207, L214-216) | — (cerrado) |

---

## §Plan de homologación / remediación desarrollada (Deuda A propia de 18)

> **Deuda A propia de 18 = 2 findings + 1 cosmético.** El gap crítico (C1/set_runner) es **cara-factory de
> FIND-EXEC1**, cuya remediación desarrollada (ExR1) y xfail viven en **05** — 18 **no lo re-cuenta** para no
> inflar (lección 00: "el canónico tiene más código en bootstrap" ≠ "18 tiene N gaps propios" cuando el trabajo
> real es cablear seams de otras capas). Lo que sigue es lo que 18 **posee** como Deuda A: la calidad del propio
> ensamblado.

**FaR1 — Fail-fast de inyecciones requeridas al ensamblar**
- *Comportamiento:* `create_runtime()` con `model_caller=None` (o `model_id=""`) hoy ensambla un runtime
  **silenciosamente no funcional**: al primer turno `AgentLoop.run` hace `logger.warning("no hay model_caller")`
  + `return` (agent_loop.py:181-183) — el agente "corre" y no produce nada, sin señal al integrador en el punto de
  ensamblado. El canónico hace **fail-fast** en `init.ts::enableConfigs()` (`ConfigParseError` → stderr +
  `gracefulShutdownSync(1)` en headless). El ensamblado debe fallar temprano, no diferir el fallo a un no-op.
- *Seam:* `create_runtime` (o `_build_local`) valida las inyecciones mínimas para el `execution_mode` pedido
  **antes** de retornar. Modo `local` requiere `model_caller` y `model_id` no vacío. Se añade un flag explícito
  `allow_incomplete: bool = False` para los tests que construyen runtimes parciales a propósito (evita romper la
  suite existente que hoy asume construcción tolerante).
- *Firma:* `create_runtime(*, execution_mode="local", config=None, allow_incomplete=False)`; helper
  `_validate_config(config, execution_mode) -> None` que lanza `RuntimeConfigError` (nueva excepción en
  `factory.py`, espejo de `ConfigParseError`) enumerando **todos** los campos faltantes de una vez.
- *Cableado:* `factory.py::create_runtime` justo tras resolver `config`; `_build_local` no cambia de firma.
- *Orden:* independiente; hacer junto a FaR2 (misma zona del archivo).
- *Test:* xfail(strict)→pass `test_create_runtime_fails_fast_without_model_caller`: `create_runtime(config=RuntimeConfig())`
  (sin `model_caller`) debe lanzar `RuntimeConfigError`; con `allow_incomplete=True` no lanza. Hoy no lanza (retorna
  un runtime no funcional) → el no-lanzar ES la evidencia del gap.

**FaR2 — No cablear el `CapabilitiesResolver` legacy (camino muerto)**
- *Comportamiento:* `_build_local` construye un `CapabilitiesResolver` (factory.py:197-201) y lo pasa a
  `LocalAgentRuntime` → `AgentLoop` (runtime.py:359). Ese camino es **muerto en todo runtime de `create_runtime`**:
  en `agent_loop.py:194` la rama `if (tool_registry OR capability_manager)` **siempre gana** (el factory **siempre**
  construye ambos), así que el `elif self._capabilities_resolver` (L201) **nunca se alcanza**. Es peor que ruido:
  es un camino que, si alguien alguna vez pasara `capability_manager=None`, se activaría y **no puede ejecutar
  tools** (solo las anuncia — el dispatcher resuelve de `ctx.tool_pool`, que ese path no puebla). Deuda estructural
  hermana de 09·B2 (dos registries) y 01/05 (solapamientos de rol).
- *Seam:* el factory deja de construir/pasar `capabilities_resolver`; `LocalAgentRuntime.__init__` y
  `AgentLoop.__init__` retiran el parámetro; se borra la rama `elif` de `agent_loop.py:201-205`. El único camino de
  resolución de tools queda el pool ensamblado (native + capability).
- *Firma:* eliminar `capabilities_resolver` de `RuntimeConfig`-flow, `_build_local`, `LocalAgentRuntime.__init__`,
  `AgentLoop.__init__`. `CapabilitiesResolver` queda como clase suelta hasta que 09·B2 decida su borrado final.
- *Cableado:* `factory.py:196-201, 222`; `execution/local/runtime.py:359`; `loop/agent_loop.py:201-205`.
- *Orden:* con FaR1; coordinar con 09·B2 (dueño del veredicto final sobre los dos registries/resolver).
- *Test:* `test_create_runtime_does_not_wire_dead_resolver`: `runtime._capabilities_resolver is None` tras
  `create_runtime`. (Y la suite de loop sigue verde porque el path real es el pool.)

**FaR3 — Ternario muerto (cosmético, sin gap de comportamiento)**
- *Comportamiento:* `factory.py:129` `cls._modes[name] = name if False else runtime_cls` ≡ `= runtime_cls`. Hoy
  **funciona** (no hay bug); es residuo. **No es xfail-able** (no hay comportamiento roto — no se infla como
  finding). Ajuste directo al implementar: `cls._modes[name] = runtime_cls`.

---

## Ledger de cierre (columna "Lectura")

### Runtime
| Archivo | LOC | Lectura |
|---|---|---|
| `factory.py` | 267 | **íntegro 1→EOF** (archivo grande del subsistema; barrido top-level completo, defaults y orden de ensamblado cerrados — lección 08) |
| `execution/local/runtime.py` | 435 | **íntegro 1→EOF** (verificación de qué cablea el runtime internamente: `startup`/`shutdown`, `_build_child`, `_run_loop`, `_persist`, `_wire_tts`; confirma que `set_runner` NO se llama y que el extractor de memoria NO se registra) |
| `execution/runner.py` | 41 | **íntegro** (`_runner=None`, `get_runner` lanza, `set_runner`) — prueba C1 |
| `capabilities/manager.py` | 111 | tramos: firmas + `startup`/`shutdown`/`build_tool_pool` (confirma `shutdown`→`provider.shutdown`) |
| `loop/agent_loop.py` (ramas de ensamblado) | — | tramos 85-214 (`_build_tool_pool`/`_restrict_to_agent_tools`/`run`: confirma el `if/elif` que hace muerto al resolver legacy — FaR2 — y el `warning+return` sin model_caller — FaR1) |
| `tools/native/agent.py` (llamada al runner) | — | tramo 100-110 (`get_runner().run(...)`) — prueba C1 |
| `tests/test_runtime_factory.py` | — | íntegro (estilo/cobertura actual: defaults, storage, extras; **no** cubre runner/validación) |
| `tests/test_execution_homologation.py` (xfail EXEC1) | — | tramo 108-118 (confirma que C1 ya está codificado como xfail en 05) |

### Canónico
| Archivo | LOC | Lectura |
|---|---|---|
| `bootstrap/state.ts` | 1758 | **1-431 íntegro** (`State` type + `getInitialState()` + `STATE` singleton = el sembrado); **431-1758 barrido top-level completo** (get/set/reset del singleton global) → ⛔ por divergencia arquitectónica (runtime = estado per-ctx/session, sin singleton). "Abierto ≠ íntegro": el seed se leyó íntegro; los ~130 accessors se barrieron por top-level y son mecánicos |
| `setup.ts` | 477 | **íntegro 1→EOF** (extraídos: invariante de orden setCwd/hooks, `initSessionMemory()`=cableado de memoria en bootstrap, gate `bypassPermissions`; resto = backups iTerm2/Terminal.app/tmux/worktree/release-notes = ⛔ terminal) |
| `entrypoints/init.ts` | 340 | **íntegro 1→EOF** (extraídos: `init` memoizado, `enableConfigs`=fail-fast de config, dos-fases env/trust, `setupGracefulShutdown`/`registerCleanup`; resto = telemetría/mTLS/proxy = ⛔ integrador) |
| `entrypoints/cli.tsx` | 302 | **abierto** → ⛔ terminal (arranque CLI ink; abierto antes de clasificar — lección 02 — confirmado bootstrap de terminal, sin comportamiento core ausente en el runtime) |
| `entrypoints/mcp.ts` | 196 | abierto → ⛔ (entrypoint MCP-server-mode del canónico; el runtime expone MCP como capability, no como entrypoint) |
| `entrypoints/init.ts` peers (`agentSdkTypes.ts` 443, `sandboxTypes.ts` 156, `sdk/`) | — | barrido: tipos SDK/sandbox = contrato de la capa SDK/entrypoint → ⛔ (front/integrador); no esconden comportamiento de ensamblado del core |

### §Nota de honestidad
- **`factory.py` y `execution/local/runtime.py` se leyeron 1→EOF** (los dos archivos donde vive el cableado real),
  no por hitos: sólo así se confirma que `set_runner` **no** se llama y que el extractor de memoria **no** se
  registra — ambas omisiones viven en lo que el ensamblado **no hace**, invisibles a un grep de lo que sí hace.
- **`bootstrap/state.ts` (1758) NO se declara "íntegro" en falso**: se leyó íntegro el **seed** (1-431) y se
  **barrió el top-level** del resto (accessors del singleton global). El resto es ⛔ **por divergencia
  arquitectónica verificada** (el runtime no tiene singleton global — README §Alcance), no ⛔-por-título: se abrió y
  se comprobó que son get/set mecánicos sobre `STATE`, cuyo *comportamiento* (sembrado) sí se mapeó (tabla F3).
- **Los entrypoints (`cli.tsx`/`mcp.ts`) se ABRIERON antes de clasificarlos ⛔** (lección 02): el veredicto
  ⛔-terminal es tras abrir, no por título.
- **Honestidad de doble filo aplicada** (lección 03): el gap crítico C1 (set_runner) **no se contó como Deuda A de
  18** — su hogar y xfail están en 05·ExR1; 18 lo verifica y confirma convergencia. Igual con C2/C3/C4/C5 (hogares
  13/14/07/15). Inflar 18 con esos 5 sería duplicar deuda ya contabilizada. La Deuda A **propia** de 18 es
  honestamente delgada (FaR1/FaR2 + FaR3 cosmético) porque 18 es un **punto de convergencia**, no un subsistema de
  features. Subcubrir tampoco: cada cabo se nombra con hogar y estado-hoy verificado (§Convergencia).
- **No se inventó Deuda A ficticia**: el lifecycle `startup`/`shutdown` **existe** (E1) y se dice ✅, no se disfrazó
  de gap; el gate de seguridad `bypassPermissions` (F4) se remitió al integrador/B-02, no se contó como gap del
  factory.

### 4 preguntas de cierre
1. **¿Se revisó todo cada archivo canónico?** Sí. `setup.ts` (477) y `entrypoints/init.ts` (340) **íntegros
   1→EOF**; `bootstrap/state.ts` (1758) con el **seed íntegro** (1-431) + **barrido top-level** del resto (accessors
   del singleton, ⛔-arquitectónico verificado); `cli.tsx`/`mcp.ts` + peers SDK **abiertos antes de clasificar**
   ⛔-terminal/integrador. El *comportamiento* de bootstrap (orden de init, resolución de config, sembrado) se mapeó
   uno a uno (tabla F).
2. **¿Se revisó todo cada archivo runtime?** Sí. `factory.py` (267) y `execution/local/runtime.py` (435) **íntegros
   1→EOF**; `execution/runner.py` (41) íntegro; `capabilities/manager.py` y las ramas de ensamblado de
   `loop/agent_loop.py` en sus tramos exactos; `tools/native/agent.py` (llamada al runner). El cableado se verificó
   **abriendo el código**, no infiriendo.
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí. Se verificó **seam por seam** cada cabo que apuntaba a 18
   (§Convergencia C1-C10), abriendo el archivo en cada caso; C1 (set_runner) se confirmó irrefutablemente (los
   tests lo llaman a mano). Los findings **propios** de 18 (FaR1/FaR2) salieron de leer `factory.py`+`agent_loop.py`
   íntegros (el resolver muerto y el no-op sin model_caller viven en las ramas, no en las firmas), con
   seam/firma/cableado/orden/test desarrollados (lección 05).
4. **¿Todo cubierto (nada pendiente)?** Sí. Los 10 cabos hacia 18 tienen **hogar verificado** (§Convergencia):
   C1→05, C2→13, C3→14, C4→07, C5→15, C6→18/integrador, C7/C8/C9/C10 **cerrados**. Deuda A propia = FaR1/FaR2 con
   §Plan desarrollado + xfail; FaR3 cosmético anotado. Ningún cabo queda "en ningún sitio". **El tablero 01-18
   está completo** (ver §Síntesis final).

---

## Targets de test de homologación (xfail(strict))
- `test_create_runtime_fails_fast_without_model_caller` (FaR1) — **xfail**: hoy `create_runtime(RuntimeConfig())`
  retorna un runtime no funcional en vez de lanzar. Passing = fail-fast al ensamblar.
- `test_create_runtime_does_not_wire_dead_resolver` (FaR2) — **xfail**: hoy `runtime._capabilities_resolver` no es
  None. Passing = el factory no teje el camino muerto.
- `test_create_runtime_wires_runner_so_subagents_spawn` (**C1**, convergencia de FIND-EXEC1) — **xfail**: hoy, tras
  `create_runtime`, `get_runner()` lanza `RuntimeError` (el factory no llama `set_runner`). Passing = el factory
  registra el runner (remediación real en 05·ExR1; el xfail de 18 prueba la convergencia observable: un subagente
  spawnea sin `set_runner` manual).
- **Passing** (ensamblado ya homologado): `test_create_runtime_local_mode_returns_local_runtime` (D1) ·
  `test_create_runtime_defaults_filesystem_storage` (B1) · `test_runtime_config_defaults_are_valid` (A1) ·
  `test_create_runtime_injects_custom_storage` (B1) · `test_create_runtime_extra_tools_registered` (B2) ·
  gate de voz (B7, vía `test_voice_io`) · presentation default (B4, vía `test_path_presentation`) ·
  lifecycle `startup`/`shutdown` (E1, vía `test_capability_registration_e2e`).

---

## §Síntesis final del tablero (01-18 completos)

> Con 18 cerrado, los **18 subsistemas** tienen doc con estado, §Plan de remediación desarrollada y ledger honesto;
> la **Deuda B transversal** tiene sus 7 hogares con diseño listo. Esta síntesis verifica que **ningún cabo de
> ningún §Plan queda sin hogar**.

**Forma del sistema (verificada extremo a extremo).** El runtime es el **core desacoplado** del canónico terminal:
- **Motor** (01 contracts · 02 loop · 03 context · 07 events · 08 signals) — el turno de agente, el ctx per-request,
  el stream de eventos, la cancelación. Deuda concentrada en la **forma compartida** → Deuda B (`ToolResult`,
  `AbortScope`, `Usage`).
- **Ejecución** (04 modes · 05 execution · 06 hooks) — foreground/background/fork, subagentes, hooks configurables.
  El gap crítico transversal (C1/FIND-EXEC1: el runner sin cablear) **converge en 18** y se remedia en 05·ExR1.
- **Tools** (09 infra · 10 native) — el pool ensamblado por-turno (anuncio=ejecución del mismo pool), 25 tools
  nativas vs ~44 canónicas; lo no portado con hogar (Notebook/Brief/LSP/Cron/RemoteTrigger) o ⛔ (terminal).
- **Capabilities** (11 mcp · 12 skills · 13 memory · 14 plan) — providers que convergen en el pool; todos se
  **ensamblan en 18** vía `_build_capability_manager`, con C2/C3 (memoria→Stop, built-ins) como caras-factory
  pendientes.
- **Bordes** (15 storage · 16 models · 17 voice) — persistencia pluggable (habilita MinIO), delegación a
  `agentic_models` (superset multi-provider), voz STT (core) + TTS (superset).
- **Ensamblado** (18 factory) — **este doc**: el punto donde todo lo anterior se cablea; homologado en el núcleo,
  con C1 crítico y C2-C5 como caras-factory con hogar.

**Reparto de capas (no es deuda, es arquitectura).** Lo que el canónico hace inline en terminal se reparte: el
**core-lib** (este runtime) porta el comportamiento; el **integrador** (`agentic_assistant`) aporta motores de I/O
(STT, MinIO/WorkerStateUploader, runtime remoto) y sesiones/usuarios; el **front** (bff/KrakenD/Keycloak) aporta
terminal/UI/auth. Los ⛔ se clasificaron **tras abrir** (lección 02), nombrando su capa-hogar, nunca "a ningún sitio".

**Cabos → hogar (barrido final, todos verificados con destino):**
- Deuda B (7): `B-02` permisos · `B-signals` AbortScope (absorbe `B-orphans`) · `B-new_messages` · `B-concurrency` ·
  `B-usage` cache-tokens · `B-structured-output` — diseño listo en `DEUDA-B-transversal.md`.
- Convergencias en 18: C1→05, C2→13, C3→14, C4→07, C5→15, C6→18/integrador; C7-C10 cerrados.
- Cross-refs previos aterrizados: 16→{B-usage/07·EVT1, B-signals/08, 02·loop-motor#2, 07·D5, 01·CompactionProvider,
  09} · 14→{B-02, 05, front} · 15→{01, 13·MEM9, 09, 18} · 13→{01/compact, B, implementador} · 17→dentro-de-17.

**Estado de cierre honesto:** 18/18 subsistemas + Deuda B documentados. Los tres subsistemas re-auditados por
reproche de superficialidad (11, 12, 15) y los disparados por el propio rigor (05, 06, 07, 08, 10) quedaron con
ledger honesto y §nota de honestidad. **El modo de fallo #1 (superficialidad) se combatió con lectura íntegra del
archivo grande en cada subsistema** — incluido este: `factory.py`+`runtime.py` 1→EOF fueron lo que destapó que el
cableado del runner y del extractor de memoria **no existe**, no que exista mal.

---

## §Re-visita de COMPLETITUD (2ª vuelta · gate 11 / L09) — 2026-07-20

> **Objeto verificado: la homologación A↔B del ENSAMBLADO, no el documento** (L11). Para cada ✅/🔀 se abrió el
> código de B que produce el comportamiento y se siguió el dato de punta a punta en el ensamblador; el lado A del
> bootstrap se re-abrió 1→EOF ESTA ronda. 18 es la categoría de CIERRE (convergencia de todos los cabos de
> cableado). **Resultado: doc de la 1ª pasada CONFIRMADO en sustancia — CERO cambios de estado, código intacto.**
> Una única PRECISIÓN de observable (C1, no voltea estado) + confirmación por lectura de que **el factory nunca
> consume ningún §B-orphan**.

### Cableado confirmado abriendo el ENSAMBLADOR `factory.py` 267 **1→EOF** (L09)

- **Núcleo del ensamblado — cableado en ruta real (✅):** `_build_local` (178-240) puebla, en orden y por lectura:
  storage `StorageRegistry.create(backend, …)` (:186) → tools `create_tools(extras)` → `ToolRegistry` (:189) →
  `_build_capability_manager(caps, storage=)` (:194) → presentation `config.presentation or IdentityPresentation()`
  (:207) → exec_env `config.exec_env or LocalExecEnvironment()` (:210) → gate de voz por-canal
  (:214-216 `stt = voice.stt if (voice.stt is not None and voice.stt_enabled) else None`, idem tts) → retorna
  `LocalAgentRuntime(...)` (:218-240) recibiendo cada primitiva. `startup()`/`shutdown()` (runtime.py:118-128)
  delegan a `CapabilityManager.startup/shutdown` (manager.py:36-42) → `provider.startup/shutdown`. `execution_mode`:
  `create_runtime` (:243-267) rutea `local`→`_build_local`, custom→`_modes`, `remote/tmux/kubernetes/lambda`→
  `NotImplementedError`; `register_execution_mode` (:127-129) es la extension primitive.
- **Providers CONDICIONALES vs INCONDICIONAL confirmado por lectura de `_build_capability_manager` (132-175):**
  `PlanModeProvider()` **SIEMPRE** (:146); MCP sólo si `caps.mcp_servers or caps.mcp_config_store` (:148); Skills sólo
  si `caps.skill_dirs or caps.skill_store` (:160); Memory sólo si `caps.memory_store or caps.memory_root` (:166). =
  exacto a lo que 13/14 verificaron aguas abajo.

### PRECISIÓN de observable en C1 = FIND-EXEC1 (❌ CRÍTICO — **no voltea estado**, gate-11 value-add)

- El doc/README/memoria dicen "todo spawn de subagente **REVIENTA** / `get_runner()` lanza `RuntimeError`". Al leer
  la ruta real: `tools/native/agent.py:104-107` envuelve `get_runner().run(...)` en `try/except Exception` →
  devuelve `ToolResult.error(self.name, "Subagent failed: …")`. **El `RuntimeError` de `runner.py:38` SÍ se lanza,
  pero se CAPTURA en agent.py:106** ⇒ el observable no es un crash del loop padre sino que **cada spawn de
  subagente devuelve un tool-result de error**. El ❌ crítico SE SOSTIENE (los subagentes **nunca** funcionan bajo
  `create_runtime`); sólo se afina el observable.
- **C1 está DOBLEMENTE roto (confirmado leyendo runtime.py 1→EOF):** además de que `_build_local` nunca llama
  `set_runner` (grep de AUSENCIA: sólo `runner.py` def/export + `test_context_identity.py:109/129` a mano +
  `test_execution_homologation.py`/`test_factory_homologation.py` como xfail), **`LocalAgentRuntime` NO implementa
  `SubagentRunnerProtocol.run(fork_ctx, *, background)`** — su método es `dispatch(task, parent_snapshot, *,
  on_event)`. Aunque el integrador llamara `set_runner(runtime)` a mano, faltaría el **adaptador
  ForkContext→RuntimeTask** (= exactamente 05·FIND-EXEC1). Hogar de remediación intacto: 05·ExR1.

### §B-orphans CONVERGEN aquí — el factory NUNCA los consume (anti-padding L10/L11, confirmado por lectura + AUSENCIA)

18 es el punto donde aterrizan todos los huérfanos/costuras latentes registrados en `DEUDA-B-transversal.md §B-orphans`.
Leyendo `_build_local` 1→EOF + grep de AUSENCIA sobre `factory.py`:

| §B-orphan (origen) | ¿Lo consume el factory? | Evidencia |
|---|---|---|
| **`config.models`/`ModelsConfig.extras`** (16·LAT-MODELS1, el más fresco) | **NO** | grep `\.models` en factory.py = **0 lecturas**; sólo `ModelsConfig` def (:59) + campo `models:` (:83). `_build_local` nunca registra modelos extra — el integrador arma su `model_caller` directo |
| `get_registry`/`set_registry` singleton (05·LAT-EXEC1) | **NO** | factory pasa `task_registry=config.task_registry` (:224) por inyección de instancia; el singleton módulo-level no se toca |
| `observer/` (05·FIND-EXEC4) · `modes/` (04·FIND-MODE1) · `SignalBus` (08·FIND-SIG1) · `NativeToolRegistry` (09·FIND-TOOL10) | **NO** | grep `observer|SignalBus|NativeToolRegistry|get_observer` en factory.py = **vacío**. Confirmado además por `test_single_registry_no_native_registry_wired` (passing) |
| `category`/`to_llm`/`timeout_seconds`/`auth_headers`(LAT-MCP1)/`Skill.args`(LAT-SKILL1) | N/A (internos) | el factory sólo construye providers/tools que los portan; ningún prod los lee (ya homed en su categoría) |

Ninguno es Deuda A de 18 (**anti-padding L10:** extensiones sin contraparte canónica = tech-debt B-interno, no brecha
A↔B). 18 los VERIFICA convergentes; la decisión (borrar los duplicados-muertos, cablear los útiles) vive en
`DEUDA-B-transversal.md §B-orphans`. **Sin costuras latentes NUEVAS** en esta ronda (18 no añade features; confirma
que las conocidas no se cablean).

### Deuda A propia de 18 — re-confirmada por lectura ESTA ronda

- **FaR1** (sin fail-fast): `create_runtime(RuntimeConfig())` (:253-267) no valida; `model_caller=None` → el loop
  `agent_loop.py:181-183` hace `logger.warning(...)+return` (no-op). Canónico: `init.ts:65` `enableConfigs()` →
  catch `ConfigParseError` (:216) → `gracefulShutdownSync(1)` (:224). ❌ intacto.
- **FaR2** (resolver legacy muerto): factory teje `CapabilitiesResolver` (:197-201) y lo pasa (:222); en el loop
  `agent_loop.py:194` la rama `if tool_registry or capability_manager` **siempre gana** (el factory siempre
  construye ambos) ⇒ el `elif self._capabilities_resolver` (:201-205) es **inalcanzable**. Confirmado leyendo el
  head del loop 1→234. tech-debt intacto.
- **FaR3** (ternario muerto cosmético): `factory.py:129` `cls._modes[name] = name if False else runtime_cls`. Intacto.

### C2/C3/C5 (caras-factory con hogar en otra categoría) — re-confirmadas por lectura

- **C2** (extractor memoria→Stop no cableado): `_build_capability_manager` registra `MemoryProvider(store)` (:172)
  pero no cablea el extractor a un hook `Stop`. Canónico lo hace en `setup.ts:294 initSessionMemory()` (releído
  1→EOF: "registers hook, gate check happens lazily"). 🟡 hogar 13.
- **C3** (built-ins Explore/Plan no sembrados): `agent_resolver=config.agent_resolver` pasado tal cual (:237); en
  standalone `agent_resolver=None` ⇒ fork genérico (=14·FIND-PLAN3). 🟡 hogar 14.
- **C5** (user_id a los stores): `_build_capability_manager(caps, storage=)` — stores construidos una vez sin
  `user_id`. 15 ya afinó: `token_storage` auto-cableado con `user_id="mcp"` **default** (colisión multi-usuario),
  `mcp_config_store`/`skill_store` no auto-cableados. 🟡 hogar 15.

### Ledger de lectura — 2ª vuelta (columna "Lectura" = ESTA ronda)

**Runtime (B):**
| Archivo | LOC | Lectura ESTA ronda |
|---|---|---|
| `factory.py` | 267 | **íntegro 1→EOF** (ensamblador; seam por seam, orden y defaults, §B-orphans por AUSENCIA) |
| `execution/local/runtime.py` | 435 | **íntegro 1→EOF** (`__init__` acepta las primitivas; `startup`/`shutdown`; `_build_child`; `_run_loop`; confirma que NO implementa `run(fork_ctx,*,background)` → C1 doble) |
| `execution/runner.py` | 41 | **íntegro** (`_runner=None`, `get_runner` lanza, `set_runner`) — prueba C1 |
| `capabilities/manager.py` | 111 | **íntegro 1→EOF** (`startup`/`shutdown`→provider; `build_tool_pool`; `catalog`/`active_context`/`compact_context`) |
| `storage/factory.py` · `tools/factory.py` · `loop/factory.py` | 33·75·27 | **íntegros 1→EOF** (registry de backends; 25 nativas + extras; `create_loop` helper del consumidor) |
| `loop/agent_loop.py` | 1→234 | tramo de ensamblado **1→234 contiguo** (FaR1 warning+return :181-183; FaR2 if/elif :194/:201; pool per-turno :194-200) |
| `tools/native/agent.py` | 119 | **íntegro 1→EOF** (`get_runner().run` :105 en try/except :104-107 → precisión C1) |
| Grep de AUSENCIA | — | `set_runner` / `config.models` / `observer` / `SignalBus` / `NativeToolRegistry` / `get_registry` (prod vs test) |

**Canónico (A) — RE-ABIERTO 1→EOF ESTA ronda (L11):**
| Archivo | LOC | Lectura ESTA ronda |
|---|---|---|
| `bootstrap/state.ts` | 1758 | **íntegro 1→EOF** (L08): `State` (~90 campos) + `getInitialState()` (seed, F3) + `STATE` singleton (:429) + ~130 accessors mecánicos (:431→EOF). ⛔-arquitectónico **verificado por lectura** (el runtime no tiene singleton global; estado per-ctx/session) |
| `setup.ts` | 477 | **íntegro 1→EOF**: F1 `setCwd`:161 → `captureHooksConfigSnapshot`:166; **C2** `initSessionMemory()`:294; F4 gate bypass:395-442; resto terminal/telemetría ⛔ tras abrir |
| `entrypoints/init.ts` | 340 | **íntegro 1→EOF**: F5 `init=memoize`:57; **FaR1** `enableConfigs`:65 → `ConfigParseError`:216 → `gracefulShutdownSync(1)`:224; F2 `applySafe…`:74 / `applyConfig…`:269; E1/E2 `setupGracefulShutdown`:87 + `registerCleanup`:189/:195 |
| `entrypoints/cli.tsx` | 302 | **íntegro 1→EOF**: dispatcher de flags/subcomandos (`--version`/daemon/bridge/bg/templates/…) → cae a `main.tsx`:293-297. ⛔ terminal-entrypoint **tras abrir** (L02) |
| `entrypoints/mcp.ts` | 196 | **íntegro 1→EOF**: MCP-server-mode (sirve al PROPIO CC como servidor MCP stdio, re-expone `getTools`). ⛔ entrypoint/deployment **tras abrir** (el runtime expone MCP como capability, no como entrypoint) |
| `entrypoints/sandboxTypes.ts` | 156 | **íntegro 1→EOF** (peer): schemas zod de sandbox (network/filesystem/settings). ⛔-satélite de la capa exec-env/permisos (09/15/B-02) **tras abrir** (L02); sin bootstrap-wiring |
| `entrypoints/agentSdkTypes.ts` | 443 | **íntegro 1→EOF** (peer): superficie pública del SDK — re-exports de tipos + funciones STUB (`query`/`tool`/`listSessions`/`forkSession`/`watchScheduledTasks`/`connectRemoteControl`, todas `throw 'not implemented'`). Comportamientos→07(SDKMessage)/15(session ops)/10(cron/remote). ⛔-satélite de la capa SDK/entrypoint **tras abrir** (L02); sin bootstrap-wiring |
| `entrypoints/sdk/coreSchemas.ts` | 1889 | ⛔-con-destino **07·events** (`SDKMessageSchema`); archivo in-scope de 07, leído 1→EOF en esa ronda — L07, no re-leído aquí |

**DRIFT (L11):** tamaños idénticos a la 1ª pasada (1758/477/340/302/196). Sin anclas-de-línea previas que
contradecir en A (la 1ª pasada citó funciones, no líneas); esta ronda fija anclas exactas (arriba).

### §Nota de honestidad (2ª vuelta)
- **Todo A in-scope se RE-ABRIÓ 1→EOF ESTA ronda** (L11), incluidos los 2 ⛔-entrypoint (`cli.tsx`/`mcp.ts`) abiertos
  antes de clasificar (L02) y el archivo grande `state.ts` 1758 leído 1→EOF (L08). NO se heredó nada del ledger de
  la 1ª pasada.
- **La conclusión de cableado se sacó leyendo el ENSAMBLADOR `factory.py` 1→EOF** (L09), no de grep; grep se usó SÓLO
  para probar AUSENCIA (los 0-consumidores de `config.models`/`set_runner`/§B-orphans), corroborada por lectura del
  factory 1→EOF. Es la regla re-interiorizada tras los reproches de 07/09/11/12/13/14/15.
- **Anti-padding aplicado (L10):** los §B-orphans NO se cuentan como Deuda A de 18 (son tech-debt B-interno sin
  contraparte canónica); 18 sólo verifica que el factory no los cablea. La Deuda A propia sigue **delgada y honesta**
  (FaR1/FaR2 + FaR3 cosmético) — 18 es punto de convergencia, no subsistema de features.
- **Precisión sobre C1 declarada explícitamente**, no corregida en silencio: el observable es `ToolResult.error`, no
  crash; el ❌ crítico se sostiene.

### 4 preguntas de cierre (2ª vuelta)
1. **¿Se revisó todo cada archivo A?** Sí, **RE-ABIERTOS 1→EOF ESTA ronda**: `state.ts` 1758 (seed íntegro +
   accessors barridos 1→EOF, ⛔-arquitectónico por lectura), `setup.ts` 477, `init.ts` 340 íntegros; `cli.tsx` 302 y
   `mcp.ts` 196 abiertos 1→EOF antes de clasificar ⛔ (L02). NO se apoyó en la 1ª pasada (L11).
2. **¿Se revisó todo cada archivo B?** Sí. `factory.py` 267 + sub-factories (33/75/27) + `runtime.py` 435 +
   `manager.py` 111 + `agent.py` 119 leídos 1→EOF; el tramo de ensamblado del loop 1→234; grep de AUSENCIA para los
   §B-orphans. El cableado se siguió punta a punta, no por inventario.
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí. Cada seam ✅ se confirmó cableado-en-ruta-real abriendo el
   ensamblador; C1/FaR1/FaR2/FaR3 re-confirmados por lectura; §B-orphans confirmados no-consumidos por lectura +
   AUSENCIA; 1 precisión de observable (C1) destapada al leer `agent.py` en su contexto. Evidencia de tests:
   **16 passed · 3 xfailed(strict, sin xpass)** (`test_factory_homologation.py`+`test_runtime_factory.py`) — los 3
   xfail = C1/FaR1/FaR2; los gaps persisten, ninguno pasó por sorpresa.
4. **¿Todo cubierto (nada pendiente)?** Sí. **CERO cambios de estado**, código intacto. C1→05, C2→13, C3→14, C4→07,
   C5→15, C6→18/integrador; C7-C10 cerrados; §B-orphans→`DEUDA-B §B-orphans`. Deuda A propia = FaR1/FaR2 (xfail) +
   FaR3 (cosmético). Ningún cabo sin hogar. **Con 18 validada, la 2ª vuelta 01→18 queda COMPLETA.**

### VEREDICTO DE AVANCE
**✅ NADA PENDIENTE — 18·factory VALIDADA. La 2ª vuelta de validación (gate 11 / L09) sobre 01→18 queda COMPLETA.**
No quedan subsistemas por validar. Siguiente paso (fuera del bucle 01→18): revisar si `DEUDA-B-transversal.md` tiene
ítems pendientes de re-visita de 2ª pasada (los §B-orphans quedaron confirmados-convergentes aquí en 18).
