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

import asyncio
import contextlib
import functools
import http.server
import json
import os
import random
import ssl
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, ClassVar

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


# ──────────────────────────────────────────────────────────────────────────────
# E2·c/E2·d/E7·f · LAS 18 TOOLS NATIVAS: censo, anuncio, selección por el LLM y
# no-escape de la costura
# ──────────────────────────────────────────────────────────────────────────────
#
# Por qué existe este bloque: el barrido de las 18 tools nativas de la 5ª ventana
# se firmó con **grep + una tabla de conteos** y la frase «nada que ajustar». Eso
# es `D-05` al revés (grep como fuente de veredicto) y `L09` (cablear ≠ existir).
# Aquí el barrido se MECANIZA y CORRE, que es lo único que lo convierte en prueba.
#
# El censo se congela a propósito en literal en vez de derivarse del registry: si
# se derivara del mismo objeto que se está midiendo, el test sería una tautología
# y una tool nueva entraría sin que nadie la barriera.

#: 18 MÓDULOS nativos → 25 tools registradas. Censo congelado (`create_tools`).
_NATIVE_CENSUS = frozenset({
    "Agent", "AskUserQuestion", "Config", "Edit", "EnterPlanMode", "EnterWorktree",
    "ExitPlanMode", "ExitWorktree", "Sleep", "TaskCreate", "TaskGet", "TaskList",
    "TaskOutput", "TaskStop", "TaskUpdate", "TodoWrite", "ToolSearch", "WebFetch",
    "WebSearch", "bash", "clone_repository", "glob", "grep", "read_file", "write_file",
})


def test_e2c_the_native_census_is_exactly_what_the_factory_registers():
    """Ancla del barrido: 25 tools en 18 módulos, ni una menos.

    Si alguien añade una tool nativa y no la barre, este test se pone ROJO y le
    obliga a darle una entrada en `_TOOL_INPUTS` (abajo) — es decir, a barrerla.
    """
    from agentic_runtime.tools.factory import create_tools

    registered = {t.name for t in create_tools().all_tools()}
    assert registered == set(_NATIVE_CENSUS), (
        f"censo desincronizado: sobran {sorted(registered - _NATIVE_CENSUS)}, "
        f"faltan {sorted(_NATIVE_CENSUS - registered)}"
    )
    modules = {type(t).__module__.rsplit(".", 1)[-1] for t in create_tools().all_tools()}
    assert len(modules) == 18, f"18 módulos nativos, medidos {len(modules)}: {sorted(modules)}"


async def test_e2c_the_production_pool_announces_the_whole_census(tmp_path):
    """`S16`+pool+`S26`: las nativas llegan al ANUNCIO por el camino de producción.

    No basta con que el factory las registre: entre el registry y el modelo están
    el filtro por kind, el deny, `_restrict_to_agent_tools` y la estrategia de
    diferidas. Esto mide el extremo que el modelo ve de verdad.

    **Hallazgo de la primera corrida, convertido en invariante:** la primera
    versión aseveraba «las 25 siempre» y se puso ROJA por `ToolSearch`. No es un
    fallo: `deferred_strategy.py:64-66` la omite a propósito cuando no hay ninguna
    diferida en el pool («sin diferidas, no hay nada que buscar»), igual que el
    canónico. Así que se aseveran **las dos ramas** — que es más fuerte que lo que
    yo había escrito: 24 SIEMPRE, y `ToolSearch` **si y sólo si** hay diferidas.
    """
    from agentic_runtime.contracts.events import DoneEvent

    always = _NATIVE_CENSUS - {"ToolSearch"}

    class _CensusCaller:
        def __init__(self) -> None:
            self.announced: set[str] = set()

        def supports_native_tool_search(self, model_id: str = "") -> bool:
            return False

        async def complete(self, messages, tools, *, stop=None, **kwargs):
            self.announced = {t.get("name") for t in tools}

            async def _gen():
                yield DoneEvent(stop_reason="end_turn")

            return _gen()

    class _DeferredWitness:
        name = "censo_diferida"
        description = "Diferida de control."
        input_schema = {"type": "object", "properties": {}}
        category = ToolCategory.UTILITY
        requires_permission = False
        safe_for_background = True
        timeout_seconds = 10.0
        deferred = True

        async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
            return ToolResult(tool_name=self.name, output="ok")

    async def _announce(extras: tuple, tag: str) -> set[str]:
        caller = _CensusCaller()
        runtime = _runtime(tmp_path / tag, caller, extras, Scope(f"scope-e2c-{tag}"))
        task_id = await runtime.dispatch(RuntimeTask(
            prompt="hola",
            description=f"gate-e2c-censo-{tag}",
            session_id=f"sess-E2c-{tag}-{uuid.uuid4().hex}",
        ))
        await runtime._task_registry.get(task_id).asyncio_task
        assert caller.announced, "el turno no llegó a llamar al modelo"
        return caller.announced

    # Rama A — sin diferidas en el pool.
    plain = await _announce((), "plain")
    assert always <= plain, (
        f"tools nativas que NO llegan al anuncio: {sorted(always - plain)}"
    )
    assert "ToolSearch" not in plain, (
        "`ToolSearch` se anuncia sin haber ninguna diferida que buscar"
    )

    # Rama B — con una diferida: aparece ToolSearch, y la diferida NO se anuncia.
    with_deferred = await _announce((_DeferredWitness(),), "deferred")
    assert always <= with_deferred, (
        f"tools nativas que NO llegan al anuncio: {sorted(always - with_deferred)}"
    )
    assert "ToolSearch" in with_deferred, (
        "hay una diferida en el pool y `ToolSearch` no se anunció: es inalcanzable"
    )
    assert "censo_diferida" not in with_deferred, "una diferida no descubierta no se anuncia"


#: Escapes MEDIDOS corriendo (no inferidos) en el barrido de las 25, con motivo y
#: destino. **22 de 25 pasan por la costura; estas 3 no.**
#:
#: ⚠ **Re-medido tras `FIND-E7F-1` (6ª ventana), y el número cambió.** Lo anterior
#: decía «23 de 25 … estas 2» y estaba MAL: `clone_repository` recibía `url`/`destination`
#: cuando su schema declara `repository`/`directory`, así que volvía en la primera línea
#: (`repository es obligatorio`) sin llegar nunca a `asyncio.create_subprocess_exec`. Con la
#: entrada correcta el barrido lo caza en el acto. No es un escape nuevo: `clone_repository.py`
#: lo declara en su docstring («decisión A: el `git clone` corre FUERA del sandbox, como
#: subproceso privilegiado del runtime con red») desde que existe. Lo nuevo es que **está
#: medido**, que es justo lo que el barrido decía hacer y no hacía. Que un escape declarado
#: en el fuente pasara tres ventanas sin aparecer en la tabla de escapes es la demostración
#: de que la tabla no medía: `L09`, verificar el cableado y no la existencia.
#:
#: `clone_repository` NO se paga aquí por el mismo motivo que las otras dos: sacarlo por
#: `S15` lo dejaría sin red bajo `BwrapExecEnvironment` (`--unshare-all`) y por tanto
#: inservible, y la política de red es `09·F3`, arriba de la LÍNEA DE CORTE del tramo 1.
#:
#: `WebFetch`/`WebSearch` llaman `urllib.request.urlopen` **directo**, en el proceso
#: del runtime y sobre la red del host. Es la MISMA forma que tenía `worktree.py`
#: con git: un integrador que inyecte `BwrapExecEnvironment` (`--unshare-all`, sin
#: red) deja `bash` genuinamente aislado y estas dos siguen saliendo a Internet, con
#: la URL elegida por el MODELO y sin guarda de SSRF (`169.254.169.254`, `127.0.0.1:*`).
#:
#: **Por qué NO se paga aquí, y por qué eso no es `declaración-como-pago`:** el
#: canónico ubica la política de red en las reglas de permiso `WebFetch(domain:*)`,
#: que el `sandbox-adapter` deriva a `allowedDomains`/`deniedDomains` (`09·F3`). Esas
#: dos piezas —`09·F3` política de sandbox y `S17 PermissionGate`— están **arriba de
#: la LÍNEA DE CORTE** del tramo 1, enteras y nombradas, y `C6` las excluye por su
#: nombre («quedan fuera: … política de sandbox (`09·F3`)»). Estaban diferidas ANTES
#: de que este barrido las encontrara; pagarlas aquí sería inventarme alcance.
#:
#: Lo que sí se paga es dejar de no saberlo: aquí queda MEDIDO y acotado a dos tools.
_ESCAPES_DECLARADOS: dict[str, list[str]] = {
    "WebFetch": ["red-directa"],
    "WebSearch": ["red-directa"],
    "clone_repository": ["subproceso-directo"],
}


#: Entrada mínima por tool para el barrido. Cubrir el censo ENTERO es parte del
#: contrato del test: `test_e7f` asevera que las claves == `_NATIVE_CENSUS`.
#:
#: ⚠ **`FIND-E7F-1`, pagado aquí.** La versión anterior de esta tabla pasaba claves
#: que NO eran las del schema en cuatro entradas —`read_file`/`write_file` recibían
#: `file_path` y declaran `path`; `Config` iba vacía y declara `setting` requerido;
#: `clone_repository` recibía `url`/`destination` y declara `repository`/`directory`—
#: y el `except Exception` del barrido se tragaba el `KeyError`/el `is_error` de vuelta
#: temprana. Resultado: **4 de 25 no cruzaban la puerta** y el barrido salía verde
#: igual, así que el «23 de 25 pasan por la costura» que se firmó con esa tabla no
#: medía lo que decía. Dos entradas más estaban mal sin que nadie las hubiera nombrado
#: (`TaskCreate` mandaba `prompt`, que no existe en su schema, y `TaskUpdate` mandaba
#: `status`, tampoco): ésas sí cruzaban —las tools leen con `.get(..., default)`— pero
#: eran igual de falsas como entrada.
#:
#: Lo que impide que vuelva a pasar no es esta tabla corregida sino
#: `_assert_input_matches_schema`, que la valida contra el `input_schema` REAL de cada
#: tool ANTES de ejecutar: una clave inventada o un `required` ausente ponen el test
#: rojo en vez de convertirse en una vuelta temprana silenciosa.
def _tool_inputs(ws: Path, seeded: Path) -> dict[str, dict]:
    return {
        "Agent": {"description": "x", "prompt": "y"},
        "AskUserQuestion": {"questions": [{
            "question": "¿q?", "header": "h", "multiSelect": False,
            "options": [{"label": "a", "description": "d"}, {"label": "b", "description": "d"}],
        }]},
        "Config": {"setting": "model", "value": "x"},
        "Edit": {"file_path": str(seeded), "old_string": "token", "new_string": "otro"},
        "EnterPlanMode": {},
        "EnterWorktree": {"name": "barrido"},
        "ExitPlanMode": {},
        "ExitWorktree": {"action": "keep"},
        "Sleep": {"duration": 0},
        "TaskCreate": {"subject": "s", "description": "d"},
        "TaskGet": {"task_id": "no-existe"},
        "TaskList": {},
        "TaskOutput": {"task_id": "no-existe"},
        "TaskStop": {"task_id": "no-existe"},
        "TaskUpdate": {"task_id": "no-existe", "description": "d"},
        "TodoWrite": {"todos": []},
        "ToolSearch": {"query": "select:bash", "max_results": 3},
        "WebFetch": {"url": "http://127.0.0.1:9/no-existe"},
        "WebSearch": {"query": "x"},
        "bash": {"command": "echo hola"},
        "clone_repository": {"repository": "https://example.invalid/r.git", "directory": "r"},
        "glob": {"pattern": "*"},
        "grep": {"pattern": "token"},
        "read_file": {"path": str(seeded)},
        "write_file": {"path": str(ws / "salida.txt"), "content": "c"},
    }


class _SeamEscape(Exception):
    """Una tool salió por fuera de la costura. Tipo propio, no `AssertionError`.

    La versión anterior levantaba `AssertionError` desde las trampas y el bucle hacía
    `except AssertionError: raise`, así que el barrido **moría en el primer escape** y
    no llegaba a medir los 24 restantes. Con un tipo propio, la trampa registra, el
    barrido sigue, y quien decide es la igualdad EXACTA contra `_ESCAPES_DECLARADOS`
    del final: aparecer un escape nuevo pone rojo igual, y además se ve el mapa entero.
    """


def _assert_input_matches_schema(name: str, payload: dict, schema: dict) -> None:
    """Guarda de `FIND-E7F-1`: la entrada del barrido tiene que ser la del schema.

    Dos direcciones, y las dos hacen falta:

    · falta un `required` → la tool vuelve temprano (`is_error`) o revienta con
      `KeyError`, y en ambos casos NO cruza la puerta que el barrido dice medir;
    · sobra una clave que el schema no declara → la entrada es ficción: el modelo
      real nunca la mandaría, así que lo barrido no es lo que corre en producción.

    Se valida contra `input_schema` **de la tool**, no contra una copia en el test:
    si mañana cambia el schema y la tabla no, esto se pone rojo (`L09`).
    """
    props = set((schema.get("properties") or {}).keys())
    required = set(schema.get("required") or ())
    faltan = required - set(payload)
    sobran = set(payload) - props
    assert not faltan and not sobran, (
        f"entrada del barrido incompatible con el `input_schema` de `{name}`: "
        f"faltan requeridas {sorted(faltan)}; sobran no declaradas {sorted(sobran)}. "
        "Una entrada así no cruza la puerta de la tool y convierte el barrido en un "
        "conteo de vueltas tempranas (`FIND-E7F-1`)."
    )


