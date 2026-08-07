"""`FIND-TOOL-ENABLED-1` — al pool le faltaba el predicado de PUBLICACIÓN.

A tiene dos filtros en el ensamblado del pool (`tools.ts:311-326`): deny —lo que el
usuario prohibió— y `isEnabled()` —lo que el host no puede sostener—. B sólo tenía el
primero (`tools/pool.py:assemble_tool_pool`), y `isEnabled` no figuraba siquiera en la
lista de miembros diferidos del contrato (`contracts/tools.py:3-6`): era omisión no
declarada.

La consecuencia se midió en el gate E2g, tres veces, con dos tools distintas:

  · `GATE_E2G_SEED=1780649320` → `elegidas=['AskUserQuestion','glob']`, `respuesta=''`.
  · `GATE_E2G_SEED=29525785`   → el modelo entró en plan mode y se declaró bloqueado.
  · `GATE_E2G_SEED=1561952726` → ídem.

Las tres son la MISMA forma: una tool que cede el turno esperando a un humano,
publicada en un host que no tiene humano. A guarda exactamente contra esto y escribe la
razón en el canónico (`EnterPlanModeTool.ts:56-67`): *«Disable entry too so plan mode
isn't a trap the model can enter but never leave»*.

Los tests aseveran CONDUCTA (`H-L4`): qué sale del pool y qué puede ejecutarse, no si
existe un atributo. Un test sobre la firma de `is_enabled` acreditaría en falso en
cuanto alguien la añadiera devolviendo siempre `True`.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.contracts.tools import ToolCategory, ToolProtocol, tool_is_enabled
from agentic_runtime.factory import (
    CapabilitiesConfig,
    RuntimeConfig,
    StorageConfig,
    ToolsConfig,
    create_runtime,
)
from agentic_runtime.tools.native.ask_user import ASK_USER_QUESTION_TOOL_NAME
from agentic_runtime.tools.native.plan_mode import (
    ENTER_PLAN_MODE_TOOL_NAME,
    EXIT_PLAN_MODE_TOOL_NAME,
)
from agentic_runtime.tools.pool import ToolPool, assemble_tool_pool

_PUERTA_UNICA = {
    ASK_USER_QUESTION_TOOL_NAME,
    ENTER_PLAN_MODE_TOOL_NAME,
    EXIT_PLAN_MODE_TOOL_NAME,
}


class _Tool:
    """Tool mínima con enablement declarable. No hereda: el contrato es estructural."""

    description = "x"
    input_schema: ClassVar[dict] = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 1.0

    def __init__(self, name: str, enabled: bool | None = None) -> None:
        self.name = name
        if enabled is not None:
            self.is_enabled = lambda: enabled  # type: ignore[method-assign]

    async def execute(self, input: dict, ctx: object):  # pragma: no cover - no se llama
        raise AssertionError("no debería ejecutarse en estos tests")


# ──────────────────────────────────────────────────────────────────────────────
# 1 · El default: quien no se pronuncia, se publica (`TOOL_DEFAULTS.isEnabled`)
# ──────────────────────────────────────────────────────────────────────────────

def test_a_tool_that_says_nothing_is_published():
    """Fail-open, espejo de `Tool.ts:758`. Sin esto el filtro apagaría el runtime entero."""
    assert tool_is_enabled(_Tool("muda")) is True
    pool = assemble_tool_pool([_Tool("muda")], [], PermissionContext())
    assert [t.name for t in pool] == ["muda"]


def test_a_boolean_attribute_counts_as_much_as_a_method():
    """El contrato es la CONDUCTA, no la firma (`H-L4`) — y esto no era retórica vacía.

    Lo destapó una inyección que salió VERDE (`INY-76`): estrechar `tool_is_enabled` a
    «sólo callable» no ponía nada en rojo, porque el fake de arriba adjunta siempre una
    lambda. La docstring del contrato prometía aceptar ambas formas y nadie lo medía.

    Importa porque una tool de terceros que escriba `is_enabled = False` como atributo de
    clase —la grafía más natural en Python— quedaría publicada en silencio.
    """
    class _Atributo:
        name = "atributo"
        description = "x"
        input_schema: ClassVar[dict] = {"type": "object", "properties": {}}
        category = ToolCategory.UTILITY
        requires_permission = False
        safe_for_background = True
        timeout_seconds = 1.0
        is_enabled = False

        async def execute(self, input: dict, ctx: object):  # pragma: no cover
            raise AssertionError("no debería ejecutarse")

    assert tool_is_enabled(_Atributo()) is False
    assert assemble_tool_pool([_Atributo()], [], PermissionContext()) == []

    # Y no a costa del contrato: `is_enabled` NO se declara en `ToolProtocol` justo para
    # que ninguna tool de terceros deje de serlo por no implementarlo (`Tool.ts:708,758`).
    assert isinstance(_Tool("muda"), ToolProtocol)
    assert isinstance(_Atributo(), ToolProtocol)


def test_disabled_tool_is_neither_announced_nor_resolvable():
    """El filtro es de PUBLICACIÓN: en A sale del mismo pool del que se resuelve por nombre."""
    pool = ToolPool(native_tools=[_Tool("viva", True), _Tool("muerta", False)])

    assert [t.name for t in pool.assemble()] == ["viva"]
    assert pool.find("viva") is not None
    assert pool.find("muerta") is None, (
        "`muerta` está deshabilitada pero sigue siendo EJECUTABLE por nombre: el "
        "filtro se quedó en el anuncio. En A no hay dos pools (`tools.ts:325-326`)."
    )


def test_enablement_is_applied_after_dedup_so_a_capability_cannot_impersonate_a_native():
    """El ORDEN importa (`tools.ts:311-326`), y es lo que un refactor rompería en silencio."""
    pool = assemble_tool_pool(
        [_Tool("bash", False)],          # nativa apagada
        [_Tool("bash", True)],           # capability de terceros con el MISMO nombre
        PermissionContext(),
    )
    assert [t.name for t in pool] == [], (
        "una capability ocupó el hueco de una nativa apagada: el enabled se aplicó "
        "ANTES de la deduplicación y el nombre quedó libre para ser suplantado"
    )


def test_enablement_is_not_permissions():
    """Deny y enabled son ejes distintos: ninguno debe absorber al otro."""
    ctx = PermissionContext(always_deny=["prohibida"])
    pool = assemble_tool_pool(
        [_Tool("prohibida", True), _Tool("apagada", False), _Tool("viva", True)],
        [],
        ctx,
    )
    assert [t.name for t in pool] == ["viva"]


# ──────────────────────────────────────────────────────────────────────────────
# 2 · El caso medido: las tools de puerta única en un host sin humano
# ──────────────────────────────────────────────────────────────────────────────

def _runtime(tmp_path: Path, *, interactive: bool):
    return create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        tools=ToolsConfig(interactive=interactive),
        capabilities=CapabilitiesConfig(),
        model_caller=object(),
    ))


def test_the_default_host_is_headless(tmp_path: Path):
    """Sin `interactive`: el host que NO se pronuncia no tiene humano.

    Segunda inyección verde (`INY-79`): invertir el default de `ToolsConfig.interactive`
    no rompía nada, porque todos los tests de abajo lo pasan explícito. El default es
    precisamente la costura que decide el caso real —un integrador que no configuró
    nada—, así que es el que hay que aseverar por separado.

    Mismo criterio que los handlers OAuth de `CapabilitiesConfig`: el runtime headless no
    abre un navegador, y no lo hace por omisión, no por configuración.
    """
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        tools=ToolsConfig(),
        capabilities=CapabilitiesConfig(),
        model_caller=object(),
    ))
    assert _publicadas(runtime) & _PUERTA_UNICA == set(), (
        "el runtime por defecto publica tools de puerta única: un integrador que no "
        "declara humano se lleva el turno vacío sin haber tocado nada"
    )


def _publicadas(runtime) -> set[str]:
    """Lo que el modelo VE y puede ejecutar: el pool ensamblado, no el registry.

    El registry guarda todo lo construido; el filtro de publicación vive en la
    convergencia native+capability, que es lo que `manager.build_tool_pool` arma y el
    loop consume. Aseverar sobre el registry mediría el sitio equivocado y daría verde
    con el defecto puesto.
    """
    pool = ToolPool(native_tools=runtime._tool_registry.all_tools())
    return {t.name for t in pool.assemble()}


@pytest.mark.parametrize("name", sorted(_PUERTA_UNICA))
def test_single_door_tools_are_absent_from_a_headless_runtime(tmp_path: Path, name: str):
    """El default es headless: el modelo no puede elegir lo que le costaría el turno."""
    runtime = _runtime(tmp_path, interactive=False)
    publicadas = _publicadas(runtime)

    assert name not in publicadas, (
        f"`{name}` se publica en un runtime headless. Cede el turno esperando a un "
        f"humano que no existe ⇒ turno vacío garantizado (medido en el E2g)."
    )


@pytest.mark.parametrize("name", sorted(_PUERTA_UNICA))
def test_single_door_tools_come_back_when_the_host_declares_a_human(
    tmp_path: Path, name: str
):
    """Control positivo: el apagado no puede convertirse en «estas tools ya no existen»."""
    runtime = _runtime(tmp_path, interactive=True)
    publicadas = _publicadas(runtime)

    assert name in publicadas, (
        f"`{name}` no vuelve con `ToolsConfig.interactive=True`: el apagado dejó de "
        f"ser condicional y se comió la capability"
    )


def test_the_rest_of_the_pool_is_untouched_by_the_headless_default(tmp_path: Path):
    """La guarda es quirúrgica: sólo caen las de puerta única, no las demás."""
    headless = _publicadas(_runtime(tmp_path, interactive=False))
    con_humano = _publicadas(_runtime(tmp_path, interactive=True))

    assert con_humano - headless == _PUERTA_UNICA, (
        f"la diferencia entre host con y sin humano no es exactamente el conjunto de "
        f"puerta única: {con_humano - headless}"
    )
    assert {"glob", "grep", "read_file", "write_file", "bash"} <= headless
