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

Definir el backlog verificable de la fase 1.

## Criterio de aceptación de la tarea

- Cada tarea de la fase 1 tiene un resultado observable.
- Cada tarea incluye un criterio de aceptación verificable.
- El backlog no introduce implementación del pipeline ni tecnologías fuera del alcance.

## Pendiente para cerrar la fase 0

- Versionar la licencia.
- Crear el backlog de tareas de la fase 1.
- Clonar el repositorio en otra carpeta y verificar que el contexto del proyecto se recupera sin archivos locales ocultos.

## Decisiones diferidas

- La licencia del repositorio se decidirá más adelante. La fase 0 no puede cerrarse hasta resolverla o modificar explícitamente su puerta de salida.

## Bloqueos

Ninguno.

## Siguiente paso único

Convertir las tareas de reconocimiento de datos de la fase 1 en un backlog con criterios de aceptación.

## Documento de fase

`docs/PHASES.md`, sección «Fase 0 — Entorno y contrato del proyecto».
