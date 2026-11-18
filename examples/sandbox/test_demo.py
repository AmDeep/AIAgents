import subprocess

import pytest

from trusted_fixture_runner_lab.demo import run_python_fixture


def test_fixture_executes_in_temporary_working_directory():
    result = run_python_fixture("import os; print(os.path.basename(os.getcwd()).startswith('agent-lab-'))")
    assert result.returncode == 0
    assert result.stdout.strip() == "True"


def test_output_is_bounded():
    result = run_python_fixture("print('x' * 1000000)", output_limit=20)
    assert len(result.stdout) == 20
    assert result.stdout_truncated


def test_stderr_is_bounded_independently():
    result = run_python_fixture("import sys; sys.stderr.write('e' * 1000000)", output_limit=25)
    assert len(result.stderr) == 25
    assert result.stderr_truncated
    assert not result.stdout_truncated


def test_timeout_is_enforced():
    with pytest.raises(subprocess.TimeoutExpired):
        run_python_fixture("import time; time.sleep(2)", timeout_seconds=0.1)


def test_invalid_bounds_are_rejected():
    with pytest.raises(ValueError):
        run_python_fixture("print(1)", output_limit=0)
    with pytest.raises(ValueError):
        run_python_fixture("print(1)", timeout_seconds=float("inf"))
    with pytest.raises(TypeError):
        run_python_fixture(None)


def test_nonzero_exit_preserves_bounded_error_output():
    result = run_python_fixture("raise RuntimeError('fixture failure')")
    assert result.returncode != 0
    assert "RuntimeError: fixture failure" in result.stderr
