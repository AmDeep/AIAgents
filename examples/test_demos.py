"""Subprocess smoke tests for every documented runnable example."""

from pathlib import Path
import subprocess
import sys

import pytest


EXAMPLES_ROOT = Path(__file__).parent
REPOSITORY_ROOT = EXAMPLES_ROOT.parent
DEMO_MODULES = sorted(
    f"examples.{directory.name}.demo"
    for directory in EXAMPLES_ROOT.iterdir()
    if directory.is_dir() and (directory / "demo.py").is_file()
)


@pytest.mark.parametrize("module", DEMO_MODULES)
def test_demo_runs_from_repository_root(module: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", module],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == 0, f"{module} failed:\n{completed.stderr}"
    assert completed.stdout.strip(), f"{module} produced no output"
