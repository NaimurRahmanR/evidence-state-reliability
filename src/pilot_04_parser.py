from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from src.pilot_04_prompts import (
    AUDIT_EXPECTED_JSON_KEYS,
    DECISION_EXPECTED_JSON_KEYS,
    ESCALATION_EXPECTED_JSON_KEYS,
)


PILOT_04_PARSER_VERSION = "pilot_04_parser_v1"

ALLOWED_DECISION_LABELS = {"approve", "review", "decline"}
ALLOWED_ESCALATION_LABELS = {"no_escalation", "soft_escalation", "mandatory_escalation"}


@dataclass(frozen=True)
class Pilot04ParsedRecord:
    """Parsed structured output with validation metadata."""

    parser_version: str
    stage: str
    task_id: str
    condition: str
    parsed: dict[str, Any]
    schema_valid: bool
    errors: list[str]


def _load_json_object(text_or_object: str | dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    if isinstance(text_or_object, dict):
        return dict(text_or_object), []

    if not isinstance(text_or_object, str):
        return None, [f"Expected JSON text or dict, got {type(text_or_object).__name__}."]

    try:
        loaded = json.loads(text_or_object)
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON: {exc.msg} at position {exc.pos}."]

    if not isinstance(loaded, dict):
        return None, ["Expected a JSON object."]

    return loaded, []


def _check_exact_keys(parsed: dict[str, Any], expected_keys: list[str]) -> list[str]:
    errors: list[str] = []
    expected = set(expected_keys)
    actual = set(parsed.keys())

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    if missing:
        errors.append("Missing keys: " + ", ".join(missing))
    if extra:
        errors.append("Unexpected keys: " + ", ".join(extra))

    return errors


def _check_task_condition(parsed: dict[str, Any], task_id: str, condition: str) -> list[str]:
    errors: list[str] = []

    if parsed.get("task_id") != task_id:
        errors.append(f"task_id mismatch: {parsed.get('task_id')!r} != {task_id!r}")

    if parsed.get("condition") != condition:
        errors.append(f"condition mismatch: {parsed.get('condition')!r} != {condition!r}")

    return errors


def _check_bool(parsed: dict[str, Any], key: str) -> list[str]:
    if isinstance(parsed.get(key), bool):
        return []
    return [f"{key} must be boolean."]


def _check_number_range(parsed: dict[str, Any], key: str) -> list[str]:
    value = parsed.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return [f"{key} must be a number between 0 and 1."]

    if not 0 <= float(value) <= 1:
        return [f"{key} must be between 0 and 1."]

    return []


def _check_non_negative_int(parsed: dict[str, Any], key: str) -> list[str]:
    value = parsed.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return [f"{key} must be a non-negative integer."]

    if value < 0:
        return [f"{key} must be a non-negative integer."]

    return []


def _check_string(parsed: dict[str, Any], key: str) -> list[str]:
    value = parsed.get(key)
    if isinstance(value, str) and value.strip():
        return []
    return [f"{key} must be a non-empty string."]


def _check_string_list(parsed: dict[str, Any], key: str) -> list[str]:
    value = parsed.get(key)
    if not isinstance(value, list):
        return [f"{key} must be a list of strings."]

    if not all(isinstance(item, str) and item.strip() for item in value):
        return [f"{key} must contain only non-empty strings."]

    return []


def _make_record(
    *,
    stage: str,
    task_id: str,
    condition: str,
    parsed: dict[str, Any] | None,
    errors: list[str],
) -> Pilot04ParsedRecord:
    parsed_object = {} if parsed is None else parsed

    return Pilot04ParsedRecord(
        parser_version=PILOT_04_PARSER_VERSION,
        stage=stage,
        task_id=task_id,
        condition=condition,
        parsed=parsed_object,
        schema_valid=len(errors) == 0,
        errors=errors,
    )


def parse_decision_output(
    text_or_object: str | dict[str, Any],
    *,
    task_id: str,
    condition: str,
) -> Pilot04ParsedRecord:
    """Parse and validate a Pilot 04 decision-stage structured output."""
    parsed, errors = _load_json_object(text_or_object)
    if parsed is None:
        return _make_record(stage="decision", task_id=task_id, condition=condition, parsed=None, errors=errors)

    errors.extend(_check_exact_keys(parsed, DECISION_EXPECTED_JSON_KEYS))
    errors.extend(_check_task_condition(parsed, task_id, condition))

    decision_label = parsed.get("decision_label")
    if decision_label not in ALLOWED_DECISION_LABELS:
        errors.append(f"decision_label must be one of {sorted(ALLOWED_DECISION_LABELS)}.")

    errors.extend(_check_number_range(parsed, "confidence"))
    errors.extend(_check_string_list(parsed, "primary_evidence_used"))
    errors.extend(_check_bool(parsed, "missing_evidence_acknowledged"))
    errors.extend(_check_string_list(parsed, "risk_flags_identified"))
    errors.extend(_check_string(parsed, "decision_rationale_summary"))

    return _make_record(stage="decision", task_id=task_id, condition=condition, parsed=parsed, errors=errors)


def parse_audit_output(
    text_or_object: str | dict[str, Any],
    *,
    task_id: str,
    condition: str,
) -> Pilot04ParsedRecord:
    """Parse and validate a Pilot 04 audit-stage structured output."""
    parsed, errors = _load_json_object(text_or_object)
    if parsed is None:
        return _make_record(stage="audit", task_id=task_id, condition=condition, parsed=None, errors=errors)

    errors.extend(_check_exact_keys(parsed, AUDIT_EXPECTED_JSON_KEYS))
    errors.extend(_check_task_condition(parsed, task_id, condition))
    errors.extend(_check_bool(parsed, "audit_pass"))
    errors.extend(_check_number_range(parsed, "evidence_alignment_score"))
    errors.extend(_check_non_negative_int(parsed, "unsupported_claim_count"))
    errors.extend(_check_non_negative_int(parsed, "missed_key_evidence_count"))
    errors.extend(_check_string(parsed, "audit_notes_summary"))

    return _make_record(stage="audit", task_id=task_id, condition=condition, parsed=parsed, errors=errors)


def parse_escalation_output(
    text_or_object: str | dict[str, Any],
    *,
    task_id: str,
    condition: str,
) -> Pilot04ParsedRecord:
    """Parse and validate a Pilot 04 escalation-stage structured output."""
    parsed, errors = _load_json_object(text_or_object)
    if parsed is None:
        return _make_record(stage="escalation", task_id=task_id, condition=condition, parsed=None, errors=errors)

    errors.extend(_check_exact_keys(parsed, ESCALATION_EXPECTED_JSON_KEYS))
    errors.extend(_check_task_condition(parsed, task_id, condition))

    escalation_label = parsed.get("escalation_label")
    if escalation_label not in ALLOWED_ESCALATION_LABELS:
        errors.append(f"escalation_label must be one of {sorted(ALLOWED_ESCALATION_LABELS)}.")

    errors.extend(_check_string(parsed, "escalation_reason"))
    errors.extend(_check_bool(parsed, "requires_human_review"))
    errors.extend(_check_number_range(parsed, "escalation_confidence"))

    return _make_record(stage="escalation", task_id=task_id, condition=condition, parsed=parsed, errors=errors)


def parsed_record_to_flat_row(record: Pilot04ParsedRecord) -> dict[str, Any]:
    """Flatten a parsed record for sanitized CSV export."""
    return {
        "parser_version": record.parser_version,
        "stage": record.stage,
        "task_id": record.task_id,
        "condition": record.condition,
        "schema_valid": record.schema_valid,
        "n_errors": len(record.errors),
        "errors": json.dumps(record.errors, ensure_ascii=False),
        "parsed_json": json.dumps(record.parsed, ensure_ascii=False, sort_keys=True),
    }


def assert_schema_valid(record: Pilot04ParsedRecord) -> None:
    """Raise ValueError if a parsed record is not schema-valid."""
    if not record.schema_valid:
        raise ValueError(f"Invalid Pilot 04 {record.stage} output for {record.task_id}/{record.condition}: {record.errors}")
