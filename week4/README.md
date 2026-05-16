# Homework (mini-project)

In this homework we'll build a simple SQL agent that queries NYC taxi data using DuckDB, then write tests for it. The first two questions set up the agent. Questions 3 through 6 focus on testing: writing tests, verifying tool calls, using LLM judges, and tracking costs.

Note: For all questions, if your answer doesn't match exactly, pick the closest option.

# Question 1. Set Up DuckDB

- Install the required packages:

```bash
uv init
uv add duckdb pydantic-ai
```

- Create a file called sql_tools.py. Start with the database setup:

```python
import os
import urllib.request

import duckdb

DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
PARQUET_FILE = "yellow_tripdata_2024-01.parquet"

con = duckdb.connect("taxi.db")


def setup_database():
    """Download the parquet file and load it into DuckDB."""
    if not os.path.exists(PARQUET_FILE):
        print(f"Downloading {DATA_URL}...")
        urllib.request.urlretrieve(DATA_URL, PARQUET_FILE)

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS trips AS
        SELECT * FROM '{PARQUET_FILE}'
    """)
    count = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"Loaded {count} rows")
    return count
```

This connects to a local DuckDB file and downloads the NYC Yellow Taxi January 2024 dataset. The data is loaded once and persists in taxi.db.

Run the setup:

```python
from sql_tools import setup_database
count = setup_database()
```

How many rows are in the January 2024 dataset?

- 1,964,624
- 2,964,624 <-- answer
- 3,964,624
- 4,964,624

## Output
```
(week4) niteshmishra@Mac week4 % python sql_tools.py
Downloading https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet...
Loaded 2964624 rows
2964624
```

# Question 2. Create the Agent

Now implement the tools and the agent. You can use any AI assistant (ChatGPT, Claude, etc.) to help you write the code.

Add a SQLTools class to sql_tools.py with two methods (follow the same pattern we used in the module):

- get_schema() - runs DESCRIBE trips and returns all column names with their types
- run_sql(query) - executes a SQL query and returns results as text (column headers + data rows, limited to 50 rows)

Create a separate file called sql_agent.py with:

- A SQLResult pydantic model with three fields: sql_query, result_text, row_count

- A PydanticAI Agent using gpt-4o-mini, SQLResult as the output type, and the two SQL tools (pass the methods as a list: tools=[sql_tools.get_schema, sql_tools.run_sql])

- Instructions that tell the agent to always start by getting the schema before running queries


Test your agent by running uv run python sql_agent.py and asking: "What's the average trip distance for rides with 2 passengers?"

What's the average trip distance?

- 2.78
- 3.78 <-- answer
- 4.78
- 5.78

## step followed - 

1. Include methods in sql_tools.py as get_schema and run_sql
2. Create agent - sql_agent.py
3. Setup - OPENAI_API_KEY - already set in .zshrc
3. run - `uv run python sql_agent.py`

## Output
```
(week4) niteshmishra@Mac week4 % uv run python sql_agent.py
Loaded 2964624 rows
/Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
  self._model = models.infer_model(model)
sql_query='SELECT AVG(trip_distance) AS average_trip_distance FROM trips WHERE passenger_count = 2;' result_text='The average trip distance for rides with 2 passengers is approximately 3.78 miles.' row_count=1
```

## just for verification - execute - duckdb query 
```python
"""
SELECT AVG(trip_distance)
FROM trips
WHERE passenger_count = 2;
"""
python duck_dq_queries.py
Question 2 - What's the average trip distance for rides with 2 passengers?
(3.7827640377879255,)
```

# Question 3. Write Your First Test

Install the test dependencies:
```bash
uv add --dev pytest pytest-asyncio
```

Create a file called test_agent.py. Write a test that asks the agent "How many trips had more than 5 passengers?" and asserts that:

- output.sql_query is a non-empty string
- output.result_text contains the actual count

Since the data doesn't change, you can verify the exact number. Run the query directly in DuckDB first to find the answer, then assert that the agent's result_text contains that number.

How many trips had more than 5 passengers?

- 2,413
- 12,413
- 22,413 <-- answer
- 32,413

