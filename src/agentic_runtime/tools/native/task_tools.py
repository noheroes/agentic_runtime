"""
Task management tools — equivalente Python de TaskCreate/Get/List/Update/Stop/Output del canónico.

**`C7` retira el doble camino.** Estas seis tools iban por el global `get_registry()`
mientras `LocalAgentRuntime` usaba **su propia instancia inyectada**: dos caminos que
podían divergir (`SEAMS §S19`, `existe-doble-camino`) y que de hecho divergían, porque
nadie llamaba `set_registry` en producción ⇒ las seis reventaban con `RuntimeError`, el
mismo modo de fallo que `FIND-EXEC1`. Ahora hay UN camino: el registry del runtime,
threadeado al `ctx` (`S19` por DI).
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

_NO_REGISTRY = (
    "Task registry not wired: this runtime was assembled without `S19` "
    "(RuntimeConfig.task_registry → LocalAgentRuntime → ctx.task_registry)."
)


def _session_of(ctx: ToolUseContext | None) -> str | None:
    """Lista activa = sesión del contexto (espejo de `getTaskListId()`)."""
    return getattr(ctx, "session_id", None)


def _registry_of(ctx: ToolUseContext | None) -> Any:
    """El registry del turno. `None` = costura sin poblar: la tool devuelve `is_error`
    limpio, no levanta — que es lo que el global hacía y por lo que nadie lo notaba."""
    return getattr(ctx, "task_registry", None)


# Anotación SIN comillas a propósito, a diferencia de sus vecinas: el fichero tiene
# `from __future__ import annotations`, así que las comillas sobran y `ruff` las cuenta
# (`UP037`). Las vecinas son deuda heredada; ésta no la aumenta.
def _is_own_task(task_id: str, ctx: ToolUseContext | None) -> bool:
    """¿Es `task_id` la tarea que está ejecutando a quien llama? (`FIND-TASK-SELF-1`)

    En A el turno en curso **no existe** para estas tools: `TaskStopTool.ts` valida
    contra `appState.tasks`, que sólo contiene tareas de FONDO (shells, agentes async,
    sesiones remotas). B fusionó ese registro con la lista por sesión en un único
    `InMemoryTaskRegistry` donde la tarea raíz también vive, así que sin esta guarda
    `TaskList` se la sirve al modelo y `TaskStop` la mata: `kill` hace
    `asyncio_task.cancel()` sobre el propio bucle (`registry.py:118-125`).

    Medido, no supuesto: RONDA 6 del E2g (`seed 986409977`) murió así, «CANCELADA
    esperando el stream del modelo», con la respuesta vacía.

    Es una guarda, no la topología de A: la separación de los dos registros queda
    declarada y pendiente junto a `FIND-TASK-1`, no disimulada aquí."""
    own = getattr(ctx, "task_id", "")
    return bool(own) and task_id == own


def _scoped_get(task_id: str, ctx: ToolUseContext | None) -> Any:
    """Resuelve un task SÓLO si pertenece a la lista de la sesión activa.

    Un `task_id` de otra sesión es invisible (espejo: no está en el tasks-dir
    de esta sesión) → se trata como inexistente. La tarea EN CURSO tampoco es
    resoluble (`_is_own_task`): en A no está en el registro que estas tools leen."""
    registry = _registry_of(ctx)
    if registry is None:
        return None
    if _is_own_task(task_id, ctx):
        return None
    record = registry.get(task_id)
    if record is None or record.owner_session_id != _session_of(ctx):
        return None
    return record


class TaskCreateTool:
    name = "TaskCreate"
    # `searchHint` del canónico, grafía literal (`TaskCreateTool.ts:50`). Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "create a task in the task list"
    # Homologada contra `TaskCreateTool/prompt.ts:16-56` (`getPrompt()`), `GAP-PROMPT-1`.
    # OMITIDO Y DECLARADO, porque el esquema de B no lo acepta y anunciarlo repetiría
    # `FIND-E11-3` (el modelo llama con un campo que la tool se traga en silencio):
    #   · `activeForm` (`:47`) — B no tiene spinner ni campo donde guardarlo.
    #   · «use TaskUpdate to set up dependencies (blocks/blockedBy)» (`:54`) — el
    #     `TaskUpdate` de B sólo reescribe `description`; no hay grafo de dependencias.
    #   · rama `isAgentSwarmsEnabled()` (`:6-14`) — apagada también en A por defecto.
    description = """Use this tool to create a structured task list for your current coding session. \
