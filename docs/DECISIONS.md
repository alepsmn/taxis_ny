# Decisiones de negocio y de diseño

Cada entrada dice qué se decidió, por qué, qué evidencia lo sostiene y qué implica para el código.
Estados: **vigente**, **PARA DISCUTIR**, **diferida**, **sustituida por D-xx**.
La evidencia numérica procede del Parquet 2024-01 (2.964.624 filas) y 2025-01 (3.475.226 filas) salvo que se indique otra cosa.

---

## D-01. Reinicio en un repositorio nuevo
**Decisión:** el proyecto vive en `~/taxis`. `~/taxis_ny` se conserva como archivo y no se modifica.
**Por qué:** el intento anterior acumuló proceso (nueve fases, cinco documentos de estado, modo mentor) y en un mes no produjo pipeline. Arrastrar ese repositorio arrastra también su historial de decisiones pedagógicas que ya no aplican.
**Implica:** nuevo `git init` aquí. Los dos Parquet de referencia se copian, no se enlazan, para que borrar `taxis_ny` más adelante no rompa nada.
**Estado:** vigente.

## D-02. Alcance temporal: 2024-01 a 2025-12
**Decisión:** 24 particiones mensuales. Se empieza por 2024-01. 2022 y 2023 quedan como ejercicio de backfill en el corte 3 si apetece.
**Por qué:** 2024 y 2025 contienen el cambio de esquema real más interesante (`cbd_congestion_fee` aparece en 2025-01), cubren dos años completos para estacionalidad y pesan unos 1,3 GB en total, manejable en disco. Más años no añaden problemas nuevos, solo volumen.
**Evidencia:** 2024-01 tiene 19 columnas; 2025-01 tiene 20, la nueva es `cbd_congestion_fee`.
**Implica:** el comando `plan` del corte 3 recibe un rango de meses; el rango por defecto es este.
**Estado:** vigente.

## D-03. Stack: Python 3.12, uv, DuckDB, Parquet, SQLite
**Decisión:** Python coordina; DuckDB procesa Parquet con SQL; SQLite guarda el estado operativo; Parquet es el formato de todas las capas. Sin Kafka, Spark ni Airflow en el núcleo.
**Por qué:** 3 millones de filas por mes caben en un portátil. DuckDB lee Parquet fuera de memoria y expresa las reglas como SQL, que es lo que un data engineer escribiría en cualquier motor. Un orquestador o un broker solo se justifican con un problema observado, y aquí no lo hay todavía.
**Implica:** las reglas de fila se escriben como expresiones SQL; el streaming del corte 5 se simula con un replayer propio, no con un broker.
**Estado:** vigente. Se revisa si el corte 5 necesita un broker de verdad (Redpanda en Docker sería la opción).

## D-04. Unidad de trabajo: la partición mensual del fichero fuente
**Decisión:** la clave lógica es `(dataset=yellow, year, month)` y se toma del nombre del fichero, no del contenido. La versión física es el SHA-256 de los bytes. Curated se particiona por esa misma clave, no por el mes de pickup de cada fila.
**Por qué:** si particionamos por mes de pickup, una fila de diciembre que venga en el fichero de enero obliga a reescribir la partición de diciembre, y se rompe la garantía "añadir un mes solo toca su partición". Con la partición del fichero, cada mes es independiente y reprocesable por separado.
**Evidencia:** en 2024-01 solo 18 filas (0,001%) tienen pickup fuera de enero; 5 son de 2002 y 2009, claramente relojes mal puestos. No hay filas posteriores al 2 de febrero.
**Implica:** las filas con pickup fuera del mes del fichero van a cuarentena (R-04). La ruta de raw es `data/raw/year=YYYY/month=MM/<sha256>.parquet`.
**Estado:** vigente.

