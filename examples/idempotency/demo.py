"""SQLite-backed idempotency ledger and durable step checkpoints."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from typing import Any


class IdempotencyStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute("CREATE TABLE IF NOT EXISTS operations (key TEXT PRIMARY KEY, result TEXT NOT NULL)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS checkpoints (run_id TEXT NOT NULL, step TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY (run_id, step))")
        self.connection.commit()

    def execute_once(self, key: str, operation: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any], bool]:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("idempotency key must be nonempty")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute("SELECT result FROM operations WHERE key = ?", (key,)).fetchone()
            if row:
                self.connection.commit()
                return json.loads(row[0]), True
            result = operation()
            if not isinstance(result, dict):
                raise TypeError("idempotent operation must return a dictionary")
            serialized = json.dumps(result, sort_keys=True, allow_nan=False)
            self.connection.execute("INSERT INTO operations(key, result) VALUES (?, ?)", (key, serialized))
            self.connection.commit()
            return result, False
        except BaseException:
            self.connection.rollback()
            raise

    def checkpoint(self, run_id: str, step: str, data: dict[str, Any]) -> None:
        if not run_id.strip() or not step.strip():
            raise ValueError("run_id and step must be nonempty")
        self.connection.execute(
            "INSERT INTO checkpoints(run_id, step, data) VALUES (?, ?, ?) "
            "ON CONFLICT(run_id, step) DO UPDATE SET data=excluded.data",
            (run_id, step, json.dumps(data, sort_keys=True, allow_nan=False)),
        )
        self.connection.commit()

    def load_checkpoint(self, run_id: str, step: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT data FROM checkpoints WHERE run_id=? AND step=?", (run_id, step)).fetchone()
        return json.loads(row[0]) if row else None


def main() -> None:
    store = IdempotencyStore(sqlite3.connect(":memory:"))
    calls: list[int] = []
    operation = lambda: calls.append(1) or {"record_id": "local-1"}
    first, first_replay = store.execute_once("request-42", operation)
    second, second_replay = store.execute_once("request-42", operation)
    store.checkpoint("run-42", "write", first)
    print(f"first_replay={first_replay} second_replay={second_replay} calls={len(calls)} result={second}")
    print(f"checkpoint={store.load_checkpoint('run-42', 'write')}")


if __name__ == "__main__":
    main()
