# TAREA 016 — Imagen de página de PDF en respuesta del bot

- Fecha asignada: 2026-05-18
- Fase del MVP: 4 (pulido para demo)
- Estimación: ≤1 día
- Depende de: TAREA_005 (api-ingest), TAREA_007 (query), TAREA_009 (bot-telegram)

## Objetivo
Durante la ingesta de un PDF, renderizar cada página como PNG, subirla a Supabase
Storage y registrar su path en la metadata del chunk que arranca en esa página.
En la query, devolver la imagen de la página del top chunk como `ruta_imagen`
(solo si la similitud del top chunk supera 0.35) para que el bot la mande por Telegram.

## Contexto mínimo necesario
- Briefing: "Flujo RAG detallado" (líneas 80-96) y "Caso de uso demo" (179-188):
  respuesta = texto + imagen del plano/detalle relevante.
- Estado actual:
  - `src/ingesta/extractor.py` extrae texto de PDF con PyMuPDF (`fitz`), concatenando
    páginas con marcador `--- Página N ---`. PyMuPDF ya está instalado.
  - `src/api/routes/ingest.py` arma `metadata_base` (dict) y llama `chunkear(texto, metadata_base)`.
    El bucket Storage `"documentos"` ya existe y se sube con
    `supabase_client.storage.from_("documentos").upload(path=..., file=..., file_options=...)`.
  - `src/ingesta/chunker.py` propaga `metadata_base` a cada `Chunk.metadata` tal cual
    (más `chunk_index`). **No se modifica.**
  - `src/api/routes/query.py` ya calcula `score_maximo = 1.0 - chunks[0].score`
    (similitud, mayor = mejor) y ya setea `tiene_imagen` / `ruta_imagen` mirando
    `chunk.metadata.get("es_imagen")` / `"ruta_archivo"`.
  - `src/bot/main.py` ya pide signed URL y envía la foto cuando `tiene_imagen=True`.
    **No se modifica.** `schemas.py` ya tiene `ruta_imagen` en `QueryResponse`. **No se modifica.**
- Render PNG con PyMuPDF: `pix = doc[n].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))`
  → `png_bytes = pix.tobytes("png")`.

## Archivos a crear / modificar
- `src/ingesta/extractor.py` — `_extraer_pdf` debe, además del texto concatenado,
  devolver el texto por página (lista) para poder mapear offset de caracteres → página.
  Agregar campo `paginas_texto: list[str]` al dataclass `DocumentoExtraido`
  (lista vacía para Word/imagen; un elemento por página de PDF, en orden, índice 0 = página 1).
  El `texto` concatenado debe seguir igual que hoy (mismos marcadores) para no
  alterar chunking/embeddings de Fase 1.
- `src/api/routes/ingest.py` — solo para ramas PDF con texto (no imagen):
  1. Tras insertar en `documentos` y antes/junto al chunkeo, abrir el PDF con
     `fitz.open(stream=..., filetype="pdf")` y, **página por página**, renderizar
     PNG (matrix 1.5) y subir a Storage en
     `{proyecto_id}/{documento_id}/paginas/pagina_{n}.png` (n desde 1).
  2. Construir un mapa `pagina → page_image_path` solo de las páginas subidas con éxito.
  3. Después de `chunkear(...)`, recorrer los chunks y, para cada uno, calcular a qué
     página pertenece su INICIO (ver "Contrato" para el algoritmo de offset) y setear
     `chunk.metadata["page_image_path"] = mapa.get(pagina)` (puede quedar `None`).
  4. Recién entonces `embeder_y_guardar(chunks, ...)`.
- `src/api/routes/query.py` — al elegir imagen: si `chunks[0].metadata` tiene
  `page_image_path` (no `None`/vacío) **y** `score_maximo > 0.35`, entonces
  `tiene_imagen=True` y `ruta_imagen = chunks[0].metadata["page_image_path"]`.
  Mantener el comportamiento previo de planos/imagen directa (`es_imagen=True`) como
  fallback cuando no haya `page_image_path`.

## Contrato (inputs / outputs)
`DocumentoExtraido` (extractor.py):
```python
@dataclass
class DocumentoExtraido:
    texto: str
    paginas: int
    es_imagen: bool
    bytes_raw: bytes
    paginas_texto: list[str]  # NUEVO. PDF: una entrada por página (índice 0 = pág 1).
                              # Word/imagen/PDF sin páginas: []
```

Render + subida (ingest.py), por página `i` (0-based), `n = i + 1`:
```python
try:
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    png_bytes = pix.tobytes("png")
    path = f"{proyecto_id}/{documento_id}/paginas/pagina_{n}.png"
    supabase_client.storage.from_("documentos").upload(
        path=path, file=png_bytes,
        file_options={"content-type": "image/png"},
    )
    mapa_paginas[n] = path
except Exception as e:
    print(f"WARN render/subida página {n}: {e}")  # continuar, no abortar ingest
```

