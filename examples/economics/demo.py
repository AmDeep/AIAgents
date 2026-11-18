"""Deterministic economics primitives with injectable model and tool calls."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import math
from time import perf_counter
from typing import Callable, TypeVar

T = TypeVar("T")


def route(complexity: int, *, threshold: int = 5) -> str:
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (complexity, threshold)):
        raise ValueError("complexity and threshold must be nonnegative integers")
    return "small" if complexity <= threshold else "large"


class ResponseCache:
    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    @staticmethod
    def key(model: str, prompt: str) -> str:
        if not isinstance(model, str) or not isinstance(prompt, str):
            raise TypeError("model and prompt must be strings")
        encoded = json.dumps([model, prompt], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def get_or_compute(self, model: str, prompt: str, compute: Callable[[], str]) -> tuple[str, bool]:
        key = self.key(model, prompt)
        if key in self._values:
            return self._values[key], True
        value = compute()
        self._values[key] = value
        return value, False


def parallel_tools(tools: dict[str, Callable[[], T]], max_workers: int = 4) -> dict[str, T]:
    if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1:
        raise ValueError("max_workers must be a positive integer")
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {name: pool.submit(tool) for name, tool in tools.items()}
        return {name: future.result() for name, future in futures.items()}


def percentile(values: list[float], percentile_value: float) -> float:
    if not values or not math.isfinite(percentile_value) or not 0 <= percentile_value <= 100:
        raise ValueError("values must be nonempty and percentile must be between 0 and 100")
    if any(not math.isfinite(value) for value in values):
        raise ValueError("sample values must be finite")
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile_value / 100) * len(ordered)))
    index = min(len(ordered) - 1, rank - 1)
    return ordered[index]


def measure(call: Callable[[], T]) -> tuple[T, float]:
    start = perf_counter()
    result = call()
    return result, perf_counter() - start


def main() -> None:
    cache = ResponseCache()
    _, first_hit = cache.get_or_compute("small", "fixture", lambda: "cached result")
    _, second_hit = cache.get_or_compute("small", "fixture", lambda: "not used")
    outputs = parallel_tools({"profile": lambda: "ready", "lookup": lambda: "found"})
    print(f"route={route(2)} cache_hits={int(first_hit) + int(second_hit)} tools={len(outputs)} p95_ms={percentile([10, 20, 30, 40, 50], 95)}")


if __name__ == "__main__":
    main()
