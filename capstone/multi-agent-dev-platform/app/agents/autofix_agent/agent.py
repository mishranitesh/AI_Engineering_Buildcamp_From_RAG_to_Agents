from app.agents.base_agent import BaseAgent

AUTOFIX_PROMPT = """
You are a Senior Software Engineer tasked with fixing code based on review comments.

Given the original code files and a list of review issues, return ONLY the corrected code.

Format your response as one file per section:
### filename.py
```python
<corrected code>
```
Fix all issues mentioned. Do not add new features. Keep changes minimal and targeted.
"""

class AutoFixAgent(BaseAgent):
    def __init__(self):
        super().__init__(AUTOFIX_PROMPT)

    def process(self, code: str, review_comments: str) -> str:
        user_input = f"## Code\n{code}\n\n## Review Issues\n{review_comments}"
        return self.run(user_input)