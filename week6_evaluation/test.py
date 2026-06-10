from recipe_agent import agent

result = agent.run_sync("How do I make pizza?")
print(result.output)