# TAREA 012 — Dashboard de control de calidad RAG

- Fecha asignada: 2026-05-17
- Fase del MVP: 3 — Dashboard
- Estimación: ≤ 1 día
- Depende de: TAREA 011 (static files ya configurado)

## Objetivo
Crear el dashboard que muestra al jefe de obra todas las consultas realizadas, los scores de relevancia, y detecta automáticamente los gaps de documentación (preguntas sin respuesta adecuada).

## Archivos a crear / modificar

- `src/dashboard/index.html` — reemplazar el actual (está vacío/placeholder)
- `src/api/main.py` — agregar ruta GET /dashboard → FileResponse de index.html
- `src/api/routes/logs.py` — agregar endpoint GET /stats

## Nuevo endpoint GET /stats

```
GET /stats?proyecto_id=1
```

Response:
```json
{
  "total_consultas": 42,
  "score_promedio": 0.71,
  "consultas_sin_respuesta": 5,
  "score_por_dia": [
    { "fecha": "2026-05-17", "promedio": 0.68, "total": 12 }
  ],
  "gaps_documentacion": [
    {
      "mensaje": "protocolo para trabajo en espacios confinados",
      "score_maximo": 0.18,
      "timestamp": "2026-05-17T14:23:00"
    }
  ]
}
```

`gaps_documentacion` = consultas donde `score_maximo < 0.4` (similitud baja = el sistema no encontró buena documentación). Listar las últimas 10.

`score_por_dia` = agrupación diaria de consultas con promedio de score. Útil para detectar días con muchas consultas sin respuesta.

## Diseño del dashboard index.html

### Sección 1 — Cards resumen (arriba)
```
[Total consultas: 42]  [Score promedio: 71%]  [Sin respuesta: 5]
```

### Sección 2 — Tabla de consultas recientes
Carga de `GET /logs?proyecto_id=X&limit=50`, con filtro de proyecto y un input de búsqueda por texto.

| Usuario | Consulta | Score | ¿Buena? | Timestamp |
|---|---|---|---|---|
| operario_garcia | como se hace el encofrado... | 82% | ✅ | 17/05 14:23 |
| user_123 | protocolo espacios confinados | 18% | ⚠️ | 17/05 15:01 |

Color por score:
- Verde (≥ 60%): buena recuperación
- Amarillo (40–59%): recuperación dudosa  
- Rojo (< 40%): gap de documentación

Click en una fila expande la respuesta generada.

### Sección 3 — Gaps de documentación
Lista de las consultas con score bajo (gaps), ordenadas de peor a mejor. Título: "⚠️ Preguntas sin documentación adecuada". Esto es lo que el jefe de obra usa para saber qué documentos faltan cargar.

### Estilo
- Consistente con admin.html (misma paleta: fondo `#f5f5f5`, card blanco, acento `#2563eb`)
- Rojo `#dc2626`, amarillo `#d97706`, verde `#16a34a` para los scores
- Sin frameworks
- Font: system-ui

## Criterios de aceptación
- [ ] `http://localhost:8000/dashboard` sirve el HTML
- [ ] Las cards de resumen muestran datos reales de Supabase
- [ ] La tabla de consultas se carga y filtra correctamente
- [ ] Colores de score correctos (verde/amarillo/rojo)
- [ ] Sección de gaps lista consultas con score < 40%
- [ ] `GET /stats` devuelve el JSON esperado

## Qué NO hacer
- Sin gráficos complejos (D3.js, Chart.js) — barras con CSS alcanzan
- Sin autenticación
- Sin exportar a Excel/PDF — fuera del MVP

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_012_resumen.md`:

```markdown
# Resumen TAREA 012

## Qué se implementó
## Decisiones de diseño
## Problemas encontrados
## Qué datos de prueba usaste para verificar el dashboard
## Cómo probarlo
```
