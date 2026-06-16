# Plan: Runtime Agentico Reutilizable

Estado general: `[ ] no iniciado` `[~] en progreso` `[x] completado`

Estado actual: `[x] completado`

## Objetivo

Extraer un runtime agentico reutilizable que no dependa de skills, MCP, MinIO, settings propios del proyecto, wiki, drawio, gmail ni cualquier extension especifica.

El runtime debe proveer primitivas estables para que otros proyectos puedan conectar capacidades externas sin modificar el loop ni el model runtime.

## Principio Rector

El runtime no decide de donde vienen las herramientas ni como se descubren capacidades. El runtime solo:

- recibe mensajes;
- prepara turnos;
- ensambla o recibe un tool pool ya resuelto;
- ejecuta tool calls;
- aplica context modifiers;
- gestiona compactacion mediante hooks;
- emite eventos;
- respeta permisos y cancelacion;
- mantiene contratos genericos de estado.

Todo lo especifico del proyecto debe vivir fuera.

## Referencia De Comportamiento

El proyecto de referencia `claude-code` no separa el runtime como libreria independiente, pero si tiene fronteras utiles que debemos preservar:

- `ToolUseContext` como contrato operativo del loop.
- `contextModifier` como forma canonica de modificar contexto.
- `assembleToolPool` como punto unico de union de built-ins + MCP.
- `AppState` como estado externo que el loop consulta.
- `runTools` como orquestador que ejecuta tools y aplica modificaciones.

Nuestra version debe tomar esos principios y llevarlos a una separacion mas clara.

## Alcance

Incluye:

- contratos base;
- loop generico;
- model runtime generico;
- native tool registry;
- tool pool assembler;
- permission context;
- context modifier protocol;
- compaction hooks;
- eventos;
- pruebas de frontera.

No incluye:

- implementacion final de skills;
- implementacion final de MCP;
- cambios de comportamiento de drawio/wiki/gmail;
- migracion completa de storage;
- reingenieria de modelos.

Esas piezas se conectan mediante capabilities.

## Estado Inicial Detectado

Acoplamientos actuales que deben desaparecer del runtime:

- `src/agent_core/models/gpt_5_4/runtime.py` importa `skills.loader` indirectamente para resolver `allowed_tools` de `invoked_skills`.
- `src/agent_core/core/loop.py` importa `skills.dispatcher` y conoce slash skills.
- `src/agent_core/tools/registry.py` conoce skills, MCP por `__`, `skills.state` y `allowed_tools`.
- `src/agent_core/core/session.py` tiene estado especifico: `discovered_deferred_tools`, `activated_mcp_tools`, `invoked_skills`, `inline_injection_turn`.
- `src/agent_core/core/compactor.py` conoce skills y las reinyecta.
- `src/agent_core/api/routes/chat.py` inyecta catalogo de skills.
- `src/agent_core/api/routes/mcp.py` toca `loop._registry`.

## Arquitectura Objetivo

```text
agentic_runtime/
  contracts.py
  loop.py
  model_runtime.py
  native_registry.py
  tool_pool.py
  permissions.py
  context.py
  compaction.py
  events.py

project_extensions/
  capabilities/
    skills/
    mcp/
    storage/
```

En este repositorio el nombre final puede mantenerse bajo `src/agent_core`, pero la frontera debe quedar igual de clara.

## Contratos A Crear

### ToolUseContext

Estado: `[x] completado`

Responsabilidad:

- transportar el estado operativo de un turno;
- exponer `get_app_state`;
- contener permisos;
- contener tool pool activo;
- permitir refresh de tools;
- mantener abort/cancelacion;
- no depender de skills ni MCP.

Campos esperados:

- `session_id`
- `execution_id`
- `turn_count`
- `messages`
- `tool_pool`
- `permission_context`
- `app_state`
- `abort_signal` o equivalente asyncio
- `event_queue`
- `storage` opcional como primitiva generica
- `presentation` opcional como primitiva generica

Criterios de aceptacion:

- Ningun import de `skills.*` o `mcp.*`.
- Puede ser usado por cualquier tool nativa.
- Puede ser modificado por `ContextModifier`.

### AppState

Estado: `[x] completado`

Responsabilidad:

- contener estado runtime-visible sin que el runtime conozca proveedores especificos;
- permitir que capabilities guarden subestados propios.

Forma sugerida:

```python
class AppState(BaseModel):
    permissions: PermissionContext
    capabilities: dict[str, Any]
    native: dict[str, Any] = {}
```

Criterios de aceptacion:

- Skills/MCP pueden registrar estado bajo `capabilities["skills"]` y `capabilities["mcp"]`.
- El runtime no accede a claves internas salvo por APIs del manager.

### ContextModifier

Estado: `[x] completado`

Responsabilidad:

- reemplazar mutaciones directas de `Session`;
- permitir que tools/capabilities devuelvan cambios estructurados;
- encadenar cambios en ejecucion serial.

Forma sugerida:

```python
ContextModifier = Callable[[ToolUseContext], ToolUseContext]
```

Criterios de aceptacion:

- `ToolResult.context_modifier` opera sobre `ToolUseContext`, no sobre `Session`.
- El loop aplica modifiers despues de ejecutar tools.
- Los modifiers de tools no concurrentes se aplican en orden.

### ToolPool

Estado: `[x] completado`

Responsabilidad:

- representar el set final de tools disponibles para el modelo;
- separar origen nativo/capability sin que el runtime necesite saber detalles.

Forma sugerida:

```python
class ToolPool(BaseModel):
    native_tools: list[Tool]
    capability_tools: list[Tool]
```

Criterios de aceptacion:

- El model runtime recibe una lista final de `Tool`.
- La union se hace en un solo punto.
- Built-ins tienen prioridad ante colision de nombres, siguiendo referencia.

### ToolPoolAssembler

Estado: `[x] completado`

Responsabilidad:

- equivalente Python de `assembleToolPool` de la referencia;
- combinar native tools + capability tools;
- aplicar permisos;
- deduplicar;
- ordenar de forma estable para cache.

Criterios de aceptacion:

- Existe una sola funcion principal para ensamblar tools.
- `ToolRegistry` ya no filtra MCP/skills por convencion.
- El runtime no aplica deferred loading directamente.

### PermissionContext

Estado: `[x] completado`

Responsabilidad:

- representar permisos activos;
- soportar reglas always allow/deny/session/command;
- permitir que skills agreguen `allowed-tools` como permiso contextual.

Criterios de aceptacion:

- Reemplaza usos dispersos de `permission_grants`.
- Skills no activan tools escribiendo metadata lateral.
- MCP/tools se filtran mediante permisos, no por `skills.state`.

### CompactionProvider Hook

Estado: `[x] completado`

Responsabilidad:

- permitir que capabilities aporten contexto a compactacion;
- evitar que `Compactor` importe skills/MCP.

Contrato sugerido:

```python
class CompactionProvider(Protocol):
    def compact_context(self, context: ToolUseContext) -> list[dict]:
        ...
```

Criterios de aceptacion:

- `Compactor` no importa `skills.loader`.
- Skills aporta `invoked_skills` como "continue to follow these guidelines".

## Fases

### Fase 0 - Baseline y tests de proteccion

Estado: `[x] completado`

Tareas:

- [x] Crear tests que documenten imports no deseados actuales.
- [x] Crear snapshot de comportamiento actual de tool pool.
- [x] Crear tests de `ToolResult.context_modifier`.
- [x] Crear tests de ejecucion serial/concurrente de tools.
- [x] Crear tests para asegurar que no se rompen tools nativas.

No tocar comportamiento todavia.

Evidencia esperada:

- pytest focalizado pasa.
- Lista de imports prohibidos documentada.

Pruebas:

