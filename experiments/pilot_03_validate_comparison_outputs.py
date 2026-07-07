"""Validate Pilot 03 comparison, cascade, and final-figure committed outputs.

This validator checks committed sanitized derived outputs only. It makes no
external API calls and does not inspect raw prompts, raw responses, JSONL API
outputs, ignored aggregate JSON, or API keys.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_comparison_validation")

SAFE_NOTE = (
    "Validation report for committed Pilot 03 comparison outputs. This command "
    "checks internal consistency only and makes no real API calls."
)

BLOCKED_COLUMN_FRAGMENTS = [
    "raw",
    "prompt",
    "response",
    "api_key",
    "secret",
    "token",
]

RISKY_WORDING_PATTERNS = [
    r"\b" + "Q" + "1" + r"\b",
    "journal-" + "level",
    "ground" + "breaking",
    r"\bpro" + "ven" + r"\b",
    r"\buniv" + "ersal" + r"\b",
    r"\bsuper" + "ior" + r"\b",
    "real-world deployment " + "proof",
    "provider " + "rank" + "ing",
    "general GLM " + "reliability",
    "general Claude " + "reliability",
]

EXPECTED_CSVS = {
    "full_paired_chain_comparison": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_full/paired_chain_comparison.csv"),
        "rows": 60,
        "columns": [
            "task_id",
            "condition",
            "gold_decision",
            "glm_decision_correct",
            "claude_decision_correct",
            "glm_escalation_correct",
            "claude_escalation_correct",
            "glm_audit_passed",
            "claude_audit_passed",
            "glm_valid_json_chain",
            "claude_valid_json_chain",
            "glm_valid_schema_chain",
            "claude_valid_schema_chain",
            "safe_note",
        ],
    },
    "full_model_condition_summary": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_full/model_condition_summary.csv"),
        "rows": 6,
        "columns": [
            "provider",
            "model_name",
            "condition",
            "n_chains",
            "decision_correct_count",
            "decision_correct_rate",
            "escalation_correct_count",
            "escalation_correct_rate",
            "audit_passed_true_count",
            "audit_passed_true_rate",
            "valid_json_chain_count",
            "valid_json_chain_rate",
            "valid_schema_chain_count",
            "valid_schema_chain_rate",
            "safe_note",
        ],
    },
    "full_condition_delta_summary": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_full/condition_delta_summary.csv"),
        "rows": 15,
        "columns": [
            "condition",
            "metric",
            "glm_5_2_value",
            "claude_opus_4_8_value",
            "claude_minus_glm",
            "absolute_difference",
            "comparison_scope",
            "safe_note",
        ],
    },
    "full_paired_agreement_summary": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_full/paired_agreement_summary.csv"),
        "rows": 9,
        "columns": [
            "condition",
            "metric",
            "n_pairs",
            "agreement_count",
            "agreement_rate",
            "safe_note",
        ],
    },
    "full_failure_pattern_comparison": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_full/failure_pattern_comparison.csv"),
        "rows": 15,
        "columns": [
            "provider",
            "model_name",
            "condition",
            "pattern",
            "n",
            "condition_n",
            "condition_rate",
            "task_ids",
            "safe_note",
        ],
    },
    "uncertainty_model_metric_uncertainty": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_uncertainty/model_metric_uncertainty.csv"),
        "rows": 30,
        "columns": [
            "provider",
            "model_name",
            "model_label",
            "condition",
            "metric",
            "successes",
            "n",
            "estimate",
            "ci_method",
            "ci_lower",
            "ci_upper",
            "interpretation",
            "safe_note",
        ],
    },
    "uncertainty_paired_delta_uncertainty": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_uncertainty/paired_delta_uncertainty.csv"),
        "rows": 15,
        "columns": [
            "condition",
            "metric",
            "n_pairs",
            "glm_successes",
            "claude_successes",
            "glm_rate",
            "claude_rate",
            "claude_minus_glm",
            "paired_bootstrap_ci_lower",
            "paired_bootstrap_ci_upper",
            "safe_note",
        ],
    },
    "paired_task_condition_paired_outcomes": {
        "path": Path(
            "reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/task_condition_paired_outcomes.csv"
        ),
        "rows": 60,
        "columns": [
            "task_id",
            "condition",
            "gold_decision",
            "glm_decision_correct",
            "claude_decision_correct",
            "glm_escalation_correct",
            "claude_escalation_correct",
            "glm_audit_passed",
            "claude_audit_passed",
            "decision_pair_outcome",
            "escalation_pair_outcome",
            "audit_pair_outcome",
            "safe_note",
        ],
    },
    "paired_task_level_summary": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/task_level_summary.csv"),
        "rows": 20,
        "columns": [
            "task_id",
            "task_type",
            "n_conditions",
            "conditions",
            "decision_disagreement_count",
            "escalation_disagreement_count",
            "audit_disagreement_count",
            "task_pattern",
            "safe_note",
        ],
    },
    "paired_condition_pair_profile": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/condition_pair_profile.csv"),
        "rows": 3,
        "columns": [
            "condition",
            "n_pairs",
            "decision_both_correct_count",
            "decision_both_wrong_count",
            "decision_glm_only_correct_count",
            "decision_claude_only_correct_count",
            "escalation_both_correct_count",
            "escalation_both_wrong_count",
            "escalation_glm_only_correct_count",
            "escalation_claude_only_correct_count",
            "audit_both_passed_count",
            "audit_both_not_passed_count",
            "audit_glm_only_passed_count",
            "audit_claude_only_passed_count",
            "safe_note",
        ],
    },
    "paired_high_signal_cases": {
        "path": Path("reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/high_signal_cases.csv"),
        "rows": 24,
        "columns": [
            "task_id",
            "condition",
            "gold_decision",
            "reasons",
            "glm_decision_correct",
            "claude_decision_correct",
            "glm_escalation_correct",
            "claude_escalation_correct",
            "glm_audit_passed",
            "claude_audit_passed",
            "safe_note",
        ],
    },
    "cascade_model_condition_cascade_metrics": {
        "path": Path("reports/pilot_03_reliability_cascade_metrics/model_condition_cascade_metrics.csv"),
        "rows": 6,
        "columns": [
            "provider",
            "model_name",
            "model_label",
            "condition",
            "n_chains",
            "decision_correct_count",
            "decision_correct_rate",
            "decision_failure_count",
            "decision_failure_rate",
            "audit_false_assurance_count",
            "audit_false_assurance_rate",
            "undetected_decision_failure_count",
            "undetected_decision_failure_rate",
            "escalation_correct_count",
            "escalation_correct_rate",
            "cascade_failure_count",
            "cascade_failure_rate",
            "safe_note",
        ],
    },
    "cascade_evidence_condition_delta_metrics": {
        "path": Path("reports/pilot_03_reliability_cascade_metrics/evidence_condition_delta_metrics.csv"),
        "rows": 48,
        "columns": [
            "provider",
            "model_name",
            "condition",
            "baseline_condition",
            "metric",
            "baseline_value",
            "condition_value",
            "condition_minus_baseline",
            "safe_note",
        ],
    },
    "cascade_cross_model_cascade_comparison": {
        "path": Path("reports/pilot_03_reliability_cascade_metrics/cross_model_cascade_comparison.csv"),
        "rows": 30,
        "columns": [
            "condition",
            "metric",
            "glm_5_2_value",
            "claude_opus_4_8_value",
            "claude_minus_glm",
            "comparison_scope",
            "safe_note",
        ],
    },
    "cascade_metric_definitions": {
        "path": Path("reports/pilot_03_reliability_cascade_metrics/metric_definitions.csv"),
        "rows": 12,
        "columns": [
            "metric",
            "definition",
            "safe_note",
        ],
    },
}

EXPECTED_MANIFESTS = {
    "full_comparison": Path("reports/pilot_03_glm_vs_claude_t0020_full/manifest.json"),
    "uncertainty": Path("reports/pilot_03_glm_vs_claude_t0020_uncertainty/manifest.json"),
    "paired_task_analysis": Path("reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/manifest.json"),
    "cascade_metrics": Path("reports/pilot_03_reliability_cascade_metrics/manifest.json"),
    "final_figures": Path("reports/pilot_03_final_figures/manifest.json"),
}

TEXT_OUTPUTS_TO_SCAN = [
    Path("reports/pilot_03_glm_vs_claude_t0020_full/glm_vs_claude_t0020_full_comparison_report.md"),
    Path("reports/pilot_03_glm_vs_claude_t0020_uncertainty/glm_vs_claude_t0020_uncertainty_report.md"),
    Path("reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/paired_task_analysis_report.md"),
    Path("reports/pilot_03_reliability_cascade_metrics/reliability_cascade_metrics_report.md"),
    Path("reports/pilot_03_final_figures/figure_notes.md"),
    Path("reports/pilot_03_final_figures/manifest.json"),
]


@dataclass(frozen=True)
class CsvData:
    path: Path
    rows: list[dict[str, str]]
    columns: list[str]


def _status(condition: bool) -> str:
    return "PASS" if condition else "FAIL"


def _add_check(
    checks: list[dict[str, Any]],
    *,
    check_name: str,
    passed: bool,
    detail: str,
) -> None:
    checks.append(
        {
            "check_name": check_name,
            "status": _status(passed),
            "detail": detail,
        }
    )


def _read_csv(path: Path) -> CsvData:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = list(reader.fieldnames or [])

    return CsvData(path=path, rows=rows, columns=columns)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int_value(value: Any) -> int:
    text = str(value).strip()
    if text == "":
        return 0
    return int(round(float(text)))


def _float_value(value: Any) -> float:
    text = str(value).strip()
    if text == "" or text.upper() in {"N/A", "NA", "NAN", "NONE", "NULL"}:
        return math.nan
    return float(text)


def _close(left: Any, right: Any, *, tolerance: float = 1e-9) -> bool:
    left_value = _float_value(left)
    right_value = _float_value(right)
    return abs(left_value - right_value) <= tolerance


def _model_key_from_provider(provider: str) -> str:
    provider_lower = provider.strip().lower()
    if provider_lower == "zai":
        return "glm"
    if provider_lower == "anthropic":
        return "claude"
    return provider_lower


def _safe_note_nonempty(rows: list[dict[str, str]]) -> bool:
    return all(str(row.get("safe_note", "")).strip() for row in rows)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]

    for row in rows:
        values = [
            str(row.get(column, "")).replace("|", "\\|").replace("\n", " ")
            for column in columns
        ]
        lines.append("| " + " | ".join(values) + " |")

    return lines


def _load_existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = _load_json(path)
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _validate_required_files(checks: list[dict[str, Any]]) -> None:
    for key, spec in EXPECTED_CSVS.items():
        path = spec["path"]
        _add_check(
            checks,
            check_name=f"required_csv_exists::{key}",
            passed=path.exists(),
            detail=f"path={path}; exists={path.exists()}",
        )

    for key, path in EXPECTED_MANIFESTS.items():
        _add_check(
            checks,
            check_name=f"required_manifest_exists::{key}",
            passed=path.exists(),
            detail=f"path={path}; exists={path.exists()}",
        )

    notes_path = Path("reports/pilot_03_final_figures/figure_notes.md")
    _add_check(
        checks,
        check_name="required_final_figure_notes_exists",
        passed=notes_path.exists(),
        detail=f"path={notes_path}; exists={notes_path.exists()}",
    )


def _load_csvs(checks: list[dict[str, Any]]) -> dict[str, CsvData]:
    loaded: dict[str, CsvData] = {}

    for key, spec in EXPECTED_CSVS.items():
        path = spec["path"]
        if not path.exists():
            continue

        csv_data = _read_csv(path)
        loaded[key] = csv_data

        expected_rows = int(spec["rows"])
        missing_columns = [column for column in spec["columns"] if column not in csv_data.columns]

        _add_check(
            checks,
            check_name=f"csv_row_count::{key}",
            passed=len(csv_data.rows) == expected_rows,
            detail=f"actual={len(csv_data.rows)}; expected={expected_rows}; path={path}",
        )
        _add_check(
            checks,
            check_name=f"csv_required_columns::{key}",
            passed=not missing_columns,
            detail=f"missing_columns={missing_columns}; path={path}",
        )
        _add_check(
            checks,
            check_name=f"csv_safe_note_nonempty::{key}",
            passed=_safe_note_nonempty(csv_data.rows),
            detail=f"rows={len(csv_data.rows)}; path={path}",
        )

    return loaded


def _validate_manifests(checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}

    for key, path in EXPECTED_MANIFESTS.items():
        if not path.exists():
            continue

        manifest = _load_json(path)
        manifests[key] = manifest

        _add_check(
            checks,
            check_name=f"manifest_real_api_calls_zero::{key}",
            passed=manifest.get("real_api_calls") == 0,
            detail=f"path={path}; real_api_calls={manifest.get('real_api_calls')}",
        )
        _add_check(
            checks,
            check_name=f"manifest_raw_response_inspection_false::{key}",
            passed=manifest.get("raw_response_inspection") is False,
            detail=f"path={path}; raw_response_inspection={manifest.get('raw_response_inspection')}",
        )

        if key != "final_figures":
            _add_check(
                checks,
                check_name=f"manifest_status_pass::{key}",
                passed=manifest.get("status") == "PASS",
                detail=f"path={path}; status={manifest.get('status')}",
            )

    return manifests


def _validate_full_summary_against_paired(
    checks: list[dict[str, Any]],
    csvs: dict[str, CsvData],
) -> None:
    paired = csvs.get("full_paired_chain_comparison")
    summary = csvs.get("full_model_condition_summary")

    if not paired or not summary:
        return

    for summary_row in summary.rows:
        provider = summary_row["provider"]
        condition = summary_row["condition"]
        model_key = _model_key_from_provider(provider)

        matching = [row for row in paired.rows if row["condition"] == condition]

        n_actual = len(matching)
        decision_actual = sum(_bool_value(row[f"{model_key}_decision_correct"]) for row in matching)
        escalation_actual = sum(_bool_value(row[f"{model_key}_escalation_correct"]) for row in matching)
        audit_actual = sum(_bool_value(row[f"{model_key}_audit_passed"]) for row in matching)
        valid_json_actual = sum(_bool_value(row[f"{model_key}_valid_json_chain"]) for row in matching)
        valid_schema_actual = sum(_bool_value(row[f"{model_key}_valid_schema_chain"]) for row in matching)

        prefix = f"{provider}::{condition}"

        _add_check(
            checks,
            check_name=f"full_summary_n_chains_matches_paired::{prefix}",
            passed=n_actual == _int_value(summary_row["n_chains"]),
            detail=f"actual={n_actual}; expected={summary_row['n_chains']}",
        )
        _add_check(
            checks,
            check_name=f"full_summary_decision_matches_paired::{prefix}",
            passed=decision_actual == _int_value(summary_row["decision_correct_count"]),
            detail=f"actual={decision_actual}; expected={summary_row['decision_correct_count']}",
        )
        _add_check(
            checks,
            check_name=f"full_summary_escalation_matches_paired::{prefix}",
            passed=escalation_actual == _int_value(summary_row["escalation_correct_count"]),
            detail=f"actual={escalation_actual}; expected={summary_row['escalation_correct_count']}",
        )
        _add_check(
            checks,
            check_name=f"full_summary_audit_matches_paired::{prefix}",
            passed=audit_actual == _int_value(summary_row["audit_passed_true_count"]),
            detail=f"actual={audit_actual}; expected={summary_row['audit_passed_true_count']}",
        )
        _add_check(
            checks,
            check_name=f"full_summary_valid_json_matches_paired::{prefix}",
            passed=valid_json_actual == _int_value(summary_row["valid_json_chain_count"]),
            detail=f"actual={valid_json_actual}; expected={summary_row['valid_json_chain_count']}",
        )
        _add_check(
            checks,
            check_name=f"full_summary_valid_schema_matches_paired::{prefix}",
            passed=valid_schema_actual == _int_value(summary_row["valid_schema_chain_count"]),
            detail=f"actual={valid_schema_actual}; expected={summary_row['valid_schema_chain_count']}",
        )


def _validate_delta_arithmetic(
    checks: list[dict[str, Any]],
    csvs: dict[str, CsvData],
) -> None:
    delta_specs = [
        (
            "full_condition_delta_summary",
            "claude_minus_glm",
            lambda row: _float_value(row["claude_opus_4_8_value"]) - _float_value(row["glm_5_2_value"]),
        ),
        (
            "uncertainty_paired_delta_uncertainty",
            "claude_minus_glm",
            lambda row: _float_value(row["claude_rate"]) - _float_value(row["glm_rate"]),
        ),
        (
            "cascade_evidence_condition_delta_metrics",
            "condition_minus_baseline",
            lambda row: _float_value(row["condition_value"]) - _float_value(row["baseline_value"]),
        ),
        (
            "cascade_cross_model_cascade_comparison",
            "claude_minus_glm",
            lambda row: _float_value(row["claude_opus_4_8_value"]) - _float_value(row["glm_5_2_value"]),
        ),
    ]

    for key, column, expected_fn in delta_specs:
        data = csvs.get(key)
        if not data:
            continue

        failures = []
        for index, row in enumerate(data.rows, start=1):
            expected = expected_fn(row)
            actual = _float_value(row[column])
            if abs(actual - expected) > 1e-9:
                failures.append(f"row={index}; actual={actual}; expected={expected}")

        _add_check(
            checks,
            check_name=f"delta_arithmetic::{key}",
            passed=not failures,
            detail=f"n_failures={len(failures)}; first_failure={failures[:1]}",
        )


def _validate_rate_bounds_and_count_rates(
    checks: list[dict[str, Any]],
    csvs: dict[str, CsvData],
) -> None:
    count_rate_specs = {
        "full_model_condition_summary": [
            ("decision_correct_count", "decision_correct_rate", "n_chains"),
            ("escalation_correct_count", "escalation_correct_rate", "n_chains"),
            ("audit_passed_true_count", "audit_passed_true_rate", "n_chains"),
            ("valid_json_chain_count", "valid_json_chain_rate", "n_chains"),
            ("valid_schema_chain_count", "valid_schema_chain_rate", "n_chains"),
        ],
        "cascade_model_condition_cascade_metrics": [
            ("decision_correct_count", "decision_correct_rate", "n_chains"),
            ("decision_failure_count", "decision_failure_rate", "n_chains"),
            ("audit_false_assurance_count", "audit_false_assurance_rate", "n_chains"),
            ("undetected_decision_failure_count", "undetected_decision_failure_rate", "n_chains"),
            ("escalation_correct_count", "escalation_correct_rate", "n_chains"),
            ("cascade_failure_count", "cascade_failure_rate", "n_chains"),
        ],
        "full_paired_agreement_summary": [
            ("agreement_count", "agreement_rate", "n_pairs"),
        ],
    }

    rate_failures: list[str] = []

    for key, data in csvs.items():
        for row_index, row in enumerate(data.rows, start=1):
            for column, value in row.items():
                if column.endswith("_rate") or column in {"estimate", "ci_lower", "ci_upper"}:
                    parsed = _float_value(value)
                    if math.isnan(parsed):
                        continue

                    if column == "net_escalation_gain_rate":
                        in_bounds = -1.0 <= parsed <= 1.0
                    else:
                        in_bounds = 0.0 <= parsed <= 1.0

                    if not in_bounds:
                        rate_failures.append(f"{key}: row={row_index}; column={column}; value={value}")

    _add_check(
        checks,
        check_name="rate_columns_within_unit_interval",
        passed=not rate_failures,
        detail=f"n_failures={len(rate_failures)}; first_failure={rate_failures[:1]}",
    )

    for key, specs in count_rate_specs.items():
        data = csvs.get(key)
        if not data:
            continue

        failures = []
        for row_index, row in enumerate(data.rows, start=1):
            for count_column, rate_column, denominator_column in specs:
                denominator = _int_value(row[denominator_column])
                count = _int_value(row[count_column])
                expected_rate = 0.0 if denominator == 0 else count / denominator
                actual_rate = _float_value(row[rate_column])
                if abs(actual_rate - expected_rate) > 1e-9:
                    failures.append(
                        f"row={row_index}; {rate_column}={actual_rate}; expected={expected_rate}"
                    )

        _add_check(
            checks,
            check_name=f"count_rate_consistency::{key}",
            passed=not failures,
            detail=f"n_failures={len(failures)}; first_failure={failures[:1]}",
        )


def _validate_paired_profile_sums(
    checks: list[dict[str, Any]],
    csvs: dict[str, CsvData],
) -> None:
    profile = csvs.get("paired_condition_pair_profile")
    if not profile:
        return

    sum_specs = [
        (
            "decision",
            [
                "decision_both_correct_count",
                "decision_both_wrong_count",
                "decision_glm_only_correct_count",
                "decision_claude_only_correct_count",
            ],
        ),
        (
            "escalation",
            [
                "escalation_both_correct_count",
                "escalation_both_wrong_count",
                "escalation_glm_only_correct_count",
                "escalation_claude_only_correct_count",
            ],
        ),
        (
            "audit",
            [
                "audit_both_passed_count",
                "audit_both_not_passed_count",
                "audit_glm_only_passed_count",
                "audit_claude_only_passed_count",
            ],
        ),
    ]

    for label, columns in sum_specs:
        failures = []
        for row in profile.rows:
            n_pairs = _int_value(row["n_pairs"])
            total = sum(_int_value(row[column]) for column in columns)
            if total != n_pairs:
                failures.append(
                    f"condition={row['condition']}; total={total}; n_pairs={n_pairs}"
                )

        _add_check(
            checks,
            check_name=f"paired_condition_profile_sum::{label}",
            passed=not failures,
            detail=f"n_failures={len(failures)}; first_failure={failures[:1]}",
        )


def _validate_uncertainty_counts(
    checks: list[dict[str, Any]],
    csvs: dict[str, CsvData],
) -> None:
    data = csvs.get("uncertainty_model_metric_uncertainty")
    if not data:
        return

    failures = []
    for row_index, row in enumerate(data.rows, start=1):
        successes = _int_value(row["successes"])
        n = _int_value(row["n"])
        estimate = _float_value(row["estimate"])

        if successes < 0 or successes > n:
            failures.append(f"row={row_index}; successes={successes}; n={n}")

        expected_estimate = 0.0 if n == 0 else successes / n
        if abs(estimate - expected_estimate) > 1e-9:
            failures.append(
                f"row={row_index}; estimate={estimate}; expected={expected_estimate}"
            )

        lower = _float_value(row["ci_lower"])
        upper = _float_value(row["ci_upper"])
        if lower > estimate or estimate > upper:
            failures.append(
                f"row={row_index}; ci_lower={lower}; estimate={estimate}; ci_upper={upper}"
            )

    _add_check(
        checks,
        check_name="uncertainty_success_estimate_ci_consistency",
        passed=not failures,
        detail=f"n_failures={len(failures)}; first_failure={failures[:1]}",
    )


def _validate_final_figures(
    checks: list[dict[str, Any]],
    manifests: dict[str, dict[str, Any]],
) -> None:
    manifest = manifests.get("final_figures")
    if not manifest:
        return

    output_files = [Path(path) for path in manifest.get("output_files", [])]
    figures = manifest.get("figures", [])
    source_files = manifest.get("source_files", [])

    _add_check(
        checks,
        check_name="final_figures_report_name",
        passed=manifest.get("report_name") == "pilot_03_final_figures",
        detail=f"report_name={manifest.get('report_name')}",
    )
    _add_check(
        checks,
        check_name="final_figures_source_file_count",
        passed=len(source_files) == 7,
        detail=f"actual={len(source_files)}; expected=7",
    )
    _add_check(
        checks,
        check_name="final_figures_figure_count",
        passed=len(figures) == 7,
        detail=f"actual={len(figures)}; expected=7",
    )
    _add_check(
        checks,
        check_name="final_figures_output_count",
        passed=len(output_files) == 15,
        detail=f"actual={len(output_files)}; expected=15",
    )
    _add_check(
        checks,
        check_name="final_figures_paths_repo_relative",
        passed=all(not path.is_absolute() for path in output_files),
        detail=f"n_paths={len(output_files)}",
    )
    _add_check(
        checks,
        check_name="final_figures_all_outputs_exist",
        passed=all(path.exists() and path.stat().st_size > 0 for path in output_files),
        detail=f"n_paths={len(output_files)}",
    )
    _add_check(
        checks,
        check_name="final_figures_png_pdf_presence",
        passed=(
            sum(path.suffix.lower() == ".png" for path in output_files) == 7
            and sum(path.suffix.lower() == ".pdf" for path in output_files) == 7
            and any(path.name == "figure_notes.md" for path in output_files)
        ),
        detail=(
            f"png={sum(path.suffix.lower() == '.png' for path in output_files)}; "
            f"pdf={sum(path.suffix.lower() == '.pdf' for path in output_files)}"
        ),
    )


def _validate_blocked_columns(
    checks: list[dict[str, Any]],
    csvs: dict[str, CsvData],
) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []

    for csv_data in csvs.values():
        for column in csv_data.columns:
            lowered = column.lower()
            for fragment in BLOCKED_COLUMN_FRAGMENTS:
                if fragment in lowered:
                    hits.append({"path": str(csv_data.path), "column": column})
                    break

    _add_check(
        checks,
        check_name="blocked_raw_prompt_response_like_columns",
        passed=not hits,
        detail=f"n_hits={len(hits)}",
    )

    return hits


def _validate_risky_wording(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compiled = [
        (pattern, re.compile(pattern, flags=re.IGNORECASE))
        for pattern in RISKY_WORDING_PATTERNS
    ]

    paths = [
        path
        for path in TEXT_OUTPUTS_TO_SCAN
        if path.exists() and path.suffix.lower() in {".md", ".json"}
    ]

    hits: list[dict[str, Any]] = []

    for path in paths:
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

    _add_check(
        checks,
        check_name="risky_public_wording_absent",
        passed=not hits,
        detail=f"n_hits={len(hits)}",
    )

    return hits


def _write_report(
    path: Path,
    *,
    checks: list[dict[str, Any]],
    manifest: dict[str, Any],
    risky_hits: list[dict[str, Any]],
    blocked_hits: list[dict[str, str]],
) -> None:
    failed = [row for row in checks if row["status"] != "PASS"]

    lines = [
        "# Pilot 03 comparison-output validation report",
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

    lines.extend(["", "## Risky wording hits", ""])
    if risky_hits:
        lines.extend(_markdown_table(risky_hits, ["path", "line_number", "pattern", "line"]))
    else:
        lines.append("None.")

    lines.extend(["", "## Blocked column hits", ""])
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


def validate_comparison_outputs(*, output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    _validate_required_files(checks)
    csvs = _load_csvs(checks)
    manifests = _validate_manifests(checks)

    _validate_full_summary_against_paired(checks, csvs)
    _validate_delta_arithmetic(checks, csvs)
    _validate_rate_bounds_and_count_rates(checks, csvs)
    _validate_paired_profile_sums(checks, csvs)
    _validate_uncertainty_counts(checks, csvs)
    _validate_final_figures(checks, manifests)
    blocked_hits = _validate_blocked_columns(checks, csvs)
    risky_hits = _validate_risky_wording(checks)

    failed = [row for row in checks if row["status"] != "PASS"]

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "validation_results_csv": output_dir / "comparison_validation_results.csv",
        "validation_report_md": output_dir / "comparison_output_validation_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    manifest = {
        "created_at_utc": _load_existing_created_at(outputs["manifest_json"]),
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "safe_note": SAFE_NOTE,
        "status": "PASS" if not failed else "FAIL",
        "n_checks": len(checks),
        "n_failed_checks": len(failed),
        "n_risky_wording_hits": len(risky_hits),
        "n_blocked_column_hits": len(blocked_hits),
        "validated_csv_count": len(csvs),
        "validated_manifest_count": len(manifests),
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
        raise SystemExit(f"Comparison-output validation failed: {failed_names}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate committed Pilot 03 comparison outputs for internal consistency. "
            "This command makes no real API calls and does not inspect raw responses."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true", help="Print machine-readable validation output.")
    args = parser.parse_args()

    manifest = validate_comparison_outputs(output_dir=Path(args.output_dir))

    if args.json:
        print(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("Pilot 03 comparison-output validation completed.")
        print(f"output_dir: {args.output_dir}")
        print(f"status: {manifest['status']}")
        print(f"n_checks: {manifest['n_checks']}")
        print(f"n_failed_checks: {manifest['n_failed_checks']}")
        print(f"validated_csv_count: {manifest['validated_csv_count']}")
        print(f"validated_manifest_count: {manifest['validated_manifest_count']}")
        print(f"real_api_calls: {manifest['real_api_calls']}")
        print(f"raw_response_inspection: {manifest['raw_response_inspection']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
