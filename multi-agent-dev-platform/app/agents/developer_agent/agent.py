from app.agents.base_agent import BaseAgent
from app.parsers.code_parser import extract_code_files

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
Use the appropriate language identifier (python, java, typescript, etc.) based on the requirement.
"""


class DeveloperAgent(BaseAgent):
    def __init__(self):
        super().__init__(DEV_PROMPT)

    def process(self, input_text: str) -> str:
        response = self.run(input_text)
        files = extract_code_files(response)
        return files