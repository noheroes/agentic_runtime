"""Gate de fin de TRAMO 1 — las E2E **reales** `E1..E9` (`SEPARACION/TRAMO-1.md §4`).

Este módulo es el gate entero, no un test suelto: `E1..E9` viven aquí y la regla
dura del tramo es que pasen **a la vez, en una sola corrida**. Se corren con

    uv run pytest src/agentic_runtime/tests/test_tramo1_gate.py -m gate_tramo1 -q

**Un skip NO es un verde.** Las Ei que hablan con el modelo real se saltan si no
hay config Azure, y una corrida con skips **no acredita el gate** — por eso cada
una imprime su acreditación y el conteo se lee como `N passed`, nunca como
`N passed, M skipped`. Esto es `L09` aplicado al propio gate: *el catálogo verde
da falsa confianza*.

Contenido de este módulo: **`E1`**, **`E5`** (acreditan `C2`) y **`E6`** (acredita
`C9`). Las otras seis llegan con sus capacidades.

──────────────────────────────────────────────────────────────────────────────
`E6` · **sin identidad** — el turno corre entero sin que el runtime conozca a
nadie, y **ningún token de identidad llega al seam del modelo**. Acredita `C9`.

Es la prueba de que Filosofía B se cumple, y por eso se escribe de tres piezas
que sólo juntas prueban algo (cada una sola es trivialmente satisfacible):

  1. **positiva y real** — un turno de verdad contra el modelo, con tool real
     despachada, resultado dependiente de su salida. Sin esto, «no llegó
     identidad» sería cierto porque **nada corrió**.
  2. **el probe en el seam** — un decorador de `ModelCallerProtocol` (`S1`)
     cableado por el punto de composición real (`RuntimeConfig.model_caller`),
     que captura **todo** lo que cruza al proveedor y asevera que los centinelas
     de identidad no están. El probe **envuelve** al caller real, no lo
     sustituye: el motor que corre por debajo es el de producción (`L09` —
     verificar el cableado, no la existencia).
  3. **negativa** — sin `session_id` atribuido el runtime **falla en voz alta** y
     no escribe nada: la ausencia de autogen es *load-bearing*, no cosmética.

Los centinelas son valores únicos por corrida (`uuid`) que no aparecen en el
prompt ni en la descripción: si mañana alguien «enriquece» el system prompt o el
historial con el `session_id` o el `scope`, esta prueba se pone roja. Ése es su
trabajo.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.identity import Scope
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.execution.tasks.status import TaskStatus
from agentic_runtime.factory import (
    RuntimeConfig,
    StorageConfig,
    ToolsConfig,
    create_runtime,
)
from agentic_runtime.storage.protocol import StorageKeys
from agentic_runtime.tools import ToolCategory, ToolResult

from ._azure_real import build_caller as _build_caller
from ._azure_real import skip_marker as _needs_azure

pytestmark = pytest.mark.gate_tramo1

#: Grafías del cable de identidad que el runtime **no** debe emitir hacia el
#: proveedor. `AC-39`/`D-11`: el nombre del parámetro es parte de la costura, así
#: que se vigilan las cuatro que el corpus llegó a tener.
_IDENTITY_SPELLINGS = ("user_id", "userId", "owner_id", "ownerId")


# ──────────────────────────────────────────────────────────────────────────────
# El probe del seam del modelo (`S1`) — decorador, no sustituto
# ──────────────────────────────────────────────────────────────────────────────

class ModelSeamProbe:
    """Envuelve un `ModelCallerProtocol` y registra qué cruzó el cable.

    Delega **todo** en el caller envuelto (incluida
    `supports_native_tool_search`, que el loop consulta por `getattr` para elegir
    la estrategia diferida): si el probe cambiara esa respuesta, el turno que se
    mide dejaría de ser el turno real.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.calls: list[dict[str, Any]] = []
        #: la señal que el runtime pasó en cada llamada — `E1` comprueba que es una
        #: `AbortSignal` de verdad y no el `asyncio.Event` que nadie sabía leer.
        self.stops: list[Any] = []

    def supports_native_tool_search(self, model_id: str = "") -> bool:
        probe = getattr(self._inner, "supports_native_tool_search", None)
        return bool(probe(model_id)) if callable(probe) else False

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        stop: Any | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Any, None]:
        # `**kwargs` y no la lista explícita: el probe tiene que ver TODO lo que el
        # runtime pide (la `S1` de `C2` añadió siete opciones) y reenviarlo intacto.
        # Un probe con firma corta se convertiría él mismo en el descarte silencioso
        # que este gate persigue.
        self.calls.append({"messages": messages, "tools": tools, **kwargs})
        self.stops.append(stop)
        return await self._inner.complete(messages, tools, stop=stop, **kwargs)

    def wire_payload(self) -> str:
        """Todo lo capturado, serializado — la superficie que se inspecciona."""
        return json.dumps(self.calls, default=str)


