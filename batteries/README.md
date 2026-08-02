# `batteries/` — lo que el base NO trae

Este directorio vive **fuera de `src/`** a propósito: no se empaqueta con el
runtime (`[tool.setuptools.packages.find] where = ["src"]`), así que nada de lo
que hay aquí llega a un consumidor que instale `agentic-runtime`.

Es el sujeto de `E8` (`TRAMO-1 §4`): *una battery importada sólo por su
compositor; el base no la conoce*. La dirección del grafo de imports es la
capacidad que se asevera —**battery → base, nunca base → battery**— y `E8` la
mide recorriendo con `ast` los imports de todos los fuentes de las dos partes,
no leyéndolos.

Una battery se **compone o se sustituye**, nunca se sobreescribe: el base no
publica catálogo por defecto de ninguna, y el punto de composición único es
`create_runtime` (`C10`).
