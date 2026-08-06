# Estado actual

Última actualización: 6 de agosto de 2026.

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

Inspeccionar los metadatos físicos de Yellow Taxi 2024-01.

## Criterio de aceptación de la tarea

- El archivo puede abrirse como Parquet.
- Se registran número de filas, columnas, tipos físicos, row groups y compresión.
- El procedimiento utilizado queda documentado y puede repetirse sobre el mismo archivo.
- No se perfilan todavía rangos, nulos ni reglas semánticas de calidad.

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

## Pendiente para cerrar la fase 0

- Versionar la licencia.
- Crear el backlog de tareas de la fase 1.
- Clonar el repositorio en otra carpeta y verificar que el contexto del proyecto se recupera sin archivos locales ocultos.

## Decisiones diferidas

- La licencia del repositorio se decidirá más adelante. La fase 0 no puede cerrarse hasta resolverla o modificar explícitamente su puerta de salida.

## Bloqueos

Ninguno.

## Siguiente paso único

Identificar una herramienta local adecuada para leer metadatos Parquet sin cargar todas las filas en memoria.

## Documento de fase

`docs/PHASES.md`, sección «Fase 0 — Entorno y contrato del proyecto».
