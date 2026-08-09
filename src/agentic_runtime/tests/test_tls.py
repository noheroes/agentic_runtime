"""Material de confianza TLS — la CA extra se AÑADE a la base, nunca la sustituye.

Por qué existe esta suite: el defecto que la trajo se midió contra un server real
(Obsidian Local REST API, cert autofirmado en `https://127.0.0.1:5583/mcp/`). El runtime
no tenía NINGUNA forma de declarar un ancla de confianza adicional, así que el server
aprobado en `agentic_code` moría con `CERTIFICATE_VERIFY_FAILED` y toda la superficie MCP
quedaba sin consumidor real con el que medirla (`D-15`).

Lo que NO vale como arreglo, y por eso se asevera la propiedad y no la existencia:
`SSL_CERT_FILE` ya existía y **sustituye** el almacén. Un test que sólo comprobara «hay
contexto y confía en mi CA» pasaría igual con la implementación rota, porque la rota
también confía en la CA extra — lo que pierde es todo lo demás.
"""

from __future__ import annotations

import ssl
from pathlib import Path

import certifi
import pytest

from agentic_runtime import tls


@pytest.fixture(autouse=True)
def _clean_tls_cache():
    tls.clear_tls_cache()
    yield
    tls.clear_tls_cache()


def _split_bundle(tmp_path: Path) -> tuple[Path, Path, str, str]:
    """Parte el bundle de certifi en dos ficheros DISJUNTOS de un cert cada uno.

    Sirve para medir la unión sin fabricar criptografía: si el contexto resultante
    contiene los dos, la CA extra se añadió; si sólo contiene uno, se sustituyó.
    """
    raw = Path(certifi.where()).read_text(encoding="utf-8")
    marker = "-----END CERTIFICATE-----\n"
    certs = [chunk + marker for chunk in raw.split(marker) if "BEGIN CERTIFICATE" in chunk]
    assert len(certs) > 2, "el bundle de certifi debería traer muchos certificados"
    base, extra = tmp_path / "base.pem", tmp_path / "extra.pem"
    base.write_text(certs[0], encoding="utf-8")
    extra.write_text(certs[1], encoding="utf-8")

    def _subject(path: Path) -> str:
        ctx = ssl.create_default_context(cafile=str(path))
        loaded = ctx.get_ca_certs()
        assert len(loaded) == 1
        return repr(loaded[0]["subject"])

    return base, extra, _subject(base), _subject(extra)


def _subjects(context: ssl.SSLContext) -> list[str]:
    return [repr(cert["subject"]) for cert in context.get_ca_certs()]


# ---------------------------------------------------------------------------
# sin variable no se toca nada (el `undefined` de `getCACertificates`)
# ---------------------------------------------------------------------------


def test_sin_variable_no_hay_contexto_propio(monkeypatch):
    monkeypatch.delenv(tls.EXTRA_CA_CERTS_ENV, raising=False)
    assert tls.extra_ca_certs_path() is None
    assert tls.default_ssl_context() is None
    # `True` = defaults de httpx, no «sin verificar»: la diferencia importa.
    assert tls.httpx_verify(True) is True


def test_variable_vacia_o_de_espacios_cuenta_como_ausente(monkeypatch):
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, "   ")
    assert tls.extra_ca_certs_path() is None
    assert tls.default_ssl_context() is None


# ---------------------------------------------------------------------------
# la propiedad que carga el peso: UNIÓN, no sustitución
# ---------------------------------------------------------------------------


def test_la_ca_extra_se_suma_a_la_base(monkeypatch, tmp_path):
    base, extra, subject_base, subject_extra = _split_bundle(tmp_path)
    # `SSL_CERT_FILE` fija la base — es lo que hace `httpx.create_ssl_context`.
    monkeypatch.setenv("SSL_CERT_FILE", str(base))
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(extra))

    context = tls.default_ssl_context()
    assert context is not None
    subjects = _subjects(context)
    # Las dos aserciones son el test: la segunda sola pasaría con la implementación que
    # SUSTITUYE el almacén, que es exactamente el defecto que se está impidiendo.
    assert subject_base in subjects, "la CA extra sustituyó la base en vez de sumarse"
    assert subject_extra in subjects, "la CA extra no se cargó"


def test_sin_ca_extra_la_base_queda_intacta(monkeypatch, tmp_path):
    base, _extra, subject_base, subject_extra = _split_bundle(tmp_path)
    monkeypatch.setenv("SSL_CERT_FILE", str(base))
    monkeypatch.delenv(tls.EXTRA_CA_CERTS_ENV, raising=False)
    import httpx

    subjects = _subjects(httpx.create_ssl_context(verify=True))
    assert subject_base in subjects
    assert subject_extra not in subjects


