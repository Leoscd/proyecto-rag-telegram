# TAREA 006 — Retriever (búsqueda vectorial) + Prompt Builder

- Fecha asignada: 2026-05-17
- Fase del MVP: 1 — Core RAG
- Estimación: ≤ 1 día
- Depende de: TAREA 005

## Objetivo
Implementar el retriever que busca los 5 chunks más relevantes en Supabase usando distancia coseno, y el prompt builder que construye el contexto para MiniMax con instrucción anti-alucinación explícita.

## Archivos a crear
- `src/rag/retriever.py`
- `src/rag/prompt_builder.py`
- `src/rag/__init__.py` — vacío
- `tests/test_retriever.py`
- `tests/test_prompt_builder.py`

## Contrato

### retriever.py

```python
from dataclasses import dataclass

@dataclass
class ChunkRecuperado:
    chunk_id: int
    texto: str
    score: float          # distancia coseno (0=idéntico, 2=opuesto; menor = más similar)
    metadata: dict        # metadata completa del chunk (incluye es_imagen, ruta_archivo, sector)

def recuperar(
    query_embedding: list[float],   # vector de 3072 floats
    proyecto_id: int,
    top_k: int = 5,
) -> list[ChunkRecuperado]:
    """
    Busca los top_k chunks más similares usando exact scan coseno.
    Filtra por proyecto_id (no mezclar documentos de proyectos distintos).
    Retorna lista ordenada por score ascendente (menor distancia = más relevante).
    """
```

### Query SQL de búsqueda (exact scan, sin índice ANN)
```sql
SELECT id, texto, metadata,
       embedding <=> '[...query_vector...]'::vector AS score
FROM chunks
WHERE proyecto_id = {proyecto_id}
ORDER BY score ASC
LIMIT {top_k};
```

El vector de query se pasa como string en formato pgvector: `'[0.1, 0.2, ...]'`.

### prompt_builder.py

```python
def construir_prompt(
    query: str,
    chunks: list[ChunkRecuperado],
    score_umbral: float = 1.2,  # distancia coseno: > 1.2 → contexto pobre
) -> tuple[str, bool]:
    """
    Construye el prompt para MiniMax.
    Retorna (prompt_str, contexto_pobre).
    contexto_pobre=True si el mejor score > score_umbral.
    """
```

### Estructura del prompt generado
```
Sos un asistente técnico de obra. Respondé ÚNICAMENTE usando la información
del contexto. Si la información no está en el contexto, decí exactamente:
"No encontré información sobre esto en los documentos disponibles."
No inventes datos, medidas, procedimientos ni normativas.

CONTEXTO:
--- Documento: {nombre_documento} | Sector: {sector} | Tipo: {tipo} ---
{texto del chunk 1}

--- Documento: {nombre_documento} | Sector: {sector} | Tipo: {tipo} ---
{texto del chunk 2}
[... hasta top_k chunks ...]

PREGUNTA: {query}

RESPUESTA:
```

Si `contexto_pobre=True`, agregar al final del contexto:
```
ADVERTENCIA: Los documentos disponibles pueden no contener información específica sobre esta consulta.
```

## Criterios de aceptación
- [ ] `recuperar(embedding, proyecto_id)` ejecuta la query con `<=>` y filtra por `proyecto_id`.
- [ ] Retorna exactamente `top_k` chunks (o menos si hay menos en la tabla).
- [ ] Resultados ordenados por score ascendente.
- [ ] `construir_prompt` incluye instrucción anti-alucinación textual exacta.
- [ ] `contexto_pobre=True` cuando mejor score > 1.2.
- [ ] `pytest tests/test_retriever.py` pasa (Supabase mockeado).
- [ ] `pytest tests/test_prompt_builder.py` pasa (sin mocks necesarios).

## Cómo probar
```bash
pytest tests/test_retriever.py tests/test_prompt_builder.py -v

# Verificación manual del prompt:
python -c "
from src.rag.prompt_builder import construir_prompt
from src.rag.retriever import ChunkRecuperado
chunks = [ChunkRecuperado(1, 'texto de prueba', 0.3, {'nombre_documento':'manual','sector':'norte','tipo':'manual'})]
prompt, pobre = construir_prompt('como se hace el revoque exterior?', chunks)
print(prompt)
print('contexto pobre:', pobre)
"
```

## Qué NO hacer
- Sin reranking, MMR ni post-procesamiento semántico — fuera del MVP.
- Sin búsqueda híbrida (BM25 + vector) — fuera del MVP.
- Sin cambiar el score_umbral desde configuración todavía — hardcodeado con default está bien.
- No crear el índice vectorial (ya se decidió exact scan para MVP con 3072 dims).

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_006_resumen.md` y pushearlo:

```markdown
# Resumen TAREA 006

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Qué quedó fuera de scope
## Cómo probarlo
```

**Sin este archivo, la tarea no se considera entregada.**
