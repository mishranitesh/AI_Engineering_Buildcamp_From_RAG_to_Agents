from unittest.mock import MagicMock, patch


def test_github_tool_create_branch():
    with patch("app.tools.github_tool.Github") as mock_github:
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        mock_repo.get_git_ref.return_value.object.sha = "abc123"

        from app.tools.github_tool import GitHubTool
        gh = GitHubTool()
        gh.create_branch("feature/test")

        mock_repo.create_git_ref.assert_called_once()

def test_github_tool_add_pr_comment():
    with patch("app.tools.github_tool.Github") as mock_github:
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo

        from app.tools.github_tool import GitHubTool
        gh = GitHubTool()
        gh.add_pr_comment(1, "Test comment")

        mock_repo.get_pull.assert_called_with(1)
        mock_repo.get_pull.return_value.create_issue_comment.assert_called_with("Test comment")

def test_jira_tool_issue_url():
    with patch("app.tools.jira_tool.requests"):
        import os
        os.environ["JIRA_URL"] = "https://test.atlassian.net"
        os.environ["JIRA_EMAIL"] = "test@test.com"
        os.environ["JIRA_API_TOKEN"] = "token"
        os.environ["JIRA_PROJECT_KEY"] = "TEST"

        from app.tools.jira_tool import JiraTool
        jira = JiraTool()
        url = jira._issue_url("TEST-1")
        assert url == "https://test.atlassian.net/browse/TEST-1"
