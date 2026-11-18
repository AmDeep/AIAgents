"""Run each demo and render its actual stdout as a compact SVG terminal capture."""

from __future__ import annotations

import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def render_terminal_svg(title: str, output: str) -> str:
    lines = output.rstrip("\n").splitlines() or ["(no standard output)"]
    escaped = [html.escape(line) for line in lines]
    width = max(760, min(1600, max(len(line) for line in lines) * 9 + 64))
    row_height = 22
    height = 72 + row_height * len(lines)
    text = "\n".join(
        f'<text x="28" y="{74 + index * row_height}" class="line">{line}</text>'
        for index, line in enumerate(escaped)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(title)} demo stdout</title>
<desc id="desc">Terminal-style rendering of standard output captured by running the project's demo.</desc>
<style>text{{font-family:Consolas,ui-monospace,monospace}} .line{{font-size:14px;fill:#d7e0ea}} .head{{font-size:13px;fill:#9fb0c1}} .bg{{fill:#111820}} .bar{{fill:#1e2a35}}</style>
<rect class="bg" x="0" y="0" width="100%" height="100%" rx="8"/>
<path class="bar" d="M8 0h{width - 16}a8 8 0 0 1 8 8v44H0V8a8 8 0 0 1 8-8z"/>
<circle cx="22" cy="26" r="5" fill="#df756c"/><circle cx="40" cy="26" r="5" fill="#e2b764"/><circle cx="58" cy="26" r="5" fill="#78b88a"/>
<text x="78" y="31" class="head">{html.escape(title)} / captured stdout</text>
{text}
</svg>
'''


def main() -> int:
    failures: list[str] = []
    modules = sorted(
        directory.name for directory in EXAMPLES.iterdir()
        if directory.is_dir() and (directory / "demo.py").is_file()
    )
    for module_name in modules:
        project_file = EXAMPLES / module_name / "pyproject.toml"
        metadata = tomllib.loads(project_file.read_text(encoding="utf-8"))
        command = next(iter(metadata["project"]["scripts"]))
        executable = shutil.which(command)
        if executable is None:
            failures.append(f"{module_name}: console command {command!r} is not installed")
            continue
        completed = subprocess.run(
            [executable], cwd=ROOT, capture_output=True,
            text=True, timeout=30, check=False,
        )
        evidence_dir = EXAMPLES / module_name / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "module": f"{metadata['project']['name']}.demo",
            "command": [command],
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        (evidence_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        (evidence_dir / "demo-output.svg").write_text(
            render_terminal_svg(module_name, completed.stdout), encoding="utf-8"
        )
        if completed.returncode:
            failures.append(f"{module_name}: exit {completed.returncode}: {completed.stderr.strip()}")
        else:
            print(f"captured {module_name} via {command}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Captured {len(modules)} successful demo runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
