"""Bounded retry loop with explicit retryability and injectable sleeping."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, TypeVar

T = TypeVar("T")


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class RunBudget:
    max_iterations: int
    max_cost: float
    iterations: int = 0
    cost: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.max_iterations, bool) or not isinstance(self.max_iterations, int) or self.max_iterations < 0:
            raise ValueError("max_iterations must be a nonnegative integer")
        if not math.isfinite(self.max_cost) or self.max_cost < 0:
            raise ValueError("max_cost must be finite and nonnegative")
        if not 0 <= self.iterations <= self.max_iterations:
            raise ValueError("iterations must be within the configured budget")
        if not math.isfinite(self.cost) or not 0 <= self.cost <= self.max_cost:
            raise ValueError("cost must be within the configured budget")

    def consume(self, cost: float = 0.0) -> None:
        if not math.isfinite(cost) or cost < 0:
            raise ValueError("attempt cost must be finite and nonnegative")
        if self.iterations + 1 > self.max_iterations or self.cost + cost > self.max_cost:
            raise BudgetExceeded("run budget exhausted")
        self.iterations += 1
        self.cost += cost


def retry(
    operation: Callable[[], T], *, attempts: int, base_delay: float, max_delay: float,
    is_retryable: Callable[[Exception], bool], sleep: Callable[[float], None], budget: RunBudget,
    cost_per_attempt: float = 0.0,
    jitter: Callable[[float], float] | None = None,
) -> T:
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError("attempts must be at least one")
    if not math.isfinite(base_delay) or base_delay < 0 or not math.isfinite(max_delay) or max_delay < 0:
        raise ValueError("delays must be finite and nonnegative")
    if not math.isfinite(cost_per_attempt) or cost_per_attempt < 0:
        raise ValueError("cost_per_attempt must be finite and nonnegative")
    delay = min(base_delay, max_delay)
    for attempt in range(attempts):
        budget.consume(cost_per_attempt)
        try:
            return operation()
        except Exception as error:
            if attempt + 1 >= attempts or not is_retryable(error):
                raise
            wait = jitter(delay) if jitter is not None else delay
            if not math.isfinite(wait) or wait < 0 or wait > delay:
                raise ValueError("jitter must return a finite delay between zero and the backoff ceiling")
            sleep(wait)
            delay = min(delay * 2, max_delay)
    raise AssertionError("unreachable")


def main() -> None:
    budget = RunBudget(max_iterations=4, max_cost=1.0)
    tries = 0

    def flaky() -> str:
        nonlocal tries
        tries += 1
        if tries < 3:
            raise TimeoutError("transient")
        return "ok"

    waits: list[float] = []
    result = retry(flaky, attempts=3, base_delay=0.1, max_delay=1.0,
                   is_retryable=lambda error: isinstance(error, TimeoutError), sleep=waits.append, budget=budget)
    print(f"result={result} attempts={budget.iterations} waits={waits}")


if __name__ == "__main__":
    main()
