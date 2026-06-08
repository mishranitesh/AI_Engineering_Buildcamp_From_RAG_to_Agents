import json, os, sqlite3
from pathlib import Path
from openai import OpenAI

DB_FILE = Path(__file__).parent.parent / "runs" / "sessions.db"
GT_FILE = Path(__file__).parent / "ground_truth.json"
client  = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_expected_criteria(requirement: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": f"""
Given this API requirement, return a JSON object with:
- min_user_stories (int)
- required_story_keywords (list of str): key action verbs from the requirement
- required_files (list of str): e.g. ["main.py"]
- required_endpoints (list of str): HTTP methods needed e.g. ["POST","GET","DELETE"]
- review_min_items (int): always 3

Requirement: {requirement}
Return only valid JSON, no explanation.
        """}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)

def seed_from_project(project_name: str) -> bool:
    """Add one project to ground_truth.json. Returns True if added, False if duplicate."""
    if not DB_FILE.exists():
        print("No sessions.db found — run a workflow first.")
        return False

    conn = sqlite3.connect(str(DB_FILE))
    row = conn.execute(
        "SELECT state_json FROM sessions WHERE project_name = ?", (project_name,)
    ).fetchone()
    conn.close()

    if not row:
        print(f"Project '{project_name}' not found in sessions.db")
        return False

    import json as _json
    state = _json.loads(row[0])
    requirement = state.get("requirement", "")

    existing = json.loads(GT_FILE.read_text()) if GT_FILE.exists() else []
    existing_ids = {s["id"] for s in existing}

    if project_name in existing_ids:
        print(f"'{project_name}' already in ground_truth.json — skipping")
        return False

    print(f"Generating criteria for: {project_name}")
    expected = generate_expected_criteria(requirement)
    existing.append({"id": project_name, "requirement": requirement, "expected": expected})
    GT_FILE.write_text(json.dumps(existing, indent=2))
    print(f"Added '{project_name}' to ground_truth.json ({len(existing)} total samples)")
    return True

if __name__ == "__main__":
    # Seed all positively-rated projects from logs
    from pathlib import Path
    import re
    import argparse

    parser = argparse.ArgumentParser(description="Seed ground truth from user feedback")
    parser.add_argument("--project", help="Specific project name to seed. If omitted, seeds all positively-rated projects from log.")
    args = parser.parse_args()

    if args.project:
        seed_from_project(args.project)
    else:
        log = Path(__file__).parent.parent / "logs" / "workflow.log"
        if not log.exists():
            print("No log file found.")
        else:
            seen = set()
            for line in log.read_text().splitlines():
                m = re.search(r"USER_FEEDBACK \| project=(\S+) \| rating=positive", line)
                if m and m.group(1) not in seen:
                    seen.add(m.group(1))
                    seed_from_project(m.group(1))