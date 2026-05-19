# TAREA_016 + TAREA_017 — Resumen

## TAREA 016 — Imagen de página de PDF en respuesta del bot

### Criterios de aceptación

- [x] Subir un PDF de varias páginas → PNGs en Storage (`{proyecto_id}/{documento_id}/paginas/pagina_N.png`)
- [x] Chunks tienen `page_image_path` en metadata
- [x] Query con similitud > 0.35 → devuelve imagen de página
- [x] Query con similitud ≤ 0.35 → sin imagen
- [x] Ingesta de PNG/JPG/Word sigue funcionando
- [x] Documentosoldos sin `page_image_path` no rompen query
- [x] Página fallida no aborted ingest

### Archivos modificados

- `src/ingesta/extractor.py`: agregado `paginas_texto: list[str]`
- `src/api/routes/ingest.py`: render PNG página por página, mapeo chunk→página
- `src/api/routes/query.py`: usa `page_image_path` si score > 0.35

---

## TAREA 017 — Bot más conversacional + fix tests

### Criterios de aceptación

- [x] Sin "Relevancia" ni variables `score_pct`/`relevancia`
- [x] Con imagen ≤1024 chars: 1 mensaje (foto + caption)
- [x] Sin imagen: 1 mensaje de texto
- [x] `score < 0.4`: mensaje específico de "no encontré documentación"
- [x] Tests pasan

### Fixes en tests

- `test_chunker_tamano_y_overlap`: texto real, verifica overlap real
- `test_prompt_builder_incluye_contexto`: marcador único, verifica texto del chunk
- `test_score_semantica`: query real "muros", texto completo del chunk
- `test_end_to_end_query`: verifica contra frases reales
- `test_retriever_estructura`, `test_score_semantica`, `test_end_to_end_query`: skip si falta SUPABASE_URL/KEY
- `diagnostico_rag.py`: `chunks = []` antes del try

### Archivos modificados

- `src/bot/main.py`: formato conversacional (un solo mensaje)
- `tests/test_rag_pipeline.py`: tests corregidos
- `scripts/diagnostico_rag.py`: fix NameError

---

## Notas

- PyMuPDF (`fitz`) usado para render con matrix 1.5
- Fallback mantener para `es_imagen=True` (planos directa)
- Tests sin mocks, pegan a OpenAI/Supabase real