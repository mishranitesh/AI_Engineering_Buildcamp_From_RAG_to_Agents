from sql_agent import agent
from utils import collect_tools
from judge import assert_criteria    


def test_trips_more_than_5_passengers(sql_agent):

    result = agent.run_sync(
        "How many trips had more than 5 passengers?"
    )

    output = result.output

    # SQL query should exist
    assert output.sql_query != ""

    # Result should contain actual count
    assert "22,413" in output.result_text

def test_tool_order(sql_agent):

    result = agent.run_sync(
        "What is the most common payment type?"
    )

    tools = collect_tools(result.all_messages())

    # First tool should be schema lookup
    assert tools[0] == "get_schema"

    # SQL execution should happen
    assert "run_sql" in tools

    # Second tool call
    assert tools[1] == "run_sql"

def test_llm_judge(sql_agent, judge):

    question = "Which hour of the day has the highest average fare amount?"

    result = sql_agent.run_sync(question)
    output = result.output

    criteria = """
    - SQL correctly calculates average fare grouped by hour of day
    - result identifies a specific hour with highest average fare
    - result includes actual numeric average fare
    """

    judge_result = judge(
        question=question,
        sql=output.sql_query,
        result=output.result_text,
        criteria=criteria
    )

    print("Judge Evaluation:")
    print(f"Score: {judge_result.output.score}")
    print(f"Reasoning: {judge_result.output.reasoning}")

    # Assert that the judge gives a score of at least 7 out of 10
    assert_criteria(judge_result)

def test_avg_tip_credit_card(sql_agent):

    result = sql_agent.run_sync(
        "What is the average tip amount for credit card payments?"
    )

    output = result.output

    tools = collect_tools(result.all_messages())

    # Tool order
    assert tools[0] == "get_schema"
    assert tools[1] == "run_sql"

    # SQL expectations
    sql = output.sql_query.lower()

    assert "avg" in sql
    assert "tip_amount" in sql
    assert "payment" in sql
    assert "where" in sql

    # Result expectations
    assert output.result_text != ""
    assert output.row_count == 1


def test_pickup_location_with_most_trips(sql_agent):

    result = sql_agent.run_sync(
        "Which pickup location (PULocationID) has the most trips?"
    )

    output = result.output

    tools = collect_tools(result.all_messages())

    # Tool order
    assert tools[0] == "get_schema"
    assert tools[1] == "run_sql"

    sql = output.sql_query.lower()

    # SQL expectations
    assert "pulocationid" in sql
    assert "count" in sql
    assert "group by" in sql
    assert "order by" in sql
    assert "limit 1" in sql

    # Result expectations
    assert output.result_text != ""
    assert output.row_count == 1


def test_avg_fare_long_trips(sql_agent):

    result = sql_agent.run_sync(
        "What is the average fare for trips longer than 10 miles?"
    )

    output = result.output

    tools = collect_tools(result.all_messages())

    # Tool order
    assert tools[0] == "get_schema"
    assert tools[1] == "run_sql"

    sql = output.sql_query.lower()

    # SQL expectations
    assert "trip_distance" in sql
    assert "fare_amount" in sql
    assert "avg" in sql
    assert "where" in sql
    assert "> 10" in sql or ">10" in sql

    # Result expectations
    assert output.result_text != ""
    assert output.row_count == 1


def test_zero_passenger_trips(sql_agent):

    result = sql_agent.run_sync(
        "How many trips had zero passengers recorded?"
    )

    output = result.output

    tools = collect_tools(result.all_messages())

    # Tool order
    assert tools[0] == "get_schema"
    assert tools[1] == "run_sql"

    sql = output.sql_query.lower()

    # SQL expectations
    assert "passenger_count" in sql
    assert "count" in sql
    assert "where" in sql
    assert "= 0" in sql or "=0" in sql

    # Result expectations
    assert output.result_text != ""
    assert output.row_count > 0


def test_busiest_day_of_week(sql_agent):

    result = sql_agent.run_sync(
        "What is the busiest day of the week for taxi trips?"
    )

    output = result.output

    tools = collect_tools(result.all_messages())

    # Tool order
    assert tools[0] == "get_schema"
    assert tools[1] == "run_sql"

    sql = output.sql_query.lower()

    # SQL expectations
    assert "count" in sql
    assert "group by" in sql
    assert "order by" in sql
    assert "limit 1" in sql

    # Time transformation check
    assert (
        "strftime" in sql
        or "extract" in sql
        or "dayofweek" in sql
    )

    # Result expectations
    assert output.result_text != ""
    assert output.row_count > 0