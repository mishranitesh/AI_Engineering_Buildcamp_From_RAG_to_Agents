# Testing

## Type 1 — Unit Tests

Test the platform's own components: agents, tools, parsers.

Create tests/ at the multi-agent-dev-platform/ root:

```
multi-agent-dev-platform/
├── tests/
│   ├── __init__.py
│   ├── test_parsers.py          ← code parser, review comment parser, user story extractor
│   ├── test_state.py            ← WorkflowState fields and phase transitions
│   ├── test_generators.py       ← artifact writer, zip generator
│   ├── test_knowledge_base.py   ← KB retrieval, semantic relevance
│   ├── test_tools_mocked.py     ← GitHubTool and JiraTool (mocked API calls)
│   └── test_judge.py            ← LLM-as-Judge tests for all 6 agents

```

## Type 2 — Judge Tests (LLM-as-Judge)

Evaluate agent output quality using an LLM judge.

- File - tests/test_judge.py

## Run Unit Tests
```bash
cd multi-agent-dev-platform
source .venv/bin/activate
pytest tests/test_parsers.py tests/test_state.py tests/test_generators.py tests/test_knowledge_base.py tests/test_tools_mocked.py -v

# Output
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0 -- /Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/capstone/multi-agent-dev-platform/.venv/bin/python3.13
cachedir: .pytest_cache
rootdir: /Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/capstone/multi-agent-dev-platform
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 31 items

tests/test_parsers.py::test_extract_code_files_single_file PASSED                                                                                                                                        [  3%]
tests/test_parsers.py::test_extract_code_files_multiple_files PASSED                                                                                                                                     [  6%]
tests/test_parsers.py::test_extract_code_files_empty_input PASSED                                                                                                                                        [  9%]
tests/test_parsers.py::test_extract_code_files_no_match PASSED                                                                                                                                           [ 12%]
tests/test_parsers.py::test_extract_code_files_language_agnostic PASSED                                                                                                                                  [ 16%]
tests/test_parsers.py::test_parse_review_comments_splits_numbered_items PASSED                                                                                                                           [ 19%]
tests/test_parsers.py::test_parse_review_comments_preserves_content PASSED                                                                                                                               [ 22%]
tests/test_parsers.py::test_parse_review_comments_fallback_on_no_match PASSED                                                                                                                            [ 25%]
tests/test_parsers.py::test_parse_review_comments_filters_short_items PASSED                                                                                                                             [ 29%]
tests/test_parsers.py::test_extract_user_stories_picks_as_a_format PASSED                                                                                                                                [ 32%]
tests/test_parsers.py::test_extract_user_stories_caps_at_eight PASSED                                                                                                                                    [ 35%]
tests/test_parsers.py::test_extract_user_stories_fallback PASSED                                                                                                                                         [ 38%]
tests/test_state.py::test_workflow_state_defaults PASSED                                                                                                                                                 [ 41%]
tests/test_state.py::test_workflow_state_stores_requirement PASSED                                                                                                                                       [ 45%]
tests/test_state.py::test_workflow_state_jira_fields PASSED                                                                                                                                              [ 48%]
tests/test_state.py::test_workflow_state_pr_phase_transitions PASSED                                                                                                                                     [ 51%]
tests/test_generators.py::test_write_backend_files_creates_files PASSED                                                                                                                                  [ 54%]
tests/test_generators.py::test_write_backend_files_correct_content PASSED                                                                                                                                [ 58%]
tests/test_generators.py::test_write_tests_creates_test_dir PASSED                                                                                                                                       [ 61%]
tests/test_generators.py::test_write_architecture_creates_files PASSED                                                                                                                                   [ 64%]
tests/test_generators.py::test_write_review_joins_comments PASSED                                                                                                                                        [ 67%]
tests/test_generators.py::test_write_readme PASSED                                                                                                                                                       [ 70%]
tests/test_generators.py::test_create_zip_produces_file PASSED                                                                                                                                           [ 74%]
tests/test_knowledge_base.py::test_retrieve_returns_list PASSED                                                                                                                                          [ 77%]
tests/test_knowledge_base.py::test_retrieve_respects_n_results PASSED                                                                                                                                    [ 80%]
tests/test_knowledge_base.py::test_retrieve_returns_strings PASSED                                                                                                                                       [ 83%]
tests/test_knowledge_base.py::test_retrieve_semantic_relevance PASSED                                                                                                                                    [ 87%]
tests/test_knowledge_base.py::test_retrieve_different_queries_different_results PASSED                                                                                                                   [ 90%]
tests/test_tools_mocked.py::test_github_tool_create_branch PASSED                                                                                                                                        [ 93%]
tests/test_tools_mocked.py::test_github_tool_add_pr_comment PASSED                                                                                                                                       [ 96%]
tests/test_tools_mocked.py::test_jira_tool_issue_url PASSED                                                                                                                                              [100%]

============================================================================================== 31 passed in 4.39s ==============================================================================================
```

