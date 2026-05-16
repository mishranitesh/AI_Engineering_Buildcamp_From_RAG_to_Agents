# Chapter - Testing for Agents - Outcome: Set up test frameworks for your agents

# Lesson 2 - First Agent Test   

## Creating the Test - Create a tests/ directory and a test_agent.py file inside it.
```python
def create_test_agent():
    tools = create_documentation_tools_cached()
    agent_config = DocumentationAgentConfig(
        instructions=DEFAULT_INSTRUCTIONS
    )

    agent = create_agent(agent_config, tools)
    return agent


@pytest.mark.asyncio
async def test_agent_runs():
    agent = create_test_agent()

    user_prompt = 'llm as a judge'
    result = await run_agent_stream(agent, user_prompt)

    search_result = result.output
    assert search_result.answer is not None
    assert search_result.confidence >= 0.0
    assert search_result.found_answer is True
    assert len(search_result.followup_questions) > 0
```
# Lesson 3 - Testing Tool Calls

## Extracting Tool Calls
```python
@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
```
## Then create a function that collects tool calls from messages:
```python
def collect_tools(messages):
    tool_calls = []

    for m in messages:
        for p in m.parts:
            part_kind = p.part_kind

            if part_kind != 'tool-call':
                continue

            if p.tool_name == 'final_result':
                continue

            tool_calls.append(ToolCall(p.tool_name, p.args))

    return tool_calls
```
## Creating a Test for Tool Calls
```python
@pytest.mark.asyncio
async def test_agent_uses_tools():
    agent = create_test_agent()

    user_prompt = 'llm as a judge'
    result = await run_agent_stream(agent, user_prompt)

    messages = result.new_messages()

    tool_calls = collect_tools(messages)
    assert len(tool_calls) >= 2

    search_call = tool_calls[0]
    assert search_call.name == 'search'

    get_file_call = tool_calls[1]
    assert get_file_call.name == 'get_file'
```
## Running the Test
```bash
uv run pytest tests/test_agent.py::test_agent_uses_tools -s
```
# Lesson 4 - Refactoring for tests

## Measuring Loading Time
```python
from time import time

def create_test_agent():
    t0 = time()

    tools = create_documentation_tools_cached()
    agent_config = DocumentationAgentConfig(
        instructions=DEFAULT_INSTRUCTIONS
    )
    agent = create_agent(agent_config, tools)

    t1 = time()
    print(f'loading agent took {t1 - t0}')
    return agent
```

## Pytest Fixtures - sets up shared resources. Tests that need the fixture add it as a parameter, and pytest handles the injection automatically:

```python
from time import time

@pytest.fixture(scope="module") # scope="module" means the fixture is created once per test module, not once per test
def agent():
    t0 = time()

    tools = create_documentation_tools_cached()
    agent_config = DocumentationAgentConfig(
        instructions=DEFAULT_INSTRUCTIONS
    )

    agent = create_agent(agent_config, tools)

    t1 = time()
    print(f'loading agent took {t1 - t0}')

    return agent
```

## Refactoring to AgentStreamRunner