## D-05. Raw es inmutable y se identifica por contenido
**Decisión:** raw guarda los bytes tal cual llegan, nombrados por su SHA-256. Nunca se sobrescribe ni se borra. Un hash nuevo para el mismo mes es una **revisión del origen**: se guarda al lado y no sustituye a curated hasta que alguien lo acepte explícitamente (corte 2).
**Por qué:** TLC republica ficheros de meses pasados sin avisar. Si sobrescribimos, perdemos la capacidad de explicar por qué un agregado cambió. Guardar por hash hace la idempotencia trivial: mismo hash, mismo resultado, no hay nada que hacer.
**Evidencia:** hashes de referencia, descargados el 6 de agosto de 2026:
- 2024-01: `c4d59da7bbc8abaeeeb1727947ee93d9891a71acb42854bd80db1571b2030510` (49.961.641 bytes)
- 2025-01: `9af277e4c0d3f9deb30644da822981e1e7df6af58313170fd3aa8a474485488a` (59.158.238 bytes)
**Implica:** `acquire.py` calcula el hash antes de decidir si copia. Si la URL de descarga devuelve un hash distinto al conocido, no es un error: es una revisión.
**Estado:** vigente.

## D-06. Capas: raw, curated, quarantine, marts
**Decisión:** cuatro capas. `raw` bytes originales. `curated` filas que pasaron todas las puertas, con el contrato canónico aplicado. `quarantine` filas rechazadas con la lista de motivos. `marts` agregados (corte 6). No hay capa "bronze" intermedia: la transformación de raw a contrato se hace en memoria en DuckDB y solo se materializa el resultado.
**Por qué:** una capa intermedia materializada duplicaría 50 MB por mes sin que nadie la consulte. Si hace falta, raw + código la reconstruyen.
**Implica:** el layout de curated y quarantine replica `year=/month=/`. Cada fila de curated y quarantine lleva columnas de linaje (T-05).
**Estado:** vigente.

## D-07. Cuarentena, nunca borrado; una fila puede tener varios motivos
**Decisión:** ninguna regla elimina filas. Las que fallan una regla de severidad `reject` van a quarantine con una columna `reasons` que contiene **todos** los reason_codes que falló, no solo el primero.
**Por qué:** borrar destruye evidencia y hace imposible medir el impacto de cada regla. Guardar todos los motivos permite responder "cuántas filas caerían si quitara esta regla" sin reprocesar.
**Implica:** el motor evalúa todas las reglas para cada fila (un `CASE WHEN` por regla acumulado en una lista) y después separa. No hay corto-circuito.
**Estado:** vigente.

## D-08. Tres severidades: reject, warn, block
**Decisión:**
- `reject`: la fila va a cuarentena.
- `warn`: la fila se publica en curated; solo se cuenta y se informa en el resumen.
- `block`: el lote entero no se publica (reglas estructurales y de lote).
**Por qué:** hay anomalías que invalidan un viaje (duración negativa) y anomalías que solo indican que un campo es poco fiable (pasajeros = 0). Meter las segundas en cuarentena tiraría el 6% de los datos por un campo que la mayoría de los marts no usa. Y hay problemas que no son de una fila sino del fichero entero, para los que rechazar filas no tiene sentido.
**Implica:** cada regla en `docs/RULES.md` lleva una severidad; el motor las trata según ella.
**Estado:** vigente.

## D-09. Umbral de bloqueo del lote: más del 5% de filas rechazadas
**Decisión:** si las filas con severidad `reject` superan el 5% del fichero, no se publica curated ni quarantine y el comando termina con error.
**Por qué:** las reglas de rechazo están calibradas para capturar ruido de fila, no un fichero corrupto o un cambio de semántica en el origen. Si de repente el 20% de los viajes tiene importes negativos, lo que ha cambiado es el origen y hay que mirarlo, no publicar.
**Evidencia:** la unión de todas las reglas `reject` de RULES v0 afecta al 1,27% de 2024-01. El 5% deja un margen de casi cuatro veces.
**Implica:** B-01. El umbral es configuración, no constante en código.
**Estado:** vigente. Se recalibra cuando haya 12 meses procesados.

