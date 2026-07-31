# 18 · factory / ensamblado — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/18-factory.md`.
> Ciclo **A3 · 18·factory** (PLAN §7) — **ÚLTIMO ciclo por-categoría**; tras él, rollups A3.DA / A3.DB / A3.CAT.
> Fuente primaria: tracker `../18-factory.md` (470) leído **íntegro 1→470**. Esquema/tiers: `00-LEGEND.md`.
> Método: PASO 0 (11 lecciones de `~/.claude/skills/analisis-comparativo-ab/lecciones/`) ejecutado antes de abrir nada.

---

## §0 · Tesis de la categoría + desambiguación

**18 no es un subsistema: es EL punto de composición.** Todos los ciclos anteriores (01→17) terminaron sus §2.1
con una frase de la misma forma — «la costura existe; el factory la cablea» o «el factory NO la cablea». 18 es
donde esa frase se verifica o se cae. Bajo Filosofía B eso sube de rango: si el base es «framework + batteries
componibles», entonces **el ensamblador ES la arquitectura** — es el único artefacto donde se decide qué conoce el
base y qué compone el integrador. Un base perfecto con un ensamblador que hornea el catálogo sigue siendo un
monolito con costuras decorativas.

**Hallazgo raíz de forma (esta ronda, por lectura del ensamblador 1→EOF):** el runtime **no tiene un punto de
composición; tiene un cableado a mano de tres bolsas planas encadenadas**:

```
RuntimeConfig (19 campos, 11 de ellos `Any`)      factory.py:78-117
        │  _build_local (factory.py:178-240) — 20 kwargs tecleados uno a uno
        ▼
LocalAgentRuntime.__init__ (22 kwargs)            execution/local/runtime.py:55-108
        │  _run_loop (runtime.py:355-366) — 10 kwargs tecleados uno a uno
        ▼
AgentLoop.__init__ (11 params)                    loop/agent_loop.py:49-63
```

Cada eslabón re-teclea el anterior. **Consecuencias verificadas, no inferidas:**

1. **El base conoce por nombre a todas las batteries.** `_build_capability_manager` (`factory.py:132-175`) importa y
   construye `PlanModeProvider` (:141/:146, **incondicional**), `McpProvider` (:140/:149), `SkillsProvider`
   (:142/:161) y `MemoryProvider` (:167/:172) — cuatro `if` por-nombre sobre campos dedicados de
   `CapabilitiesConfig`. `create_tools` (`tools/factory.py`, 75) hardcodea las 25 nativas por clase. El único hueco
   genérico es `caps.extra_providers` (:174) y `tools.extras`. Bajo B esto está **invertido**: el base debería
   recibir una lista de composables y no conocer ni un solo nombre de battery.
2. **La superficie de composición no tiene tipos.** 21 slots `Any` (11 en `RuntimeConfig`, 8 en
   `CapabilitiesConfig`, 2 en `VoiceConfig`) + `create_runtime`/`_build_local`/`_build_capability_manager` retornan
   `Any`. Los Protocols **existen** (`ModelCallerProtocol`, `HookSinkProtocol`, `StorageProtocol`,
   `PathPresentation`, `CapabilityProvider`, `SpeechToTextProtocol`/`TextToSpeechProtocol`,
   `AgentDefinitionResolver`, `ToolProtocol`) y el punto de composición **no referencia ni uno**. El contrato de
   inyección es hoy **prosa en comentarios** (`factory.py:85-117`), no tipo verificable.
3. **La composición es parcial en ambos sentidos.** Cuatro objetos se construyen **inline** y no son inyectables
   (`tool_registry` :189 — sólo `extras`; `capability_manager` :194 — sólo `extra_providers`; `tool_dispatcher`
   :204 — nada, ni su `timeout_override`; `capabilities_resolver` :197-201 — el camino muerto). Y dos parámetros
   del grafo son **inalcanzables desde `create_runtime`**: `LocalAgentRuntime.default_timeout=300.0`
   (`runtime.py:79`, ausente de los 20 kwargs de :218-240) y `AgentLoop.deferred_strategy` (`agent_loop.py:62`,
   ausente de los 10 kwargs de `runtime.py:355-366`) — este último documentado como «inyectable (tests / selección
   explícita del consumidor)» (`agent_loop.py:78-80`): promesa inalcanzable por la única vía pública.

**Desambiguación (qué NO es 18).** (a) **No es «el canónico tiene más bootstrap»**: el lado A es un singleton
global de proceso (`bootstrap/state.ts` 1758) + bootstrap terminal; el reparto B es per-`ctx`/per-`Session` y eso
es 🔀 deliberado, no deuda (F3). (b) **No es el dueño de C1-C5**: son caras-factory de 05/13/14/07/15; aquí se
verifica su estado-hoy y se desarrolla su cara, no se re-cuenta su deuda (L10, anti-padding). (c) **No es el dueño
de la retirada de campos de config**: 17 mandó aquí el patrón «config del núcleo vs composición de batteries»
(`17-voice.md:380-381`); 14 mandó su decisión gemela (`PlanModeProvider` incondicional) a **A3.CAT**, no aquí
(`14-plan.md:234-236`) — **corrijo la nota de memoria que decía «14·§0.1b difiere a 18»: 14 difiere a A3.CAT**. 18
fija el **mecanismo** de composición; A3.CAT fija **qué battery es obligatoria y cuál opcional**.

**Doble filo (L10) por adelantado.** El ensamblado nuclear **sí funciona y está cableado en ruta real** — storage,
tools, capability-manager, presentation, exec_env, gate de voz, lifecycle: verificados línea a línea abajo. La
crítica de este §0 es de **forma bajo B**, no de funcionamiento; y la Deuda A **propia** de 18 sigue siendo
honestamente **una** (fail-fast). Inflarla sería exactamente el error que el tracker evitó.

---

## §1 · Tabla por finding

> Una fila por finding del tracker. `núcleo|cáscara-CLI` = eje §2.1 de LEGEND; TIER = §2.2; destino = §2.3.
> Los IDs `N#` son **findings NUEVOS destapados por lectura esta ronda** (L11: el tracker es hipótesis, no techo).

### A · Config dataclasses — contrato de inyección

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| A1 | Contrato de config declarativo con defaults válidos (`RuntimeConfig()` instancia) | núcleo | **T2-COSTURA** (punto de composición) → residuo **DEUDA-B** | `factory.py` reparto: núcleo mínimo vs `BatterySpec[]`; sub-configs de battery salen con su battery | — | Descomponer la bolsa: `RuntimeConfig` conserva sólo motor+seams del núcleo; `CapabilitiesConfig`/`VoiceConfig`/`ModelsConfig` migran a la config de **su** battery (17·C1 generalizado) |
| A2 | Sembrado de identidad: `session_id`/`user_id`/`agent_id` inyectables, autogenerados si faltan | núcleo | **T2-COSTURA** (S20) | `SessionRepo` (rollup A3.DA) | **【id-opaco】** autogen `sess_…`/`user_…` = mímica a ripear (05·E30) | No se resuelve aquí: se marca como touchpoint del rollup transversal DEUDA-A |
| A3 | Seams de autoría per-request del ctx raíz (`root_context_modifier`, `root_turn_start_hooks`) | núcleo | **T2-COSTURA** | base (`factory.py:99-112` → `runtime.py:329-330,372-374`) | — | Tipar (hoy `Any`; existe `ContextModifier` en `context/tool_use.py:67` con firma distinta `(ctx)->ctx` vs `(ctx,task)->ctx`) y declararlos en `SEAMS.md` — hoy **no figuran** entre las 27 |
| A4 | Semilla de permisos del agente principal (`initial_allowed_tools`) | núcleo | **T2-COSTURA** (S17 adyacente) | base; política = integrador | — | Conservar; el permiso lo declara el integrador, el base sólo lo siembra (✅ reparto correcto) |
| A5 | Resolver de subagentes pasado tal cual (`agent_resolver`) | núcleo | **T2-COSTURA** (S25) | 14·`battery_plan`/`battery_builtin_agents` | — | **=C3**: el factory NO siembra built-ins Explore/Plan. Bajo B **no debe sembrarlos** el base: los aporta la battery al componerse (ver §2.3b) |

