# TAREA 007 — Endpoint POST /query + Responder MiniMax + GET /logs

- Fecha asignada: 2026-05-17
- Fase del MVP: 1 — Core RAG
- Estimación: ≤ 1 día
- Depende de: TAREA 006

## Objetivo
Cerrar la Fase 1 Core RAG implementando el endpoint `/query` que orquesta embedding → retrieval → respuesta MiniMax, el endpoint `/logs` para el dashboard, y el responder que llama a la API de MiniMax.

## Archivos a crear / modificar
- `src/rag/responder.py` — llama MiniMax API y retorna texto
- `src/api/routes/query.py` — endpoint `POST /query`
- `src/api/routes/logs.py` — endpoint `GET /logs`
- `tests/test_query.py`
- `tests/test_responder.py` (MiniMax mockeado)

## Contrato

### responder.py

```python
def responder(
    prompt: str,
    contexto_pobre: bool = False,
) -> str:
    """
    Llama MiniMax API con el prompt construido por prompt_builder.
    Si contexto_pobre=True, agregar temperatura más baja / instrucción conservadora.
    Retorna el texto de la respuesta.
    Lanza RuntimeError si la API falla.
    """
```

#### Llamada a MiniMax (HTTP POST con httpx)
```
URL: https://api.minimax.chat/v1/text/chatcompletion_v2
Headers:
  Authorization: Bearer {MINIMAX_API_KEY}
  Content-Type: application/json
Body:
{
  "model": "MiniMax-Text-01",
  "messages": [{"role": "user", "content": prompt}],
  "temperature": 0.3,
  "max_tokens": 1024
}
```
Timeout: 30 segundos. Si falla: lanzar `RuntimeError("Error al llamar MiniMax: {detalle}")`.

---

### POST /query

**Request JSON**:
```json
{
  "proyecto_id": 1,
  "mensaje": "como se hace el revoque exterior en el sector norte",
  "usuario_telegram": "operario_garcia"
}
```

**Response 200**:
```json
{
  "respuesta": "Según el manual...",
  "chunks_usados": [12, 15, 8, 3, 21],
  "score_maximo": 0.31,
  "contexto_pobre": false,
  "tiene_imagen": true,
  "ruta_imagen": "documentos/1/plano_norte.pdf"
}
```

**`tiene_imagen`**: `True` si alguno de los chunks recuperados tiene `metadata.es_imagen == True`.
**`ruta_imagen`**: `metadata.ruta_archivo` del primer chunk con `es_imagen=True` (para que el bot adjunte el archivo).

**Pipeline interno**:
1. Generar embedding del `mensaje` con OpenAI `text-embedding-3-large`.
2. Llamar `recuperar(embedding, proyecto_id)`.
3. Llamar `construir_prompt(mensaje, chunks)` → `(prompt, contexto_pobre)`.
4. Llamar `responder(prompt, contexto_pobre)` → texto.
5. Insertar en `consultas`: `{proyecto_id, usuario_telegram, mensaje_original, respuesta_generada, chunks_usados: [ids], score_maximo, timestamp}`.
6. Retornar response.

---

### GET /logs

**Query params** (todos opcionales):
- `proyecto_id: int`
- `limit: int = 50`
- `offset: int = 0`

**Response 200**:
```json
[
  {
    "id": 1,
    "proyecto_id": 1,
    "usuario_telegram": "operario_garcia",
    "mensaje_original": "...",
    "respuesta_generada": "...",
    "chunks_usados": [12, 15],
    "score_maximo": 0.31,
    "timestamp": "2026-05-17T10:00:00"
  }
]
```

---

## Criterios de aceptación
- [ ] `POST /query` con mensaje válido → respuesta 200 con `respuesta` no vacía.
- [ ] `POST /query` inserta correctamente en `consultas` (verificable consultando `/logs`).
- [ ] `score_maximo` refleja el score del chunk más relevante (el de menor distancia coseno).
- [ ] `tiene_imagen` y `ruta_imagen` correctos cuando hay chunks de planos.
- [ ] `GET /logs` filtra por `proyecto_id` si se pasa.
- [ ] Error de MiniMax → 500 con `{"error": "mensaje legible"}`, sin stack trace.
- [ ] `pytest tests/test_query.py` pasa (OpenAI, Supabase y MiniMax mockeados).
- [ ] `pytest tests/test_responder.py` pasa (MiniMax mockeado).

## Cómo probar
```bash
pytest tests/test_query.py tests/test_responder.py -v

# Test de integración real (consume APIs — solo para verificar end-to-end):
uvicorn src.api.main:app --reload --port 8000

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 1, "mensaje": "protocolo de seguridad para trabajo en altura", "usuario_telegram": "test_user"}'

curl "http://localhost:8000/logs?proyecto_id=1&limit=5"
```

## Qué NO hacer
- Sin streaming de respuesta — respuesta completa en un solo JSON.
- Sin historial de conversación multi-turno — cada query es independiente.
- Sin caché de respuestas — fuera del MVP.
- Sin endpoint DELETE o PUT sobre consultas.
- El modelo MiniMax a usar es `"MiniMax-Text-01"` — no cambiar sin consultar.

---

## Test de Fase 1 completo (smoke test end-to-end)

Al terminar TAREA 007, el colaborador debe verificar el pipeline completo:

1. Subir un PDF de prueba: `POST /ingest` con un PDF de texto.
2. Hacer una consulta: `POST /query` con una pregunta relacionada al contenido del PDF.
3. Verificar que `/logs` registró la consulta con `score_maximo` razonable (< 0.8 si el contenido es relevante).
4. Incluir el resultado en el resumen de entrega.

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_007_resumen.md` y pushearlo. **Incluir el resultado del smoke test end-to-end.**

```markdown
# Resumen TAREA 007

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Qué quedó fuera de scope
## Resultado del smoke test end-to-end
- PDF subido: [nombre]
- Query realizada: [texto]
- Respuesta obtenida: [primeras 200 chars]
- Score máximo: [valor]
- Log guardado: [sí/no]
## Cómo probarlo
```

**Sin este archivo con el smoke test, la Fase 1 no se considera cerrada.**
