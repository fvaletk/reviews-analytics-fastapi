# /work-next-ticket

Fetches the next Todo ticket from Linear, runs it through the full agent pipeline on its own branch, and opens a pull request into `staging` for the user to review.

## Prerequisites

Run `/docker-check` first. Do not proceed if any check fails.

## What This Command Does

1. Fetch the next **Todo** ticket from Linear (project: `Reviewly`, team: Brain Spark)
2. Read the full ticket — title, description, acceptance criteria, and `gitBranchName`
3. **Validate the ticket is unambiguous** — stop and ask if anything is unclear
4. Mark ticket **In Progress**
5. **Create the ticket branch** from the latest `staging`, named exactly the ticket's `gitBranchName`
   (stop if the working tree isn't clean; check out the existing branch when resuming)
6. Spawn **implement** agent with full ticket content
7. Spawn **test** agent with acceptance criteria and list of modified files
8. Spawn **commit** agent with the ticket ID, title, URL, and branch name — it pushes the branch and opens a PR into `staging`
9. Comment the PR URL on the Linear ticket and **stop**. The ticket stays **In Progress** until you merge the PR and mark it Done.

Never pushes to `staging` or `main`, never merges, never marks a ticket Done. (Human review gate added 2026-10-06.)

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
Ticket URL: <linear url>
Branch: <gitBranchName>
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
| Working tree not clean before branching | Stop, ask user — never stash or discard |
| Tests fail | Stop, report failures, do not commit |
| Implementation bug found | Stop, report to user, do not auto-fix |
| Push fails | Stop, report the git error |
| `gh` unavailable | Report the GitHub compare URL instead of a PR URL |

Ticket stays **In Progress** on any failure. Fix manually, then re-run `/work-next-ticket` — it checks out the existing branch and resumes.

## Linear State Management

| Step | Linear status |
|---|---|
| Ticket fetched | Todo |
| Validation passed | In Progress |
| PR opened | In Progress (stays — PR URL commented on the ticket) |
| You merge the PR | You mark it Done |
| Any failure | In Progress (stays) |
