# Homework (mini-project)

Lesson 1

In this homework we'll evaluate a recipe assistant agent. The focus is on thinking about different scenarios and manual evaluation - not on writing code. That's why we provide most of the code: the agent, tools, batch runner, and judge prompt. You're welcome to write your own, but the main idea is to let you focus on the evaluation process itself.

 

We recommend using PydanticAI and OpenAI, but you can use any agent framework and any LLM provider. You're free to use AI assistants (ChatGPT, Claude, etc.) to help you with this homework.

 

Note: For all questions, if your answer doesn't match exactly, pick the closest option.

## Preparation

The agent uses a small recipe dataset (15 recipes covering Italian, Indian, Mexican, Thai, Japanese, and other cuisines) and searches it with minsearch (which you already know from Week 1). No external API needed.

Install the required packages:

```bash
python3 -m venv .venv 
source .venv/bin/activate
uv init
uv add minsearch pydantic-ai
```

## Download the starter code - the recipe data, search tools, and agent:

```bash
GIST="https://gist.githubusercontent.com/alexeygrigorev/a4448dca73cd577a7e034e20af007e76/raw"
wget ${GIST}/recipes.json
wget ${GIST}/recipe_tools.py
wget ${GIST}/recipe_agent.py
wget ${GIST}/run_scenarios.py
wget ${GIST}/judge.py
```

Alternatively, open the gist and copy the code into the respective files manually.

Take a look at the files to understand what they do:

- recipes.json - 15 recipes with name, cuisine, difficulty, ingredients, instructions, and tags
- recipe_tools.py - indexes the recipes with minsearch and provides search_recipes and get_recipe tools
- recipe_agent.py - a PydanticAI agent that uses the tools to answer cooking questions
- run_scenarios.py - loads scenarios.csv, runs the agent on each question, saves results to results.json
- judge.py - LLM judge that evaluates each agent response as "good" or "bad" with reasoning

## Test it:

```python
from recipe_agent import agent

result = agent.run_sync("How do I make pizza?")
print(result.output)

# Output
"""
(.venv) niteshmishra@Mac week6 % python test.py
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
Here's a simple recipe for **Classic Margherita Pizza**:

### Ingredients:
- Pizza dough
- San Marzano tomatoes
- Fresh mozzarella
- Fresh basil
- Olive oil
- Salt

### Instructions:
1. Preheat your oven to 475°F (245°C).
2. Roll out the pizza dough on a floured surface to your desired thickness.
3. Spread the crushed San Marzano tomatoes evenly over the dough.
4. Tear the fresh mozzarella into pieces and distribute over the sauce.
5. Bake the pizza in the oven for 12-15 minutes, or until the crust is golden brown.
6. Once cooked, top with fresh basil leaves and a drizzle of olive oil.

### Serving:
This recipe serves 4 people and is a classic vegetarian option! Enjoy your homemade pizza!
"""
```

You should see a response about the Margherita Pizza recipe. The dataset has 15 recipes.

Try a few more questions to get a feel for the agent before we start evaluating it:

- "How do I make spaghetti carbonara?"
- "What can I cook with chicken?"
- "How do I make sushi?"
- "What's the best restaurant in town?"

 

Notice how it handles recipes it has vs recipes it doesn't, and out-of-scope questions. This will help you design evaluation scenarios in the next step.

## Question 1. Design Evaluation Scenarios

Design evaluation scenarios for the recipe assistant. You can use an AI assistant (ChatGPT, Claude, etc.) to help you brainstorm scenarios.

Create a file called scenarios.csv with three columns: question, category, type.

Here are 5 to start with:

question,category,type
How do I make spaghetti carbonara?,specific-recipe,direct
What can I cook with chicken and coconut milk?,ingredient-search,ingredient-based
I want something easy and healthy for dinner,preference,vague
How do I make sushi?,missing-recipe,not-in-collection
What temperature should I set my oven to for the lava cake?,recipe-detail,specific

Add at least 15 more scenarios of your own. Use the framework from the lessons to cover:

