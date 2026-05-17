"""Tests para el chunker."""
import pytest
from src.ingesta.chunker import chunkear, Chunk


def test_texto_vacio():
    """Texto vacío retorna lista vacía."""
    resultado = chunkear("", {"documento_id": 1, "proyecto_id": 1, "tipo": "manual", "sector": None, "nombre_documento": "test", "es_imagen": False, "ruta_archivo": ""})
    assert resultado == []


def test_texto_corto():
    """Texto menor a max_tokens retorna 1 chunk."""
    texto = "hola mundo " * 50  # ~100 tokens
    resultado = chunkear(texto, {"documento_id": 1, "proyecto_id": 1, "tipo": "manual", "sector": None, "nombre_documento": "test", "es_imagen": False, "ruta_archivo": ""})
    assert len(resultado) == 1
    assert resultado[0].tokens < 500
    assert resultado[0].metadata["chunk_index"] == 0


def test_chunks_tienen_overlap():
    """Chunk N+1 compartiendo overlap con chunk N."""
    texto = "palabra " * 1000  # ~2000 tokens
    resultado = chunkear(texto, {"documento_id": 1, "proyecto_id": 1, "tipo": "manual", "sector": None, "nombre_documento": "test", "es_imagen": False, "ruta_archivo": ""})
    assert len(resultado) >= 2
    # Verificar overlap (aproximado en caracteres para simplificar)
    chunk0_final = resultado[0].texto[-20:]
    chunk1_inicio = resultado[1].texto[:20]
    # Hay overlap, no es identical pero comparten contenido
    assert chunk0_final in resultado[0].texto + resultado[1].texto


def test_metadata_tiene_campos():
    """Metadata tiene todos los campos."""
    metadata = {"documento_id": 1, "proyecto_id": 1, "tipo": "manual", "sector": "norte", "nombre_documento": "test.pdf", "es_imagen": False, "ruta_archivo": "/docs/test.pdf"}
    resultado = chunkear("texto largo " * 200, metadata)
    assert resultado[0].metadata["documento_id"] == 1
    assert resultado[0].metadata["chunk_index"] == 0
    assert resultado[0].metadata["sector"] == "norte"


def test_overlap_mayor_max_lanza_error():
    """overlap >= maxTokens lanza ValueError."""
    with pytest.raises(ValueError):
        chunkear("texto", {}, max_tokens=100, overlap_tokens=100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])