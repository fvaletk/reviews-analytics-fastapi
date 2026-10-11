# Reviewly — FastAPI Scraping Service

Stateless Python microservice. Receives a scrape request from the Rails app, fetches
reviews from the App Store (iTunes RSS) and Google Play (`google-play-scraper`) in
parallel, and returns JSON. No database, no state, no webhooks — and never add any.

**Stack:** Python 3.12 · FastAPI · Uvicorn · httpx · google-play-scraper · Docker

---

## Project knowledge lives in the Obsidian vault

```yaml
vault_project: reviewly
```

- **Found an unrelated bug mid-task?** Run `/report-issue` (no arguments). It writes a finding
  to the vault without creating a ticket or touching code. Don't fix it in the current ticket.

---

## Running things

Everything runs inside Docker. Check the environment with `/docker-check`. The repo is
mounted at `/app`, so files written locally appear in the container instantly — never use
`docker compose cp`. Use relative paths, never `/Users/...`.

```bash
docker compose exec scraper pytest                             # all tests
docker compose exec scraper pytest tests/test_scrape_router.py -v
docker compose exec scraper pip install -r requirements.txt    # after changing requirements.txt — run before anything else
```

---

## Rules

Conventions live in `.claude/rules/`. Each file is scoped by `paths:` and loads when you
work on matching files.

| Rule | Covers |
|---|---|
| `fastapi.md` | `app/`, `main.py` |
| `scrape-contract.md` | routers, models, services — the contract Rails depends on |
| `pytest.md` | `tests/` |

---

## Tickets

Tickets are worked with `/work-next-ticket` — the steps live in
`.claude/commands/work-next-ticket.md`. Whoever is working, these always hold:

- One branch per ticket, named the ticket's `gitBranchName`, cut from the latest `staging`.
- **Never push to `staging` or `main`.** Every ticket goes through a pull request into
  `staging`. (Human review gate since 2026-10-06.)
- Never merge a PR and never mark a ticket Done — both are the user's.
- Never commit or push with failing tests.

---

## Credentials

- Every environment variable is listed in `.env.example`. Read config with `os.environ.get("KEY", default)`.
- **Never read or write `.env`, and never generate credential values.** The developer manages
  it by hand. If a variable is missing, say which one and stop.
- `.claude/hooks/block-sensitive-files.sh` blocks Read/Edit/Write on `.env` files
  (`.env.example` stays readable).
