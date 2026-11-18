"""Strict JSON tool boundary: reject extras and return typed error objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_DIR = Path(__file__).with_name("schemas")
INPUT_SCHEMA = json.loads((SCHEMA_DIR / "create_ticket.input.schema.json").read_text(encoding="utf-8"))
OUTPUT_SCHEMA = json.loads((SCHEMA_DIR / "create_ticket.output.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(INPUT_SCHEMA)
Draft202012Validator.check_schema(OUTPUT_SCHEMA)
INPUT_VALIDATOR = Draft202012Validator(INPUT_SCHEMA)
OUTPUT_VALIDATOR = Draft202012Validator(OUTPUT_SCHEMA)


class ToolValidationError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolValidationError(f"duplicate_key:{key}")
        result[key] = value
    return result


def parse_create_ticket(raw: str) -> dict[str, str]:
    try:
        value = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise ToolValidationError("invalid_json") from error
    errors = sorted(INPUT_VALIDATOR.iter_errors(value), key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""))
    if errors:
        error = errors[0]
        path = ".".join(map(str, error.absolute_path)) or "$"
        raise ToolValidationError(f"invalid_argument:{path}:{error.validator}")
    if not value["title"].strip():
        raise ToolValidationError("title_must_be_nonempty_string")
    return {"title": value["title"].strip(), "priority": value["priority"]}


def create_ticket_tool(raw: str) -> dict[str, Any]:
    try:
        arguments = parse_create_ticket(raw)
    except ToolValidationError as error:
        return {"ok": False, "error": str(error)}
    result: dict[str, Any] = {"ok": True, "ticket": {"id": "T-LOCAL-001", **arguments}}
    OUTPUT_VALIDATOR.validate(result)
    return result


def validate_tool_result(result: Any) -> None:
    """Validate the result envelope before it crosses back to a caller."""
    errors = sorted(OUTPUT_VALIDATOR.iter_errors(result), key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""))
    if errors:
        error = errors[0]
        path = ".".join(map(str, error.absolute_path)) or "$"
        raise ToolValidationError(f"invalid_result:{path}:{error.validator}")


def main() -> None:
    print(json.dumps(create_ticket_tool('{"title":"Check docs","priority":"normal"}'), sort_keys=True))
    print(json.dumps(create_ticket_tool('{"title":"","priority":"urgent","extra":1}'), sort_keys=True))


if __name__ == "__main__":
    main()