## Run Judge Tests (LLM-as-Judge)
```bash
pytest tests/test_judge.py -v

# Output
(.venv) niteshmishra@Mac multi-agent-dev-platform % pytest tests/test_judge.py -v
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0 -- /Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/capstone/multi-agent-dev-platform/.venv/bin/python3.13
cachedir: .pytest_cache
rootdir: /Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/capstone/multi-agent-dev-platform
configfile: pyproject.toml
plugins: anyio-4.13.0
collected 6 items

tests/test_judge.py::test_pm_agent_generates_user_stories PASSED                                                                                                                                         [ 16%]
tests/test_judge.py::test_architect_agent_generates_architecture PASSED                                                                                                                                  [ 33%]
tests/test_judge.py::test_developer_agent_generates_code PASSED                                                                                                                                          [ 50%]
tests/test_judge.py::test_qa_agent_generates_tests PASSED                                                                                                                                                [ 66%]
tests/test_judge.py::test_review_agent_generates_structured_review PASSED                                                                                                                                [ 83%]
tests/test_judge.py::test_autofix_agent_applies_corrections PASSED                                                                                                                                       [100%]

============================================================================================== 6 passed in 40.02s ==============================================================================================
```
Note: Judge tests call the OpenAI API and will incur cost (~$0.05 per run).

## Run All Tests
```bash
pytest tests/ -v
```


## CI/CD

Unit tests run automatically on every push via GitHub Actions (`.github/workflows/tests.yml`).

`test_knowledge_base.py` and `test_tools_mocked.py` are excluded from CI — the KB tests
require the seeded `knowledge_db/` to exist locally, and mocked tool tests need real
credentials at setup time. Run these locally after `make seed`.

## End-to-End Test Checklist

Run this after any significant change to verify the full pipeline works.

**Start all services:**
```bash
make api      # terminal 1 — FastAPI (port 8000)
make ui       # terminal 2 — Streamlit UI (port 8501)
make monitor  # terminal 3 — Monitoring dashboard (port 8502)
```

Open http://localhost:8501 and run through:

Phase 1 — PM Agent + JIRA

- Enter a project name and requirement
- Check "Create JIRA Epic & Stories" → click Run PM Agent
- Verify JIRA epic and story links appear

Phase 2 — Code Generation

- Uncheck "Create JIRA Epic & Stories"
- Check "Create Draft PR on GitHub"
- Click Stories confirmed — Generate Code
- Verify code generates, ZIP download appears, Draft PR link shows

Phase 3 — PR Lifecycle

- Uncheck "Create Draft PR on GitHub"
- Click Mark Ready for Review → phase indicator advances
- Select review comments → click Fix PR → verify AutoFix commit on GitHub
- Click Merge PR → verify merged status

Monitoring — open http://localhost:8502

- Agent elapsed times bar chart shows data
- Recent events log shows the run

Resume flow (session persistence)

- Restart the API server mid-flow (Ctrl+C → make api)
- Refresh browser → "Resume Session" appears in sidebar with project name
- Click Resume → UI picks up at the correct phase

Last verified: 2026-06-08 ✅


