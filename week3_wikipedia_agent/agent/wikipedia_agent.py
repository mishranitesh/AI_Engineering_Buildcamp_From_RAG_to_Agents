# agent/wikipedia_agent.py
# PydanticAI Agent
from pydantic_ai import Agent

# Import custom tools
from tools.wikipedia_search import search_wikipedia
from tools.wikipedia_page import get_page

# Note: openai key is stored in ~/.zshrc

# ---------------------------------------------------
# Create the Agent
# ---------------------------------------------------
# We are using:
# - Framework: PydanticAI
# - LLM Provider: OpenAI
# - Model: gpt-4.1-mini
# ---------------------------------------------------

agent = Agent(
    "openai:gpt-4.1-mini",

    system_prompt="""
    You are a helpful Wikipedia research assistant.

    You can:
    - search Wikipedia pages
    - fetch Wikipedia page content
    - answer user questions using the tools provided
    """
)


# ---------------------------------------------------
# TOOL 1: Wikipedia Search
# ---------------------------------------------------
# This tool searches Wikipedia for relevant pages.
#
# Example:
# query = "capybara"
#
# Returns:
# list of matching Wikipedia page titles
# ---------------------------------------------------

@agent.tool_plain
def wiki_search(query: str) -> str:

    # Call custom search function
    results = search_wikipedia(query)

    # Extract titles from API response
    titles = [
        item["title"]
        for item in results["query"]["search"]
    ]

    # Return titles as newline-separated text
    return "\n".join(titles)


# ---------------------------------------------------
# TOOL 2: Get Wikipedia Page
# ---------------------------------------------------
# This tool fetches raw Wikipedia page content.
#
# Example:
# title = "Capybara"
#
# Returns:
# raw page text/content
# ---------------------------------------------------

@agent.tool_plain
def wiki_get_page(title: str) -> str:

    # Fetch page content using helper function
    return get_page(title)