# Phase 2 is GitHub Integration:

The flow from generating code to creating a branch, committing, opening a PR, posting review comments, running an auto-fix agent, and optionally merging.

# Implementation plan:

- `app/tools/github_tool.py` — GitHub API wrapper (create branch, commit files, open PR, post review, merge)
    - Create `app/tools/github_tool.py` — GitHub API wrapper
- `app/agents/autofix_agent/agent.py` — Auto-fix agent that takes code + review comments → improved code
    - Create app/agents/autofix_agent/agent.py — Auto-fix agent
- `app/orchestration/state.py` — Add github_branch, pr_url, pr_number, fixed_code fields
    - Update `app/orchestration/state.py` — Add GitHub fields
- `app/orchestration/workflow.py` — Add optional GitHub phase after review
    - Update `app/orchestration/workflow.py` — Add GitHub phase
- `app/main.py` — Add github_repo, create_pr, auto_merge to request/response
    - Update app/main.py — Add `github_repo/create_pr` request fields
- `ui/streamlit_app.py` — GitHub settings sidebar + PR link display
    - Update `ui/streamlit_app.py` — GitHub sidebar + PR link display

# Implementation Steps - 

## Step 1 — Install dependencies

```
cd multi-agent-dev-platform
pip install PyGithub gitpython
pip install python-dotenv

OR
# If new virtual envt is created then use 
python3 -m venv .venv &&  source .venv/bin/activate

pip install fastapi uvicorn pydantic streamlit openai python-dotenv PyGithub gitpython loguru pytest httpx

OR

uv pip install PyGithub gitpython python-dotenv
```

## Step 2 - Add env vars to .env

```
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_OWNER=your_github_username_or_org
GITHUB_REPO=your_target_repo_name
```

The GITHUB_TOKEN needs repo scope to create branches, commits, PRs, and merge.

## Step 3 — Create app/tools/ directory and github_tool.py
```
mkdir -p app/tools
touch app/tools/__init__.py
touch app/tools/github_tool.py
update app/tools/github_tool.py
```

## Step 4 — Create app/agents/autofix_agent/
```
mkdir -p app/agents/autofix_agent
touch app/agents/autofix_agent/__init__.py
touch app/agents/autofix_agent/agent.py
```

## Step 5 — Update `app/orchestration/state.py`

Add these fields to `WorkflowState`:

```python
# GitHub Phase 2 fields
github_enabled: bool = False
github_branch: str | None = None
pr_number: int | None = None
pr_url: str | None = None
fixed_code: dict[str, str] = {}
```

## Step 6 — Update app/orchestration/workflow.py
Add the GitHub phase

## Step 7 — Update app/main.py
Add `github_repo/create_pr` request fields

## Step 8 — Update ui/streamlit_app.py
GitHub settings sidebar + PR link display

## Step 9 — Test it
Run the backend and UI as before:

### Terminal 1 - API
`uvicorn app.main:app --reload`

### Terminal 2 - APP
`streamlit run ui/streamlit_app.py`

In the Streamlit sidebar, check "Push to GitHub & Open PR", enter requirement, and click Run Agents. See a PR link appear after generation completes.

```
Build a simple Inventory Management API using FastAPI.

The system should allow:
- Add inventory item (name, quantity, price)
- Get all items
- Update item quantity
- Delete item

Use in-memory storage for now.
```

```
/run-workflow  →  Phase 1: Draft PR  (auto)
                      ↓ developer inspects
/pr-transition?phase=ready_for_review  →  Phase 2: Review Agent posts comments
                      ↓ team/agent reviews, selects which comments to fix
/pr-transition?phase=fix&accepted_comments=[...]  →  Phase 3: AutoFix commits
                      ↓ final approval
/pr-transition?phase=merge  →  Phase 4: Merge to main
```

## UI flow 

## PR Workflow UI States

| Current Phase      | Button(s) Shown                                                                    |
| ------------------ | ---------------------------------------------------------------------------------- |
| `draft`            | **Mark Ready for Review →**                                                        |
| `ready_for_review` | **Fix PR →** and **Merge PR →**<br><sub>(includes review comment checkboxes)</sub> |
| `fixing`           | **Merge PR →**                                                                     |
| `merged`           | ✅ **PR merged to main!**                                                           |

![phase2_Streamlit web app](../capstone/multi-agent-dev-platform/images/phase2_Streamlit%20web%20app.png)

## Debugging 

WARNING:  StatReload detected changes in 'generated_projects/generated-project/tests/test_app.py'. Reloading...


Solution - 

The workflow writes generated files to generated_projects/, uvicorn's --reload detected those new files and restarted the server, wiping state_store — right after the draft PR was created but before you could click the next phase.

Fix: tell uvicorn to only watch the app/ directory, not the whole project:


```uvicorn app.main:app --reload --reload-dir app```

This way, generated project files won't trigger a reload. Restart with that command, run your workflow again, and the phase transitions will work.