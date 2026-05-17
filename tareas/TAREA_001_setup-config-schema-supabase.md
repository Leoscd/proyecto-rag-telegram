# TAREA 001 — Setup de configuración + esquema Supabase + verificación de conexión

- Fecha asignada: 2026-05-15
- Fase del MVP: 1 Core RAG
- Estimación: ≤ 1 día
- Depende de: ninguna

## Objetivo
Dejar la base del proyecto operativa: un módulo de configuración que carga las variables de entorno, el esquema completo de la base de datos creado en Supabase (con `pgvector` y el índice vectorial), y un chequeo que confirma que la app conecta a Supabase. Sin esto ninguna tarea de ingesta o query puede avanzar.

## Contexto mínimo necesario
- Estructura de datos y stack: `BRIEFING_CLAUDE_CODE.md`, secciones "Estructura de datos principal" y "Stack tecnico definido".
- Embeddings: OpenAI `text-embedding-3-large`, dimensión **3072** → la columna `embedding` es `vector(3072)`.
- Reglas del repo: `CLAUDE.md`.

## Archivos a crear / modificar
- `src/config.py` — carga y valida las variables de entorno con `python-dotenv` + Pydantic. Expone un objeto `settings` con: `openai_api_key`, `minimax_api_key`, `minimax_group_id`, `supabase_url`, `supabase_key`, `telegram_bot_token`. Falla con mensaje claro si falta alguna.
- `src/db.py` — crea y expone el cliente de Supabase usando `settings`. Función `get_client()`.
- `migrations/001_schema.sql` — DDL idempotente del esquema completo (ver contrato).
- `scripts/check_conexion.py` — script que carga `settings`, conecta a Supabase, hace un `select` trivial sobre `proyectos` y reporta OK/error sin exponer secrets.
- `tests/test_config.py` — tests del cargador de configuración (ver criterios).

## Contrato (inputs / outputs)

`migrations/001_schema.sql` debe crear (idempotente, `if not exists`):

- `create extension if not exists vector;`
- **proyectos**: `id` (pk), `nombre`, `descripcion`, `fecha_inicio`, `activo` (bool default true)
- **documentos**: `id` (pk), `proyecto_id` (fk → proyectos), `nombre`, `tipo`, `sector`, `ruta_archivo`, `texto_extraido`, `fecha_carga` (default now())
- **chunks**: `id` (pk), `documento_id` (fk → documentos), `proyecto_id` (fk → proyectos), `texto`, `embedding vector(3072)`, `metadata jsonb`
- **consultas**: `id` (pk), `proyecto_id` (fk → proyectos), `usuario_telegram`, `mensaje_original`, `respuesta_generada`, `chunks_usados` (array), `score_maximo` (float), `timestamp` (default now())
- Índice vectorial sobre `chunks.embedding` para distancia **coseno** (ivfflat o hnsw, operador `vector_cosine_ops`).

`src/config.py`:
```python
from src.config import settings
settings.supabase_url  # str, garantizado no vacío o error al importar/instanciar
```

## Criterios de aceptación
- [ ] `migrations/001_schema.sql` corre completo sobre una base limpia sin errores y es re-ejecutable sin romper (idempotente).
- [ ] La columna `chunks.embedding` es `vector(3072)` y existe el índice vectorial coseno.
- [ ] `src/config.py` lee `.env`, valida que las 6 variables existan y da un error claro y específico si falta alguna (sin imprimir el valor del secret).
- [ ] `python scripts/check_conexion.py` imprime un OK legible cuando las credenciales son válidas y un error claro si no, sin volcar secrets.
- [ ] `pytest tests/test_config.py` pasa: cubre caso "faltan variables → error" y "todas presentes → settings carga".
- [ ] `.env` NO se commitea; `.env.example` queda con las claves vacías.

## Cómo probar
```bash
pip install -r requirements.txt
# aplicar migrations/001_schema.sql en Supabase (SQL editor o psql)
pytest tests/test_config.py -q
python scripts/check_conexion.py
```
Para el test de "faltan variables", usar variables de entorno de prueba / monkeypatch — no depender de un `.env` real.

## Qué NO hacer
- No implementar ingesta, chunking, embeddings, retriever, API ni bot todavía (son tareas siguientes).
- No agregar autenticación, multiproyecto con permisos ni RLS fina (fuera del MVP).
- No instalar dependencias pesadas ni modelos locales.
- Sin abstracciones especulativas (ORM, capa de repos, factories): cliente Supabase directo alcanza.

## Notas para revisión
- Revisar que la dimensión del vector sea exactamente 3072 (coherente con `text-embedding-3-large`).
- Revisar que ningún secret quede hardcodeado ni se loguee.
- Revisar que el índice use operador de coseno (coherente con la búsqueda futura del retriever).
- `check_conexion.py` y `config.py` deben fallar con mensajes accionables, no stack traces crudos.

---

### Tareas siguientes (no desarrollar aún — referencia de roadmap Fase 1)
- TAREA 002 — Extractor de texto de PDF (PyMuPDF) y Word (python-docx).
- TAREA 003 — Chunker 500 tokens / 50 overlap (medido en tokens, con metadata).
- TAREA 004 — Embedder OpenAI + guardado de chunks en Supabase (lotes, reintentos).
- TAREA 005 — Retriever: búsqueda coseno top-5 filtrada por proyecto.
- TAREA 006 — Endpoint `POST /query`: embedding → retrieve → prompt → MiniMax → respuesta + log en `consultas`.
