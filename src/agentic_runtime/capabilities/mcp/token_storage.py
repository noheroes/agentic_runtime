from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from ...contracts.identity import Scope

if TYPE_CHECKING:
    from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

    from ...storage.protocol import StorageProtocol

logger = logging.getLogger(__name__)

#: Lo que `_load` devuelve es EXACTAMENTE el modelo que se le pide validar. Tiparlo
#: genérico —en vez de `Any`— es lo que hace que `get_tokens`/`get_client_info`
#: comprueben su propio tipo de retorno en vez de dejar pasar cualquier cosa.
_M = TypeVar("_M", bound=BaseModel)


class StorageBackedTokenStorage:
    """`TokenStorage` del SDK `mcp` implementado sobre el `StorageProtocol` del runtime.

    Persiste tokens y client_info por server (sobreviven reinicios → no re-autorizar).
    Es un DEFAULT inyectable: el integrador puede pasar su propia implementación (vault,
    etc.). El runtime solo define este contrato sobre su primitiva de storage.
    """

    def __init__(self, storage: StorageProtocol, server_name: str, *, scope: Scope) -> None:
        # `C9`/`ID-3`: aquí vivía `user_id: str = "mcp"`. Con ese default —que el factory
        # nunca sobrescribía— TODOS los usuarios colisionaban en `mcp/mcp/<srv>` y el
        # token OAuth de A era legible bajo B. `Scope` es obligatorio y sin default: la
        # fuga sólo era posible porque el tipo admitía un valor de conveniencia.
        self._storage = storage
        base = f"{scope.key}/mcp/{server_name}"
        self._tokens_key = f"{base}/oauth_tokens.json"
        self._client_key = f"{base}/oauth_client.json"

    async def _load(self, key: str, model: type[_M]) -> _M | None:
        try:
            if not await self._storage.exists(key):
                return None
            raw = await self._storage.download(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("mcp oauth: no se pudo leer %s: %s", key, exc)
            return None
        try:
            return model.model_validate_json(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("mcp oauth: %s corrupto, se ignora: %s", key, exc)
            return None

    async def _save(self, key: str, value: BaseModel) -> None:
        try:
            await self._storage.upload(key, value.model_dump_json().encode(), "application/json")
        except Exception as exc:  # noqa: BLE001
            logger.warning("mcp oauth: no se pudo guardar %s: %s", key, exc)

    async def get_tokens(self) -> OAuthToken | None:
        from mcp.shared.auth import OAuthToken

        return await self._load(self._tokens_key, OAuthToken)

    async def set_tokens(self, tokens: OAuthToken) -> None:
        await self._save(self._tokens_key, tokens)

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        from mcp.shared.auth import OAuthClientInformationFull

        return await self._load(self._client_key, OAuthClientInformationFull)

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        await self._save(self._client_key, client_info)


__all__ = ["StorageBackedTokenStorage"]
