# Resumen TAREA 007

## Qué se implementó
- `src/rag/responder.py` — llama MiniMax API (text-embedding-3-large)
- `src/api/routes/query.py` — endpoint POST /query (embedding → retrieval → prompt → MiniMax)
- `src/api/routes/logs.py` — endpoint GET /logs para dashboard
- Tests en `tests/test_responder.py` y `tests/test_query.py`

## Decisiones tomadas
- Modelo MiniMax: "MiniMax-Text-01"
- Temperature 0.2 si contexto pobre, 0.3 si normal
- Timeout 30s
- Inserción automática en tabla `consultas` después de cada query

## Problemas encontrados
- Ninguno significativo

## Qué quedó fuera de scope
- Streaming de respuesta
- Historial multi-turno
- Caché de respuestas
- Smoke test end-to-end (sin credenciales Supabase configuradas)

## Resultado del smoke test end-to-end
- No se ejecutó: requiere credenciales reales de Supabase + OpenAI + MiniMax
- Para probar: tener las credenciales en .env y ejecutar:
  ```bash
  uvicorn src.api.main:app --port 8000
  curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"proyecto_id": 1, "mensaje": "protocolo de seguridad", "usuario_telegram": "test"}'
  ```

## Cómo probarlo
```bash
pytest tests/test_responder.py -v
# Levantar API y probar endpoints (requiere .env con credenciales)
uvicorn src.api.main:app --port 8000
curl http://localhost:8000/
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"proyecto_id":1,"mensaje":"test","usuario_telegram":"user"}'
curl "http://localhost:8000/logs?proyecto_id=1"
```

---

## 🎉 FASE 1 CORE RAG COMPLETA

Todas las tareas de la Fase 1 implementadas:
- TAREA 001: Setup config + schema
- TAREA 002: Extractor PDF/Word/imagen
- TAREA 003: Chunker 500 tokens
- TAREA 004: Embedder OpenAI
- TAREA 005: FastAPI + POST /ingest
- TAREA 006: Retriever + prompt builder
- TAREA 007: POST /query + MiniMax + GET /logs