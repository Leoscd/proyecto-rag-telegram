"""Tests para el prompt builder."""
import pytest
from src.rag.prompt_builder import construir_prompt
from src.rag.retriever import ChunkRecuperado


def test_prompt_incluye_anti_alucinacion():
    """Prompt incluye instrucción anti-alucinación."""
    chunks = [
        ChunkRecuperado(1, "texto de prueba", 0.3, {"nombre_documento": "manual", "sector": "norte", "tipo": "manual"})
    ]
    prompt, _ = construir_prompt("como se hace el revoque?", chunks)
    
    assert "No encontré información" in prompt
    assert "No inventes" in prompt


def test_contexto_pobre_cuando_score_alto():
    """contexto_pobre=True cuando mejor score > 1.2."""
    chunks = [
        ChunkRecuperado(1, "texto", 1.5, {"nombre_documento": "doc", "sector": None, "tipo": "manual"})
    ]
    _, contexto_pobre = construir_prompt("query", chunks)
    
    assert contexto_pobre is True


def test_contexto_rico_cuando_score_bajo():
    """contexto_pobre=False cuando score < 1.2."""
    chunks = [
        ChunkRecuperado(1, "texto相关性", 0.3, {"nombre_documento": "doc", "sector": None, "tipo": "manual"})
    ]
    _, contexto_pobre = construir_prompt("query", chunks)
    
    assert contexto_pobre is False


def test_vacio_retorna_contexto_pobre():
    """Lista vacía implica contexto_pobre=True."""
    _, contexto_pobre = construir_prompt("query", [])
    assert contexto_pobre is True


def test_prompt_incluye_metadata():
    """Prompt incluye metadata de cada chunk."""
    chunks = [
        ChunkRecuperado(1, "texto 1", 0.1, {"nombre_documento": "manual", "sector": "norte", "tipo": "manual"}),
        ChunkRecuperado(2, "texto 2", 0.2, {"nombre_documento": "espec", "sector": "sur", "tipo": "especificacion"}),
    ]
    prompt, _ = construir_prompt("query", chunks)
    
    assert "manual" in prompt
    assert "norte" in prompt
    assert "espec" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])