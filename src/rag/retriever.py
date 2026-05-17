"""Retriever: búsqueda vectorial en Supabase (SQL con pgvector)."""
from dataclasses import dataclass
from supabase import Client

from ..config import get_settings_lazy
from ..db import get_client


@dataclass
class ChunkRecuperado:
    """Chunk recuperado de la base de conocimiento."""
    chunk_id: int
    texto: str
    score: float  # distancia coseno (menor = más similar)
    metadata: dict


def recuperar(
    query_embedding: list[float],
    proyecto_id: int,
    top_k: int = 5,
) -> list[ChunkRecuperado]:
    """
    Busca los top_k chunks más similares usando distancia coseno via RPC SQL.
    Filtra por proyecto_id.
    """
    supabase_client: Client = get_client()

    # Convertir a string formato pgvector: "[0.1, 0.2, ...]"
    vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Llamar función RPC SQL
    result = supabase_client.rpc(
        "buscar_chunks_similares",
        {
            "query_vector": vector_str,
            "pid": proyecto_id,
            "top_k": top_k,
        }
    ).execute()

    if not result.data:
        return []

    chunks = []
    for row in result.data:
        chunks.append(
            ChunkRecuperado(
                chunk_id=row["id"],
                texto=row["texto"],
                score=float(row["score"]),
                metadata=row["metadata"] or {},
            )
        )

    return chunks