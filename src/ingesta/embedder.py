"""Embedder: genera embeddings y guarda chunks en Supabase."""
import time
from openai import OpenAI
from supabase import Client

from .chunker import Chunk
from ..config import get_settings_lazy
from ..db import get_client


def embeder_y_guardar(
    chunks: list[Chunk],
    documento_id: int,
    proyecto_id: int,
    batch_size: int = 100,
) -> int:
    """
    Genera embeddings en lotes y los guarda en Supabase.
    Retorna la cantidad de chunks guardados.
    """
    settings = get_settings_lazy()
    openai_client = OpenAI(api_key=settings.openai_api_key)
    supabase_client: Client = get_client()

    if not chunks:
        return 0

    total_chunks = len(chunks)
    total_lotes = (total_chunks + batch_size - 1) // batch_size
    chunks_guardados = 0

    for i in range(0, total_chunks, batch_size):
        lote = i // batch_size + 1
        batch = chunks[i:i + batch_size]
        print(f"Procesando lote {lote}/{total_lotes} ({len(batch)} chunks)...")

        try:
            # Generar embeddings
            textos = [chunk.texto for chunk in batch]
            response = openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=textos,
            )

            embeddings = [item.embedding for item in response.data]

            # Insertar en Supabase
            registros = []
            for chunk, embedding in zip(batch, embeddings):
                registros.append({
                    "documento_id": documento_id,
                    "proyecto_id": proyecto_id,
                    "texto": chunk.texto,
                    "embedding": embedding,
                    "metadata": chunk.metadata,
                })

            supabase_client.table("chunks").insert(registros).execute()
            chunks_guardados += len(batch)

        except Exception as e:
            error_msg = str(e)
            # Rate limit → retry
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                print("Rate limit detectado, esperando 20s y reintentando...")
                time.sleep(20)
                try:
                    response = openai_client.embeddings.create(
                        model="text-embedding-3-large",
                        input=[chunk.texto for chunk in batch],
                    )
                    embeddings = [item.embedding for item in response.data]

                    registros = []
                    for chunk, embedding in zip(batch, embeddings):
                        registros.append({
                            "documento_id": documento_id,
                            "proyecto_id": proyecto_id,
                            "texto": chunk.texto,
                            "embedding": embedding,
                            "metadata": chunk.metadata,
                        })

                    supabase_client.table("chunks").insert(registros).execute()
                    chunks_guardados += len(batch)
                except Exception as retry_error:
                    raise RuntimeError(f"Error al guardar chunks (retry): {retry_error}")
            else:
                raise RuntimeError(f"Error al guardar chunks: {e}")

    return chunks_guardados