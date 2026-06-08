import sqlite3
import functools
from pathlib import Path
from app.orchestration.state import WorkflowState

DB_PATH = Path(__file__).parent.parent.parent / "runs" / "sessions.db"

class SessionStore:
    def __init__(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                project_name TEXT PRIMARY KEY,
                state_json   TEXT,
                updated_at   TEXT DEFAULT (datetime('now'))
            )
        """)
        self._db.commit()

    def get(self, project_name: str) -> WorkflowState | None:
        row = self._db.execute(
            "SELECT state_json FROM sessions WHERE project_name = ?", (project_name,)
        ).fetchone()
        return WorkflowState.model_validate_json(row[0]) if row else None

    def save(self, state: WorkflowState) -> None:
        self._db.execute("""
            INSERT INTO sessions (project_name, state_json, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(project_name) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
        """, (state.project_name, state.model_dump_json()))
        self._db.commit()

    def list_resumable(self) -> list[dict]:
        rows = self._db.execute(
            "SELECT project_name, state_json, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
        result = []
        for name, json_str, updated_at in rows:
            s = WorkflowState.model_validate_json(json_str)
            if s.pr_phase != "merged":   # skip fully done runs
                result.append({
                    "project_name": name,
                    "final_status": s.final_status,
                    "pr_phase": s.pr_phase,
                    "jira_epic_key": s.jira_epic_key,
                    "pr_url": s.pr_url,
                    "updated_at": updated_at,
                })
        return result

    def delete(self, project_name: str) -> None:
        self._db.execute("DELETE FROM sessions WHERE project_name = ?", (project_name,))
        self._db.commit()

_store = SessionStore()   # module-level singleton

def checkpoint(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        state = method(self, *args, **kwargs)
        _store.save(state)
        return state
    return wrapper

def clear_checkpoint(project_name: str) -> None:
    _store.delete(project_name)
