# TAREA 015 — Testing profundo y diagnóstico del pipeline RAG

- Fecha asignada: 2026-05-17
- Fase del MVP: 4 (pulido para demo)
- Estimación: ≤1 día
- Depende de: TAREA_006 (retriever/prompt), TAREA_007 (query/responder/logs), TAREA_013 (demo data), TAREA_014 (deploy VPS)

## Objetivo
Que el pipeline RAG responda con la información que tiene en vez de rendirse (fix de umbral y prompt), y que exista una batería de tests reales (sin mocks) más un script de diagnóstico paso a paso, ambos ejecutables en el VPS donde ya hay datos cargados (proyecto_id=1, documento "muros_paz.pdf", 3 chunks).

## Contexto mínimo necesario
- Briefing: secciones "Flujo RAG detallado" y "Prioridad de desarrollo / Fase 4".
- El LLM de respuesta ya es OpenAI `gpt-4o-mini` (ver `src/rag/responder.py`), NO MiniMax. No cambiar eso.
- **Semántica de score (crítico, leer dos veces):**
  - `retriever.recuperar()` retorna `ChunkRecuperado.score` = **distancia coseno** (menor = más similar).
  - `routes/query.py` calcula `score_maximo = 1.0 - distancia` = **similitud** (mayor = más similar, rango ~[0,1]).
  - El "58%" observado en producción es una **similitud de 0.58** (distancia 0.42).
  - En `prompt_builder.construir_prompt` la condición actual `chunks[0].score > score_umbral` con `score_umbral=0.6` compara contra la **distancia**. Bajar ese número a 0.35 sobre la distancia haría el sistema MÁS restrictivo (exactamente lo contrario de lo que se quiere). El fix correcto es trabajar en términos de **similitud** y marcar contexto pobre cuando la similitud del mejor chunk es **menor** que 0.35.
- Datos de prueba en el VPS: proyecto_id=1 tiene el documento "muros_paz.pdf" con 3 chunks. La query "muros" debe recuperar contexto relevante.

## Archivos a crear / modificar
- `src/rag/prompt_builder.py` — cambiar la lógica del umbral a similitud con default 0.35; mejorar el tono del prompt. (modificar)
- `tests/test_rag_pipeline.py` — tests reales del pipeline contra Supabase y OpenAI reales. (crear)
- `scripts/diagnostico_rag.py` — script CLI que imprime el pipeline completo paso a paso. (crear)
- `tareas/resumenes/TAREA_015_resumen.md` — resumen de entrega. (crear)

NO modificar: `retriever.py`, `embedder.py`, `chunker.py`, `responder.py`, rutas de API, bot, dashboard, esquema de DB.

## Contrato (inputs / outputs)

### Parte 1 — `src/rag/prompt_builder.py`
Mantener la firma pública pero cambiar la semántica del umbral a similitud:

```python
def construir_prompt(
    query: str,
    chunks: list[ChunkRecuperado],
    similitud_umbral: float = 0.35,
) -> tuple[str, bool]:
    ...
```

- Convertir la distancia del mejor chunk a similitud: `similitud_top = 1.0 - chunks[0].score` (si hay chunks).
- `contexto_pobre = (not chunks) or (similitud_top < similitud_umbral)`.
- El parámetro **debe llamarse `similitud_umbral`** y su default es `0.35`. (Si se prefiere conservar el nombre `score_umbral` por compatibilidad de llamadas, está permitido renombrar internamente pero el default debe pasar a 0.35 y la comparación debe ser sobre similitud, no sobre distancia. `query.py` llama `construir_prompt(request.mensaje, chunks)` por posición, así que el nombre del 3er parámetro no rompe la llamada — pero la lógica sí debe quedar como se describe.)
- Prompt mejorado, requisitos concretos:
  - Tono de asistente técnico de obra que **ayuda con lo que tiene**, en español rioplatense neutro.
  - Debe **intentar responder usando el contexto disponible** aunque sea parcial, en vez de rendirse.
  - Si el contexto es parcial o no cubre todo, que responda con lo que sí está y lo aclare con una fórmula tipo "Según los documentos disponibles, ..." y mencione qué parte no figura, en vez de devolver solo "No encontré información...".
  - Solo debe decir que no hay información cuando el contexto es **realmente** vacío o no relacionado (caso `contexto_pobre` sin nada útil).
  - Mantener la regla anti-alucinación: no inventar medidas, procedimientos ni normativas que no estén en el contexto.
  - El prompt debe seguir incluyendo, textualmente: el texto de cada chunk recuperado y la `query` del usuario.

### Parte 2 — `tests/test_rag_pipeline.py` (pytest, sin mocks de DB ni OpenAI)
Usa variables de entorno reales vía `src/config.py` / `src/db.py`. Si faltan credenciales o no hay datos en proyecto_id=1, los tests pueden hacer `pytest.skip(...)` con mensaje claro (no fallar silenciosamente). Tests requeridos:

