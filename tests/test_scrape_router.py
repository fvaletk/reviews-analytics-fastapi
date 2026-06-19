from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

APP_REVIEW = {
    "external_id": "r1",
    "author": "Alice",
    "rating": 5,
    "title": "Great",
    "body": "Love it",
    "reviewed_at": "2024-01-01T00:00:00Z",
    "store": "app_store",
}

PLAY_REVIEW = {
    "external_id": "p1",
    "author": "Bob",
    "rating": 4,
    "title": None,
    "body": "Good app",
    "reviewed_at": "2024-01-02T00:00:00Z",
}


def test_scrape_both_stores_returns_combined_reviews(mocker):
    mocker.patch(
        "app.routers.scrape.app_store_scraper.fetch_reviews",
        return_value=[APP_REVIEW],
    )
    mocker.patch(
        "app.routers.scrape.play_store_scraper.fetch_reviews",
        return_value=[PLAY_REVIEW],
    )

    response = client.post(
        "/scrape",
        json={"app_store_id": "123456789", "play_store_id": "com.example.app"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["app_store_count"] == 1
    assert data["play_store_count"] == 1
    assert len(data["reviews"]) == 2
    assert data["errors"] == []
    assert data["partial"] is False


def test_scrape_both_stores_tags_play_store_reviews(mocker):
    mocker.patch(
        "app.routers.scrape.app_store_scraper.fetch_reviews",
        return_value=[],
    )
    mocker.patch(
        "app.routers.scrape.play_store_scraper.fetch_reviews",
        return_value=[PLAY_REVIEW],
    )

    response = client.post(
        "/scrape",
        json={"app_store_id": "123456789", "play_store_id": "com.example.app"},
    )

    data = response.json()
    play_reviews = [r for r in data["reviews"] if r.get("store") == "play_store"]
    assert len(play_reviews) == 1


def test_scrape_only_app_store_id_calls_only_app_store(mocker):
    app_mock = mocker.patch(
        "app.routers.scrape.app_store_scraper.fetch_reviews",
        return_value=[APP_REVIEW],
    )
    play_mock = mocker.patch(
        "app.routers.scrape.play_store_scraper.fetch_reviews",
        return_value=[],
    )

    response = client.post("/scrape", json={"app_store_id": "123456789"})

    assert response.status_code == 200
    app_mock.assert_called_once()
    play_mock.assert_not_called()
    data = response.json()
    assert data["app_store_count"] == 1
    assert data["play_store_count"] == 0


def test_scrape_only_play_store_id_calls_only_play_store(mocker):
    app_mock = mocker.patch(
        "app.routers.scrape.app_store_scraper.fetch_reviews",
        return_value=[],
    )
    play_mock = mocker.patch(
        "app.routers.scrape.play_store_scraper.fetch_reviews",
        return_value=[PLAY_REVIEW],
    )

    response = client.post("/scrape", json={"play_store_id": "com.example.app"})

    assert response.status_code == 200
    app_mock.assert_not_called()
    play_mock.assert_called_once()
    data = response.json()
    assert data["play_store_count"] == 1
    assert data["app_store_count"] == 0


def test_scrape_no_store_id_returns_422():
    response = client.post("/scrape", json={"max_reviews": 100})
    assert response.status_code == 422


def test_scrape_partial_true_when_one_scraper_fails(mocker):
    mocker.patch(
        "app.routers.scrape.app_store_scraper.fetch_reviews",
        return_value=[APP_REVIEW],
    )
    mocker.patch(
        "app.routers.scrape.play_store_scraper.fetch_reviews",
        side_effect=Exception("network timeout"),
    )

    response = client.post(
        "/scrape",
        json={"app_store_id": "123456789", "play_store_id": "com.example.app"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["partial"] is True
    assert len(data["errors"]) == 1
    assert "play_store" in data["errors"][0]
    assert data["app_store_count"] == 1
    assert data["play_store_count"] == 0
