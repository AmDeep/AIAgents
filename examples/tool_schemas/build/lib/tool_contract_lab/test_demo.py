import json

import pytest

from tool_contract_lab.demo import ToolValidationError, create_ticket_tool, parse_create_ticket, validate_tool_result


def test_valid_arguments_are_normalized():
    assert parse_create_ticket('{"title":"  Check docs ","priority":"high"}') == {
        "title": "Check docs", "priority": "high"
    }


@pytest.mark.parametrize("raw", [
    "not json", "[]", '{"title":"x","priority":"normal","extra":true}',
    '{"title":"","priority":"normal"}', '{"title":"x","priority":"urgent"}',
    '{"title":1,"priority":"normal"}', '{"title":"x","priority":[]}',
    '{"title":"first","title":"second","priority":"normal"}',
])
def test_invalid_arguments_are_rejected(raw):
    with pytest.raises(ToolValidationError):
        parse_create_ticket(raw)


def test_tool_returns_explicit_error_envelope():
    assert create_ticket_tool("{}") == {"ok": False, "error": "invalid_argument:$:required"}
    assert create_ticket_tool('{"title":"x","priority":"low"}') ["ok"] is True


@pytest.mark.parametrize("result", [
    {"ok": True},
    {"ok": True, "ticket": {"id": "", "title": "x", "priority": "high"}},
    {"ok": False, "error": ""},
    {"ok": False, "error": "failure", "extra": True},
])
def test_output_schema_rejects_malformed_result_envelopes(result):
    with pytest.raises(ToolValidationError, match="invalid_result"):
        validate_tool_result(result)


def test_output_schema_accepts_success_and_error_envelopes():
    validate_tool_result({"ok": True, "ticket": {"id": "T-1", "title": "A", "priority": "normal"}})
    validate_tool_result({"ok": False, "error": "invalid_json"})