### B · Ensamblado local (`_build_local`) — el cableado real

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| B1 | Storage pluggable por registry de backends (`StorageRegistry.create`) | núcleo | **T2-BASE-MECANISMO** + costura S13 | base (`storage/factory.py`) | 【id-opaco】 clave = repo genérico (15) | Conservar el pluggable; **retirar el registry de clase** (ver N4) a favor de inyectar la instancia o la fábrica |
| B2 | Tools nativas → `ToolRegistry` como input del pool (`create_tools(extras)`) | núcleo | **T2-BASE-MECANISMO** + **BATTERY** (el catálogo) | base = ensamblado del pool; catálogo de 25 nativas = battery `tools-native` | — | **=C8 (cerrado)** en cuanto a doble-registry. Bajo B: `create_tools` deja de hardcodear; el set nativo se compone (ver N5) |
| B3 | **Seam runner ↔ runtime: `_build_local` nunca puebla el runner** | núcleo | **DEUDA-B** (cableado) + T2-COSTURA S18 | base — **DI por constructor**, NO `set_runner` | — | **=C1**. **CORRECCIÓN vs el tracker:** A2.5 retiró «cablear `set_runner` en el factory»; el patrón validado es **deps-DI** (`SKELETON-REPORT.md §2·S18`, `SEAMS.md §S18`): el factory construye el runner con una fábrica `build_child` y lo inyecta al `LocalAgentRuntime`, que lo threadea al `ctx`; `AgentTool` lee `ctx.runner` |
| B4 | Presentación de paths con default identidad (`config.presentation or IdentityPresentation()`) | núcleo | **T2-COSTURA** S12 | base default / integrador | 【id-opaco】 no filtrar rutas reales | ✅ cableado real (:207); conservar. Tipar a `PathPresentation` |
| B5 | Entorno de ejecución de tools con default in-process | núcleo | **T2-COSTURA** S15 | base default / integrador (bwrap/remoto) | — | ✅ cableado real (:210); conservar. Tipar |
| B6 | Confinamiento fs: si `config.fs is None` el ctx conserva su default seguro | núcleo | **T2-BASE-MECANISMO** S14 | base | — | ✅ default **nunca ilimitado** (`runtime.py:322-325` + `context/tool_use.py:16-20`); conservar |
| B7 | Gate de voz por-canal (primitiva inyectada **y** flag `*_enabled`) | núcleo | **BATTERY** (composición) → residuo DEUDA-B | battery `voice` (17·C1) | — | **=C10/17·C1**: bajo composición el gate **es** la composición ⇒ los flags se borran al extraer `VoiceConfig` del núcleo. Caso testigo del patrón de A1 |

### C · Ensamblado de capabilities (`_build_capability_manager`)

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| C-cap1 | `PlanModeProvider()` **siempre** presente (:146) | núcleo | **BATTERY** | `battery_plan` (14) | — | Decisión obligatoria-vs-opcional = **A3.CAT** (`14-plan.md:234-236`); el **mecanismo** (registro por lista compuesta, no por `if` hardcodeado) se fija aquí (N5) |
| C-cap2 | MCP provider construido si hay servers/store; **conecta en `startup()`**, no al ensamblar | núcleo | **BATTERY** + T2-COSTURA (lifecycle) | `battery_mcp` (11) | 【id-opaco】 `token_storage` con `user_id="mcp"` default (C5) | ✅ separación ensamblado/conexión **correcta y load-bearing** (el factory no abre red); conservar como invariante del mecanismo de composición |
| C-cap3 | Skills provider + `load_dir(root)` por cada `skill_dirs` | núcleo | **BATTERY** | `battery_skills` (12) | — | Idem C-cap1: el `if` por-nombre (:160) se sustituye por composición |
| C-cap4 | Memory provider registrado, **extractor NO cableado al hook `Stop`** | núcleo | **BATTERY** + **CORE-GAP (hogar 13)** | 13·MeR | 【id-opaco】 store sin `user_id` (C5) | **=C2**: cara-factory. Bajo B el cableado del hook lo hace **la battery al componerse** (recibe el `HookRunner` por la costura), no el factory por nombre |
| C-cap5 | `extra_providers` extendidos; `user_id` **no** se hila a los stores | núcleo | **CORE-GAP (hogar 15)** + T2-COSTURA | 15·StR | 【id-opaco】 **central**: multi-usuario comparte store | **=C5**: cara-factory. La costura de composición debe pasar el scope opaco a cada battery stateful (no un `user_id` interpretado: un token opaco del repo) |

### D · `execution_mode` + extension primitive

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| D1 | `create_runtime(execution_mode="local")`; `remote/tmux/kubernetes/lambda` → `NotImplementedError` | núcleo | **T2-BASE-MECANISMO** | base | — | **=C7** cerrado. Conservar **un solo** `create_runtime` como punto único de composición (`SKELETON-REPORT.md §4.1`) |
| D2 | `RuntimeFactory.register_execution_mode(name, cls)` + `_modes` | núcleo | **T2-COSTURA** (extension primitive) | base | — | Ver **N6** (sin contrato) y **N4** (registro global de clase) |
| D3 | `RemoteAgentRuntime`/CCR/teleport no implementado | núcleo | **T3-INTEGRADOR** | `agentic_assistant` (OI-15, 05·E31) | 【id-opaco】 affinity por tenant | 🔀 con hogar nombrado; el `NotImplementedError` explícito es la costura correcta (declara, no finge) |
| D4 | Ternario muerto `name if False else runtime_cls` (:129) | núcleo | **DEUDA-B** (cosmético) | base | — | **=FaR3**: `cls._modes[name] = runtime_cls`. No xfail-able (no hay comportamiento roto) |

### E · Lifecycle + emisión de sesión

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| E1 | `startup()`/`shutdown()` delegan a `CapabilityManager` → `provider.*` | núcleo | **T2-BASE-MECANISMO** + obligación de integrador | base + **OI-FAC-2** | — | ✅ existe (`runtime.py:118-128`, `manager.py`); **NO inflar**. Lo que falta no es el mecanismo sino **quién lo invoca** → obligación universal §2.4 |
| E2 | Sin registry arbitrario de cleanups (`registerCleanup`) | núcleo | 🔀 + **T3-INTEGRADOR** | integrador | — | 🔀 legítimo (shutdown provider-scoped); los cleanups no-provider son del integrador. **Pero** ver S23 (teardown por-agente) que sigue ausente y NO se cubre con esto |
| E3 | Ningún frame `init`/handshake emitido desde el contexto ensamblado | núcleo | **CORE-GAP (hogar 07)** | 07·EvR / battery `wire` | — | **=C4**: cara-factory. El estado que lo alimenta (providers, tools, model, modo) **sólo existe completo aquí** ⇒ el ensamblador debe exponerlo como dato (`RuntimeManifest`), y 07 lo serializa |
| E4 | `create_runtime()` ensambla **sin validar**: `model_caller=None` → loop `warning`+`return` | núcleo | **CORE-GAP propio (keystone)** | base — **CG-FAC-1** | — | **=FaR1**. Remediación desarrollada en §2.3 |

