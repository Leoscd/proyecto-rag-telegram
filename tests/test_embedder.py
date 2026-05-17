"""Tests para el embedder (todo mockeado)."""
import pytest
from unittest.mock import patch, MagicMock


def test_embeder_usa_modelo_correcto():
    """Verifica que usa text-embedding-3-large."""
    with patch("src.ingesta.embedder.OpenAI") as mock_ai, \
         patch("src.ingesta.embedder.get_settings_lazy") as mock_settings, \
         patch("src.ingesta.embedder.get_client") as mock_client:
        
        from src.ingesta.embedder import embeder_y_guardar
        from src.ingesta.chunker import Chunk

        # Setup mocks
        mock_settings.return_value.openai_api_key = "sk-test"
        
        mock_ai_instance = MagicMock()
        mock_ai.return_value = mock_ai_instance
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 3072)]
        mock_ai_instance.embeddings.create.return_value = mock_response

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        chunks = [Chunk(texto="test", tokens=1, indice=0, metadata={})]
        
        embeder_y_guardar(chunks, documento_id=1, proyecto_id=1)

        call_args = mock_ai_instance.embeddings.create.call_args
        assert call_args.kwargs["model"] == "text-embedding-3-large"


def test_procesa_en_lotes():
    """Procesa en lotes de batch_size."""
    with patch("src.ingesta.embedder.OpenAI") as mock_ai, \
         patch("src.ingesta.embedder.get_settings_lazy") as mock_settings, \
         patch("src.ingesta.embedder.get_client") as mock_client:
        
        from src.ingesta.embedder import embeder_y_guardar
        from src.ingesta.chunker import Chunk

        mock_settings.return_value.openai_api_key = "sk-test"
        
        mock_ai_instance = MagicMock()
        mock_ai.return_value = mock_ai_instance
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 3072)]
        mock_ai_instance.embeddings.create.return_value = mock_response

        mock_client.return_value = MagicMock()

        # 150 chunks → 2 lotes
        chunks = [Chunk(texto=f"test {i}", tokens=1, indice=i, metadata={}) for i in range(150)]

        embeder_y_guardar(chunks, documento_id=1, proyecto_id=1, batch_size=100)

        assert mock_ai_instance.embeddings.create.call_count == 2


def test_retorna_cantidad_chunks_guardados():
    """Retorna cantidad exacta de chunks guardados."""
    with patch("src.ingesta.embedder.OpenAI") as mock_ai, \
         patch("src.ingesta.embedder.get_settings_lazy") as mock_settings, \
         patch("src.ingesta.embedder.get_client") as mock_client:
        
        from src.ingesta.embedder import embeder_y_guardar
        from src.ingesta.chunker import Chunk

        mock_settings.return_value.openai_api_key = "sk-test"
        
        mock_ai_instance = MagicMock()
        mock_ai.return_value = mock_ai_instance
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 3072)]
        mock_ai_instance.embeddings.create.return_value = mock_response

        mock_client.return_value = MagicMock()

        chunks = [Chunk(texto="test", tokens=1, indice=i, metadata={}) for i in range(10)]

        resultado = embeder_y_guardar(chunks, documento_id=1, proyecto_id=1)

        assert resultado == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])