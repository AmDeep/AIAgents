"""Validated task envelopes keep scope and acceptance criteria across handoffs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskEnvelope:
    task_id: str
    objective: str
    allowed_actions: frozenset[str]
    acceptance_criteria: tuple[str, ...]
    context_refs: tuple[str, ...]

    def validate(self) -> None:
        if not self.task_id.strip() or not self.objective.strip():
            raise ValueError("task_id and objective are required")
        if not self.acceptance_criteria:
            raise ValueError("at least one acceptance criterion is required")
        if any(not item.strip() for item in self.acceptance_criteria):
            raise ValueError("acceptance criteria must be nonempty")


@dataclass(frozen=True)
class HandoffResult:
    task_id: str
    summary: str
    artifacts: tuple[str, ...]
    unresolved: tuple[str, ...]
    actions_taken: tuple[str, ...] = ()


def accept_handoff(task: TaskEnvelope, result: HandoffResult) -> None:
    task.validate()
    if result.task_id != task.task_id:
        raise ValueError("handoff task id mismatch")
    if not result.summary.strip():
        raise ValueError("handoff summary is required")
    if result.unresolved:
        raise ValueError("handoff has unresolved items")
    unauthorized = set(result.actions_taken) - task.allowed_actions
    if unauthorized:
        raise ValueError(f"handoff used unauthorized actions: {', '.join(sorted(unauthorized))}")


def main() -> None:
    task = TaskEnvelope("task-7", "Review local fixture", frozenset({"read_fixture"}),
                        ("Report findings",), ("fixture://sample",))
    result = HandoffResult("task-7", "Fixture reviewed; no issue found.", ("report://local",), ())
    accept_handoff(task, result)
    print(f"accepted task={result.task_id} artifacts={len(result.artifacts)} unresolved={len(result.unresolved)}")


if __name__ == "__main__":
    main()
