# Guía de desarrollo — Colaborador RAG-Obras

Este documento es tu referencia de trabajo. Leelo una vez y consultalo cuando tengas dudas. Todo lo demás está en las tareas de `tareas/`.

---

## Cómo funciona el flujo

1. Leonardo te deja tareas en `tareas/TAREA_NNN_*.md`
2. Vos las ejecutás **una por una**, en orden, respetando el "Depende de"
3. Al terminar cada tarea, creás `tareas/resumenes/TAREA_NNN_resumen.md` y lo pusheás
4. Leonardo y Claude revisan desde el repo y te dan feedback o aprobación
5. **El repo es el único canal de comunicación.** Sin resumen pusheado = tarea no entregada

---

## Reglas de oro

### 1. Hacé solo lo que dice la tarea
Si la tarea no lo pide, no lo implementes. No agregues features, no anticipes fases, no "mejorás" cosas que no se pidieron. Si ves algo que falta o que está mal → escribilo en el resumen, no lo implementes.

**Ejemplo:** las TAREA 002–007 eran Fase 1 (Core RAG). El bot de Telegram es Fase 2. Entregarlo en Fase 1 generó bugs y trabajo de revisión extra.

### 2. Stack fijo — sin sustituciones
| Componente | Tecnología — no cambiar |
|---|---|
| API | FastAPI + uvicorn |
| Bot | python-telegram-bot |
| Embeddings | OpenAI `text-embedding-3-large`, **dimensión 3072** |
| LLM respuesta | MiniMax API (`MiniMax-Text-01`) |
| Base vectorial | Supabase pgvector |
| Storage | Supabase Storage |
| Frontend | HTML + CSS + JS vanilla (sin frameworks) |

Sin torch, transformers, sentence-transformers, langchain, ni modelos locales. El VPS tiene 2GB/1vCPU compartidos.

### 3. Nombres exactos — no inventar
- Tablas: `proyectos`, `documentos`, `chunks`, `consultas`
- Endpoints: `/ingest`, `/query`, `/logs`
- Vector: `vector(3072)`
- Chunking: 500 tokens / 50 overlap, medido en **tokens** con tiktoken `cl100k_base`
- Retrieval: similitud **coseno**, **top 5**, filtrado por `proyecto_id`

### 4. Secrets solo por entorno
- Nunca hardcodear API keys, tokens ni URLs de Supabase
- Todo va en `.env` (no commitear), `.env.example` sí se versiona con valores vacíos
- Variables: `OPENAI_API_KEY`, `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`, `SUPABASE_URL`, `SUPABASE_KEY`, `TELEGRAM_BOT_TOKEN`

### 5. Tests que prueben de verdad
- Cada test debe tener al menos un `assert`. Un test con `pass` no es un test.
- Mockear APIs externas (OpenAI, MiniMax, Supabase) — no llamar servicios reales en `pytest`
- Usar `patch.dict(os.environ, vars, clear=True)` + `Settings(_env_file=None)` para aislar config del `.env` real del disco
- Correr `pytest` antes de entregar y confirmar verde en el resumen

### 6. Sin over-engineering
- Resolvé la tarea, no el futuro
- Sin abstracciones que la tarea no pidió (factories, registries, capas extra)
- Sin lógica especulativa ("esto podría ser útil más adelante")
- Tres líneas repetidas > una abstracción prematura

---

## Errores frecuentes que ya ocurrieron — evitalos

### Imports relativos en FastAPI
Si un archivo está en `src/api/routes/archivo.py`, los imports son:
```python
from ..schemas import MiSchema      # schemas.py está en src/api/
from ...config import get_settings  # config.py está en src/
from ...db import get_client        # db.py está en src/
from ...ingesta import extraer      # ingesta/ está en src/
```
No uses `from .schemas` si `schemas.py` no está en la misma carpeta.

### Temp files sin extensión
```python
# ❌ Crea /tmp/tmpXXXX sin extensión → extraer() falla
with tempfile.NamedTemporaryFile(delete=False) as tmp:

# ✅ Preserva la extensión del archivo original
suffix = Path(nombre_archivo).suffix
with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
```

