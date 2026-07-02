from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_validation")

REQUIRED_FILES = [
    Path("reports/pilot_03_real_glm_t0020_condition_summary.csv"),
    Path("reports/pilot_03_glm_vs_claude_comparison/shared_5_task_condition_comparison.csv"),
    Path("reports/pilot_03_uncertainty/manifest.json"),
    Path("reports/pilot_03_uncertainty/glm20_condition_uncertainty.csv"),
    Path("reports/pilot_03_uncertainty/shared5_provider_condition_uncertainty.csv"),
    Path("reports/pilot_03_uncertainty/condition_difference_uncertainty.csv"),
    Path("reports/pilot_03_uncertainty/shared5_provider_difference_uncertainty.csv"),
    Path("reports/pilot_03_stage_cascade/manifest.json"),
    Path("reports/pilot_03_stage_cascade/glm20_sanitized_chain_summary.csv"),
    Path("reports/pilot_03_stage_cascade/shared5_sanitized_chain_summary.csv"),
    Path("reports/pilot_03_stage_cascade/cascade_pattern_summary.csv"),
    Path("reports/pilot_03_stage_cascade/stage_transition_summary.csv"),
]

RISKY_WORDING_PATTERNS = [
    r"\bQ1\b",
    r"journal-level",
    r"groundbreaking",
    r"\bproven\b",
    r"\buniversal\b",
    r"\bsuperior\b",
    r"real-world deployment proof",
    r"Q1-ready evidence already complete",
    r"general GLM reliability",
    r"general Claude reliability",
]

BLOCKED_COLUMN_FRAGMENTS = [
    "raw",
    "prompt",
    "response",
    "api_key",
    "secret",
    "token",
]

SAFE_NOTE = (
    "Validation report for committed Pilot 03 outputs. This command checks internal "
    "consistency only and makes no real API calls."
)


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


def _is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int_value(value: Any) -> int:
    return int(str(value).strip())


def _parse_count_map(value: str) -> dict[str, int]:
    value = str(value).strip()

    if not value:
        return {}

    output: dict[str, int] = {}

    for part in value.split(","):
        part = part.strip()
        if not part:
            continue

        label, count = part.rsplit(":", 1)
        output[label.strip()] = int(count.strip())

    return output


def _status(condition: bool) -> str:
    return "PASS" if condition else "FAIL"


def _add_check(
    rows: list[dict[str, Any]],
    *,
    check_name: str,
    passed: bool,
    detail: str,
) -> None:
    rows.append(
        {
            "check_name": check_name,
            "status": _status(passed),
            "detail": detail,
        }
    )


def _count_rows_by_field(rows: list[dict[str, str]], field: str) -> Counter[str]:
    return Counter(str(row.get(field, "")) for row in rows)


def _find_risky_wording(paths: list[Path]) -> list[dict[str, Any]]:
    compiled = [
        (pattern, re.compile(pattern, flags=re.IGNORECASE))
        for pattern in RISKY_WORDING_PATTERNS
    ]

    hits: list[dict[str, Any]] = []

    for path in paths:
        if not path.exists() or not path.is_file():
            continue

        if path.suffix.lower() not in {".py", ".md", ".csv", ".json"}:
            continue

        text = path.read_text(encoding="utf-8", errors="replace")

        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern, regex in compiled:
                if regex.search(line):
                    hits.append(
                        {
                            "path": str(path),
                            "line_number": line_number,
                            "pattern": pattern,
                            "line": line.strip(),
                        }
                    )

    return hits


