#!/usr/bin/env python
"""
Pilot 05 CFPB no-call cascade execution scaffold.

This script creates dry-run scaffolding for a future approved cascade execution
over the committed Pilot 05 CFPB evidence-state conditions.

It does not call any model or API. It does not write raw prompt instances or raw
responses. It writes prompt templates, response schemas, parser rules, a dry-run
request manifest, and expected sanitized output structures.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "pilot_05_cfpb_cascade_v1"

STAGES = ["decision", "audit", "escalation"]
CONDITIONS = ["clean", "compressed", "partial_dropout", "noisy_conflicting"]

EXPECTED_CONDITION_HEADER = [
    "evidence_state_id",
    "packet_id",
    "subset_rank",
    "condition_name",
    "condition_order",
    "evidence_state_text",
    "degradation_profile",
]

EXPECTED_LABEL_HEADER = [
    "evidence_state_id",
    "packet_id",
    "target_timely_response",
]

FORBIDDEN_EVIDENCE_TEXT_FRAGMENTS = [
    "Consumer complaint narrative",
    "Complaint ID",
    "ZIP code",
    "Timely response",
    "target_timely_response",
    "Company response to consumer",
    "Company public response",
    "Date sent to company",
    "Closed with",
    "In progress",
    "Untimely response",
    "XX/XX/XXXX",
    "XXXX XXXX",
    "{$",
    "I received",
    "I contacted",
    "death certificate",
    "fingerprint",
    "Best Buy",
    "raw_prompt",
    "raw_response",
    "api_response",
    "model_response",
    "llm_response",
]

PROMPT_TEMPLATES = {
    "decision_v1": {
        "stage_name": "decision",
        "system_template": (
            "You are a controlled experimental decision component. "
            "Use only the provided sanitized evidence-state text. "
            "Return JSON only. Do not include free-text explanation, chain-of-thought, "
            "raw prompt text, raw evidence copy, or personal data."
        ),
        "user_template": (
            "Given evidence_state_id={evidence_state_id}, packet_id={packet_id}, "
            "condition_name={condition_name}, and sanitized evidence_state_text={evidence_state_text}, "
            "predict the binary administrative process outcome using the response schema. "
            "Allowed predicted_process_outcome values are Yes, No, insufficient_evidence."
        ),
        "raw_prompt_instance_written": False,
    },
    "audit_v1": {
        "stage_name": "audit",
        "system_template": (
            "You are a controlled experimental audit component. "
            "Audit only the sanitized decision record and evidence metadata provided at runtime. "
            "Return JSON only. Do not include free-text explanation, chain-of-thought, "
            "raw prompt text, raw evidence copy, or personal data."
        ),
        "user_template": (
            "Given evidence_state_id={evidence_state_id}, packet_id={packet_id}, "
            "condition_name={condition_name}, and a sanitized decision output reference, "
            "audit whether the decision should pass, fail, or escalate under the response schema."
        ),
        "raw_prompt_instance_written": False,
    },
    "escalation_v1": {
        "stage_name": "escalation",
        "system_template": (
            "You are a controlled experimental escalation component. "
            "Use only sanitized decision and audit records provided at runtime. "
            "Return JSON only. Do not include free-text explanation, chain-of-thought, "
            "raw prompt text, raw evidence copy, or personal data."
        ),
        "user_template": (
            "Given evidence_state_id={evidence_state_id}, packet_id={packet_id}, "
            "condition_name={condition_name}, and sanitized decision/audit output references, "
            "choose an escalation decision under the response schema."
        ),
        "raw_prompt_instance_written": False,
    },
}

RESPONSE_SCHEMA = {
    "schema_version": SCHEMA_VERSION,
    "common_required_fields": [
        "schema_version",
        "stage_name",
        "evidence_state_id",
        "packet_id",
        "condition_name",
        "parse_safety",
    ],
    "parse_safety_required": {
        "raw_personal_data_in_response": False,
        "raw_prompt_repeated": False,
        "target_label_claimed_seen": False,
    },
    "stage_schemas": {
        "decision": {
            "required_fields": [
                "predicted_process_outcome",
                "confidence_bin",
                "evidence_sufficiency",
                "decision_reason_codes",
            ],
            "allowed_values": {
                "predicted_process_outcome": ["Yes", "No", "insufficient_evidence"],
                "confidence_bin": ["low", "medium", "high"],
                "evidence_sufficiency": ["sufficient", "partial", "insufficient"],
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
            "required_fields": [
                "audit_outcome",
                "audit_confidence_bin",
                "detected_risk_codes",
                "recommended_action",
            ],
            "allowed_values": {
                "audit_outcome": ["pass", "fail", "escalate"],
                "audit_confidence_bin": ["low", "medium", "high"],
                "detected_risk_codes": [
                    "none",
                    "insufficient_evidence",
                    "low_confidence",
                    "condition_degradation",
                    "conflicting_signal",
                    "schema_concern",
                ],
                "recommended_action": [
                    "accept_decision",
                    "request_escalation",
                    "withhold_output",
                ],
            },
        },
        "escalation": {
            "required_fields": [
                "escalation_decision",
                "final_answer_status",
                "escalation_reason_codes",
            ],
            "allowed_values": {
                "escalation_decision": [
                    "no_escalation",
                    "escalate_for_review",
                    "withhold_output",
                ],
                "final_answer_status": ["usable", "uncertain", "invalid"],
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
    },
    "forbidden_response_storage": [
        "raw_response",
        "raw_prompt",
        "chain_of_thought",
        "free_text_rationale",
        "verbatim_evidence_copy",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create no-call cascade scaffold for Pilot 05 CFPB."
    )
    parser.add_argument("--condition-file", required=True, type=Path)
    parser.add_argument("--condition-labels-file", required=True, type=Path)
    parser.add_argument("--condition-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 8)


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj, dialect=csv.excel)
        header = list(reader.fieldnames or [])
        rows = [
            {
                str(key): normalize_space("" if value is None else str(value))
                for key, value in row.items()
                if key is not None
            }
            for row in reader
        ]
    return header, rows


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


def assert_no_forbidden_evidence_text(text: str) -> None:
    text_lower = text.lower()
    for fragment in FORBIDDEN_EVIDENCE_TEXT_FRAGMENTS:
        if fragment.lower() in text_lower:
            raise ValueError(f"Forbidden fragment in evidence-state text: {fragment}")


def make_request_id(evidence_state_id: str, stage_name: str) -> str:
    short_stage = {
        "decision": "D",
        "audit": "A",
        "escalation": "E",
    }[stage_name]
    return f"{evidence_state_id}_{short_stage}"


def create_dry_run_manifest(condition_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    request_rows: list[dict[str, Any]] = []

    for condition_row in condition_rows:
        evidence_state_id = condition_row["evidence_state_id"]
        packet_id = condition_row["packet_id"]
        condition_name = condition_row["condition_name"]

        decision_request_id = make_request_id(evidence_state_id, "decision")
        audit_request_id = make_request_id(evidence_state_id, "audit")
        escalation_request_id = make_request_id(evidence_state_id, "escalation")

        stage_specs = [
            {
                "dry_run_request_id": decision_request_id,
                "stage_name": "decision",
                "template_id": "decision_v1",
                "input_reference": "evidence_state_conditions.csv:evidence_state_text",
                "dependency_reference": "",
            },
            {
                "dry_run_request_id": audit_request_id,
                "stage_name": "audit",
                "template_id": "audit_v1",
                "input_reference": "sanitized_decision_output_reference",
                "dependency_reference": decision_request_id,
            },
            {
                "dry_run_request_id": escalation_request_id,
                "stage_name": "escalation",
                "template_id": "escalation_v1",
                "input_reference": "sanitized_decision_and_audit_output_references",
                "dependency_reference": f"{decision_request_id}|{audit_request_id}",
            },
        ]

        for stage_index, stage_spec in enumerate(stage_specs, start=1):
            request_rows.append(
                {
                    "dry_run_request_id": stage_spec["dry_run_request_id"],
                    "stage_name": stage_spec["stage_name"],
                    "stage_order": stage_index,
                    "template_id": stage_spec["template_id"],
                    "schema_version": SCHEMA_VERSION,
                    "evidence_state_id": evidence_state_id,
                    "packet_id": packet_id,
                    "condition_name": condition_name,
                    "input_reference": stage_spec["input_reference"],
                    "dependency_reference": stage_spec["dependency_reference"],
                    "target_label_reference_excluded": True,
                    "prompt_template_only": True,
                    "raw_prompt_instance_written": False,
                    "raw_response_written": False,
                    "api_call_executed": False,
                    "model_call_executed": False,
                }
            )

    return request_rows


def create_parser_rules_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    rows.append(
        {
            "rule_id": "PR001",
            "stage_name": "all",
            "field_name": "raw_response",
            "rule_type": "storage_forbidden",
            "allowed_values": "",
            "required": "False",
            "notes": "Raw model responses must not be committed or written to reports.",
        }
    )
    rows.append(
        {
            "rule_id": "PR002",
            "stage_name": "all",
            "field_name": "raw_prompt",
            "rule_type": "storage_forbidden",
            "allowed_values": "",
            "required": "False",
            "notes": "Raw prompt instances must not be committed or written to reports.",
        }
    )
    rows.append(
        {
            "rule_id": "PR003",
            "stage_name": "all",
            "field_name": "schema_version",
            "rule_type": "exact_match",
            "allowed_values": SCHEMA_VERSION,
            "required": "True",
            "notes": "All parsed responses must use the approved schema version.",
        }
    )

    rule_index = 4
    for stage_name, stage_schema in RESPONSE_SCHEMA["stage_schemas"].items():
        for field_name, allowed_values in stage_schema["allowed_values"].items():
            rows.append(
                {
                    "rule_id": f"PR{rule_index:03d}",
                    "stage_name": stage_name,
                    "field_name": field_name,
                    "rule_type": "enum_or_enum_list",
                    "allowed_values": "|".join(allowed_values),
                    "required": str(field_name in stage_schema["required_fields"]),
                    "notes": "Parsed field must use controlled vocabulary only.",
                }
            )
            rule_index += 1

    for field_name, expected_value in RESPONSE_SCHEMA["parse_safety_required"].items():
        rows.append(
            {
                "rule_id": f"PR{rule_index:03d}",
                "stage_name": "all",
                "field_name": f"parse_safety.{field_name}",
                "rule_type": "exact_match",
                "allowed_values": str(expected_value),
                "required": "True",
                "notes": "Safety declaration must remain false for unsafe raw-data or prompt leakage.",
            }
        )
        rule_index += 1

    return rows


def create_expected_output_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_decisions.csv",
            "field_name": "evidence_state_id",
            "stage_name": "decision",
            "allowed_values": "",
            "notes": "Identifier only; no raw evidence text.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_decisions.csv",
            "field_name": "predicted_process_outcome",
            "stage_name": "decision",
            "allowed_values": "Yes|No|insufficient_evidence",
            "notes": "Parsed enum only.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_decisions.csv",
            "field_name": "confidence_bin",
            "stage_name": "decision",
            "allowed_values": "low|medium|high",
            "notes": "Parsed enum only.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_audits.csv",
            "field_name": "audit_outcome",
            "stage_name": "audit",
            "allowed_values": "pass|fail|escalate",
            "notes": "Parsed enum only.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_escalations.csv",
            "field_name": "escalation_decision",
            "stage_name": "escalation",
            "allowed_values": "no_escalation|escalate_for_review|withhold_output",
            "notes": "Parsed enum only.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_joined_evaluation.csv",
            "field_name": "target_timely_response",
            "stage_name": "evaluation_only",
            "allowed_values": "Yes|No",
            "notes": "Labels may be joined only after sanitized outputs are parsed; labels are never prompt inputs.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_metrics.csv",
            "field_name": "condition_name",
            "stage_name": "evaluation_only",
            "allowed_values": "clean|compressed|partial_dropout|noisy_conflicting",
            "notes": "Metrics grouped by evidence-state condition.",
        },
    ]


def create_expected_output_files_rows() -> list[dict[str, Any]]:
    return [
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_decisions.csv",
            "created_by_future_step": "approved_model_execution",
            "raw_response_allowed": "False",
            "raw_prompt_allowed": "False",
            "label_allowed": "False",
            "purpose": "Sanitized parsed decision-stage outputs.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_audits.csv",
            "created_by_future_step": "approved_model_execution",
            "raw_response_allowed": "False",
            "raw_prompt_allowed": "False",
            "label_allowed": "False",
            "purpose": "Sanitized parsed audit-stage outputs.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_sanitized_escalations.csv",
            "created_by_future_step": "approved_model_execution",
            "raw_response_allowed": "False",
            "raw_prompt_allowed": "False",
            "label_allowed": "False",
            "purpose": "Sanitized parsed escalation-stage outputs.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_joined_evaluation.csv",
            "created_by_future_step": "post_parse_evaluation",
            "raw_response_allowed": "False",
            "raw_prompt_allowed": "False",
            "label_allowed": "True",
            "purpose": "Evaluation join between sanitized outputs and separate labels.",
        },
        {
            "output_file": "pilot_05_cfpb_cascade_metrics.csv",
            "created_by_future_step": "post_parse_evaluation",
            "raw_response_allowed": "False",
            "raw_prompt_allowed": "False",
            "label_allowed": "True",
            "purpose": "Reliability-cascade metrics by evidence-state condition.",
        },
    ]


def create_stage_definition_rows() -> list[dict[str, Any]]:
    return [
        {
            "stage_name": "decision",
            "stage_order": 1,
            "input_type": "sanitized_evidence_state_text",
            "output_type": "sanitized_structured_decision_json",
            "purpose": "Predict process outcome from the evidence state.",
        },
        {
            "stage_name": "audit",
            "stage_order": 2,
            "input_type": "sanitized_decision_output_reference",
            "output_type": "sanitized_structured_audit_json",
            "purpose": "Audit decision reliability and flag escalation risks.",
        },
        {
            "stage_name": "escalation",
            "stage_order": 3,
            "input_type": "sanitized_decision_and_audit_output_references",
            "output_type": "sanitized_structured_escalation_json",
            "purpose": "Decide whether output is usable, uncertain, or should be withheld/escalated.",
        },
    ]


def create_metrics_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric_name": "decision_accuracy_by_condition",
            "required_future_outputs": "sanitized_decisions + separate labels",
            "level": "decision",
            "claim_boundary": "Controlled evaluation metric only.",
        },
        {
            "metric_name": "invalid_json_rate_by_condition",
            "required_future_outputs": "parser validation records",
            "level": "structural",
            "claim_boundary": "Parser/schema reliability metric only.",
        },
        {
            "metric_name": "audit_escalation_rate_by_condition",
            "required_future_outputs": "sanitized_audits",
            "level": "audit",
            "claim_boundary": "Controlled audit-behaviour metric only.",
        },
        {
            "metric_name": "withhold_or_escalate_rate_by_condition",
            "required_future_outputs": "sanitized_escalations",
            "level": "escalation",
            "claim_boundary": "Controlled escalation-behaviour metric only.",
        },
        {
            "metric_name": "reliability_delta_clean_to_degraded",
            "required_future_outputs": "condition-grouped metrics",
            "level": "cascade",
            "claim_boundary": "Evidence-state degradation comparison within this controlled setup only.",
        },
    ]


def construct_scaffold(
    *,
    condition_file: Path,
    condition_labels_file: Path,
    condition_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    condition_manifest = load_json(condition_manifest_path)

    if condition_manifest.get("status") != "PASS":
        raise ValueError("Condition manifest status is not PASS.")

    if condition_manifest.get("safety", {}).get("target_label_in_evidence_state_text") is not False:
        raise ValueError("Input condition manifest does not confirm target labels excluded from evidence-state text.")

    condition_header, condition_rows = read_csv_rows(condition_file)
    label_header, label_rows = read_csv_rows(condition_labels_file)

    if condition_header != EXPECTED_CONDITION_HEADER:
        raise ValueError(f"Unexpected condition header: {condition_header!r}")

    if label_header != EXPECTED_LABEL_HEADER:
        raise ValueError(f"Unexpected label header: {label_header!r}")

    if len(condition_rows) != 240:
        raise ValueError(f"Expected 240 condition rows, found {len(condition_rows)}.")

    if len(label_rows) != 240:
        raise ValueError(f"Expected 240 condition label rows, found {len(label_rows)}.")

    condition_counts = Counter(row["condition_name"] for row in condition_rows)
    label_counts = Counter(row["target_timely_response"] for row in label_rows)

    for condition in CONDITIONS:
        if condition_counts[condition] != 60:
            raise ValueError(f"Condition {condition} expected 60 rows, found {condition_counts[condition]}.")

    if label_counts["No"] != 120 or label_counts["Yes"] != 120:
        raise ValueError(f"Expected balanced condition labels 120/120, found {dict(label_counts)}.")

    label_by_evidence_state = {
        row["evidence_state_id"]: row["target_timely_response"]
        for row in label_rows
    }

    for row in condition_rows:
        evidence_state_id = row["evidence_state_id"]

        if evidence_state_id not in label_by_evidence_state:
            raise ValueError(f"Missing label for evidence_state_id: {evidence_state_id}")

        assert_no_forbidden_evidence_text(row["evidence_state_text"])

    dry_run_rows = create_dry_run_manifest(condition_rows)
    stage_counts = Counter(row["stage_name"] for row in dry_run_rows)

    if len(dry_run_rows) != 720:
        raise ValueError(f"Expected 720 dry-run request rows, found {len(dry_run_rows)}.")

    for stage in STAGES:
        if stage_counts[stage] != 240:
            raise ValueError(f"Expected 240 dry-run rows for stage {stage}, found {stage_counts[stage]}.")

    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "pilot_05_cfpb_cascade_prompt_templates.json", PROMPT_TEMPLATES)
    write_json(output_dir / "pilot_05_cfpb_cascade_response_schema.json", RESPONSE_SCHEMA)

    write_csv(
        output_dir / "pilot_05_cfpb_cascade_dry_run_request_manifest.csv",
        [
            "dry_run_request_id",
            "stage_name",
            "stage_order",
            "template_id",
            "schema_version",
            "evidence_state_id",
            "packet_id",
            "condition_name",
            "input_reference",
            "dependency_reference",
            "target_label_reference_excluded",
            "prompt_template_only",
            "raw_prompt_instance_written",
            "raw_response_written",
            "api_call_executed",
            "model_call_executed",
        ],
        dry_run_rows,
    )

    parser_rule_rows = create_parser_rules_rows()
    write_csv(
        output_dir / "pilot_05_cfpb_cascade_parser_validation_rules.csv",
        ["rule_id", "stage_name", "field_name", "rule_type", "allowed_values", "required", "notes"],
        parser_rule_rows,
    )

    expected_output_schema_rows = create_expected_output_schema_rows()
    write_csv(
        output_dir / "pilot_05_cfpb_cascade_expected_output_schema.csv",
        ["output_file", "field_name", "stage_name", "allowed_values", "notes"],
        expected_output_schema_rows,
    )

    expected_output_files_rows = create_expected_output_files_rows()
    write_csv(
        output_dir / "pilot_05_cfpb_cascade_expected_output_files.csv",
        ["output_file", "created_by_future_step", "raw_response_allowed", "raw_prompt_allowed", "label_allowed", "purpose"],
        expected_output_files_rows,
    )

    stage_definition_rows = create_stage_definition_rows()
    write_csv(
        output_dir / "pilot_05_cfpb_cascade_stage_definitions.csv",
        ["stage_name", "stage_order", "input_type", "output_type", "purpose"],
        stage_definition_rows,
    )

    metrics_plan_rows = create_metrics_plan_rows()
    write_csv(
        output_dir / "pilot_05_cfpb_cascade_metrics_plan.csv",
        ["metric_name", "required_future_outputs", "level", "claim_boundary"],
        metrics_plan_rows,
    )

    dry_run_summary_rows = [
        {"metric": "status", "value": "PASS"},
        {"metric": "input_evidence_state_rows", "value": len(condition_rows)},
        {"metric": "input_label_rows_separate", "value": len(label_rows)},
        {"metric": "dry_run_request_rows", "value": len(dry_run_rows)},
        {"metric": "decision_stage_requests", "value": stage_counts["decision"]},
        {"metric": "audit_stage_requests", "value": stage_counts["audit"]},
        {"metric": "escalation_stage_requests", "value": stage_counts["escalation"]},
        {"metric": "prompt_templates_written", "value": len(PROMPT_TEMPLATES)},
        {"metric": "raw_prompt_instances_written", "value": False},
        {"metric": "raw_responses_written", "value": False},
        {"metric": "real_api_calls", "value": 0},
        {"metric": "model_calls", "value": 0},
        {"metric": "dataset_downloads", "value": 0},
        {"metric": "raw_cfpb_rows_written", "value": False},
        {"metric": "target_labels_used_as_prompt_inputs", "value": False},
        {"metric": "target_label_in_evidence_state_text", "value": False},
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_cascade_dry_run_summary.csv",
        ["metric", "value"],
        dry_run_summary_rows,
    )

    manifest = {
        "status": "PASS",
        "scope": "Pilot 05 CFPB no-call cascade execution scaffold",
        "schema_version": SCHEMA_VERSION,
        "source_condition_file": str(condition_file),
        "source_condition_labels_file": str(condition_labels_file),
        "source_condition_manifest": str(condition_manifest_path),
        "stages": STAGES,
        "conditions": CONDITIONS,
        "row_counts": {
            "input_evidence_state_rows": len(condition_rows),
            "input_label_rows_separate": len(label_rows),
            "dry_run_request_rows": len(dry_run_rows),
            "decision_stage_requests": stage_counts["decision"],
            "audit_stage_requests": stage_counts["audit"],
            "escalation_stage_requests": stage_counts["escalation"],
            "prompt_templates_written": len(PROMPT_TEMPLATES),
            "parser_rules_written": len(parser_rule_rows),
            "expected_output_schema_rows": len(expected_output_schema_rows),
            "expected_output_files_rows": len(expected_output_files_rows),
        },
        "condition_counts": dict((condition, condition_counts[condition]) for condition in CONDITIONS),
        "label_counts_separate_file_only": dict(sorted(label_counts.items())),
        "outputs": {
            "prompt_templates_json": str(output_dir / "pilot_05_cfpb_cascade_prompt_templates.json"),
            "response_schema_json": str(output_dir / "pilot_05_cfpb_cascade_response_schema.json"),
            "dry_run_request_manifest_csv": str(output_dir / "pilot_05_cfpb_cascade_dry_run_request_manifest.csv"),
            "parser_validation_rules_csv": str(output_dir / "pilot_05_cfpb_cascade_parser_validation_rules.csv"),
            "expected_output_schema_csv": str(output_dir / "pilot_05_cfpb_cascade_expected_output_schema.csv"),
            "expected_output_files_csv": str(output_dir / "pilot_05_cfpb_cascade_expected_output_files.csv"),
            "stage_definitions_csv": str(output_dir / "pilot_05_cfpb_cascade_stage_definitions.csv"),
            "metrics_plan_csv": str(output_dir / "pilot_05_cfpb_cascade_metrics_plan.csv"),
            "dry_run_summary_csv": str(output_dir / "pilot_05_cfpb_cascade_dry_run_summary.csv"),
            "report_md": str(output_dir / "pilot_05_cfpb_cascade_scaffold_report.md"),
        },
        "safety": {
            "real_api_calls": 0,
            "model_calls": 0,
            "dataset_downloads": 0,
            "raw_prompt_instances_written": False,
            "raw_responses_written": False,
            "raw_cfpb_rows_written": False,
            "raw_narratives_written": False,
            "company_names_written": False,
            "complaint_ids_written": False,
            "zip_codes_written": False,
            "target_labels_used_as_prompt_inputs": False,
            "target_label_in_evidence_state_text": False,
            "labels_kept_separate": True,
        },
        "claim_boundary": "No-call cascade execution scaffold only; not a model result, not a deployment result, and not a broad reliability claim.",
    }
    write_json(output_dir / "pilot_05_cfpb_cascade_scaffold_manifest.json", manifest)

    report = f"""# Pilot 05 CFPB Cascade Execution Scaffold

