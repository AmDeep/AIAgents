import pytest

from retry_budget_lab.demo import BudgetExceeded, RunBudget, retry


def test_retries_only_transient_failures_with_capped_backoff():
    calls = 0
    waits = []

    def operation():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TimeoutError()
        return "done"

    budget = RunBudget(3, 0)
    result = retry(operation, attempts=3, base_delay=0.2, max_delay=0.25,
                   is_retryable=lambda error: isinstance(error, TimeoutError), sleep=waits.append, budget=budget)
    assert result == "done"
    assert waits == [0.2, 0.25]
    assert budget.iterations == 3


def test_non_retryable_error_is_not_replayed():
    calls = []
    with pytest.raises(ValueError):
        retry(lambda: calls.append(1) or (_ for _ in ()).throw(ValueError()), attempts=5,
              base_delay=1, max_delay=2, is_retryable=lambda _: False, sleep=lambda _: None, budget=RunBudget(5, 0))
    assert len(calls) == 1


def test_budget_exhaustion_stops_before_next_attempt():
    calls = []
    with pytest.raises(BudgetExceeded):
        retry(lambda: calls.append(1) or (_ for _ in ()).throw(TimeoutError()), attempts=5,
              base_delay=0, max_delay=0, is_retryable=lambda _: True, sleep=lambda _: None, budget=RunBudget(1, 0))
    assert len(calls) == 1


def test_cost_budget_is_charged_for_each_attempt():
    budget = RunBudget(5, 0.2)
    calls = []
    with pytest.raises(BudgetExceeded):
        retry(lambda: calls.append(1) or (_ for _ in ()).throw(TimeoutError()), attempts=4,
              base_delay=0, max_delay=0, is_retryable=lambda _: True, sleep=lambda _: None,
              budget=budget, cost_per_attempt=0.1)
    assert calls == [1, 1]
    assert budget.iterations == 2
    assert budget.cost == pytest.approx(0.2)


@pytest.mark.parametrize("arguments", [
    {"max_iterations": -1, "max_cost": 1},
    {"max_iterations": 1.5, "max_cost": 1},
    {"max_iterations": 1, "max_cost": float("nan")},
    {"max_iterations": 1, "max_cost": -1},
])
def test_invalid_run_budget_configuration_is_rejected(arguments):
    with pytest.raises(ValueError):
        RunBudget(**arguments)


@pytest.mark.parametrize("delay", [-0.1, float("inf"), float("nan")])
def test_invalid_retry_delays_are_rejected_before_operation(delay):
    calls = []
    with pytest.raises(ValueError):
        retry(lambda: calls.append(1), attempts=1, base_delay=delay, max_delay=1,
              is_retryable=lambda _: False, sleep=lambda _: None, budget=RunBudget(1, 1))
    assert calls == []


def test_injected_jitter_is_bounded_and_deterministic():
    waits = []
    calls = []

    def operation():
        calls.append(1)
        if len(calls) == 1:
            raise TimeoutError()
        return "ok"

    result = retry(operation, attempts=2, base_delay=0.4, max_delay=1,
                   is_retryable=lambda _: True, sleep=waits.append,
                   budget=RunBudget(2, 0), jitter=lambda ceiling: ceiling / 2)
    assert result == "ok"
    assert waits == [0.2]


@pytest.mark.parametrize("jitter_value", [-0.1, 0.5, float("nan")])
def test_jitter_cannot_exceed_or_invalidate_backoff(jitter_value):
    with pytest.raises(ValueError, match="jitter"):
        retry(lambda: (_ for _ in ()).throw(TimeoutError()), attempts=2, base_delay=0.2, max_delay=1,
              is_retryable=lambda _: True, sleep=lambda _: None, budget=RunBudget(2, 0),
              jitter=lambda _: jitter_value)
