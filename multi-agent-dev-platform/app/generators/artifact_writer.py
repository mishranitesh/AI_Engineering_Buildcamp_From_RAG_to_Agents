from pathlib import Path


def write_backend_files(
    project_dir: Path,
    files: dict
):

    backend_dir = project_dir / "backend"

    backend_dir.mkdir(
        exist_ok=True
    )

    for filename, content in files.items():

        with open(
            backend_dir / filename,
            "w"
        ) as f:
            f.write(content)


def write_tests(
    project_dir: Path,
    tests: dict
):

    test_dir = project_dir / "tests"

    test_dir.mkdir(
        exist_ok=True
    )

    for filename, content in tests.items():

        with open(
            test_dir / filename,
            "w"
        ) as f:
            f.write(content)


def write_architecture(
    project_dir: Path,
    architecture: str,
    mermaid: str
):

    with open(
        project_dir / "architecture.md",
        "w"
    ) as f:
        f.write(architecture)

    with open(
        project_dir / "architecture.mmd",
        "w"
    ) as f:
        f.write(mermaid)


def write_review(
    project_dir: Path,
    review: list
):

    with open(
        project_dir / "review.md",
        "w"
    ) as f:
        f.write("\n\n".join(review))


def write_readme(
    project_dir: Path,
    content: str
):

    with open(
        project_dir / "README.md",
        "w"
    ) as f:
        f.write(content)