"""Tests para proyectos."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def test_get_proyectos():
    """GET /proyectos retorna lista."""
    with patch("src.api.routes.proyectos.get_client") as mock_client:
        mock_client.return_value.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "nombre": "Obra 1", "descripcion": "Test", "activo": True}]
        )

        from src.api.main import app
        client = TestClient(app)

        response = client.get("/proyectos")

        assert response.status_code == 200
        assert len(response.json()) > 0


def test_post_proyectos_valido():
    """POST /proyectos con nombre válido retorna 201."""
    with patch("src.api.routes.proyectos.get_client") as mock_client:
        mock_client.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "nombre": "Nueva Obra", "activo": True}]
        )

        from src.api.main import app
        client = TestClient(app)

        response = client.post(
            "/proyectos",
            json={"nombre": "Nueva Obra", "descripcion": "Test"}
        )

        assert response.status_code == 201
        assert response.json()["nombre"] == "Nueva Obra"


def test_post_proyectos_vacio_retorna_422():
    """POST /proyectos con nombre vacío retorna 422."""
    from src.api.main import app
    client = TestClient(app)

    response = client.post(
        "/proyectos",
        json={"nombre": ""}
    )

    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])