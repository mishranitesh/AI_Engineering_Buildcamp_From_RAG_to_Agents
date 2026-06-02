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
            gh.add_pr_comment(state.pr_number, f"## Review Agent Report\n\n{state.review_comments[0]}")

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

    """
    def _run_github_phase(self, state: WorkflowState, auto_merge: bool = False) -> None:
        gh = GitHubTool()
        autofix = AutoFixAgent()

        branch_name = f"ai-gen/{state.project_name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # 1. Create branch
        t = time.time()
        gh.create_branch(branch_name)
        logger.info(f"GitHub branch created | branch={branch_name} | elapsed={time.time()-t:.1f}s")
        state.github_branch = branch_name

        # 2. Commit generated files
        all_files = {}
        for fname, code in state.backend_code.items():
            all_files[f"backend/{fname}"] = code
        for fname, code in state.tests.items():
            all_files[f"tests/{fname}"] = code

        t = time.time()
        gh.commit_files(branch_name, all_files, f"feat: AI-generated code for {state.project_name}", project_name=state.project_name)
        logger.info(f"GitHub files committed | files={list(all_files.keys())} | elapsed={time.time()-t:.1f}s")

        # 3. Open PR
        pr_body = f"## AI-Generated Project\n\n**Requirement:**\n{state.requirement[:500]}\n\n**Review Comments:**\n{state.review_comments[0][:1000] if state.review_comments else ''}"
        t = time.time()
        pr_number, pr_url = gh.create_pull_request(branch_name, f"AI: {state.project_name}", pr_body)
        logger.info(f"GitHub PR created | pr_url={pr_url} | elapsed={time.time()-t:.1f}s")
        state.pr_number = pr_number
        state.pr_url = pr_url

        # 4. Post review comments on PR
        if state.review_comments:
            gh.add_pr_comment(pr_number, f"## Review Agent Report\n\n{state.review_comments[0]}")

        # 5. Auto-fix Agent
        t = time.time()
        code_str = self._dict_to_str(state.backend_code)
        review_str = state.review_comments[0] if state.review_comments else ""
        fixed_raw = autofix.process(code_str, review_str)
        state.fixed_code = self._extract_files_from_autofix(fixed_raw)
        logger.info(f"AutoFix Agent done | files={list(state.fixed_code.keys())} | elapsed={time.time()-t:.1f}s")

        # Commit fixed code if any files were extracted
        if state.fixed_code:
            fixed_with_path = {f"backend/{f}": c for f, c in state.fixed_code.items()}
            gh.commit_files(branch_name, fixed_with_path, "fix: Apply Auto-Fix Agent review corrections", project_name=state.project_name)
            gh.add_pr_comment(pr_number, "Auto-Fix Agent applied corrections based on review comments.")

        # 6. Optionally merge
        if auto_merge:
            merged = gh.merge_pull_request(pr_number)
            if merged:
                logger.info(f"GitHub PR merged | pr_number={pr_number}")
    """
    
    def run(self, requirement: str, github_enabled: bool = False, auto_merge: bool = False) -> WorkflowState:
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