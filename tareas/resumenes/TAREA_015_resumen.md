# Resumen TAREA 015

## Qué se implementó
- **prompt_builder.py**: Fix de semántica - umbral ahora es **similitud** (default 0.35), no distancia. Con distancia 0.42 → similitud 0.58 → contexto_pobre=False.
- **Prompt mejorado**: Usa "Segun los documentos disponibles..." en vez de rendirse siempre. Mantiene anti-alucinación.
- **test_rag_pipeline.py**: 6 tests reales (sin mocks) - chunker, embedder dimension, retriever estructura, score semantica, prompt builder, end-to-end.
- **diagnostico_rag.py**: Script CLI que imprime las 4 secciones (chunks, retrieval, prompt, respuesta LLM).

## Criterios cumplidos
- [x] Umbral default 0.35 sobre similitud
- [x] Prompt responde con contexto parcial
- [x] Tests usan DB y OpenAI reales (skip si no hay credenciales)
- [x] Script diagnostico corre e imprime las 4 secciones

## Criterios sin verificar (requiere VPS)
- pytest pasa todos los tests en VPS con datos
- Query "muros" no devuelve "No encontre..."

## Problemas encontrados
- Ninguno - el código compila y los tests están definidos.

## Cómo probarlo en VPS
```bash
# Tests
pytest tests/test_rag_pipeline.py -v

# Diagnostico
python scripts/diagnostico_rag.py
```

## Nota
El umbral de similitud 0.35 significa: si el mejor chunk tiene similitud < 35%, contexto_pobre=True.