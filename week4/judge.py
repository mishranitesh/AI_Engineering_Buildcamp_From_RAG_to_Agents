from pydantic_ai import Agent
from pydantic import BaseModel


class JudgeResult(BaseModel):
    score: int
    reasoning: str


judge_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=JudgeResult,
)


def evaluate_agent_performance(question: str, sql: str, result: str, criteria: str):
    prompt = f"""
        You are an expert SQL evaluator.

        Question: {question}

        SQL Query:
        {sql}

        Result:
        {result}

        Evaluation Criteria:
        {criteria}

        Return a score (0-10) and reasoning.
    """

    return judge_agent.run_sync(prompt)


def assert_criteria(judge_result):
    """Fail test if score is too low."""
    assert judge_result.output.score >= 7, judge_result.output.reasoning