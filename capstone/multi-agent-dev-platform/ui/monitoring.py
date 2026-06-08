# ui/monitoring.py
import streamlit as st
import re
from pathlib import Path
from collections import Counter
import pandas as pd

LOG_FILE = Path(__file__).parent.parent / "logs" / "workflow.log"

st.title("Monitoring Dashboard")

if not LOG_FILE.exists():
    st.warning("No log file found. Run a workflow first.")
    st.stop()

raw_lines = LOG_FILE.read_text().splitlines()

# Parse log lines
records = []
pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+) \| (.+)")
for line in raw_lines:
    m = pattern.match(line)
    if m:
        records.append({"time": m.group(1), "level": m.group(2), "message": m.group(3)})

df = pd.DataFrame(records)
if df.empty:
    st.info("No structured log entries yet.")
    st.stop()

df["time"] = pd.to_datetime(df["time"])

# ── Metrics ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", len(df))
col2.metric("Errors", len(df[df["level"] == "ERROR"]))
col3.metric("Workflows Run", df["message"].str.contains("Workflow started|PM phase started").sum())
col4.metric("PRs Created", df["message"].str.contains("Phase 1 done").sum())

st.divider()

# ── Agent Performance ─────────────────────────────────────────────────────────
st.subheader("Agent Elapsed Times")
agent_df = df[df["message"].str.contains("elapsed=")]
if not agent_df.empty:
    agent_df = agent_df.copy()
    agent_df["agent"] = agent_df["message"].str.extract(r"(PM|Architect|Developer|QA|Review|AutoFix) Agent done")
    agent_df["elapsed"] = agent_df["message"].str.extract(r"elapsed=([\d.]+)s").astype(float)
    agent_df = agent_df.dropna(subset=["agent", "elapsed"])
    avg_elapsed = agent_df.groupby("agent")["elapsed"].mean().reset_index()
    st.bar_chart(avg_elapsed.set_index("agent"))

st.divider()

# ── Error Log ─────────────────────────────────────────────────────────────────
st.subheader("Errors")
errors = df[df["level"] == "ERROR"]
if errors.empty:
    st.success("No errors recorded")
else:
    st.dataframe(errors[["time", "message"]], width='stretch')

st.divider()

# ── Recent Events ─────────────────────────────────────────────────────────────
st.subheader("Recent Events")
st.dataframe(df.tail(50)[["time", "level", "message"]].iloc[::-1], width='stretch')

if st.button("Refresh"):
    st.rerun()