## D-10. El "bloque nulo" se conserva
**Decisión:** las filas en las que `passenger_count`, `RatecodeID`, `store_and_fwd_flag`, `congestion_surcharge` y `Airport_fee` son NULL a la vez se publican en curated con warn, no se rechazan.
**Por qué:** son registros enviados sin los campos extendidos, casi seguro por un proveedor o un canal concreto. Los campos que importan para un viaje (timestamps, zonas, importes) están presentes y son coherentes. Rechazarlos sesgaría cualquier agregado de ingresos.
**Evidencia:** 140.162 filas (4,73%) en 2024-01, exactamente las mismas filas en las cinco columnas, y las mismas que tienen `payment_type = 0`. En 2025-01 procesado (fichero descargado ago-2026, sha `9af277e4`): 85.030 filas con `payment_type = 0` (2,45%), muy por debajo de la cifra de 540.149 (15,5%) del perfilado anterior sobre `taxis_ny`. El fichero de TLC fue republicado entre ambas descargas; la evidencia actual manda. El patrón sigue siendo sistemático pero menor que en 2024-01.
**Implica:** R-11, R-13, R-14 son `warn`. `payment_type = 0` se conserva como código; el catálogo lo etiqueta "desconocido".
**Estado:** vigente.

## D-11. No hay regla de reconciliación de `total_amount`
**Decisión:** no se comprueba que `total_amount` sea igual a la suma de sus componentes. `total_amount` es la cifra autoritativa de lo cobrado.
**Por qué:** el origen no cumple esa igualdad de forma sistemática, y no por errores sino por cómo rellena `extra`.
**Evidencia:** 761.838 filas (25,7%) de 2024-01 no cuadran. El residuo es casi siempre exactamente -2,50 (591.045 filas) o +2,50 (129.332): la tasa de congestión aparece a la vez en `congestion_surcharge` y dentro de `extra` (3,50 = 1,00 de hora punta + 2,50). Es una convención del origen, no un fallo.
**Implica:** los marts de ingresos usan `total_amount`; los componentes se publican tal cual y se documentan como "no reconciliables".
**Estado:** vigente.

## D-12. Importes negativos se rechazan
**Decisión:** `fare_amount < 0` o `total_amount < 0` es `reject` con reason `negative_amount`.
**Por qué:** en los datos de TLC un importe negativo representa una anulación, reembolso o disputa registrada como viaje. No es un viaje cobrado y contaminaría los ingresos y los promedios de tarifa. En cuarentena siguen disponibles si algún día se quiere analizar reembolsos.
**Evidencia:** 37.448 filas (1,26%) con `fare_amount < 0`. El 76% de los totales negativos tienen `payment_type` 3 (sin cargo) o 4 (disputa). El signo de `fare_amount` y `total_amount` coincide en el 99,7% de los casos.
**Estado:** **PARA DISCUTIR** si más adelante se quiere un mart de anulaciones. Opciones: (a) mantener reject y construir ese mart desde quarantine, (b) pasar a warn y añadir una columna `is_refund`. Recomiendo (a): curated significa "viajes cobrados" y esa definición es simple de explicar.

## D-13. Duración máxima 24 horas, distancia máxima 200 millas
**Decisión:** duración > 24 h y `trip_distance > 200` son `reject`. Duración > 3 h y `trip_distance = 0` son `warn`.
**Por qué:** un taxi amarillo opera dentro del área metropolitana; un viaje de más de 24 h o de más de 200 millas no es un viaje sino un taxímetro que no se apagó o un GPS roto. En cambio 3 h a JFK con tráfico es raro pero posible, y distancia 0 con tarifa positiva es un patrón real (carreras canceladas con tarifa mínima, fallos de odómetro) que aparece en el 2% de las filas.
**Evidencia:** 16 filas con más de 24 h (ejemplo: 0,7 millas en 31 horas por 9,70 $). 31 filas con más de 200 millas (ejemplo: 312.722 millas en 13 minutos por 22 $). 1.983 filas entre 3 y 24 h. 60.371 filas con distancia 0, de las cuales 56.569 tienen tarifa positiva.
**Estado:** vigente. Los umbrales son configuración.

