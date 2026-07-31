"""Evidencia del ciclo A2.2 — un TURNO REAL texto-solo por la costura S1.

Gate PLAN §4 A2.2: "corre 1 turno real". A diferencia del smoke A2.1 (eventos canned),
esto cablea `bridge.AgenticModelsCaller` → `agentic_models` → API real y valida que la
firma S1 enriquecida aguanta: system/temperature/max_tokens/metadata VIAJAN, y vuelve
`Usage` con cache/coste REALES. Correr (venv del runtime tiene agentic_models):

    cd agentic_runtime && PYTHONPATH=src/HOMOLOGATION/SEPARACION \
      .venv/bin/python -m skeleton._motor

Credencial: token OAuth de Claude Code (`~/.claude/.credentials.json`, scope user:inference).
Se lee en runtime y se pasa como api_key; NO se imprime. Modelo: claude-haiku-4-5 (barato).
"""

from __future__ import annotations

import asyncio
import json
import ssl
from pathlib import Path
from typing import Any

from skeleton.bridge import AgenticModelsCaller
from skeleton.contracts import DoneEvent, ResultEvent, RuntimeTask
from skeleton.runtime import LocalAgentRuntime
from skeleton.stubs import PassthroughInputProcessor

_MODEL_ID = "claude-haiku-4-5"
_CRED_PATH = Path.home() / ".claude" / ".credentials.json"


# --- SHIM DE ENTORNO (no es parte de la costura) -----------------------------
# Este WSL corporativo intercepta TLS con un proxy MITM cuya CA openssl 3.x rechaza
# por "Basic Constraints not marked critical" (Node/CLI la tolera vía NODE_EXTRA_CA_CERTS;
# Python no). La CA corporativa YA se carga vía SSL_CERT_FILE; sólo hay que relajar el
# chequeo estricto de encoding — la verificación de cadena sigue activa. Aislado al RUNNER
# del spike; `bridge.py` (la costura real) no lo conoce ni depende de él.
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

    # Cliente OAuth pre-construido (ver HALLAZGO A2.2 en bridge.py): auth_token, SIN api_key,
    # con las betas oauth+CC. `options.client` fuerza is_oauth=False en el motor ⇒ la identidad
    # CC va en el system-prompt de abajo.
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
    # VERIFICACIÓN efecto-en-cable (A2.2, cerrada por reto auto-adversarial): `on_payload`
    # captura el dict `params` EXACTO que va al SDK antes del envío ⇒ prueba que
    # temperature/max_tokens/metadata NO sólo entran al code-path sino que se TRANSMITEN.
    captured: dict[str, Any] = {}

    async def _capture(params: dict[str, Any], _model: Any) -> None:
        captured.update(params)
        return None  # no modifica el payload

    caller = AgenticModelsCaller(model, client=oauth_client, on_payload=_capture)
    runtime = LocalAgentRuntime(
        caller=caller,
        input_processor=PassthroughInputProcessor(),
        model_id=_MODEL_ID,
        # knobs enriquecidos que el turno real DEBE transportar (validación S1). El system
        # antepone la identidad CC (obligatoria bajo OAuth) + la instrucción de la tarea.
        system_prompt=(
            "You are Claude Code, Anthropic's official CLI for Claude.\n\n"
            "Responde en una sola frase, en español."
        ),
        temperature=0.0,
        max_tokens=64,
        metadata={"user_id": "opaque-owner"},  # 【id-opaco】 sólo user_id se reenvía
    )
    task = RuntimeTask(
        prompt="Di 'hola motor' y nada mas.",
        owner_id="opaque-owner",
        session_id="opaque-sess",
    )

    print(f"--- turno REAL texto-solo (S1 → agentic_models · {_MODEL_ID}) ---")
    saw_token = False
    result: ResultEvent | None = None
    usage_line = ""
    async for event in runtime.stream(task):
        name = type(event).__name__
        if name == "TokenEvent":
            saw_token = True
            print(f"  {name}: {event.text!r}")  # type: ignore[attr-defined]
        elif isinstance(event, DoneEvent):
            u = event.usage
            usage_line = (
                f"in={u.input_tokens} out={u.output_tokens} "
                f"cache_r={u.cache_read} cache_w={u.cache_write} "
                f"total={u.total_tokens} cost_usd={u.cost_usd:.6f} stop={event.stop_reason}"
            )
            print(f"  {name}: {usage_line}")
        elif isinstance(event, ResultEvent):
            result = event
            print(f"  {name}: text={event.text!r}")
        else:
            print(f"  {name}: {event!r}")

    # --- verificación efecto-en-cable (params transmitidos al SDK) ---
    wire_temp = captured.get("temperature")
    wire_max = captured.get("max_tokens")
    wire_meta = captured.get("metadata")
    print("\n--- efecto-en-cable (params → SDK, vía on_payload) ---")
    print(f"  temperature = {wire_temp!r}   (esperado 0.0)")
    print(f"  max_tokens  = {wire_max!r}   (esperado 64)")
    print(f"  metadata    = {wire_meta!r}   (esperado {{'user_id': 'opaque-owner'}})")
    wire_ok = (
        wire_temp == 0.0
        and wire_max == 64
        and wire_meta == {"user_id": "opaque-owner"}
    )
    print(f"  wire: {'CONFIRMADO' if wire_ok else 'DISCREPANCIA'}")

    ok = bool(result and result.text.strip() and saw_token) and wire_ok
    print(f"\nVEREDICTO turno: {'OK' if ok else 'FALLO'} | usage: {usage_line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
