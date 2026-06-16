"""
E2E del runtime ensamblado — vía `create_runtime()`, sin cableado manual.

Dos modos:
  faux (default) : caller determinista, sin red. Evidencia repetible bit a bit.
  real           : provider real (agentic_models + OPENAI_API_KEY). Evidencia con LLM real.

Uso:
    uv run python scripts/e2e_runtime_test.py            # faux
    uv run python scripts/e2e_runtime_test.py --real     # real (requiere OPENAI_API_KEY)
    E2E_REAL=1 uv run python scripts/e2e_runtime_test.py # real por env

El script arma el runtime con create_runtime(), despacha un prompt que fuerza al menos
un tool call, e imprime la traza de turnos / tool dispatch / texto final.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# ── resolución de imports del paquete ──────────────────────────────────────────
_SRC = Path(__file__).resolve().parents[2]  # src/
sys.path.insert(0, str(_SRC))

from agentic_runtime.contracts.runtime import RuntimeTask  # noqa: E402
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent  # noqa: E402
from agentic_runtime.factory import (  # noqa: E402
    RuntimeConfig,
    StorageConfig,
    ToolsConfig,
    create_runtime,
)
from agentic_runtime.tools import ToolCategory, ToolResult  # noqa: E402


# ── tool determinista para el modo faux ────────────────────────────────────────

class EchoTool:
    name = "echo"
    description = "Devuelve el texto recibido"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx) -> ToolResult:
        return ToolResult(tool_name=self.name, output=f"echo:{input.get('text', '')}")


# ── caller faux guionado (stream determinista) ─────────────────────────────────

class FauxScriptedCaller:
    """Reproduce un guion fijo: turno 1 → tool call; turno 2 → texto final."""

    def __init__(self) -> None:
        self._script = [
            [ToolCallEvent(tool_name="echo", tool_input={"text": "ping"}, call_id="c1"),
             DoneEvent(stop_reason="tool_calls")],
            [TokenEvent(content="Listo: la tool echo respondió correctamente."),
             DoneEvent(stop_reason="stop")],
        ]
        self._turn = 0

    async def complete(self, messages, tools, *, stop=None, model_id=""):
        events = self._script[self._turn] if self._turn < len(self._script) else [DoneEvent(stop_reason="stop")]
        self._turn += 1

        async def _gen():
            for ev in events:
                yield ev
        return _gen()


# ── construcción del runtime por modo ──────────────────────────────────────────

def _build_faux(tmp: Path):
    config = RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp),
        model_caller=FauxScriptedCaller(),
        tools=ToolsConfig(extras=[EchoTool()]),
    )
    prompt = "Usa la tool echo con el texto 'ping' y confirma el resultado."
    return create_runtime(config=config), prompt


def _build_real(tmp: Path):
    from agentic_models import get_model, register_builtins
    from agentic_runtime.models.caller import AgenticModelsCaller

    register_builtins()
    api_key = os.environ.get("OPENAI_API_KEY") or ""
    if not api_key:
        print("ERROR: modo real requiere OPENAI_API_KEY en el entorno.", file=sys.stderr)
        sys.exit(2)

    caller = AgenticModelsCaller(
        model=get_model("gpt-4o-mini"),
        api_key=api_key,
        system_prompt="Eres un asistente. Usa las tools disponibles cuando se te pida.",
    )
    config = RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp),
        model_caller=caller,
        model_id="gpt-4o-mini",
    )
    prompt = (
        "Ejecuta `echo hola-e2e` con la tool bash y dime exactamente qué imprimió."
    )
    return create_runtime(config=config), prompt


# ── main ───────────────────────────────────────────────────────────────────────

async def main() -> int:
    real = "--real" in sys.argv or os.environ.get("E2E_REAL") == "1"
    mode = "real" if real else "faux"
    tmp = Path(__file__).parent / f"_e2e_storage_{mode}"

    print("=" * 64)
    print(f"E2E runtime — modo {mode.upper()} — vía create_runtime()")
    print("=" * 64)

    runtime, prompt = _build_real(tmp) if real else _build_faux(tmp)
    print(f"PROMPT: {prompt}\n")

    t0 = time.time()
    task_id = await runtime.dispatch(RuntimeTask(prompt=prompt, description="e2e"))
    rec = runtime._task_registry.get(task_id)
    await rec.asyncio_task
    elapsed = round(time.time() - t0, 2)

    # ── traza de tool dispatch capturada por el registry ──
    print("─ Traza de eventos del runtime ─")
    for ev in rec.events:
        if ev["type"] == "tool_start":
            print(f"  [tool_call]   {ev['name']}({json.dumps(ev['args'], ensure_ascii=False)})")
        elif ev["type"] == "tool_result":
            snippet = str(ev["output"])[:160].replace("\n", "\\n")
            flag = " ERROR" if ev.get("is_error") else ""
            print(f"  [tool_result]{flag} → {snippet}")

    print("\n─ Resultado ─")
    print(f"  status     : {runtime.status(task_id).name}")
    print(f"  turnos     : {rec.turn_count}")
    print(f"  duración   : {elapsed}s")
    print(f"  texto final: {runtime.result(task_id)!r}")

    ok = runtime.status(task_id).name == "COMPLETED" and bool(runtime.result(task_id))
    tool_used = any(e["type"] == "tool_result" for e in rec.events)
    print("\n" + ("OK — runtime completó con tool dispatch." if ok and tool_used
                   else "FALLO — revisar traza."))
    return 0 if ok and tool_used else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