## Steps followed - 
1. for assert in test_agent.py - execute - sql query 
```
(week4) niteshmishra@Mac week4 % python duck_dq_queries.py
Question 2 - What's the average trip distance for rides with 2 passengers?
(3.782764037787934,)
Question 3 - How many rides had more than 5 passengers?
(22413,)
```
2. write - test_agent.py with 2 assert 
```python
 # SQL query should exist
    assert output.sql_query != ""

    # Result should contain actual count
    assert "22413" in output.result_text
```
3. Run `uv run pytest`

## Output

- Test failed 
```
(week4) niteshmishra@Mac week4 % uv run pytest
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4
configfile: pyproject.toml
plugins: logfire-4.33.0, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 0 items

============================================================================================ no tests ran in 0.01s =============================================================================================
(week4) niteshmishra@Mac week4 % clear
(week4) niteshmishra@Mac week4 % uv run pytest
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4
configfile: pyproject.toml
plugins: logfire-4.33.0, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

test_agent.py F                                                                                                                                                                                          [100%]

=================================================================================================== FAILURES ===================================================================================================
______________________________________________________________________________________ test_trips_more_than_5_passengers _______________________________________________________________________________________

    def test_trips_more_than_5_passengers():

        result = agent.run_sync(
            "How many trips had more than 5 passengers?"
        )

        output = result.output

        # SQL query should exist
        assert output.sql_query != ""

        # Result should contain actual count
>       assert "22413" in output.result_text
E       AssertionError: assert '22413' in 'There were 22,413 trips with more than 5 passengers.'
E        +  where 'There were 22,413 trips with more than 5 passengers.' = SQLResult(sql_query='SELECT COUNT(*) AS trip_count FROM trips WHERE passenger_count > 5;', result_text='There were 22,413 trips with more than 5 passengers.', row_count=22413).result_text

test_agent.py:16: AssertionError
=============================================================================================== warnings summary ===============================================================================================
.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
    self._model = models.infer_model(model)

.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970: DeprecationWarning: There is no current event loop
    event_loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================================================================================== short test summary info ============================================================================================
FAILED test_agent.py::test_trips_more_than_5_passengers - AssertionError: assert '22413' in 'There were 22,413 trips with more than 5 passengers.'
======================================================================================== 1 failed, 2 warnings in 9.73s =========================================================================================
(week4) niteshmishra@Mac week4 %
```

## Reason - 
```
Your test is failing because the agent returned: 22,413
with a comma, but your assertion checks for: "22413"
```

## Fixed assert in test_agent.py. Output after fix - 
```
(week4) niteshmishra@Mac week4 % uv run pytest
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4
configfile: pyproject.toml
plugins: logfire-4.33.0, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

test_agent.py .                                                                                                                                                                                          [100%]

=============================================================================================== warnings summary ===============================================================================================
.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
    self._model = models.infer_model(model)

.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970: DeprecationWarning: There is no current event loop
    event_loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================================================================== 1 passed, 2 warnings in 8.26s =========================================================================================
(week4) niteshmishra@Mac week4 %
```

# Question 4. Testing Tool Calls

Your agent should always get the schema first, then run SQL queries. Let's write a test that verifies this behavior by checking the order of tool calls.

Create a file called utils.py with the collect_tools helper from the module. This function extracts tool calls from the agent's message history.

In test_agent.py, write a test that:

- Ask "What is the most common payment type?"
- Asserts the first tool call is get_schema
- Asserts that run_sql is also called

What is the name of the second tool the agent calls?

- get_schema
- run_sql <-- run sql
- describe_table
- list_columns

## steps followed 

- 1. reate utils.py with collect_tools helper to extract tool calls from agent's message history
- 2. Add test in test-agent.py
- 3. Run `uv run pytest`

## Output 
```
 week4 % uv run pytest
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4
configfile: pyproject.toml
plugins: logfire-4.33.0, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

test_agent.py .                                                                                                                                                                                          [100%]

=============================================================================================== warnings summary ===============================================================================================
.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
    self._model = models.infer_model(model)

.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970: DeprecationWarning: There is no current event loop
    event_loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================================================================== 1 passed, 2 warnings in 8.59s =========================================================================================
(week4) niteshmishra@Mac week4 %
```

