from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from src.pilot_03_llm_client import Pilot03LLMCallRecord


PILOT_03_PARSER_VERSION = "pilot_03_parser_v1"

DECISION_STAGE = "decision"
AUDIT_STAGE = "audit"
ESCALATION_STAGE = "escalation"

VALID_DECISIONS = {"approve", "reject"}
VALID_STAGES = {DECISION_STAGE, AUDIT_STAGE, ESCALATION_STAGE}


@dataclass(frozen=True)
class Pilot03ParsedResponse:
    """Parsed and validated response for one Pilot 03 call record."""

    call_id: str
    task_id: str
    stage: str
    parser_version: str
    raw_response_text: str
    parsed_response: dict[str, Any]
    valid_json: bool
    valid_schema: bool
    errors: list[str]


def parse_json_response(raw_response_text: str) -> tuple[dict[str, Any], bool, list[str]]:
    """Parse a raw model response as JSON."""
    errors: list[str] = []

    try:
        parsed = json.loads(raw_response_text)
    except json.JSONDecodeError as exc:
        return {}, False, [f"invalid_json: {exc.msg}"]

    if not isinstance(parsed, dict):
        errors.append(f"json_not_object: expected dict, got {type(parsed).__name__}")
        return {}, True, errors

    return parsed, True, errors


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_number_between_zero_and_one(value: Any) -> bool:
    if not isinstance(value, (int, float)):
        return False

    return 0.0 <= float(value) <= 1.0


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_final_decision(value: Any, field_name: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field_name}_not_string")
        return

    if value.lower() not in VALID_DECISIONS:
        errors.append(f"{field_name}_invalid: {value}")


def validate_decision_response(parsed_response: dict[str, Any]) -> list[str]:
    """Validate a decision-stage response schema."""
    errors: list[str] = []

    _validate_final_decision(parsed_response.get("final_decision"), "final_decision", errors)

    if not _is_number_between_zero_and_one(parsed_response.get("confidence")):
        errors.append("confidence_missing_or_out_of_range")

    if not _is_string_list(parsed_response.get("used_evidence_unit_ids")):
        errors.append("used_evidence_unit_ids_not_string_list")

    if not _non_empty_string(parsed_response.get("reason")):
        errors.append("reason_missing_or_empty")

    return errors


def validate_audit_response(parsed_response: dict[str, Any]) -> list[str]:
    """Validate an audit-stage response schema."""
    errors: list[str] = []

    if not _is_bool(parsed_response.get("audit_passed")):
        errors.append("audit_passed_not_bool")

    if not _is_bool(parsed_response.get("detected_issue")):
        errors.append("detected_issue_not_bool")

    _validate_final_decision(parsed_response.get("supported_decision"), "supported_decision", errors)

    if not _is_string_list(parsed_response.get("missing_or_conflicting_evidence_unit_ids")):
        errors.append("missing_or_conflicting_evidence_unit_ids_not_string_list")

    if not _non_empty_string(parsed_response.get("reason")):
        errors.append("reason_missing_or_empty")

    return errors


def validate_escalation_response(parsed_response: dict[str, Any]) -> list[str]:
    """Validate an escalation-stage response schema."""
    errors = validate_decision_response(parsed_response)

    if not _is_bool(parsed_response.get("overrode_previous_stage")):
        errors.append("overrode_previous_stage_not_bool")

    return errors


def validate_response_for_stage(stage: str, parsed_response: dict[str, Any]) -> list[str]:
    """Validate a parsed response based on the pipeline stage."""
    if stage not in VALID_STAGES:
        return [f"unknown_stage: {stage}"]

    if stage == DECISION_STAGE:
        return validate_decision_response(parsed_response)

    if stage == AUDIT_STAGE:
        return validate_audit_response(parsed_response)

    if stage == ESCALATION_STAGE:
        return validate_escalation_response(parsed_response)

    return [f"unknown_stage: {stage}"]


