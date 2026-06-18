# Plan de Documentación — agentic_runtime (Obsidian)

Estado general: `[ ] no iniciado` `[~] en progreso` `[x] completado`
Estado actual: `[ ] no iniciado`

## Objetivo

Documentar `agentic_runtime` en el vault de Obsidian, **una página por etapa**, de modo que al
terminar cada etapa se pueda `/clear` sin perder el hilo. La técnica va primero; las guías de uso
(cómo lo implementa un tercero) van al final, con especial cuidado.

- **Repo:** `/home/noheroes/python/agentic_runtime` (paquete `src/agentic_runtime`).
- **Destino Obsidian:** carpeta `agent-runtime/` del vault (vía MCP `obsidian`). Índice:
  `agent-runtime/index.md`. Páginas técnicas en `agent-runtime/wiki/<slug>.md`; guías de uso en
  `agent-runtime/wiki/uso/<slug>.md`.
- **Proyecto hermano:** `agent-llm/` documenta `agentic_models` (el runtime lo consume vía
  `models/caller.py`). Enlazar con `[[agent-llm/index]]` donde aplique.

## Cómo retomar tras un `/clear` (protocolo de cada sesión)

1. Leer este archivo: ir al **§Registro De Avance** y a la **tabla de etapas**; identificar la
   primera etapa `[ ]`.
2. Cargar las tools del MCP de Obsidian con `ToolSearch` (`select:mcp__obsidian__vault_write,
   mcp__obsidian__vault_read,mcp__obsidian__vault_patch,mcp__obsidian__vault_list,
   mcp__obsidian__vault_get_document_map`).
3. Leer **solo** las "Fuentes" listadas para esa etapa (no más — el objetivo es no saturar).
4. Escribir la página destino con `vault_write` (crea o reemplaza). Seguir la **Convención de página**.
5. Actualizar la TOC en `agent-runtime/index.md` (añadir el `[[wikilink]]` de la página nueva).
6. Marcar la etapa `[x]` en la tabla + una línea en el **§Registro De Avance** (el WHY/lo verificado,
   no el WHAT). Luego `/clear` y repetir.

## Convención de página (estándar del vault)

- **Verificado contra código.** Cada afirmación sale de leer el código actual, no de memoria.
- Encabezado con un bloque **Fuente** que cite los archivos exactos leídos (ruta relativa al paquete;
  `archivo.py:línea` cuando se referencia algo puntual) y la fecha de verificación.
- Idioma español (Perú). Enlaces internos con `[[wikilink]]`. Tono de referencia, no tutorial salvo
  en `wiki/uso/`.
- No documentar lo trivial (imports, `__init__` vacíos); documentar contratos, responsabilidades,
  invariantes, puntos de extensión y "qué inyecta el integrador".
- Plantilla mínima:
  ```markdown
  # <Título>

  > **Fuente:** `tools/dispatcher.py`, `tools/pool.py` — verificado contra código 2026-06-18.

  <cuerpo>

  ## Referencias cruzadas
  - [[agent-runtime/index]]
  ```

## Etapas (1 página por etapa)

### Bloque 0 — Setup

| # | Página destino | Fuentes a leer | Criterio de cierre |
|---|---|---|---|
| E0 | `agent-runtime/index.md` (actualizar) | `pyproject.toml`, salida de tests/lint, este plan | Índice con repo path correcto (`agentic_runtime`, NO `agent-runtime`), estado real (tests/lint), y TOC con todas las páginas planeadas (como enlaces aún por crear) |

### Bloque 1 — Técnica

