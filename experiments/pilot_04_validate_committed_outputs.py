from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("reports/pilot_04_validation")

TASK_EXPORT_MANIFEST = Path("reports/pilot_04_tasks/manifest.json")
TASK_INVENTORY_CSV = Path("reports/pilot_04_tasks/task_inventory.csv")
CONDITION_INVENTORY_CSV = Path("reports/pilot_04_tasks/condition_inventory.csv")
DATA_TASK_CSV = Path("data/pilot_04_tasks.csv")

DRY_RUN_MANIFEST = Path("reports/pilot_04_dry_run/manifest.json")
DECISION_OUTPUTS_CSV = Path("reports/pilot_04_dry_run/decision_outputs.csv")
AUDIT_OUTPUTS_CSV = Path("reports/pilot_04_dry_run/audit_outputs.csv")
ESCALATION_OUTPUTS_CSV = Path("reports/pilot_04_dry_run/escalation_outputs.csv")
CHAIN_OUTPUTS_CSV = Path("reports/pilot_04_dry_run/chain_outputs.csv")

DESIGN_DOC = Path("docs/pilot_04_second_domain_design.md")

EXPECTED_TASK_COUNT = 24
EXPECTED_CONDITIONS = ["complete", "partial", "conflicted"]
EXPECTED_CONDITION_SET = set(EXPECTED_CONDITIONS)
EXPECTED_CONDITION_ROWS = EXPECTED_TASK_COUNT * len(EXPECTED_CONDITIONS)
EXPECTED_STAGE_ROWS = EXPECTED_CONDITION_ROWS
EXPECTED_STAGE_RECORDS = EXPECTED_STAGE_ROWS * 3

ALLOWED_GOLD_LABELS = {"approve", "review", "decline"}
ALLOWED_DECISION_LABELS = {"approve", "review", "decline"}
ALLOWED_ESCALATION_LABELS = {"no_escalation", "soft_escalation", "mandatory_escalation"}

TASK_REQUIRED_COLUMNS = {
    "task_id",
    "task_type",
    "applicant_id",
    "case_summary",
    "gold_decision",
    "gold_answer",
    "gold_reason",
    "decision_rule",
    "original_evidence_units",
    "required_evidence_unit_ids",
    "expected_primary_evidence_unit_ids",
    "condition_payloads",
    "original_evidence_text",
}

CONDITION_REQUIRED_COLUMNS = {
    "task_id",
    "task_type",
    "condition",
    "gold_decision",
    "visible_evidence_unit_ids",
    "n_visible_evidence_units",
    "n_required_visible",
    "n_required_total",
    "n_risk_units_visible",
    "n_support_units_visible",
    "conflict_note_visible",
    "degraded_evidence_note",
    "expected_reliability_stress",
    "visible_evidence_text",
}

DECISION_REQUIRED_COLUMNS = {
    "dry_run_version",
    "task_id",
    "task_type",
    "condition",
    "gold_decision",
    "schema_valid",
    "decision_label",
    "decision_matches_gold",
    "confidence",
    "n_primary_evidence_used",
    "primary_evidence_used",
    "missing_evidence_acknowledged",
    "n_risk_flags_identified",
    "risk_flags_identified",
    "decision_rationale_summary",
}

AUDIT_REQUIRED_COLUMNS = {
    "dry_run_version",
    "task_id",
    "task_type",
    "condition",
    "gold_decision",
    "schema_valid",
    "audit_pass",
    "evidence_alignment_score",
    "unsupported_claim_count",
    "missed_key_evidence_count",
    "audit_notes_summary",
}

ESCALATION_REQUIRED_COLUMNS = {
    "dry_run_version",
    "task_id",
    "task_type",
    "condition",
    "gold_decision",
    "schema_valid",
    "escalation_label",
    "requires_human_review",
    "escalation_confidence",
    "escalation_reason",
}

