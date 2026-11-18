import json
import pytest

from agent_trace_lab.demo import Trace


def test_trace_has_order_parentage_and_cost():
    trace = Trace("trace-test")
    root = trace.record("run.start", cost=0.1)
    child = trace.record("tool.call", parent_id=root, tool="fixture")
    trace.record("run.end", parent_id=root, cost=0.2)
    assert child == "2"
    assert trace.events[1].parent_id == root
    assert trace.total_cost() == 0.30000000000000004
    assert len(trace.to_jsonl().splitlines()) == 3


def test_trace_serialization_is_structured():
    trace = Trace("fixed")
    trace.record("call", input_bytes=12)
    event = json.loads(trace.to_jsonl())
    assert event["trace_id"] == "fixed"
    assert event["attributes"]["input_bytes"] == 12


@pytest.mark.parametrize("kwargs", [
    {"parent_id": "missing"},
    {"cost": -1},
    {"cost": float("nan")},
    {"nested": {"secret": "value"}},
])
def test_invalid_trace_relationships_and_attributes_are_rejected(kwargs):
    trace = Trace("fixed")
    with pytest.raises(ValueError):
        trace.record("call", **kwargs)


def test_empty_event_name_is_rejected():
    with pytest.raises(ValueError, match="event name"):
        Trace("fixed").record(" ")
