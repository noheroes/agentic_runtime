"""`S11` · `UserInputProcessor` — preproceso de la entrada, ANTES del turno.

La entrada del usuario no llega cruda al modelo: hay un paso previo que puede
reescribirla (expansión de invocaciones, adjuntos) o **resolverla del todo sin ir
al modelo** (un slash-command local). Ese paso es política del integrador, no
mecanismo del runtime: por eso es costura y no motor.

**Forma, y por qué ésta.** El canónico devuelve un único resultado con un
booleano —`processUserInput.ts:64-83` publica `{messages, shouldQuery, …}` y el
consumidor hace `this.mutableMessages.push(...messagesFromUserInput)` **siempre**
y luego `if (!shouldQuery) { … }` (`QueryEngine.ts:431` y `:556`)—; el walking
skeleton A2, que es el único artefacto de grado **G1** de esta costura, corrió
exactamente esa forma (`skeleton/seams.py:84-99`). El borrador de `SEAMS §S11`
proponía en cambio una unión `ProcessedInput | ShortCircuit`. Gana el canónico:
un booleano en un resultado único, porque el corte **no** es una excepción ni un
tipo aparte — es un turno que terminó antes, con texto ya resuelto.

**Lo que este contrato NO copia del canónico, dicho en voz alta:** el canónico
devuelve además `allowedTools`/`model`/`effort` (un slash-command puede cambiar
el modelo o abrir permisos del turno). Eso es la battery `commands`, que está
**bajo la línea de corte** (`TRAMO-1 §3·B`) y se difiere **entera y nombrada**
(`L07`). Publicar hoy esos campos sin consumidor sería superficie muerta.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .tools import ToolContext


@dataclass(frozen=True)
class ProcessedInput:
    """Resultado del preproceso.

    - `prompt`: el texto que efectivamente entra al turno (puede diferir del que
      escribió el usuario: expansiones, adjuntos resueltos).
    - `short_circuit=True`: el turno **no** va al modelo. Espejo de
      `shouldQuery === false`.
    - `result_text`: lo ya resuelto localmente. Con `short_circuit=True` es lo que
      el turno rinde como respuesta; el canónico lo empuja igualmente al historial
      (`<local-command-stdout>`), así que aquí también se persiste como turno del
      asistente y no se pierde.
    """

    prompt: str
    short_circuit: bool = False
    result_text: str | None = None


@runtime_checkable
class UserInputProcessor(Protocol):
    """Preprocesa la entrada del usuario antes del turno.

    `@runtime_checkable` (paga `FIND-01` para esta costura): un consumidor puede
    comprobar que lo que inyecta realiza el protocolo, en vez de descubrirlo con
    un `AttributeError` a mitad de un turno real.

    `ctx` se tipa con `ToolContext` —el protocolo **estrecho** de `contracts`— y
    no con el `ToolUseContext` del base: `contracts` es la hoja del grafo y no
    importa nada del base (`C1`). El ctx real lo satisface estructuralmente.
    """

    async def process(self, prompt: str, ctx: ToolContext) -> ProcessedInput: ...


class NoopUserInputProcessor:
    """Passthrough: un runtime sin comandos propios.

    Es el default del loop, y por eso importa que sea **exactamente** identidad:
    con él cableado, el comportamiento del turno es el que había antes de existir
    la costura.
    """

    async def process(self, prompt: str, ctx: ToolContext) -> ProcessedInput:
        return ProcessedInput(prompt=prompt)


__all__ = ["NoopUserInputProcessor", "ProcessedInput", "UserInputProcessor"]
