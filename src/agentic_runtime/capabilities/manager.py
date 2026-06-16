from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .contracts import CapabilityProvider, CapabilitySummary

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext
    from ..tools.pool import ToolPool
    from ..tools.protocol import ToolProtocol

logger = logging.getLogger(__name__)


class CapabilityManager:
    """Coordina providers de capacidades sin conocer ninguno en concreto.

    El runtime habla solo con el manager (o recibe su resultado). Agregar un
    provider nuevo no requiere cambiar el manager ni el loop: basta registrarlo.

    Las uniones se construyen en orden de registro. Las tools se deduplican por
    nombre, conservando la primera aparición (prioridad por orden de registro).
    """

    def __init__(self, providers: list[CapabilityProvider] | None = None) -> None:
        self._providers: list[CapabilityProvider] = list(providers or [])

    def register(self, provider: CapabilityProvider) -> None:
        self._providers.append(provider)

    @property
    def providers(self) -> list[CapabilityProvider]:
        return list(self._providers)

    async def startup(self) -> None:
        for provider in self._providers:
            await provider.startup()

    async def shutdown(self) -> None:
        for provider in self._providers:
            await provider.shutdown()

    def catalog(self, context: "ToolUseContext") -> list[CapabilitySummary]:
        entries: list[CapabilitySummary] = []
        for provider in self._providers:
            entries.extend(provider.catalog(context))
        return entries

    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]:
        result: list["ToolProtocol"] = []
        seen: set[str] = set()
        for provider in self._providers:
            for tool in provider.tools(context):
                if tool.name in seen:
                    continue
                result.append(tool)
                seen.add(tool.name)
        return result

    def build_tool_pool(
        self,
        native_tools: list["ToolProtocol"],
        context: "ToolUseContext",
    ) -> "ToolPool":
        """Punto de convergencia native + capability — el resultado que el runtime consume.

        Es el análogo de `assembleToolPool(permissionContext, mcpTools)` del canónico: el
        caller (loop/integrador) pasa las tools nativas ya registradas en el runtime; el
        manager aporta las de las capabilities. La fusión real (built-ins como prefijo
        contiguo, dedup native-gana, deny) la hace `ToolPool.assemble()` — un único punto,
        igual que allí. La dirección de dependencia es capabilities → tools, nunca al revés.
        """
        from ..tools.pool import ToolPool

        return ToolPool(
            native_tools=list(native_tools),
            capability_tools=self.tools(context),
        )

    def active_context(self, context: "ToolUseContext") -> list[dict]:
        messages: list[dict] = []
        for provider in self._providers:
            messages.extend(provider.active_context(context))
        return messages

    def compact_context(self, context: "ToolUseContext") -> list[dict]:
        messages: list[dict] = []
        for provider in self._providers:
            messages.extend(provider.compact_context(context))
        return messages


__all__ = ["CapabilityManager"]
