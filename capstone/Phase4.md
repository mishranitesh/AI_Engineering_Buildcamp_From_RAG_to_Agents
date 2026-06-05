# Revisit Evaluation Criteria 

# Knowledge Base and Retrieval
This criterion evaluates your use of a knowledge base and retrieval methods.

Scoring:
- No knowledge database is used in the project: 0 points
- A knowledge base is used: 1 point
- A knowledge base is used, retrieval is properly evaluated, the best performing search approach is used, and everything is documented: 2 points

## Current Score: 0 / 2
No knowledge base or retrieval system exists anywhere in the project. All agents make pure LLM calls with no external knowledge.

## To reach 2/2 — here's what's needed:

### What to build

The most natural fit is a `Code Patterns & Best Practices Knowledge Base` that the Developer and Review agents query before generating/reviewing code.

Seeded with:

- Framework-specific best practices (FastAPI, SQLAlchemy, pytest patterns)
- Common bug patterns and their fixes
- Architecture templates (REST API, service layer, repository pattern)
- Previously generated and reviewed code from past runs

Used by:

- DeveloperAgent — retrieves relevant patterns before generating code
- ReviewAgent — retrieves known bug patterns to guide review

### Implementation plan

```
Step 1 — Add ChromaDB (local, no infra needed):

pip install chromadb openai

Step 2 — Create app/tools/knowledge_base.py

Step 3 — Seed the KB with a seed_knowledge_base.py script:

```

### Retrieval evaluation (required for 2/2)
Compare two approaches and document results:

### Knowledge Retrieval Strategy

| Approach        | Description                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Semantic Search | Uses ChromaDB with `text-embedding-3-small` embeddings to retrieve contextually relevant information from the knowledge base |
| Keyword Search  | Uses simple grep/substring matching against knowledge base documents for exact term and phrase lookups                       |

### Retrieval Flow

```text
User Query
    │
    ▼
Hybrid Retrieval
    │
    ├── Semantic Search
    │      └── ChromaDB + text-embedding-3-small
    │
    └── Keyword Search
           └── Grep / Substring Matching
    │
    ▼
Combine Results
    │
    ▼
Provide Context to AI Agents
```

### Why Use Both?

* **Semantic Search** finds relevant content even when wording differs from the original documentation.
* **Keyword Search** is effective for exact matches such as API names, class names, file paths, and technical terms.
* Combining both approaches improves retrieval accuracy and reduces missed requirements.

Metric: for 5 test queries, measure how many of the top-3 results are actually relevant (manual precision score). Document which approach wins and why.

### Add a KNOWLEDGE_BASE.md explaining:

What's in the KB and why
How retrieval is used by each agent
Evaluation results showing semantic > keyword

### Ref: Knowledge_Base.md

### Testing

```
Requirement to enter:

Build a simple Todo API using FastAPI with endpoints to create, list, and delete todos. Use in-memory storage.

Step 1 — Seed the KB first (only needed once):

cd multi-agent-dev-platform
python seed_knowledge_base.py


Expected Output - Knowledge base seeded and created knowledge_db/ folder

Step 2 — Start the server:

uvicorn app.main:app --reload --reload-dir app


Step 3 — Full flow on UI http://localhost:8501:

## End-to-End Workflow Validation

| Step | Action                                          | Expected Result                                                          |
| ---- | ----------------------------------------------- | ------------------------------------------------------------------------ |
| 1    | Check **"Create JIRA Epic & Stories"**          | Workflow configured to create project artifacts in JIRA                  |
| 2    | Paste the Todo API requirement                  | Requirement is loaded and ready for analysis                             |
| 3    | Click **"Run PM Agent"**                        | One Epic and three Stories are created in JIRA                           |
| 4    | Click **"✅ Stories Confirmed — Generate Code"** | Architecture, code, tests, documentation, and pull request are generated |
| 5    | Check API logs                                  | Knowledge Base retrieval and context injection are visible in logs       |

### Expected Flow

User Requirement
        │
        ▼
PM Agent
        │
        ▼
JIRA Epic + 3 Stories
        │
        ▼
User Reviews Stories
        │
        ▼
Generate Code
        │
        ├── KB Retrieval
        ├── Architecture Agent
        ├── Developer Agents
        ├── Test Agent
        └── Review Agent
        │
        ▼
Generated Repository + Pull Request


Step 4 — Verify KB is being used — look for this in the API logs:

INFO | Developer Agent done | ...

Add a temporary log line in developer_agent/agent.py to confirm retrieval:

def process(self, requirement: str) -> dict:
    patterns = retrieve(requirement, n_results=3)
    logger.info(f"KB retrieved {len(patterns)} patterns: {[p[:50] for p in patterns]}")
    ...

You should see something like:

INFO | KB retrieved 3 patterns: ['Best practice: Keep business logic...', 'Best practice: Validate and sanitize...', ...]

That confirms the KB is being queried and injected into the agent prompt before code generation.

Add similar log in review_agent/agent.py

def process(self, code: str) -> str:
    patterns = retrieve(code[:500], n_results=3)
    logger.info(f"KB retrieved {len(patterns)} patterns for review: {[p[:50] for p in patterns]}")
    context = "\n".join(f"- {p}" for p in patterns)
    augmented_input = f"## Known Best Practices to Check Against\n{context}\n\n## Code to Review\n{code}"
    return self.run(augmented_input)

That confirms both agents are using the KB.
```

### How KB contribute / help LLM ?