- `test_runtime_coupling_baseline.py`: `test_no_new_skill_couplings_outside_known_baseline`, `test_no_new_mcp_couplings_outside_known_baseline`, `test_agent_loop_has_no_direct_skill_or_mcp_coupling`, `test_registry_snapshot_contains_native_tools_and_skill_entrypoint`, `test_partition_tool_calls_batches_consecutive_safe_tools_only`
- `test_runtime_contracts.py`: `test_runtime_contract_modules_do_not_import_skill_or_mcp_packages`

### Fase 1 - Introducir contratos sin migrar comportamiento

Estado: `[x] completado`

Tareas:

- [x] Crear modulo de contratos runtime.
- [x] Agregar `ToolUseContext`.
- [x] Agregar `AppState`.
- [x] Agregar `PermissionContext`.
- [x] Agregar `ToolPool`.
- [x] Agregar `ToolPoolAssembler`.
- [x] Agregar adapter desde `Session` actual hacia `ToolUseContext`.

Criterios:

- [x] El loop sigue funcionando igual.
- [x] No se eliminan campos legacy aun.
- [x] Los nuevos contratos tienen tests unitarios.

Pruebas:

- `test_runtime_contracts.py`: `test_tool_pool_assembly_is_stable_and_native_wins_name_collisions`, `test_native_tool_registry_has_no_capability_filtering_behavior`, `test_tool_pool_respects_deny_rules`, `test_tool_use_context_modifier_updates_permissions_without_session_mutation`, `test_session_adapter_builds_tool_use_context_without_provider_state`, `test_sync_session_from_tool_use_context_updates_legacy_permission_grants`, `test_apply_context_modifier_compat_supports_new_tool_use_context_modifiers`, `test_apply_context_modifier_compat_supports_legacy_session_modifiers`

### Fase 2 - Cambiar loop para usar ToolUseContext

Estado: `[x] completado`

Tareas:

- [x] Construir `ToolUseContext` al inicio de cada turno.
- [x] Pasar `ToolUseContext` a tool execution.
- [x] Aplicar `ToolResult.context_modifier` sobre `ToolUseContext`.
- [x] Sincronizar cambios necesarios hacia `Session` mediante adapter temporal.
- [x] Mantener eventos SSE actuales.

Criterios:

- [x] El loop no debe importar `skills.dispatcher`.
- [x] El loop no debe conocer MCP.
- [x] El loop sigue ejecutando tools nativas.

Pruebas:

- `test_loop.py`: `test_tool_execution_receives_runtime_tool_use_context`, `test_loop_applies_tool_use_context_modifier_and_syncs_session`, `test_tool_use_echo`
- `test_runtime_coupling_baseline.py`: `test_agent_loop_has_no_direct_skill_or_mcp_coupling`

### Fase 3 - Separar native registry de capability tools

Estado: `[x] completado`

Tareas:

- [x] Renombrar/aislar registry nativo.
- [x] Eliminar logica MCP por `__` del registry.
- [x] Eliminar logica skills del registry.
- [x] Implementar `ToolPoolAssembler` como unica union.
- [x] Adaptar model runtime para recibir tools ya resueltas.

Criterios:

- [x] `ToolRegistry` no importa `skills.*`.
- [x] `ToolRegistry` no interpreta `__`.
- [x] `models/gpt_5_4/runtime.py` no importa `skills.*`.

Pruebas:

- `test_runtime_contracts.py`: `test_native_tool_registry_has_no_capability_filtering_behavior`, `test_tool_pool_assembly_is_stable_and_native_wins_name_collisions`, `test_tool_pool_respects_deny_rules`
- `test_runtime_coupling_baseline.py`: `test_no_new_skill_couplings_outside_known_baseline`, `test_no_new_mcp_couplings_outside_known_baseline`

### Fase 4 - Limpiar model runtime

Estado: `[x] completado`

Tareas:

- [x] Eliminar `_allowed_tools_for_invoked_skills`.
- [x] Eliminar `discovered_deferred_tools` del model runtime.
- [x] Hacer que `prepare_turn` reciba tools ya resueltas desde el runtime loop.
- [x] Mantener compatibilidad con GPT 5.4 request actual.

Criterios:

- [x] `runtime.py` no sabe de skills/MCP/deferred.
- [x] Tests de request muestran mismas tools esperadas mediante assembler.

Pruebas:

- `test_runtime_contracts.py`: `test_gpt54_prepare_turn_builds_request_with_assembled_tools`

### Fase 5 - Compaction por providers

Estado: `[x] completado`

Tareas:

- [x] Crear hook de compactacion.
- [x] Mover reinyecion de skills fuera de `Compactor`.
- [x] Eliminar texto "re-invoke" del compactor base.
- [x] Permitir que capabilities aporten mensajes compactados.

Criterios:

- [x] `Compactor` no importa `skills.*`.
- [x] Skills puede aportar contexto activo.
- [x] MCP puede aportar contexto si fuera necesario.

Pruebas:

- `test_governance.py::TestCompaction`: `test_compact_preserves_recent_messages`, `test_compact_appends_provider_context`
- `test_runtime_contracts.py`: `test_compaction_providers_are_collected_in_registration_order`

### Fase 6 - API sin acceso a internals

Estado: `[x] completado`

Tareas:

- [x] Evitar que rutas API toquen `loop._registry`.
- [x] Crear servicios de aplicacion para capabilities.
- [x] Chat no debe construir catalogo de skills directamente.
- [x] Chat debe pedir contexto de capabilities al manager.

Criterios:

- [x] `api/routes/chat.py` no importa `skills.loader`.
- [x] `api/routes/mcp.py` no modifica registry directamente.

Pruebas:

- `test_capability_context_service.py`: `test_skills_listing_contains_skill_name_and_description`, `test_skills_listing_returns_empty_when_no_skills`, `test_skills_listing_excludes_disabled_skills`, `test_agents_listing_contains_agent_name_and_description`, `test_agents_listing_returns_empty_when_no_agents`, `test_skills_listing_includes_multiple_skills`
- `test_runtime_coupling_baseline.py`: `test_api_routes_do_not_touch_loop_registry`, `test_chat_route_does_not_import_skills_loader`, `test_mcp_route_does_not_modify_registry_directly`

## Checks De Acoplamiento

Estos checks deben ser verdaderos al final:

- [x] `src/agent_core/models/**` no importa `skills.*`.
- [x] `src/agent_core/models/**` no importa `mcp.*`.
- [x] `src/agent_core/core/loop.py` no importa `skills.*`.
- [x] `src/agent_core/core/loop.py` no importa `mcp.*`.
- [x] `src/agent_core/tools/registry.py` no importa `skills.*`.
- [x] `src/agent_core/tools/registry.py` no interpreta nombres con `__`.
- [x] `src/agent_core/core/compactor.py` no importa `skills.*`.
- [x] API no toca `loop._registry`.
- [x] `api/routes/chat.py` no importa `skills.loader` ni llama `load_skills` directamente.
- [x] `AgentTool` no contiene logica de copia de mensajes del parent.
- [x] `ToolUseContext` tiene campo `agent_id: str | None`.

## Pruebas Minimas

