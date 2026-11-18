import pytest

from authorization_boundary_lab.demo import AccessDenied, Action, Policy, guarded_operation


def test_allowed_action_loads_credential_and_runs():
    policy = Policy(frozenset({Action.READ_FIXTURE}))
    assert guarded_operation(Action.READ_FIXTURE, policy, lambda: "fixture-token", lambda token: token) == "fixture-token"


def test_denial_happens_before_credential_access():
    calls = []
    with pytest.raises(AccessDenied):
        guarded_operation(Action.WRITE_PRODUCTION, Policy(frozenset()), lambda: calls.append("secret") or "", lambda _: "")
    assert calls == []


def test_policy_does_not_infer_permission_from_related_action():
    policy = Policy(frozenset({Action.READ_FIXTURE, Action.WRITE_FIXTURE}))
    assert policy.authorize(Action.WRITE_PRODUCTION) is False


def test_credential_loader_failure_does_not_run_operation():
    operations = []

    def fail_to_load():
        raise RuntimeError("credential provider unavailable")

    with pytest.raises(RuntimeError, match="credential provider unavailable"):
        guarded_operation(Action.READ_FIXTURE, Policy(frozenset({Action.READ_FIXTURE})),
                          fail_to_load, lambda credential: operations.append(credential))
    assert operations == []
