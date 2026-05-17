"""Router para endpoint GET /storage/url - generar URL firmada."""
from fastapi import APIRouter, Query
from supabase import Client

from ...db import get_client


router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/url")
async def get_signed_url(path: str = Query(..., description="Path del archivo en Storage")):
    """
    Genera URL firmada de Supabase Storage (válida 1 hora).
    """
    supabase_client: Client = get_client()

    result = supabase_client.storage.from_("documentos").create_signed_url(
        path=path,
        expires_in=3600,
    )

    return {"url": result["signedURL"]}