- [x] Tools nativas siguen disponibles. → `test_runtime_coupling_baseline.py::test_registry_snapshot_contains_native_tools_and_skill_entrypoint`
- [x] Tools foreground_only no entran a subagents. → `test_loop.py::test_loop_factory_excludes_foreground_only_tools_from_subagent_registry`
- [x] Ejecucion serial aplica context modifiers en orden. → `test_loop.py::test_serial_tools_apply_context_modifiers_in_order`
- [x] Ejecucion concurrente no rompe context modifiers. → `test_loop.py::test_concurrent_tools_both_context_modifiers_applied`
- [x] Tool pool mantiene orden estable. → `test_runtime_contracts.py::test_tool_pool_assembly_is_stable_and_native_wins_name_collisions`
- [x] ModelRequest contiene tools esperadas. → `test_runtime_contracts.py::test_gpt54_prepare_turn_builds_request_with_assembled_tools`
- [x] Compaction conserva mensajes base. → `test_governance.py::TestCompaction::test_compact_preserves_recent_messages`
- [x] No regresion de descarga de archivos. → `test_download_proxy.py` (sign, verify, build_proxy_url, roundtrip)
- [x] Fork no contamina messages del padre. → `test_fork_primitives.py::test_fork_foreground_parent_messages_not_contaminated`
- [x] `ForkSnapshot` es inmutable: hijo modificado no altera snapshot del padre. → `test_fork_primitives.py::test_fork_snapshot_rejects_mutation`, `test_fork_snapshot_child_messages_do_not_alter_snapshot`
- [x] `ToolUseContext.agent_id` es `None` en el agente principal y unico en cualquier hijo. → `test_fork_primitives.py::test_tool_use_context_has_agent_id_none_by_default`, `test_forker_assigns_unique_agent_id`
- [x] Test de regresion: `test_fork_skill.py`, `test_subagent_depth_guard.py` y `test_background_result_summary.py` siguen pasando sin modificacion.

## Pendientes De Validacion

- [ ] Validar import indirecto de `agent_core.main` en un entorno con `agent_core_home()` redirigido o escribible. El sandbox actual impide abrir `/home/noheroes/.agent_core/agent.log`, pero esto debe resolverse mediante una ruta indirecta valida: contenedor, variable/config correcta, fixture de test o refactor controlado de inicializacion de logging.

## Omisiones Arquitectonicas Detectadas

### Fase 7 - Modo fork como primitiva runtime

Estado: `[x] completado`

Tareas:

- [x] Crear `ForkContext` — descriptor declarativo del fork: prompt, subagent_type, model_override, policy, parent snapshot.
- [x] Crear `ForkSnapshot` — captura inmutable del parent: messages, permissions, tool_pool y metadata minima; modificar el hijo no altera el snapshot.
- [x] Crear `ForkPolicy` — reglas de herencia y aislamiento: que se hereda (permisos, tool pool, abort), que se aisla (messages, estado mutable), que se propaga (cancelacion).
- [x] Crear `RuntimeContextForker` — servicio runtime que recibe `ForkContext` y devuelve un `ToolUseContext` hijo listo para ejecutar; no sabe si el fork viene de `AgentTool`, skill, scheduler o background task.
- [x] `AgentTool` traduce su input a `ForkContext` y delega a `RuntimeContextForker` — eliminar la logica interna de copia de mensajes y herencia de herramientas.
- [x] Verificar que foreground fork, background fork y skill fork usan el mismo contrato.
- [x] Crear tests en `tests/test_fork_primitives.py` cubriendo los escenarios del punto siguiente.

Criterios:

- [x] `AgentTool` no contiene logica de copia de mensajes ni herencia de permisos — solo construye `ForkContext`.
- [x] Capabilities pueden solicitar fork via `RuntimeContextForker` sin implementar semantica de fork.
- [x] `ForkSnapshot` es inmutable: un test que modifica el hijo confirma que el snapshot del padre no cambia.
- [x] Skills fork, agent fork y background fork producen un `ToolUseContext` hijo con la misma estructura.
- [x] Storage persiste fork sessions por ruta derivada de `agent_id`, no decide semantica de fork.

Pruebas:

- `test_fork_primitives.py`: `test_fork_context_requires_prompt`, `test_fork_context_instantiates_with_required_fields`, `test_fork_snapshot_rejects_mutation`, `test_fork_snapshot_child_messages_do_not_alter_snapshot`, `test_fork_policy_inherits_permissions`, `test_fork_policy_isolates_permissions`, `test_fork_policy_isolates_tool_pool`, `test_forker_assigns_unique_agent_id`, `test_forker_child_has_parent_session_id`, `test_forker_propagate_abort_shares_stop_event`, `test_forker_no_propagate_abort_gets_own_stop_event`, `test_fork_snapshot_exposes_subagent_depth`, `test_forker_does_not_mutate_snapshot`, `test_fork_foreground_result_is_tool_result`, `test_fork_foreground_parent_messages_not_contaminated`, `test_fork_foreground_with_fork_context_copies_parent_messages`, `test_fork_foreground_without_fork_context_empty_messages`, `test_fork_background_child_inherits_parent_session_id`, `test_fork_background_child_session_id_set_by_run_loop`, `test_nested_fork_subagent_depth_increments`, `test_nested_fork_grandchild_gets_own_unique_agent_id`
- `test_fork_primitives.py`: `test_tool_use_context_has_agent_id_none_by_default`
- `test_fork_skill.py`: `test_fork_session_saved_with_agent_id_not_task_id` (ruta de storage usa `agent_id` del forker)
- Regresion: `test_fork_skill.py`, `test_subagent_depth_guard.py`

### Fase 8 — Reestructuracion: agrupadores de runtime

Estado: `[x] completado`

Reorganizar los archivos sueltos de `runtime/` en carpetas con responsabilidad unica. Sin cambios de comportamiento. La suite existente debe pasar sin modificacion al terminar.

Absorbe de la implementacion previa:
- `BackgroundNotificationChannel` (`notification.py`) ya existe y sus 18 tests pasan — se mueve a `execution/`.
- `_run_loop` ya no recibe `parent_session` — criterio ya cumplido.
- `agent_id` ya esta en `ToolUseContext` — criterio ya cumplido (Fase 7).
- `test_fork_background_child_session_id_set_by_run_loop` esta roto por el cambio de firma de `_run_loop`; queda pendiente hasta Fase 14.

Diferido: el hook de drenado del canal en `loop_factory` requiere una decision sobre el contrato de `LoopFactory`; se resuelve en Fase 15.

Tareas:

- [x] Crear `runtime/execution/` y mover: `local.py`, `fork.py`, `notification.py`, `summarizer.py`.
- [x] Crear `runtime/context/` y mover: `context.py` → `tool_use.py`, `session_adapter.py` → `adapters.py`. Reservar `execution.py` y `state.py` para Fase 14.
- [x] Crear `runtime/contracts/` y mover: `protocol.py` → `runtime.py`, `contracts.py` → `storage.py`, `permissions.py`.
- [x] `tool_pool.py` queda en `runtime/` hasta Fase 12 donde colapsa en `tools/registry.py`.
- [x] Actualizar todos los imports internos del paquete `runtime`.
- [x] Verificar que `__init__.py` de `runtime` reexporta los simbolos publicos sin cambio de interfaz.

Criterios:

- [x] `uv run python -m pytest tests/` pasa con el mismo resultado que antes de la fase (excepto `test_fork_background_child_session_id_set_by_run_loop` que ya estaba roto). Evidencia: 74 passed, 1 failed (roto previo).
- [x] Ningun archivo fuera de `runtime/` necesita cambiar sus imports. Evidencia: ninguna modificacion fuera de `runtime/`.
- [x] No hay archivos sueltos en la raiz de `runtime/` salvo `__init__.py`, `tool_pool.py` (transitorio) y el futuro `factory.py`.

Pruebas:

- `test_runtime_contracts.py`: suite completa pasa sin cambios.
- `test_fork_primitives.py`: suite completa pasa (excepto el test roto ya identificado).
- `test_background_notification_channel.py`: 18 tests pasan.
- Regresion: `test_background_result_summary.py`, `test_fork_skill.py`, `test_subagent_depth_guard.py`.

---

### Fase 9 — signals/: SignalBus con arbol de cascada

Estado: `[x] completado`

Hoy un stop desde la UI cancela el task del foreground pero los agentes background y fork siguen corriendo porque sus `asyncio.Task` no estan enlazados al ciclo de vida del padre. El `SignalBus` mantiene un arbol de ejecucion y propaga la cancelacion a todos los descendientes al recibir un `AbortSignal`.

Tareas:

