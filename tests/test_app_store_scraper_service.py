"""
Tests for app/services/app_store_scraper.py — BRA-25.

Acceptance criteria covered:
1. Function exists and returns correctly shaped dicts (field mapping for all 7 fields)
2. Stops paginating when results are exhausted (pagination stops on empty page)
3. Respects max_reviews cap
4. Returns empty list (not exception) on network error
5. HTTP error (raise_for_status) returns partial results — only page-1 reviews
"""

from unittest.mock import patch, MagicMock, call

import httpx

from app.services.app_store_scraper import fetch_reviews


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    id_label="rev-001",
    author_name="Alice",
    rating_label="5",
    title_label="Great app",
    content_label="Love it",
    updated_label="2024-01-01T00:00:00-07:00",
):
    return {
        "id": {"label": id_label},
        "author": {"name": {"label": author_name}},
        "im:rating": {"label": rating_label},
        "title": {"label": title_label},
        "content": {"label": content_label},
        "updated": {"label": updated_label},
    }


def _make_response(entries):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"feed": {"entry": entries}}
    return mock_response


def _make_empty_response():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"feed": {}}
    return mock_response


# ---------------------------------------------------------------------------
# 1. Field mapping — all 7 fields
# ---------------------------------------------------------------------------

def test_fetch_reviews_returns_list():
    entry = _make_entry()
    mock_resp = _make_response([entry])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert isinstance(reviews, list)


def test_fetch_reviews_external_id_mapped():
    mock_resp = _make_response([_make_entry(id_label="abc123")])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert reviews[0]["external_id"] == "abc123"


def test_fetch_reviews_author_mapped():
    mock_resp = _make_response([_make_entry(author_name="Bob")])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert reviews[0]["author"] == "Bob"


def test_fetch_reviews_rating_mapped_as_int():
    mock_resp = _make_response([_make_entry(rating_label="4")])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert reviews[0]["rating"] == 4
    assert isinstance(reviews[0]["rating"], int)


def test_fetch_reviews_title_mapped():
    mock_resp = _make_response([_make_entry(title_label="Awesome")])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert reviews[0]["title"] == "Awesome"


def test_fetch_reviews_body_mapped():
    mock_resp = _make_response([_make_entry(content_label="Really love this")])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert reviews[0]["body"] == "Really love this"


def test_fetch_reviews_reviewed_at_mapped():
    mock_resp = _make_response([_make_entry(updated_label="2024-06-01T12:00:00-07:00")])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert reviews[0]["reviewed_at"] == "2024-06-01T12:00:00-07:00"


def test_fetch_reviews_store_is_app_store():
    mock_resp = _make_response([_make_entry()])

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[mock_resp, _make_empty_response()]):
        reviews = fetch_reviews("123456", "us", max_reviews=50)

    assert reviews[0]["store"] == "app_store"


# ---------------------------------------------------------------------------
# 2. Pagination stops when page returns no entries
# ---------------------------------------------------------------------------

def test_pagination_stops_on_empty_entry_list():
    page1_resp = _make_response([_make_entry(id_label="r1"), _make_entry(id_label="r2")])
    page2_resp = _make_response([])

    mock_get = MagicMock(side_effect=[page1_resp, page2_resp])

    with patch("app.services.app_store_scraper.httpx.get", mock_get):
        reviews = fetch_reviews("123456", "us", max_reviews=500)

    assert mock_get.call_count == 2
    assert len(reviews) == 2


def test_pagination_stops_on_missing_entry_key():
    page1_resp = _make_response([_make_entry(id_label="r1")])
    page2_resp = _make_empty_response()

    mock_get = MagicMock(side_effect=[page1_resp, page2_resp])

    with patch("app.services.app_store_scraper.httpx.get", mock_get):
        reviews = fetch_reviews("123456", "us", max_reviews=500)

    assert mock_get.call_count == 2
    assert len(reviews) == 1


# ---------------------------------------------------------------------------
# 3. max_reviews cap
# ---------------------------------------------------------------------------

def test_max_reviews_cap_not_exceeded():
    entries_page = [_make_entry(id_label=f"r{i}") for i in range(10)]
    page_resp = _make_response(entries_page)

    responses = [_make_response(list(entries_page)) for _ in range(10)]

    with patch("app.services.app_store_scraper.httpx.get", side_effect=responses):
        reviews = fetch_reviews("123456", "us", max_reviews=5)

    assert len(reviews) <= 5


def test_max_reviews_exact_cap():
    entries = [_make_entry(id_label=f"r{i}") for i in range(20)]
    page1_resp = _make_response(entries)
    page2_resp = _make_response(entries)

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[page1_resp, page2_resp]):
        reviews = fetch_reviews("123456", "us", max_reviews=3)

    assert len(reviews) == 3


# ---------------------------------------------------------------------------
# 4. Network error returns empty list (not an exception)
# ---------------------------------------------------------------------------

def test_returns_empty_list_on_generic_exception():
    with patch("app.services.app_store_scraper.httpx.get", side_effect=Exception("timeout")):
        reviews = fetch_reviews("123456", "us")

    assert reviews == []


def test_no_exception_raised_on_network_error():
    with patch("app.services.app_store_scraper.httpx.get", side_effect=Exception("connection refused")):
        try:
            result = fetch_reviews("123456", "us")
            raised = False
        except Exception:
            raised = True

    assert raised is False


# ---------------------------------------------------------------------------
# 5. HTTP error on raise_for_status returns partial results (not empty list)
# ---------------------------------------------------------------------------

def test_http_error_on_page2_returns_page1_results():
    page1_resp = _make_response([_make_entry(id_label="r1"), _make_entry(id_label="r2")])

    page2_resp = MagicMock()
    page2_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found",
        request=MagicMock(),
        response=MagicMock(),
    )

    mock_get = MagicMock(side_effect=[page1_resp, page2_resp])

    with patch("app.services.app_store_scraper.httpx.get", mock_get):
        reviews = fetch_reviews("123456", "us", max_reviews=500)

    assert len(reviews) == 2
    assert reviews[0]["external_id"] == "r1"
    assert reviews[1]["external_id"] == "r2"


def test_http_error_on_page2_does_not_return_empty_list():
    page1_resp = _make_response([_make_entry(id_label="r1")])

    page2_resp = MagicMock()
    page2_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error",
        request=MagicMock(),
        response=MagicMock(),
    )

    with patch("app.services.app_store_scraper.httpx.get", side_effect=[page1_resp, page2_resp]):
        reviews = fetch_reviews("123456", "us", max_reviews=500)

    assert reviews != []
