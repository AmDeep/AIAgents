"""A completion claim is accepted only when external postconditions hold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CompletionClaim:
    run_id: str
    claimed_status: str


@dataclass(frozen=True)
class Verification:
    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]


def verify_completion(claim: CompletionClaim, checks: dict[str, Callable[[], bool]]) -> Verification:
    if claim.claimed_status != "completed":
        return Verification(False, (), ("agent_did_not_claim_completion",))
    passed: list[str] = []
    failed: list[str] = []
    for name, check in checks.items():
        try:
            (passed if check() else failed).append(name)
        except Exception:
            failed.append(name)
    return Verification(not failed and bool(passed), tuple(passed), tuple(failed))


def main() -> None:
    result = verify_completion(CompletionClaim("run-9", "completed"), {
        "artifact_exists": lambda: True,
        "tests_pass": lambda: True,
    })
    print(f"verified={result.passed} checks={','.join(result.checks)}")


if __name__ == "__main__":
    main()