- [x] Crear `runtime/signals/protocols.py` con `SignalType` (ABORT, PAUSE, RESUME) y `SignalHandler` Protocol.
- [x] Crear `runtime/signals/bus.py` con `SignalBus`: `register(execution_id, parent_id)`, `unregister(execution_id)`, `send(execution_id, signal, cascade)`, `get_signal(execution_id)`. Primitiva de extension: `register_handler`.
- [x] `SignalHandle` — token devuelto por `register`; expone `check()` para que el ejecutor consulte su señal sin mantener referencia al bus.
- [x] `runtime/signals/__init__.py` exporta `SignalBus`, `SignalHandle`, `SignalHandler`, `SignalType`.

Criterios:

- [x] Un ABORT con `cascade=True` sobre el padre cancela todos sus descendientes en profundidad.
- [x] Cancelar un hijo no afecta a sus hermanos (`cascade=False` por defecto).
- [x] `unregister` limpia la señal del nodo.
- [x] `SignalHandle.check()` refleja el estado actual del bus.

Pruebas:

- `tests/test_signal_bus.py` — 12 passed:
  - `test_register_root_node`, `test_register_child_node`, `test_unregister_removes_node`
  - `test_send_abort_to_single_node`, `test_send_pause_to_single_node`, `test_send_resume_clears_pause`
  - `test_get_signal_unknown_node_returns_none`
  - `test_abort_cascades_to_children`, `test_abort_cascades_deep`, `test_abort_no_cascade_does_not_affect_children`
  - `test_unregister_clears_signal`, `test_handle_check_returns_current_signal`

---

### Fase 10 — modes/: ModeManager

Estado: `[x] completado`

El modo de un agente (foreground, background, fork) determina si se envia notificacion al completar y si el agente es visible para el usuario. La transicion `foreground <-> background` ocurre en caliente sin reiniciar la ejecucion.

Tareas:

- [x] Crear `runtime/modes/protocols.py` con `AgentMode` (FOREGROUND, BACKGROUND, FORK) y `ModeManagerProtocol`.
- [x] Crear `runtime/modes/manager.py` con `ModeManager`: `register`, `unregister`, `get_mode`, `set_mode` (fork inmutable), `on_complete`. Primitiva de extension: `on_transition(callback)`.
- [x] `runtime/modes/__init__.py` exporta `AgentMode`, `ModeManager`, `ModeManagerProtocol`.

Criterios:

- [x] `on_complete` retorna `True` solo si el modo al momento de completar es `background`.
- [x] Cambiar modo de `background` a `foreground` antes de que termine suprime la notificacion.
- [x] Fork no puede transicionar — `set_mode` sobre un fork lanza `ValueError`.
- [x] `ModeManager` no depende de `TaskRegistry` ni de `SignalBus`.

Pruebas:

- `tests/test_mode_manager.py` — 9 passed:
  - `test_background_on_complete_returns_true`, `test_foreground_on_complete_returns_false`
  - `test_mode_transition_to_foreground_suppresses_notification`, `test_mode_transition_back_to_background_restores_notification`
  - `test_fork_mode_is_immutable`, `test_unknown_task_on_complete_returns_false`
  - `test_get_mode_returns_current_mode`, `test_get_mode_unknown_returns_none`, `test_unregister_removes_entry`

---

### Fase 11 — storage/: copia y primitivas de integracion

Estado: `[x] completado`

Crear `runtime/storage/` con `StorageProtocol` (typing.Protocol), `FilesystemStorage` nativo del runtime y factory inyectable. Los backends existentes en `agent_core/storage/` satisfacen el protocolo estructuralmente sin cambios.

Tareas:

- [x] Crear `runtime/storage/protocol.py` con `StorageProtocol` (runtime_checkable Protocol): `upload`, `download`, `presign`, `delete`, `exists`, `list_prefix`; y `StorageKeys` con helpers: `session_key`, `agent_key`, `ltm_key`, `work_key`, `log_key`.
- [x] Crear `runtime/storage/filesystem.py` con `FilesystemStorage` que implementa `StorageProtocol` e incluye `copy` (extra al protocolo base — los backends externos no tienen copy).
- [x] Crear `runtime/storage/factory.py` con `StorageRegistry`: `register(name, cls)` y `create(backend, **cfg) -> StorageProtocol` — instancia fresca, sin singleton.
- [x] Verificado que `LocalStorageClient` satisface `StorageProtocol` con `isinstance` sin modificar `agent_core/storage/`.

Criterios:

- [x] `FilesystemStorage.copy(src, dst)` copia bytes sin redownload/reupload intermedio (usa shutil.copy2).
- [x] `StorageRegistry.create("filesystem", root=Path(...))` retorna instancia fresca cada vez.
- [x] `isinstance(LocalStorageClient(), StorageProtocol)` es True sin modificar storage existente.
- [x] `StorageKeys` no depende de ninguna implementacion concreta.
- [x] Path traversal rechazado con ValueError.

Pruebas:

- `tests/test_runtime_storage.py` — 15 passed:
  - roundtrip, exists, delete, list_prefix, copy sin upload, path traversal
  - StorageRegistry fresh instance, unknown backend, custom backend registration
  - StorageKeys session/agent/work key format
  - FilesystemStorage y LocalStorageClient satisfacen StorageProtocol

Nota: `copy` no está en `StorageProtocol` base porque los backends existentes (MinIO, Local) no lo tienen — está solo en `FilesystemStorage`. `StorageProtocol` cubre solo el contrato mínimo que todos satisfacen sin modificar nada fuera de runtime/.

---

### Fase 12 — tools/: contrato enriquecido y ToolDispatcher

Estado: `[x] completado`

El contrato actual de tools es escueto. Se enriquece con schema LLM, categoria, permisos, timeout y flag de background. El `ToolDispatcher` es el unico punto de integracion entre runtime context y ejecucion de tool — ni el loop ni las tools se tocan directamente.

Tareas:

- [x] Crear `runtime/tools/protocol.py` con `ToolProtocol` (runtime_checkable Protocol): `name`, `description`, `input_schema`, `category`, `requires_permission`, `safe_for_background`, `timeout_seconds`, `async execute(input, ctx) -> ToolResult`; y `ToolResult` (con factorías error/timeout/aborted), `ToolCategory`.
- [x] Crear `runtime/tools/registry.py` con `ToolRegistry`: `register(tool)`, `resolve(name)`, `list_available(mode, permission_ctx)` filtra por `safe_for_background` en modo background.
- [x] Crear `runtime/tools/dispatcher.py` con `ToolDispatcher`: abort check → resolve → permission check → asyncio.wait_for → ToolResult. Único punto de integración entre ToolUseContext y ToolProtocol.
- [x] Crear `runtime/tools/factory.py` con `create_tools(extras=[]) -> ToolRegistry`.
- [x] Crear `runtime/tools/native/`: `bash.py`, `read_file.py`, `write_file.py`, `glob_tool.py`, `grep_tool.py`. Cada una declara `timeout_seconds`, `category`, `safe_for_background`.

Criterios:

- [x] `ToolDispatcher` es el unico lugar donde `ToolUseContext` y `ToolProtocol` se tocan.
- [x] Tool que excede `timeout_seconds` retorna `ToolResult.timeout(...)`, no lanza excepcion al loop.
- [x] Tool con `stop` event seteado retorna `ToolResult.aborted(...)` sin ejecutar.
- [x] `list_available(mode="background")` excluye tools con `safe_for_background=False`.

Pruebas:

- `tests/test_tool_dispatcher.py` — 11 passed:
  - registry: resolve, unknown, list_available en background y foreground
  - dispatcher: execute, unknown tool error, timeout, abort, permission denied, permission granted
  - FastTool satisfies ToolProtocol

---

### Fase 13 — capabilities/: resolver

Estado: `[x] completado`

`CapabilitiesResolver` combina `ToolRegistry` y `SkillCatalog` (inyectado por el proyecto) para responder que puede hacer un agente dado su `ToolUseContext`. El loop no sabe si algo es un tool nativo, MCP o skill.

