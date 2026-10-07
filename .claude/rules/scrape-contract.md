---
paths:
  - "app/routers/**"
  - "app/models/**"
  - "app/services/**"
  - "main.py"
---

# Scraping contract (provider side)

The Rails app (`~/Projects/reviews-analytics-rails`, `app/services/scraping_service.rb`)
is the only consumer. **Any change to the request or response shape is a two-repo
change** — Rails upserts on these fields.

Request and response envelope: `app/models/scrape.py`. The review items are untyped
(`list[dict]`), so their shape is defined here:

| Field | Type | Notes |
|---|---|---|
| `store` | string | `"app_store"` or `"play_store"` |
| `external_id` | string | The store's native ID. Rails dedupes on `(app_id, store, external_id)`. |
| `author` | string or null | |
| `rating` | integer | 1–5 |
| `title` | string or null | Always `null` for Play Store. |
| `body` | string | |
| `reviewed_at` | ISO 8601 string | Not normalized: App Store carries its feed's offset, Play Store is naive. |

## Semantics

- 422 if neither `app_store_id` nor `play_store_id` is given.
- `max_reviews` defaults to 500. It is not capped server-side.
- `partial: true` when one store failed and the other succeeded; `errors` holds one string per
  failure. (Known gap: scrapers swallow their own exceptions, so a failed store currently returns
  `[]` with no error and `partial: false` — see `fastapi.md`.)
- `app_store_count` / `play_store_count` count the reviews returned per store.
- `GET /health` → `{"status": "ok"}`.

## Timing

Both stores run in parallel. A full scrape takes 20–60 s (Play Store is the slow side).
Rails times out at 120 s, so a response must come back well inside that.
