"""Evidencia del ciclo A2.4 — COMPOSICIÓN de una battery + costura de sesión (S20).

Gate PLAN §4 A2.4: "la battery se anuncia/consume **sin que el base la conozca**" +
"el turno corre **sin userId**". Es un gate ARQUITECTÓNICO (composición), no "1 turno
real" (eso fue A2.2/A2.3; el end-to-end real es A2.5) ⇒ se valida OFFLINE con callers
CANNED deterministas, más `mypy --strict` + `ruff` limpios. Este runner es el
integrador/compositor del spike: es el ÚNICO módulo que importa la battery.

    cd agentic_runtime && PYTHONPATH=src/HOMOLOGATION/SEPARACION \
      .venv/bin/python -m skeleton._battery

Demuestra dos cosas:
  (A) S9 composición — el MISMO turno corre SIN battery (base default, trigger inerte) y
      CON battery inyectada (el trigger del loop dispara el motor y funde el historial),
      probando que el base es agnóstico: sólo conoce el Protocol `CompactionMotor`.
  (B) S20 identidad — se crea la sesión en el repo con metadata RICA, el turno viaja con
      SÓLO el `SessionId` OPACO (sin owner/userId en el camino loop→modelo), y el
      integrador scopea por SU metadata (`list`). La identidad vive en el repo, no en el base.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping

from skeleton.battery_compaction import (
    SimpleCompactionBattery,  # ← ÚNICO import de la battery
)
from skeleton.contracts import (
    CompactBoundaryEvent,
    Event,
    Message,
    ResultEvent,
    RuntimeTask,
    ToolSchema,
)
from skeleton.runtime import LocalAgentRuntime
from skeleton.seams import AbortSignal, ModelCallerProtocol
from skeleton.stubs import (
    InMemorySessionRepo,
    PassthroughInputProcessor,
    StubToolModelCaller,
)
from skeleton.tools import AddTool, ToolPool


class _MetadataProbe:
    """Envuelve un caller (S1) y REGISTRA la metadata que el base le pasó — evidencia dura
    de que el turno S20 corre SIN userId (el base no threadea identidad al seam del modelo)."""

    def __init__(self, inner: ModelCallerProtocol) -> None:
        self._inner = inner
        self.seen_metadata: list[Mapping[str, str] | None] = []

    def supports_native_tool_search(self) -> bool:
        return self._inner.supports_native_tool_search()

    def complete(
        self,
        messages: list[Message],  # el probe no inspecciona el historial; delega tal cual
        tools: list[ToolSchema],
        *,
        model_id: str,
        stop: AbortSignal,
        system_override: str | None = None,
        system_sections: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, str] | None = None,
        effort: str | None = None,
    ) -> AsyncIterator[Event]:
        self.seen_metadata.append(metadata)
        return self._inner.complete(
            messages,
            tools,
            model_id=model_id,
            stop=stop,
            system_override=system_override,
            system_sections=system_sections,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
            effort=effort,
        )


def _new_tool_caller() -> StubToolModelCaller:
    return StubToolModelCaller(tool_name="add_numbers", tool_input={"a": 17, "b": 25})


async def _run_turn(
    *,
    compose_battery: bool,
    metadata: Mapping[str, str] | None,
    session_id: str,
) -> tuple[int, str]:
    """Corre el turno canned de tool. Devuelve (nº de CompactBoundaryEvent, texto final)."""
    probe = _MetadataProbe(_new_tool_caller())
    runtime = LocalAgentRuntime(
        caller=probe,
        input_processor=PassthroughInputProcessor(),
        tool_pool=ToolPool([AddTool()]),
        metadata=metadata,
        # Composición: la battery se INYECTA por fuera (S27). `None` = base sin battery.
        compaction=SimpleCompactionBattery(threshold=3, keep_last=2) if compose_battery else None,
    )
    task = RuntimeTask(prompt="suma 17 y 25", session_id=session_id)  # SÓLO id opaco

    boundaries = 0
    final = ""
    async for event in runtime.stream(task):
        if isinstance(event, CompactBoundaryEvent):
            boundaries += 1
            print(f"    CompactBoundaryEvent: collapsed={event.collapsed} reason={event.reason!r}")
        elif isinstance(event, ResultEvent):
            final = event.text
    # Evidencia S20: el base NUNCA recibió userId por el seam del modelo.
    assert all(
        m is None or "user_id" not in m for m in probe.seen_metadata
    ), f"userId se filtró al seam del modelo: {probe.seen_metadata}"
    return boundaries, final


async def _main() -> int:
    print("=== A2.4 · (A) COMPOSICIÓN de battery (S9) — base agnóstico ===")
    repo = InMemorySessionRepo()

    # (B) S20: sesión con metadata RICA → id OPACO. El base jamás ve la metadata.
    session_id = repo.create({"owner": "acme/rubén", "tenant": "acme", "plan": "pro"})
    print(f"  repo.create(metadata rica) → SessionId OPACO = {session_id!r}")
    assert session_id.startswith("sess_")

    # Mismo turno, SIN battery (base default) y CON battery compuesta. metadata=None ⇒
    # el turno corre SIN userId (sólo el SessionId opaco viaja en el task).
    print("\n  [sin battery] base default, trigger inerte:")
    n_without, text_without = await _run_turn(
        compose_battery=False, metadata=None, session_id=session_id
    )
    print(f"    → CompactBoundaryEvent={n_without} · final={text_without!r}")

    print("\n  [con battery] SimpleCompactionBattery inyectada por el integrador:")
    n_with, text_with = await _run_turn(
        compose_battery=True, metadata=None, session_id=session_id
    )
    print(f"    → CompactBoundaryEvent={n_with} · final={text_with!r}")

    print("\n=== A2.4 · (B) IDENTIDAD en el repo (S20) — integrador scopea por SU metadata ===")
    # Otra sesión de otro tenant, para probar el scoping del integrador.
    other = repo.create({"owner": "globex/ana", "tenant": "globex", "plan": "free"})
    scoped = repo.list({"tenant": "acme"})
    print(f"  repo.list({{'tenant':'acme'}}) = {scoped}  (excluye {other!r} de globex)")
    meta = repo.get_metadata(session_id)
    print(f"  repo.get_metadata({session_id!r}) = {meta}  (vive en el repo, NO en el base)")

    # --- gate A2.4 ---
    print("\n=== gate A2.4 ===")
    base_agnostic = n_without == 0 and n_with >= 1
    behavior_preserved = "42" in text_without and "42" in text_with
    identity_in_repo = scoped == [session_id] and meta is not None and "tenant" in meta
    turn_without_userid = True  # asegurado por el assert de `probe.seen_metadata` en cada turno
    print(f"  base agnóstico (trigger inerte sin battery / dispara con battery) = {base_agnostic}")
    print(f"  comportamiento preservado (ambos turnos citan 42)               = {behavior_preserved}")
    print(f"  turno corre SIN userId (metadata del modelo sin user_id)        = {turn_without_userid}")
    print(f"  identidad vive en el repo (scoping por metadata del integrador) = {identity_in_repo}")
    ok = base_agnostic and behavior_preserved and identity_in_repo and turn_without_userid
    print(f"\nVEREDICTO A2.4: {'OK' if ok else 'FALLO'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
