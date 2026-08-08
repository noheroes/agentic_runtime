"""`FIND-PLAN-FILE-1` — el plan-file, de punta a punta.

Tres cortes independientes que la 19ª ventana encontró leyendo el camino entero, y que hasta
hoy ningún test veía porque cada pieza estaba probada **aislada de las otras dos**:

1. `ctx.storage` no se poblaba nunca en producción (`runtime.py:426-439` threadea `fs`,
   `exec_env`, `presentation`, `runner`, `task_registry` — `storage` no estaba). ⇒ `get_plan`
   devolvía `None` siempre y `ExitPlanMode` erraba invariablemente.
2. No había campo en `RuntimeConfig` por el que inyectar un `StorageContract`; el único hueco
   era el parámetro `storage=` de `ConfinedFilesystem`, que no llega al ctx.
3. `provider.py:40-42` ordena escribir el plan en `/plans/plan.md`, y ese token cae FUERA del
   `write_roots` del workspace ⇒ `PathOutsideWorkspace`. El modelo no podía obedecer la
   instrucción que el propio runtime le da.

El canónico dicta la exención (`D-08`): `isSessionPlanFile` (`filesystem.ts:245`) se consume en
la capa de PERMISOS, dos veces — `checkEditableInternalPath` (`:1488`, *«Plan files for current
session are allowed for writing»*) y su gemelo de lectura (`:1645`). Es exención del chequeo de
workspace, no de un «candado de plan mode».
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from agentic_runtime.capabilities.plan.plan_file import get_plan, get_plan_file_path
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.identity import Scope
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, ToolCallEvent
from agentic_runtime.factory import (
    RuntimeConfig,
    StorageConfig,
    ToolsConfig,
    create_runtime,
)
from agentic_runtime.tools import ToolCategory, ToolResult
from agentic_runtime.tools.fs_env import ConfinedFilesystem, PathOutsideWorkspace
from agentic_runtime.tools.native.read_file import ReadFileTool
from agentic_runtime.tools.native.write_file import WriteFileTool


class _WorkspaceStorage:
    """`StorageContract` mínimo: mapea la familia `/plans/<n>.md` a un dir de estado.

    Es exactamente la forma que el integrador tiene que implementar (`agentic_code` la tiene
    en `storage.py`); aquí vive para que el test mida el CONTRATO, no una implementación.
    """

    def __init__(self, plans_dir: Path, workspace: Path) -> None:
        self.plans_dir = plans_dir
        self.workspace = workspace

    def real_path(self, token: str) -> Path:
        if token.startswith("/plans/"):
            return self.plans_dir / token[len("/plans/") :]
        if token.startswith("/"):
            return Path(token)
        return self.workspace / token

    async def ensure_local(self, token: str) -> Path:
        return self.real_path(token)

    async def commit(self, token: str, content: bytes, mime: str | None = None) -> str:
        path = self.real_path(token)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return token

    async def teardown(self) -> None:
        return None


def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev

            return _gen()

    return StubCaller()


class _StorageProbe:
    """Registra lo que la tool VE en su ctx — no lo que el ensamblador cree haber puesto."""

    name = "probe"
    description = "probe"
    input_schema: ClassVar[dict] = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    def __init__(self) -> None:
        self.seen: list[object] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.seen.append(ctx.storage)
        return ToolResult(tool_name=self.name, output="ok")


def _ctx_with(storage: _WorkspaceStorage, workspace: Path) -> ToolUseContext:
    ctx = ToolUseContext(session_id="S1")
    ctx.storage = storage
    ctx.fs = ConfinedFilesystem(
        roots=[workspace], write_roots=[workspace], storage=storage
    )
    return ctx


# ── Corte 1 + 2: el cable llega al ctx REAL que produce el runtime ──────────────────────


@pytest.mark.asyncio
async def test_storage_contract_reaches_the_root_context(tmp_path):
    """El `StorageContract` inyectado por el integrador llega a `ctx.storage`.

    Se mide en el ctx que ve la TOOL, no en el que ve el `root_context_modifier`: el modifier
    corre antes de que el turno arranque y podría taparlo. Sin este cable, todo
    `capabilities/plan/` es código muerto en producción.
    """
    contract = _WorkspaceStorage(tmp_path / "plans", tmp_path / "ws")
    probe = _StorageProbe()
    caller = _make_caller(
        ToolCallEvent(tool_name="probe", tool_input={}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    rt = create_runtime(
        config=RuntimeConfig(
            storage=StorageConfig(backend="filesystem", root=tmp_path / "rt"),
            storage_contract=contract,
            model_caller=caller,
            tools=ToolsConfig(extras=[probe]),
        )
    )

    async for _ in rt.stream(
        RuntimeTask(
            prompt="usa probe",
            description="t",
            session_id="S-plan",
            scope=Scope("SC-plan"),
        )
    ):
        pass

    assert probe.seen == [contract]


def test_runtime_config_defaults_storage_contract_to_none():
    """El campo es OPCIONAL: un runtime sin integrador de storage sigue componiéndose."""
    assert RuntimeConfig(model_caller=None).storage_contract is None


# ── Corte 3: el confinamiento y la exención del plan-file ───────────────────────────────


@pytest.mark.asyncio
async def test_write_file_can_write_the_plan_file_token(tmp_path):
    """El token que `provider.py:40-42` le ORDENA al modelo tiene que ser escribible.

    Homólogo de `checkEditableInternalPath` (`filesystem.ts:1488`): el plan-file de la sesión
    está exento del chequeo de workspace. Sin la exención, la única instrucción operativa de
    plan mode es imposible de cumplir.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()
    contract = _WorkspaceStorage(tmp_path / "plans", workspace)
    ctx = _ctx_with(contract, workspace)

    result = await WriteFileTool().execute(
        {"path": "/plans/plan.md", "content": "# Plan\n\n1. hacer algo\n"}, ctx
    )

    assert not result.is_error, result.output
    assert (tmp_path / "plans" / "plan.md").read_text() == "# Plan\n\n1. hacer algo\n"


