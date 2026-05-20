# Monitoring with Pydantic Logfire

# Lesson 2 - Logfire integration with PydanticAI

- Pydantic Logfire is an observability platform developed by the Pydantic team. 
- Under the hood, Logfire uses OTel (OpenTelemetry). OpenTelemetry is an open source observability framework that provides a standardized way to collect, process, and export telemetry data (metrics, logs, and traces) from applications.
- It's become the industry standard for observability, allowing you to instrument your code once and send data to any compatible backend. 

## Setting Up Logfire

- Create an account at https://logfire.pydantic.dev/ 
- Create a new project in your Logfire dashboard
- Generate a write token for your project
- Add the token to your .env file: `LOGFIRE_TOKEN="your-logfire-write-token"`
- Install Logfire: `uv add logfire`

## Integrating Logfire with PydanticAI

```python
import logfire
from dotenv import load_dotenv

load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai() # The instrument_pydantic_ai() call injects observability into all PydanticAI operations. Every time we send a request to any provider, Logfire sees it and sends the telemetry data to the backend via OpenTelemetry.
```

## Logfire Dashboard

After running the agent, open the Logfire dashboard and you'll see:

- Complete traces of agent interactions - which tools were called, in what order
- Token usage and costs for each request (e.g. 1/10th of a cent for a simple query)
- The actual content of each request and response

