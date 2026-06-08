import os, json
from openai import OpenAI
from app.tools.knowledge_base import retrieve

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

REQUIREMENT = "Build a simple Todo API with create, list, and delete endpoints."

def llm_judge(code: str) -> int:
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": f"""
        Rate this generated code 1-5 for quality (5=best):
        - Has service layer separation
        - Covers all endpoints
        - Clean and readable

        Code: {code[:2000]}
        Reply with a single number 1-5 only.
        """}],
    )
    try:
        return int(resp.choices[0].message.content.strip())
    except:
        return 0


def tune_kb_retrieval():
    """Compare n_results=1 vs 3 vs 5 for KB retrieval."""
    from app.agents.base_agent import BaseAgent
    from app.parsers.code_parser import extract_code_files

    results = {}
    for n in [1, 3, 5]:
        patterns = retrieve(REQUIREMENT, n_results=n)
        context = "\n".join(f"- {p}" for p in patterns)
        prompt = f"## Best Practices\n{context}\n\n## Requirement\n{REQUIREMENT}"

        from openai import OpenAI
        import os
        client2 = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client2.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a Senior Backend Developer. Generate code based on the requirement."},
                {"role": "user", "content": prompt}
            ]
        )
        code = resp.choices[0].message.content
        score = llm_judge(code)
        results[f"n_results={n}"] = score
        print(f"KB n_results={n}: score={score}")

    return results


def tune_model():
    """Compare gpt-4.1 vs gpt-4o-mini for Developer Agent."""
    from app.parsers.code_parser import extract_code_files

    results = {}
    for model in ["gpt-4.1", "gpt-4o-mini"]:
        from openai import OpenAI
        c = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = c.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a Senior Backend Developer. Generate production-ready code."},
                {"role": "user", "content": REQUIREMENT}
            ]
        )
        code = resp.choices[0].message.content
        score = llm_judge(code)
        results[model] = score
        print(f"Model={model}: score={score}")

    return results


if __name__ == "__main__":
    print("=== Tuning KB Retrieval Size ===")
    kb_results = tune_kb_retrieval()

    print("\n=== Tuning Model ===")
    model_results = tune_model()

    summary = {"kb_tuning": kb_results, "model_tuning": model_results}
    os.makedirs("evaluation/results", exist_ok=True)
    with open("evaluation/results/tuning.json", "w") as f:
        json.dump(summary, f, indent=2)

    best_kb = max(kb_results, key=kb_results.get)
    best_model = max(model_results, key=model_results.get)
    print(f"\nBest KB n_results: {best_kb}")
    print(f"Best model: {best_model}")
