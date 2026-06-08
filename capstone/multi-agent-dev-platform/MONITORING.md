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


**README check:** Already has `make monitor # terminal 3 — start monitoring dashboard (port 8502)` — sufficient.

---

## TODO 
**Bonus points:**

**User feedback (+1):** ❌ Not implemented. The simplest addition would be a thumbs up/down button in the Streamlit UI after code generation that appends a line to the log. ~10 lines of code.

**Logs → ground truth → evaluation (+2):** This is partially possible already — your logs capture `requirement`, agent outputs, and elapsed times. The mechanism to auto-generate ground truth from logs doesn't exist yet but would be a strong addition. Worth noting if you implement it.

