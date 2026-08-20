# Embudo — defectos observados

Se consumen en la etapa de la tool destinataria. Atribución: `rival` sobre-reclama · `descripción` de la medida infra-reclama · `resultado` de la medida no cierra · `prueba` enunciado mal calibrado · `gpt-5.x` conducta.

Al calibrar `grep`, `glob` y `bash` se reutilizan enunciados de los de `read_file` y `write_file`, para ver de paso si sus defectos ya han desaparecido.

| rondas | destinataria | observado | atribución |
|---|---|---|---|
| bx1..bx4 | `bash` | consumidos en `D-33`: `ls` dentro de `bash` (7 llamadas, 5/5) y censo de repo sin relación (`git status` 4/5, `git rev-parse` 5/5) — tras el corte, 0/20, 1/5 y 1/5 | descripción |
| b3, bx2_5, by2_3, by2_5 | `bash` | intérprete para escribir fuente: heredoc de Python, y `perl -0pi -e`. La descripción ya lo nombra de tres formas y sigue apareciendo (1/5 → 2/5, ruido de la misma clase) | gpt-5.x |
| b4, by1_2, by1_4 | `bash` | verificación con `read_file` + `glob` de un fichero cuya existencia el propio programa ya afirmó por stdout (`wrote N lines to …`, o un `&& wc -l` encadenado por el modelo). No hay afirmación que añadir | gpt-5.x |
| x3 | `grep` | localizar un fichero por nombre (`code of conduct\|contributing`) en vez de `glob` | rival |
| y2, y4, d2, d3, d5 | `grep` | patrón amplio sobre `**/*` en árbol de 10 ficheros, con `glob` ya corrido en la misma tanda | rival |
| z2 | `grep` | `glob: "pyproject.toml\|src/**/*.py\|CHANGELOG.md"` — la alternancia no es sintaxis glob: no casa nada y devuelve vacío en silencio, indistinguible de «sin coincidencias» | resultado |
| z2, d3, d4 | `grep` | consumido en `D-34`: buscaba dentro de `.pyc` porque no respetaba `.gitignore`, que es de donde A lo hereda gratis vía ripgrep | resultado |
| gy1..gy4 | `grep` | consumido en `D-34`: el idioma `*.py` —28 de 29 globs en caliente— seleccionaba 0 ficheros con `pathlib` anclado y volvía como «sin coincidencias»; falso negativo indistinguible de ausencia real | resultado |
| gx1..gx3, gy1..gy3 | `grep` | relectura con `read_file` de un fichero que `grep` ya había citado verbatim. Declarados `-C`/`-A`/`-B` en el esquema, el modelo no los usa **ni una vez en 29 llamadas** y `cierra` no mejora (7/20 → 5/20). Segunda refutación de la palanca redactada tras `D-31` | gpt-5.x |
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
| wxw4_1..wxw4_5 | `WebSearch` | enunciado con URL canónica adivinable (documentación oficial de PostgreSQL): las 5 rondas van directas a `WebFetch` sin buscar. El caso no era suyo; sustituido por uno sin URL canónica | prueba |
| wzw2, wzw3, wzw4 | `WebSearch` | enunciados de GRADO 2, no suyos: piden contenido de página («y qué trae de nuevo», «cuéntame qué pasó»), que no es lo que un resultado de búsqueda afirma. Rehecho el bloque a grado 1 estricto (última versión de Python, de Django, LTS de Node, de PostgreSQL): cierra 20/20. El 8/20 medía el enunciado | prueba |
| wzw2, wzw3, wzw4 | `WebSearch` | consumido en `D-35`: en los casos de grado 2 el snippet no basta y el modelo bajaba a `bash` a escribir scrapers ad-hoc (`urllib` + `HTMLParser` a mano) sobre las URL devueltas, en vez de pedirlas por `WebFetch`. La información ya estaba escrita en la descripción de `WebFetch`, pero `WebFetch` es `deferred` y `bash` residente: no era persuasión, era presencia. Trailer en el resultado de `WebSearch` (el canal que A usa para el REMINDER de `Sources:`), medido `wz`→`wr`: scraper real 7/20 → 1/20, `WebFetch` 4/20 → 12/20, acierto 19/20 → 20/20 | descripción |
| wrw1..wrw4 | `WebSearch` | `cierra` cae 8/20 → 5/20 con el trailer y NO es regresión: el trailer prescribe una segunda llamada, así que la columna es inexpresable en grado 2. Donde `cierra` significa algo es en los casos de grado 1, que siguen 20/20 | prueba |
| wrw3_3 | `WebSearch` | única superviviente del scraper tras el trailer, y con tanteo previo (`print('skip')`, `print('ok')`, intento con `bs4`) antes de acertar con `urllib`. 1 de 20 | gpt-5.x |
| wrw4_1..wrw4_5, wrw3_5 | `WebSearch` | el modelo sale a `bash` **a preguntar en qué año vive** (`date +%Y`, `date -I`, `python -c print(date.today().year)`). La descripción le exige en mayúsculas usar el año en curso en la consulta y el contexto no lo lleva: verificado en `wrw4_3/state/.../session.json`, el único `2026` anterior a la primera llamada es el que el propio modelo escribe en la query; los demás son la salida de sus `date`. Mismo patrón que `D-35` —información que falta, herramienta genérica— pero se paga en el bloque de entorno del integrador, no en el runtime | descripción |
| wrw2_1..wrw2_5 | `WebSearch` | `gh release view`, `gh api` y `pip index versions` en el caso de httpx: NO es desvío, lo prescribe la propia descripción de `WebFetch` («For GitHub URLs, prefer the `gh` CLI via the bash tool»). Se lee aparte del recuento de scrapers | — |
| wxw3_1 | `WebSearch` | única ronda donde CERRAR costó el acierto: cerró con el snippet «Django 6.0 release notes» (bajo URL `/en/6.1/`) y respondió 6.0 siendo 6.1 la última. Cruce completo: cerraron 8 → acierto 8/8; no cerraron 12 → acierto 11/12. Forzar el cierre por redacción compraría `cierra` pagando `acierto` | resultado |
| wgg2, wgg4 | `WebSearch` | dos enunciados más descartados por mal calibrados: el de «dónde vive la documentación de uv» lo contesta el modelo SIN llamar a nada (URL anterior a su corte), y el de la alternativa a `black` se lee como pregunta sobre el repo del workspace y se va a `grep`/`glob` | prueba |
| whg1_1 | `WebSearch` | rotula la sección obligatoria como «Fuentes:» en vez del literal «Sources:» que exige la descripción, 1 de 10 rondas; el resto la emite literal | gpt-5.x |
| wzw3, wzw4 | `WebSearch` | `read_file` sobre una ruta inexistente (`ws/does-not-exist`, `offset: 1, limit: 1`) como sonda tras la búsqueda, en 7 de 20 rondas y sin uso posterior | gpt-5.x |
| wzw2_1, wzw4_1 | `WebSearch` | `python` no está en el PATH del ws y el scraper improvisado muere con `127` antes de reintentar con `python3` — mismo corte por entorno ya anotado en `bash` | prueba |
| wxf1_2, wxf1_5 | `WebFetch` | acierto marcado en rojo por el instrumento, no por la tool: la respuesta traducía el Zen al español y el criterio exigía la palabra «zen». Criterio reescrito sobre el primer y el último principio | prueba |
