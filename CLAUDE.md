# RAG-Obras — Reglas para el colaborador (ejecución con MiniMax 2.7)

Este repo implementa el sistema RAG para obras descrito en `BRIEFING_CLAUDE_CODE.md` (raíz del repo). El trabajo se hace por tareas diarias dejadas en `tareas/TAREA_NNN_*.md`. Hacé **solo la tarea del día**, contra sus criterios de aceptación.

## Reglas

1. **No salgas del alcance de la tarea.** Lo que no esté en la spec del día no se hace, aunque parezca buena idea. Si algo falta, anotalo, no lo implementes.
2. **Stack fijo, sin sustituciones.** FastAPI · python-telegram-bot · OpenAI `text-embedding-3-large` (3072) · MiniMax API (respuesta) · Supabase (pgvector/Storage/Postgres) · front HTML/CSS/JS vanilla. Sin frameworks JS. Sin modelos locales pesados (sin torch/transformers/sentence-transformers locales).
3. **Nombres exactos.** Tablas: `proyectos`, `documentos`, `chunks`, `consultas`. Endpoints: `/ingest`, `/query`, `/logs`. Vector dimensión 3072. Chunking 500 tokens / 50 overlap. Similitud coseno, top 5.
4. **Secrets solo por entorno.** Nada hardcodeado. Variables en `.env` (no commitear); `.env.example` con claves vacías sí se versiona. Variables: `OPENAI_API_KEY`, `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`, `SUPABASE_URL`, `SUPABASE_KEY`, `TELEGRAM_BOT_TOKEN`.
5. **Pensá en el VPS chico (2GB/1vCPU, compartido).** No cargar todo en RAM; procesar documentos en lotes/streaming. Sin servicios escuchando en `0.0.0.0` público — el VPS está en red privada Tailscale. Bot por long polling.
6. **Sin over-engineering.** Resolvé la tarea, no el futuro. Tres líneas repetidas antes que una abstracción prematura. Sin feature flags ni capas de compatibilidad que la tarea no pidió.
7. **Tests.** Si la tarea pide tests, que prueben lo que importa y pasen. No mockear lo que la spec diga que se prueba de verdad.
8. **Estructura de carpetas** según el briefing (`src/ingesta`, `src/rag`, `src/bot`, `src/api`, `src/dashboard`, `tests/`).

## Entrega

- Commit/PR enfocado solo en la tarea del día, con mensaje que diga qué tarea cierra (`TAREA_NNN`).
- En el PR/entrega, listá qué criterios de aceptación cumpliste y cuáles no y por qué.
- La revisión y aprobación las hace el equipo Leonardo + Claude; no implementes en el VPS por tu cuenta salvo que la tarea lo indique.