```python
class AgentStreamRunner:

    def __init__(self, agent: Agent, handler: JSONParserHandler):
        self.agent = agent
        self.handler = handler


    async def run(self, user_prompt: str, message_history=None):
        if message_history is None:
            message_history = []

        async with self.agent.iter(
            user_prompt,
            message_history=message_history,
            output_type=RAGResponse
        ) as agent_run:
            async for node in agent_run:
                if Agent.is_user_prompt_node(node):
                    await self.process_user_node(node, agent_run)
                elif Agent.is_model_request_node(node):
                    await self.process_model_request_node(node, agent_run)
                elif Agent.is_call_tools_node(node):
                    await self.process_call_tools_node(node, agent_run)

            return agent_run.result

    async def process_user_node(self, node: UserPromptNode, agent_run: AgentRun):
        print(f"USER PROMPT ({self.agent.name}): {node.user_prompt}")

    async def process_model_request_node(self, node: ModelRequestNode, agent_run: AgentRun):
        args_so_far = ""

        parser = StreamingJSONParser(self.handler)

        async with node.stream(agent_run.ctx) as stream:
            async for response in stream.stream_responses():
                for part in response.parts:
                    if part.part_kind != 'tool-call':
                        continue
                    if part.tool_name != 'final_result':
                        continue

                    args_new = part.args
                    args_new_chunk = args_new[len(args_so_far):]
                    args_so_far = args_new

                    parser.parse_incremental(args_new_chunk)

    async def process_call_tools_node(self, node: CallToolsNode, agent_run: AgentRun):
        async with node.stream(agent_run.ctx) as events:
            async for event in events:
                if not isinstance(event, FunctionToolCallEvent):
                    continue

                tool_name = event.part.tool_name
                args = event.part.args
                print(f"TOOL CALL ({self.agent.name}): {tool_name}({args})")
```

## The run_agent_stream function becomes a thin wrapper that creates the runner with the production handler:
```python
async def run_agent_stream(
    agent: Agent,
    user_prompt: str,
    message_history=None
):
    runner = AgentStreamRunner(agent, RAGResponseHandler())
    return await runner.run(user_prompt, message_history)
```

## Updating the Tests : With the AgentStreamRunner class, we create a test-specific runner that uses JSONParserHandler - a no-op handler that doesn't print anything:
```python
async def run_agent_test(agent, user_prompt, message_history=None):
    runner = AgentStreamRunner(agent, JSONParserHandler())
    return await runner.run(user_prompt, message_history)
```
## The tests now receive the agent from the fixture and use run_agent_test: 
```python
@pytest.mark.asyncio
async def test_agent_runs(agent):
    user_prompt = 'llm as a judge'
    result = await run_agent_test(agent, user_prompt)

    search_result = result.output
    assert search_result.answer is not None
    assert search_result.confidence >= 0.0
    assert search_result.found_answer is True
    assert len(search_result.followup_questions) > 0
```
## The tool call test works the same way:
```python
@pytest.mark.asyncio
async def test_agent_uses_tools(agent):
    user_prompt = 'llm as a judge'
    result = await run_agent_test(agent, user_prompt)

    messages = result.new_messages()

    tool_calls = collect_tools(messages)
    assert len(tool_calls) >= 2

    search_call = tool_calls[0]
    assert search_call.name == 'search'

    get_file_call = tool_calls[1]
    assert get_file_call.name == 'get_file'
```
# Lesson 5 - More tests: code blocks and adding references

## Testing for Code Examples - write the test first, watch it fail, then fix the agent to make it pass.
```python
@pytest.mark.asyncio
async def test_agent_includes_code_in_answer(agent):
    user_prompt = 'llm as a judge'
    result = await run_agent_test(agent, user_prompt)

    answer = result.output
    assert '```python' in answer.answer
```

## run
```bash
uv run pytest tests/test_agent.py::test_agent_includes_code_in_answer -s
```
## This test fails. The agent returns a text explanation but doesn't include any code from the documentation. 

## Fixing the Instructions - prompt

```
Your user is a developer who is using Evidently and your task is to help them with it.
That's why when you see code examples in the documents you analyze,
always include code snippets in your answer.
```
```bash
uv run pytest tests/test_agent.py::test_agent_includes_code_in_answer -s
```
## Adding References

```python
class Reference(BaseModel):
    """
    A reference to a document that was used to generate the answer.
    """

    file_path: str = Field(description="The path to the document")
    explanation: str = Field(description="The explanation of how this document is relevant and was used in the answer")