### F · Comportamiento de bootstrap canónico → mapeo

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| F1 | Invariante de orden de init (`setCwd` antes de dependientes) ↔ storage → tools → caps(storage) → … | núcleo | **T2-BASE-MECANISMO** | base | — | ✅ orden respetado sin dependencia hacia adelante (:186→:189→:194→:207→:210→:214→:218). **Bajo composición hay que preservarlo explícitamente**: las batteries tienen orden (una recibe el storage ya construido) ⇒ el compositor necesita fases, no una lista plana (§2.1·S28) |
| F2 | Resolución de config en dos fases alrededor del trust | cáscara | **T3-INTEGRADOR** | integrador (arranque) | — | ⛔-tras-abrir (`setup.ts` 477 leído 1→EOF en el tracker): trust/env-vars = capa que arranca el runtime headless |
| F3 | Sembrado de estado global (`getInitialState`, ~90 campos) | núcleo | 🔀 **por diseño B** | per-`ctx`/per-`Session` | 【id-opaco】 el estado no es global porque hay multi-sesión | 🔀 deliberado y **verificado** (state.ts 1758 leído 1→EOF); no es deuda. **Pero** ver N4: el runtime sí tiene 6 globals de proceso — el 🔀 vale para el *estado de sesión*, no para «cero globals» |
| F4 | Gate de seguridad `bypassPermissions` (root/sandbox/internet) | cáscara | **T3-INTEGRADOR** + B-02 | integrador / 06·GAP-02 | — | ⛔-tras-abrir con hogar; el base no valida el entorno de arranque |
| F5 | `init` memoizado una sola vez | núcleo | N/A (semántica de factory) | — | — | ✅ `create_runtime` no memoiza **por diseño**: el integrador puede ensamblar N runtimes (multi-tenant). 🔀 correcto |

### §Convergencia — cabos sin fila en la rejilla

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| C6 | `WorkerStateUploader` (upsert coalescente del sidecar meta) | núcleo (patrón) | **T3-INTEGRADOR** | `agentic_assistant`/MinIO (15·STOR11) | 【id-opaco】 clave del sidecar | ⛔ fuera del factory, con hogar; el base sólo expone `StorageProtocol` |
| C9 | Filtro `is_subagent` / `ASYNC_AGENT_ALLOWED_TOOLS` | núcleo | **T2-BASE-MECANISMO** | 02·loop (`_build_tool_pool` `mode="background"`) | — | ✅ cerrado — **no era del factory**; se verifica y se deja donde vive |
| FaR2 | El factory teje un `CapabilitiesResolver` legacy: **camino muerto** (`agent_loop.py:194` siempre gana) | núcleo | **DEUDA-B** (estructural) | base — borrar de `RuntimeConfig`-flow, `_build_local`, `LocalAgentRuntime.__init__`, `AgentLoop.__init__` | — | Remediación en §2.4; **acoplada a N1** (borrarlo rompe `create_loop`) |

### §Verificaciones de AUSENCIA (§B-orphans que convergen aquí — no son deuda de 18)

| ID | resumen | destino | acción |
|---|---|---|---|
| OR1 | `config.models`/`ModelsConfig.extras` — el factory **no** lo lee (0 consumidores; sólo def :59 y campo :83) | 16·LAT-MODELS1 → `DEUDA-B §B-orphans` | Bajo B `ModelsConfig` sale del núcleo con la battery del bridge (caso del patrón A1) |
| OR2 | `get_registry`/`set_registry` singleton — el factory inyecta la instancia (:224), no toca el global | 05·LAT-EXEC1 / S19 | Confirmado por lectura; el doble-camino real lo prueba `task_tools.py` (SKELETON-REPORT §2) |
| OR3 | `observer/` · `modes/` · `SignalBus` · `NativeToolRegistry` — cero referencias en el ensamblador | 05/04/08/09 → `DEUDA-B §B-orphans` | El factory no los cablea: siguen huérfanos (verificado por lectura 1→EOF + ausencia) |
| OR4 | `category`/`to_llm`/`timeout_seconds`/`auth_headers`/`Skill.args` — internos de providers | sus categorías | N/A para el ensamblado |

### §Findings NUEVOS de esta ronda (L11 — el tracker es hipótesis, no techo)

| ID | resumen | núcleo\|cáscara | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **N1** | `loop/factory.py::create_loop` (el helper **público** del consumidor) cablea **sólo** `capabilities_resolver` — sin `tool_registry` ni `capability_manager` ⇒ produce un loop que **anuncia tools y no puede ejecutarlas** (es exactamente el camino que FaR2 declara muerto). Cero consumidores en prod (sólo el re-export `loop/__init__.py:3,6`) | núcleo | **DEUDA-B** (estructural, acoplada a FaR2) | base | — | Decidir **junto a FaR2**: o `create_loop` se re-firma sobre `tool_registry`/`capability_manager` (y entonces FaR2 puede borrar el resolver), o se **borra** el helper. Hoy la remediación FaR2 tal como está escrita **rompería** `create_loop` sin decirlo |
| **N2** | La superficie de composición **no tiene tipos**: 21 slots `Any` + 3 retornos `Any`; los Protocols existen y no se referencian | núcleo | **T1-CONTRATO** (aplicar) + DEUDA-B | base | 【id-opaco】 tipar **no** significa tipar identidad: los ids siguen opacos | Sustituir `Any` por los Protocols ya escritos (`ModelCallerProtocol`, `StorageProtocol`, `PathPresentation`, `CapabilityProvider`, `SpeechToText/TextToSpeechProtocol`, `AgentDefinitionResolver`, `HookSinkProtocol`) y tipar el retorno a `AgentRuntime` (`contracts/runtime.py:36`) |
| **N3** | Objetos construidos inline **no inyectables** (`tool_registry`, `capability_manager`, `tool_dispatcher`, `capabilities_resolver`) + parámetros **inalcanzables** desde `create_runtime` (`default_timeout=300.0` `runtime.py:79`; `deferred_strategy` `agent_loop.py:62`, documentado como inyectable) | núcleo | **T2-COSTURA** (completar) | base | — | Todo lo que el grafo acepta debe ser alcanzable desde el punto de composición, o retirarse del grafo. `default_timeout` → campo de config (liga S24); `deferred_strategy` → composable (S26) |
| **N4** | **Seis** almacenes globales mutables de proceso: `RuntimeFactory._modes` (`factory.py:125`), `StorageRegistry._backends` (`storage/factory.py:17`), `_registry` (`execution/tasks/registry.py:153`), `_channel` (`execution/local/notification.py:22`), `_observer` (`execution/observer/observer.py:28`), `_runner` (`execution/runner.py:28`) | núcleo | **DEUDA-B** (transversal) | base — criterio **deps-DI** (`SKELETON-REPORT.md §4.2`) | 【id-opaco】 `_channel` está scopeado por `(user_id, session_id)` **globalmente** ⇒ fuga entre runtimes del mismo proceso en multi-tenant | La afirmación del tracker «el runtime **no tiene singleton global**» es cierta **sólo** para el estado de sesión (F3), **no** para el registro de mecanismo. Convertir los 2 registries de clase en instancias inyectadas y aplicar a `_registry`/`_channel` el mismo criterio DI ya validado para `_runner` |
| **N5** | El base **conoce el catálogo de batteries por nombre**: 4 `if` con import directo en `_build_capability_manager` (:139-172) + 25 tools hardcodeadas en `create_tools` | núcleo | **T2-COSTURA** (nueva, S28) + requisito de re-arquitectura B | base (mecanismo) / batteries (catálogo) | — | Invertir: `RuntimeConfig.batteries: list[Battery]`; cada battery aporta providers/tools/hooks/config y el base itera. Es el **mecanismo** que hace realizable la decisión de A3.CAT (obligatoria vs opcional) y la retirada de config de 17·C1 |
| **N6** | `register_execution_mode(name, cls: Type)` **sin contrato**: `Type` sin Protocol, retorno `Any`, y el único contrato implícito es la forma de llamada `custom_cls(config=config)` (:262) ⇒ un modo custom recibe la **bolsa entera**, incluida la config de batteries que no compone | núcleo | **T2-COSTURA** (extension primitive, enriquecer) | base | — | Tipar contra `AgentRuntime` (`contracts/runtime.py:36`, ya `runtime_checkable`) y fijar la firma de construcción; el modo custom debe recibir el **núcleo** de la config, no la bolsa |

---

## §2 · Síntesis de la categoría

### 2.1 Costuras que implica

**Ya existentes que 18 CABLEA (verificado abriendo el ensamblador 1→EOF):**

