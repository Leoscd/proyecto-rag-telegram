"""Router para documentos."""
from fastapi import APIRouter, Query
from supabase import Client
from typing import Optional

from ..schemas import DocumentoResponse
from ...db import get_client


router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.get("", response_model=list[DocumentoResponse])
async def list_documentos(
    proyecto_id: int = Query(None),
    tipo: str = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    """
    Lista documentos.
    Filtros: proyecto_id, tipo.
    """
    supabase_client: Client = get_client()

    query = supabase_client.table("documentos").select("*")

    if proyecto_id is not None:
        query = query.eq("proyecto_id", proyecto_id)

    if tipo:
        query = query.eq("tipo", tipo)

    result = query.range(offset, offset + limit - 1).execute()

    # Agregar chunks_count a cada documento
    docs = result.data or []
    for doc in docs:
        # Contar chunks asociados
        chunks_result = supabase_client.table("chunks").select(
            "id", count="exact"
        ).eq("documento_id", doc["id"]).execute()
        doc["chunks_count"] = chunks_result.count or 0

    return docs