import pytest
import json
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings
from app.endpoints.v1.endpoints import get_settings, get_s3_client


def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "LLM Classifier API"
    assert "endpoints" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_metrics_success(mock_s3_client, test_settings):
    """Test successful metrics retrieval."""
    # Setup mock S3 data
    test_data = {"total_conversations": 100, "classified": 85}
    mock_s3_client.put_object(
        Bucket="test-bucket",
        Key="curated/metrics_daily/date=2026-01-03/metrics.json",
        Body=json.dumps(test_data)
    )
    
    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_s3_client] = lambda: mock_s3_client
    
    client = TestClient(app)
    response = client.get("/v1/metrics?date=2026-01-03")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    assert response.json() == test_data


def test_get_metrics_missing_date(client):
    """Test metrics endpoint without date parameter."""
    response = client.get("/v1/metrics")
    assert response.status_code == 422


def test_get_reports_success(mock_s3_client, test_settings):
    """Test successful reports retrieval."""
    # Setup mock S3 data
    test_data = {"status": "completed", "timestamp": "2026-01-03T10:00:00"}
    mock_s3_client.put_object(
        Bucket="test-bucket",
        Key="reports/date=2026-01-03/run_latest.json",
        Body=json.dumps(test_data)
    )
    
    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_s3_client] = lambda: mock_s3_client
    
    client = TestClient(app)
    response = client.get("/v1/reports?date=2026-01-03")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    assert response.json() == test_data


def test_get_reports_not_found(mock_s3_client, test_settings):
    """Test reports endpoint with non-existent date."""
    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_s3_client] = lambda: mock_s3_client
    
    client = TestClient(app)
    response = client.get("/v1/reports?date=2099-12-31")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 404