- `test_chunker_tamano_y_overlap`: generar un texto de ~1000 tokens; `chunkear()` con defaults (500/50) debe producir ≥2 chunks; cada chunk (salvo posible merge del último) con `tokens` en rango [400, 520]; verificar overlap real comparando tokens finales del chunk i con tokens iniciales del chunk i+1 (overlap ≈ 50, tolerancia ±10).
- `test_embedder_dimension`: pedir un embedding real a OpenAI (`text-embedding-3-large`) para un texto corto; verificar `len(vector) == 3072` y que no son todos cero (`any(abs(x) > 0 for x in vector)`).
- `test_retriever_estructura`: embeddear "muros", llamar `recuperar(emb, proyecto_id=1, top_k=5)`; verificar que retorna lista no vacía y que cada elemento tiene `chunk_id` (int), `texto` (str no vacío), `metadata` (dict), `score` (float).
- `test_score_semantica`: tomar el texto de un chunk real recuperado de proyecto_id=1, embeddearlo y recuperarlo; verificar que la **similitud** (`1.0 - score`) del mejor match está en [0,1] y es `> 0.9` (consultar con el propio texto del chunk debe dar match casi perfecto).
- `test_prompt_builder_incluye_contexto`: construir `ChunkRecuperado` de prueba y verificar que el prompt devuelto por `construir_prompt` contiene el `texto` del chunk y la `query`; y que con un chunk de similitud alta `contexto_pobre is False`, con lista vacía `contexto_pobre is True`.
- `test_end_to_end_query`: con FastAPI `TestClient`, `POST /query` con `{"proyecto_id": 1, "mensaje": "muros", "usuario_telegram": "test_pytest"}`; verificar HTTP 200, `score_maximo > 0`, `respuesta` string no vacío, y que la respuesta NO sea exactamente el texto de rendición ("No encontré información sobre esto en los documentos disponibles.").

### Parte 3 — `scripts/diagnostico_rag.py`
Script CLI ejecutable con `python scripts/diagnostico_rag.py` (sin argumentos; query hardcodeada `"muros mampostería"`, proyecto_id hardcodeado `1`). Debe imprimir, con secciones separadas y legibles:
1. **CHUNKS DEL PROYECTO**: todos los chunks de proyecto_id=1 (consulta directa a tabla `chunks` filtrando `proyecto_id`), mostrando por chunk: `id`, primeros 100 chars de `texto`, `metadata`.
2. **RETRIEVAL**: embeddear la query, llamar `recuperar(...)`, listar los top 5 con `chunk_id`, `score` (distancia), similitud (`1 - score`) y primeros 100 chars del texto.
3. **PROMPT**: el prompt completo que devolvería `construir_prompt(query, chunks)` y el flag `contexto_pobre`.
4. **RESPUESTA LLM**: el resultado de `responder(prompt, contexto_pobre)`.
- Manejo de errores: si falta una credencial o no hay datos, imprimir el problema en claro y salir con código ≠ 0 (no stacktrace crudo sin contexto).

## Criterios de aceptación
- [ ] En `src/rag/prompt_builder.py` el umbral por defecto es **0.35** y la comparación de contexto pobre se hace sobre **similitud** (`1 - distancia`), de modo que similitud 0.58 → `contexto_pobre is False`.
- [ ] El prompt mejorado instruye al LLM a responder con el contexto parcial usando "Según los documentos disponibles, ..." y solo rendirse cuando no hay nada útil; sigue prohibiendo inventar.
- [ ] `pytest tests/test_rag_pipeline.py -v` pasa todos los tests en el VPS (con datos de proyecto_id=1 cargados); los skips, si los hay, son explícitos y justificados.
- [ ] Los tests usan Supabase y OpenAI reales (sin mock de DB ni de OpenAI).
- [ ] `python scripts/diagnostico_rag.py` corre en el VPS e imprime las 4 secciones (chunks, retrieval, prompt, respuesta LLM) de forma legible.
- [ ] Con la query "muros" / "muros mampostería" sobre proyecto_id=1, el LLM ya NO devuelve "No encontré información..." (responde con el contenido de los chunks).
- [ ] `tareas/resumenes/TAREA_015_resumen.md` creado: qué criterios se cumplieron, cuáles no y por qué, y la salida resumida de `diagnostico_rag.py` para la query de ejemplo.

## Cómo probar
1. En el VPS, con `.env` cargado y datos de proyecto_id=1 presentes:
   - `pytest tests/test_rag_pipeline.py -v` → todos PASS (skips justificados permitidos).
   - `python scripts/diagnostico_rag.py` → imprime las 4 secciones; en RETRIEVAL la similitud del top chunk para "muros mampostería" debería ser > 0.35 y en RESPUESTA LLM debe haber una respuesta sustantiva (no la frase de rendición).
2. Sanity manual del fix de umbral: para un `chunks[0].score` (distancia) de 0.42 → similitud 0.58 ≥ 0.35 → `contexto_pobre is False`.

## Qué NO hacer
- No tocar `retriever.py`, `embedder.py`, `chunker.py`, `responder.py`, rutas de API, bot ni dashboard.
- No cambiar el modelo LLM ni el de embeddings ni dimensiones; no cambiar chunking 500/50; no cambiar top_k=5; no tocar el esquema de DB ni la RPC `buscar_chunks_similares`.
- No mockear Supabase ni OpenAI en los tests.
- No agregar dependencias nuevas más allá de `pytest` y `httpx`/`TestClient` de FastAPI (ya en el stack).
- No reentrenar, no cachear embeddings en disco, no construir framework de fixtures elaborado: tres tests directos antes que una capa de helpers.
- No crear datos nuevos en producción salvo el log de consulta inevitable del test end-to-end (usuario `test_pytest`).

## Notas para revisión
- Revisor RAG: confirmar que el fix de umbral va en el sentido correcto (similitud, no distancia) — error clásico de signo invertido. Verificar que el prompt mejorado no abre la puerta a alucinaciones (debe seguir anclado al contexto).
- Revisor código: que los tests no dejen basura en Supabase más allá del log esperado; que los `skip` no oculten fallas reales; sin secrets hardcodeados (todo por `.env`).
- Revisor deploy: que `pytest` y el script corran dentro del presupuesto del VPS (2GB/1vCPU) — los tests llaman APIs externas (latencia/costo OpenAII), no cargan modelos locales; vigilar que el end-to-end no dispare timeouts.
