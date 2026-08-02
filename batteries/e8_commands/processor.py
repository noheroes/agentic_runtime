"""El motor de la battery: un `UserInputProcessor` (`S11`) con comandos locales.

Es la forma que el canónico le da a un slash-command: la entrada se resuelve
**sin ir al modelo** y el turno rinde lo ya resuelto (`shouldQuery === false`).
Aquí está reducido a lo mínimo que se puede aseverar sin ambigüedad:

- `/eco <texto>` → corte: el turno no llama al modelo y responde `eco: <texto>`.
- cualquier otra cosa → passthrough exacto, para que la rama sin comando siga
  siendo el turno de siempre.

Importa del base (`ProcessedInput`) y el base no importa de aquí: ésa es la
dirección que `E8` mide.
"""
from __future__ import annotations

from typing import Any

from agentic_runtime.contracts.user_input import ProcessedInput

#: Prefijo del único comando de la battery. Público porque el compositor y quien
#: la ejercita necesitan nombrarlo sin duplicar la cadena.
ECHO_COMMAND = "/eco"


class EchoCommandProcessor:
    """Resuelve `/eco` localmente; lo demás pasa intacto."""

    async def process(self, prompt: str, ctx: Any) -> ProcessedInput:
        texto = prompt.strip()
        if texto.startswith(ECHO_COMMAND):
            resuelto = texto[len(ECHO_COMMAND):].strip()
            return ProcessedInput(
                prompt=texto,
                short_circuit=True,
                result_text=f"eco: {resuelto}",
            )
        return ProcessedInput(prompt=prompt)


__all__ = ["ECHO_COMMAND", "EchoCommandProcessor"]
