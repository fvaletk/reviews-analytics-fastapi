# Reviews Analytics — FastAPI Scraping Service

Stateless Python microservice. Receives a scrape request, fetches reviews
from App Store (iTunes RSS) and Google Play (google-play-scraper) in parallel,
returns JSON. No database. No state. No webhooks.

**Stack:** Python 3.12 · FastAPI · Uvicorn · google-play-scraper · httpx · Docker

---

## Project knowledge lives in the Obsidian vault

This repo is one half of Reviewly. The context — status, decisions, technical
findings, ticket conventions — lives in the vault at `~/Projects/Capri`:

| What | Where |
|---|---|
| Project file — status, decisions, Linear conventions | `01-projects/reviewly/reviewly.md` |
| Current technical understanding, open threads | `01-projects/reviewly/analysis/current-understanding.md` |
| Session logs — the reasoning behind past decisions | `01-projects/reviewly/analysis/YYYY-MM-DD-*.md` |
| Captured findings awaiting triage | `01-projects/reviewly/findings/` |

**Read `current-understanding.md` before making decisions about the LLM pipeline,
review sampling, or cost.** It records what has already been settled and why —
including constraints that look real but aren't.

### Reporting a finding

Ran into a bug or figured something out mid-task? Run **`/report-issue`** —
no arguments. It summarizes the issue **from the current conversation** and
writes it to `01-projects/reviewly/findings/` in the vault, carrying over the
file/line references, what was ruled out, and what's still unknown, plus the
current branch and commit.

It does not create a ticket and does not change any code. Triage happens later
via `/triage-findings`, which verifies each finding before anything is filed.

Use it instead of fixing unrelated things mid-task, and instead of losing the
observation when the session ends.

---

## Prerequisites

Before running `/work-next-ticket`, ensure the environment is healthy:
```
/docker-check
```
Do not proceed if any check fails.

## /work-next-ticket

1. Fetch the next **Todo** ticket from Linear project `Reviewly` (team: Brain Spark)
2. Read the full ticket — title, description, and acceptance criteria
3. **If anything is ambiguous or missing context: STOP. Ask the user. Do not guess.**
4. Mark ticket **In Progress**
5. Spawn **Sub-agent 1 — Implement**
   - Load relevant skills before writing any code (see Skills below)
   - Implement exactly what the acceptance criteria describe, nothing more
6. Spawn **Sub-agent 2 — Test**
   - Load `pytest-patterns` skill
   - Write pytest tests. Do not modify implementation files.
7. Spawn **Sub-agent 3 — Commit**
   - Run `pytest` inside Docker — if any test fails, stop and report back
   - Commit: `git add -A && git commit -m "[BRA-XX] <ticket title>"`
   - Push to `staging` branch: `git push origin staging`
8. Mark ticket **Done** in Linear
9. Loop — fetch next ticket

## Sub-agent Rules

- Each sub-agent starts fresh. Pass all needed context explicitly.
- Sessions are workers, not storage. Nothing important lives in a session.
- Never add state to this service. It must remain stateless.
- Sub-agent 3 never pushes if tests are failing.

## Docker Rules

- The project directory is volume-mounted at `/app` inside the container
- Always use relative paths — never absolute paths like `/Users/...`
- Run all commands inside the container:
  ```bash
  docker compose exec scraper <command>
  ```
- Never use `docker compose cp` — write files locally, they appear in the container instantly
- After modifying `requirements.txt`, always run before anything else:
  ```bash
  docker compose exec scraper pip install -r requirements.txt
  ```
- Never include `#` comments inside multi-line bash strings — use a temp file or remove comments

## Environment Variables

All required environment variables are documented in `.env.example`.
Sub-agents must use `os.environ.get('KEY')` in code — never read `.env` directly.
Hooks in `.claude/hooks/` block read access to `.env` and credential files.
**Never write, copy, or generate credential values into `.env` — the developer
manages this file manually. If a variable is missing, report it and stop.**

## Skills

| Skill | Load when... |
|---|---|
| `fastapi-conventions` | any FastAPI file |
| `pytest-patterns` | writing tests |
| `scrape-contract` | anything touching the `/scrape` endpoint or response shape |

Skills live in `.claude/skills/`.