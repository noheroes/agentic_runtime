"""Battery `e8_commands` — un integrador que añade slash-commands locales (`S11`).

**Este `__init__` no importa nada del paquete a propósito.** «Importada sólo por
su compositor» (`E8`) se mide sobre el grafo de imports real: si este módulo
re-exportara el procesador, cualquiera que tocase el paquete lo arrastraría y la
aserción de `E8` dejaría de significar lo que dice. El único módulo que conoce
`processor` es `compose`, que es el punto de composición de la battery.
"""
from __future__ import annotations

__all__: list[str] = []
