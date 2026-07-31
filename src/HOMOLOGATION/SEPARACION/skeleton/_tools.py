"""Evidencia del ciclo A2.3 — un TURNO REAL con TOOL por la costura S16.

Gate PLAN §4 A2.3: "el modelo llama la tool y el resultado se aplana". A diferencia del
canned de `_smoke` (StubToolModelCaller), esto cablea `bridge.AgenticModelsCaller` →
`agentic_models` → API real, anuncia la tool nativa `AddTool` y valida el round-trip
MULTIVUELTA completo: el modelo emite `tool_use(add_numbers)`, el `ToolDispatcher`
ejecuta la tool y aplana `42`, y el modelo redacta la respuesta final citando el número.

    cd agentic_runtime && PYTHONPATH=src/HOMOLOGATION/SEPARACION \
      .venv/bin/python -m skeleton._tools

Credencial: token OAuth de Claude Code (`~/.claude/.credentials.json`). Modelo: claude-haiku-4-5.
NOTA (hallazgo #3 A2.2): `options.client` fuerza `is_oauth=False` ⇒ el motor NO mapea
nombres de tool a los canónicos CC (`_to_cc_name` bypassed, anthropic.py:248/643). Para una
tool CUSTOM (`add_numbers`, no un builtin CC) esto es lo correcto: el nombre round-trippea
verbatim. El cabo forward #3 quedaba así NEUTRALIZADO para tools de nombre propio.
"""

from __future__ import annotations

import asyncio
import json
import ssl
from pathlib import Path
from typing import Any

from skeleton.bridge import AgenticModelsCaller
from skeleton.contracts import (
    DoneEvent,
    ResultEvent,
    RuntimeTask,
    ToolCallEvent,
    ToolResultEvent,
)
from skeleton.runtime import LocalAgentRuntime
from skeleton.stubs import PassthroughInputProcessor
from skeleton.tools import AddTool, ToolPool

_MODEL_ID = "claude-haiku-4-5"
_CRED_PATH = Path.home() / ".claude" / ".credentials.json"

# --- SHIM DE ENTORNO (idéntico a _motor; no es parte de la costura) ----------
_orig_ctx = ssl.create_default_context


def _lenient_ctx(*args: Any, **kwargs: Any) -> ssl.SSLContext:
    ctx = _orig_ctx(*args, **kwargs)
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def _install_tls_shim() -> None:
    setattr(ssl, "create_default_context", _lenient_ctx)


def _load_oauth_token() -> str:
    data = json.loads(_CRED_PATH.read_text())
    token: str = data["claudeAiOauth"]["accessToken"]
    return token


async def _main() -> int:
    import agentic_models as am
    from anthropic import AsyncAnthropic

    _install_tls_shim()
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

    caller = AgenticModelsCaller(model, client=oauth_client)
    pool = ToolPool([AddTool()])
    runtime = LocalAgentRuntime(
        caller=caller,
        input_processor=PassthroughInputProcessor(),
        model_id=_MODEL_ID,
        system_prompt=(
            "You are Claude Code, Anthropic's official CLI for Claude.\n\n"
            "Cuando necesites sumar, USA la herramienta add_numbers en vez de calcular tú. "
            "Responde en una sola frase, en español."
        ),
        temperature=0.0,
        max_tokens=256,
        metadata={"user_id": "opaque-owner"},
        tool_pool=pool,
    )
    task = RuntimeTask(
        prompt="¿Cuánto es 17 más 25? Usa la herramienta.",
        owner_id="opaque-owner",
        session_id="opaque-sess",
    )

    print(f"--- turno REAL con TOOL (S16 → dispatch → re-entrada · {_MODEL_ID}) ---")
    saw_tool_call = False
    flattened = ""
    result: ResultEvent | None = None
    usage_line = ""
    async for event in runtime.stream(task):
        name = type(event).__name__
        if isinstance(event, ToolCallEvent):
            saw_tool_call = True
            print(f"  {name}: name={event.name!r} input={event.input!r}")
        elif isinstance(event, ToolResultEvent):
            flattened = event.output
            print(f"  {name}: call_id={event.call_id!r} output={event.output!r} is_error={event.is_error}")
        elif isinstance(event, DoneEvent):
            u = event.usage
            usage_line = (
                f"in={u.input_tokens} out={u.output_tokens} total={u.total_tokens} "
                f"cost_usd={u.cost_usd:.6f} stop={event.stop_reason}"
            )
            print(f"  {name}: {usage_line}")
        elif isinstance(event, ResultEvent):
            result = event
            print(f"  {name}: text={event.text!r}")
        else:
            print(f"  {name}: {event!r}")

    # --- gate A2.3: el modelo LLAMÓ la tool, el resultado se APLANÓ (42), y la
    #     respuesta final lo cita (el modelo re-entró con el tool_result). ---
    print("\n--- gate A2.3 (turno real) ---")
    final_ok = bool(result and "42" in result.text)
    print(f"  tool invocada por el modelo = {saw_tool_call}")
    print(f"  resultado aplanado          = {flattened!r}   (esperado '42')")
    print(f"  respuesta final cita 42     = {final_ok}")
    ok = saw_tool_call and flattened == "42" and final_ok
    acc = result.usage if result else None
    acc_line = (
        f"in={acc.input_tokens} out={acc.output_tokens} total={acc.total_tokens} "
        f"cost_usd={acc.cost_usd:.6f}"
        if acc
        else "(sin ResultEvent)"
    )
    print(f"  (última vuelta: {usage_line})")
    print(f"\nVEREDICTO turno: {'OK' if ok else 'FALLO'} | usage ACUMULADO (2 vueltas): {acc_line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
