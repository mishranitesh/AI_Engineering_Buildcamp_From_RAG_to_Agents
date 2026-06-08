# Monitoring

## Log Collection

Logs are collected via **Loguru** and written to two sinks simultaneously:

| Sink | Format | Level | Rotation |
|---|---|---|---|
| stdout | `YYYY-MM-DD HH:mm:ss \| LEVEL \| message` | INFO | — |
| `logs/workflow.log` | same | DEBUG | 10 MB / 7 days retained |

Every agent phase emits a structured log line, e.g.:

```
2026-06-06 15:22:38 | INFO | PM Agent done | elapsed=4.2s
2026-06-06 15:22:44 | INFO | KB retrieved 3 patterns: [...]
2026-06-06 15:23:10 | INFO | JIRA Epic created | key=KAN-42 | url=...
2026-06-06 15:23:28 | ERROR | GitHub draft PR phase failed: 401 Unauthorized
```

## Monitoring Dashboard

A Streamlit dashboard (`ui/monitoring.py`) parses `logs/workflow.log` in real time.

### How to access
```bash
make monitor   # starts on port 8502
# or: streamlit run ui/monitoring.py --server.port 8502
```

- Main app: http://localhost:8501
- Monitoring: http://localhost:8502

## What it shows

| Panel | Source | Description |
|--------|--------|-------------|
| Total Events | all log lines | Count of structured log entries |
| Errors | `level == ERROR` | Count of error events |
| Workflows Run | `"PM phase started"` | Number of workflow runs |
| PRs Created | `"Phase 1 done"` | Number of draft PRs opened |
| Agent Elapsed Times | `elapsed=Xs` in message | Bar chart — average seconds per agent |
| Error Log | `level == ERROR` | Timestamped error table |
| Recent Events | last 50 lines | Live event feed, newest first |

## How logs are processed
The dashboard uses re to parse each log line into {time, level, message} fields,
loads them into a pandas DataFrame, then derives metrics and charts from that DataFrame.
No external monitoring infrastructure is required.


**README check:** Already has `make monitor # terminal 3 — start monitoring dashboard (port 8502)`.

**User feedback (+1):** ✅ Thumbs up/down buttons appear after code generation.
Feedback is logged as `USER_FEEDBACK | project=... | rating=...` and counted
in the monitoring dashboard metrics row.

**Logs → ground truth → evaluation**
Here's the mechanism. Each positive feedback log entry has the project name, and earlier in the same log there's the requirement that was used. You can parse both together to auto-build ground truth samples.

`evaluation/seed_from_feedback.py`
parses `logs/workflow.log` for `USER_FEEDBACK | rating=positive` entries,
extracts the corresponding requirement, generates expected criteria via LLM,
and appends to `evaluation/ground_truth.json`. Run with `make seed-gt` then
`make evaluate` to re-evaluate against user-validated samples.


Log lines that exist for every run:

```
INFO | PM phase started | requirement='Build a Todo API...'
INFO | USER_FEEDBACK | project=todo-api | rating=positive
```

A script reads the log, finds positive feedback entries, looks up the matching requirement, generates basic expected criteria from it via LLM, and appends to ground_truth.json.

## Usage:


### Seed a specific project after a good run
make seed-gt PROJECT=bookmark-api

#### At end of month — seed everything positive from the full log
make seed-gt

#### Future weekly/monthly cron (no code changes needed, just schedule this)
```
0 0 * * 0  cd /path/to/multi-agent-dev-platform && make seed-gt
```

Note: The /feedback endpoint stays simple — just logs, no auto-seeding. Seeding remains a deliberate human decision, which also means you control what goes into your ground truth dataset.


## The full cycle:
```
User rates output 👍
        ↓
LOG: USER_FEEDBACK | project=my-api | rating=positive
        ↓
make seed-gt  →  parses log, finds requirement, LLM infers expected criteria
        ↓
ground_truth.json grows with real-world validated samples
        ↓
make evaluate  →  runs LLM judge against the enriched dataset
        ↓
Richer evaluation with user-validated cases
```

## Testing User feedback and ground truth → evaluation

### Step 1 - Run a new requirement through the UI (http://localhost:8501):

- Project name: bookmark-api
- Requirement: Build a Bookmark Manager API with endpoints to add, list, and delete bookmarks. Each bookmark has a title and URL. Use in-memory storage.
- Click Run PM Agent → then Generate Code
- Click 👍 Good output when it appears

### Step 2 — Verify the feedback hit the log:

```bash
grep "USER_FEEDBACK" capstone/multi-agent-dev-platform/logs/workflow.log
```

Expected Output
```
2026-06-08 ... | INFO | USER_FEEDBACK | project=bookmark-api | rating=positive
```

