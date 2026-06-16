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

Estado: `[ ] no iniciado`

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

Estado: `[ ] no iniciado`

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

Estado: `[ ] no iniciado`

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

Estado: `[ ] no iniciado`

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

Estado: `[ ] no iniciado`

- [ ] Crear `SkillsProvider`.
- [ ] Mover acceso a `skills.loader` detras del provider.
- [ ] Exponer catalogo desde provider.
- [ ] Mantener `SkillTool` actual como adapter temporal.
- [ ] Tests de catalogo.

Criterios:

- `chat.py` puede pedir catalogo al manager, no a `skills.loader`.
- No cambia comportamiento aun.

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

Estado: `[ ] no iniciado`

- [ ] Crear `McpProvider`.
- [ ] Mover `load_mcp_tools` detras del provider.
- [ ] Mantener wrappers actuales como adapter temporal.
- [ ] Exponer `mcp.tools` desde provider.
- [ ] Exponer `mcp.resources` desde provider.

Criterios:

- `main.py` inicializa provider.
- El registry nativo no necesita cargar MCP para startup.

#### Fase M1 - Estado MCP separado

Estado: `[ ] no iniciado`

- [ ] Crear `McpState`.
- [ ] Guardar servers, clients, tools, resources.
- [ ] Mover `_clients` y `_clients_by_name` fuera de globals o encapsularlos.
- [ ] Dejar API de acceso por provider.

Criterios:

- Resource tools no llaman `mcp.loader` directamente.
- Gmail adapter recibe provider/client resolver.

#### Fase M2 - Tool pool MCP

Estado: `[ ] no iniciado`

- [ ] Sacar MCP wrappers del registry nativo.
- [ ] `McpProvider.tools(context)` devuelve tools activas.
- [ ] `ToolPoolAssembler` combina native + MCP.
- [ ] Deduplicar con prioridad native.
- [ ] Orden estable siguiendo referencia.

Criterios:

- `registry.py` no interpreta nombres con `__`.
- `main.py` no registra MCP wrappers en registry nativo.

#### Fase M3 - Deferred loading

Estado: `[ ] no iniciado`

- [ ] Mover `discovered_deferred_tools` a `McpState` o `CapabilityState`.
- [ ] `ToolSearch` debe llamar `CapabilityManager.activate(...)`.
- [ ] Skills allowed-tools debe activar MCP tools via permission/context, no via runtime.
- [ ] El runtime no recibe `deferred_loading_enabled` como logica MCP.

Criterios:

- `runtime.py` no conoce deferred MCP.
- ToolSearch no escribe session metadata MCP directamente.

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

Estado: `[ ] no iniciado`

Tareas:

- [ ] Crear `CapabilityManager` con lista de providers registrados.
- [ ] Registrar `SkillsProvider` y `McpProvider` en el manager.
- [ ] Exponer `catalog(context) -> list[CapabilitySummary]`.
- [ ] Exponer `tools(context) -> list[Tool]`.
- [ ] Exponer `compact_context(context) -> list[dict]`.

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

### YYYY-MM-DD

Estado:

- Implementado:
- En progreso:
- Bloqueado:
- Probado:
- No probado:
- Notas:

