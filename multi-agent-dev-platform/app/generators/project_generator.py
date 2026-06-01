from pathlib import Path


def create_project_directory(project_name: str):

    root = (
        Path("generated_projects")
        / project_name
    )

    root.mkdir(
        parents=True,
        exist_ok=True
    )

    return root