Without KB:
```
LLM prompt:
"You are a Senior Code Reviewer. Review this code: [code]"

LLM has to rely entirely on its training data to decide what to look for.
```

With KB:
```
LLM prompt:
"You are a Senior Code Reviewer.

## Known Best Practices to Check Against
- Best practice: Keep business logic in a service layer, not route handlers
- Best practice: Service layer raises domain exceptions, API layer translates to HTTP
- Best practice: Each test should be fully isolated with setup/teardown fixtures

## Code to Review
[code]"

LLM is now guided to specifically check for these patterns.
```

Concrete impact:

| Without Knowledge Base                 | With Knowledge Base                                                    |
| -------------------------------------- | ---------------------------------------------------------------------- |
| May miss service layer violations      | Explicitly checks for service layer violations and architectural rules |
| Generic review based on model training | Targeted review based on project-specific standards                    |
| Different results across runs          | More consistent and focused review findings                            |
| No project-specific knowledge          | Can enforce your team's coding, testing, and architecture standards    |


Key Advantage:

The Knowledge Base transforms the Review Agent from a general-purpose code reviewer into a project-aware reviewer that understands your organization's architecture guidelines, coding standards, testing practices, and engineering conventions.

The real power — the KB is your team's knowledge, not just general best practices. Over time you can add:

- Past bugs found in your codebase
- Architecture decisions specific to your project
- Patterns your team has agreed on

So the more you seed it, the more the LLM behaves like a senior engineer who knows your codebase — not just a generic code reviewer.


### Logs 

```
INFO:     Application startup complete.
2026-06-04 20:24:36 | INFO | PM phase started | requirement='Build a simple Todo API using FastAPI with endpoints to create, list, and delete...'
2026-06-04 20:24:40 | INFO | PM Agent done | elapsed=4.2s
2026-06-04 20:24:41 | INFO | JIRA Epic created | key=KAN-84
2026-06-04 20:24:42 | INFO | JIRA Story created | key=KAN-85
2026-06-04 20:24:43 | INFO | JIRA Story created | key=KAN-86
2026-06-04 20:24:44 | INFO | JIRA Story created | key=KAN-87
INFO:     127.0.0.1:54013 - "POST /run-pm HTTP/1.1" 200 OK
2026-06-04 20:25:16 | INFO | Fetched 3 confirmed stories from JIRA
2026-06-04 20:25:21 | INFO | Architect Agent done | elapsed=4.9s
2026-06-04 20:25:22 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Keep business logic in a service la']
2026-06-04 20:25:30 | INFO | Developer Agent done | files=['main.py', 'models.py', 'schemas.py', 'services.py'] | elapsed=8.2s
2026-06-04 20:25:43 | INFO | QA Agent done | elapsed=13.9s
2026-06-04 20:25:44 | INFO | KB retrieved 3 patterns for review: ['Best practice: Separate data models (DB schema), b', 'Best practice: Service layer should raise domain e', 'Best practice: Define explicit request and respons']
2026-06-04 20:25:55 | INFO | Review Agent done | elapsed=11.8s
DEBUG GitHub: owner=mishranitesh, repo=AI_Engineering_Buildcamp_From_RAG_to_Agents, token_set=True
2026-06-04 20:26:08 | INFO | Phase 1 done | draft PR=https://github.com/mishranitesh/AI_Engineering_Buildcamp_From_RAG_to_Agents/pull/13
INFO:     127.0.0.1:54027 - "POST /run-codegen HTTP/1.1" 200 OK
DEBUG GitHub: owner=mishranitesh, repo=AI_Engineering_Buildcamp_From_RAG_to_Agents, token_set=True
2026-06-04 20:27:40 | INFO | Phase 2 done | PR marked ready | pr=13
INFO:     127.0.0.1:54250 - "POST /pr-transition HTTP/1.1" 200 OK
DEBUG GitHub: owner=mishranitesh, repo=AI_Engineering_Buildcamp_From_RAG_to_Agents, token_set=True
2026-06-04 20:28:00 | INFO | Phase 3 done | fixed files=['schemas.py']
INFO:     127.0.0.1:54253 - "POST /pr-transition HTTP/1.1" 200 OK
DEBUG GitHub: owner=mishranitesh, repo=AI_Engineering_Buildcamp_From_RAG_to_Agents, token_set=True
2026-06-04 20:28:18 | INFO | Phase 4 done | PR merged | pr=13
INFO:     127.0.0.1:54256 - "POST /pr-transition HTTP/1.1" 200 OK
```

Mainly

```
2026-06-04 20:25:22 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Keep business logic in a service la']

2026-06-04 20:25:44 | INFO | KB retrieved 3 patterns for review: ['Best practice: Separate data models (DB schema), b', 'Best practice: Service layer should raise domain e', 'Best practice: Define explicit request and respons']
```

The entire end-to-end flow worked perfectly:

```
PM Agent          → 3 JIRA Stories created (KAN-85, 86, 87)
JIRA confirmed    → 3 stories fetched back
Architect Agent   → done
Developer Agent   → KB retrieved 3 patterns → 4 files generated
QA Agent          → tests generated
Review Agent      → KB retrieved 3 patterns → review complete
GitHub Phase 1    → Draft PR #13 created
GitHub Phase 2    → PR marked ready for review
GitHub Phase 3    → AutoFix applied (schemas.py fixed)
GitHub Phase 4    → PR merged to main ✅
```

KB is working — both agents retrieved 3 relevant patterns before running, confirming the knowledge base is actively contributing to code generation and review.

Full Phase 3 + Phase 4 (Knowledge Base) complete.