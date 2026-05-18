# TAREA 017 — Bot más conversacional + fix de tests de TAREA_015

- Fecha asignada: 2026-05-18
- Fase del MVP: 2
- Estimación: ≤1 día
- Depende de: TAREA_015 (tests y diagnóstico RAG)

## Objetivo
Que el bot de Telegram responda al operario con un solo mensaje fluido (foto+caption cuando hay imagen, texto solo cuando no), sin el mensaje separado de "Relevancia: X%"; y que los tests de `tests/test_rag_pipeline.py` verifiquen realmente lo que dicen verificar y pasen en el VPS con datos reales.

## Contexto mínimo necesario
- El bot hoy manda 2-3 mensajes: "Buscando...", la respuesta, "Relevancia X%" y la foto aparte. El operario en obra necesita una respuesta directa, no metadatos de scoring.
- Frases reales de "sin información" en el código (NO las cambies, solo úsalas como referencia en los tests):
  - en `src/rag/query.py`: `"No encontré documentos relevantes para esta consulta."`
  - en `src/rag/prompt_builder.py`: `"No tengo informacion sobre esto en los documentos disponibles."`
- Esta tarea NO toca el pipeline RAG ni el prompt: solo formato de mensajes del bot, los tests y un fix menor en el script de diagnóstico.
- Ver briefing: flujo RAG y bot de Telegram (Fase 2).

## Archivos a crear / modificar
- `src/bot/main.py` — modificar SOLO la función `handle_query`: eliminar mensaje de relevancia; unificar foto+texto en un único mensaje cuando hay imagen; texto solo cuando no hay; mensaje directo cuando `score < 0.4`.
- `tests/test_rag_pipeline.py` — corregir los 5 tests defectuosos descritos abajo.
- `scripts/diagnostico_rag.py` — fix menor: inicializar `chunks = []` antes del `try` de retrieval.

## Contrato (inputs / outputs)

### PARTE A — `src/bot/main.py` :: `handle_query`
Comportamiento esperado tras el cambio (la firma de la función NO cambia):

1. Mantener el indicador `await update.message.reply_text("🔎 Buscando en los documentos...")` tal como está.
2. Tras obtener `data` de la API (`respuesta`, `score_maximo`, `tiene_imagen`, `ruta_imagen`) y descargar `img_bytes` igual que hoy:
   - Si `score < 0.4`: enviar UN solo mensaje de texto exactamente:
     `"⚠️ No encontré documentación sobre esto en los documentos cargados. Intentá reformular la pregunta."`
     y `return` (no enviar imagen ni nada más).
   - Si hay `img_bytes`: enviar UN solo mensaje con `await update.message.reply_photo(photo=img_bytes, caption=respuesta)`.
     - Telegram limita el caption a ~1024 caracteres. Si `len(respuesta) > 1024`, enviar primero `await update.message.reply_text(respuesta)` y luego la foto sin caption (`reply_photo(photo=img_bytes)`). Es el único caso con 2 mensajes y es aceptable.
   - Si NO hay `img_bytes`: enviar UN solo mensaje `await update.message.reply_text(respuesta)`.
3. Eliminar por completo las variables/strings `score_pct` y `relevancia` y los `reply_text(relevancia)`.
4. Mantener intactos los `except` (TimeoutException / Exception) y los handlers de error HTTP existentes.

### PARTE B — `tests/test_rag_pipeline.py`

1. `test_chunker_tamano_y_overlap`:
   - Reemplazar el texto por: `texto = " ".join(["construccion obra revoque mortero mamposteria hierro cemento arena"] * 60)`.
   - Mantener el assert de `len(chunks) >= 2` y el de rango de tokens.
   - Agregar un assert real de overlap: las últimas N palabras del texto de `chunks[0]` deben aparecer al inicio de `chunks[1]`. Verificar que el solapamiento medido en tokens sea ≈ 50 con tolerancia ±15 (rango aceptado [35, 65]). Medir tokens con el mismo tokenizador que usa `chunker` (importar de `src/ingesta/chunker.py` lo que ya use; no introducir dependencia nueva). Si chunker expone una función de conteo de tokens, usarla; si no, contar el solapamiento de palabras consecutivas entre fin de chunk0 e inicio de chunk1 y exigir ≈50 ±15.

2. `test_prompt_builder_incluye_contexto`:
   - Usar un texto de chunk único e inconfundible, p. ej. `texto="XJ7QZ_marcador_unico_de_chunk_para_test"`.
   - Cambiar el assert a `assert "XJ7QZ_marcador_unico_de_chunk_para_test" in prompt` (debe pasar por el TEXTO del chunk, no por el `nombre_documento`).
   - Mantener el resto de asserts (query en prompt, `contexto_pobre` para similitud alta/baja/vacía).

3. `test_score_semantica`:
   - Cambiar la recuperación inicial: usar embedding real de la query `"muros"` (igual que `test_retriever_estructura`) en lugar de `[0.1]*3072`.
   - Tomar el texto COMPLETO del top chunk recuperado (sin `[:100]`).
   - Re-embeddear ese texto completo y recuperar `top_k=1`.
   - `similitud = 1.0 - recovered[0].score`; assert `0 <= similitud <= 1` y assert `similitud > 0.9`.

