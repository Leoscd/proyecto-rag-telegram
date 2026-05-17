# Resumen TAREA 006

## Qué se implementó
- `src/rag/retriever.py` con función `recuperar()` — búsqueda coseno top_k
- `src/rag/prompt_builder.py` con función `construir_prompt()` para MiniMax
- Tests en `tests/test_retriever.py` y `tests/test_prompt_builder.py`

## Decisiones tomadas
- Distancia coseno calculada en Python (workaround por limitaciones de Supabase)
- Score Umbral hardcodeado en 1.2
- Prompt incluye instrucción anti-alucinación exacta

## Problemas encontrados
- Supabase postgREST no permite SQL raw directamente (workaround implementado)

## Qué quedó fuera de scope
- Reranking / MMR
- Búsqueda híbrida BM25 + vector
- SQL directo (usamos cálculo en Python)

## Cómo probarlo
```bash
pytest tests/test_retriever.py tests/test_prompt_builder.py -v
python3 -c "
from src.rag.prompt_builder import construir_prompt
from src.rag.retriever import ChunkRecuperado
chunks = [ChunkRecuperado(1, 'texto', 0.3, {'nombre_documento':'manual','sector':'norte','tipo':'manual'})]
prompt, pobre = construir_prompt('query?', chunks)
print('contexto pobre:', pobre)
"
```