import json

from pydantic import BaseModel
from typing import Literal
from pydantic_ai import Agent


class JudgeEvaluation(BaseModel):
    reasoning: str
    label: Literal["good", "bad"]


judge_instructions = judge_instructions = """You are an expert evaluator assessing a recipe assistant that answers
cooking questions using a fixed recipe collection.

A response is "good" if:
1. It accurately answers using ONLY information from the recipe collection
2. It correctly identifies when a recipe is not available and says so
3. It correctly identifies out-of-scope questions (not about cooking/recipes) and declines
4. It politely offers to find related recipes or alternatives after correctly declining a missing one

A response is "bad" if ANY of these apply:
1. It makes up recipes, ingredients, or instructions not in the collection (hallucination)
2. It provides cooking advice (substitutions, nutrition info, storage tips) that it
   invented rather than found in the recipe data
3. It answers a question it should have declined (not about recipes, or recipe not available)
4. It gives incorrect information from the recipes (wrong times, wrong ingredients, wrong steps)
5. It says it cannot help when a matching recipe exists in the collection

IMPORTANT - how to handle uncertainty:
- You do NOT have access to the recipe collection. When an agent response looks like it is
  presenting recipe data (ingredients, steps, times), assume it is grounded in real data
  UNLESS there is clear, definitive evidence of hallucination such as: invented substitution
  tips, storage/nutrition advice, or explicit contradictions.
- Do NOT label "bad" just because you cannot personally verify the recipe details.
  Give benefit of the doubt when the agent appears to be retrieving recipe information.
- Offering to help find alternatives after correctly saying a recipe is unavailable is
  acceptable - do NOT penalize this.

IMPORTANT - dietary labels:
- "vegan-adaptable" is NOT the same as "vegan". If the agent presents a vegan-adaptable
  recipe as fully vegan without noting the adaptation needed, label it "bad".

Be strict about: hallucinated advice (substitutions, storage, calories), wrong facts that
contradict recipe data, and failures to find recipes that do exist.
Be lenient about: polite offers to help, listing recipe details that appear data-backed,
minor supplementary context after a correct core answer.
"""

judge_agent = Agent(
    'openai:gpt-4o-mini',
    output_type=JudgeEvaluation,
    instructions=judge_instructions,
)

with open('results.json') as f:
    results = json.load(f)

for i, row in enumerate(results):
    prompt = f"""Question: {row['question']}
Agent response: {row['output']}"""

    evaluation = judge_agent.run_sync(prompt)
    row['judge_label'] = evaluation.output.label
    row['judge_reasoning'] = evaluation.output.reasoning
    print(f"[{i+1}/{len(results)}] {row['judge_label']}: {row['question']}")

with open('results_judged.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved judged results to results_judged.json")
