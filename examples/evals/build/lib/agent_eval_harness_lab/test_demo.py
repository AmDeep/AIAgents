from agent_eval_harness_lab.demo import CASES, EvalCase, fixture_system, run_evals


def test_checked_in_regression_and_adversarial_cases_pass():
    results = run_evals(CASES, fixture_system)
    assert all(result.passed for result in results)
    assert {result.category for result in results} >= {"regression", "adversarial"}


def test_eval_runner_turns_system_exception_into_visible_failure():
    result = run_evals([EvalCase("raises", "x", "ok", "failure")], lambda _: 1 / 0)[0]
    assert not result.passed and result.actual == "error:ZeroDivisionError"


def test_unexpected_output_fails_named_case():
    result = run_evals([EvalCase("drift", "x", "expected", "regression")], lambda _: "changed")[0]
    assert not result.passed and result.name == "drift"
