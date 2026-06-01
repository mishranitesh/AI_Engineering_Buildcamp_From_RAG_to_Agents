from app.agents.base_agent import BaseAgent

PM_PROMPT = """
You are a Product Manager Agent.

Given a software requirement:
1. Break it into user stories
2. Define acceptance criteria
3. Suggest basic tech stack

Return in structured format:
- User Stories
- Acceptance Criteria
- Tech Stack Suggestions
"""


class PMAgent(BaseAgent):
    def __init__(self):
        super().__init__(PM_PROMPT)

    def process(self, requirement: str) -> str:
        return self.run(requirement)