```

## Then add the references field to RAGResponse:
```python
class RAGResponse(BaseModel):
    """
    This model provides a structured answer with metadata about the response,
    including confidence, categorization, and follow-up suggestions.
    """

    answer: str = Field(description="The main answer to the user's question in markdown")
    references: list[Reference] = Field(description="List of references to documents used to generate the answer")
    found_answer: bool = Field(description="True if relevant information was found in the documentation")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0 indicating how certain the answer is")
    confidence_explanation: str = Field(description="Explanation about the confidence level")
    answer_type: Literal["how-to", "explanation", "troubleshooting", "comparison", "reference"] = Field(description="The category of the answer")
    followup_questions: list[str] = Field(description="Suggested follow-up questions the user might want to ask")
```

## Test
```python
@pytest.mark.asyncio
async def test_agent_includes_references(agent):
    user_prompt = 'llm as a judge'
    result = await run_agent_test(agent, user_prompt)

    answer = result.output

    references = answer.references
    assert len(references) >= 1
    assert references[0].file_path is not None
    assert references[0].explanation is not None

    used_references = {r.file_path: r for r in references}
    assert "examples/LLM_judge.mdx" in used_references
```
## Run it
```bash
uv run pytest tests/test_agent.py::test_agent_includes_references -s
```
## Running All Tests
```bash
uv run pytest tests/test_agent.py -s
```
## Showing References in the UI - prompt

```
The agent now returns a `references` field in its structured output.
Each reference has `file_path` and `explanation`.

Update app.py to display references below the answer. For each reference,
show the file path as a clickable link to the GitHub source
(using the GITHUB_BASE URL that already exists in the code)
and the explanation next to it.

Add references to both the streaming response and the chat history replay.
Match the existing dark theme styling.
```

# Lesson 6 - Tracking cost

## Getting Usage
```python
async def run_agent_test(agent, user_prompt, message_history=None):
    runner = AgentStreamRunner(agent, JSONParserHandler())
    result = await runner.run(user_prompt, message_history)

    usage = result.usage()
    print(f"Usage: {usage}")

    return result
```
## Collecting Usage and Calculating Costs - prices are per million tokens 
```python
usages = []

def capture_usage(usage):
    usages.append(usage)

MODEL_PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

def calculate_cost(model_name, input_tokens, output_tokens):
    prices = MODEL_PRICES[model_name.lower()]
    input_cost = (input_tokens / 1_000_000) * prices["input"] 
    output_cost = (output_tokens / 1_000_000) * prices["output"]
    return input_cost + output_cost
```
##  calculate the total cost:
```python
def display_total_usage():
    print()

    total_cost = 0
    for usage in usages:
        cost = calculate_cost('gpt-4o-mini', usage.input_tokens, usage.output_tokens)
        total_cost += cost

    print(f"Total cost: ${total_cost:.6f}")
```
## pytest Hooks

How do we run display_total_usage at the end of all tests? pytest has a special file called conftest.py for configuring tests. It supports hooks - functions that run at specific points. For example, pytest_unconfigure runs at the end:

```python
def pytest_unconfigure(config):
    print("\n[HOOK] pytest is unconfiguring (end of run)")
```

## Putting It Together

Put the cost tracking code in tests/cost_tracker.py with a capture_usage function. Then in run_agent_test, call it after each run:

```python
async def run_agent_test(agent, user_prompt, message_history=None):
    runner = AgentStreamRunner(agent, JSONParserHandler())
    result = await runner.run(user_prompt, message_history)

    usage = result.usage()
    capture_usage(usage)
    return result
```

And in conftest.py, call display_total_usage when the session finishes:

```python
from tests.cost_tracker import display_total_usage

def pytest_sessionfinish(session, exitstatus):
    display_total_usage()
```

# Nest Chapter - Test Judges - Outcome: Use LLMs to evaluate agent quality

# Lesson 2 - Creating an LLM judge

## Starting with Criteria - create tests/test_judge.py and define the criteria first: These are plain English descriptions of what the agent should do. 

```python
criteria = [
    "performs search using the 'search' tool",
    "checks the content of the 'examples/LLM_judge.mdx' using 'get_file' tool",
    "makes at least 2 tool calls",
]
```

## Judge Output Models : create tests/judge.py with the models for the judge's structured output. 

```python
class JudgeCriterion(BaseModel):
    criterion_description: str
    passed: bool
    judgement: str

