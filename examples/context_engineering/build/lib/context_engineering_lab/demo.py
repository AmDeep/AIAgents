"""Budgeted context construction with summary and tagged retrieval."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import tempfile


@dataclass(frozen=True)
class MemoryItem:
    key: str
    text: str
    kind: str
    priority: int = 0
    tags: frozenset[str] = frozenset()
    source: str = "unspecified"


@dataclass(frozen=True)
class TaskSummary:
    goal: str
    constraints: tuple[str, ...] = ()
    open_items: tuple[str, ...] = ()
    decisions: tuple[str, ...] = ()
    completed: tuple[str, ...] = ()

    def render(self, token_budget: int) -> str:
        if isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget < 0:
            raise ValueError("summary token budget must be a nonnegative integer")
        if not self.goal.strip():
            raise ValueError("summary goal must be nonempty")
        required = [f"goal: {self.goal.strip()}"]
        required.extend(f"constraint: {item.strip()}" for item in self.constraints if item.strip())
        used = sum(estimate_tokens(line) for line in required)
        if used > token_budget:
            raise ValueError("summary budget cannot fit the goal and constraints")
        lines = list(required)
        optional_groups = (
            ("open", self.open_items),
            ("decision", self.decisions),
            ("completed", self.completed),
        )
        for label, items in optional_groups:
            for item in items:
                if not item.strip():
                    continue
                line = f"{label}: {item.strip()}"
                cost = estimate_tokens(line)
                if used + cost <= token_budget:
                    lines.append(line)
                    used += cost
        return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """Stable rough estimate for demos; production should use its model tokenizer."""
    return max(1, (len(text) + 3) // 4) if text else 0


def retrieve(items: list[MemoryItem], query_tags: set[str], limit: int) -> list[MemoryItem]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("retrieval limit must be a nonnegative integer")
    matches = [item for item in items if item.tags.intersection(query_tags)]
    return sorted(matches, key=lambda item: (-item.priority, item.key))[:limit]


class MemoryStore:
    """Small SQLite-backed memory index suitable for local examples and tests."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "key TEXT PRIMARY KEY, text TEXT NOT NULL, kind TEXT NOT NULL, priority INTEGER NOT NULL, "
            "tags TEXT NOT NULL, source TEXT NOT NULL)"
        )
        self.connection.commit()

    def put(self, item: MemoryItem) -> None:
        if not item.key.strip() or not item.text.strip() or not item.kind.strip() or not item.source.strip():
            raise ValueError("memory key, text, kind, and source must be nonempty")
        self.connection.execute(
            "INSERT INTO memories(key, text, kind, priority, tags, source) VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET text=excluded.text, kind=excluded.kind, "
            "priority=excluded.priority, tags=excluded.tags, source=excluded.source",
            (item.key, item.text, item.kind, item.priority, json.dumps(sorted(item.tags)), item.source),
        )
        self.connection.commit()

    def retrieve(self, query_tags: set[str], limit: int) -> list[MemoryItem]:
        rows = self.connection.execute(
            "SELECT key, text, kind, priority, tags, source FROM memories"
        ).fetchall()
        items = [MemoryItem(key, text, kind, priority, frozenset(json.loads(tags)), source)
                 for key, text, kind, priority, tags, source in rows]
        return retrieve(items, query_tags, limit)


def build_context(
    *, system: str, recent: list[str], summary: str, memories: list[MemoryItem],
    query_tags: set[str], token_budget: int, retrieval_limit: int = 3,
) -> tuple[str, list[str]]:
    """Pack fixed instructions, a summary, recent turns and relevant memory in order."""
    if isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget < 0:
        raise ValueError("token budget must be a nonnegative integer")
    if isinstance(retrieval_limit, bool) or not isinstance(retrieval_limit, int) or retrieval_limit < 0:
        raise ValueError("retrieval limit must be a nonnegative integer")
    sections: list[tuple[str, str]] = [("system", system)]
    sections.extend(
        (f"memory:{item.key}", item.text if item.source == "unspecified" else f"{item.text} [source: {item.source}]")
        for item in retrieve(memories, query_tags, retrieval_limit)
    )
    sections.append(("summary", summary))
    sections.extend((f"recent-{index}", text) for index, text in enumerate(recent))
    selected: list[str] = []
    output: list[str] = []
    system_section = f"[{sections[0][0]}] {sections[0][1]}"
    used = estimate_tokens(system_section)
    if used > token_budget:
        raise ValueError("token budget cannot fit required system context")
    selected.append(sections[0][0])
    output.append(system_section)
    for label, text in sections[1:]:
        rendered = f"[{label}] {text}"
        cost = estimate_tokens(rendered)
        if used + cost <= token_budget:
            output.append(rendered)
            selected.append(label)
            used += cost
    return "\n".join(output), selected


def main() -> None:
    memory = MemoryItem("constraint-1", "Never write to production.", "constraint", 10,
                        frozenset({"safety"}), "local-policy.md")
    summary = TaskSummary("Verify a local change", ("Never write to production.",),
                          ("Inspect the staging fixture.",)).render(40)
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "memory.sqlite3"
        with closing(sqlite3.connect(database)) as connection:
            MemoryStore(connection).put(memory)
        with closing(sqlite3.connect(database)) as connection:
            memories = MemoryStore(connection).retrieve({"safety"}, 3)
        text, labels = build_context(
            system="You are a local test agent.", recent=["Inspect the staging fixture."],
            summary=summary, memories=memories,
            query_tags={"safety"}, token_budget=80,
        )
        print(f"selected={','.join(labels)}")
        print(text)


if __name__ == "__main__":
    main()