## D-14. Zonas 264 y 265 se conservan
**Decisión:** `PULocationID` o `DOLocationID` fuera de 1..265 es `reject`. Los valores 264 y 265 (Unknown y N/A en el catálogo oficial de zonas) son `warn`.
**Por qué:** 264 y 265 son valores legítimos del catálogo de TLC que significan "zona no determinada". El viaje ocurrió y se cobró; solo se pierde la dimensión geográfica. Un valor fuera del catálogo sí es un dato corrupto.
**Evidencia:** 0 filas fuera de 1..265; 31.527 filas (1,06%) con 264 o 265.
**Implica:** el catálogo de zonas (`taxi_zone_lookup.csv` de TLC) se versiona en el repositorio como dato de referencia pequeño en el corte 6.
**Estado:** vigente.

## D-15. Contrato canónico v1
**Decisión:** nombres en snake_case, tipos explícitos, dinero como DECIMAL(10,2), timestamps sin zona horaria.
- `vendor_id` INTEGER, `pickup_at` TIMESTAMP, `dropoff_at` TIMESTAMP, `passenger_count` INTEGER nullable, `trip_distance` DOUBLE, `ratecode_id` INTEGER nullable, `store_and_fwd_flag` VARCHAR nullable, `pu_location_id` INTEGER, `do_location_id` INTEGER, `payment_type` INTEGER, `fare_amount`, `extra`, `mta_tax`, `tip_amount`, `tolls_amount`, `improvement_surcharge`, `total_amount` DECIMAL(10,2), `congestion_surcharge`, `airport_fee`, `cbd_congestion_fee` DECIMAL(10,2) nullable.
**Por qué:**
- El origen alterna INT32 e INT64 para el mismo campo según el mes; un contrato fija un tipo y convierte.
- El dinero en DOUBLE produce residuos como 2,4999999999999964; DECIMAL(10,2) representa exactamente lo que el taxímetro cobró.
- Los timestamps de TLC son hora local de Nueva York sin zona. Convertirlos a UTC exigiría adivinar el lado correcto en los cambios de horario; se dejan como están y se documenta.
- `Airport_fee` se llama `airport_fee` en ficheros anteriores a 2024; el contrato mapea nombres sin distinguir mayúsculas.
**Evidencia:** esquemas físicos de 2024-01 y 2025-01 en `~/taxis_ny/docs/reference-data.md` y `DESCRIBE` sobre ambos ficheros.
**Estado:** vigente. Cualquier cambio sube la versión del contrato y queda registrado aquí.

## D-16. Columnas opcionales y ausentes
**Decisión:** `congestion_surcharge`, `airport_fee` y `cbd_congestion_fee` son opcionales. Si el fichero no trae la columna, curated la publica como NULL, nunca como 0. Una columna desconocida en el origen se registra con warn y se descarta. Una columna obligatoria ausente o con tipo no convertible bloquea.
**Por qué:** ausencia y cero significan cosas distintas. La tasa CBD no existía antes del 5 de enero de 2025; ponerle 0 en 2024 afirmaría que se aplicó y fue cero. Una columna nueva no rompe a nadie que consuma curated, así que no debe bloquear; solo avisar para que se añada al contrato si interesa.
**Evidencia:** en 2025-01 `cbd_congestion_fee` es 0 en 1.222.178 filas y positiva en 2.246.495; nunca NULL.
**Implica:** S-01, S-02, S-03 y T-03.
**Estado:** vigente.

## D-17. Sin deduplicación por viaje en v1
**Decisión:** no se intenta detectar viajes duplicados. Se mide el número de filas exactamente idénticas como métrica informativa.
**Por qué:** TLC no da identificador de viaje. Dos filas idénticas pueden ser dos viajes reales (misma zona, misma tarifa mínima, mismo minuto) o un duplicado. Sin clave no hay forma honesta de decidir, y borrar por parecido inventaría una garantía que no existe.
**Implica:** la idempotencia se garantiza a nivel de fichero y partición (D-05), no de fila.
**Estado:** vigente. Se revisa si la métrica de duplicados exactos supera el 0,1% en algún mes.

