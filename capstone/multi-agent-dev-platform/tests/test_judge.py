import os
import pytest
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Fixed requirement ensures test reproducibility across runs
REQUIREMENT = "Build a simple Todo API with create, list, and delete endpoints. Use in-memory storage."


def llm_judge(prompt: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


# ── PM Agent ──────────────────────────────────────────────────────────────────

def test_pm_agent_generates_user_stories():
    from app.agents.pm_agent.agent import PMAgent
    output = PMAgent().process(REQUIREMENT)

    verdict = llm_judge(f"""
    Review this PM Agent output and answer YES or NO for each:
    1. Does it contain user stories?
    2. Does it contain acceptance criteria?
    3. Are the stories relevant to the requirement?

    Requirement: {REQUIREMENT}
    Output: {output[:1500]}

    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:3] if "YES" in l)
    assert passed >= 2, f"QA Judge failed (got {passed}/4):\n{verdict}"


# ── Architect Agent ───────────────────────────────────────────────────────────

def test_architect_agent_generates_architecture():
    from app.agents.pm_agent.agent import PMAgent
    from app.agents.architect_agent.agent import ArchitectAgent
    pm_output = PMAgent().process(REQUIREMENT)
    arch_output, mermaid_output = ArchitectAgent().process(pm_output)

    verdict = llm_judge(f"""
    Review this architecture output and answer YES or NO for each:
    1. Does it describe system components or modules?
    2. Is it relevant to the requirement?
    3. Does the mermaid output contain any valid mermaid diagram syntax?

    Requirement: {REQUIREMENT}
    Architecture: {arch_output[:1000]}
    Mermaid: {mermaid_output[:500]}

    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:3] if "YES" in l)
    assert passed >= 2, f"QA Judge failed (got {passed}/4):\n{verdict}"

# ── Developer Agent ───────────────────────────────────────────────────────────

def test_developer_agent_generates_code():
    from app.agents.developer_agent.agent import DeveloperAgent
    output = DeveloperAgent().process(REQUIREMENT)

    verdict = llm_judge(f"""
    Review this generated code and answer YES or NO for each:
    1. Does it include route or endpoint handlers?
    2. Does it include a service or business logic layer?
    3. Based on what is visible, does the code appear syntactically valid?
    4. Does it address at least one of the requirements (create, list, or delete)?


    Requirement: {REQUIREMENT}
    Code files: {str(output)[:4000]}

    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:4] if "YES" in l)
    assert passed >= 3, f"QA Judge failed (got {passed}/4):\n{verdict}"

# ── QA Agent ──────────────────────────────────────────────────────────────────

def test_qa_agent_generates_tests():
    from app.agents.developer_agent.agent import DeveloperAgent
    from app.agents.qa_agent.agent import QAAgent
    dev_output = DeveloperAgent().process(REQUIREMENT)
    test_output = QAAgent().process(dev_output)

    verdict = llm_judge(f"""
    Review these generated tests and answer YES or NO for each:
    1. Do the tests cover the main endpoints (create, list, delete)?
    2. Are there assertions in the tests?
    3. Does the test file import or reference the code being tested?
    4. Is there at least one test function or test case?

    Tests: {str(test_output)[:3000]}

    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:4] if "YES" in l)
    assert passed >= 3, f"QA Judge failed (got {passed}/4):\n{verdict}"

# ── Review Agent ──────────────────────────────────────────────────────────────

def test_review_agent_generates_structured_review():
    from app.agents.review_agent.agent import ReviewAgent
    sample_code = """
    ### main.py
    ```python
    todos = []
    def create(item): todos.append(item)
    def list_all(): return todos
    def delete(i): todos.pop(i)
    """

    output = ReviewAgent().process(sample_code)

    verdict = llm_judge(f"""
    Review this code review output and answer YES or NO for each:
    1. Is it formatted as a numbered list?
    2. Does each item identify a specific issue or improvement?
    3. Are there at least 3 review items?

    Review output: {output[:1500]}

    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:3] if "YES" in l)
    assert passed >= 2, f"QA Judge failed (got {passed}/4):\n{verdict}"

# ── AutoFix Agent ──────────────────────────────────────────────────────────────

def test_autofix_agent_applies_corrections():
    from app.agents.autofix_agent.agent import AutoFixAgent
    sample_code = """

    main.py

    todos = []
    def create(item): todos.append(item)
    """
    review_comments = "1. [Bug] No input validation on create. Add a check that item is not empty."
    output = AutoFixAgent().process(sample_code, review_comments)


    verdict = llm_judge(f"""
    Review this auto-fixed code and answer YES or NO for each:
    1. Does the fixed code address the review comment about input validation?
    2. Is the output valid code?
    3. Is the fix minimal and targeted (not a complete rewrite)?

    Original review: {review_comments}
    Fixed code: {output[:1500]}

    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:3] if "YES" in l)
    assert passed >= 2, f"QA Judge failed (got {passed}/4):\n{verdict}"