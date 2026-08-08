"""Sustitución de argumentos en el cuerpo de una skill — espejo de
`utils/argumentSubstitution.ts:24-145`.

`LAT-SKILL1`. `SkillTool.input_schema` anunciaba `args` al modelo (y la descripción
homologada llega a poner un ejemplo con args), pero `execute()` los descartaba: el
`$ARGUMENTS` de una skill escrita para el canónico se quedaba LITERAL en las
instrucciones, sin error y sin señal. Lo mismo por la vía del slash command.

Formas soportadas, en el orden en que A las resuelve (`:109-136`):

1. nombrados (`$origen`), que son alias POSICIONALES de los `arguments:` del frontmatter,
2. indexados (`$ARGUMENTS[0]`),
3. atajo indexado (`$0`),
4. y por último `$ARGUMENTS`, la cadena entera.

El orden importa: `$ARGUMENTS` se resuelve al final justamente para no comerse el prefijo
de `$ARGUMENTS[0]`.
"""
from __future__ import annotations

import re
import shlex
from collections.abc import Sequence

#: Un nombre de argumento numérico colisionaría con el atajo `$0`/`$1` (`:57-59`).
_SOLO_DIGITOS = re.compile(r"^\d+$")
_INDEXADO = re.compile(r"\$ARGUMENTS\[(\d+)\]")
_ATAJO = re.compile(r"\$(\d+)(?!\w)")


def parse_arguments(args: str) -> list[str]:
    """Trocea la cadena de argumentos con reglas de SHELL — espejo de `parseArguments`.

    Es troceo, no ejecución: `shlex` no expande nada, así que un `$HOME` sobrevive
    literal igual que en A, donde el resolver de variables devuelve `$KEY` (`:29-30`).
    Entrada malformada (comilla sin cerrar) NO lanza: cae al split por espacios (`:31-34`).

    Divergencia declarada: A filtra los operadores de shell que su parser reifica
    (`:36-39`); `shlex` no los reifica, los devuelve como tokens de texto. Consecuencia
    dicha: un `&&` en los args de una skill llega como argumento en vez de descartarse.
    Es inerte —de aquí no sale ningún comando, sale una sustitución de texto— y el sentido
    del filtro de A es el mismo: nada de esto se ejecuta.
    """
    if not args or not args.strip():
        return []
    try:
        return shlex.split(args)
    except ValueError:
        return [t for t in args.split() if t]


def parse_argument_names(argument_names: str | Sequence[str] | None) -> list[str]:
    """Nombres declarados en el frontmatter `arguments:` — espejo de `parseArgumentNames`.

    Acepta lista o cadena separada por espacios. Descarta vacíos y numéricos puros.
    """
    if not argument_names:
        return []
    if isinstance(argument_names, str):
        candidatos: list[str] = argument_names.split()
    elif isinstance(argument_names, Sequence):
        candidatos = [str(n) for n in argument_names]
    else:
        return []
    return [n for n in candidatos if n.strip() and not _SOLO_DIGITOS.match(n)]


def substitute_arguments(
    content: str,
    args: str | None,
    *,
    append_if_no_placeholder: bool = True,
    argument_names: Sequence[str] = (),
) -> str:
    """Sustituye los placeholders de `content` — espejo de `substituteArguments`.

    `args is None` significa **no se pasaron argumentos** y devuelve el contenido intacto;
    `""` significa **invocada sin argumentos**, que sí es una entrada válida: vacía los
    placeholders y no apendiza (`:100-104`, `:140`).

    Si no había ningún placeholder y los args no están vacíos, se apendiza
    `ARGUMENTS: …`: el dato del usuario no se pierde por que la skill no lo previera.
    """
    if args is None:
        return content

    parsed = parse_arguments(args)
    original = content

    def _en(indice: int) -> str:
        return parsed[indice] if 0 <= indice < len(parsed) else ""

    for i, name in enumerate(argument_names):
        if not name:
            continue
        # `re.escape`: el nombre viene de un frontmatter de terceros, así que es DATO y
        # nunca patrón. La guarda de A (`(?![\[\w])`) evita que `$org` muerda `$orgX`.
        content = re.sub(
            rf"\${re.escape(name)}(?![\[\w])",
            lambda _m, _i=i: _en(_i),  # type: ignore[misc]
            content,
        )

    content = _INDEXADO.sub(lambda m: _en(int(m.group(1))), content)
    content = _ATAJO.sub(lambda m: _en(int(m.group(1))), content)
    content = content.replace("$ARGUMENTS", args)

    if content == original and append_if_no_placeholder and args:
        content = f"{content}\n\nARGUMENTS: {args}"
    return content


__all__ = ["parse_argument_names", "parse_arguments", "substitute_arguments"]
