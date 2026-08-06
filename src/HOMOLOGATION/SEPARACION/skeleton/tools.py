"""Infraestructura de TOOLS del walking skeleton (ciclo A2.3).

Cablea la costura **S16** (`ToolProtocol`) con los mecanismos-base que SEAMS.md §2 nota
como "firma = base, no rellenable": `ToolPool` (assemble/find, invariante pool-único
09·C1-C4/D1) y `ToolDispatcher` (dispatch+timeout 09·D1/D5). Y la costura **S26**
(`DeferredToolStrategy`) en su realización EAGER por defecto (con 1 tool no hay nada que
diferir; las ramas Simulada/Nativa quedan declaradas, no ejercitadas — L09).

Gate A2.3 (PLAN §4): el modelo llama la tool y el resultado se APLANA de vuelta al turno.
Evidencia: `skeleton._tools` (turno real) + `_smoke` canned multivuelta.
"""

from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

from skeleton.contracts import (
    ToolCall,
    ToolResult,
    ToolResultEvent,
    ToolSchema,
)
from skeleton.seams import StubToolContext, SubagentSpec, ToolProtocol


# --- S26 · DeferredToolStrategy (T2-COSTURA) — realización EAGER por defecto ---
@runtime_checkable
class DeferredToolStrategy(Protocol):
    """SEAMS §S26. Decide cómo se anuncian las tools al modelo. El productor
    (`AgentLoop`) elige la estrategia por `caller.supports_native_tool_search()`:
    - **Eager** (default base): anuncia TODO el pool; nadie posee search-dispatch.
    - **Simulada** (battery tool-search): filtra por descubrimiento client-side.
    - **Nativa** (`defer_loading` server-side): el provider resuelve el search.
    A2.3 sólo EJERCITA la eager (1 tool → nada que diferir).

    ⚠ DESACTUALIZADO respecto a producción (11ª ventana, `FIND-E2G-3`): `owns_search_dispatch`
    fue RETIRADO de `tools/deferred_strategy.py` por redundante —el hecho ya lo codifica
    `tool_schemas`— y porque A no tiene contraparte: su ToolSearch es client-side y punto,
    de modo que el dilema «¿quién despacha?» no existe en el canónico. Este fichero se
    conserva como artefacto de diseño histórico; NO es fuente de estado."""

    def owns_search_dispatch(self) -> bool: ...  # RETIRADO en producción — ver nota arriba

    def filter_announced(
        self, pool: ToolPool, discovered: frozenset[str]
    ) -> list[ToolSchema]: ...

    def should_defer_turn(self, pool: ToolPool, model_id: str) -> bool: ...  # 09·E9 auto-mode


class EagerToolStrategy:
    """Realiza S26 sin diferir nada: anuncia el pool entero. Base default hasta que la
    battery `tool-search` (A3·10) sustituya por la Simulada/Nativa."""

    def owns_search_dispatch(self) -> bool:
        return False

    def filter_announced(
        self, pool: ToolPool, discovered: frozenset[str]
    ) -> list[ToolSchema]:
        return pool.announced_schemas()

    def should_defer_turn(self, pool: ToolPool, model_id: str) -> bool:
        return False


# --- ToolPool (mecanismo base: assemble/find; invariante pool-único) ----------
class ToolPool:
    """09·C1-C4/D1 — colección única de tools del turno. `find` por nombre;
    `announced_schemas` proyecta al contrato que el caller anuncia al modelo (S1)."""

    def __init__(self, tools: list[ToolProtocol] | None = None) -> None:
        self._by_name: dict[str, ToolProtocol] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: ToolProtocol) -> None:
        # Invariante pool-único: un nombre = una tool (09·C-dedup).
        self._by_name[tool.name] = tool

    def find(self, name: str) -> ToolProtocol | None:
        return self._by_name.get(name)

    def announced_schemas(self) -> list[ToolSchema]:
        return [
            ToolSchema(
                name=t.name,
                description=t.description(None),
                input_schema=t.input_schema,
            )
            for t in self._by_name.values()
        ]

    def __len__(self) -> int:
        return len(self._by_name)


