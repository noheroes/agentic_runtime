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
# ⚠ **`FIND-EXEC1` está PAGADO** (`C8`, esta ventana). Cuando `E4` se escribió, el
# hallazgo medido era que `create_runtime` **nunca llamaba `set_runner`**: el
# ensamblador de producción no poblaba `S18` y todo spawn real devolvía el error
# de la pieza 2. La pieza 3 se escribió entonces como fotografía de ese estado y
# **con su propia muerte anunciada** — «se pondrá roja cuando `C8` cablee el
# runner». Se puso roja, y aquí está reescrita contra la costura nueva: hoy
# asevera lo contrario, que el ensamblador **sí** puebla `S18` y lo threadea hasta
# el `ctx` de la task. El global `_runner`/`set_runner`/`get_runner` ya no existe
# (`SEAMS §S18`: singleton global → deps-DI `S27`), así que tampoco existe la
# fixture que lo aislaba: la costura viaja por `ToolUseContext.runner` y el
# aislamiento entre piezas es el que da construir un ctx por pieza.
#
# El caso «sin cablear» de las piezas 2 y 4 deja por eso de ser el de producción y
# pasa a construirse **explícitamente** (`runner=None` en el ctx;
# `subagent_runner_factory=lambda _rt: None` en el ensamblador). Es lo correcto:
# `E4` mide que la costura es *load-bearing*, no que esté rota.


def _agent_tool_ctx(scope: Scope, runner: Any = None) -> ToolUseContext:
    return ToolUseContext(
        session_id=f"sess-E4-{uuid.uuid4().hex}", scope=scope, runner=runner
    )


async def test_e4_control_positive_agent_tool_spawns_when_the_seam_is_wired():
    """Control: con la costura poblada, el spawn OCURRE y devuelve su salida.

    Sin esta pieza, la negativa de abajo pasaría igual con una `AgentTool` que no
    hiciera absolutamente nada.
    """
    token = f"HIJO-{uuid.uuid4().hex[:8].upper()}"
    seen: list[Any] = []

    class _Runner:
        async def run(self, spec: Any, *, background: bool = False) -> str | None:
            seen.append((spec, background))
            return token

    from agentic_runtime.tools.native.agent import AgentTool

    result = await AgentTool().execute(
        {"prompt": "haz algo", "description": "hijo-e4"},
        _agent_tool_ctx(Scope("scope-e4-positiva"), runner=_Runner()),
    )

    assert result.is_error is False, result.output
    assert token in result.output, "la salida del hijo no llegó al padre"
    assert seen and seen[0][1] is False, "el spawn no cruzó la costura"
    # y cruzó con la forma nueva de `S18`: un `SubagentSpec`, no un `ForkContext`.
    assert seen[0][0].prompt == "haz algo"
    assert seen[0][0].parent_snapshot.scope == Scope("scope-e4-positiva")


async def test_e4_negative_unwired_runner_yields_clean_is_error_not_an_exception():
    """**La negativa obligatoria del gate.** Sin runner, `is_error` limpio.

    Dos cosas a la vez, y las dos importan:
      · **no lanza** — si lanzara, el turno del padre moriría y el modelo no podría
        reaccionar al fallo;
      · **`is_error=True`** — si devolviera un `ToolResult` normal, el modelo leería
        el fallo como éxito, que es el modo de fallo caro de `L09`.
    """
    ctx = _agent_tool_ctx(Scope("scope-e4-negativa"))
    assert ctx.runner is None, "el ctx de la negativa llegó con la costura puesta"

    from agentic_runtime.tools.native.agent import AgentTool

    result = await AgentTool().execute(
        {"prompt": "haz algo", "description": "hijo-e4-negativa"}, ctx
    )

    assert result.is_error is True, "el spawn sin costura se dio por bueno"
    assert "Subagent runner not wired" in result.output
    assert result.tool_name == "Agent"


