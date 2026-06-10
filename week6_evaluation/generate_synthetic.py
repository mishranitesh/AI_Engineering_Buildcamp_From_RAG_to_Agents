import json
import csv
from pydantic import BaseModel
from pydantic_ai import Agent

class Question(BaseModel):
    question: str
    category: str
    type: str

class GeneratedQuestions(BaseModel):
    questions: list[Question]

generator = Agent(
    'openai:gpt-4o-mini',
    output_type=GeneratedQuestions,
)

with open('recipes.json') as f:
    recipes = json.load(f)

all_questions = []

for recipe in recipes:
    prompt = f"""Given this recipe, generate 5 questions a user might ask.
Include: 1 factual, 1 how-to, 1 detail, 1 substitution, 1 comparison with another dish.

Recipe: {recipe['name']}
Cuisine: {recipe['cuisine']}
Ingredients: {', '.join(recipe['ingredients'])}
Instructions: {recipe['instructions']}"""

    result = generator.run_sync(prompt)
    for q in result.output.questions:
        all_questions.append({
            'question': q.question,
            'category': q.category,
            'type': q.type,
        })
    print(f"Generated 5 questions for: {recipe['name']}")

with open('synthetic_scenarios.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['question', 'category', 'type'])
    writer.writeheader()
    writer.writerows(all_questions)

print(f"\nSaved {len(all_questions)} questions to synthetic_scenarios.csv")