class JudgeFeedback(BaseModel):
    criteria: list[JudgeCriterion]
    feedback: str
```

## With Docstrings

```python
class JudgeCriterion(BaseModel):
    """
    Evaluation of a single test requirement or behavioral rule.
    """
    criterion_description: str = Field(
        description="The specific requirement or rule that the agent is being evaluated against."
    )
    passed: bool = Field(
        description="Indicates whether the agent's response and actions successfully satisfied this requirement."
    )
    judgement: str = Field(
        description="A clear explanation of why the agent passed or failed, referencing specific evidence from the agent's output or tool calls."
    )


class JudgeFeedback(BaseModel):
    """
    The complete evaluation report from the judge agent, summarizing performance across all criteria.
    """
    criteria: list[JudgeCriterion] = Field(
        description="A collection of individual evaluations for each performance requirement provided in the test."
    )
    feedback: str = Field(
        description="A holistic summary of the agent's performance, providing overall context and identifying key strengths or failures."
    )
```

## Judge Instructions and Prompt

```python
judge_instructions = """
You are an expert judge evaluating the performance of an
AI agent.
""".strip()

judge_user_prompt_template = """
Evaluate the agent's performance based on the following criteria:
<CRITERIA>
{criteria}
</CRITERIA>

The agent's final output was:
<AGENT_OUTPUT>
{output}
</AGENT_OUTPUT>

Tool calls:
<TOOL_CALLS>
{tool_calls}
</TOOL_CALLS>
""".strip()
```

## Create the judge agent using gpt-4o-mini:

```python
def create_judge_agent():
    agent = Agent(
        name="judge",
        model="openai:gpt-4o-mini",
        instructions=judge_instructions,
        output_type=JudgeFeedback,
    )
    return agent

```

## The assert_criteria Function

```python
async def assert_criteria(result, criteria):
    messages = result.new_messages()
    tool_calls = collect_tools(messages)
    output = result.output.model_dump_json()

    judge_agent = create_judge_agent()
    judge_user_prompt = judge_user_prompt_template.format(
        criteria='\n'.join(criteria),
        output=output,
        tool_calls='\n'.join([str(tc) for tc in tool_calls]),
    )

    judge_result = await judge_agent.run(judge_user_prompt)

    model = get_model_name(judge_agent)
    capture_usage(model, judge_result)

    print('judge feedback:')
    print(judge_result.output.feedback)

    for criterion in judge_result.output.criteria:
        print(f"{criterion.criterion_description}: {criterion.judgement}")
        assert criterion.passed, \
            f"{criterion.criterion_description}: {criterion.judgement}"
```

## Writing the Test - write the actual test at tests/test_judge.py

```python
@pytest.mark.asyncio
async def test_agent_uses_tools(agent):
    user_prompt = 'llm as a judge'
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "makes at least 2 tool calls",
        "performs search using the 'search' tool",
        "checks the content of the 'examples/LLM_judge.mdx' using 'get_file' tool",
    ])
```

## Run it:

```bash
uv run pytest tests/test_judge.py::test_agent_uses_tools -s
```

## Makefile

```makefile
tests:
	uv run pytest

run:
	uv run python main.py
