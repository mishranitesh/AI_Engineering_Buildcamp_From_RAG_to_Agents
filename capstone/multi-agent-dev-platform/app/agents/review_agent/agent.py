from app.agents.base_agent import BaseAgent
from app.tools.knowledge_base import retrieve
from app.monitoring.logger import logger

REVIEW_PROMPT = """
You are a Senior Code Reviewer.

Review the provided code and tests. Return your findings as a numbered list where EACH item starts with a number and period on its own line, like this exact format:

1. [Bug] Description of bug and how to fix it
2. [Bug] Another bug
3. [Improvement] Suggested improvement
4. [Test] Missing test case
5. [Architecture] Architecture concern

Rules:
- One issue per numbered item
- Start each item with the number, a period, and a space
- Keep each item to 2-3 sentences max
- Do not use markdown headers or sub-numbering like 1.1
- Return between 5 and 15 items total
"""


class ReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(REVIEW_PROMPT)

    def process(self, code: str) -> str:
        patterns = retrieve(code[:500], n_results=3)   # use first 500 chars as query
        logger.info(f"KB retrieved {len(patterns)} patterns for review: {[p[:50] for p in patterns]}")
        context = "\n".join(f"- {p}" for p in patterns)
        augmented_input = f"## Known Best Practices to Check Against\n{context}\n\n## Code to Review\n{code}"
        return self.run(augmented_input)