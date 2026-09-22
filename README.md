# taxis

Pipeline de Data Engineering sobre los datos de NYC TLC Yellow Taxi. Ingesta, validacion, curado y agregacion de ~3M viajes/mes con calidad de datos trazable.

## Que hace

Toma los ficheros Parquet mensuales de TLC (o los descarga), los pasa por un pipeline de calidad con 19 reglas de validacion y produce dos salidas:

- **curated**: viajes que pasaron todas las reglas, con esquema canonico.
- **quarantine**: viajes rechazados con la lista de motivos.

Despues, tres marts dbt agregan los datos curados para analisis.

```
Parquet TLC --> acquire --> structural gate --> transforms --> row gate --> batch gate --> publish
                 |              S-01..S-04       T-01..T-05     R-01..R-19    B-01..B-02      |
                 |                                                                            |
                 +-- data/raw/                                        data/curated/ -----------+
                                                                      data/quarantine/
                                                                      data/marts/ (dbt)
```

## Stack

Python 3.12, uv, DuckDB, Parquet, SQLite, dbt-duckdb.

## Instalacion

```bash
git clone <repo>
cd taxis
uv sync
```

## Uso

### Procesar un mes (fichero local)

```bash
uv run taxis ingest 2024-01 data/reference/yellow_tripdata_2024-01.parquet
```

### Procesar un mes (descarga de TLC)

```bash
uv run taxis ingest 2024-01 --download
```

### Ver meses pendientes

```bash
uv run taxis plan
```

### Backfill de un rango

```bash
uv run taxis backfill 2024-01 2024-12 --download
```

### Generar marts

```bash
uv run taxis marts
```

## Estructura del proyecto

```
taxis/
├── src/taxis/
│   ├── cli.py               # comandos: ingest, plan, backfill, marts
│   ├── acquire.py            # descarga o copia local, SHA-256, raw
│   ├── contract.py           # esquema canonico v1, reglas R-xx
│   ├── transforms.py         # T-01..T-05: renombrado, cast, duracion, linaje
│   ├── gates/
│   │   ├── structural.py     # S-01..S-04: columnas, tipos, esquema
│   │   ├── rows.py           # R-01..R-19: validacion fila a fila
│   │   └── batch.py          # B-01..B-02: ratio rejects, duplicados
│   ├── publish.py            # staging atomico + rename
│   ├── manifest.py           # estado en SQLite (idempotencia)
│   ├── pipeline.py           # orquestacion ingest/backfill
│   └── plan.py               # calculo de meses pendientes
├── dbt/
│   ├── models/
│   │   ├── mart_hourly.sql   # viajes por zona x hora x mes
│   │   ├── mart_daily.sql    # actividad por dia
│   │   └── mart_zone_pair.sql # rutas mas frecuentes por mes
│   ├── dbt_project.yml
│   └── profiles.yml
├── tests/
│   └── test_pipeline.py      # 27 tests: reglas, structural, batch, idempotencia
├── docs/
│   ├── DECISIONS.md           # decisiones de negocio y diseno (D-01..D-27)
│   └── RULES.md               # catalogo de reglas de validacion
├── PLAN.md                    # plan de trabajo y cortes verticales
└── data/                      # no versionado
    ├── raw/                   # parquets originales por SHA-256
    ├── curated_rows/          # viajes validados, particionados year=/month=/
    ├── quarantine_rows/       # viajes rechazados con motivos
    ├── control/               # manifest.db (SQLite)
    └── marts/                 # agregados (DuckDB + Parquet)
```

## Calidad de datos

Tres niveles de puerta, evaluados en orden:

| Puerta | Reglas | Que hace |
|--------|--------|----------|
| Structural | S-01..S-04 | Columnas obligatorias, tipos compatibles, columnas desconocidas |
| Row | R-01..R-19 | Validacion fila a fila: timestamps, distancias, importes, zonas |
| Batch | B-01..B-02 | Ratio de rechazo >5% bloquea el lote; duplicados exactos |

Severidades: `reject` (fila a quarantine), `warn` (fila a curated con aviso), `block` (lote entero rechazado).

Detalle completo en `docs/RULES.md`.

## Incrementalidad

- **Pipeline**: el manifiesto SQLite registra cada mes publicado. Mismo hash = skip. Mes nuevo = solo se procesa ese mes.
- **Marts**: dbt con `materialized='incremental'` y `delete+insert`. Solo se agregan meses nuevos. `--full-refresh` para recalcular todo.

## Tests

```bash
uv run pytest -v
```

27 tests cubriendo reglas de fila (parametrize con 19 reglas + valores limite), puerta structural, batch y manifiesto.

## CI

GitHub Actions: ruff + pytest en cada push.
