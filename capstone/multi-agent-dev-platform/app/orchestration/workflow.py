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

    def run(self, requirement: str) -> WorkflowState:
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

        return state