## D-18. Publicación atómica
**Decisión:** curated y quarantine se escriben en un directorio de staging y se mueven al destino con un rename. El estado "publicado" se registra después del rename, nunca antes.
**Por qué:** si el proceso muere a mitad de escritura, nadie debe ver una partición a medias como si fuera válida. Un rename dentro del mismo sistema de ficheros es atómico en Linux.
**Implica:** staging vive bajo `data/` para estar en el mismo filesystem. En el corte 2 se prueba con un fallo inyectado entre escribir y renombrar.
**Estado:** vigente.

## D-19. Manifiesto de estado en SQLite
**Decisión:** una base de datos SQLite en `data/control/manifest.db` registra cada partición publicada. Una tabla `partitions` con:

| Columna | Tipo | Descripción |
|---|---|---|
| year | INTEGER NOT NULL | Año de la partición |
| month | INTEGER NOT NULL | Mes de la partición |
| sha256 | TEXT NOT NULL | Hash del fichero raw procesado |
| contract_version | INTEGER NOT NULL | Versión del contrato aplicado |
| row_count | INTEGER NOT NULL | Filas en el fichero raw |
| curated_count | INTEGER NOT NULL | Filas publicadas en curated |
| quarantine_count | INTEGER NOT NULL | Filas en quarantine |
| published_at | TEXT NOT NULL | Timestamp ISO 8601 del momento de publicación |

Clave primaria: `(year, month)`. Solo un registro activo por partición; un reprocess actualiza el registro, no añade uno nuevo.
**Por qué:** la idempotencia a nivel de fichero (D-05) necesita saber qué se ha publicado para decidir si hay trabajo. SQLite es el motor de estado del stack (D-03), es un solo fichero copiable y consultable desde cualquier herramienta. Guardar solo el registro activo es suficiente para el corte 2; si se necesita historial de revisiones, se añade una tabla de log en un corte posterior.
**Evidencia:** con 24 particiones mensuales (D-02), la tabla nunca superará unas decenas de filas. No hay necesidad de un motor más pesado.
**Implica:**
- `manifest.py` con `lookup(year, month)` y `register(...)`.
- `ingest` consulta el manifiesto antes de procesar: mismo sha256 → skip; distinto sha256 → rechazar sin `--reprocess` (D-05: una revisión requiere aceptación explícita).
- El INSERT/UPDATE se ejecuta **después** del rename exitoso de publish (D-18), nunca antes.
- `--reprocess` salta la comprobación de idempotencia y actualiza el registro.
**Estado:** **PARA DISCUTIR** — ¿guardar solo el registro activo por partición, o mantener historial de todas las versiones procesadas? Recomiendo registro activo: el historial vive en git (commits de curated) y en los JSON de resumen impresos por stdout. Una tabla de log solo añade complejidad sin consumidor claro en este corte.

## D-20. El origen añade columnas `month` y `year`
**Decisión:** las columnas `month` y `year` que aparecen en los ficheros de TLC se descartan con warn (S-03). No se añaden al contrato.
**Por qué:** son redundantes con la clave de partición, que se toma del nombre del fichero (D-04). Incorporarlas al contrato no aporta información nueva y crearía ambigüedad si el valor de la columna no coincide con la partición.
**Evidencia:** los ficheros de referencia originales (descarga ago-2026) de 2024-01 tenían 19 columnas y 2025-01 tenía 22. TLC ha republicado los ficheros de 2024: las descargas de sep-2026 de 2024-02 y 2024-03 ya incluyen `month` y `year`. Las columnas aparecen en todo el rango, no solo a partir de 2025.
**Implica:** no hay cambio en código. S-03 las detecta y descarta correctamente en todos los meses.
**Estado:** vigente.

