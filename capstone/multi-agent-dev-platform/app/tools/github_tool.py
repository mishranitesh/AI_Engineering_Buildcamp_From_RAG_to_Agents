import os
from github import Github, GithubException
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class GitHubTool:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        self.client = Github(token)
        owner = os.getenv("GITHUB_OWNER")
        repo_name = os.getenv("GITHUB_REPO")
        print(f"DEBUG GitHub: owner={owner}, repo={repo_name}, token_set={bool(token)}")
        self.repo = self.client.get_repo(f"{owner}/{repo_name}")
        self.base_path = os.getenv("GITHUB_BASE_PATH", "").strip("/")

    def _full_path(self, path: str, project_name: str) -> str:
        if self.base_path:
            return f"{self.base_path}/{project_name}/{path}"
        return path

    def create_branch(self, branch_name: str, base: str = "main") -> str:
        base_ref = self.repo.get_git_ref(f"heads/{base}")
        self.repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_ref.object.sha
        )
        return branch_name

    def commit_files(self, branch_name: str, files: Dict[str, str], commit_message: str, project_name: str = "project") -> None:
        for path, content in files.items():
            full_path = self._full_path(path, project_name)
            try:
                existing = self.repo.get_contents(full_path, ref=branch_name)
                self.repo.update_file(
                    path=full_path,
                    message=commit_message,
                    content=content,
                    sha=existing.sha,
                    branch=branch_name
                )
            except GithubException:
                self.repo.create_file(
                    path=full_path,
                    message=commit_message,
                    content=content,
                    branch=branch_name
                )

    def create_pull_request(self, branch_name: str, title: str, body: str) -> tuple[int, str]:
        pr = self.repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main"
        )
        return pr.number, pr.html_url

    def add_pr_comment(self, pr_number: int, comment: str) -> None:
        pr = self.repo.get_pull(pr_number)
        pr.create_issue_comment(comment)

    def merge_pull_request(self, pr_number: int, commit_message: str = "Auto-merged by Review Agent") -> bool:
        pr = self.repo.get_pull(pr_number)
        result = pr.merge(commit_message=commit_message)
        return result.merged
    
    def create_draft_pull_request(self, branch_name: str, title: str, body: str) -> tuple[int, str]:
        pr = self.repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main",
            draft=True          # <-- the only change vs current create_pull_request
        )
        return pr.number, pr.html_url

    def mark_pr_ready_for_review(self, pr_number: int) -> None:
        """PyGithub has no native method; use GraphQL."""
        import requests
        pr = self.repo.get_pull(pr_number)
        query = """
        mutation($prId: ID!) {
        markPullRequestReadyForReview(input: {pullRequestId: $prId}) {
            pullRequest { isDraft }
        }
        }
        """
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"prId": pr.node_id}},
            headers={"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"},
        )
        resp.raise_for_status()

    def get_pr_comments(self, pr_number: int) -> list[str]:
        pr = self.repo.get_pull(pr_number)
        return [c.body for c in pr.get_issue_comments()]

