---
paths:
  - "tests/**"
---

# pytest

Uses `pytest`, `pytest-mock` (the `mocker` fixture), and FastAPI's `TestClient`.
`tests/conftest.py` puts the project root on `sys.path` so `from main import app` works.

## Where tests go

| Source | Test |
|---|---|
| `app/routers/<x>.py` | `tests/test_<x>_router.py` |
| `app/services/<x>.py` | `tests/test_<x>_service.py` |
| `main.py` | `tests/test_main.py` |

`tests/test_scrape_router.py` and `tests/test_app_store_scraper_service.py` are the references.

## Rules

- Never make real network calls. Mock `httpx` and `google_play_scraper`.
- **Mock where it's used, not where it's defined.** When testing the router, patch
  `app.routers.scrape.app_store_scraper.fetch_reviews`, not
  `app.services.app_store_scraper.fetch_reviews`.
- Test the failure path too: a scraper returns `[]` on error. To exercise `partial: true` in a
  router test, make the patched scraper raise.
- No `time.sleep()` or real delays.
- One assertion per test where practical.
