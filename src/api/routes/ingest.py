"""Router para endpoint /ingest."""
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
    4. Embedder + guardado
    """
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(422, f"Tipo inválido. Usar: {', '.join(TIPOS_VALIDOS)}")

    settings = get_settings_lazy()
    supabase_client: Client = get_client()
    bucket_name = "documentos"

    tmp_path = None
    try:
        # 1. Guardar archivo temporalmente
        suffix = Path(nombre).suffix
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