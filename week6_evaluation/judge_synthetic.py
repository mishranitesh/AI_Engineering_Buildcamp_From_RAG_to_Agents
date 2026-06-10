import json
from pydantic import BaseModel
from typing import Literal
from pydantic_ai import Agent

class JudgeEvaluation(BaseModel):
    reasoning: str
    label: Literal["good", "bad"]

# reuse the same updated prompt from judge.py
from judge import judge_instructions

judge_agent = Agent('openai:gpt-4o-mini', output_type=JudgeEvaluation,
                    instructions=judge_instructions)

with open('synthetic_results.json') as f:
    results = json.load(f)

for i, row in enumerate(results):
    prompt = f"Question: {row['question']}\nAgent response: {row['output']}"
    evaluation = judge_agent.run_sync(prompt)
    row['judge_label'] = evaluation.output.label
    row['judge_reasoning'] = evaluation.output.reasoning
    print(f"[{i+1}/{len(results)}] {row['judge_label']}: {row['question']}")

with open('synthetic_results_judged.json', 'w') as f:
    json.dump(results, f, indent=2)

bad = sum(1 for r in results if r['judge_label'] == 'bad')
print(f"\nBad: {bad}/{len(results)} = {bad/len(results):.1%}")
