# /work-next-ticket

Fetches the next Todo ticket from Linear, runs it through the full agent pipeline, and marks it Done.

## Prerequisites

Run `/docker-check` first. Do not proceed if any check fails.

## What This Command Does

1. Fetch the next **Todo** ticket from Linear (project: `Reviewly`, team: Brain Spark)
2. Read the full ticket — title, description, and acceptance criteria
3. **Validate the ticket is unambiguous** — stop and ask if anything is unclear
4. Mark ticket **In Progress**
5. Spawn **implement** agent with full ticket content
6. Spawn **test** agent with acceptance criteria and list of modified files
7. Spawn **commit** agent with ticket ID and title
8. Mark ticket **Done** if commit agent reports success

## How to Run

```
/work-next-ticket
```

To work on a specific ticket:
```
/work-next-ticket BRA-24
```

## Agent Handoff Protocol

Each agent gets an explicit context block — never assume agents share state.

**Implement agent receives:**
```
Ticket ID: BRA-XX
Title: <title>
Description: <full description>
Acceptance Criteria:
- [ ] criterion 1
- [ ] criterion 2
```

**Test agent receives:**
```
Ticket ID: BRA-XX
Acceptance Criteria:
- [ ] criterion 1
- [ ] criterion 2
Files created or modified:
- app/routers/scrape.py
- app/services/app_store_scraper.py
```

**Commit agent receives:**
```
Ticket ID: BRA-XX
Title: <title>
Test results: <summary from test agent>
```

## After requirements.txt Changes

If the implement agent modifies `requirements.txt`, the commit agent must run before anything else:

```bash
docker compose exec scraper pip install -r requirements.txt
```

## Failure Handling

| Failure point | Action |
|---|---|
| docker-check fails | Stop, fix environment first |
| Ticket is ambiguous | Stop, ask user, wait for clarification |
| Tests fail | Stop, report failures, do not commit |
| Implementation bug found | Stop, report to user, do not auto-fix |
| Push fails | Stop, report the git error |

Ticket stays **In Progress** on any failure. Fix manually, then re-run `/work-next-ticket`.

## Linear State Management

| Step | Linear status |
|---|---|
| Ticket fetched | Todo |
| Validation passed | In Progress |
| All agents done + pushed | Done |
| Any failure | In Progress (stays) |
