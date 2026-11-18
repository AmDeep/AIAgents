"""In-memory structured trace events with parent spans and cost totals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from uuid import uuid4


@dataclass(frozen=True)
class Event:
    trace_id: str
    span_id: str
    parent_id: str | None
    name: str
    attributes: dict[str, str | int | float | bool]
    timestamp: str


class Trace:
    def __init__(self, trace_id: str | None = None) -> None:
        self.trace_id = trace_id or str(uuid4())
        self.events: list[Event] = []

    def record(self, name: str, *, parent_id: str | None = None, **attributes: str | int | float | bool) -> str:
        if not name.strip():
            raise ValueError("event name must be nonempty")
        known_spans = {event.span_id for event in self.events}
        if parent_id is not None and parent_id not in known_spans:
            raise ValueError("parent span must refer to an existing event")
        for key, value in attributes.items():
            if not key.strip() or not isinstance(value, (str, int, float, bool)):
                raise ValueError("attributes must have nonempty keys and scalar values")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("numeric attributes must be finite")
        cost = attributes.get("cost", 0)
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0:
            raise ValueError("cost must be a nonnegative number")
        span_id = str(len(self.events) + 1)
        self.events.append(Event(self.trace_id, span_id, parent_id, name, attributes,
                                 datetime.now(timezone.utc).isoformat()))
        return span_id

    def total_cost(self) -> float:
        return sum(float(event.attributes.get("cost", 0)) for event in self.events)

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(asdict(event), sort_keys=True) for event in self.events)


def main() -> None:
    trace = Trace("trace-demo")
    root = trace.record("run.start", model="small", cost=0.002)
    trace.record("tool.call", parent_id=root, tool="search_fixture", cost=0.0)
    trace.record("run.complete", parent_id=root, cost=0.003)
    print(f"events={len(trace.events)} cost={trace.total_cost():.3f}")
    print(trace.to_jsonl())


if __name__ == "__main__":
    main()
