# TAREA 011 — Panel admin HTML (carga de documentos)

- Fecha asignada: 2026-05-17
- Fase del MVP: 3 — Panel admin
- Estimación: ≤ 1 día
- Depende de: TAREA 010 (endpoints proyectos + documentos)

## Objetivo
Crear el panel web que usa el jefe de obra para cargar documentos al sistema. HTML + CSS + JS vanilla, sin frameworks. Se sirve como archivo estático desde FastAPI.

## Archivos a crear / modificar

- `src/dashboard/admin.html` — panel principal
- `src/api/main.py` — servir archivos estáticos desde `src/dashboard/`

## Servir el HTML desde FastAPI

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# En src/api/main.py, después de incluir routers:
static_path = Path(__file__).parent.parent / "dashboard"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/admin")
def admin():
    from fastapi.responses import FileResponse
    return FileResponse(str(static_path / "admin.html"))
```

Agregar `pip install aiofiles` en requirements.txt (necesario para StaticFiles).

## Diseño y funcionalidad de admin.html

### Secciones

**1. Selector de proyecto (arriba)**
- Dropdown que se puebla llamando `GET /proyectos`
- Botón "Nuevo proyecto" → abre un formulario inline para `POST /proyectos`

**2. Formulario de carga de documento**
```
[Archivo]  (.pdf, .docx, .png, .jpg)
[Nombre del documento]
[Tipo]     (dropdown: manual / especificacion / plano / protocolo / cronograma)
[Sector]   (texto libre, opcional)
[Botón: Cargar documento]
```
Al enviar: `POST /ingest` con `FormData`. Mostrar spinner mientras procesa.

Respuesta exitosa → mostrar:
```
✅ Cargado: manual_seguridad.pdf — 18 chunks generados
```

**3. Lista de documentos cargados**
Tabla con documentos del proyecto seleccionado (`GET /documentos?proyecto_id=X`):

| Nombre | Tipo | Sector | Fecha | Chunks | Es imagen |
|---|---|---|---|---|---|
| manual_seg.pdf | manual | norte | 17/05/26 | 18 | No |
| plano_columna.png | plano | A | 17/05/26 | 1 | Sí |

Botón "Actualizar" para recargar la tabla.

### Estilo
- Sin frameworks CSS
- Paleta: fondo `#f5f5f5`, card blanco `#ffffff`, acento azul `#2563eb`
- Responsive básico (que no se rompa en mobile)
- Font: system-ui o similar, sin Google Fonts (VPS puede estar offline)

### JS: sin fetch con async/await complejo
Usar `fetch()` con `.then()/.catch()` para simplicidad. No usar import/export ni módulos ES6 (compatibilidad máxima). Todo en un `<script>` al final del body.

## Criterios de aceptación
- [ ] Abrir `http://localhost:8000/admin` sirve el HTML sin errores
- [ ] El dropdown se puebla con los proyectos reales de Supabase
- [ ] Cargar un PDF funciona: llama a `/ingest`, muestra el resultado
- [ ] La tabla de documentos se carga correctamente
- [ ] El formulario muestra error claro si `/ingest` falla (sin mostrar stack traces internos)
- [ ] No usa React, Vue, Angular ni ningún framework JS

## Cómo probar
```bash
uvicorn src.api.main:app --port 8000
# Abrir en el browser: http://localhost:8000/admin
# Cargar un PDF de data/demo/ y verificar que aparece en la tabla
```

## Qué NO hacer
- Sin login / autenticación
- Sin editar ni borrar documentos desde el panel
- Sin drag & drop (keep it simple)
- Sin uso de localStorage, cookies ni sesiones

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_011_resumen.md`:

```markdown
# Resumen TAREA 011

## Qué se implementó
## Decisiones de diseño (ej: cómo manejaste el fetch, el spinner, errores)
## Problemas encontrados
## Screenshot o descripción del panel funcionando
## Cómo probarlo
```
