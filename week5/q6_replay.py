from logfire.query_client import LogfireQueryClient

from trace_replay import (
    fetch_trace,
    trace_to_run_result,
)

MODEL_PRICES = {
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
}


def calculate_cost(
    model_name,
    input_tokens,
    output_tokens
):
    prices = MODEL_PRICES[model_name.lower()]

    input_cost = (
        input_tokens / 1_000_000
    ) * prices["input"]

    output_cost = (
        output_tokens / 1_000_000
    ) * prices["output"]

    return input_cost + output_cost


# Create query client
client = LogfireQueryClient(
    read_token="pylf_v1_us_pd1Qz3Wvyjt1y1zb3wqzFVDyYlRLnZJrkWpdv6D3Y3td"
)

# Your trace ID
trace_id = "019e47557826eb59c16d5e7e47e0bb63"
"""
# Query ALL agent runs in the trace
result = client.query_json_rows(
    sql=f
    SELECT
        attributes->>'gen_ai.usage.input_tokens' as input_tokens,
        attributes->>'gen_ai.usage.output_tokens' as output_tokens
    FROM records
    WHERE trace_id = '{trace_id}'
      AND span_name = 'agent run'
    
)

rows = result["rows"]

# Sum token usage
total_input_tokens = sum(
    int(row.get("input_tokens") or 0)
    for row in rows
)

total_output_tokens = sum(
    int(row.get("output_tokens") or 0)
    for row in rows
)

print("\n=== TOTAL SESSION TOKENS ===")
print("Input tokens:", total_input_tokens)
print("Output tokens:", total_output_tokens)

cost = calculate_cost(
    "gpt-4o-mini",
    total_input_tokens,
    total_output_tokens,
)

print("\n=== TOTAL SESSION COST ===")
print(f"${cost:.6f}")
"""

# Fetch trace
trace = fetch_trace(trace_id, client)

print(f"\n=== TRACE INFO === {trace} ") 

# Convert back into AgentRunResult
run_result = trace_to_run_result(trace)

print("\n=== RECONSTRUCTED OUTPUT ===")
print(run_result.output)

print("\n=== TOKEN USAGE ===")
print("Input tokens:", trace.input_tokens)
print("Output tokens:", trace.output_tokens)

# Calculate cost
cost = calculate_cost(
    "gpt-4o-mini",
    trace.input_tokens,
    trace.output_tokens,
)

print("\n=== APPROXIMATE COST ===")
print(f"${cost:.6f}")