class IdentityWitnessTool:
    """Tool real que **testifica el ctx** que le llega y devuelve un token único.

    Doble función a propósito: el token hace que el resultado del turno sea
    inadivinable (prueba de que la tool se despachó y el modelo consumió su
    salida) y el ctx capturado permite aseverar que la identidad viaja **por
    dato** hasta el último eslabón — el punto donde la mímica anterior
    autogeneraba `user_<hex>`.
    """

    name = "consultar_expediente"
    description = "Consulta el expediente activo y devuelve su código de verificación."
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self, code: str) -> None:
        self._code = code
        self.seen: list[ToolUseContext] = []

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        self.seen.append(ctx)
        return ToolResult(tool_name=self.name, output=f"codigo de verificacion: {self._code}")


def _runtime(tmp_path: Path, caller: Any, tools: tuple, scope: Scope | None, **extra: Any):
    """Punto de composición **real** (`C10`): el mismo `create_runtime` de producción."""
    return create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        tools=ToolsConfig(extras=list(tools)),
        scope=scope,
        **extra,
    ))


# ──────────────────────────────────────────────────────────────────────────────
# E1 · la `S1` enriquecida llega AL CABLE — turno real texto-solo
# ──────────────────────────────────────────────────────────────────────────────
#
# Acredita `C2`. Dos observatorios, porque uno solo se puede satisfacer sin que
# nada funcione:
#
#   · el **seam** (`ModelSeamProbe`) ve lo que el runtime PIDE al motor;
#   · el **cable** (`on_payload`) ve los params exactos con los que el provider
#     llama a Azure — es lo único que distingue «el kwarg viajó» de «el kwarg
#     llegó». Un puente que aceptara `max_tokens` y no lo tradujera pasaría el
#     primero y fallaría el segundo.
#
# ⚠ **límite honesto medido en la wheel `agentic_models==0.2.0`, no supuesto:**
# `metadata` es un campo real de `StreamOptions`, pero el provider
# `azure-openai-responses` **no lo lee** — no aparece en sus params. Por eso aquí
# se acredita donde de verdad se puede: llega al seam (transporte de `ID-7`) y el
# runtime **no lo interpreta** por el camino. Lo mismo con `tool_choice`/
# `output_format`: no existen en esa versión, y por eso el puente los **rechaza**
# en vez de tragárselos — eso se prueba abajo, sin gastar un turno real.