## D-21. Salto en `negative_amount` entre 2024-01 y 2025-01
**Decisión:** se registra como observación. No se cambia la regla R-07 ni el umbral de B-01.
**Por qué:** `negative_amount` (R-07) pasa de 37.448 rejects (1,26%) en 2024-01 a 144.439 (4,16%) en 2025-01. El ratio de rechazo total sube de 1,27% a 4,16%, todavía bajo el 5% de B-01 pero con margen muy reducido. Si la tendencia continúa en 2025-02, B-01 podría bloquear. Antes de cambiar el umbral conviene ver si es un patrón estable o un pico puntual.
**Evidencia:** resumen JSON de `ingest 2025-01`: 144.703 quarantine / 3.475.226 total = 4,16%.
**Implica:** vigilar los próximos meses. B-04 (row_count_drift, pendiente de implementar) ayudará a detectar estos saltos automáticamente. Si 2025-02 supera el 5%, se abre decisión sobre recalibrar B-01.
**Estado:** vigente.

## D-22. Descarga desde TLC
**Decisión:** `acquire.py` puede descargar el Parquet mensual desde TLC. URL: `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{YYYY}-{MM}.parquet`. La descarga se escribe en un fichero `.part` temporal y se renombra al completar, igual que la publicación (D-18). Si el proceso muere a mitad, el `.part` queda y no se confunde con un fichero completo. La descarga es por streaming (`stream=True`, `iter_content`) para no cargar 50-60 MB en memoria.
**Política de reintentos:**
- Reintentar (transitorios): 429, 500, 502, 503, 504, timeout de conexión/lectura, error de conexión. Máximo 4 intentos con backoff exponencial entre ellos (1s, 2s, 4s).
- No reintentar (permanentes): cualquier otro 4xx (401, 403, etc.). Se propaga la excepción.
- 404: no es error. Significa que TLC aún no ha publicado ese mes. `download()` devuelve `None`; quien llama lo traduce a `not_published`.
- Timeouts: 30s de conexión, 300s de lectura.
- Agotados los intentos: `RuntimeError` encadenado con la última excepción.
**Librería:** `requests` con `stream=True`. Es dependencia nueva en `pyproject.toml`.
**Dónde queda el fichero:** en raw, nombrado por su SHA-256, como cualquier otro origen (D-05). `download()` escribe el `.part` en la partición de raw, calcula el hash al completar y renombra a `<sha256>.parquet`. Devuelve ese `Path`. `get_file()` recibe después esa ruta, recalcula el hash y no copia porque el destino ya existe. Así raw tiene una sola copia por fichero y el nombre del fichero nunca depende del nombre que use TLC.
**Idempotencia:** `ingest --download` de un mes ya publicado descarga igualmente. Es el precio de detectar revisiones del origen (D-05): el hash no se conoce hasta tener los bytes. `backfill --download` no tiene ese coste porque solo pide los meses pendientes según el manifiesto.
**Implica:** firma `download(year, month, raw_base_path) -> Path | None`. Los mensajes de progreso de la descarga no van por stdout, que está reservado al resumen JSON (corte 1, etapa 6); van por stderr.
**Estado:** vigente.

## D-23. Flag `--download` en CLI
**Decisión:** `ingest` recibe un flag `--download`. Si se pasa, descarga de TLC en vez de exigir el fichero local. Los dos modos son excluyentes y pasar ambos, o ninguno, es error con exit 1. `backfill` acepta el mismo flag y descarga cada mes pendiente. Si un mes devuelve 404 durante el backfill, se anota en el resumen y se continúa con el siguiente: no es un error que deba frenar el backfill.
**Por qué:** un flag explícito deja claro qué va a hacer el comando. Hacer el fichero opcional e inferir "si no lo pasas, descarga" es ambiguo.
**Nombres:** en `ingest` el origen local es un fichero (`source_file`); en `backfill` es el directorio donde están los ficheros con nombre `yellow_tripdata_YYYY-MM.parquet` (`source_path`). Son cosas distintas y llevan nombre distinto. El nombre Python del flag puede ser `download_flag` para no pisar la función `download` importada, pero el nombre visible en CLI es `--download` (`typer.Option(False, "--download")`).
**Implica:** `source_file` y `source_path` pasan a ser `Optional[Path]` con default `None`. El resumen de `backfill` distingue lo procesado, lo no encontrado (404 o fichero local ausente) y el error que detuvo el bucle, si lo hubo.
**Estado:** vigente.