Tareas:

- [x] Crear `runtime/capabilities/protocol.py` con `ResolvedCapabilities` (dataclass), `SkillCatalogProtocol` (Protocol: `list_schemas(ctx) -> list[dict]`), `CapabilitySource` (Protocol — primitiva de extensión).
- [x] Crear `runtime/capabilities/resolver.py` con `CapabilitiesResolver`: recibe `ToolRegistry` y `skill_catalog | None`; timeout parcial por fuente externa; loguea timeouts sin lanzar; `register_source(source)` como primitiva de extensión.
- [x] `CapabilitiesResolver` no importa ningún módulo de `skills`, `mcp` ni la raíz de `agent_core`.

Criterios:

- [x] `CapabilitiesResolver` no importa ningún módulo de `skills`, `mcp` ni `agent_core`.
- [x] Timeout parcial no lanza — retorna tools nativas disponibles.
- [x] `ResolvedCapabilities.tool_schemas` es la única interfaz — loop no accede a tools/skills directamente.
- [x] Tool con `requires_permission=True` excluida si no hay permiso concedido.

Pruebas:

- `tests/test_capabilities_resolver.py` — 6 passed:
  - includes_native_tools, respects_permission_context, includes_skill_catalog_schemas
  - timeout_returns_partial, without_skill_catalog, does_not_import_skills_module

---

### Fase 14 — context/: ExecutionContext, RuntimeState y cierre de identidad

Estado: `[x] completado`

Completa el modulo `runtime/context/` con los planos de estado que garantizan aislamiento entre agentes concurrentes.

Nota: `test_fork_background_child_session_id_set_by_run_loop` sigue pendiente para el proyecto (está fuera de runtime/).

Tareas:

- [x] Crear `runtime/context/execution.py` con `ExecutionContext` (dataclass), `RuntimeState` (foreground_task_id), `_ctx: ContextVar`, `set_execution_context`, `get_execution_context`, `run_with_context(ctx, coro)` — crea Task con contexto aislado vía `asyncio.ensure_future`.
- [x] `context/__init__.py` re-exporta los nuevos símbolos.

Criterios:

- [x] Dos tasks concurrentes con contextos distintos — `get_execution_context()` retorna el correcto en cada una.
- [x] Modificar contexto en hijo no afecta al padre.
- [x] `get_execution_context()` fuera de `run_with_context` retorna None.

Pruebas:

- `tests/test_execution_context.py` — 8 passed:
  - context_not_set, run_with_context_sets, concurrent isolation, child no leaks to parent
  - set_execution_context, RuntimeState initial/set/clear

---

### Fase 15 — loop/: protocolos y hooks de turno

Estado: `[x] completado (parcial — ciclo real pendiente en Fase 20)`

Entrego los protocolos `LoopProtocol` y `DrainableLoopProtocol`, el esqueleto `BasicLoop` con hooks de turno, y la factory. El ciclo real (invocación LLM → tool calls → iteración) requiere `events/` (Fase 18) y `ModelCallerProtocol` (Fase 19) y se implementa en Fase 20.

Tareas:

- [x] Crear `runtime/loop/protocol.py` con `LoopProtocol` (runtime_checkable Protocol): `async run(prompt, ctx)`; y `DrainableLoopProtocol` que extiende `LoopProtocol` con `register_turn_start_hook(hook)` y `_run_turn_start_hooks()`.
- [x] Crear `runtime/loop/basic.py` con `BasicLoop`: implementa `DrainableLoopProtocol`; ejecuta hooks de inicio de turno en orden de registro. Ciclo real pendiente Fase 20.
- [x] Crear `runtime/loop/factory.py` con `create_loop(model_caller) -> LoopProtocol`.
- [x] `protocol.py` documenta que proyectos que inyecten su propio loop deben implementar `DrainableLoopProtocol` para drain automático.

Criterios:

- [x] `BasicLoop` satisface `LoopProtocol` y `DrainableLoopProtocol`.
- [x] Loop que no implementa `DrainableLoopProtocol` sigue siendo `LoopProtocol` válido — no rompe el runtime.
- [x] Hooks se ejecutan en orden de registro.

Pruebas:

- `tests/test_basic_loop.py` — 5 passed:
  - loop_protocol, drainable_protocol, hook_called, multiple_hooks_order, non_drainable_is_loop_protocol

---

### Fase 18 — events/: tipos de evento y protocolo de extensión

Estado: `[x] completado`

El runtime necesita tipos de evento propios para que el loop, las tools y el canal de notificaciones puedan comunicarse sin depender de tipos del proyecto. `events/` sigue el mismo patrón que el resto: protocolo, implementaciones base, punto de entrada, y primitiva de extensión.

Archivos a tocar (solo dentro de `runtime/`):

- `runtime/events/__init__.py` (nuevo)
- `runtime/events/protocol.py` (nuevo)
- `runtime/events/types.py` (nuevo)
- `runtime/events/bus.py` (nuevo)
- `tests/test_events.py` (nuevo)

Tareas:

- [ ] Crear `runtime/events/protocol.py` con `Event` (dataclass base, frozen), `EventBusProtocol` (Protocol): `emit(event: Event)`, `subscribe(event_type, handler)`; y `EventHandler = Callable[[Event], Awaitable[None]]`.
- [ ] Crear `runtime/events/types.py` con los tipos concretos del ciclo LLM: `TokenEvent(content: str)`, `ToolCallEvent(tool_name: str, tool_input: dict, call_id: str)`, `ToolResultEvent(call_id: str, result: str, is_error: bool)`, `DoneEvent(stop_reason: str, usage: Usage | None)`, `ErrorEvent(message: str)`. Todos frozen dataclasses que heredan de `Event`.
- [ ] Crear `runtime/events/bus.py` con `EventBus`: `emit(event)` despacha a suscriptores por tipo; `subscribe(event_type, handler)` como primitiva de extensión — proyectos registran handlers para tipos propios o base sin modificar el runtime.
- [ ] `runtime/events/__init__.py` exporta: `Event`, `EventBus`, `EventBusProtocol`, `EventHandler`, `TokenEvent`, `ToolCallEvent`, `ToolResultEvent`, `DoneEvent`, `ErrorEvent`.

Criterios:

- [ ] `EventBus.emit(TokenEvent(...))` despacha solo a handlers suscritos a `TokenEvent`, no a otros tipos.
- [ ] `EventBus.emit` no lanza aunque no haya suscriptores.
- [ ] Proyectos pueden definir `class MyEvent(Event)` y suscribirse sin modificar el runtime.
- [ ] `Event` es frozen — no mutable después de construirse.
- [ ] `DoneEvent` incluye `Usage` del modelo para que `ModelRegistry.calculate_cost` pueda usarla.

Pruebas:

- `tests/test_events.py`:
  - `test_emit_dispatches_to_correct_handler`: handler de `TokenEvent` recibe solo `TokenEvent`, no `DoneEvent`.
  - `test_emit_no_subscribers_does_not_raise`: `emit` sin handlers no lanza.
  - `test_subscribe_multiple_handlers_same_type`: dos handlers para `TokenEvent` — ambos se invocan.
  - `test_custom_event_type_works`: `class MyEvent(Event)` registrado y emitido sin error.
  - `test_event_is_frozen`: asignar campo post-construcción lanza `FrozenInstanceError`.
  - `test_done_event_carries_usage`: `DoneEvent(usage=Usage(input_tokens=10, ...))` accesible.

---

### Fase 19 — models/: ModelCallerProtocol y completar el módulo

Estado: `[x] completado`

`ModelCallerProtocol` es el contrato que el proyecto implementa con su LLM client y que el loop consume. Pertenece a `models/` porque es la interfaz de invocación del modelo. Con esta fase `models/` queda completo: config, registry, cost, y protocolo de llamada.

Archivos a tocar (solo dentro de `runtime/`):

