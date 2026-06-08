# Tools Documentation

## Tool Summary

| Tool | File | Used By | Trigger |
|---|---|---|---|
| GitHubTool | `app/tools/github_tool.py` | WorkflowOrchestrator | PR lifecycle phases (draft → review → fix → merge) |
| JiraTool | `app/tools/jira_tool.py` | WorkflowOrchestrator | PM phase — epic, stories, tasks creation |
| KnowledgeBase | `app/tools/knowledge_base.py` | DeveloperAgent, ReviewAgent | Before every LLM call — RAG retrieval augments the prompt |

The KnowledgeBase tool implements the RAG pattern: query is embedded and semantically matched against stored best practices, then injected into the agent's prompt before the LLM generates output.

## 1. GitHubTool
**File:** `app/tools/github_tool.py`  
**Purpose:** Manages the full PR lifecycle on GitHub

| Method | Description |
|---|---|
| `create_branch()` | Creates a new feature branch from main |
| `commit_files()` | Commits generated code files to the branch |
| `create_draft_pull_request()` | Opens a Draft PR for developer review |
| `mark_pr_ready_for_review()` | Converts draft PR to ready via GraphQL |
| `add_pr_comment()` | Posts review comments on the PR |
| `merge_pull_request()` | Merges the PR to main |

**Used by:** `WorkflowOrchestrator` phases 1–4  
**Config:** `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_BASE_PATH` in `.env`

---

## 2. JiraTool
**File:** `app/tools/jira_tool.py`  
**Purpose:** Creates and retrieves JIRA issues from PM Agent output

| Method | Description |
|---|---|
| `create_epic()` | Creates an Epic for the project requirement |
| `create_story()` | Creates a Story under the Epic per user story |
| `create_task()` | Creates a Task under a Story |
| `get_stories()` | Fetches confirmed stories from JIRA before code generation |

**Used by:** `WorkflowOrchestrator._create_jira_epic_and_stories()` and `run_codegen_phase()`  
**Config:** `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` in `.env`

---

## 3. KnowledgeBase
**File:** `app/tools/knowledge_base.py`  
**Purpose:** RAG retrieval of best practices to augment agent prompts

See [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md) for full documentation.

**Used by:** `DeveloperAgent`, `ReviewAgent`


