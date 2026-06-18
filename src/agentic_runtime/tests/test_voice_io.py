"""I/O por voz: STT entra como prompt, TTS deriva la salida incremental, ambos
canales se activan/desactivan por configuración.

El runtime solo aporta primitivas + plomería; aquí los motores STT/TTS son fakes
(los inyecta el integrador). Lo único que se verifica es el cableado:
  (a) STT: el audio adjunto se transcribe y llega al modelo COMO prompt.
  (b) TTS: cada fragmento del stream se deriva ya saneado, con flush al cerrar.
  (c) config: con el flag apagado, el canal no se invoca.
  (d) saneo: el texto pasa por `PathPresentation` antes del TTS.
  (e) los subagentes no hablan.
"""
from __future__ import annotations

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, TokenEvent
from agentic_runtime.events.bus import EventBus
from agentic_runtime.execution.local.runtime import LocalAgentRuntime
from agentic_runtime.factory import (
    RuntimeConfig,
    StorageConfig,
    VoiceConfig,
    create_runtime,
)
from agentic_runtime.voice import AudioInput


class _FakeSTT:
    def __init__(self, text: str) -> None:
        self._text = text
        self.calls: list[AudioInput] = []

    async def transcribe(self, audio: AudioInput, ctx) -> str:
        self.calls.append(audio)
        return self._text


class _FakeTTS:
    def __init__(self) -> None:
        self.spoken: list[str] = []
        self.flushes = 0

    async def speak(self, text: str, ctx) -> None:
        self.spoken.append(text)

    async def flush(self, ctx) -> None:
        self.flushes += 1


class _StreamingCaller:
    """Captura el prompt (primer 'user') y emite un stream de tokens fijo."""

    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks
        self.user_prompts: list[str] = []

    async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
        for m in messages:
            if m.get("role") == "user":
                self.user_prompts.append(m.get("content") or "")
                break

        chunks = self._chunks

        async def gen():
            for c in chunks:
                yield TokenEvent(content=c)
            yield DoneEvent(stop_reason="stop")

        return gen()


class _RealPathPresentation:
    """Presentación que oculta una ruta real tras un token falso (espejo infra)."""

    def to_llm(self, host_path):  # pragma: no cover - no usado aquí
        return str(host_path)

    def sanitize_output(self, text: str) -> str:
        return text.replace("/srv/secreto", "[ruta]")


async def _dispatch_and_wait(runtime, task: RuntimeTask) -> None:
    await runtime.startup()
    try:
        task_id = await runtime.dispatch(task)
        rec = runtime._task_registry.get(task_id)
        await rec.asyncio_task
    finally:
        await runtime.shutdown()


# ---------------------------------------------------------------------------
# STT (entrada → prompt)
# ---------------------------------------------------------------------------

async def test_stt_transcription_arrives_as_prompt(tmp_path):
    stt = _FakeSTT("arregla el login de sesión")
    caller = _StreamingCaller([])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        voice=VoiceConfig(stt=stt),
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(
        prompt="", description="voz", audio_prompt=AudioInput(data=b"\x00\x01"),
    ))
    assert stt.calls, "el STT no se invocó"
    assert caller.user_prompts == ["arregla el login de sesión"]


async def test_stt_disabled_uses_text_prompt(tmp_path):
    stt = _FakeSTT("transcripción que no debe usarse")
    caller = _StreamingCaller([])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        voice=VoiceConfig(stt=stt, stt_enabled=False),  # canal apagado por config
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(
        prompt="texto directo", description="voz", audio_prompt=AudioInput(data=b"x"),
    ))
    assert stt.calls == []
    assert caller.user_prompts == ["texto directo"]


async def test_stt_without_audio_keeps_text_prompt(tmp_path):
    stt = _FakeSTT("no aplica")
    caller = _StreamingCaller([])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        voice=VoiceConfig(stt=stt),
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(prompt="solo texto", description="voz"))
    assert stt.calls == []
    assert caller.user_prompts == ["solo texto"]


# ---------------------------------------------------------------------------
# TTS (salida incremental)
# ---------------------------------------------------------------------------

async def test_tts_speaks_each_chunk_incrementally_then_flush(tmp_path):
    tts = _FakeTTS()
    caller = _StreamingCaller(["Hola ", "mundo", "."])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        voice=VoiceConfig(tts=tts),
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(prompt="saluda", description="voz"))
    assert tts.spoken == ["Hola ", "mundo", "."]  # fragmento a fragmento, sin esperar el fin
    assert tts.flushes == 1


async def test_tts_disabled_does_not_speak(tmp_path):
    tts = _FakeTTS()
    caller = _StreamingCaller(["algo"])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        voice=VoiceConfig(tts=tts, tts_enabled=False),  # canal apagado por config
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(prompt="saluda", description="voz"))
    assert tts.spoken == []
    assert tts.flushes == 0


async def test_tts_text_is_sanitized_by_presentation(tmp_path):
    tts = _FakeTTS()
    caller = _StreamingCaller(["el log está en /srv/secreto/app.log"])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        presentation=_RealPathPresentation(),
        voice=VoiceConfig(tts=tts),
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(prompt="dónde", description="voz"))
    assert tts.spoken == ["el log está en [ruta]/app.log"]
    assert all("/srv/secreto" not in s for s in tts.spoken)


# ---------------------------------------------------------------------------
# Subagentes no hablan + flush solo al cerrar el turno de habla
# ---------------------------------------------------------------------------

async def test_subagent_does_not_speak():
    tts = _FakeTTS()
    runtime = LocalAgentRuntime(tts=tts)
    bus = EventBus()
    ctx = ToolUseContext(session_id="s", agent_id="a", is_subagent=True)
    runtime._wire_tts(bus, ctx)  # no debe suscribir nada
    await bus.emit(TokenEvent(content="texto"))
    await bus.emit(DoneEvent(stop_reason="stop"))
    assert tts.spoken == [] and tts.flushes == 0


async def test_tts_no_flush_on_tool_call_turn():
    tts = _FakeTTS()
    runtime = LocalAgentRuntime(tts=tts)
    bus = EventBus()
    ctx = ToolUseContext(session_id="s", agent_id="a")
    runtime._wire_tts(bus, ctx)
    await bus.emit(TokenEvent(content="pensando"))
    await bus.emit(DoneEvent(stop_reason="tool_calls"))  # corte por tools, no fin de habla
    assert tts.spoken == ["pensando"]
    assert tts.flushes == 0