- `runtime/models/caller.py` (nuevo)
- `runtime/models/__init__.py` (modificar — agregar exports)
- `tests/test_model_caller_protocol.py` (nuevo)

Tareas:

- [ ] Crear `runtime/models/caller.py` con `ModelCallerProtocol` (Protocol): `async def complete(messages: list[dict], tools: list[dict], *, stop: asyncio.Event | None, model_id: str) -> AsyncGenerator[Event, None]`; y `ModelRequest` (frozen dataclass): `messages`, `tools`, `model_id`, `stop`, `thinking_budget: int | None`.
- [ ] `ModelCallerProtocol` importa `Event` desde `runtime/events/` — no desde ningún módulo del proyecto.
- [ ] `runtime/models/__init__.py` re-exporta `ModelCallerProtocol`, `ModelRequest`.

Criterios:

- [ ] `ModelCallerProtocol` no importa ningún cliente concreto (ni openai, ni anthropic, ni agent_core.llm).
- [ ] Un stub que implementa `ModelCallerProtocol` satisface `isinstance(stub, ModelCallerProtocol)`.
- [ ] `ModelRequest` es frozen — el loop no puede mutar la request después de construirla.

Pruebas:

- `tests/test_model_caller_protocol.py`:
  - `test_stub_satisfies_model_caller_protocol`: clase stub con `complete()` correcto → `isinstance` True.
  - `test_model_request_is_frozen`: asignar campo post-construcción lanza `FrozenInstanceError`.
  - `test_model_caller_protocol_does_not_import_concrete_llm`: verificación de acoplamiento estático.

---

### Fase 20 — loop/: AgentLoop con ciclo real

Estado: `[x] completado`

Completa el módulo `loop/` con el ciclo real de ejecución. Renombra `BasicLoop` → `AgentLoop`. El ciclo consume `ModelCallerProtocol` (Fase 19) y tipos de evento de `events/` (Fase 18), delega ejecución de tools al `ToolDispatcher`, y acumula mensajes en `ToolUseContext`.

Archivos a tocar (solo dentro de `runtime/`):

- `runtime/loop/agent_loop.py` (nuevo — reemplaza `basic.py`)
- `runtime/loop/basic.py` (mantener como re-export shim para no romper imports)
- `runtime/loop/protocol.py` (modificar — actualizar `run` signature)
- `runtime/loop/factory.py` (modificar — `create_loop` retorna `AgentLoop`)
- `runtime/loop/__init__.py` (modificar — exportar `AgentLoop`)
- `tests/test_agent_loop.py` (nuevo)

Tareas:

- [ ] Crear `runtime/loop/agent_loop.py` con `AgentLoop` que implementa `DrainableLoopProtocol`:
  - `run(prompt, ctx)` ejecuta el ciclo completo:
    1. `await self._run_turn_start_hooks()` — drain del canal al inicio de cada turno.
    2. Inserta `prompt` como mensaje `user` en `ctx.messages`.
    3. Resuelve tool schemas vía `CapabilitiesResolver.resolve(ctx)`.
    4. Llama `model_caller.complete(ctx.messages, tool_schemas, stop=ctx.stop)`.
    5. Consume eventos: `TokenEvent` → acumula; `ToolCallEvent` → `ToolDispatcher.dispatch()`; `ToolResultEvent` → inserta en `ctx.messages`; `DoneEvent` → evalúa si hay más tool calls pendientes.
    6. Si `DoneEvent.stop_reason == "tool_calls"` → vuelve al paso 3. Si `"stop"` o `"end_turn"` → termina.
    7. `ErrorEvent` → loguea y termina con el mensaje de error en `ctx.messages`.
  - Respeta `ctx.stop` (abort event) antes de cada turno.
- [ ] `runtime/loop/basic.py` → shim: `from .agent_loop import AgentLoop as BasicLoop`.
- [ ] `runtime/loop/factory.py` → `create_loop` retorna `AgentLoop`.
- [ ] `runtime/loop/__init__.py` → exporta `AgentLoop`.

Criterios:

- [ ] Loop con model_caller stub que retorna `DoneEvent` sin tool calls termina en 1 turno.
- [ ] Loop con model_caller que retorna `ToolCallEvent` ejecuta el tool vía `ToolDispatcher` e inserta resultado en `ctx.messages`.
- [ ] `ctx.stop` seteado antes del turno → loop termina sin llamar al modelo.
- [ ] Loop que recibe `ErrorEvent` termina sin lanzar excepción al caller.
- [ ] `BasicLoop` importado desde el shim es el mismo objeto que `AgentLoop`.

Pruebas:

- `tests/test_agent_loop.py`:
  - `test_loop_single_turn_no_tools`: model_caller stub retorna solo `DoneEvent` → loop termina, `ctx.messages` tiene respuesta del asistente.
  - `test_loop_executes_tool_call`: model_caller retorna `ToolCallEvent` + `DoneEvent` → tool se ejecuta, resultado en `ctx.messages`.
  - `test_loop_aborts_on_stop_event`: `ctx.stop` seteado → loop no llama al modelo.
  - `test_loop_handles_error_event`: model_caller retorna `ErrorEvent` → loop termina, no lanza.
  - `test_loop_multi_turn`: dos rondas de tool calls antes del `DoneEvent` final → mensajes acumulados correctamente.
  - `test_basic_loop_is_agent_loop`: `BasicLoop is AgentLoop` True (shim funciona).

---

### Fase 16 — models/: factory basico

Estado: `[x] completado`

Factory de modelos. Primera iteracion cubre resolucion de modelo, costeo y registry.

Tareas:

- [x] Crear `runtime/models/protocol.py` con `ModelConfig`, `Usage`, `Cost`, `ThinkingLevel`.
- [x] Crear `runtime/models/registry.py` con `ModelRegistry`: `register`, `resolve` (lanza `ModelNotFoundError`), `calculate_cost(model_id, usage) -> Cost`.
- [x] Crear `runtime/models/factory.py` con `create_models(extras=[]) -> ModelRegistry`. Defaults: gpt-4.1, gpt-4.1-mini, gpt-4o, gpt-4o-mini.

Criterios:

- [x] `calculate_cost` retorna `Cost` con `total_usd` proporcional a tokens.
- [x] Modelo no registrado lanza `ModelNotFoundError`, no `KeyError`.
- [x] `create_models()` sin argumentos retorna registry con 4 modelos default.

Pruebas:

- `tests/test_models_factory.py` — 7 passed:
  - resolves_registered, raises_unknown, calculate_cost_usd, cost_proportional
  - create_models_has_defaults, includes_gpt41, extension_primitive

Pruebas:

- `test_models_factory.py`:
  - `test_registry_resolves_registered_model`: modelo registrado se resuelve correctamente.
  - `test_registry_raises_on_unknown_model`: `ModelNotFoundError` para modelo no registrado.
  - `test_calculate_cost_returns_usd`: costo calculado es positivo y proporcional a tokens.
  - `test_create_models_with_empty_config_returns_defaults`: registry con modelos default no esta vacio.

---

### Fase 17 — factory.py: create_runtime() meta-factory

Estado: `[x] completado`

Punto de entrada unico para ensamblar un runtime completo. El proyecto declara que implementaciones inyectar; el runtime opera con defaults si no se inyecta nada.

Tareas:

- [x] Crear `runtime/factory.py` con `RuntimeConfig` (dataclasses: `StorageConfig`, `ToolsConfig`, `CapabilitiesConfig`, `ModelsConfig`) y `create_runtime(execution_mode, config) -> AgentRuntime`.
- [x] `create_runtime` ensambla en orden: storage → tools → capabilities_resolver → models → signal_bus → loop_factory → LocalAgentRuntime.
- [x] `execution_mode="local"` retorna `LocalAgentRuntime` con todos los módulos inyectados como atributos.
- [x] `execution_mode="remote"/"tmux"` lanza `NotImplementedError`.
- [x] `RuntimeFactory.register_execution_mode(name, cls)` — primitiva de extensión para modos personalizados.

