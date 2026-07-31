"""Errores de configuración del runtime — T1 invariante.

Existen porque `C9`/`ID-1` exige que la ausencia de identidad **falle en voz alta**:
la alternativa que había —fabricar un `user_<hex>`/`sess_<hex>` nuevo por despacho—
no es un default benigno, es un fallo funcional silencioso (`H-1`: la memoria del
agente principal nunca se recuperaba porque su clave cambiaba en cada turno).

Es la cara mínima y local de `K8` (fail-fast), **no** `K8` entero: el motor general
de fail-fast sigue por encima de la línea de corte (`TRAMO-1 §3·E`).
"""
from __future__ import annotations


class RuntimeConfigError(Exception):
    """El runtime se compuso de forma que no puede correr correctamente."""


class RuntimeIdentityError(RuntimeConfigError):
    """Falta identidad atribuida y el runtime **no la inventa** (`C9`, `DEUDA-A ID-1`)."""


__all__ = ["RuntimeConfigError", "RuntimeIdentityError"]