| costura | punto de cableado (`archivo:L`) | estado verificado hoy |
|---|---|---|
| S1 `ModelCallerProtocol` | `factory.py:219` (`model_caller=config.model_caller`) | cableado por paso-a-través; **sin validar** (=CG-FAC-1) |
| S12 `PathPresentation` | `factory.py:207` → `runtime.py:317` | cableado con default identidad |
| S13 `StorageContract`/`StorageProtocol` | `factory.py:186` → `:226` → `runtime.py:419-430` | cableado; instancia fresca compartida |
| S14 `ConfinedFilesystem` | `factory.py:229` → `runtime.py:322-325` | cableado con **default seguro** (nunca ilimitado) |
| S15 `ToolExecEnvironment` | `factory.py:210` → `:228` → `runtime.py:318` | cableado con default in-process |
| S16 `ToolProtocol` | `factory.py:189` (`create_tools(extras)`) | cableado; catálogo hardcodeado (N5) |
| S19 `TaskRegistryProtocol` | `factory.py:224` → `runtime.py:86` (`or InMemoryTaskRegistry()`) | inyección de instancia ✅; el global `_registry` no se toca (OR2) |
| S24 `arm_watchdog` | `dispatch` **sí lo llama** (`runtime.py:149`, `task.timeout_seconds or self._default_timeout`) → `registry.py:88-91` = literal `pass` | **existe-noop PROBADO** (no heredado del tracker): el default `InMemoryTaskRegistry` no arma nada. Precisión sobre N3: el timeout **per-task** SÍ es alcanzable (vía `RuntimeTask.timeout_seconds`); lo inalcanzable es **sólo el default 300s** del constructor |
| voz (17) | `factory.py:214-216` → `:238-239` → `runtime.py:106-107` | gate por-canal cableado |
| A3 seams de ctx raíz | `factory.py:105/112` → `runtime.py:329-330` / `:372-374` | cableados; **no declarados en `SEAMS.md`** (hueco del corpus) |

**Que 18 NO cablea (verificado por lectura + ausencia):** S18 `SubagentRunnerProtocol` (=C1/B3, el crítico), S6 wire,
S8 fire-points más allá de `PRE_TOOL_USE`, S9 motor de compactación, S10 `RetryPolicy`, S11 `UserInputProcessor`,
S22/S23 (force-async/teardown), S3 `AuthProvider`.

**Costura NUEVA que 18 exige (no está entre las 27 de `SEAMS.md`):**

- **S28 · `Battery` (unidad componible) + `compose()` por fases** — *tier:* T2-COSTURA (rectora de B).
  *productor:* `create_runtime`, que itera la lista. *consumidor:* cada paquete estándar (`battery_mcp`,
  `battery_skills`, `battery_memory`, `battery_plan`, `battery_voice`, `tools-native`, `compaction`,
  `resilience`, …). *Firma BORRADOR:*
  ```python
  class Battery(Protocol):
      name: str
      def requires(self) -> tuple[str, ...]: ...                 # orden/fases (F1: storage antes que caps)
      def providers(self, host: RuntimeHost) -> list[CapabilityProvider]: ...
      def tools(self, host: RuntimeHost) -> list[ToolProtocol]: ...
      def hooks(self, host: RuntimeHost) -> list[tuple[HookEvent, HookHandler]]: ...   # cierra C2 sin `if` por-nombre
      def agents(self, host: RuntimeHost) -> list[AgentDefinition]: ...                # cierra C3 sin `if` por-nombre
      async def startup(self) -> None: ...
      async def shutdown(self) -> None: ...
  class RuntimeHost(Protocol):        # lo que el base ofrece a la battery al componerse
      storage: StorageProtocol
      hook_runner: HookSinkProtocol | None
      scope: OpaqueScope            # 【id-opaco】 token del repo, NO user_id interpretado — cierra C5
  ```
  *Por qué es costura y no azúcar:* es lo único que permite (a) que el base **deje de importar** `McpProvider`/
  `SkillsProvider`/`MemoryProvider`/`PlanModeProvider` (N5), (b) que C2 (hook `Stop`) y C3 (built-ins) se cierren
  **por composición** en vez de por cableado hardcodeado del factory, y (c) que 17·C1 (retirar `VoiceConfig` del
  núcleo) sea realizable sin perder el gate. *Preserva F1:* `requires()` da fases, no una lista plana.
  *Validación pendiente:* NO ejercitada por A2 (A2.4 compuso **una** battery por constructor, `SKELETON-REPORT §1·S9`)
  ⇒ se valida en Fase C, no se declara validada aquí (L09).
  *Coste real menor de lo que sugiere N5 (verificado al abrir `manager.py` 1→111):* **`CapabilityManager.__init__`
  ya recibe una `list[CapabilityProvider]`** (:26-27) y **no conoce ningún provider concreto** — itera y punto
  (`startup`/`shutdown` :36-42, `tools` con dedup por nombre :50-59, `system_prompt_sections` tolerante vía
  `getattr` :81-96). El hardcodeo por nombre vive **sólo en el factory** (`_build_capability_manager:139-172`), no
  en el mecanismo. S28 por tanto **no reescribe el manager**: lo alimenta. Esto rebaja el coste de RB-1 y refuerza
  que N5 es un defecto **del ensamblador**, no del núcleo de capabilities.

- **S29 · `RuntimeManifest`** — *tier:* T2-COSTURA (dato, no comportamiento). El ensamblador es el **único** sitio
  donde el inventario completo existe (providers activos, tools, modelo, modo de permiso, batteries compuestas).
  Hoy no se expone ⇒ E3/C4 (frame `init`) no tiene de dónde leer. *Firma:* `def manifest(self) -> RuntimeManifest`
  en el runtime ensamblado; 07 lo serializa a `InitEvent`. *Reparto honesto:* **el dato es de 18; el evento es de 07.**

### 2.2 Batteries que alimenta

18 no crea batteries nuevas: **las descubre por el revés** — cada `if` por-nombre del ensamblador es una battery
que hoy vive dentro del base.

| battery | evidencia en el ensamblador | qué se lleva del núcleo al extraerse |
|---|---|---|
| `battery_mcp` (11) | `factory.py:140,148-158` | `CapabilitiesConfig.{mcp_servers, mcp_config_store, mcp_config_watcher, mcp_oauth_*}` (5 campos) |
| `battery_skills` (12) | `factory.py:142,160-164` | `CapabilitiesConfig.{skill_dirs, skill_store, skill_catalog}` (3) |
| `battery_memory` (13) | `factory.py:167-172` | `CapabilitiesConfig.{memory_root, memory_store}` (2) + el hook `Stop` (C2) |
| `battery_plan` (14) | `factory.py:141,146` (**incondicional**) | nada de config hoy; obligatoria-vs-opcional → **A3.CAT** |
| `battery_voice` (17) | `factory.py:214-216` | `VoiceConfig` entero (4 campos; los 2 flags **se borran**, 17·C1) |
| `tools-native` (10) | `tools/factory.py` (25 clases) | el catálogo; el base conserva `ToolPool`/`ToolDispatcher`/deferral |
| bridge de modelo (16) | `ModelsConfig` **no consumido** (OR1) | `ModelsConfig` sale entero con el bridge |

**Saldo del patrón de 17·C1 generalizado (lo que 18 debía resolver «de forma sistemática»):** de los **19** campos
de `RuntimeConfig` + **11** de sus sub-configs, **14 son de battery** (5 MCP + 3 skills + 2 memory + 4 voice) y
**1 es huérfano** (`models`). El núcleo mínimo queda en: `storage`, `model_caller`, `model_id`, `hook_runner`,
`task_registry`, `presentation`, `exec_env`, `fs`, `git_credentials`, `small_llm`,
`background_result_max_chars`, `initial_allowed_tools`, `root_context_modifier`, `root_turn_start_hooks`,
`agent_resolver`, `tools.extras` — **más** `batteries: list[Battery]` (S28) y los dos knobs hoy inalcanzables
(N3). Ese es el reparto concreto que 17 mandó aquí; **la decisión de cuáles se componen por defecto en cada
integrador es de A3.CAT**, no de 18.

### 2.3 CORE-GAPs (keystone primero → rollup `DEUDA-A.md`)

**Uno solo, y es honesto que sea uno** (18 es punto de convergencia; C1-C5 tienen hogar en 05/13/14/07/15 y
re-contarlos sería inflar — L10).