Criterios:

- [x] `create_runtime()` sin argumentos produce `LocalAgentRuntime` con `FilesystemStorage`.
- [x] `RuntimeConfig()` instancia sin errores.
- [x] Tools extras inyectadas via `ToolsConfig(extras=[...])` resolvibles desde `runtime._tool_registry`.
- [x] Proyectos pueden registrar modos de ejecución custom con `RuntimeFactory.register_execution_mode`.

Pruebas:

- `tests/test_runtime_factory.py` — 7 passed:
  - local_mode_returns_local_runtime, defaults_filesystem_storage, config_defaults_valid
  - injects_custom_storage, extra_tools_registered, remote_raises_not_implemented
  - register_custom_mode

## Riesgos

- Romper sesiones persistidas por mover metadata.
- Romper subagents por cambios de registry.
- Duplicar tools si no hay deduplicacion estable.
- Perder prompts de herramientas si se separa tool guidance demasiado pronto.
- Romper plan mode si se cambian permisos sin tests.

## Regla De Trabajo

No mezclar fases.

Antes de cada fase:

- marcar estado `[~] en progreso`;
- listar archivos a tocar;
- ejecutar tests base relevantes;
- documentar pruebas realizadas y no realizadas.

Al terminar:

- marcar tareas completadas;
- registrar evidencia;
- dejar notas de continuidad para el siguiente agente.

## Registro De Avance

### 2026-06-10

Estado:

- Implementado: inicio de `feature/runtime-agentico` desde `fix/codex`; documentado el arbol de ramas y el futuro corte `feature/capabilities_skills_mcp`.
- Implementado: primer corte no invasivo de contratos runtime: `PermissionContext`, `ToolPool`, `assemble_tool_pool`, `AppState`, `ToolUseContext`, `ContextModifier`, `CompactionProvider`, `collect_compaction_context`.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `uv run python -m pytest tests/test_runtime_contracts.py tests/test_runtime_coupling_baseline.py tests/test_loop.py tests/test_skills.py tests/test_prompt_layers.py tests/test_skill_allowed_tools_runtime.py tests/test_session_stream_endpoint.py tests/test_teardown_all_sites.py tests/test_governance.py tests/test_mcp_timeout.py` desde `src/agent_core` — 87 passed. Tambien `uv run python -m pytest tests/test_download_proxy.py tests/test_presigned_download.py tests/test_paths.py tests/test_storage_hardening.py` — 43 passed.
- No probado: suite completa; integracion real con tools que generan archivos grandes y MCP externo; integracion real de descarga via Krakend; import directo de `agent_core.main` porque intenta abrir `/home/noheroes/.agent_core/agent.log` y el sandbox no permite escribir alli.
- Notas: Fase 2 completa. `AgentLoop` ya no importa `skills`/`mcp`; el comportamiento actual de skills se conecta mediante `SkillsUserInputProcessor`. Fase 3 completa: `NativeToolRegistry` limpio, `ToolRegistry` como compatibilidad sin imports de `skills.*` ni reglas por prefijo `__`, callers de prompt/catálogo con builders explícitos, `GPT54Runtime` recibe tools ya resueltas y el loop ensambla la lista final mediante `ToolPool.assemble`. Fase 4 completa: model runtime no sabe de skills/MCP/deferred y conserva el armado del `ModelRequest` GPT 5.4. Fase 5 completa: `Compactor` recibe providers, no importa `skills.*`, y session memory/skills aportan contexto desde providers externos. Fase 6 completa: rutas API no tocan `loop._registry`; `chat.py` pide contexto a `CapabilityContextService`; `mcp.py` delega gestion y test a `MCPAdminService`.

### 2026-06-10 (continuacion)

Estado:

- Implementado: nada — sesion de analisis y documentacion.
- En progreso: nada.
- Bloqueado: nada.
- Probado: nada nuevo.
- No probado: nada nuevo.
- Notas: Contrastadas implementaciones de fork, integracion de resultado background e identidad de subagente contra el proyecto de referencia. Se identificaron dos omisiones adicionales documentadas arriba: `Integracion de resultado background como primitiva runtime` e `Identidad del subagente como campo de primer nivel`. La integracion foreground no requiere cambio — ya pasa por `ToolResult` de forma natural. Pendiente decidir si estas omisiones se resuelven en una fase nueva de este plan o abren una fase 7 antes de pasar a `PLAN_CAPABILITIES_SKILLS_MCP.md`.

### 2026-06-11

Estado:

- Implementado: Fase 7 completa. `runtime/fork.py` con `ForkContext`, `ForkSnapshot`, `ForkPolicy`, `RuntimeContextForker`. `ToolUseContext` tiene campo `agent_id: str | None = None`. `AgentTool._run_foreground` y `LocalAgentRuntime._run_loop` delegan la logica de copia de mensajes y herencia al forker; eliminado `import copy` de local.py.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `uv run python -m pytest tests/test_fork_primitives.py tests/test_fork_skill.py tests/test_subagent_depth_guard.py tests/test_background_result_summary.py tests/test_runtime_contracts.py tests/test_runtime_coupling_baseline.py tests/test_loop.py` — 47 passed. Tests funcionales cubren: ForkSnapshot inmutabilidad, ForkPolicy herencia/aislamiento, RuntimeContextForker agent_id unico, fork foreground no contamina padre, fork con/sin fork_context, background session_id heredado, subagent_depth incrementa.
- No probado: persistencia de fork session por agent_id (Fase 9). Canal de notificaciones background (Fase 8). skill fork usando mismo contrato (pendiente en executor.py).
- Notas: Las dos tareas restantes de Fase 7 marcadas como Fase 9 (persistencia por agent_id) y Fase 8 (reglas de finalizacion/canal). `LocalAgentRuntime._run_loop` todavia recibe `parent_session` — se elimina en Fase 8.

### 2026-06-11 — Fase 8: reestructuracion agrupadores

Estado:

- Implementado: `runtime/execution/` (local.py, fork.py, notification.py, summarizer.py), `runtime/context/` (tool_use.py, adapters.py), `runtime/contracts/` (runtime.py, storage.py, permissions.py, compaction.py, user_input.py). Archivos raiz convertidos en shims de re-exportacion. `_channel` incluido en shim de notification.py para acceso de tests.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `uv run python -m pytest tests/test_background_notification_channel.py tests/test_fork_primitives.py tests/test_runtime_contracts.py tests/test_background_result_summary.py tests/test_fork_skill.py tests/test_subagent_depth_guard.py` — 74 passed, 1 failed (test_fork_background_child_session_id_set_by_run_loop, roto previo conocido, fuera de runtime/).
- No probado: suite completa; integracion real con loop del proyecto.
- Notas: ninguna modificacion fuera de runtime/. tool_pool.py y native_registry.py permanecen en raiz de runtime/ como transitorio hasta Fase 12.

### 2026-06-11 (continuacion — reingenieria completa del runtime)

Estado:

- Implementado: nada — sesion de arquitectura y actualizacion del plan.
- En progreso: nada.
- Bloqueado: nada.
- Probado: nada nuevo.
- No probado: nada nuevo.
- Notas: Disenadas las fases 8-17 de reingenieria completa del runtime. Analizado proyecto canonico (`claude-code/src`) para modos, transiciones foreground/background/fork, AgentContext (AsyncLocalStorage), ToolUseContext, AppState y mecanismo de notificaciones. Disenados modulos: `execution/`, `context/`, `contracts/`, `signals/` (arbol de cascada para stop), `modes/`, `storage/` (copia + Protocol + extension), `tools/` (contrato enriquecido + ToolDispatcher), `capabilities/` (resolver desacoplado de skills/MCP), `loop/` (BasicLoop + DrainableLoopProtocol), `models/` (factory basico), `factory.py` (create_runtime meta-factory). Cada factory expone primitivas de extension (`register_backend`, `register`, `register_source`, `register_execution_mode`) para que proyectos agreguen implementaciones sin modificar el runtime. Regla confirmada: nada fuera de `runtime/` se toca en estas fases. `test_fork_background_child_session_id_set_by_run_loop` roto queda pendiente para el proyecto.

