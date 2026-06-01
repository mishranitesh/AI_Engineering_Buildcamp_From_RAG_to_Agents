from app.agents.base_agent import BaseAgent
from app.parsers.mermaid_parser import extract_mermaid

ARCHITECT_PROMPT = """
You are a Software Architect Agent.

Given user stories:
1. Design system architecture
2. Provide Mermaid diagram
3. Define APIs

Return:
- Architecture Explanation
- Mermaid Diagram
- API Contracts
"""


class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(ARCHITECT_PROMPT)

    def process(self, stories: str) -> str:
        response = self.run(stories)
        mermaid = extract_mermaid(response)
        return response, mermaid