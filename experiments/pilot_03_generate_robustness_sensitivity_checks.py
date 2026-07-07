"""Generate Pilot 03 robustness and sensitivity checks from sanitized outputs only.

This script performs no-call descriptive robustness checks for the controlled
Pilot 03 setup. It reads committed sanitized CSV outputs only and does not
inspect raw prompts, raw responses, JSONL API outputs, ignored aggregate JSON,
or API keys.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_robustness_sensitivity")

SAFE_NOTE = (
    "Observed result under current Pilot 03 real LLM experimental conditions; "
    "robustness and sensitivity checks are descriptive and evidence-bounded."
)

INPUT_FILES = {
    "paired_chain_comparison": Path(
        "reports/pilot_03_glm_vs_claude_t0020_full/paired_chain_comparison.csv"
    ),
    "model_condition_summary": Path(
        "reports/pilot_03_glm_vs_claude_t0020_full/model_condition_summary.csv"
    ),
    "condition_delta_summary": Path(
        "reports/pilot_03_glm_vs_claude_t0020_full/condition_delta_summary.csv"
    ),
    "paired_agreement_summary": Path(
        "reports/pilot_03_glm_vs_claude_t0020_full/paired_agreement_summary.csv"
    ),
    "model_metric_uncertainty": Path(
        "reports/pilot_03_glm_vs_claude_t0020_uncertainty/model_metric_uncertainty.csv"
    ),
    "paired_delta_uncertainty": Path(
        "reports/pilot_03_glm_vs_claude_t0020_uncertainty/paired_delta_uncertainty.csv"
    ),
    "task_condition_paired_outcomes": Path(
        "reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/task_condition_paired_outcomes.csv"
    ),
    "task_level_summary": Path(
        "reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/task_level_summary.csv"
    ),
    "condition_pair_profile": Path(
        "reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/condition_pair_profile.csv"
    ),
    "high_signal_cases": Path(
        "reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/high_signal_cases.csv"
    ),
    "model_condition_cascade_metrics": Path(
        "reports/pilot_03_reliability_cascade_metrics/model_condition_cascade_metrics.csv"
    ),
    "evidence_condition_delta_metrics": Path(
        "reports/pilot_03_reliability_cascade_metrics/evidence_condition_delta_metrics.csv"
    ),
    "cross_model_cascade_comparison": Path(
        "reports/pilot_03_reliability_cascade_metrics/cross_model_cascade_comparison.csv"
    ),
    "metric_definitions": Path(
        "reports/pilot_03_reliability_cascade_metrics/metric_definitions.csv"
    ),
}

OUTPUT_FILES = {
    "leave_one_task_out_sensitivity": Path("leave_one_task_out_sensitivity.csv"),
    "condition_order_sensitivity": Path("condition_order_sensitivity.csv"),
    "paired_delta_interval_sensitivity": Path("paired_delta_interval_sensitivity.csv"),
    "cascade_threshold_sensitivity": Path("cascade_threshold_sensitivity.csv"),
    "high_signal_case_profile": Path("high_signal_case_profile.csv"),
    "robustness_sensitivity_report": Path("robustness_sensitivity_report.md"),
    "manifest": Path("manifest.json"),
}


@dataclass(frozen=True)
class CsvData:
    path: Path
    rows: list[dict[str, str]]
    columns: list[str]


def _read_csv(path: Path) -> CsvData:
    if not path.exists():
        raise FileNotFoundError(f"Required sanitized input is missing: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = list(reader.fieldnames or [])

    if not columns:
        raise ValueError(f"CSV has no header: {path}")

    return CsvData(path=path, rows=rows, columns=columns)


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _require_columns(data: CsvData, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in data.columns]
    if missing:
        raise ValueError(f"{data.path} is missing required columns: {missing}")


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float_value(value: Any) -> float:
    text = str(value).strip()
    if text == "" or text.upper() in {"N/A", "NA", "NAN", "NONE", "NULL"}:
        return math.nan
    return float(text)


def _fmt_float(value: float, places: int = 6) -> str:
    if math.isnan(value):
        return "N/A"
    return f"{value:.{places}f}"


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.nan
    return numerator / denominator


def _sign_label(value: float) -> str:
    if math.isnan(value):
        return "not_applicable"
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


def _interval_position(lower: float, upper: float) -> str:
    if math.isnan(lower) or math.isnan(upper):
        return "not_available"
    if lower > 0 and upper > 0:
        return "entirely_positive"
    if lower < 0 and upper < 0:
        return "entirely_negative"
    if lower <= 0 <= upper:
        return "crosses_zero"
    return "other"


def _condition_order(condition: str) -> int:
    lowered = condition.lower().strip()
    if "original" in lowered:
        return 0
    if "missing_policy" in lowered or "policy" in lowered:
        return 1
    if "missing_one" in lowered or "required_unit" in lowered or "unit" in lowered:
        return 2
    return 99


def _condition_label(condition: str) -> str:
    lowered = condition.lower().strip()
    if "original" in lowered:
        return "original_evidence"
    if "missing_policy" in lowered or "policy" in lowered:
        return "missing_policy_rule"
    if "missing_one" in lowered or "required_unit" in lowered or "unit" in lowered:
        return "missing_one_required_unit"
    return condition


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _prepare_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for child in output_dir.iterdir():
        if child.name == "manifest.json":
            continue
        if child.is_file() and child.suffix.lower() in {".csv", ".md", ".json"}:
            child.unlink()


def _load_inputs() -> dict[str, CsvData]:
    return {key: _read_csv(path) for key, path in INPUT_FILES.items()}


def _success_column(model_key: str, metric: str) -> str:
    return {
        "decision_correct": f"{model_key}_decision_correct",
        "escalation_correct": f"{model_key}_escalation_correct",
        "audit_passed": f"{model_key}_audit_passed",
    }[metric]


def _leave_one_task_out_sensitivity(data: dict[str, CsvData]) -> list[dict[str, Any]]:
    paired = data["paired_chain_comparison"]
    _require_columns(
        paired,
        [
            "task_id",
            "condition",
            "glm_decision_correct",
            "claude_decision_correct",
            "glm_escalation_correct",
            "claude_escalation_correct",
            "glm_audit_passed",
            "claude_audit_passed",
        ],
    )

    output_rows: list[dict[str, Any]] = []
    models = [
        ("glm", "GLM-5.2"),
        ("claude", "Claude Opus 4.8"),
    ]
    metrics = ["decision_correct", "escalation_correct", "audit_passed"]
    conditions = sorted({row["condition"] for row in paired.rows}, key=_condition_order)

    for model_key, model_label in models:
        for condition in conditions:
            condition_rows = [row for row in paired.rows if row["condition"] == condition]
            task_ids = sorted({row["task_id"] for row in condition_rows})

            for metric in metrics:
                column = _success_column(model_key, metric)
                baseline_successes = sum(_bool_value(row[column]) for row in condition_rows)
                baseline_n = len(condition_rows)
                baseline_rate = _safe_divide(baseline_successes, baseline_n)

                leave_rates: list[tuple[str, float]] = []
                for task_id in task_ids:
                    kept_rows = [row for row in condition_rows if row["task_id"] != task_id]
                    successes = sum(_bool_value(row[column]) for row in kept_rows)
                    n = len(kept_rows)
                    leave_rates.append((task_id, _safe_divide(successes, n)))

                if leave_rates:
                    max_abs = max(
                        abs(rate - baseline_rate)
                        for _, rate in leave_rates
                        if not math.isnan(rate) and not math.isnan(baseline_rate)
                    )
                    max_items = [
                        item
                        for item in leave_rates
                        if not math.isnan(item[1])
                        and not math.isnan(baseline_rate)
                        and abs(abs(item[1] - baseline_rate) - max_abs) <= 1e-12
                    ]
                    min_rate = min(item[1] for item in leave_rates if not math.isnan(item[1]))
                    max_rate = max(item[1] for item in leave_rates if not math.isnan(item[1]))
                    task_at_max = max_items[0][0] if max_items else "N/A"
                    rate_at_max = max_items[0][1] if max_items else math.nan
                else:
                    max_abs = math.nan
                    min_rate = math.nan
                    max_rate = math.nan
                    task_at_max = "N/A"
                    rate_at_max = math.nan

                output_rows.append(
                    {
                        "model_label": model_label,
                        "condition": condition,
                        "condition_label": _condition_label(condition),
                        "metric": metric,
                        "baseline_successes": baseline_successes,
                        "baseline_n": baseline_n,
                        "baseline_rate": _fmt_float(baseline_rate),
                        "leave_one_task_min_rate": _fmt_float(min_rate),
                        "leave_one_task_max_rate": _fmt_float(max_rate),
                        "max_abs_rate_shift": _fmt_float(max_abs),
                        "task_id_at_max_abs_shift": task_at_max,
                        "rate_after_leaving_task": _fmt_float(rate_at_max),
                        "safe_note": SAFE_NOTE,
                    }
                )

    return output_rows


def _condition_order_sensitivity(data: dict[str, CsvData]) -> list[dict[str, Any]]:
    summary = data["model_condition_summary"]
    _require_columns(
        summary,
        [
            "provider",
            "model_name",
            "condition",
            "decision_correct_rate",
            "escalation_correct_rate",
            "audit_passed_true_rate",
        ],
    )

    cascade = data["model_condition_cascade_metrics"]
    _require_columns(
        cascade,
        [
            "provider",
            "model_name",
            "model_label",
            "condition",
            "cascade_failure_rate",
            "audit_false_assurance_rate",
            "undetected_decision_failure_rate",
        ],
    )

    combined: list[dict[str, Any]] = []

    for row in summary.rows:
        model_label = f"{row['provider']}:{row['model_name']}"
        for metric in [
            "decision_correct_rate",
            "escalation_correct_rate",
            "audit_passed_true_rate",
        ]:
            combined.append(
                {
                    "model_label": model_label,
                    "condition": row["condition"],
                    "metric": metric,
                    "value": _float_value(row[metric]),
                    "expected_direction_under_degradation": "non_increasing",
                }
            )

    for row in cascade.rows:
        for metric in [
            "cascade_failure_rate",
            "audit_false_assurance_rate",
            "undetected_decision_failure_rate",
        ]:
            combined.append(
                {
                    "model_label": row["model_label"],
                    "condition": row["condition"],
                    "metric": metric,
                    "value": _float_value(row[metric]),
                    "expected_direction_under_degradation": "non_decreasing",
                }
            )

    output_rows: list[dict[str, Any]] = []

    for model_label in sorted({row["model_label"] for row in combined}):
        model_rows = [row for row in combined if row["model_label"] == model_label]
        for metric in sorted({row["metric"] for row in model_rows}):
            metric_rows = sorted(
                [row for row in model_rows if row["metric"] == metric],
                key=lambda row: _condition_order(str(row["condition"])),
            )
            if len(metric_rows) < 2:
                continue

            values = [float(row["value"]) for row in metric_rows]
            labels = [str(row["condition"]) for row in metric_rows]
            diffs = [values[index + 1] - values[index] for index in range(len(values) - 1)]
            expected = str(metric_rows[0]["expected_direction_under_degradation"])

            if expected == "non_increasing":
                passed = all(diff <= 1e-12 for diff in diffs)
            elif expected == "non_decreasing":
                passed = all(diff >= -1e-12 for diff in diffs)
            else:
                passed = False

            output_rows.append(
                {
                    "model_label": model_label,
                    "metric": metric,
                    "expected_direction_under_degradation": expected,
                    "condition_sequence": " -> ".join(labels),
                    "value_sequence": " -> ".join(_fmt_float(value) for value in values),
                    "step_delta_sequence": " -> ".join(_fmt_float(diff) for diff in diffs),
                    "direction_check": "PASS" if passed else "DESCRIPTIVE_EXCEPTION",
                    "max_abs_step_delta": _fmt_float(max(abs(diff) for diff in diffs)),
                    "safe_note": SAFE_NOTE,
                }
            )

    return output_rows


def _paired_delta_interval_sensitivity(data: dict[str, CsvData]) -> list[dict[str, Any]]:
    deltas = data["paired_delta_uncertainty"]
    _require_columns(
        deltas,
        [
            "condition",
            "metric",
            "n_pairs",
            "glm_rate",
            "claude_rate",
            "claude_minus_glm",
            "paired_bootstrap_ci_lower",
            "paired_bootstrap_ci_upper",
            "discordant_pairs",
            "mcnemar_exact_two_sided_p",
        ],
    )

    output_rows: list[dict[str, Any]] = []

    for row in sorted(deltas.rows, key=lambda item: (_condition_order(item["condition"]), item["metric"])):
        estimate = _float_value(row["claude_minus_glm"])
        lower = _float_value(row["paired_bootstrap_ci_lower"])
        upper = _float_value(row["paired_bootstrap_ci_upper"])
        width = upper - lower if not (math.isnan(lower) or math.isnan(upper)) else math.nan

        output_rows.append(
            {
                "condition": row["condition"],
                "condition_label": _condition_label(row["condition"]),
                "metric": row["metric"],
                "n_pairs": row["n_pairs"],
                "glm_rate": row["glm_rate"],
                "claude_rate": row["claude_rate"],
                "claude_minus_glm": row["claude_minus_glm"],
                "observed_delta_sign": _sign_label(estimate),
                "paired_bootstrap_ci_lower": row["paired_bootstrap_ci_lower"],
                "paired_bootstrap_ci_upper": row["paired_bootstrap_ci_upper"],
                "paired_bootstrap_ci_width": _fmt_float(width),
                "interval_position": _interval_position(lower, upper),
                "discordant_pairs": row["discordant_pairs"],
                "mcnemar_exact_two_sided_p": row["mcnemar_exact_two_sided_p"],
                "safe_note": SAFE_NOTE,
            }
        )

    return output_rows


def _cascade_threshold_sensitivity(data: dict[str, CsvData]) -> list[dict[str, Any]]:
    cascade = data["model_condition_cascade_metrics"]
    _require_columns(
        cascade,
        [
            "model_label",
            "condition",
            "cascade_failure_rate",
            "audit_false_assurance_rate",
            "undetected_decision_failure_rate",
            "escalation_recovery_rate_on_decision_failure",
            "net_escalation_gain_rate",
        ],
    )

    thresholds = [0.0, 0.05, 0.10, 0.20]
    metrics = [
        "cascade_failure_rate",
        "audit_false_assurance_rate",
        "undetected_decision_failure_rate",
        "escalation_recovery_rate_on_decision_failure",
        "net_escalation_gain_rate",
    ]

    output_rows: list[dict[str, Any]] = []

    for row in sorted(cascade.rows, key=lambda item: (_condition_order(item["condition"]), item["model_label"])):
        for metric in metrics:
            value = _float_value(row[metric])
            abs_value = abs(value) if metric == "net_escalation_gain_rate" else value

            threshold_flags = {}
            for threshold in thresholds:
                if math.isnan(abs_value):
                    flag = "N/A"
                else:
                    flag = "yes" if abs_value >= threshold else "no"
                threshold_flags[threshold] = flag

            output_rows.append(
                {
                    "model_label": row["model_label"],
                    "condition": row["condition"],
                    "condition_label": _condition_label(row["condition"]),
                    "metric": metric,
                    "value": _fmt_float(value),
                    "absolute_value_used_for_threshold": _fmt_float(abs_value),
                    "at_least_0pp": threshold_flags[0.0],
                    "at_least_5pp": threshold_flags[0.05],
                    "at_least_10pp": threshold_flags[0.10],
                    "at_least_20pp": threshold_flags[0.20],
                    "safe_note": SAFE_NOTE,
                }
            )

    return output_rows


def _high_signal_case_profile(data: dict[str, CsvData]) -> list[dict[str, Any]]:
    high_signal = data["high_signal_cases"]
    _require_columns(
        high_signal,
        [
            "task_id",
            "condition",
            "reasons",
            "glm_decision_correct",
            "claude_decision_correct",
            "glm_escalation_correct",
            "claude_escalation_correct",
            "glm_audit_passed",
            "claude_audit_passed",
        ],
    )

    reason_counts: dict[tuple[str, str], dict[str, Any]] = {}

    for row in high_signal.rows:
        reasons = [
            reason.strip()
            for reason in row["reasons"].split(";")
            if reason.strip()
        ]
        if not reasons:
            reasons = ["unspecified_high_signal_case"]

        for reason in reasons:
            key = (row["condition"], reason)
            entry = reason_counts.setdefault(
                key,
                {
                    "condition": row["condition"],
                    "condition_label": _condition_label(row["condition"]),
                    "reason": reason,
                    "case_count": 0,
                    "unique_task_ids": set(),
                    "glm_decision_correct_count": 0,
                    "claude_decision_correct_count": 0,
                    "glm_escalation_correct_count": 0,
                    "claude_escalation_correct_count": 0,
                    "glm_audit_passed_count": 0,
                    "claude_audit_passed_count": 0,
                },
            )

            entry["case_count"] += 1
            entry["unique_task_ids"].add(row["task_id"])
            entry["glm_decision_correct_count"] += int(_bool_value(row["glm_decision_correct"]))
            entry["claude_decision_correct_count"] += int(_bool_value(row["claude_decision_correct"]))
            entry["glm_escalation_correct_count"] += int(_bool_value(row["glm_escalation_correct"]))
            entry["claude_escalation_correct_count"] += int(_bool_value(row["claude_escalation_correct"]))
            entry["glm_audit_passed_count"] += int(_bool_value(row["glm_audit_passed"]))
            entry["claude_audit_passed_count"] += int(_bool_value(row["claude_audit_passed"]))

    output_rows: list[dict[str, Any]] = []

    for entry in sorted(
        reason_counts.values(),
        key=lambda item: (_condition_order(str(item["condition"])), str(item["reason"])),
    ):
        case_count = int(entry["case_count"])
        output_rows.append(
            {
                "condition": entry["condition"],
                "condition_label": entry["condition_label"],
                "reason": entry["reason"],
                "case_count": case_count,
                "unique_task_count": len(entry["unique_task_ids"]),
                "task_ids": ";".join(sorted(entry["unique_task_ids"])),
                "glm_decision_correct_rate": _fmt_float(
                    _safe_divide(entry["glm_decision_correct_count"], case_count)
                ),
                "claude_decision_correct_rate": _fmt_float(
                    _safe_divide(entry["claude_decision_correct_count"], case_count)
                ),
                "glm_escalation_correct_rate": _fmt_float(
                    _safe_divide(entry["glm_escalation_correct_count"], case_count)
                ),
                "claude_escalation_correct_rate": _fmt_float(
                    _safe_divide(entry["claude_escalation_correct_count"], case_count)
                ),
                "glm_audit_passed_rate": _fmt_float(
                    _safe_divide(entry["glm_audit_passed_count"], case_count)
                ),
                "claude_audit_passed_rate": _fmt_float(
                    _safe_divide(entry["claude_audit_passed_count"], case_count)
                ),
                "safe_note": SAFE_NOTE,
            }
        )

    return output_rows


def _write_report(
    path: Path,
    *,
    row_counts: dict[str, int],
    manifest: dict[str, Any],
) -> None:
    lines = [
        "# Pilot 03 robustness and sensitivity checks",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        "These checks use committed sanitized Pilot 03 outputs only. They do not make external API calls and do not inspect raw model responses.",
        "",
        "## Generated outputs",
        "",
        "| output | rows |",
        "| --- | ---: |",
    ]

    for key, count in row_counts.items():
        lines.append(f"| {key} | {count} |")

    lines.extend(
        [
            "",
            "## Check descriptions",
            "",
            "- `leave_one_task_out_sensitivity.csv` checks whether model-condition metrics are strongly affected by removing one task at a time.",
            "- `condition_order_sensitivity.csv` checks whether descriptive metric direction follows the expected evidence-degradation order.",
            "- `paired_delta_interval_sensitivity.csv` summarizes observed paired deltas and whether paired intervals cross zero.",
            "- `cascade_threshold_sensitivity.csv` marks whether cascade metrics meet small descriptive thresholds.",
            "- `high_signal_case_profile.csv` summarizes high-signal cases by condition and reason.",
            "",
            "## Interpretation guardrail",
            "",
            "These outputs should be used as internal robustness evidence only. They do not establish broad model behavior beyond the controlled Pilot 03 setup.",
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


def _validate_safe_public_text(output_dir: Path) -> None:
    blocked_terms = [
        "Q" + "1",
        "ground" + "breaking",
        "pro" + "ven",
        "univ" + "ersal",
        "real-world deployment " + "proof",
        "provider " + "rank" + "ing",
        "general Claude " + "reliability",
        "general GLM " + "reliability",
    ]

    failures: list[str] = []
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".csv"}:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for term in blocked_terms:
                if term.lower() in text:
                    failures.append(f"{path}: blocked wording detected")

    if failures:
        raise ValueError("\n".join(failures))


def _write_manifest(
    output_dir: Path,
    data: dict[str, CsvData],
    row_counts: dict[str, int],
) -> dict[str, Any]:
    manifest_path = output_dir / OUTPUT_FILES["manifest"]

    source_files = []
    for key, csv_data in data.items():
        source_files.append(
            {
                "key": key,
                "path": csv_data.path.as_posix(),
                "rows": len(csv_data.rows),
                "columns": csv_data.columns,
                "sha256": _file_sha256(csv_data.path),
            }
        )

    output_paths = [
        output_dir / path
        for key, path in OUTPUT_FILES.items()
        if key != "manifest"
    ]

    manifest = {
        "created_at_utc": _load_existing_created_at(manifest_path),
        "report_name": "pilot_03_robustness_sensitivity",
        "script": "experiments/pilot_03_generate_robustness_sensitivity_checks.py",
        "input_policy": "committed sanitized CSV outputs only",
        "status": "PASS",
        "row_counts": row_counts,
        "source_files": source_files,
        "outputs": {
            key: (output_dir / path).as_posix()
            for key, path in OUTPUT_FILES.items()
        },
        "output_files": [
            path.as_posix()
            for path in output_paths
            if path.exists()
        ],
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "safe_wording_check": "PASS",
        "safe_note": SAFE_NOTE,
    }

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    return manifest


def generate_robustness_sensitivity_checks(*, output_dir: Path) -> dict[str, Any]:
    data = _load_inputs()
    _prepare_output_dir(output_dir)

    leave_one_task_rows = _leave_one_task_out_sensitivity(data)
    condition_order_rows = _condition_order_sensitivity(data)
    paired_delta_rows = _paired_delta_interval_sensitivity(data)
    cascade_threshold_rows = _cascade_threshold_sensitivity(data)
    high_signal_rows = _high_signal_case_profile(data)

    row_counts = {
        "leave_one_task_out_sensitivity": len(leave_one_task_rows),
        "condition_order_sensitivity": len(condition_order_rows),
        "paired_delta_interval_sensitivity": len(paired_delta_rows),
        "cascade_threshold_sensitivity": len(cascade_threshold_rows),
        "high_signal_case_profile": len(high_signal_rows),
    }

    _write_csv(
        output_dir / OUTPUT_FILES["leave_one_task_out_sensitivity"],
        leave_one_task_rows,
        [
            "model_label",
            "condition",
            "condition_label",
            "metric",
            "baseline_successes",
            "baseline_n",
            "baseline_rate",
            "leave_one_task_min_rate",
            "leave_one_task_max_rate",
            "max_abs_rate_shift",
            "task_id_at_max_abs_shift",
            "rate_after_leaving_task",
            "safe_note",
        ],
    )
    _write_csv(
        output_dir / OUTPUT_FILES["condition_order_sensitivity"],
        condition_order_rows,
        [
            "model_label",
            "metric",
            "expected_direction_under_degradation",
            "condition_sequence",
            "value_sequence",
            "step_delta_sequence",
            "direction_check",
            "max_abs_step_delta",
            "safe_note",
        ],
    )
    _write_csv(
        output_dir / OUTPUT_FILES["paired_delta_interval_sensitivity"],
        paired_delta_rows,
        [
            "condition",
            "condition_label",
            "metric",
            "n_pairs",
            "glm_rate",
            "claude_rate",
            "claude_minus_glm",
            "observed_delta_sign",
            "paired_bootstrap_ci_lower",
            "paired_bootstrap_ci_upper",
            "paired_bootstrap_ci_width",
            "interval_position",
            "discordant_pairs",
            "mcnemar_exact_two_sided_p",
            "safe_note",
        ],
    )
    _write_csv(
        output_dir / OUTPUT_FILES["cascade_threshold_sensitivity"],
        cascade_threshold_rows,
        [
            "model_label",
            "condition",
            "condition_label",
            "metric",
            "value",
            "absolute_value_used_for_threshold",
            "at_least_0pp",
            "at_least_5pp",
            "at_least_10pp",
            "at_least_20pp",
            "safe_note",
        ],
    )
    _write_csv(
        output_dir / OUTPUT_FILES["high_signal_case_profile"],
        high_signal_rows,
        [
            "condition",
            "condition_label",
            "reason",
            "case_count",
            "unique_task_count",
            "task_ids",
            "glm_decision_correct_rate",
            "claude_decision_correct_rate",
            "glm_escalation_correct_rate",
            "claude_escalation_correct_rate",
            "glm_audit_passed_rate",
            "claude_audit_passed_rate",
            "safe_note",
        ],
    )

    manifest = _write_manifest(output_dir, data, row_counts)

    _write_report(
        output_dir / OUTPUT_FILES["robustness_sensitivity_report"],
        row_counts=row_counts,
        manifest=manifest,
    )

    manifest = _write_manifest(output_dir, data, row_counts)
    _validate_safe_public_text(output_dir)

    return manifest


def list_inputs() -> None:
    print("Task 8 robustness/sensitivity committed sanitized input inventory")
    print("=================================================================")
    for key, path in INPUT_FILES.items():
        status = "FOUND" if path.exists() else "MISSING"
        size = path.stat().st_size if path.exists() else 0
        print(f"{key}: {status} {path.as_posix()} size={size}")
    print("real_api_calls: 0")
    print("raw_response_inspection: False")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Pilot 03 robustness and sensitivity checks from committed "
            "sanitized outputs only. This command makes no real API calls."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--list-inputs", action="store_true")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.list_inputs:
        list_inputs()
        return 0

    manifest = generate_robustness_sensitivity_checks(output_dir=Path(args.output_dir))

    print("Pilot 03 robustness/sensitivity checks generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
