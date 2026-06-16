# Plan: Capabilities — Skills, MCP, Voz (STT/TTS) Y Memoria

Estado general: `[ ] no iniciado` `[~] en progreso` `[x] completado`

Estado actual: `[ ] no iniciado`

## Objetivo

Implementar una capa de capabilities que conecte skills y MCP al runtime agentico mediante primitivas estables, reproduciendo el comportamiento del proyecto de referencia `claude-code`.

Este plan no busca mejorar el comportamiento aun. Busca alinearlo.

> **Re-base 2026-06-14.** Las primitivas de runtime (fork, background, `agent_id`, notificación,
> `EventBus`) ya **no** son trabajo de este plan: las provee de forma nativa
> `PLAN_COMPLEMENTARIO_RUNTIME.md` (runtime reescrito, agent_core descartado por D4). Este plan
> cubre solo la **capa de capabilities sobre el runtime nuevo**: Skills, MCP y —agregado aquí—
> STT/TTS como capability de I/O por voz. Las secciones que referían al primer plan
> (`PLAN_RUNTIME_AGENTICO.md`) o a internals de agent_core quedaron superadas por el complementario.

## Principio Rector

Skills y MCP no deben vivir dentro del runtime. Deben ser providers conectados por contratos:

- aportan catalogo;
- aportan tools;
- procesan comandos o llamadas;
- modifican contexto mediante `context_modifier`;
- aportan contexto para compactacion;
- mantienen su propio estado.

El runtime no debe saber si una tool viene de MCP, skill, plugin u otra capability.

## Referencia De Comportamiento

Patrones a replicar desde `claude-code`:

- MCP vive en `appState.mcp.tools`, `appState.mcp.commands`, `appState.mcp.resources`.
- `assembleToolPool(permissionContext, mcpTools)` combina tools base y MCP.
- Skills se modelan como comandos.
- `SkillTool` obtiene comandos locales y MCP skills.
- `processPromptSlashCommand` produce mensajes, `allowedTools`, `command_permissions`.
- `SkillTool` devuelve `newMessages` y `contextModifier`.
- `invoked_skills` se conserva para compactacion como "continue to follow these guidelines".

## Arquitectura Objetivo

```text
capabilities/
  manager.py
  contracts.py

  skills/
    provider.py
    loader.py
    command_processor.py
    skill_tool.py
    compaction.py
    state.py

  mcp/
    provider.py
    client.py
    tool_adapter.py
    resources.py
    state.py
```

Los nombres finales pueden variar, pero las responsabilidades deben quedar separadas.

## Contratos Comunes

### CapabilityProvider

Estado: `[x] completado`

Responsabilidad:

- exponer tools;
- exponer catalogo;
- activar capacidades;
- aportar contexto activo;
- aportar compactacion;
- manejar startup/shutdown si aplica.

Forma sugerida:

```python
class CapabilityProvider(Protocol):
    name: str

    async def startup(self) -> None: ...
    async def shutdown(self) -> None: ...

    def catalog(self, context: ToolUseContext) -> list[CapabilitySummary]: ...
    def tools(self, context: ToolUseContext) -> list[Tool]: ...
    def active_context(self, context: ToolUseContext) -> list[dict]: ...
    def compact_context(self, context: ToolUseContext) -> list[dict]: ...
```

### CapabilityManager

Estado: `[x] completado`

Responsabilidad:

- coordinar providers;
- construir catalogos;
- construir tools de capability;
- aplicar activaciones;
- aportar contexto a chat/prompts;
- reemplazar logica dispersa en API/runtime/registry.

Criterios:

- El runtime solo habla con el manager o recibe su resultado.
- Skills/MCP no escriben en `SessionMetadata` directamente salvo adapter temporal.

### CapabilitySummary

Estado: `[x] completado`

Responsabilidad:

- representar una capability visible al modelo.

Campos sugeridos:

- `name`
- `kind`: `skill`, `mcp_tool`, `mcp_resource`, etc.
- `description`
- `when_to_use`
- `provider`
- `deferred`

### CapabilityActivation

Estado: `[x] completado`

Responsabilidad:

- resultado estructurado de activar una capability.

Campos sugeridos:

- `tools_to_enable`
- `messages_to_append`
- `permission_rules`
- `active_state`
- `refresh_tool_pool`

## Skills Provider

### Objetivo

Mover el soporte de skills fuera de runtime/loop/API y alinearlo al comportamiento de referencia.

### Estado Actual Detectado

Problemas actuales:

- `SkillTool` inyecta `SKILL.md` como mensaje `user` normal.
- `SkillTool` solo registra nombre en `session.metadata.invoked_skills`.
- `allowed-tools` se resuelve indirectamente en `runtime.py`.
- `sections.py` fuerza `call Skill FIRST` antes de cada output.
- `chat.py` inyecta catalogo completo en cada mensaje.
- `compactor.py` dice "re-invoke" en vez de "continue to follow".
- `loop.py` expande slash inline skills.
- Tests actuales permiten reinvocacion, lo cual ya no representa el comportamiento deseado.

### Comportamiento Objetivo

Skill invocation debe producir:

- mensajes meta con contenido de la skill;
- `allowedTools` estructurados;
- attachment o equivalente `command_permissions`;
- `context_modifier` que agrega permisos al contexto;
- registro de skill invocada con nombre, path, contenido, tiempo y agent id si aplica;
- contexto de compactacion que diga "continue to follow these guidelines".

### Tareas

#### Fase S0 - Provider shell

Estado: `[x] completado`

- [x] Crear `SkillsProvider` (segundo `CapabilityProvider` concreto, `capabilities/skills/`).
- [~] Mover acceso a `skills.loader` detras del provider. → N/A en este repo: no existe loader de
      skills heredado (eso era `new_core`). El loader nace dentro del provider (`skills/loader.py`),
      detrás de él; el integrador carga vía `provider.load_dir(...)`.
- [x] Exponer catalogo desde provider (`catalog(context)` → `CapabilitySummary(kind="skill")`).
- [~] Mantener `SkillTool` actual como adapter temporal. → N/A (no hay `SkillTool` heredado). La tool
      de invocación `Skill` se construye en S1; en S0 `tools()` devuelve `[]` (shell honesto).
- [x] Tests de catalogo.
- [x] Parseo de frontmatter **tolerante** (`skills/frontmatter.py`): `SkillFrontmatter` (`extra="allow"`,
      todo campo operativo `Optional` con validadores `mode="before"` que degradan tipos inválidos a
      default); `parse_frontmatter` nunca lanza (sin frontmatter / YAML inválido / no-mapping → `{}`).
- [x] Aislamiento por ítem: `load_skills_dir` salta con log un `SKILL.md` ilegible; un frontmatter
      corrupto carga igual con defaults (identidad desde el directorio), no aborta la carga del resto.

