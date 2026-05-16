import pytest
from patch_agent import patch_agent
from sql_tools import setup_database
from sql_agent import agent
from judge import evaluate_agent_performance
import cost_tracker


TOTAL_COST = 0.0

@pytest.fixture(scope="session", autouse=True)
def db():
    setup_database()
    return True


@pytest.fixture(scope="module")
def sql_agent():
    return patch_agent(agent)


@pytest.fixture(scope="module")
def judge():
    return evaluate_agent_performance

def pytest_sessionfinish(session, exitstatus):
    """
    Print approximate cost tracking summary after all tests.
    """

    global TOTAL_COST

    print("\n" + "=" * 50)
    print(f"Approximate Total LLM Cost: ${cost_tracker.TOTAL_COST:.6f}")
    print("=" * 50)