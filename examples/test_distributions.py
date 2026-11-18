"""Verify every lab's installed package namespace is runnable."""

from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = []
for project_file in sorted((Path(__file__).parent).glob("*/pyproject.toml")):
    metadata = tomllib.loads(project_file.read_text(encoding="utf-8"))
    scripts = metadata["project"]["scripts"]
    for command, target in scripts.items():
        module = target.split(":", maxsplit=1)[0]
        PROJECTS.append((project_file.parent.name, command, module))


@pytest.mark.parametrize(("project", "command", "module"), PROJECTS)
def test_distribution_module_runs_after_install(project: str, command: str, module: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-I", "-m", module], cwd=ROOT, capture_output=True,
        text=True, timeout=15, check=False,
    )
    assert completed.returncode == 0, f"{project} / {command} failed:\n{completed.stderr}"
    assert completed.stdout.strip(), f"{project} / {command} returned no output"


@pytest.mark.parametrize(("project", "command", "module"), PROJECTS)
def test_console_entry_point_runs(project: str, command: str, module: str) -> None:
    executable = shutil.which(command)
    assert executable is not None, f"{project} console command {command!r} is not installed"
    completed = subprocess.run(
        [executable], cwd=ROOT, capture_output=True, text=True, timeout=15, check=False,
    )
    assert completed.returncode == 0, f"{project} / {command} failed:\n{completed.stderr}"
    assert completed.stdout.strip(), f"{project} / {command} returned no output"
