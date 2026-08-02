"""El **compositor** de la battery: el ÚNICO módulo que conoce `processor`.

Lo que hace un integrador de verdad: componer el runtime por el punto de
composición único del base (`create_runtime`, `C10`) enchufando su motor en la
costura que corresponde (`S11 · RuntimeConfig.input_processor`). El base no se
entera de que existe esta battery — ni la importa, ni la registra, ni la trae por
defecto: aparece porque **alguien la compone aquí**.

Nada de esto se «instala» ni se sobreescribe: si el consumidor quiere otros
comandos, compone otro procesador en esta misma ranura.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_runtime.factory import (
    RuntimeConfig,
    StorageConfig,
    ToolsConfig,
    create_runtime,
)

from .processor import EchoCommandProcessor


def compose(
    *,
    storage_root: Path,
    model_caller: Any,
    scope: Any = None,
    **extra: Any,
) -> Any:
    """Compone un runtime del base CON la battery enchufada en `S11`."""
    return create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=storage_root),
        model_caller=model_caller,
        tools=ToolsConfig(),
        scope=scope,
        input_processor=EchoCommandProcessor(),
        **extra,
    ))


__all__ = ["compose"]