def parse_and_validate_raw_response(
    *,
    call_id: str,
    task_id: str,
    stage: str,
    raw_response_text: str,
) -> Pilot03ParsedResponse:
    """Parse and validate one raw response."""
    parsed_response, valid_json, parse_errors = parse_json_response(raw_response_text)
    schema_errors = validate_response_for_stage(stage, parsed_response) if valid_json else []

    errors = parse_errors + schema_errors

    return Pilot03ParsedResponse(
        call_id=call_id,
        task_id=task_id,
        stage=stage,
        parser_version=PILOT_03_PARSER_VERSION,
        raw_response_text=raw_response_text,
        parsed_response=parsed_response,
        valid_json=valid_json,
        valid_schema=valid_json and not schema_errors and not parse_errors,
        errors=errors,
    )


def parse_and_validate_call_record(record: Pilot03LLMCallRecord) -> Pilot03ParsedResponse:
    """Parse and validate one Pilot 03 LLM call record."""
    return parse_and_validate_raw_response(
        call_id=record.call_id,
        task_id=record.task_id,
        stage=record.stage,
        raw_response_text=record.raw_response_text,
    )


def parse_and_validate_call_records(records: list[Pilot03LLMCallRecord]) -> list[Pilot03ParsedResponse]:
    """Parse and validate multiple Pilot 03 LLM call records."""
    return [parse_and_validate_call_record(record) for record in records]


def parsed_response_to_dict(parsed_response: Pilot03ParsedResponse) -> dict[str, Any]:
    """Convert a parsed response object into a dictionary."""
    return asdict(parsed_response)


def parsed_responses_to_dicts(parsed_responses: list[Pilot03ParsedResponse]) -> list[dict[str, Any]]:
    """Convert parsed responses into dictionaries."""
    return [parsed_response_to_dict(parsed_response) for parsed_response in parsed_responses]


def summarise_parsed_responses(parsed_responses: list[Pilot03ParsedResponse]) -> dict[str, Any]:
    """Return a compact parser/validation summary."""
    stage_counts = Counter(parsed.stage for parsed in parsed_responses)
    valid_json_counts = Counter(str(parsed.valid_json) for parsed in parsed_responses)
    valid_schema_counts = Counter(str(parsed.valid_schema) for parsed in parsed_responses)

    error_counts: Counter[str] = Counter()
    for parsed in parsed_responses:
        for error in parsed.errors:
            error_counts[error] += 1

    return {
        "parser_version": PILOT_03_PARSER_VERSION,
        "n_parsed_responses": len(parsed_responses),
        "stage_counts": dict(stage_counts),
        "valid_json_counts": dict(valid_json_counts),
        "valid_schema_counts": dict(valid_schema_counts),
        "n_invalid_json": sum(1 for parsed in parsed_responses if not parsed.valid_json),
        "n_invalid_schema": sum(1 for parsed in parsed_responses if not parsed.valid_schema),
        "error_counts": dict(error_counts),
    }


def assert_all_responses_valid(parsed_responses: list[Pilot03ParsedResponse]) -> None:
    """
    Raise an error if any response fails JSON parsing or schema validation.

    This is useful for smoke tests. In later real LLM runs, we may choose to log
    invalid responses instead of stopping immediately.
    """
    invalid = [parsed for parsed in parsed_responses if not parsed.valid_schema]

    if invalid:
        preview = "; ".join(
            f"{parsed.call_id}/{parsed.stage}: {parsed.errors}" for parsed in invalid[:5]
        )
        raise AssertionError(f"{len(invalid)} Pilot 03 responses failed validation. First errors: {preview}")


if __name__ == "__main__":
    from experiments.pilot_03_dry_run_runner import flatten_call_records, run_pilot_03_dry_run

    results = run_pilot_03_dry_run(n_tasks=2)
    call_records = flatten_call_records(results)
    parsed = parse_and_validate_call_records(call_records)

    print("Pilot 03 parser smoke test")
    print("==========================")
    print(summarise_parsed_responses(parsed))
    assert_all_responses_valid(parsed)
    print("all_responses_valid: True")