async def test_e7f_no_native_tool_escapes_the_exec_or_network_seam(tmp_path, monkeypatch):
    """Barrido CORRIENDO de las 25 tools: ninguna sale por fuera de la costura.

    Generaliza `E7e` de una tool a todo el censo. La trampa es la misma que cazó
    a `worktree.py`: se prohíbe el spawn directo y la red directa, y se inyecta un
    `exec_env` espía; cualquier tool que se salte `S15` explota en el acto.

    Los escapes DECLARADOS son una lista blanca con motivo y destino, no una
    excusa: si aparece uno nuevo, el test se pone rojo; si alguien PAGA uno de los
    declarados, también (la igualdad es exacta), y eso obliga a tocar el tracker.
    """
    import asyncio as _asyncio
    import urllib.request as _urlreq

    from agentic_runtime.tools.exec_env import ShellResult
    from agentic_runtime.tools.factory import create_tools
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    ws = tmp_path / "ws"
    ws.mkdir()
    seeded = ws / "expediente.txt"
    seeded.write_text("token\n", encoding="utf-8")

    inputs = _tool_inputs(ws, seeded)
    assert set(inputs) == set(_NATIVE_CENSUS), (
        "el barrido no cubre el censo — sin cubrirlo entero, es una tabla de conteos, "
        f"no un barrido. Sin entrada: {sorted(_NATIVE_CENSUS - set(inputs))}; "
        f"sobrantes: {sorted(set(inputs) - _NATIVE_CENSUS)}"
    )

    current: dict[str, str] = {}
    escapes: dict[str, set[str]] = {}

    def _record(kind: str) -> None:
        escapes.setdefault(current.get("tool", "?"), set()).add(kind)

    def _no_spawn(*a: Any, **k: Any):
        _record("subproceso-directo")
        raise _SeamEscape(f"{current.get('tool')}: subproceso FUERA de `S15`")

    def _no_net(*a: Any, **k: Any):
        _record("red-directa")
        raise _SeamEscape(f"{current.get('tool')}: red FUERA de toda costura")

    monkeypatch.setattr(_asyncio, "create_subprocess_exec", _no_spawn)
    monkeypatch.setattr(_asyncio, "create_subprocess_shell", _no_spawn)
    monkeypatch.setattr(_urlreq, "urlopen", _no_net)
    # Sin clave, `WebSearch` vuelve antes de tocar la red y el barrido no vería nada.
    monkeypatch.setenv("SERPER_API_KEY", "clave-de-barrido")

    seen_argv: list[list[str]] = []

    class _SpyExecEnv:
        """No delega: el barrido mide POR DÓNDE sale, no qué devuelve."""

        async def run_shell(self, command: str, *, timeout: float) -> ShellResult:
            seen_argv.append(["sh", "-c", command])
            return ShellResult(output="", returncode=0)

        async def run_argv(self, argv, *, cwd=None, timeout: float) -> ShellResult:
            seen_argv.append(list(argv))
            return ShellResult(output="", returncode=0)

    class _MaskingPresentation:
        def to_llm(self, host_path: Path) -> str:
            return f"/workspace/{Path(host_path).name}"

        def sanitize_output(self, text: str) -> str:
            return text

    outputs: dict[str, str] = {}
    for tool in sorted(create_tools().all_tools(), key=lambda t: t.name):
        current["tool"] = tool.name
        ctx = ToolUseContext(
            session_id="sess-e7f",
            fs=ConfinedFilesystem(roots=[ws], write_roots=[ws]),
            presentation=_MaskingPresentation(),
            exec_env=_SpyExecEnv(),
        )
        # `FIND-E7F-1`: la entrada se valida contra el schema REAL antes de ejecutar.
        # Sin esto, una entrada mal formada se convierte en vuelta temprana y el
        # barrido cuenta como «pasó por la costura» a una tool que no llegó a entrar.
        _assert_input_matches_schema(tool.name, inputs[tool.name], tool.input_schema)
        try:
            result = await tool.execute(inputs[tool.name], ctx)
            outputs[tool.name] = result.output or ""
        except _SeamEscape as exc:
            # Escape REGISTRADO (arriba, en la trampa) y barrido que continúa: quien
            # dictamina es la igualdad exacta del final, no morir en el primero.
            outputs[tool.name] = f"<escape {exc}>"
        # `KeyError`/`TypeError` ya NO se tragan: son exactamente la firma de una
        # entrada que no cruza la puerta, que es como `FIND-E7F-1` pasó desapercibido.
        # La guarda de arriba debería haberlos hecho imposibles; si aparecen, el
        # barrido está mintiendo otra vez y tiene que decirlo en voz alta.
        except (KeyError, TypeError) as exc:
            raise AssertionError(
                f"`{tool.name}` no cruzó la puerta: {type(exc).__name__}: {exc}. "
                "La entrada del barrido no es la que la tool lee (`FIND-E7F-1`)."
            ) from exc
        # Silenciado a propósito, y sólo esto: el barrido mide POR DÓNDE sale la tool,
        # no si tiene éxito. Una tool puede reventar por falta de cableado (sin
        # `task_registry`, sin runner) y aun así haber intentado escaparse — el
        # registro del escape ya ocurrió arriba. Lo que NO puede es no haber entrado.
        except Exception as exc:  # noqa: BLE001
            outputs[tool.name] = f"<excepción {type(exc).__name__}: {exc}>"

    assert {k: sorted(v) for k, v in escapes.items()} == _ESCAPES_DECLARADOS, (
        "el conjunto de tools que salen por fuera de la costura cambió. Medido: "
        + json.dumps({k: sorted(v) for k, v in escapes.items()}, ensure_ascii=False)
        + f" · declarado: {json.dumps(_ESCAPES_DECLARADOS, ensure_ascii=False)}"
    )

    # `S12` sobre TODO el censo: ninguna EMITE una ruta host que haya resuelto ella
    # misma. El eco del token que mandó el modelo NO cuenta como fuga —no le revela
    # nada que no supiera—, y descontarlo es lo que hace que la asersión signifique algo.
    #
    # Esto lo afinó una corrida, no una lectura: la primera versión marcó `Edit` y era
    # un artefacto de MI test (le pasé una ruta host como token). `file_edit.py:64/69/78`
    # devuelve `input["file_path"]` verbatim, así que bajo fake-path el modelo recibe su
    # propio `/workspace/...`. Su hermana `write_file.py:38` sí enmascara la RESUELTA.
    leaks: dict[str, str] = {}
    for name, out in outputs.items():
        echoed = {v for v in inputs[name].values() if isinstance(v, str)}
        if str(ws) in out and not any(str(ws) in e and e in out for e in echoed):
            leaks[name] = out
    assert leaks == {}, (
        "ruta host RESUELTA por la tool y filtrada al modelo: "
        + json.dumps(leaks, ensure_ascii=False)
    )


