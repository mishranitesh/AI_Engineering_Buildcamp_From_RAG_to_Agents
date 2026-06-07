from app.orchestration.state import WorkflowState


def test_workflow_state_defaults():
    state = WorkflowState(requirement="Build a Todo API")
    assert state.final_status == "pending"
    assert state.pr_phase == "none"
    assert state.github_enabled is False
    assert state.jira_enabled is False
    assert state.user_stories == []
    assert state.backend_code == {}
    assert state.tests == {}

def test_workflow_state_stores_requirement():
    state = WorkflowState(requirement="Build a Todo API")
    assert state.requirement == "Build a Todo API"

def test_workflow_state_jira_fields():
    state = WorkflowState(requirement="test")
    state.jira_epic_key = "KAN-1"
    state.jira_story_keys = ["KAN-2", "KAN-3"]
    assert len(state.jira_story_keys) == 2

def test_workflow_state_pr_phase_transitions():
    state = WorkflowState(requirement="test")
    for phase in ["draft", "ready_for_review", "fixing", "merged"]:
        state.pr_phase = phase
        assert state.pr_phase == phase
