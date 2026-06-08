from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.orchestration.workflow import WorkflowOrchestrator
from app.orchestration.state import WorkflowState
from app.orchestration.session_store import SessionStore

app = FastAPI()
orchestrator = WorkflowOrchestrator()

state_store = SessionStore()

class PMRequest(BaseModel):
    requirement: str
    project_name: str
    jira_enabled: bool = False

@app.post("/run-pm")
def run_pm(req: PMRequest):
    state = orchestrator.run_pm_phase(
        req.requirement,
        project_name=req.project_name,
        jira_enabled=req.jira_enabled
    )
    state_store.save(state)
    return {
        "status": state.final_status,
        "project_name": state.project_name,
        "user_stories": state.user_stories,
        "jira_epic_key": state.jira_epic_key,
        "jira_epic_url": state.jira_epic_url,
        "jira_story_keys": state.jira_story_keys,
        "jira_story_urls": state.jira_story_urls,
    }

@app.get("/sessions")
def list_sessions():
    """List all resumable (not yet merged) sessions."""
    return state_store.list_resumable()

@app.get("/session/{project_name}")
def get_session(project_name: str):
    state = state_store.get(project_name)
    if not state:
        raise HTTPException(404, "Session not found")
    return state.model_dump()

class CodegenRequest(BaseModel):
    project_name: str
    github_enabled: bool = False

@app.post("/run-codegen")
def run_codegen(req: CodegenRequest):
    state = state_store.get(req.project_name)
    if not state:
        raise HTTPException(status_code=404, detail="No PM phase found for this project")
    orchestrator.run_codegen_phase(state, github_enabled=req.github_enabled)
    state_store.save(state)
    return {
        "status": state.final_status,
        "project_name": state.project_name,
        "generated_path": state.generated_path,
        "zip_file": state.zip_file,
        "github_branch": state.github_branch,
        "pr_url": state.pr_url,
        "pr_number": state.pr_number,
        "pr_phase": state.pr_phase,
        "review_comments": state.review_comments,
    }

class PRTransitionRequest(BaseModel):
    project_name: str
    phase: str                          # ready_for_review | fix | merge
    accepted_comments: list[str] = []   # for phase=fix

@app.post("/pr-transition")
async def pr_transition(req: PRTransitionRequest):
    """Advance the PR to the next lifecycle phase."""
    # You'll need a way to reload/persist state — see note below
    state = state_store.get(req.project_name)
    if not state:
        raise HTTPException(404, "No active workflow for this project")

    if req.phase == "ready_for_review":
        orchestrator.phase_ready_for_review(state)
    elif req.phase == "fix":
        state.pr_accepted_comments = req.accepted_comments
        orchestrator.phase_fix_pr(state)
    elif req.phase == "merge":
        orchestrator.phase_merge_pr(state)
    else:
        raise HTTPException(400, f"Unknown phase: {req.phase}")

    state_store.save(state)
    return {"pr_phase": state.pr_phase, "pr_url": state.pr_url}

# main.py
@app.get("/debug/jira-issue-types")
def debug_jira_issue_types():
    import requests as req
    from app.tools.jira_tool import JiraTool
    jira = JiraTool()
    resp = req.get(
        f"{jira.url}/rest/api/3/project/{jira.project_key}",
        headers=jira.headers,
        auth=jira.auth,
    )
    issue_types = [it["name"] for it in resp.json().get("issueTypes", [])]
    return {"issue_types": issue_types}

"""
Hit http://localhost:8000/debug/jira-issue-types — it will return the exact names you need to use, for example:

{"issue_types": ["Story", "Task", "Bug", "Epic", "Subtask"]}
"""

class FeedbackRequest(BaseModel):
    project_name: str
    rating: str   # "positive" or "negative"

@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    from app.monitoring.logger import logger
    logger.info(f"USER_FEEDBACK | project={req.project_name} | rating={req.rating}")
    return {"status": "recorded"}
