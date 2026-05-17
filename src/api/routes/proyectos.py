"""Router para proyectos."""
from fastapi import APIRouter, Query
from supabase import Client

from ..schemas import ProyectoCreate, ProyectoResponse
from ...db import get_client


router = APIRouter(prefix="/proyectos", tags=["proyectos"])


@router.get("", response_model=list[ProyectoResponse])
async def list_proyectos(activo: bool = Query(None)):
    """
    Lista todos los proyectos.
    Opcional: ?activo=true para filtrar solo activos.
    """
    supabase_client: Client = get_client()

    query = supabase_client.table("proyectos").select("*")

    if activo is not None:
        query = query.eq("activo", activo)

    result = query.execute()
    return result.data


@router.post("", response_model=ProyectoResponse, status_code=201)
async def create_proyecto(proyecto: ProyectoCreate):
    """
    Crea un nuevo proyecto.
    """
    if not proyecto.nombre or not proyecto.nombre.strip():
        from fastapi import HTTPException
        raise HTTPException(422, "El nombre no puede estar vacío")

    supabase_client: Client = get_client()

    data = {
        "nombre": proyecto.nombre,
        "descripcion": proyecto.descripcion,
        "fecha_inicio": proyecto.fecha_inicio,
        "activo": True,
    }

    result = supabase_client.table("proyectos").insert(data).execute()
    return result.data[0]