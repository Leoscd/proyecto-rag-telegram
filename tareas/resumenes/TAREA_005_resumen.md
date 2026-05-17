# Resumen TAREA 005

## Qué se implementó
- FastAPI app en `src/api/main.py` con health check `GET /`
- Endpoint `POST /ingest` en `src/api/routes/ingest.py`
- Esquemas Pydantic en `src/api/schemas.py`
- Pipeline: Storage → extraer → chunkear → embedder → guardar en Supabase

## Decisiones tomadas
- Usé multipart/form-data para recibir archivo
- Guardado temporal con tempfile para procesar
- Validación de tipos con TIPOS_VALIDOS
- Bucket "documentos" en Supabase Storage

## Problemas encontrados
- Ninguno significativo

## Qué quedó fuera de scope
- Autenticación — fuera del MVP
- Excel — tarea futura
- Async dentro del endpoint

## Cómo probarlo
```bash
uvicorn src.api.main:app --reload --port 8000
curl http://localhost:8000/
curl -X POST http://localhost:8000/ingest \
  -F "archivo=@data/demo/test.pdf" \
  -F "proyecto_id=1" \
  -F "nombre=test.pdf" \
  -F "tipo=manual"
```