This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool

Use this tool proactively in these scenarios:

- Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
- Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
- Plan mode - When using plan mode, create a task list to track the work
- User explicitly requests todo list - When the user directly asks you to use the todo list
- User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
- After receiving new instructions - Immediately capture user requirements as tasks

## When NOT to Use This Tool

Skip using this tool when:
- There is only a single, straightforward task
- The task is trivial and tracking it provides no organizational benefit
- The task can be completed in less than 3 trivial steps
- The task is purely conversational or informational

NOTE that you should not use this tool if there is only one trivial task to do. In this case you \
are better off just doing the task directly.

## Task Fields

- **subject**: A brief, actionable title in imperative form (e.g., "Fix authentication bug in login flow")
- **description**: What needs to be done

All tasks are created with status `pending`.

## Tips

- Create tasks with clear, specific subjects that describe the outcome
- Check TaskList first to avoid creating duplicate tasks
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "Brief title for the task."},
            "description": {"type": "string", "description": "What needs to be done."},
        },
        "required": ["subject", "description"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        subject = input.get("subject", "")
        description = input.get("description", "")
        registry = _registry_of(ctx)
        if registry is None:
            return ToolResult.error(self.name, _NO_REGISTRY)
        record = registry.register(
            description=f"{subject}: {description}", session_id=_session_of(ctx)
        )
        return ToolResult(
            tool_name=self.name,
            output=json.dumps({"task_id": record.task_id, "subject": subject}),
        )


class TaskGetTool:
    name = "TaskGet"
    # `searchHint` del canónico, grafía literal (`TaskGetTool.ts:40`). Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "retrieve a task by ID"
    # Homologada contra `TaskGetTool/prompt.ts:3-22` (`PROMPT`), `GAP-PROMPT-1`.
    # OMITIDO Y DECLARADO: `blocks` / `blockedBy` (`:8`, `:16-17`, `:21`) — B no tiene
    # grafo de dependencias, así que anunciarlos prometería una salida inexistente.
    # AÑADIDO por conducta REAL de B, no por invención: `result`, que el `execute`
    # sí devuelve (`:105-110`); callarlo dejaría al modelo sin saber dónde mirar.
    description = """Use this tool to retrieve a task by its ID from the task list.

## When to Use This Tool

- When you need the full description and context before starting work on a task
- After being assigned a task, to get complete requirements

## Output

Returns full task details:
- **task_id**: Task identifier
- **description**: Detailed requirements and context
- **status**: task status, e.g. 'pending', 'running', 'completed'
- **result**: the task's result once it has one, otherwise null

## Tips

- Use TaskList to see all tasks in summary form.
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the task."}
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        task_id = input.get("task_id", "")
        record = _scoped_get(task_id, ctx)
        if record is None:
            return ToolResult.error(self.name, f"No task found with id: {task_id}")
        return ToolResult(
            tool_name=self.name,
            output=json.dumps({
                "task_id": record.task_id,
                "description": record.description,
                "status": record.status,
                "result": record.result,
            }),
        )


class TaskListTool:
    name = "TaskList"
    # `searchHint` del canónico, grafía literal (`TaskListTool.ts:35`). Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "list all tasks"
    # Homologada contra `TaskListTool/prompt.ts:24-49` (`getPrompt()`), `GAP-PROMPT-1`.
    # OMITIDO Y DECLARADO: `owner` y `blockedBy` (`:44-46`) y todo el criterio de
    # «disponible» que se apoya en ellos (`:31`, `:36`) — B no los tiene. También la
    # rama `isAgentSwarmsEnabled()` (`:7-36`), apagada por defecto en A.
    description = """Use this tool to list all tasks in the task list.

## When to Use This Tool

- To see what tasks are available to work on
- To check overall progress on the project
- After completing a task, to check for the next available task
- **Prefer working on tasks in ID order** (lowest ID first) when multiple tasks are available, \
as earlier tasks often set up context for later ones

## Output

Returns a summary of each task:
- **task_id**: Task identifier (use with TaskGet, TaskUpdate)
- **description**: Brief description of the task
- **status**: task status, e.g. 'pending', 'running', 'completed'

Use TaskGet with a specific task ID to view full details including its result.
"""
    #: **Sin parámetros, como el canónico** (`TaskListTool.ts:13`:
    #: `inputSchema = z.strictObject({})`).
    #:
    #: ⚠ Aquí había un `status` de filtro que **A no tiene**, y que cobró en `E11`
    #: (`FIND-E11-3`): el modelo leyó «Filter by status (pending, running, …). Omit
    #: for all.» y llamó con `status="all"`. Como el campo era `string` libre —sin
    #: `enum` que acotara el dominio— y el filtro comparaba por igualdad, un valor
    #: fuera de dominio se tragaba en silencio y devolvía `[]`: **indistinguible de
    #: «no hay tareas»**. El modelo concluyó que la sesión no tenía trabajos y
    #: respondió eso, con dos tareas sembradas delante. No es un fallo del modelo:
    #: es una invención de B, mal acotada, que hace mentir a la tool. `L10` —una
    #: divergencia con el canónico no es una mejora hasta que se demuestre— así que
    #: se retira en vez de parchearse con un `enum`.
    input_schema: dict[str, Any] = {"type": "object", "properties": {}}  # noqa: RUF012
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        registry = _registry_of(ctx)
        if registry is None:
            return ToolResult.error(self.name, _NO_REGISTRY)
        # Escopado a la lista de la sesión activa (espejo de `getTaskListId()` →
        # `getSessionId()`): una sesión sólo ve sus propias tareas, sin bleed.
        # La tarea EN CURSO se excluye del listado (`FIND-TASK-SELF-1`): en A el turno
        # principal no es una entrada de `appState.tasks`, y ofrecérsela al modelo es
        # justo lo que le hizo apuntarle un `TaskStop`.
        records = [
            r for r in registry.list_for(_session_of(ctx))
            if not _is_own_task(r.task_id, ctx)
        ]

        return ToolResult(
            tool_name=self.name,
            output=json.dumps([
                {
                    "task_id": r.task_id,
                    "description": r.description,
                    "status": r.status,
                }
                for r in records
            ]),
        )


class TaskUpdateTool:
    name = "TaskUpdate"
    # `searchHint` del canónico, grafía literal (`TaskUpdateTool.ts:90`). Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "update a task"
    # Homologada contra `TaskUpdateTool/prompt.ts:3-84` (`PROMPT`), `GAP-PROMPT-1`.
    #
    # ⚠ Ésta es la más recortada de la familia, y el recorte NO es cosmético: de los
    # 8 campos actualizables de A (`:35-43`) B acepta UNO, `description`. Todo el
    # cuerpo del canónico —flujo de estados `pending → in_progress → completed`, el
    # `deleted`, `owner`, `metadata`, `addBlocks`/`addBlockedBy` y sus 5 ejemplos
    # (`:60-84`)— habla de parámetros que el esquema de B **no tiene**. Portarlo
    # literal sería la trampa exacta de `FIND-E11-3`: el modelo lee el campo, lo
    # manda, y B lo descarta en silencio.
    #
    # La carencia de fondo queda registrada aparte como `FIND-TASK-1` (en B no hay
    # forma de que el modelo marque una tarea como completada; el `status` lo mueve
    # sólo el registry por la ejecución en background). Eso NO se paga con una
    # descripción y no se disimula con una.
    description = """Use this tool to update a task in the task list.

## When to Use This Tool

**Update task details:**
- When requirements change or become clearer

## Fields You Can Update

- **description**: Change the task description

## Staleness

Make sure to read a task's latest state using `TaskGet` before updating it.

## Examples

Rewrite a task's description:
```json
{"task_id": "1", "description": "Run the integration tests, not just the unit tests"}
```
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The task ID to update."},
            "description": {"type": "string", "description": "New description."},
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        task_id = input.get("task_id", "")
        record = _scoped_get(task_id, ctx)
        if record is None:
            return ToolResult.error(self.name, f"No task found with id: {task_id}")

        new_desc = input.get("description")
        if new_desc is not None:
            record.description = new_desc

        return ToolResult(
            tool_name=self.name,
            output=json.dumps({"task_id": task_id, "description": record.description}),
        )


class TaskStopTool:
    name = "TaskStop"
    # `searchHint` del canónico, grafía literal (`TaskStopTool.ts:41`). Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "kill a running background task"
    # Homologada contra `TaskStopTool/prompt.ts:3-8` (`DESCRIPTION`), `GAP-PROMPT-1`.
    # Portada LITERAL: es la única de la familia donde la conducta de A y la de B
    # coinciden campo a campo, así que no hay nada que omitir ni que adaptar.
    description = """
- Stops a running background task by its ID
- Takes a task_id parameter identifying the task to stop
- Returns a success or failure status
- Use this tool when you need to terminate a long-running task
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the task to stop."}
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        task_id = input.get("task_id", "")
        if _scoped_get(task_id, ctx) is None:
            return ToolResult.error(
                self.name, f"Task {task_id} not found or already terminal."
            )
        killed = _registry_of(ctx).kill(task_id)
        if not killed:
            return ToolResult.error(
                self.name, f"Task {task_id} not found or already terminal."
            )
        return ToolResult(
            tool_name=self.name,
            output=f"Task {task_id} stopped.",
        )


class TaskOutputTool:
    name = "TaskOutput"
    # `searchHint` del canónico, grafía literal (`TaskOutputTool.tsx:146`). Fuera del
    # contrato T1 (`contracts/tools.py:5`); lo lee ToolSearch para rankear.
    search_hint = "read output/logs from a background task"
    # Homologada contra `TaskOutputTool.tsx:172-182` (prompt inline en `async prompt()`),
    # `GAP-PROMPT-1`.
    # OMITIDO Y DECLARADO:
    #   · El encabezado `DEPRECATED: Prefer using the Read tool on the task's output
    #     file path` (`:173`) — en B las tareas NO devuelven un `output_file`; el
    #     resultado vive en `record.result` y `TaskOutput` es la ÚNICA vía. Portar el
    #     «usa Read en su lugar» mandaría al modelo a un fichero que no existe.
    #   · `block=true/false` (`:178-179`) — B no tiene ese parámetro; su lectura no
    #     bloquea nunca y devuelve el estado si aún no hay resultado (`:241-245`).
    #   · «Task IDs can be found using the /tasks command» (`:180`) — superficie de
    #     CLI del integrador, no del runtime.
    description = """\
- Retrieves output from a running or completed task (background shell, agent, or remote session)
- Takes a task_id parameter identifying the task
- Returns the task output along with status information
- Works with all task types: background shells, async agents, and remote sessions
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the task."}
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        task_id = input.get("task_id", "")
        record = _scoped_get(task_id, ctx)
        if record is None:
            return ToolResult.error(self.name, f"No task found with id: {task_id}")
        if record.result is None:
            return ToolResult(
                tool_name=self.name,
                output=f"Task {task_id} has status '{record.status}' and no result yet.",
            )
        return ToolResult(tool_name=self.name, output=record.result)
