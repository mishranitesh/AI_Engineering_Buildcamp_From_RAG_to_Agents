import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()


class JiraTool:
    def __init__(self):
        self.url = os.getenv("JIRA_URL").rstrip("/")
        self.auth = HTTPBasicAuth(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
        self.project_key = os.getenv("JIRA_PROJECT_KEY")
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def _post(self, payload: dict) -> dict:
        resp = requests.post(
            f"{self.url}/rest/api/3/issue",
            json=payload,
            headers=self.headers,
            auth=self.auth,
        )
        if not resp.ok:
            raise Exception(f"{resp.status_code} {resp.reason}: {resp.text}")   # log full body
        return resp.json()

    def _issue_url(self, key: str) -> str:
        return f"{self.url}/browse/{key}"

    def create_epic(self, title: str, description: str) -> tuple[str, str]:
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": title,
                "description": {
                    "type": "doc", "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
                },
                "issuetype": {"name": "Epic"},
            }
        }
        data = self._post(payload)
        key = data["key"]
        return key, self._issue_url(key)

    def create_story(self, summary: str, epic_key: str) -> tuple[str, str]:
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary[:255],
                "issuetype": {"name": "Story"},
                "parent": {"key": epic_key},
            }
        }
        data = self._post(payload)
        key = data["key"]
        return key, self._issue_url(key)

    def create_task(self, summary: str, story_key: str) -> tuple[str, str]:
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary[:255],
                "issuetype": {"name": "Task"},
                "parent": {"key": story_key},
            }
        }
        data = self._post(payload)
        key = data["key"]
        return key, self._issue_url(key)
    
    def get_stories(self, epic_key: str) -> list[str]:
        """Fetch story summaries from JIRA after human review/edits."""
        resp = requests.post(
            f"{self.url}/rest/api/3/search/jql",
            json={
                "jql": f"parent={epic_key} AND issuetype=Story ORDER BY created ASC",
                "fields": ["summary"],
                "maxResults": 50,
            },
            headers=self.headers,
            auth=self.auth,
        )
        resp.raise_for_status()
        return [issue["fields"]["summary"] for issue in resp.json()["issues"]]