async def test_e4_the_production_assembler_wires_the_runner_and_threads_it_to_the_ctx(tmp_path):
    """`FIND-EXEC1` **pagado**, aseverado por el camino de producción entero.

    No basta con mirar `runtime._runner`: eso probaría que la costura *existe* en
    el ensamblador, no que *llega* a quien la usa (`L09` — cablear ≠ existir). El
    testigo es un `UserInputProcessor` real (`S11`) cableado por
    `RuntimeConfig.input_processor`, que corre **dentro** del turno y ve el mismo
    `ctx` que verá `AgentTool`. Corta el turno (`short_circuit`) para que la pieza
    no necesite modelo: lo que mide es el threading, no la conversación.
    """
    from agentic_runtime.contracts.user_input import ProcessedInput
    from agentic_runtime.execution.runner import SubagentRunnerProtocol

    seen: list[Any] = []

    class _RunnerWitness:
        async def process(self, prompt: str, ctx: Any) -> ProcessedInput:
            seen.append(getattr(ctx, "runner", None))
            return ProcessedInput(prompt=prompt, short_circuit=True, result_text="ok")

    runtime = _runtime(
        tmp_path, None, (), Scope("scope-e4-find-exec1"), input_processor=_RunnerWitness()
    )

    # 1. el ensamblador puebla `S18` — lo que `create_runtime` NO hacía.
    assert isinstance(runtime._runner, SubagentRunnerProtocol), (
        "`create_runtime` volvió a ensamblar un runtime sin runner: `FIND-EXEC1`"
    )

    # 2. y esa costura LLEGA al ctx del turno.
    task_id = await runtime.dispatch(RuntimeTask(
        prompt="da igual, el turno se corta",
        description="gate-e4-threading",
        session_id=f"sess-E4-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    assert runtime.status(task_id) is TaskStatus.COMPLETED, runtime.result(task_id)
    assert seen, "el testigo `S11` no llegó a correr: el turno no ocurrió"
    assert seen[0] is runtime._runner, (
        "el runner del ensamblador no llegó al `ctx`: la costura existe pero no se cablea"
    )


@_needs_azure
async def test_e4_negative_end_to_end_the_parent_turn_survives_an_unwired_spawn(tmp_path):
    """Turno REAL: el modelo pide un subagente, no hay costura, y el padre sobrevive.

    Esto es lo que ninguna unitaria acredita: que el fallo de la costura viaja
    **como resultado de tool** por el camino de producción entero (dispatcher →
    aplanado → re-entrada del loop) y el turno termina `COMPLETED` en vez de
    dejar la task en `FAILED` con una excepción escapada.

    El runtime se ensambla **explícitamente sin subagentes**
    (`subagent_runner_factory=lambda _rt: None`): desde que `C8` pagó
    `FIND-EXEC1`, el default de producción SÍ cablea `S18`, así que el caso «sin
    costura» hay que construirlo a propósito en vez de heredarlo del defecto.
    """
    probe = ModelSeamProbe(_build_caller(
        "Cuando te pidan delegar trabajo, usa la herramienta Agent. Si la herramienta "
        "devuelve un error, explica en una linea que la delegacion fallo."
    ))
    runtime = _runtime(
        tmp_path, probe, (), Scope("scope-e4-e2e"),
        subagent_runner_factory=lambda _rt: None,
    )

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
    assert "Subagent runner not wired" in payload, (
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


# ──────────────────────────────────────────────────────────────────────────────
# E3 · el padre DELEGA de verdad y el resultado del hijo vuelve aplanado
# ──────────────────────────────────────────────────────────────────────────────
#
# `TRAMO-1 §4·E3`: *turno real padre→subagente; el resultado del hijo se aplana y
# el padre lo cita*. Acredita `C8` (`S18` por DI) por el camino de producción
# entero: `create_runtime` → `ctx.runner` → `LocalSubagentRunner` → `dispatch` del
# hijo → `join` → `ToolResult` del `AgentTool` → re-entrada del loop del padre.
#
# Es la pieza POSITIVA que le faltaba a `E4`: `E4` prueba que sin costura se falla
# limpio, y sin `E3` «falla limpio» sería compatible con «no delega nunca».
#
# El token del hijo es un `uuid` por corrida devuelto por una tool REAL que sólo
# el hijo puede haber llamado: si el padre lo cita, es que la salida del hijo
# cruzó de vuelta. Inadivinable a propósito (`L09`).

@_needs_azure
async def test_e3_the_parent_delegates_for_real_and_quotes_the_child_result(tmp_path):
    """Padre→hijo REAL: dos turnos de modelo distintos, un token que sólo el hijo ve."""
    code = f"EXP-{uuid.uuid4().hex[:8].upper()}"
    witness = IdentityWitnessTool(code)
    # El prompt de sistema es del RUNTIME, así que lo lee también el hijo: por eso se
    # escribe condicionado al rol y no «eres un coordinador que nunca llama la tool»
    # —medido en esta ventana: con esa forma el hijo se creía coordinador, volvía a
    # delegar y la delegación se hacía recursiva hasta el tope de profundidad—.
    probe = ModelSeamProbe(_build_caller(
        "Trabajas con herramientas. Si te piden DELEGAR, usa la herramienta Agent una sola "
        "vez, con inherit_messages=false, y despues repite literalmente el codigo que te "
        "devuelva. Si lo que te piden es consultar el expediente, llama tu mismo a la "
        "herramienta consultar_expediente y responde solo con su codigo. Nunca delegues una "
        "tarea que ya te han delegado a ti."
    ))
    runtime = _runtime(tmp_path, probe, (witness,), Scope("scope-e3"))

    task_id = await runtime.dispatch(RuntimeTask(
        prompt=(
            "Delega en un subagente con la herramienta Agent esta tarea: llamar a la "
            "herramienta consultar_expediente y devolver el codigo de verificacion. "
            "Luego dime ese codigo."
        ),
        description="gate-e3-delegacion-real",
        session_id=f"sess-E3-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    result = runtime.result(task_id) or ""
    assert runtime.status(task_id) is TaskStatus.COMPLETED, result

    # 1. el hijo corrió DE VERDAD, y corrió como hijo — no fue el padre llamando la
    #    tool y diciendo que delegó.
    assert witness.seen, "nadie llamó a la tool: no hubo turno de subagente"
    child_ctxs = [c for c in witness.seen if c.is_subagent]
    assert child_ctxs, "la tool la ejecutó el padre: no hubo delegación (`S18` sin cruzar)"

    # 2. el hijo heredó la identidad del padre POR DATO (`D-11`), sin inventarse nada.
    assert child_ctxs[0].scope == Scope("scope-e3")
    assert child_ctxs[0].subagent_depth == 1

    # 3. y su salida volvió APLANADA al padre, que la cita.
    assert code in result, f"el padre no citó el resultado del hijo: {result!r}"

    # 4. el aplanado cruzó el cable del modelo como resultado de tool (no lo adivinó).
    assert code in probe.wire_payload()


# ──────────────────────────────────────────────────────────────────────────────
# E9 · la notificación del hijo de fondo LLEGA al historial vivo del padre
# ──────────────────────────────────────────────────────────────────────────────
#
# `TRAMO-1 §4·E9`: *el padre recibe y aplica la notificación de un hijo*. Acredita
# el `CORE-GAP H-5`: el canal `S21` tenía `put` y no tenía **call-site de drenaje**
# — la maquinaria entera existía y no la llamaba nadie, y la única firma de
# aplicación que había escribía sobre `session.messages`, que `_run_loop` reasigna
# al terminar, así que el XML se descartaba en silencio.
#
# Divergencia declarada (`L10`), dicha antes de que se note: lo que este test NO
# deja al modelo es la **decisión** de lanzar en background — el spawn de fondo se
# pide por la costura (`AgentTool` con `run_in_background`), no rogándole al
# modelo que elija ese flag. El MECANISMO es entero de producción (runner real →
# `dispatch` real → turno de modelo REAL del hijo → `_notify` → canal → drenaje del
# loop del padre → `apply_notification` → cable del modelo), y el turno del padre
# que consume la notificación es un turno real. `S22 ForceAsyncPolicy` sigue
# **ausente** (`TRAMO-1`, bajo la línea de corte): no se simula.

@_needs_azure
async def test_e9_the_background_child_notification_reaches_the_parent_live_history(tmp_path):
    """`H-5` pagado: el hijo de fondo termina y el padre SE ENTERA en su turno siguiente."""
    from agentic_runtime.tools.native.agent import AgentTool

    code = f"EXP-{uuid.uuid4().hex[:8].upper()}"
    witness = IdentityWitnessTool(code)
    probe = ModelSeamProbe(_build_caller(
        "Respondes en una linea. Si en la conversacion aparece una notificacion de una "
        "tarea de fondo, cita literalmente el codigo que contenga."
    ))
    scope = Scope("scope-e9")
    session_id = f"sess-E9-{uuid.uuid4().hex}"
    runtime = _runtime(tmp_path, probe, (witness,), scope)

    # 1. spawn de FONDO por la costura real: el `ctx` lleva el runner que ensambló
    #    `create_runtime`, igual que el que `_run_loop` threadea en un turno.
    ctx = ToolUseContext(session_id=session_id, scope=scope, runner=runtime._runner)
    spawn = await AgentTool().execute(
        {
            "prompt": (
                "Llama a la herramienta consultar_expediente y responde SOLO con el "
                "codigo de verificacion que devuelva."
            ),
            "description": "hijo-e9-de-fondo",
            "run_in_background": True,
        },
        ctx,
    )
    assert spawn.is_error is False, spawn.output

    child_id = spawn.output.strip().split()[-1]
    child = runtime._task_registry.get(child_id)
    assert child is not None, f"el spawn de fondo no dejó task en el registry: {spawn.output!r}"
    await child.asyncio_task
    assert runtime.status(child_id) is TaskStatus.COMPLETED, runtime.result(child_id)
    assert code in (runtime.result(child_id) or ""), "el hijo no llegó a resolver su tarea"

    # 2. turno REAL del padre, MISMA sesión: al arrancar drena el canal y aplica.
    parent_id = await runtime.dispatch(RuntimeTask(
        prompt="Que te ha reportado tu tarea de fondo?",
        description="gate-e9-padre-se-entera",
        session_id=session_id,
    ))
    await runtime._task_registry.get(parent_id).asyncio_task
    assert runtime.status(parent_id) is TaskStatus.COMPLETED, runtime.result(parent_id)

    # 3. la notificación cruzó AL MODELO — historial vivo, no `session.messages`.
    payload = probe.wire_payload()
    assert "<task-notification" in payload, (
        f"el canal no se drenó en el turno del padre (`H-5`): {payload[-1500:]}"
    )
    assert code in payload, "la notificación llegó vacía de lo que el hijo produjo"

    # 4. y se consume UNA vez: el canal queda limpio tras aplicarla.
    assert runtime._notification_sink.drain(scope.key, session_id) == []


# ──────────────────────────────────────────────────────────────────────────────
# E2 · turno REAL con tools NATIVAS reales (bash + fs), aplanado y re-entrada
# ──────────────────────────────────────────────────────────────────────────────
#
# `TRAMO-1 §4·E2`: *turno real con tool nativa real (bash + fs), resultado
# aplanado, re-entrada*. Acredita `C4`·`C5`·`C6` por el camino de producción
# entero: `create_runtime` → `create_tools` (nativas, no fakes) → `ToolPool` del
# turno → `ToolDispatcher` (schema + permisos + timeout + choke `S12`) → efecto
# REAL en disco → aplanado → re-entrada del loop.
#
# El token es un `uuid` que **sólo existe dentro de un archivo sembrado**: no está
# en el prompt, ni en el system prompt, ni en ninguna descripción. Si el modelo lo
# cita, es porque `bash` corrió de verdad y su stdout volvió aplanado (`L09`: se
# verifica el cable, no el catálogo). Y no basta con que lo cite: `write_file`
# tiene que haber dejado el archivo EN DISCO, que es el efecto que ninguna
# narración puede fingir.
#
# El `fs` se inyecta confinado a `tmp_path` por la costura real
# (`RuntimeConfig.fs`) — el default seguro confina a `cwd()` y rechazaría escribir
# ahí. Esa misma costura es la que `E7` ataca por el lado NEGATIVO.

@_needs_azure
async def test_e2_real_turn_with_real_native_tools_bash_and_fs(tmp_path):
    """bash lee un token que sólo está en disco; write_file lo deja en otro archivo."""
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    code = f"EXP-{uuid.uuid4().hex[:8].upper()}"
    seeded = tmp_path / "expediente.txt"
    seeded.write_text(f"codigo de verificacion: {code}\n", encoding="utf-8")
    out = tmp_path / "copia.txt"

    probe = ModelSeamProbe(_build_caller(
        "Trabajas con herramientas reales sobre un sistema de archivos. Usa la herramienta "
        "bash para leer archivos con cat, y la herramienta write_file para escribirlos. "
        "Haz exactamente lo que se te pida, un paso por herramienta, y termina respondiendo "
        "solo con el codigo que hayas leido."
    ))
    runtime = _runtime(
        tmp_path, probe, (), Scope("scope-e2"),
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
        initial_allowed_tools=["bash", "write_file"],
    )

    task_id = await runtime.dispatch(RuntimeTask(
        prompt=(
            f"1) Con la herramienta bash, ejecuta: cat {seeded}\n"
            f"2) Con la herramienta write_file, escribe en la ruta {out} exactamente el "
            "codigo de verificacion que acabas de leer, y nada mas.\n"
            "3) Dime ese codigo."
        ),
        description="gate-e2-tools-nativas-reales",
        session_id=f"sess-E2-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    result = runtime.result(task_id) or ""
    assert runtime.status(task_id) is TaskStatus.COMPLETED, result

    # 1. `bash` corrió de VERDAD: el token sólo estaba en disco, y cruzó el cable del
    #    modelo como resultado de tool. Sin esto, citarlo sería adivinarlo.
    payload = probe.wire_payload()
    assert code in payload, (
        f"el stdout de bash no volvió aplanado al modelo: {payload[-1500:]}"
    )

    # 2. `write_file` produjo el EFECTO real — lo que ninguna narración finge.
    assert out.exists(), f"write_file no escribió en disco: {sorted(p.name for p in tmp_path.iterdir())}"
    assert code in out.read_text(encoding="utf-8")

    # 3. re-entrada: tras el resultado de la tool el loop volvió al modelo, y la
    #    respuesta final del turno depende de lo que la tool devolvió.
    assert code in result, f"el turno no re-entró con el resultado de la tool: {result!r}"

    # 4. hubo MÁS de una llamada al modelo — un turno de una sola pasada no pudo
    #    haber despachado tool y luego respondido con su salida.
    assert len(probe.calls) >= 2, f"no hubo re-entrada: {len(probe.calls)} llamada(s) al modelo"


# ──────────────────────────────────────────────────────────────────────────────
# E2·b · el INVARIANTE DEL POOL ÚNICO, sobre el ctx de producción
# ──────────────────────────────────────────────────────────────────────────────
#
# `TRAMO-1 §2·C5`: *anuncio y ejecución resuelven del MISMO objeto* ⇒ diferida =
# **visibilidad, no disponibilidad**. Es la pieza que impide que vuelva el modo de
# fallo de `FIND-EXEC1`/`S19`: dos caminos (uno para anunciar, otro para ejecutar)
# que pueden divergir y de hecho divergen.
#
# No lleva `@_needs_azure` **a propósito**: no necesita modelo, así que corre
# siempre y el gate no puede acreditarse con esta pieza saltada.
#
# Se mide sobre el ctx REAL que el runtime compone, capturado por la costura de
# producción `root_context_modifier` — no sobre un `ToolUseContext` fabricado aquí.

async def test_e2b_unique_pool_deferred_is_visibility_not_availability(tmp_path):
    """Una tool diferida NO se anuncia y SÍ se despacha — del mismo pool."""
    from agentic_runtime.tools.dispatcher import ToolDispatcher

    code = f"POOL-{uuid.uuid4().hex[:8].upper()}"

    class _DeferredWitness:
        name = "consultar_expediente_diferido"
        description = "Consulta diferida."
        input_schema = {"type": "object", "properties": {}}
        category = ToolCategory.UTILITY
        requires_permission = False
        safe_for_background = True
        timeout_seconds = 10.0
        deferred = True  # `S26`: fuera del anuncio hasta que ToolSearch la descubra

        async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
            return ToolResult(tool_name=self.name, output=code)

    captured: dict[str, Any] = {}

    def _capture_ctx(ctx: ToolUseContext, task: Any) -> ToolUseContext:
        captured["ctx"] = ctx
        return ctx

    class _OneShotCaller:
        """Caller mínimo: el turno no necesita modelo real para medir el POOL.

        Lo que se mide aquí es el ensamblado del pool y la resolución del
        dispatcher sobre el ctx de producción; el turno real con modelo es `E2`.
        """

        def supports_native_tool_search(self, model_id: str = "") -> bool:
            return False

        async def complete(self, messages, tools, *, stop=None, **kwargs):
            captured["announced"] = [t.get("name") for t in tools]

            async def _gen():
                from agentic_runtime.contracts.events import DoneEvent
                yield DoneEvent(stop_reason="end_turn")

            return _gen()

    runtime = _runtime(
        tmp_path, _OneShotCaller(), (_DeferredWitness(),), Scope("scope-e2b"),
        root_context_modifier=_capture_ctx,
    )
    task_id = await runtime.dispatch(RuntimeTask(
        prompt="hola",
        description="gate-e2b-pool-unico",
        session_id=f"sess-E2b-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    ctx = captured.get("ctx")
    assert ctx is not None, "no se capturó el ctx de producción"
    announced = captured.get("announced")
    assert announced is not None, "el turno no llegó a llamar al modelo"

    # 1. VISIBILIDAD: la diferida no se anunció...
    assert "consultar_expediente_diferido" not in announced, (
        f"la tool diferida se anunció: {announced}"
    )
    # ...pero el anuncio NO está vacío: si lo estuviera, (1) sería trivial.
    assert "bash" in announced, f"el anuncio no trae las nativas: {announced}"

    # 2. DISPONIBILIDAD: y aun así se resuelve y ejecuta desde ese MISMO pool.
    r = await ToolDispatcher().dispatch(
        tool_name="consultar_expediente_diferido", tool_input={}, ctx=ctx,
    )
    assert r.is_error is False, r.output
    assert r.output == code

    # 3. mismo OBJETO, no dos pools equivalentes: lo que se anunció y lo que se
    #    despachó salieron de `ctx.tool_pool`.
    assert ctx.tool_pool.find("consultar_expediente_diferido", ctx.permission_context) is not None


# ──────────────────────────────────────────────────────────────────────────────
# E7 · CONFINAMIENTO — la NEGATIVA del tramo
# ──────────────────────────────────────────────────────────────────────────────
#
# `TRAMO-1 §4·E7`: *confinamiento: traversal/symlink/allow-set rechazados*.
# Acredita `C6` y es lo que lo promueve **G2→G1**: la ficha lo tenía `existe-fiel
# por lectura, no corrido`, y leer no es correr.
#
# Tres piezas, porque cada una sola es satisfacible sin que el confinamiento sirva:
#
#   · `E7·a` **mecanismo** — las cuatro formas de salirse rebotan en `ctx.fs`.
#   · `E7·b` **la costura `S15` es load-bearing** — `bash` va al backend inyectado,
#     no al host: si `exec_env` no estuviera cableado, el comando correría igual y
#     nadie lo notaría (es el modo de fallo de `FIND-EXEC1`, otra vez).
#   · `E7·c` **extremo a extremo, NEGATIVA real** — un secreto vive fuera de las
#     raíces y el modelo, con tools reales, no consigue traerlo. Lo que se asevera
#     es que el token **no aparece en ningún sitio**: ni en la respuesta, ni en el
#     cable del modelo. Una negativa que sólo mirase `is_error` sería verde también
#     con un runtime que no hace nada.
#
# `E7·a`/`E7·b` no llevan `@_needs_azure`: no necesitan modelo y por tanto el gate
# no puede acreditarse con ellas saltadas.

def test_e7a_negative_confinement_rejects_traversal_symlink_and_outside_allow_set(tmp_path):
    """Las cuatro formas de salirse del allow-set rebotan en la costura `S14`."""
    from agentic_runtime.tools.fs_env import ConfinedFilesystem, PathOutsideWorkspace

    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "fuera"
    outside.mkdir()
    (outside / "secreto.txt").write_text("no-debe-salir", encoding="utf-8")

    fs = ConfinedFilesystem(roots=[workspace], write_roots=[workspace])

    # 1. traversal léxico
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(workspace / ".." / "fuera" / "secreto.txt"), for_write=False)

    # 2. absoluto fuera del allow-set
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(outside / "secreto.txt"), for_write=False)

    # 3. symlink que apunta fuera — el chequeo mira también la forma con symlinks
    #    resueltos, así que no se evade creando el enlace DENTRO del workspace.
    link = workspace / "atajo.txt"
    link.symlink_to(outside / "secreto.txt")
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(link), for_write=False)

    # 4. allow-set de ESCRITURA más estrecho que el de lectura: leer sí, escribir no.
    solo_lectura = tmp_path / "ro"
    solo_lectura.mkdir()
    split = ConfinedFilesystem(roots=[workspace, solo_lectura], write_roots=[workspace])
    assert split.resolve(str(solo_lectura / "x.txt"), for_write=False)
    with pytest.raises(PathOutsideWorkspace):
        split.resolve(str(solo_lectura / "x.txt"), for_write=True)

    # 5. `FIND-C6-1` (regresión): un token RELATIVO se autoriza expandido contra el
    #    root y debe DEVOLVERSE expandido. Devolverlo crudo hacía que la tool lo
    #    abriera contra el cwd del proceso: pasaba el gate y escribía fuera.
    relativo = fs.resolve("notas.txt", for_write=True)
    assert relativo.is_absolute(), f"token relativo devuelto sin expandir: {relativo!r}"
    assert relativo == workspace / "notas.txt"


async def test_e7d_clone_repository_does_not_leak_the_host_path_that_git_prints(tmp_path):
    """`S12`, 4º punto de emisión: la ruta host la imprime **git**, no el runtime.

    `clone_repository` pasa `str(dest)` en el `argv`, así que el stdout de git trae
    `Cloning into '/ruta/host/absoluta/…'` y ese stdout se devuelve al modelo. Se
    encontró abriendo los 18 módulos de `tools/native/`: la ronda anterior sólo había
    abierto 11 y firmó «los 3 puntos que emiten ruta host, y sólo esos», que era falso.

    No hay red: se clona contra un puerto cerrado. Git imprime el destino ANTES de
    fallar, que es exactamente el caso que filtra.
    """
    from agentic_runtime.tools.fs_env import ConfinedFilesystem
    from agentic_runtime.tools.native.clone_repository import CloneRepositoryTool

    workspace = tmp_path / "ws"
    workspace.mkdir()

    class _MaskingPresentation:
        """Lo que hará el integrador (`agentic_code`/`agentic_assistant`): host → fake."""

        def to_llm(self, host_path: Path) -> str:
            return f"/workspace/{Path(host_path).name}"

        def sanitize_output(self, text: str) -> str:
            return text

    ctx = ToolUseContext(
        session_id="sess-e7d",
        fs=ConfinedFilesystem(roots=[workspace], write_roots=[workspace]),
        presentation=_MaskingPresentation(),
    )

    r = await CloneRepositoryTool().execute(
        {"repository": "https://127.0.0.1:1/acme/demo.git"}, ctx
    )

    # Control positivo: si git no llegó a imprimir el destino, el test no prueba nada.
    assert "Cloning into" in r.output, f"git no imprimió el destino: {r.output!r}"
    assert "/workspace/demo" in r.output
    assert str(workspace) not in r.output, f"ruta host filtrada al modelo: {r.output!r}"


async def test_e7e_worktree_goes_through_the_seams_instead_of_around_them(tmp_path):
    """`S15`+`S14`+`S12` en `EnterWorktree`/`ExitWorktree`, las tres esquivadas a la vez.

    La versión anterior lanzaba git con `asyncio.create_subprocess_exec` **directo** (con
    un `BwrapExecEnvironment` inyectado, `bash` quedaba aislado y git no), componía el
    destino a mano sin pasar por ningún allow-set, y interpolaba la ruta host cruda en el
    `output`. `E7b` no lo cazaba porque sólo acreditaba `bash`.

    El espía **delega** en el backend real: git corre de verdad, así que lo que se acredita
    es el cableado, no un mock que diga que sí.
    """
    from agentic_runtime.tools.exec_env import LocalExecEnvironment, ShellResult
    from agentic_runtime.tools.fs_env import ConfinedFilesystem
    from agentic_runtime.tools.native.worktree import (
        EnterWorktreeTool,
        ExitWorktreeTool,
    )

    workspace = tmp_path / "ws"
    workspace.mkdir()
    for argv in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "gate@example.invalid"],
        ["git", "config", "user.name", "gate"],
        ["git", "commit", "-q", "--allow-empty", "-m", "root"],
    ):
        setup = await LocalExecEnvironment().run_argv(argv, cwd=str(workspace), timeout=30.0)
        assert setup.returncode == 0, f"{argv}: {setup.output}"

    seen: list[list[str]] = []

    class _SpyExecEnv:
        """Delega en el backend real y anota lo que pasó por la costura."""

        def __init__(self) -> None:
            self._inner = LocalExecEnvironment()

        async def run_shell(self, command: str, *, timeout: float) -> ShellResult:
            raise AssertionError("worktree no debe pasar por `sh -c`: el nombre viene del modelo")

        async def run_argv(self, argv, *, cwd=None, timeout: float) -> ShellResult:
            seen.append(list(argv))
            return await self._inner.run_argv(argv, cwd=cwd, timeout=timeout)

    class _MaskingPresentation:
        def to_llm(self, host_path: Path) -> str:
            return f"/workspace/{Path(host_path).name}"

        def sanitize_output(self, text: str) -> str:
            return text

    ctx = ToolUseContext(
        session_id="sess-e7e",
        fs=ConfinedFilesystem(roots=[workspace], write_roots=[workspace]),
        presentation=_MaskingPresentation(),
        exec_env=_SpyExecEnv(),
    )

    enter = await EnterWorktreeTool().execute({"name": "demo"}, ctx)
    assert enter.is_error is False, enter.output

    # `S15`: git fue por la costura, no por un subproceso propio.
    assert ["git", "worktree", "add", "-b", "worktree/demo", ".worktrees/demo"] in seen, seen
    # `S14`: el worktree cayó DENTRO del write-root, y existe de verdad.
    assert (workspace / ".worktrees" / "demo").is_dir()
    # `S12`: la ruta host no viaja al modelo.
    assert "/workspace/demo" in enter.output
    assert str(workspace) not in enter.output, f"ruta host filtrada: {enter.output!r}"

    assert enter.context_modifier is not None
    ctx = enter.context_modifier(ctx)

    exit_r = await ExitWorktreeTool().execute({"action": "remove"}, ctx)
    assert exit_r.is_error is False, exit_r.output
    assert str(workspace) not in exit_r.output, f"ruta host filtrada: {exit_r.output!r}"
    assert not (workspace / ".worktrees" / "demo").exists()


async def test_e7b_bash_goes_through_the_injected_exec_env_not_the_host(tmp_path):
    """`S15` load-bearing: el backend inyectado por `RuntimeConfig` es el que corre."""
    from agentic_runtime.tools.exec_env import ShellResult

    token = f"FAKE-{uuid.uuid4().hex[:8].upper()}"
    seen: list[str] = []

    class _FakeExecEnv:
        async def run_shell(self, command: str, *, timeout: float) -> ShellResult:
            seen.append(command)
            return ShellResult(output=token, returncode=0)

    captured: dict[str, Any] = {}

    def _capture_ctx(ctx: ToolUseContext, task: Any) -> ToolUseContext:
        captured["ctx"] = ctx
        return ctx

    class _NoopCaller:
        def supports_native_tool_search(self, model_id: str = "") -> bool:
            return False

        async def complete(self, messages, tools, *, stop=None, **kwargs):
            async def _gen():
                from agentic_runtime.contracts.events import DoneEvent
                yield DoneEvent(stop_reason="end_turn")

            return _gen()

    runtime = _runtime(
        tmp_path, _NoopCaller(), (), Scope("scope-e7b"),
        exec_env=_FakeExecEnv(),
        initial_allowed_tools=["bash"],
        root_context_modifier=_capture_ctx,
    )
    task_id = await runtime.dispatch(RuntimeTask(
        prompt="hola", description="gate-e7b-exec-env", session_id=f"sess-E7b-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    ctx = captured["ctx"]
    from agentic_runtime.tools.dispatcher import ToolDispatcher

    # Un comando que en el host REAL produciría otra cosa: si el resultado es el
    # token del fake, es que no tocó el host.
    r = await ToolDispatcher().dispatch(
        tool_name="bash", tool_input={"command": "echo host-real"}, ctx=ctx,
    )
    assert r.is_error is False, r.output
    assert r.output == token, f"bash no fue por el backend inyectado: {r.output!r}"
    assert seen == ["echo host-real"], f"el comando no llegó verbatim al backend: {seen}"


@_needs_azure
async def test_e7c_negative_end_to_end_the_model_cannot_read_outside_its_roots(tmp_path):
    """NEGATIVA real: el secreto vive fuera de las raíces y no cruza por ningún cable."""
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "fuera"
    outside.mkdir()
    secret = outside / "secreto.txt"
    token = f"SECRETO-{uuid.uuid4().hex[:8].upper()}"
    secret.write_text(f"codigo: {token}\n", encoding="utf-8")

    # Señuelo DENTRO del workspace: prueba que las fs-tools funcionan en esta corrida.
    # Sin él, «no leyó el secreto» sería cierto también si las tools estuvieran rotas.
    bait = workspace / "permitido.txt"
    bait_token = f"PERMITIDO-{uuid.uuid4().hex[:8].upper()}"
    bait.write_text(f"codigo: {bait_token}\n", encoding="utf-8")

    probe = ModelSeamProbe(_build_caller(
        "Trabajas con herramientas de archivos reales. Usa read_file para leer rutas. "
        "Si una lectura falla, informa del error y sigue con lo que si puedas leer. "
        "Termina diciendo los codigos que hayas conseguido leer."
    ))
    runtime = _runtime(
        tmp_path, probe, (), Scope("scope-e7c"),
        # El allow-set NO incluye `outside`, aunque esté bajo el mismo tmp_path.
        fs=ConfinedFilesystem(roots=[workspace], write_roots=[workspace]),
        initial_allowed_tools=["read_file", "write_file"],
    )

    task_id = await runtime.dispatch(RuntimeTask(
        prompt=(
            f"Lee con read_file estos dos archivos y dime los codigos que contienen:\n"
            f"1) {bait}\n"
            f"2) {secret}\n"
        ),
        description="gate-e7c-confinamiento-negativo",
        session_id=f"sess-E7c-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    result = runtime.result(task_id) or ""
    assert runtime.status(task_id) is TaskStatus.COMPLETED, result
    payload = probe.wire_payload()

    # 1. control POSITIVO: dentro de las raíces las fs-tools sí funcionan en esta
    #    misma corrida. Sin esto, (2) sería verde con un runtime inerte.
    assert bait_token in payload, (
        f"ni siquiera leyó lo permitido: las fs-tools no corrieron. {payload[-1500:]}"
    )

    # 2. la NEGATIVA: el secreto de fuera no cruzó NINGÚN cable.
    assert token not in payload, "el contenido de fuera del allow-set llegó al modelo"
    assert token not in result, "el contenido de fuera del allow-set llegó a la respuesta"

    # 3. y el rechazo fue explícito, no un silencio: la tool devolvió el error de
    #    confinamiento al modelo.
    assert "outside the allowed" in payload, (
        f"no hubo rechazo explícito de confinamiento en el turno: {payload[-1500:]}"
    )
