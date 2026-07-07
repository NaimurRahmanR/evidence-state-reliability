from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path("reports/cross_pilot_validation")
MANIFEST_JSON = OUTPUT_DIR / "manifest.json"
VALIDATION_SUMMARY_CSV = OUTPUT_DIR / "validation_summary.csv"

REPORT_DIR = Path("reports/cross_pilot_evidence_state_reliability")
REPORT_MANIFEST = REPORT_DIR / "manifest.json"
REPORT_MD = REPORT_DIR / "cross_pilot_report.md"
FRAMEWORK_SUMMARY_CSV = REPORT_DIR / "cross_pilot_framework_summary.csv"
VALIDATION_INPUT_CSV = REPORT_DIR / "pipeline_validation_summary.csv"
CONDITION_ALIGNMENT_CSV = REPORT_DIR / "condition_metric_alignment.csv"
METRIC_INVENTORY_CSV = REPORT_DIR / "metric_inventory.csv"

RISKY_PUBLIC_WORDING = [
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


def _check(condition: bool, check_name: str, detail: str, checks: list[ValidationCheck]) -> None:
    checks.append(
        ValidationCheck(
            check_name=check_name,
            status="PASS" if condition else "FAIL",
            detail=detail,
        )
    )


def validate_cross_pilot_report(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    checks: list[ValidationCheck] = []

    required_paths = [
        REPORT_MANIFEST,
        REPORT_MD,
        FRAMEWORK_SUMMARY_CSV,
        VALIDATION_INPUT_CSV,
        CONDITION_ALIGNMENT_CSV,
        METRIC_INVENTORY_CSV,
    ]

    for path in required_paths:
        _check(path.exists(), f"path_exists::{path}", "required cross-pilot output exists", checks)

    if not all(path.exists() for path in required_paths):
        manifest = {
            "artifact": "cross_pilot_evidence_state_report_validation",
            "status": "FAIL",
            "created_at_utc": _load_existing_created_at(MANIFEST_JSON),
            "reason": "missing required cross-pilot output",
            "n_checks": len(checks),
            "n_failed_checks": sum(1 for check in checks if check.status != "PASS"),
            "real_api_calls": 0,
            "raw_response_inspection": False,
        }
        _write_validation_outputs(output_dir, checks, manifest)
        return manifest

    report_manifest = _load_json(REPORT_MANIFEST)
    report_text = REPORT_MD.read_text(encoding="utf-8")
    framework_rows = _read_csv(FRAMEWORK_SUMMARY_CSV)
    validation_rows = _read_csv(VALIDATION_INPUT_CSV)
    condition_rows = _read_csv(CONDITION_ALIGNMENT_CSV)
    metric_inventory_rows = _read_csv(METRIC_INVENTORY_CSV)

    _check(report_manifest.get("status") == "PASS", "report_manifest_status", str(report_manifest.get("status")), checks)
    _check(report_manifest.get("real_api_calls") == 0, "report_manifest_real_api_calls", str(report_manifest.get("real_api_calls")), checks)
    _check(
        report_manifest.get("raw_response_inspection") is False,
        "report_manifest_raw_response_inspection",
        str(report_manifest.get("raw_response_inspection")),
        checks,
    )
    _check(
        report_manifest.get("raw_prompts_exported") is False,
        "report_manifest_raw_prompts_exported",
        str(report_manifest.get("raw_prompts_exported")),
        checks,
    )
    _check(
        report_manifest.get("raw_responses_exported") is False,
        "report_manifest_raw_responses_exported",
        str(report_manifest.get("raw_responses_exported")),
        checks,
    )
    _check(
        report_manifest.get("public_wording_safety_check") == "PASS",
        "report_manifest_public_wording_safety",
        str(report_manifest.get("public_wording_safety_check")),
        checks,
    )

    _check(len(framework_rows) == 2, "framework_summary_row_count", str(len(framework_rows)), checks)
    _check(len(validation_rows) == 4, "pipeline_validation_summary_row_count", str(len(validation_rows)), checks)
    _check(len(condition_rows) >= 4, "condition_metric_alignment_min_rows", str(len(condition_rows)), checks)
    _check(len(metric_inventory_rows) > 0, "metric_inventory_non_empty", str(len(metric_inventory_rows)), checks)

    pilot_ids = {row["pilot_id"] for row in framework_rows}
    _check(pilot_ids == {"pilot_03", "pilot_04"}, "framework_summary_pilot_ids", str(sorted(pilot_ids)), checks)

    validation_pilot_ids = {row["pilot_id"] for row in validation_rows}
    _check(validation_pilot_ids == {"pilot_03", "pilot_04"}, "validation_summary_pilot_ids", str(sorted(validation_pilot_ids)), checks)

    failed_validation_rows = [row for row in validation_rows if row["status"] != "PASS"]
    _check(not failed_validation_rows, "cross_pilot_inputs_all_pass", f"failed={failed_validation_rows[:3]}", checks)

    nonzero_api_rows = [row for row in validation_rows if str(row["real_api_calls"]) != "0"]
    _check(not nonzero_api_rows, "cross_pilot_validation_inputs_zero_api_calls", f"nonzero={nonzero_api_rows[:3]}", checks)

    raw_response_rows = [row for row in validation_rows if str(row["raw_response_inspection"]) != "False"]
    _check(not raw_response_rows, "cross_pilot_validation_inputs_no_raw_response_inspection", f"hits={raw_response_rows[:3]}", checks)

    required_report_phrases = [
        "Pilot 03 remains the locked first real-LLM evidence package.",
        "Pilot 04 is a deterministic no-call second-domain implementation.",
        "structural validity and evidence-state reliability can be measured as different layers",
        "real_api_calls: 0",
        "raw_response_inspection: False",
    ]

    for phrase in required_report_phrases:
        _check(phrase in report_text, f"report_required_phrase::{phrase}", "required report phrase present", checks)

    wording_hits = [phrase for phrase in RISKY_PUBLIC_WORDING if phrase in report_text]
    _check(not wording_hits, "report_public_wording_safety_scan", f"hits={wording_hits}", checks)

    forbidden_markers = [
        "raw_prompt_text",
        "raw_response_text",
        "api_key",
        "secret_key",
        "BEGIN_API",
        "END_API",
    ]

    scanned_paths = [
        REPORT_MANIFEST,
        REPORT_MD,
        FRAMEWORK_SUMMARY_CSV,
        VALIDATION_INPUT_CSV,
        CONDITION_ALIGNMENT_CSV,
        METRIC_INVENTORY_CSV,
    ]

    marker_hits: list[str] = []
    for path in scanned_paths:
        text = path.read_text(encoding="utf-8")
        for marker in forbidden_markers:
            if marker in text:
                marker_hits.append(f"{path}::{marker}")

    _check(not marker_hits, "cross_pilot_outputs_no_raw_or_secret_markers", f"hits={marker_hits[:10]}", checks)

    failed_checks = [check for check in checks if check.status != "PASS"]

    manifest = {
        "artifact": "cross_pilot_evidence_state_report_validation",
        "status": "PASS" if not failed_checks else "FAIL",
        "created_at_utc": _load_existing_created_at(MANIFEST_JSON),
        "validator": "experiments.validate_cross_pilot_evidence_state_report",
        "n_checks": len(checks),
        "n_failed_checks": len(failed_checks),
        "validated_files": [str(path) for path in required_paths],
        "output_files": [
            str(VALIDATION_SUMMARY_CSV),
            str(MANIFEST_JSON),
        ],
        "real_api_calls": 0,
        "raw_response_inspection": False,
    }

    _write_validation_outputs(output_dir, checks, manifest)
    return manifest


def _write_validation_outputs(
    output_dir: Path,
    checks: list[ValidationCheck],
    manifest: dict[str, Any],
) -> None:
    rows = [
        {
            "check_name": check.check_name,
            "status": check.status,
            "detail": check.detail,
        }
        for check in checks
    ]

    _write_csv(output_dir / "validation_summary.csv", rows)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    manifest = validate_cross_pilot_report()
    print("Cross-pilot evidence-state report validation completed.")
    print(f"output_dir: {OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"n_checks: {manifest['n_checks']}")
    print(f"n_failed_checks: {manifest['n_failed_checks']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")

    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
