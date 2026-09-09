# Instrucciones para Claude en este repositorio

Pipeline de Data Engineering sobre NYC TLC Yellow Taxi. Alex programa; Claude decide y explica reglas de negocio y diseño.

## Al empezar cada sesión
1. Leer `PLAN.md` completo. La sección "Siguiente tarea" es la única tarea activa.
2. Leer de `docs/DECISIONS.md` y `docs/RULES.md` solo las entradas que afectan a esa tarea.
3. Mirar `git status` y `git log --oneline -10`.
4. Decir en dos líneas: tarea activa y qué falta para cerrarla.

## Reparto
- Alex escribe todo el código en `src/taxis/` y `tests/`. Claude no implementa salvo petición explícita.
- Claude mantiene solo tres documentos: `PLAN.md`, `docs/DECISIONS.md`, `docs/RULES.md`. No crear más documentos de estado, backlog ni ADR.
- Toda decisión de negocio se escribe en `docs/DECISIONS.md` con: qué, por qué, evidencia, qué implica en código, estado. Las discutibles se marcan **PARA DISCUTIR** con recomendación.
- Toda regla o transformación se escribe en `docs/RULES.md` antes de implementarse, con id estable, severidad, condición SQL y reason_code.

## Cómo revisar código de Alex
- Comparar contra `docs/RULES.md` y las decisiones aplicables, no contra preferencias propias.
- Señalar primero lo que rompe una regla o garantía; después estilo.
- Explicar el porqué de cada observación en una o dos frases.

## Al cerrar una tarea
Actualizar "Siguiente tarea" en `PLAN.md`. No actualizar nada más salvo que una decisión haya cambiado.

## Fijo
- Stack: Python 3.12, uv, DuckDB, Parquet, SQLite. Sin Kafka, Spark ni Airflow salvo decisión registrada.
- `~/taxis_ny` es el intento anterior. Es archivo: no se edita ni se referencia como fuente de verdad.
- `data/` no se versiona. Nunca poner filas reales en Git.
