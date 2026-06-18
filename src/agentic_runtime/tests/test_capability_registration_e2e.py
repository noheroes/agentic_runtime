"""E2E de REGISTRO de MCP + skill: se persiste en un store que el runtime encuentra
al arrancar, y se verifica que operan con normalidad en un turno real.

- Transporte MCP **Streamable HTTP REAL** (FastMCP en `_mcp_echo_server.py --http`), no
  fake — es el tipo que usa el `wiki` del usuario (type: http).
- El integrador EXTRAE su JSON de registro al contrato `McpServerConfig` (simulado por
  `_extract_mcp`); el contrato no se deforma para tragar el JSON externo.
- Un server inalcanzable (estilo `wiki` sin servidor) se aísla (FAILED) sin tumbar al resto.
"""
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from agentic_runtime.capabilities.mcp import StorageBackedMcpConfigStore
from agentic_runtime.capabilities.skills import StorageBackedSkillStore
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.factory import CapabilitiesConfig, RuntimeConfig, StorageConfig, create_runtime
from agentic_runtime.storage.filesystem import FilesystemStorage

_SERVER = str((Path(__file__).parent / "_mcp_echo_server.py").resolve())


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_port(port: int, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.2)
    return False


def _self_signed_cert(dirpath: Path) -> tuple[str, str]:
    """Genera un cert self-signed (CN=localhost) — el server lo usa para TLS y el
    cliente debe aceptarlo SOLO con ssl_verify=False (cert no confiable)."""
    cert, key = dirpath / "cert.pem", dirpath / "key.pem"
    rc = subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(key), "-out", str(cert), "-days", "1",
         "-subj", "/CN=localhost"],
        capture_output=True,
    )
    if rc.returncode != 0:
        pytest.skip(f"openssl no disponible: {rc.stderr.decode()[:200]}")
    return str(cert), str(key)


def _start_https_server(port: int, cert: str, key: str) -> subprocess.Popen:
    proc = subprocess.Popen([sys.executable, _SERVER, "--https", str(port), cert, key])
    if not _wait_port(port):
        proc.terminate()
        raise RuntimeError("el server MCP HTTPS no levantó a tiempo")
    return proc

_OFFICE_SKILL = (
    "---\n"
    "name: office\n"
    "description: edita documentos de oficina\n"
    "allowed-tools: echo_upper\n"
    "---\n"
    "Para editar, usa la tool echo_upper."
)


def _extract_mcp(name: str, registry_json: dict) -> dict:
    """Capa del INTEGRADOR: extrae lo relevante de su JSON de registro y lo mapea al
    contrato de capabilities. NO se mete el JSON externo crudo en McpServerConfig."""
    auth = registry_json.get("auth") or {}
    mapped: dict = {
        "type": registry_json["type"],
        "url": registry_json.get("url"),
        "ssl_verify": registry_json.get("ssl_verify", True),
    }
    if isinstance(auth, dict) and auth.get("type") == "bearer":
        mapped["auth"] = "bearer"
        mapped["token"] = auth.get("token")
    return {k: v for k, v in mapped.items() if v is not None}


class _ScriptedCaller:
    """Conduce: turno1 Skill(office) → habilita echo_upper; turno2 echo_upper; fin."""

    def __init__(self):
        self.turns: list[list[str]] = []
        self.last_messages: list = []

    async def complete(self, messages, tools, *, stop=None, model_id=""):
        self.turns.append([t["name"] for t in tools])
        self.last_messages = list(messages)
        n = len(self.turns)

        async def gen():
            if n == 1:
                yield ToolCallEvent(tool_name="Skill", tool_input={"command": "office"}, call_id="c1")
                yield DoneEvent(stop_reason="tool_calls")
            elif n == 2:
                yield ToolCallEvent(tool_name="echo_upper", tool_input={"text": "hola mundo"}, call_id="c2")
                yield DoneEvent(stop_reason="tool_calls")
            else:
                yield TokenEvent(content="listo")
                yield DoneEvent(stop_reason="stop")

        return gen()


