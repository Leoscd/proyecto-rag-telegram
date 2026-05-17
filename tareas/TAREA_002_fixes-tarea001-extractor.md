# TAREA 002 — Fixes TAREA 001 + Extractor de texto (PDF / Word / imagen)

- Fecha asignada: 2026-05-17
- Fase del MVP: 1 — Core RAG
- Estimación: ≤ 1 día
- Depende de: TAREA 001 (cerrada)

## Objetivo
Corregir los tres menores que quedaron de TAREA 001 e implementar el extractor de texto que convierte documentos (PDF, Word, imagen de plano) en texto plano listo para chunkear.

---

## Parte A — Fixes de TAREA 001 (hacerlos primero, son rápidos)

### A1. `src/config.py` — migrar a SettingsConfigDict
Reemplazar el bloque `class Config` interno (estilo Pydantic v1, deprecado) por:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    # ... resto igual
```

### A2. `tests/test_config.py` — aislar del .env real
Los tres tests deben usar `Settings(_env_file=None)` para no leer el `.env` del disco.
Ejemplo:
```python
with patch.dict(os.environ, {}, clear=True):
    settings = Settings(_env_file=None)  # no lee .env
```
Reemplazar también la llamada a `get_settings()` con una instancia directa de `Settings(_env_file=None)`
más la validación manual, para que el test no dependa de efectos secundarios del cwd.

### A3. `requirements.txt` — pinear versiones mínimas conocidas
Agregar versiones `>=X.Y` sobre las dependencias principales. No pinear exacto (`==`), sino mínimo conocido:
```
fastapi>=0.111
uvicorn[standard]>=0.29
python-telegram-bot>=21.0
openai>=1.30
supabase>=2.4
pymupdf>=1.24
python-docx>=1.1
python-dotenv>=1.0
pydantic-settings>=2.2
tiktoken>=0.7
httpx>=0.27
pytest>=8.0
```

---

## Parte B — Extractor de texto

### Archivos a crear
- `src/ingesta/extractor.py` — lógica de extracción
- `src/ingesta/__init__.py` — vacío
- `tests/test_extractor.py` — tests unitarios

### Contrato

```python
from dataclasses import dataclass

@dataclass
class DocumentoExtraido:
    texto: str           # texto extraído (vacío si es imagen sin OCR)
    paginas: int         # número de páginas (1 para Word/imagen)
    es_imagen: bool      # True si el doc es plano/imagen (no texto extraíble)
    bytes_raw: bytes     # bytes originales del archivo (para guardar en Storage)

def extraer(ruta_archivo: str) -> DocumentoExtraido:
    """
    Extrae texto de un documento según su extensión.
    - .pdf  → PyMuPDF (fitz). Si el PDF tiene texto extraíble, devuelve texto.
              Si todas las páginas están vacías (PDF de imagen), setear es_imagen=True.
    - .docx → python-docx. Extrae párrafos y texto de tablas.
    - .doc  → No soportado: lanzar ValueError con mensaje claro.
    - .png / .jpg / .jpeg → es_imagen=True, texto="" (OCR fuera del MVP).
    - otros → lanzar ValueError(f"Tipo de archivo no soportado: {ext}")
    """
```

### Reglas de extracción
- **PDF con texto**: concatenar texto de todas las páginas, separadas por `\n\n--- Página {n} ---\n\n`.
- **PDF sin texto** (plano escaneado): `texto=""`, `es_imagen=True`. Guardar bytes para Storage.
- **Word**: extraer párrafos (`doc.paragraphs`) + texto de celdas de tablas. Separar párrafos con `\n`.
- **Imagen**: `texto=""`, `es_imagen=True`, `paginas=1`.
- No silenciar excepciones: si PyMuPDF falla en un PDF corrupto, dejar que suba el error.

### Criterios de aceptación
- [ ] `extraer("archivo.pdf")` devuelve `DocumentoExtraido` con texto no vacío para PDF con texto.
- [ ] PDF escaneado (sin texto) → `es_imagen=True`, `texto=""`.
- [ ] `extraer("archivo.docx")` devuelve texto de párrafos y tablas.
- [ ] `.png` → `es_imagen=True`, `texto=""`.
- [ ] Extensión no soportada → `ValueError` con mensaje claro.
- [ ] `pytest tests/test_extractor.py` pasa (usar archivos de fixture pequeños o mocks).
- [ ] `pytest tests/test_config.py` pasa después de los fixes de Parte A.

### Cómo probar
```bash
pytest tests/test_extractor.py tests/test_config.py -v
# Smoke test manual con un PDF real:
python -c "from src.ingesta.extractor import extraer; r = extraer('data/demo/test.pdf'); print(r.texto[:200])"
```

### Qué NO hacer
- Sin OCR (Tesseract, easyocr, etc.) — fuera del MVP.
- Sin soporte `.doc` (formato binario antiguo) — solo `.docx`.
- Sin descarga de URLs — solo rutas locales.
- Sin procesamiento de Excel — es TAREA de Fase posterior.

---

## Resumen de entrega (OBLIGATORIO)

Al terminar, crear el archivo `tareas/resumenes/TAREA_002_resumen.md` y pushearlo al repo con este formato:

```markdown
# Resumen TAREA 002

## Qué se implementó
- ...

## Decisiones tomadas
- (ej: "usé fitz.open() en vez de PdfReader porque...")

## Problemas encontrados
- ...

## Qué quedó fuera de scope
- ...

## Cómo probarlo
- comando exacto para verificar
```

**Sin este archivo, la tarea no se considera entregada.**
