from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPORT_DIR = Path("reports/pilot_03_anthropic_t0020_valid")
SELECTOR_DIR = Path("reports/pilot_03_anthropic_validity_selector")

EXPECTED_FILES = {
    "chain_summary_csv": REPORT_DIR / "anthropic_t0020_valid_chain_summary.csv",
    "condition_summary_csv": REPORT_DIR / "anthropic_t0020_valid_condition_summary.csv",
    "failure_patterns_csv": REPORT_DIR / "anthropic_t0020_valid_failure_patterns.csv",
    "parser_summary_csv": REPORT_DIR / "anthropic_t0020_valid_parser_summary.csv",
    "report_md": REPORT_DIR / "anthropic_t0020_valid_report.md",
    "manifest_json": REPORT_DIR / "manifest.json",
    "selector_manifest_json": SELECTOR_DIR / "manifest.json",
    "selector_selected_run_dirs_txt": SELECTOR_DIR / "selected_run_dirs.txt",
    "selector_candidate_rows_csv": SELECTOR_DIR / "candidate_rows.csv",
    "selector_selection_issues_csv": SELECTOR_DIR / "selection_issues.csv",
    "selector_report_md": SELECTOR_DIR / "anthropic_validity_selector_report.md",
}

BLOCKED_COLUMN_FRAGMENTS = [
    "raw",
    "prompt",
    "response",
    "api_key",
    "secret",
    "token",
]

RISKY_WORDING = [
    "Q1",
    "journal-level",
    "groundbreaking",
    "proven",
    "universal",
    "provider ranking",
    "provider rankings",
    "general Claude reliability",
    "general GLM reliability",
    "real-world deployment proof",
]

