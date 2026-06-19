from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter

from app.models.scrape import ScrapeRequest, ScrapeResponse
from app.services import app_store_scraper, play_store_scraper

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest) -> ScrapeResponse:
    app_store_reviews: list[dict] = []
    play_store_reviews: list[dict] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}

        if request.app_store_id:
            futures["app_store"] = executor.submit(
                app_store_scraper.fetch_reviews,
                request.app_store_id,
                request.app_store_country,
                request.max_reviews,
            )
        if request.play_store_id:
            futures["play_store"] = executor.submit(
                play_store_scraper.fetch_reviews,
                request.play_store_id,
                request.max_reviews,
            )

        for store, future in futures.items():
            try:
                result = future.result()
                if store == "app_store":
                    app_store_reviews = result
                else:
                    play_store_reviews = [
                        {**review, "store": "play_store"} for review in result
                    ]
            except Exception as exc:
                errors.append(f"{store}: {exc}")

    succeeded = sum([
        bool(app_store_reviews) or "app_store" not in futures,
        bool(play_store_reviews) or "play_store" not in futures,
    ])
    failed = len(errors)
    partial = failed > 0 and succeeded > 0

    return ScrapeResponse(
        reviews=app_store_reviews + play_store_reviews,
        errors=errors,
        partial=partial,
        app_store_count=len(app_store_reviews),
        play_store_count=len(play_store_reviews),
    )
