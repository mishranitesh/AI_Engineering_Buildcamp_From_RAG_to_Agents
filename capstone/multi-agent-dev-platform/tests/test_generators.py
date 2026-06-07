import tempfile
from pathlib import Path
from app.generators.artifact_writer import (
    write_backend_files, write_tests, write_architecture, write_review, write_readme
)
from app.generators.zip_generator import create_zip


def test_write_backend_files_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        write_backend_files(project_dir, {"main.py": "print('hello')", "models.py": "class User: pass"})
        assert (project_dir / "backend" / "main.py").exists()
        assert (project_dir / "backend" / "models.py").exists()

def test_write_backend_files_correct_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        write_backend_files(project_dir, {"main.py": "print('hello')"})
        content = (project_dir / "backend" / "main.py").read_text()
        assert content == "print('hello')"

def test_write_tests_creates_test_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        write_tests(project_dir, {"test_main.py": "def test_foo(): pass"})
        assert (project_dir / "tests" / "test_main.py").exists()

def test_write_architecture_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        write_architecture(project_dir, "# Architecture", "graph TD; A-->B")
        assert (project_dir / "architecture.md").exists()
        assert (project_dir / "architecture.mmd").exists()

def test_write_review_joins_comments():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        write_review(project_dir, ["Comment 1", "Comment 2"])
        content = (project_dir / "review.md").read_text()
        assert "Comment 1" in content
        assert "Comment 2" in content

def test_write_readme():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        write_readme(project_dir, "# My Project")
        assert (project_dir / "README.md").read_text() == "# My Project"

def test_create_zip_produces_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "main.py").write_text("code")
        zip_path = create_zip(project_dir)
        assert Path(zip_path).exists()
        assert zip_path.endswith(".zip")
