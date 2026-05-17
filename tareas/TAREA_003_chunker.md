# TAREA 003 — Chunker: dividir texto en chunks con metadata

- Fecha asignada: 2026-05-17
- Fase del MVP: 1 — Core RAG
- Estimación: ≤ 1 día
- Depende de: TAREA 002

## Objetivo
Implementar el chunker que toma el texto extraído de un documento y lo divide en fragmentos de 500 tokens con 50 tokens de overlap, propagando la metadata necesaria para el retriever y el adjunto de imágenes.

## Archivos a crear / modificar
- `src/ingesta/chunker.py` — lógica de chunking
- `tests/test_chunker.py` — tests unitarios

## Contrato

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Chunk:
    texto: str
    tokens: int
    indice: int          # posición del chunk en el documento (0-based)
    metadata: dict       # ver estructura abajo

def chunkear(
    texto: str,
    metadata_base: dict,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """
    Divide texto en chunks de max_tokens con overlap_tokens de solape.
    - Usa tiktoken con encoding "cl100k_base" (compatible con text-embedding-3-large).
    - El overlap son los últimos `overlap_tokens` del chunk anterior.
    - Si texto == "" o len(tokens) == 0: retornar lista vacía.
    - Si texto cabe en un solo chunk: retornar lista con un elemento.
    - metadata_base se copia en cada chunk y se le agrega chunk_index.
    """
```

### Estructura de `metadata_base` (la recibe, no la construye el chunker)
```python
{
    "documento_id": int,
    "proyecto_id": int,
    "tipo": str,          # "manual" | "especificacion" | "plano" | "protocolo" | "cronograma"
    "sector": str | None,
    "nombre_documento": str,
    "es_imagen": bool,    # True si el documento es un plano/imagen
    "ruta_archivo": str,  # ruta en Supabase Storage (para adjuntar imagen)
}
```

Cada `Chunk.metadata` = `{**metadata_base, "chunk_index": indice}`.

### Reglas
- Medir todo en **tokens** (tiktoken), nunca en caracteres.
- El overlap no puede causar chunks de 0 tokens (si overlap >= max_tokens, lanzar ValueError).
- No cortar palabras a mitad: si el corte cae a mitad de una palabra, retroceder al espacio anterior. (Esto es automático si se trabaja con tokens de tiktoken y se decodifica.)
- Texto muy corto (< max_tokens): un solo chunk, sin overlap.
- El campo `tokens` de cada Chunk refleja los tokens reales de ese chunk (no siempre max_tokens).

## Criterios de aceptación
- [ ] Chunks de texto largo tienen exactamente `max_tokens` tokens (último puede ser menor).
- [ ] El inicio del chunk N+1 comparte los últimos `overlap_tokens` del chunk N.
- [ ] `texto=""` → `[]` (lista vacía).
- [ ] Texto corto (< 500 tokens) → lista con 1 chunk, tokens correcto.
- [ ] `metadata` de cada chunk contiene todos los campos de `metadata_base` + `chunk_index`.
- [ ] `pytest tests/test_chunker.py` pasa, incluyendo casos edge.

## Cómo probar
```bash
pytest tests/test_chunker.py -v
# Verificación rápida:
python -c "
from src.ingesta.chunker import chunkear
texto = 'palabra ' * 1000
chunks = chunkear(texto, {'documento_id':1,'proyecto_id':1,'tipo':'manual','sector':None,'nombre_documento':'test','es_imagen':False,'ruta_archivo':''})
print(f'{len(chunks)} chunks, primer chunk tokens: {chunks[0].tokens}, overlap ok: {chunks[1].texto[:50] == chunks[0].texto[-50:] if len(chunks)>1 else True}')
"
```

## Qué NO hacer
- Sin chunking semántico ni por párrafo — solo ventana deslizante de tokens.
- Sin dependencias extra (spacy, nltk, langchain) — solo tiktoken.
- Sin lógica de guardado en DB — eso es TAREA 004.

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_003_resumen.md` y pushearlo al repo:

```markdown
# Resumen TAREA 003

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Qué quedó fuera de scope
## Cómo probarlo
```

**Sin este archivo, la tarea no se considera entregada.**
