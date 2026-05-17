# TAREA 004 — Embedder: generar embeddings y guardar chunks en Supabase

- Fecha asignada: 2026-05-17
- Fase del MVP: 1 — Core RAG
- Estimación: ≤ 1 día
- Depende de: TAREA 003

## Objetivo
Tomar la lista de chunks del chunker, generar embeddings con OpenAI `text-embedding-3-large` (3072 dims) en lotes, y persistirlos en la tabla `chunks` de Supabase junto con su metadata.

## Archivos a crear
- `src/ingesta/embedder.py`
- `tests/test_embedder.py` (con mocks — no llamar la API real en tests)

## Contrato

```python
def embeder_y_guardar(
    chunks: list[Chunk],           # output de TAREA 003
    documento_id: int,
    proyecto_id: int,
    batch_size: int = 100,
) -> int:
    """
    Genera embeddings en lotes y los guarda en Supabase.
    Retorna la cantidad de chunks guardados.
    Lanza RuntimeError si OpenAI o Supabase fallan tras reintentos.
    """
```

### Llamada a OpenAI
```python
response = openai_client.embeddings.create(
    model="text-embedding-3-large",
    input=[chunk.texto for chunk in batch],  # lista de strings
)
# response.data[i].embedding → list[float] de 3072 elementos
```

### Fila a insertar en `chunks`
```python
{
    "documento_id": documento_id,
    "proyecto_id": proyecto_id,
    "texto": chunk.texto,
    "embedding": embedding_vector,   # list[float] de 3072
    "metadata": chunk.metadata,      # dict completo del chunk
}
```

### Manejo de errores y rate limit
- Si OpenAI devuelve `RateLimitError`: esperar 20 segundos y reintentar **una vez**. Si falla de nuevo, lanzar `RuntimeError`.
- Si Supabase falla en el insert: lanzar `RuntimeError` con mensaje claro.
- Procesar en lotes de `batch_size` (default 100). Un lote que falla no debe silenciarse.
- Loguear con `print` el progreso: `"Procesando lote 1/5 ({n} chunks)..."`.

## Criterios de aceptación
- [ ] Llama a OpenAI con `model="text-embedding-3-large"` — verificable en los mocks del test.
- [ ] Procesa en lotes de `batch_size`, no chunk por chunk.
- [ ] Inserta correctamente en `chunks` con todos los campos del esquema.
- [ ] `RateLimitError` → espera 20s y reintenta (mockear el sleep en tests).
- [ ] Retorna el número exacto de chunks guardados.
- [ ] `pytest tests/test_embedder.py` pasa (todo mockeado, sin llamadas reales a API).

## Cómo probar
```bash
pytest tests/test_embedder.py -v
# Smoke test real (consume créditos OpenAI — solo para verificar integración):
# python scripts/smoke_embedder.py  (crearlo si querés, no es obligatorio)
```

## Qué NO hacer
- Sin retry infinito — máximo 1 reintento por lote.
- Sin procesamiento paralelo/async por ahora — secuencial está bien para el MVP.
- Sin caché de embeddings — fuera del MVP.
- No llamar la API real en `pytest`.

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_004_resumen.md` y pushearlo:

```markdown
# Resumen TAREA 004

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Qué quedó fuera de scope
## Cómo probarlo
```

**Sin este archivo, la tarea no se considera entregada.**