You can also set up usage overview dashboards, add pricing information, and configure alerts (for example, if you're getting too many errors or too many requests).

# Lesson 3 - Joining multiple runs under one span tree

After setting up Logfire, we notice a problem: when we interact with the agent multiple times within one session - a first question followed by a follow-up - they show up as two separate traces in the Logfire dashboard. We want to keep results from one conversation in one trace, so it's easier to see they belong to the same session and to see the total cost.

We need three Logfire functions to fix this:

- logfire.span('name') - creates a parent span (the root of the tree)
- logfire.get_context() - captures the current span context so we can reuse it later
- logfire.attach_context(context) - attaches a saved context, making all operations within it children of that span


## Creating the Logfire Context

```python
if "logfire_context" not in st.session_state:
    with logfire.span('streamlit_session'): # creates a span called "streamlit_session" 
        st.session_state.logfire_context = logfire.get_context() # captures the span context
```

## Attaching the Context to Agent Runs

```python
with logfire.attach_context(st.session_state.logfire_context):
    answer, metadata, followup_questions, references, new_messages, act_list = asyncio.run(
        run_streaming(
            prompt,
            st.session_state.agent_messages,
            [answer_placeholder, act_placeholder, ref_placeholder],
        )
    )
```

## Resetting the Context

```python
if st.button("Clear conversation"):
    st.session_state.messages = []
    st.session_state.agent_messages = []
    with logfire.span('streamlit_session'):
        st.session_state.logfire_context = logfire.get_context()
    st.rerun()
```

# Lesson 4 - Tracking user feedback

Now that we have Logfire integrated and all agent runs grouped under one session span, we can track custom events. 

We want to track two events:

- followup_question_clicked - when a user clicks a suggested follow-up question, with the actual question text
- user_feedback - when a user clicks thumbs up (+1) or thumbs down (-1)

## Adding Events with an AI Assistant

### Prompt
```
In app.py I want to track these events:

- user clicks on the follow up question button. event: followup_question_clicked {'question': 'actual followup question'}
- add +1/-1 feedback buttons. event: user_feedback {'feedback': 1 or -1}
```

## Tracking Follow-up Clicks

```python
if col.button(q, key=f"followup_{q[:40]}"):
    with logfire.attach_context(st.session_state.logfire_context):
        logfire.info("followup_question_clicked", question=q) # sends an event with the name followup_question_clicked
    st.session_state.pending_followup = q
    st.rerun()
```

## Tracking Feedback
For feedback, we add thumbs up and thumbs down buttons next to the metadata badges:

```python
f1, f2 = st.columns(2)
if f1.button("👍", key=f"upvote_{idx}"):
    with logfire.attach_context(st.session_state.logfire_context): # feedback event appears under the same session span as the agent run that produced the answer.
        logfire.info("user_feedback", feedback=1)
    st.toast("Thanks for the feedback!", icon="👍")
if f2.button("👎", key=f"downvote_{idx}"):
    with logfire.attach_context(st.session_state.logfire_context): # feedback event appears under the same session span as the agent run that produced the answer.
        logfire.info("user_feedback", feedback=-1)
    st.toast("Thanks for the feedback!", icon="👎")
```

same pattern: logfire.info("event_name", key=value) wrapped in logfire.attach_context(). The events show up in the Logfire dashboard alongside the agent traces, so you can see the full picture of each session.

# Lesson 5 - Downloading traces data from logfire

Now we want to download this data so we can use it for evaluation. We want to know which interactions were good and which were bad, so we can use that data to improve the system. The goal is to reconstruct the original PydanticAI agent runs from the trace data stored in Logfire.

## Setting Up the Query Client

- You need a read token to query data from Logfire. 
- Go to your project settings, find "Read tokens", and create one. Add it to your .env: `LOGFIRE_READ_TOKEN="your-logfire-read-token"`

- Create the client:
```python
import dotenv
dotenv.load_dotenv()

import os
from logfire.query_client import LogfireQueryClient

read_token = os.getenv('LOGFIRE_READ_TOKEN')
logfire_query_client = LogfireQueryClient(read_token=read_token)
```

You can query Logfire using SQL. 

## Querying Trace Data

### Fetch recent traces

```python
trace_rows = logfire_query_client.query_json_rows(
    sql="""
    SELECT
        trace_id,
        start_timestamp,
        duration
    FROM records
    WHERE span_name = 'agent run'
    ORDER BY start_timestamp DESC
    LIMIT 2
    """
)
```

### Extract the trace IDs:
```python
trace_ids = [r['trace_id'] for r in trace_rows['rows']]
trace_ids

# Output
#['019c53cc187190acc3d5ca23805f9fdc', '019c53cbef71d25518ad64c30659e6cd']
```

### For a specific trace, we can fetch the agent run data. 

```python
trace_id = trace_ids[0]

run_row = logfire_query_client.query_json_rows(
    sql=f"""
    SELECT
        attributes->'pydantic_ai.all_messages' as all_messages,
        attributes->>'gen_ai.usage.input_tokens' as input_tokens,
        attributes->>'gen_ai.usage.output_tokens' as output_tokens
    FROM records
    WHERE trace_id = '{trace_id}'
      AND span_name = 'agent run'
    ORDER BY start_timestamp DESC
    LIMIT 1
    """
)

# We order by start_timestamp DESC and limit to 1 because when there are multiple agent runs in a session (e.g. a follow-up question), the last one contains all the messages from both runs

all_messages = run_row['rows'][0]
all_messages['all_messages'][0]

# Output - The messages are in OpenTelemetry format, which is different from PydanticAI's format. For example, the OTel format uses type and parts while PydanticAI uses part_kind and different field names.
"""
{'role': 'user',
 'parts': [{'type': 'text',
   'content': 'What metrics does Evidently support?'}]}
"""
```

## Converting Back to PydanticAI Format

-  There's a built-in converter from PydanticAI to OTel, but no way back - so we recreated it.

- Full implementation by alexy from OTel to PydanticAI - https://github.com/alexeygrigorev/ai-engineering-buildcamp-code/blob/ff4aff7/documentation-agent/trace_replay/converter.py

```python
import trace_replay

trace = trace_replay.fetch_trace(trace_id, logfire_query_client) # fetch trace

run = trace_replay.trace_to_run_result(trace) # Convert to a full AgentRunResult:

run.output # access

# Output
"""
{'found_answer': True,
 'title': 'Metrics Supported by Evidently',
 'sections': [{'heading': 'Regression Metrics',
   'content': 'Evidently calculates several standard regression quality metrics to evaluate model performance. These include Mean Error (ME), Mean Absolute Error (MAE), and Mean Absolute Percentage Error (MAPE). Additionally, it generates interactive visualizations to help analyze model performance and identify areas for improvement.',
   'references': [{'title': 'Regression metrics',
     'filename': 'metrics/explainer_regression.mdx'}]},
  {'heading': 'Classification Metrics',
   'content': 'For classification tasks, Evidently supports metrics such as Accuracy, Precision, Recall, F1-score, ROC AUC, and LogLoss. These metrics are essential for assessing the performance of classification models, and Evidently also provides visual tools to understand how the model performs across different classes.',
   'references': [{'title': 'Classification metrics',
     'filename': 'metrics/explainer_classification.mdx'}]},
  {'heading': 'Ranking and Recommendation Metrics',
   'content': 'Evidently also supports various metrics tailored for ranking and recommendation systems, including Recall at K, Precision at K, F Beta at K, Mean Average Precision (MAP), Normalized Discounted Cumulative Gain (NDCG), and Hit Rate. These metrics help evaluate the effectiveness of the recommender systems in retrieving relevant items and their placement in recommended lists.',
   'references': [{'title': 'Ranking and RecSys metrics',
     'filename': 'metrics/explainer_recsys.mdx'}]}],
 'references': [{'title': 'Regression metrics',
   'filename': 'metrics/explainer_regression.mdx'},
  {'title': 'Classification metrics',
   'filename': 'metrics/explainer_classification.mdx'},
  {'title': 'Ranking and RecSys metrics',
   'filename': 'metrics/explainer_recsys.mdx'}]}
"""
```

## Fetching Multiple Traces and Saving

To build an evaluation dataset, fetch all traces and convert them:

```python
traces = trace_replay.fetch_traces(trace_ids, logfire_query_client)

runs = []

for trace in traces.values():
    run = trace_replay.trace_to_run_result(trace)
    runs.append(run)

# save using pickle or any serialization format works
import pickle

with open('data/logs.bin', 'wb') as f_out:
    pickle.dump(runs, f_out)

# To load them back
with open('data/logs.bin', 'rb') as f_in:
    runs = pickle.load(f_in)
```

 