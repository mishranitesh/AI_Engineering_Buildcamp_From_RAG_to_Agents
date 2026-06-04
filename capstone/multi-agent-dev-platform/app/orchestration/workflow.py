from app.orchestration.state import WorkflowState
from app.agents.pm_agent.agent import PMAgent
from app.agents.architect_agent.agent import ArchitectAgent
from app.agents.developer_agent.agent import DeveloperAgent
from app.agents.qa_agent.agent import QAAgent
from app.agents.review_agent.agent import ReviewAgent
from app.generators.project_generator import create_project_directory
from app.generators.readme_generator import generate_readme
from app.generators.artifact_writer import (
    write_backend_files,
    write_tests,
    write_architecture,
    write_review,
    write_readme
)
from app.generators.zip_generator import create_zip
from app.monitoring.logger import logger
import time

from app.tools.github_tool import GitHubTool
from app.agents.autofix_agent.agent import AutoFixAgent
import re
import datetime


class WorkflowOrchestrator:
    def __init__(self):
        self.pm = PMAgent()
        self.architect = ArchitectAgent()
        self.dev = DeveloperAgent()
        self.qa = QAAgent()
        self.review = ReviewAgent()

    def _dict_to_str(self, d: dict) -> str:
        return "\n\n".join(
            f"### {fname}\n```python\n{content}\n```"
            for fname, content in d.items()
        )
    
    def _extract_files_from_autofix(self, raw: str) -> dict[str, str]:
        """Parse ### filename.py code blocks from auto-fix agent output."""
        pattern = r"###\s+(\S+\.py)\s+```python\s+(.*?)```"
        matches = re.findall(pattern, raw, re.DOTALL)
        if not matches:
            return {}
        return {fname: code.strip() for fname, code in matches}
    
    def phase_draft_pr(self, state: WorkflowState) -> WorkflowState:
        """Phase 1: Create branch, commit code, open as Draft PR."""
        gh = GitHubTool()
        branch_name = f"ai-gen/{state.project_name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        gh.create_branch(branch_name)
        state.github_branch = branch_name

        all_files = {f"backend/{k}": v for k, v in state.backend_code.items()}
        all_files.update({f"tests/{k}": v for k, v in state.tests.items()})
        gh.commit_files(branch_name, all_files, f"feat: AI-generated code for {state.project_name}", state.project_name)

        pr_body = (
            f"## AI-Generated Project\n\n**Requirement:**\n{state.requirement[:500]}\n\n"
            f"> _Draft — pending developer review before opening for team_"
        )
        pr_number, pr_url = gh.create_draft_pull_request(branch_name, f"AI: {state.project_name}", pr_body)
        state.pr_number = pr_number
        state.pr_url = pr_url
        state.pr_phase = "draft"

        logger.info(f"Phase 1 done | draft PR={pr_url}")
        return state

    def phase_ready_for_review(self, state: WorkflowState) -> WorkflowState:
        """Phase 2: Mark PR ready, post Review Agent comments."""
        gh = GitHubTool()

        gh.mark_pr_ready_for_review(state.pr_number)

        if state.review_comments:
            all_comments = "\n\n".join(
                f"{i+1}. {c}" for i, c in enumerate(state.review_comments)
            )
            gh.add_pr_comment(state.pr_number, f"## Review Agent Report\n\n{all_comments}")

        state.pr_phase = "ready_for_review"
        logger.info(f"Phase 2 done | PR marked ready | pr={state.pr_number}")
        return state

    def phase_fix_pr(self, state: WorkflowState) -> WorkflowState:
        """Phase 3: AutoFix based on accepted review comments, commit fixes."""
        gh = GitHubTool()
        autofix = AutoFixAgent()

        # Use accepted comments if set, otherwise fall back to review agent output
        review_str = (
            "\n".join(state.pr_accepted_comments)
            if state.pr_accepted_comments
            else (state.review_comments[0] if state.review_comments else "")
        )

        code_str = self._dict_to_str(state.backend_code)
        fixed_raw = autofix.process(code_str, review_str)
        state.fixed_code = self._extract_files_from_autofix(fixed_raw)

        if state.fixed_code:
            fixed_with_path = {f"backend/{f}": c for f, c in state.fixed_code.items()}
            gh.commit_files(state.github_branch, fixed_with_path, "fix: AutoFix Agent corrections", state.project_name)
            gh.add_pr_comment(state.pr_number, "Auto-Fix Agent applied corrections. Please re-review.")

        state.pr_phase = "fixing"
        logger.info(f"Phase 3 done | fixed files={list(state.fixed_code.keys())}")
        return state

    def phase_merge_pr(self, state: WorkflowState) -> WorkflowState:
        """Phase 4: Merge PR to main."""
        gh = GitHubTool()
        merged = gh.merge_pull_request(state.pr_number)
        if merged:
            state.pr_phase = "merged"
            logger.info(f"Phase 4 done | PR merged | pr={state.pr_number}")
        return state

    def _extract_user_stories(self, pm_output: str) -> list[str]:
        stories = []
        in_section = False
        for line in pm_output.split("\n"):
            low = line.lower().strip()

            # Detect section start
            if "user stor" in low and ("##" in line or "**" in line or low.startswith("user stor")):
                in_section = True
                continue

            # Stop at next section
            if in_section and any(k in low for k in ("acceptance criteria", "tech stack", "## ")):
                in_section = False

            if not in_section or not line.strip():
                continue

            # Only take top-level items — skip indented sub-points
            if line.startswith("  ") or line.startswith("\t"):
                continue

            story = re.sub(r"^[\s\-\*\d\.]+", "", line).strip()

            # Only keep lines that look like actual stories
            if len(story) > 15 and story.lower().startswith(("as a", "user can", "the system", "allow")):
                stories.append(story)

        return stories[:8] or ["Implement core functionality"]   # hard cap at 8

    def _extract_tasks_from_architecture(self, arch_output: str) -> list[str]:
        """Extract component/module names from architecture output as tasks."""
        tasks = []
        for line in arch_output.split("\n"):
            line = line.strip()
            if line.startswith(("-", "*", "•")) and len(line) > 5:
                task = re.sub(r"^[\s\-\*•]+", "", line).strip()
                if task:
                    tasks.append(task)
        return tasks[:8]  # cap at 8 tasks

    def phase_jira(self, state: WorkflowState) -> WorkflowState:
        """Phase 3: Create Epic → Stories → Tasks in JIRA."""
        from app.tools.jira_tool import JiraTool
        jira = JiraTool()

        # Epic from requirement
        epic_key, epic_url = jira.create_epic(
            title=f"[AI] {state.project_name}",
            description=state.requirement[:500],
        )
        state.jira_epic_key = epic_key
        state.jira_epic_url = epic_url
        logger.info(f"JIRA Epic created | key={epic_key} | url={epic_url}")

        # Stories from PM Agent output
        stories = self._extract_user_stories(state.user_stories[0] if state.user_stories else "")
        tasks_source = self._extract_tasks_from_architecture(state.architecture)

        for story_text in stories:
            story_key, story_url = jira.create_story(story_text, epic_key)
            state.jira_story_keys.append(story_key)
            state.jira_story_urls.append(story_url)
            logger.info(f"JIRA Story created | key={story_key}")

            # Create tasks under first story only (architecture components)
            if story_key == state.jira_story_keys[0]:
                for task_text in tasks_source:
                    task_key, _ = jira.create_task(task_text, story_key)
                    state.jira_task_keys.append(task_key)
                    logger.info(f"JIRA Task created | key={task_key}")

        state.jira_enabled = True
        return state

    def run_pm_phase(self, requirement: str, jira_enabled: bool = False) -> WorkflowState:
        """Stage 1: PM Agent + optional JIRA setup. Returns state, waits for confirmation."""
        state = WorkflowState(requirement=requirement)
        logger.info(f"PM phase started | requirement='{requirement[:80]}...'")

        t = time.time()
        pm_output = self.pm.process(requirement)
        logger.info(f"PM Agent done | elapsed={time.time()-t:.1f}s")
        state.user_stories = [pm_output]

        if jira_enabled:
            try:
                self._create_jira_epic_and_stories(state)
            except Exception as e:
                logger.error(f"JIRA phase failed: {e}")

        state.final_status = "pm_complete"
        return state
    
    def run_codegen_phase(self, state: WorkflowState, github_enabled: bool = False) -> WorkflowState:
        """Stage 2: Fetch confirmed JIRA stories → generate code → GitHub."""

        # If JIRA enabled, fetch potentially edited stories back from JIRA
        if state.jira_enabled and state.jira_epic_key:
            try:
                from app.tools.jira_tool import JiraTool
                confirmed = JiraTool().get_stories(state.jira_epic_key)
                if confirmed:
                    state.user_stories = confirmed   # replace PM output with JIRA-confirmed stories
                    logger.info(f"Fetched {len(confirmed)} confirmed stories from JIRA")
            except Exception as e:
                logger.error(f"Could not fetch JIRA stories, using PM output: {e}")

        pm_context = "\n".join(state.user_stories)

        t = time.time()
        arch_output, mermaid_output = self.architect.process(pm_context)
        logger.info(f"Architect Agent done | elapsed={time.time()-t:.1f}s")
        state.architecture = arch_output
        state.mermaid = mermaid_output

        t = time.time()
        dev_output = self.dev.process(pm_context + "\n" + arch_output)
        logger.info(f"Developer Agent done | files={list(dev_output.keys())} | elapsed={time.time()-t:.1f}s")
        state.backend_code = dev_output

        t = time.time()
        test_output = self.qa.process(dev_output)
        logger.info(f"QA Agent done | elapsed={time.time()-t:.1f}s")
        state.tests = test_output

        t = time.time()
        review_output = self.review.process(self._dict_to_str(dev_output) + "\n" + self._dict_to_str(test_output))
        logger.info(f"Review Agent done | elapsed={time.time()-t:.1f}s")
        state.review_comments = self._parse_review_comments(review_output)

        project_dir = create_project_directory(state.project_name)
        write_backend_files(project_dir, state.backend_code)
        write_tests(project_dir, state.tests)
        write_architecture(project_dir, state.architecture, state.mermaid)
        write_review(project_dir, state.review_comments)
        readme = generate_readme(state)
        write_readme(project_dir, readme)
        zip_file = create_zip(project_dir)

        state.generated_path = str(project_dir)
        state.zip_file = zip_file
        state.final_status = "completed"

        if github_enabled:
            state.github_enabled = True
            try:
                self.phase_draft_pr(state)
            except Exception as e:
                logger.error(f"GitHub draft PR phase failed: {e}")

        return state
    
    def _create_jira_epic_and_stories(self, state: WorkflowState) -> None:
        from app.tools.jira_tool import JiraTool
        jira = JiraTool()

        epic_key, epic_url = jira.create_epic(
            title=f"[AI] {state.project_name}",
            description=state.requirement[:500],
        )
        state.jira_epic_key = epic_key
        state.jira_epic_url = epic_url
        state.jira_enabled = True
        logger.info(f"JIRA Epic created | key={epic_key}")

        stories = self._extract_user_stories(state.user_stories[0])
        for story_text in stories:
            story_key, story_url = jira.create_story(story_text, epic_key)
            state.jira_story_keys.append(story_key)
            state.jira_story_urls.append(story_url)
            logger.info(f"JIRA Story created | key={story_key}")

    def _parse_review_comments(self, review_output: str) -> list[str]:
        """Split review output into individual numbered items."""
        import re
        lines = review_output.split("\n")
        items = []
        current = []
        for line in lines:
            if re.match(r'^\d+\.\s', line.strip()):   # starts with "1. ", "2. " etc.
                if current:
                    items.append("\n".join(current).strip())
                current = [line.strip()]
            elif current:
                current.append(line.strip())
        if current:
            items.append("\n".join(current).strip())
        return [i for i in items if len(i) > 10] or [review_output]
    
    """
    def run(self, requirement: str, github_enabled: bool = False, auto_merge: bool = False, jira_enabled: bool = False) -> WorkflowState:
        state = WorkflowState(requirement=requirement)
        logger.info(f"Workflow started | requirement='{requirement[:80]}...'")

        # PM Agent
        t = time.time()
        pm_output = self.pm.process(requirement)
        logger.info(f"PM Agent done | elapsed={time.time()-t:.1f}s")
        state.user_stories = [pm_output]

        # Architect Agent
        t = time.time()
        arch_output, mermaid_output = self.architect.process(pm_output)
        logger.info(f"Architect Agent done | elapsed={time.time()-t:.1f}s")
        state.architecture = arch_output
        state.mermaid = mermaid_output

        # Developer Agent
        t = time.time()
        dev_output = self.dev.process(pm_output + "\n" + arch_output)
        logger.info(f"Developer Agent done | files={list(dev_output.keys())} | elapsed={time.time()-t:.1f}s")
        state.backend_code = dev_output # Now it's already a dict from parser

        # QA Agent
        t = time.time()
        test_output = self.qa.process(dev_output)
        logger.info(f"QA Agent done | files={list(test_output.keys())} | elapsed={time.time()-t:.1f}s")
        state.tests = test_output # Now it's already a dict from parser

        # Review Agent
        t = time.time()
        review_input = self._dict_to_str(dev_output) + "\n" + self._dict_to_str(test_output)
        review_output = self.review.process(review_input)
        logger.info(f"Review Agent done | elapsed={time.time()-t:.1f}s")
        state.review_comments = [review_output]

        if jira_enabled:
            try:
                self.phase_jira(state)
            except Exception as e:
                logger.error(f"JIRA phase failed: {e}")

        # Add file generation pipeline at the end
        project_dir = create_project_directory(state.project_name)

        write_backend_files(project_dir, state.backend_code)
        write_tests(project_dir, state.tests)
        write_architecture(project_dir, state.architecture, state.mermaid)
        write_review(project_dir, state.review_comments)

        readme = generate_readme(state)
        write_readme(project_dir, readme)

        zip_file = create_zip(project_dir)

        state.generated_path = str(project_dir)
        state.zip_file = zip_file

        state.final_status = "completed"

        # Phase 2: GitHub Integration
        if github_enabled:
            state.github_enabled = True
            try:
                self.phase_draft_pr(state)
            except Exception as e:
                logger.error(f"GitHub draft PR phase failed: {e}")

        return state
    """