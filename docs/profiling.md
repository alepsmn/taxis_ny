# Perfil mínimo reproducible

## Propósito

Definir qué medir en los Parquet Yellow Taxi 2024-01 y 2025-01 antes de
redactar el contrato de datos v0. Cada métrica debe aportar evidencia para una
decisión de contrato o para una posible regla de calidad.

Esta especificación no implementa el perfil, no corrige valores y no convierte
anomalías observadas en reglas definitivas de cuarentena.

## Entradas identificadas

| Mes | Ruta local | SHA-256 esperado |
|---|---|---|
| 2024-01 | `data/reference/yellow_tripdata_2024-01.parquet` | `c4d59da7bbc8abaeeeb1727947ee93d9891a71acb42854bd80db1571b2030510` |
| 2025-01 | `data/reference/yellow_tripdata_2025-01.parquet` | `9af277e4c0d3f9deb30644da822981e1e7df6af58313170fd3aa8a474485488a` |

Los resultados solo son comparables si proceden de estos contenidos o si una
revisión posterior queda identificada con otro hash.

## Principios de interpretación

- El perfil registra hechos observados; no define por sí solo valores válidos.
- `MIN` y `MAX` delimitan el rango observado, no el rango permitido.
- Un valor extremo requiere investigación; no se elimina solo por ser raro.
- `NULL` y cero no son equivalentes.
- La frecuencia mide impacto, no validez semántica.
- Los tipos físicos no determinan qué métricas tienen sentido: manda la
  semántica del campo.
- Raw se conserva sin correcciones. Cualquier normalización o cuarentena se
  decidirá después en el contrato y las reglas de calidad.

## Clasificación semántica

| Familia | Columnas |
|---|---|
| Identificadores | `PULocationID`, `DOLocationID` |
| Categóricas codificadas | `VendorID`, `RatecodeID`, `store_and_fwd_flag`, `payment_type` |
| Conteo discreto | `passenger_count` |
| Medida continua | `trip_distance` |
| Timestamps | `tpep_pickup_datetime`, `tpep_dropoff_datetime` |
| Importes monetarios | `fare_amount`, `extra`, `mta_tax`, `tip_amount`, `tolls_amount`, `improvement_surcharge`, `total_amount`, `congestion_surcharge`, `Airport_fee` y, cuando exista, `cbd_congestion_fee` |

La clasificación es lógica. Una columna almacenada como número puede ser un
identificador o un código categórico y no una magnitud calculable.

## Métricas comunes

Para cada archivo:

- Ruta y SHA-256 del contenido analizado.
- Número total de filas.
- Nombre y tipo lógico de cada columna.
- Conteo y porcentaje de `NULL` por columna.

La presencia de `NULL` demuestra nulabilidad observada en el origen. No decide
si `curated` debe admitirlo. La decisión depende de la función semántica del
campo, su criticidad y el impacto de rechazar esas filas.

## Métricas por familia

### Identificadores y categóricas

- Valores distintos no nulos.
- Conteo y porcentaje por valor, incluido `NULL` por separado.
- Contraste con un dominio oficial versionado cuando exista.

`COUNT(DISTINCT ...)` aislado no muestra los valores ni prueba que pertenezcan
al dominio válido. Para zonas, la pertenencia se contrastará con una versión
identificada del catálogo; el rango numérico del ID no representa distancia ni
proximidad geográfica.

### Conteos discretos

Para `passenger_count`:

- Frecuencia de cada valor, incluido `NULL`.
- Mínimo y máximo observados.
- Conteo y porcentaje de valores negativos.

Un `NULL` puede representar número de pasajeros desconocido sin invalidar todo
el viaje. La severidad se decidirá después con evidencia semántica.

### Distancia

Para `trip_distance`:

- Mínimo, máximo, P50, P95 y P99.
- Conteo y porcentaje de valores negativos.
- Conteo y porcentaje de valores iguales a cero.

Los extremos permiten localizar casos que investigar. No justifican aplicar
`ABS`, reemplazar por cero ni definir un límite válido sin más evidencia.

### Timestamps y duración derivada

- Mínimo y máximo de recogida y entrega.
- Conteo y porcentaje de `NULL` en cada timestamp.
- Conteo de recogidas fuera del mes nominal del archivo.
- Conteo y porcentaje de duraciones negativas.
- Conteo y porcentaje de duraciones cero.
- Separación de duración cero con distancia cero y con distancia positiva.

La partición canónica propuesta usa el mes de `tpep_pickup_datetime`, porque
asigna el viaje al mes en que comienza. Esta propuesta se confirmará en el
contrato v0. Una duración negativa contradice el orden temporal, pero no indica
cuál timestamp es incorrecto. Una duración cero es una anomalía distinta y
requiere contraste con distancia e importes.

### Importes monetarios

Para cada importe:

- Mínimo, máximo, P50, P95 y P99.
- Conteo y porcentaje de negativos.
- Conteo y porcentaje de `NULL`.

Para `total_amount`, además se medirá la diferencia respecto a la suma de los
componentes que la documentación aplicable confirme. La comparación admitirá
una tolerancia monetaria explícita para diferencias de representación de
`DOUBLE`; la tolerancia no debe ocultar componentes ausentes ni discrepancias
semánticas. La fórmula y el umbral quedan pendientes de confirmación.

## Comprobaciones cruzadas

- Duración negativa: `dropoff < pickup`.
- Duración cero con distancia positiva.
- Distancia negativa o cero, segmentada por duración e importes.
- Diferencia entre `total_amount` y componentes documentados.
- Códigos categóricos observados fuera de dominios documentados.
- IDs de zona no presentes en el catálogo versionado.

Cada comprobación debe informar filas afectadas y porcentaje. Un patrón
frecuente puede indicar evolución sistemática del origen; no se vuelve válido
ni inválido solo por su frecuencia.

## Salida e interfaz previstas

La implementación posterior expondrá una interfaz equivalente a:

```bash
uv run python scripts/profile_parquet.py data/reference/yellow_tripdata_2024-01.parquet
uv run python scripts/profile_parquet.py data/reference/yellow_tripdata_2025-01.parquet
```

La salida debe ser determinista, incluir la identidad del archivo y permitir
comparar ambos meses. El formato concreto se decidirá al comenzar F1-02. Los
archivos Parquet y las filas reales no se versionarán.

## Límites

El perfil no demuestra la corrección del taxímetro, del proveedor ni de TLC.
Tampoco permite recuperar valores verdaderos ausentes, intercambiar timestamps,
convertir importes `NULL` en cero ni corregir extremos por intuición.
