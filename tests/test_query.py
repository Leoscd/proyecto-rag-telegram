"""Tests para el endpoint /query."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def test_query_con_chunks_retorna_respuesta():
    """POST /query con chunks recuperados retorna respuesta 200."""
    with patch("src.api.routes.query.get_settings_lazy") as mock_settings, \
         patch("src.api.routes.query.OpenAI") as mock_openai, \
         patch("src.api.routes.query.get_client") as mock_client, \
         patch("src.api.routes.query.recuperar") as mock_recuperar, \
         patch("src.api.routes.query.construir_prompt") as mock_prompt, \
         patch("src.api.routes.query.responder") as mock_responder:
        
        # Setup mocks
        mock_settings.return_value.openai_api_key = "sk-test"
        
        # OpenAI embedding mock
        mock_ai = MagicMock()
        mock_openai.return_value = mock_ai
        mock_ai.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1] * 3072)]
        )
        
        # Retrieval mock
        from src.rag.retriever import ChunkRecuperado
        mock_recuperar.return_value = [
            ChunkRecuperado(chunk_id=1, texto="texto relevante", score=0.3, metadata={"nombre_documento": "doc"})
        ]
        
        # Prompt builder mock
        mock_prompt.return_value = ("prompt", False)
        
        # Responder mock
        mock_responder.return_value = "Respuesta del modelo"
        
        # Client mock
        mock_client.return_value = MagicMock()
        
        from src.api.main import app
        client = TestClient(app)
        
        response = client.post(
            "/query",
            json={"proyecto_id": 1, "mensaje": "pregunta test", "usuario_telegram": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "respuesta" in data
        assert data["respuesta"] == "Respuesta del modelo"


def test_query_sin_chunks_retorna_contexto_pobre():
    """POST /query sin chunks retorna contexto_pobre=True y score=0.0."""
    with patch("src.api.routes.query.get_settings_lazy") as mock_settings, \
         patch("src.api.routes.query.OpenAI") as mock_openai, \
         patch("src.api.routes.query.get_client") as mock_client, \
         patch("src.api.routes.query.recuperar") as mock_recuperar:
        
        mock_settings.return_value.openai_api_key = "sk-test"
        
        mock_ai = MagicMock()
        mock_openai.return_value = mock_ai
        mock_ai.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1] * 3072)]
        )
        
        # Sin chunks encontrados
        mock_recuperar.return_value = []
        
        mock_client.return_value = MagicMock()
        
        from src.api.main import app
        client = TestClient(app)
        
        response = client.post(
            "/query",
            json={"proyecto_id": 1, "mensaje": "pregunta", "usuario_telegram": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["contexto_pobre"] is True
        assert data["score_maximo"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])