CHAIN_REQUIRED_COLUMNS = {
    "dry_run_version",
    "task_id",
    "task_type",
    "condition",
    "gold_decision",
    "visible_evidence_unit_ids",
    "missing_required_evidence_unit_ids",
    "n_visible_evidence_units",
    "n_missing_required_evidence_units",
    "decision_label",
    "decision_matches_gold",
    "decision_confidence",
    "missing_evidence_acknowledged",
    "audit_pass",
    "evidence_alignment_score",
    "unsupported_claim_count",
    "missed_key_evidence_count",
    "escalation_label",
    "requires_human_review",
    "escalation_confidence",
    "all_stage_schemas_valid",
    "prompt_instruction_text_exported",
    "real_api_calls",
}


@dataclass(frozen=True)
class ValidationCheck:
    check_name: str
    status: str
    detail: str


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _check(condition: bool, name: str, detail: str, rows: list[ValidationCheck]) -> None:
    status = "PASS" if condition else "FAIL"
    rows.append(ValidationCheck(check_name=name, status=status, detail=detail))


def _require_path(path: Path, rows: list[ValidationCheck]) -> None:
    _check(path.exists(), f"path_exists::{path}", "required committed output exists", rows)


def _check_required_columns(path: Path, required: set[str], rows: list[ValidationCheck]) -> None:
    records = _read_csv(path)
    columns = set(records[0].keys()) if records else set()
    missing = sorted(required - columns)
    _check(not missing, f"required_columns::{path}", f"missing={missing}", rows)


def _as_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"Expected serialized boolean True/False, got {value!r}")


def _as_int(value: str) -> int:
    return int(value)


def _as_float(value: str) -> float:
    return float(value)


