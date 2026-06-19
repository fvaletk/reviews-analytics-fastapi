import logging

from google_play_scraper import Sort, reviews

logger = logging.getLogger(__name__)


def fetch_reviews(app_id: str, max_reviews: int = 500) -> list[dict]:
    try:
        raw_reviews, _ = reviews(app_id, count=max_reviews, sort=Sort.NEWEST)
    except Exception as exc:
        logger.error("Failed to fetch Play Store reviews for %s: %s", app_id, exc)
        return []

    results: list[dict] = []
    for entry in raw_reviews:
        try:
            reviewed_at = entry["at"].isoformat()
            results.append(
                {
                    "external_id": entry["reviewId"],
                    "author": entry["userName"],
                    "rating": entry["score"],
                    "title": None,
                    "body": entry["content"],
                    "reviewed_at": reviewed_at,
                }
            )
        except Exception as exc:
            logger.warning("Skipping malformed Play Store review entry: %s", exc)

    return results
