# Skill: fastapi-conventions

## Project Structure

```
app/
  routers/          # FastAPI routers — one file per resource
  services/         # Business logic — scrapers, parsers
  models/           # Pydantic request/response models only
main.py             # App entry point — mounts routers, health check
```

## Stateless by Design

This service has no database, no queue, no session state, no persistent storage.
Every request is fully self-contained. Never add state.

## Router Pattern

```python
# app/routers/scrape.py
from fastapi import APIRouter
from app.models.scrape import ScrapeRequest, ScrapeResponse

router = APIRouter()

@router.post("/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest) -> ScrapeResponse:
    ...
```

Mount in `main.py`:
```python
from app.routers import scrape
app.include_router(scrape.router)
```

## Pydantic Models

```python
# app/models/scrape.py
from pydantic import BaseModel, model_validator
from typing import Optional

class ScrapeRequest(BaseModel):
    app_store_id: Optional[str] = None
    app_store_country: Optional[str] = "us"
    play_store_id: Optional[str] = None
    max_reviews: int = 500

    @model_validator(mode="after")
    def at_least_one_store(self):
        if not self.app_store_id and not self.play_store_id:
            raise ValueError("At least one of app_store_id or play_store_id is required")
        return self
```

## Parallel Execution

Both scrapers always run in parallel using `ThreadPoolExecutor`.
Never run them sequentially — it doubles the response time.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {}
    if request.app_store_id:
        futures["app_store"] = executor.submit(
            app_store_scraper.fetch_reviews,
            request.app_store_id,
            request.app_store_country,
            request.max_reviews
        )
    if request.play_store_id:
        futures["play_store"] = executor.submit(
            play_store_scraper.fetch_reviews,
            request.play_store_id,
            request.max_reviews
        )
```

## Error Handling

Scrapers must never raise to the router. They return empty list + populate `errors`.
The router always returns HTTP 200 with `partial: true` if one store failed.
Only return HTTP 422 for invalid request shape (Pydantic handles this automatically).

## Environment Variables

```python
import os
SCRAPING_SERVICE_URL = os.environ.get("SCRAPING_SERVICE_URL", "http://localhost:8000")
```

All env vars documented in `.env.example`. Never hardcode.

## Rules

- No global state or module-level side effects
- All functions are pure where possible — inputs in, output out
- Type hints on all function signatures
- No print() in committed code — use Python `logging` if needed
