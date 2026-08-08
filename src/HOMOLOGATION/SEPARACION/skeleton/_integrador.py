"""Evidencia del ciclo A2.5 — INTEGRADOR: turno end-to-end con SUBAGENTE (costuras S18/S4/S21).

Cierra el walking skeleton. Valida la costura CRÍTICA de la espina de ejecución (S18
`SubagentRunnerProtocol`, 05·E24: en la mímica ningún subagente corría porque el factory nunca
poblaba el runner) más S4 (façade dispatch/status/result) y S21 (`NotificationSink` put+drain).

    cd agentic_runtime && PYTHONPATH=src/HOMOLOGATION/SEPARACION \
      .venv/bin/python -m skeleton._integrador          # canned + negativa + S4 (offline, HARD gate)
    cd agentic_runtime && PYTHONPATH=src/HOMOLOGATION/SEPARACION \
      .venv/bin/python -m skeleton._integrador --real   # + turno REAL padre→subagente (best-effort)

Cuatro comprobaciones:
  (A) CANNED end-to-end: el padre llama la tool `agent` → el runner (S18) construye un runtime
      HIJO → el hijo llama `add_numbers` → 42 se aplana al padre, que lo cita. Determinista, offline.
  (B) NEGATIVA (L09 — cableado, no existencia): un runtime SIN el runner del factory (runner=None)
      hace que `AgentTool` devuelva is_error ⇒ la costura S18 es LOAD-BEARING (sin el cableado del
      factory no hay spawn — reproduce el bug mímica, ahora imposible de olvidar).
  (C) S4 façade: `dispatch()` → `status()`=COMPLETED + `result()` no-None bajo el MISMO id.
  (D) S21: la `Notification` que el child publicó se DRENA del sink con el resultado del subagente.
"""

from __future__ import annotations

import asyncio
import json
import ssl
import sys
from pathlib import Path
from typing import Any

