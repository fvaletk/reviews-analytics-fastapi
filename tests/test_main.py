"""
Tests for main.py — BRA-24: health check route and Swagger UI availability.

Acceptance criteria covered:
- GET /health returns {"status": "ok"}
- GET /docs returns FastAPI's auto-generated Swagger UI (HTTP 200)

Skipped criterion:
- `docker compose up` starts the scraper service — Docker lifecycle is not unit-testable
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


def test_docs_returns_200():
    response = client.get("/docs")
    assert response.status_code == 200


def test_docs_returns_html():
    response = client.get("/docs")
    assert "text/html" in response.headers["content-type"]
