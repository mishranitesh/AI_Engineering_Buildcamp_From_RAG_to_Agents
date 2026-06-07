from app.parsers.code_parser import extract_code_files
from app.orchestration.workflow import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()


# ── code_parser ───────────────────────────────────────────────────────────────

def test_extract_code_files_single_file():
    text = "### main.py\n```python\nprint('hello')\n```"
    result = extract_code_files(text)
    assert "main.py" in result
    assert "print('hello')" in result["main.py"]

def test_extract_code_files_multiple_files():
    text = "### main.py\n```python\ncode1\n```\n### models.py\n```python\ncode2\n```"
    result = extract_code_files(text)
    assert len(result) == 2
    assert "main.py" in result
    assert "models.py" in result

def test_extract_code_files_empty_input():
    assert extract_code_files("") == {}

def test_extract_code_files_no_match():
    assert extract_code_files("no code blocks here") == {}

def test_extract_code_files_language_agnostic():
    text = "### app.ts\n```typescript\nconst x = 1;\n```"
    result = extract_code_files(text)
    assert "app.ts" in result

# ── review parser ─────────────────────────────────────────────────────────────

def test_parse_review_comments_splits_numbered_items():
    review = "1. [Bug] Missing validation\n2. [Improvement] Add logging\n3. [Test] No edge cases"
    result = orchestrator._parse_review_comments(review)
    assert len(result) == 3

def test_parse_review_comments_preserves_content():
    review = "1. [Bug] Missing validation in the input field"
    result = orchestrator._parse_review_comments(review)
    assert "Missing validation" in result[0]

def test_parse_review_comments_fallback_on_no_match():
    review = "This is a general review with no numbered items."
    result = orchestrator._parse_review_comments(review)
    assert len(result) == 1
    assert result[0] == review

def test_parse_review_comments_filters_short_items():
    review = "1. [Bug] x\n2. [Bug] This is a meaningful review comment that is long enough"
    result = orchestrator._parse_review_comments(review)
    assert all(len(r) > 10 for r in result)

# ── user story extractor ──────────────────────────────────────────────────────

def test_extract_user_stories_picks_as_a_format():
    pm_output = "## User Stories\nAs a user I want to create items so that I can manage inventory\nAs a user I want to list items\n## Acceptance Criteria\nsome criteria"
    result = orchestrator._extract_user_stories(pm_output)
    assert len(result) >= 1
    assert any("As a user" in s for s in result)

def test_extract_user_stories_caps_at_eight():
    stories = "\n".join([f"As a user I want to do thing number {i} in the system" for i in range(20)])
    pm_output = f"## User Stories\n{stories}\n## Acceptance Criteria\ndone"
    result = orchestrator._extract_user_stories(pm_output)
    assert len(result) <= 8

def test_extract_user_stories_fallback():
    result = orchestrator._extract_user_stories("no user stories here")
    assert result == ["Implement core functionality"]