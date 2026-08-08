"""C1 · la prueba de que el paquete `contracts` es INVARIANTE.

`TRAMO-1 §2·C1`: *«test que importe `contracts` con el base **ausente del path**
(si falla, el contrato no es invariante)»*.

Dos aserciones complementarias, porque una sola dejaría un hueco:

1. **Dinámica** — se carga `agentic_runtime.contracts` en un intérprete donde
   `agentic_runtime` es un stub vacío y **cualquier** import de otro submódulo del
   base revienta. Es la que acredita el comportamiento (`L09`: cablear ≠ existir).
2. **Estática** — se recorre el AST de todos los módulos de `contracts/` y se
   comprueba que ninguno importa el base, **ni siquiera bajo `TYPE_CHECKING`**. La
   dinámica no ve esos imports porque no se ejecutan, pero un contrato que sólo
   tipa contra el base sigue sin poder reimplementarse aparte: forkea igual.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"
SRC_DIR = CONTRACTS_DIR.parent.parent


_LOADER = '''
import importlib.machinery, importlib.util, sys, types

SRC = {src!r}
ROOT = {root!r}
sys.path.insert(0, SRC)

# `agentic_runtime` reducido a un cascarón: tiene __path__ (para que se encuentre el
# subpaquete) y NADA más. El `__init__.py` real del base no se ejecuta.
pkg = types.ModuleType("agentic_runtime")
pkg.__path__ = [ROOT]
pkg.__spec__ = importlib.machinery.ModuleSpec("agentic_runtime", None, is_package=True)
sys.modules["agentic_runtime"] = pkg


class _BaseBlocker:
    """Revienta si `contracts` intenta alcanzar cualquier otra parte del base."""

    def find_spec(self, name, path=None, target=None):
        if name.startswith("agentic_runtime.") and not name.startswith("agentic_runtime.contracts"):
            raise ImportError("contracts importó el base: " + name)
        return None


sys.meta_path.insert(0, _BaseBlocker())

import agentic_runtime.contracts as c

# No basta con que el paquete cargue: los símbolos rectores tienen que estar vivos.
for name in ("RuntimeTask", "Event", "Usage", "PermissionContext", "PermissionMode",
             "ToolProtocol", "ToolResult", "ToolCategory", "AgentDefinition",
             "Scope", "SessionRepo", "RuntimeSessionProtocol", "TaskStatus",
             "AbortSignal", "AgentRuntime"):
    getattr(c, name)

assert c.PermissionContext().mode is c.PermissionMode.DEFAULT, "el default NO puede ser bypass"
print("INVARIANTE-OK")
'''


def test_contracts_imports_with_the_base_absent_from_the_path() -> None:
    code = _LOADER.format(src=str(SRC_DIR), root=str(CONTRACTS_DIR.parent))
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(SRC_DIR.parent),
        check=False,  # el returncode ES la aserción de abajo
    )
    assert proc.returncode == 0, (
        "el paquete `contracts` NO es invariante — no carga sin el base:\n"
        f"{proc.stdout}\n{proc.stderr}"
    )
    assert "INVARIANTE-OK" in proc.stdout


def test_no_contracts_module_imports_the_base_even_under_type_checking() -> None:
    offenders: list[str] = []
    for path in sorted(CONTRACTS_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # level 1 == `from .x import y` → dentro de contracts, correcto.
                # level >= 2 == `from ..x import y` → sale del paquete: es el base.
                if node.level >= 2:
                    offenders.append(f"{path.name}:{node.lineno} from {'.' * node.level}{node.module or ''}")
                elif node.level == 0 and (node.module or "").startswith("agentic_runtime"):
                    offenders.append(f"{path.name}:{node.lineno} from {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("agentic_runtime"):
                        offenders.append(f"{path.name}:{node.lineno} import {alias.name}")
    assert not offenders, "contracts importa el base (forkea el ecosistema):\n" + "\n".join(offenders)
