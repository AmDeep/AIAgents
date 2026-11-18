from contextlib import closing
import sqlite3

from context_engineering_lab.demo import MemoryItem, MemoryStore, TaskSummary, build_context, estimate_tokens, retrieve
import pytest


def test_context_budget_and_constraint_retrieval():
    items = [MemoryItem("safety", "Never write to production.", "constraint", 9, frozenset({"safety"}))]
    text, labels = build_context(
        system="Rules", recent=["Recent task"], summary="Summary", memories=items,
        query_tags={"safety"}, token_budget=40,
    )
    assert "Never write to production." in text
    assert labels[0] == "system"
    assert sum(estimate_tokens(part) for part in text.split("\n")) <= 40


def test_retrieval_is_relevant_ranked_and_bounded():
    items = [
        MemoryItem("b", "B", "note", 1, frozenset({"x"})),
        MemoryItem("a", "A", "note", 5, frozenset({"x"})),
        MemoryItem("c", "C", "note", 20, frozenset({"y"})),
    ]
    assert [item.key for item in retrieve(items, {"x"}, 1)] == ["a"]


def test_empty_text_has_zero_cost():
    assert estimate_tokens("") == 0


def test_required_system_context_cannot_be_silently_dropped():
    with pytest.raises(ValueError, match="required system context"):
        build_context(system="Long required instruction", recent=[], summary="", memories=[],
                      query_tags=set(), token_budget=1)


def test_high_priority_safety_memory_is_packed_before_recent_details():
    memory = MemoryItem("prod", "Never write to production.", "constraint", 100, frozenset({"safety"}))
    text, labels = build_context(
        system="S", recent=["Long recent detail that can be omitted."], summary="Brief summary.",
        memories=[memory], query_tags={"safety"}, token_budget=15,
    )
    assert "Never write to production." in text
    assert "recent-0" not in labels


def test_zero_retrieval_limit_returns_no_memories():
    item = MemoryItem("a", "remember me", "note", 1, frozenset({"x"}))
    assert retrieve([item], {"x"}, 0) == []


@pytest.mark.parametrize("budget", [-1, 1.5, True])
def test_invalid_context_budget_is_rejected(budget):
    with pytest.raises(ValueError, match="token budget"):
        build_context(system="rules", recent=[], summary="", memories=[], query_tags=set(), token_budget=budget)


def test_negative_retrieval_limit_is_rejected():
    with pytest.raises(ValueError, match="retrieval limit"):
        retrieve([], set(), -1)


def test_summary_preserves_goal_and_constraints_before_optional_details():
    summary = TaskSummary(
        "Ship local change", ("No production writes",),
        open_items=("Verify the tests",), decisions=("Use local SQLite",), completed=("Inspect code",),
    ).render(14)
    assert "goal: Ship local change" in summary
    assert "constraint: No production writes" in summary
    assert "open:" not in summary


def test_summary_rejects_budget_that_cannot_fit_required_facts():
    with pytest.raises(ValueError, match="goal and constraints"):
        TaskSummary("Important goal", ("Never expose credentials",)).render(1)


def test_summary_requires_goal_and_valid_budget():
    with pytest.raises(ValueError, match="goal"):
        TaskSummary(" ").render(10)
    with pytest.raises(ValueError, match="summary token budget"):
        TaskSummary("Goal").render(-1)


def test_memory_retrieval_survives_store_reconstruction_with_provenance(tmp_path):
    database = tmp_path / "memory.sqlite3"
    with closing(sqlite3.connect(database)) as connection:
        first = MemoryStore(connection)
        first.put(MemoryItem("policy", "No production writes.", "constraint", 10,
                             frozenset({"safety"}), "policy.md"))

    with closing(sqlite3.connect(database)) as connection:
        reopened = MemoryStore(connection)
        result = reopened.retrieve({"safety"}, 1)
    assert result == [MemoryItem("policy", "No production writes.", "constraint", 10,
                                 frozenset({"safety"}), "policy.md")]


def test_memory_upsert_replaces_existing_record():
    store = MemoryStore(sqlite3.connect(":memory:"))
    store.put(MemoryItem("note", "old", "note", 1, frozenset({"old"}), "old.txt"))
    store.put(MemoryItem("note", "new", "decision", 2, frozenset({"new"}), "new.txt"))
    assert store.retrieve({"old"}, 5) == []
    assert store.retrieve({"new"}, 5) == [MemoryItem("note", "new", "decision", 2, frozenset({"new"}), "new.txt")]


def test_memory_store_rejects_missing_provenance():
    store = MemoryStore(sqlite3.connect(":memory:"))
    with pytest.raises(ValueError, match="source"):
        store.put(MemoryItem("key", "text", "note", source=" "))


def test_context_includes_memory_source_for_provenance():
    item = MemoryItem("policy", "No production writes.", "constraint", 2,
                      frozenset({"safety"}), "policy.md")
    text, _ = build_context(system="rules", recent=[], summary="", memories=[item],
                            query_tags={"safety"}, token_budget=40)
    assert "[source: policy.md]" in text
