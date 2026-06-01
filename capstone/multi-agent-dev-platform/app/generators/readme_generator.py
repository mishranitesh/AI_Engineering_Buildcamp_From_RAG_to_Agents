from app.orchestration.state import WorkflowState


def generate_readme(
    state: WorkflowState
):

    return f"""
        # {state.project_name}

        ## Requirement

        {state.requirement}

        ## User Stories

        {chr(10).join(state.user_stories)}

        ## Architecture

        See architecture.md

        ## Run

        ```bash
        uvicorn backend.main:app --reload
        ```
    """