from skeleton.contracts import (
    ErrorEvent,
    ResultEvent,
    RuntimeTask,
    TaskStatus,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from skeleton.factory import create_runtime
from skeleton.runtime import LocalAgentRuntime
from skeleton.seams import ModelCallerProtocol, SubagentSpec
from skeleton.stubs import PassthroughInputProcessor, StubToolModelCaller
from skeleton.tools import AddTool, AgentTool, ToolPool

_MODEL_ID = "claude-haiku-4-5"
_CRED_PATH = Path.home() / ".claude" / ".credentials.json"


# ══════════════════════════════════════════════════════════════════════════════
# (A) CANNED end-to-end — HARD gate arquitectónico (offline, determinista)
# ══════════════════════════════════════════════════════════════════════════════
async def _run_canned() -> bool:
    print("=== A2.5 · (A) CANNED end-to-end (padre → S18 runner → subagente) ===")
    # Padre: llama la tool `agent` con la subtarea. Hijo: llama `add_numbers(17,25)`.
    parent, sink = create_runtime(
        parent_caller=StubToolModelCaller(
            tool_name="agent", tool_input={"prompt": "suma 17 y 25"}
        ),
        child_caller_factory=lambda _spec: StubToolModelCaller(
            tool_name="add_numbers", tool_input={"a": 17, "b": 25}
        ),
        child_tools=lambda: [AddTool()],
    )
    task = RuntimeTask(prompt="delega la suma en un subagente", session_id="opaque-parent-sess")

    delegated = False
    agent_result = ""
    parent_final = ""
    async for event in parent.stream(task):
        if isinstance(event, ToolCallEvent) and event.name == "agent":
            delegated = True
            print(f"  padre → ToolCallEvent: name={event.name!r} input={event.input!r}")
        elif isinstance(event, ToolResultEvent):
            agent_result = event.output
            print(f"  runner → ToolResultEvent: output={event.output!r} is_error={event.is_error}")
        elif isinstance(event, ResultEvent):
            parent_final = event.text

    notes = sink.drain()  # (D) S21: el integrador drena lo que el child publicó
    print(f"  padre ResultEvent.text = {parent_final!r}")
    print(f"  sink.drain() = {notes}")

    subagent_ran = delegated and "42" in agent_result
    parent_cites = "42" in parent_final
    notified = len(notes) == 1 and "42" in notes[0].result and notes[0].status == "completed"
    ok = subagent_ran and parent_cites and notified
    print(f"  subagente corrió por S18 (padre delegó + result cita 42) = {subagent_ran}")
    print(f"  padre aplanó el resultado del subagente (cita 42)        = {parent_cites}")
    print(f"  S21 notificación drenada con el resultado                = {notified}")
    print(f"  → (A) {'OK' if ok else 'FALLO'}\n")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# (B) NEGATIVA — la costura S18 es load-bearing (sin cableado del factory: no hay spawn)
# ══════════════════════════════════════════════════════════════════════════════
async def _run_negative() -> bool:
    print("=== A2.5 · (B) NEGATIVA: runtime SIN runner (factory no cableó S18) ===")
    # Construcción DELIBERADAMENTE incompleta: AgentTool en el pool pero runner=None.
    bare = LocalAgentRuntime(
        caller=StubToolModelCaller(tool_name="agent", tool_input={"prompt": "suma 17 y 25"}),
        input_processor=PassthroughInputProcessor(),
        tool_pool=ToolPool([AgentTool()]),
        # runner=None (default) — el factory es quien lo poblaría; aquí NO se usó el factory.
    )
    task = RuntimeTask(prompt="delega", session_id="opaque-sess")

    errored = False
    async for event in bare.stream(task):
        if isinstance(event, ToolResultEvent):
            errored = event.is_error and "not wired" in event.output
            print(f"  ToolResultEvent: output={event.output!r} is_error={event.is_error}")
    print(f"  spawn falló por S18 sin poblar (esperado)               = {errored}")
    print(f"  → (B) {'OK' if errored else 'FALLO'}\n")
    return errored


# ══════════════════════════════════════════════════════════════════════════════
# (C) S4 façade — dispatch/status/result coherentes bajo el mismo id
# ══════════════════════════════════════════════════════════════════════════════
async def _run_s4_facade() -> bool:
    print("=== A2.5 · (C) S4 façade: dispatch → status/result ===")
    parent, _sink = create_runtime(
        parent_caller=StubToolModelCaller(
            tool_name="agent", tool_input={"prompt": "suma 17 y 25"}
        ),
        child_caller_factory=lambda _spec: StubToolModelCaller(
            tool_name="add_numbers", tool_input={"a": 17, "b": 25}
        ),
        child_tools=lambda: [AddTool()],
    )
    task = RuntimeTask(prompt="delega la suma", session_id="opaque-parent-sess")
    task_id = await parent.dispatch(task)
    status = parent.status(task_id)
    result = parent.result(task_id)
    result_text = result.text if result is not None else None
    print(f"  dispatch() → task_id={task_id!r}")
    print(f"  status(task_id) = {status}")
    print(f"  result(task_id) = {result_text!r}")
    ok = status == TaskStatus.COMPLETED and result is not None and "42" in result.text
    print(f"  → (C) {'OK' if ok else 'FALLO'}\n")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# (REAL) turno end-to-end con modelo real — best-effort (A2.5 gate "turno real")
# ══════════════════════════════════════════════════════════════════════════════
_orig_ctx = ssl.create_default_context


def _lenient_ctx(*args: Any, **kwargs: Any) -> ssl.SSLContext:
    ctx = _orig_ctx(*args, **kwargs)
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def _load_oauth_token() -> str:
    data = json.loads(_CRED_PATH.read_text())
    token: str = data["claudeAiOauth"]["accessToken"]
    return token


_CC_IDENTITY = "You are Claude Code, Anthropic's official CLI for Claude.\n\n"


async def _run_real() -> bool:
    print("=== A2.5 · (REAL) turno end-to-end padre→subagente (modelo real) ===")
    import agentic_models as am
    from anthropic import AsyncAnthropic

    from skeleton.bridge import AgenticModelsCaller

    ssl.create_default_context = _lenient_ctx
    am.register_builtins()
    model: Any = am.get_registry().get_by_provider("anthropic", _MODEL_ID)
    oauth_client = AsyncAnthropic(
        auth_token=_load_oauth_token(),
        base_url=model.base_url,
        default_headers={
            "anthropic-beta": "claude-code-20250219,oauth-2025-04-20",
            "user-agent": "claude-cli/1.0.0",
            "x-app": "cli",
            "anthropic-dangerous-direct-browser-access": "true",
        },
    )

    def child_caller(_spec: SubagentSpec) -> ModelCallerProtocol:
        return AgenticModelsCaller(model, client=oauth_client)

    parent, sink = create_runtime(
        parent_caller=AgenticModelsCaller(model, client=oauth_client),
        child_caller_factory=child_caller,
        model_id=_MODEL_ID,
        parent_system_prompt=(
            _CC_IDENTITY
            + "Para resolver CUALQUIER suma, NO calcules tú: DELEGA en un subagente usando la "
            "herramienta `agent`, pasándole la petición en `prompt`. Cuando el subagente te "
            "responda, da el resultado final en UNA sola frase, en español."
        ),
        child_system_prompt=(
            _CC_IDENTITY
            + "Cuando necesites sumar, USA la herramienta add_numbers en vez de calcular tú. "
            "Responde en una sola frase, en español."
        ),
        child_tools=lambda: [AddTool()],
        temperature=0.0,
        max_tokens=256,
        metadata={"user_id": "opaque-owner"},
    )
    task = RuntimeTask(
        prompt="¿Cuánto es 17 más 25? Delégalo en un subagente.",
        owner_id="opaque-owner",
        session_id="opaque-parent-sess",
    )

    delegated = False
    agent_result = ""
    parent_final = ""
    async for event in parent.stream(task):
        if isinstance(event, ToolCallEvent) and event.name == "agent":
            delegated = True
            print(f"  padre → ToolCallEvent(agent): input={event.input!r}")
        elif isinstance(event, ToolResultEvent):
            agent_result = event.output
            print(f"  runner → ToolResultEvent: output={event.output!r}")
        elif isinstance(event, ResultEvent):
            parent_final = event.text
            print(f"  padre ResultEvent.text = {event.text!r}")
        elif isinstance(event, ErrorEvent):
            print(f"  padre → ErrorEvent: code={event.code!r} message={event.message!r}")
        elif isinstance(event, TokenEvent):
            print(f"  padre → TokenEvent[{event.kind}]: {event.text!r}")

    notes = sink.drain()
    print(f"  sink.drain() = {notes}")
    subagent_ran = delegated and "42" in agent_result
    parent_cites = "42" in parent_final
    notified = len(notes) == 1 and "42" in notes[0].result
    ok = subagent_ran and parent_cites and notified
    print(f"  padre delegó + subagente devolvió 42 = {subagent_ran}")
    print(f"  padre cita 42 = {parent_cites} · S21 notificación con 42 = {notified}")
    print(f"  → (REAL) {'OK' if ok else 'FALLO'}\n")
    return ok


async def _main(real: bool) -> int:
    a = await _run_canned()
    b = await _run_negative()
    c = await _run_s4_facade()
    offline_ok = a and b and c
    print(f"=== gate OFFLINE (A∧B∧C): {'OK' if offline_ok else 'FALLO'} ===")

    real_ok: bool | None = None
    if real:
        try:
            real_ok = await _run_real()
        except Exception as exc:  # noqa: BLE001 — best-effort; el gate duro es el offline.
            print(f"  (REAL) EXCEPCIÓN (no bloquea el gate offline): {type(exc).__name__}: {exc}")
            real_ok = False

    verdict = "OK" if offline_ok else "FALLO"
    real_line = "" if real_ok is None else f" | REAL end-to-end: {'OK' if real_ok else 'FALLO/n-d'}"
    print(f"\nVEREDICTO A2.5: {verdict}{real_line}")
    return 0 if offline_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main(real="--real" in sys.argv)))
