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

    pr_phase: str = "none"  # none | draft | ready_for_review | fixing | merged
    pr_accepted_comments: list[str] = []  # comments selected for autofix

    jira_enabled: bool = False
    jira_epic_key: str | None = None
    jira_epic_url: str | None = None
    jira_story_keys: list[str] = []
    jira_story_urls: list[str] = []
    jira_task_keys: list[str] = []
