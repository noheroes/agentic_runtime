from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..contracts.identity import Scope


@runtime_checkable
class StorageProtocol(Protocol):
    """Contrato estructural de storage — cualquier backend que implemente estos métodos lo satisface."""

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str: ...
    async def download(self, key: str) -> bytes: ...
    async def presign(self, key: str, ttl_seconds: int = 3600) -> str: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def list_prefix(self, prefix: str) -> list[str]: ...


@runtime_checkable
class StorageLifecycle(Protocol):
    async def teardown(self) -> None: ...


class StorageKeys:
    """
    Claves canónicas del runtime — deterministas, sin dependencia de implementación.

    Taxonomía (contrato de bordes, B4):

    - **config** scope: ``<scope>/config.json``, ``<scope>/agent.md``, ``<scope>/ltm/...``.
    - **conversación + artefactos** scope+session bajo ``<scope>/<sid>/``; el main vive en
      la raíz de ese subtree y cada subagente en ``<scope>/<sid>/subagents/<agent_id>/``.

    **La primera componente es un `Scope`, no un `user_id: str`** (`C9`/`ID-3`, grafía
    `AC-39`). El tipo es la defensa: un `str` admite silenciosamente el default de
    conveniencia —``user_id="mcp"``— que es exactamente como se coló la fuga
    multi-usuario de los tokens OAuth. Un `Scope` hay que producirlo, y lo produce el
    integrador.

    Dos planos separados por clave:

    - **conversación**: ``session.json`` (transcript) + sidecar mutable ``session.meta.json``
      (ahí vive ``is_backgrounded`` y demás meta de observación).
    - **artefactos**: ``work/<filename>`` (scope compartido; lo exige el caso distribuido).

    NOTA — abierta (memo project_runtime_boundaries / plan B4): el mapeo de la **cascada de
    4 niveles** del canónico (managed/user/project/local + @include) al modelo cloud está
    pendiente de decidir; ``config_key`` cubre por ahora solo el nivel user.
    """

    # ------------------------------------------------------------------
    # Base por agente: main en la raíz del subtree de sesión; subagentes anidados.
    # ------------------------------------------------------------------
    @staticmethod
    def _agent_base(scope: Scope, session_id: str, agent_id: str = "main") -> str:
        root = f"{scope.key}/{session_id}"
        if agent_id and agent_id != "main":
            return f"{root}/subagents/{agent_id}"
        return root

    # ------------------------------------------------------------------
    # config — scope user
    # ------------------------------------------------------------------
    @staticmethod
    def config_key(scope: Scope) -> str:
        return f"{scope.key}/config.json"

    @staticmethod
    def agent_md_key(scope: Scope) -> str:
        return f"{scope.key}/agent.md"

    @staticmethod
    def ltm_key(scope: Scope) -> str:
        return f"{scope.key}/ltm/memories.json"

    # ------------------------------------------------------------------
    # plano conversación — transcript + sidecar meta (mutable)
    # ------------------------------------------------------------------
    @staticmethod
    def transcript_key(scope: Scope, session_id: str, agent_id: str = "main") -> str:
        return f"{StorageKeys._agent_base(scope, session_id, agent_id)}/session.json"

    @staticmethod
    def meta_key(scope: Scope, session_id: str, agent_id: str = "main") -> str:
        return f"{StorageKeys._agent_base(scope, session_id, agent_id)}/session.meta.json"

    # ------------------------------------------------------------------
    # plano artefactos — work/ (scope compartido)
    # ------------------------------------------------------------------
    @staticmethod
    def work_key(scope: Scope, session_id: str, filename: str, agent_id: str = "main") -> str:
        return f"{StorageKeys._agent_base(scope, session_id, agent_id)}/work/{filename}"

    # ------------------------------------------------------------------
    # log
    # ------------------------------------------------------------------
    @staticmethod
    def log_key(scope: Scope, session_id: str, agent_id: str = "main") -> str:
        return f"{StorageKeys._agent_base(scope, session_id, agent_id)}/agent.log"