EXPECTED_CONDITION_ROWS = {
    "original_evidence": {
        "n_chains": "20",
        "decision_correct_count": "20",
        "decision_correct_rate": "1.0",
        "escalation_correct_count": "20",
        "escalation_correct_rate": "1.0",
        "audit_passed_true_count": "20",
        "audit_passed_true_rate": "1.0",
        "valid_json_chain_count": "20",
        "valid_json_chain_rate": "1.0",
        "valid_schema_chain_count": "20",
        "valid_schema_chain_rate": "1.0",
    },
    "missing_policy_rule": {
        "n_chains": "20",
        "decision_correct_count": "10",
        "decision_correct_rate": "0.5",
        "escalation_correct_count": "17",
        "escalation_correct_rate": "0.85",
        "audit_passed_true_count": "0",
        "audit_passed_true_rate": "0.0",
        "valid_json_chain_count": "20",
        "valid_json_chain_rate": "1.0",
        "valid_schema_chain_count": "20",
        "valid_schema_chain_rate": "1.0",
    },
    "missing_one_required_unit": {
        "n_chains": "20",
        "decision_correct_count": "10",
        "decision_correct_rate": "0.5",
        "escalation_correct_count": "10",
        "escalation_correct_rate": "0.5",
        "audit_passed_true_count": "14",
        "audit_passed_true_rate": "0.7",
        "valid_json_chain_count": "20",
        "valid_json_chain_rate": "1.0",
        "valid_schema_chain_count": "20",
        "valid_schema_chain_rate": "1.0",
    },
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _add(results: list[CheckResult], name: str, passed: bool, detail: str) -> None:
    results.append(CheckResult(name=name, passed=passed, detail=detail))


def _has_absolute_windows_path(text: str) -> bool:
    lowered = text.lower()
    return "c:\\users\\" in lowered or "c:/users/" in lowered


def _scan_risky_wording(paths: list[Path]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []

    for path in paths:
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        lowered_text = text.lower()

        for pattern in RISKY_WORDING:
            if pattern.lower() in lowered_text:
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if pattern.lower() in line.lower():
                        hits.append(
                            {
                                "path": str(path),
                                "line_number": line_number,
                                "pattern": pattern,
                                "line": line.strip(),
                            }
                        )

    return hits


def _blocked_columns(path: Path) -> list[str]:
    rows = _read_csv(path)

    if not rows:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
    else:
        columns = list(rows[0].keys())

    return [
        column
        for column in columns
        if any(fragment in column.lower() for fragment in BLOCKED_COLUMN_FRAGMENTS)
    ]


def _validate_files_exist(results: list[CheckResult]) -> None:
    for label, path in EXPECTED_FILES.items():
        _add(
            results,
            f"file_exists::{label}",
            path.exists(),
            str(path),
        )


def _validate_manifest(results: list[CheckResult]) -> dict[str, Any]:
    manifest = _read_json(EXPECTED_FILES["manifest_json"])

    expected_top_level = {
        "status": "PASS",
        "provider": "anthropic",
        "model_name": "claude-opus-4-8",
        "real_api_calls": 0,
        "raw_prompt_or_response_columns_exported": False,
    }

    for key, expected_value in expected_top_level.items():
        actual = manifest.get(key)
        _add(
            results,
            f"manifest::{key}",
            actual == expected_value,
            f"actual={actual!r}; expected={expected_value!r}",
        )

    row_counts = manifest.get("row_counts", {})
    expected_row_counts = {
        "chain_summary": 60,
        "condition_summary": 3,
        "parser_summary": 10,
        "failure_patterns": 7,
    }

    for key, expected_value in expected_row_counts.items():
        actual = row_counts.get(key)
        _add(
            results,
            f"manifest::row_counts::{key}",
            actual == expected_value,
            f"actual={actual!r}; expected={expected_value!r}",
        )

    validity = manifest.get("validity", {})
    expected_validity = {
        "n_source_runs": 46,
        "n_raw_response_records": 180,
        "n_chain_rows": 60,
        "n_parsed_responses": 180,
        "n_invalid_json": 0,
        "n_invalid_schema": 0,
        "valid_json_counts": {"True": 180},
        "valid_schema_counts": {"True": 180},
    }

    for key, expected_value in expected_validity.items():
        actual = validity.get(key)
        _add(
            results,
            f"manifest::validity::{key}",
            actual == expected_value,
            f"actual={actual!r}; expected={expected_value!r}",
        )

    manifest_text = EXPECTED_FILES["manifest_json"].read_text(encoding="utf-8")
    _add(
        results,
        "manifest::no_absolute_windows_path",
        not _has_absolute_windows_path(manifest_text),
        "Manifest should not contain absolute local Windows user paths.",
    )

    return manifest


def _validate_selector_manifest(results: list[CheckResult]) -> dict[str, Any]:
    selector_manifest = _read_json(EXPECTED_FILES["selector_manifest_json"])

    expected = {
        "status": "PASS",
        "real_api_calls": 0,
        "baseline_run_dirs_from_planner": 46,
        "candidate_run_dirs_found": 48,
        "selected_run_dirs": 46,
        "selected_unique_task_condition_keys": 60,
        "required_task_condition_keys": 60,
        "missing_selected_valid_keys": [],
        "duplicate_selected_keys": [],
        "n_invalid_selected_rows": 0,
        "n_replacements": 0,
        "n_unresolved": 0,
    }

    for key, expected_value in expected.items():
        actual = selector_manifest.get(key)
        _add(
            results,
            f"selector_manifest::{key}",
            actual == expected_value,
            f"actual={actual!r}; expected={expected_value!r}",
        )

    selector_text = EXPECTED_FILES["selector_manifest_json"].read_text(encoding="utf-8")
    _add(
        results,
        "selector_manifest::no_absolute_windows_path",
        not _has_absolute_windows_path(selector_text),
        "Selector manifest should not contain absolute local Windows user paths.",
    )

    return selector_manifest


def _validate_selected_run_dirs(results: list[CheckResult]) -> None:
    lines = [
        line.strip()
        for line in EXPECTED_FILES["selector_selected_run_dirs_txt"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    _add(
        results,
        "selector_selected_run_dirs::count",
        len(lines) == 46,
        f"actual={len(lines)}; expected=46",
    )

    _add(
        results,
        "selector_selected_run_dirs::unique",
        len(set(lines)) == len(lines),
        f"unique={len(set(lines))}; total={len(lines)}",
    )

    absolute_hits = [line for line in lines if _has_absolute_windows_path(line)]
    _add(
        results,
        "selector_selected_run_dirs::no_absolute_windows_path",
        not absolute_hits,
        f"absolute_hits={absolute_hits[:3]}",
    )

    p03_t0015_repair_hits = [
        line for line in lines
        if "pilot_03_anthropic_small_chain_p03_t0015_20260702T031208Z" in line
    ]
    old_invalid_hits = [
        line for line in lines
        if "pilot_03_anthropic_small_chain_p03_t0015_20260702T024939Z" in line
    ]

    _add(
        results,
        "selector_selected_run_dirs::contains_repair_run",
        len(p03_t0015_repair_hits) == 1,
        f"repair_hits={p03_t0015_repair_hits}",
    )

    _add(
        results,
        "selector_selected_run_dirs::excludes_old_invalid_run",
        len(old_invalid_hits) == 0,
        f"old_invalid_hits={old_invalid_hits}",
    )


def _validate_csv_shapes_and_columns(results: list[CheckResult]) -> None:
    expected_row_counts = {
        EXPECTED_FILES["chain_summary_csv"]: 60,
        EXPECTED_FILES["condition_summary_csv"]: 3,
        EXPECTED_FILES["failure_patterns_csv"]: 7,
        EXPECTED_FILES["parser_summary_csv"]: 10,
        EXPECTED_FILES["selector_candidate_rows_csv"]: 64,
        EXPECTED_FILES["selector_selection_issues_csv"]: 0,
    }

    for path, expected_count in expected_row_counts.items():
        rows = _read_csv(path)
        _add(
            results,
            f"csv_row_count::{path}",
            len(rows) == expected_count,
            f"actual={len(rows)}; expected={expected_count}",
        )

        blocked = _blocked_columns(path)
        _add(
            results,
            f"csv_blocked_columns::{path}",
            not blocked,
            f"blocked={blocked}",
        )

        text = path.read_text(encoding="utf-8", errors="replace")
        _add(
            results,
            f"csv_no_absolute_windows_path::{path}",
            not _has_absolute_windows_path(text),
            "CSV should not contain absolute local Windows user paths.",
        )


def _validate_condition_summary(results: list[CheckResult]) -> None:
    rows = _read_csv(EXPECTED_FILES["condition_summary_csv"])
    rows_by_condition = {row["condition"]: row for row in rows}

    _add(
        results,
        "condition_summary::conditions",
        set(rows_by_condition.keys()) == set(EXPECTED_CONDITION_ROWS.keys()),
        f"actual={sorted(rows_by_condition.keys())}",
    )

    for condition, expected_fields in EXPECTED_CONDITION_ROWS.items():
        row = rows_by_condition.get(condition, {})

        for key, expected_value in expected_fields.items():
            actual = row.get(key)
            _add(
                results,
                f"condition_summary::{condition}::{key}",
                actual == expected_value,
                f"actual={actual!r}; expected={expected_value!r}",
            )


def _validate_chain_summary(results: list[CheckResult]) -> None:
    rows = _read_csv(EXPECTED_FILES["chain_summary_csv"])

    keys = {
        (row["task_id"], row["condition"])
        for row in rows
    }

    _add(
        results,
        "chain_summary::unique_task_condition_keys",
        len(keys) == 60,
        f"unique={len(keys)}; rows={len(rows)}",
    )

    expected_conditions = {
        "original_evidence": 20,
        "missing_policy_rule": 20,
        "missing_one_required_unit": 20,
    }

    for condition, expected_count in expected_conditions.items():
        actual_count = sum(1 for row in rows if row["condition"] == condition)
        _add(
            results,
            f"chain_summary::condition_count::{condition}",
            actual_count == expected_count,
            f"actual={actual_count}; expected={expected_count}",
        )

    invalid_json = [
        row for row in rows
        if row.get("valid_json_chain") != "True"
    ]
    invalid_schema = [
        row for row in rows
        if row.get("valid_schema_chain") != "True"
    ]

    _add(
        results,
        "chain_summary::all_valid_json_chain",
        not invalid_json,
        f"invalid_json_rows={len(invalid_json)}",
    )

    _add(
        results,
        "chain_summary::all_valid_schema_chain",
        not invalid_schema,
        f"invalid_schema_rows={len(invalid_schema)}",
    )

    repair_rows = [
        row for row in rows
        if row.get("task_id") == "P03-T0015"
        and row.get("condition") == "missing_one_required_unit"
        and row.get("source_run_name") == "pilot_03_anthropic_small_chain_p03_t0015_20260702T031208Z"
    ]

    old_invalid_rows = [
        row for row in rows
        if row.get("source_run_name") == "pilot_03_anthropic_small_chain_p03_t0015_20260702T024939Z"
    ]

    _add(
        results,
        "chain_summary::uses_repair_row_for_p03_t0015_missing_one_required_unit",
        len(repair_rows) == 1,
        f"repair_rows={len(repair_rows)}",
    )

    _add(
        results,
        "chain_summary::excludes_old_invalid_p03_t0015_row",
        len(old_invalid_rows) == 0,
        f"old_invalid_rows={len(old_invalid_rows)}",
    )


def _validate_parser_summary(results: list[CheckResult]) -> None:
    rows = _read_csv(EXPECTED_FILES["parser_summary_csv"])
    values = {row["metric"]: row["value"] for row in rows}

    expected = {
        "n_source_runs": "46",
        "n_raw_response_records": "180",
        "parser_version": "pilot_03_parser_v2",
        "n_parsed_responses": "180",
        "stage_counts": '{"audit": 60, "decision": 60, "escalation": 60}',
        "valid_json_counts": '{"True": 180}',
        "valid_schema_counts": '{"True": 180}',
        "n_invalid_json": "0",
        "n_invalid_schema": "0",
        "error_counts": "{}",
    }

    for key, expected_value in expected.items():
        actual = values.get(key)
        _add(
            results,
            f"parser_summary::{key}",
            actual == expected_value,
            f"actual={actual!r}; expected={expected_value!r}",
        )


def _validate_text_safety(results: list[CheckResult]) -> None:
    paths = [
        EXPECTED_FILES["report_md"],
        EXPECTED_FILES["manifest_json"],
        EXPECTED_FILES["chain_summary_csv"],
        EXPECTED_FILES["condition_summary_csv"],
        EXPECTED_FILES["failure_patterns_csv"],
        EXPECTED_FILES["parser_summary_csv"],
        EXPECTED_FILES["selector_manifest_json"],
        EXPECTED_FILES["selector_selected_run_dirs_txt"],
        EXPECTED_FILES["selector_candidate_rows_csv"],
        EXPECTED_FILES["selector_selection_issues_csv"],
        EXPECTED_FILES["selector_report_md"],
    ]

    risky_hits = _scan_risky_wording(paths)
    _add(
        results,
        "text_safety::risky_wording",
        not risky_hits,
        f"hits={risky_hits[:3]}",
    )

    absolute_hits = []
    for path in paths:
        if path.exists() and _has_absolute_windows_path(path.read_text(encoding="utf-8", errors="replace")):
            absolute_hits.append(str(path))

    _add(
        results,
        "text_safety::absolute_windows_paths",
        not absolute_hits,
        f"hits={absolute_hits}",
    )


def validate() -> list[CheckResult]:
    results: list[CheckResult] = []

    _validate_files_exist(results)

    if not all(result.passed for result in results):
        return results

    _validate_manifest(results)
    _validate_selector_manifest(results)
    _validate_selected_run_dirs(results)
    _validate_csv_shapes_and_columns(results)
    _validate_condition_summary(results)
    _validate_chain_summary(results)
    _validate_parser_summary(results)
    _validate_text_safety(results)

    _add(
        results,
        "validator::real_api_calls",
        True,
        "This validator reads committed sanitized files only and makes 0 real API calls.",
    )

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate committed-safe Anthropic/Claude Pilot 03 T0020 report outputs. "
            "This command makes no real API calls and does not inspect raw responses."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable validation output.",
    )
    args = parser.parse_args()

    results = validate()
    failed = [result for result in results if not result.passed]

    output = {
        "status": "PASS" if not failed else "FAIL",
        "n_checks": len(results),
        "n_failed": len(failed),
        "real_api_calls": 0,
        "failed_checks": [
            {
                "name": result.name,
                "detail": result.detail,
            }
            for result in failed
        ],
    }

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("Pilot 03 Anthropic/Claude T0020 committed-report validation")
        print("==========================================================")
        print(f"status: {output['status']}")
        print(f"n_checks: {output['n_checks']}")
        print(f"n_failed: {output['n_failed']}")
        print(f"real_api_calls: {output['real_api_calls']}")

        if failed:
            print("")
            print("Failed checks:")
            for result in failed:
                print(f"- {result.name}: {result.detail}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
