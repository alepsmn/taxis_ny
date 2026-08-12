# Estado actual

Última actualización: 12 de agosto de 2026.

## Fase activa

Fase 0 — Entorno y contrato del proyecto.

## Objetivo de la fase

Disponer de un repositorio remoto, recuperable y reproducible en WSL2 antes de implementar el pipeline.

## Estado comprobado

- El proyecto reside en el filesystem Linux de WSL2: `/home/alex/taxis_ny`.
- El repositorio Git usa la rama `main`.
- `main` está sincronizada con `origin/main`.
- El remoto es `https://github.com/alepsmn/taxis_ny.git`.
- `README.md` define alcance, cobertura, capas, garantías previstas y exclusiones.
- `AGENTS.md` contiene las reglas de trabajo y aprendizaje.
- `docs/ROADMAP.md` conserva el plan detallado.
- `docs/PHASES.md` proporciona el contexto resumido por fases.
- `docs/DECISION_LOG.md` conserva la secuencia breve de decisiones confirmadas, diferidas o sustituidas.
- `.gitignore` excluye `.local/`, datos, secretos, logs y bases SQLite locales.

## Evidencia

- `4772bdd docs: define project scope`
- `72498e0 docs: add project guidance and phase context`

## Tarea activa

Versionar el entorno reproducible y la inspección física de Yellow Taxi 2024-01.

## Criterio de aceptación de la tarea

- El diff contiene únicamente el entorno reproducible, el script de inspección, la documentación y la memoria operativa relacionadas.
- `.venv/`, los Parquet y `docs/adr/LOG_PREGUNTAS.md` no se incluyen.
- `uv lock --check`, el script de inspección y `git diff --check` finalizan correctamente.
- El cambio queda registrado en un commit pequeño y descriptivo.

## Último resultado verificado

- `yellow_tripdata_2024-01.parquet` descargado manualmente mediante `curl`.
- Tamaño comprobado: `49,961,641` bytes.
- SHA-256 comprobado: `c4d59da7bbc8abaeeeb1727947ee93d9891a71acb42854bd80db1571b2030510`.
- `git status --short` no muestra el archivo.
- `yellow_tripdata_2025-01.parquet` descargado manualmente mediante `curl` y publicado localmente después de completar el archivo `.part`.
- Tamaño comprobado: `59,158,238` bytes.
- SHA-256 comprobado: `9af277e4c0d3f9deb30644da822981e1e7df6af58313170fd3aa8a474485488a`.
- `git status --short` no muestra ninguno de los Parquet.
- `docs/reference-data.md` registra URL, fecha de descarga, tamaño y SHA-256 de ambos archivos.
- La adquisición fue manual y no implementó un extractor.
- `uv 0.12.2` está instalado en WSL en `/home/alex/.local/bin/uv` y el binario responde correctamente mediante su ruta absoluta.
- `uv init --bare --python 3.12` creó `pyproject.toml` sin entorno virtual; `requires-python = ">=3.12,<3.13"` limita el proyecto a Python 3.12.x.
- `uv python pin 3.12` creó `.python-version` con `3.12`; esto fija la versión solicitada, pero todavía no prueba que el intérprete pueda ejecutarse.
- `.gitignore` excluye `.venv/`; `git check-ignore -v --no-index .venv/test` confirma la regla antes de crear el entorno.
- `uv sync` creó `.venv/` y `uv.lock`; `uv run python --version` ejecuta Python 3.12.13, `.venv/` no aparece en `git status` y DuckDB todavía no está instalado.
- `uv add duckdb` declaró `duckdb>=1.5.5`; DuckDB 1.5.5 se importa correctamente y `uv lock --check` confirma que `uv.lock` está actualizado.
- DuckDB abre `yellow_tripdata_2024-01.parquet`: el footer declara 2.964.624 filas, 3 row groups y 19 columnas hoja; los tipos físicos observados son `INT32`, `INT64`, `DOUBLE` y `BYTE_ARRAY`.
- Los tres row groups contienen 1.048.576, 1.048.576 y 867.472 filas, todos con compresión `ZSTD`; su suma coincide con las 2.964.624 filas del footer.
- `scripts/inspect_parquet_metadata.py` y `docs/reference-data.md` conservan el procedimiento y el resultado verificado sin perfilar valores de viajes.
- El autor explicó correctamente que el footer describe la estructura interna y que SHA-256 se calcula externamente sobre todos los bytes para detectar cambios de contenido.

## Pendiente para cerrar la fase 0

- Versionar la licencia.
- Crear el backlog de tareas de la fase 1.
- Clonar el repositorio en otra carpeta y verificar que el contexto del proyecto se recupera sin archivos locales ocultos.

## Decisiones diferidas

- La licencia del repositorio se decidirá más adelante. La fase 0 no puede cerrarse hasta resolverla o modificar explícitamente su puerta de salida.

## Bloqueos

Ninguno.

## Siguiente paso único

Revisar y preparar para commit únicamente los archivos relacionados con el entorno reproducible y la inspección Parquet.

## Documento de fase

`docs/PHASES.md`, sección «Fase 0 — Entorno y contrato del proyecto».
