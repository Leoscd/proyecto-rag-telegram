"""Router para endpoint /query."""
from openai import OpenAI
from fastapi import APIRouter, HTTPException
from supabase import Client

from ..schemas import QueryRequest, QueryResponse, ErrorResponse
from ...config import get_settings_lazy
from ...db import get_client
from ...rag import recuperar, construir_prompt, ChunkRecuperado
from ...rag.responder import responder


router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_doc(
    request: QueryRequest,
):
    """
    Pipeline query:
    1. Embedding del mensaje
    2. Retrieval top-5
    3. Prompt builder
    4. MiniMax response
    5. Log en tabla consultas
    """
    settings = get_settings_lazy()
    openai_client = OpenAI(api_key=settings.openai_api_key)
    supabase_client: Client = get_client()

    try:
        # 1. Generar embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=request.mensaje,
        )
        query_embedding = embedding_response.data[0].embedding

        # 2. Retrieval
        chunks: list[ChunkRecuperado] = recuperar(
            query_embedding=query_embedding,
            proyecto_id=request.proyecto_id,
            top_k=5,
        )

        if not chunks:
            return QueryResponse(
                respuesta="No encontré documentos relevantes para esta consulta.",
                chunks_usados=[],
                score_maximo=2.0,
                contexto_pobre=True,
                tiene_imagen=False,
                ruta_imagen=None,
            )

        # 3. Construir prompt
        prompt, contexto_pobre = construir_prompt(request.mensaje, chunks)
        score_maximo = chunks[0].score

        # 4. Responder con MiniMax
        respuesta_texto = responder(prompt, contexto_pobre)

        # 5. Determinar si tiene imagen
        tiene_imagen = False
        ruta_imagen = None
        for chunk in chunks:
            if chunk.metadata.get("es_imagen"):
                tiene_imagen = True
                ruta_imagen = chunk.metadata.get("ruta_archivo")
                break

        chunks_usados = [c.chunk_id for c in chunks]

        # 6. Log en consultas
        supabase_client.table("consultas").insert({
            "proyecto_id": request.proyecto_id,
            "usuario_telegram": request.usuario_telegram,
            "mensaje_original": request.mensaje,
            "respuesta_generada": respuesta_texto,
            "chunks_usados": chunks_usados,
            "score_maximo": score_maximo,
        }).execute()

        return QueryResponse(
            respuesta=respuesta_texto,
            chunks_usados=chunks_usados,
            score_maximo=score_maximo,
            contexto_pobre=contexto_pobre,
            tiene_imagen=tiene_imagen,
            ruta_imagen=ruta_imagen,
        )

    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error procesando consulta: {e}")