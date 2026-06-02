from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.orchestration.workflow import WorkflowOrchestrator
from app.orchestration.state import WorkflowState

app = FastAPI()
orchestrator = WorkflowOrchestrator()

# In-memory store — lives for the lifetime of the FastAPI process
state_store: dict[str, WorkflowState] = {}

class RequirementRequest(BaseModel):
    requirement: str
    github_enabled: bool = False
    auto_merge: bool = False


@app.post("/run-workflow")
def run_workflow(req: RequirementRequest):
    result = orchestrator.run(
        req.requirement,
        github_enabled=req.github_enabled,
        auto_merge=req.auto_merge
    )
    
    state_store[result.project_name] = result   # <-- save so /pr-transition can find it

    return {
        "status": result.final_status,
        "project_name": result.project_name,
        "generated_path": result.generated_path,
        "zip_file": result.zip_file,
        "github_branch": result.github_branch,
        "pr_url": result.pr_url,
        "pr_number": result.pr_number,
        "pr_phase": result.pr_phase,             # <-- expose phase to UI
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

    state_store[req.project_name] = state
    return {"pr_phase": state.pr_phase, "pr_url": state.pr_url}
