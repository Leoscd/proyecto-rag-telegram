# TAREA 010 — Endpoints proyectos y documentos (base del panel admin)

- Fecha asignada: 2026-05-17
- Fase del MVP: 3 — Panel admin
- Estimación: ≤ 1 día
- Depende de: TAREA 008

## Objetivo
Agregar los endpoints que necesita el panel de administración para listar proyectos, crear proyectos y listar documentos cargados. El panel HTML (TAREA 011) los consume.

## Archivos a crear / modificar

- `src/api/routes/proyectos.py` — router `/proyectos`
- `src/api/routes/documentos.py` — router `/documentos`
- `src/api/schemas.py` — agregar schemas nuevos
- `src/api/main.py` — registrar los dos routers nuevos
- `tests/test_proyectos.py`
- `tests/test_documentos.py`

## Contrato

### GET /proyectos
```json
[
  { "id": 1, "nombre": "Obra Ruta 40", "descripcion": "...", "fecha_inicio": "2026-01-01", "activo": true }
]
```
Query param opcional: `activo=true` para filtrar solo proyectos activos.

### POST /proyectos
Request JSON:
```json
{ "nombre": "Obra Ruta 40", "descripcion": "Construcción vial", "fecha_inicio": "2026-01-01" }
```
Response 201:
```json
{ "id": 5, "nombre": "Obra Ruta 40", "activo": true }
```
Validar que `nombre` no esté vacío (422 si está vacío).

### GET /documentos
Query params opcionales: `proyecto_id=1`, `tipo=manual`, `limit=50`, `offset=0`

Response:
```json
[
  {
    "id": 3,
    "proyecto_id": 1,
    "nombre": "manual_seguridad.pdf",
    "tipo": "manual",
    "sector": "norte",
    "ruta_archivo": "1/manual_seguridad.pdf",
    "fecha_carga": "2026-05-17T10:00:00",
    "chunks_count": 18
  }
]
```

`chunks_count` = COUNT de chunks asociados a ese documento_id. Obtenerlo con una query que cuente en `chunks` o con una subconsulta. Si es costoso, puede ser -1 y se documenta como "no implementado en MVP".

### DELETE /proyectos/{id} — opcional, si da tiempo
Marca `activo=False` (soft delete, no borrar). Si no da tiempo, omitir y documentarlo en el resumen.

## Criterios de aceptación
- [ ] `GET /proyectos` lista todos los proyectos
- [ ] `POST /proyectos` con nombre válido → 201 con `id` generado
- [ ] `POST /proyectos` con nombre vacío → 422
- [ ] `GET /documentos?proyecto_id=1` filtra correctamente
- [ ] Los routers están registrados en `src/api/main.py` y accesibles
- [ ] `pytest tests/test_proyectos.py tests/test_documentos.py` pasa

## Qué NO hacer
- Sin autenticación
- Sin paginación compleja — `limit`/`offset` básico alcanza
- Sin endpoint para eliminar chunks o re-indexar documentos (Fase posterior)

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_010_resumen.md`:

```markdown
# Resumen TAREA 010

## Qué se implementó
## Decisiones tomadas
## Problemas encontrados
## Resultado pytest
## Cómo probarlo (curl examples)
```