**CG-FAC-1 (keystone) · Fail-fast de la composición** — `=E4/FaR1`
- *comportamiento:* `create_runtime(RuntimeConfig())` retorna hoy un runtime **silenciosamente no funcional**: sin
  `model_caller`, `AgentLoop.run` hace `logger.warning(...)` + `return` (`agent_loop.py:181-183`) — el agente
  «corre» y no produce nada, sin señal en el punto de ensamblado. El canónico hace fail-fast
  (`entrypoints/init.ts:65 enableConfigs()` → `ConfigParseError` :216 → `gracefulShutdownSync(1)` :224).
- *costura:* `create_runtime` valida el conjunto mínimo exigido por el `execution_mode` **antes** de retornar.
  Bajo B se amplía: valida también las **dependencias declaradas por las batteries compuestas** (`Battery.requires()`,
  S28) — es el mismo mecanismo, no dos.
- *firma:* `create_runtime(*, execution_mode="local", config=None, allow_incomplete=False) -> AgentRuntime`;
  `_validate(config, execution_mode, batteries) -> None` lanza `RuntimeConfigError` enumerando **todos** los
  faltantes de una vez (no el primero).
- *realización:* modo `local` exige `model_caller` y `model_id` no vacío; `allow_incomplete=True` para los tests que
  construyen runtimes parciales a propósito (evita romper la suite tolerante existente).
- *orden:* junto a la descomposición de config (misma zona del archivo) y **después** de S28 si se hace en un paso
  (la validación de `requires()` necesita la lista de batteries); si se hace antes, se implementa sólo la parte de
  núcleo y se amplía luego.
- *criterio de aceptación:* `test_create_runtime_fails_fast_without_model_caller` — hoy **no lanza** (el no-lanzar
  ES la evidencia del gap, xfail(strict) ya codificado en el tracker); passing = lanza `RuntimeConfigError` y con
  `allow_incomplete=True` no lanza. Segundo criterio bajo B: componer una battery cuyo `requires()` no se satisface
  falla al ensamblar, no al primer turno.

### 2.3b Requisitos de re-arquitectura B (NO son CORE-GAP — no van a `DEUDA-A.md`)

Separados a propósito: el canónico **no** tiene un mecanismo de composición mejor (tiene un singleton global), así
que esto **no es brecha A↔B**. Es trabajo de forma que B se impone a sí misma, y confundirlo con deuda del
canónico inflaría el rollup.

1. **RB-1 · Punto de composición explícito** (N5 + S28): el base deja de conocer batteries por nombre.
2. **RB-2 · Descomposición de `RuntimeConfig`** (A1 + 17·C1 generalizado + §2.2): núcleo vs config-de-battery.
3. **RB-3 · Superficie de composición tipada** (N2): los Protocols ya existen; usarlos.
4. **RB-4 · Alcanzabilidad total** (N3): lo que el grafo acepta, el punto de composición lo expone; o se retira.
5. **RB-5 · Registro por instancia, no por clase/módulo** (N4 + `SKELETON-REPORT §4.2`).
6. **RB-6 · Contrato del `execution_mode`** (N6): `AgentRuntime` como tipo, núcleo-de-config como entrada.

### 2.4 DEUDA-B (higiene interna del runtime → rollup `DEUDA-B.md`)

| ID | qué | evidencia | acción | acoplamiento |
|---|---|---|---|---|
| **B-runner-wiring** (=C1/B3) | el ensamblador no puebla el runner ⇒ **todo** spawn de subagente devuelve `ToolResult.error` | `factory.py:178-240` (ausencia, leído 1→EOF) + `runner.py:36-41` + `agent.py:104-107` | **DI**: el factory construye `LocalSubagentRunner(build_child=…)` y lo inyecta al runtime → `ctx.runner`; **no** `set_runner` | Remediación en 05·ExR1, patrón fijado por A2.5 |
| **B-dead-resolver** (=FaR2) | `CapabilitiesResolver` tejido y muerto (`agent_loop.py:194` siempre gana) | `factory.py:197-201,222` · `runtime.py:359` · `agent_loop.py:194,201-205` | borrar del flujo de config, `_build_local`, ambos `__init__` y la rama `elif` | **⚠ N1**: borrarlo **rompe `create_loop`**, cuyo único camino es ese `elif`. La remediación del tracker no lo dice |
| **B-create-loop** (=N1) | el helper público produce un loop que no ejecuta tools; 0 consumidores en prod | `loop/factory.py:9-27` (1→EOF) · `loop/__init__.py:3,6` | re-firmar sobre `tool_registry`/`capability_manager`, o borrar | con B-dead-resolver (decisión conjunta) |
| **B-global-registries** (=N4) | 6 almacenes globales de proceso | 6 anclas exactas en N4 | deps-DI (criterio A2.5) | toca 05 (`_registry`), 07/05 (`_channel`), 08/05 (`_observer`) |
| **B-untyped-composition** (=N2) | 21 slots `Any` + 3 retornos `Any` | `factory.py:34-117,132,178,247` | tipar contra los Protocols existentes | RB-3 |
| **B-unreachable-knobs** (=N3) | `default_timeout` / `deferred_strategy` / `tool_dispatcher` | `runtime.py:79` · `agent_loop.py:62,78-80` · `factory.py:204` | exponer o retirar | S24 / S26 |
| **B-dead-ternary** (=FaR3/D4) | `name if False else runtime_cls` | `factory.py:129` | `= runtime_cls` | — |
| §B-orphans (OR1-OR3) | el factory no los consume | tabla de ausencias | ya homed en `DEUDA-B §B-orphans` | — |

### 2.5 Elementos de integrador (detalle simétrico L05 → `00-INTEGRADORES.md`)

**OI-FAC-1 · Componer el runtime (elegir el conjunto de batteries y pasarlo)** — amplía OI-18 (09) del *tool-set* a
la *composición entera*
- *capacidad:* todo integrador **decide qué es su runtime**: qué batteries compone (MCP, skills, memoria, plan,
  voz, tools nativas, compaction, resilience), con qué config cada una, y en qué orden. El base **no** trae un
  catálogo por defecto: sin composición hay un runtime núcleo que corre un turno de texto y nada más.
- *origen:* N5/S28 + la retirada de config de A1/17·C1 + `00-INTEGRADORES §1.5` (que hoy cubre sólo tools/exec_env).
- *firma que consume:* `create_runtime(config=RuntimeConfig(..., batteries=[...]))` con `Battery` (S28).
- *cableado en el integrador:* `agentic_code` (degenerado) compone **muchas** y usa defaults minimal;
  `agentic_assistant` (complejo) compone **selectivamente** y sustituye las que su orquestación ya posee.
- *orden:* prerrequisito de todo lo demás en Fase E/F; depende de RB-1/RB-2 en Fase B–C.
- *criterio de aceptación:* un runtime compuesto **sin** `battery_mcp` no importa `McpProvider` en ningún punto
  (aserción ejecutable de aislamiento, patrón `SKELETON-REPORT §4.4`); y componer dos integradores distintos sobre
  el mismo base no requiere tocar el base.

**OI-FAC-2 · Invocar y cerrar el ciclo de vida del ensamblado** — obligación universal hoy **no escrita** en
`00-INTEGRADORES.md`
- *capacidad:* `create_runtime` **no** arranca nada: los providers (p.ej. las conexiones MCP) se conectan en
  `await runtime.startup()` y se cierran en `await runtime.shutdown()`. Un integrador que no los llame tiene un
  runtime con capabilities registradas y **desconectadas**, sin error visible.
- *origen:* E1 (`runtime.py:118-128` → `manager.py`), C-cap2 (MCP conecta en startup, no al ensamblar), E2
  (cleanups no-provider = integrador), S23 (teardown por-agente, **ausente**).
- *firma que consume:* `await runtime.startup()` / `await runtime.shutdown()`; + registrar sus propios cleanups
  fuera del ámbito de providers.
- *cableado en el integrador:* degenerado = `startup` al arrancar el proceso CLI y `shutdown` en el `finally` del
  entrypoint; complejo = por tenant/worker, con el par ligado al ciclo de vida del pod y drenaje de tasks en curso.
