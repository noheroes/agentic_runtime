"""Material de confianza TLS del runtime — homólogo de `utils/caCerts.ts` del canónico.

En A esta pieza es casi invisible porque Node la resuelve solo: `NODE_EXTRA_CA_CERTS`
**añade** el fichero indicado a las CAs de base y se aplica a TODO el TLS del proceso
(fetch de la API, transportes MCP http/sse, WebFetch/WebSearch). El único código propio
que A escribe es el que reconstruye ese comportamiento cuando hay que fijar `ca` a mano
(`getCACertificates`, `caCerts.ts:28-115`), y su docstring dice la trampa con todas las
letras: *«setting `ca` on an HTTPS agent replaces the default certificate store, so we
must always include base CAs»*.

Python no tiene equivalente nativo. Las dos variables que sí honra la stdlib
(`SSL_CERT_FILE`/`SSL_CERT_DIR`, que `httpx.create_ssl_context` también respeta)
**SUSTITUYEN** el almacén, no lo amplían: apuntarlas a un CA corporativo deja fuera a
todo lo público, y apuntarlas a un bundle público deja fuera al CA propio. Por eso el
comportamiento de A no se obtiene «configurando bien el entorno»: hay que construirlo.

Contrato (idéntico al de A, sin inventar nada):

- La ruta del bundle EXTRA se lee de la variable de entorno `AGENTIC_EXTRA_CA_CERTS`.
  `caCerts.ts` lee **sólo** `process.env`, a propósito y con la razón escrita: la capa
  TLS no debe depender del grafo de configuración. Quién puebla esa variable a partir de
  ajustes del producto es del INTEGRADOR (`caCertsConfig.ts` hace justo eso en A).
- El bundle extra se **AÑADE** a la base (`SSL_CERT_FILE`/`SSL_CERT_DIR` si están, si no
  el bundle de `certifi`, que es la base que usa httpx). Nunca la sustituye.
- Sin variable no se toca nada: se devuelve `None` para que apliquen los defaults del
  runtime, como A devuelve `undefined`.
- Un fichero ilegible o inválido se registra como error y NO tumba el arranque
  (`caCerts.ts:86-93` hace `logForDebugging(..., {level: 'error'})` y sigue). Degradar a
  «sin CA extra» es lo mismo que hacía antes de configurarla.

El resultado se memoiza como en A (`memoize`), con `clear_tls_cache()` para invalidarlo
cuando el entorno cambia (homólogo de `clearCACertsCache`).
"""

from __future__ import annotations

import logging
import os
import ssl

logger = logging.getLogger(__name__)

#: Homóloga de `NODE_EXTRA_CA_CERTS`: ruta a un bundle PEM que se AÑADE a las CAs de base.
EXTRA_CA_CERTS_ENV = "AGENTIC_EXTRA_CA_CERTS"

#: Memoización del contexto construido, indexada por la ruta leída del entorno. La clave
#: incluye la ruta para que un cambio de variable no sirva un contexto obsoleto sin que
#: nadie llame a `clear_tls_cache()`.
_CACHE: dict[str, ssl.SSLContext | None] = {}


def extra_ca_certs_path() -> str | None:
    """Ruta del bundle extra declarada en el entorno, o `None` si no hay ninguna."""
    value = os.environ.get(EXTRA_CA_CERTS_ENV, "").strip()
    return value or None


def _base_context() -> ssl.SSLContext:
    """Contexto con la MISMA base que usaría httpx con `verify=True`.

    Se delega en `httpx.create_ssl_context` en vez de replicar su cascada
    (`SSL_CERT_FILE` → `SSL_CERT_DIR` → `certifi`): replicarla dejaría dos verdades que
    se separan en cuanto httpx cambie la suya, y la base es justo lo que no puede
    perderse al añadir el CA extra.
    """
    import httpx

    return httpx.create_ssl_context(verify=True)


def default_ssl_context() -> ssl.SSLContext | None:
    """Contexto TLS del runtime: base + CA extra, o `None` si no hay CA extra.

    `None` significa «usa los defaults», no «no verifiques»: es el `undefined` de
    `getCACertificates`.
    """
    path = extra_ca_certs_path()
    if path is None:
        return None
    if path in _CACHE:
        return _CACHE[path]

    context: ssl.SSLContext | None
    try:
        context = _base_context()
        context.load_verify_locations(cafile=path)
        logger.debug("tls: CA extra añadida a las de base desde %s (%s)", path, EXTRA_CA_CERTS_ENV)
    except (OSError, ssl.SSLError) as exc:
        # A registra el fallo y sigue con las CAs de base; tumbar el proceso por un CA
        # extra ilegible convertiría un ajuste opcional en un fallo de arranque.
        logger.error("tls: no se pudo cargar %s=%s — se sigue sin CA extra: %s", EXTRA_CA_CERTS_ENV, path, exc)
        context = None

    _CACHE[path] = context
    return context


def httpx_verify(ssl_verify: bool = True) -> bool | ssl.SSLContext:
    """Valor de `verify` para un `httpx.AsyncClient`, honrando la CA extra.

    `ssl_verify=False` (que es una opción POR SERVER de la config MCP, no del entorno)
    manda: quien desactiva la validación no quiere un contexto, quiere no validar.
    """
    if not ssl_verify:
        return False
    return default_ssl_context() or True


def clear_tls_cache() -> None:
    """Invalida el contexto memoizado — homólogo de `clearCACertsCache()`."""
    _CACHE.clear()


__all__ = [
    "EXTRA_CA_CERTS_ENV",
    "clear_tls_cache",
    "default_ssl_context",
    "extra_ca_certs_path",
    "httpx_verify",
]