Mapeo chunk → página por offset de caracteres (en ingest.py, tras chunkear):
- `paginas_texto[k]` corresponde a la página `n = k + 1`.
- Calcular los offsets acumulados de inicio de cada página dentro de `texto_extraido`
  reusando el MISMO formato que arma el extractor (marcador `--- Página N ---`).
  Recomendado: que el extractor devuelva además `offsets_paginas: list[int]`
  (offset de char donde empieza el texto de cada página dentro de `texto`),
  o calcularlo en ingest a partir de `paginas_texto` y el marcador. Elegí UNA vía
  y dejala consistente; no dupliques la lógica de formato.
- Para cada chunk, hallar su offset de inicio dentro de `texto_extraido`
  (`texto.find(chunk.texto)` desde un cursor que avanza para evitar coincidencias
  repetidas; si `find` falla, usar el último offset conocido). La página del chunk
  es la mayor `n` cuyo offset de inicio ≤ offset del chunk.
- `chunk.metadata["page_image_path"] = mapa_paginas.get(pagina_del_chunk)` (o `None`).

Query (query.py) — selección de imagen:
```
top = chunks[0]
pip = top.metadata.get("page_image_path")
if pip and score_maximo > 0.35:
    tiene_imagen, ruta_imagen = True, pip
else:
    # fallback existente: primer chunk con es_imagen=True → ruta_archivo
```

## Criterios de aceptación
- [ ] Subir un PDF de varias páginas por el admin → en Storage aparecen
      `{proyecto_id}/{documento_id}/paginas/pagina_1.png ... pagina_N.png`.
- [ ] Los chunks de ese PDF tienen `page_image_path` en `metadata` apuntando al PNG
      de la página donde empieza su texto (verificable en tabla `chunks`).
- [ ] Consultar por Telegram contenido de ese PDF con buena similitud (>0.35) →
      el bot responde texto Y envía la foto de la página relevante.
- [ ] Consulta con similitud ≤0.35 → responde texto sin imagen (no manda PNG irrelevante).
- [ ] Ingesta de PNG/JPG y de Word sigue funcionando igual; planos imagen directa
      siguen devolviendo su imagen como antes.
- [ ] Documentos cargados antes de esta tarea (sin `page_image_path` en metadata)
      siguen consultándose sin error y sin imagen de página.
- [ ] Si una página individual falla al renderizar/subir, el ingest termina OK con
      el resto de páginas y chunks; el resumen lo menciona.
- [ ] PNG con matrix 1.5; ninguna imagen de página > 5MB en PDFs de prueba normales.

## Cómo probar
1. `pytest tests/` (existentes) deben seguir pasando.
2. Test nuevo en `tests/test_ingesta.py`: dado un PDF de prueba de ≥2 páginas con
   texto distinto por página, verificar que `extraer(...)` devuelve
   `len(paginas_texto) == paginas` y que el mapeo offset→página asigna a un chunk
   conocido la página correcta (podés testear la función de mapeo aislada).
3. Manual end-to-end: levantar API + bot, subir `data/demo/muros_paz.pdf` (o cualquier
   PDF multipágina) desde admin, confirmar PNGs en Storage, preguntar al bot algo
   contenido en una página específica y ver que llega la foto de esa página.
4. Regresión: subir un `.png` y un `.docx`; confirmar ingest OK sin rama de páginas.

## Qué NO hacer
- No modificar `chunker.py`, `retriever.py`, `prompt_builder.py`, `responder.py`,
  `schemas.py` ni `bot/main.py`.
- No hacer OCR ni extraer imágenes embebidas; solo render de página completa.
- No cargar el PDF entero en memoria como imágenes: render y subida página por página,
  liberando cada pixmap antes de la siguiente (VPS 2GB/1vCPU).
- No tocar el formato del `texto` concatenado del extractor (no re-chunkear distinto).
- No agregar render de páginas para Word ni imágenes (no tienen páginas).
- No subir un solo PDF gigante a RAM ni paralelizar; secuencial y simple.
- No agregar config nuevas, feature flags ni capas de compatibilidad.

## Notas para revisión
- Revisor mira: que el ingest NO aborte por una página fallida (try/except por página);
  que el mapeo offset→página sea robusto si `texto.find(chunk.texto)` no matchea
  (cursor + fallback); que documentos viejos sin `page_image_path` no rompan query
  (`.get()` con `None`); que el umbral 0.35 esté aplicado sobre `score_maximo`
  (similitud), no sobre la distancia cruda.
- Recursos VPS: confirmar liberación de pixmaps/`doc.close()`; PDFs de 50+ páginas
  procesan pero el resumen debe mencionar el tamaño/conteo.
- Secrets: ninguno nuevo; reutiliza cliente Supabase existente.
- Entrega: código + `tareas/resumenes/TAREA_016_resumen.md` (qué criterios cumplidos
  y cuáles no, tamaño del PDF de prueba y cantidad de páginas subidas).
