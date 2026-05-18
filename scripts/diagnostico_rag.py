#!/usr/bin/env python3
"""Script de diagnóstico del pipeline RAG."""
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from src.db import get_client
from src.rag.retriever import recuperar, ChunkRecuperado
from src.rag.prompt_builder import construir_prompt
from src.rag.responder import responder


def diagnostico():
    """Ejecuta diagnóstico completo."""
    print("=" * 60)
    print("DIAGNÓSTICO RAG - RAG-Obras")
    print("=" * 60)
    
    # Verificar config
    try:
        from src.config import get_settings
        settings = get_settings()
    except ValueError as e:
        print(f"\n❌ ERROR: Faltan variables de entorno: {e}")
        sys.exit(1)
    
    proyecto_id = 1
    query = "muros mampostería"
    
    # === PARTE 1: CHUNKS ===
    print("\n" + "=" * 60)
    print("1. CHUNKS DEL PROYECTO")
    print("=" * 60)
    
    try:
        supabase = get_client()
        result = supabase.table("chunks").select("id, texto, metadata").eq("proyecto_id", proyecto_id).execute()
        chunks_db = result.data or []
        
        if not chunks_db:
            print("⚠️  No hay chunks en proyecto_id=1")
        else:
            for c in chunks_db:
                texto_preview = c.get("texto", "")[:100]
                meta = c.get("metadata", {})
                print(f"  ID {c['id']}: {texto_preview}...")
                print(f"    Metadata: {meta}")
    except Exception as e:
        print(f"❌ Error consultando chunks: {e}")
    
    # === PARTE 2: RETRIEVAL ===
    print("\n" + "=" * 60)
    print("2. RETRIEVAL")
    print("=" * 60)
    
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        print(f"  Query: '{query}'")
        
        # Embeddear
        emb_response = client.embeddings.create(
            model="text-embedding-3-large",
            input=query,
        )
        query_emb = emb_response.data[0].embedding
        
        # Recuperar
        chunks = recuperar(query_emb, proyecto_id=proyecto_id, top_k=5)
        
        if not chunks:
            print("  ⚠️  No se recuperaron chunks")
        else:
            print(f"  Top {len(chunks)} chunks:")
            for i, c in enumerate(chunks):
                distancia = c.score
                similitud = 1.0 - distancia
                texto_preview = c.texto[:100]
                print(f"  [{i+1}] ID={c.chunk_id} | distancia={distancia:.3f} | similitud={similitud:.3f}")
                print(f"      texto: {texto_preview}...")
    except Exception as e:
        print(f"❌ Error en retrieval: {e}")
    
    # === PARTE 3: PROMPT ===
    print("\n" + "=" * 60)
    print("3. PROMPT CONSTRUIDO")
    print("=" * 60)
    
    try:
        prompt, contexto_pobre = construir_prompt(query, chunks)
        print(f"  Contexto pobre: {contexto_pobre}")
        print(f"  --- Prompt ---")
        print(prompt[:1000])
        if len(prompt) > 1000:
            print("  ... (truncado)")
    except Exception as e:
        print(f"❌ Error construyendo prompt: {e}")
    
    # === PARTE 4: RESPUESTA LLM ===
    print("\n" + "=" * 60)
    print("4. RESPUESTA LLM")
    print("=" * 60)
    
    try:
        respuesta = responder(prompt, contexto_pobre)
        print(f"  Respuesta: {respuesta[:500]}")
        if len(respuesta) > 500:
            print("  ... (truncado)")
    except Exception as e:
        print(f"❌ Error en responder: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 60)


if __name__ == "__main__":
    diagnostico()