def _blocked_column_hits(csv_paths: list[Path]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []

    for path in csv_paths:
        if not path.exists():
            continue

        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for column in reader.fieldnames or []:
                column_lower = column.lower()
                if any(fragment in column_lower for fragment in BLOCKED_COLUMN_FRAGMENTS):
                    hits.append(
                        {
                            "path": str(path),
                            "column": column,
                        }
                    )

    return hits


def _validate_required_files(checks: list[dict[str, Any]]) -> None:
    for path in REQUIRED_FILES:
        _add_check(
            checks,
            check_name=f"required_file_exists::{path}",
            passed=path.exists(),
            detail=f"exists={path.exists()}",
        )


def _validate_manifest_row_counts(
    checks: list[dict[str, Any]],
    *,
    manifest_path: Path,
    csv_map: dict[str, Path],
) -> None:
    manifest = _load_json(manifest_path)

    _add_check(
        checks,
        check_name=f"manifest_real_api_calls_zero::{manifest_path}",
        passed=manifest.get("real_api_calls") == 0,
        detail=f"real_api_calls={manifest.get('real_api_calls')}",
    )

    for key, csv_path in csv_map.items():
        rows = _read_csv(csv_path)
        expected = manifest["row_counts"][key]
        actual = len(rows)

        _add_check(
            checks,
            check_name=f"manifest_row_count::{key}",
            passed=actual == expected,
            detail=f"actual={actual}; expected={expected}; path={csv_path}",
        )


def _validate_stage_manifest_flags(checks: list[dict[str, Any]]) -> None:
    manifest_path = Path("reports/pilot_03_stage_cascade/manifest.json")
    manifest = _load_json(manifest_path)

    _add_check(
        checks,
        check_name="stage_cascade_raw_prompt_response_export_flag_false",
        passed=manifest.get("raw_prompt_or_response_columns_exported") is False,
        detail=f"raw_prompt_or_response_columns_exported={manifest.get('raw_prompt_or_response_columns_exported')}",
    )


def _validate_glm_condition_vs_chain(checks: list[dict[str, Any]]) -> None:
    condition_rows = _read_csv(Path("reports/pilot_03_real_glm_t0020_condition_summary.csv"))
    chain_rows = _read_csv(Path("reports/pilot_03_stage_cascade/glm20_sanitized_chain_summary.csv"))

    chain_by_condition: dict[str, list[dict[str, str]]] = {}

    for row in chain_rows:
        chain_by_condition.setdefault(row["condition"], []).append(row)

    for condition_row in condition_rows:
        condition = condition_row["condition"]
        rows = chain_by_condition.get(condition, [])

        n_expected = _int_value(condition_row["n"])
        decision_expected = _int_value(condition_row["decision_correct"])
        escalation_expected = _int_value(condition_row["escalation_correct"])
        valid_expected = _int_value(condition_row["valid_chain"])
        audit_expected_map = _parse_count_map(condition_row["audit_passed"])

        n_actual = len(rows)
        decision_actual = sum(_is_true(row["decision_correct"]) for row in rows)
        escalation_actual = sum(_is_true(row["escalation_correct"]) for row in rows)
        valid_actual = sum(_is_true(row["stages_present"]) for row in rows)
        audit_actual_map = dict(_count_rows_by_field(rows, "audit_passed"))

        _add_check(
            checks,
            check_name=f"glm_condition_vs_chain_n::{condition}",
            passed=n_actual == n_expected,
            detail=f"actual={n_actual}; expected={n_expected}",
        )
        _add_check(
            checks,
            check_name=f"glm_condition_vs_chain_decision_correct::{condition}",
            passed=decision_actual == decision_expected,
            detail=f"actual={decision_actual}; expected={decision_expected}",
        )
        _add_check(
            checks,
            check_name=f"glm_condition_vs_chain_escalation_correct::{condition}",
            passed=escalation_actual == escalation_expected,
            detail=f"actual={escalation_actual}; expected={escalation_expected}",
        )
        _add_check(
            checks,
            check_name=f"glm_condition_vs_chain_valid_chain::{condition}",
            passed=valid_actual == valid_expected,
            detail=f"actual={valid_actual}; expected={valid_expected}",
        )
        _add_check(
            checks,
            check_name=f"glm_condition_vs_chain_audit_passed::{condition}",
            passed=audit_actual_map == audit_expected_map,
            detail=f"actual={audit_actual_map}; expected={audit_expected_map}",
        )


def _validate_shared_comparison_vs_chain(checks: list[dict[str, Any]]) -> None:
    comparison_rows = _read_csv(
        Path("reports/pilot_03_glm_vs_claude_comparison/shared_5_task_condition_comparison.csv")
    )
    chain_rows = _read_csv(Path("reports/pilot_03_stage_cascade/shared5_sanitized_chain_summary.csv"))

    chain_by_provider_condition: dict[tuple[str, str], list[dict[str, str]]] = {}

    for row in chain_rows:
        key = (row["provider"], row["condition"])
        chain_by_provider_condition.setdefault(key, []).append(row)

    for comparison_row in comparison_rows:
        provider = comparison_row["provider"]
        condition = comparison_row["condition"]
        key = (provider, condition)
        rows = chain_by_provider_condition.get(key, [])

        n_expected = _int_value(comparison_row["n_chains"])
        decision_expected = _int_value(comparison_row["decision_correct_count"])
        escalation_expected = _int_value(comparison_row["escalation_correct_count"])
        audit_true_expected = _int_value(comparison_row["audit_passed_true_count"])
        valid_expected = _int_value(comparison_row["valid_chain_count"])

        n_actual = len(rows)
        decision_actual = sum(_is_true(row["decision_correct"]) for row in rows)
        escalation_actual = sum(_is_true(row["escalation_correct"]) for row in rows)
        audit_true_actual = sum(_is_true(row["audit_passed"]) for row in rows)
        valid_actual = sum(_is_true(row["stages_present"]) for row in rows)

        prefix = f"shared_comparison_vs_chain::{provider}::{condition}"

        _add_check(
            checks,
            check_name=f"{prefix}::n",
            passed=n_actual == n_expected,
            detail=f"actual={n_actual}; expected={n_expected}",
        )
        _add_check(
            checks,
            check_name=f"{prefix}::decision_correct",
            passed=decision_actual == decision_expected,
            detail=f"actual={decision_actual}; expected={decision_expected}",
        )
        _add_check(
            checks,
            check_name=f"{prefix}::escalation_correct",
            passed=escalation_actual == escalation_expected,
            detail=f"actual={escalation_actual}; expected={escalation_expected}",
        )
        _add_check(
            checks,
            check_name=f"{prefix}::audit_passed_true",
            passed=audit_true_actual == audit_true_expected,
            detail=f"actual={audit_true_actual}; expected={audit_true_expected}",
        )
        _add_check(
            checks,
            check_name=f"{prefix}::valid_chain",
            passed=valid_actual == valid_expected,
            detail=f"actual={valid_actual}; expected={valid_expected}",
        )


def _validate_blocked_columns(checks: list[dict[str, Any]]) -> list[dict[str, str]]:
    csv_paths = [
        Path("reports/pilot_03_stage_cascade/glm20_sanitized_chain_summary.csv"),
        Path("reports/pilot_03_stage_cascade/shared5_sanitized_chain_summary.csv"),
        Path("reports/pilot_03_stage_cascade/cascade_pattern_summary.csv"),
        Path("reports/pilot_03_stage_cascade/stage_transition_summary.csv"),
    ]
    hits = _blocked_column_hits(csv_paths)

    _add_check(
        checks,
        check_name="blocked_raw_prompt_response_like_columns",
        passed=len(hits) == 0,
        detail=f"hits={hits}",
    )

    return hits


def _validate_risky_wording(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        Path("experiments/pilot_03_generate_uncertainty_tables.py"),
        Path("experiments/pilot_03_generate_stage_cascade_tables.py"),
        Path("reports/pilot_03_uncertainty/uncertainty_tables_report.md"),
        Path("reports/pilot_03_stage_cascade/stage_cascade_report.md"),
        Path("reports/pilot_03_stage_cascade/manifest.json"),
        Path("reports/pilot_03_uncertainty/manifest.json"),
    ]

    hits = _find_risky_wording(paths)

    _add_check(
        checks,
        check_name="risky_public_wording_absent",
        passed=len(hits) == 0,
        detail=f"hit_count={len(hits)}",
    )

    return hits


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")

    return lines


def _write_report(
    path: Path,
    *,
    checks: list[dict[str, Any]],
    manifest: dict[str, Any],
    risky_hits: list[dict[str, Any]],
    blocked_hits: list[dict[str, str]],
) -> None:
    failed = [row for row in checks if row["status"] != "PASS"]

    lines: list[str] = [
        "# Pilot 03 committed-output validation report",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        f"Validation status: **{'PASS' if not failed else 'FAIL'}**",
        "",
        "## Checks",
        "",
    ]

    lines.extend(_markdown_table(checks, ["check_name", "status", "detail"]))

    lines.extend(
        [
            "",
            "## Risky wording hits",
            "",
        ]
    )

    if risky_hits:
        lines.extend(_markdown_table(risky_hits, ["path", "line_number", "pattern", "line"]))
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Blocked column hits",
            "",
        ]
    )

    if blocked_hits:
        lines.extend(_markdown_table(blocked_hits, ["path", "column"]))
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Manifest",
            "",
            "```json",
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
            "```",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def validate_committed_outputs(*, output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    _validate_required_files(checks)

    _validate_manifest_row_counts(
        checks,
        manifest_path=Path("reports/pilot_03_uncertainty/manifest.json"),
        csv_map={
            "glm_condition_uncertainty": Path("reports/pilot_03_uncertainty/glm20_condition_uncertainty.csv"),
            "shared_provider_condition_uncertainty": Path(
                "reports/pilot_03_uncertainty/shared5_provider_condition_uncertainty.csv"
            ),
            "condition_difference_uncertainty": Path(
                "reports/pilot_03_uncertainty/condition_difference_uncertainty.csv"
            ),
            "provider_difference_uncertainty": Path(
                "reports/pilot_03_uncertainty/shared5_provider_difference_uncertainty.csv"
            ),
        },
    )

    _validate_manifest_row_counts(
        checks,
        manifest_path=Path("reports/pilot_03_stage_cascade/manifest.json"),
        csv_map={
            "glm20_sanitized_chain_summary": Path(
                "reports/pilot_03_stage_cascade/glm20_sanitized_chain_summary.csv"
            ),
            "shared5_sanitized_chain_summary": Path(
                "reports/pilot_03_stage_cascade/shared5_sanitized_chain_summary.csv"
            ),
            "cascade_pattern_summary": Path("reports/pilot_03_stage_cascade/cascade_pattern_summary.csv"),
            "stage_transition_summary": Path("reports/pilot_03_stage_cascade/stage_transition_summary.csv"),
        },
    )

    _validate_stage_manifest_flags(checks)
    _validate_glm_condition_vs_chain(checks)
    _validate_shared_comparison_vs_chain(checks)
    blocked_hits = _validate_blocked_columns(checks)
    risky_hits = _validate_risky_wording(checks)

    failed = [row for row in checks if row["status"] != "PASS"]

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "validation_results_csv": output_dir / "validation_results.csv",
        "validation_report_md": output_dir / "committed_output_validation_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "real_api_calls": 0,
        "safe_note": SAFE_NOTE,
        "status": "PASS" if not failed else "FAIL",
        "n_checks": len(checks),
        "n_failed_checks": len(failed),
        "n_risky_wording_hits": len(risky_hits),
        "n_blocked_column_hits": len(blocked_hits),
        "outputs": {name: str(path) for name, path in outputs.items()},
    }

    _write_csv(
        outputs["validation_results_csv"],
        checks,
        ["check_name", "status", "detail"],
    )

    outputs["manifest_json"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    _write_report(
        outputs["validation_report_md"],
        checks=checks,
        manifest=manifest,
        risky_hits=risky_hits,
        blocked_hits=blocked_hits,
    )

    if failed:
        failed_names = [row["check_name"] for row in failed]
        raise SystemExit(f"Committed-output validation failed: {failed_names}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate committed Pilot 03 report outputs for internal consistency. "
            "This command makes no real API calls."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = validate_committed_outputs(output_dir=Path(args.output_dir))

    print("Pilot 03 committed-output validation completed.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"n_checks: {manifest['n_checks']}")
    print(f"n_failed_checks: {manifest['n_failed_checks']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