Actual Output
```
(.venv) niteshmishra@Mac AI_Engineering_Buildcamp_From_RAG_to_Agents % grep "USER_FEEDBACK" capstone/multi-agent-dev-platform/logs/workflow.log
2026-06-08 15:37:00 | INFO | USER_FEEDBACK | project=bookmark-api | rating=positive
```

### Step 3 — Seed ground truth from feedback:
```bash
cd capstone/multi-agent-dev-platform
make seed-gt

OR 

make seed-gt PROJECT=bookmark-api

# Output
.venv/bin/python -m evaluation.seed_from_feedback --project bookmark-api
Generating criteria for: bookmark-api
Added 'bookmark-api' to ground_truth.json (4 total samples)
```

### Step 4 — Check ground_truth.json now has 4 samples:

```bash
cat evaluation/ground_truth.json | python -c "import json,sys; d=json.load(sys.stdin); [print(s['id']) for s in d]"

# Output
(.venv) niteshmishra@Mac multi-agent-dev-platform % cat evaluation/ground_truth.json | python -c "import json,sys; d=json.load(sys.stdin); [print(s['id']) for s in d]"
todo-api
inventory-api
user-auth-api
bookmark-api
```

### Step 5 - Check ground_truth.json now has additional entry for bookmark-api

```
# Output
{
    "id": "bookmark-api",
    "requirement": "Build a Bookmark Manager API with endpoints to add, list, and delete bookmarks. Each bookmark has a title and URL. Use in-memory storage.",
    "expected": {
      "min_user_stories": 3,
      "required_story_keywords": [
        "add",
        "list",
        "delete"
      ],
      "required_files": [
        "main.py"
      ],
      "required_endpoints": [
        "POST",
        "GET",
        "DELETE"
      ],
      "review_min_items": 3
    }
  }
```

Should print: todo-api, inventory-api, user-auth-api, bookmark-api

### Step 6 — Run evaluation against enriched dataset:

```bash
make evaluate

# Output
(.venv) niteshmishra@Mac multi-agent-dev-platform % make evaluate
.venv/bin/python -m evaluation.run_evaluation

==================================================
Evaluating: todo-api
==================================================
PM Agent: 3/3
2026-06-08 15:44:55 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Keep business logic in a service la']
Developer Agent: 4/4
2026-06-08 15:45:00 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Keep business logic in a service la']
2026-06-08 15:45:04 | INFO | KB retrieved 3 patterns for review: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Service layer should raise domain e']
Review Agent: 3/3

==================================================
Evaluating: inventory-api
==================================================
PM Agent: 3/3
2026-06-08 15:45:12 | INFO | KB retrieved 3 patterns: ['Best practice: Define explicit request and respons', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Separate data models (DB schema), b']
Developer Agent: 3/4
2026-06-08 15:45:20 | INFO | KB retrieved 3 patterns: ['Best practice: Define explicit request and respons', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Separate data models (DB schema), b']
2026-06-08 15:45:27 | INFO | KB retrieved 3 patterns for review: ['Best practice: Define explicit request and respons', 'Best practice: Separate data models (DB schema), b', 'Best practice: Service layer should raise domain e']
Review Agent: 3/3

==================================================
Evaluating: user-auth-api
==================================================
PM Agent: 3/3
2026-06-08 15:45:38 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Define explicit request and respons']
Developer Agent: 3/4
2026-06-08 15:45:45 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Define explicit request and respons']
2026-06-08 15:45:55 | INFO | KB retrieved 3 patterns for review: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Service layer should raise domain e']
Review Agent: 3/3

==================================================
Evaluating: bookmark-api
==================================================
PM Agent: 3/3
2026-06-08 15:46:03 | INFO | KB retrieved 3 patterns: ['Best practice: Always release external resources (', 'Best practice: Define explicit request and respons', 'Best practice: Validate and sanitize all inputs at']
Developer Agent: 3/4
2026-06-08 15:46:08 | INFO | KB retrieved 3 patterns: ['Best practice: Always release external resources (', 'Best practice: Define explicit request and respons', 'Best practice: Validate and sanitize all inputs at']
2026-06-08 15:46:12 | INFO | KB retrieved 3 patterns for review: ['Best practice: Define explicit request and respons', 'Best practice: Separate data models (DB schema), b', 'Best practice: Keep business logic in a service la']
Review Agent: 3/3

==================================================
EVALUATION SUMMARY
==================================================
todo-api: 10/10 (100%)
inventory-api: 9/10 (90%)
user-auth-api: 9/10 (90%)
bookmark-api: 9/10 (90%)
```

**Notable improvement**: todo-api jumped from 90% → 100% (Developer Agent now 4/4 vs 3/4 previously). The bookmark-api seeded from real user feedback slots right in at 90%, consistent with the others.

The ground truth dataset is now self-growing — every positively-rated run can become a new evaluation sample with one command.