# --- ToolDispatcher (mecanismo base: dispatch + timeout; aplana ToolResult) ----
class ToolDispatcher:
    """09·D1/D5 — ejecuta UNA tool pedida por el modelo y APLANA el resultado a un
    `ToolResultEvent` (lo que re-entra al modelo). Aísla el fallo: una tool ausente,
    una excepción o un timeout se aplanan a `is_error=True`, nunca tumban el turno."""

    def __init__(self, pool: ToolPool, *, timeout_seconds: float | None = 30.0) -> None:
        self._pool = pool
        self._timeout = timeout_seconds

    async def dispatch(self, call: ToolCall, ctx: StubToolContext) -> ToolResultEvent:
        tool = self._pool.find(call.name)
        if tool is None:
            return ToolResultEvent(
                call_id=call.call_id,
                output=f"tool not found: {call.name}",
                is_error=True,
            )
        try:
            coro = tool.execute(call.input, ctx)
            result: ToolResult = (
                await asyncio.wait_for(coro, self._timeout)
                if self._timeout is not None
                else await coro
            )
        except asyncio.TimeoutError:
            return ToolResultEvent(
                call_id=call.call_id,
                output=f"tool timed out after {self._timeout}s: {call.name}",
                is_error=True,
            )
        except Exception as exc:  # noqa: BLE001 — 09·D5: aislar el fallo de la tool.
            return ToolResultEvent(
                call_id=call.call_id,
                output=f"tool error: {type(exc).__name__}: {exc}",
                is_error=True,
            )
        return ToolResultEvent(
            call_id=call.call_id,
            output=result.output,
            is_error=result.is_error,
        )


# --- AddTool — 1 tool nativa (realiza S16) — determinista, invocable por el modelo ---
class AddTool:
    """Realiza `ToolProtocol` (S16). Suma dos enteros: determinista y verificable, de
    modo que el turno real prueba el round-trip completo (el modelo la invoca, el
    resultado se aplana, y el modelo redacta la respuesta con el número devuelto)."""

    name: str = "add_numbers"
    input_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "a": {"type": "integer", "description": "primer sumando"},
            "b": {"type": "integer", "description": "segundo sumando"},
        },
        "required": ["a", "b"],
    }

    def description(self, input: dict[str, object] | None = None) -> str:
        return "Suma dos números enteros y devuelve el total. Úsala para cualquier suma."

    async def execute(self, input: dict[str, object], ctx: StubToolContext) -> ToolResult:
        try:
            a = int(str(input["a"]))
            b = int(str(input["b"]))
        except (KeyError, TypeError, ValueError) as exc:
            return ToolResult(output=f"invalid input: {exc}", is_error=True)
        return ToolResult(output=str(a + b))


# --- AgentTool — la tool `agent` que SPAWNEA un subagente vía S18 (ciclo A2.5) ------
class AgentTool:
    """Realiza `ToolProtocol` (S16). Es el productor de la costura CRÍTICA S18: su `execute`
    lee `ctx.runner` (el `SubagentRunnerProtocol` que el factory pobló) y delega una subtarea
    a un subagente aislado, aplanando su texto final de vuelta al turno del padre.

    Aquí vive el fix del bug mímica (05·E24): si `ctx.runner is None` —el factory NO cableó la
    costura— el spawn FALLA de forma visible (`is_error`) en vez de lanzar en tiempo de ejecución.
    El turno end-to-end de A2.5 prueba que el factory SÍ lo cablea (L09: cableado, no existencia)."""

    name: str = "agent"
    input_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "la subtarea a delegar al subagente"},
            "subagent_type": {
                "type": "string",
                "description": "tipo de subagente (opcional)",
            },
        },
        "required": ["prompt"],
    }

    def description(self, input: dict[str, object] | None = None) -> str:
        return (
            "Delega una subtarea a un subagente aislado y devuelve su resultado. "
            "Úsala para cualquier cálculo o subtarea que otro agente deba resolver."
        )

    async def execute(self, input: dict[str, object], ctx: StubToolContext) -> ToolResult:
        runner = ctx.runner
        if runner is None:
            # Costura S18 SIN poblar: el factory no inyectó el runner. Reproduce el síntoma
            # de la mímica (spawn imposible), pero contenido como error de tool, no crash.
            return ToolResult(
                output="subagent runner not wired (S18 sin poblar por el factory)",
                is_error=True,
            )
        prompt = input.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            return ToolResult(output="missing 'prompt' for subagent", is_error=True)
        raw_type = input.get("subagent_type")
        spec = SubagentSpec(
            prompt=prompt,
            subagent_type=str(raw_type) if isinstance(raw_type, str) and raw_type else None,
            parent_session_id=ctx.task.session_id,  # id opaco heredado (S20)
        )
        result = await runner.run(spec, background=False)
        return ToolResult(output=result or "")
