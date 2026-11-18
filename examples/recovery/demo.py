"""Append-only JSONL event log with deterministic state reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunState:
    status: str = "pending"
    completed_steps: tuple[str, ...] = ()
    outputs: tuple[tuple[str, Any], ...] = ()


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")
        stream.flush()


def reconstruct(path: Path) -> RunState:
    state = RunState()
    if not path.exists():
        return state
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event must be an object")
            kind = event["type"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid event at line {line_number}") from error
        if kind == "started":
            if state.status != "pending":
                raise ValueError(f"invalid transition at line {line_number}: started from {state.status}")
            state = RunState("running", state.completed_steps, state.outputs)
        elif kind == "step_completed":
            if state.status != "running":
                raise ValueError(f"invalid transition at line {line_number}: step_completed from {state.status}")
            step = event["step"]
            if not isinstance(step, str) or not step.strip():
                raise ValueError(f"invalid step at line {line_number}")
            outputs = dict(state.outputs)
            outputs[step] = event.get("output")
            state = RunState(state.status, tuple(dict.fromkeys((*state.completed_steps, step))), tuple(sorted(outputs.items())))
        elif kind == "failed":
            if state.status != "running":
                raise ValueError(f"invalid transition at line {line_number}: failed from {state.status}")
            state = RunState("failed", state.completed_steps, state.outputs)
        elif kind == "completed":
            if state.status != "running":
                raise ValueError(f"invalid transition at line {line_number}: completed from {state.status}")
            state = RunState("completed", state.completed_steps, state.outputs)
        else:
            raise ValueError(f"unknown event type at line {line_number}: {kind}")
    return state


def main() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "run.jsonl"
        append_event(path, {"type": "started"})
        append_event(path, {"type": "step_completed", "step": "inspect", "output": "ok"})
        state = reconstruct(path)
        print(f"status={state.status} completed={','.join(state.completed_steps)} output={dict(state.outputs)['inspect']}")


if __name__ == "__main__":
    main()
