"""Tests para el retriever (SQL con pgvector)."""
import pytest
from unittest.mock import MagicMock, patch


def test_recuperar_retorna_lista_vacia():
    """Sin chunks en la base, retorna lista vacía."""
    with patch("src.rag.retriever.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # RPC retorna lista vacía
        mock_client.rpc.return_value.execute.return_value.data = []

        from src.rag.retriever import recuperar

        resultado = recuperar([0.1] * 3072, proyecto_id=1, top_k=5)

        assert resultado == []
        mock_client.rpc.assert_called_once()


def test_recuperar_ordena_por_score():
    """Resultados vienen ordenados por score (menor distancia = más similar)."""
    with patch("src.rag.retriever.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # RPC retorna chunks con diferentes scores
        mock_client.rpc.return_value.execute.return_value.data = [
            {"id": 1, "texto": "texto1", "metadata": {}, "score": 0.1},
            {"id": 2, "texto": "texto2", "metadata": {}, "score": 0.5},
        ]

        from src.rag.retriever import recuperar

        resultado = recuperar([0.1] * 3072, proyecto_id=1, top_k=5)

        assert len(resultado) == 2
        assert resultado[0].chunk_id == 1
        assert resultado[1].chunk_id == 2
        # Verificar que score es float
        assert isinstance(resultado[0].score, float)


def test_recuperar_tiene_metadata():
    """Chunks tienen metadata correctamente."""
    with patch("src.rag.retriever.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.rpc.return_value.execute.return_value.data = [
            {"id": 1, "texto": "test", "metadata": {"sector": "norte"}, "score": 0.2}
        ]

        from src.rag.retriever import recuperar

        resultado = recuperar([0.1] * 3072, proyecto_id=1, top_k=5)

        assert resultado[0].metadata["sector"] == "norte"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])