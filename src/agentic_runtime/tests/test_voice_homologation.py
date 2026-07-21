"""Homologación 17·voice — `voice/{protocol,__init__}.py` + el cableado en
`execution/local/runtime.py` (`_resolve_prompt` STT, `_wire_tts` TTS) + el gate en `factory.py::VoiceConfig`,
vs el árbol voice canónico (`services/voice*`, `hooks/useVoice*`, `context/voice.tsx`, `commands/voice/`).

Ver `src/HOMOLOGATION/17-voice.md`. El core STT (audio→prompt), el gate por-canal, la derivación TTS
incremental, subagentes-mudos y el no-flush-en-tool_calls **ya están homologados** y se codifican en
`test_voice_io.py` (comportamiento cableado). El canónico es **STT-only** (no hay TTS: verificado con grep) y
**push-to-talk terminal** (motor STT = integrador; keybindings/prompt-input/`/voice` = front), por lo que la
mayoría del canónico es ⛔-integrador/⛔-front, no gap.

El único `xfail(strict=True)` codifica **FIND-VOICE1 / VoR1**: `_wire_tts` sanea `sanitize_output` **por-chunk**,
así que una ruta real partida entre dos `TokenEvent` evade el choke point de `PathPresentation` y se habla en
claro — violando el invariante que el propio `protocol.py` declara ("nunca se leen en voz alta rutas reales de
infra"). Falla HOY; su fallo ES la evidencia del gap. Si empezara a pasar, el strict lo vuelve error → señal de
reclasificar en `17-voice.md`.
"""
from __future__ import annotations

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, TokenEvent
from agentic_runtime.events.bus import EventBus
from agentic_runtime.execution.local.runtime import LocalAgentRuntime


class _FakeTTS:
    def __init__(self) -> None:
        self.spoken: list[str] = []
        self.flushes = 0

    async def speak(self, text: str, ctx) -> None:
        self.spoken.append(text)

    async def flush(self, ctx) -> None:
        self.flushes += 1


class _RealPathPresentation:
    """Oculta una ruta real de infra tras un token falso (espejo de test_voice_io)."""

    def to_llm(self, host_path):  # pragma: no cover - no usado aquí
        return str(host_path)

    def sanitize_output(self, text: str) -> str:
        return text.replace("/srv/secreto", "[ruta]")


# ---------------------------------------------------------------------------
# GAP (xfail strict) — codifica el target de §Plan VoR1
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason="FIND-VOICE1/VoR1: _wire_tts sanea per-chunk; una ruta partida entre dos TokenEvent evade el saneo",
)
async def test_tts_sanitizes_across_chunk_boundary():
    """VoR1: el invariante 'nunca rutas reales de infra en voz alta' debe cumplirse aunque la ruta quede
    partida entre chunks. Con saneo per-chunk, ni `"/srv/sec"` ni `"reto/app.log"` contienen `/srv/secreto`,
    así que `sanitize_output` no matchea y la ruta se reconstruye en `spoken` → fuga. Passing = saneo sobre el
    acumulado en límites seguros restaura el invariante."""
    tts = _FakeTTS()
    runtime = LocalAgentRuntime(tts=tts, presentation=_RealPathPresentation())
    bus = EventBus()
    ctx = ToolUseContext(session_id="s", agent_id="a")
    ctx.presentation = _RealPathPresentation()
    runtime._wire_tts(bus, ctx)

    # La ruta secreta llega partida en la frontera de dos TokenEvent.
    await bus.emit(TokenEvent(content="el log está en /srv/sec"))
    await bus.emit(TokenEvent(content="reto/app.log"))
    await bus.emit(DoneEvent(stop_reason="stop"))

    # Ningún fragmento hablado (ni su concatenación) puede contener la ruta real en claro.
    assert "/srv/secreto" not in "".join(tts.spoken), (
        f"la ruta real se habló en claro por frontera de chunk: {tts.spoken!r}"
    )
