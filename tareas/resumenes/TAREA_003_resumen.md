# Resumen TAREA 003

## Qué se implementó
- `src/ingesta/chunker.py` con función `chunkear()` que divide texto en chunks de 500 tokens con 50 de overlap
- Usa tiktoken con encoding `cl100k_base` (compatible con text-embedding-3-large)
- Tests en `tests/test_chunker.py`

## Decisiones tomadas
- Usé tiktoken directo (no spacy/nltk) para keep it simple
- Chunking con ventana deslizante de tokens, no semántico
- Si último chunk es muy pequeño (< 25%), merge con anterior
- El overlap opera en tokens, no caracteres

## Problemas encontrados
- Syntax error por paréntesis extra — corregido

## Qué quedó fuera de scope
- Chunking semántico por párrafos — solo tokens
- Guardado en DB — TAREA 004

## Cómo probarlo
```bash
pytest tests/test_chunker.py -v
python3 -c "
from src.ingesta.chunker import chunkear
texto = 'palabra ' * 1000
chunks = chunkear(texto, {'documento_id':1,'proyecto_id':1,'tipo':'manual','sector':None,'nombre_documento':'test','es_imagen':False,'ruta_archivo':''})
print(f'{len(chunks)} chunks')
"
```