@_needs_azure
async def test_e2d_the_model_selects_native_tools_by_name_from_the_full_census(tmp_path):
    """El LLM ELIGE tools nativas del censo COMPLETO, y las elegidas producen efecto.

    `E2` acredita `bash`+`write_file` con un pool acotado por `initial_allowed_tools`.
    Aquí el modelo ve el censo entero (24 tools anunciadas) y tiene que **discriminar**:
    con 24 opciones, elegir `grep`, `read_file` y `write_file` en el orden pedido ya no
    es una tool obvia por descarte. Se separa a propósito lo ANUNCIADO (`calls[*].tools`)
    de lo ELEGIDO (`calls[*].messages`) — si se mezclaran, el anuncio haría pasar por
    «seleccionada» a una tool que el modelo nunca invocó.
    """
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    code = f"CENSO-{uuid.uuid4().hex[:8].upper()}"
    seeded = tmp_path / "expediente.txt"
    seeded.write_text(f"codigo de verificacion: {code}\n", encoding="utf-8")
    out = tmp_path / "copia.txt"

    probe = ModelSeamProbe(_build_caller(
        "Trabajas con herramientas reales sobre un sistema de archivos. Usa EXACTAMENTE "
        "la herramienta que se te nombre en cada paso, una por paso. Termina respondiendo "
        "solo con el codigo que hayas leido."
    ))
    runtime = _runtime(
        tmp_path, probe, (), Scope("scope-e2d"),
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
        initial_allowed_tools=sorted(_NATIVE_CENSUS),
    )

    task_id = await runtime.dispatch(RuntimeTask(
        prompt=(
            f"1) Con la herramienta grep, busca el patron 'codigo de verificacion' en {tmp_path}\n"
            f"2) Con la herramienta read_file, lee el archivo {seeded}\n"
            f"3) Con la herramienta write_file, escribe en {out} exactamente el codigo "
            "de verificacion que leiste, y nada mas.\n"
            "4) Dime ese codigo."
        ),
        description="gate-e2d-seleccion-desde-el-censo",
        session_id=f"sess-E2d-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    result = runtime.result(task_id) or ""
    assert runtime.status(task_id) is TaskStatus.COMPLETED, result

    # 1. El censo llegó al cable REAL del proveedor (no a un caller de mentira).
    announced = {t.get("name") for call in probe.calls for t in call["tools"]}
    always = _NATIVE_CENSUS - {"ToolSearch"}
    assert always <= announced, (
        f"tools nativas que no llegaron al anuncio real: {sorted(always - announced)}"
    )

    # 2. SELECCIÓN: sólo una `tool_call` REAL del modelo cuenta como elegida — ver
    #    `_invoked_tool_names`, que sustituye al substring que contaba menciones.
    selected = _invoked_tool_names(probe.calls)
    assert {"grep", "read_file", "write_file"} <= selected, (
        f"el modelo no seleccionó las tools pedidas del censo; vio {len(announced)} "
        f"y eligió {sorted(selected)}"
    )

    # 3. EFECTO real en disco — lo que ninguna narración finge.
    assert out.exists(), f"write_file no escribió: {sorted(p.name for p in tmp_path.iterdir())}"
    assert code in out.read_text(encoding="utf-8")

    # 4. Re-entrada: el turno volvió al modelo con el resultado de las tools.
    assert code in result, f"el turno no re-entró con el resultado: {result!r}"
    assert len(probe.calls) >= 3, f"no hubo cadena de tools: {len(probe.calls)} llamada(s)"


# ──────────────────────────────────────────────────────────────────────────────
# E2·e — la rama POSITIVA del descubrimiento: `ToolSearch` ACTIVA una diferida
# ──────────────────────────────────────────────────────────────────────────────
#
# `E2c` prueba la rama negativa (una diferida no descubierta NO se anuncia) y
# `E2b` que sigue siendo despachable. Falta la mitad que hace útil al mecanismo:
# que `ToolSearch` la **descubra** y que a partir de ahí SÍ se anuncie. Sin esto,
# lo acreditado es un mecanismo que sólo sabe esconder.
#
# ⚠ **Hallazgo declarado, y es la razón de que el sujeto haya que construirlo:**
# en el runtime **ninguna tool nativa marca `deferred`** (`grep -c "deferred = True"
# tools/native/*.py` = cero). El único sujeto del camino diferido en producción es
# MCP (`capabilities/mcp/tool_adapter.py:30`), que lo setea a mano — exactamente lo
# que `09·E1` anticipaba. Lo que difiere `WebFetch`/`WebSearch` en el canónico es
# `shouldDefer` dentro de la precedencia de `isDeferredTool` (`prompt.ts:62`), y esa
# precedencia es `GAP-TOOL3`/`09·TiR5`, **no implementada**. Así que aquí se
# CONFIGURA el runtime como el canónico lo configura —`WebFetch`/`WebSearch`
# diferidas— y se mide el ciclo entero sobre ese supuesto, declarado y no disimulado.
#
# Las dos aserciones que hacen que esto no sea un interruptor global:
#   · se descubre `WebFetch` y **sólo** `WebFetch`; `WebSearch`, diferida y no
#     seleccionada, sigue oculta en el mismo turno;
#   · el resultado de `ToolSearch` trae el **schema completo** de la descubierta,
#     que es lo que permite al modelo invocarla ya, sin esperar al anuncio.

async def test_e2e_tool_search_discovers_a_deferred_tool_and_it_becomes_announced(
    tmp_path, monkeypatch,
):
    """`S26` de ida y vuelta: oculta → `ToolSearch` → anunciada, y sólo la elegida."""
    from agentic_runtime.contracts.events import DoneEvent, ToolCallEvent
    from agentic_runtime.tools.deferred import discovered_tool_names
    from agentic_runtime.tools.native.web_fetch import WebFetchTool
    from agentic_runtime.tools.native.web_search import WebSearchTool

    # El runtime no marca ninguna nativa como diferida (ver cabecera). `monkeypatch`
    # revierte esto al salir del test — no queda estado global tocado.
    monkeypatch.setattr(WebFetchTool, "deferred", True, raising=False)
    monkeypatch.setattr(WebSearchTool, "deferred", True, raising=False)

    captured: dict[str, Any] = {}

    def _capture_ctx(ctx: ToolUseContext, task: Any) -> ToolUseContext:
        captured["ctx"] = ctx
        return ctx

    class _SearchThenStopCaller:
        """Turno 1: invoca `ToolSearch(select:WebFetch)`. Turno 2: termina.

        Sin modelo real a propósito: lo que se mide es el mecanismo de
        descubrimiento y el re-anuncio del turno siguiente. Que un modelo de verdad
        sepa llegar hasta aquí **sin que nadie se lo diga** es `E2g` — no `E2f`, que
        corre con las 24 anunciadas y por tanto nunca necesita buscar nada.
        """

        def __init__(self) -> None:
            self.announced: list[set[str]] = []
            self.messages: list[list[dict]] = []

        def supports_native_tool_search(self, model_id: str = "") -> bool:
            return False

        async def complete(self, messages, tools, *, stop=None, **kwargs):
            self.announced.append({t.get("name") for t in tools})
            self.messages.append(messages)
            first = len(self.announced) == 1

            async def _gen():
                if first:
                    yield ToolCallEvent(
                        tool_name="ToolSearch",
                        tool_input={"query": "select:WebFetch"},
                        call_id="call-e2e-1",
                    )
                # `agent_loop.py:476` re-entra SÓLO con `stop_reason == "tool_calls"`.
                yield DoneEvent(stop_reason="tool_calls" if first else "end_turn")

            return _gen()

    caller = _SearchThenStopCaller()
    runtime = _runtime(
        tmp_path, caller, (), Scope("scope-e2e"),
        root_context_modifier=_capture_ctx,
        initial_allowed_tools=sorted(_NATIVE_CENSUS),
    )
    task_id = await runtime.dispatch(RuntimeTask(
        prompt="descubre la herramienta de red",
        description="gate-e2e-descubrimiento",
        session_id=f"sess-E2e-{uuid.uuid4().hex}",
    ))
    await runtime._task_registry.get(task_id).asyncio_task

    assert len(caller.announced) >= 2, (
        f"el turno no re-entró tras ToolSearch: {len(caller.announced)} llamada(s) — "
        "sin segundo turno no hay nada que medir sobre el re-anuncio"
    )
    before, after = caller.announced[0], caller.announced[1]

    # 1. ANTES: las dos diferidas ocultas, y `ToolSearch` presente para alcanzarlas.
    assert "WebFetch" not in before, "una diferida no descubierta se anunció"
    assert "WebSearch" not in before, "una diferida no descubierta se anunció"
    assert "ToolSearch" in before, "hay diferidas y `ToolSearch` no se anunció: inalcanzables"

    # 2. DESPUÉS: la descubierta se anuncia...
    assert "WebFetch" in after, (
        f"`ToolSearch` la marcó descubierta pero el turno siguiente no la anuncia: {sorted(after)}"
    )
    # 3. ...y SÓLO ella. El descubrimiento es por tool, no un interruptor global.
    assert "WebSearch" not in after, (
        "descubrir una diferida destapó también a la otra: el descubrimiento no discrimina"
    )

    # 4. El estado de descubrimiento es exactamente el pedido.
    ctx = captured.get("ctx")
    assert ctx is not None, "no se capturó el ctx de producción"
    assert discovered_tool_names(ctx) == {"WebFetch"}, discovered_tool_names(ctx)

    # 5. El resultado de `ToolSearch` trae el SCHEMA COMPLETO — sin él, «descubierta»
    #    sería una etiqueta: el modelo sabría el nombre y no cómo llamarla.
    #    Se PARSEA en vez de buscar la cadena: el payload viaja serializado dentro
    #    del contenido del mensaje, así que un `'"WebFetch"' in wire` da falso
    #    negativo por el escapado — lo comprobé poniendo el test en rojo.
    payload = next(
        (p for p in _tool_result_payloads(caller.messages[-1])
         if isinstance(p, dict) and "matches" in p),
        None,
    )
    assert payload is not None, (
        f"el resultado de ToolSearch no viajó al modelo: "
        f"{json.dumps(caller.messages[-1], default=str)[:400]}"
    )
    match = next((m for m in payload["matches"] if m["name"] == "WebFetch"), None)
    assert match is not None, payload
    assert match["parameters"].get("properties", {}).get("url"), (
        f"la descubierta llegó sin schema invocable: {match}"
    )
    assert payload["total_deferred_tools"] == 2, (
        f"el censo de diferidas del pool no cuadra: {payload['total_deferred_tools']}"
    )


def _invoked_tool_names(calls: list[dict]) -> set[str]:
    """Tools que el modelo **invocó de verdad**, leídas de la estructura del historial.

    Antes esto se hacía con un substring (`f'"{name}"' in json.dumps(messages)`) y era
    un **falso positivo esperando**: el resultado de `ToolSearch` viaja en los mensajes
    con los nombres de sus coincidencias —señuelos incluidos— así que una tool que el
    modelo nunca llamó contaba como «elegida», y una aserción del tipo «usó alguna
    capaz» podía satisfacerse con una MENCIÓN en un payload. Medido: `E2g` reportaba
    hasta 11 de 25 elegidas por esa vía. Aquí se lee la única fuente que no admite
    confusión — `msg["tool_calls"][*]["function"]["name"]`, que es exactamente lo que
    `agent_loop.py:401-403` escribe cuando el modelo pide una tool.
    """
    names: set[str] = set()
    for call in calls:
        for msg in call["messages"]:
            for tc in msg.get("tool_calls") or ():
                name = (tc.get("function") or {}).get("name")
                if name:
                    names.add(name)
    return names


def _tool_result_payloads(messages: list[dict]) -> list[Any]:
    """Todo bloque de texto del historial que sea JSON, ya parseado.

    Deliberadamente tolerante con el ENVOLTORIO (el test mide el contenido
    descubierto, no fija la forma del mensaje de resultado — eso lo fija `E2`) y
    estricto con el CONTENIDO: sólo devuelve lo que parsea, así que el test acaba
    aseverando sobre estructura, no sobre subcadenas.
    """
    out: list[Any] = []

    def _maybe(val: Any) -> None:
        if not isinstance(val, str):
            return
        try:
            out.append(json.loads(val))
        except (ValueError, TypeError):
            pass

    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    for key in ("content", "output", "text"):
                        _maybe(block.get(key))
        else:
            _maybe(content)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# E2·f — SOLVENCIA del modelo sobre el censo: enunciado de OBJETIVO, no de tool
# ──────────────────────────────────────────────────────────────────────────────
#
# `E2d` nombra la herramienta en el enunciado («con la herramienta grep, …»): mide
# que el modelo sabe INVOCAR lo que se le dice. Esto es otra cosa y es la que falla
# en la práctica: se enuncia el **objetivo** y el modelo tiene que **elegir** entre
# las 25, conducir la tool y usar su salida. Es el modo de fallo que el usuario vio
# en `agent_core`.
#
# Tres decisiones de diseño, cada una para cerrar una forma de aprobar sin mérito:
#
#   1. **Los datos son aleatorios por corrida** (centinelas `uuid4`). Nada de lo que
#      se pide puede salir del conocimiento paramétrico del modelo ni de una corrida
#      anterior: si la respuesta trae el centinela, la tool se ejecutó y su salida se
#      consumió. El **orden** de los escenarios también se baraja.
#   2. **Se asevera el OBJETIVO, no una tool exacta**, salvo donde el enunciado deja
#      una sola opción legítima. Exigir `grep` cuando `bash`+`grep(1)` resuelve
#      igual mediría obediencia, no solvencia — y castigaría una elección correcta.
#   3. **La red de `WebSearch` va sustituida** (`urlopen` devuelve un SERP canónico
#      con el centinela). Lo que se mide aquí es *el modelo elige WebSearch, la
#      parametriza y usa lo que devuelve*, no la disponibilidad de Serper: un gate
#      que dependa de una API de pago de terceros no es un gate. El egress REAL de
#      esa tool ya está medido, y acotado, en `E7f`.
#
# La semilla se imprime en el fallo y se puede fijar con `GATE_E2F_SEED` para
# reproducir exactamente una corrida roja.

_E2F_SYSTEM = (
    "Eres un agente con herramientas reales. Elige tu la herramienta adecuada para "
    "cada objetivo; nadie te va a decir cual usar. No inventes datos: si necesitas "
    "un dato que no tienes, obtenlo con una herramienta. Responde al final con el "
    "dato pedido, sin adornos."
)


def _e2f_scenarios(tmp_path: Path, rnd: random.Random) -> list[dict]:
    """Escenarios objetivo→resultado, con carga útil aleatoria por corrida."""
    def tag(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    # 1 · BÚSQUEDA WEB. El enunciado cierra la puerta a WebFetch a propósito (no hay
    #     URL que traer), así que aquí el conjunto aceptable sí es de una sola tool.
    web_code = tag("ORBITA")
    web_topic = rnd.choice(["zarpuel", "quivandro", "melbrisa", "tandroque"])

    # 2 · BÚSQUEDA EN ARCHIVOS. Varias tools resuelven esto legítimamente.
    grep_code = tag("LEGAJO")
    haystack = tmp_path / "archivo"
    haystack.mkdir(exist_ok=True)
    for i in range(6):
        (haystack / f"nota_{i}.txt").write_text(f"linea de relleno {i}\n", encoding="utf-8")
    (haystack / f"nota_{rnd.randrange(6)}.txt").write_text(
        f"referencia interna: {grep_code}\n", encoding="utf-8",
    )

    # 3 · ESCRITURA. El efecto es verificable en disco, no en la narración.
    write_code = tag("ACTA")
    target = tmp_path / f"salida_{rnd.randrange(1000)}.txt"

    return [
        {
            "id": "web",
            "prompt": (
                f"Necesito saber cual es el numero de registro del proyecto '{web_topic}'. "
                "No lo conoces y no tienes ninguna URL: busca en la web por palabras clave "
                "y dime el numero de registro que encuentres."
            ),
            "acceptable": {"WebSearch"},
            "expect_in_answer": web_code,
            "serp": web_code,
        },
        {
            "id": "buscar-en-archivos",
            "prompt": (
                f"En el directorio {haystack} hay varios archivos. Uno contiene una "
                "'referencia interna'. Dime su valor exacto."
            ),
            "acceptable": {"grep", "bash", "glob", "read_file"},
            "expect_in_answer": grep_code,
            "serp": None,
        },
        {
            "id": "escribir",
            "prompt": (
                f"Deja constancia del identificador {write_code} guardandolo, tal cual y "
                f"sin nada mas, en el archivo {target}. Luego confirma diciendo el "
                "identificador."
            ),
            "acceptable": {"write_file", "bash", "Edit"},
            "expect_in_answer": write_code,
            "expect_file": (target, write_code),
            "serp": None,
        },
    ]


@_needs_azure
async def test_e2f_the_model_is_solvent_choosing_tools_from_goal_statements(
    tmp_path, monkeypatch,
):
    """Enunciado de objetivo → el modelo ELIGE de las 25, conduce la tool y usa su salida."""
    import urllib.request

    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    seed = int(os.getenv("GATE_E2F_SEED") or uuid.uuid4().int % (2**32))
    rnd = random.Random(seed)

    scenarios = _e2f_scenarios(tmp_path, rnd)
    rnd.shuffle(scenarios)

    monkeypatch.setenv("SERPER_API_KEY", "gate-e2f-stub")

    #: SERP sustituido — ver decisión 3 en la cabecera. `current` lo apunta al
    #: escenario en curso para que el centinela sea distinto en cada uno.
    current: dict[str, Any] = {"serp": None}

    class _StubResponse:
        def __init__(self, body: bytes) -> None:
            self._body = body

        def read(self) -> bytes:
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            return None

    def _fake_urlopen(req: Any, *a: Any, **k: Any):
        code = current["serp"]
        assert code is not None, (
            "una tool salio a la red en un escenario que no la esperaba: "
            f"{getattr(req, 'full_url', req)}"
        )
        return _StubResponse(json.dumps({"organic": [{
            "title": "Registro oficial de proyectos",
            "link": "https://example.invalid/registro",
            "snippet": f"El numero de registro asignado es {code}.",
        }]}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    fallos: list[str] = []
    elegidas_total: set[str] = set()
    for n, sc in enumerate(scenarios):
        current["serp"] = sc["serp"]
        probe = ModelSeamProbe(_build_caller(_E2F_SYSTEM))
        runtime = _runtime(
            tmp_path / f"rt_{n}", probe, (), Scope(f"scope-e2f-{n}"),
            fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
            initial_allowed_tools=sorted(_NATIVE_CENSUS),
        )
        task_id = await runtime.dispatch(RuntimeTask(
            prompt=sc["prompt"],
            description=f"gate-e2f-{sc['id']}",
            session_id=f"sess-E2f-{sc['id']}-{uuid.uuid4().hex}",
        ))
        await runtime._task_registry.get(task_id).asyncio_task

        answer = runtime.result(task_id) or ""
        status = runtime.status(task_id)
        announced = {t.get("name") for call in probe.calls for t in call["tools"]}
        selected = _invoked_tool_names(probe.calls)
        elegidas_total |= selected

        # Los datos del escenario se pasan explícitos y no se capturan del bucle:
        # una clausura sobre `sc`/`answer` funcionaría hoy (se llama en la misma
        # iteración) y mentiría en cuanto alguien acumulara los fallos para después.
        def _fail(msg: str, *, sc=sc, announced=announced, selected=selected, answer=answer) -> None:
            fallos.append(
                f"[{sc['id']}] {msg}\n"
                f"    anunciadas={len(announced)} elegidas={sorted(selected)}\n"
                f"    respuesta={answer[:200]!r}"
            )

        if status is not TaskStatus.COMPLETED:
            _fail(f"la tarea no completó ({status})")
            continue
        # El censo entero estuvo delante: la elección fue una elección, no un menú de dos.
        assert len(announced) >= 20, f"[{sc['id']}] anuncio incompleto: {sorted(announced)}"

        if not (selected & sc["acceptable"]):
            _fail(f"no eligió ninguna tool capaz de resolverlo (aceptables: {sorted(sc['acceptable'])})")
        if sc["expect_in_answer"] not in answer:
            _fail(f"el centinela {sc['expect_in_answer']} no llegó a la respuesta")
        if "expect_file" in sc:
            path, want = sc["expect_file"]
            if not path.exists():
                _fail(f"no se creó {path.name}")
            elif want not in path.read_text(encoding="utf-8"):
                _fail(f"{path.name} no contiene {want}")

    # Censo de lo que el modelo LLEGÓ A ELEGIR, acumulado. Sin esto, «eligió de las
    # 25» es una frase: lo que el test asevera es que eligió UNA capaz por escenario,
    # y cuántas tools distintas toca de verdad la batería sólo se sabe contándolas.
    print(
        f"\n[E2f] GATE_E2F_SEED={seed} · tools DISTINTAS INVOCADAS por el modelo: "
        f"{len(elegidas_total)} de las {len(_NATIVE_CENSUS)} del censo "
        f"(censo = {len(_NATIVE_CENSUS)} tools en 18 módulos): {sorted(elegidas_total)}",
    )
    assert not fallos, (
        f"SOLVENCIA: {len(fallos)}/{len(scenarios)} escenarios fallaron "
        f"(GATE_E2F_SEED={seed} para reproducir)\n" + "\n".join(fallos)
    )



# ──────────────────────────────────────────────────────────────────────────────
# E2·g — SOLVENCIA CON `ToolSearch`: el modelo descubre él solo lo que no ve
# ──────────────────────────────────────────────────────────────────────────────
#
# La pieza que faltaba, y su ausencia era un agujero de verdad:
#
#   · `E2e` prueba el MECANISMO de descubrimiento, pero la llamada a `ToolSearch`
#     la guionó un caller de mentira: el modelo no decide nada ahí.
#   · `E2f` prueba la SOLVENCIA, pero con las 24 anunciadas: no hay nada que
#     descubrir, así que `ToolSearch` nunca hace falta.
#
# Aquí se cierran las dos a la vez: **las tools capaces de resolver el objetivo se
# difieren**, y el modelo recibe un enunciado cuyo dato sólo se obtiene con una de
# ellas. Ningún paso está guionado: tiene que darse cuenta, buscar, leer el schema
# devuelto e invocar la descubierta.
#
# **Dos ramas, porque `S26` tiene dos y sólo una es la que el Azure real toma.**
# `agent_loop.py:168-186` elige por capability del provider:
#
#   · `simulada` (`supports_native_tool_search() → False`, default seguro de todo
#     provider sin search server-side): las diferidas **no se anuncian**, aparece
#     `ToolSearch`, y el descubrimiento es client-side. Es la rama que este test
#     persigue: la solvencia es del modelo.
#   · `nativa` (gpt-5/Responses, lo que devuelve el caller real): se anuncian TODAS
#     con `defer_loading=True` y **`ToolSearch` se retira** porque lo pone el
#     provider. Aquí la solvencia es de la API; lo que le toca al runtime es emitir
#     bien el flag, y eso es lo que se asevera.
#
# La rama simulada se selecciona **por su entrada documentada** — un caller que
# declara `False`, que es literalmente el caso de producción de cualquier provider
# de terceros — no parcheando la estrategia. Correr sólo la nativa habría dejado
# `ToolSearch` sin probar con modelo real para siempre, que es el agujero.
#
# Lo que impide aprobar por accidente:
#
#   · **se difiere el conjunto ENTERO de tools capaces**, no una: si difiriera sólo
#     `grep` dejando `bash` a la vista, el modelo resolvería sin tocar `ToolSearch`.
#   · **señuelos aleatorios**: cada corrida difiere además 2–3 tools del censo al
#     azar, así que `ToolSearch` tiene que DISCRIMINAR y no le vale devolver «la
#     única diferida».
#   · centinelas `uuid4` por corrida y escenarios barajados, como en `E2f`.
#   · se asevera que lo necesario **no estaba anunciado en el primer turno**: sin
#     eso, «la usó» no distinguiría descubrimiento de disponibilidad.
#
# ⚠ **LAS DOS RAMAS SE ASEVERAN IGUAL, y eso es deliberado.**
# Hubo una versión de este test que exigía la solvencia sólo en la simulada y en la
# nativa se limitaba a imprimir lo observado, con el argumento de que allí el
# mecanismo es de la API y no del runtime. Era un colchón: `FIND-E2G-1` —el
# tool-search server-side falló 2 de 6 corridas del caso `archivos`, con el modelo
# tirando de `AskUserQuestion` y devolviendo vacío, mientras la simulada resolvía 6
# de 6— es un problema **de ahora**, y un `print` dentro de un test verde no lo
# atiende: lo entierra. La rama nativa NO es ajena al runtime: es la que el runtime
# **elige** cuando el catálogo declara `native_tool_search=True`
# (`agent_loop.py:168-186`, `caller.py:151`), así que su solvencia es consecuencia
# de una decisión del sujeto. Se asevera. Si sale roja, el gate está rojo y el tramo
# no cierra — que es la verdad, no un accidente del test.
# Además se exige lo que el runtime posee sin discusión: que las diferidas viajen
# con `defer_loading=True` y que `ToolSearch` client-side se retire —
# `agentic_models` convierte ese flag y añade `{"type":"tool_search","execution":
# "server"}` (`openai_responses_shared.py:225,231-232`), leído, no supuesto.

_E2G_SYSTEM = (
    "Eres un agente con herramientas reales. Puede que la herramienta que necesitas "
    "no aparezca en la lista que ves: en ese caso usa ToolSearch para buscarla y, "
    "cuando te devuelva su schema, invocala. Elige tu las herramientas; nadie te va "
    "a decir cuales. No inventes datos: obtenlos con una herramienta. Responde al "
    "final con el dato pedido, sin adornos."
)


class _NoNativeToolSearch:
    """Caller que declara **no** tener search server-side.

    No es un doble del modelo: delega `complete` intacto en el caller real de Azure.
    Lo único que cambia es la capability que el loop consulta en
    `agent_loop.py:180`, y `False` es lo que devuelve de verdad cualquier provider
    sin `native_tool_search` (`caller.py:151`). Es decir: se elige la rama simulada
    por la puerta por la que se elige en producción.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def supports_native_tool_search(self, model_id: str = "") -> bool:
        return False

    async def complete(self, messages, tools, *, stop=None, **kwargs):
        return await self._inner.complete(messages, tools, stop=stop, **kwargs)


def _e2g_scenarios(tmp_path: Path, rnd: random.Random) -> list[dict]:
    """Como `E2f`, pero cada escenario declara el conjunto ENTERO de tools capaces
    de resolverlo — ese conjunto es el que se difiere, para que la única salida sea
    descubrirlo."""
    def tag(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    web_code = tag("PADRON")
    web_topic = rnd.choice(["zarpuel", "quivandro", "melbrisa", "tandroque"])

    grep_code = tag("SUMARIO")
    haystack = tmp_path / "gaveta"
    haystack.mkdir(exist_ok=True)
    for i in range(6):
        (haystack / f"pieza_{i}.txt").write_text(f"relleno {i}\n", encoding="utf-8")
    (haystack / f"pieza_{rnd.randrange(6)}.txt").write_text(
        f"clave de sumario: {grep_code}\n", encoding="utf-8",
    )

    return [
        {
            "id": "web",
            # `WebFetch` entra en el conjunto a diferir aunque el enunciado excluya
            # las URL: si quedara a la vista, el modelo podría inventarse una y el
            # SERP sustituido se la respondería igual — pasaría sin descubrir nada.
            "hide": {"WebSearch", "WebFetch"},
            "must_use": {"WebSearch"},
            "prompt": (
                f"Necesito el numero de padron del proyecto '{web_topic}'. No lo conoces "
                "y no tienes ninguna URL: hay que buscarlo en la web por palabras clave. "
                "Dime el numero de padron."
            ),
            "expect_in_answer": web_code,
            "serp": web_code,
        },
        {
            "id": "archivos",
            "hide": {"grep", "bash", "glob", "read_file"},
            "must_use": {"grep", "bash", "glob", "read_file"},
            "prompt": (
                f"En el directorio {haystack} hay varios archivos. Uno contiene una "
                "'clave de sumario'. Dime su valor exacto."
            ),
            "expect_in_answer": grep_code,
            "serp": None,
        },
    ]


@_needs_azure
async def test_e2g_the_model_reaches_for_tool_search_when_what_it_needs_is_hidden(
    tmp_path, monkeypatch,
):
    """El modelo llega solo hasta `ToolSearch` cuando lo que necesita no se anuncia."""
    import urllib.request

    from agentic_runtime.tools import factory as tool_factory
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    seed = int(os.getenv("GATE_E2G_SEED") or uuid.uuid4().int % (2**32))
    rnd = random.Random(seed)

    scenarios = _e2g_scenarios(tmp_path, rnd)
    rnd.shuffle(scenarios)

    monkeypatch.setenv("SERPER_API_KEY", "gate-e2g-stub")
    current: dict[str, Any] = {"serp": None}

    class _StubResponse:
        def __init__(self, body: bytes) -> None:
            self._body = body

        def read(self) -> bytes:
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            return None

    def _fake_urlopen(req: Any, *a: Any, **k: Any):
        code = current["serp"]
        assert code is not None, (
            f"una tool salio a la red donde no se esperaba: {getattr(req, 'full_url', req)}"
        )
        return _StubResponse(json.dumps({"organic": [{
            "title": "Padron oficial de proyectos",
            "link": "https://example.invalid/padron",
            "snippet": f"El numero de padron asignado es {code}.",
        }]}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    fallos: list[str] = []
    elegidas_total: set[str] = set()
    n = 0
    for sc in scenarios:
        # Señuelos fijos por escenario: las dos ramas ven exactamente el mismo
        # conjunto oculto, para que la comparación entre ellas signifique algo.
        decoys = set(rnd.sample(
            sorted(_NATIVE_CENSUS - sc["hide"] - {"ToolSearch"}), rnd.randint(2, 3),
        ))
        hidden = sc["hide"] | decoys

        for rama in ("simulada", "nativa"):
            n += 1
            current["serp"] = sc["serp"]
            caso = f"{sc['id']}/{rama}"

            with monkeypatch.context() as mp:
                # Se difiere sobre las CLASES que instancia el factory de producción,
                # no sobre un pool fabricado en el test. El `context()` lo revierte
                # al salir, para que la rama siguiente parta limpia.
                for tool in tool_factory.create_tools().all_tools():
                    if tool.name in hidden:
                        mp.setattr(type(tool), "deferred", True, raising=False)

                inner = _build_caller(_E2G_SYSTEM)
                probe = ModelSeamProbe(
                    _NoNativeToolSearch(inner) if rama == "simulada" else inner,
                )
                runtime = _runtime(
                    tmp_path / f"rt_{n}", probe, (), Scope(f"scope-e2g-{n}"),
                    fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
                    initial_allowed_tools=sorted(_NATIVE_CENSUS),
                )
                task_id = await runtime.dispatch(RuntimeTask(
                    prompt=sc["prompt"],
                    description=f"gate-e2g-{caso}",
                    session_id=f"sess-E2g-{sc['id']}-{rama}-{uuid.uuid4().hex}",
                ))
                # El await se protege a propósito: `await` sobre una tarea AJENA que
                # fue cancelada relanza `CancelledError` en el que espera sin que él
                # esté cancelado, y sin esto el caso reventaría como error opaco de
                # asyncio en vez de decir QUÉ eligió el modelo antes de morir. Ver
                # `FIND-E2G-2` en `SEAMS.md`: nada del runtime cancela
                # (`registry.py:89-92`, `arm_watchdog` es un no-op).
                cancelado = False
                try:
                    await runtime._task_registry.get(task_id).asyncio_task
                except asyncio.CancelledError:
                    cancelado = True

            answer = runtime.result(task_id) or ""
            status = runtime.status(task_id)
            first = probe.calls[0]["tools"] if probe.calls else []
            first_names = {t.get("name") for t in first}
            deferred_flagged = {t.get("name") for t in first if t.get("defer_loading")}
            selected = _invoked_tool_names(probe.calls)
            elegidas_total |= selected

            def _diag(msg: str, *, caso=caso, hidden=hidden, first_names=first_names,
                      selected=selected, answer=answer) -> str:
                return (
                    f"[{caso}] {msg}\n"
                    f"    ocultas={sorted(hidden)}\n"
                    f"    anunciadas_1er_turno={len(first_names)} elegidas={sorted(selected)}\n"
                    f"    respuesta={answer[:200]!r}"
                )

            def _fail(msg: str, *, _d=_diag) -> None:
                fallos.append(_d(msg))

            if rama == "simulada":
                # Premisa: lo que hace falta NO estaba a la vista. Sin esto, el resto
                # del test no mediría descubrimiento y habría que saberlo.
                visibles = hidden & first_names
                assert not visibles, (
                    f"[{caso}] el montaje no ocultó lo que debía ({sorted(visibles)}): "
                    "no se estaría midiendo descubrimiento"
                )
                assert "ToolSearch" in first_names, (
                    f"[{caso}] `ToolSearch` no se anunció: las diferidas son inalcanzables"
                )
            else:
                # Rama nativa: nada se oculta — se marca. Y `ToolSearch` se retira
                # porque el search lo pone el provider (`deferred_strategy.py:87-88`).
                assert hidden <= deferred_flagged, (
                    f"[{caso}] diferidas sin `defer_loading` en el cable: "
                    f"{sorted(hidden - deferred_flagged)}"
                )
                assert "ToolSearch" not in first_names, (
                    f"[{caso}] la rama nativa no debe anunciar `ToolSearch` client-side"
                )

            if cancelado:
                _fail("la tarea fue CANCELADA esperando el stream del modelo")
                continue
            if status is not TaskStatus.COMPLETED:
                _fail(f"la tarea no completó ({status})")
                continue
            if rama == "simulada" and "ToolSearch" not in selected:
                _fail("no recurrió a `ToolSearch` teniendo oculto lo que necesitaba")
            if not (selected & sc["must_use"]):
                _fail(f"no llegó a usar ninguna capaz ({sorted(sc['must_use'])})")
            if sc["expect_in_answer"] not in answer:
                _fail(f"el centinela {sc['expect_in_answer']} no llegó a la respuesta")

    print(
        f"\n[E2g] GATE_E2G_SEED={seed} · {n} casos corridos, {len(fallos)} incumplimientos"
        f" · tools DISTINTAS INVOCADAS por el modelo: {len(elegidas_total)} de las "
        f"{len(_NATIVE_CENSUS)} del censo (censo = {len(_NATIVE_CENSUS)} tools en "
        f"18 módulos): {sorted(elegidas_total)}",
    )
    assert not fallos, (
        f"SOLVENCIA CON ToolSearch: {len(fallos)} incumplimientos en {n} casos "
        f"(GATE_E2G_SEED={seed} para reproducir)\n" + "\n".join(fallos)
    )


# ══════════════════════════════════════════════════════════════════════════════
# E10 · MATRIZ FUNCIONAL DE LAS 25 — que la tool OPERE, no que el test corra
# ══════════════════════════════════════════════════════════════════════════════
#
# **Por qué existe, dicho sin adorno.** La 5ª ventana cerró con una auditoría propia
# que decía que la capa por tool acreditaba MECANISMO y no FUNCIÓN, y tenía razón:
# `E2c` prueba que las 25 se registran, `E2c'` que se anuncian, `E7f` que no se
# escapan de la costura. Ninguna de las tres prueba que la tool HAGA SU TRABAJO.
# Se podía vaciar el cuerpo de `Edit` dejando `return ToolResult(output="Edited x")`
# y el censo, el anuncio y el barrido seguían verdes los tres. Literalmente:
# **nadie había aseverado nunca que `Edit` editara**.
#
# Es `L09` —verificar el cableado, no la existencia— aplicado a la última capa que
# se había quedado sin él. Reglas de esta matriz, y son las que la hacen prueba:
#
#   1. **Se asevera el EFECTO OBSERVABLE, nunca `is_error is False`.** Un
#      `is_error` falso sólo dice que la tool no reventó. Lo que se mira es el
#      archivo en disco, el registro en el registry, el estado en `app_state`, el
#      árbol de git, los segundos de reloj. Donde el único efecto de una tool es su
#      contrato de turno (`AskUserQuestion`), se dice y se asevera ESO.
#   2. **Cableado real**: `ConfinedFilesystem` real sobre un workspace real,
#      `LocalExecEnvironment` real (subprocesos de verdad), `InMemoryTaskRegistry`
#      real, git real sobre un repo real, servidor HTTP real en `127.0.0.1` para
#      `WebFetch`, servidor HTTPS real sirviendo un repo bare para
#      `clone_repository`. Nada de dobles donde el sujeto es la tool.
#   3. **Negativas donde el modo de fallo importa**: que `Edit` no toque el archivo
#      cuando el `old_string` es ambiguo vale tanto como que lo edite cuando no lo es.
#   4. **Cierra con `set(comprobadas) == _NATIVE_CENSUS`**: ninguna se queda fuera en
#      silencio. Y `_E10_CASES` se compara con el censo ANTES de correr, así que una
#      tool nueva sin caso pone rojo en vez de colarse.
#   5. **Se recogen TODOS los fallos y se reportan juntos.** Morir en el primero
#      daría una matriz de una casilla. El `except Exception` de aquí NO silencia:
#      convierte en fallo reportado, y el test acaba rojo igual.
#
# ⚠ **Las dos substituciones que hay, declaradas, no disimuladas:**
#
#   · `WebSearch` apunta a `https://google.serper.dev` **en literal** dentro de
#     `_serper_search`: no hay costura por donde redirigirlo a un servidor local, así
#     que su peer de red va sustituido y lo que se asevera es (a) la petición que la
#     tool CONSTRUYE de verdad —método, cabecera `X-API-KEY`, cuerpo `q`/`num`— y (b)
#     el renderizado de la respuesta. Un gate que dependa de una API de pago de
#     terceros no es un gate (misma decisión que `E2f·3`). El egress REAL de esa tool
#     ya está medido y acotado en `E7f`.
#   · `ExitPlanMode` lee por `ctx.storage`, y el runtime **no envía ninguna
#     implementación concreta** de `StorageContract` (`FilesystemStorage` no tiene
#     `real_path`/`ensure_local`: son del integrador). Así que se implementa el seam
#     con E/S de disco REAL — es el contrato tal cual, no un doble que finge la lectura.
#
# **Acreditación adversarial de la propia matriz (6ª ventana).** `E10` salió verde
# 25/25 a la primera, y un verde total a la primera es indistinguible de una matriz
# que no mide nada — que es exactamente lo que `E7f` acababa de descubrir de la capa
# anterior. Así que se midió con **violación inyectada**: 7 mutaciones en 6 fuentes
# (`Edit` devuelve «Edited …» sin escribir · `write_file` escribe cadena vacía ·
# `TaskUpdate` no persiste en el registry · `TaskStop` no llama a `kill` · `Sleep`
# duerme 0 · `Config` no guarda el valor en el modifier · `WebFetch` devuelve un
# cuerpo fijo sin usar el de la red) — todas dejando el `is_error` en `False`, que es
# el modo de fallo que las capas viejas no veían. Resultado medido:
# **7 rojas de 7 inyecciones y las 18 restantes en verde** (sin falsos positivos).
# Fuentes restaurados desde copia propia y verificados con `sha256sum -c`.
#
# ⚠ **Hallazgo del montaje, y es del sujeto, no del test:** `clone_repository`
# **reescribe a `https://` cualquier URL de entrada** (`_normalize` devuelve
# `f"https://{host}/{path}.git"` aunque el esquema recibido sea `http`). Por eso este
# caso monta un TLS de verdad con certificado autofirmado en vez de un http plano:
# no es capricho del test, es la única forma de que la tool llegue a hablar con él.


class _E10Env:
    """Cableado compartido de la matriz: workspace real, repo git real, registry real."""

    def __init__(self, ws: Path, tmp: Path, monkeypatch: Any, session_id: str) -> None:
        from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry

        self.ws = ws
        self.tmp = tmp
        self.mp = monkeypatch
        self.session_id = session_id
        self.registry = InMemoryTaskRegistry()

    def tag(self, prefijo: str) -> str:
        """Centinela único por corrida: si aparece en el efecto, lo puso ESTA ejecución."""
        return f"{prefijo}-{uuid.uuid4().hex[:10].upper()}"

    def ctx(self, **overrides: Any) -> ToolUseContext:
        from agentic_runtime.tools.exec_env import LocalExecEnvironment
        from agentic_runtime.tools.fs_env import ConfinedFilesystem

        base: dict[str, Any] = {
            "session_id": self.session_id,
            "fs": ConfinedFilesystem(roots=[self.ws], write_roots=[self.ws]),
            "exec_env": LocalExecEnvironment(),
            "task_registry": self.registry,
        }
        base.update(overrides)
        return ToolUseContext(**base)

    def hermana(self, nombre: str) -> Any:
        """La tool `nombre` del pool de PRODUCCIÓN (para pares como Enter/ExitWorktree)."""
        from agentic_runtime.tools.factory import create_tools

        tool = next((t for t in create_tools().all_tools() if t.name == nombre), None)
        assert tool is not None, f"la tool hermana `{nombre}` no está en el pool"
        return tool


def _aplicar(result: Any, ctx: ToolUseContext) -> ToolUseContext:
    """Aplica el `context_modifier` como lo aplica el dispatcher. Sin esto, aseverar
    sobre `app_state` mediría lo que la tool PROMETE, no lo que el turno hace."""
    assert result.context_modifier is not None, (
        f"`{result.tool_name}` dice tener efecto de contexto y no trae `context_modifier`"
    )
    return result.context_modifier(ctx)


def _git(*argv: str, cwd: Path) -> subprocess.CompletedProcess:
    """git REAL. Identidad por env: un `git commit` sin `user.email` falla en CI limpio."""
    return subprocess.run(
        ["git", *argv],
        cwd=str(cwd),
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "gate", "GIT_AUTHOR_EMAIL": "gate@tramo1",
            "GIT_COMMITTER_NAME": "gate", "GIT_COMMITTER_EMAIL": "gate@tramo1",
        },
        check=True, capture_output=True, text=True,
    )


@contextlib.contextmanager
def _servidor_http(cuerpo: bytes):
    """Servidor HTTP REAL en `127.0.0.1`, puerto efímero. Para `WebFetch`."""

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *a: Any) -> None:
            return None

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()


@contextlib.contextmanager
def _servidor_git_https(raiz: Path, tmp: Path):
    """Repo bare servido por HTTPS real (dumb protocol) con cert autofirmado.

    TLS y no http plano **porque la tool lo obliga**: `_normalize` reescribe el esquema
    a `https://` pase lo que pase. `GIT_SSL_NO_VERIFY` lo pone el caso, no esto.
    """
    key, crt = tmp / "e10_key.pem", tmp / "e10_crt.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(key), "-out", str(crt), "-days", "1",
         "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1"],
        check=True, capture_output=True,
    )
    class _Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a: Any) -> None:
            return None

    # `partial` SOBRE la subclase, nunca al revés: `functools.partial` devuelve un
    # objeto, no una clase, y heredar de él revienta con `TypeError: the first
    # argument must be callable` al instanciar el servidor.
    handler = functools.partial(_Silencioso, directory=str(raiz))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(str(crt), str(key))
    httpd.socket = ssl_ctx.wrap_socket(httpd.socket, server_side=True)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()


# ── los 25 casos ──────────────────────────────────────────────────────────────
# Cada uno devuelve la frase de lo que dejó ASEVERADO; esa frase es la que se
# imprime como matriz al final, para que el veredicto se lea sin abrir el código.


async def _e10_bash(tool: Any, env: _E10Env) -> str:
    marca = env.tag("BASH")
    destino = env.ws / "bash.out"
    ctx = env.ctx()
    r = await tool.execute({"command": f"printf %s '{marca}' > '{destino}'"}, ctx)
    assert not r.is_error, f"bash falló: {r.output!r}"
    assert destino.read_text() == marca, (
        f"el subproceso no escribió el efecto en disco: {destino.read_text()!r}"
    )
    r2 = await tool.execute({"command": "exit 3"}, ctx)
    assert r2.is_error, "un returncode != 0 no se propagó como `is_error`"
    return "subproceso REAL: escribió el centinela en disco; rc!=0 → is_error"


async def _e10_write_file(tool: Any, env: _E10Env) -> str:
    marca = env.tag("WRITE")
    destino = env.ws / "sub" / "escrito.txt"
    ctx = env.ctx()
    r = await tool.execute({"path": str(destino), "content": marca}, ctx)
    assert not r.is_error, r.output
    assert destino.read_text() == marca, "no escribió el contenido pedido"
    fuera = env.tmp / "fuera_del_workspace.txt"
    r2 = await tool.execute({"path": str(fuera), "content": "x"}, ctx)
    assert r2.is_error, "escribió fuera del write-root sin error"
    assert not fuera.exists(), "NEGATIVA rota: el archivo fuera del workspace se creó"
    return "creó el archivo (y los padres) con el contenido exacto; fuera del root no escribe"


async def _e10_read_file(tool: Any, env: _E10Env) -> str:
    marca = env.tag("READ")
    p = env.ws / "leido.txt"
    p.write_text(f"linea0\n{marca}\nlinea2\n", encoding="utf-8")
    ctx = env.ctx()
    r = await tool.execute({"path": str(p)}, ctx)
    assert not r.is_error, r.output
    assert r.output == f"linea0\n{marca}\nlinea2", f"no devolvió el contenido: {r.output!r}"
    r2 = await tool.execute({"path": str(p), "offset": 1, "limit": 1}, ctx)
    assert r2.output == marca, f"offset/limit no recorta: {r2.output!r}"
    return "devolvió el contenido real del archivo; `offset`/`limit` recortan de verdad"


async def _e10_edit(tool: Any, env: _E10Env) -> str:
    """El agujero que nombró la auditoría: NADIE había aseverado nunca que `Edit` edite."""
    viejo, nuevo = env.tag("VIEJO"), env.tag("NUEVO")
    p = env.ws / "editado.txt"
    p.write_text(f"cabecera\n{viejo}\npie\n", encoding="utf-8")
    ctx = env.ctx()

    r = await tool.execute(
        {"file_path": str(p), "old_string": viejo, "new_string": nuevo}, ctx
    )
    assert not r.is_error, f"Edit falló: {r.output!r}"
    contenido = p.read_text(encoding="utf-8")
    assert contenido == f"cabecera\n{nuevo}\npie\n", (
        f"`Edit` NO editó el archivo como dice: {contenido!r}"
    )

    # NEGATIVA 1 — `old_string` que ya no está: error y archivo INTACTO.
    antes = p.read_text(encoding="utf-8")
    r2 = await tool.execute(
        {"file_path": str(p), "old_string": viejo, "new_string": "z"}, ctx
    )
    assert r2.is_error, "reemplazó un `old_string` inexistente"
    assert p.read_text(encoding="utf-8") == antes, "tocó el archivo en el camino de error"

    # NEGATIVA 2 — `old_string` ambiguo: error y archivo INTACTO (no edita «el primero»).
    amb = env.ws / "ambiguo.txt"
    amb.write_text("REP\nmedio\nREP\n", encoding="utf-8")
    r3 = await tool.execute(
        {"file_path": str(amb), "old_string": "REP", "new_string": "X"}, ctx
    )
    assert r3.is_error, "editó con un `old_string` que casa 2 veces"
    assert amb.read_text(encoding="utf-8") == "REP\nmedio\nREP\n", (
        "el camino de ambigüedad dejó el archivo modificado"
    )

    # NEGATIVA 3 — ruta relativa: rechazada por contrato.
    r4 = await tool.execute({"file_path": "rel.txt", "old_string": "a", "new_string": "b"}, ctx)
    assert r4.is_error, "aceptó un `file_path` relativo"
    return "EDITA de verdad (contenido nuevo en disco) y no toca el archivo en 3 negativas"


async def _e10_glob(tool: Any, env: _E10Env) -> str:
    d = env.ws / "globdir"
    d.mkdir(exist_ok=True)
    for n in ("a.py", "b.py", "c.txt"):
        (d / n).write_text("x", encoding="utf-8")
    ctx = env.ctx()
    r = await tool.execute({"pattern": "globdir/*.py"}, ctx)
    assert not r.is_error, r.output
    lineas = [ln for ln in r.output.splitlines() if ln.strip()]
    nombres = {Path(ln).name for ln in lineas}
    assert nombres == {"a.py", "b.py"}, f"no devolvió los matches reales: {nombres}"
    assert all(Path(ln).exists() for ln in lineas), (
        f"emitió rutas que no existen: {lineas}"
    )
    return "devolvió exactamente los archivos que casan y existen en disco"


async def _e10_grep(tool: Any, env: _E10Env) -> str:
    marca = env.tag("GREP")
    d = env.ws / "grepdir"
    d.mkdir(exist_ok=True)
    (d / "con.txt").write_text(f"ruido\nclave: {marca}\n", encoding="utf-8")
    (d / "silencio.txt").write_text("nada aqui\n", encoding="utf-8")
    ctx = env.ctx()
    r = await tool.execute({"pattern": marca, "path": str(d)}, ctx)
    assert not r.is_error, r.output
    assert marca in r.output, f"no encontró la línea que casa: {r.output!r}"
    assert "con.txt:2:" in r.output, f"no reporta archivo:línea: {r.output!r}"
    assert "silencio.txt" not in r.output, "reportó un archivo que no casa"
    return "encontró la coincidencia real con archivo:línea y excluyó la que no casa"


async def _e10_sleep(tool: Any, env: _E10Env) -> str:
    ctx = env.ctx()
    t0 = time.monotonic()
    r = await tool.execute({"duration": 0.25}, ctx)
    transcurrido = time.monotonic() - t0
    assert not r.is_error, r.output
    assert transcurrido >= 0.2, f"no durmió de verdad: {transcurrido:.3f}s"
    assert r.output == "Slept for 0.25 seconds.", r.output
    # El clamp inferior, medido: negativo → 0.0 y vuelve en el acto.
    t1 = time.monotonic()
    r2 = await tool.execute({"duration": -5}, ctx)
    assert time.monotonic() - t1 < 0.2, "un `duration` negativo no volvió inmediato"
    assert r2.output == "Slept for 0.0 seconds.", r2.output
    return "durmió el tiempo de reloj pedido; clamp inferior a 0.0 medido"


async def _e10_web_fetch(tool: Any, env: _E10Env) -> str:
    marca = env.tag("FETCH")
    ctx = env.ctx()
    with _servidor_http(f"<html>{marca}</html>".encode()) as puerto:
        r = await tool.execute({"url": f"http://127.0.0.1:{puerto}/x"}, ctx)
    assert not r.is_error, f"no trajo la página: {r.output!r}"
    assert marca in r.output, f"el cuerpo servido no llegó a la salida: {r.output!r}"
    ctx2 = env.ctx()
    r2 = await tool.execute({"url": "file:///etc/passwd"}, ctx2)
    assert r2.is_error and "http" in r2.output, f"aceptó un esquema no-http: {r2.output!r}"
    return "trajo por HTTP REAL el cuerpo servido en 127.0.0.1; `file://` rechazado"


async def _e10_web_search(tool: Any, env: _E10Env) -> str:
    """Peer de red SUSTITUIDO (endpoint en literal, sin costura). Ver cabecera de `E10`."""
    import urllib.request

    marca = env.tag("SERP")
    capturado: dict[str, Any] = {}

    class _Resp:
        def __init__(self, body: bytes) -> None:
            self._b = body

        def read(self) -> bytes:
            return self._b

        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            return None

    def _fake_urlopen(req: Any, *a: Any, **k: Any) -> _Resp:
        capturado["url"] = req.full_url
        capturado["method"] = req.get_method()
        capturado["headers"] = {k.lower(): v for k, v in req.header_items()}
        capturado["body"] = json.loads(req.data)
        return _Resp(json.dumps({"organic": [
            {"title": "Titulo uno", "link": "https://ej.invalid/1", "snippet": f"dice {marca}"},
            {"title": "Titulo dos", "link": "https://ej.invalid/2", "snippet": "otro"},
        ]}).encode())

    ctx = env.ctx()
    with env.mp.context() as mp:
        mp.setenv("SERPER_API_KEY", "clave-e10")
        mp.setattr(urllib.request, "urlopen", _fake_urlopen)
        r = await tool.execute({"query": "consulta", "max_results": 2}, ctx)
        assert not r.is_error, r.output
        # (a) la petición que la tool CONSTRUYE de verdad
        assert capturado["url"] == "https://google.serper.dev/search", capturado["url"]
        assert capturado["method"] == "POST", capturado["method"]
        assert capturado["headers"].get("X-api-key".lower()) == "clave-e10", capturado["headers"]
        assert capturado["body"] == {"q": "consulta", "num": 2}, capturado["body"]
        # (b) el renderizado de la respuesta
        assert "1. **Titulo uno**" in r.output, r.output
        assert "https://ej.invalid/1" in r.output and marca in r.output, r.output
        # el filtro de dominios entra en la query efectiva
        await tool.execute({"query": "q", "allowed_domains": ["a.io"]}, ctx)
        assert capturado["body"]["q"] == "(q) (site:a.io)", capturado["body"]

        mp.delenv("SERPER_API_KEY")
        r3 = await tool.execute({"query": "q"}, ctx)
        assert r3.is_error and "SERPER_API_KEY" in r3.output, r3.output
    return "construyó POST+X-API-KEY+cuerpo q/num, renderizó los resultados, y sin clave falla"


async def _e10_clone_repository(tool: Any, env: _E10Env) -> str:
    marca = env.tag("CLON")
    origen = env.tmp / "origen"
    origen.mkdir()
    (origen / "SENTINELA.txt").write_text(f"{marca}\n", encoding="utf-8")
    _git("init", "-q", "-b", "main", cwd=origen)
    _git("add", "-A", cwd=origen)
    _git("commit", "-q", "-m", "inicial", cwd=origen)

    servidos = env.tmp / "servidos"
    servidos.mkdir()
    _git("clone", "-q", "--bare", str(origen), str(servidos / "repo.git"), cwd=env.tmp)
    _git("-C", str(servidos / "repo.git"), "update-server-info", cwd=env.tmp)

    ctx = env.ctx()
    with env.mp.context() as mp:
        mp.setenv("GIT_SSL_NO_VERIFY", "1")  # cert autofirmado del servidor de prueba
        with _servidor_git_https(servidos, env.tmp) as puerto:
            r = await tool.execute(
                {"repository": f"https://127.0.0.1:{puerto}/repo.git", "directory": "clonado"},
                ctx,
            )
            assert not r.is_error, f"el clone falló: {r.output!r}"
            clonado = env.ws / "clonado"
            assert (clonado / ".git").is_dir(), "no quedó un repo git en el destino"
            assert (clonado / "SENTINELA.txt").read_text().strip() == marca, (
                "el árbol clonado no trae el contenido del origen"
            )
            r2 = await tool.execute(
                {"repository": f"https://127.0.0.1:{puerto}/repo.git", "directory": "clonado"},
                ctx,
            )
            assert r2.is_error and "ya existe" in r2.output, r2.output
    r3 = await tool.execute({"repository": "ftp://ej.invalid/x"}, env.ctx())
    assert r3.is_error, "aceptó un esquema no soportado"
    return "clonó con git REAL por HTTPS: árbol y .git en el workspace; destino ocupado → error"


async def _e10_config(tool: Any, env: _E10Env) -> str:
    marca = env.tag("CFG")
    ctx = env.ctx()
    r = await tool.execute({"setting": "model", "value": marca}, ctx)
    assert not r.is_error, r.output
    ctx = _aplicar(r, ctx)
    assert (ctx.app_state.native.get("config") or {}).get("model") == marca, (
        f"el `set` no dejó el valor en `app_state`: {ctx.app_state.native.get('config')}"
    )
    assert json.loads(r.output)["operation"] == "set"
    r2 = await tool.execute({"setting": "model"}, ctx)
    assert json.loads(r2.output)["value"] == marca, f"el `get` no lee lo escrito: {r2.output}"
    r3 = await tool.execute({"setting": ""}, ctx)
    assert r3.is_error, "aceptó un `setting` vacío"
    return "el `set` deja el valor en `app_state` y el `get` posterior lo lee"


async def _e10_todo_write(tool: Any, env: _E10Env) -> str:
    marca = env.tag("TODO")
    todos = [{"id": "1", "content": marca, "status": "pending", "priority": "high"}]
    ctx = env.ctx()
    r = await tool.execute({"todos": todos}, ctx)
    ctx = _aplicar(r, ctx)
    assert ctx.app_state.native["todos"] == todos, (
        f"la lista no quedó en `app_state`: {ctx.app_state.native.get('todos')}"
    )
    assert json.loads(r.output)["old_todos"] == [], r.output
    nuevos = [{"id": "1", "content": marca, "status": "completed", "priority": "high"}]
    r2 = await tool.execute({"todos": nuevos}, ctx)
    assert json.loads(r2.output)["old_todos"] == todos, (
        f"no reporta la lista anterior: {r2.output}"
    )
    ctx = _aplicar(r2, ctx)
    assert ctx.app_state.native["todos"] == nuevos, "el segundo write no reemplazó"
    return "escribe la lista en `app_state` y reporta la anterior en el reemplazo"


async def _e10_tool_search(tool: Any, env: _E10Env) -> str:
    from agentic_runtime.tools.deferred import discovered_tool_names
    from agentic_runtime.tools.pool import ToolPool

    class _DiferidaTestigo:
        name = "e10_diferida"
        description = "Testigo diferido de la matriz funcional."
        input_schema: ClassVar[dict] = {
            "type": "object", "properties": {"campo": {"type": "string"}},
        }
        category = ToolCategory.UTILITY
        requires_permission = False
        safe_for_background = True
        timeout_seconds = 5.0
        deferred = True

        async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
            return ToolResult(tool_name=self.name, output="ok")

    ctx = env.ctx(tool_pool=ToolPool(capability_tools=[_DiferidaTestigo()]))
    r = await tool.execute({"query": "select:e10_diferida"}, ctx)
    assert not r.is_error, r.output
    payload = json.loads(r.output)
    nombres = [m["name"] for m in payload["matches"]]
    assert nombres == ["e10_diferida"], f"no resolvió la diferida por nombre: {nombres}"
    assert payload["matches"][0]["parameters"]["properties"].get("campo"), (
        "devolvió la descubierta sin schema invocable"
    )
    assert discovered_tool_names(ctx) == {"e10_diferida"}, discovered_tool_names(ctx)
    r2 = await tool.execute({"query": "select:bash"}, env.ctx())
    assert json.loads(r2.output)["matches"] == [], "descubrió una tool que no es diferida"
    return "descubrió la diferida, devolvió su schema y marcó el estado; una no-diferida no"


async def _e10_ask_user_question(tool: Any, env: _E10Env) -> str:
    """Su efecto ES el contrato de turno: `ends_turn` y no bloquear. Se asevera eso."""
    ctx = env.ctx()
    t0 = time.monotonic()
    r = await tool.execute({"questions": [{
        "question": "¿seguimos?", "header": "rumbo",
        "options": [{"label": "si", "description": "d"}, {"label": "no", "description": "d"}],
    }]}, ctx)
    transcurrido = time.monotonic() - t0
    assert not r.is_error, r.output
    assert r.ends_turn is True, "no cedió el turno: el HITL multi-turno no arranca"
    assert transcurrido < 2.0, (
        f"BLOQUEÓ {transcurrido:.1f}s (su `timeout_seconds` es 300): la tool debe volver ya"
    )
    assert r.output.strip(), "volvió sin placeholder para el tool_result"
    return "cede el turno (`ends_turn`) y vuelve en el acto en vez de bloquear 300s"


async def _e10_agent(tool: Any, env: _E10Env) -> str:
    from agentic_runtime.execution.runner import SubagentSpec

    marca = env.tag("SUBAG")
    recibidos: list[Any] = []

    class _RunnerTestigo:
        async def run(self, spec: Any, *, background: bool = False) -> str:
            recibidos.append((spec, background))
            return f"salida del subagente {marca}"

    ctx = env.ctx(runner=_RunnerTestigo())
    r = await tool.execute({"prompt": "haz X", "description": "desc"}, ctx)
    assert not r.is_error, r.output
    assert len(recibidos) == 1, "no delegó en el runner"
    spec, background = recibidos[0]
    assert isinstance(spec, SubagentSpec), f"delegó con algo que no es `SubagentSpec`: {spec!r}"
    assert spec.prompt == "haz X" and spec.description == "desc"
    assert spec.parent_session_id == env.session_id, (
        f"no transportó el `session_id` padre: {spec.parent_session_id!r}"
    )
    assert background is False
    assert marca in r.output, f"no devolvió lo que produjo el runner: {r.output!r}"

    r2 = await tool.execute({"prompt": "x", "description": "d"}, env.ctx(runner=None))
    assert r2.is_error and "S18" in r2.output, f"sin runner no falla en voz alta: {r2.output!r}"
    r3 = await tool.execute(
        {"prompt": "x", "description": "d"}, env.ctx(runner=_RunnerTestigo(), subagent_depth=5)
    )
    assert r3.is_error and "depth" in r3.output.lower(), r3.output
    return "delegó un `SubagentSpec` real con el session_id padre y devolvió su salida"


async def _e10_enter_plan_mode(tool: Any, env: _E10Env) -> str:
    from agentic_runtime.capabilities.plan.plan_file import _PLAN_MODE_KEY

    ctx = env.ctx()
    r = await tool.execute({}, ctx)
    assert not r.is_error, r.output
    ctx = _aplicar(r, ctx)
    assert ctx.app_state.native.get(_PLAN_MODE_KEY) is True, (
        f"no dejó plan mode activo: {ctx.app_state.native}"
    )
    r2 = await tool.execute({}, env.ctx(is_subagent=True))
    assert r2.is_error, "un subagente pudo entrar en plan mode (es root-only)"
    return "deja `plan_mode=True` en `app_state`; desde subagente es error"


async def _e10_exit_plan_mode(tool: Any, env: _E10Env) -> str:
    from agentic_runtime.capabilities.plan.plan_file import (
        _PLAN_EXIT_PENDING_KEY,
        _PLAN_KEY,
        _PLAN_MODE_KEY,
    )

    marca = env.tag("PLAN")

    class _StoragePlanReal:
        """`StorageContract` con E/S de disco REAL — el runtime no trae implementación."""

        def __init__(self, raiz: Path) -> None:
            self._raiz = raiz

        def real_path(self, token: str) -> Path:
            return self._raiz / token.lstrip("/")

        async def ensure_local(self, token: str) -> Path:
            return self.real_path(token)

        async def commit(self, token: str, content: bytes, mime: str | None = None) -> str:
            p = self.real_path(token)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content)
            return token

        async def teardown(self) -> None:
            return None

    raiz = env.tmp / "plan_storage"
    storage = _StoragePlanReal(raiz)

    # NEGATIVA primero: sin plan-file en disco, error — y no toca el estado.
    ctx_vacio = env.ctx(storage=storage)
    ctx_vacio.app_state.native[_PLAN_MODE_KEY] = True
    r0 = await tool.execute({}, ctx_vacio)
    assert r0.is_error, "salió de plan mode sin plan escrito"
    assert ctx_vacio.app_state.native.get(_PLAN_MODE_KEY) is True, (
        "el camino de error ya había desactivado plan mode"
    )

    destino = raiz / "plans" / "plan.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(f"# Plan\n\n{marca}\n", encoding="utf-8")

    ctx = env.ctx(storage=storage)
    ctx.app_state.native[_PLAN_MODE_KEY] = True
    r = await tool.execute({}, ctx)
    assert not r.is_error, r.output
    assert marca in r.output, f"no leyó el plan del disco: {r.output!r}"
    assert r.ends_turn is True, "no cedió el turno para esperar aprobación"
    ctx = _aplicar(r, ctx)
    assert ctx.app_state.native.get(_PLAN_MODE_KEY) is None, "no salió de plan mode"
    assert marca in ctx.app_state.native[_PLAN_KEY], "no cacheó el plan leído"
    assert ctx.app_state.native[_PLAN_EXIT_PENDING_KEY] is True, "no armó el one-shot"
    return "leyó el plan-file REAL de disco, salió de plan mode y armó el one-shot"


async def _e10_enter_worktree(tool: Any, env: _E10Env) -> str:
    from agentic_runtime.tools.native.worktree import _WORKTREE_KEY

    nombre = "e10-enter"
    ctx = env.ctx()
    r = await tool.execute({"name": nombre}, ctx)
    assert not r.is_error, f"EnterWorktree falló: {r.output!r}"
    destino = env.ws / ".worktrees" / nombre
    assert destino.is_dir(), "no creó el directorio del worktree"
    assert (destino / ".git").exists(), "el directorio creado no es un worktree de git"
    listado = _git("worktree", "list", cwd=env.ws).stdout
    assert str(destino) in listado, f"git no lo reconoce como worktree: {listado!r}"
    ramas = _git("branch", "--list", f"worktree/{nombre}", cwd=env.ws).stdout
    assert f"worktree/{nombre}" in ramas, f"no creó la rama: {ramas!r}"
    ctx = _aplicar(r, ctx)
    assert ctx.app_state.native[_WORKTREE_KEY]["branch"] == f"worktree/{nombre}"
    r2 = await tool.execute({"name": "otro"}, ctx)
    assert r2.is_error, "permitió anidar dos sesiones de worktree"
    r3 = await tool.execute({"name": "mal nombre/../x"}, env.ctx())
    assert r3.is_error, "aceptó un nombre de rama inválido"
    return "creó un worktree de git REAL (dir + rama + `worktree list`) y guardó la sesión"


async def _e10_exit_worktree(tool: Any, env: _E10Env) -> str:
    """Se prueba el PAR: se entra con la tool real y se sale con ésta."""
    from agentic_runtime.tools.native.worktree import _WORKTREE_KEY

    nombre = "e10-exit"
    ctx = env.ctx()
    entrada = await env.hermana("EnterWorktree").execute({"name": nombre}, ctx)
    assert not entrada.is_error, f"no se pudo montar el caso: {entrada.output!r}"
    ctx = _aplicar(entrada, ctx)
    destino = env.ws / ".worktrees" / nombre
    assert destino.is_dir()

    r = await tool.execute({"action": "remove"}, ctx)
    assert not r.is_error, f"ExitWorktree falló: {r.output!r}"
    assert not destino.exists(), "dijo que lo quitó y el directorio sigue en disco"
    listado = _git("worktree", "list", cwd=env.ws).stdout
    assert nombre not in listado, f"git sigue registrando el worktree: {listado!r}"
    ctx = _aplicar(r, ctx)
    assert _WORKTREE_KEY not in ctx.app_state.native, "no limpió la sesión de worktree"

    r2 = await tool.execute({"action": "keep"}, env.ctx())
    assert r2.is_error, "salió de un worktree sin estar en ninguno"
    return "quitó el worktree del disco y del registro de git, y limpió la sesión"


async def _e10_task_create(tool: Any, env: _E10Env) -> str:
    marca = env.tag("TCREATE")
    ctx = env.ctx()
    r = await tool.execute({"subject": marca, "description": "lo que hay que hacer"}, ctx)
    assert not r.is_error, r.output
    task_id = json.loads(r.output)["task_id"]
    record = env.registry.get(task_id)
    assert record is not None, "dijo crear una tarea que el registry no tiene"
    assert record.description == f"{marca}: lo que hay que hacer", record.description
    assert record.owner_session_id == env.session_id, (
        f"no escopó la tarea a la sesión: {record.owner_session_id!r}"
    )
    r2 = await tool.execute({"subject": "s", "description": "d"}, env.ctx(task_registry=None))
    assert r2.is_error and "S19" in r2.output, r2.output
    return "registró la tarea REAL en el registry, escopada a la sesión"


async def _e10_task_get(tool: Any, env: _E10Env) -> str:
    marca = env.tag("TGET")
    rec = env.registry.register(description=marca, session_id=env.session_id)
    ajena = env.registry.register(description="ajena", session_id="otra-sesion")
    ctx = env.ctx()
    r = await tool.execute({"task_id": rec.task_id}, ctx)
    assert not r.is_error, r.output
    datos = json.loads(r.output)
    assert datos["description"] == marca and datos["task_id"] == rec.task_id, datos
    r2 = await tool.execute({"task_id": ajena.task_id}, ctx)
    assert r2.is_error, "leyó una tarea de OTRA sesión (bleed de aislamiento)"
    return "leyó la tarea real del registry; la de otra sesión es invisible"


async def _e10_task_list(tool: Any, env: _E10Env) -> str:
    marca = env.tag("TLIST")
    env.registry.register(description=marca, session_id=env.session_id)
    env.registry.register(description="de-otra-sesion", session_id="otra-sesion")
    ctx = env.ctx()
    r = await tool.execute({}, ctx)
    assert not r.is_error, r.output
    descripciones = [t["description"] for t in json.loads(r.output)]
    assert marca in descripciones, f"no listó la tarea de la sesión: {descripciones}"
    assert "de-otra-sesion" not in descripciones, "listó tareas de otra sesión"
    # `FIND-E11-3`: el filtro `status` que B se había inventado (A: `z.strictObject({})`)
    # convertía un valor fuera de dominio en `[]` — «no hay tareas» donde sí las había.
    # Que el schema no lo declare es lo que impide que el modelo lo intente.
    assert not (tool.input_schema.get("properties") or {}), (
        f"`TaskList` volvió a declarar parámetros: {tool.input_schema}. El canónico "
        "no tiene ninguno, y un filtro sin dominio acotado hace mentir a la tool."
    )
    return "listó las tareas reales de SU sesión y sólo ésas; schema sin parámetros (como A)"


async def _e10_task_update(tool: Any, env: _E10Env) -> str:
    nueva = env.tag("TUPD")
    rec = env.registry.register(description="original", session_id=env.session_id)
    ctx = env.ctx()
    r = await tool.execute({"task_id": rec.task_id, "description": nueva}, ctx)
    assert not r.is_error, r.output
    assert env.registry.get(rec.task_id).description == nueva, (
        "la descripción del REGISTRO no cambió (el output puede decir misa)"
    )
    r2 = await tool.execute({"task_id": "no-existe"}, ctx)
    assert r2.is_error, "actualizó una tarea inexistente"
    return "cambió la descripción en el registro del registry, no sólo en su salida"


async def _e10_task_stop(tool: Any, env: _E10Env) -> str:
    rec = env.registry.register(description="a-matar", session_id=env.session_id)
    ctx = env.ctx()
    r = await tool.execute({"task_id": rec.task_id}, ctx)
    assert not r.is_error, r.output
    assert env.registry.get(rec.task_id).status is TaskStatus.KILLED, (
        f"la tarea no quedó KILLED: {env.registry.get(rec.task_id).status}"
    )
    ajena = env.registry.register(description="ajena", session_id="otra-sesion")
    r2 = await tool.execute({"task_id": ajena.task_id}, ctx)
    assert r2.is_error, "mató una tarea de otra sesión"
    assert env.registry.get(ajena.task_id).status is not TaskStatus.KILLED, (
        "NEGATIVA rota: la tarea ajena quedó matada igual"
    )
    return "dejó la tarea en KILLED en el registry; una de otra sesión no la toca"


async def _e10_task_output(tool: Any, env: _E10Env) -> str:
    marca = env.tag("TOUT")
    rec = env.registry.register(description="con-salida", session_id=env.session_id)
    ctx = env.ctx()
    r0 = await tool.execute({"task_id": rec.task_id}, ctx)
    assert not r0.is_error and "no result yet" in r0.output, r0.output
    env.registry.complete(rec.task_id, result=marca)
    r = await tool.execute({"task_id": rec.task_id}, ctx)
    assert not r.is_error, r.output
    assert r.output == marca, f"no devolvió el resultado real de la tarea: {r.output!r}"
    return "devolvió el resultado que el registry tiene, y avisa cuando aún no lo hay"


#: Un caso por tool del censo. La igualdad con `_NATIVE_CENSUS` se asevera al correr:
#: una tool nueva sin caso pone el gate rojo en vez de entrar sin prueba funcional.
_E10_CASES: dict[str, Any] = {
    "Agent": _e10_agent,
    "AskUserQuestion": _e10_ask_user_question,
    "Config": _e10_config,
    "Edit": _e10_edit,
    "EnterPlanMode": _e10_enter_plan_mode,
    "EnterWorktree": _e10_enter_worktree,
    "ExitPlanMode": _e10_exit_plan_mode,
    "ExitWorktree": _e10_exit_worktree,
    "Sleep": _e10_sleep,
    "TaskCreate": _e10_task_create,
    "TaskGet": _e10_task_get,
    "TaskList": _e10_task_list,
    "TaskOutput": _e10_task_output,
    "TaskStop": _e10_task_stop,
    "TaskUpdate": _e10_task_update,
    "TodoWrite": _e10_todo_write,
    "ToolSearch": _e10_tool_search,
    "WebFetch": _e10_web_fetch,
    "WebSearch": _e10_web_search,
    "bash": _e10_bash,
    "clone_repository": _e10_clone_repository,
    "glob": _e10_glob,
    "grep": _e10_grep,
    "read_file": _e10_read_file,
    "write_file": _e10_write_file,
}


async def test_e10_every_native_tool_produces_its_observable_effect(tmp_path, monkeypatch):
    """`E10`: las 25 corren con cableado real y se asevera su EFECTO, no su `is_error`."""
    from agentic_runtime.tools.factory import create_tools

    assert set(_E10_CASES) == set(_NATIVE_CENSUS), (
        "la matriz funcional no cubre el censo — sin caso, una tool entra sin prueba de "
        f"que opere. Sin caso: {sorted(_NATIVE_CENSUS - set(_E10_CASES))}; "
        f"sobrantes: {sorted(set(_E10_CASES) - _NATIVE_CENSUS)}"
    )

    ws = tmp_path / "ws"
    ws.mkdir()
    # Repo git real: lo necesitan `EnterWorktree`/`ExitWorktree`, y un repo sin
    # ningún commit no tiene HEAD, así que `worktree add` no tendría de dónde partir.
    _git("init", "-q", "-b", "main", cwd=ws)
    (ws / "README.md").write_text("gate tramo 1\n", encoding="utf-8")
    _git("add", "-A", cwd=ws)
    _git("commit", "-q", "-m", "inicial", cwd=ws)

    env = _E10Env(ws=ws, tmp=tmp_path, monkeypatch=monkeypatch, session_id="sess-e10")

    comprobadas: set[str] = set()
    fallos: list[str] = []
    matriz: list[str] = []

    for tool in sorted(create_tools().all_tools(), key=lambda t: t.name):
        caso = _E10_CASES[tool.name]
        # Se marca ANTES de correr: «comprobada» = el caso se ejecutó sobre esta tool.
        # Que además pase lo decide `fallos`. Así una tool no puede quedar fuera del
        # censo por haberse caído — que es como se pierden las cosas en silencio.
        comprobadas.add(tool.name)
        try:
            nota = await caso(tool, env)
            matriz.append(f"  ✔ {tool.name}: {nota}")
        except AssertionError as exc:
            fallos.append(f"[{tool.name}] {exc}")
            matriz.append(f"  ✘ {tool.name}: {str(exc).splitlines()[0]}")
        # No silencia: convierte en fallo REPORTADO. Un caso que revienta por algo
        # inesperado es un rojo del gate igual, con su tipo de excepción a la vista.
        except Exception as exc:  # noqa: BLE001
            fallos.append(f"[{tool.name}] excepción inesperada {type(exc).__name__}: {exc}")
            matriz.append(f"  ✘ {tool.name}: {type(exc).__name__}: {exc}")

    print(f"\n[E10] matriz funcional de las {len(_NATIVE_CENSUS)} nativas:\n" + "\n".join(matriz))

    assert comprobadas == set(_NATIVE_CENSUS), (
        f"quedaron tools sin comprobar: {sorted(set(_NATIVE_CENSUS) - comprobadas)}"
    )
    assert not fallos, (
        f"MATRIZ FUNCIONAL: {len(fallos)}/{len(_NATIVE_CENSUS)} tools no acreditan su "
        "efecto observable\n" + "\n".join(fallos)
    )


# ══════════════════════════════════════════════════════════════════════════════
# E11 · las 11 que NINGUNA corrida medida había conducido — ahora con modelo real
# ══════════════════════════════════════════════════════════════════════════════
#
# **El agujero, tal cual salió del censo honesto de la 6ª corrección.** Cuando
# `_invoked_tool_names` dejó de contar por substring y pasó a leer
# `msg["tool_calls"][*]["function"]["name"]`, la unión de tools que el modelo había
# invocado de verdad en TODAS las corridas medidas (`E2d`+`E2f`+`E2g`) bajó a 14 de
# 25. Las otras 11 estaban **anunciadas** (`E2c'`) y **barridas** (`E7f`) y desde
# `E10` también **acreditadas funcionalmente** — pero ningún modelo las había
# conducido nunca. Eso no es una laguna cosmética: entre el schema que se anuncia y
# la tool que se ejecuta hay una traducción, y una descripción ambigua o un schema
# que el modelo no sabe rellenar rompe la cadena sin que ninguna de las tres capas
# anteriores se entere. Aquí se cierra.
#
# **`E10` mide EFECTO; `E11` mide CONDUCCIÓN.** Son cosas distintas y por eso son
# dos tests: `E10` invoca la tool a mano y mira lo que dejó; `E11` no la nombra
# jamás en el enunciado —enuncia el objetivo— y mira si el modelo llega a ella con
# argumentos válidos. Donde el escenario tiene además efecto verificable (archivo,
# árbol de git, registro del registry) se asevera **también** el efecto: así una
# invocación con argumentos plausibles pero inertes no cuenta como conducida.
#
# **El censo ENTERO está delante en todos los escenarios, y no por elegancia.**
# La primera versión de este test retiraba del anuncio las alternativas equivalentes
# (`bash` con `sed` sustituye a `Edit`, con `curl` a `WebFetch`, con `git clone` a
# `clone_repository`) para que el escenario sólo se pudiera resolver con la tool
# objetivo. Dos cosas salieron de correrlo, y ninguna es la que yo esperaba:
#
#   1. **`FIND-E11-1` — no existe la costura.** Yo pasaba `initial_allowed_tools`
#      creyendo que restringía el anuncio, y no: es una **allow-list de permisos**
#      (`runtime.py:295-298` → `PermissionContext(always_allow_command=…)`), aditiva,
#      que concede a las `requires_permission` y no retira nada. La guarda del test
#      lo cazó (se anunciaron las 24 igual). Revisado el ensamblador entero: el único
#      mecanismo de restricción por nombre es `agent_allowed_tools`, y sólo alcanza a
#      **subagentes** con `AgentDefinition` (`runtime.py:447-472`,
#      `agent_loop.py:139`). Para el agente RAÍZ el integrador no tiene ninguna vía de
#      no anunciar una tool nativa. Queda **nombrado y sin pagar aquí**, por el mismo
#      motivo que los escapes de red de `E7f`: eso es `S17 PermissionGate`, arriba de
#      la LÍNEA DE CORTE del tramo 1. Lo que se paga es dejar de no saberlo.
#   2. **El resultado medido es MÁS fuerte que el diseño.** Con las 24 anunciadas —
#      `bash` y `write_file` incluidos— el modelo condujo **las 11** igual: eligió
#      `Edit` teniendo `sed` a mano y `clone_repository` teniendo `git` a mano. Así
#      que el andamio se retira en vez de arreglarse: el escenario ya no le quita
#      alternativas a nadie, y sigue aseverando la conducción. Un escenario con menú
#      corto habría medido obediencia (`E2d`); éste mide elección.
#
# ⚠ El precio, dicho: sin exclusión, una corrida en la que el modelo resuelva
# `editar-en-sitio` con `bash` sale ROJA. Ese rojo sería verdad —no condujo `Edit`—
# y es el que hay que ver, no el que hay que evitar.
#
# ── LO QUE ESTE TEST COBRÓ EL PRIMER DÍA ─────────────────────────────────────
#
# `FIND-E11-3` · **defecto del SUJETO, pagado aquí.** `TaskList` declaraba un
# parámetro `status` que **el canónico no tiene** (`TaskListTool.ts:13` es
# `z.strictObject({})`, leído 1→EOF). El campo era `string` libre, sin `enum`, y su
# descripción decía «Filter by status (…). Omit for all» — así que el modelo llamó
# con `status="all"`, el filtro comparó por igualdad, y la tool devolvió `[]`:
# **indistinguible de «no hay tareas»**. El modelo respondió «no hay trabajos en
# segundo plano en esta sesión» con dos tareas sembradas delante. Retirado el
# parámetro (`L10`: una divergencia con A no es una mejora hasta que se demuestre);
# la regresión la fija `_e10_task_list`.
#
# `FIND-E11-2` · **ABIERTO y vigilado por el gate.** En 2 de 4 corridas medidas el
# modelo resolvió `preguntar-al-usuario` **preguntando en prosa** en vez de conducir
# `AskUserQuestion` (respuesta: «¿Qué formato quieres…? - PDF - DOCX - ZIP»). Se
# verificó que no es déficit del montaje: la descripción de la tool en B dice
# literalmente «Prefer this over asking in free-form prose whenever you need input to
# proceed» —fiel a A— y el único empujón que A pone en su system prompt es para el
# caso de tool denegada (`prompts.ts:365-366`), no una cláusula general. Así que es
# solvencia del modelo, y **no se atiende retocando el enunciado ni el system prompt
# para que pase**: eso sería el tell exacto. Queda rojo cuando pasa, igual que
# `FIND-E2G-1`.
#
# Lo que impide aprobar sin mérito, igual que en `E2f`/`E2g`: centinelas `uuid4` por
# corrida (nada sale del conocimiento paramétrico), escenarios barajados, la tool
# **nunca nombrada** en el prompt, y la semilla impresa y fijable por
# `GATE_E11_SEED`. Cierra con `assert conducidas == _E11_OBJETIVO`: si mañana un
# escenario deja de conducir la suya, el gate se pone rojo en vez de perderla.

#: Las 11 del censo que ninguna corrida medida había conducido nunca.
_E11_OBJETIVO = frozenset({
    "AskUserQuestion", "Config", "Edit", "EnterWorktree", "ExitWorktree",
    "TaskList", "TaskOutput", "TaskStop", "TodoWrite", "WebFetch",
    "clone_repository",
})

_E11_SYSTEM = (
    "Eres un agente con herramientas reales. Elige tu la herramienta adecuada para "
    "cada objetivo; nadie te va a decir cual usar. No inventes datos ni finjas "
    "haber hecho algo: si hay que actuar, actua con una herramienta. Cuando "
    "termines, responde con el dato pedido, sin adornos."
)


def _invoked_tool_args(calls: list[dict], name: str) -> list[dict]:
    """Argumentos con los que el modelo invocó `name`, parseados del historial.

    Misma fuente estructural que `_invoked_tool_names` — `tool_calls`, no texto —
    porque lo que se quiere aseverar es *con qué la llamó*, y eso en el cuerpo de un
    mensaje sería adivinar.
    """
    out: list[dict] = []
    for call in calls:
        for msg in call["messages"]:
            for tc in msg.get("tool_calls") or ():
                fn = tc.get("function") or {}
                if fn.get("name") != name:
                    continue
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except (ValueError, TypeError):
                    continue
                if isinstance(args, dict):
                    out.append(args)
    return out


def _e11_scenarios(
    tmp_path: Path, rnd: random.Random, puertos: dict[str, int], codigos: dict[str, str],
) -> list[dict]:
    """Un escenario por objetivo. `must_use` es la tool que debe quedar conducida.

    Campos: `id` · `prompt` (nunca nombra la tool) · `must_use` · `tambien` (otras
    que el escenario debe conducir) · `seed(runtime, session_id)` opcional ·
    `expect_in_answer` · `check(runtime, session_id, answer, probe) -> str|None` con
    el efecto observable.
    """
    def tag(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    escenarios: list[dict] = []

    # 1 · Edit — sustitución quirúrgica sobre un archivo que NO se puede reescribir
    #     entero: el enunciado pide explícitamente conservar el resto.
    viejo, nuevo = tag("CLAVE"), tag("NUEVA")
    # DENTRO del write-root: la primera versión lo puso en `tmp_path` (sólo lectura) y
    # el runtime lo rechazó con razón — el confinamiento hizo su trabajo, el montaje no.
    edit_dir = tmp_path / "ws" / "edit"
    edit_dir.mkdir(parents=True, exist_ok=True)
    edit_file = edit_dir / "registro.txt"
    relleno = "\n".join(f"linea de relleno numero {i}" for i in range(40))
    edit_file.write_text(f"{relleno}\nclave activa: {viejo}\n{relleno}\n", encoding="utf-8")

    def _check_edit(runtime, sid, answer, probe, *, p=edit_file, v=viejo, n=nuevo, r=relleno):
        contenido = p.read_text(encoding="utf-8")
        if n not in contenido:
            return f"el archivo no contiene la clave nueva {n}"
        if v in contenido:
            return f"la clave vieja {v} sigue en el archivo"
        if contenido != f"{r}\nclave activa: {n}\n{r}\n":
            return "el archivo cambió más allá de la clave (no fue una edición quirúrgica)"
        return None

    escenarios.append({
        "id": "editar-en-sitio",
        "prompt": (
            f"En el archivo {edit_file} hay una linea que dice 'clave activa: {viejo}'. "
            f"Sustituye ese valor por {nuevo} dejando el resto del archivo exactamente "
            "igual, sin reescribirlo entero. Luego confirma diciendo la clave nueva."
        ),
        "must_use": "Edit",
        "check": _check_edit,
    })

    # 2 · WebFetch — hay URL concreta, así que `WebSearch` no aplica; se retira `bash`
    #     para que `curl`/`wget` no sean la vía.
    escenarios.append({
        "id": "traer-una-url",
        "prompt": (
            f"En la pagina http://127.0.0.1:{puertos['http']}/boletin hay un codigo de "
            "boletin. Traela y dime el codigo exacto que aparece."
        ),
        "must_use": "WebFetch",
        "expect_in_answer": codigos["fetch"],
    })

    # 3 · clone_repository — repo git servido de verdad; se retira `bash` para que no
    #     sea `git clone` a mano.
    escenarios.append({
        "id": "clonar-repo",
        "prompt": (
            f"Clona el repositorio https://127.0.0.1:{puertos['git']}/repo.git en el "
            "directorio 'copia' de tu espacio de trabajo y dime que dice el archivo "
            "SENTINELA.txt que hay dentro."
        ),
        "must_use": "clone_repository",
        "expect_in_answer": codigos["clone"],
    })

    # 4 · TodoWrite — el objetivo es registrar el plan, no ejecutarlo.
    def _check_todos(runtime, sid, answer, probe):
        args = _invoked_tool_args(probe.calls, "TodoWrite")
        if not args:
            return "no llegaron argumentos de TodoWrite al historial"
        todos = args[-1].get("todos")
        if not isinstance(todos, list) or len(todos) < 3:
            return f"registró una lista que no tiene las 3 tareas pedidas: {todos!r}"
        return None

    escenarios.append({
        "id": "registrar-plan",
        "prompt": (
            "Voy a pedirte un trabajo largo en tres pasos: (1) revisar el inventario, "
            "(2) corregir los precios, (3) publicar el informe. Antes de empezar, deja "
            "registrada tu lista de tareas pendientes con esos tres pasos. No ejecutes "
            "ninguno todavia; responde 'listo' cuando la lista este registrada."
        ),
        "must_use": "TodoWrite",
        "check": _check_todos,
    })

    # 5 · Config — set y luego get: la respuesta sólo puede salir de leer lo escrito.
    cfg_valor = tag("PERFIL")
    escenarios.append({
        "id": "ajuste-de-sesion",
        "prompt": (
            f"Deja el ajuste 'model' de esta sesion con el valor {cfg_valor}. Despues "
            "consulta ese mismo ajuste y dime el valor que tiene ahora."
        ),
        "must_use": "Config",
        "expect_in_answer": cfg_valor,
    })

    # 6 · TaskList — no se le da ningún id, así que enumerar es la única vía.
    lista_desc = tag("ENCARGO")

    def _seed_list(runtime, sid, *, desc=lista_desc):
        runtime._task_registry.register(description=f"{desc}: revisar el almacen", session_id=sid)
        runtime._task_registry.register(description="otro encargo distinto", session_id=sid)

    escenarios.append({
        "id": "enumerar-tareas",
        "prompt": (
            "Tienes trabajos en segundo plano de esta sesion. No se sus identificadores. "
            "Averigua cuales hay y dime la descripcion completa del que empieza por "
            f"{lista_desc}."
        ),
        "must_use": "TaskList",
        "seed": _seed_list,
        "expect_in_answer": lista_desc,
    })

    # 7 · TaskOutput — se da el id y se pide el RESULTADO. Se retira `TaskGet` porque
    #     devuelve el registro entero y resolvería el objetivo por otra puerta.
    out_code = tag("DICTAMEN")
    out_id: dict[str, str] = {}

    def _seed_out(runtime, sid, *, code=out_code, holder=out_id):
        rec = runtime._task_registry.register(description="analisis del lote", session_id=sid)
        runtime._task_registry.complete(rec.task_id, result=f"resultado final: {code}")
        holder["id"] = rec.task_id

    # ⚠ **`TaskOutput` y `TaskGet` son redundantes para este objetivo, y es del
    #   catálogo, no del modelo**: `TaskGet` devuelve el registro ENTERO, `result`
    #   incluido (`task_tools.py:105-111`), así que «dime qué resultado produjo» lo
    #   resuelven las dos y **no hay enunciado por objetivo que las discrimine**.
    #   Retirar `TaskGet` del anuncio tampoco se puede (`FIND-E11-1`). Así que el
    #   escenario se parte en dos y cada mitad dice su grado:
    #     · por OBJETIVO — se acepta cualquiera de las dos; lo que se asevera es que
    #       el modelo consultó el registry de verdad (el centinela sólo está ahí).
    #     · DIRIGIDO — la tool se nombra en el enunciado. Es el régimen de `E2d`
    #       (invocar lo que se te dice), más débil que el resto de `E11`, y se
    #       declara como tal en vez de disfrazarlo de elección. Es lo máximo
    #       acreditable para una tool redundante sin inventarme una restricción que
    #       el runtime no ofrece.
    escenarios.append({
        "id": "resultado-de-tarea",
        "prompt_factory": lambda: (
            f"El trabajo en segundo plano {out_id['id']} ya termino. Dime exactamente "
            "que resultado produjo."
        ),
        "must_use": "TaskOutput",
        "aceptables": {"TaskOutput", "TaskGet"},
        "seed": _seed_out,
        "expect_in_answer": out_code,
    })

    out2_code = tag("VEREDICTO")
    out2_id: dict[str, str] = {}

    def _seed_out2(runtime, sid, *, code=out2_code, holder=out2_id):
        rec = runtime._task_registry.register(description="segundo lote", session_id=sid)
        runtime._task_registry.complete(rec.task_id, result=f"salida cruda: {code}")
        holder["id"] = rec.task_id

    escenarios.append({
        "id": "resultado-de-tarea-dirigido",
        "prompt_factory": lambda: (
            f"Con la herramienta TaskOutput, obten la salida del trabajo en segundo "
            f"plano {out2_id['id']} y dimela tal cual."
        ),
        "must_use": "TaskOutput",
        "seed": _seed_out2,
        "expect_in_answer": out2_code,
    })

    # 8 · TaskStop — efecto REAL sobre el registry, no sobre la narración.
    stop_id: dict[str, str] = {}

    def _seed_stop(runtime, sid, *, holder=stop_id):
        rec = runtime._task_registry.register(description="proceso desbocado", session_id=sid)
        holder["id"] = rec.task_id

    def _check_stop(runtime, sid, answer, probe, *, holder=stop_id):
        rec = runtime._task_registry.get(holder["id"])
        if rec.status is not TaskStatus.KILLED:
            return f"la tarea sigue en {rec.status} — no la detuvo de verdad"
        return None

    escenarios.append({
        "id": "detener-tarea",
        "prompt_factory": lambda: (
            f"El trabajo en segundo plano {stop_id['id']} se ha desbocado y hay que "
            "pararlo ya. Encargate y confirma diciendo 'detenida'."
        ),
        "must_use": "TaskStop",
        "seed": _seed_stop,
        "check": _check_stop,
    })

    # 9 · el PAR de worktree en un solo turno: abrir aislamiento y deshacerlo.
    wt_nombre = f"aislado-{rnd.randrange(10_000)}"
    escenarios.append({
        "id": "worktree-ida-y-vuelta",
        "prompt": (
            f"Necesito trabajar aislado del arbol principal: abre un espacio de trabajo "
            f"aislado llamado '{wt_nombre}' sobre el repositorio actual. En cuanto lo "
            "tengas abierto, cierralo eliminandolo por completo. Responde 'hecho'."
        ),
        "must_use": "EnterWorktree",
        "tambien": {"ExitWorktree"},
        "wt": wt_nombre,
    })

    # 10 · AskUserQuestion — el dato NO existe en ninguna parte: la única salida
    #      legítima es preguntar. Si el modelo inventa, el escenario lo caza.
    escenarios.append({
        "id": "preguntar-al-usuario",
        "prompt": (
            "Tengo que archivar unos documentos y no te he dicho en que formato los "
            "quiero. Ese dato no esta en ningun archivo ni en la web: solo lo se yo. "
            "No elijas por mi ni supongas nada: consultamelo a mi antes de seguir."
        ),
        "must_use": "AskUserQuestion",
    })

    return escenarios


@_needs_azure
async def test_e11_the_model_conducts_the_eleven_never_conducted_tools(tmp_path, monkeypatch):
    """`E11`: modelo real conduce las 11 que ninguna corrida medida había conducido."""
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    seed = int(os.getenv("GATE_E11_SEED") or uuid.uuid4().int % (2**32))
    rnd = random.Random(seed)

    # Workspace REAL y compartido: repo git con un commit (lo piden los worktree) y
    # raíz de confinamiento de todos los escenarios.
    ws = tmp_path / "ws"
    ws.mkdir()
    _git("init", "-q", "-b", "main", cwd=ws)
    (ws / "README.md").write_text("gate e11\n", encoding="utf-8")
    _git("add", "-A", cwd=ws)
    _git("commit", "-q", "-m", "inicial", cwd=ws)

    # Repo bare servido por HTTPS real, igual que en `E10` (la tool fuerza `https://`).
    sentinela = f"CARGA-{uuid.uuid4().hex[:10].upper()}"
    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "SENTINELA.txt").write_text(f"{sentinela}\n", encoding="utf-8")
    _git("init", "-q", "-b", "main", cwd=origen)
    _git("add", "-A", cwd=origen)
    _git("commit", "-q", "-m", "inicial", cwd=origen)
    servidos = tmp_path / "servidos"
    servidos.mkdir()
    _git("clone", "-q", "--bare", str(origen), str(servidos / "repo.git"), cwd=tmp_path)
    _git("-C", str(servidos / "repo.git"), "update-server-info", cwd=tmp_path)
    monkeypatch.setenv("GIT_SSL_NO_VERIFY", "1")

    fallos: list[str] = []
    conducidas: set[str] = set()
    matriz: list[str] = []

    with contextlib.ExitStack() as stack:
        fetch_code = f"BOLETIN-{uuid.uuid4().hex[:10].upper()}"
        puerto_http = stack.enter_context(
            _servidor_http(f"<html><body>codigo de boletin: {fetch_code}</body></html>".encode())
        )
        puerto_git = stack.enter_context(_servidor_git_https(servidos, tmp_path))

        escenarios = _e11_scenarios(
            tmp_path, rnd,
            {"http": puerto_http, "git": puerto_git},
            {"fetch": fetch_code, "clone": sentinela},
        )
        rnd.shuffle(escenarios)

        for n, sc in enumerate(escenarios):
            objetivo = {sc["must_use"], *sc.get("tambien", set())}
            probe = ModelSeamProbe(_build_caller(_E11_SYSTEM))
            runtime = _runtime(
                tmp_path / f"rt_e11_{n}", probe, (), Scope(f"scope-e11-{n}"),
                fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[ws]),
                # Allow-list de PERMISOS, no de anuncio (`FIND-E11-1`): sin esto las
                # `requires_permission` quedan fuera del pool y el escenario mediría
                # una restricción que nadie pidió.
                initial_allowed_tools=sorted(_NATIVE_CENSUS),
            )
            session_id = f"sess-E11-{sc['id']}-{uuid.uuid4().hex}"
            if "seed" in sc:
                sc["seed"](runtime, session_id)
            prompt = sc["prompt_factory"]() if "prompt_factory" in sc else sc["prompt"]

            task_id = await runtime.dispatch(RuntimeTask(
                prompt=prompt, description=f"gate-e11-{sc['id']}", session_id=session_id,
            ))
            await runtime._task_registry.get(task_id).asyncio_task

            answer = runtime.result(task_id) or ""
            status = runtime.status(task_id)
            invocadas = _invoked_tool_names(probe.calls)
            conducidas |= invocadas & _E11_OBJETIVO
            anunciadas = {t.get("name") for call in probe.calls for t in call["tools"]}

            problemas: list[str] = []
            # `AskUserQuestion` cede el turno: la tarea no «completa» resolviendo, y
            # exigirle COMPLETED sería exigirle que ignore su propio contrato.
            if status is not TaskStatus.COMPLETED and sc["must_use"] != "AskUserQuestion":
                problemas.append(f"la tarea no completó ({status})")
            # El censo entero estuvo delante: la elección fue una elección. `ToolSearch`
            # se retira en la rama nativa, de ahí el 24 y no 25 (`E2g`).
            if len(anunciadas) < 20:
                problemas.append(f"anuncio incompleto ({len(anunciadas)}): {sorted(anunciadas)}")
            # `aceptables` = el objetivo admite más de una tool legítima (ver el par
            # `TaskOutput`/`TaskGet`): basta con que eligiera UNA capaz. Sin él, se
            # exigen todas las del objetivo.
            if "aceptables" in sc:
                faltan = set() if (invocadas & sc["aceptables"]) else set(sc["aceptables"])
                if faltan:
                    problemas.append(
                        f"no eligió ninguna capaz de {sorted(sc['aceptables'])} "
                        f"(invocó {sorted(invocadas)})"
                    )
            else:
                faltan = objetivo - invocadas
                if faltan:
                    problemas.append(f"no condujo {sorted(faltan)} (invocó {sorted(invocadas)})")
            if "expect_in_answer" in sc and sc["expect_in_answer"] not in answer:
                problemas.append(f"el centinela {sc['expect_in_answer']} no llegó a la respuesta")
            if "check" in sc and not faltan:
                fallo = sc["check"](runtime, session_id, answer, probe)
                if fallo:
                    problemas.append(fallo)
            if "wt" in sc and not faltan and (ws / ".worktrees" / sc["wt"]).exists():
                problemas.append("el worktree sigue en disco: no completó la vuelta")

            if problemas:
                # Los argumentos REALES de la tool objetivo van en el fallo: sin ellos,
                # «la invocó y no salió el efecto» obliga a adivinar si el problema es
                # del modelo, del schema o del montaje. Con ellos se lee.
                fallos.append(
                    f"[{sc['id']}] " + "; ".join(problemas)
                    + f"\n    anunciadas={len(anunciadas)} invocadas={sorted(invocadas)}"
                    + f"\n    args({sc['must_use']})={_invoked_tool_args(probe.calls, sc['must_use'])}"
                    + f"\n    respuesta={answer[:200]!r}"
                )
                matriz.append(f"  ✘ {sc['id']} → {sorted(objetivo)}: {problemas[0]}")
            else:
                matriz.append(f"  ✔ {sc['id']} → condujo {sorted(objetivo)}")

    print(
        f"\n[E11] GATE_E11_SEED={seed} · conducción por el modelo de las "
        f"{len(_E11_OBJETIVO)} nunca conducidas:\n" + "\n".join(matriz)
        + f"\n  conducidas: {sorted(conducidas)}"
    )
    assert not fallos, (
        f"CONDUCCIÓN: {len(fallos)}/{len(_E11_OBJETIVO)} objetivos sin acreditar "
        f"(GATE_E11_SEED={seed} para reproducir)\n" + "\n".join(fallos)
    )
    assert conducidas == set(_E11_OBJETIVO), (
        "quedaron tools del objetivo sin conducir por el modelo: "
        f"{sorted(set(_E11_OBJETIVO) - conducidas)}"
    )
