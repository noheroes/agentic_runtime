# Embudo — defectos observados

Se consumen en la etapa de la tool destinataria. Atribución: `rival` sobre-reclama · `descripción` de la medida infra-reclama · `resultado` de la medida no cierra · `prueba` enunciado mal calibrado · `gpt-5.x` conducta.

| rondas | destinataria | observado | atribución |
|---|---|---|---|
| x1, x2 | `bash` | `ls -la <dir>` con `glob` en el pool | rival |
| x3 | `bash` | `git status --short` sin relación con el encargo | rival |
| b3 | `bash` | heredoc de Python con `read_text` + `replace` + `write_text` sobre dos ficheros: escribe fuente saltándose la tool de escritura | rival |
| b4 | `bash` | `ls -l` para confirmar el fichero que acababa de crear con una redirección | resultado |
| x3 | `grep` | localizar un fichero por nombre (`code of conduct\|contributing`) en vez de `glob` | rival |
| y2, y4 | `grep` | `log\|logger\|logging` sobre `**/*` en árbol de 8 ficheros; en y2 con `glob '**/*'` ya corrido | rival |
| z2 | `grep` | `glob: "pyproject.toml\|src/**/*.py\|CHANGELOG.md"` — la alternancia no es sintaxis glob: no casa nada y devuelve vacío en silencio, indistinguible de «sin coincidencias» | resultado |
| z2 | `grep` | busca dentro de `.pyc` y devuelve binario ilegible | resultado |
| x4 | `glob` | 6 tanteos sucesivos con `README*` y `**/README.md` repetidos | — |
| x1, x3, y1, y2, y4 | `glob` | `'**/*'` como primer movimiento | por decidir |
| x1, x2, x3 | `read_file` | `offset: 1, limit: 220/250/80` sobre ficheros de ≤40 líneas | descripción |
| x1, x2, x3, x4 | `write_file` | relectura del fichero recién escrito, y en x1 y x3 además `glob` del nombre para confirmar que existe | resultado |
| y1 | `read_file` | `git log --all` tras leer el `CHANGELOG`, sin uso en la respuesta final | resultado |
