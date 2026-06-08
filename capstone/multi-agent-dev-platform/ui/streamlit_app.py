# ui/streamlit_app.py

import streamlit as st
import requests

API = "http://localhost:8000"

st.title("Multi-Agent Software Builder")

col1, col2 = st.columns([1, 2])
with col1:
    project_name_input = st.text_input("Project Name", placeholder="e.g. todo-api")
with col2:
    req = st.text_area("Enter Requirement")

# At the top of streamlit_app.py, right after imports:

RESUME_LABELS = {
    ("pm_complete", "none"):             "PM done, Jira created — waiting for code generation",
    ("completed",   "draft"):            "Code generated — Draft PR open",
    ("completed",   "ready_for_review"): "PR marked ready for review",
    ("completed",   "fixing"):           "AutoFix applied — ready to merge or fix more",
}

with st.sidebar:
    st.header("Options")
    jira_enabled = st.checkbox("Create JIRA Epic & Stories")
    github_enabled = st.checkbox("Create Draft PR on GitHub")

    st.divider()
    st.subheader("Resume Session")
    sessions_resp = requests.get(f"{API}/sessions")
    sessions = sessions_resp.json() if sessions_resp.status_code == 200 else []

    if sessions:
        names = [s["project_name"] for s in sessions]
        selected = st.selectbox("Interrupted sessions", names)
        session = next(s for s in sessions if s["project_name"] == selected)
        label = RESUME_LABELS.get(
            (session["final_status"], session["pr_phase"]), "Interrupted"
        )
        st.caption(f"Stage: {label}")
        if session.get("jira_epic_key"):
            st.caption(f"Jira: {session['jira_epic_key']}")
        if session.get("pr_url"):
            st.caption(f"PR: {session['pr_url']}")

        if st.button("▶️ Resume this session"):
            full = requests.get(f"{API}/session/{selected}").json()
            if full["final_status"] == "pm_complete":
                st.session_state["pm_result"] = full
            else:
                st.session_state["pm_result"] = full
                st.session_state["result"] = full
            st.rerun()
    else:
        st.caption("No interrupted sessions")

# Stage 1
if st.button("Run PM Agent"):
    if not project_name_input.strip():
        st.error("Please enter a project name")
        st.stop()
    with st.spinner("Running PM Agent..."):
        r = requests.post(f"{API}/run-pm", json={
            "requirement": req,
            "project_name": project_name_input.strip(),
            "jira_enabled": jira_enabled
        })
        if r.status_code == 200:
            st.session_state["pm_result"] = r.json()
            st.session_state.pop("result", None) # clear any previous codegen result
        else:
            st.error(r.text)

pm_result = st.session_state.get("pm_result")

if pm_result:
    if pm_result.get("jira_epic_url"):
        st.subheader("📋 JIRA Issues Created")
        st.markdown(f"**Epic:** [{pm_result['jira_epic_key']}]({pm_result['jira_epic_url']})")
        for key, url in zip(pm_result["jira_story_keys"], pm_result["jira_story_urls"]):
            st.markdown(f"- [{key}]({url})")
        st.info("Review and edit stories in JIRA if needed, then click Generate Code.")
    else:
        st.subheader("📋 PM Agent Output")
        st.markdown(pm_result["user_stories"][0] if pm_result.get("user_stories") else "")
        st.info("Review the stories above, then click Generate Code.")

    # Stage 2 gate
    st.divider()
    if st.button("✅ Stories confirmed — Generate Code"):
        with st.spinner("Generating code..."):
            r = requests.post(f"{API}/run-codegen", json={
                "project_name": pm_result["project_name"],
                "github_enabled": github_enabled,
            })
            if r.status_code == 200:
                st.session_state["result"] = r.json()
            else:
                st.error(f"Code generation failed: {r.text}")

# ── Results ───────────────────────────────────────────────────────────────────
result = st.session_state.get("result")

if result:
    st.success("Project Generated!")
    st.subheader(f"📦 {result['project_name']}")
    st.write(f"Path: {result['generated_path']}")

    with open(result["zip_file"], "rb") as f:
        st.download_button("Download ZIP", f, "generated-project.zip", "application/zip")

    # ── User Feedback ──────────────────────────────────────────────────────────
    st.divider()
    if "feedback_given" not in st.session_state:
        st.markdown("**How was the generated output?**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Good output"):
                requests.post(f"{API}/feedback", json={
                    "project_name": result["project_name"], "rating": "positive"
                })
                st.session_state["feedback_given"] = "positive"
                st.rerun()
        with col2:
            if st.button("👎 Needs improvement"):
                requests.post(f"{API}/feedback", json={
                    "project_name": result["project_name"], "rating": "negative"
                })
                st.session_state["feedback_given"] = "negative"
                st.rerun()
    else:
        msg = "Thanks for the feedback!" if st.session_state["feedback_given"] == "positive" else "Thanks — noted for improvement."
        st.info(msg)

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
            st.info("AutoFix applied. Review the PR commits, then fix more or merge.")

            review_comments = result.get("review_comments", [])
            accepted = []
            if review_comments:
                st.markdown("**Select additional comments to fix (optional):**")
                for i, comment in enumerate(review_comments):
                    if st.checkbox(comment[:120], key=f"refix_comment_{i}"):
                        accepted.append(comment)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Fix More →"):
                    transition("fix", accepted)
            with col2:
                if st.button("Merge PR →"):
                    transition("merge")

        elif phase == "merged":
            st.success("PR merged to main!")
