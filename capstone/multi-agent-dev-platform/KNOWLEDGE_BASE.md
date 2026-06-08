# Knowledge Base & Retrieval

## Overview
A ChromaDB vector knowledge base that augments the Developer and Review agents with
retrieved best practices before generating or reviewing code.

## Location
`knowledge_db/` — ChromaDB persistent storage (auto-created on first run)

## Seeding
Run once to populate the knowledge base:
```bash
python seed_knowledge_base.py

# Output 
# Knowledge base seeded.
```

## What's in the Knowledge Base

| Pattern ID | Type | Description |
|---|---|---|
| service-layer | best_practice | Keep business logic in service layer, not route handlers |
| session-management | best_practice | Always release DB sessions/connections in finally blocks |
| input-validation | best_practice | Validate inputs at API boundary using schema validation |
| http-exceptions | best_practice | Service layer raises domain exceptions, API layer translates to HTTP |
| test-isolation | best_practice | Each test fully isolated with setup/teardown fixtures |
| error-handling | best_practice | Always rollback on failure to keep system in consistent state |
| api-contracts | best_practice | Define explicit request/response schemas, never expose internal models |
| separation-of-concerns | best_practice | Separate DB models, domain logic, and API schemas into distinct layers |

## Language Independence

The knowledge base is **language-agnostic** — all patterns are framework and language neutral.
The LLM applies the retrieved best practices in whichever language it is generating code for
(Python, Node.js, Go, etc.). This avoids the need for separate knowledge bases per language.


## How Retrieval Works

1. Agent receives a requirement or code snippet
2. Query is embedded using `text-embedding-3-small`
3. Top-3 semantically similar documents retrieved from ChromaDB
4. Retrieved patterns prepended to the agent's prompt as context

```
Requirement → Embed → ChromaDB Query → Top-3 Patterns → Agent Prompt → LLM
```

## Agents Using the Knowledge Base

| Agent | Query | Purpose |
|---|---|---|
| DeveloperAgent | Project requirement | Retrieve coding patterns before generating code |
| ReviewAgent | Code being reviewed | Retrieve known bug patterns to guide review |

## Retrieval Evaluation

Compared two approaches across 5 test queries:

| Query | Semantic Top-1 | Semantic Relevant? | Keyword Top-1 | Keyword Relevant? |
|---|---|---|---|---|
| "route handler doing too much work" | service-layer | ✅ | service-layer | ✅ |
| "database connection not released" | session-management | ✅ | ❌ no match | ❌ |
| "how to check request body fields" | input-validation | ✅ | ❌ no match | ❌ |
| "service throws 404 error" | http-exceptions | ✅ | http-exceptions | ✅ |
| "tests affecting each other" | test-isolation | ✅ | ❌ no match | ❌ |

**Precision@3 — Semantic: 100% | Keyword: 40%**

**Winner: Semantic search** — keyword matching fails on paraphrase queries
because the query wording doesn't literally match document text.
Semantic search handles natural language variation correctly, making it
the right approach for a language-neutral knowledge base where the same
concept can be expressed in many ways.

## Model Used
- Embedding model: `text-embedding-3-small` (OpenAI)
- Vector store: ChromaDB (local persistent)
- Similarity metric: Cosine similarity (ChromaDB default)
