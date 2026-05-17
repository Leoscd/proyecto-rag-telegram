"""Retriever: búsqueda vectorial en Supabase."""
import math
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


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Calcula distancia coseno entre dos vectores."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 2.0  # máximo
    return 1.0 - (dot_product / (norm_a * norm_b))


def recuperar(
    query_embedding: list[float],
    proyecto_id: int,
    top_k: int = 5,
) -> list[ChunkRecuperado]:
    """
    Busca los top_k chunks más similares usando distancia coseno.
    Filtra por proyecto_id.
    """
    supabase_client: Client = get_client()

    # Traer todos los chunks del proyecto ( workaround para MVP)
    result = supabase_client.table("chunks").select(
        "id, texto, metadata, embedding"
    ).eq("proyecto_id", proyecto_id).execute()

    if not result.data:
        return []

    # Calcular scores
    chunks_con_score = []
    for row in result.data:
        if row.get("embedding"):
            score = _cosine_distance(query_embedding, row["embedding"])
            chunks_con_score.append(
                ChunkRecuperado(
                    chunk_id=row["id"],
                    texto=row["texto"],
                    score=score,
                    metadata=row.get("metadata") or {},
                )
            )

    # Ordenar por score y tomar top_k
    chunks_con_score.sort(key=lambda x: x.score)
    return chunks_con_score[:top_k]