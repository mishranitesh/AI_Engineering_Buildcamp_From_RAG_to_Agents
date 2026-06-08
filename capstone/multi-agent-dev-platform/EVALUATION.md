# Evaluation

## What is Evaluation?
Evaluation answers the question: "How well are our agents actually performing?"

Without evaluation you're flying blind — you run the agents, they produce output, but you don't know if it's good, consistent, or getting better or worse over time.

## Three layers we built

### Layer 1 — Ground Truth Dataset (ground_truth.json)
A set of hand-crafted known inputs with expected outputs:

```
Input:  "Build a Todo API with create, list, delete"
Expected:
  - At least 3 user stories
  - Stories mention: create, list, delete
  - Code has POST, GET, DELETE endpoints
  - At least 3 review items
```

Think of it like an exam answer key — you know what the correct answer looks like, so you can grade the agent's response against it.

Why hand-crafted matters: If you generate the ground truth with an LLM, you're asking the LLM to grade itself — biased. Hand-crafted means a human decided what "good" looks like.

### Layer 2 — LLM-as-Judge (run_evaluation.py)
For each ground truth sample, we:

1. Run the actual agent with the real requirement
2. Ask GPT-4.1 to compare the output against the expected criteria
3. Score each question YES/NO

```
PM Agent output → Judge asks:
  "Are there at least 3 stories?" → YES ✅
  "Do stories mention create/list/delete?" → YES ✅
  "Are stories actionable?" → YES ✅
  Score: 3/3
```

`Why use an LLM as judge?` Because agent output is free-form text — you can't do assert output == "expected string". The LLM judge understands meaning, not just exact matches.

Results showed:

```
todo-api:      PM 3/3 | Developer 3/4 | Review 3/3 → 90%
inventory-api: PM 3/3 | Developer 2/4 | Review 3/3 → 80%
user-auth-api: PM 3/3 | Developer 3/4 | Review 3/3 → 90%
```

This told us the Developer Agent is the weakest agent — not obvious without evaluation.

### Layer 3 — Parameter Tuning (tune_parameters.py)
Once we knew Developer Agent was weakest, we tested whether changing parameters could improve it:

KB retrieval size:
```
n_results=1 → score 3/5   (too little context)
n_results=3 → score 4/5   ← optimal
n_results=5 → score 4/5   (same quality, more tokens wasted)
```

Model:
```
gpt-4o-mini → score 2/5   (cheaper but worse)
gpt-4.1     → score 3/5   ← optimal
```

`What this proved`: Our current configuration n_results=3 + gpt-4.1 is already optimal — backed by data, not guesswork.

## How it helped — concrete impact

| Without Evaluation | With Evaluation |
|-------------------|-----------------|
| "The agents seem to work" | "Agents score 87% on average" |
| No idea which agent is weakest | Developer Agent clearly identified as weakest |
| Configuration chosen by intuition | Configuration validated by tuning data |
| No regression detection | Run evaluation again after any change to detect regressions |

## The full cycle

```
Write ground truth (human judgment of what "good" looks like)
         ↓
Run agents on ground truth inputs
         ↓
LLM judge scores outputs against expected criteria
         ↓
Identify weak agents (Developer Agent = 80-90%)
         ↓
Tune parameters (KB size, model)
         ↓
Confirm best configuration with data
         ↓
Document findings → ship with confidence
```

## Full design

```
multi-agent-dev-platform/
├── evaluation/
│   ├── ground_truth.json      ← hand-crafted dataset (bonus points)
│   ├── run_evaluation.py      ← LLM judge against ground truth
│   ├── tune_parameters.py     ← prompt/model/KB tuning
│   └── results/               ← saved evaluation outputs
├── EVALUATION.md              ← full documentation
```

## Step 1 — Hand-crafted ground truth dataset
Create evaluation/ground_truth.json — write these manually, not LLM-generated

File: `evaluation/ground_truth.json`

Each sample defines:
- `requirement` — the input to the platform
- `expected.min_user_stories` — minimum stories PM should generate
- `expected.required_story_keywords` — keywords that must appear in stories
- `expected.required_endpoints` — HTTP methods the generated code must include
- `expected.review_min_items` — minimum review comments expected

