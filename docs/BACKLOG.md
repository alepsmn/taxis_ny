# Backlog — Fase 1

Objetivo de la fase: diseñar el contrato desde evidencia reproducible de los
Parquet Yellow Taxi 2024-01 y 2025-01, sin implementar todavía el downloader ni
el pipeline productivo.

## F1-01 — Definir el perfil mínimo reproducible

- **Resultado:** especificación breve de las métricas necesarias para reconocer ambos archivos sin convertir el trabajo en análisis exploratorio abierto.
- **Propiedad protegida:** toda métrica calculada debe justificar una decisión posterior del contrato o de calidad.
- **Dependencias:** inspección física de 2024-01 completada.
- **Criterio de aceptación:** quedan definidos, por columna, tipo lógico observado, nulabilidad, valores extremos relevantes y cardinalidad cuando aporte evidencia; cada métrica incluye su propósito y el comando previsto para obtenerla.
- **Duración prevista:** 45–60 minutos.

## F1-02 — Perfilar valores de 2024-01

- **Resultado:** perfil reproducible del archivo de referencia 2024-01 según F1-01.
- **Propiedad protegida:** los resultados se derivan del Parquet identificado por su SHA-256 documentado y pueden repetirse con un comando versionado.
- **Dependencias:** F1-01.
- **Criterio de aceptación:** el comando termina sobre el archivo local documentado, produce todas las métricas acordadas y conserva resultados verificables sin copiar datos reales al repositorio.
- **Duración prevista:** 60–90 minutos.

## F1-03 — Perfilar valores de 2025-01

- **Resultado:** perfil reproducible de 2025-01 comparable con el de 2024-01.
- **Propiedad protegida:** una diferencia entre meses se observa sobre archivos identificados, no se infiere desde documentación externa.
- **Dependencias:** F1-02.
- **Criterio de aceptación:** se ejecutan las mismas métricas sobre el SHA-256 documentado de 2025-01 y el resultado incluye presencia, tipo lógico, nulabilidad y valores observados de `cbd_congestion_fee`.
- **Duración prevista:** 60–90 minutos.

## F1-04 — Comparar esquema y perfil entre 2024-01 y 2025-01

- **Resultado:** comparación reproducible que separa cambios físicos, cambios lógicos y cambios de distribución relevantes.
- **Propiedad protegida:** la evolución del contrato se basa en diferencias observadas y clasificadas.
- **Dependencias:** F1-02 y F1-03.
- **Criterio de aceptación:** la comparación identifica columnas añadidas, eliminadas o con tipo distinto; documenta la aparición de `cbd_congestion_fee`; y distingue hechos observados de decisiones todavía propuestas.
- **Duración prevista:** 60–90 minutos.

## F1-05 — Redactar el contrato de datos v0

- **Resultado:** contrato canónico versionado para las columnas aceptadas de Yellow Taxi.
- **Propiedad protegida:** cada campo publicado tiene nombre, tipo lógico, nulabilidad y tratamiento de evolución explícitos.
- **Dependencias:** F1-04.
- **Criterio de aceptación:** el contrato cubre ambos meses, define el tratamiento de `cbd_congestion_fee` cuando no existe en 2024-01 y no atribuye garantías todavía no implementadas.
- **Duración prevista:** 90–120 minutos.

## F1-06 — Definir reglas de calidad iniciales

- **Resultado:** catálogo versionado de reglas candidatas para validar o poner filas en cuarentena durante fases posteriores.
- **Propiedad protegida:** ninguna fila se rechaza por intuición ni por ser un outlier sin justificación semántica.
- **Dependencias:** F1-04 y F1-05.
- **Criterio de aceptación:** cada regla indica campo, condición, fundamento semántico, severidad, acción prevista y métrica de impacto; las reglas no ejecutadas están marcadas como propuestas.
- **Duración prevista:** 60–90 minutos.

## F1-07 — Documentar el alcance Yellow Taxi en un ADR

- **Resultado:** ADR que explica por qué el contrato inicial se limita a Yellow Taxi.
- **Propiedad protegida:** el alcance puede reconstruirse sin inventar motivaciones retrospectivas.
- **Dependencias:** F1-05 y F1-06.
- **Criterio de aceptación:** el ADR contiene contexto, alternativas reales, decisión, consecuencias, límites y condición de revisión; diferencia evidencia confirmada de trabajo futuro.
- **Duración prevista:** 45–60 minutos.

## F1-08 — Verificar la puerta de salida de la fase 1

- **Resultado:** revisión conjunta de perfiles, comparación, contrato, reglas y ADR antes de comenzar la fase 2.
- **Propiedad protegida:** la fase no se cierra por existencia de archivos, sino por evidencia reproducible y comprensión demostrada.
- **Dependencias:** F1-01 a F1-07.
- **Criterio de aceptación:** las verificaciones relevantes pasan, el diff no contiene datos reales ni cambios accidentales y el autor puede dar un resumen de 60 segundos, un recorrido de 5 minutos y defender una decisión con alternativa, trade-off y límite.
- **Duración prevista:** 45–60 minutos.
