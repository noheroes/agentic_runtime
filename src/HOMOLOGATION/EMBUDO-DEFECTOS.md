# Embudo — defectos observados

Se consumen en la etapa de la tool destinataria. Atribución: `rival` sobre-reclama · `descripción` de la medida infra-reclama · `resultado` de la medida no cierra · `prueba` enunciado mal calibrado · `gpt-5.x` conducta.

Al calibrar `grep`, `glob` y `bash` se reutilizan enunciados de los de `read_file` y `write_file`, para ver de paso si sus defectos ya han desaparecido.

| rondas | destinataria | observado | atribución |
|---|---|---|---|
| x1, x2, c1 | `bash` | `ls -la <dir>` con `glob` en el pool | rival |
| x3, c3, d5 | `bash` | `git status --short` sin relación con el encargo | rival |
| b3 | `bash` | heredoc de Python con `read_text` + `replace` + `write_text` sobre dos ficheros: escribe fuente saltándose la tool de escritura | rival |
| b4 | `bash` | `ls -l` para confirmar el fichero que acababa de crear con una redirección | resultado |
| x3 | `grep` | localizar un fichero por nombre (`code of conduct\|contributing`) en vez de `glob` | rival |
| y2, y4, d2, d3, d5 | `grep` | patrón amplio sobre `**/*` en árbol de 10 ficheros, con `glob` ya corrido en la misma tanda | rival |
| z2 | `grep` | `glob: "pyproject.toml\|src/**/*.py\|CHANGELOG.md"` — la alternancia no es sintaxis glob: no casa nada y devuelve vacío en silencio, indistinguible de «sin coincidencias» | resultado |
| z2, d3, d4 | `grep` | busca dentro de `.pyc` y devuelve binario ilegible | resultado |
| x4 | `glob` | 6 tanteos sucesivos con `README*` y `**/README.md` repetidos | — |
| c1 | `glob` | 3 tanteos (`README*`, `docs/**/*.md`, `**/README*`) para decidir dónde escribir | — |
| g2 | `glob` | 3 tanteos en paralelo (`**/*test*`, `**/tests/**/*`, `**/test/**/*`) en la misma tanda; el primero ya resolvía y el tercero devolvió vacío | gpt-5.x |
| x1, x3, y1, y2, y4, c3, d2, d3 | `glob` | `'**/*'` como primer movimiento — no reaparece en g1..g4, los cuatro patrones fueron dirigidos | por decidir |
| c2 | `grep` | leer `patterns.py` ya localizado, en vez de `read_file` | rival |
| x1, x2, x3, c3, d4, g4 | `read_file` | `offset: 1, limit: 220/250/80/40` sobre ficheros de ≤40 líneas | descripción |
| x1, x2, x3, x4 | `write_file` | relectura del fichero recién escrito, y en x1 y x3 además `glob` del nombre para confirmar que existe | resultado |
| c3 | `write_file` | `glob` de la ruta exacta recién creada, con el sello de cierre ya en el acuse | resultado |
| c1, c2, c4 | `write_file` | relectura del fichero recién escrito, con el sello de cierre ya en el acuse | gpt-5.x |
| d4 | `write_file` | `grep` acotado al fichero recién escrito para comprobar que la cadena ya no está; el enunciado pedía «una sola fuente» y mezclaba escritura con censo del árbol — d5, mismo grado sin censo, no sondeó | prueba |
| d2, d3, d4, d5 | `write_file` | relectura del fichero recién escrito, con el sello reforzado en el acuse — en g4, mismo sello y escritura tras censo con `glob`, no reapareció | gpt-5.x |
| c2, d2, d3, d5 | `bash` | `python` y `pytest` no están en el PATH del ws: la verificación funcional del encargo se corta por entorno, no por conducta | prueba |
| y1 | `read_file` | `git log --all` tras leer el `CHANGELOG`, sin uso en la respuesta final | resultado |
