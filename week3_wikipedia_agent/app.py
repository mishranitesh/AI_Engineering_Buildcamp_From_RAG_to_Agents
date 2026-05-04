from tools.wikipedia_search import search_wikipedia
from tools.wikipedia_page import get_page

# Question 1 - Define the Search Tool
results = search_wikipedia("capybara")

search_items = results["query"]["search"]

print(f"Total results: {len(search_items)}")

print("\nTitles:\n")

for item in search_items:
    print("-", item["title"])

# Question 2 - Analyzing Search Results
count = 0

for item in search_items:

    title = item["title"]

    if "capybara" in title.lower():
        count += 1

print(f"\nTitles containing 'capybara': {count}")

# Question 3 - Define the Get Page Tool

content = get_page("Capybara")

print("\nCharacter count:")
print(len(content))

# Question 5 - Testing Your Agent - Single Page
'''
from agent.wikipedia_agent import agent


result = agent.run_sync(
    "What is this page about? https://en.wikipedia.org/wiki/Capybara"
)

print(result.output)
'''

# Question 6 - Testing Your Agent - Search Then Fetch
from agent.wikipedia_agent import agent


result = agent.run_sync(
    "What are the main threats to capybara populations?"
)

print("\nFINAL ANSWER:\n")
print(result.output)


print("\n--- TOOL TRACE ---\n")

for msg in result.all_messages():
    print(msg)
    print("-" * 50)