- *orden:* inmediatamente tras OI-FAC-1; antes de `dispatch`.
- *criterio de aceptación:* un servidor MCP declarado responde a una tool tras `startup()` y no antes; tras
  `shutdown()` no queda conexión abierta; el proceso termina sin tareas colgadas.

**OI-FAC-3 · Declarar la completitud de su perfil de config (y consumir el fail-fast)**
- *capacidad:* el integrador declara qué exige su `execution_mode`/perfil (motor, modelo, storage, política de
  permisos) y **trata el fallo de ensamblado como fatal**, en vez de descubrirlo como un turno vacío.
- *origen:* CG-FAC-1 (E4/FaR1) + F2/F4 (trust y gate de entorno son del integrador, no del base).
- *firma que consume:* `RuntimeConfigError` de `create_runtime`; `allow_incomplete=True` **sólo** en tests.
- *cableado en el integrador:* degenerado = stderr + exit(1) (espejo `gracefulShutdownSync(1)`); complejo = health
  check que falla el arranque del pod y no admite tráfico.
- *orden:* con CG-FAC-1.
- *criterio de aceptación:* arrancar sin credencial/motor **no** produce un agente mudo: produce un fallo con la
  lista completa de campos faltantes.

**Caras-factory de cabos con hogar en otra categoría (detalle de la cara, remediación en su dueño):**

- **C2 (13·memory)** — *cara-factory:* hoy el extractor de memoria no se registra en ningún fire point; el canónico
  lo hace en el bootstrap (`setup.ts:294 initSessionMemory()`). *Bajo B la cara cambia de dueño:* no es «el factory
  registra el hook», es «`battery_memory.hooks(host)` devuelve `(Stop, extractor)` y el compositor lo registra»
  (S28). *Obligación del integrador:* proveer el `HookRunner` (hoy `RuntimeConfig.hook_runner=None` por defecto ⇒
  **aunque la battery devolviera el hook, no habría dónde registrarlo**) — dato nuevo de esta ronda que 13 debe
  conocer.
- **C3 (14·plan)** — *cara-factory:* `agent_resolver` se pasa tal cual (:237); en standalone es `None` ⇒ fork
  genérico. *Bajo B:* los built-ins Explore/Plan los aporta `battery_plan.agents(host)`, y el `agent_resolver` del
  integrador **compone** su catálogo con el de las batteries (no lo sustituye). *Obligación del integrador:*
  OI-PLAN-B ya escrita en 14.
- **C4 (07·events)** — *cara-factory:* el inventario para el frame `init` sólo existe completo en el ensamblador ⇒
  18 aporta **S29 `RuntimeManifest`** (el dato); 07 aporta el evento y su serialización.
- **C5 (15·storage)** — *cara-factory:* los stores de capability se construyen una vez, sin scope (`token_storage`
  con `user_id="mcp"` por defecto = colisión multi-usuario). *Bajo B:* `RuntimeHost.scope` (token **opaco**, no
  `user_id` interpretado) se pasa a cada battery stateful al componerse. Es un touchpoint del rollup **A3.DA**.
- **C6 (15/integrador)** — el `WorkerStateUploader` no es del factory; `agentic_assistant` lo respalda tras
  `StorageProtocol`.

### 2.6 Cabos que aterrizan fuera de 18

| cabo | destino | por qué no se resuelve aquí |
|---|---|---|
| Obligatoria-vs-opcional de cada battery (empezando por `battery_plan` incondicional) | **A3.CAT** | 18 fija el mecanismo de composición; el catálogo y sus defaults son el rollup de catálogo (`14-plan.md:234-236`) |
| Reparto final del hilo de identidad (A2, C5, `_channel` global) | **A3.DA** | No se resuelve categoría a categoría (`00-BLUEPRINT.md §2.1`) |
| Los 6 globals + los §B-orphans + `create_loop` | **A3.DB** | Rollup de higiene; aquí quedan con ancla y criterio |
| Firma final de S28/S29 | **Fase C** (validación real) | A2 **no** las ejercitó: A2.4 compuso una battery por constructor, no por catálogo (L09 — no se declaran validadas) |
| Fail-fast del bridge OAuth / `options.client` | **Fase D** (`agentic_models`) | es raíz del motor, no del ensamblado (`SEAMS.md §S3`) |

---

## §3 · GATEKEEPER de cierre (`00-LEGEND.md §3.3`)

> **Frase de rigor:** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo
> respalda; ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí
> quede sin colocar —o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá
> incompleto e inútil.

### Ledger — una fila por CADA finding (43)

