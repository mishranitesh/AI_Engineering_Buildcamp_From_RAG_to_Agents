from logfire.query_client import LogfireQueryClient

# Replace with your read token
client = LogfireQueryClient(
    read_token="pylf_v1_us_pd1Qz3Wvyjt1y1zb3wqzFVDyYlRLnZJrkWpdv6D3Y3td"
)

# Query recent traces
rows = client.query_json("""
SELECT
    trace_id,
    span_name,
    start_timestamp
FROM records
WHERE span_name = 'trivia_session'
ORDER BY start_timestamp DESC
LIMIT 10
""")

print(rows)