@_needs_azure
async def test_e1_enriched_model_seam_reaches_the_provider_wire(tmp_path):
    from agentic_models.model_types import StreamOptions

    from agentic_runtime.contracts.abort import AbortSignal
    from agentic_runtime.models.protocol import Effort, ModelOptions

    wire: list[dict] = []

    async def _on_payload(params: dict, model: Any):
        wire.append(params)

    opaque = f"tenant-E1-{uuid.uuid4().hex}"
    probe = ModelSeamProbe(_build_caller(
        "Responde en una sola linea, sin herramientas.",
        options=StreamOptions(on_payload=_on_payload),
    ))
    runtime = _runtime(
        tmp_path, probe, (), Scope("scope-e1"),
        model_options=ModelOptions(
            effort=Effort.LOW,
            max_tokens=2048,
            metadata={"tenant": opaque},
        ),
    )

    task_id = await runtime.dispatch(RuntimeTask(
        prompt="Di exactamente: LISTO. Nada mas.",
        description="gate-e1-turno-texto-solo",
        session_id=f"sess-E1-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    # --- el turno corrió DE VERDAD -------------------------------------------
    assert runtime.status(task_id) == TaskStatus.COMPLETED, runtime.result(task_id)
    assert "LISTO" in (runtime.result(task_id) or "").upper()

    # --- 1. el seam: el runtime pidió lo que el integrador declaró ------------
    assert probe.calls, "el probe no interceptó el seam"
    call = probe.calls[0]
    assert call["effort"] is Effort.LOW
    assert call["max_tokens"] == 2048
    assert call["metadata"] == {"tenant": opaque}      # `ID-7`: transportada…
    assert "tenant" not in json.dumps(call["messages"], default=str), (
        "…y NO interpretada: la metadata del integrador se filtró al prompt"
    )

    # --- 2. la señal de abort es del tipo que el motor sabe leer --------------
    stop = probe.stops[0]
    assert stop is not None, "el runtime no armó ninguna señal de abort (S2 latente)"
    assert isinstance(stop, AbortSignal), f"llegó {type(stop).__name__}, no una AbortSignal"
    assert stop.aborted is False

    # --- 3. el CABLE: los params reales con los que se llamó a Azure ----------
    assert wire, "on_payload no se disparó: no hay cable que medir"
    params = wire[0]
    assert params["max_output_tokens"] == 2048, (
        f"`max_tokens` no llegó traducido al provider: {params.keys()}"
    )
    # `effort` NO es passthrough: lo traduce el puente vía `stream_simple(reasoning=…)`
    # y el provider lo rinde como `reasoning.effort` (`SEAMS §S1 A2.2`).
    assert params.get("reasoning", {}).get("effort"), (
        f"el razonamiento pedido no llegó al provider: {params.get('reasoning')}"
    )
    # Lo que el provider NO lee, no se finge que lee.
    assert opaque not in json.dumps(params, default=str)


def test_e1_the_bridge_refuses_what_it_cannot_translate_instead_of_dropping_it():
    """La otra mitad de `C2`: lo intraducible **revienta**.

    `tool_choice` y `output_format` no tienen representación alguna en
    `agentic_models 0.2.0` (medido leyendo `model_types.py` 1→EOF). Tragárselos
    daría un turno que corre bien y hace algo distinto de lo pedido — que es
    exactamente el modo de fallo con el que nació el `stop` roto. No gasta turno
    real porque falla **antes** de abrir el stream: ése es el punto.
    """
    import asyncio as _asyncio

    from agentic_runtime.models.caller import AgenticModelsCaller
    from agentic_runtime.models.protocol import (
        OutputFormat,
        ToolChoice,
        UnsupportedModelOptionError,
    )

    caller = AgenticModelsCaller(model=object())

    for kwargs in (
        {"output_format": OutputFormat(json_schema={"type": "object"})},
        {"tool_choice": ToolChoice(mode="required")},
    ):
        with pytest.raises(UnsupportedModelOptionError):
            _asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
                caller.complete([], [], **kwargs)
            )


# ──────────────────────────────────────────────────────────────────────────────
# E5 · el abort CORTA el stream a mitad — turno real
# ──────────────────────────────────────────────────────────────────────────────
#
# Acredita la segunda mitad de `C2` (`S2`). El corte se dispara desde fuera, en
# vivo, mientras los tokens reales de Azure están llegando: es el caso HITL.
#
# ⚠ **límite honesto medido en la wheel**: sólo el provider `anthropic` consulta
# `signal.aborted` DENTRO de su iterador SSE (`_iterate_sse:450`); el camino
# `azure-openai-responses` lo mira **después** de terminar el stream
# (`azure_openai_responses.py:213`). Luego el corte a mitad **es del runtime** —
# el chequeo por evento de `AgentLoop` (`_aborted(ctx)`)— y así se acredita.
# Decirlo aquí es parte de la prueba: fingir que corta el provider sería
# acreditar una capacidad que este motor no tiene.

@_needs_azure
async def test_e5_arming_the_abort_mid_stream_cuts_the_turn(tmp_path):
    from agentic_runtime.contracts.abort import AbortReason
    from agentic_runtime.events.event_types import TokenEvent

    tail = "FINDECUENTA"
    prompt = (
        "Escribe los numeros del 1 al 60, uno por linea, sin ningun otro texto, "
        f"y termina escribiendo la palabra {tail}."
    )

    async def _run(abort_after: int | None) -> dict:
        captured: dict[str, Any] = {}

        def _capture_ctx(ctx, task):
            captured["ctx"] = ctx  # seam real de producción: `root_context_modifier`
            return ctx

        seen: list[Any] = []

        async def _on_event(event: Any) -> None:
            seen.append(event)
            if abort_after is None:
                return
            tokens = [e for e in seen if isinstance(e, TokenEvent)]
            if len(tokens) == abort_after:
                # Alguien de FUERA corta, en mitad del stream vivo.
                captured["ctx"].stop.abort(AbortReason.USER_INTERRUPT)
                captured["cut_at"] = len(seen)

        runtime = _runtime(
            tmp_path / f"run-{abort_after}", ModelSeamProbe(_build_caller(
                "Obedeces al pie de la letra y no usas herramientas."
            )), (), Scope("scope-e5"),
            root_context_modifier=_capture_ctx,
        )
        task_id = await runtime.dispatch(
            RuntimeTask(
                prompt=prompt,
                description=f"gate-e5-{abort_after}",
                session_id=f"sess-E5-{uuid.uuid4().hex}",
            ),
            on_event=_on_event,
        )
        await runtime._task_registry.get(task_id).asyncio_task
        return {
            "runtime": runtime, "task_id": task_id, "seen": seen,
            "ctx": captured.get("ctx"), "cut_at": captured.get("cut_at"),
            "text": (runtime.result(task_id) or ""),
        }

    # --- control POSITIVO: sin abort, el turno llega hasta el final ----------
    full = await _run(abort_after=None)
    full_tokens = [e for e in full["seen"] if isinstance(e, TokenEvent)]
    assert tail in full["text"].replace(" ", "").upper(), (
        "sin abort el modelo no llegó al final: el corte de abajo no probaría nada"
    )

    # --- el corte real -------------------------------------------------------
    cut = await _run(abort_after=3)
    cut_tokens = [e for e in cut["seen"] if isinstance(e, TokenEvent)]

    # 1. el loop dejó de rendir eventos EN EL ACTO (el de por evento es su único
    #    punto de control: el provider Azure no mira la señal a mitad de stream).
    assert cut["cut_at"] is not None
    assert len(cut["seen"]) == cut["cut_at"], (
        f"llegaron {len(cut['seen']) - cut['cut_at']} eventos DESPUÉS del abort"
    )
    # 2. y había mucho más por venir: el corte no coincidió con el fin natural.
    assert len(cut_tokens) < len(full_tokens), (
        f"el turno abortado rindió {len(cut_tokens)} tokens y el completo "
        f"{len(full_tokens)}: no se cortó nada"
    )
    # 3. el turno abortado no dejó la respuesta: dejó un corte.
    assert tail not in cut["text"].replace(" ", "").upper()
    # 4. no hubo re-prompt tras el corte, y el motivo sobrevivió al camino.
    assert cut["runtime"]._task_registry.get(cut["task_id"]).turn_count == 1
    assert cut["ctx"].stop.aborted is True
    assert cut["ctx"].stop.reason() is AbortReason.USER_INTERRUPT


# ──────────────────────────────────────────────────────────────────────────────
# E6 · pieza 1+2 — turno real sin identidad + probe en el seam del modelo
# ──────────────────────────────────────────────────────────────────────────────

@_needs_azure
async def test_e6_full_turn_without_identity_and_no_identity_reaches_the_model_seam(tmp_path):
    session_sentinel = f"sess-E6-{uuid.uuid4().hex}"
    scope_sentinel = f"scope-E6-{uuid.uuid4().hex}"
    code = f"VF-{uuid.uuid4().hex[:8].upper()}"

    tool = IdentityWitnessTool(code)
    probe = ModelSeamProbe(_build_caller(
        "Eres un asistente. Usa la herramienta disponible cuando te pidan el codigo "
        "de verificacion, y responde incluyendo el codigo exacto que obtengas."
    ))
    runtime = _runtime(tmp_path, probe, (tool,), Scope(scope_sentinel))

    # Ni `owner_id` ni nada que identifique a una persona: sólo la sesión opaca que
    # atribuye el integrador y el scope de persistencia — los DOS cables de `D-11`.
    task = RuntimeTask(
        prompt="Dame el codigo de verificacion del expediente activo. Usa la herramienta.",
        description="gate-e6-sin-identidad",
        session_id=session_sentinel,
    )
    assert task.owner_id is None, "E6 corre sin owner_id: el runtime no conoce usuarios"

    task_id = await runtime.dispatch(task)
    await runtime._task_registry.get(task_id).asyncio_task

    # --- 1. el turno corrió DE VERDAD (si no, lo demás no probaría nada) -------
    assert runtime.status(task_id) == TaskStatus.COMPLETED
    result = runtime.result(task_id) or ""
    assert code in result, "el modelo no consumió la salida real de la tool"
    assert len(tool.seen) >= 1, "la tool no se despachó: no hay turno que medir"
    assert runtime._task_registry.get(task_id).turn_count >= 2

    # --- 2. la identidad llegó por DATO hasta el último eslabón ---------------
    seen = tool.seen[0]
    assert seen.session_id == session_sentinel
    assert seen.scope == Scope(scope_sentinel)
    assert not hasattr(seen, "user_id"), "el runtime volvió a conocer usuarios (C9)"

    # --- 3. el probe capturó el cable, y la identidad NO cruzó ----------------
    assert len(probe.calls) >= 2, "el probe no interceptó el seam del modelo"
    payload = probe.wire_payload()
    # el probe mira de verdad (si no viera el turno, lo de abajo pasaría vacío)
    assert "codigo de verificacion" in payload

    assert session_sentinel not in payload, "el session_id opaco cruzó al proveedor"
    assert scope_sentinel not in payload, "el scope de persistencia cruzó al proveedor"
    for spelling in _IDENTITY_SPELLINGS:
        assert spelling not in payload, f"grafía de identidad '{spelling}' en el cable del modelo"

    # --- 4. la persistencia se escribió bajo el SCOPE, no bajo un id inventado -
    transcript = tmp_path / StorageKeys.transcript_key(Scope(scope_sentinel), session_sentinel)
    assert transcript.exists(), "el transcript no se persistió bajo la clave scopeada"
    written = [str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file()]
    assert written and all(p.startswith(f"{scope_sentinel}/") for p in written), (
        f"algo se escribió fuera del scope atribuido: {written}"
    )
    assert not any("user_" in p or "sess_" in p for p in written), (
        f"reapareció un id autogenerado en las claves: {written}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# E6 · pieza 3 — la NEGATIVA: sin identidad atribuida no hay turno, ni escritura
# ──────────────────────────────────────────────────────────────────────────────

async def test_e6_negative_runtime_refuses_to_invent_identity_end_to_end(tmp_path):
    """Sin `session_id` el runtime falla en voz alta **por el camino real**.

    No usa el modelo: revienta antes de llegar al seam, que es justo lo que se
    acredita. Corre siempre — parte del gate no depende de tener Azure.
    """
    probe = ModelSeamProbe(object())  # si algo lo llamara, reventaría: nadie debe
    runtime = _runtime(tmp_path, probe, (), Scope("scope-e6-negativa"))

    task_id = await runtime.dispatch(
        RuntimeTask(prompt="hola", description="gate-e6-negativa")  # sin session_id
    )
    await runtime._task_registry.get(task_id).asyncio_task

    assert probe.calls == [], "se llamó al modelo con una identidad que nadie atribuyó"
    # **Aserción reforzada por `C4`.** Cuando `E6` se escribió, esto sólo podía decir
    # `!= COMPLETED`: `_build_child` se llamaba FUERA del `try:` de `_run_loop`, la
    # `RuntimeIdentityError` se escapaba a la `asyncio.Task` y el registry se quedaba
    # en `RUNNING`. Fallar en voz alta y fallar **registrado** no son lo mismo, y sólo
    # lo segundo es observable. Pagado el defecto, la negativa asevera el estado real.
    assert runtime.status(task_id) is TaskStatus.FAILED
    assert "session_id" in (runtime._task_registry.get(task_id).error or "")
    assert [p for p in tmp_path.rglob("*") if p.is_file()] == [], (
        "se persistió algo bajo una clave inventada"
    )


# ──────────────────────────────────────────────────────────────────────────────
# E4 · la NEGATIVA OBLIGATORIA — sin runner cableado, el spawn falla LIMPIO
# ──────────────────────────────────────────────────────────────────────────────
#
# `TRAMO-1 §4·E4`: *runtime sin cablear (`runner=None`) ⇒ `is_error` limpio, no
# excepción*; acredita que las costuras son **load-bearing**. Va antes que `E2` y
# `E3` a propósito: sin ella, el verde de un turno padre→hijo no distingue «la
# costura está cableada» de «la costura existe y algo la suple» (`L09`).
#
# Se escribe en tres piezas porque cada una sola es trivialmente satisfacible:
#
#   1. **control positivo** — con el runner puesto, el spawn de verdad ocurre. Sin
#      esto, «devolvió `is_error`» sería cierto porque la tool no hace nada.
#   2. **negativa de costura** — sin runner, `AgentTool` devuelve `is_error=True` y
#      **no lanza**: el turno del padre puede continuar.
#   3. **negativa E2E real** — el modelo llama a `Agent` en un runtime ensamblado
#      por `create_runtime`, y el turno **completa**: el fallo viaja como resultado
#      de tool y el loop re-entra. Es lo único que distingue *falla limpio* de
#      *revienta el turno*.
#
# ⚠ **hallazgo medido en esta ventana, no inferido** (`factory.py` leído 1→EOF):
# `create_runtime` **nunca llama `set_runner`** — el ensamblador de producción no
# puebla `S18`. O sea que hoy el estado «sin cablear» **no es un caso de prueba
# artificial: es el de producción**, y todo spawn real devuelve el error de la
# pieza 2. Es `FIND-EXEC1`, sigue abierto, y su pago es de **`C8`** (que además
# retira el global en favor de `ctx.runner`, `TRAMO-1 §C8·cableado`). `E4` lo deja
# aseverado en vez de narrado: cuando `C8` cablee el runner, la pieza 3 seguirá
# midiendo lo mismo porque construye su runtime **sin** él explícitamente.
#
# El global `_runner` se aísla en cada pieza: es estado de proceso, y dejarlo
# sucio contamina otras corridas (medido: `test_context_identity.py:152,172` lo
# setea y no lo restaura).

@pytest.fixture
def _isolated_runner():
    """Salva y restaura el `_runner` global — sin esto, `E4` mide al vecino."""
    from agentic_runtime.execution import runner as runner_mod

    previous = runner_mod._runner
    runner_mod._runner = None
    try:
        yield runner_mod
    finally:
        runner_mod._runner = previous


def _agent_tool_ctx(scope: Scope) -> ToolUseContext:
    return ToolUseContext(session_id=f"sess-E4-{uuid.uuid4().hex}", scope=scope)


async def test_e4_control_positive_agent_tool_spawns_when_the_seam_is_wired(_isolated_runner):
    """Control: con la costura poblada, el spawn OCURRE y devuelve su salida.

    Sin esta pieza, la negativa de abajo pasaría igual con una `AgentTool` que no
    hiciera absolutamente nada.
    """
    token = f"HIJO-{uuid.uuid4().hex[:8].upper()}"
    seen: list[Any] = []

    class _Runner:
        async def run(self, fork_ctx: Any, *, background: bool) -> str | None:
            seen.append((fork_ctx, background))
            return token

    _isolated_runner.set_runner(_Runner())

    from agentic_runtime.tools.native.agent import AgentTool

    result = await AgentTool().execute(
        {"prompt": "haz algo", "description": "hijo-e4"},
        _agent_tool_ctx(Scope("scope-e4-positiva")),
    )

    assert result.is_error is False, result.output
    assert token in result.output, "la salida del hijo no llegó al padre"
    assert seen and seen[0][1] is False, "el spawn no cruzó la costura"


async def test_e4_negative_unwired_runner_yields_clean_is_error_not_an_exception(_isolated_runner):
    """**La negativa obligatoria del gate.** Sin runner, `is_error` limpio.

    Dos cosas a la vez, y las dos importan:
      · **no lanza** — si lanzara, el turno del padre moriría y el modelo no podría
        reaccionar al fallo;
      · **`is_error=True`** — si devolviera un `ToolResult` normal, el modelo leería
        el fallo como éxito, que es el modo de fallo caro de `L09`.
    """
    assert _isolated_runner._runner is None, "la fixture no aisló el global"

    from agentic_runtime.tools.native.agent import AgentTool

    result = await AgentTool().execute(
        {"prompt": "haz algo", "description": "hijo-e4-negativa"},
        _agent_tool_ctx(Scope("scope-e4-negativa")),
    )

    assert result.is_error is True, "el spawn sin costura se dio por bueno"
    assert "Subagent failed" in result.output
    assert result.tool_name == "Agent"


def test_e4_the_production_assembler_does_not_wire_the_runner_yet(tmp_path, _isolated_runner):
    """`FIND-EXEC1` **aseverado**, no narrado: `create_runtime` no puebla `S18`.

    Este test es una **fotografía del estado real**, y está escrito para ponerse
    ROJO cuando `C8` cablee el runner por `ctx.runner`. Ese rojo será la señal de
    que la pieza 3 hay que reescribirla contra la costura nueva — que es
    exactamente lo que se quiere que ocurra, en vez de que `E4` siga verde
    midiendo un mundo que ya cambió.
    """
    _runtime(tmp_path, object(), (), Scope("scope-e4-find-exec1"))

    assert _isolated_runner._runner is None, (
        "`create_runtime` ya cablea el runner: `FIND-EXEC1` está pagado y la pieza 3 "
        "de `E4` debe reescribirse contra `ctx.runner` (`C8`)"
    )


@_needs_azure
async def test_e4_negative_end_to_end_the_parent_turn_survives_an_unwired_spawn(
    tmp_path, _isolated_runner,
):
    """Turno REAL: el modelo pide un subagente, no hay costura, y el padre sobrevive.

    Esto es lo que ninguna unitaria acredita: que el fallo de la costura viaja
    **como resultado de tool** por el camino de producción entero (dispatcher →
    aplanado → re-entrada del loop) y el turno termina `COMPLETED` en vez de
    dejar la task en `FAILED` con una excepción escapada.
    """
    probe = ModelSeamProbe(_build_caller(
        "Cuando te pidan delegar trabajo, usa la herramienta Agent. Si la herramienta "
        "devuelve un error, explica en una linea que la delegacion fallo."
    ))
    runtime = _runtime(tmp_path, probe, (), Scope("scope-e4-e2e"))

    task_id = await runtime.dispatch(RuntimeTask(
        prompt="Delega en un subagente la tarea de listar tres colores. Usa la herramienta Agent.",
        description="gate-e4-spawn-sin-cablear",
        session_id=f"sess-E4-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    # 1. el turno del padre NO murió: el fallo de la costura no es una excepción.
    assert runtime.status(task_id) is TaskStatus.COMPLETED, runtime.result(task_id)
    assert (runtime.result(task_id) or "").strip(), "el padre no llegó a responder"

    # 2. y el modelo LLEGÓ a pedir el spawn — si no, no habría fallo que sobrevivir.
    payload = probe.wire_payload()
    assert "Subagent failed" in payload, (
        "el error de la costura no volvió al modelo como resultado de tool: "
        f"{payload[-1500:]}"
    )
    # 3. re-entrada: hubo un turno DESPUÉS del fallo (el padre reaccionó).
    assert runtime._task_registry.get(task_id).turn_count >= 2


# ──────────────────────────────────────────────────────────────────────────────
# E6 · guardia de grafía — `AC-39`/`D-11`: un rename no puede pasar en silencio
# ──────────────────────────────────────────────────────────────────────────────

def test_e6_old_identity_spelling_explodes_instead_of_being_dropped():
    """`extra="forbid"` es lo que impide el verde que ya no prueba nada.

    Sin él, `ToolUseContext(user_id=…)` se **descartaría en silencio** y un test
    que aseverase «no hay user_id» seguiría verde midiendo nada.
    """
    from pydantic import ValidationError

    for spelling in _IDENTITY_SPELLINGS:
        with pytest.raises(ValidationError):
            ToolUseContext(session_id="s1", **{spelling: "u1"})
