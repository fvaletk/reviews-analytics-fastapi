# Skill: pytest-patterns

## Setup Assumptions

- `pytest`, `pytest-mock`, `httpx` are in `requirements.txt`
- FastAPI's `TestClient` is used for endpoint tests

## File Locations

```
tests/
  test_app_store_scraper.py
  test_play_store_scraper.py
  test_scrape_router.py
```

## Endpoint Tests (TestClient)

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_scrape_returns_reviews(mocker):
    mocker.patch(
        "app.routers.scrape.app_store_scraper.fetch_reviews",
        return_value=[{"external_id": "1", "store": "app_store", "rating": 5, "body": "Great"}]
    )
    mocker.patch(
        "app.routers.scrape.play_store_scraper.fetch_reviews",
        return_value=[]
    )

    response = client.post("/scrape", json={"app_store_id": "123456789"})

    assert response.status_code == 200
    data = response.json()
    assert data["app_store_count"] == 1
    assert data["partial"] is False

def test_scrape_requires_at_least_one_store_id():
    response = client.post("/scrape", json={"max_reviews": 100})
    assert response.status_code == 422
```

## Unit Tests (services)

```python
# test_app_store_scraper.py
from unittest.mock import patch, MagicMock
from app.services.app_store_scraper import fetch_reviews

def test_fetch_reviews_returns_correct_shape():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "feed": {
            "entry": [
                {
                    "id": {"label": "abc123"},
                    "author": {"name": {"label": "Alice"}},
                    "im:rating": {"label": "5"},
                    "title": {"label": "Great app"},
                    "content": {"label": "Love it"},
                    "updated": {"label": "2024-01-01T00:00:00-07:00"}
                }
            ]
        }
    }

    with patch("httpx.get", return_value=mock_response):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert len(reviews) == 1
    assert reviews[0]["external_id"] == "abc123"
    assert reviews[0]["rating"] == 5
    assert reviews[0]["store"] == "app_store"

def test_fetch_reviews_returns_empty_on_network_error():
    with patch("httpx.get", side_effect=Exception("timeout")):
        reviews = fetch_reviews("123456", "us")
    assert reviews == []
```

## Rules

- Always mock external HTTP calls — never make real network requests in tests
- Mock at the point of use, not at the import — use `mocker.patch("app.routers.scrape.app_store_scraper.fetch_reviews")` not `mocker.patch("app.services.app_store_scraper.fetch_reviews")` when testing the router
- One assertion per test where practical
- Test the failure path — empty list on error, `partial: true` on partial failure
- No `time.sleep()` or real delays in tests
