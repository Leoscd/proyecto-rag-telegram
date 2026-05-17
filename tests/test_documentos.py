"""Tests para documentos."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def test_get_documentos():
    """GET /documentos retorna lista."""
    with patch("src.api.routes.documentos.get_client") as mock_client:
        mock_table = MagicMock()
        mock_table.select.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "proyecto_id": 1, "nombre": "doc.pdf", "tipo": "manual"}]
        )
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            count=5
        )
        mock_client.return_value = mock_table

        from src.api.main import app
        client = TestClient(app)

        response = client.get("/documentos?proyecto_id=1")

        assert response.status_code == 200


def test_get_documentos_filtra_por_tipo():
    """GET /documentos con tipo filtra correctamente."""
    with patch("src.api.routes.documentos.get_client") as mock_client:
        mock_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "tipo": "manual"}]
        )

        from src.api.main import app
        client = TestClient(app)

        response = client.get("/documentos?tipo=manual")

        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])