"""Tests para runtime/factory.py — create_runtime() meta-factory."""
import pytest

from agentic_runtime.factory import RuntimeConfig, StorageConfig, create_runtime
from agentic_runtime.execution.local import LocalAgentRuntime
from agentic_runtime.storage.filesystem import FilesystemStorage
from agentic_runtime.storage.protocol import StorageProtocol


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def test_create_runtime_local_mode_returns_local_runtime(tmp_path):
    runtime = create_runtime(execution_mode="local", config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path)
    ))
    assert isinstance(runtime, LocalAgentRuntime)


def test_create_runtime_defaults_filesystem_storage(tmp_path):
    config = RuntimeConfig(storage=StorageConfig(backend="filesystem", root=tmp_path))
    runtime = create_runtime(config=config)
    assert isinstance(runtime._storage, FilesystemStorage)


def test_runtime_config_defaults_are_valid():
    # RuntimeConfig() sin args debe instanciar sin error
    config = RuntimeConfig()
    assert config is not None
    assert config.storage is not None


# ---------------------------------------------------------------------------
# Custom injection
# ---------------------------------------------------------------------------

def test_create_runtime_injects_custom_storage(tmp_path):
    config = RuntimeConfig(storage=StorageConfig(backend="filesystem", root=tmp_path))
    runtime = create_runtime(config=config)

    assert isinstance(runtime._storage, StorageProtocol)


def test_create_runtime_extra_tools_registered(tmp_path):
    from agentic_runtime.tools.protocol import ToolCategory, ToolResult

    class MyTool:
        name = "my_custom_tool"
        description = "Custom"
        input_schema: dict = {}
        category = ToolCategory.UTILITY
        requires_permission = False
        safe_for_background = True
        timeout_seconds = 5.0

        async def execute(self, input, ctx):
            return ToolResult(tool_name=self.name, output="ok")

    from agentic_runtime.factory import ToolsConfig
    config = RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        tools=ToolsConfig(extras=[MyTool()]),
    )
    runtime = create_runtime(config=config)
    # El registry nativo es input al ensamblado del pool (ya no es lookup de ejecución).
    assert runtime._tool_registry.resolve("my_custom_tool") is not None


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_create_runtime_remote_raises_not_implemented(tmp_path):
    with pytest.raises(NotImplementedError):
        create_runtime(
            execution_mode="remote",
            config=RuntimeConfig(storage=StorageConfig(backend="filesystem", root=tmp_path))
        )


# ---------------------------------------------------------------------------
# RuntimeFactory extension primitive
# ---------------------------------------------------------------------------

def test_runtime_factory_register_custom_mode(tmp_path):
    from agentic_runtime.factory import RuntimeFactory

    class MyRuntime:
        def __init__(self, **cfg):
            self.cfg = cfg

    RuntimeFactory.register_execution_mode("my_mode", MyRuntime)
    runtime = create_runtime(
        execution_mode="my_mode",
        config=RuntimeConfig(storage=StorageConfig(backend="filesystem", root=tmp_path))
    )
    assert isinstance(runtime, MyRuntime)


# ---------------------------------------------------------------------------
# End-to-end: create_runtime() ejecuta una task completa sin tocar agent_core
# ---------------------------------------------------------------------------
#
# Caller determinista (no red). El FauxProvider de agentic_models no es usable
# todavía: register_faux_provider() pasa un dict a register_api_provider(), que
# espera un objeto con `.api` — bug del port que corresponde al Track M (M1).
# El cableado de create_runtime() se prueba igual con un caller guionado.

@pytest.mark.asyncio
async def test_create_runtime_runs_task_end_to_end(tmp_path):
    from agentic_runtime.contracts.runtime import RuntimeTask
    from agentic_runtime.events import DoneEvent, TokenEvent
    from agentic_runtime.execution.tasks.status import TaskStatus

    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                yield TokenEvent(content="respuesta final")
                yield DoneEvent(stop_reason="stop")
            return _gen()

    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=StubCaller(),
    ))

    task_id = await runtime.dispatch(RuntimeTask(prompt="hola", description="e2e"))
    rec = runtime._task_registry.get(task_id)
    await rec.asyncio_task

    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert runtime.result(task_id) == "respuesta final"


def test_create_runtime_wires_git_credentials(tmp_path):
    sentinel = object()
    config = RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        git_credentials=sentinel,
    )
    runtime = create_runtime(config=config)
    # el runtime lo asigna a cada ctx (peer de exec_env) para que clone_repository lo vea
    assert runtime._git_credentials is sentinel


def test_git_credentials_default_none(tmp_path):
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path)
    ))
    assert runtime._git_credentials is None