# ---------------------------------------------------------------------------
# degradación: un CA extra ilegible no puede tumbar el arranque
# ---------------------------------------------------------------------------


def test_ca_extra_inexistente_degrada_sin_lanzar(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(tmp_path / "no-existe.pem"))
    with caplog.at_level("ERROR"):
        assert tls.default_ssl_context() is None
    assert any("no se pudo cargar" in r.message for r in caplog.records)


def test_ca_extra_corrupta_degrada_sin_lanzar(monkeypatch, tmp_path):
    roto = tmp_path / "roto.pem"
    roto.write_text("-----BEGIN CERTIFICATE-----\nno soy base64\n-----END CERTIFICATE-----\n")
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(roto))
    assert tls.default_ssl_context() is None


# ---------------------------------------------------------------------------
# `ssl_verify=False` es del server, no del entorno, y manda
# ---------------------------------------------------------------------------


def test_ssl_verify_false_manda_sobre_la_ca_extra(monkeypatch, tmp_path):
    _base, extra, _sb, _se = _split_bundle(tmp_path)
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(extra))
    assert tls.httpx_verify(False) is False


def test_ssl_verify_true_con_ca_extra_devuelve_contexto(monkeypatch, tmp_path):
    _base, extra, _sb, _se = _split_bundle(tmp_path)
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(extra))
    assert isinstance(tls.httpx_verify(True), ssl.SSLContext)


# ---------------------------------------------------------------------------
# caché: memoizar no puede servir un contexto de otra ruta
# ---------------------------------------------------------------------------


def test_cambiar_la_ruta_no_sirve_el_contexto_anterior(monkeypatch, tmp_path):
    base, extra, subject_base, subject_extra = _split_bundle(tmp_path)
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(base))
    primero = tls.default_ssl_context()
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(extra))
    segundo = tls.default_ssl_context()
    assert primero is not segundo
    assert subject_base in _subjects(primero or ssl.create_default_context())
    assert subject_extra in _subjects(segundo or ssl.create_default_context())


def test_clear_tls_cache_fuerza_reconstruccion(monkeypatch, tmp_path):
    _base, extra, _sb, _se = _split_bundle(tmp_path)
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(extra))
    primero = tls.default_ssl_context()
    assert tls.default_ssl_context() is primero  # memoizado
    tls.clear_tls_cache()
    assert tls.default_ssl_context() is not primero


# ---------------------------------------------------------------------------
# La CA extra es del PROCESO, no de MCP: en A la aplica Node y `fetch` la hereda en
# todas las salidas. En B cada salida se construye a mano, así que la que se olvide
# queda con el almacén por defecto — y falla SÓLO contra el server con CA propia, que
# es el caso que nadie prueba hasta que revienta en producción.
# ---------------------------------------------------------------------------


def test_web_fetch_construye_el_opener_con_la_ca_extra(monkeypatch, tmp_path):
    import urllib.request

    from agentic_runtime.tools.native import web_fetch

    _base, extra, _sb, subject_extra = _split_bundle(tmp_path)
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(extra))
    tls.clear_tls_cache()
    handlers: list[object] = []

    def _capturar(*args):
        handlers.extend(args)
        raise RuntimeError("corte deliberado: el test sólo mide cómo se arma el opener")

    monkeypatch.setattr(urllib.request, "build_opener", _capturar)
    with pytest.raises(RuntimeError):
        web_fetch._descargar("https://ejemplo.invalid/x")

    https = [h for h in handlers if isinstance(h, urllib.request.HTTPSHandler)]
    assert https, "el opener se armó sin handler https propio: usa el almacén por defecto"
    context = https[0]._context  # type: ignore[attr-defined]
    assert subject_extra in _subjects(context), "la CA extra no llegó a WebFetch"


def test_web_search_pasa_la_ca_extra_a_urlopen(monkeypatch, tmp_path):
    import urllib.request

    from agentic_runtime.tools.native import web_search

    _base, extra, _sb, subject_extra = _split_bundle(tmp_path)
    monkeypatch.setenv(tls.EXTRA_CA_CERTS_ENV, str(extra))
    tls.clear_tls_cache()
    capturado: dict = {}

    def _capturar(req, timeout=None, context=None):
        capturado["context"] = context
        raise RuntimeError("corte deliberado")

    monkeypatch.setattr(urllib.request, "urlopen", _capturar)
    resultado = web_search._serper_search("WebSearch", "q", 3, "k")

    assert resultado.is_error, resultado.output
    context = capturado["context"]
    assert context is not None, "urlopen salió sin contexto: ignora la CA extra"
    assert subject_extra in _subjects(context), "la CA extra no llegó a WebSearch"
