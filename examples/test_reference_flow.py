"""Exercise several guardrails together as a local end-to-end run."""

import json
import sqlite3

from authorization_boundary_lab.demo import AccessDenied, Action, Policy, guarded_operation
from completion_verification_lab.demo import CompletionClaim, verify_completion
from idempotency_ledger_lab.demo import IdempotencyStore
from agent_trace_lab.demo import Trace
from tool_contract_lab.demo import create_ticket_tool


def test_local_tool_run_is_authorized_deduplicated_verified_and_traced():
    policy = Policy(frozenset({Action.WRITE_FIXTURE}))
    store = IdempotencyStore(sqlite3.connect(":memory:"))
    trace = Trace("integration-run")
    trace.record("run.start", action=Action.WRITE_FIXTURE.value)
    calls = []

    def write_fixture(_: str) -> dict[str, str]:
        calls.append("write")
        return {"record_id": "fixture-17"}

    def authorized_idempotent_write() -> tuple[dict[str, str], bool]:
        return guarded_operation(
            Action.WRITE_FIXTURE,
            policy,
            lambda: "fake-scoped-credential",
            lambda credential: store.execute_once(
                "request-17",
                lambda: write_fixture(credential),
            ),
        )

    first, replayed = authorized_idempotent_write()
    second, replayed_again = authorized_idempotent_write()
    trace.record("tool.complete", parent_id="1", replay=replayed_again, cost=0.0)

    claim = CompletionClaim("integration-run", "completed")
    verification = verify_completion(claim, {
        "write_result_matches": lambda: first == second == {"record_id": "fixture-17"},
        "write_not_repeated": lambda: calls == ["write"],
    })
    trace.record("run.verified", parent_id="1", passed=verification.passed)

    assert replayed is False
    assert replayed_again is True
    assert verification.passed
    assert trace.total_cost() == 0
    assert [event.name for event in trace.events] == ["run.start", "tool.complete", "run.verified"]


def test_denial_stops_before_tool_validation_or_write():
    policy = Policy(frozenset())
    writes = []
    result = create_ticket_tool(json.dumps({"title": "fixture change", "priority": "normal"}))
    assert result["ok"] is True
    try:
        guarded_operation(Action.WRITE_FIXTURE, policy, lambda: "must-not-load",
                          lambda _: writes.append(result["ticket"]) or "written")
    except AccessDenied:
        pass
    else:
        raise AssertionError("denied action was not blocked")
    assert writes == []
