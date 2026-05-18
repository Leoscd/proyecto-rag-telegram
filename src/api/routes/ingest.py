"""Router para endpoint /ingest."""
import fitz  # PyMuPDF
import tempfile
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from supabase import Client

from ..schemas import IngestResponse
from ...ingesta import (
    extraer,
    chunkear,
    embeder_y_guardar,
    DocumentoExtraido,
    Chunk,
)
from ...config import get_settings_lazy
from ...db import get_client


router = APIRouter(prefix="/ingest", tags=["ingesta"])

TIPOS_VALIDOS = {"manual", "especificacion", "plano", "protocolo", "cronograma"}


@router.post("", response_model=IngestResponse)
async def ingest_doc(
    proyecto_id: int = Form(...),
    nombre: str = Form(...),
    tipo: str = Form(...),
    sector: str = Form(""),
    archivo: UploadFile = File(...),
):
    """
    Orchestras el pipeline de ingesta:
    1. Guarda en Storage
    2. Extrae texto
    3. Chunkea / chunk sintético si es imagen
    4. Render páginas PNG (solo PDF con texto)
    5. Mapeo chunk→página
    6. Embedder + guardado
    """
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(422, f"Tipo inválido. Usar: {', '.join(TIPOS_VALIDOS)}")

    settings = get_settings_lazy()
    supabase_client: Client = get_client()
    bucket_name = "documentos"

    tmp_path = None
    try:
        # 1. Guardar archivo temporalmente
        suffix = Path(archivo.filename or nombre).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            contenido = await archivo.read()
            tmp.write(contenido)
            tmp_path = tmp.name

        # 2. Subir a Supabase Storage
        path_storage = f"{proyecto_id}/{nombre}"
        supabase_client.storage.from_(bucket_name).upload(
            path=path_storage,
            file=contenido,
            file_options={"content-type": archivo.content_type or "application/octet-stream"},
        )

        # 3. Extraer texto
        extractor_result: DocumentoExtraido = extraer(tmp_path)

        # 4. Insertar en tabla documentos
        doc_insert = {
            "proyecto_id": proyecto_id,
            "nombre": nombre,
            "tipo": tipo,
            "sector": sector or None,
            "ruta_archivo": path_storage,
            "texto_extraido": extractor_result.texto if not extractor_result.es_imagen else "",
        }
        doc_response = supabase_client.table("documentos").insert(doc_insert).execute()
        documento_id = doc_response.data[0]["id"]

        chunks_generados = 0

        # 5. Si no es imagen → chunkear + embedder
        if not extractor_result.es_imagen:
            metadata_base = {
                "documento_id": documento_id,
                "proyecto_id": proyecto_id,
                "tipo": tipo,
                "sector": sector or None,
                "nombre_documento": nombre,
                "es_imagen": False,
                "ruta_archivo": path_storage,
            }
            chunks = chunkear(extractor_result.texto, metadata_base)

            # --- NUEVO: Render páginas PNG para PDFs ---
            pagina_a_path: dict[int, str] = {}
            if suffix.lower() == '.pdf' and extractor_result.paginas_texto:
                try:
                    # Abrir PDF para render
                    with open(tmp_path, 'rb') as f:
                        pdf_bytes = f.read()
                    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                    for i in range(len(pdf_doc)):
                        try:
                            # Render página como PNG
                            pix = pdf_doc[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                            png_bytes = pix.tobytes("png")

                            n = i + 1  # página 1-indexed
                            path_png = f"{proyecto_id}/{documento_id}/paginas/pagina_{n}.png"

                            supabase_client.storage.from_(bucket_name).upload(
                                path=path_png,
                                file=png_bytes,
                                file_options={"content-type": "image/png"},
                            )
                            pagina_a_path[n] = path_png
                        except Exception as e:
                            print(f"WARN render página {n}: {e}")
                        finally:
                            if i < len(pdf_doc):
                                pdf_doc[i] = None  # Liberar memoria

                    pdf_doc.close()

                    # --- Mapeo chunk → página por offset ---
                    if pagina_a_path and extractor_result.paginas_texto:
                        # Calcular offsets donde empieza cada página en el texto concatenado
                        offsets_paginas = []
                        texto_concatenado = extractor_result.texto
                        for i, texto_pag in enumerate(extractor_result.paginas_texto):
                            # Buscar el marcador "--- Página N ---" y luego el inicio del texto
                            marcador = f"--- Página {i+1} ---"
                            idx = texto_concatenado.find(marcador)
                            if idx >= 0:
                                # El offset es donde termina el marcador + newline
                                offset = idx + len(marcador) + 2  # +2 por los \n\n
                                offsets_paginas.append(offset)

                        # Para cada chunk, determinar a qué página pertenece
                        cursor = 0
                        for chunk in chunks:
                            # Buscar offset de inicio del chunk en el texto
                            offset_chunk = texto_concatenado.find(chunk.texto, cursor)
                            if offset_chunk < 0:
                                offset_chunk = cursor  # fallback: usar último offset conocido

                            # La página del chunk es la mayor página cuyo offset ≤ offset_chunk
                            pagina_del_chunk = None
                            for pg, offset_pg in enumerate(offsets_paginas, start=1):
                                if offset_pg <= offset_chunk:
                                    pagina_del_chunk = pg
                                else:
                                    break

                            if pagina_del_chunk and pagina_del_chunk in pagina_a_path:
                                chunk.metadata["page_image_path"] = pagina_a_path[pagina_del_chunk]

                            cursor = offset_chunk

                except Exception as e:
                    print(f"WARN render/subida páginas PDF: {e}")

            # --- FIN render páginas ---

            chunks_generados = embeder_y_guardar(chunks, documento_id, proyecto_id)

            # Actualizar texto_extraido
            supabase_client.table("documentos").update(
                {"texto_extraido": extractor_result.texto}
            ).eq("id", documento_id).execute()
        else:
            # Es imagen → crear chunk sintético con texto de búsqueda
            texto_busqueda = f"Plano: {nombre}. Sector: {sector or 'general'}. Tipo: {tipo}."
            chunk_sintetico = Chunk(
                texto=texto_busqueda,
                tokens=len(texto_busqueda.split()),
                indice=0,
                metadata={
                    "documento_id": documento_id,
                    "proyecto_id": proyecto_id,
                    "tipo": tipo,
                    "sector": sector or None,
                    "nombre_documento": nombre,
                    "es_imagen": True,
                    "ruta_archivo": path_storage,
                },
            )
            chunks_generados = embeder_y_guardar([chunk_sintetico], documento_id, proyecto_id)

        return IngestResponse(
            documento_id=documento_id,
            nombre=nombre,
            chunks_generados=chunks_generados,
            es_imagen=extractor_result.es_imagen,
            status="ok",
        )

    except Exception as e:
        print(f"ERROR en /ingest: {e}")
        raise HTTPException(500, "Error procesando el documento")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)