# Resumen TAREA 004

## Qué se implementó
- `src/ingesta/embedder.py` con función `embeder_y_guardar()` 
- OpenAI `text-embedding-3-large` (3072 dims)
- Guardado en lotes en Supabase tabla `chunks`
- Retry en rate limit (20s espera)
- Tests en `tests/test_embedder.py`

## Decisiones tomadas
- Proceso en lotes de 100 (default)
- Retry solo una vez en rate limit
- Uso el cliente OpenAI directo (no langchain)
- Logueo con print el progreso

## Problemas encontrados
- Ninguno significativo

## Qué quedó fuera de scope
- Procesamiento paralelo/async
- Caché de embeddings
- Retry infinito (solo 1)

## Cómo probarlo
```bash
pytest tests/test_embedder.py -v
# Smoke real (consume créditos):
# python3 -c "from src.ingesta import embeder_y_guardar, chunkear; ..."
```