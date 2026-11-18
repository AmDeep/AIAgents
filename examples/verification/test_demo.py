from completion_verification_lab.demo import CompletionClaim, verify_completion


def test_completion_requires_all_external_postconditions():
    result = verify_completion(CompletionClaim("r", "completed"), {"saved": lambda: True, "tested": lambda: True})
    assert result.passed and result.checks == ("saved", "tested")


def test_failed_or_raising_check_prevents_success():
    result = verify_completion(CompletionClaim("r", "completed"), {
        "saved": lambda: True,
        "tested": lambda: False,
        "readback": lambda: (_ for _ in ()).throw(OSError()),
    })
    assert not result.passed
    assert result.failures == ("tested", "readback")


def test_no_checks_cannot_verify_completion():
    assert not verify_completion(CompletionClaim("r", "completed"), {}).passed


def test_missing_completion_claim_fails_closed():
    result = verify_completion(CompletionClaim("r", "running"), {"saved": lambda: True})
    assert result.failures == ("agent_did_not_claim_completion",)