## Step 2 — evaluation/run_evaluation.py
LLM judge against ground truth

File: `evaluation/run_evaluation.py`

Run LLM Evaluation: 

```bash
cd multi-agent-dev-platform
source .venv/bin/activate
python -m evaluation.run_evaluation

# Output
(.venv) niteshmishra@Mac multi-agent-dev-platform % python -m evaluation.run_evaluation

==================================================
Evaluating: todo-api
==================================================
PM Agent: 3/3
2026-06-06 15:22:38 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Keep business logic in a service la']
Developer Agent: 3/4
2026-06-06 15:22:44 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Keep business logic in a service la']
2026-06-06 15:22:50 | INFO | KB retrieved 3 patterns for review: ['Best practice: Separate data models (DB schema), b', 'Best practice: Define explicit request and respons', 'Best practice: Service layer should raise domain e']
Review Agent: 3/3

==================================================
Evaluating: inventory-api
==================================================
PM Agent: 3/3
2026-06-06 15:22:59 | INFO | KB retrieved 3 patterns: ['Best practice: Define explicit request and respons', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Separate data models (DB schema), b']
Developer Agent: 2/4
2026-06-06 15:23:06 | INFO | KB retrieved 3 patterns: ['Best practice: Define explicit request and respons', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Separate data models (DB schema), b']
2026-06-06 15:23:10 | INFO | KB retrieved 3 patterns for review: ['Best practice: Define explicit request and respons', 'Best practice: Service layer should raise domain e', 'Best practice: Separate data models (DB schema), b']
Review Agent: 3/3

==================================================
Evaluating: user-auth-api
==================================================
PM Agent: 3/3
2026-06-06 15:23:21 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Define explicit request and respons']
Developer Agent: 3/4
2026-06-06 15:23:28 | INFO | KB retrieved 3 patterns: ['Best practice: Separate data models (DB schema), b', 'Best practice: Validate and sanitize all inputs at', 'Best practice: Define explicit request and respons']
2026-06-06 15:23:38 | INFO | KB retrieved 3 patterns for review: ['Best practice: Define explicit request and respons', 'Best practice: Separate data models (DB schema), b', 'Best practice: Service layer should raise domain e']
Review Agent: 3/3

==================================================
EVALUATION SUMMARY
==================================================
todo-api: 9/10 (90%)
inventory-api: 8/10 (80%)
user-auth-api: 9/10 (90%)

```
Results saved to `evaluation/results/latest.json`

The evaluation ran successfully across all 3 ground truth samples:

| Sample         | PM  | Developer | Review | Total |
|---------------|-----|-----------|--------|-------|
| todo-api      | 3/3 | 3/4       | 3/3    | 90%   |
| inventory-api | 3/3 | 2/4       | 3/3    | 80%   |
| user-auth-api | 3/3 | 3/4       | 3/3    | 90%   |

Key observations:

- PM and Review agents score perfectly across all samples
- Developer Agent is the weak point — consistently losing 1-2 points, likely on "service layer separation" or "complete enough to run" questions
- Inventory API scores lowest (80%) — the more complex the requirement, the harder it is for the Developer Agent

## Step 3 — evaluation/tune_parameters.py
Compares KB retrieval size and model — earns the 3rd point

File: `evaluation/tune_parameters.py`

## Run Parameter Tuning
```bash
python -m evaluation.tune_parameters

# Output
(.venv) niteshmishra@Mac multi-agent-dev-platform % python -m evaluation.tune_parameters
=== Tuning KB Retrieval Size ===
KB n_results=1: score=3
KB n_results=3: score=4
KB n_results=5: score=4

=== Tuning Model ===
Model=gpt-4.1: score=3
Model=gpt-4o-mini: score=2

Best KB n_results: n_results=3
Best model: gpt-4.1
```
Compares:
- KB retrieval size: n_results = 1, 3, 5
- Model: gpt-4.1 vs gpt-4o-mini

Results saved to `evaluation/results/tuning.json`

**KB Retrieval Size** (n_results)

| n_results | Score |
|---|---|
| 1 | 3/5 |
| 3 | 4/5 ← selected |
| 5 | 4/5 |

