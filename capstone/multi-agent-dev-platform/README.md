# Multi-Agent Software Development Platform

An AI-powered platform where specialized agents collaborate to convert requirements into architecture, code, tests, reviews, and GitHub PRs.

## Architecture

```
Requirement → PM Agent → JIRA Epic/Stories → [Human confirms]
                                    ↓
                          Architect → Developer → QA → Review Agent
                                    ↓
                          Draft PR → Ready for Review → AutoFix → Merge
```

## Prerequisites

- Python 3.11+
- OpenAI API key
- GitHub personal access token (repo scope)
- JIRA account (optional)

## Setup

### 1. Configure environment variables
Create a `.env` file in `multi-agent-dev-platform/`:
```
OPENAI_API_KEY=your_openai_api_key

# GitHub Integration (Phase 2)
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_target_repo_name
GITHUB_BASE_PATH=capstone/testing/ai_generated_projects

# JIRA Integration (Phase 3)
JIRA_URL=https://yourorg.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=KAN
```

## Quick Start
```bash
make install   # create venv and install dependencies
make seed      # seed the knowledge base (run once)
make api       # terminal 1 — start FastAPI server (port 8000)
make ui        # terminal 2 — start main UI (port 8501)
make monitor   # terminal 3 — start monitoring dashboard (port 8502)
```

## Usage

1. Open `http://localhost:8501`
2. Check **"Create JIRA Epic & Stories"** and/or **"Create Draft PR on GitHub"** in the sidebar
3. Enter a requirement eg - `Build a simple Todo API using FastAPI with endpoints to create, list, and delete todos. Use in-memory storage.` and click **"Run PM Agent"**
4. Review JIRA stories, 
     - then uncheck **Create JIRA Epic & Stories"** 
     - then **"✅ Create Draft PR on GitHub"** to create Draft PR 
     - then click **"✅ Stories confirmed — Generate Code"**
     - Once Draft PR is created - uncheck **"✅ Create Draft PR on GitHub"**
5. Use the PR Lifecycle panel to advance through Draft → Review → Fix → Merge

## Testing

### Run unit tests
```bash
pytest tests/test_parsers.py tests/test_state.py tests/test_generators.py \
       tests/test_knowledge_base.py tests/test_tools_mocked.py -v
```

### Run judge tests (LLM-as-Judge)
```bash
pytest tests/test_judge.py -v
```

### Run evaluation
```bash
python -m evaluation.run_evaluation
```

### Run parameter tuning
```bash
python -m evaluation.tune_parameters
```

## Project Structure

```
multi-agent-dev-platform/
├── app/
│   ├── agents/          # PM, Architect, Developer, QA, Review, AutoFix agents
│   ├── tools/           # GitHubTool, JiraTool, KnowledgeBase
│   ├── orchestration/   # WorkflowOrchestrator, WorkflowState
│   ├── generators/      # File, ZIP, README generators
│   ├── parsers/         # Code and Mermaid parsers
│   └── monitoring/      # Loguru logger
├── ui/
│   ├── streamlit_app.py # Main application UI
│   └── monitoring.py    # Monitoring dashboard
├── tests/               # Unit and judge tests
├── evaluation/          # Ground truth dataset and evaluation scripts
├── logs/                # Runtime logs
├── knowledge_db/        # ChromaDB vector store (auto-generated)
├── generated_projects/  # Output from each workflow run
├── seed_knowledge_base.py
└── .env                 # Environment variables (not committed)
```

## Documentation

| Document | Description |
|---|---|
| [TOOLS.md](TOOLS.md) | GitHub, JIRA, and Knowledge Base tool documentation |
| [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md) | KB design, retrieval evaluation, results |
| [EVALUATION.md](EVALUATION.md) | Evaluation framework, ground truth, tuning results |
| [Testing.md](Testing.md) | Test strategy, how to run tests |
| [Monitoring.md](Monitoring.md) | Monitoring setup and dashboard access |
