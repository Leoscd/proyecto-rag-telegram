"""Tests para el responder."""
import pytest
from unittest.mock import patch, MagicMock


def test_responder_llama_minimax():
    """Verifica que llama a MiniMax con prompt correcto."""
    with patch("src.rag.responder.get_settings_lazy") as mock_settings, \
         patch("src.rag.responder.httpx.Client") as mock_client:
        
        mock_settings.return_value.minimax_api_key = "sk-test"
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "respuesta de prueba"}}]
        }
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        from src.rag.responder import responder
        
        result = responder("prompt de prueba", contexto_pobre=False)
        
        assert "prueba" in result


def test_responder_runtime_error():
    """Error de API lanza RuntimeError."""
    with patch("src.rag.responder.get_settings_lazy") as mock_settings, \
         patch("src.rag.responder.httpx.Client") as mock_client:
        
        mock_settings.return_value.minimax_api_key = "sk-test"
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.side_effect = Exception("API down")
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        from src.rag.responder import responder
        
        with pytest.raises(RuntimeError):
            responder("prompt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])