"""Helpers compartidos para los E2E reales contra Azure gpt-5.4-mini.

No tiene prefijo `test_` → pytest no lo colecta. Centraliza la carga de la config
Azure desde el `.env` de agent_core (instrucción del usuario) y la construcción del
caller real, para que los módulos de test no la dupliquen.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# file: <repo>/src/agentic_runtime/tests/_azure_real.py → parents[2]=src, parents[3]=<repo>
_AGENT_CORE_ENV = Path(__file__).resolve().parents[2] / "agent_core" / ".env"
CA_BUNDLE = Path(__file__).resolve().parents[3] / "certs" / "cacert.pem"


def _load_azure_config() -> dict | None:
    """Lee la config Azure del .env de agent_core. None si falta algo esencial."""
    if not _AGENT_CORE_ENV.exists():
        return None
    cfg: dict[str, str] = {}
    for line in _AGENT_CORE_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.split("#", 1)[0].strip()
    key = cfg.get("AZURE_OPENAI_API_KEY")
    endpoint = cfg.get("AGENT_AZURE_ENDPOINT")
    if not key or not endpoint:
        return None
    return {"api_key": key, "endpoint": endpoint}


AZURE = _load_azure_config()

skip_marker = pytest.mark.skipif(
    AZURE is None or not CA_BUNDLE.exists(),
    reason="Sin config Azure (agent_core/.env) o CA bundle (certs/cacert.pem)",
)


def build_caller(system_prompt: str):
    """Caller real apuntando al modelo Azure gpt-5.4-mini.

    `get_model` es ambiguo (varios providers comparten el id 'gpt-5.4-mini' y gana la
    última registración); se selecciona el modelo Azure explícitamente por provider.
    """
    from agentic_models import get_registry, register_builtins

    from agentic_runtime.models.caller import AgenticModelsCaller

    os.environ["AZURE_OPENAI_BASE_URL"] = AZURE["endpoint"]
    os.environ["AZURE_OPENAI_API_VERSION"] = "preview"  # surface Responses v1 de Azure
    os.environ.setdefault("SSL_CERT_FILE", str(CA_BUNDLE))

    register_builtins()
    model = get_registry().get_by_provider("azure-openai-responses", "gpt-5.4-mini")
    return AgenticModelsCaller(model=model, api_key=AZURE["api_key"], system_prompt=system_prompt)
