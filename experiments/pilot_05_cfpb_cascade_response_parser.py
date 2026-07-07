#!/usr/bin/env python
"""
Pilot 05 CFPB cascade response parser/validator scaffold.

This module defines the structured response contract for future approved model
runs. It does not call any model or API, does not read raw CFPB data, and does
not write raw responses.

Future execution code should store only sanitized parsed fields and validation
status, not raw model responses.
"""

from __future__ import annotations

import json
from typing import Any


SCHEMA_VERSION = "pilot_05_cfpb_cascade_v1"

STAGES = {
    "decision": {
        "required": [
            "schema_version",
            "stage_name",
            "evidence_state_id",
            "packet_id",
            "condition_name",
            "predicted_process_outcome",
            "confidence_bin",
            "evidence_sufficiency",
            "decision_reason_codes",
            "parse_safety",
        ],
        "enums": {
            "predicted_process_outcome": ["Yes", "No", "insufficient_evidence"],
            "confidence_bin": ["low", "medium", "high"],
            "evidence_sufficiency": ["sufficient", "partial", "insufficient"],
        },
        "list_enums": {
            "decision_reason_codes": [
                "product_signal",
                "issue_signal",
                "submission_channel_signal",
                "temporal_signal",
                "narrative_availability_signal",
                "field_dropout_uncertainty",
                "conflicting_signal_uncertainty",
                "insufficient_evidence",
            ],
        },
    },
    "audit": {
        "required": [
            "schema_version",
            "stage_name",
            "evidence_state_id",
            "packet_id",
            "condition_name",
            "audit_outcome",
            "audit_confidence_bin",
            "detected_risk_codes",
            "recommended_action",
            "parse_safety",
        ],
        "enums": {
            "audit_outcome": ["pass", "fail", "escalate"],
            "audit_confidence_bin": ["low", "medium", "high"],
            "recommended_action": ["accept_decision", "request_escalation", "withhold_output"],
        },
        "list_enums": {
            "detected_risk_codes": [
                "none",
                "insufficient_evidence",
                "low_confidence",
                "condition_degradation",
                "conflicting_signal",
                "schema_concern",
            ],
        },
    },
    "escalation": {
        "required": [
            "schema_version",
            "stage_name",
            "evidence_state_id",
            "packet_id",
            "condition_name",
            "escalation_decision",
            "final_answer_status",
            "escalation_reason_codes",
            "parse_safety",
        ],
        "enums": {
            "escalation_decision": ["no_escalation", "escalate_for_review", "withhold_output"],
            "final_answer_status": ["usable", "uncertain", "invalid"],
        },
        "list_enums": {
            "escalation_reason_codes": [
                "none",
                "audit_failed",
                "insufficient_evidence",
                "conflicting_signal",
                "low_confidence",
                "condition_degradation",
                "schema_concern",
            ],
        },
    },
}

FORBIDDEN_FREE_TEXT_KEYS = {
    "rationale",
    "explanation",
    "chain_of_thought",
    "reasoning",
    "raw_response",
    "raw_prompt",
    "prompt",
    "full_text",
    "verbatim",
}

REQUIRED_PARSE_SAFETY = {
    "raw_personal_data_in_response": False,
    "raw_prompt_repeated": False,
    "target_label_claimed_seen": False,
}


def parse_json_object(raw_text: str) -> tuple[dict[str, Any] | None, list[str]]:
    """
    Parse a raw response string into a JSON object.

    This function returns validation errors but does not write or persist the raw
    response. Future execution code should call this function in memory and then
    discard raw_text after extracting sanitized fields.
    """
    errors: list[str] = []

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return None, [f"json_decode_error:{exc.msg}"]

    if not isinstance(parsed, dict):
        return None, ["parsed_response_not_object"]

    return parsed, errors


def validate_response(
    payload: dict[str, Any],
    *,
    expected_stage_name: str,
    expected_evidence_state_id: str | None = None,
    expected_packet_id: str | None = None,
    expected_condition_name: str | None = None,
) -> dict[str, Any]:
    """
    Validate and sanitize a parsed response object.

    Returns a sanitized validation record. It does not include raw text.
    """
    errors: list[str] = []

    if expected_stage_name not in STAGES:
        raise ValueError(f"Unknown expected stage: {expected_stage_name}")

    schema = STAGES[expected_stage_name]

    for key in payload:
        if str(key).lower() in FORBIDDEN_FREE_TEXT_KEYS:
            errors.append(f"forbidden_free_text_key:{key}")

    for required_key in schema["required"]:
        if required_key not in payload:
            errors.append(f"missing_required_key:{required_key}")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("invalid_schema_version")

    if payload.get("stage_name") != expected_stage_name:
        errors.append("stage_name_mismatch")

    if expected_evidence_state_id is not None and payload.get("evidence_state_id") != expected_evidence_state_id:
        errors.append("evidence_state_id_mismatch")

    if expected_packet_id is not None and payload.get("packet_id") != expected_packet_id:
        errors.append("packet_id_mismatch")

    if expected_condition_name is not None and payload.get("condition_name") != expected_condition_name:
        errors.append("condition_name_mismatch")

    for field_name, allowed_values in schema["enums"].items():
        if field_name in payload and payload[field_name] not in allowed_values:
            errors.append(f"invalid_enum:{field_name}")

    for field_name, allowed_values in schema["list_enums"].items():
        values = payload.get(field_name)
        if values is None:
            continue

        if not isinstance(values, list):
            errors.append(f"not_list:{field_name}")
            continue

        for value in values:
            if value not in allowed_values:
                errors.append(f"invalid_list_enum:{field_name}:{value}")

    parse_safety = payload.get("parse_safety")
    if not isinstance(parse_safety, dict):
        errors.append("missing_or_invalid_parse_safety")
    else:
        for field_name, expected_value in REQUIRED_PARSE_SAFETY.items():
            if parse_safety.get(field_name) is not expected_value:
                errors.append(f"parse_safety_violation:{field_name}")

    sanitized_record = {
        "schema_version": payload.get("schema_version", ""),
        "stage_name": payload.get("stage_name", ""),
        "evidence_state_id": payload.get("evidence_state_id", ""),
        "packet_id": payload.get("packet_id", ""),
        "condition_name": payload.get("condition_name", ""),
        "parse_status": "PASS" if not errors else "FAIL",
        "validation_error_count": len(errors),
        "validation_errors": "|".join(errors),
    }

    for field_name in schema["enums"]:
        sanitized_record[field_name] = payload.get(field_name, "")

    for field_name in schema["list_enums"]:
        values = payload.get(field_name, [])
        if isinstance(values, list):
            sanitized_record[field_name] = "|".join(str(value) for value in values)
        else:
            sanitized_record[field_name] = ""

    return sanitized_record


def response_contract_summary() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stages": list(STAGES.keys()),
        "raw_response_storage_allowed": False,
        "raw_prompt_storage_allowed": False,
        "sanitized_parsed_fields_only": True,
    }