| ID | TIER | destino | cara | evidencia | detalle desarrollado | nota-identidad |
|---|---|---|---|---|---|---|
| A1 | T2-COSTURA→DEUDA-B | reparto núcleo/battery | ambas | ensamblador `factory.py:78-117` 1→EOF | sí (§2.2 saldo 14+1 campos) | — |
| A2 | T2-COSTURA (S20) | rollup A3.DA | ambas | `runtime.py:198-218` 1→EOF | N/A (rollup transversal) | 【id-opaco】 autogen a ripear |
| A3 | T2-COSTURA | base | ambas | `factory.py:99-112` + `runtime.py:329-330,372-374` | sí (tipar + declarar en SEAMS) | — |
| A4 | T2-COSTURA | base + política integrador | ambas | `factory.py:95-98` → `runtime.py:96` | sí (§1) | — |
| A5 (=C3) | T2-COSTURA (S25) | 14·battery_plan | ambas | `factory.py:237` 1→EOF | sí (§2.5 cara-C3) | — |
| B1 | T2-BASE + S13 | base | ambas | `factory.py:182-186` + `storage/factory.py` 1→33 | sí (§1 + N4) | 【id-opaco】 clave repo |
| B2 (=C8) | T2-BASE + BATTERY | base + `tools-native` | ambas | `factory.py:189` + `tools/factory.py` 1→75 | sí (N5) | — |
| B3 (=C1) | DEUDA-B + S18 | base (DI) | ambas | `factory.py:178-240` (ausencia) + `runner.py` 1→41 + `agent.py:104-107` | sí (§2.4 B-runner-wiring) | — |
| B4 (=C10) | T2-COSTURA (S12) | base/integrador | ambas | `factory.py:207` → `runtime.py:317` | sí (§1) | 【id-opaco】 no filtrar rutas |
| B5 | T2-COSTURA (S15) | base/integrador | ambas | `factory.py:210,228` → `runtime.py:318` | sí (§1) | — |
| B6 | T2-BASE (S14) | base | base | `runtime.py:322-325` + `context/tool_use.py:16-20` 1→EOF | sí (§1) | — |
| B7 (=C10/17·C1) | BATTERY→DEUDA-B | `battery_voice` | ambas | `factory.py:214-216,238-239` | sí (§2.2) | — |
| C-cap1 | BATTERY | `battery_plan` / A3.CAT | ambas | `factory.py:141,146` | sí (§2.2 + §2.6) | — |
| C-cap2 | BATTERY + lifecycle | `battery_mcp` | ambas | `factory.py:140,148-158` | sí (§2.5 OI-FAC-2) | 【id-opaco】 `user_id="mcp"` |
| C-cap3 | BATTERY | `battery_skills` | ambas | `factory.py:142,160-164` | sí (§2.2) | — |
| C-cap4 (=C2) | BATTERY + CORE-GAP(13) | 13·MeR | ambas | `factory.py:166-172` + `RuntimeConfig.hook_runner=None` :86 | sí (§2.5 cara-C2) | 【id-opaco】 store sin scope |
| C-cap5 (=C5) | CORE-GAP(15) + T2-COSTURA | 15·StR / A3.DA | ambas | `factory.py:132,174` 1→EOF | sí (§2.5 cara-C5 + S28 `scope`) | 【id-opaco】 **central** |
| D1 (=C7) | T2-BASE | base | ambas | `factory.py:243-267` 1→EOF | sí (§1) | — |
| D2 | T2-COSTURA | base | ambas | `factory.py:124-129` | sí (N6) | — |
| D3 | T3-INTEGRADOR | `agentic_assistant` (OI-15) | integrador | `factory.py:264-265` | sí (05·E31 + §1) | 【id-opaco】 affinity |
| D4 (=FaR3) | DEUDA-B cosmético | base | base | `factory.py:129` | N/A (DEUDA-B) | — |
| E1 | T2-BASE + OI | base + **OI-FAC-2** | ambas | `runtime.py:118-128` + `manager.py` 1→111 | sí (§2.5 OI-FAC-2) | — |
| E2 | 🔀 + T3 | integrador | integrador | `runtime.py:126-128` (ausencia de registry) | sí (§1, con reserva S23) | — |
| E3 (=C4) | CORE-GAP(07) | 07·EvR + **S29** | ambas | `factory.py` 1→EOF (ausencia de emisión) | sí (§2.1 S29 + §2.5 cara-C4) | — |
| E4 (=FaR1) | **CORE-GAP propio (keystone)** | base — CG-FAC-1 | ambas | `factory.py:253-267` + `agent_loop.py:181-183` 1→EOF | sí (6 campos, §2.3) | — |
| F1 | T2-BASE | base | base | `factory.py:186→240` (orden leído) | sí (§2.1 S28 `requires()`) | — |
| F2 | T3-INTEGRADOR | integrador | integrador | tracker (`setup.ts` 477 1→EOF) | sí (§1 + OI-FAC-3) | — |
| F3 | 🔀 por diseño B | per-ctx/session | base | tracker (`state.ts` 1758 1→EOF) | sí (§1, matizado por N4) | 【id-opaco】 multi-sesión |
| F4 | T3-INTEGRADOR + B-02 | integrador / 06 | integrador | tracker (`setup.ts:395-442`) | sí (§1 + OI-FAC-3) | — |
| F5 | N/A semántica | — | base | `factory.py:243-267` | sí (§1: no-memoizar es correcto multi-tenant) | 【id-opaco】 N runtimes |
| C6 | T3-INTEGRADOR | `agentic_assistant` (15·STOR11) | integrador | tracker-leído (⛔ fuera del factory) | sí (§2.5) | 【id-opaco】 clave sidecar |
| C9 | T2-BASE | 02·loop | base | `agent_loop.py` `_build_tool_pool` (tramo leído) | N/A (cerrado, no era del factory) | — |
| FaR2 | DEUDA-B estructural | base | base | `factory.py:197-201,222` + `agent_loop.py:194,201-205` 1→EOF | sí (§2.4 + acople N1) | — |
| OR1 | DEUDA-B (16) | `DEUDA-B §B-orphans` | base | `factory.py` 1→EOF (0 lecturas de `.models`) | N/A (ausencia) | — |
| OR2 | DEUDA-B (05/S19) | `DEUDA-B §B-orphans` | base | `factory.py:224` + `tasks/registry.py:153` | N/A (ausencia) | — |
| OR3 | DEUDA-B (04/05/08/09) | `DEUDA-B §B-orphans` | base | `factory.py` 1→EOF + `observer.py:28` | N/A (ausencia) | — |
| OR4 | interno de providers | sus categorías | base | tracker-leído | N/A | — |
| **N1** | DEUDA-B estructural | base | base | `loop/factory.py` 1→27 + `loop/protocol.py` 1→27 + `agent_loop.py:194-207` + ausencia de consumidores | sí (§2.4 B-create-loop) | — |
| **N2** | T1-CONTRATO + DEUDA-B | base | ambas | `factory.py:34-117,132,178,247` 1→EOF + los 9 `*/protocol.py` 1→EOF | sí (§2.3b RB-3) | 【id-opaco】 tipar ≠ tipar identidad |
| **N3** | T2-COSTURA | base | base | `runtime.py:79,218-240` + `agent_loop.py:62,78-80` + `factory.py:204` | sí (§2.4 B-unreachable-knobs) | — |
| **N4** | DEUDA-B transversal | base (deps-DI) | ambas | 6 anclas 1→EOF (`factory.py:125`, `storage/factory.py:17`, `tasks/registry.py:153`, `notification.py:22`, `observer.py:28`, `runner.py:28`) | sí (§2.4 B-global-registries) | 【id-opaco】 `_channel` global = fuga multi-tenant |
| **N5** | T2-COSTURA nueva (S28) | base + batteries | ambas | `factory.py:132-175` 1→EOF + `tools/factory.py` 1→75 | sí (§2.1 S28 firma + §2.2 saldo) | 【id-opaco】 `RuntimeHost.scope` |
| **N6** | T2-COSTURA (enriquecer) | base | ambas | `factory.py:124-129,260-262` + `contracts/runtime.py:35-67` 1→EOF | sí (§2.3b RB-6) | — |

### 5 preguntas de cierre

1. **¿Se leyó ÍNTEGRO `../18-factory.md`?** **Sí — 1→470** (esta sesión, con el Read tool, no por tramos ni grep).
   Incluye la §Re-visita de gate-11 (330-470) y sus dos ledgers de lectura.

2. **¿Reconcilia el conteo?** Findings del tracker = **33** (rejilla A1-A5·5 + B1-B7·7 + C-cap1..5·5 + D1-D4·4 +
   E1-E4·4 + F1-F5·5 = **30**; + **C6** y **C9**, únicos cabos de §Convergencia sin fila en la rejilla; + **FaR2**,
   sin fila propia). Colocados = **33**; sin colocar = **0**. Los demás cabos son **alias verificados**, no findings
   nuevos: C1=B3 · C2=C-cap4 · C3=A5 · C4=E3 · C5=C-cap5 · C7=D1/D4 · C8=B2 · C10=B4/B7 · FaR1=E4 · FaR3=D4 — se
   citan, **no se re-cuentan** (evitar el doble conteo es la razón de esta nota). El ledger lleva **43** filas =
   33 vinculantes + **4** verificaciones de ausencia (OR1-OR4, ya homed en `DEUDA-B §B-orphans`) + **6** findings
   NUEVOS de esta ronda (N1-N6), que **no** estaban en el tracker y se declaran como adición, no como recuento.

