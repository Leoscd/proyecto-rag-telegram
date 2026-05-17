# TAREA 013 — Demo data: documentos reales + script de carga

- Fecha asignada: 2026-05-17
- Fase del MVP: 4 — Pulido demo
- Estimación: ≤ 1 día
- Depende de: TAREA 009 + TAREA 011 (pipeline completo funcionando)

## Objetivo
Preparar el conjunto de datos de demo para el pitch TIIC: crear/conseguir documentos de construcción representativos, cargarlos al sistema vía script, y verificar que las consultas del caso de uso demo responden correctamente.

## Caso de uso demo (del briefing — esto es lo que el jurado debe ver)

El operario envía: *"estoy por arrancar el encofrado de columnas, que tengo que revisar antes"*

El sistema debe responder:
- Texto: pasos de verificación previa al encofrado según especificación técnica
- Imagen: plano de detalle de columna del sector correspondiente
- Texto adicional: advertencias de seguridad para trabajo con encofrados

**El objetivo de esta tarea es que esa consulta funcione de extremo a extremo.**

## Archivos a crear

- `data/demo/README.md` — descripción de cada documento de demo
- `scripts/cargar_demo.py` — script que ingesta todos los docs de demo vía API
- `data/demo/` — los documentos (ver abajo)

Los documentos en `data/demo/` NO se commitean (están en `.gitignore`).
El `README.md` de `data/demo/` SÍ se commitea y describe qué debe ir ahí.

## Documentos de demo que necesitás conseguir o crear

Crear documentos de texto realistas para una obra ficticia "Edificio Central" en sectores Norte, Sur, A:

### 1. `manual_seguridad_encofrados.pdf`
Contenido mínimo (podés generarlo con cualquier editor y exportar a PDF):
- Sección: "Verificación previa al encofrado de columnas"
  - Lista de pasos: revisión de armadura, limpieza, alineación, torques
- Sección: "Advertencias de seguridad con encofrados"
  - Protecciones personales, riesgo de aplastamiento, procedimiento de desencofrado
- Sección: "Trabajo en altura con encofrados"
  - Arnés requerido, puntos de anclaje, zona de exclusión

### 2. `especificacion_tecnica_columnas.pdf`
Contenido mínimo:
- Especificación de columnas tipo C1 y C2
- Dimensiones, resistencia del hormigón, cuantía de armadura
- Referencias al plano: "ver Plano EST-C-01"

### 3. `plano_columna_sector_norte.png`
Una imagen simple (puede ser un esquema dibujado, una captura o cualquier imagen que represente un plano de columna). El texto del nombre del archivo y sector es suficiente para el MVP.

### 4. `cronograma_obra.pdf` (opcional, si da tiempo)
Tabla con tareas, fechas, responsables. Útil para el dashboard.

## Script cargar_demo.py

```python
"""Carga los documentos de demo al sistema vía API."""
import httpx
from pathlib import Path

API_URL = "http://localhost:8000"
PROYECTO_ID = 1
DEMO_DIR = Path("data/demo")

DOCUMENTOS = [
    {
        "archivo": "manual_seguridad_encofrados.pdf",
        "nombre": "Manual de seguridad — Encofrados",
        "tipo": "manual",
        "sector": "general",
    },
    {
        "archivo": "especificacion_tecnica_columnas.pdf",
        "nombre": "Especificación técnica — Columnas",
        "tipo": "especificacion",
        "sector": "norte",
    },
    {
        "archivo": "plano_columna_sector_norte.png",
        "nombre": "Plano columna sector norte",
        "tipo": "plano",
        "sector": "norte",
    },
]

def cargar_todos():
    # Primero crear el proyecto demo si no existe
    with httpx.Client(timeout=120.0) as client:
        # Crear proyecto
        resp = client.post(f"{API_URL}/proyectos",
                          json={"nombre": "Edificio Central Demo",
                                "descripcion": "Proyecto demo para pitch TIIC",
                                "fecha_inicio": "2026-01-01"})
        if resp.status_code == 201:
            proyecto_id = resp.json()["id"]
            print(f"Proyecto creado: id={proyecto_id}")
        else:
            proyecto_id = PROYECTO_ID
            print(f"Usando proyecto_id={proyecto_id}")

        # Ingestar documentos
        for doc in DOCUMENTOS:
            archivo_path = DEMO_DIR / doc["archivo"]
            if not archivo_path.exists():
                print(f"⚠️  No encontrado: {archivo_path} — saltando")
                continue

            print(f"Cargando: {doc['nombre']}...")
            with open(archivo_path, "rb") as f:
                resp = client.post(
                    f"{API_URL}/ingest",
                    data={
                        "proyecto_id": proyecto_id,
                        "nombre": doc["nombre"],
                        "tipo": doc["tipo"],
                        "sector": doc["sector"],
                    },
                    files={"archivo": (doc["archivo"], f)},
                )
            if resp.status_code == 200:
                r = resp.json()
                print(f"  ✅ {r['nombre']} — {r['chunks_generados']} chunks, imagen={r['es_imagen']}")
            else:
                print(f"  ❌ Error: {resp.text[:200]}")

if __name__ == "__main__":
    cargar_todos()
```

## Verificación del caso de uso demo

Al terminar la carga, correr estas queries y documentar las respuestas en el resumen:

```bash
# Query principal del caso de uso TIIC
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 1, "mensaje": "estoy por arrancar el encofrado de columnas, que tengo que revisar antes", "usuario_telegram": "demo_test"}' \
  | python -m json.tool

# Verificar que tiene plano
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 1, "mensaje": "mostrame el plano de columna del sector norte", "usuario_telegram": "demo_test"}' \
  | python -m json.tool

# Verificar gap (pregunta sin documentación)
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 1, "mensaje": "precio del acero en mercado local", "usuario_telegram": "demo_test"}' \
  | python -m json.tool
```

## Criterios de aceptación
- [ ] `python scripts/cargar_demo.py` carga los 3 documentos sin errores
- [ ] Query del caso de uso TIIC devuelve respuesta con score ≥ 0.5 (buena recuperación)
- [ ] Query de plano devuelve `tiene_imagen=True` y `ruta_imagen` válido
- [ ] Query de gap devuelve respuesta honesta de "no encontré información" o `contexto_pobre=True`
- [ ] `data/demo/README.md` describe los documentos y cómo conseguirlos/crearlos
- [ ] `scripts/cargar_demo.py` está commiteado y funciona

## Qué NO hacer
- No commitear los PDFs/imágenes de demo (`.gitignore` ya los excluye)
- No inventar datos técnicos incorrectos — si los procedimientos son ficticios, que sean plausibles
- Sin script de borrado de datos — si hay que resetear, hacerlo manualmente desde Supabase

---

## Resumen de entrega (OBLIGATORIO)

Crear `tareas/resumenes/TAREA_013_resumen.md`:

```markdown
# Resumen TAREA 013

## Documentos de demo creados
- [nombre]: [descripción breve, páginas/tamaño]

## Resultado del script de carga
(output del script: qué se cargó, cuántos chunks)

## Verificación del caso de uso TIIC
- Query encofrado: [score_maximo, primeras 200 chars de respuesta]
- Query plano: [tiene_imagen, ruta_imagen]
- Query gap: [contexto_pobre, respuesta]

## Qué mejoraría para la demo real
```