### Temp files que no se borran
```python
# ❌ Si hay excepción, tmp_path queda huérfano en el disco del VPS
tmp_path = ...
resultado = procesar(tmp_path)
Path(tmp_path).unlink()  # nunca llega si procesar() lanza

# ✅ Siempre usar finally
try:
    resultado = procesar(tmp_path)
finally:
    Path(tmp_path).unlink(missing_ok=True)
```

### Retriever — usar SQL con pgvector, no Python puro
```python
# ❌ Trae TODOS los chunks a Python, calcula en RAM — explota en VPS con muchos docs
chunks = supabase.table("chunks").select("*").eq("proyecto_id", pid).execute()
scores = [cosine(query_vec, row["embedding"]) for row in chunks.data]

# ✅ Operador <=> de pgvector, calcula en la base, retorna solo top_k
sql = """
  SELECT id, texto, metadata,
         embedding <=> :query_vec::vector AS score
  FROM chunks
  WHERE proyecto_id = :proyecto_id
  ORDER BY score ASC
  LIMIT :top_k
"""
```

### Errores HTTP que exponen internos
```python
# ❌ Expone mensajes de Supabase/OpenAI con info sensible
raise HTTPException(500, str(e))

# ✅ Mensaje genérico para el cliente, loguear el detalle internamente
print(f"ERROR interno: {e}")  # log server-side
raise HTTPException(500, "Error procesando la solicitud")
```

### Score de similitud — sentido correcto
La distancia coseno con pgvector `<=>` devuelve valores donde **menor = más similar**.
- `score = 0.0` → textos idénticos
- `score = 1.0` → textos sin relación
- `score > 1.0` → raros, textos opuestos

El umbral de "contexto pobre" debe estar en **0.6**, no 1.2. Con 1.2 el sistema nunca detecta búsquedas fallidas y responde inventando.

Si persistís score en la tabla `consultas`, guardá `1 - distancia` como similitud (mayor = mejor) para que el dashboard se lea naturalmente.

---

## Estructura de paquetes Python

```
src/
├── __init__.py          ← vacío
├── config.py
├── db.py
├── api/
│   ├── __init__.py      ← vacío (obligatorio para que sea paquete)
│   ├── main.py
│   ├── schemas.py
│   └── routes/
│       ├── __init__.py  ← vacío
│       ├── ingest.py
│       ├── query.py
│       └── logs.py
├── ingesta/
│   ├── __init__.py      ← expone extraer, chunkear, embeder_y_guardar
│   ├── extractor.py
│   ├── chunker.py
│   └── embedder.py
├── rag/
│   ├── __init__.py      ← expone recuperar, construir_prompt
│   ├── retriever.py
│   ├── prompt_builder.py
│   └── responder.py
└── bot/
    ├── __init__.py      ← vacío
    └── main.py
```

Cada carpeta necesita su `__init__.py` o los imports relativos no funcionan.

---

## Cómo arrancar el entorno

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
cp .env.example .env            # completar con las keys reales

# Levantar la API
uvicorn src.api.main:app --reload --port 8000

# Correr tests (sin keys reales)
pytest -v

# Verificar conexión a Supabase
python scripts/check_conexion.py
```

---

## Formato del resumen de entrega

Cada tarea tiene su plantilla. Lo mínimo necesario:

```markdown
# Resumen TAREA NNN

## Qué se implementó
(lista de archivos y qué hace cada uno)

## Decisiones tomadas
(por qué elegiste tal enfoque — especialmente si hay alternativas posibles)

## Problemas encontrados
(errores que apareció, cómo los resolviste, qué no pudiste resolver)

## Qué quedó fuera de scope
(lo que detectaste pero no implementaste — y por qué)

## Resultado de pytest
(cuántos tests pasan/fallan — mandatory antes de entregar)

## Cómo probarlo
(comando exacto para verificar que funciona)
```

**Esto es lo que Leonardo y Claude revisan. Sin resumen = sin revisión = sin avance.**

---

## Referencia rápida

- **Fuente de verdad del producto:** `BRIEFING_CLAUDE_CODE.md`
- **Reglas de este repo:** `CLAUDE.md`
- **Tareas pendientes:** `tareas/TAREA_NNN_*.md`
- **Tus entregas:** `tareas/resumenes/TAREA_NNN_resumen.md`
- **Schema SQL aplicado:** `migrations/001_schema.sql`