Criterios:

- `chat.py` puede pedir catalogo al manager, no a `skills.loader`. ✓ (vía `CapabilityManager.catalog`;
  el wiring real en `chat.py` es fase C — el contrato ya lo permite).
- No cambia comportamiento aun. ✓ (`tools/active_context/compact_context` vacíos; declarado, no fingido).
- Una skill de terceros con frontmatter mínimo (solo `name`/`description`, sin `allowed-tools`
  ni `model`) carga y opera con defaults definidos: no activa tools extra; hereda el modelo del padre. ✓
- Tests: frontmatter ausente/parcial/malformado → carga estable con defaults, sin excepción. ✓

Evidencia S0: `capabilities/skills/{frontmatter,loader,state,provider}.py`. `SkillFrontmatter`
(`extra="allow"`, `allowed-tools` acepta lista o CSV, `name`/`description`/`model` no-string → `None`).
`parse_frontmatter` total. `SkillDefinition` tipada: `name` ← dir cuando falta, `description` ← primer
párrafo del cuerpo cuando falta, `model` ø/`inherit` → `None` (hereda), `allowed_tools` ø → `[]`.
`load_skills_dir` aísla por ítem. `SkillsProvider` cumple `CapabilityProvider`; su catálogo converge por
`CapabilityManager`. 18 tests en `test_skills_provider.py`. Dependencia nueva: `pyyaml` (parseo YAML del
frontmatter, espejo del canónico; no estaba en el repo).

#### Fase S1 - Skill como comando procesado

Estado: `[ ] no iniciado`

- [ ] Crear `SkillCommandProcessor`.
- [ ] Renderizar skill con metadata.
- [ ] Producir mensajes meta, no mensaje user plano.
- [ ] Producir `allowed_tools`.
- [ ] Producir `command_permissions` o equivalente Python.
- [ ] Registrar invoked skill con contenido completo.

Criterios:

- Una invocacion de `Skill` deja estado activo estructurado.
- El modelo recibe instrucciones de skill sin tener que reinvocar.

#### Fase S2 - Context modifier de skills

Estado: `[ ] no iniciado`

- [ ] `SkillTool` devuelve `context_modifier`.
- [ ] El modifier agrega allowed tools al `PermissionContext`.
- [ ] El modifier agrega skill activa al `AppState`.
- [ ] El runtime no deriva tools desde `invoked_skills`.

Criterios:

- `models/gpt_5_4/runtime.py` no contiene `_allowed_tools_for_invoked_skills`.
- Tests verifican que allowed tools aparecen por permisos/contexto.

#### Fase S3 - Catalogo organico

Estado: `[ ] no iniciado`

- [ ] Mover construccion del catalogo a `SkillsProvider`.
- [ ] Eliminar regla global "SKILL CHECK before EVERY step" de `sections.py`.
- [ ] Catalogo debe servir para seleccion, no para reinvocacion.
- [ ] Si una skill esta activa, el contexto debe decir que se continue siguiendo sus instrucciones.

Criterios:

- Follow-ups no reinvocan skill por defecto.
- `Skill(drawio-diagrams)` seguido de tareas internas habilita `drawio__*`.

#### Fase S4 - Slash commands

Estado: `[ ] no iniciado`

Prerequisito: primitivas fork del runtime (provistas por el complementary plan).

- [ ] Sacar `skills.dispatcher` del loop.
- [ ] Procesar slash commands mediante provider/command processor.
- [ ] Mantener compatibilidad con `/skill args`.
- [ ] Fork/background pasan por `ForkContext` via `RuntimeContextForker` — ver Primitivas Fork Y Background.

Criterios:

- `core/loop.py` no importa `skills.dispatcher`.
- Slash skill produce los mismos eventos que antes o equivalentes documentados.
- La capability no decide como se hereda el contexto del fork — lo decide `ForkPolicy`.

#### Fase S5 - Compaction

Estado: `[ ] no iniciado`

- [ ] SkillsProvider aporta compact context.
- [ ] El texto debe seguir referencia: "continue to follow these guidelines".
- [ ] Eliminar "re-invoke" de compactor base.
- [ ] Guardar contenido de skills invocadas, no solo nombres.

Criterios:

- Tras compactacion no se pierde skill activa.
- Tras compactacion no se induce reinvocacion.

### Tests Skills

- [ ] Invocar skill agrega active skill context.
- [ ] Invocar skill agrega allowed tools al permission context.
- [ ] Follow-up usa tools permitidas sin reinvocar skill.
- [ ] Compaction preserva instrucciones de skill.
- [ ] No se inyecta catalogo como mandato de reinvocacion.
- [ ] Slash inline funciona via provider.
- [ ] Fork/background siguen funcionando.

## MCP Provider

### Objetivo

Mover MCP fuera del registry nativo y alinearlo al patron de referencia: MCP state separado + tool pool assembler.

### Estado Actual Detectado

Problemas actuales:

- `main.py` registra MCP wrappers directamente en `ToolRegistry`.
- `ToolRegistry` identifica MCP por `__`.
- `ToolRegistry` usa `skills.state` para visibilidad MCP.
- `runtime.py` usa `session.metadata.discovered_deferred_tools`.
- `ToolSearch` activa MCP escribiendo en session metadata.
- `api/routes/mcp.py` toca `loop._registry`.
- `MCPListResources` y `MCPReadResource` dependen directamente de `mcp.loader`.
- Gmail tools son nativas pero dependen del MCP loader global.

### Comportamiento Objetivo

MCP debe mantener estado propio:

- servers conectados;
- tools MCP;
- commands MCP si aplica;
- resources MCP;
- pending/failed servers;
- activaciones deferred por sesion/contexto.

Tool pool final se obtiene desde el manager, no registrando MCP como nativas.

### Tareas

#### Fase M0 - Provider shell

Estado: `[x] completado`

- [x] Crear `McpProvider` (primer `CapabilityProvider` concreto, `capabilities/mcp/`).
- [~] Mover `load_mcp_tools` detras del provider. → N/A en este repo: no existe loader MCP
      heredado (eso era `new_core`). En su lugar el provider define el **punto de inyección**:
      el integrador conecta servers/transporte y registra specs; el transporte (`McpCall`) se
      inyecta, el shell no lo implementa (ciclo de vida real = M1).
