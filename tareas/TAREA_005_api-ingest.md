# TAREA 005 — FastAPI app + endpoint POST /ingest

- Fecha asignada: 2026-05-17
- Fase del MVP: 1 — Core RAG
- Estimación: ≤ 1 día
- Depende de: TAREA 004

## Objetivo
Levantar la aplicación FastAPI con su estructura base y el endpoint `POST /ingest` que orquesta todo el pipeline de ingesta: recibe un archivo, lo guarda en Supabase Storage, extrae texto, chunkea y guarda embeddings.

## Archivos a crear / modificar
- `src/api/main.py` — app FastAPI con health check
- `src/api/schemas.py` — modelos Pydantic de request/response
- `src/api/routes/ingest.py` — router con `POST /ingest`
- `src/api/__init__.py` — vacío
- `src/api/routes/__init__.py` — vacío
- `tests/test_ingest.py` — tests con TestClient (mocks de OpenAI y Supabase)

## Contrato

### `GET /`
```json
{ "status": "ok", "servicio": "RAG-Obras API" }
```

### `POST /ingest`
**Request**: `multipart/form-data`
```
archivo:     file  (PDF / DOCX / PNG / JPG)
proyecto_id: int
nombre:      str   (nombre legible del documento)
tipo:        str   (manual | especificacion | plano | protocolo | cronograma)
sector:      str   (opcional, puede ser "")
```

**Response 200**:
```json
{
  "documento_id": 42,
  "nombre": "manual_seguridad.pdf",
  "chunks_generados": 18,
  "es_imagen": false,
  "status": "ok"
}
```

**Response 422**: validación Pydantic fallida (automático).
**Response 500**: error interno con `{"error": "mensaje legible"}` — nunca exponer stack trace ni secrets.

### Pipeline interno de `/ingest`
1. Guardar el archivo en Supabase Storage (bucket `documentos`, path `{proyecto_id}/{nombre_archivo}`).
2. Insertar fila en tabla `documentos` con `ruta_archivo` = path de Storage.
3. Llamar `extraer(ruta_local_tmp)` → `DocumentoExtraido`.
4. Si `es_imagen=False`: llamar `chunkear(texto, metadata_base)` → lista de chunks.
5. Llamar `embeder_y_guardar(chunks, documento_id, proyecto_id)`.
6. Actualizar `documentos.texto_extraido` con el texto extraído.
7. Retornar response.

Para guardar temporalmente el archivo antes de procesar: usar `tempfile.NamedTemporaryFile`.

### Bucket de Storage
Nombre del bucket: `documentos`. Si no existe, crearlo al inicio de la app (startup event o simplemente documentar que debe existir — no crear automáticamente si eso requiere permisos extra).

## Criterios de aceptación
- [ ] `GET /` devuelve `{"status": "ok", ...}`.
- [ ] `POST /ingest` con PDF válido → respuesta 200 con `documento_id` y `chunks_generados > 0`.
- [ ] `POST /ingest` con imagen → `es_imagen: true`, `chunks_generados: 0`.
- [ ] Error 500 nunca expone secrets ni stack traces.
- [ ] `pytest tests/test_ingest.py` pasa (mocks de Storage, OpenAI y Supabase insert).
- [ ] La app arranca con `uvicorn src.api.main:app --host 0.0.0.0 --port 8000` sin errores.

## Cómo probar
```bash
# Levantar la API
uvicorn src.api.main:app --reload --port 8000

# Health check
curl http://localhost:8000/

# Ingest de prueba (necesita .env con keys válidas)
curl -X POST http://localhost:8000/ingest \
  -F "archivo=@data/demo/test.pdf" \
  -F "proyecto_id=1" \
  -F "nombre=test.pdf" \
  -F "tipo=manual" \
  -F "sector=norte"

# Tests unitarios (mockeados)
pytest tests/test_ingest.py -v
```

## Qué NO hacer
- Sin autenticación — fuera del MVP.
- Sin procesamiento async dentro del endpoint (puede bloquear, está bien para demo).
- Sin soporte de Excel en esta tarea.
- No exponer `/ingest` con método GET.
- El bucket de Storage no tiene que ser público.

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_005_resumen.md` y pushearlo:

```markdown
# Resumen TAREA 005

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Qué quedó fuera de scope
## Cómo probarlo
```

**Sin este archivo, la tarea no se considera entregada.**
