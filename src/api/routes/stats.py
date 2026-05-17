"""Router para stats del dashboard."""
from fastapi import APIRouter, Query
from supabase import Client
from datetime import datetime, timedelta

from ...db import get_client


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(proyecto_id: int = Query(None)):
    """
    Estadísticas del dashboard.
    """
    supabase_client: Client = get_client()

    # Total consultas
    query = supabase_client.table("consultas").select("id", count="exact")
    if proyecto_id:
        query = query.eq("proyecto_id", proyecto_id)
    total_result = query.execute()
    total_consultas = total_result.count or 0

    if total_consultas == 0:
        return {
            "total_consultas": 0,
            "score_promedio": 0.0,
            "consultas_sin_respuesta": 0,
            "score_por_dia": [],
            "gaps_documentacion": [],
        }

    # Get all consulta scores
    consultar_query = supabase_client.table("consultas").select("score_maximo, timestamp, mensaje_original")
    if proyecto_id:
        consultar_query = consultar_query.eq("proyecto_id", proyecto_id)
    consultas_result = consultar_query.execute()
    consultas = consultas_result.data or []

    # Score promedio
    score_promedio = sum(c["score_maximo"] for c in consultas) / len(consultas) if consultas else 0

    # Sin respuesta (score < 0.4)
    sin_respuesta = sum(1 for c in consultas if c["score_maximo"] < 0.4)

    # Score por día
    score_por_dia = {}
    for c in consultas:
        ts = c.get("timestamp", "")
        if ts:
            fecha = ts[:10]
            if fecha not in score_por_dia:
                score_por_dia[fecha] = {"scores": [], "total": 0}
            score_por_dia[fecha]["scores"].append(c["score_maximo"])
            score_por_dia[fecha]["total"] += 1

    score_por_dia_list = []
    for fecha, data in sorted(score_por_dia.items()):
        avg = sum(data["scores"]) / len(data["scores"])
        score_por_dia_list.append({
            "fecha": fecha,
            "promedio": avg,
            "total": data["total"],
        })

    # Gaps de documentación (score < 0.4)
    gaps = [
        {
            "mensaje": c["mensaje_original"],
            "score_maximo": c["score_maximo"],
            "timestamp": c.get("timestamp", ""),
        }
        for c in consultas
        if c["score_maximo"] < 0.4
    ]
    gaps = sorted(gaps, key=lambda x: x["score_maximo"])[:10]

    return {
        "total_consultas": total_consultas,
        "score_promedio": score_promedio,
        "consultas_sin_respuesta": sin_respuesta,
        "score_por_dia": score_por_dia_list,
        "gaps_documentacion": gaps,
    }