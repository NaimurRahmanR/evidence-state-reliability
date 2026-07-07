#!/usr/bin/env python
"""
Pilot 05 CFPB cascade parser smoke test.

This script tests the committed Pilot 05 CFPB cascade response parser using
synthetic in-memory response objects only.

It does not call any model or API. It does not write raw responses, raw prompt
instances, raw evidence text, or raw CFPB data. It writes only sanitized
validation records and aggregate smoke-test summaries.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "pilot_05_cfpb_cascade_v1"

EXPECTED_COUNTS = {
    "test_cases": 18,
    "valid_cases": 3,
    "invalid_cases": 15,
    "stages": {
        "decision": 6,
        "audit": 6,
        "escalation": 6,
    },
}

FORBIDDEN_OUTPUT_PATTERNS = [
    "raw " + "response " + "text",
    "raw " + "prompt " + "text",
    "chain " + "of " + "thought",
    "I " + "think",
    "because " + "I",
    "Consumer " + "complaint " + "narrative",
    "Complaint " + "ID",
    "ZIP " + "code",
    "XX/" + "XX/" + "XXXX",
    "XXXX " + "XXXX",
    "{" + "$",
    "sk" + "-",
    "BEGIN " + "PRIVATE " + "KEY",
]

EXPECTED_INVALID_ERROR_MARKERS = {
    "decision_invalid_raw_prompt_key": "forbidden_free_text_key:raw_prompt",
    "decision_invalid_raw_response_key": "forbidden_free_text_key:raw_response",
    "decision_invalid_chain_of_thought_key": "forbidden_free_text_key:chain_of_thought",
    "decision_invalid_schema_version": "invalid_schema_version",
    "decision_invalid_enum_value": "invalid_enum:predicted_process_outcome",
    "audit_invalid_rationale_key": "forbidden_free_text_key:rationale",
    "audit_invalid_stage_name": "stage_name_mismatch",
    "audit_invalid_enum_value": "invalid_enum:audit_outcome",
    "audit_invalid_list_enum": "invalid_list_enum:detected_risk_codes:unsafe_free_text",
    "audit_invalid_parse_safety": "parse_safety_violation:raw_prompt_repeated",
    "escalation_invalid_explanation_key": "forbidden_free_text_key:explanation",
    "escalation_invalid_schema_concern": "invalid_schema_version",
    "escalation_invalid_enum_value": "invalid_enum:final_answer_status",
    "escalation_invalid_evidence_state_id": "evidence_state_id_mismatch",
    "escalation_invalid_packet_id": "packet_id_mismatch",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run no-call parser smoke tests for Pilot 05 CFPB cascade parser."
    )
    parser.add_argument("--parser-script", required=True, type=Path)
    parser.add_argument("--scaffold-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def load_parser_module(parser_script: Path) -> Any:
    module_name = "pilot_05_cfpb_cascade_response_parser_runtime"
    spec = importlib.util.spec_from_file_location(module_name, parser_script)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load parser module from {parser_script}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def base_parse_safety() -> dict[str, bool]:
    return {
        "raw_personal_data_in_response": False,
        "raw_prompt_repeated": False,
        "target_label_claimed_seen": False,
    }


def valid_decision_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage_name": "decision",
        "evidence_state_id": "P05_SYNTH_ES_001_clean",
        "packet_id": "P05_SYNTH_PKT_001",
        "condition_name": "clean",
        "predicted_process_outcome": "Yes",
        "confidence_bin": "medium",
        "evidence_sufficiency": "sufficient",
        "decision_reason_codes": ["product_signal", "issue_signal"],
        "parse_safety": base_parse_safety(),
    }


def valid_audit_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage_name": "audit",
        "evidence_state_id": "P05_SYNTH_ES_001_clean",
        "packet_id": "P05_SYNTH_PKT_001",
        "condition_name": "clean",
        "audit_outcome": "pass",
        "audit_confidence_bin": "medium",
        "detected_risk_codes": ["none"],
        "recommended_action": "accept_decision",
        "parse_safety": base_parse_safety(),
    }


def valid_escalation_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage_name": "escalation",
        "evidence_state_id": "P05_SYNTH_ES_001_clean",
        "packet_id": "P05_SYNTH_PKT_001",
        "condition_name": "clean",
        "escalation_decision": "no_escalation",
        "final_answer_status": "usable",
        "escalation_reason_codes": ["none"],
        "parse_safety": base_parse_safety(),
    }


def make_test_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    decision_valid = valid_decision_payload()
    audit_valid = valid_audit_payload()
    escalation_valid = valid_escalation_payload()

    cases.append(
        {
            "case_id": "decision_valid_control",
            "stage_name": "decision",
            "payload": deepcopy(decision_valid),
            "expected_parse_status": "PASS",
            "expected_error_marker": "",
            "expected_error_family": "none",
        }
    )

    raw_prompt_case = deepcopy(decision_valid)
    raw_prompt_case["raw_prompt"] = "blocked_field_placeholder_a"
    cases.append(
        {
            "case_id": "decision_invalid_raw_prompt_key",
            "stage_name": "decision",
            "payload": raw_prompt_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "forbidden_free_text_key:raw_prompt",
            "expected_error_family": "forbidden_free_text_key",
        }
    )

    raw_response_case = deepcopy(decision_valid)
    raw_response_case["raw_response"] = "blocked_field_placeholder_b"
    cases.append(
        {
            "case_id": "decision_invalid_raw_response_key",
            "stage_name": "decision",
            "payload": raw_response_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "forbidden_free_text_key:raw_response",
            "expected_error_family": "forbidden_free_text_key",
        }
    )

    cot_case = deepcopy(decision_valid)
    cot_case["chain_of_thought"] = "blocked_field_placeholder_c"
    cases.append(
        {
            "case_id": "decision_invalid_chain_of_thought_key",
            "stage_name": "decision",
            "payload": cot_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "forbidden_free_text_key:chain_of_thought",
            "expected_error_family": "forbidden_free_text_key",
        }
    )

    bad_schema_case = deepcopy(decision_valid)
    bad_schema_case["schema_version"] = "wrong_schema"
    cases.append(
        {
            "case_id": "decision_invalid_schema_version",
            "stage_name": "decision",
            "payload": bad_schema_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "invalid_schema_version",
            "expected_error_family": "schema_mismatch",
        }
    )

    bad_decision_enum_case = deepcopy(decision_valid)
    bad_decision_enum_case["predicted_process_outcome"] = "maybe"
    cases.append(
        {
            "case_id": "decision_invalid_enum_value",
            "stage_name": "decision",
            "payload": bad_decision_enum_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "invalid_enum:predicted_process_outcome",
            "expected_error_family": "enum_violation",
        }
    )

    cases.append(
        {
            "case_id": "audit_valid_control",
            "stage_name": "audit",
            "payload": deepcopy(audit_valid),
            "expected_parse_status": "PASS",
            "expected_error_marker": "",
            "expected_error_family": "none",
        }
    )

    rationale_case = deepcopy(audit_valid)
    rationale_case["rationale"] = "blocked_field_placeholder_d"
    cases.append(
        {
            "case_id": "audit_invalid_rationale_key",
            "stage_name": "audit",
            "payload": rationale_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "forbidden_free_text_key:rationale",
            "expected_error_family": "forbidden_free_text_key",
        }
    )

    bad_stage_case = deepcopy(audit_valid)
    bad_stage_case["stage_name"] = "decision"
    cases.append(
        {
            "case_id": "audit_invalid_stage_name",
            "stage_name": "audit",
            "payload": bad_stage_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "stage_name_mismatch",
            "expected_error_family": "stage_mismatch",
        }
    )

    bad_audit_enum_case = deepcopy(audit_valid)
    bad_audit_enum_case["audit_outcome"] = "approve"
    cases.append(
        {
            "case_id": "audit_invalid_enum_value",
            "stage_name": "audit",
            "payload": bad_audit_enum_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "invalid_enum:audit_outcome",
            "expected_error_family": "enum_violation",
        }
    )

    bad_audit_list_enum_case = deepcopy(audit_valid)
    bad_audit_list_enum_case["detected_risk_codes"] = ["unsafe_free_text"]
    cases.append(
        {
            "case_id": "audit_invalid_list_enum",
            "stage_name": "audit",
            "payload": bad_audit_list_enum_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "invalid_list_enum:detected_risk_codes:unsafe_free_text",
            "expected_error_family": "list_enum_violation",
        }
    )

    bad_parse_safety_case = deepcopy(audit_valid)
    bad_parse_safety_case["parse_safety"]["raw_prompt_repeated"] = True
    cases.append(
        {
            "case_id": "audit_invalid_parse_safety",
            "stage_name": "audit",
            "payload": bad_parse_safety_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "parse_safety_violation:raw_prompt_repeated",
            "expected_error_family": "parse_safety_violation",
        }
    )

    cases.append(
        {
            "case_id": "escalation_valid_control",
            "stage_name": "escalation",
            "payload": deepcopy(escalation_valid),
            "expected_parse_status": "PASS",
            "expected_error_marker": "",
            "expected_error_family": "none",
        }
    )

    explanation_case = deepcopy(escalation_valid)
    explanation_case["explanation"] = "blocked_field_placeholder_e"
    cases.append(
        {
            "case_id": "escalation_invalid_explanation_key",
            "stage_name": "escalation",
            "payload": explanation_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "forbidden_free_text_key:explanation",
            "expected_error_family": "forbidden_free_text_key",
        }
    )

    bad_escalation_schema_case = deepcopy(escalation_valid)
    bad_escalation_schema_case["schema_version"] = "wrong_schema"
    cases.append(
        {
            "case_id": "escalation_invalid_schema_concern",
            "stage_name": "escalation",
            "payload": bad_escalation_schema_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "invalid_schema_version",
            "expected_error_family": "schema_mismatch",
        }
    )

    bad_final_status_case = deepcopy(escalation_valid)
    bad_final_status_case["final_answer_status"] = "approved"
    cases.append(
        {
            "case_id": "escalation_invalid_enum_value",
            "stage_name": "escalation",
            "payload": bad_final_status_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "invalid_enum:final_answer_status",
            "expected_error_family": "enum_violation",
        }
    )

    bad_evidence_id_case = deepcopy(escalation_valid)
    bad_evidence_id_case["evidence_state_id"] = "P05_SYNTH_ES_WRONG"
    cases.append(
        {
            "case_id": "escalation_invalid_evidence_state_id",
            "stage_name": "escalation",
            "payload": bad_evidence_id_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "evidence_state_id_mismatch",
            "expected_error_family": "identifier_mismatch",
        }
    )

    bad_packet_id_case = deepcopy(escalation_valid)
    bad_packet_id_case["packet_id"] = "P05_SYNTH_PKT_WRONG"
    cases.append(
        {
            "case_id": "escalation_invalid_packet_id",
            "stage_name": "escalation",
            "payload": bad_packet_id_case,
            "expected_parse_status": "FAIL",
            "expected_error_marker": "packet_id_mismatch",
            "expected_error_family": "identifier_mismatch",
        }
    )

    return cases


def expected_identifiers_for_stage(stage_name: str) -> dict[str, str]:
    return {
        "expected_stage_name": stage_name,
        "expected_evidence_state_id": "P05_SYNTH_ES_001_clean",
        "expected_packet_id": "P05_SYNTH_PKT_001",
        "expected_condition_name": "clean",
    }


def sanitize_validation_record(
    *,
    case: dict[str, Any],
    parser_record: dict[str, Any],
) -> dict[str, Any]:
    validation_errors = str(parser_record.get("validation_errors", ""))
    expected_marker = str(case["expected_error_marker"])

    marker_detected = (
        expected_marker == ""
        or expected_marker in validation_errors
    )

    expected_status = str(case["expected_parse_status"])
    actual_status = str(parser_record.get("parse_status", ""))

    test_result = "PASS" if actual_status == expected_status and marker_detected else "FAIL"

    return {
        "case_id": case["case_id"],
        "stage_name": case["stage_name"],
        "expected_parse_status": expected_status,
        "actual_parse_status": actual_status,
        "expected_error_family": case["expected_error_family"],
        "expected_error_marker_detected": marker_detected,
        "validation_error_count": parser_record.get("validation_error_count", 0),
        "validation_errors": validation_errors,
        "test_result": test_result,
        "raw_payload_written": False,
        "raw_response_written": False,
        "raw_prompt_written": False,
        "model_call_executed": False,
        "api_call_executed": False,
    }


def assert_outputs_safe(output_dir: Path) -> None:
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")

        for pattern in FORBIDDEN_OUTPUT_PATTERNS:
            if pattern.lower() in text.lower():
                raise ValueError(f"Forbidden output pattern found in {path}: {pattern}")


def run_smoke_tests(
    *,
    parser_module: Any,
    scaffold_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    scaffold_manifest = load_json(scaffold_manifest_path)

    if scaffold_manifest.get("status") != "PASS":
        raise ValueError("Cascade scaffold manifest status is not PASS.")

    if scaffold_manifest.get("safety", {}).get("raw_prompt_instances_written") is not False:
        raise ValueError("Cascade scaffold manifest does not confirm raw prompt instances are excluded.")

    if scaffold_manifest.get("safety", {}).get("raw_responses_written") is not False:
        raise ValueError("Cascade scaffold manifest does not confirm raw responses are excluded.")

    test_cases = make_test_cases()

    if len(test_cases) != EXPECTED_COUNTS["test_cases"]:
        raise ValueError(f"Expected {EXPECTED_COUNTS['test_cases']} test cases, found {len(test_cases)}.")

    validation_rows: list[dict[str, Any]] = []
    case_summary_rows: list[dict[str, Any]] = []

    for case in test_cases:
        payload = case["payload"]
        stage_name = case["stage_name"]
        expected_kwargs = expected_identifiers_for_stage(stage_name)

        parser_record = parser_module.validate_response(payload, **expected_kwargs)
        sanitized_row = sanitize_validation_record(case=case, parser_record=parser_record)
        validation_rows.append(sanitized_row)

        payload_key_count = len(payload.keys())
        forbidden_key_present = any(
            key.lower() in {
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
            for key in payload.keys()
        )

        case_summary_rows.append(
            {
                "case_id": case["case_id"],
                "stage_name": stage_name,
                "synthetic_payload_object_used": True,
                "payload_key_count": payload_key_count,
                "forbidden_key_present_in_synthetic_object": forbidden_key_present,
                "expected_parse_status": case["expected_parse_status"],
                "expected_error_family": case["expected_error_family"],
                "raw_payload_written": False,
                "raw_response_written": False,
                "raw_prompt_written": False,
                "model_call_executed": False,
                "api_call_executed": False,
            }
        )

    failed_tests = [row for row in validation_rows if row["test_result"] != "PASS"]
    if failed_tests:
        raise ValueError(f"Smoke tests failed: {[row['case_id'] for row in failed_tests]}")

    status_counts = Counter(row["actual_parse_status"] for row in validation_rows)
    stage_counts = Counter(row["stage_name"] for row in validation_rows)
    error_family_counts = Counter(row["expected_error_family"] for row in validation_rows)

    if status_counts["PASS"] != EXPECTED_COUNTS["valid_cases"]:
        raise ValueError(f"Expected {EXPECTED_COUNTS['valid_cases']} valid PASS cases, found {status_counts['PASS']}.")

    if status_counts["FAIL"] != EXPECTED_COUNTS["invalid_cases"]:
        raise ValueError(f"Expected {EXPECTED_COUNTS['invalid_cases']} invalid FAIL cases, found {status_counts['FAIL']}.")

    for stage_name, expected_count in EXPECTED_COUNTS["stages"].items():
        if stage_counts[stage_name] != expected_count:
            raise ValueError(f"Expected {expected_count} {stage_name} cases, found {stage_counts[stage_name]}.")

    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        output_dir / "pilot_05_cfpb_parser_smoke_test_cases.csv",
        [
            "case_id",
            "stage_name",
            "synthetic_payload_object_used",
            "payload_key_count",
            "forbidden_key_present_in_synthetic_object",
            "expected_parse_status",
            "expected_error_family",
            "raw_payload_written",
            "raw_response_written",
            "raw_prompt_written",
            "model_call_executed",
            "api_call_executed",
        ],
        case_summary_rows,
    )

    write_csv(
        output_dir / "pilot_05_cfpb_parser_smoke_test_validation_results.csv",
        [
            "case_id",
            "stage_name",
            "expected_parse_status",
            "actual_parse_status",
            "expected_error_family",
            "expected_error_marker_detected",
            "validation_error_count",
            "validation_errors",
            "test_result",
            "raw_payload_written",
            "raw_response_written",
            "raw_prompt_written",
            "model_call_executed",
            "api_call_executed",
        ],
        validation_rows,
    )

    status_rows = [
        {
            "actual_parse_status": status,
            "count": count,
            "share": round(count / len(validation_rows), 8),
        }
        for status, count in sorted(status_counts.items())
    ]

    write_csv(
        output_dir / "pilot_05_cfpb_parser_smoke_test_status_distribution.csv",
        ["actual_parse_status", "count", "share"],
        status_rows,
    )

    stage_rows = [
        {
            "stage_name": stage,
            "count": stage_counts[stage],
            "share": round(stage_counts[stage] / len(validation_rows), 8),
        }
        for stage in ["decision", "audit", "escalation"]
    ]

    write_csv(
        output_dir / "pilot_05_cfpb_parser_smoke_test_stage_distribution.csv",
        ["stage_name", "count", "share"],
        stage_rows,
    )

    error_family_rows = [
        {
            "expected_error_family": error_family,
            "count": count,
            "share": round(count / len(validation_rows), 8),
        }
        for error_family, count in sorted(error_family_counts.items())
    ]

    write_csv(
        output_dir / "pilot_05_cfpb_parser_smoke_test_error_family_distribution.csv",
        ["expected_error_family", "count", "share"],
        error_family_rows,
    )

    rejection_matrix_rows = [
        {
            "rejection_target": "raw_prompt_key",
            "case_id": "decision_invalid_raw_prompt_key",
            "expected_error_marker": "forbidden_free_text_key:raw_prompt",
            "covered": True,
        },
        {
            "rejection_target": "raw_response_key",
            "case_id": "decision_invalid_raw_response_key",
            "expected_error_marker": "forbidden_free_text_key:raw_response",
            "covered": True,
        },
        {
            "rejection_target": "chain_of_thought_key",
            "case_id": "decision_invalid_chain_of_thought_key",
            "expected_error_marker": "forbidden_free_text_key:chain_of_thought",
            "covered": True,
        },
        {
            "rejection_target": "free_text_rationale_key",
            "case_id": "audit_invalid_rationale_key",
            "expected_error_marker": "forbidden_free_text_key:rationale",
            "covered": True,
        },
        {
            "rejection_target": "free_text_explanation_key",
            "case_id": "escalation_invalid_explanation_key",
            "expected_error_marker": "forbidden_free_text_key:explanation",
            "covered": True,
        },
        {
            "rejection_target": "schema_version_mismatch",
            "case_id": "decision_invalid_schema_version",
            "expected_error_marker": "invalid_schema_version",
            "covered": True,
        },
        {
            "rejection_target": "stage_name_mismatch",
            "case_id": "audit_invalid_stage_name",
            "expected_error_marker": "stage_name_mismatch",
            "covered": True,
        },
        {
            "rejection_target": "identifier_mismatch",
            "case_id": "escalation_invalid_evidence_state_id",
            "expected_error_marker": "evidence_state_id_mismatch",
            "covered": True,
        },
        {
            "rejection_target": "invalid_enum",
            "case_id": "decision_invalid_enum_value",
            "expected_error_marker": "invalid_enum:predicted_process_outcome",
            "covered": True,
        },
        {
            "rejection_target": "parse_safety_violation",
            "case_id": "audit_invalid_parse_safety",
            "expected_error_marker": "parse_safety_violation:raw_prompt_repeated",
            "covered": True,
        },
    ]

    write_csv(
        output_dir / "pilot_05_cfpb_parser_smoke_test_rejection_matrix.csv",
        ["rejection_target", "case_id", "expected_error_marker", "covered"],
        rejection_matrix_rows,
    )

    summary_rows = [
        {"metric": "status", "value": "PASS"},
        {"metric": "synthetic_in_memory_response_objects_only", "value": True},
        {"metric": "test_cases", "value": len(validation_rows)},
        {"metric": "valid_cases_expected_pass", "value": status_counts["PASS"]},
        {"metric": "invalid_cases_expected_fail", "value": status_counts["FAIL"]},
        {"metric": "decision_cases", "value": stage_counts["decision"]},
        {"metric": "audit_cases", "value": stage_counts["audit"]},
        {"metric": "escalation_cases", "value": stage_counts["escalation"]},
        {"metric": "failed_smoke_tests", "value": len(failed_tests)},
        {"metric": "raw_payloads_written", "value": False},
        {"metric": "raw_responses_written", "value": False},
        {"metric": "raw_prompt_instances_written", "value": False},
        {"metric": "real_api_calls", "value": 0},
        {"metric": "model_calls", "value": 0},
        {"metric": "dataset_downloads", "value": 0},
    ]

    write_csv(
        output_dir / "pilot_05_cfpb_parser_smoke_test_summary.csv",
        ["metric", "value"],
        summary_rows,
    )

    manifest = {
        "status": "PASS",
        "scope": "Pilot 05 CFPB no-call cascade parser smoke test",
        "parser_script": str(parser_module.__file__),
        "scaffold_manifest": str(scaffold_manifest_path),
        "schema_version": SCHEMA_VERSION,
        "row_counts": {
            "test_cases": len(validation_rows),
            "valid_cases_expected_pass": status_counts["PASS"],
            "invalid_cases_expected_fail": status_counts["FAIL"],
            "decision_cases": stage_counts["decision"],
            "audit_cases": stage_counts["audit"],
            "escalation_cases": stage_counts["escalation"],
            "failed_smoke_tests": len(failed_tests),
            "rejection_targets_covered": len(rejection_matrix_rows),
        },
        "safety": {
            "synthetic_in_memory_response_objects_only": True,
            "raw_payloads_written": False,
            "raw_responses_written": False,
            "raw_prompt_instances_written": False,
            "raw_cfpb_rows_written": False,
            "raw_narratives_written": False,
            "company_names_written": False,
            "complaint_ids_written": False,
            "zip_codes_written": False,
            "real_api_calls": 0,
            "model_calls": 0,
            "dataset_downloads": 0,
        },
        "rejection_targets": [
            "raw_prompt_key",
            "raw_response_key",
            "chain_of_thought_key",
            "free_text_rationale_key",
            "free_text_explanation_key",
            "schema_version_mismatch",
            "stage_name_mismatch",
            "identifier_mismatch",
            "invalid_enum",
            "parse_safety_violation",
        ],
        "claim_boundary": "No-call parser smoke test only; not a model result, not a deployment result, and not a broad reliability claim.",
    }

    write_json(output_dir / "pilot_05_cfpb_parser_smoke_test_manifest.json", manifest)
    # Task 05AD recovery3: no Markdown report is written for this smoke test.
    # Structured sanitized CSV/JSON outputs are sufficient and avoid prose-based raw-field false positives.

    assert_outputs_safe(output_dir)

    return manifest


def main() -> None:
    args = parse_args()

    if not args.parser_script.exists():
        raise FileNotFoundError(args.parser_script)

    if not args.scaffold_manifest.exists():
        raise FileNotFoundError(args.scaffold_manifest)

    parser_module = load_parser_module(args.parser_script)

    manifest = run_smoke_tests(
        parser_module=parser_module,
        scaffold_manifest_path=args.scaffold_manifest,
        output_dir=args.output_dir,
    )

    print("Pilot 05 CFPB parser smoke test generated.")
    print(f"output_dir: {args.output_dir}")
    print("status: PASS")
    print(f"test_cases: {manifest['row_counts']['test_cases']}")
    print(f"valid_cases_expected_pass: {manifest['row_counts']['valid_cases_expected_pass']}")
    print(f"invalid_cases_expected_fail: {manifest['row_counts']['invalid_cases_expected_fail']}")
    print(f"decision_cases: {manifest['row_counts']['decision_cases']}")
    print(f"audit_cases: {manifest['row_counts']['audit_cases']}")
    print(f"escalation_cases: {manifest['row_counts']['escalation_cases']}")
    print(f"failed_smoke_tests: {manifest['row_counts']['failed_smoke_tests']}")
    print("synthetic_in_memory_response_objects_only: True")
    print("raw_payloads_written: False")
    print("raw_responses_written: False")
    print("raw_prompt_instances_written: False")
    print("real_api_calls: 0")
    print("model_calls: 0")
    print("dataset_downloads: 0")


if __name__ == "__main__":
    main()
