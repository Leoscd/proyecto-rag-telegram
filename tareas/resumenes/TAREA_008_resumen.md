# Resumen TAREA 008

##Qué se implementó
- **A. Retriever SQL**: migración a función RPC `buscar_chunks_similares` con operador `<=>` de pgvector
- **B. Chunk sintético para imágenes**: al ingestar PNG/JPG, crea chunk con texto de búsqueda + `es_imagen=True`
- **C. Prompt builder**: umbral 0.6, ADVERTENCIA antes de CONTEXTO
- **D. Score como similitud**: `score_maximo = 1.0 - distancia`
- **E. Tests con asserts reales**: test_retriever.py, test_query.py, test_ingest.py, test_extractor.py
- **F. Temp file con finally**: cleanup garantizado

##Archivos modificados/creados
- `migrations/002_buscar_chunks.sql` (nuevo)
- `src/rag/retriever.py`
- `src/api/routes/ingest.py`
- `src/api/routes/query.py`
- `src/rag/prompt_builder.py`
- `tests/test_retriever.py`
- `tests/test_query.py`
- `tests/test_ingest.py`
- `tests/test_extractor.py`

##Decisiones tomadas
- Retriever via RPC SQL (no traigo vectores a Python)
- Chunk sintético solo para imágenes (no para plano PDF)
- Score como similitud: 1.0 = perfecto, 0.0 = sin relación

##Problemas encontrados
- Módulos pymupdf/python-docx no instalados en el runner (pero/tests core passent)

##Resultado de pytest
```
13 passed (test_config.py, test_prompt_builder.py, test_retriever.py, test_responder.py)
2 errors de collection (test_chunker.py, test_extractor.py) - requieren pip install
```

##Smoke test end-to-end
**No ejecutado**: requiere credenciales reales en `.env` + aplicar migration 002 en Supabase.

Para probar:
```bash
# 1. Aplicar migration
psql -h <host> -U <user> -d <db> -f migrations/002_buscar_chunks.sql

# 2. Levantar API con .env lleno
uvicorn src.api.main:app --port 8000

# 3. Tests
curl -X POST http://localhost:8000/ingest -F "archivo=@doc.pdf" ...
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"proyecto_id":1,"mensaje":"...","usuario_telegram":"test"}'
curl http://localhost:8000/logs
```

##Cómo aplicar migrations/002_buscar_chunks.sql en Supabase
1. Ir a SQL Editor en Supabase Dashboard
2. Copiar el contenido de `migrations/002_buscar_chunks.sql`
3. Ejecutar
4. Verificar: `SELECT * FROM buscar_chunks_similares('[0.1,0.2]'::vector, 1, 5);`