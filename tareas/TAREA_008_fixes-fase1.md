# TAREA 008 — Fixes Fase 1: retriever SQL, imagen↔plano, tests, calidad RAG

- Fecha asignada: 2026-05-17
- Fase del MVP: 1 — Core RAG (cierre)
- Estimación: ≤ 1 día
- Depende de: TAREA 007

## Contexto
Los bloqueantes mecánicos (imports, __init__.py, temp file, python-multipart) ya fueron corregidos por el equipo y están en main. Esta tarea cubre los problemas que requieren lógica: retriever SQL, el vínculo plano↔imagen, calidad del prompt, y los tests que quedaron como stubs vacíos.

Leer `COLABORADOR_GUIA.md` antes de empezar — los errores frecuentes de la entrega anterior están documentados ahí.

---

## A — Retriever: migrar de Python puro a SQL con pgvector

**Archivo:** `src/rag/retriever.py`

El retriever actual trae todos los chunks a Python y calcula coseno en memoria. Reemplazarlo por una query SQL que usa el operador `<=>` de pgvector.

La API de supabase-py no soporta `<=>` directamente en `.select()`. Usar `execute_sql` vía `rpc` o la función `postgrest` con un query raw. La forma más simple con supabase-py:

```python
# Convertir query_embedding a string formato pgvector: "[0.1, 0.2, ...]"
vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

result = supabase_client.rpc(
    "buscar_chunks_similares",
    {
        "query_vector": vector_str,
        "pid": proyecto_id,
        "top_k": top_k,
    }
).execute()
```

Crear la función SQL en una nueva migración `migrations/002_buscar_chunks.sql`:

```sql
CREATE OR REPLACE FUNCTION buscar_chunks_similares(
    query_vector vector(3072),
    pid integer,
    top_k integer DEFAULT 5
)
RETURNS TABLE(
    id integer,
    texto text,
    metadata jsonb,
    score float
)
LANGUAGE sql STABLE AS $$
    SELECT
        id,
        texto,
        metadata,
        (embedding <=> query_vector)::float AS score
    FROM chunks
    WHERE proyecto_id = pid
    ORDER BY embedding <=> query_vector
    LIMIT top_k;
$$;
```

La función va a Supabase con `migrations/002_buscar_chunks.sql`. Documentar en el resumen cómo aplicarla (SQL editor de Supabase o psql).

**Criterios:**
- [ ] `recuperar()` usa la función RPC, no `.select("*, embedding")`
- [ ] No se traen vectores a Python — el score llega calculado desde la base
- [ ] Filtra por `proyecto_id` en la función SQL
- [ ] `tests/test_retriever.py` tiene tests reales (no `pass`) con Supabase mockeado

---

## B — Vínculo plano↔imagen en la ingesta y el query

**Problema:** los documentos tipo imagen (planos) no generan chunks → el retriever nunca devuelve `es_imagen=True` → nunca se adjunta una imagen al operario.

**Solución para el MVP:** cuando se ingesta un plano (imagen), crear un chunk con el texto del nombre del documento + sector como "texto de búsqueda" del plano, con `es_imagen=True` y `ruta_archivo` en la metadata. Así el retriever puede recuperar ese chunk si la consulta es relevante al sector/especialidad.

**Cambios en `src/api/routes/ingest.py`:**
```python
# Si es imagen → crear un chunk sintético con texto de búsqueda
if extractor_result.es_imagen:
    texto_busqueda = f"Plano: {nombre}. Sector: {sector or 'general'}. Tipo: {tipo}."
    chunk_sintetico = Chunk(
        texto=texto_busqueda,
        tokens=len(texto_busqueda.split()),  # aproximado, es un chunk sintético
        indice=0,
        metadata={
            "documento_id": documento_id,
            "proyecto_id": proyecto_id,
            "tipo": tipo,
            "sector": sector or None,
            "nombre_documento": nombre,
            "es_imagen": True,
            "ruta_archivo": path_storage,
        }
    )
    chunks_generados = embeder_y_guardar([chunk_sintetico], documento_id, proyecto_id)
```

**Cambios en `src/api/routes/query.py`:**
El campo `ruta_imagen` debe venir de `chunk.metadata.get("ruta_archivo")` cuando `es_imagen=True`. Verificar que la lógica de `tiene_imagen` y `ruta_imagen` usa esto correctamente (ya estaba, solo faltaba que hubiera chunks con `es_imagen=True`).

**Criterios:**
- [ ] Ingestar un PNG/JPG crea exactamente 1 chunk con `es_imagen=True` y `ruta_archivo` correcto
- [ ] Consultar "plano del sector norte" recupera el chunk del plano si fue ingested
- [ ] El campo `tiene_imagen` y `ruta_imagen` en la respuesta de `/query` se pueblan correctamente

---

## C — Calidad del prompt: umbral y posición del ADVERTENCIA

**Archivo:** `src/rag/prompt_builder.py`

**Fix 1 — Umbral de score:** cambiar `score_umbral=1.2` a `score_umbral=0.6`. Con 1.2 el sistema nunca detecta contexto pobre y responde inventando.

