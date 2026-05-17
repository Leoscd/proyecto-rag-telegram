"""Router para endpoint /logs."""
from fastapi import APIRouter, Query
from supabase import Client

from ..schemas import LogResponse
from ...db import get_client


router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[LogResponse])
async def get_logs(
    proyecto_id: int = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    """
    GET /logs — retrieve consultas del dashboard.
    """
    supabase_client: Client = get_client()

    query = supabase_client.table("consultas").select(
        "id, proyecto_id, usuario_telegram, mensaje_original, respuesta_generada, chunks_usados, score_maximo, timestamp"
    )

    if proyecto_id is not None:
        query = query.eq("proyecto_id", proyecto_id)

    result = query.range(offset, offset + limit - 1).execute()

    logs = []
    for row in result.data:
        logs.append(LogResponse(
            id=row["id"],
            proyecto_id=row["proyecto_id"],
            usuario_telegram=row["usuario_telegram"],
            mensaje_original=row["mensaje_original"],
            respuesta_generada=row["respuesta_generada"],
            chunks_usados=row["chunks_usados"] or [],
            score_maximo=row["score_maximo"],
            timestamp=row["timestamp"],
        ))

    return logs