## D-24. Marts con dbt-duckdb
**Decisión:** los agregados analíticos se construyen con dbt-duckdb. El proyecto dbt vive en `dbt/` dentro del repo. dbt lee de curated (Parquet) y escribe marts como Parquet en `data/marts/<nombre>/`. Un comando `uv run taxis marts` envuelve `dbt run`.
**Por qué:** dbt aporta tres cosas que merece la pena aprender: un DAG declarativo de modelos SQL, materialización incremental, y tests de esquema integrados (`dbt test`). Hacerlo con scripts SQL sueltos funcionaría, pero no enseña el patrón que usa la industria para la capa de transformación analítica. Además, `dbt-duckdb` no necesita un warehouse remoto: lee y escribe Parquet local, coherente con el stack (D-01).
**Dependencia:** `dbt-duckdb` se añade como dependencia de producción en `pyproject.toml` (trae `dbt-core` como transitiva). No se añade `dbt-core` por separado.
**Estructura:**
```
dbt/
├── dbt_project.yml
├── profiles.yml          # versionado, con paths relativos a data/
├── models/
│   ├── sources.yml       # curated como source dbt
│   ├── mart_hourly.sql
│   ├── mart_daily.sql
│   └── mart_zone_pair.sql
└── target/               # no versionado (.gitignore)
```
**profiles.yml versionado:** se versiona porque usa paths relativos y no contiene credenciales. `target/` no se versiona.
**Implica:** `data/marts/` se añade a `.gitignore` junto con `dbt/target/`. El layout del repo se actualiza en PLAN.md.
**Estado:** vigente.

## D-25. Definición de marts
**Decisión:** tres marts, todos incrementales por mes.

**mart_hourly** — granularidad: (año, mes, zona_pickup, hora_del_día).
Columnas: `source_year`, `source_month`, `pu_location_id`, `hour_of_day`, `trip_count`, `avg_fare`, `avg_distance`, `avg_duration_min`.
Responde a: ¿qué zonas y franjas generan más actividad e ingreso?

**mart_daily** — granularidad: (día natural).
Columnas: `trip_date`, `trip_count`, `total_revenue`, `avg_distance`, `avg_duration_min`.
Responde a: ¿cómo varía la actividad día a día?

**mart_zone_pair** — granularidad: (año, mes, zona_pickup, zona_dropoff), solo pares con ≥ 10 viajes.
Columnas: `source_year`, `source_month`, `pu_location_id`, `do_location_id`, `trip_count`, `avg_fare`.
Responde a: ¿cuáles son las rutas más frecuentes y más caras?

**`source_year` en el grano:** los marts originales agrupaban solo por `source_month` (1-12), lo que mezclaría enero de 2024 con enero de 2025 al procesar varios años. Añadir `source_year` al grano de `mart_hourly` y `mart_zone_pair` hace que cada fila represente un mes-calendario concreto, y es necesario para que `delete+insert` borre solo las filas del mes que se reprocesa. `mart_daily` no necesita `source_year` en su salida porque `trip_date` ya identifica el día sin ambigüedad.
**Columnas excluidas del cálculo:** `reasons` (siempre vacía en curated), `warnings`, `source_sha256`, `contract_version`, `ingested_at`. Las columnas `month` y `year` de TLC también se excluyen (S-03 las descarta del schema pero DuckDB las genera por Hive partitioning al leer `year=*/month=*/`; los modelos las ignoran y usan `source_year`/`source_month` del linaje).
**Filtro base en todos los marts:** solo filas de curated, que por definición tienen `reasons` vacía. No se aplica filtro adicional sobre warnings: un viaje con `zero_distance` o `passenger_count_unknown` es un viaje válido para contar y promediar.
**Incrementalidad:** ver D-27.
**Estado:** vigente.

## D-27. DuckDB persistente, incrementalidad y rutas portables
**Decisión:** tres cambios que van juntos porque se necesitan mutuamente.

