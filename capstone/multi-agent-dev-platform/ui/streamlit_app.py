# ui/streamlit_app.py

import streamlit as st
import requests

API = "http://localhost:8000"

st.title("Multi-Agent Software Builder")

req = st.text_area("Enter Requirement")

with st.sidebar:
    st.header("GitHub Integration (Phase 2)")
    github_enabled = st.checkbox("Create Draft PR on GitHub")

# ── Run Workflow ──────────────────────────────────────────────────────────────
if st.button("Run Agents"):
    with st.spinner("Generating project..."):
        try:
            response = requests.post(
                f"{API}/run-workflow",
                json={"requirement": req, "github_enabled": github_enabled},
            )
            if response.status_code != 200:
                st.error(f"API Error {response.status_code}")
                st.write(response.text)
            else:
                result = response.json()
                if result.get("status") == "completed":
                    st.session_state["result"] = result   # persist across reruns
                else:
                    st.error("Project generation failed")
                    st.write(result)
        except Exception as e:
            st.error(f"Error: {e}")

# ── Results ───────────────────────────────────────────────────────────────────
result = st.session_state.get("result")

if result:
    st.success("Project Generated!")
    st.subheader(f"📦 {result['project_name']}")
    st.write(f"Path: {result['generated_path']}")

    with open(result["zip_file"], "rb") as f:
        st.download_button("Download ZIP", f, "generated-project.zip", "application/zip")

    # ── PR Lifecycle Panel ────────────────────────────────────────────────────
    if result.get("pr_url"):
        st.divider()
        st.subheader("🐙 PR Lifecycle")

        phase = result.get("pr_phase", "draft")

        # Phase indicator
        phases = ["draft", "ready_for_review", "fixing", "merged"]
        labels = ["1 · Draft", "2 · Ready for Review", "3 · Fix PR", "4 · Merged"]
        cols = st.columns(4)
        for i, (col, label) in enumerate(zip(cols, labels)):
            active = phases[i] == phase
            col.markdown(
                f"**:blue[{label}]**" if active else f"<span style='color:grey'>{label}</span>",
                unsafe_allow_html=True,
            )

        st.markdown(f"**Branch:** `{result['github_branch']}`")
        st.markdown(f"**PR:** [{result['pr_url']}]({result['pr_url']})")
        st.markdown(f"**Current phase:** `{phase}`")

        def transition(phase_name: str, accepted_comments: list[str] | None = None):
            payload = {
                "project_name": result["project_name"],
                "phase": phase_name,
                "accepted_comments": accepted_comments or [],
            }
            with st.spinner(f"Transitioning to {phase_name}..."):
                r = requests.post(f"{API}/pr-transition", json=payload)
            if r.status_code == 200:
                st.session_state["result"]["pr_phase"] = r.json()["pr_phase"]
                st.rerun()
            else:
                st.error(f"Transition failed: {r.text}")

        # ── Phase-specific actions ────────────────────────────────────────────
        if phase == "draft":
            st.info("Draft PR is open. Review the code, then mark it ready.")
            if st.button("Mark Ready for Review →"):
                transition("ready_for_review")

        elif phase == "ready_for_review":
            st.info("PR is open for review. Select comments to fix, or merge directly.")
            review_comments = result.get("review_comments", [])
            accepted = []
            if review_comments:
                st.markdown("**Review comments — check those to include in fix:**")
                for i, comment in enumerate(review_comments):
                    if st.checkbox(comment[:120], key=f"comment_{i}"):
                        accepted.append(comment)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Fix PR →"):
                    transition("fix", accepted)
            with col2:
                if st.button("Merge PR →"):
                    transition("merge")

        elif phase == "fixing":
            st.info("AutoFix applied. Review the new commits, then merge.")
            if st.button("Merge PR →"):
                transition("merge")

        elif phase == "merged":
            st.success("PR merged to main!")
