"""Contratos T1 del turno — **paquete invariante**.

Regla que lo define, y su prueba: este paquete **no importa nada del base**. Si
lo importara, reimplementar los contratos obligaría a arrastrar el runtime
entero y el ecosistema se forkearía. La invariancia no se declara: la comprueba
`tests/test_contracts_invariant.py` cargando el paquete con el resto de
`agentic_runtime` **bloqueado en el path**.
"""
from .abort import AbortController, AbortReason, AbortSignal
from .agents import (
    INHERIT,
    AgentDefinition,
    AgentDefinitionResolver,
    resolve_subagent_model,
)
from .compaction import CompactionProvider, collect_compaction_context
from .errors import RuntimeConfigError, RuntimeIdentityError
from .events import (
    DoneEvent,
    ErrorEvent,
    Event,
    EventBusProtocol,
    EventHandler,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
    Usage,
)
from .identity import (
    RuntimeSessionProtocol,
    Scope,
    SessionId,
    SessionInfo,
    SessionRepo,
)
from .permissions import PermissionContext, PermissionMode
from .runtime import AgentRuntime, RuntimeTask
from .storage import PathPresentation, StorageContract
from .tasks import TaskStatus
from .tools import ToolCategory, ToolContext, ToolProtocol, ToolResult
from .user_input import NoopUserInputProcessor, UserInputProcessor
from .voice import AudioInput

__all__ = [
    "INHERIT",
    "AbortController",
    "AbortReason",
    "AbortSignal",
    "AgentDefinition",
    "AgentDefinitionResolver",
    "AgentRuntime",
    "AudioInput",
    "CompactionProvider",
    "DoneEvent",
    "ErrorEvent",
    "Event",
    "EventBusProtocol",
    "EventHandler",
    "NoopUserInputProcessor",
    "PathPresentation",
    "PermissionContext",
    "PermissionMode",
    "RuntimeConfigError",
    "RuntimeIdentityError",
    "RuntimeSessionProtocol",
    "RuntimeTask",
    "Scope",
    "SessionId",
    "SessionInfo",
    "SessionRepo",
    "StorageContract",
    "TaskStatus",
    "TokenEvent",
    "ToolCallEvent",
    "ToolCategory",
    "ToolContext",
    "ToolProtocol",
    "ToolResult",
    "ToolResultEvent",
    "Usage",
    "UserInputProcessor",
    "collect_compaction_context",
    "resolve_subagent_model",
]