- [~] Mantener wrappers actuales como adapter temporal. → N/A (no hay wrappers heredados).
- [x] Exponer `mcp.tools` desde provider (`tools(context)` vía `McpState.all_tools()`).
- [x] Exponer `mcp.resources` desde provider (`resources(context)`).
- [ ] Config de server **tolerante en lo operativo, estricta en lo de seguridad** (ver "Robustez
      ante skills/MCP de terceros"): props no estándar (p.ej. `model`) → `Optional` + default;
      validez de config/identidad del server → validación dura que rechaza explícitamente.
- [ ] Aislamiento por ítem: un server/tool malformado se salta con log, no tumba al resto.
- [ ] Campos de tool del estándar pero opcionales (annotations/hints) → default seguro (`?? false`).

Criterios:

- `main.py` inicializa provider.
- El registry nativo no necesita cargar MCP para startup.
- Un MCP de terceros sin las props no estándar opera con defaults; una config de server inválida
  se rechaza con error claro (borde de seguridad), no se ignora silenciosamente.
- Tests: tool MCP sin annotations → default; server con config inválida → rechazo explícito.

Evidencia M0: `capabilities/mcp/{config,tool_adapter,state,provider}.py`. `McpServerConfig`
(`extra="allow"`, `command` xor `url` validado → rechaza). `parse_server_config` estricto (lanza),
`load_server_configs` tolerante (salta con log). `build_mcp_tool` tolerante (annotations opcionales,
sin `name` → omite). `McpProvider` cumple `CapabilityProvider`; sus tools convergen por
`CapabilityManager.build_tool_pool`. 17 tests en `test_mcp_provider.py`.

#### Fase M1 - Estado MCP separado

Estado: `[x] completado`

- [x] Crear `McpState`. → ya existía (M0); M1 le añade clients + estado de conexión.
- [x] Guardar servers, clients, tools, resources (`McpState`: `_clients`, `_status`, `_errors`).
- [x] Mover `_clients` fuera de globals o encapsularlos → viven en `McpState`, no en globals;
      el provider los gestiona por su ciclo de vida.
- [x] Dejar API de acceso por provider (`connect_server`, `startup`/`shutdown`, `state.clients/...`).

Criterios:

- Resource tools no llaman `mcp.loader` directamente. ✓ (no hay loader global; el client encapsula
  el transporte; `resources()` sale del estado poblado por `connect_server`).
- Gmail adapter recibe provider/client resolver. → N/A en este repo (no hay Gmail adapter heredado).

Evidencia M1: `capabilities/mcp/client.py` (`McpClient`: transporte stdio/streamable-http vía SDK `mcp`,
`connect`/`list_tools`/`list_resources`/`call`/`read_resource`/`aclose`; `McpToolError` mapea
`isError`→error sin re-llamar). `McpState` con `ServerStatus` (configured/pending/connected/failed) +
`pending_servers`/`failed_servers`/`connected_servers`. `McpProvider.connect_server` descubre y registra
tools/resources con aislamiento por ítem; `startup` conecta todos, un server caído se marca FAILED y no
aborta el resto; `shutdown` cierra todos los clients. Transporte inyectable (`client_factory`) para tests.
6 tests en `test_mcp_client.py` (cliente fake). No unit-testeado el transporte real (necesita un server
MCP vivo — se cubrirá con la referencia real al integrar).

#### Fase M2 - Tool pool MCP

Estado: `[x] completado` (incluye cableado C1/C2 — aprobado explícitamente, R4)

- [x] Sacar MCP wrappers del registry nativo → nunca estuvieron ahí; el dispatcher ya NO usa el
      registry nativo para ejecutar. Las MCP viven solo en el provider.
- [x] `McpProvider.tools(context)` devuelve tools activas (desde `McpState`).
- [x] `ToolPoolAssembler` combina native + MCP → `CapabilityManager.build_tool_pool` + `ToolPool.assemble`.
- [x] Deduplicar con prioridad native (en `assemble_tool_pool`, ya desde C0).
- [x] Orden estable siguiendo referencia (native prefijo, ambos sorted por nombre — cache-estable).

**Alineamiento canónico (contrastado, ver memoria de decisión):** el canónico resuelve la ejecución
con `findToolByName(toolUseContext.options.tools, name)` — el MISMO pool ensamblado que anuncia, no un
registry aparte. Adaptación aprobada: el loop ensambla `ctx.tool_pool` por turno
(`manager.build_tool_pool(registry.list_available(mode), ctx)`), deriva los schemas de él, y el
`ToolDispatcher` resuelve la ejecución desde `ctx.tool_pool.find(name)`. El `ToolRegistry` pasó a ser
solo **input** del ensamblado (análogo `getAllBaseTools()`), ya no lookup de ejecución.

Criterios:

- `registry.py` no interpreta nombres con `__`. ✓ (nunca lo hizo; el dispatcher ya no lo consulta).
- `main.py` no registra MCP wrappers en registry nativo. ✓ (no hay main.py; el provider las posee y
  convergen por el manager).

Evidencia M2/cableado: `ToolPool.find` (findToolByName), `ToolDispatcher` sin registry (resuelve de
`ctx.tool_pool`), `AgentLoop` (`tool_registry`+`capability_manager`: `_build_tool_pool`+`_schemas_for_turn`),
`LocalAgentRuntime` (`startup`/`shutdown` conectan/cierran providers), `factory._build_capability_manager`
(registra McpProvider/SkillsProvider desde `CapabilitiesConfig.mcp_servers`/`skill_dirs`/`extra_providers`).
Tests: `test_capability_wiring.py` (4: anuncio+ejecución de tool MCP desde pool con registry nativo vacío,
factory registra provider, startup conecta). Migrados a pool: dispatcher/agent_loop/path_presentation/
runtime_v2/runtime_e2e/runtime_factory. Suite 255 passed. Lint limpio.

#### Fase M3 - Deferred loading

Estado: `[x] completado`

- [x] Mover `discovered_deferred_tools` a `CapabilityState` → estado de descubrimiento en
      `ctx.app_state.capabilities["discovered_tools"]`, scopeado por agente (`tools/deferred.py`:
      `discovered_tool_names`/`mark_tools_discovered`). No vive en `session.metadata`.
- [x] `ToolSearch` descubre (activa): marca las matched en el estado del contexto y devuelve sus
      schemas; en turnos siguientes se anuncian. (No llama un `manager.activate` aparte — la activación
      ES el descubrimiento, como en el canónico vía historial; aquí materializado en el contexto.)
- [~] Skills allowed-tools activa MCP tools via permission/context → la activación va por
      descubrimiento (ToolSearch) + permiso, no por el runtime. El cruce skill→MCP se cierra en S2.
- [x] El runtime/loop no recibe `deferred_loading_enabled` como lógica MCP → la proyección diferida
      vive en `_schemas_for_turn` del loop sobre `is_deferred_tool`, agnóstica de MCP.

**Alineamiento canónico:** `isDeferredTool` (MCP siempre diferido; ToolSearch nunca) → `is_deferred_tool`.
`claude.ts` arma el anuncio = no-diferidas + ToolSearch + diferidas DESCUBIERTAS, y descarta ToolSearch
si no hay diferidas → replicado en `_schemas_for_turn`. **Deferred es visibilidad, no disponibilidad**:
la tool diferida sigue ejecutable desde `ctx.tool_pool` aunque no se anuncie (test que lo prueba).

Criterios:

- `runtime.py` no conoce deferred MCP. ✓ (lógica en loop/deferred, sobre `is_deferred_tool`).
- ToolSearch no escribe session metadata MCP directamente. ✓ (escribe `ctx.app_state.capabilities`).

Evidencia M3: `tools/deferred.py` (`is_deferred_tool`, `discovered_tool_names`, `mark_tools_discovered`),
`McpTool.deferred = True`, `AgentLoop._schemas_for_turn` (proyección), `ToolSearchTool.execute`
(descubre + devuelve schemas, busca solo diferidas). Tests: `test_deferred_loading.py` (7). Suite 262.

#### Fase M4 - MCP resources

Estado: `[ ] no iniciado`

- [ ] Convertir `MCPListResources` y `MCPReadResource` en tools del provider o adapters inyectados.
- [ ] Resource access usa provider.
- [ ] Evitar imports directos a `mcp.loader`.

Criterios:

- `tools/mcp_resource_tools.py` no depende del loader global o queda dentro del provider.

#### Fase M5 - MCP management API

Estado: `[ ] no iniciado`

- [ ] API `/mcp` llama service/provider.
- [ ] API no toca `loop._registry`.
- [ ] Toggle/add/delete actualiza provider state.
- [ ] Tool pool refresh se hace via capability manager.

Criterios:

- `api/routes/mcp.py` no modifica registry directamente.

### Tests MCP

- [ ] Provider conecta server y expone tools.
- [ ] Tool pool incluye MCP activo.
- [ ] Tool pool no incluye MCP diferido no activado.
- [ ] ToolSearch activa MCP via manager.
- [ ] Toggle MCP actualiza provider sin tocar registry interno.
- [ ] Resource read/list funciona por provider.
- [ ] Timeout MCP sigue usando configuracion.
- [ ] Wrapper no hace doble llamada en error.

## STT/TTS Provider (capability de I/O por voz)

### Objetivo

Agregar interacción por voz humano–asistente como **capability de I/O sobre el runtime**, no como
tool. STT y TTS son adaptadores en los bordes que el runtime ya expone; no aportan catálogo ni tools.

### Naturaleza — capability de borde, no de tools

A diferencia de Skills/MCP (capabilities que aportan tools al pool), STT/TTS es una capability de
**borde de I/O** y se conecta a primitivas que el runtime ya expone:

- **STT (entrada)**: convierte voz → texto y lo entrega como prompt del turno (`RuntimeTask.prompt`).
  El runtime es agnóstico al origen del prompt.
- **TTS (salida)**: consume el stream de `TokenEvent` del `EventBus` y lo sintetiza a voz de forma
  **incremental** (baja latencia — por eso el streaming token-a-token es requisito).
- **Barge-in**: el usuario habla encima del asistente → cancela la generación en curso vía
  `SignalBus` / `ctx.stop`. El abort responsivo es requisito, no opcional.

Es el mismo patrón que los canales de texto (WhatsApp/Telegram/Teams son adaptadores del `EventBus`):
la voz es ese patrón con STT añadido en la entrada. No expone `catalog()`/`tools()`.

### Tareas

Estado: `[ ] no iniciado`

- [ ] Definir `VoiceIOAdapter` (STT in / TTS out) como capa del consumidor sobre el runtime.
- [ ] STT: entregar la transcripción como prompt del turno.
- [ ] TTS: suscribirse a `TokenEvent` del `EventBus` y sintetizar incremental.
- [ ] Barge-in: la señal de voz entrante dispara `ctx.stop` / `SignalBus`.
- [ ] Saneo: el texto que va a TTS pasa por el mismo choke point de `PathPresentation` — nunca
      leer en voz alta rutas reales de infra (la fuga por voz es la peor).

Criterios:

- El runtime no cambia: STT/TTS viven en el borde del consumidor sobre primitivas existentes.
- TTS recibe tokens ya saneados (fake-path), igual que las cards de la UI.
- Barge-in cancela la generación de forma responsiva.

### Tests STT/TTS

- [ ] STT entrega prompt: una transcripción produce un turno de usuario equivalente al texto.
- [ ] TTS incremental: cada `TokenEvent` se entrega al sintetizador sin esperar el fin del turno.
- [ ] Barge-in: señal entrante durante generación dispara `ctx.stop` y corta el stream.
- [ ] Saneo: una ruta real en el texto de salida no llega al TTS (pasa por `PathPresentation`).

## MemoryProvider (capability de memoria del agente)

### Objetivo

Memoria que el agente guarda para recordar entre sesiones — sobrevive compactación y reinicio.
Construida **sobre** primitivas del runtime, no dentro de él.

### Naturaleza — capability sobre primitivas runtime

La memoria es una capability (como Skills/MCP): pone la **opinión** (qué guardar, recall, ranking,
inyección). El runtime solo aporta los primitivos:

- **Persistencia**: `StorageProtocol` + `StorageKeys.ltm_key(user_id)` — **ya existe** en el runtime.
- **Sobrevivir compactación**: contrato `CompactionProvider` / `collect_compaction_context`.
- **Extracción en background**: `RuntimeContextForker` + `BackgroundNotificationChannel`.

Distinción clave: la cascada config/`agent.md` (CLAUDE.md) es **instrucción humana** al system
prompt; esta memoria es **conocimiento auto-generado por el agente**. Son providers distintos que
alimentan el prompt, no el mismo.

### Por qué NO en el runtime

"Qué recordar", ranking de recall, prompts de extracción y thresholds son opiniones que varían por
producto (un CLI quiere un `MEMORY.md` simple; cloud quiere LTM con ranking semántico). Mismo
razonamiento que fake-path: el runtime expone el primitivo (storage), la capability implementa la
opinión. `ltm_key` ya vive en el runtime como **clave**, sin lógica de memoria al lado.

### Tareas

Estado: `[ ] no iniciado`

- [ ] Crear `MemoryProvider` como `CapabilityProvider`.
- [ ] Tool `remember` (save) que persiste vía `StorageProtocol` bajo `ltm_key`.
- [ ] Recall con ranking (recencia/relevancia) — opinión del provider.
- [ ] `active_context(context)` inyecta memorias relevantes al inicio del turno, scopeado por `agent_id`.
- [ ] `compact_context(context)` preserva memorias activas tras compactación.
- [ ] (Opcional) extracción background al fin del turno vía `RuntimeContextForker`.

Criterios:

- El runtime no tiene lógica de memoria — solo storage + contrato de compactación.
- La memoria sobrevive reinicio (persistida) y compactación (`compact_context`).
- Recall determinista dado el mismo estado y `agent_id`.

### Tests Memory

- [ ] Save persiste: tras "reinicio" (releer storage) la memoria sigue disponible.
- [ ] `active_context` inyecta memorias relevantes al inicio del turno.
- [ ] `compact_context` preserva memorias activas tras compactación.
- [ ] Recall scopeado por `agent_id`: un hijo no ve memorias de otro agente salvo política.
- [ ] Test de acoplamiento: el runtime no importa lógica de memoria.

## Robustez Ante Skills/MCP De Terceros

> Decisión de diseño validada contra el canónico (2026-06-16). Aplica a `SkillsProvider` (S0) y
> `McpProvider` (M0). Motivada por la fragilidad observada en `agent_core` (versión preliminar,
> todo mezclado): el enforcement de directivas del frontmatter era débil.

### El hecho

La spec de Agent Skills de Anthropic estandariza pocas directivas (`name`, `description`); y la spec
de Model Context Protocol tampoco incluye varias props que el canónico usa (p.ej. `model`). Es decir,
**propiedades operativas importantes NO son parte del estándar**. Como hoy hay registros y listas de
terceros que consolidan skills/MCP, no controlamos esas propiedades: en skills/MCP de terceros
simplemente no vendrán. El objetivo es **comportamiento estable con skills/MCP propios o de terceros**.

### Cómo lo resuelve el canónico (patrón a replicar)

Patrón único en skills y MCP: *schema abierto + parseo tolerante por campo con default definido +
aislamiento por ítem; rigor solo en los bordes de seguridad/identidad.*

1. **Schema abierto** — nunca rechaza claves desconocidas (`FrontmatterData` cierra con
   `[key: string]: unknown`); estándar y extensiones operativas conviven.
2. **Parseo total que nunca lanza** — sin frontmatter → `{}`; YAML inválido → reintento → log + `{}`.
3. **Cada campo operativo degrada a un default que DEFINE comportamiento, no a error**:
   `allowed-tools` ø → no activa tools extra; `model` ø/`inherit` → hereda el del padre;
   `description` ø → se deriva del cuerpo; `effort`/`shell` inválidos → log + default.
4. **Aislamiento por ítem** — un skill/server malformado se salta con log; el resto carga.
5. **Rigor solo en seguridad/identidad** — validez de config de server se valida y **rechaza**
   (no se ignora); skills remotas MCP nunca ejecutan shell inline. Tolerancia en lo operativo,
   estrictez en lo que compromete seguridad.

### La pregunta de diseño correcta

No es "¿cómo forzar que traigan `allowed-tools`/`model`?" sino **"¿qué hace el sistema cuando NO
vienen?"** — y la respuesta debe estar fijada por campo, con un default seguro y documentado.

### Criterios de aceptación (S0/M0)

- Modelo de metadata tipado (Pydantic): todo campo operativo `Optional` + default explícito; el
  parser nunca lanza por campo ausente/malformado.
- Tabla estándar-vs-operativo documentada en el provider, con el default-comportamiento de cada
  campo operativo.
- Aislamiento por ítem (un ítem malo no aborta la carga).
- Estrictez reservada a bordes de seguridad/identidad (config de server, ejecución remota).

## Primitivas Fork Y Background (provistas por el runtime)

> **Re-basado.** Esta sección era trabajo del primer plan. Las primitivas ya existen de forma
> nativa en el runtime nuevo (`PLAN_COMPLEMENTARIO_RUNTIME.md`): `ForkContext` / `ForkSnapshot` /
> `ForkPolicy` / `RuntimeContextForker` (`execution/fork`), `BackgroundNotificationChannel`
> (`execution/local/notification.py`), y `agent_id` en `ToolUseContext`. El `LocalAgentRuntime`
> forkea vía `RuntimeContextForker` y notifica por `session_id` **sin recibir `parent_session`** (R2).
> Los "problemas actuales" que listaba esta sección eran internals de agent_core, descartados por D4.

Lo que **sí** es de este plan: cuando se construyan `SkillsProvider`, `McpProvider` (y cualquier
capability que lance subagentes) sobre el runtime nuevo, deben **consumir** estas primitivas —
nunca implementar semántica de fork, copia de mensajes ni background propias.

### Invariantes de capability (criterios de aceptación al construir los providers)

- Ninguna capability copia mensajes ni hereda permisos internamente: lo decide `ForkPolicy`.
- Los resultados background van al `BackgroundNotificationChannel` por `session_id`, no a
  `session.messages` del padre. El formato `<task-notification>` no cambia — solo el emisor.
- El estado activo de una capability se scopea por `context.agent_id`: un hijo no hereda el
  catálogo activo del padre salvo que `ForkPolicy` lo indique; el estado no se filtra entre
  agentes que comparten `session_id` pero tienen distinto `agent_id`.
- La capability **no genera `agent_id`** — lo recibe del runtime vía `RuntimeContextForker`.
- `CapabilityProvider.active_context()` es determinista dado `context.agent_id`.

## Capability Manager

### Fase C0 - Integracion inicial

Estado: `[~] en progreso`

Tareas:

- [x] Crear `CapabilityManager` con lista de providers registrados.
- [x] Registrar `SkillsProvider` y `McpProvider` en el manager (vía `factory._build_capability_manager`
      desde `CapabilitiesConfig`; cableado al loop por turno — M2).
- [x] Exponer `catalog(context) -> list[CapabilitySummary]`.
- [x] Exponer `tools(context) -> list[Tool]`.
- [x] Exponer `compact_context(context) -> list[dict]`.
- [x] Convergencia native + capability preparada: `manager.build_tool_pool(native_tools, context)`
      produce el `ToolPool` que el runtime consume; la fusión la hace `ToolPool.assemble()`
      (built-ins como prefijo contiguo, dedup native-gana, deny) — paridad con `assembleToolPool`.

Criterios:

- El manager coordina providers sin importar ninguno directamente en el runtime.
- Agregar un provider nuevo no requiere cambiar el manager ni el loop.

Pruebas:

- Manager con dos providers registrados: `tools()` devuelve la union de los dos sin duplicados.
- Manager con provider que no expone tools: `tools()` devuelve lista de los otros providers sin error.
- `catalog()` incluye entradas de todos los providers registrados.
- `compact_context()` concatena el aporte de cada provider en orden de registro.
- Ningun provider falla si `context.agent_id` es `None` — caso del agente principal.

### Fase C1 - Chat integration

Estado: `[ ] no iniciado`

Tareas:

- [ ] `chat.py` pide catalogo al manager via `CapabilityContextService` — eliminar llamada directa a `build_skills_listing(load_skills())`.
- [ ] Artifact manifest queda separado del catalogo de capabilities.
- [ ] Verificar que el catalogo no contiene reglas imperativas que contradigan el active context del agente.

Criterios:

- `chat.py` no importa `skills.loader` ni `skills.state`.
- El catalogo sirve para seleccion, no para forzar reinvocacion.

Pruebas:

- `chat.py` llama al manager para obtener catalogo; el catalogo no contiene la regla `call Skill FIRST`.
- Catalogo retornado por el manager coincide con el que antes construia `build_skills_listing`.
- Artifact manifest se construye independientemente del catalogo de capabilities.
- Test de acoplamiento: `chat.py` no importa `skills.loader`.
- Test de regresion: el prompt enviado al modelo incluye el catalogo de skills con el mismo contenido que antes.

### Fase C2 - Loop integration

Estado: `[ ] no iniciado`

Prerequisito: primitivas fork/background/`agent_id` del runtime (provistas por el complementary plan).

Tareas:

- [ ] Loop crea `ToolUseContext` solicitando tool pool al manager en lugar de construirlo directamente.
- [ ] Loop pide tool pool al manager via `CapabilityManager.tools(context)` y lo pasa al assembler.
- [ ] Loop aplica `context_modifier` devueltos por capabilities tras cada tool call.
- [ ] Loop refresca tool pool si algun provider lo solicita via `CapabilityActivation.refresh_tool_pool`.
- [ ] Loop asigna `agent_id` en `ToolUseContext` al crear contexto hijo — delegando a `RuntimeContextForker` (runtime).
- [ ] Loop drena `BackgroundNotificationChannel` al inicio de cada turno antes de llamar al modelo (runtime).

Criterios:

- El loop no conoce providers individuales — solo habla con el manager.
- El loop no decide que tools expone cada capability — las recibe del manager.

Pruebas:

- Loop con dos providers: tool pool del turno incluye tools de ambos.
- Loop aplica `context_modifier` de capability tras tool call; el contexto del siguiente turno refleja el cambio.
- Loop refresca tool pool cuando provider emite `refresh_tool_pool=True` en `CapabilityActivation`.
- Loop drena canal antes de la primera llamada al modelo en el turno: notificaciones pendientes llegan como mensajes user antes del model call.
- Loop crea contexto hijo con `agent_id` asignado por el runtime, no por el manager.
- Test de acoplamiento: `loop.py` no importa `SkillsProvider` ni `McpProvider` directamente.
- Test de regresion: `test_loop.py` pasa sin modificacion; el comportamiento del loop principal no cambia.

### Fase C3 - Compaction integration

Estado: `[ ] no iniciado`

Tareas:

- [ ] Compactor pide contextos compactables al manager via `CapabilityManager.compact_context(context)`.
- [ ] `SkillsProvider` aporta mensajes de skills activas con "continue to follow these guidelines".
- [ ] `McpProvider` puede aportar mensajes si tiene contexto activo relevante.
- [ ] Eliminar imports directos desde compactor a providers especificos.

Criterios:

- `Compactor` no importa `SkillsProvider`, `McpProvider` ni ningun provider directamente.
- Tras compactacion, skills activas siguen en contexto sin inducir reinvocacion.

Pruebas:

- Compactacion con skill activa: el mensaje compactado incluye "continue to follow these guidelines" con el contenido de la skill, no "re-invoke".
- Compactacion sin skills activas: el manager devuelve lista vacia; el compactor no agrega mensajes extra.
- Compactacion con MCP activo: el provider MCP puede aportar contexto; el compactor lo incluye.
- Compactacion de contexto hijo: solo las skills activas en ese `agent_id` aparecen en el mensaje compactado.
- Test de acoplamiento: `compactor.py` no importa `skills.loader` ni `mcp.loader`.
- Test de regresion: `test_skills.py` pasa; el comportamiento de compactacion de skills no cambia.

## Checks De Acoplamiento

Al final deben cumplirse:

- [ ] `runtime.py` no importa `skills.*`.
- [ ] `runtime.py` no importa `mcp.*`.
- [ ] `loop.py` no importa `skills.dispatcher`.
- [ ] `registry.py` no importa `skills.loader`.
- [ ] `registry.py` no usa `skills.state` para MCP.
- [ ] `registry.py` no interpreta `__`.
- [ ] `chat.py` no llama `build_skills_listing(load_skills())`.
- [ ] `api/routes/mcp.py` no toca `loop._registry`.
- [ ] `ToolSearch` no escribe `discovered_deferred_tools` directamente.
- [ ] Ninguna capability copia `parent_session.messages` internamente para crear un fork.
- [ ] `CapabilityProvider.active_context()` acepta `ToolUseContext` y usa `agent_id` para scopear su respuesta.

(El check `LocalAgentRuntime._run_loop` no recibe `parent_session` ya está cubierto por el runtime — R2 del complementary plan.)

## Orden Recomendado

1. Primitivas de runtime ya provistas por `PLAN_COMPLEMENTARIO_RUNTIME.md` (fork, background, `agent_id`, `EventBus`).
2. Crear `CapabilityManager` sin mover comportamiento.
3. Encapsular MCP provider primero.
4. Encapsular SkillsProvider despues.
5. Cambiar tool pool.
6. Cambiar context modifiers.
7. Limpiar prompts/sections.
8. Limpiar metadata legacy.

## Pruebas De Comportamiento Esperadas

Caso wiki + drawio:

- [ ] Usuario pide diagrama draw.io y buscar en wiki.
- [ ] El agente usa wiki primero si necesita informacion.
- [ ] Luego activa/usa drawio-diagrams.
- [ ] No reinvoca drawio-diagrams repetidamente.
- [ ] Usa `drawio__*` cuando la skill esta activa.
- [ ] El diagrama se genera.
- [ ] Si el MCP devuelve imagen interna, el modelo puede revisarla.

Caso MCP deferred:

- [ ] MCP tools de sistema no aparecen por defecto si son diferidas.
- [ ] ToolSearch o skill allowed-tools las activan.
- [ ] Runtime no decide esa activacion.

Caso compaction:

- [ ] Skill invocada sobrevive compactacion.
- [ ] El mensaje dice continuar instrucciones, no reinvocar.

## Riesgos

- Romper herramientas MCP existentes por sacarlas del registry.
- Romper skill fork/background.
- Romper Gmail, porque es adapter nativo sobre MCP.
- Duplicar tools si provider y registry las exponen a la vez.
- Perder recursos MCP si se mueve loader sin reemplazar API.
- Cambiar prompts antes de tener active context puede empeorar comportamiento.

## Regla De Trabajo

No hacer cambios de comportamiento sin tests de antes/despues.

Antes de cada fase:

- marcar `[~] en progreso`;
- listar archivos a tocar;
- declarar comportamiento esperado;
- declarar pruebas a ejecutar.

Al terminar:

- marcar `[x] completado`;
- registrar evidencia;
- registrar "probado" y "no probado";
- dejar notas para que otro agente pueda continuar.

## Registro De Avance

### 2026-06-14 — Re-base contra el complementary plan + STT/TTS

- Re-basado: las primitivas de runtime (fork/background/`agent_id`/notificación/`EventBus`) ya no son
  trabajo de este plan — las provee `PLAN_COMPLEMENTARIO_RUNTIME.md` de forma nativa. La sección
  "Uso De Primitivas Fork Y Background" (F0-F2, que referían internals de agent_core descartados por
  D4) se reemplazó por "Primitivas Fork Y Background (provistas por el runtime)" + invariantes de
  capability. Check de acoplamiento `_run_loop sin parent_session` marcado como cubierto (R2).
- Referencias al primer plan (`PLAN_RUNTIME_AGENTICO.md`) y a fases F0/F1/F2 actualizadas.
- Agregado: **STT/TTS Provider** como capability de I/O por voz (adaptador sobre `EventBus`/prompt/
  `SignalBus`, no aporta tools). Mismo patrón que los canales de texto (WhatsApp/Telegram/Teams).
- Agregado: **MemoryProvider** como capability de memoria del agente (save/recall/active_context/
  compact_context) sobre `StorageProtocol`/`ltm_key` + `CompactionProvider` + fork/background. El
  runtime no lleva lógica de memoria; `ltm_key` ya existe como clave.
- Pendiente sin cambios: construir Skills (S0-S5), MCP (M0-M5), CapabilityManager (C0-C3) y STT/TTS
  sobre el runtime nuevo. Falta cablear en el runtime las primitivas `PathPresentation` y
  `ToolExecEnvironment` (sandbox bwrap) — ver complementary plan.

### 2026-06-15 — C0: CapabilityManager + contratos (sin mover comportamiento)

- Implementado el esqueleto de la capa de capabilities como el plan pide *empezar*: contratos
  estables (`capabilities/contracts.py`) + coordinador (`capabilities/manager.py`). Nada de
  comportamiento del runtime cambia todavía — esto es la junta a la que después se enchufan
  Skills/MCP. Por eso C0 queda `[~]`: el manager existe y está testeado, pero registrar
  `SkillsProvider`/`McpProvider` no es posible aún (no existen; son M0/S0).
- **Por qué Pydantic en `CapabilitySummary`/`CapabilityActivation` y no dict**: regla de salida
  tipada. El catálogo que ve el modelo y el resultado de activar una capability viajan por bordes
  del runtime; un dict suelto ahí es justo lo que el plan quiere erradicar.
- **Por qué `CapabilityProvider` como `Protocol` (no clase base)**: el manager coordina por
  contrato y no debe importar ningún provider concreto (criterio C0: "sin importar ninguno
  directamente en el runtime"). Test de acoplamiento lo fija: el source de `manager.py` no
  menciona `SkillsProvider`/`McpProvider`.
- **Decisión de convivencia**: el `capabilities/` previo (`CapabilitiesResolver`/`protocol.py`)
  es un primitivo anterior y distinto (resuelve schemas para el resolver); se dejó intacto y los
  contratos nuevos se agregaron al lado. Reconciliar/unificar ambos se difiere a cuando MCP/Skills
  providers existan y se vea el solapamiento real — no antes (evita refactor especulativo).
- **Dedup de tools**: por nombre, primera aparición gana = prioridad por orden de registro. Es la
  misma semántica que `assemble_tool_pool` (native gana), coherente para cuando el assembler
  consuma `manager.tools()`.
- **Convergencia native ↔ capability (preparada, igual que el canónico)**: skills/MCP los registra
  *quien embebe el runtime* (no el runtime). Para que las tools de esas capabilities y las nativas
  ya registradas converjan como en `claude-code`, se replicó su punto único `assembleToolPool`:
  - Canónico: native (`getTools()`) y MCP (`appState.mcp.tools`) viven separadas y se fusionan SOLO
    en `assembleToolPool(permissionContext, mcpTools)` — el caller pasa `mcpTools`; ese punto no
    importa el estado MCP. Invariantes: built-ins como **prefijo contiguo** (prompt-cache; el server
    pone el breakpoint tras la última built-in), **dedup por nombre native-gana**, deny a ambos. No
    se identifica MCP por `__`: partición explícita (`isMcpTool`).
  - Aquí: `tools/pool.py::assemble_tool_pool` ya replicaba esa semántica; faltaba el puente desde el
    manager. Se agregó `CapabilityManager.build_tool_pool(native_tools, context) -> ToolPool`, que
    es "el resultado que el runtime consume" (criterio C0). La fusión la hace `ToolPool.assemble()`,
    único punto. Dirección de dependencia capabilities → tools, nunca al revés (igual que allí).
- Probado: `test_capability_manager.py` (12 casos): 8 del manager (unión sin duplicados, provider
  sin tools, catálogo de todos, compact en orden, `agent_id=None` no rompe, startup/shutdown,
  acoplamiento) + 4 de convergencia (particiones, prefijo contiguo native, native-gana en colisión,
  deny a ambas particiones). Suite completa **205 passed, 5 skipped** (193 → +12). Lint limpio.
- No probado: integración real con providers concretos (no existen aún) y cableado en el loop
  (consumir `build_tool_pool` por turno = Fase C2, requiere tests antes/después). C1/C2/C3 dependen
  de M0+/S0+.
- Siguiente: M0 (McpProvider shell) según Orden Recomendado — MCP antes que Skills. Será el primer
  `CapabilityProvider` concreto que el integrador podrá registrar y cuyas tools convergerán por
  `build_tool_pool`.

### 2026-06-16 — Decisión de diseño: robustez ante skills/MCP de terceros (S0/M0)

- **Por qué ahora**: cerrar la idea antes de construir los providers. En `agent_core` (preliminar,
  todo mezclado) se constató enforcement débil de las directivas del frontmatter. Propiedades
  operativas clave (skill: `allowed-tools`; MCP: `model`) NO están en los estándares de Anthropic
  Skills / MCP, y como skills/MCP se consumen de registros de terceros, no controlamos su presencia.
- **Qué se hizo**: revisión directa del canónico (`skills/loadSkillsDir.ts`, `utils/frontmatterParser.ts`,
  `services/mcp/config.ts`, `services/mcp/client.ts`) y se destiló el patrón: schema abierto +
  parseo tolerante por campo con default que define comportamiento + aislamiento por ítem + rigor
  solo en bordes de seguridad/identidad. Se agregó la sección "Robustez Ante Skills/MCP De Terceros"
  y criterios de aceptación a S0 y M0.
- **Insight central**: la pregunta no es cómo forzar las props no estándar, sino qué hace el sistema
  cuando faltan — respuesta fijada por campo (`allowed-tools` ø → no activa nada; `model` ø → hereda).
- **Asimetría clave**: tolerante en lo operativo, estricto en seguridad (config de server inválida se
  rechaza; skill remota MCP nunca ejecuta shell inline). `CapabilitySummary` ya nació alineado
  (campos opcionales con default); falta que S0/M0 hereden el contrato de robustez.
- Doc-only; no se tocó código (los providers no existen aún). Sin tests nuevos en esta entrada.

### 2026-06-16 — M0: McpProvider shell (primer CapabilityProvider concreto)

- Implementado `capabilities/mcp/`: `config.py` (`McpServerConfig` schema abierto + identidad
  estricta), `tool_adapter.py` (`McpTool` + `build_mcp_tool` tolerante), `state.py` (`McpState`
  separado del registry nativo, patrón `appState.mcp.*`), `provider.py` (`McpProvider`).
- **Por qué se adaptó el M0 del plan**: sus bullets ("mover `load_mcp_tools`", "mantener wrappers")
  describían `new_core`, donde MCP vivía disperso. En este repo NO existe loader MCP heredado, así
  que no hay nada que "mover". M0 aquí = construir el shell desde cero con el contrato de robustez,
  definiendo el **punto de inyección**: el integrador conecta servers y registra specs; el transporte
  (`McpCall`) se inyecta. El shell no abre conexiones (eso es M1). Sin transporte fake.
- **Robustez aplicada (no teórica)**: identidad/seguridad estricta — `add_server` lanza si la config
  es inválida (`command` xor `url`); operativo tolerante — `extra="allow"` conserva props de terceros,
  `load_servers` salta inválidos con log, `build_mcp_tool` degrada annotations ausentes a default
  seguro (tercero no anotado: requiere permiso, no background). Asimetría tal cual el canónico.
- **Decisión de permisos**: tools MCP de terceros siempre `requires_permission=True` (no confiables);
  solo `readOnlyHint` las marca `safe_for_background`. Conservador por defecto.
- **Convergencia verificada**: `McpProvider` cumple `CapabilityProvider`; sus tools fluyen por
  `CapabilityManager.build_tool_pool` y quedan como sufijo tras las nativas (paridad assembleToolPool).
- Probado: `test_mcp_provider.py` (17): contrato, identidad estricta, schema abierto, tolerancia en
  bloque, adapter tolerante (sin name/annotations/inputSchema malformado), execute (ok + error de
  transporte envuelto), catálogo `mcp_tool`, resources, timeout por server, convergencia con C0.
  Suite **222 passed, 5 skipped** (205 → +17). Lint limpio.
- No probado: transporte/cliente real (M1), deferred loading (M3), API de management (M5), resources
  como tools del provider (M4). Cableado en loop/factory pendiente (no se registró el provider en
  `factory.py` aún — lo hará el integrador / fase de wiring).
- Siguiente: S0 (SkillsProvider shell) — mismo contrato de robustez — o M1 (estado/cliente MCP).

### 2026-06-16 — S0: SkillsProvider shell (segundo CapabilityProvider concreto)

- Implementado `capabilities/skills/`: `frontmatter.py` (`SkillFrontmatter` schema abierto + parseo
  total), `loader.py` (`SkillDefinition` tipada + `load_skill_text`/`load_skill_file`/`load_skills_dir`),
  `state.py` (`SkillsState` separado del registry), `provider.py` (`SkillsProvider`).
- **Por qué se adaptó el S0 del plan**: igual que M0, sus bullets ("mover `skills.loader`", "mantener
  `SkillTool`") describían `new_core`. En este repo no hay loader de skills ni `SkillTool` heredados:
  S0 aquí = construir el shell desde cero con el contrato de robustez. El loader nace **dentro** del
  provider; la tool `Skill` (invocación) es S1, por eso `tools()`/`active_context()`/`compact_context()`
  devuelven `[]` hoy — declarado, no fingido (no fuerza avance aparente).
- **Robustez aplicada (no teórica)**: la pregunta "¿qué hace el sistema cuando NO vienen?" resuelta por
  campo — `name` ø/no-string → identidad desde el nombre del directorio; `description` ø → primer
  párrafo del cuerpo; `model` ø/`inherit` → `None` (hereda el del padre); `allowed-tools` ø → `[]` (no
  activa nada), acepta lista o CSV. `parse_frontmatter` nunca lanza (sin frontmatter / YAML inválido /
  no-mapping → `{}`). Aislamiento por ítem en `load_skills_dir`. **Sin borde estricto**: a diferencia de
  M0 (config de server), la identidad de skill siempre se resuelve desde el directorio, así que no hay
  nada que rechazar — la tabla estándar-vs-operativo queda documentada en el docstring del provider.
- **Decisión sobre YAML**: el frontmatter ES YAML y el contrato exige "YAML inválido → log + {}";
  escribir un parser a mano sería frágil/heurístico (R1). Se añadió `pyyaml` como dependencia (no estaba
  en el repo) — herramienta correcta, espejo del canónico; no es cambio arquitectónico.
- **Convergencia verificada**: `SkillsProvider` cumple `CapabilityProvider`; su catálogo fluye por
  `CapabilityManager.catalog`. Al no aportar tools en S0, el pool sigue siendo solo el nativo.
- Probado: `test_skills_provider.py` (18): contrato, frontmatter ausente/abierto-sin-cierre/YAML
  inválido/no-mapping/schema abierto/no-string/allowed-tools lista+CSV, defaults por campo, override de
  `name`, `model: inherit`→None, aislamiento por ítem en dir, catálogo, shell honesto vacío, convergencia
  con C0. Suite **245 passed, 0 skipped** (227 → +18). Lint limpio.
- No probado / pendiente: invocación de skill como comando procesado (S1), context modifier de
  allowed-tools (S2), catálogo orgánico sin "SKILL CHECK before EVERY step" (S3), slash commands (S4),
  compactación (S5). Cableado en `chat.py`/loop/`factory.py` = fases C — el provider aún NO está en
  `factory.py`.
- Siguiente: registrar `SkillsProvider`+`McpProvider` en el manager vía `factory.py` y consumir
  `build_tool_pool` por turno en el loop (fases C1/C2), o M1 (cliente MCP real), o S1 (invocación).

### YYYY-MM-DD

Estado:

- Implementado:
- En progreso:
- Bloqueado:
- Probado:
- No probado:
- Notas:

