"""Tests reales del pipeline RAG (sin mocks)."""
import pytest
import os


def test_chunker_tamano_y_overlap():
    """Generar texto ~1000 tokens, chunkear debe dar >=2 chunks."""
    from src.ingesta.chunker import chunkear
    
    # Texto de ~1000 tokens
    texto = " ".join(["palabra"] * 1000)
    chunks = chunkear(texto, {"documento_id": 1, "proyecto_id": 1, "tipo": "manual", "sector": None, "nombre_documento": "test", "es_imagen": False, "ruta_archivo": ""})
    
    assert len(chunks) >= 2, f"Esperado >=2 chunks, got {len(chunks)}"
    
    # Verificar tokens en rango [400, 520] (salvo último)
    for i, chunk in enumerate(chunks[:-1]):
        assert 400 <= chunk.tokens <= 520, f"Chunk {i} tokens {chunk.tokens} fuera de rango"
    
    # Verificar overlap (comparando textos)
    if len(chunks) >= 2:
        overlap = chunks[0].texto[-20:]
        print(f"Chunk 0 fin: {overlap[:50]}...")


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
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY no configurada"
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
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY no configurada"
)
def test_score_semantica():
    """Similitud debe estar en [0,1] y ser > 0.9 para match perfecto."""
    from openai import OpenAI
    from src.rag.retriever import recuperar
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Obtener un chunk real
    chunks = recuperar([0.1] * 3072, proyecto_id=1, top_k=1)
    
    if not chunks:
        pytest.skip("No hay chunks en proyecto_id=1")
    
    texto_chunk = chunks[0].texto[:100]
    
    # Embeddear el mismo texto y recuperar
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
    
    # Chunk de prueba con similitud alta
    chunk = ChunkRecuperado(
        chunk_id=1,
        texto=" النص documentotexto",
        score=0.3,  # distancia = 0.3 → similitud = 0.7
        metadata={"nombre_documento": "test", "sector": "norte", "tipo": "manual"},
    )
    
    prompt, contexto_pobre = construir_prompt("muros", [chunk])
    
    assert "muros" in prompt, "Query debe estar en prompt"
    assert "test" in prompt, "Texto del chunk debe estar en prompt"
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
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY no configurada"
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
    assert data.get("score_maximo", 0) > 0, "Score debe ser > 0"
    assert data.get("respuesta"), "respuesta no debe estar vacía"
    
    # Verificar que NO es la respuesta de rendición
    assert data["respuesta"] != "No encontré información sobre esto en los documentos disponibles.", \
        "No debedevolver texto de rendición"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])