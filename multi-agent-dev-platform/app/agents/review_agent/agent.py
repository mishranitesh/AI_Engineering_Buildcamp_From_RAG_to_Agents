from app.agents.base_agent import BaseAgent

REVIEW_PROMPT = """
You are a Senior Code Reviewer.

Review the given code and:
- find bugs
- suggest improvements
- check missing tests
- check architecture issues
"""


class ReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(REVIEW_PROMPT)

    def process(self, code: str) -> str:
        return self.run(code)