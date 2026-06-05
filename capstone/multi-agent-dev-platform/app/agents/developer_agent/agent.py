from app.agents.base_agent import BaseAgent
from app.parsers.code_parser import extract_code_files
from app.tools.knowledge_base import retrieve
from app.monitoring.logger import logger

DEV_PROMPT = """
You are a Senior Backend Developer.

Generate production-ready backend code based on:
- user stories
- architecture

Rules:
- Include models, routes, services
- Keep code clean and modular

Output each file using EXACTLY this format — no extra headers, no directory structure, no numbering:

### main.py
```python
<code here>
```
Use the appropriate language identifier (python, java, typescript, etc.) based on the requirement.
"""


class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__(DEV_PROMPT)

    def process(self, requirement: str) -> dict:
        patterns = retrieve(requirement, n_results=3)
        logger.info(f"KB retrieved {len(patterns)} patterns: {[p[:50] for p in patterns]}")
        context = "\n".join(f"- {p}" for p in patterns)
        augmented_input = f"## Relevant Best Practices\n{context}\n\n## Requirement\n{requirement}"
        raw = self.run(augmented_input)
        return extract_code_files(raw) # it parses the LLM's raw text output into a {filename: code} dict that the rest of the workflow expects.