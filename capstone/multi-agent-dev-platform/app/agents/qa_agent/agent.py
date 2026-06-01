from app.agents.base_agent import BaseAgent
from app.parsers.code_parser import extract_code_files

QA_PROMPT = """
You are a QA Engineer.

Generate pytest test cases for given backend code.

Include:
- unit tests
- API tests
- edge cases

Output each test file using EXACTLY this format — no extra headers, no numbering:

### test_app.py
```python
<tests here>

Use the appropriate language identifier based on the code provided.
"""


class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__(QA_PROMPT)

    def process(self, code: dict) -> str:
        # Convert dict to string for OpenAI
        code_str = "\n\n".join([
            f"### {fname}\n```python\n{content}\n```" 
            for fname, content in code.items()
        ])
        
        response = self.run(code_str)
        """
        - Tests should be stored as individual files (test_app.py, test_models.py, etc.)
        - Uses the same extract_code_files parser to split test code
        - The workflow expects state.tests to be a dictionary, not a string
        """
        tests = extract_code_files(response)
        return tests