async def test_register_and_operate_mcp_and_skill_end_to_end(tmp_path):
    port = _free_port()
    cert, key = _self_signed_cert(tmp_path)
    server = _start_https_server(port, cert, key)
    try:
        storage = FilesystemStorage(root=tmp_path)

        # --- el integrador REGISTRA (persiste) en los stores ---
        mcp_store = StorageBackedMcpConfigStore(storage)
        # server Streamable HTTP REAL sobre TLS self-signed (alcanzable) — estilo 'wiki'.
        # El integrador EXTRAE su JSON de registro al contrato (incluye ssl_verify=False).
        wiki_registry = {
            "type": "http", "enabled": True, "url": f"https://127.0.0.1:{port}/mcp",
            "auth": {"type": "bearer", "token": "x"}, "ssl_verify": False, "system": True,
        }
        local_cfg = _extract_mcp("wiki", wiki_registry)
        local_cfg.pop("auth", None)  # el server de prueba no exige auth; conservamos ssl_verify
        local_cfg.pop("token", None)
        await mcp_store.save("local", local_cfg)
        # un server inalcanzable: debe AISLARSE (FAILED) sin tumbar al resto
        await mcp_store.save("dead", {"type": "http", "url": f"https://127.0.0.1:{_free_port()}/mcp"})

        skill_store = StorageBackedSkillStore(storage)
        await skill_store.write("office", _OFFICE_SKILL)

        # --- el runtime ENCUENTRA lo registrado al arrancar ---
        caller = _ScriptedCaller()
        runtime = create_runtime(config=RuntimeConfig(
            storage=StorageConfig(backend="filesystem", root=tmp_path),
            model_caller=caller,
            capabilities=CapabilitiesConfig(mcp_config_store=mcp_store, skill_store=skill_store),
        ))
        await runtime.startup()

        try:
            mcp = [p for p in runtime._capability_manager.providers if p.name == "mcp"][0]
            # conectó al server TLS self-signed gracias a ssl_verify=False
            assert mcp.state.status("local").value == "connected"
            assert mcp.state.status("dead").value == "failed"  # aislado, no abortó al resto

            task_id = await runtime.dispatch(RuntimeTask(prompt="haz la tarea", description="e2e"))
            rec = runtime._task_registry.get(task_id)
            await rec.asyncio_task  # espera a que el turno real termine
        finally:
            await runtime.shutdown()
    finally:
        server.terminate()
        server.wait(timeout=10)

    # turno 1: Skill y ToolSearch visibles; echo_upper diferido oculto
    assert "Skill" in caller.turns[0]
    assert "ToolSearch" in caller.turns[0]
    assert "echo_upper" not in caller.turns[0]
    # turno 2: tras invocar la skill, echo_upper anunciado (descubierto + permitido)
    assert "echo_upper" in caller.turns[1]
    # operó con normalidad: el server MCP REAL (Streamable HTTP/TLS) devolvió mayúsculas
    contents = " ".join(str(m.get("content", "")) for m in caller.last_messages)
    assert "HOLA MUNDO" in contents


async def test_ssl_verify_true_rejects_self_signed(tmp_path):
    """Contraprueba: con ssl_verify=True (default) el cert self-signed se RECHAZA.
    Demuestra que el flag se respeta en ambos sentidos."""
    port = _free_port()
    cert, key = _self_signed_cert(tmp_path)
    server = _start_https_server(port, cert, key)
    try:
        from agentic_runtime.capabilities.mcp import McpProvider

        provider = McpProvider()
        provider.add_server("strict", {"type": "http", "url": f"https://127.0.0.1:{port}/mcp"})  # ssl_verify default True
        ok = await provider.connect_server("strict")
        assert ok is False
        assert provider.state.status("strict").value == "failed"
        await provider.shutdown()
    finally:
        server.terminate()
        server.wait(timeout=10)
