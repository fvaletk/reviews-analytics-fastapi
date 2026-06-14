# Skill: scrape-contract

## Purpose

This skill defines the exact contract between the Rails app and the FastAPI
scraping service. Both sides must conform to this shape precisely.

---

## POST /scrape

### Request

```json
{
  "app_store_id": "1234567890",
  "app_store_country": "us",
  "play_store_id": "com.example.app",
  "max_reviews": 500
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `app_store_id` | string | conditional | Required if `play_store_id` absent |
| `app_store_country` | string | no | Defaults to `"us"` |
| `play_store_id` | string | conditional | Required if `app_store_id` absent |
| `max_reviews` | integer | no | Defaults to 500, max 500 |

Returns **HTTP 422** if neither store ID is provided.

### Response

```json
{
  "reviews": [
    {
      "store": "app_store",
      "external_id": "string",
      "author": "string or null",
      "rating": 5,
      "title": "string or null",
      "body": "string",
      "reviewed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "errors": [],
  "partial": false,
  "app_store_count": 500,
  "play_store_count": 500
}
```

| Field | Type | Notes |
|---|---|---|
| `reviews` | array | Combined from both stores |
| `store` | string | `"app_store"` or `"play_store"` |
| `external_id` | string | Store's native review ID — used for deduplication |
| `title` | string or null | Play Store reviews have no title — always `null` |
| `reviewed_at` | string | ISO 8601 UTC |
| `errors` | array of strings | Empty on full success |
| `partial` | boolean | `true` if one store succeeded and the other failed |
| `app_store_count` | integer | Count of App Store reviews returned |
| `play_store_count` | integer | Count of Play Store reviews returned |

### Timing Expectations

- App Store (10 pages × 50 reviews): 3–20 seconds
- Play Store (500 reviews via continuation tokens): 20–60 seconds
- Both run in **parallel** — total expected time: 20–60 seconds
- Rails sets a **120 second timeout** on the HTTP call

---

## GET /health

```json
{ "status": "ok" }
```

Used by Rails to verify the service is reachable before enqueuing jobs.

---

## How Rails Uses This (reference only)

In `ScrapingService`:
```ruby
response = Faraday.post(
  "#{ENV['SCRAPING_SERVICE_URL']}/scrape",
  { app_store_id:, app_store_country:, play_store_id:, max_reviews: 500 }.to_json,
  "Content-Type" => "application/json"
)
```

Reviews are then upserted into Postgres:
```ruby
Review.insert_all(
  formatted_reviews,
  unique_by: [:app_id, :store, :external_id]
)
```
