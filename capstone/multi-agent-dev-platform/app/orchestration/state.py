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

    # GitHub Phase 2 fields
    github_enabled: bool = False
    github_branch: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    fixed_code: dict[str, str] = {}

    # Add to WorkflowState
    pr_phase: str = "none"  # none | draft | ready_for_review | fixing | merged
    pr_accepted_comments: list[str] = []  # comments selected for autofix
