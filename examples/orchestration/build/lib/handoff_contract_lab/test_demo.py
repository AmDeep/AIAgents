import pytest

from handoff_contract_lab.demo import HandoffResult, TaskEnvelope, accept_handoff


def task():
    return TaskEnvelope("t1", "Inspect fixture", frozenset({"read"}), ("include evidence",), ("fixture://1",))


def test_valid_handoff_is_accepted():
    accept_handoff(task(), HandoffResult("t1", "Checked fixture", ("artifact://1",), ()))


@pytest.mark.parametrize("result", [
    HandoffResult("wrong", "Summary", (), ()),
    HandoffResult("t1", "", (), ()),
    HandoffResult("t1", "Summary", (), ("Need permission",)),
])
def test_incomplete_or_mismatched_handoff_is_rejected(result):
    with pytest.raises(ValueError):
        accept_handoff(task(), result)


def test_task_without_acceptance_criteria_is_rejected():
    invalid = TaskEnvelope("t1", "Inspect", frozenset(), (), ())
    with pytest.raises(ValueError, match="acceptance criterion"):
        accept_handoff(invalid, HandoffResult("t1", "done", (), ()))


def test_handoff_cannot_claim_actions_outside_task_allowlist():
    result = HandoffResult("t1", "Checked fixture", (), (), ("read", "write_production"))
    with pytest.raises(ValueError, match="unauthorized actions"):
        accept_handoff(task(), result)