4. `test_end_to_end_query`:
   - Eliminar la comparación contra `"No encontré información sobre esto en los documentos disponibles."` (esa frase no existe).
   - Cuando hay datos (`score_maximo > 0`), assert que `data["respuesta"]` NO sea ninguna de las dos frases reales:
     - `"No encontré documentos relevantes para esta consulta."`
     - `"No tengo informacion sobre esto en los documentos disponibles."`

5. Skip gates Supabase: en `test_retriever_estructura`, `test_score_semantica` y `test_end_to_end_query`, además de `OPENAI_API_KEY`, el `skipif` debe skipear si falta `SUPABASE_URL` **o** `SUPABASE_KEY`. (No tocar `test_embedder_dimension`, que no usa Supabase.)

### Fix menor — `scripts/diagnostico_rag.py`
- Inicializar `chunks = []` ANTES del `try` que hace el retrieval, de modo que la sección PROMPT no lance `NameError` si el retrieval falla.

## Criterios de aceptación
- [ ] `src/bot/main.py`: no existe ningún string "Relevancia" ni variable `score_pct`/`relevancia` en `handle_query`.
- [ ] Con imagen disponible y respuesta ≤1024 chars: el bot envía exactamente 1 mensaje (foto con caption = respuesta).
- [ ] Sin imagen: el bot envía exactamente 1 mensaje de texto con la respuesta.
- [ ] `score < 0.4`: el bot envía exactamente el texto `"⚠️ No encontré documentación sobre esto en los documentos cargados. Intentá reformular la pregunta."` y nada más.
- [ ] Se mantiene "🔎 Buscando en los documentos..." y los except de timeout/error.
- [ ] `pytest tests/test_rag_pipeline.py -v` pasa en el VPS con datos reales (proyecto_id=1 con chunks).
- [ ] `test_chunker_tamano_y_overlap` falla si el overlap real no está en [35,65] tokens (verificado bajando overlap a mano y viendo que rompe).
- [ ] `test_prompt_builder_incluye_contexto` falla si se quita el texto del chunk del prompt (no pasa por `nombre_documento`).
- [ ] `test_score_semantica` usa query real "muros" y texto completo del chunk; exige similitud > 0.9.
- [ ] `test_end_to_end_query` no referencia la frase inexistente y chequea contra las 2 frases reales.
- [ ] Los 3 tests Supabase skipean (no fallan) si falta `SUPABASE_URL` o `SUPABASE_KEY`.
- [ ] `python scripts/diagnostico_rag.py` no lanza `NameError` aunque el retrieval falle.
- [ ] No se modificó ningún archivo fuera de los 3 listados.

## Cómo probar
1. Tests (en el VPS, con `.env` cargado y datos reales en proyecto_id=1):
   `pytest tests/test_rag_pipeline.py -v`
   Todos deben pasar; ninguno debe quedar en FAIL ni en ERROR.
2. Verificar gate de skip: correr `pytest tests/test_rag_pipeline.py -v` con `SUPABASE_KEY` desactivada → los 3 tests Supabase deben aparecer SKIPPED, no FAILED.
3. Diagnóstico: `python scripts/diagnostico_rag.py` y, además, forzar un fallo de retrieval (p. ej. proyecto inexistente o cortando la conexión) → debe imprimir el error de retrieval pero NO un `NameError` en la sección PROMPT.
4. Bot (manual, en VPS con bot corriendo): hacer una pregunta con respuesta documentada y con imagen asociada → debe llegar UNA sola burbuja con foto y texto debajo. Hacer una pregunta sin documentación → debe llegar solo el mensaje de "No encontré documentación... Intentá reformular".

## Qué NO hacer
- NO modificar `prompt_builder.py`, `query.py`, `retriever.py`, `responder.py`, `embedder.py`, `chunker.py`, `extractor.py`, dashboard ni schemas.
- NO cambiar las frases de "sin información" del código (solo se usan como referencia en los tests).
- NO tocar otras funciones de `main.py` (`start`, `ayuda`, `proyecto_command`, `main`).
- NO cambiar el tono ni el prompt del bot (ya quedó en TAREA_015).
- NO agregar dependencias nuevas (sin tiktoken nuevo si el chunker no lo usa ya; reusar lo que haya).
- NO mockear OpenAI/Supabase en los tests: se prueban de verdad y por eso tienen skip gates.
- NO refactorizar ni "mejorar de paso" el resto del archivo de tests.

## Notas para revisión
- Edge case caption >1024 chars: confirmar que es el único caso con 2 mensajes y que está manejado.
- Confirmar que `test_score_semantica` NO usa `[:100]` ni vector basura, y que el umbral 0.9 es realista con re-embedding del texto completo.
- Confirmar que el assert de overlap rompe de verdad si se altera el overlap (que no sea un assert decorativo).
- Revisar que los skip gates usen `os.environ.get` para `SUPABASE_URL` y `SUPABASE_KEY` (sin hardcodear secrets).
- Recursos VPS: los tests reales pegan a OpenAI/Supabase; correrlos una vez, no en loop. El bot sigue en long polling, sin abrir puertos públicos.
- Verificar que no quedó código muerto (variables `relevancia`/`score_pct`) tras el cambio en `handle_query`.
