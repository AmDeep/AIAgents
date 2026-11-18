import pytest

from run_recovery_lab.demo import append_event, reconstruct


def test_interrupted_run_reconstructs_completed_steps(tmp_path):
    log = tmp_path / "run.jsonl"
    append_event(log, {"type": "started"})
    append_event(log, {"type": "step_completed", "step": "one", "output": {"ok": True}})
    state = reconstruct(log)
    assert state.status == "running"
    assert state.completed_steps == ("one",)
    assert dict(state.outputs)["one"] == {"ok": True}


def test_reconstruction_is_repeatable_and_completion_is_terminal_state(tmp_path):
    log = tmp_path / "run.jsonl"
    append_event(log, {"type": "started"})
    append_event(log, {"type": "completed"})
    assert reconstruct(log) == reconstruct(log)
    assert reconstruct(log).status == "completed"


def test_corrupt_log_fails_loudly_with_line_number(tmp_path):
    log = tmp_path / "run.jsonl"
    log.write_text('{"type":"started"}\nnot-json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        reconstruct(log)


def test_missing_log_means_pending(tmp_path):
    assert reconstruct(tmp_path / "missing.jsonl").status == "pending"


@pytest.mark.parametrize("events", [
    [{"type": "completed"}],
    [{"type": "started"}, {"type": "started"}],
    [{"type": "started"}, {"type": "completed"}, {"type": "step_completed", "step": "late"}],
])
def test_impossible_run_transitions_are_rejected(tmp_path, events):
    log = tmp_path / "invalid.jsonl"
    for event in events:
        append_event(log, event)
    with pytest.raises(ValueError, match="invalid transition"):
        reconstruct(log)


def test_non_object_event_and_blank_step_are_rejected(tmp_path):
    log = tmp_path / "invalid.jsonl"
    log.write_text('[]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid event at line 1"):
        reconstruct(log)
    log.write_text('{"type":"started"}\n{"type":"step_completed","step":" "}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid step at line 2"):
        reconstruct(log)
