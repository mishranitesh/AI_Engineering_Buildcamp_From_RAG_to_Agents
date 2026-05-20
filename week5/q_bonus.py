from logfire.query_client import LogfireQueryClient

# Replace with your read token
client = LogfireQueryClient(
    read_token="pylf_v1_us_pd1Qz3Wvyjt1y1zb3wqzFVDyYlRLnZJrkWpdv6D3Y3td"
)

# Query recent traces
rows = client.query_json("""
SELECT
    attributes->>'score' AS score,
    COUNT(*) AS count
FROM records
WHERE span_name = 'user_feedback'
GROUP BY score
ORDER BY score DESC
""")

print(rows)