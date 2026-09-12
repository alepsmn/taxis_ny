# Plan de trabajo

Proyecto: pipeline de Data Engineering sobre NYC TLC Yellow Taxi.
Reinicio ordenado del intento anterior (`~/taxis_ny`, que se conserva como archivo).

## Reparto de roles

| Quién | Qué | Dónde queda |
|---|---|---|
| Claude | Decisiones de negocio y de diseño, cada una con su porqué y su evidencia | `docs/DECISIONS.md` |
| Claude | Catálogo de reglas de validación y lista de transformaciones, listo para implementar | `docs/RULES.md` |
| Claude | Mantener este plan y la sección "Siguiente tarea" | `PLAN.md` |
| Alex | Todo el código, tests y estructura del paquete | `src/`, `tests/` |

Regla de oro: si una decisión afecta a cómo se programa algo, está escrita en `docs/` antes de programarlo.
Si una decisión merece razonarla juntos, aparece marcada como **PARA DISCUTIR** con las opciones y una recomendación.
No hay otros documentos de estado. Tres ficheros y ya.

## Qué se rescata del intento anterior

- Stack: Python 3.12 + uv + DuckDB + Parquet + SQLite. Decidido y correcto.
- Ficheros de referencia 2024-01 y 2025-01 con sus SHA-256 (`docs/DECISIONS.md`, D-05).
- La evidencia del perfilado (nulos, dominios, extremos). Ya está convertida en reglas en `docs/RULES.md`.
- Las ideas de raw inmutable por hash, cuarentena con motivo y publicación atómica. Se implementan por cortes, no todas a la vez.

## Qué se deja atrás y por qué

- El modo mentor que exigía predecir, explicar y defender cada paso. Un mes de trabajo produjo un script de perfilado y cero pipeline.
- Nueve fases y cinco documentos de estado sincronizados entre sí. El coste de mantenerlos superaba al de programar.
- Diseñar el contrato completo antes de procesar un solo mes. Ahora primero pasa un mes de punta a punta, luego se endurece.

## Cortes verticales

Cada corte deja algo ejecutable de punta a punta. No se empieza el siguiente sin que el anterior funcione sobre 2024-01.

### Corte 1: un mes de punta a punta, sin estado
Un comando toma un Parquet mensual y produce `curated` y `quarantine` para ese mes.
Etapas, en este orden:
1. Adquisición: fichero local o descarga a `.part`, SHA-256, copia a `data/raw/year=YYYY/month=MM/<sha256>.parquet`.
2. Puerta estructural (RULES S-xx): columnas obligatorias, tipos convertibles, columnas desconocidas.
3. Transformaciones (RULES T-xx): lista ordenada, desacoplada del flujo.
4. Puertas de fila (RULES R-xx): cada regla es un objeto con id, severidad, condición SQL y reason_code. El motor las recorre; el flujo no las conoce.
5. Puerta de lote (RULES B-xx): decide si se publica.
6. Publicación: escribir `curated` y `quarantine` en staging y mover al destino final. Resumen JSON por stdout.

Mapeo con tu minimotor anterior: missing fields y conversión de tipos = puerta estructural; validación semántica = puertas de fila; tu lista de transformaciones = T-xx; tu clase filtro = la puerta de lote.

### Corte 2: estado e idempotencia
SQLite con un manifiesto por partición y versión (D-19). Repetir el mismo mes con el mismo hash es un no-op. Publicación atómica verificada con fallo inyectado. `--reprocess` explícito.

### Corte 3: incremental, backfill y evolución de esquema
`plan` calcula qué meses faltan entre dos fechas. Procesar 2025-01 con `cbd_congestion_fee` sin tocar 2024. Backfill reanudable. Cambio de contrato bloquea la publicación cuando es incompatible.

### Corte 4: ingesta resistente
Descarga real con timeouts, reintentos solo para errores transitorios (429, 5xx, timeout), 404 como "mes aún no publicado". Tests con servidor HTTP local.

### Corte 5: streaming simulado
Un replayer lee un mes de raw y emite viajes ordenados por hora de pickup a una cola local. Un consumidor procesa micro-lotes reutilizando las mismas puertas y escribe en particiones por hora. Aquí aparecen datos tardíos y ventanas. Sin broker externo salvo que se decida en un ADR.

