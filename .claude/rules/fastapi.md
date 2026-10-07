---
paths:
  - "app/**/*.py"
  - "main.py"
---

# FastAPI conventions

## Where code goes

```
app/
  routers/   # One file per resource. Mounted in main.py with app.include_router.
  services/  # Scrapers and parsers — the actual work.
  models/    # Pydantic request/response models only.
main.py      # Entry point: mounts routers, /health.
```

## Stateless

No database, no queue, no sessions, no file writes, no module-level state. Every
request is self-contained. Never add state.

## Scrapers

- Both stores run in parallel through `ThreadPoolExecutor(max_workers=2)` in
  `app/routers/scrape.py`. Never run them one after the other — it doubles the response time.
- A scraper never raises to the router. On failure it logs and returns `[]`.
- The router returns 200 with `partial: true` when one store failed. 422 is only for an invalid
  request shape, and Pydantic produces it.
- **Known gap:** the router adds to `errors` only when a future raises. Scrapers swallow their
  own exceptions, so today a failed store comes back as an empty list with `partial: false`.
  Don't write tests that assume otherwise, and don't fix it outside a ticket.

## Code

- Type hints on every function signature.
- Pure functions where possible — inputs in, output out.
- `logging`, never `print()`.
- Read config with `os.environ.get("KEY", default)`. Every variable goes into `.env.example`.
