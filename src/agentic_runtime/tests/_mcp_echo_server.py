"""Server MCP REAL para los E2E (FastMCP). Soporta stdio, Streamable HTTP y HTTPS.

Expone `echo_upper(text)` -> text.upper() y `dump_docs(text)`, cuya descripción es
DESMEDIDA a propósito (`FIND-DEFER-2`). Uso:
  python _mcp_echo_server.py                              # stdio
  python _mcp_echo_server.py --http <port>                # Streamable HTTP (sin TLS)
  python _mcp_echo_server.py --https <port> <cert> <key>  # Streamable HTTP con TLS
"""
import sys

from mcp.server.fastmcp import FastMCP

#: Descripción desmedida, del tamaño que el canónico dice haber MEDIDO en servers MCP
#: generados desde OpenAPI: «observed dumping 15-60KB of endpoint docs into
#: tool.description» (`services/mcp/client.ts:213-217`). Está aquí, en el SERVER, y no
#: fabricada en el test: el cap sólo queda acreditado si el texto entra de verdad por el
#: transporte de un tercero.
HUGE_DESCRIPTION = "DUMP " + "x" * 60_000


def _build() -> FastMCP:
    mcp = FastMCP("echo-test")

    @mcp.tool()
    def echo_upper(text: str) -> str:
        """Devuelve el texto en mayúsculas."""
        return text.upper()

    @mcp.tool(description=HUGE_DESCRIPTION)
    def dump_docs(text: str) -> str:
        return text

    return mcp


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--http":
        mcp = _build()
        mcp.settings.port = int(args[1])
        mcp.run(transport="streamable-http")
    elif args and args[0] == "--https":
        import uvicorn

        port, certfile, keyfile = int(args[1]), args[2], args[3]
        uvicorn.run(
            _build().streamable_http_app(),
            host="127.0.0.1", port=port,
            ssl_certfile=certfile, ssl_keyfile=keyfile,
            log_level="warning",
        )
    else:
        _build().run()  # stdio
