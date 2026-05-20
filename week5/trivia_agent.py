"""
A simple trivia quizmaster agent that uses the TriviaTools to fetch questions and interact with the player.
"""
from trivia_tools import TriviaTools
from pydantic_ai import Agent
import logfire
import questionary

# Configure logfire to capture logs from the agent and tools.
logfire.configure()
# This will automatically capture logs from any code that uses logfire, including the agent and tools.
logfire.instrument_pydantic_ai()

# Define the instructions for the trivia quizmaster agent.
instructions = """
You are a trivia quizmaster.

IMPORTANT:
- You MUST call get_categories before asking for a category.
- You MUST call get_questions before asking trivia questions.
- Do not make up categories or questions yourself.
- Only use information returned by the tools.

When asked to play trivia:
1. Use the available tools to fetch trivia questions
2. Ask the player one question at a time with multiple choice options
3. Wait for their answer before moving to the next question
4. Explain why the correct answer is correct
5. After all questions, give the final score
"""

# Initialize tools
trivia_tools = TriviaTools()

# Create the agent with the specified model, tools, and instructions.
agent = Agent(
    'openai:gpt-4o-mini',
    tools=[trivia_tools.get_categories, trivia_tools.get_questions],
    instructions=instructions,
)

def ask_feedback():
    result = questionary.select(
        "How was the trivia session?",
        choices=["👍 Good", "👎 Bad", "Skip"],
    ).ask()

    if result is None or result == "Skip":
        return None

    return 1 if "Good" in result else -1

def run(prompt):
    message_history = []

    while True:
        result = agent.run_sync(prompt, message_history=message_history)
        print("\n=== AGENT RESPONSE ===")
        print(result.output)
        # Save conversation history
        message_history = result.all_messages()

        # Get user input
        prompt = input("You (write 'stop' to stop): ")
        
        # Stop condition
        if not prompt or prompt.lower().strip() == 'stop':
            break

# Start full trivia session
with logfire.span('trivia_session'):
    run("Let's play 5 easy questions from Science & Nature")
    # feedback is still inside same span → same trace
    feedback = ask_feedback()

    logfire.info(
        "user_feedback",
        score=feedback,
    )

"""
# Run the agent
# run_sync is a blocking call that will wait until the agent has completed its interaction.
result = agent.run_sync("Let's play trivia")

print("\n=== FINAL OUTPUT ===")
print(result.output)

print("\n=== MESSAGE HISTORY ===")

for msg in result.all_messages():
    print(msg)
    print("-" * 50)
"""