Status: PASS

This no-call scaffold prepares a future approved cascade execution over the committed Pilot 05 CFPB evidence-state condition rows.

## Inputs

- Evidence-state condition rows: {len(condition_rows)}
- Separate label rows: {len(label_rows)}
- Conditions: clean, compressed, partial_dropout, noisy_conflicting

## Planned cascade stages

- decision
- audit
- escalation

## Dry-run request manifest

- Total planned dry-run request rows: {len(dry_run_rows)}
- Decision-stage planned rows: {stage_counts["decision"]}
- Audit-stage planned rows: {stage_counts["audit"]}
- Escalation-stage planned rows: {stage_counts["escalation"]}

## Safety boundary

This task writes prompt templates only, not raw prompt instances.

This task writes parser rules and expected sanitized output structures only, not raw model responses.

The target labels remain separate and are not prompt inputs. Labels may only be joined after future sanitized outputs are parsed for evaluation.

No API or model call was executed.

## Claim boundary

This scaffold is a no-call preparation layer for later approved controlled cascade execution. It does not claim model reliability, provider ranking, financial safety, legal safety, consumer harm prevalence, real-world deployment validity, or regulated lending validity.
"""
    (output_dir / "pilot_05_cfpb_cascade_scaffold_report.md").write_text(report, encoding="utf-8")

    return manifest


def main() -> None:
    args = parse_args()

    for path in [args.condition_file, args.condition_labels_file, args.condition_manifest]:
        if not path.exists():
            raise FileNotFoundError(path)

    manifest = construct_scaffold(
        condition_file=args.condition_file,
        condition_labels_file=args.condition_labels_file,
        condition_manifest_path=args.condition_manifest,
        output_dir=args.output_dir,
    )

    print("Pilot 05 CFPB cascade scaffold generated.")
    print(f"output_dir: {args.output_dir}")
    print("status: PASS")
    print(f"input_evidence_state_rows: {manifest['row_counts']['input_evidence_state_rows']}")
    print(f"input_label_rows_separate: {manifest['row_counts']['input_label_rows_separate']}")
    print(f"dry_run_request_rows: {manifest['row_counts']['dry_run_request_rows']}")
    print(f"decision_stage_requests: {manifest['row_counts']['decision_stage_requests']}")
    print(f"audit_stage_requests: {manifest['row_counts']['audit_stage_requests']}")
    print(f"escalation_stage_requests: {manifest['row_counts']['escalation_stage_requests']}")
    print("raw_prompt_instances_written: False")
    print("raw_responses_written: False")
    print("real_api_calls: 0")
    print("model_calls: 0")
    print("dataset_downloads: 0")


if __name__ == "__main__":
    main()