### Corte 6: marts y observabilidad
Agregados por zona, hora y día con dbt-duckdb. Métricas por etapa, runbook.

## Layout previsto del repositorio

```
taxis/
├── PLAN.md
├── docs/DECISIONS.md
├── docs/RULES.md
├── pyproject.toml, uv.lock, .python-version
├── src/taxis/
│   ├── cli.py            # comandos: ingest (corte 1), luego plan/status/backfill
│   ├── contract.py       # esquema canónico v1 (nombres, tipos, obligatoriedad)
│   ├── acquire.py        # descarga o copia local, hash, escritura en raw
│   ├── gates/
│   │   ├── structural.py # S-xx
│   │   ├── rows.py       # R-xx: lista de reglas
│   │   └── batch.py      # B-xx
│   ├── transforms.py     # T-xx: lista ordenada
│   └── publish.py        # staging -> destino
├── tests/
└── data/                 # no versionado
    ├── reference/  raw/  curated/  quarantine/  control/
```

Los directorios aparecen cuando existe código que los necesita.

## Completado

**Tarea 1 (corte 1, etapas 1 y 2): adquisición y puerta estructural.** ✓
- `acquire.py`: sha256 por bloques, copia idempotente a `data/raw/year=YYYY/month=MM/<hash>.parquet`.
- `contract.py`: contrato v1 como dataclass `Column` (20 columnas), `COMPATIBLE_TYPES` y `RULES` (R-01..R-19).
- `gates/structural.py`: `comparing_schemas()` — S-01..S-04 con `DESCRIBE SELECT * FROM read_parquet(?)`.
- `cli.py`: Typer, encadena acquire → structural → JSON resumen → exit code 2 si block.
- Probado con 2024-01 y 2025-01: hashes y row counts coinciden con D-05.

**Tarea 2 (corte 1, etapas 3 y 4): transformaciones y reglas de fila.** ✓
- `transforms.py`: T-01..T-05 en una sola consulta SQL (subconsulta para renombrar/castear, externa para duration y linaje). Usa `duckdb.sql()` para devolver `DuckDBPyRelation`.
- `gates/rows.py`: `row_rule()` — evalúa R-01..R-19 con `CASE WHEN` por regla, produce `reasons` (reject) y `warnings` (warn) como listas por fila via `list_filter`. Registra la relación como vista con `.create_view("transformed")`.

**Tarea 3 (corte 1, etapas 5 y 6): batch, publicación y resumen completo.** ✓
- `gates/batch.py`: `batch_door()` — B-01 (ratio rejects > 5% → block), B-02 (duplicados exactos > 0,1% → warn). Separa curated (reasons vacía) y quarantine (reasons no vacía). Conteo por reason_code con UNNEST.
- `publish.py`: `publication_parquet()` — staging temporal + `replace()` atómico (D-18). `ParquetNoEscrito` si falla la escritura.
- `cli.py`: cadena completa acquire → structural → transform → rows → batch → publish. JSON resumen por stdout con month, sha256, row_count, gates, curated/quarantine counts, rejected/warning counts.
- Tests diferidos.

## Siguiente tarea

**Tarea 4 (corte 2): manifiesto SQLite e idempotencia.**

Entregable: ejecutar `uv run taxis 2024-01 ...` dos veces consecutivas; la segunda es un no-op con mensaje. `uv run taxis --reprocess 2024-01 ...` fuerza el reprocesamiento.

Lo que falta:
1. `manifest.py`: crear `data/control/manifest.db` con tabla `partitions` (D-19). Funciones: `lookup(year, month)` → registro o None, `register(year, month, sha256, summary)` → INSERT o UPDATE.
2. En `cli.py`, antes de procesar: consultar manifiesto. Mismo (year, month, sha256) ya publicado → skip con mensaje. Distinto sha256 para el mismo mes → avisar de revisión y rechazar sin `--reprocess` (D-05).
3. En `cli.py`, después de publish exitoso: registrar en manifiesto. El INSERT va después del rename, nunca antes (D-18).
4. Flag `--reprocess` en el comando `ingest`: salta la comprobación de idempotencia y actualiza el registro del manifiesto.
5. Publicación atómica verificada con fallo inyectado — diferida con tests.
