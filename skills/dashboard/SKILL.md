# Skill: Dashboard para RAG-Obras

## Descripción
Dashboard web simples para control de calidad del sistema RAG. Muestra consultas, documentos subidos y métricas.

## Endpoints de la API
- `GET /logs` — historial de consultas
- `GET /documentos` — lista de documentos (futuro)
- `POST /ingest` — subir documentos

## Estructura
- HTML + CSS vanilla
- Fetch a `/logs` para mostrar datos
- Tabla de consultas con score, timestamp, usuario

##部署
```bash
# Simple: servir con Python
python -m http.server 8080
# O con la API
uvicorn src.api.main:app --port 8000
# Acceder a http://localhost:8080/dashboard.html
```