```

# Lesson 3 - Using the agent and coming up with test cases

## Query "judge":

- the agent finds content about LLM judges, not legal/judicial content
- follow-up questions are about LLM evaluation, not the legal system

## Query "judge" (code formatting):

- code examples use 4-space indentation, one argument per line
- no spaces around = in keyword arguments (but spaces in variable assignments)

## Query "Sicilian defense" (off-topic):

- the agent returns low or zero confidence
- the agent doesn't hallucinate references that don't exist
- follow-up questions are still relevant to the documentation, not to chess

## Query "how do I implement LLM as a judge? I already have it in a pandas dataframe with columns question, generated_answer, expected_answer":

- the answer adapts to the user's specific situation and column names
- doesn't show a generic tutorial that ignores the user's context

## Any query with code examples:

- installation instructions use uv add instead of pip install

# Lesson 4 - Creating more judge tests with AI assistants

```python
# Query "judge"
@pytest.mark.asyncio
async def test_ambiguous_term_judge(agent):
    user_prompt = "judge"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the answer is about 'LLM as a judge' (using an LLM to evaluate outputs), not about legal judges or the judicial system",
        "follow-up questions are about LLM evaluation or related ML topics, not about the legal system or courts",
    ])

# code formatting
@pytest.mark.skip(reason="gpt-4o-mini copies code from docs verbatim, ignoring formatting instructions")
@pytest.mark.asyncio
async def test_code_formatting(agent):
    user_prompt = "how to use LLM as a judge"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "code examples use 4-space indentation",
        "function/constructor calls with multiple keyword arguments place each argument on its own line",
        "keyword arguments in function calls have no spaces around '=' (e.g. provider=\"openai\", not provider = \"openai\")",
        "normal variable assignments still use spaces around '=' (e.g. llm_eval = LLMEval(...))",
    ])

# off-topic
@pytest.mark.asyncio
async def test_off_topic_question(agent):
    user_prompt = "Sicilian defense"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "explicitly state that the question is off-topic and it only provides information about Evidently/ML evaluation",
        "return low or zero confidence (confidence <= 0.1) since the query is unrelated to the documentation",
        "use the 'search' tool",
        "don't use 'get_file' tool",
        "return no references in the answer",
        "follow-up questions are about ML/LLM evaluation not about chess",
    ])

# adaptation test checks - that the agent uses the context the user provides instead of showing a generic tutorial:
@pytest.mark.asyncio
async def test_adapts_to_user_context(agent):
    user_prompt = (
        "how do I implement LLM as a judge? I already have my input "
        "in a pandas dataframe with columns question, generated_answer, "
        "expected_answer"
    )
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the answer acknowledges the user's existing pandas dataframe and references their specific column names (question, generated_answer, expected_answer)",
        "the answer does not show a generic tutorial that starts from scratch with a toy dataset, ignoring the user's existing data structure",
    ])

# Package management - we want uv add instead of pip install
@pytest.mark.asyncio
async def test_uses_uv_add_not_pip(agent):
    user_prompt = "how do I install evidently?"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "any package installation instructions use 'uv add' instead of 'pip install'",
    ])
```

## Running Tests - pytest-xdist for parallel test execution

```bash
uv run pytest tests/test_judge.py -n 4 -s #  -n 4 flag runs tests in parallel using 4 workers
```

## Skipping Hard Tests - to revisit later

```python
@pytest.mark.skip(reason="gpt-4o-mini copies code from docs verbatim, ignoring formatting instructions")
```

## Makefile

```makefile
.PHONY: tests run tests-judge

tests:
	uv run pytest

tests-judge:
	uv run pytest tests/test_judge.py -n 4
```

# Lesson - Fixing the agent and the tests: self-checking and different models

## Prompt Improvements

```
CRITICAL: The documentation contains 'pip install' commands.
You MUST replace ALL 'pip install' with 'uv add' in your answers.
Do NOT mention 'pip' at all — always refer to 'uv' as the
package manager.
```

```javascript
Adapting to user context:
- Pay close attention to what the user already has (existing data,
  code, variables, setup).
- Tailor your answer to their specific situation. Reference their
  variable names, column names, and data structures.
- Do NOT show generic from-scratch tutorials when the user has
  described their existing setup.
- NEVER create sample/toy DataFrames or example data when the user
  already has their own data. Use their data directly in all
  code examples.
```

## Self-Verification Checklist



```python
# add a Check model:
class Check(BaseModel):
    rule: str = Field(description="The rule being verified")
    passed: bool = Field(description="Whether the response complies with this rule")
    explanation: str = Field(description="Evidence: what in the response passes or violates this rule")

