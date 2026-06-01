from fastapi import FastAPI
from pydantic import BaseModel
from app.orchestration.workflow import WorkflowOrchestrator

app = FastAPI()
orchestrator = WorkflowOrchestrator()


class RequirementRequest(BaseModel):
    requirement: str


@app.post("/run-workflow")
def run_workflow(req: RequirementRequest):
    result = orchestrator.run(req.requirement)
    # Return structured data to the client
    return {
        "status": result.final_status,
        "project_name": result.project_name,
        "generated_path": result.generated_path,
        "zip_file": result.zip_file
    }