**Finding:** n_results=3 and n_results=5 perform equally. n_results=3 is chosen
as it uses fewer tokens with no quality loss.

**Model Comparison**

| Model | Score |
|---|---|
| gpt-4.1 | 3/5 ← selected |
| gpt-4o-mini | 2/5 |

**Finding:** gpt-4.1 outperforms gpt-4o-mini. Current configuration is optimal.

**Conclusion**
- Current configuration (n_results=3, gpt-4.1) is validated as optimal by tuning.
- Overall platform scores 87% average across 3 ground truth samples.
- Developer Agent is the weakest link — future improvement should focus on
- strengthening its prompt for multi-endpoint APIs.

Good news — the tuning confirms your current settings are already optimal. No code changes needed — the evaluation just proves it with data

## Manual Evaluation
For each sample in `ground_truth.json`:
1. Run the full platform with the requirement
2. Check generated files against `expected.required_files`
3. Check user stories against `expected.required_story_keywords`
4. Score each agent 0-3 and record in `evaluation/results/manual.md`

## Manual Evaluation Results

| Sample | PM Stories | Keywords | Endpoints | Review Items | Notes |
|---|---|---|---|---|---|
| todo-api | ✅ 4 stories | ✅ create/list/delete | ✅ POST/GET/DELETE | ✅ 4 items | Service layer present |
| inventory-api | ✅ 5 stories | ✅ add/get/update/delete | ✅ POST/GET/PUT/DELETE | ✅ 3 items | Missing input validation |
| user-auth-api | ✅ 3 stories | ✅ register/login/logout | ✅ POST | ✅ 3 items | Token handling not generated |

## Observations

| Sample | Notes |
|---|---|
| todo-api | All 3 agents performed well. Developer generated a clean service/route separation. Review agent identified 4 specific, actionable issues. ZIP download and GitHub PR created successfully. |
| inventory-api | Most complex requirement — Developer Agent struggled slightly (scored 2/4 in LLM eval). Generated endpoints but skipped input validation on quantity field. PM Agent correctly extracted all 4 CRUD operations into separate stories. |
| user-auth-api | PM Agent correctly structured register/login/logout as 3 distinct stories. Developer Agent generated POST endpoints but omitted token/session handling — the requirement said "in-memory storage" which may have led the agent to skip auth tokens. Review Agent correctly flagged this as a gap. |

## Key Findings

- **PM Agent** is the most reliable — scored 3/3 across all 3 samples in both automated and manual evaluation
- **Developer Agent** is the weakest link — performs well on simple CRUD (todo-api) but misses implementation details on complex or security-sensitive requirements (inventory validation, auth tokens)
- **Review Agent** reliably catches what Developer Agent misses — the review output correctly identified missing input validation and token handling in both cases
- **Overall**: platform handles standard REST API generation well; prompt engineering for the Developer Agent on security/auth requirements is the primary improvement opportunity

## Automated vs Manual Comparison

| Sample | Automated Score | Manual Pass |
|---|---|---|
| todo-api | 9/10 (90%) | ✅ All criteria met |
| inventory-api | 8/10 (80%) | ✅ All criteria met (input validation noted as gap) |
| user-auth-api | 9/10 (90%) | ✅ All criteria met (token handling noted as gap) |

Automated and manual evaluations are consistent — both identify the Developer Agent on complex requirements as the area for improvement.


## Latest Evaluation Results (2026-06-08)

| Sample | PM | Developer | Review | Total |
|---|---|---|---|---|
| todo-api | 3/3 | 4/4 | 3/3 | **100%** |
| inventory-api | 3/3 | 3/4 | 3/3 | 90% |
| user-auth-api | 3/3 | 3/4 | 3/3 | 90% |
| bookmark-api *(from feedback)* | 3/3 | 3/4 | 3/3 | 90% |

**Average: 92.5%** — up from 87% (3 samples). `bookmark-api` added automatically via user feedback → `make seed-gt`.

**Notable improvement**: todo-api jumped from 90% → 100% (Developer Agent now 4/4 vs 3/4 previously). The bookmark-api seeded from real user feedback slots right in at 90%, consistent with the others.