| # | Página destino | Fuentes a leer | Criterio de cierre |
|---|---|---|---|
| T1 | `wiki/arquitectura.md` | `__init__.py`, `factory.py`, `contracts/runtime.py`; de contexto `PLAN_RUNTIME_AGENTICO.md` y `PLAN_COMPLEMENTARIO_RUNTIME.md` | Visión general: qué es/no es (runtime agnóstico, sin entry point/HTTP/auth), principios D1–D5, capas, diagrama del flujo de un turno |
| T2 | `wiki/factory.md` | `factory.py`, `contracts/runtime.py` | `create_runtime()` + `RuntimeConfig`/`CapabilitiesConfig`: qué ensambla, qué exige al integrador, qué trae por defecto |
| T3 | `wiki/contratos.md` | `contracts/{runtime,permissions,storage,compaction,user_input}.py` | Catálogo de Protocols de frontera y quién los implementa (runtime vs integrador) |
| T4 | `wiki/loop.md` | `loop/{agent_loop,protocol,basic,factory}.py` | El loop: fases del turno, ensamblaje de pool por turno, aplicación de `context_modifier`, cierre |
| T5 | `wiki/modelos-caller.md` | `models/{caller,protocol}.py` | `ModelCallerProtocol` + `AgenticModelsCaller` (puente a `agent-llm`); `system_sections`, `model_id` por request. Enlazar `[[agent-llm/index]]` |
| T6 | `wiki/eventos.md` | `events/{bus,event_types,protocol}.py` | Bus de eventos, taxonomía de eventos (TokenEvent, tool, etc.), cómo se suscribe el integrador |
| T7 | `wiki/tools-core.md` | `tools/{protocol,dispatcher,pool,registry,native_registry,factory,exec_env,deferred}.py` | Modelo de tools: protocolo, dispatch desde `ctx.tool_pool`, `assemble_tool_pool` (prefijo nativo/dedup/deny), deferred/ToolSearch, exec env inyectable |
| T8 | `wiki/tools-nativas.md` | `tools/native/*.py` (17 archivos) | Catálogo de tools nativas: propósito + permisos de cada una (bash, read/write/edit, glob/grep, agent, task_tools, todo_write, plan_mode, worktree, web_*, ask_user, sleep, config, tool_search) |
| T9 | `wiki/contexto.md` | `context/{tool_use,execution,presentation,adapters}.py` | `ToolUseContext`/`ExecutionContext`, `PathPresentation` (choke point), adapters; qué estado viaja por turno |
| T10 | `wiki/ejecucion.md` | `execution/runner.py`, `execution/local/{runtime,notification,summarizer}.py` | `LocalAgentRuntime`, runner, canal de notificación de background, summarizer/compactación |
| T11 | `wiki/sesiones-tareas.md` | `execution/session/{protocol,session}.py`, `execution/tasks/{registry,status}.py`, `execution/observer/{events,observer}.py`, `execution/fork/__init__.py`, `execution/context/agent_context.py` | Sesión, registro de tareas + estados, observer, fork de contexto, agent_id |
| T12 | `wiki/modos-senales.md` | `modes/{manager,protocols}.py`, `signals/{bus,protocols}.py` | ModeManager (transición de modo), SignalBus (abort/cascade); estado actual de cableado |
| T13 | `wiki/hooks.md` | `hooks/{protocol,runner}.py` | Sistema de hooks: protocolo, runner, puntos de invocación |
| T14 | `wiki/storage.md` | `storage/{protocol,filesystem,factory}.py`, `contracts/storage.py` | `StorageProtocol`, default filesystem, factory/registry, taxonomía `StorageKeys` (dos planos) |
| T15 | `wiki/capabilities-core.md` | `capabilities/{protocol,contracts,manager,resolver}.py` | Modelo de capability: `CapabilityProvider`, `CapabilityManager`, convergencia native↔capability (`build_tool_pool`), `CapabilitiesResolver` |
| T16 | `wiki/capability-mcp.md` | `capabilities/mcp/*.py` (10 archivos) | Provider MCP: cliente (stdio/http), config + auth (estrategias none/bearer/oauth), state, tool_adapter, resources, stores; lo que inyecta el integrador (TokenStorage, handlers) |
| T17 | `wiki/capability-skills.md` | `capabilities/skills/*.py` (8 archivos) | Provider Skills: frontmatter, loader, SkillTool, context modifier, catálogo, slash commands, store, base_dir |
| T18 | `wiki/capability-memoria.md` | `capabilities/memory/*.py` (5 archivos) | Provider Memoria: store filesystem, recall, prompt section, scope (`main` vs subagente), guardado canónico vía `write_file` |
| T19 | `wiki/capability-voz.md` | `voice/{protocol}.py`, `factory.py` (VoiceConfig + `_wire_tts`/`_resolve_prompt`) | Capability de borde STT/TTS: puertos, plomería en el runtime, activación por config, barge-in |

### Bloque 2 — Uso (cómo implementarlo — especial atención)

| # | Página destino | Fuentes a leer | Criterio de cierre |
|---|---|---|---|
| U1 | `wiki/uso/quickstart.md` | `factory.py`, `scripts/` o `tests/test_runtime_e2e.py` | Mínimo viable: `create_runtime()` → despachar una task → leer el resultado/stream. Ejemplo copy-paste verificado |
| U2 | `wiki/uso/inyeccion-dependencias.md` | `contracts/*.py`, `factory.py` | Qué DEBE proveer el integrador vs qué trae por defecto: model caller, storage, presentation, permissions, exec env. Tabla puerto→default→cuándo reemplazar |
| U3 | `wiki/uso/eventos-streaming.md` | `events/*.py`, un test de loop | Suscribirse a eventos, stream de tokens, eventos de tool; patrón para una UI/relay |
| U4 | `wiki/uso/activar-capabilities.md` | `factory.py` (`CapabilitiesConfig`), tests E2E de capabilities | Habilitar MCP servers, skill dirs, memoria y voz por config; sembrar permisos (`initial_allowed_tools`) |
| U5 | `wiki/uso/subagentes-background.md` | `tools/native/{agent,task_tools}.py`, `execution/{tasks,fork,local/notification}` | Lanzar subagentes, background tasks, fork de contexto, recibir notificaciones |
| U6 | `wiki/uso/permisos-y-modos.md` | `contracts/permissions.py`, `tools/native/{plan_mode,worktree}.py`, `modes/` | Modelo de permisos, plan mode, worktree; cómo gobernar qué puede hacer el agente |
| U7 | `wiki/uso/checklist-integrador.md` | revisión de las páginas anteriores | Checklist de integración end-to-end + errores comunes + enlaces a todas las páginas. Cierre del plan |

## Mapeo etapa → página (resumen para la TOC del índice)

Técnica: arquitectura, factory, contratos, loop, modelos-caller, eventos, tools-core, tools-nativas,
contexto, ejecucion, sesiones-tareas, modos-senales, hooks, storage, capabilities-core,
capability-mcp, capability-skills, capability-memoria, capability-voz.
Uso: quickstart, inyeccion-dependencias, eventos-streaming, activar-capabilities,
subagentes-background, permisos-y-modos, checklist-integrador.

## Registro De Avance

<!-- Una línea por etapa cerrada: fecha — etapa — qué se verificó / decisiones. El WHY, no el WHAT. -->