3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador, sin grep?** **Sí — pero SÓLO tras una 2ª
   iteración: el 1er cierre SOBRE-DECLARÓ esta pregunta y su ✅ quedó RETRACTADA.** Lo que el gate encontró y lo
   que se hizo:
   - **Sobre-declarado en la 1ª pasada** (declarado 1→EOF sin estarlo): `00-LEGEND.md` («1→158» cuando lo abierto
     fue §3.1-§5 = 95-158; el esquema §1/§2 se aplicó **de memoria de ciclos previos**) · `runtime.py` y
     `agent_loop.py` («1→EOF en la fase previa» cuando lo registrado eran **tramos**) · `manager.py` 111 ·
     `resolver.py` 82 · `agents.py` 66 · `runner.py` 41 · `tools/factory.py` 75 · `loop/protocol.py` 27 (listados
     como abiertos sin registro de lectura) · y **`tasks/registry.py:153` + `observer.py:28`**, de los que escribí
     «cada una **abierta** en su archivo» cuando salieron del **barrido grep** ⇒ N4 se apoyaba en grep en 2 de sus
     6 anclas.
   - **Abiertos 1→EOF en la 2ª pasada** (todos, sin excepción): `00-LEGEND.md` 1→94 (el resto ya leído) ·
     `execution/local/runtime.py` **1→435** · `loop/agent_loop.py` **1→352** · `capabilities/manager.py` 1→111 ·
     `capabilities/resolver.py` 1→82 · `execution/agents.py` 1→66 · `execution/runner.py` 1→41 ·
     `execution/tasks/registry.py` **1→166** · `execution/observer/observer.py` 1→37 · `tools/factory.py` 1→75 ·
     `loop/protocol.py` 1→27.
   - **Resultado del re-examen: 0 cambios de clasificación** (los 43 se sostienen) y **2 precisiones que la
     inferencia no daba**: (a) **S24 `arm_watchdog` era "existe-noop" HEREDADO del tracker y ahora está PROBADO** —
     `dispatch` sí lo llama (`runtime.py:149`) y el default `InMemoryTaskRegistry.arm_watchdog` es un literal
     `pass` (`registry.py:88-91`); además el timeout **per-task** SÍ es alcanzable (`RuntimeTask.timeout_seconds`),
     luego N3 se acota al **default** del constructor; (b) **S28 es más barata de lo que N5 sugería** —
     `CapabilityManager.__init__` ya recibe una `list[CapabilityProvider]` y no conoce ningún provider concreto
     (`manager.py:26-27,36-96`), así que el hardcodeo por nombre vive **sólo en el factory**: S28 alimenta el
     manager, no lo reescribe.
   - Resto de archivos abiertos 1→EOF ya en la 1ª pasada: `factory.py` 1→267 · `storage/factory.py` 1→33 ·
     `loop/factory.py` 1→27 · `execution/local/notification.py` 1→72 · `execution/__init__.py` 1→21.
   - Contratos (base de la tesis de N2/N6): `capabilities/contracts.py` 1→76 · `capabilities/protocol.py` 1→25 ·
     `contracts/{__init__ 17, runtime 67, storage 40, permissions 33, compaction 27, user_input 46}` ·
     `context/tool_use.py` 1→70 · `tools/{protocol 61, dispatcher 84, registry 37, pool 78}` ·
     `storage/protocol.py` 1→87 · `models/protocol.py` 1→37 · `events/protocol.py` 1→22 · `hooks/protocol.py` 1→72 ·
     `voice/protocol.py` 1→58.
   - Corpus SEPARACION sobre el que descansa la clasificación: `00-BLUEPRINT.md` **1→185
     (abierto ÍNTEGRO esta ronda — 17 lo dejó declarado como no abierto)** · `00-INTEGRADORES.md` 1→207 ·
     `SEAMS.md` 1→435 · `SKELETON-REPORT.md` 1→138.
   - **Grep usado SÓLO para probar AUSENCIA** (y corroborado por la lectura 1→EOF del ensamblador): consumidores de
     `create_loop` (=∅ salvo el re-export) y el barrido de globals de módulo (6 anclas, cada una **abierta** en su
     archivo).
   - **Lectura NO íntegra, declarada:** `PLAN.md` §7 (líneas 110-132) se leyó **truncada a 600 chars/línea** con
     `awk` porque el Read tool excede el límite de tokens en esas líneas; suficiente para identificar el primer
     ciclo sin marcar, insuficiente para citar su contenido completo — y así se declara. Los trackers `../13`,
     `../14`, `../15`, `../17` **no** se re-abrieron íntegros: de 14 y 17 se leyeron los tramos exactos citados
     (`14-plan.md:15-40,230-236,286-292` · `17-voice.md:94,356,380-381,407`), y de 13/15 se toma lo que el tracker
     de 18 y `SEAMS.md` ya destilaron. No sostengo ninguna clasificación **nueva** sobre 13/15 más allá de repetir
     su hogar.

4. **¿La cara integrador quedó al MISMO detalle que la base?** Sí: **OI-FAC-1/2/3** con los 6 campos (capacidad ·
   origen · firma · cableado · orden · aceptación), más las **4 caras-factory** de C2/C3/C4/C5 desarrolladas
   individualmente (§2.5) y C6/D3 con destino nombrado. Ningún «→ integrador» a secas. **OI-FAC-2 es una obligación
   universal que `00-INTEGRADORES.md` no tenía escrita** (§1.2 cubre el caller, no la invocación del ciclo de vida).

5. **¿Doble filo (L10)?** Sí, en ambas direcciones y nombrado:
   - **No inflo:** el ensamblado nuclear se declara ✅ **cableado en ruta real** (storage/tools/caps/presentation/
     exec_env/voz/lifecycle/orden F1), C1-C5 **no** se re-cuentan como deuda de 18, los §B-orphans **no** son
     CORE-GAP, y los requisitos de re-arquitectura B se separan **explícitamente** de `DEUDA-A.md` (§2.3b) porque el
     canónico no tiene un mecanismo mejor: llamarlos «brecha A↔B» sería fabricar deuda.
   - **No acredito divergencia como des-fusión correcta:** el 🔀 «el runtime no tiene singleton global» del tracker
     se **acota** con N4 — es cierto para el estado de sesión (F3) y **falso** para el registro de mecanismo (6
     globals de proceso, uno de ellos `_channel` con clave `(user_id, session_id)` ⇒ fuga entre runtimes del mismo
     proceso). Y la remediación FaR2 del tracker se corrige: tal como está escrita **rompe** `create_loop` (N1) sin
     decirlo.

### §Honestidad — lo NO verificado primero

- **S28 `Battery` y S29 `RuntimeManifest` son firmas BORRADOR sin validar por ejecución.** A2 **no** ejercitó
  composición por catálogo (A2.4 compuso **una** battery por constructor). No hay evidencia-de-correr detrás de
  ellas; su hogar de validación es Fase C. No las cuento como costuras existentes.
- **El reparto de 14 campos de config a batteries (§2.2) es un cálculo sobre la config actual, no un diseño
  ejecutado.** Nadie ha comprobado que `battery_mcp` funcione con esos 5 campos y ninguno más.
- **No re-abrí los trackers 13/15 ni los `SEPARACION/13,15` íntegros** (ver pregunta 3). Las caras-factory de C2/C5
  las desarrollo desde el ensamblador y desde lo ya destilado; si 13/15 tienen matices que contradigan mi
  desarrollo, mandan ellos.
- **El dato nuevo `RuntimeConfig.hook_runner=None` por defecto** (⇒ C2 no tiene dónde registrarse aunque la battery
  aporte el hook) lo deduzco de la lectura del ensamblador; **no** verifiqué si algún test o integrador lo puebla
  hoy — no hay integrador aún, así que la afirmación se limita a `create_runtime` standalone.
- **`PLAN.md` §7 leído truncado** (600 chars/línea), declarado arriba.
- **No corrí ningún test ni código** en este ciclo: A3 es diseño, no implementación. Las 3 xfail(strict) que el
  tracker cita (C1/FaR1/FaR2) se toman de su ledger, no re-ejecutadas.
- **Corrijo una nota de mi propia memoria:** decía que 14·§0.1b difería el patrón de config a 18; **14 lo difiere a
  A3.CAT** (`14-plan.md:234-236`). Sólo 17 difiere a 18 (`17-voice.md:380-381`).
- **No me acredito rigor:** el número de iteraciones y la suficiencia de las lecturas los dictamina el gate del
  usuario, no este documento.

### VEREDICTO

**⚠ La ✅ de la 1ª pasada quedó RETRACTADA por Q3 (ver arriba): 11 archivos declarados 1→EOF sin estarlo, y 2 de
las 6 anclas de N4 apoyadas en grep. Abiertos todos en la 2ª pasada; 0 cambios de clasificación, 2 precisiones
(S24 probado, S28 más barata). Reproche recurrente por 6ª vez (04·11·12·14·17·18) y de clase nueva otra vez: aquí
el fallo no fue omitir archivos, fue DECLARAR como leído 1→EOF lo que se había leído por tramos o heredado de una
fase previa de la misma sesión. Regla dura que se añade: una lectura de una fase previa (o anterior a una
compactación de contexto) NO cuenta como "abierto este ciclo" — o se re-abre, o se declara como heredada.**

**✅ NADA PENDIENTE → A3.DA** (ganado en 2ª iteración). 33 findings del tracker colocados (0 sin colocar) + 4 ausencias verificadas + 6
findings nuevos declarados. 1 CORE-GAP propio (CG-FAC-1, keystone, 6 campos), 6 requisitos de re-arquitectura B
separados del rollup de deuda, 7 ítems de DEUDA-B con ancla y criterio, 2 costuras nuevas propuestas como BORRADOR
no validado, 3 obligaciones universales de integrador con detalle simétrico + 4 caras-factory desarrolladas, 5
cabos con destino explícito (A3.CAT · A3.DA · A3.DB · Fase C · Fase D).

**Con 18 cerrado, los 18 ciclos por-categoría de A3 quedan COMPLETOS.** Siguiente = **A3.DA** (rollup transversal
de identidad → `DEUDA-A.md`).
