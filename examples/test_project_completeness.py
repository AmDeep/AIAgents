"""Repository-level contract for the twelve independently runnable labs."""

from pathlib import Path
import html
import json
import re
import tomllib


ROOT = Path(__file__).parent
REQUIRED_LABS = {
    "context_engineering",
    "tool_schemas",
    "permissions",
    "retry_budgets",
    "idempotency",
    "orchestration",
    "verification",
    "evals",
    "observability",
    "recovery",
    "sandbox",
    "economics",
}


def test_all_labs_have_independent_project_artifacts():
    found = {path.parent.name for path in ROOT.glob("*/pyproject.toml")}
    assert found == REQUIRED_LABS
    for name in sorted(REQUIRED_LABS):
        project = ROOT / name
        assert (project / "README.md").is_file(), name
        assert (project / "demo.py").is_file(), name
        assert list(project.glob("test_*.py")), name
        assert (project / "architecture" / "overview.mmd").is_file(), name
        assert (project / "evidence" / "demo-output.svg").is_file(), name
        assert (project / "evidence" / "run.json").is_file(), name


def test_package_metadata_has_unique_distribution_and_console_command():
    distributions = set()
    commands = set()
    for project_file in ROOT.glob("*/pyproject.toml"):
        data = tomllib.loads(project_file.read_text(encoding="utf-8"))
        distribution = data["project"]["name"]
        script_map = data["project"]["scripts"]
        assert distribution not in distributions
        distributions.add(distribution)
        assert len(script_map) == 1
        command = next(iter(script_map))
        assert command not in commands
        commands.add(command)


def test_project_guides_have_distinct_titles_and_substantial_unique_content():
    guides = [path.read_text(encoding="utf-8") for path in sorted(ROOT.glob("*/README.md"))]
    titles = [next(line for line in guide.splitlines() if line.startswith("# ")) for guide in guides]
    assert len(titles) == len(set(titles)) == 12
    assert len(set(guides)) == 12
    assert all(len(guide.split()) >= 150 for guide in guides)


def test_committed_run_records_and_svg_screenshots_are_current():
    for project in sorted(path for path in ROOT.iterdir() if path.is_dir() and (path / "pyproject.toml").is_file()):
        record = json.loads((project / "evidence" / "run.json").read_text(encoding="utf-8"))
        stdout = record["stdout"].rstrip("\n").splitlines() or ["(no standard output)"]
        svg = (project / "evidence" / "demo-output.svg").read_text(encoding="utf-8")
        assert record["exit_code"] == 0, project.name
        for line in stdout:
            escaped_line = html.escape(line)
            assert re.sub(r"\s+", " ", escaped_line).strip() in re.sub(r"\s+", " ", svg), project.name
        assert "<svg " in svg and "<script>" not in svg, project.name
