# Resumen TAREA 002

## Qué se implementó
- **Fix A1**: `src/config.py` migrate a `SettingsConfigDict` (Pydantic v2)
- **Fix A2**: Tests aislados del `.env` real usando `_env_file=None`
- **Fix A3**: Versiones mínimas pineadas en `requirements.txt`
- **Parte B**: `src/ingesta/extractor.py` con función `extraer()` para PDF, Word e imágenes

## Decisiones tomadas
- Usé `fitz.open(stream=...)` en vez de ruta de archivo para mantener los bytes en memoria
- PDF sin texto → `es_imagen=True` (no hago OCR)
- Word: extraigo párrafos + texto de celdas de tablas
- No soporté `.doc` (formato binario antiguo), solo `.docx`

## Problemas encontrados
- Error de indentación en `_extraer_pdf` (espacio vs tab) — corregido

## Qué quedó fuera de scope
- OCR (Tesseract, easyocr) — fuera del MVP
- Soporte `.doc` — solo `.docx`
- Descarga de URLs — solo rutas locales
- Procesamiento Excel — tarea futura

## Cómo probarlo
```bash
pip install -r requirements.txt
pytest tests/test_extractor.py tests/test_config.py -v
# Smoke test:
python3 -c "from src.ingesta.extractor import extraer; print('OK')"
```