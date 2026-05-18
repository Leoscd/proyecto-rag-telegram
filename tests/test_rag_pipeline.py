"""Tests reales del pipeline RAG (sin mocks)."""
import pytest
import os


def test_chunker_tamano_y_overlap():
    """Generar texto ~1000 tokens, chunkear debe dar >=2 chunks."""
    from src.ingesta.chunker import chunkear
    
    # Texto de ~1000 tokens con palabras repetidas para forzar overlap real
    texto = " ".join(["construccion obra revoque mortero mamposteria hierro cemento arena"] * 60)
    chunks = chunkear(texto, {"documento_id": 1, "proyecto_id": 1, "tipo": "manual", "sector": None, "nombre_documento": "test", "es_imagen": False, "ruta_archivo": ""})
    
    assert len(chunks) >= 2, f"Esperado >=2 chunks, got {len(chunks)}"
    
    # Verificar tokens en rango [400, 520] (salvo último)
    for i, chunk in enumerate(chunks[:-1]):
        assert 400 <= chunk.tokens <= 520, f"Chunk {i} tokens {chunk.tokens} fuera de rango"
    
    # Verificar overlap real: el mayor sufijo de chunk0 que es prefijo de chunk1 debe ser ~50 palabras
    if len(chunks) >= 2:
        tokens0 = chunks[0].texto.split()
        tokens1 = chunks[1].texto.split()

        overlap_count = 0
        min_len = min(len(tokens0), len(tokens1))
        for k in range(min_len, 0, -1):
            if tokens0[-k:] == tokens1[:k]:
                overlap_count = k
                break

        assert 35 <= overlap_count <= 65, (
            f"Overlap esperado [35,65] palabras, got {overlap_count}. "
            f"Fin chunk0: {tokens0[-10:]} | Inicio chunk1: {tokens1[:10]}"
        )


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY no configurada"
)
def test_embedder_dimension():
    """Embedding debe tener 3072 dims y no ser todo ceros."""
    from openai import OpenAI
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input="texto de prueba",
    )
    
    vector = response.data[0].embedding
    assert len(vector) == 3072, f"Esperado 3072, got {len(vector)}"
    assert any(abs(x) > 0 for x in vector), "Embedding es todo ceros"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") or not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"),
    reason="OPENAI_API_KEY, SUPABASE_URL o SUPABASE_KEY no configuradas"
)
def test_retriever_estructura():
    """Retrieval debe retornar estructura correcta."""
    from openai import OpenAI
    from src.rag.retriever import recuperar
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Embeddear "muros"
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input="muros",
    )
    query_emb = response.data[0].embedding
    
    chunks = recuperar(query_emb, proyecto_id=1, top_k=5)
    
    # Verificar estructura (si hay datos)
    if not chunks:
        pytest.skip("No hay chunks en proyecto_id=1")
    
    for chunk in chunks:
        assert isinstance(chunk.chunk_id, int), f"chunk_id debe ser int, got {type(chunk.chunk_id)}"
        assert isinstance(chunk.texto, str) and chunk.texto, "texto debe ser str no vacío"
        assert isinstance(chunk.metadata, dict), "metadata debe ser dict"
        assert isinstance(chunk.score, float), "score debe ser float"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") or not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"),
    reason="OPENAI_API_KEY, SUPABASE_URL o SUPABASE_KEY no configuradas"
)
def test_score_semantica():
    """Similitud debe estar en [0,1] y ser > 0.9 para match perfecto."""
    from openai import OpenAI
    from src.rag.retriever import recuperar
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Embeddear "muros" (query real)
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input="muros",
    )
    query_emb = response.data[0].embedding
    
    chunks = recuperar(query_emb, proyecto_id=1, top_k=1)
    
    if not chunks:
        pytest.skip("No hay chunks en proyecto_id=1")
    
    # Usar el texto COMPLETO del chunk (no [:100])
    texto_chunk = chunks[0].texto
    
    # Re-embeddear el texto completo y recuperar
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=texto_chunk,
    )
    query_emb = response.data[0].embedding
    
    recovered = recuperar(query_emb, proyecto_id=1, top_k=1)
    
    if not recovered:
        pytest.skip("No se pudo recuperar")
    
    # Similitud = 1 - distancia
    distancia = recovered[0].score
    similitud = 1.0 - distancia
    
    assert 0 <= similitud <= 1, f"Similitud fuera de rango: {similitud}"
    assert similitud > 0.9, f"Similitud muy baja: {similitud}"


def test_prompt_builder_incluye_contexto():
    """Prompt debe incluir texto y query."""
    from src.rag.prompt_builder import construir_prompt
    from src.rag.retriever import ChunkRecuperado
    
    # Chunk de prueba con similitud alta - usar marcador único
    chunk = ChunkRecuperado(
        chunk_id=1,
        texto="XJ7QZ_marcador_unico_de_chunk_para_test",
        score=0.3,  # distancia = 0.3 → similitud = 0.7
        metadata={"nombre_documento": "test", "sector": "norte", "tipo": "manual"},
    )
    
    prompt, contexto_pobre = construir_prompt("muros", [chunk])
    
    assert "muros" in prompt, "Query debe estar en prompt"
    assert "XJ7QZ_marcador_unico_de_chunk_para_test" in prompt, "Texto del chunk debe estar en prompt (no solo nombre_documento)"
    assert contexto_pobre is False, "Con similitud 0.7 > 0.35 no debe ser pobre"
    
    # Chunk con similitud baja
    chunk_bajo = ChunkRecuperado(
        chunk_id=2,
        texto="otro texto",
        score=0.9,  # distancia = 0.9 → similitud = 0.1
        metadata={"nombre_documento": "test", "sector": "sur", "tipo": "especificacion"},
    )
    
    _, contexto_pobre_bajo = construir_prompt("muros", [chunk_bajo])
    
    assert contexto_pobre_bajo is True, "Con similitud 0.1 < 0.35 debe ser pobre"
    
    # Lista vacía
    _, contexto_vacio = construir_prompt("muros", [])
    assert contexto_vacio is True, "Lista vacía debe ser contexto_pobre"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") or not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"),
    reason="OPENAI_API_KEY, SUPABASE_URL o SUPABASE_KEY no configuradas"
)
def test_end_to_end_query():
    """Test end-to-end con /query."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    client = TestClient(app)
    
    response = client.post(
        "/query",
        json={
            "proyecto_id": 1,
            "mensaje": "muros",
            "usuario_telegram": "test_pytest",
        }
    )
    
    assert response.status_code == 200, f"HTTP {response.status_code}"
    
    data = response.json()
    score_maximo = data.get("score_maximo", 0)
    
    if score_maximo > 0:
        # Si hay datos, la respuesta NO debe ser ninguna de las frases de "sin información"
        assert data.get("respuesta") not in [
            "No encontré documentos relevantes para esta consulta.",
            "No tengo informacion sobre esto en los documentos disponibles.",
        ], "No debe devolver frase de sin información cuando hay score > 0"
    else:
        # Si no hay datos, debe devolver alguna de las frases reales
        assert data.get("respuesta") in [
            "No encontré documentos relevantes para esta consulta.",
            "No tengo informacion sobre esto en los documentos disponibles.",
        ], "Debe devolver frase de sin información cuando no hay chunks"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])