Or run `uv run pytest -s test_agent.py::test_tool_order` for specific tests

# Question 5. LLM Judge Test

Now let's add an LLM judge that evaluates the agent's output using natural language criteria. Create a judge.py file with the judge from the module (the evaluate_agent_performance and assert_criteria functions).

Write a test that asks the agent "Which hour of the day has the highest average fare amount?" and evaluates the response with these criteria:

- the SQL query correctly calculates average fare by hour of day
- the result identifies a specific hour as having the highest average fare
- the result includes the actual average fare amount

Which hour of the day has the highest average fare amount?

- 4
- 5 <-- answer
- 17
- 22

## steps followed - 

- 1. Create judge.py and include evaluation for the agent's output using natural language criteria
- 2. Write test in test_agent.py 
- 3. Run - `uv run pytest -s test_agent.py::test_llm_judge`

## For verification - sql output 
```sql
 SELECT EXTRACT(HOUR FROM tpep_pickup_datetime) AS hour,
       AVG(fare_amount) AS avg_fare
    FROM trips
    GROUP BY hour
    ORDER BY avg_fare DESC
    LIMIT 1;

-- Output : 
"""
(week4) niteshmishra@Mac week4 % python duck_dq_queries.py
Question 2 - What's the average trip distance for rides with 2 passengers?
(3.7827640377879264,)
Question 3 - How many rides had more than 5 passengers?
(22413,)
Question 5 - Which hour of the day has the highest average fare amount?
(5, 26.61991846088257)
"""
```

## Output of test_llm_agent
```
(week4) niteshmishra@Mac week4 % rm -rf __pycache__
uv run pytest -s test_agent.py::test_llm_judge
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4
configfile: pyproject.toml
plugins: logfire-4.33.0, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 1 item

test_agent.py Loaded 2964624 rows
Judge Evaluation:
Score: 10
Reasoning: The SQL query correctly extracts the hour from the pickup datetime, calculates the average fare for each hour, and sorts the results to find the hour with the highest average fare. The result specifically identifies a time (5 AM) along with its corresponding average fare amount ($26.62), meeting all evaluation criteria.
.

=============================================================================================== warnings summary ===============================================================================================
.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
    self._model = models.infer_model(model)

test_agent.py::test_llm_judge
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970: DeprecationWarning: There is no current event loop
    event_loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================================================================== 1 passed, 2 warnings in 6.29s =========================================================================================
```

# Question 6. Writing More Tests

Here are more questions you can ask the agent:

- "What is the average tip amount for credit card payments?"
- "Which pickup location (PULocationID) has the most trips?"
- "What is the average fare for trips longer than 10 miles?"
- "How many trips had zero passengers recorded?"
- "What is the busiest day of the week for taxi trips?"


For each question, think about what scenario you are testing:

- Which columns should appear in the SQL query?
- In what order should the tools be called?
- What specific value should the result contain?

Write or generate tests with AI for each of these queries.

For the question "How many trips had zero passengers recorded?", which column should the agent's SQL query filter on?

- tip_amount
- fare_amount
- passenger_count <-- answer
- trip_distance


## 1. What is the average tip amount for credit card payments?

### Scenario being tested
- Filtering categorical column (payment method)
- Aggregation correctness (AVG)

### Columns expected
- tip_amount
- payment_type

### Tool order expected
- get_schema
- run_sql

### SQL shape expectation
- WHERE payment_type = 'Credit Card'
- AVG(tip_amount)

### Result expectation
- Single numeric value (float)
- One row only



## 2. Which pickup location has the most trips?

### Scenario being tested
- GROUP BY correctness
- ranking logic

### Columns expected
- PULocationID


### Tool order expected
- get_schema
- run_sql

### SQL shape expectation
- COUNT(*)
- GROUP BY PULocationID
- ORDER BY COUNT DESC
- LIMIT 1


### Result expectation
- 1 row
- contains location ID + count