**Fix 2 — Posición del ADVERTENCIA:** moverlo ANTES del bloque CONTEXTO, dentro de las instrucciones:

```python
prompt = f"""Sos un asistente técnico de obra. Respondé ÚNICAMENTE usando la información
del contexto. Si la información no está en el contexto, decí exactamente:
"No encontré información sobre esto en los documentos disponibles."
No inventes datos, medidas, procedimientos ni normativas.
{advertencia_si_aplica}
CONTEXTO:
{contexto}

PREGUNTA: {query}

RESPUESTA:
"""
```

Donde `advertencia_si_aplica` es el string de ADVERTENCIA si `contexto_pobre=True`, vacío si no.

**Criterios:**
- [ ] `score_umbral` por defecto es 0.6
- [ ] La ADVERTENCIA aparece antes de CONTEXTO cuando `contexto_pobre=True`
- [ ] `pytest tests/test_prompt_builder.py` pasa y verifica la posición del ADVERTENCIA

---

## D — `score_maximo` con semántica correcta

**Archivo:** `src/api/routes/query.py`

`score_maximo` se guarda como la distancia del chunk más similar (menor = mejor match). En el dashboard esto se lee al revés. Guardar como similitud: `1 - distancia`.

```python
score_maximo = 1.0 - chunks[0].score  # similitud: mayor = mejor match
```

Actualizar también en el `QueryResponse` y en la inserción en `consultas`.

**Criterio:**
- [ ] `score_maximo = 1.0` significa match perfecto, `0.0` significa sin relación

---

## E — Tests con asserts reales

Los siguientes tests se entregaron como stubs (`pass`). Implementarlos:

**`tests/test_query.py`** — Al menos 2 tests:
- POST `/query` con chunks recuperados → respuesta 200 con `respuesta` no vacía (mockear OpenAI, retriever, MiniMax)
- POST `/query` sin chunks → respuesta con `contexto_pobre=True` y `score_maximo=0.0`

**`tests/test_retriever.py`** — Al menos 2 tests:
- `recuperar()` con mocks de Supabase RPC → retorna lista de `ChunkRecuperado` ordenada por score
- `recuperar()` con resultado vacío → retorna `[]`

**`tests/test_ingest.py`** — Al menos 2 tests con asserts:
- POST `/ingest` con PDF válido → status 200, `chunks_generados > 0`
- POST `/ingest` con imagen → status 200, `es_imagen=True`, `chunks_generados=1` (el chunk sintético)

**`tests/test_extractor.py`** — Al menos 2 tests con asserts:
- PDF con texto → `es_imagen=False`, `texto` no vacío
- PNG → `es_imagen=True`, `texto=""`

**Criterio:**
- [ ] `pytest -v` corre sin errores de collection
- [ ] Ningún test tiene solo `pass` como cuerpo
- [ ] Todos los mocks de APIs externas funcionan offline (sin keys reales)

---

## F — Robustez: temp file + errores HTTP

**`src/api/routes/ingest.py`** — agregar `finally` para limpiar el tmp:
```python
tmp_path = None
try:
    suffix = Path(nombre).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        contenido = await archivo.read()
        tmp.write(contenido)
        tmp_path = tmp.name
    # ... resto del pipeline ...
except Exception as e:
    print(f"ERROR en /ingest: {e}")
    raise HTTPException(500, "Error procesando el documento")
finally:
    if tmp_path:
        Path(tmp_path).unlink(missing_ok=True)
```

Mismo patrón de error genérico en `query.py`: no exponer `str(e)` al cliente.

---

## Entrega

### Archivos a modificar
- `src/rag/retriever.py`
- `src/api/routes/ingest.py`
- `src/api/routes/query.py`
- `src/rag/prompt_builder.py`
- `tests/test_query.py`
- `tests/test_retriever.py`
- `tests/test_ingest.py`
- `tests/test_extractor.py`

### Archivos a crear
- `migrations/002_buscar_chunks.sql`

### Smoke test obligatorio para cerrar Fase 1
Con el `.env` completo y la API levantada:
1. `POST /ingest` con un PDF de texto real → anotar `documento_id` y `chunks_generados`
2. `POST /ingest` con una imagen (PNG de plano) → anotar `es_imagen: true`
3. `POST /query` con pregunta relacionada al PDF → anotar `respuesta` y `score_maximo`
4. `GET /logs` → verificar que la consulta quedó registrada
5. Incluir los resultados en el resumen

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_008_resumen.md`:

```markdown
# Resumen TAREA 008

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Resultado de pytest (cuántos pasan/fallan)
## Smoke test end-to-end
- PDF ingested: [nombre, chunks_generados]
- Imagen ingested: [nombre, es_imagen]
- Query: [texto, score_maximo, respuesta primeras 100 chars]
- Logs: [registrado sí/no]
## Cómo aplicar migrations/002_buscar_chunks.sql en Supabase
```

**Sin smoke test con resultados reales, la Fase 1 no se considera cerrada.**