@pytest.mark.asyncio
async def test_read_file_can_read_the_plan_file_token(tmp_path):
    """La exención es simétrica: A la aplica también en lectura (`filesystem.ts:1645`)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "plan.md").write_text("# Plan\n")
    ctx = _ctx_with(_WorkspaceStorage(plans, workspace), workspace)

    result = await ReadFileTool().execute({"path": "/plans/plan.md"}, ctx)

    assert not result.is_error, result.output
    assert "# Plan" in result.output


def test_exemption_does_not_open_the_workspace(tmp_path):
    """Control negativo — sin él la exención sería un agujero, no una exención.

    Un token FUERA del workspace que no es plan-file sigue rebotando, y también rebota lo que
    sólo se le PARECE: `/plans/notas.txt` (sufijo malo), `/plansX/plan.md` (prefijo malo) y
    —el que importa— `/plans/../../etc/passwd.md`, que SATISFACE el predicado de plan-file
    (prefijo y sufijo correctos) y saldría por la puerta recién abierta si no hubiera guard
    de traversal. A se defiende del mismo bypass y lo dice: *«SECURITY: Normalize to prevent
    path traversal bypasses via .. segments»* (`filesystem.ts:249`).
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()
    fs = ConfinedFilesystem(
        roots=[workspace],
        write_roots=[workspace],
        storage=_WorkspaceStorage(tmp_path / "plans", workspace),
    )

    for token in (
        "/etc/passwd",
        "/plans/notas.txt",
        "/plansX/plan.md",
        "/plans/../../etc/passwd.md",
    ):
        with pytest.raises(PathOutsideWorkspace):
            fs.resolve(token, for_write=True)


# ── El ciclo completo: es el único que caza los tres cortes a la vez ────────────────────


@pytest.mark.asyncio
async def test_plan_file_round_trip_write_then_get_plan(tmp_path):
    """El modelo escribe el plan donde el reminder le dice; `ExitPlanMode` lo lee de ahí.

    Cada pieza suelta ya tenía test verde y el ciclo estaba roto igual: éste es el que mide la
    propiedad que importa, que es que el token de ESCRITURA y el de LECTURA son el mismo.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()
    ctx = _ctx_with(_WorkspaceStorage(tmp_path / "plans", workspace), workspace)

    token = get_plan_file_path(ctx)
    write = await WriteFileTool().execute({"path": token, "content": "## Plan\npasos\n"}, ctx)
    assert not write.is_error, write.output

    assert await get_plan(ctx) == "## Plan\npasos\n"


@pytest.mark.asyncio
async def test_get_plan_survives_a_storage_without_the_contract(tmp_path):
    """Un `storage` que no implementa `StorageContract` no puede reventar la tool.

    El `storage` NATIVO del runtime (`FilesystemStorage`) implementa `StorageProtocol`
    (`upload/download/...`), que no tiene `ensure_local`. `get_plan` sólo atrapaba `OSError`,
    así que el `AttributeError` se escapaba hasta `ExitPlanMode.execute` y la tool reventaba
    en vez de errar. Erra: no revienta.
    """

    class _NotAContract:
        async def upload(self, key, data, content_type="application/octet-stream"):
            return key

    ctx = ToolUseContext(session_id="S1")
    ctx.storage = _NotAContract()

    assert await get_plan(ctx) is None
