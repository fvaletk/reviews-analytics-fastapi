"""
Tests for app/services/play_store_scraper.py — BRA-26.

Acceptance criteria covered:
1. Function exists and returns correctly shaped dicts (field mapping for all 6 fields)
2. `reviewed_at` is a valid ISO8601 string
3. Mocks `google_play_scraper.reviews` and verifies field mapping and call args
4. Returns empty list (not exception) on library error
5. Malformed entries are skipped, returning partial results
"""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from app.services.play_store_scraper import fetch_reviews


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_raw_entry(
    review_id="gp-001",
    user_name="Alice",
    score=5,
    content="Great app",
    at=None,
):
    return {
        "reviewId": review_id,
        "userName": user_name,
        "score": score,
        "content": content,
        "at": at or datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    }


# ---------------------------------------------------------------------------
# 1. Field mapping
# ---------------------------------------------------------------------------

def test_fetch_reviews_returns_list():
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry()], None)):
        result = fetch_reviews("com.example.app")

    assert isinstance(result, list)


def test_fetch_reviews_external_id_mapped():
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry(review_id="abc123")], None)):
        result = fetch_reviews("com.example.app")

    assert result[0]["external_id"] == "abc123"


def test_fetch_reviews_author_mapped():
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry(user_name="Bob")], None)):
        result = fetch_reviews("com.example.app")

    assert result[0]["author"] == "Bob"


def test_fetch_reviews_rating_mapped():
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry(score=3)], None)):
        result = fetch_reviews("com.example.app")

    assert result[0]["rating"] == 3


def test_fetch_reviews_title_always_none():
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry()], None)):
        result = fetch_reviews("com.example.app")

    assert result[0]["title"] is None


def test_fetch_reviews_body_mapped():
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry(content="Really love it")], None)):
        result = fetch_reviews("com.example.app")

    assert result[0]["body"] == "Really love it"


# ---------------------------------------------------------------------------
# 2. reviewed_at is a valid ISO8601 string
# ---------------------------------------------------------------------------

def test_reviewed_at_is_string():
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry()], None)):
        result = fetch_reviews("com.example.app")

    assert isinstance(result[0]["reviewed_at"], str)


def test_reviewed_at_is_valid_iso8601():
    at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry(at=at)], None)):
        result = fetch_reviews("com.example.app")

    parsed = datetime.fromisoformat(result[0]["reviewed_at"])
    assert parsed == at


def test_reviewed_at_matches_isoformat():
    at = datetime(2024, 3, 10, 8, 45, 0, tzinfo=timezone.utc)
    with patch("app.services.play_store_scraper.reviews", return_value=([_make_raw_entry(at=at)], None)):
        result = fetch_reviews("com.example.app")

    assert result[0]["reviewed_at"] == at.isoformat()


# ---------------------------------------------------------------------------
# 3. Mocks library and verifies call arguments
# ---------------------------------------------------------------------------

def test_reviews_called_with_correct_app_id():
    from google_play_scraper import Sort

    mock_reviews = MagicMock(return_value=([], None))
    with patch("app.services.play_store_scraper.reviews", mock_reviews):
        fetch_reviews("com.example.app")

    call_args = mock_reviews.call_args
    assert call_args[0][0] == "com.example.app"


def test_reviews_called_with_default_max_reviews():
    mock_reviews = MagicMock(return_value=([], None))
    with patch("app.services.play_store_scraper.reviews", mock_reviews):
        fetch_reviews("com.example.app")

    assert mock_reviews.call_args[1]["count"] == 500


def test_reviews_called_with_custom_max_reviews():
    mock_reviews = MagicMock(return_value=([], None))
    with patch("app.services.play_store_scraper.reviews", mock_reviews):
        fetch_reviews("com.example.app", max_reviews=100)

    assert mock_reviews.call_args[1]["count"] == 100


def test_reviews_called_with_sort_newest():
    from google_play_scraper import Sort

    mock_reviews = MagicMock(return_value=([], None))
    with patch("app.services.play_store_scraper.reviews", mock_reviews):
        fetch_reviews("com.example.app")

    assert mock_reviews.call_args[1]["sort"] == Sort.NEWEST


# ---------------------------------------------------------------------------
# 4. Returns empty list (not exception) on library error
# ---------------------------------------------------------------------------

def test_returns_empty_list_on_library_error():
    with patch("app.services.play_store_scraper.reviews", side_effect=Exception("network error")):
        result = fetch_reviews("com.example.app")

    assert result == []


def test_no_exception_raised_on_library_error():
    with patch("app.services.play_store_scraper.reviews", side_effect=Exception("timeout")):
        try:
            fetch_reviews("com.example.app")
            raised = False
        except Exception:
            raised = True

    assert raised is False


# ---------------------------------------------------------------------------
# 5. Malformed entries are skipped — partial results returned
# ---------------------------------------------------------------------------

def test_malformed_entry_skipped_partial_results():
    good_entry = _make_raw_entry(review_id="good-1")
    bad_entry = {"no_fields": "here"}

    with patch("app.services.play_store_scraper.reviews", return_value=([good_entry, bad_entry], None)):
        result = fetch_reviews("com.example.app")

    assert len(result) == 1
    assert result[0]["external_id"] == "good-1"


def test_malformed_entry_does_not_raise():
    bad_entry = {"no_fields": "here"}

    with patch("app.services.play_store_scraper.reviews", return_value=([bad_entry], None)):
        try:
            fetch_reviews("com.example.app")
            raised = False
        except Exception:
            raised = True

    assert raised is False
