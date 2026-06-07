from openai import OpenAI
import os

class BaseAgent:
    def __init__(self, system_prompt: str, model: str = "gpt-4.1"):
        self.system_prompt = system_prompt
        self.model = model
        self._client = None  # lazy-initialize the client so it doesn't fail at import

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    def run(self, user_input: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content