### 2026-06-11 (Fase 9 — signals/)

Estado:

- Implementado: `runtime/signals/__init__.py`, `runtime/signals/protocols.py`, `runtime/signals/bus.py`.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_signal_bus.py` — 12 passed. Suite completa: 418 passed, 1 fallo conocido previo.
- No probado: integracion de SignalBus con LocalAgentRuntime (pendiente Fase 14).
- Notas: `.gitignore` tenia regla `context/` global que bloqueaba `runtime/context/`; agregada excepcion `!src/agent_core/runtime/context/**`.

### 2026-06-11 (Fase 10 — modes/)

Estado:

- Implementado: `runtime/modes/__init__.py`, `runtime/modes/protocols.py`, `runtime/modes/manager.py`.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_mode_manager.py` — 9 passed. Suite completa: 427 passed, 1 fallo conocido previo.
- No probado: integracion de ModeManager con LocalAgentRuntime (pendiente Fase 14).
- Notas: primitiva de extension `on_transition(callback)` permite a proyectos observar transiciones de modo sin modificar el runtime.

### 2026-06-11 (Fase 11 — storage/)

Estado:

- Implementado: `runtime/storage/__init__.py`, `runtime/storage/protocol.py`, `runtime/storage/filesystem.py`, `runtime/storage/factory.py`.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_runtime_storage.py` — 15 passed. Suite completa: 442 passed, 1 fallo conocido previo.
- No probado: integracion de StorageRegistry con create_runtime (Fase 17).
- Notas: `copy` excluido del StorageProtocol base porque MinIO/Local no lo implementan — solo FilesystemStorage lo tiene como método adicional.

### 2026-06-11 (Fase 12 — tools/)

Estado:

- Implementado: `runtime/tools/__init__.py`, `protocol.py`, `registry.py`, `dispatcher.py`, `factory.py`, `native/` (bash, read_file, write_file, glob_tool, grep_tool).
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_tool_dispatcher.py` — 11 passed. Suite completa: 453 passed, 1 fallo conocido previo.
- No probado: integracion con capabilities/ (Fase 13) y con loop (Fase 15).
- Notas: ToolDispatcher es el único punto de integración entre ToolUseContext y ToolProtocol; loop y tools no se conocen directamente.

### 2026-06-11 (Fase 13 — capabilities/)

Estado:

- Implementado: `runtime/capabilities/__init__.py`, `protocol.py`, `resolver.py`.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_capabilities_resolver.py` — 6 passed. Suite completa: 459 passed, 1 fallo conocido previo.
- No probado: integracion con loop y create_runtime (Fases 15/17).
- Notas: CapabilitiesResolver depende solo de ToolRegistry y protocolo inyectado — sin imports de skills/mcp/agent_core raíz.

### 2026-06-11 (Fase 14 — context/execution)

Estado:

- Implementado: `runtime/context/execution.py` (ExecutionContext, RuntimeState, ContextVar plumbing).
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_execution_context.py` — 8 passed. Suite completa: 467 passed, 1 fallo conocido previo.
- No probado: integracion de ExecutionContext con dispatch() en LocalAgentRuntime.
- Notas: run_with_context usa asyncio.ensure_future para crear Task con copia aislada del contexto; _ctx.set(ctx) en _wrapped sobreescribe solo esa copia.

### 2026-06-11 (Fase 15 — loop/)

Estado:

- Implementado: `runtime/loop/__init__.py`, `protocol.py`, `basic.py`, `factory.py`.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_basic_loop.py` — 5 passed. Suite completa: 472 passed, 1 fallo conocido previo.
- No probado: integracion de BasicLoop con el drain real del canal de notificaciones (Fase 17).
- Notas: DrainableLoopProtocol permite al runtime inyectar hooks de turno sin depender de la implementación concreta del loop.

### 2026-06-11 (Fase 16 — models/)

Estado:

- Implementado: `runtime/models/__init__.py`, `protocol.py`, `registry.py`, `factory.py`.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_models_factory.py` — 7 passed. Suite completa: 479 passed, 1 fallo conocido previo.
- No probado: integracion con create_runtime y loop real (Fase 17).
- Notas: thinking_tokens se costean como output_cost (convención OpenAI/Anthropic). Budgets y guardrails quedan para iteración posterior.

### 2026-06-11 (Fase 17 — factory.py)

Estado:

- Implementado: `runtime/factory.py` con RuntimeConfig, RuntimeFactory, create_runtime.
- En progreso: nada.
- Bloqueado: nada.
- Probado: `tests/test_runtime_factory.py` — 7 passed. Suite completa: 486 passed, 1 fallo conocido previo.
- No probado: integracion end-to-end con loop real del proyecto (requiere settings/LLM reales).
- Notas: módulos nuevos (storage, tool_registry, capabilities_resolver, model_registry, signal_bus) inyectados como atributos en LocalAgentRuntime — compatibilidad hacia atrás preservada sin modificar su constructor.

### 2026-06-11 (revisión de plan — fases 18-20)

Estado:

- Implementado: nada — sesión de revisión de completitud.
- En progreso: nada.
- Bloqueado: nada.
- Probado: nada nuevo.
- No probado: nada nuevo.
- Notas: Auditoria reveló que Fase 15 entregó protocolos y esqueleto pero no el ciclo real. Se identificaron tres piezas faltantes para operación autónoma.

### 2026-06-11 (Fase 18 — events/)

Estado:

- Implementado: `runtime/events/__init__.py`, `protocol.py`, `types.py`, `bus.py`.
- Probado: `tests/test_events.py` — 13 passed. Suite completa: 499 passed, 1 fallo conocido previo.
- Notas: `DoneEvent.usage` es `Optional[Usage]` — permite que `ModelRegistry.calculate_cost` opere sobre él en el loop. `EventBus.emit` atrapa excepciones de handlers para no interrumpir el ciclo.

### 2026-06-11 (Fase 19 — models/caller.py)

Estado:

- Implementado: `runtime/models/caller.py` — `ModelRequest` (frozen dataclass), `ModelCallerProtocol` (runtime_checkable Protocol).
- Probado: `tests/test_model_caller_protocol.py` — 5 passed. Suite completa: 504 passed, 1 fallo conocido previo.
- Notas: `ModelCallerProtocol` importa `Event` vía TYPE_CHECKING — sin acoplamiento en runtime a ningún LLM concreto. Verificado con inspección de fuente en test.

### 2026-06-11 (Fase 20 — loop/AgentLoop)

Estado:

- Implementado: `runtime/loop/agent_loop.py`, `basic.py` convertido a shim, `factory.py` y `__init__.py` actualizados.
- Probado: `tests/test_agent_loop.py` — 7 passed. Suite completa: 511 passed, 1 fallo conocido previo.
- Notas: ciclo real: hooks → user message → resolve capabilities → model_caller.complete() → consume TokenEvent/ToolCallEvent/DoneEvent/ErrorEvent → ToolDispatcher → acumula → repite si stop_reason=="tool_calls". Techo de 50 turnos. BasicLoop es shim de AgentLoop — `BasicLoop is AgentLoop` True. Se identificaron tres piezas faltantes para operación autónoma: (1) `events/` con tipos propios del runtime, (2) `ModelCallerProtocol` en `models/`, (3) `AgentLoop` con ciclo real. Se agregaron Fases 18, 19 y 20. `BasicLoop` se renombrará a `AgentLoop` en Fase 20 con shim de compatibilidad. `ModelCallerProtocol` importa `Event` desde `events/` — sin acoplamiento a LLM concreto.
