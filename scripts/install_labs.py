"""Install every independently packaged lab into the active Python environment."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    project_files = sorted((ROOT / "examples").glob("*/pyproject.toml"))
    if len(project_files) != 12:
        raise SystemExit(f"expected 12 lab packages, found {len(project_files)}")
    for project_file in project_files:
        print(f"Installing {project_file.parent.name}", flush=True)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "--editable", str(project_file.parent)],
            cwd=ROOT,
            check=True,
        )
    print(f"Installed {len(project_files)} lab packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
