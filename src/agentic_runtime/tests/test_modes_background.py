"""B3 — modos: is_backgrounded MUTABLE en TaskRecord + filtro safe_for_background por KIND.

Dos ejes ortogonales:
- `is_backgrounded` (relativo al observador) se flipea vía el registry; NO toca el toolset.
- el toolset se filtra por KIND: un subagente (unattended) solo ve tools safe_for_background;
  el main las ve todas. Promover a background NO re-filtra (es por kind, no por el flag).
"""
import asyncio


from agentic_runtime.capabilities import CapabilitiesResolver
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry
from agentic_runtime.execution.tasks.status import TaskStatus
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult


# --- stub tools: una interactiva (no background) y una segura ---------------

class _InteractiveTool:
    name = "ask_user"
    description = "needs a human"
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="ok")


class _SafeTool:
    name = "read_file"
    description = "safe to run unattended"
    input_schema: dict = {}
    category = ToolCategory.FILE
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="ok")


def _resolver() -> CapabilitiesResolver:
    reg = ToolRegistry()
    reg.register(_InteractiveTool())
    reg.register(_SafeTool())
    return CapabilitiesResolver(tool_registry=reg)


def _names(ctx) -> set[str]:
    resolved = asyncio.run(_resolver().resolve(ctx))
    return {s["name"] for s in resolved.tool_schemas}


# --- filtro por kind --------------------------------------------------------

def test_main_sees_all_tools():
    names = _names(ToolUseContext(session_id="s1", is_subagent=False))
    assert names == {"ask_user", "read_file"}


def test_subagent_filtered_to_safe_for_background():
    names = _names(ToolUseContext(session_id="s1", is_subagent=True))
    assert names == {"read_file"}  # ask_user (no safe_for_background) excluida


# --- is_backgrounded mutable, ortogonal al toolset --------------------------

def test_is_backgrounded_default_false_and_mutable():
    reg = InMemoryTaskRegistry()
    rec = reg.register(description="t")
    assert rec.is_backgrounded is False
    reg.set_backgrounded(rec.task_id, True)
    assert reg.get(rec.task_id).is_backgrounded is True
    reg.set_backgrounded(rec.task_id, False)
    assert reg.get(rec.task_id).is_backgrounded is False


def test_backgrounding_does_not_refilter_toolset():
    """El flag mutable no participa en la resolución del toolset (es por kind)."""
    # main backgrounded sigue viendo todas las tools (kind no cambió)
    names_main = _names(ToolUseContext(session_id="s1", is_subagent=False))
    assert "ask_user" in names_main
    # set_backgrounded vive en el registry y no toca ctx.is_subagent ni la resolución
    reg = InMemoryTaskRegistry()
    rec = reg.register(description="t")
    reg.set_backgrounded(rec.task_id, True)
    assert reg.get(rec.task_id).status == TaskStatus.PENDING  # solo flip, sin efectos