## 3. Average fare for trips longer than 10 miles
### Scenario being tested
- numeric filtering
- aggregation with condition


### Columns expected
- trip_distance
- fare_amount

### Tool order expected
- get_schema
- run_sql

### SQL shape expectation
- WHERE trip_distance > 10
- AVG(fare_amount)

### Result expectation
- single float value



## 4. How many trips had zero passengers recorded?
### Scenario being tested
- edge-case filtering
- count aggregation

### Columns expected
- passenger_count

### Tool order expected
- get_schema
- run_sql

### SQL shape expectation
- WHERE passenger_count = 0
- COUNT(*)

### Result expectation
- single integer



## 5. What is the busiest day of the week?
### Scenario being tested
- time transformation
- derived feature grouping

### Columns expected
- pickup datetime column (e.g. tpep_pickup_datetime)

### Tool order expected
- get_schema
- run_sql 

### SQL shape expectation
- extract day:
- strftime('%w', pickup_datetime)
- GROUP BY
- ORDER BY COUNT DESC
- LIMIT 1

### Result expectation
- one row (day + count)

## Question 7 (Bonus). Cost Tracking

Add cost tracking from the module (patch_agent.py and conftest.py) and run the full test suite. What is the approximate total cost?

- Less than $0.05 <-- answer
- $0.05 - $0.20
- $0.20 - $1.00
- More than $1.00

### After adding patch_agent.py and conftest.py Run `pytest -v -s`


### Output
```
(week4) niteshmishra@Mac week4 % pytest -v -s
============================================================================================= test session starts ==============================================================================================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0 -- /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4
configfile: pyproject.toml
plugins: logfire-4.33.0, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 8 items

test_agent.py::test_trips_more_than_5_passengers Loaded 2964624 rows
input=647, output=90, cost=$0.000151
PASSED
test_agent.py::test_tool_order input=654, output=106, cost=$0.000162
tools called: ['get_schema', 'run_sql', 'final_result']
PASSED
test_agent.py::test_llm_judge input=695, output=162, cost=$0.000201
Judge Evaluation:
Score: 10
Reasoning: The SQL query correctly calculates the average fare amount grouped by the hour of the day. It uses the EXTRACT function to get the hour from the pickup datetime, averages the fare amounts, groups the results by hour, and orders them to find the hour with the highest average fare. Additionally, the result successfully identifies a specific hour (5 AM) along with the numeric average fare amount ($26.62), meeting all the evaluation criteria.
PASSED
test_agent.py::test_avg_tip_credit_card input=660, output=100, cost=$0.000159
tools called: ['get_schema', 'run_sql', 'final_result']
PASSED
test_agent.py::test_pickup_location_with_most_trips input=688, output=143, cost=$0.000189
tools called: ['get_schema', 'run_sql', 'final_result']
PASSED
test_agent.py::test_avg_fare_long_trips input=668, output=104, cost=$0.000163
tools called: ['get_schema', 'run_sql', 'final_result']
PASSED
test_agent.py::test_zero_passenger_trips input=647, output=97, cost=$0.000155
tools called: ['get_schema', 'run_sql', 'final_result']
PASSED
test_agent.py::test_busiest_day_of_week input=691, output=149, cost=$0.000193
tools called: ['get_schema', 'run_sql', 'final_result']
PASSED
==================================================
Approximate Total LLM Cost: $0.001373
==================================================


=============================================================================================== warnings summary ===============================================================================================
.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/agent/__init__.py:394: PydanticAIDeprecationWarning: In v2.0, 'openai:' will resolve to the OpenAI Responses API by default. Use 'openai-chat:' to keep current Chat Completions behavior, or 'openai-responses:' to opt in early.
    self._model = models.infer_model(model)

test_agent.py::test_trips_more_than_5_passengers
  /Users/niteshmishra/AI/AI_Engineering_Buildcamp_From_RAG_to_Agents/week4/.venv/lib/python3.13/site-packages/pydantic_ai/_utils.py:970: DeprecationWarning: There is no current event loop
    event_loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================================================================== 8 passed, 2 warnings in 30.63s ========================================================================================
(week4) niteshmishra@Mac week4 %
```