- Different phrasings: "I want pasta" vs "What Italian dishes do you have?"
- Substitution questions: "Can I use bacon instead of guanciale in carbonara?" (the recipe doesn't mention substitutions)
- Dietary questions: "Is the Caesar salad vegetarian?" (it has anchovy paste)
- Questions the dataset can't answer: "What's the calorie count?" or "How do I make ramen?"
- Out-of-scope: "What's the best restaurant in town?" or "How do I fix my dishwasher?"
- Edge cases: "Can I make the falafel with canned chickpeas?" (the recipe specifically says not to)

You need at least 20 scenarios total.

Now run the agent on this question: "Can I substitute almond milk in the pancakes?" The pancake recipe lists "milk" as an ingredient but says nothing about substitutions.

Look at the agent's response. Did the agent hallucinate?

- Yes, the agent made up substitution advice not in the recipe data <-- answer
- No, the agent said it doesn't have substitution information

### Steps followed

Create scenarios.csv

### Create q1_test.py

### Run q1_test.py

Output
```
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
I don't have a specific pancake recipe that includes almond milk or details about substitutions. However, almond milk is often used as a substitute for regular milk in pancake recipes and should work well in most cases. If you would like, I can help you find a pancake recipe to confirm that almond milk can be used. Would you like me to do that?
```

### Hallucination verdict: Yes
The response is a textbook hallucination — a two-part answer that reveals the failure mode clearly:

| Part | What it says | Verdict |
|------|-------------|---------|
| "I don't have a specific pancake recipe that includes almond milk or details about substitutions" | Correctly acknowledges the data gap | ✅ Good |
| "almond milk is often used as a substitute for regular milk in pancake recipes and should work well in most cases" | General LLM knowledge, not from the recipe data | ❌ Hallucination |

Yes, the agent made up substitution advice not in the recipe data

The correct behavior would be to stop after the first sentence — "I don't have substitution information in my recipes" — and not supplement with outside knowledge. This is a key failure mode to test for in agentic RAG systems: the model uses retrieval as a "check" but falls back to parametric memory when the retrieved data is silent on the question.

## Question 2. Run Scenarios in Batch
Run the agent on all your scenarios and save the results. You can write your own script or use the run_scenarios.py we provided in the preparation step. It loads scenarios.csv, runs the agent on each question, and saves results to results.json.

Run it:
```
uv run python run_scenarios.py
```

The script tracks token usage and cost for each scenario (using gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output).

Make sure you included the "Can I substitute almond milk in the pancakes?" scenario from Question 1 in your CSV. Look at its cost in results.json.

What is the approximate cost of that scenario?

- Less than $0.001 <-- answer
- $0.001 - $0.01
- $0.01 - $0.05
- More than $0.05

### Output of `uv run python run_scenarios.py`

```
(.venv) niteshmishra@Mac week6 % uv run python run_scenarios.py
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
[1/24] How do I make spaghetti carbonara?
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/run_scenarios.py:33: PydanticAIDeprecationWarning: `AgentRunResult.usage` is no longer a method; access it as a property (drop the parentheses).
  usage = result.usage()
  Done in 6.5s ($0.000304)
[2/24] What can I cook with chicken and coconut milk?
  Done in 5.6s ($0.000351)
[3/24] I want something easy and healthy for dinner
  Done in 9.1s ($0.000579)
[4/24] How do I make sushi?
  Done in 2.3s ($0.00012)
[5/24] What temperature should I set my oven to for the lava cake?
  Done in 2.9s ($0.000199)
[6/24] What Italian dishes do you have?
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/run_scenarios.py:33: PydanticAIDeprecationWarning: `AgentRunResult.usage` is no longer a method; access it as a property (drop the parentheses).
  usage = result.usage()
  Done in 5.4s ($0.000332)
[7/24] I want something with pasta
  Done in 5.0s ($0.000295)
[8/24] Can I use bacon instead of guanciale in carbonara?
  Done in 1.4s ($7.7e-05)
[9/24] Can I substitute almond milk in the pancakes?
  Done in 1.6s ($8.1e-05)
[10/24] Is the Caesar salad vegetarian?
  Done in 1.9s ($8.8e-05)
[11/24] Is the falafel wrap vegan?
  Done in 2.7s ($0.000127)
[12/24] What's the calorie count for the margherita pizza?
  Done in 4.3s ($0.000236)
[13/24] How do I make ramen?
  Done in 1.8s ($0.000107)
[14/24] What's the best restaurant in town?
  Done in 1.0s ($5.7e-05)
[15/24] How do I fix my dishwasher?
  Done in 1.0s ($5.7e-05)
[16/24] Can I make the falafel with canned chickpeas?
  Done in 1.8s ($8.6e-05)
[17/24] How many servings does the chocolate lava cake make?
  Done in 3.2s ($0.0001)
[18/24] What can I make if I'm vegan?
  Done in 7.2s ($0.000295)
[19/24] What can I cook without any meat?
  Done in 5.3s ($0.000261)
[20/24] How long can I store leftover chicken tikka masala in the fridge?
  Done in 1.5s ($7.3e-05)
[21/24] What's the hardest recipe in your collection?
  Done in 2.0s ($6.1e-05)
[22/24] Can I make mushroom risotto without wine?
  Done in 2.3s ($0.000137)
[23/24] Do you have any dessert recipes?
  Done in 3.1s ($0.000149)
[24/24] What spices are needed for chicken tikka masala?
  Done in 1.9s ($0.000142)

Saved 24 results to results.json
Total cost: $0.0043
```

The almond milk scenario (#9) cost $8.1e-05 = $0.000081.

Answer to Question 2: Less than $0.001 ✅

Quick summary of the run:

24 scenarios completed, total cost $0.0043
Almond milk scenario was one of the cheapest ($0.000081) — fast because the agent gave a short answer without doing a tool call to retrieve the recipe
Most expensive scenarios were the vague preference ones (#3, #18, #19) at ~$0.0003–0.0006, because the agent searched multiple times and returned longer responses
Results saved to results.json, ready for Question 3 (judge evaluation)

## Question 3

Question 3. Label the Results

Review each result and label it as "good" or "bad". Here are a few ways to do it:

- Spreadsheet: convert results.json to CSV (ask AI to write a script), open in Excel or Google Sheets, add a "label" column, go through each row
- Streamlit app: take the labeling app from the lessons (label_evals.py) and ask AI to adapt it for this homework. It loads results.json, shows each question and response, and lets you click good/bad
- Jupyter notebook: load results.json, loop through results with ipywidgets buttons for good/bad, save labels to a file
- Simple script: write a Python script that prints each question and response, asks for your label via input(), and saves to CSV

Pick whatever works for you. The important thing is to look at each response carefully and decide if it's good or bad.

A response is "good" when:

- The answer is correct and based on the recipe data, or
- The agent correctly says it doesn't have a recipe when asked about something not in the collection

A response is "bad" when:

- The agent makes up a recipe or ingredients not in the dataset (hallucination)
- The agent gives cooking advice not supported by the recipe data (e.g., invented substitution tips)
- The agent says it can't help when a matching recipe actually exists
- The agent gives incorrect details from the recipe (wrong times, wrong ingredients)

For bad responses, also note WHY it failed (hallucination, wrong-scope, incomplete, etc.). These failure categories will help you understand patterns.

How many of your 20 scenarios did the agent get wrong?

Answer - 10 of 24 bad.

### Steps followed 

- Create label_results.py
- Run - `uv run python label_results.py`
  - It will print each question + agent response one at a time and ask you to type g (good) or b (bad). For bad ones it asks for a failure reason. Results save to labels.csv.

```
(.venv) niteshmishra@Mac week6 % uv run python label_results.py

============================================================
[1/24] How do I make spaghetti carbonara?
Category: specific-recipe / direct

Agent response:
Here's how to make Spaghetti Carbonara, an Italian classic:

### Ingredients:
- Spaghetti
- Guanciale
- Egg yolks
- Pecorino Romano cheese
- Black pepper
- Salt

### Instructions:
1. Cook the spaghetti in salted boiling water until al dente.
2. While the pasta cooks, crisp the guanciale in a pan over medium heat until it is golden and crispy.
3. In a bowl, whisk together the egg yolks, grated pecorino romano, and black pepper.
4. Once the pasta is cooked, drain it, reserving some of the pasta water.
5. Toss the hot pasta with the crispy guanciale in the pan.
6. Quickly stir in the egg mixture off the heat to create a creamy sauce, adding reserved pasta water as needed to achieve the desired consistency.
7. Serve immediately with extra pecorino romano on top.

This recipe serves 4 and takes about 30 minutes in total (10 minutes prep and 20 minutes cooking). Enjoy your meal!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[2/24] What can I cook with chicken and coconut milk?
Category: ingredient-search / ingredient-based

Agent response:
You can make **Thai Green Curry** with chicken and coconut milk! Here’s the recipe:

### Thai Green Curry

**Cuisine:** Thai
**Difficulty:** Medium
**Prep time:** 20 minutes
**Cook time:** 25 minutes
**Servings:** 4

#### Ingredients:
- Chicken thigh
- Coconut milk
- Green curry paste
- Bamboo shoots
- Thai basil
- Fish sauce
- Palm sugar
- Eggplant
- Bell pepper
- Jasmine rice

#### Instructions:
1. Heat coconut cream in a wok until the oil separates.
2. Fry the green curry paste for 2 minutes.
3. Add the sliced chicken and cook until sealed.
4. Pour in the coconut milk and bring to a simmer.
5. Add the eggplant and bamboo shoots, and cook for 10 minutes.
6. Season with fish sauce and palm sugar.
7. Add bell pepper and Thai basil.
8. Serve over jasmine rice.

This dish has a spicy and rich flavor from the coconut milk and curry. Enjoy cooking!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[3/24] I want something easy and healthy for dinner
Category: preference / vague

Agent response:
Here are three easy and healthy dinner options for you:

### 1. Vegetable Stir Fry
- **Cuisine**: Chinese
- **Prep Time**: 15 minutes
- **Cook Time**: 10 minutes
- **Servings**: 3

**Ingredients**:
- Broccoli
- Bell pepper
- Carrot
- Snap peas
- Soy sauce
- Sesame oil
- Garlic
- Ginger
- Cornstarch
- Rice

**Instructions**:
1. Cut all vegetables into bite-sized pieces.
2. Heat sesame oil in a wok over high heat. Add garlic and ginger; stir for 30 seconds.
3. Add vegetables starting with carrots and broccoli, then the softer vegetables.
4. Stir in soy sauce and cornstarch slurry, cooking until the sauce thickens.
5. Serve over rice.

### 2. Miso Soup
- **Cuisine**: Japanese
- **Prep Time**: 5 minutes
- **Cook Time**: 10 minutes
- **Servings**: 4

**Ingredients**:
- Dashi stock
- White miso paste
- Silken tofu
- Wakame seaweed
- Green onion

**Instructions**:
1. Bring dashi stock to a gentle simmer.
2. Add cubed tofu and rehydrated wakame.
3. Ladle some broth into a bowl, dissolve miso paste in it, then pour back into the pot. Do not boil after adding miso.
4. Serve topped with sliced green onion.

### 3. Greek Salad
- **Cuisine**: Greek
- **Prep Time**: 10 minutes
- **Cook Time**: 0 minutes
- **Servings**: 4

**Ingredients**:
- Cucumber
- Tomato
- Red onion
- Kalamata olives
- Feta cheese
- Olive oil
- Oregano
- Red wine vinegar

**Instructions**:
1. Chop cucumber, tomatoes, and red onion into chunks.
2. Combine in a bowl with Kalamata olives and crumbled feta.
3. Dress with olive oil, red wine vinegar, and oregano. Toss gently.
4. Let sit for 5 minutes before serving.

Feel free to choose any of these recipes for a nutritious dinner!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[4/24] How do I make sushi?
Category: missing-recipe / not-in-collection

Agent response:
I don't have a specific sushi recipe available. However, if you're looking for general guidance, traditional sushi typically involves making sushi rice, preparing fillings like fish and vegetables, and wrapping them in seaweed (nori). Would you be interested in a different type of Japanese dish or a specific sushi variant?

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): hallucination
  Saved as BAD

============================================================
[5/24] What temperature should I set my oven to for the lava cake?
Category: recipe-detail / specific

Agent response:
For the chocolate lava cake, you should set your oven to **425°F (220°C)**. Bake it for exactly 12-14 minutes until the edges are firm and the center is still soft.

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[6/24] What Italian dishes do you have?
Category: collection-query / browse

Agent response:
Here are some Italian dishes you can try:

1. **Classic Margherita Pizza**
   - **Prep Time:** 20 minutes
   - **Cook Time:** 15 minutes
   - **Servings:** 4
   - **Ingredients:** Pizza dough, San Marzano tomatoes, fresh mozzarella, fresh basil, olive oil, salt
   - **Tags:** Vegetarian, Classic

2. **Spaghetti Carbonara**
   - **Prep Time:** 10 minutes
   - **Cook Time:** 20 minutes
   - **Servings:** 4
   - **Ingredients:** Spaghetti, guanciale, egg yolks, pecorino romano, black pepper, salt
   - **Tags:** Classic, Pasta

3. **Mushroom Risotto**
   - **Prep Time:** 10 minutes
   - **Cook Time:** 35 minutes
   - **Servings:** 4
   - **Ingredients:** Arborio rice, mixed mushrooms, onion, garlic, white wine, vegetable broth, parmesan cheese, butter, olive oil, thyme
   - **Tags:** Vegetarian, Comfort-food

If you're interested in any specific recipe, let me know!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[7/24] I want something with pasta
Category: preference / vague

Agent response:
I found a recipe for **Spaghetti Carbonara**, a classic Italian dish. Here are the details:

### Ingredients:
- Spaghetti
- Guanciale
- Egg yolks
- Pecorino Romano cheese
- Black pepper
- Salt

### Instructions:
1. Cook spaghetti in salted water until al dente.
2. In a separate pan, crisp the guanciale over medium heat.
3. In a bowl, whisk together the egg yolks, grated pecorino romano, and black pepper.
4. Drain the pasta, reserving some of the cooking water.
5. Toss the hot pasta with the guanciale, then quickly stir in the egg mixture off the heat to create a creamy sauce.
6. Add reserved pasta water as needed to achieve the desired consistency.
7. Serve immediately with extra pecorino romano on top.

### Cooking Time:
- Prep: 10 minutes
- Cook: 20 minutes
- Serves: 4

Enjoy your cooking!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[8/24] Can I use bacon instead of guanciale in carbonara?
Category: substitution / not-in-data

Agent response:
Yes, you can use bacon as a substitute for guanciale in carbonara. While guanciale is traditional and has a unique flavor, bacon will work in a pinch. Just keep in mind that bacon is generally smokier and saltier, so you might want to adjust the seasoning of your dish accordingly. Enjoy your carbonara!

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): hallucination
  Saved as BAD

============================================================
[9/24] Can I substitute almond milk in the pancakes?
Category: substitution / not-in-data

Agent response:
I don’t have a specific pancake recipe that includes almond milk, but in general, almond milk can be used as a substitute for regular milk in pancake recipes. It will give a slightly different flavor but should work well.

If you would like, I can search for pancake recipes and check if any of them use almond milk or similar alternatives. Would you like me to do that?

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): hallucination
  Saved as BAD

============================================================
[10/24] Is the Caesar salad vegetarian?
Category: dietary-check / tricky

Agent response:
A traditional Caesar salad is not vegetarian because it typically contains anchovies in the dressing. Additionally, many recipes include Parmesan cheese, which may not be suitable for some vegetarians due to the use of animal rennet in its production.

However, there are vegetarian versions of Caesar salad that substitute the anchovies with other ingredients while still aiming to provide a similar flavor profile. If you'd like, I can help you find a vegetarian Caesar salad recipe.

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): hallucination
  Saved as BAD

============================================================
[11/24] Is the falafel wrap vegan?
Category: dietary-check / specific

Agent response:
Yes, the falafel wrap is vegan. It contains ingredients like chickpeas, onion, garlic, parsley, cilantro, cumin, coriander, flour, baking powder, pita bread, tahini, lettuce, tomato, and pickles, which are all plant-based.

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[12/24] What's the calorie count for the margherita pizza?
Category: missing-info / not-in-data

Agent response:
The recipe for Classic Margherita Pizza does not specify the calorie count directly. However, the calorie count can vary based on the specific amounts of ingredients used and serving sizes.

For a general idea, a single slice of margherita pizza can range from approximately 200-300 calories, but this can greatly depend on the dough thickness, amount of cheese, and other ingredients. If you need a more precise calorie count, it would be best to calculate based on the specific ingredient quantities you intend to use.

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): hallucination
  Saved as BAD

============================================================
[13/24] How do I make ramen?
Category: missing-recipe / not-in-collection

Agent response:
I don't have a specific ramen recipe available. However, if you'd like, I can help you find recipes for similar dishes or alternatives such as noodle soups. Would you like me to do that?

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[14/24] What's the best restaurant in town?
Category: out-of-scope / irrelevant

Agent response:
I don't have information on restaurants. You might want to check local review sites or ask for recommendations from locals. If you have questions about specific recipes or cooking, feel free to ask!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[15/24] How do I fix my dishwasher?
Category: out-of-scope / irrelevant

Agent response:
I'm not equipped to provide troubleshooting for appliances like dishwashers. I can help you find recipes or answer cooking-related questions if you need assistance in the kitchen. Just let me know!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[16/24] Can I make the falafel with canned chickpeas?
Category: edge-case / specific

Agent response:
Yes, you can make falafel with canned chickpeas. While traditional recipes typically call for dried chickpeas that are soaked and then blended, using canned chickpeas can be a convenient alternative. Just be sure to drain and rinse the canned chickpeas before using them in your falafel mix.

If you need a specific falafel recipe, I can help you find one! Would you like me to do that?

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): wrong-answer
  Saved as BAD

============================================================
[17/24] How many servings does the chocolate lava cake make?
Category: recipe-detail / specific

Agent response:
The chocolate lava cake recipe makes 4 servings.

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[18/24] What can I make if I'm vegan?
Category: preference / dietary-filter

Agent response:
Here are some delicious vegan recipes you can try:

1. **Vegetable Stir Fry**
   - **Cuisine:** Chinese
   - **Prep Time:** 15 min
   - **Cook Time:** 10 min
   - **Serves:** 3
   - **Ingredients:** Broccoli, bell pepper, carrot, snap peas, soy sauce, sesame oil, garlic, ginger, cornstarch, rice.
   - **Tags:** Vegetarian, vegan, quick, healthy.

2. **Falafel Wrap**
   - **Cuisine:** Middle Eastern
   - **Prep Time:** 30 min
   - **Cook Time:** 15 min
   - **Serves:** 4
   - **Ingredients:** Chickpeas, onion, garlic, parsley, cilantro, cumin, coriander, flour, baking powder, pita bread, tahini, lettuce, tomato, pickles.
   - **Tags:** Vegetarian, vegan, street-food.

3. **Miso Soup**
   - **Cuisine:** Japanese
   - **Prep Time:** 5 min
   - **Cook Time:** 10 min
   - **Serves:** 4
   - **Ingredients:** Dashi stock, white miso paste, silken tofu, wakame seaweed, green onion.
   - **Tags:** Soup, quick, healthy, vegan-adaptable.

Let me know if you would like more details or instructions for any of these recipes!

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): Wrong scope
  Saved as BAD

============================================================
[19/24] What can I cook without any meat?
Category: preference / dietary-filter

Agent response:
Here are some delicious vegetarian recipes you can try:

1. **Classic Margherita Pizza**
   - **Cuisine:** Italian
   - **Prep Time:** 20 min
   - **Cook Time:** 15 min
   - **Servings:** 4
   - **Ingredients:** pizza dough, San Marzano tomatoes, fresh mozzarella, fresh basil, olive oil, salt

2. **Vegetable Stir Fry**
   - **Cuisine:** Chinese
   - **Prep Time:** 15 min
   - **Cook Time:** 10 min
   - **Servings:** 3
   - **Ingredients:** broccoli, bell pepper, carrot, snap peas, soy sauce, sesame oil, garlic, ginger, cornstarch, rice

3. **Mushroom Risotto**
   - **Cuisine:** Italian
   - **Prep Time:** 10 min
   - **Cook Time:** 35 min
   - **Servings:** 4
   - **Ingredients:** arborio rice, mixed mushrooms, onion, garlic, white wine, vegetable broth, parmesan cheese, butter, olive oil, thyme

If you're interested in recipes for any of these dishes, let me know!

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[20/24] How long can I store leftover chicken tikka masala in the fridge?
Category: missing-info / not-in-data

Agent response:
Leftover chicken tikka masala can typically be stored in the fridge for about 3 to 4 days. Make sure to keep it in an airtight container to maintain freshness and prevent contamination. If you want to keep it longer, consider freezing it, which can prolong its shelf life for several months.

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): hallucination
  Saved as BAD

============================================================
[21/24] What's the hardest recipe in your collection?
Category: collection-query / meta

Agent response:
I don't have information about the difficulty level of recipes in my collection. If you're looking for specific types of recipes or cuisines, I could help you find some options! Please let me know what you're interested in.

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): failed-to-query
  Saved as BAD

============================================================
[22/24] Can I make mushroom risotto without wine?
Category: substitution / not-in-data

Agent response:
I found a recipe for Mushroom Risotto that includes white wine as one of the ingredients. However, you can definitely make mushroom risotto without wine; just replace the wine with additional vegetable broth or water to add moisture and flavor. Would you like the full details for the original recipe, or do you want to discuss possible adjustments further?

Label (g=good, b=bad, s=skip): b
Failure reason (hallucination / wrong-answer / wrong-scope / failed-to-query): Hallucination
  Saved as BAD

============================================================
[23/24] Do you have any dessert recipes?
Category: collection-query / browse

Agent response:
I found a dessert recipe for Chocolate Lava Cake. Here are the details:

### Chocolate Lava Cake
- **Cuisine**: French
- **Prep Time**: 20 minutes
- **Cook Time**: 14 minutes
- **Servings**: 4

#### Ingredients:
- Dark chocolate
- Butter
- Eggs
- Sugar
- Flour
- Vanilla extract
- Powdered sugar

Would you like to see the full instructions for this recipe?

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

============================================================
[24/24] What spices are needed for chicken tikka masala?
Category: recipe-detail / specific

Agent response:
For chicken tikka masala, you will need the following spices:

- Garam masala
- Turmeric
- Cumin

Additionally, other ingredients include chicken breast, yogurt, tomato sauce, heavy cream, garlic, ginger, onion, cilantro, and rice.

Label (g=good, b=bad, s=skip): g
  Saved as GOOD

Done. 10/24 bad. Saved to labels.csv
```

`10/24 bad.`

## Question 4. Run the LLM Judge

We provided judge.py in the preparation step. It uses structured output with reasoning before label - this forces the LLM to think through its evaluation before deciding. Open the file and read the judge prompt to understand what it checks for.

Run it:
```
uv run python judge.py
```

It reads results.json, evaluates each response, and saves the results with judge labels and reasoning to results_judged.json.

How many of your results does the judge label as "bad"?

`14/24 bad.`
### Output after executing `uv run python judge.py`

```
(.venv) niteshmishra@Mac week6 % uv run python judge.py
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
[1/24] good: How do I make spaghetti carbonara?
[2/24] good: What can I cook with chicken and coconut milk?
[3/24] bad: I want something easy and healthy for dinner
[4/24] bad: How do I make sushi?
[5/24] good: What temperature should I set my oven to for the lava cake?
[6/24] bad: What Italian dishes do you have?
[7/24] good: I want something with pasta
[8/24] bad: Can I use bacon instead of guanciale in carbonara?
[9/24] bad: Can I substitute almond milk in the pancakes?
[10/24] bad: Is the Caesar salad vegetarian?
[11/24] bad: Is the falafel wrap vegan?
[12/24] bad: What's the calorie count for the margherita pizza?
[13/24] bad: How do I make ramen?
[14/24] good: What's the best restaurant in town?
[15/24] good: How do I fix my dishwasher?
[16/24] bad: Can I make the falafel with canned chickpeas?
[17/24] good: How many servings does the chocolate lava cake make?
[18/24] good: What can I make if I'm vegan?
[19/24] good: What can I cook without any meat?
[20/24] bad: How long can I store leftover chicken tikka masala in the fridge?
[21/24] bad: What's the hardest recipe in your collection?
[22/24] bad: Can I make mushroom risotto without wine?
[23/24] good: Do you have any dessert recipes?
[24/24] bad: What spices are needed for chicken tikka masala?

Saved judged results to results_judged.json
```
Answer to Question 4: 14 bad


## Question 5. Measure Alignment
Compare the judge's labels with your human labels. Load results_judged.json and your labels, then calculate alignment metrics.

For each result, there are four possible outcomes:

- True positive (TP): judge says "bad" AND human says "bad"
- False positive (FP): judge says "bad" BUT human says "good"
- False negative (FN): judge says "good" BUT human says "bad"
- True negative (TN): judge says "good" AND human says "good"

Calculate:

accuracy = (tp + tn) / total
precision = tp / (tp + fp)  # when judge says "bad", how often is it right?
recall = tp / (tp + fn)     # of all actual "bad", how many did the judge catch?

Now look at the almond milk substitution scenario specifically. Find it in results_judged.json and compare:

Your label from Question 3 (did you mark it as "good" or "bad"?)

The judge's label and reasoning

Did you and the judge agree on this scenario?

- Yes, we both said "good"
- Yes, we both said "bad"
- No, I said "good" but the judge said "bad"
- No, I said "bad" but the judge said "good"

Submit the judge's reasoning for this scenario.

### Steps followed 

- Create alignment.py
- Run - `uv run python alignment.py`

Output
```
(.venv) niteshmishra@Mac week6 % uv run python alignment.py
TP=9  FP=5  FN=1  TN=9  Total=24
Accuracy:  75.00%
Precision: 64.29%
Recall:    90.00%

Mismatches:
  FP: 'I want something easy and healthy for dinner' | judge=bad, human=good
  FP: 'What Italian dishes do you have?' | judge=bad, human=good
  FP: 'Is the falafel wrap vegan?' | judge=bad, human=good
  FP: 'How do I make ramen?' | judge=bad, human=good
  FN: 'What can I make if I'm vegan?' | judge=good, human=bad
  FP: 'What spices are needed for chicken tikka masala?' | judge=bad, human=good
```

### Almond milk scenario
- My label (Q3): BAD
- Judge label: BAD
- Agreement: Yes, we both said "bad"
- Judge's reasoning:
```
"The response includes general cooking advice about using almond milk as a substitute, which is not information found in the recipe collection, constituting hallucination. Additionally, it incorrectly states that a pancake recipe is not available without checking the recipe data."
```

## Question 6. Improve the Judge
Now compare your labels with the judge's labels across ALL scenarios. Go through each one and find the disagreements.

For each disagreement:

- Read the question and the agent's response
- Read the judge's reasoning
- Compare it with your own reasoning - who is right?

Do you see a pattern? Maybe the judge is too strict on certain types of questions (flags correct responses as "bad"), or too lenient on others (misses actual problems). Look at the disagreements as a group, not individually.

Update the judge prompt in judge.py to address the patterns. Be careful not to overfit: don't put specific test questions or scenarios in the prompt. Instead, add general rules that address the types of mistakes the judge makes.

Re-run the judge and compare the results with your labels again.

Did the number of disagreements go down? Submit the number of disagreements before and after your change.

`Disagreements before: 6 → after: 3 (50% reduction)`

### Answer
`Pattern 1` — Judge is too strict on collection-retrieval responses (FP ×5)
The judge doesn't have access to the recipe collection, so when the agent returns correct recipe data, the judge says things like "may not accurately reflect what is in the recipe collection" or "without valid confirmation". It treats its own uncertainty as evidence of hallucination.

| Question | Judge's Real Problem | Root Cause |
|----------|---------------------|------------|
| #3 Easy healthy dinner | "recipes do not exist in the collection" — they do | Doesn't know the collection |
| #6 Italian dishes | "may have included info not derived from collection" — it did | Doesn't know the collection |
| #11 Falafel wrap vegan? | "lacks confirmation that such a recipe exists" — it does | Doesn't know the collection |
| #13 Ramen | "suggesting alternatives not explicitly requested" | Too strict on polite offers |
| #24 Tikka masala spices | "may not accurately reflect the collection" — it does | Doesn't know the collection |

`Pattern 2` — Judge too lenient on dietary misclassification (FN ×1)

| Question | Why Judge Missed It | Root Cause |
|----------|---------------------|------------|
| #18 Vegan options | Missed that Miso Soup is "vegan-adaptable" ≠ "vegan" | Didn't distinguish the tag |

### Update judge.py prompt 

Original prompt

```
judge_instructions = """You are an expert evaluator assessing a recipe assistant that answers
cooking questions using a fixed recipe collection.

A response is "good" if:
1. It accurately answers using ONLY information from the recipe collection
2. It correctly identifies when a recipe is not available and says so
3. It correctly identifies out-of-scope questions (not about cooking/recipes) and declines

A response is "bad" if ANY of these apply:
1. It makes up recipes, ingredients, or instructions not in the collection (hallucination)
2. It provides cooking advice (substitutions, nutrition info, storage tips) that it
   invented rather than found in the recipe data
3. It answers a question it should have declined (not about recipes, or recipe not available)
4. It gives incorrect information from the recipes (wrong times, wrong ingredients, wrong steps)
5. It says it cannot help when a matching recipe exists in the collection

Be strict about hallucination. The assistant should only provide information it found
in the recipe data. General cooking knowledge that goes beyond the recipe text counts
as hallucination.
"""
```

Updated prompt

```
judge_instructions = """You are an expert evaluator assessing a recipe assistant that answers
cooking questions using a fixed recipe collection.

A response is "good" if:
1. It accurately answers using ONLY information from the recipe collection
2. It correctly identifies when a recipe is not available and says so
3. It correctly identifies out-of-scope questions (not about cooking/recipes) and declines
4. It politely offers to find related recipes or alternatives after correctly declining a missing one

A response is "bad" if ANY of these apply:
1. It makes up recipes, ingredients, or instructions not in the collection (hallucination)
2. It provides cooking advice (substitutions, nutrition info, storage tips) that it
   invented rather than found in the recipe data
3. It answers a question it should have declined (not about recipes, or recipe not available)
4. It gives incorrect information from the recipes (wrong times, wrong ingredients, wrong steps)
5. It says it cannot help when a matching recipe exists in the collection

IMPORTANT - how to handle uncertainty:
- You do NOT have access to the recipe collection. When an agent response looks like it is
  presenting recipe data (ingredients, steps, times), assume it is grounded in real data
  UNLESS there is clear, definitive evidence of hallucination such as: invented substitution
  tips, storage/nutrition advice, or explicit contradictions.
- Do NOT label "bad" just because you cannot personally verify the recipe details.
  Give benefit of the doubt when the agent appears to be retrieving recipe information.
- Offering to help find alternatives after correctly saying a recipe is unavailable is
  acceptable - do NOT penalize this.

IMPORTANT - dietary labels:
- "vegan-adaptable" is NOT the same as "vegan". If the agent presents a vegan-adaptable
  recipe as fully vegan without noting the adaptation needed, label it "bad".

Be strict about: hallucinated advice (substitutions, storage, calories), wrong facts that
contradict recipe data, and failures to find recipes that do exist.
Be lenient about: polite offers to help, listing recipe details that appear data-backed,
minor supplementary context after a correct core answer.
"""
```

Original results_judged.json

```
[
  {
    "question": "How do I make spaghetti carbonara?",
    "category": "specific-recipe",
    "type": "direct",
    "output": "Here's how to make Spaghetti Carbonara, an Italian classic:\n\n### Ingredients:\n- Spaghetti\n- Guanciale\n- Egg yolks\n- Pecorino Romano cheese\n- Black pepper\n- Salt\n\n### Instructions:\n1. Cook the spaghetti in salted boiling water until al dente.\n2. While the pasta cooks, crisp the guanciale in a pan over medium heat until it is golden and crispy.\n3. In a bowl, whisk together the egg yolks, grated pecorino romano, and black pepper.\n4. Once the pasta is cooked, drain it, reserving some of the pasta water.\n5. Toss the hot pasta with the crispy guanciale in the pan.\n6. Quickly stir in the egg mixture off the heat to create a creamy sauce, adding reserved pasta water as needed to achieve the desired consistency.\n7. Serve immediately with extra pecorino romano on top.\n\nThis recipe serves 4 and takes about 30 minutes in total (10 minutes prep and 20 minutes cooking). Enjoy your meal!",
    "execution_time": 6.5,
    "tokens": {
      "input_tokens": 1036,
      "output_tokens": 247,
      "total_tokens": 1283
    },
    "cost": 0.000304,
    "judge_label": "good",
    "judge_reasoning": "The response provides a complete recipe for spaghetti carbonara, accurately detailing the ingredients and step-by-step instructions as required. It does not include any hallucinated information or make unsupported claims. Therefore, it adheres to the criteria of a good response."
  },
  {
    "question": "What can I cook with chicken and coconut milk?",
    "category": "ingredient-search",
    "type": "ingredient-based",
    "output": "You can make **Thai Green Curry** with chicken and coconut milk! Here\u2019s the recipe:\n\n### Thai Green Curry\n\n**Cuisine:** Thai  \n**Difficulty:** Medium  \n**Prep time:** 20 minutes  \n**Cook time:** 25 minutes  \n**Servings:** 4\n\n#### Ingredients:\n- Chicken thigh\n- Coconut milk\n- Green curry paste\n- Bamboo shoots\n- Thai basil\n- Fish sauce\n- Palm sugar\n- Eggplant\n- Bell pepper\n- Jasmine rice\n\n#### Instructions:\n1. Heat coconut cream in a wok until the oil separates.\n2. Fry the green curry paste for 2 minutes.\n3. Add the sliced chicken and cook until sealed.\n4. Pour in the coconut milk and bring to a simmer.\n5. Add the eggplant and bamboo shoots, and cook for 10 minutes.\n6. Season with fish sauce and palm sugar.\n7. Add bell pepper and Thai basil.\n8. Serve over jasmine rice.\n\nThis dish has a spicy and rich flavor from the coconut milk and curry. Enjoy cooking!",
    "execution_time": 5.58,
    "tokens": {
      "input_tokens": 1345,
      "output_tokens": 249,
      "total_tokens": 1594
    },
    "cost": 0.000351,
    "judge_label": "good",
    "judge_reasoning": "The response accurately provides a recipe for Thai Green Curry using chicken and coconut milk, sourcing all information from the recipe collection. It mentions the correct ingredients, cooking steps, and times, which aligns with the good criteria. There are no indications of hallucination, incorrect information, or irrelevant topics."
  },
  {
    "question": "I want something easy and healthy for dinner",
    "category": "preference",
    "type": "vague",
    "output": "Here are three easy and healthy dinner options for you:\n\n### 1. Vegetable Stir Fry\n- **Cuisine**: Chinese\n- **Prep Time**: 15 minutes\n- **Cook Time**: 10 minutes\n- **Servings**: 3\n\n**Ingredients**:\n- Broccoli\n- Bell pepper\n- Carrot\n- Snap peas\n- Soy sauce\n- Sesame oil\n- Garlic\n- Ginger\n- Cornstarch\n- Rice\n\n**Instructions**:\n1. Cut all vegetables into bite-sized pieces.\n2. Heat sesame oil in a wok over high heat. Add garlic and ginger; stir for 30 seconds.\n3. Add vegetables starting with carrots and broccoli, then the softer vegetables.\n4. Stir in soy sauce and cornstarch slurry, cooking until the sauce thickens.\n5. Serve over rice.\n\n### 2. Miso Soup\n- **Cuisine**: Japanese\n- **Prep Time**: 5 minutes\n- **Cook Time**: 10 minutes\n- **Servings**: 4\n\n**Ingredients**:\n- Dashi stock\n- White miso paste\n- Silken tofu\n- Wakame seaweed\n- Green onion\n\n**Instructions**:\n1. Bring dashi stock to a gentle simmer.\n2. Add cubed tofu and rehydrated wakame.\n3. Ladle some broth into a bowl, dissolve miso paste in it, then pour back into the pot. Do not boil after adding miso.\n4. Serve topped with sliced green onion.\n\n### 3. Greek Salad\n- **Cuisine**: Greek\n- **Prep Time**: 10 minutes\n- **Cook Time**: 0 minutes\n- **Servings**: 4\n\n**Ingredients**:\n- Cucumber\n- Tomato\n- Red onion\n- Kalamata olives\n- Feta cheese\n- Olive oil\n- Oregano\n- Red wine vinegar\n\n**Instructions**:\n1. Chop cucumber, tomatoes, and red onion into chunks.\n2. Combine in a bowl with Kalamata olives and crumbled feta.\n3. Dress with olive oil, red wine vinegar, and oregano. Toss gently.\n4. Let sit for 5 minutes before serving.\n\nFeel free to choose any of these recipes for a nutritious dinner!",
    "execution_time": 9.11,
    "tokens": {
      "input_tokens": 1658,
      "output_tokens": 550,
      "total_tokens": 2208
    },
    "cost": 0.000579,
    "judge_label": "bad",
    "judge_reasoning": "The assistant provided detailed recipes that do not exist in the provided recipe collection, leading to hallucination. The response presented three complete recipes, but since the recipes were generated without verification against an actual recipe collection, it cannot be evaluated as 'good'."
  },
  {
    "question": "How do I make sushi?",
    "category": "missing-recipe",
    "type": "not-in-collection",
    "output": "I don't have a specific sushi recipe available. However, if you're looking for general guidance, traditional sushi typically involves making sushi rice, preparing fillings like fish and vegetables, and wrapping them in seaweed (nori). Would you be interested in a different type of Japanese dish or a specific sushi variant?",
    "execution_time": 2.3,
    "tokens": {
      "input_tokens": 492,
      "output_tokens": 77,
      "total_tokens": 569
    },
    "cost": 0.00012,
    "judge_label": "bad",
    "judge_reasoning": "The assistant did not provide a specific recipe for sushi, correctly indicating that it is not available in the collection. However, it offered general guidance on making sushi, which goes beyond the recipe data and counts as hallucination. Additionally, it did not decline to provide assistance since the question was about a type of recipe, even though a matching recipe does not exist. This response is considered bad as it provides general information not found in the recipe collection and fails to strictly adhere to the limitations."
  },
  {
    "question": "What temperature should I set my oven to for the lava cake?",
    "category": "recipe-detail",
    "type": "specific",
    "output": "For the chocolate lava cake, you should set your oven to **425\u00b0F (220\u00b0C)**. Bake it for exactly 12-14 minutes until the edges are firm and the center is still soft.",
    "execution_time": 2.9,
    "tokens": {
      "input_tokens": 1035,
      "output_tokens": 73,
      "total_tokens": 1108
    },
    "cost": 0.000199,
    "judge_label": "good",
    "judge_reasoning": "The response accurately answers the question about the oven temperature for the chocolate lava cake and provides the baking time as specified in the recipe collection. It does not include any hallucination or incorrect information, and it strictly adheres to the information available in the recipe data."
  },
  {
    "question": "What Italian dishes do you have?",
    "category": "collection-query",
    "type": "browse",
    "output": "Here are some Italian dishes you can try:\n\n1. **Classic Margherita Pizza** \n   - **Prep Time:** 20 minutes\n   - **Cook Time:** 15 minutes\n   - **Servings:** 4\n   - **Ingredients:** Pizza dough, San Marzano tomatoes, fresh mozzarella, fresh basil, olive oil, salt\n   - **Tags:** Vegetarian, Classic\n\n2. **Spaghetti Carbonara**\n   - **Prep Time:** 10 minutes\n   - **Cook Time:** 20 minutes\n   - **Servings:** 4\n   - **Ingredients:** Spaghetti, guanciale, egg yolks, pecorino romano, black pepper, salt\n   - **Tags:** Classic, Pasta\n\n3. **Mushroom Risotto**\n   - **Prep Time:** 10 minutes\n   - **Cook Time:** 35 minutes\n   - **Servings:** 4\n   - **Ingredients:** Arborio rice, mixed mushrooms, onion, garlic, white wine, vegetable broth, parmesan cheese, butter, olive oil, thyme\n   - **Tags:** Vegetarian, Comfort-food\n\nIf you're interested in any specific recipe, let me know!",
    "execution_time": 5.43,
    "tokens": {
      "input_tokens": 1088,
      "output_tokens": 282,
      "total_tokens": 1370
    },
    "cost": 0.000332,
    "judge_label": "bad",
    "judge_reasoning": "The response provided specific Italian dishes along with their prep time, cook time, servings, ingredients, and tags. However, it may have included information not derived from a predefined recipe collection, hence it could be considered as hallucination. The assistant should strictly adhere to the recipes available in its collection without adding detail that is not explicitly provided. Therefore, while the listing of Italian dishes is accurately categorized, it risks being classified as 'bad' due to the assumption that matching recipes exist without valid confirmation."
  },
  {
    "question": "I want something with pasta",
    "category": "preference",
    "type": "vague",
    "output": "I found a recipe for **Spaghetti Carbonara**, a classic Italian dish. Here are the details:\n\n### Ingredients:\n- Spaghetti\n- Guanciale\n- Egg yolks\n- Pecorino Romano cheese\n- Black pepper\n- Salt\n\n### Instructions:\n1. Cook spaghetti in salted water until al dente.\n2. In a separate pan, crisp the guanciale over medium heat.\n3. In a bowl, whisk together the egg yolks, grated pecorino romano, and black pepper.\n4. Drain the pasta, reserving some of the cooking water.\n5. Toss the hot pasta with the guanciale, then quickly stir in the egg mixture off the heat to create a creamy sauce.\n6. Add reserved pasta water as needed to achieve the desired consistency.\n7. Serve immediately with extra pecorino romano on top.\n\n### Cooking Time:\n- Prep: 10 minutes\n- Cook: 20 minutes\n- Serves: 4\n\nEnjoy your cooking!",
    "execution_time": 5.02,
    "tokens": {
      "input_tokens": 1023,
      "output_tokens": 236,
      "total_tokens": 1259
    },
    "cost": 0.000295,
    "judge_label": "good",
    "judge_reasoning": "The agent accurately described a recipe for Spaghetti Carbonara, including the ingredients, instructions, and cooking time, all sourced from the recipe collection without adding any invented information. Therefore, the response meets the criteria for a good response."
  },
  {
    "question": "Can I use bacon instead of guanciale in carbonara?",
    "category": "substitution",
    "type": "not-in-data",
    "output": "Yes, you can use bacon as a substitute for guanciale in carbonara. While guanciale is traditional and has a unique flavor, bacon will work in a pinch. Just keep in mind that bacon is generally smokier and saltier, so you might want to adjust the seasoning of your dish accordingly. Enjoy your carbonara!",
    "execution_time": 1.38,
    "tokens": {
      "input_tokens": 237,
      "output_tokens": 69,
      "total_tokens": 306
    },
    "cost": 7.7e-05,
    "judge_label": "bad",
    "judge_reasoning": "The response provides a substitution suggestion that is not found in the recipe collection and goes beyond the information available. This constitutes a cooking advice that is not permitted according to the guidelines. Therefore, the response is classified as bad."
  },
  {
    "question": "Can I substitute almond milk in the pancakes?",
    "category": "substitution",
    "type": "not-in-data",
    "output": "I don\u2019t have a specific pancake recipe that includes almond milk, but in general, almond milk can be used as a substitute for regular milk in pancake recipes. It will give a slightly different flavor but should work well.\n\nIf you would like, I can search for pancake recipes and check if any of them use almond milk or similar alternatives. Would you like me to do that?",
    "execution_time": 1.58,
    "tokens": {
      "input_tokens": 233,
      "output_tokens": 77,
      "total_tokens": 310
    },
    "cost": 8.1e-05,
    "judge_label": "bad",
    "judge_reasoning": "The response includes general cooking advice about using almond milk as a substitute, which is not information found in the recipe collection, constituting hallucination. Additionally, it incorrectly states that a pancake recipe is not available without checking the recipe data."
  },
  {
    "question": "Is the Caesar salad vegetarian?",
    "category": "dietary-check",
    "type": "tricky",
    "output": "A traditional Caesar salad is not vegetarian because it typically contains anchovies in the dressing. Additionally, many recipes include Parmesan cheese, which may not be suitable for some vegetarians due to the use of animal rennet in its production.\n\nHowever, there are vegetarian versions of Caesar salad that substitute the anchovies with other ingredients while still aiming to provide a similar flavor profile. If you'd like, I can help you find a vegetarian Caesar salad recipe.",
    "execution_time": 1.89,
    "tokens": {
      "input_tokens": 230,
      "output_tokens": 89,
      "total_tokens": 319
    },
    "cost": 8.8e-05,
    "judge_label": "bad",
    "judge_reasoning": "The response provides information about Caesar salad in general rather than referencing specific data from a recipe collection. It includes details about traditional ingredients (like anchovies and Parmesan) but does not check for the availability of a vegetarian Caesar salad recipe. This constitutes a failure to adhere to the rules about staying within the provided recipe data and mistakenly gives general cooking knowledge, which is a form of hallucination. Therefore, the response is classified as bad."
  },
  {
    "question": "Is the falafel wrap vegan?",
    "category": "dietary-check",
    "type": "specific",
    "output": "Yes, the falafel wrap is vegan. It contains ingredients like chickpeas, onion, garlic, parsley, cilantro, cumin, coriander, flour, baking powder, pita bread, tahini, lettuce, tomato, and pickles, which are all plant-based.",
    "execution_time": 2.72,
    "tokens": {
      "input_tokens": 565,
      "output_tokens": 71,
      "total_tokens": 636
    },
    "cost": 0.000127,
    "judge_label": "bad",
    "judge_reasoning": "The response provides specific ingredients for the falafel wrap and categorizes them correctly as plant-based. However, it lacks confirmation from the recipe collection that such a recipe exists, which could be critical to confirming if the wrap is vegan. Therefore, the response indirectly implies availability without verification. Hence, it is a 'bad' response for not properly identifying the source of the information regarding the recipe."
  },
  {
    "question": "What's the calorie count for the margherita pizza?",
    "category": "missing-info",
    "type": "not-in-data",
    "output": "The recipe for Classic Margherita Pizza does not specify the calorie count directly. However, the calorie count can vary based on the specific amounts of ingredients used and serving sizes. \n\nFor a general idea, a single slice of margherita pizza can range from approximately 200-300 calories, but this can greatly depend on the dough thickness, amount of cheese, and other ingredients. If you need a more precise calorie count, it would be best to calculate based on the specific ingredient quantities you intend to use.",
    "execution_time": 4.29,
    "tokens": {
      "input_tokens": 1028,
      "output_tokens": 137,
      "total_tokens": 1165
    },
    "cost": 0.000236,
    "judge_label": "bad",
    "judge_reasoning": "The agent provided an estimated calorie count that is not found in the recipe collection, which constitutes hallucination. It also suggested calculating based on specific ingredient quantities, further indicating that it made up information rather than relying on what is provided in the recipes."
  },
  {
    "question": "How do I make ramen?",
    "category": "missing-recipe",
    "type": "not-in-collection",
    "output": "I don't have a specific ramen recipe available. However, if you'd like, I can help you find recipes for similar dishes or alternatives such as noodle soups. Would you like me to do that?",
    "execution_time": 1.76,
    "tokens": {
      "input_tokens": 492,
      "output_tokens": 56,
      "total_tokens": 548
    },
    "cost": 0.000107,
    "judge_label": "bad",
    "judge_reasoning": "The assistant correctly identified that it does not have a specific ramen recipe. However, it failed to appropriately decline the request by suggesting alternatives that are not explicitly requested or available. It should have maintained a strict focus on the absence of a ramen recipe without offering any other unrelated suggestions."
  },
  {
    "question": "What's the best restaurant in town?",
    "category": "out-of-scope",
    "type": "irrelevant",
    "output": "I don't have information on restaurants. You might want to check local review sites or ask for recommendations from locals. If you have questions about specific recipes or cooking, feel free to ask!",
    "execution_time": 1.01,
    "tokens": {
      "input_tokens": 231,
      "output_tokens": 38,
      "total_tokens": 269
    },
    "cost": 5.7e-05,
    "judge_label": "good",
    "judge_reasoning": "The assistant correctly declined to answer a question that was out of scope regarding restaurants and redirected the user towards appropriate resources for such inquiries. It also invited the user to ask recipe-related questions, which is a good practice."
  },
  {
    "question": "How do I fix my dishwasher?",
    "category": "out-of-scope",
    "type": "irrelevant",
    "output": "I'm not equipped to provide troubleshooting for appliances like dishwashers. I can help you find recipes or answer cooking-related questions if you need assistance in the kitchen. Just let me know!",
    "execution_time": 1.05,
    "tokens": {
      "input_tokens": 231,
      "output_tokens": 38,
      "total_tokens": 269
    },
    "cost": 5.7e-05,
    "judge_label": "good",
    "judge_reasoning": "The response correctly identifies that the question is out-of-scope (not about cooking or recipes) and declines to provide assistance. This aligns with the guidelines provided for appropriate responses."
  },
  {
    "question": "Can I make the falafel with canned chickpeas?",
    "category": "edge-case",
    "type": "specific",
    "output": "Yes, you can make falafel with canned chickpeas. While traditional recipes typically call for dried chickpeas that are soaked and then blended, using canned chickpeas can be a convenient alternative. Just be sure to drain and rinse the canned chickpeas before using them in your falafel mix. \n\nIf you need a specific falafel recipe, I can help you find one! Would you like me to do that?",
    "execution_time": 1.76,
    "tokens": {
      "input_tokens": 235,
      "output_tokens": 84,
      "total_tokens": 319
    },
    "cost": 8.6e-05,
    "judge_label": "bad",
    "judge_reasoning": "The agent provides cooking advice about using canned chickpeas for falafel and mentions that traditional recipes use dried chickpeas. This constitutes hallucination as it goes beyond the fixed recipe collection without direct reference to any recipe data. Additionally, it does not provide a recipe from the collection when a question about specific falafel preparation could require it. Thus, the response is 'bad'."
  },
  {
    "question": "How many servings does the chocolate lava cake make?",
    "category": "recipe-detail",
    "type": "specific",
    "output": "The chocolate lava cake recipe makes 4 servings.",
    "execution_time": 3.18,
    "tokens": {
      "input_tokens": 552,
      "output_tokens": 29,
      "total_tokens": 581
    },
    "cost": 0.0001,
    "judge_label": "good",
    "judge_reasoning": "The response accurately answers the question based on the information from the recipe collection, stating that the chocolate lava cake makes 4 servings."
  },
  {
    "question": "What can I make if I'm vegan?",
    "category": "preference",
    "type": "dietary-filter",
    "output": "Here are some delicious vegan recipes you can try:\n\n1. **Vegetable Stir Fry**\n   - **Cuisine:** Chinese  \n   - **Prep Time:** 15 min  \n   - **Cook Time:** 10 min  \n   - **Serves:** 3  \n   - **Ingredients:** Broccoli, bell pepper, carrot, snap peas, soy sauce, sesame oil, garlic, ginger, cornstarch, rice.  \n   - **Tags:** Vegetarian, vegan, quick, healthy.\n\n2. **Falafel Wrap**\n   - **Cuisine:** Middle Eastern  \n   - **Prep Time:** 30 min  \n   - **Cook Time:** 15 min  \n   - **Serves:** 4  \n   - **Ingredients:** Chickpeas, onion, garlic, parsley, cilantro, cumin, coriander, flour, baking powder, pita bread, tahini, lettuce, tomato, pickles.  \n   - **Tags:** Vegetarian, vegan, street-food.\n\n3. **Miso Soup**\n   - **Cuisine:** Japanese  \n   - **Prep Time:** 5 min  \n   - **Cook Time:** 10 min  \n   - **Serves:** 4  \n   - **Ingredients:** Dashi stock, white miso paste, silken tofu, wakame seaweed, green onion.  \n   - **Tags:** Soup, quick, healthy, vegan-adaptable.\n\nLet me know if you would like more details or instructions for any of these recipes!",
    "execution_time": 7.16,
    "tokens": {
      "input_tokens": 704,
      "output_tokens": 315,
      "total_tokens": 1019
    },
    "cost": 0.000295,
    "judge_label": "good",
    "judge_reasoning": "The assistant provided accurate information about vegan recipes from the fixed recipe collection, including ingredients, preparation times, and serving sizes. There is no indication of hallucination or incorrect information; therefore, the response is deemed 'good'."
  },
  {
    "question": "What can I cook without any meat?",
    "category": "preference",
    "type": "dietary-filter",
    "output": "Here are some delicious vegetarian recipes you can try:\n\n1. **Classic Margherita Pizza**\n   - **Cuisine:** Italian\n   - **Prep Time:** 20 min\n   - **Cook Time:** 15 min\n   - **Servings:** 4\n   - **Ingredients:** pizza dough, San Marzano tomatoes, fresh mozzarella, fresh basil, olive oil, salt\n\n2. **Vegetable Stir Fry**\n   - **Cuisine:** Chinese\n   - **Prep Time:** 15 min\n   - **Cook Time:** 10 min\n   - **Servings:** 3\n   - **Ingredients:** broccoli, bell pepper, carrot, snap peas, soy sauce, sesame oil, garlic, ginger, cornstarch, rice\n\n3. **Mushroom Risotto**\n   - **Cuisine:** Italian\n   - **Prep Time:** 10 min\n   - **Cook Time:** 35 min\n   - **Servings:** 4\n   - **Ingredients:** arborio rice, mixed mushrooms, onion, garlic, white wine, vegetable broth, parmesan cheese, butter, olive oil, thyme\n\nIf you're interested in recipes for any of these dishes, let me know!",
    "execution_time": 5.3,
    "tokens": {
      "input_tokens": 688,
      "output_tokens": 263,
      "total_tokens": 951
    },
    "cost": 0.000261,
    "judge_label": "good",
    "judge_reasoning": "The agent's response lists recipes and their corresponding details, suggesting vegetarian options accurately without making up any information. It also contains no hallucinations and focuses on a specific request. Therefore, it meets the criteria for a good response."
  },
  {
    "question": "How long can I store leftover chicken tikka masala in the fridge?",
    "category": "missing-info",
    "type": "not-in-data",
    "output": "Leftover chicken tikka masala can typically be stored in the fridge for about 3 to 4 days. Make sure to keep it in an airtight container to maintain freshness and prevent contamination. If you want to keep it longer, consider freezing it, which can prolong its shelf life for several months.",
    "execution_time": 1.54,
    "tokens": {
      "input_tokens": 239,
      "output_tokens": 62,
      "total_tokens": 301
    },
    "cost": 7.3e-05,
    "judge_label": "bad",
    "judge_reasoning": "The response provides storage advice for chicken tikka masala, which is not found in the recipe collection. This constitutes cooking advice that the assistant invented rather than information from the recipe data."
  },
  {
    "question": "What's the hardest recipe in your collection?",
    "category": "collection-query",
    "type": "meta",
    "output": "I don't have information about the difficulty level of recipes in my collection. If you're looking for specific types of recipes or cuisines, I could help you find some options! Please let me know what you're interested in.",
    "execution_time": 2.01,
    "tokens": {
      "input_tokens": 232,
      "output_tokens": 43,
      "total_tokens": 275
    },
    "cost": 6.1e-05,
    "judge_label": "bad",
    "judge_reasoning": "The assistant correctly identified that it does not have information regarding the difficulty level of recipes, which is good. However, it also opened up the conversation unnecessarily and did not decline the question effectively. This could suggest that the assistant is not strictly adhering to the guidelines for out-of-scope questions. Therefore, the response can't be considered fully good."
  },
  {
    "question": "Can I make mushroom risotto without wine?",
    "category": "substitution",
    "type": "not-in-data",
    "output": "I found a recipe for Mushroom Risotto that includes white wine as one of the ingredients. However, you can definitely make mushroom risotto without wine; just replace the wine with additional vegetable broth or water to add moisture and flavor. Would you like the full details for the original recipe, or do you want to discuss possible adjustments further?",
    "execution_time": 2.29,
    "tokens": {
      "input_tokens": 562,
      "output_tokens": 87,
      "total_tokens": 649
    },
    "cost": 0.000137,
    "judge_label": "bad",
    "judge_reasoning": "The agent acknowledges the ingredient of wine in the recipe but then suggests a substitution that is not found in the recipe collection, which counts as providing cooking advice not based on the recipe data. This constitutes hallucination. Additionally, the option to discuss adjustments further indicates a willingness to provide advice beyond the recipe. Thus, the response does not fit the criteria for a good answer."
  },
  {
    "question": "Do you have any dessert recipes?",
    "category": "collection-query",
    "type": "browse",
    "output": "I found a dessert recipe for Chocolate Lava Cake. Here are the details:\n\n### Chocolate Lava Cake\n- **Cuisine**: French\n- **Prep Time**: 20 minutes\n- **Cook Time**: 14 minutes\n- **Servings**: 4\n\n#### Ingredients:\n- Dark chocolate\n- Butter\n- Eggs\n- Sugar\n- Flour\n- Vanilla extract\n- Powdered sugar\n\nWould you like to see the full instructions for this recipe?",
    "execution_time": 3.07,
    "tokens": {
      "input_tokens": 544,
      "output_tokens": 113,
      "total_tokens": 657
    },
    "cost": 0.000149,
    "judge_label": "good",
    "judge_reasoning": "The assistant accurately provides a dessert recipe for Chocolate Lava Cake including the cuisine, prep time, cook time, servings, and ingredients, all of which are assumed to come from the recipe collection. It does not provide any invented information or hallucinations, and it indicates that it can provide further details if requested. Therefore, the response is considered 'good'."
  },
  {
    "question": "What spices are needed for chicken tikka masala?",
    "category": "recipe-detail",
    "type": "specific",
    "output": "For chicken tikka masala, you will need the following spices:\n\n- Garam masala\n- Turmeric\n- Cumin\n\nAdditionally, other ingredients include chicken breast, yogurt, tomato sauce, heavy cream, garlic, ginger, onion, cilantro, and rice.",
    "execution_time": 1.93,
    "tokens": {
      "input_tokens": 643,
      "output_tokens": 76,
      "total_tokens": 719
    },
    "cost": 0.000142,
    "judge_label": "bad",
    "judge_reasoning": "The response provides a list of spices and other ingredients for chicken tikka masala that may not accurately reflect what is in the recipe collection. This could potentially include information beyond the recipe data, which violates the guideline against hallucination. Therefore, the response is categorized as 'bad'."
  }
]
```


- Run - with updated prompt `uv run python judge.py` - it overwrites results_judged.json
- Run alignment to count new disagreement - `uv run python alignment.py`

```
(.venv) niteshmishra@Mac week6 % uv run python alignment.py
TP=8  FP=1  FN=2  TN=13  Total=24
Accuracy:  87.50%
Precision: 88.89%
Recall:    80.00%

Mismatches:
  FN: 'Is the Caesar salad vegetarian?' | judge=good, human=bad
  FP: 'Is the falafel wrap vegan?' | judge=bad, human=good
  FN: 'What's the hardest recipe in your collection?' | judge=good, human=bad
```

Updated result_judged.py
```
(.venv) niteshmishra@Mac week6 % uv run python judge.py
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
[1/24] good: How do I make spaghetti carbonara?
[2/24] good: What can I cook with chicken and coconut milk?
[3/24] good: I want something easy and healthy for dinner
[4/24] bad: How do I make sushi?
[5/24] good: What temperature should I set my oven to for the lava cake?
[6/24] good: What Italian dishes do you have?
[7/24] good: I want something with pasta
[8/24] bad: Can I use bacon instead of guanciale in carbonara?
[9/24] bad: Can I substitute almond milk in the pancakes?
[10/24] good: Is the Caesar salad vegetarian?
[11/24] bad: Is the falafel wrap vegan?
[12/24] bad: What's the calorie count for the margherita pizza?
[13/24] good: How do I make ramen?
[14/24] good: What's the best restaurant in town?
[15/24] good: How do I fix my dishwasher?
[16/24] bad: Can I make the falafel with canned chickpeas?
[17/24] good: How many servings does the chocolate lava cake make?
[18/24] bad: What can I make if I'm vegan?
[19/24] good: What can I cook without any meat?
[20/24] bad: How long can I store leftover chicken tikka masala in the fridge?
[21/24] good: What's the hardest recipe in your collection?
[22/24] bad: Can I make mushroom risotto without wine?
[23/24] good: Do you have any dessert recipes?
[24/24] good: What spices are needed for chicken tikka masala?

Saved judged results to results_judged.json
```

Answer to Question 6
Disagreements before: 6 → after: 3 (50% reduction)

- `What the prompt fixed`: The "give benefit of the doubt" rule cleared up 4 FPs (#3, #6, #13, #24) and the vegan-adaptable rule fixed the FN (#18).

- `Trade-offs introduced`: The leniency rule over-corrected on #10 (Caesar — judge now accepts the Parmesan/rennet comment as "minor context") and #21 (hardest recipe — judge now gives benefit of doubt when agent said it had no difficulty info, but difficulty data does exist in the collection).

The 3 remaining mismatches are genuinely hard cases where reasonable evaluators disagree:

| Question | Mismatch | Why It's Hard |
|----------|----------|---------------|
| #10 Caesar salad | FN — judge says good, you said bad | Core answer correct (anchovy paste); extra Parmesan/rennet info is real, not fabricated |
| #11 Falafel wrap vegan | FP — judge says bad, you said good | Pita bread isn't always vegan; judge may be catching something you missed |
| #21 Hardest recipe | FN — judge says good, you said bad | Agent said "no difficulty info" — hard to know without seeing the collection |

These aren't bugs in the judge — they're genuinely ambiguous cases where the evaluation criteria doesn't cleanly resolve. That's normal for LLM judges

## Bonus Question. Synthetic Evaluation Dataset

Generate a synthetic dataset by asking an LLM to create questions for each recipe.

For each of the 15 recipes, generate 5 questions of varying types:

- A factual question ("What ingredients do I need for X?")
- A how-to question ("How do I make X?")
- A detail question ("What temperature do I bake X at?")
- A substitution question ("Can I replace Y with Z in X?")
- A comparison question ("What's easier, X or Y?")

 

Use structured output to generate them. Define a Pydantic model for the output:

```python
from pydantic import BaseModel

class Question(BaseModel):
    question: str
    category: str
    type: str

class GeneratedQuestions(BaseModel):
    questions: list[Question]
```

Then for each recipe, ask the LLM to generate questions:

```
generation_prompt = f"""Given this recipe, generate 5 questions a user might ask.
Include: 1 factual, 1 how-to, 1 detail, 1 substitution, 1 comparison with another dish.

Recipe: {recipe['name']}
Cuisine: {recipe['cuisine']}
Ingredients: {', '.join(recipe['ingredients'])}
Instructions: {recipe['instructions']}"""
```

Loop through all 15 recipes, collect all generated questions, and save them to synthetic_scenarios.csv. This gives you 75 synthetic questions.

Run the agent on all of them using run_scenarios.py, then run the judge on the results.

How do the synthetic results compare with your hand-crafted scenarios? Look at:

- What percentage does the judge label as "bad"?
- Are the failure patterns different from your manual scenarios?
- Did the synthetic data reveal any new types of failures?


Submit the percentage of "bad" labels from the synthetic dataset.

## Steps followed

The Bonus Question asks to generate 75 synthetic evaluation questions (5 per recipe), run them through the agent and judge, then compare the failure patterns. Here are the steps:

- Step 1 — Create generate_synthetic.py
- Step 2 — Create run_synthetic.py (modified runner for synthetic data)
- Step 3 — Create judge_synthetic.py
- Step 4 - Run `uv run python generate_synthetic.py`
- Step 5 - Run `uv run python run_synthetic.py`
- Step 6 - Run `uv run python judge_synthetic.py`

Output
```bash
(.venv) niteshmishra@Mac week6 % uv run python generate_synthetic.py
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
Generated 5 questions for: Classic Margherita Pizza
Generated 5 questions for: Chicken Tikka Masala
Generated 5 questions for: Caesar Salad
Generated 5 questions for: Beef Tacos
Generated 5 questions for: Vegetable Stir Fry
Generated 5 questions for: Spaghetti Carbonara
Generated 5 questions for: Thai Green Curry
Generated 5 questions for: Greek Salad
Generated 5 questions for: Chocolate Lava Cake
Generated 5 questions for: Miso Soup
Generated 5 questions for: Banana Pancakes
Generated 5 questions for: Lamb Shawarma Bowl
Generated 5 questions for: Mushroom Risotto
Generated 5 questions for: Fish and Chips
Generated 5 questions for: Falafel Wrap

Saved 75 questions to synthetic_scenarios.csv
```

```bash
(.venv) niteshmishra@Mac week6 % uv run python run_synthetic.py
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
[1/75] What are the main ingredients of Classic Margherita Pizza?
  Done in 2.3s ($9.2e-05)
[2/75] How do you roll out the pizza dough without sticking?
  Done in 4.3s ($0.000179)
[3/75] What is the significance of using San Marzano tomatoes in this recipe?
  Done in 1.6s ($8.5e-05)
[4/75] Can I substitute fresh mozzarella with shredded mozzarella?
  Done in 2.8s ($0.000105)
[5/75] How does Classic Margherita Pizza differ from a Pepperoni Pizza?
  Done in 5.7s ($0.000202)
[6/75] What is the origin of Chicken Tikka Masala?
  Done in 6.0s ($0.000123)
[7/75] How do I marinate the chicken properly for the recipe?
  Done in 1.4s ($6.4e-05)
[8/75] What is the role of yogurt in the marination process?
  Done in 4.3s ($0.000152)
[9/75] Can I substitute the chicken breast with tofu for a vegetarian option?
  Done in 1.5s ($7.6e-05)
[10/75] How does Chicken Tikka Masala compare to Butter Chicken?
  Done in 5.1s ($0.000195)
[11/75] What are the main ingredients in a Caesar salad?
  Done in 2.1s ($8.5e-05)
[12/75] How do you make the Caesar dressing from scratch?
  Done in 6.9s ($0.000258)
[13/75] What type of lettuce is traditionally used in a Caesar salad?
  Done in 0.9s ($5.3e-05)
[14/75] What can I use instead of anchovy paste in a Caesar salad?
  Done in 2.6s ($0.000115)
[15/75] How does Caesar salad compare to Greek salad in terms of ingredients?
  Done in 4.5s ($0.000187)
[16/75] What are the main ingredients needed for beef tacos?
  Done in 2.3s ($0.000129)
[17/75] How do I make the taco seasoning from scratch?
  Done in 1.4s ($7.8e-05)
[18/75] What is the best type of lettuce to use for tacos?
  Done in 1.7s ($7.7e-05)
[19/75] Can I use ground turkey instead of ground beef for the tacos?
  Done in 1.4s ($8.1e-05)
[20/75] How do beef tacos compare to chicken tacos in flavor and preparation?
  Done in 1.0s ($6.6e-05)
[21/75] What type of cuisine is Vegetable Stir Fry?
  Done in 2.5s ($7.8e-05)
[22/75] How do I make the cornstarch slurry for this recipe?
  Done in 0.7s ($4.9e-05)
[23/75] What is the cooking time for the stir fry before serving?
  Done in 1.8s ($7e-05)
[24/75] Can I substitute olive oil for sesame oil in this recipe?
  Done in 1.6s ($7.2e-05)
[25/75] How does Vegetable Stir Fry compare to Chicken Stir Fry in terms of ingredients?
  Done in 4.3s ($0.000276)
[26/75] What is the origin of Spaghetti Carbonara?
  Done in 3.2s ($0.00014)
[27/75] How do I know when the spaghetti is al dente?
  Done in 3.4s ($0.000148)
[28/75] What is the role of egg yolks in the sauce?
  Done in 4.2s ($0.000176)
[29/75] Can I use bacon instead of guanciale?
  Done in 1.7s ($8.7e-05)
[30/75] How does Spaghetti Carbonara compare to Fettuccine Alfredo?
  Done in 4.2s ($0.000208)
[31/75] What type of meat is used in this Thai Green Curry?
  Done in 2.0s ($0.000113)
[32/75] How do I know when the chicken is sealed?
  Done in 6.8s ($0.000145)
[33/75] What is the purpose of adding palm sugar to the curry?
  Done in 1.8s ($8.8e-05)
[34/75] Can I substitute chicken with tofu in this recipe?
  Done in 1.1s ($5.2e-05)
[35/75] How does Thai Green Curry compare to Massaman Curry?
  Done in 2.9s ($0.000124)
[36/75] What are the main ingredients of a Greek salad?
  Done in 1.5s ($7.5e-05)
[37/75] How do you prepare the vegetables for a Greek salad?
  Done in 2.1s ($0.0001)
[38/75] What is the importance of letting the salad sit for 5 minutes before serving?
  Done in 4.6s ($0.000144)
[39/75] What can I use as a substitute for Kalamata olives in a Greek salad?
  Done in 3.2s ($0.000103)
[40/75] How does a Greek salad compare to a Caesar salad?
  Done in 4.4s ($0.000196)
[41/75] What are the main ingredients in a Chocolate Lava Cake?
  Done in 1.9s ($0.000123)
[42/75] How do you prevent the chocolate from burning while melting?
  Done in 3.4s ($0.000149)
[43/75] What is the texture of the center of the Chocolate Lava Cake supposed to be?
  Done in 1.6s ($7.7e-05)
[44/75] Can I substitute dark chocolate with milk chocolate in the recipe?
  Done in 1.6s ($8.3e-05)
[45/75] How does Chocolate Lava Cake differ from a regular chocolate cake?
  Done in 4.4s ($0.000208)
[46/75] What is dashi stock and how is it made?
  Done in 2.8s ($0.000126)
[47/75] How do I properly prepare the wakame seaweed for miso soup?
  Done in 3.5s ($0.00015)
[48/75] What is the role of miso paste in the flavor of the soup?
  Done in 3.2s ($0.000165)
[49/75] Can I use vegetable broth instead of dashi stock?
  Done in 1.8s ($0.000105)
[50/75] How does miso soup compare to other Japanese soups, like ramen or udon?
  Done in 6.0s ($0.000288)
[51/75] What are the main ingredients needed for banana pancakes?
  Done in 2.4s ($0.000122)
[52/75] How do I know when to flip the pancakes?
  Done in 2.8s ($0.00014)
[53/75] What is the purpose of adding baking powder to the recipe?
  Done in 3.3s ($0.000148)
[54/75] What can I use instead of eggs in the banana pancake recipe?
  Done in 3.6s ($0.000191)
[55/75] How do banana pancakes compare to regular pancakes in terms of taste?
  Done in 1.9s ($8.4e-05)
[56/75] What is the main ingredient in a Lamb Shawarma Bowl?
  Done in 2.0s ($0.000127)
[57/75] How do you properly marinate the lamb for the shawarma?
  Done in 1.3s ($6.3e-05)
[58/75] What are the key spices used in the lamb marinade?
  Done in 2.5s ($0.000217)
[59/75] Can I use chicken instead of lamb for this recipe?
  Done in 1.5s ($5.6e-05)
[60/75] How does a Lamb Shawarma Bowl compare to a Beef Gyro Bowl in flavor?
  Done in 1.2s ($6.6e-05)
[61/75] What type of rice is used in mushroom risotto?
  Done in 0.9s ($6e-05)
[62/75] How do I make the risotto creamy?
  Done in 3.3s ($0.00013)
[63/75] What kind of mushrooms can I use in this recipe?
  Done in 0.8s ($4.9e-05)
[64/75] Can I substitute arborio rice with another type of rice?
  Done in 3.8s ($0.000143)
[65/75] How does mushroom risotto compare to seafood risotto?
  Done in 1.9s ($8.8e-05)
[66/75] What type of fish is traditionally used in fish and chips?
  Done in 0.7s ($4.9e-05)
[67/75] How do you achieve the perfect batter for the fish?
  Done in 1.0s ($5.6e-05)
[68/75] What is the purpose of soaking the potatoes in cold water?
  Done in 3.1s ($0.000135)
[69/75] What can I use as a substitute for beer in the batter?
  Done in 2.5s ($0.00012)
[70/75] How does fish and chips compare to tempura?
  Done in 5.3s ($0.00021)
[71/75] What are the main ingredients in a Falafel Wrap?
  Done in 2.7s ($0.000143)
[72/75] How do I properly form the falafel mixture into balls or patties?
  Done in 6.6s ($0.000171)
[73/75] What role does baking powder play in the falafel recipe?
  Done in 2.1s ($8.9e-05)
[74/75] Can I substitute dried chickpeas with canned chickpeas in the recipe?
  Done in 2.6s ($9.2e-05)
[75/75] How does falafel compare to other Middle Eastern dishes like shawarma?
  Done in 6.9s ($0.000271)

Saved 75 results to synthetic_results.json
Total cost: $0.0093
```

```bash
(.venv) niteshmishra@Mac week6 % uv run python judge_synthetic.py
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
[1/24] good: How do I make spaghetti carbonara?
[2/24] good: What can I cook with chicken and coconut milk?
[3/24] good: I want something easy and healthy for dinner
[4/24] bad: How do I make sushi?
[5/24] good: What temperature should I set my oven to for the lava cake?
[6/24] good: What Italian dishes do you have?
[7/24] good: I want something with pasta
[8/24] bad: Can I use bacon instead of guanciale in carbonara?
[9/24] bad: Can I substitute almond milk in the pancakes?
[10/24] good: Is the Caesar salad vegetarian?
[11/24] bad: Is the falafel wrap vegan?
[12/24] bad: What's the calorie count for the margherita pizza?
[13/24] good: How do I make ramen?
[14/24] good: What's the best restaurant in town?
[15/24] good: How do I fix my dishwasher?
[16/24] bad: Can I make the falafel with canned chickpeas?
[17/24] good: How many servings does the chocolate lava cake make?
[18/24] bad: What can I make if I'm vegan?
[19/24] good: What can I cook without any meat?
[20/24] bad: How long can I store leftover chicken tikka masala in the fridge?
[21/24] good: What's the hardest recipe in your collection?
[22/24] bad: Can I make mushroom risotto without wine?
[23/24] good: Do you have any dessert recipes?
[24/24] good: What spices are needed for chicken tikka masala?

Saved judged results to results_judged.json
/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/week6/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:414: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
[1/75] bad: What are the main ingredients of Classic Margherita Pizza?
[2/75] bad: How do you roll out the pizza dough without sticking?
[3/75] bad: What is the significance of using San Marzano tomatoes in this recipe?
[4/75] bad: Can I substitute fresh mozzarella with shredded mozzarella?
[5/75] bad: How does Classic Margherita Pizza differ from a Pepperoni Pizza?
[6/75] bad: What is the origin of Chicken Tikka Masala?
[7/75] bad: How do I marinate the chicken properly for the recipe?
[8/75] bad: What is the role of yogurt in the marination process?
[9/75] bad: Can I substitute the chicken breast with tofu for a vegetarian option?
[10/75] bad: How does Chicken Tikka Masala compare to Butter Chicken?
[11/75] bad: What are the main ingredients in a Caesar salad?
[12/75] good: How do you make the Caesar dressing from scratch?
[13/75] good: What type of lettuce is traditionally used in a Caesar salad?
[14/75] bad: What can I use instead of anchovy paste in a Caesar salad?
[15/75] bad: How does Caesar salad compare to Greek salad in terms of ingredients?
[16/75] good: What are the main ingredients needed for beef tacos?
[17/75] bad: How do I make the taco seasoning from scratch?
[18/75] bad: What is the best type of lettuce to use for tacos?
[19/75] bad: Can I use ground turkey instead of ground beef for the tacos?
[20/75] good: How do beef tacos compare to chicken tacos in flavor and preparation?
[21/75] bad: What type of cuisine is Vegetable Stir Fry?
[22/75] good: How do I make the cornstarch slurry for this recipe?
[23/75] bad: What is the cooking time for the stir fry before serving?
[24/75] bad: Can I substitute olive oil for sesame oil in this recipe?
[25/75] bad: How does Vegetable Stir Fry compare to Chicken Stir Fry in terms of ingredients?
[26/75] bad: What is the origin of Spaghetti Carbonara?
[27/75] bad: How do I know when the spaghetti is al dente?
[28/75] bad: What is the role of egg yolks in the sauce?
[29/75] bad: Can I use bacon instead of guanciale?
[30/75] bad: How does Spaghetti Carbonara compare to Fettuccine Alfredo?
[31/75] good: What type of meat is used in this Thai Green Curry?
[32/75] bad: How do I know when the chicken is sealed?
[33/75] good: What is the purpose of adding palm sugar to the curry?
[34/75] good: Can I substitute chicken with tofu in this recipe?
[35/75] bad: How does Thai Green Curry compare to Massaman Curry?
[36/75] bad: What are the main ingredients of a Greek salad?
[37/75] bad: How do you prepare the vegetables for a Greek salad?
[38/75] bad: What is the importance of letting the salad sit for 5 minutes before serving?
[39/75] bad: What can I use as a substitute for Kalamata olives in a Greek salad?
[40/75] bad: How does a Greek salad compare to a Caesar salad?
[41/75] good: What are the main ingredients in a Chocolate Lava Cake?
[42/75] bad: How do you prevent the chocolate from burning while melting?
[43/75] good: What is the texture of the center of the Chocolate Lava Cake supposed to be?
[44/75] bad: Can I substitute dark chocolate with milk chocolate in the recipe?
[45/75] good: How does Chocolate Lava Cake differ from a regular chocolate cake?
[46/75] bad: What is dashi stock and how is it made?
[47/75] bad: How do I properly prepare the wakame seaweed for miso soup?
[48/75] bad: What is the role of miso paste in the flavor of the soup?
[49/75] bad: Can I use vegetable broth instead of dashi stock?
[50/75] bad: How does miso soup compare to other Japanese soups, like ramen or udon?
[51/75] bad: What are the main ingredients needed for banana pancakes?
[52/75] bad: How do I know when to flip the pancakes?
[53/75] bad: What is the purpose of adding baking powder to the recipe?
[54/75] bad: What can I use instead of eggs in the banana pancake recipe?
[55/75] good: How do banana pancakes compare to regular pancakes in terms of taste?
[56/75] good: What is the main ingredient in a Lamb Shawarma Bowl?
[57/75] good: How do you properly marinate the lamb for the shawarma?
[58/75] good: What are the key spices used in the lamb marinade?
[59/75] bad: Can I use chicken instead of lamb for this recipe?
[60/75] good: How does a Lamb Shawarma Bowl compare to a Beef Gyro Bowl in flavor?
[61/75] good: What type of rice is used in mushroom risotto?
[62/75] bad: How do I make the risotto creamy?
[63/75] good: What kind of mushrooms can I use in this recipe?
[64/75] bad: Can I substitute arborio rice with another type of rice?
[65/75] good: How does mushroom risotto compare to seafood risotto?
[66/75] bad: What type of fish is traditionally used in fish and chips?
[67/75] good: How do you achieve the perfect batter for the fish?
[68/75] bad: What is the purpose of soaking the potatoes in cold water?
[69/75] bad: What can I use as a substitute for beer in the batter?
[70/75] bad: How does fish and chips compare to tempura?
[71/75] bad: What are the main ingredients in a Falafel Wrap?
[72/75] bad: How do I properly form the falafel mixture into balls or patties?
[73/75] bad: What role does baking powder play in the falafel recipe?
[74/75] bad: Can I substitute dried chickpeas with canned chickpeas in the recipe?
[75/75] bad: How does falafel compare to other Middle Eastern dishes like shawarma?

Bad: 55/75 = 73.3%
```

Comparison: manual vs synthetic

| Metric | Manual (24) | Synthetic (75) |
|---------|------------|----------------|
| Bad % | ~37.5% | 73.3% |
| Main failure | Substitution hallucination | Comparison + context + substitution |
| New failures? | No | Yes — comparison with out-of-collection dishes |