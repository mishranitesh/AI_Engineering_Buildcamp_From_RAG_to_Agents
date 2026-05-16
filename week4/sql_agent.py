from pydantic import BaseModel
from pydantic_ai import Agent
from sql_tools import SQLTools

sql_tools = SQLTools()

class SQLResult(BaseModel):
    sql_query: str
    result_text: str
    row_count: int

agent = Agent(
    "openai:gpt-4o-mini",
    output_type=SQLResult,
    tools=[sql_tools.get_schema, sql_tools.run_sql],
    system_prompt="Always call get_schema first before running queries."
)