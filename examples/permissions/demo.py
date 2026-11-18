"""Deny-by-default authorization checked before a secret is read."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable


class Action(StrEnum):
    READ_FIXTURE = "read_fixture"
    WRITE_FIXTURE = "write_fixture"
    WRITE_PRODUCTION = "write_production"


@dataclass(frozen=True)
class Policy:
    allowed: frozenset[Action]

    def authorize(self, action: Action) -> bool:
        return action in self.allowed


class AccessDenied(PermissionError):
    pass


def guarded_operation(action: Action, policy: Policy, load_credential: Callable[[], str], operation: Callable[[str], str]) -> str:
    """The credential loader is unreachable unless policy permits the action."""
    if not policy.authorize(action):
        raise AccessDenied(f"denied:{action.value}")
    credential = load_credential()
    return operation(credential)


def main() -> None:
    policy = Policy(frozenset({Action.READ_FIXTURE}))
    result = guarded_operation(Action.READ_FIXTURE, policy, lambda: "local-test-credential", lambda _: "fixture read")
    print(f"allowed={result}")
    try:
        guarded_operation(Action.WRITE_PRODUCTION, policy, lambda: "should-not-load", lambda _: "written")
    except AccessDenied as error:
        print(str(error))


if __name__ == "__main__":
    main()
