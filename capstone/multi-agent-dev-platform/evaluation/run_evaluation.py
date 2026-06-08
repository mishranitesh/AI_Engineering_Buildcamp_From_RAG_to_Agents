import json
import os
from openai import OpenAI
from app.agents.pm_agent.agent import PMAgent
from app.agents.developer_agent.agent import DeveloperAgent
from app.agents.review_agent.agent import ReviewAgent
from app.orchestration.workflow import WorkflowOrchestrator

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
orchestrator = WorkflowOrchestrator()


def llm_judge(prompt: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def evaluate_pm(requirement: str, expected: dict) -> dict:
    output = PMAgent().process(requirement)
    stories = orchestrator._extract_user_stories(output)

    verdict = llm_judge(f"""
    Given this requirement and PM output, answer YES or NO for each:
    1. Are there at least {expected['min_user_stories']} user stories?
    2. Do the stories cover these keywords: {expected['required_story_keywords']}?
    3. Are the stories actionable and specific?

    Requirement: {requirement}
    PM Output: {output[:1500]}
    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:3] if "YES" in l)
    return {"agent": "PM", "passed": passed, "total": 3, "verdict": verdict}


def evaluate_developer(requirement: str, expected: dict) -> dict:
    output = DeveloperAgent().process(requirement)
    files = list(output.keys())

    verdict = llm_judge(f"""
    Given this requirement and generated code, answer YES or NO for each:
    1. Does it include these HTTP methods: {expected['required_endpoints']}?
    2. Does it include at least one of these files: {expected['required_files']}?
    3. Is there separation between routes and business logic?
    4. Is the code complete enough to run?

    Requirement: {requirement}
    Files generated: {files}
    Code: {str(output)[:3000]}
    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:4] if "YES" in l)
    return {"agent": "Developer", "passed": passed, "total": 4, "verdict": verdict}


def evaluate_review(requirement: str, expected: dict) -> dict:
    dev_output = DeveloperAgent().process(requirement)
    review_output = ReviewAgent().process(str(dev_output))
    items = orchestrator._parse_review_comments(review_output)

    verdict = llm_judge(f"""
    Given this code review output, answer YES or NO for each:
    1. Are there at least {expected['review_min_items']} review items?
    2. Is each item specific and actionable?
    3. Does the review follow a numbered list format?

    Review: {review_output[:1500]}
    Answer YES/NO one per line.
    """)

    lines = [l for l in verdict.strip().split("\n") if l.strip()]
    passed = sum(1 for l in lines[:3] if "YES" in l)
    return {"agent": "Review", "passed": passed, "total": 3, "verdict": verdict}


def run_evaluation():
    with open("evaluation/ground_truth.json") as f:
        dataset = json.load(f)

    results = []
    for sample in dataset:
        print(f"\n{'='*50}")
        print(f"Evaluating: {sample['id']}")
        print(f"{'='*50}")

        sample_results = {"id": sample["id"], "requirement": sample["requirement"], "agents": []}

        for evaluate_fn in [evaluate_pm, evaluate_developer, evaluate_review]:
            result = evaluate_fn(sample["requirement"], sample["expected"])
            sample_results["agents"].append(result)
            score = f"{result['passed']}/{result['total']}"
            print(f"{result['agent']} Agent: {score}")

        results.append(sample_results)

    # Save results
    os.makedirs("evaluation/results", exist_ok=True)
    with open("evaluation/results/latest.json", "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    print(f"\n{'='*50}")
    print("EVALUATION SUMMARY")
    print(f"{'='*50}")
    for r in results:
        total_passed = sum(a["passed"] for a in r["agents"])
        total_questions = sum(a["total"] for a in r["agents"])
        pct = round(total_passed / total_questions * 100)
        print(f"{r['id']}: {total_passed}/{total_questions} ({pct}%)")


if __name__ == "__main__":
    run_evaluation()
