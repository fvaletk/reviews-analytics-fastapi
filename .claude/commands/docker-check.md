# /docker-check

Verifies the Docker environment is healthy before working on tickets.

## When to Run

- Before starting a new work session
- After modifying `requirements.txt`
- After pulling changes from `staging`
- When the container crashes or won't start

## Step 1 — Verify container is running

```bash
docker compose ps
```

Expected: `scraper` shows status `running`.

If not running:
```bash
docker compose up -d
```

If it keeps restarting, check logs:
```bash
docker compose logs scraper --tail=50
```

Report the output and stop if the container won't start.

## Step 2 — Verify dependencies are installed

```bash
docker compose exec scraper pip check
```

If any packages are missing or conflicting:
```bash
docker compose exec scraper pip install -r requirements.txt
```

## Step 3 — Verify the app boots

```bash
docker compose exec scraper python -c "from main import app; print('OK')"
```

Expected output: `OK`

If this fails, report the full error and stop.

## Step 4 — Verify health endpoint

```bash
curl -s http://localhost:8000/health
```

Expected: `{"status":"ok"}`

If this fails, check that port 8000 is mapped correctly in `docker-compose.yml`.

---

## All Checks Pass

Report back:
```
✅ Container: running
✅ Dependencies: installed
✅ App boot: OK
✅ Health endpoint: OK

Environment is healthy. Ready to work on tickets.
```

## Any Check Fails

Report exactly which step failed and the full error output.
Do not proceed to ticket work until all checks pass.
