"""Walking skeleton (Fase A2) — spike que VALIDA las costuras de `SEAMS.md`.

NO es el runtime de producción: es un spike clean-room de la Filosofía B (base
framework + costuras) que ejercita un TURNO real a través de las costuras, para
confirmarlas o corregirlas ANTES de la construcción de Fase B. El `src/agentic_runtime`
mímica NO se toca aquí; Fase B lo re-homa guiado por lo que este spike valide.

Crecimiento del spike (PLAN §4 · SEAMS §5):
- A2.1 (este ciclo): andamiaje — stubs de S4/S5/S16/S11 + caller-stub (S1) + loop mínimo SIN tools. Gate: typechecks.
- A2.2: cablear S1 (`ModelCallerProtocol`) -> `agentic_models`; 1 turno real texto-solo.
- A2.3: S16 + dispatch (S26/pool) + 1 tool nativa.
- A2.4: componer 1 battery (S9/S10) + S20 (`SessionRepo`, turno sin userId).
- A2.5: S18 (`SubagentRunnerProtocol`) + S4 + S21; turno end-to-end; `SKELETON-REPORT.md`.
"""

from skeleton.contracts import (
    CompactBoundaryEvent,
    DoneEvent,
    ErrorEvent,
    Event,
    InitEvent,
    Message,
    ResultEvent,
    RuntimeTask,
    TaskStatus,
    ThinkingEvent,
    TokenEvent,
    ToolCall,
    ToolCallEvent,
    ToolResult,
    ToolResultEvent,
    ToolSchema,
    Usage,
)
from skeleton.bridge import AgenticModelsCaller
from skeleton.events import EventBus, Unsubscribe
from skeleton.factory import create_runtime
from skeleton.loop import AgentLoop
from skeleton.runner import LocalSubagentRunner
from skeleton.runtime import LocalAgentRuntime
from skeleton.seams import (
    AbortSignal,
    AgentRuntime,
    CompactBoundary,
    CompactionMotor,
    ModelCallerProtocol,
    Notification,
    NotificationSink,
    ProcessedInput,
    RetryPolicy,
    SessionId,
    SessionRepo,
    StubToolContext,
    SubagentRunnerProtocol,
    SubagentSpec,
    ToolProtocol,
    UserInputProcessor,
)
from skeleton.stubs import (
    InMemoryNotificationSink,
    InMemorySessionRepo,
    NullAbortSignal,
    PassthroughInputProcessor,
    StubModelCaller,
    StubToolModelCaller,
)
from skeleton.tools import (
    AddTool,
    AgentTool,
    DeferredToolStrategy,
    EagerToolStrategy,
    ToolDispatcher,
    ToolPool,
)

__all__ = [
    "AbortSignal",
    "AddTool",
    "AgentLoop",
    "AgentRuntime",
    "AgentTool",
    "AgenticModelsCaller",
    "CompactBoundary",
    "CompactBoundaryEvent",
    "CompactionMotor",
    "DeferredToolStrategy",
    "DoneEvent",
    "EagerToolStrategy",
    "ErrorEvent",
    "Event",
    "EventBus",
    "InMemoryNotificationSink",
    "InMemorySessionRepo",
    "InitEvent",
    "LocalAgentRuntime",
    "LocalSubagentRunner",
    "Message",
    "ModelCallerProtocol",
    "Notification",
    "NotificationSink",
    "NullAbortSignal",
    "PassthroughInputProcessor",
    "ProcessedInput",
    "ResultEvent",
    "RetryPolicy",
    "RuntimeTask",
    "SessionId",
    "SessionRepo",
    "StubModelCaller",
    "StubToolContext",
    "StubToolModelCaller",
    "SubagentRunnerProtocol",
    "SubagentSpec",
    "TaskStatus",
    "ThinkingEvent",
    "TokenEvent",
    "ToolCall",
    "ToolCallEvent",
    "ToolDispatcher",
    "ToolPool",
    "ToolProtocol",
    "ToolResult",
    "ToolResultEvent",
    "ToolSchema",
    "Unsubscribe",
    "Usage",
    "UserInputProcessor",
    "create_runtime",
]
