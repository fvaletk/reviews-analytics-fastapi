import logging

import httpx

logger = logging.getLogger(__name__)

_RSS_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/id={app_id}/sortBy=mostRecent/page={page}/json"
)


def fetch_reviews(
    app_id: str, country: str, max_reviews: int = 500
) -> list[dict]:
    results: list[dict] = []

    try:
        for page in range(1, 11):
            if len(results) >= max_reviews:
                break

            url = _RSS_URL.format(country=country, app_id=app_id, page=page)

            try:
                response = httpx.get(url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("HTTP error fetching App Store page %d: %s", page, exc)
                break

            feed = response.json().get("feed", {})
            entries = feed.get("entry", [])

            if not entries:
                break

            for entry in entries:
                if len(results) >= max_reviews:
                    break

                raw_rating = entry.get("im:rating", {}).get("label", "0")
                try:
                    rating = int(raw_rating)
                except (ValueError, TypeError):
                    rating = 0

                author_label = (
                    entry.get("author", {}).get("name", {}).get("label")
                )

                title_label = entry.get("title", {}).get("label")

                results.append(
                    {
                        "external_id": entry.get("id", {}).get("label"),
                        "author": author_label,
                        "rating": rating,
                        "title": title_label,
                        "body": entry.get("content", {}).get("label"),
                        "reviewed_at": entry.get("updated", {}).get("label"),
                        "store": "app_store",
                    }
                )
    except Exception as exc:
        logger.error("Unexpected error in fetch_reviews: %s", exc)
        return []

    return results
