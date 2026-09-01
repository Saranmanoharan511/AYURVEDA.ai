import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Ayurveda AI Platform API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"


def test_health_endpoint_without_database(client):
    """Test the health endpoint without database connection."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "app_name" in data
    assert "app_version" in data
    assert "environment" in data
    assert "database" in data