**DuckDB persistente.** `profiles.yml` pasa de `path: ":memory:"` a `path: "data/marts/marts.duckdb"`. Con `:memory:` las tablas desaparecían al terminar dbt y `is_incremental()` era siempre `False`. Con un fichero en disco, las tablas persisten entre ejecuciones y dbt puede detectar qué meses ya están procesados.
**Por qué no queda en `:memory:`:** la incrementalidad de dbt requiere que la tabla exista de una ejecución a la siguiente. Sin persistencia no hay referencia contra la que comparar.

**Incrementalidad `delete+insert`.** Los modelos cambian de `materialized='external'` a `materialized='incremental'` con `incremental_strategy='delete+insert'` y `unique_key=['source_year', 'source_month']` (en `mart_daily`, `unique_key=['trip_date']`). Un filtro `{% if is_incremental() %} WHERE (source_year, source_month) NOT IN (SELECT DISTINCT ... FROM {{ this }}) {% endif %}` excluye los meses que ya están en la tabla. `delete+insert` es la red de seguridad: si llegan datos de un mes que ya existía, borra las filas viejas antes de insertar las nuevas. Para reprocesar un mes, se usa `dbt run --full-refresh`.
**Por qué `delete+insert` y no `append`:** con `append`, un fallo o una re-ejecución duplicaría filas. `delete+insert` garantiza idempotencia a nivel de mes.

**Exportación a Parquet.** `materialized='external'` escribía los Parquet directamente. Con `incremental`, los marts viven como tablas en `marts.duckdb`. El comando `taxis marts` exporta cada tabla a `data/marts/<nombre>.parquet` con `COPY ... TO ... (FORMAT PARQUET)` después de `dbt run`. Ambos formatos coexisten: DuckDB es la fuente de verdad incremental, Parquet es la copia publicada.

**Rutas portables.** `profiles.yml`, `sources.yml` y los modelos ya no contienen `/home/alex/taxis/`. Todas las rutas son relativas a la raíz del proyecto, que es desde donde se ejecuta `taxis marts` (`uv run dbt run --project-dir dbt --profiles-dir dbt`). DuckDB resuelve las rutas relativas desde el CWD del proceso.
**Por qué no `env_var()`:** el comando siempre se lanza desde la raíz del proyecto. Una variable de entorno solo añadiría un paso de configuración sin consumidor que lo justifique.

**Implica:**
- `profiles.yml`: `path: "data/marts/marts.duckdb"`.
- `sources.yml`: `external_location: "data/curated_rows/year=*/month=*/curated_rows.parquet"`.
- Los modelos no tienen `location`; ya no usan `materialized='external'`.
- `cli.py`: `marts()` añade el paso de exportación a Parquet tras `dbt run`.
- `.gitignore`: `dbt/target/` y `dbt/logs/` añadidos (`data/marts/` ya está cubierto por `data/`).
- `marts.duckdb` se crea automáticamente en la primera ejecución. Borrarlo equivale a `--full-refresh`.
**Estado:** vigente.

## D-26. Observabilidad — descartada
**Decisión:** no se implementa una capa de observabilidad adicional.
**Por qué:** el pipeline ya emite un JSON de resumen por stdout con filas leídas, curated, quarantine, conteo por reason_code y resultado de cada gate. El manifiesto SQLite (D-19) registra qué se publicó y cuándo. Con 24 particiones en un entorno local, no hay ejecuciones desatendidas ni consumidores que necesiten alertas o dashboards. Añadir una tabla `runs` o log estructurado sería un `INSERT INTO` sin consumidor real — esfuerzo que no enseña nada nuevo ni mejora el pipeline.
**En producción se haría distinto:** si el pipeline corriera en un scheduler (Airflow, cron) sin nadie mirando, se añadiría: tabla `runs` en SQLite para consultar historial, métricas por etapa (filas/segundo, duración), alertas cuando el ratio de rechazo suba (D-21 como antecedente), y log estructurado compatible con un agregador (ELK, Datadog). La infraestructura actual no lo justifica.
**Estado:** descartada.
