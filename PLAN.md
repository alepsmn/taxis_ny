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

### ~~Corte 5: streaming simulado~~ — descartado
Los datos de TLC son batch por naturaleza (Parquet mensual). Simular un stream con un replayer no enseña los problemas reales de streaming (backpressure, late data, consumer groups, checkpointing). Si se quiere aprender streaming, hacerlo en un proyecto aparte con una fuente que sea streaming de verdad (websocket de precios, GTFS-RT, etc.).

### Corte 5: marts y observabilidad
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

**Tarea 4 (corte 2): manifiesto SQLite e idempotencia.** ✓
- `manifest.py`: `lookup(db_path, year, month)` → sha256 o None; `register(...)` → INSERT con CREATE TABLE IF NOT EXISTS en ambas funciones. DB en `data/control/manifest.db` (D-19).
- `cli.py`: lookup después de acquire; mismo sha → skip con exit 0; distinto sha → aviso de revisión con exit 1 (D-05).
- `cli.py`: register después de publish exitoso (`if all(written_paths)`), con timestamp UTC (D-18).
- Flag `--reprocess`: salta la comprobación de idempotencia.
- Publicación atómica verificada con fallo inyectado — diferida con tests.

**Tarea 5 (corte 3): incremental y backfill.** ✓
- `plan.py`: comando `plan` que calcula meses pendientes entre dos fechas consultando el manifiesto (rango por defecto 2024-01 a 2025-12, D-02).
- `cli.py`: backfill reanudable — los meses ya publicados se saltan por idempotencia; si se interrumpe a mitad, se retoma donde quedó.
- 2025-01 procesado con `cbd_congestion_fee` sin tocar 2024-01 (columnas opcionales manejadas por T-03, D-16).
- D-21 registrada: salto en `negative_amount` de 1,26% a 4,16% entre 2024-01 y 2025-01.
- B-04 y evolución de esquema diferidos: el dataset actual no permite validarlos con datos reales (ver "Pendiente fuera de corte").

**Tarea 6 (corte 4): ingesta resistente.** ✓
- `acquire.py`: `download(year, month, raw_base_path)` — GET streaming a `.part`, rename por sha al completar. Reintentos con backoff exponencial para 429/5xx/timeout. 404 → `None` (mes no publicado). Timeouts separados: 30s conexión, 300s lectura (D-22).
- `cli.py`: flag `--download` en `ingest` y `backfill`, excluyente con el origen local (D-23).
- `pipeline.py`: `run_backfill` maneja ambos modos (descarga o local) en un solo bucle, mes a mes.
- Probado con descarga real: 2024-02 y 2024-03 descargados y procesados correctamente.
- D-20 actualizada: TLC republicó los ficheros de 2024 con columnas `month` y `year`.
- Tests de `download()` con servidor HTTP local diferidos.

## Siguiente tarea

**Tarea 7 (corte 5): marts y observabilidad.**

Dos partes, en este orden:

**Parte A — Marts con dbt-duckdb (D-24, D-25).**
Tres modelos que leen de curated y producen tablas agregadas en `data/marts/`:
1. `mart_hourly`: viajes, ingreso medio, distancia media, duración media por zona de pickup × hora del día × mes. Responde a "¿qué zonas y franjas horarias generan más viajes y más ingreso?"
2. `mart_daily`: viajes, ingreso total, distancia media por día natural × mes. Responde a "¿cómo varía la actividad día a día?"
3. `mart_zone_pair`: viajes y tarifa media por par origen-destino × mes (solo pares con ≥ 10 viajes). Responde a "¿cuáles son las rutas más frecuentes y más caras?"

Cada modelo es incremental por mes: al procesar un nuevo mes, solo se recalcula ese mes.
Los marts se publican como Parquet en `data/marts/<nombre>/`.
Un comando `uv run taxis marts` lanza `dbt run` sobre el proyecto dbt que vive en `dbt/`.

Estructura dbt:
```
dbt/
├── dbt_project.yml
├── profiles.yml
├── models/
│   ├── sources.yml          # curated como source
│   ├── mart_hourly.sql
│   ├── mart_daily.sql
│   └── mart_zone_pair.sql
└── target/                  # no versionado
```

**Parte B — Observabilidad (D-26). PARA DISCUTIR, puede ser tarea 8.**
Pendiente de definir el alcance: ¿métricas en el JSON de resumen (ya está parcialmente), log estructurado a stderr, tabla en SQLite, o dashboard? Depende de para quién sea el consumidor.

Lo que falta por decidir antes de programar:
1. ¿Qué columnas de curated se excluyen de marts? `reasons`, `warnings`, `source_sha256`, etc. son linaje, no análisis. Y `month`/`year` de TLC siguen apareciendo en curated (deberían haberse descartado en S-03).
2. ¿`dbt-duckdb` como dependencia de desarrollo o de producción? Recomendación: producción, porque los marts son un entregable del pipeline.
3. ¿Tests dbt (`dbt test`) para validar marts, o tests pytest que lean los Parquet resultantes? Recomendación: ambos — dbt test para unicidad y not-null, pytest para valores esperados.

## Pendiente fuera de corte (por orden de prioridad)

1. **Evolución de esquema.** Cuando el contrato suba de versión, decidir si el cambio es compatible (columna opcional nueva → curated viejo se lee con NULL) o incompatible (cambio de tipo, columna obligatoria nueva → bloquear hasta reprocesar). No se implementa hasta que haya un caso real, pero es lo primero que se aborda al terminar los cortes porque afecta a la integridad de curated a largo plazo.
2. B-04 (`row_count_drift`): warn si las filas difieren >50% del mes anterior. Útil como red de seguridad, baja prioridad porque el dataset actual es estable.
