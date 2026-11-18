import sqlite3

import pytest

from idempotency_ledger_lab.demo import IdempotencyStore


def test_repeated_key_returns_original_result_without_repeating_write():
    store = IdempotencyStore(sqlite3.connect(":memory:"))
    calls = []
    operation = lambda: calls.append(1) or {"id": "one"}
    result, replayed = store.execute_once("key", operation)
    again, replayed_again = store.execute_once("key", operation)
    assert result == again == {"id": "one"}
    assert replayed is False and replayed_again is True
    assert len(calls) == 1


def test_checkpoint_can_be_loaded_after_store_reconstruction():
    connection = sqlite3.connect(":memory:")
    first = IdempotencyStore(connection)
    first.checkpoint("run", "step", {"cursor": 8})
    reconstructed = IdempotencyStore(connection)
    assert reconstructed.load_checkpoint("run", "step") == {"cursor": 8}


def test_failed_operation_does_not_reserve_key():
    store = IdempotencyStore(sqlite3.connect(":memory:"))
    with pytest.raises(RuntimeError):
        store.execute_once("key", lambda: (_ for _ in ()).throw(RuntimeError("failed")))
    result, replayed = store.execute_once("key", lambda: {"ok": True})
    assert result == {"ok": True} and replayed is False


def test_invalid_key_and_result_fail_without_reserving_operation():
    store = IdempotencyStore(sqlite3.connect(":memory:"))
    calls = []
    with pytest.raises(ValueError, match="idempotency key"):
        store.execute_once(" ", lambda: calls.append(1) or {})
    with pytest.raises(TypeError, match="dictionary"):
        store.execute_once("key", lambda: ["not", "a", "mapping"])
    result, replayed = store.execute_once("key", lambda: {"ok": True})
    assert calls == []
    assert result == {"ok": True} and not replayed


def test_checkpoint_upserts_data_and_scopes_by_run_and_step():
    store = IdempotencyStore(sqlite3.connect(":memory:"))
    store.checkpoint("run-a", "step-1", {"cursor": 1})
    store.checkpoint("run-a", "step-1", {"cursor": 2})
    store.checkpoint("run-b", "step-1", {"cursor": 3})
    assert store.load_checkpoint("run-a", "step-1") == {"cursor": 2}
    assert store.load_checkpoint("run-b", "step-1") == {"cursor": 3}
    assert store.load_checkpoint("run-a", "missing") is None


def test_checkpoint_rejects_empty_scope_and_non_json_values():
    store = IdempotencyStore(sqlite3.connect(":memory:"))
    with pytest.raises(ValueError, match="run_id and step"):
        store.checkpoint("", "step", {})
    with pytest.raises(ValueError):
        store.checkpoint("run", "step", {"value": float("nan")})