def _json_list(value: str) -> list[Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        raise ValueError("Expected JSON list.")
    return loaded


def _validate_task_exports(rows: list[ValidationCheck]) -> dict[str, Any]:
    task_manifest = _load_json(TASK_EXPORT_MANIFEST)
    data_tasks = _read_csv(DATA_TASK_CSV)
    report_tasks = _read_csv(TASK_INVENTORY_CSV)
    condition_rows = _read_csv(CONDITION_INVENTORY_CSV)

    _check(task_manifest.get("status") == "PASS", "task_manifest_status", str(task_manifest.get("status")), rows)
    _check(task_manifest.get("real_api_calls") == 0, "task_manifest_real_api_calls", str(task_manifest.get("real_api_calls")), rows)
    _check(
        task_manifest.get("raw_response_inspection") is False,
        "task_manifest_raw_response_inspection",
        str(task_manifest.get("raw_response_inspection")),
        rows,
    )
    _check(
        task_manifest.get("raw_prompts_exported") is False,
        "task_manifest_raw_prompts_exported",
        str(task_manifest.get("raw_prompts_exported")),
        rows,
    )
    _check(
        task_manifest.get("raw_responses_exported") is False,
        "task_manifest_raw_responses_exported",
        str(task_manifest.get("raw_responses_exported")),
        rows,
    )

    _check(len(data_tasks) == EXPECTED_TASK_COUNT, "data_task_inventory_row_count", str(len(data_tasks)), rows)
    _check(len(report_tasks) == EXPECTED_TASK_COUNT, "report_task_inventory_row_count", str(len(report_tasks)), rows)
    _check(len(condition_rows) == EXPECTED_CONDITION_ROWS, "condition_inventory_row_count", str(len(condition_rows)), rows)

    task_ids = [row["task_id"] for row in report_tasks]
    _check(len(task_ids) == len(set(task_ids)), "task_ids_unique", f"n_unique={len(set(task_ids))}", rows)

    labels = Counter(row["gold_decision"] for row in report_tasks)
    _check(
        set(labels) == ALLOWED_GOLD_LABELS,
        "task_gold_labels_allowed",
        f"labels={dict(sorted(labels.items()))}",
        rows,
    )
    _check(
        labels == {"approve": 8, "decline": 8, "review": 8},
        "task_gold_labels_balanced",
        f"labels={dict(sorted(labels.items()))}",
        rows,
    )

    malformed_json_fields = []
    for task_row in report_tasks:
        for field in ["original_evidence_units", "required_evidence_unit_ids", "expected_primary_evidence_unit_ids", "condition_payloads"]:
            try:
                loaded = json.loads(task_row[field])
            except json.JSONDecodeError:
                malformed_json_fields.append(f"{task_row['task_id']}::{field}")
                continue

            if not isinstance(loaded, list):
                malformed_json_fields.append(f"{task_row['task_id']}::{field}::not_list")

    _check(
        not malformed_json_fields,
        "task_nested_json_fields_parse",
        f"malformed={malformed_json_fields[:5]}",
        rows,
    )

    condition_counts = Counter(row["condition"] for row in condition_rows)
    _check(
        set(condition_counts) == EXPECTED_CONDITION_SET,
        "condition_names_allowed",
        f"condition_counts={dict(sorted(condition_counts.items()))}",
        rows,
    )
    _check(
        all(condition_counts[condition] == EXPECTED_TASK_COUNT for condition in EXPECTED_CONDITIONS),
        "condition_counts_per_condition",
        f"condition_counts={dict(sorted(condition_counts.items()))}",
        rows,
    )

    condition_pairs = Counter((row["task_id"], row["condition"]) for row in condition_rows)
    duplicate_condition_pairs = [pair for pair, count in condition_pairs.items() if count != 1]
    _check(not duplicate_condition_pairs, "task_condition_pairs_unique", f"duplicates={duplicate_condition_pairs[:5]}", rows)

    partial_rows = [row for row in condition_rows if row["condition"] == "partial"]
    conflicted_rows = [row for row in condition_rows if row["condition"] == "conflicted"]

    _check(
        all(_as_int(row["n_required_visible"]) < _as_int(row["n_required_total"]) for row in partial_rows),
        "partial_condition_removes_required_evidence",
        "all partial rows hide at least one required unit",
        rows,
    )
    _check(
        all(row["conflict_note_visible"] == "True" for row in conflicted_rows),
        "conflicted_condition_exposes_conflict_note",
        "all conflicted rows expose E8 conflict note",
        rows,
    )

    return {
        "task_rows": len(report_tasks),
        "condition_rows": len(condition_rows),
        "task_label_counts": dict(sorted(labels.items())),
        "condition_counts": dict(sorted(condition_counts.items())),
    }


def _validate_dry_run_outputs(rows: list[ValidationCheck]) -> dict[str, Any]:
    dry_run_manifest = _load_json(DRY_RUN_MANIFEST)
    decision_rows = _read_csv(DECISION_OUTPUTS_CSV)
    audit_rows = _read_csv(AUDIT_OUTPUTS_CSV)
    escalation_rows = _read_csv(ESCALATION_OUTPUTS_CSV)
    chain_rows = _read_csv(CHAIN_OUTPUTS_CSV)

    _check(dry_run_manifest.get("status") == "PASS", "dry_run_manifest_status", str(dry_run_manifest.get("status")), rows)
    _check(dry_run_manifest.get("real_api_calls") == 0, "dry_run_manifest_real_api_calls", str(dry_run_manifest.get("real_api_calls")), rows)
    _check(
        dry_run_manifest.get("raw_response_inspection") is False,
        "dry_run_manifest_raw_response_inspection",
        str(dry_run_manifest.get("raw_response_inspection")),
        rows,
    )
    _check(
        dry_run_manifest.get("raw_prompts_exported") is False,
        "dry_run_manifest_raw_prompts_exported",
        str(dry_run_manifest.get("raw_prompts_exported")),
        rows,
    )
    _check(
        dry_run_manifest.get("raw_responses_exported") is False,
        "dry_run_manifest_raw_responses_exported",
        str(dry_run_manifest.get("raw_responses_exported")),
        rows,
    )
    _check(
        dry_run_manifest.get("prompt_instruction_text_exported") is False,
        "dry_run_manifest_prompt_text_not_exported",
        str(dry_run_manifest.get("prompt_instruction_text_exported")),
        rows,
    )

    _check(len(decision_rows) == EXPECTED_STAGE_ROWS, "decision_outputs_row_count", str(len(decision_rows)), rows)
    _check(len(audit_rows) == EXPECTED_STAGE_ROWS, "audit_outputs_row_count", str(len(audit_rows)), rows)
    _check(len(escalation_rows) == EXPECTED_STAGE_ROWS, "escalation_outputs_row_count", str(len(escalation_rows)), rows)
    _check(len(chain_rows) == EXPECTED_STAGE_ROWS, "chain_outputs_row_count", str(len(chain_rows)), rows)

    _check(
        dry_run_manifest.get("summary", {}).get("n_chains") == EXPECTED_STAGE_ROWS,
        "dry_run_summary_chain_count",
        str(dry_run_manifest.get("summary", {}).get("n_chains")),
        rows,
    )
    _check(
        dry_run_manifest.get("summary", {}).get("n_stage_records") == EXPECTED_STAGE_RECORDS,
        "dry_run_summary_stage_record_count",
        str(dry_run_manifest.get("summary", {}).get("n_stage_records")),
        rows,
    )
    _check(
        dry_run_manifest.get("summary", {}).get("all_stage_schemas_valid") is True,
        "dry_run_summary_all_stage_schemas_valid",
        str(dry_run_manifest.get("summary", {}).get("all_stage_schemas_valid")),
        rows,
    )

    _check(
        all(row["schema_valid"] == "True" for row in decision_rows),
        "decision_schema_valid_all_rows",
        "all decision rows schema_valid=True",
        rows,
    )
    _check(
        all(row["schema_valid"] == "True" for row in audit_rows),
        "audit_schema_valid_all_rows",
        "all audit rows schema_valid=True",
        rows,
    )
    _check(
        all(row["schema_valid"] == "True" for row in escalation_rows),
        "escalation_schema_valid_all_rows",
        "all escalation rows schema_valid=True",
        rows,
    )
    _check(
        all(row["all_stage_schemas_valid"] == "True" for row in chain_rows),
        "chain_all_stage_schemas_valid_all_rows",
        "all chain rows all_stage_schemas_valid=True",
        rows,
    )
    _check(
        all(row["prompt_instruction_text_exported"] == "False" for row in chain_rows),
        "chain_prompt_text_not_exported_all_rows",
        "all chain rows prompt_instruction_text_exported=False",
        rows,
    )
    _check(
        all(row["real_api_calls"] == "0" for row in chain_rows),
        "chain_real_api_calls_zero_all_rows",
        "all chain rows real_api_calls=0",
        rows,
    )

    decision_labels = Counter(row["decision_label"] for row in decision_rows)
    escalation_labels = Counter(row["escalation_label"] for row in escalation_rows)
    decision_conditions = Counter(row["condition"] for row in decision_rows)

    _check(
        set(decision_labels).issubset(ALLOWED_DECISION_LABELS),
        "decision_labels_allowed",
        f"decision_labels={dict(sorted(decision_labels.items()))}",
        rows,
    )
    _check(
        set(escalation_labels).issubset(ALLOWED_ESCALATION_LABELS),
        "escalation_labels_allowed",
        f"escalation_labels={dict(sorted(escalation_labels.items()))}",
        rows,
    )
    _check(
        all(decision_conditions[condition] == EXPECTED_TASK_COUNT for condition in EXPECTED_CONDITIONS),
        "decision_condition_counts",
        f"condition_counts={dict(sorted(decision_conditions.items()))}",
        rows,
    )

    confidence_errors = []
    for row in decision_rows:
        value = _as_float(row["confidence"])
        if not 0 <= value <= 1:
            confidence_errors.append(f"decision::{row['task_id']}::{row['condition']}::{value}")

    for row in audit_rows:
        value = _as_float(row["evidence_alignment_score"])
        if not 0 <= value <= 1:
            confidence_errors.append(f"audit::{row['task_id']}::{row['condition']}::{value}")

    for row in escalation_rows:
        value = _as_float(row["escalation_confidence"])
        if not 0 <= value <= 1:
            confidence_errors.append(f"escalation::{row['task_id']}::{row['condition']}::{value}")

    _check(not confidence_errors, "numeric_scores_within_unit_interval", f"errors={confidence_errors[:5]}", rows)

    partial_human_review = sum(
        1 for row in chain_rows if row["condition"] == "partial" and row["requires_human_review"] == "True"
    )
    conflicted_human_review = sum(
        1 for row in chain_rows if row["condition"] == "conflicted" and row["requires_human_review"] == "True"
    )
    complete_human_review = sum(
        1 for row in chain_rows if row["condition"] == "complete" and row["requires_human_review"] == "True"
    )

    _check(partial_human_review > 0, "partial_condition_has_review_triggers", str(partial_human_review), rows)
    _check(conflicted_human_review > 0, "conflicted_condition_has_review_triggers", str(conflicted_human_review), rows)
    _check(complete_human_review == 0, "complete_condition_has_no_review_triggers", str(complete_human_review), rows)

    parsed_json_errors = []
    for row in decision_rows:
        try:
            _json_list(row["primary_evidence_used"])
            _json_list(row["risk_flags_identified"])
        except Exception as exc:
            parsed_json_errors.append(f"decision::{row['task_id']}::{row['condition']}::{exc}")

    for row in chain_rows:
        try:
            _json_list(row["visible_evidence_unit_ids"])
            _json_list(row["missing_required_evidence_unit_ids"])
        except Exception as exc:
            parsed_json_errors.append(f"chain::{row['task_id']}::{row['condition']}::{exc}")

    _check(not parsed_json_errors, "dry_run_json_list_fields_parse", f"errors={parsed_json_errors[:5]}", rows)

    return {
        "decision_rows": len(decision_rows),
        "audit_rows": len(audit_rows),
        "escalation_rows": len(escalation_rows),
        "chain_rows": len(chain_rows),
        "decision_label_counts": dict(sorted(decision_labels.items())),
        "escalation_label_counts": dict(sorted(escalation_labels.items())),
        "human_review_counts": {
            "complete": complete_human_review,
            "partial": partial_human_review,
            "conflicted": conflicted_human_review,
        },
    }


def _validate_design_doc(rows: list[ValidationCheck]) -> dict[str, Any]:
    text = DESIGN_DOC.read_text(encoding="utf-8")

    required_phrases = [
        "Pilot 03 remains locked",
        "synthetic loan-risk decision-support setting",
        "no-call",
        "real_api_calls: 0",
        "raw_response_inspection: False",
        "must not modify, reinterpret, or replace Pilot 03",
    ]

    for phrase in required_phrases:
        _check(phrase in text, f"design_doc_required_phrase::{phrase}", "required scope phrase present", rows)

    risky_phrases = [
        "Q1",
        "journal-level",
        "groundbreaking",
        "proven",
        "universal",
        "real-world deployment proof",
        "provider ranking",
        "general Claude reliability",
        "general GLM reliability",
        "live deployment validity",
        "broad LLM reliability",
        "general model superiority",
        "financial safety",
        "legal safety",
        "medical safety",
        "lending regulation",
        "compliance with lending regulation",
    ]

    hits = [phrase for phrase in risky_phrases if phrase in text]
    _check(not hits, "design_doc_public_wording_safety", f"hits={hits}", rows)

    return {
        "required_phrase_count": len(required_phrases),
        "risky_phrase_hits": hits,
    }


def _validate_no_raw_or_secret_markers(rows: list[ValidationCheck]) -> dict[str, Any]:
    output_paths = [
        DATA_TASK_CSV,
        TASK_INVENTORY_CSV,
        CONDITION_INVENTORY_CSV,
        TASK_EXPORT_MANIFEST,
        DECISION_OUTPUTS_CSV,
        AUDIT_OUTPUTS_CSV,
        ESCALATION_OUTPUTS_CSV,
        CHAIN_OUTPUTS_CSV,
        DRY_RUN_MANIFEST,
    ]

    forbidden_substrings = [
        "raw_prompt_text",
        "raw_response_text",
        "api_key",
        "secret_key",
        "BEGIN_API",
        "END_API",
    ]

    hits: list[str] = []
    for path in output_paths:
        text = path.read_text(encoding="utf-8")
        for substring in forbidden_substrings:
            if substring in text:
                hits.append(f"{path}::{substring}")

    _check(not hits, "committed_outputs_no_raw_or_secret_markers", f"hits={hits[:10]}", rows)

    return {
        "scanned_output_files": len(output_paths),
        "marker_hits": hits,
    }


def validate_committed_outputs(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    """Validate committed Pilot 04 design, task, and dry-run outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    checks: list[ValidationCheck] = []

    required_paths = [
        DESIGN_DOC,
        DATA_TASK_CSV,
        TASK_INVENTORY_CSV,
        CONDITION_INVENTORY_CSV,
        TASK_EXPORT_MANIFEST,
        DECISION_OUTPUTS_CSV,
        AUDIT_OUTPUTS_CSV,
        ESCALATION_OUTPUTS_CSV,
        CHAIN_OUTPUTS_CSV,
        DRY_RUN_MANIFEST,
    ]

    for path in required_paths:
        _require_path(path, checks)

    if any(check.status == "FAIL" for check in checks):
        summary = {
            "artifact": "pilot_04_committed_output_validation",
            "status": "FAIL",
            "created_at_utc": _load_existing_created_at(output_dir / "manifest.json"),
            "reason": "one or more required files are missing",
            "n_checks": len(checks),
            "n_failed_checks": sum(1 for check in checks if check.status == "FAIL"),
            "real_api_calls": 0,
            "raw_response_inspection": False,
        }
        _write_validation_outputs(output_dir, checks, summary)
        return summary

    _check_required_columns(DATA_TASK_CSV, TASK_REQUIRED_COLUMNS, checks)
    _check_required_columns(TASK_INVENTORY_CSV, TASK_REQUIRED_COLUMNS, checks)
    _check_required_columns(CONDITION_INVENTORY_CSV, CONDITION_REQUIRED_COLUMNS, checks)
    _check_required_columns(DECISION_OUTPUTS_CSV, DECISION_REQUIRED_COLUMNS, checks)
    _check_required_columns(AUDIT_OUTPUTS_CSV, AUDIT_REQUIRED_COLUMNS, checks)
    _check_required_columns(ESCALATION_OUTPUTS_CSV, ESCALATION_REQUIRED_COLUMNS, checks)
    _check_required_columns(CHAIN_OUTPUTS_CSV, CHAIN_REQUIRED_COLUMNS, checks)

    design_summary = _validate_design_doc(checks)
    task_summary = _validate_task_exports(checks)
    dry_run_summary = _validate_dry_run_outputs(checks)
    marker_summary = _validate_no_raw_or_secret_markers(checks)

    failed_checks = [check for check in checks if check.status != "PASS"]

    summary = {
        "artifact": "pilot_04_committed_output_validation",
        "status": "PASS" if not failed_checks else "FAIL",
        "created_at_utc": _load_existing_created_at(output_dir / "manifest.json"),
        "validator": "experiments.pilot_04_validate_committed_outputs",
        "n_checks": len(checks),
        "n_failed_checks": len(failed_checks),
        "design_summary": design_summary,
        "task_summary": task_summary,
        "dry_run_summary": dry_run_summary,
        "marker_summary": marker_summary,
        "validated_files": [str(path) for path in required_paths],
        "output_files": [
            str(output_dir / "validation_summary.csv"),
            str(output_dir / "manifest.json"),
        ],
        "real_api_calls": 0,
        "raw_response_inspection": False,
    }

    _write_validation_outputs(output_dir, checks, summary)
    return summary


def _write_validation_outputs(
    output_dir: Path,
    checks: list[ValidationCheck],
    summary: dict[str, Any],
) -> None:
    validation_rows = [
        {
            "check_name": check.check_name,
            "status": check.status,
            "detail": check.detail,
        }
        for check in checks
    ]

    _write_csv(output_dir / "validation_summary.csv", validation_rows)
    (output_dir / "manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    manifest = validate_committed_outputs()
    print("Pilot 04 committed-output validation completed.")
    print(f"output_dir: {DEFAULT_OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"n_checks: {manifest['n_checks']}")
    print(f"n_failed_checks: {manifest['n_failed_checks']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")

    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
