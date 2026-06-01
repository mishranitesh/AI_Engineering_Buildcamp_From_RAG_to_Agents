from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class WorkflowState(BaseModel):
    requirement: str

    project_name: str = "generated-project"

    user_stories: list[str] = []

    architecture: str = ""
    mermaid: str = ""

    backend_code: dict[str, str] = {}

    tests: dict[str, str] = {}

    review_comments: list[str] = []

    generated_path: str | None = None
    zip_file: str | None = None

    final_status: str = "pending"