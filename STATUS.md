# Estado actual

Última actualización: 12 de agosto de 2026.

## Fase activa

Fase 1 — Reconocimiento y contrato de datos.

## Objetivo de la fase

Diseñar desde evidencia reproducible de los Parquet reales de 2024-01 y 2025-01, no solo desde documentación externa.

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
- La fase 0 quedó verificada: el repositorio se recupera desde un clon limpio y el entorno bloqueado se reconstruye sin datos ni estado local.
- `docs/BACKLOG.md` descompone las entregas de la fase 1 en ocho tareas ordenadas de 45–120 minutos.

## Evidencia

- `4772bdd docs: define project scope`
- `72498e0 docs: add project guidance and phase context`

## Tarea activa

F1-01 — Definir el perfil mínimo reproducible.

## Criterio de aceptación de la tarea

- Quedan definidas las métricas necesarias por columna para reconocer ambos archivos.
- Cada métrica tiene un propósito ligado al contrato o a una regla de calidad.
- Se incluyen tipo lógico observado, nulabilidad, extremos relevantes y cardinalidad solo cuando aporta evidencia.
- Se define el comando previsto, pero todavía no se implementa el perfil ni el pipeline.

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
- `3ae3d95 feat: add reproducible Parquet metadata inspection` versiona el entorno, el script y la evidencia; `main` y `origin/main` están sincronizadas y el árbol quedó limpio tras el commit.
- `origin/main` se clonó en `/tmp/taxis-ny-recovery-asqp52/taxis_ny` desde el commit `4663948`.
- El clon contiene `README.md`, `AGENTS.md`, `STATUS.md`, `docs/DECISION_LOG.md`, `docs/PHASES.md`, `docs/reference-data.md`, el script de inspección, `.python-version`, `pyproject.toml`, `uv.lock` y `.gitignore`.
- Antes de reconstruir el entorno, el clon no contenía `.venv/`, `data/`, `.local/`, `.env` ni archivos Parquet, SQLite o log.
- `/home/alex/.local/bin/uv sync --locked` reconstruyó `.venv/` con Python 3.12.13 y DuckDB 1.5.5. El aviso de copia en lugar de hardlinks no impidió la instalación.
- Después de reconstruir el entorno, `git status --short --branch` mostró `main...origin/main` sin cambios; `.venv/` continuó fuera del estado versionado.
- El autor explicó correctamente que el clon debe contener lo necesario para reconstruir el entorno sin depender del estado local y que la prueba no detecta secretos ya versionados ni archivos sensibles fuera de los patrones comprobados.

## Pendiente para cerrar la fase 1

- Completar F1-01 a F1-08 según `docs/BACKLOG.md`.

## Decisiones diferidas

- La licencia del repositorio se decidirá cuando exista una necesidad concreta de autorizar reutilización, modificación o redistribución. Desde el 12 de agosto de 2026 ya no bloquea el cierre de la fase 0.

## Bloqueos

Ninguno.

## Siguiente paso único

Para F1-01, anticipar qué decisión del contrato permite tomar cada métrica propuesta antes de escribir consultas.

## Documento de fase

`docs/PHASES.md`, sección «Fase 1 — Reconocimiento y contrato de datos».