# Then add a checks field to RAGResponse:

checks: list[Check] = Field(
    description="Self-verification checklist. For each applicable rule, verify your response complies. If any check fails, fix your response before submitting."
)

# And in the agent instructions, add a checklist the model must fill in:

Self-verification checklist:
Before submitting, verify each applicable rule and fill in
the 'checks' field. If any check fails, fix your response first.
Only include relevant checks.

1. "No verbatim code from docs" — rewrite all code, don't copy
   from documentation
2. "uv not pip" — use 'uv add', never 'pip install'
3. "User context used" — use the user's variable names, data,
   and setup instead of generic examples
4. "Code formatting" — kwargs have no spaces around '=',
   multi-arg calls use hanging indent
5. "On-topic follow-ups" — for on-topic answers, follow-ups
   match the specific topic

# This forces the model to verify each rule and explain whether it passed. If any check fails, the model should fix its response first. With smaller models like gpt-4o-mini, this kind of structured self-verification helps because it makes the model explicitly reason about compliance.
```

##  Text Output for Judge Evaluation

```python
# Sometimes the agent would actually follow the formatting rules, but the judge would still fail the test. The agent output was being sent to the judge as JSON (via model_dump_json()), which is harder for the judge LLM to parse correctly.

# add a to_string() method to RAGResponse that formats the output as plain text:

def to_string(self):
    parts = []

    parts.append(self.answer)
    parts.append("")
    parts.append(f"found_answer: {self.found_answer}")
    parts.append(f"confidence: {self.confidence}")
    parts.append(f"confidence_explanation: {self.confidence_explanation}")
    parts.append(f"answer_type: {self.answer_type}")

    for ref in self.references:
        parts.append(f"reference: {ref.file_path} — {ref.explanation}")

    for q in self.followup_questions:
        parts.append(f"follow_up_question: {q}")

    for check in self.checks:
        parts.append(f"self_check: [{'+' if check.passed else '-'}] {check.rule} — {check.explanation}")

    return "\n".join(parts)

def __str__(self):
    return self.to_string()

# Then in judge.py, I replaced result.output.model_dump_json() with str(result.output):
output = str(result.output)

# This sends plain text to the judge instead of JSON. It saves tokens and makes it easier for the judge to evaluate the response correctly.

```

## File-Based Cost Tracking

```python
# When running tests in parallel with pytest-xdist, each test runs in a separate process. The in-memory cost tracker from the previous lesson can't aggregate costs across processes because each one has its own memory. At the end it would report zero cost.

#The fix: write costs to a temporary JSONL file. Each process appends its usage data to a shared file:

def capture_usage(model, result):
    usage = result.usage()
    entry = {
        "model": model,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
    }
    with open(COST_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

# At the start of the test session, we clear any leftover data from previous runs. At the end, we read all entries and aggregate by model:

def display_total_usage():
    print()

    if not COST_FILE.exists():
        print("Total cost: $0.000000")
        return

    totals = {}
    for line in COST_FILE.read_text().splitlines():
        entry = json.loads(line)
        model = entry["model"]
        if model not in totals:
            totals[model] = {"input_tokens": 0, "output_tokens": 0}
        totals[model]["input_tokens"] += entry["input_tokens"]
        totals[model]["output_tokens"] += entry["output_tokens"]

    total_cost = 0
    for model, tokens in totals.items():
        cost = calculate_cost(model, tokens["input_tokens"], tokens["output_tokens"])
        print(f"{model}: ${cost:.6f}")
        total_cost += cost

    print(f"Total cost: ${total_cost:.6f}")

# The session hooks in conftest.py call these at the right time. We also import reset_cost_file alongside display_total_usage:

def pytest_sessionstart(session):
    reset_cost_file()

def pytest_sessionfinish(session, exitstatus):
    display_total_usage()
```