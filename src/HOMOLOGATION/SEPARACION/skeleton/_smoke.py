"""Smoke del andamiaje A2.1 — corre un turno CANNED end-to-end por las costuras.

El gate FORMAL de A2.1 es `typechecks` (PLAN §4); este smoke es evidencia EXTRA barata
de que el cableado de costuras es coherente y el canal ordenado emite Init -> Token ->
Done -> Result. NO usa modelo real (eso es A2.2). Correr:

    cd agentic_runtime && PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._smoke
"""

from __future__ import annotations

import asyncio

from skeleton.contracts import ResultEvent, RuntimeTask, ToolResultEvent
from skeleton.runtime import LocalAgentRuntime
from skeleton.stubs import (
    PassthroughInputProcessor,
    StubModelCaller,
    StubToolModelCaller,
)
from skeleton.tools import AddTool, ToolPool


async def _text_turn() -> None:
    runtime = LocalAgentRuntime(
        caller=StubModelCaller(),
        input_processor=PassthroughInputProcessor(),
    )
    task = RuntimeTask(prompt="hola andamiaje", owner_id="opaque-owner", session_id="opaque-sess")

    print("--- canal único ordenado (S5) · texto-solo (A2.1) ---")
    async for event in runtime.stream(task):
        print(f"  {type(event).__name__}: {event!r}")


async def _tool_turn() -> int:
    """Round-trip de tool CANNED (A2.3): el caller pide `add_numbers(17,25)`; el dispatcher
    ejecuta la tool nativa y APLANA `42`; el caller cierra con texto que lo cita."""
    pool = ToolPool([AddTool()])
    runtime = LocalAgentRuntime(
        caller=StubToolModelCaller(tool_name="add_numbers", tool_input={"a": 17, "b": 25}),
        input_processor=PassthroughInputProcessor(),
        tool_pool=pool,
    )
    task = RuntimeTask(prompt="suma 17 y 25", owner_id="opaque-owner", session_id="opaque-sess")

    print("\n--- round-trip de tool CANNED (S16 dispatch · A2.3) ---")
    flattened = ""
    final = ""
    async for event in runtime.stream(task):
        print(f"  {type(event).__name__}: {event!r}")
        if isinstance(event, ToolResultEvent):
            flattened = event.output
        elif isinstance(event, ResultEvent):
            final = event.text
    ok = flattened == "42" and "42" in final
    print(f"  gate A2.3 (canned): resultado aplanado={flattened!r} · final cita 42={'42' in final} → {'OK' if ok else 'FALLO'}")
    return 0 if ok else 1


async def _main() -> int:
    await _text_turn()
    return await _tool_turn()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
