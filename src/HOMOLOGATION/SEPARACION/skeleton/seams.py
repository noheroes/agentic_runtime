"""Costuras (SEAMS.md) que el andamiaje A2.1 declara como Protocols.

Sólo las firmas que A2.1 ejercita (SEAMS §5): S4/S5/S16/S11 + el mínimo de S1/S2
que un loop necesita para pedir una vuelta de modelo. Las firmas RICAS (S1 enriquecida
con thinking/effort/tool_choice; S16 con check_permissions/output_schema) llegan en
A2.2/A2.3 — aquí se deja el borrador MÍNIMO forward-compatible, no la firma final.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from skeleton.contracts import (
    Event,
    Message,
    ResultEvent,
    RuntimeTask,
    TaskStatus,
    ToolResult,
    ToolSchema,
    Usage,
)


# --- S2 · señal de abort (T1-MOTOR) ------------------------------------------
@runtime_checkable
class AbortSignal(Protocol):
    """SEAMS §S2. En la mímica se pasa un `asyncio.Event` roto (16·A6: el provider
    chequea `.aborted`, que Event no tiene). Aquí la costura correcta: `.aborted`."""

    @property
    def aborted(self) -> bool: ...


# --- S1 · costura al motor de modelo (T1-MOTOR) — MÍNIMA para A2.1 ------------
@runtime_checkable
class ModelCallerProtocol(Protocol):
    """SEAMS §S1 (LA costura central). Firma enriquecida y VALIDADA/CORREGIDA en A2.2
    contra `agentic_models` con un turno real texto-solo (`bridge.AgenticModelsCaller`).

    Reparto validado (leyendo `agentic_models.providers.anthropic._build_params`):
    - **Viajan por `StreamOptions` (passthrough, VALIDADO por el turno real):**
      `temperature` (sólo si no hay thinking, anthropic.py:290) · `max_tokens`
      (→ `model.max_tokens` si None) · `metadata` (sólo `user_id` se reenvía,
      anthropic.py:320-323) 【id-opaco】 · `stop` → `StreamOptions.signal`.
    - **NO viajan por `StreamOptions` (CORRECCIÓN A2.2 al borrador SEAMS):**
      `effort`/`thinking`/`tool_choice` se leen por `getattr(options, ...)` (duck-typing)
      y sólo se pueblan vía `stream_simple(reasoning=...)`, que subclasa `StreamOptions`
      y setea `thinking_enabled`/`effort`/`thinking_budget_tokens` por atributo
      (anthropic.py:751-792). Por eso el borrador que los ponía como campos de `complete`
      con destino `StreamOptions` era incorrecto: son **traducidos por el bridge**, no
      passthrough. Se declaran aquí pero **NO** los ejercita el turno texto-solo de A2.2
      (thinking = fuera de "texto-solo"); su cableado real vive en A2.3+/battery.
    - `system_override`/`system_sections` → `Context.system_prompt` (el bridge compone;
      bajo OAuth el provider antepone el system CC fijo, anthropic.py:282-285).
    """

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model_id: str,
        stop: AbortSignal,
        system_override: str | None = None,
        system_sections: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, str] | None = None,  # 【id-opaco】 sólo user_id se reenvía
        effort: str | None = None,  # CORRECCIÓN A2.2: NO StreamOptions; bridge-traducido (stream_simple). No ejercitado texto-solo.
    ) -> AsyncIterator[Event]:
        # Firma NO-async a propósito: llamar a un async-generator DEVUELVE un
        # AsyncIterator sin awaitar; declararlo `async def` lo tiparía como
        # Coroutine[..., AsyncIterator]. Los stubs/bridges lo implementan con `async def`+`yield`.
        ...

    def supports_native_tool_search(self) -> bool:  # 16·A8
        ...


# --- S11 · UserInputProcessor (T2-COSTURA) -----------------------------------
@dataclass(frozen=True)
class ProcessedInput:
    """Resultado del preproceso de entrada. `short_circuit=True` corta el turno sin
    ir al modelo (un slash-command resuelto localmente — battery `commands`, A3·12)."""

    prompt: str
    short_circuit: bool = False
    result_text: str | None = None  # si short-circuita, el texto a devolver ya resuelto


@runtime_checkable
class UserInputProcessor(Protocol):
    """SEAMS §S11. `existe-sin-poblar` en la mímica (exportado, ningún consumidor lo
    invoca — 01·GAP-01). Aquí el loop SÍ lo invoca pre-turno; el stub es passthrough."""

    async def process(self, prompt: str, ctx: StubToolContext) -> ProcessedInput: ...


# --- S16 · ToolProtocol (T1-CONTRATO + costura) — CABLEADO+EJERCITADO en A2.3 ------
@runtime_checkable
class ToolProtocol(Protocol):
    """SEAMS §S16. A2.1 sólo DECLARÓ el contrato; **A2.3 lo cablea y lo EJERCITA** con
    dispatch real (`tools.ToolDispatcher`) + 1 tool nativa (`tools.AddTool`) invocada por
    el modelo en un turno real (L09: ejercitada, no sólo declarada).

    Los 4 miembros de aquí SON los ejercitados por el round-trip A2.3
    (name/input_schema/description/execute). Los miembros de **comportamiento**
    (is_concurrency_safe 09·A3 · check_permissions 09·A6-A8 →S17 · validate_input 09·A9 ·
    output_schema 09·A15) **NO se añaden aquí**: sin consumidor que los ejercite serían
    superficie muerta (L09 inverso). Su hogar es A3 (06·hooks / permisos); se crecerán
    cuando exista quien los invoque, no antes."""

    name: str
    input_schema: dict[str, object]

    def description(self, input: dict[str, object] | None = None) -> str: ...

    async def execute(self, input: dict[str, object], ctx: StubToolContext) -> ToolResult: ...


# --- contexto de ejecución (mínimo; crece en A2.3+) --------------------------
@dataclass
class StubToolContext:
    """`ToolUseContext` reducido a lo que A2.1 necesita: ids opacos + task. Crece con
    exec_env/storage/permission/hooks en los ciclos siguientes.

    A2.5: portador de la costura S18 (`runner`) y S21 (`notifier`). El runtime las
    threadea al ctx del turno (deps-DI S27); el `AgentTool` lee `ctx.runner` para spawnear
    un subagente. `runner is None` ⇒ ningún subagente corre (reproduce el crítico de la
    mímica 05·E24: `get_runner()` lanzaba en todo spawn) — pero AQUÍ el factory lo puebla."""

    task: RuntimeTask
    extras: Mapping[str, object] = field(default_factory=dict)
    runner: SubagentRunnerProtocol | None = None  # S18 — poblado por el factory (A2.5)
    notifier: NotificationSink | None = None  # S21 — canal <task-notification>


# --- S9 · CompactionMotor (BATTERY seam) — el loop lo invoca en el trigger LR1 ---
@dataclass(frozen=True)
class CompactBoundary:
    """Resultado de compactar: el historial nuevo + cuántos mensajes se fundieron
    (evidencia de que el trigger disparó). SEAMS §S9: el MOTOR (battery) produce esto;
    el loop (base-mecanismo LR1) sólo lo consume y emite `CompactBoundaryEvent`."""

    messages: list[Message]
    collapsed: int
    reason: str = "overflow"


@runtime_checkable
class CompactionMotor(Protocol):
    """SEAMS §S9 — el **motor** de compactación (la battery). El loop invoca el trigger
    (`should_compact`) en la frontera de vuelta (canónico `agent_loop.py:189`, LR1 =
    base-mecanismo) y, si dispara, `compact`. La firma-provider `collect_compaction_context`
    (contribuir contexto a preservar) queda DECLARADA en SEAMS pero NO se ejercita aquí
    (sin consumidor sería superficie muerta — L09); su hogar es la battery `compaction` de
    Fase C. A2.4 valida sólo la COMPOSICIÓN: el base declara este Protocol y dispara el
    trigger; la battery concreta se inyecta por fuera (S27 deps-DI) y el base NO la importa."""

    def should_compact(self, messages: list[Message], usage: Usage) -> bool: ...

    def compact(self, messages: list[Message]) -> CompactBoundary: ...


# --- S10 · RetryPolicy (BATTERY seam) — DECLARADA, no ejercitada en A2.4 -------
@runtime_checkable
class RetryPolicy(Protocol):
    """SEAMS §S10 — battery `resilience` (backoff+jitter+retry-after; 529→fallback;
    streaming→non-streaming). Se DECLARA aquí para fijar que es EL MISMO patrón de
    composición que S9 (seam base + trigger en el loop + battery inyectada por fuera),
    pero A2.4 NO la ejercita: "componer **1** battery trivial" (PLAN §4) = compaction.
    La battery `resilience` y su cableado (loop envuelve `complete()`, LR2) → Fase C.
    Declarada-no-cableada a propósito (L09): que exista el Protocol NO la da por validada."""

    async def with_retry(
        self,
        call: Callable[[], AsyncIterator[Event]],
        *,
        fallback_model: str | None,
    ) -> AsyncIterator[Event]: ...


# --- S20 · SessionRepo (T3-INTEGRADOR / costura) — 【NIDO DEL HILO DE IDENTIDAD】 ---
# `SessionId` es un token OPACO: el base lo transporta pero NUNCA lo interpreta ni deriva
# de él userId/tenant. El integrador lo atribuye vía su repo (metadata FUERA del base).
SessionId = str


@runtime_checkable
class SessionRepo(Protocol):
    """SEAMS §S20. El integrador REALIZA este repo; el base sólo obtiene un `SessionId`
    OPACO y lee `session_id` del `RuntimeTask` sin interpretarlo. `create` recibe la
    metadata RICA del integrador (owner/tenant/…) y devuelve un id opaco; el base jamás
    ve esa metadata. `list(query)` deja al integrador SCOPEAR por SU metadata (la
    identidad vive en el repo, no en el runtime). A2.4: un turno corre pasando sólo el
    `SessionId` opaco — **sin userId** en el camino del loop/modelo."""

    def create(self, metadata: Mapping[str, object]) -> SessionId: ...

    def get_metadata(self, session_id: SessionId) -> Mapping[str, object] | None: ...

    def list(self, query: Mapping[str, object]) -> list[SessionId]: ...


# --- S4 · AgentRuntime façade (T2-COSTURA) -----------------------------------
@runtime_checkable
class AgentRuntime(Protocol):
    """SEAMS §S4. El base envía `LocalAgentRuntime` default; el integrador complejo
    puede implementar la suya. A2.1 realiza `stream`; dispatch/status/cancel/result
    se completan en A2.5 (subagentes)."""

    def stream(self, task: RuntimeTask) -> AsyncIterator[Event]: ...

    async def dispatch(self, task: RuntimeTask) -> str: ...

    def status(self, task_id: str) -> TaskStatus: ...

    def result(self, task_id: str) -> ResultEvent | None: ...


# --- S18 · SubagentRunnerProtocol (T2-COSTURA) — 【CRÍTICO: sin él ningún subagente corre】 ---
@dataclass(frozen=True)
class SubagentSpec:
    """El `ForkContext` del canónico REDUCIDO a lo que A2.5 ejercita: qué correr y bajo qué
    identidad OPACA. El adaptador S18 lo traduce a `RuntimeTask` (SEAMS §S18 borrador). Los
    ids que porta son opacos: el runner los PROPAGA sin interpretarlos (el hijo hereda el
    scope del padre vía `parent_session_id`, atribuido por el repo del integrador, S20)."""

    prompt: str
    subagent_type: str | None = None
    model_override: str | None = None
    parent_session_id: str | None = None  # id opaco heredado; nunca userId interpretado


@runtime_checkable
class SubagentRunnerProtocol(Protocol):
    """SEAMS §S18 — LA costura crítica de la espina de ejecución. En la mímica
    (05·E24/FIND-EXEC1) `get_runner()` lanzaba `RuntimeError` en TODO spawn porque
    `set_runner` sólo se llamaba en tests: el ensamblador (factory) nunca poblaba la costura
    ⇒ ningún subagente corría en producción (L09: existe la pieza, el puente no la cablea = ❌).

    A2.5 CORRIGE el patrón: en vez del singleton global `set_runner/get_runner` (doble-camino
    con S19, DEUDA-B), el runner se inyecta por deps-DI (S27) al runtime, que lo threadea al
    `ctx` del turno; el `AgentTool` lee `ctx.runner`. El factory `create_runtime` es el ÚNICO
    punto que lo puebla (18·C1) — validado por el turno end-to-end: si el factory NO lo cablea,
    `ctx.runner is None` ⇒ el spawn falla (mismo síntoma que la mímica, ahora imposible de
    olvidar porque el turno real lo ejercita).

    `run` devuelve el texto final del subagente (camino SÍNCRONO, A2.5) o `None` en el camino
    background (fire-and-forget → resultado se recoge por S4 `result()`; NO ejercitado en A2.5,
    su hogar es S22 force-async + el daemon del integrador complejo — Fase F)."""

    async def run(self, spec: SubagentSpec, *, background: bool = False) -> str | None: ...


# --- S21 · NotificationSink (T2-COSTURA) — canal <task-notification> (drain/process) --------
@dataclass(frozen=True)
class Notification:
    """Shape XML `<task-notification>` REDUCIDO (05·E19 → 07): lo mínimo para validar el
    par put/drain. El shape rico (tool-use-id/output-file/worktree/`<usage>`) crece en 07."""

    task_id: str  # id opaco del subagente que la emitió
    status: str  # "completed" | "failed" | "running"
    summary: str
    result: str


@runtime_checkable
class NotificationSink(Protocol):
    """SEAMS §S21 — en la mímica `existe-put-sin-drain` (05·E5/LAT-EXEC2: el runtime ESCRIBE
    `put_notification` pero nada auto-drena; delegado al integrador, 🔀 no bug). A2.5 valida
    AMBAS puntas: el runner (child) hace `put`; el integrador `drain` al inicio/fin del turno
    y presenta al padre/usuario. `scope` deja al integrador filtrar por SU metadata (id-opaco,
    patrón repo S20). El drain vacía lo drenado (una notificación se presenta una vez)."""

    def put(self, note: Notification) -> None: ...

    def drain(self, scope: Mapping[str, object] | None = None) -> list[Notification]: ...
