from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_PAIRED_CHAIN_CSV = Path("reports/pilot_03_glm_vs_claude_t0020_full/paired_chain_comparison.csv")
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_reliability_cascade_metrics")

CONDITIONS = [
    "original_evidence",
    "missing_policy_rule",
    "missing_one_required_unit",
]

MODELS = [
    {
        "provider": "zai",
        "model_name": "glm-5.2",
        "prefix": "glm",
        "label": "GLM-5.2",
    },
    {
        "provider": "anthropic",
        "model_name": "claude-opus-4-8",
        "prefix": "claude",
        "label": "Claude Opus 4.8",
    },
]

SAFE_NOTE = (
    "Reliability cascade metrics for the controlled Pilot 03 20-task comparison. "
    "Metrics are computed from committed sanitized paired-chain outputs only and should not be interpreted "
    "as broad deployment evidence or broad cross-provider conclusions."
)

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

BLOCKED_COLUMN_FRAGMENTS = [
    "raw",
    "prompt",
    "response",
    "api_key",
    "secret",
    "token",
]

METRIC_DEFINITIONS = [
    {
        "metric": "valid_chain_rate",
        "definition": "Share of selected chains with both valid JSON and valid schema indicators.",
    },
    {
        "metric": "decision_correct_rate",
        "definition": "Share of chains where the decision-stage final decision matched the gold decision.",
    },
    {
        "metric": "decision_failure_rate",
        "definition": "Share of chains where the decision-stage final decision did not match the gold decision.",
    },
    {
        "metric": "audit_pass_rate",
        "definition": "Share of chains where the audit stage returned pass.",
    },
    {
        "metric": "audit_false_assurance_rate",
        "definition": "Share of chains where the audit stage passed although the decision-stage output was incorrect.",
    },
    {
        "metric": "audit_detection_rate_on_decision_failure",
        "definition": "Among decision-stage failures, share where audit did not pass.",
    },
    {
        "metric": "undetected_decision_failure_rate",
        "definition": "Share of all chains where the decision-stage output was incorrect and audit still passed.",
    },
    {
        "metric": "escalation_correct_rate",
        "definition": "Share of chains where the escalation-stage final decision matched the gold decision.",
    },
    {
        "metric": "escalation_recovery_rate_on_decision_failure",
        "definition": "Among decision-stage failures, share recovered to the correct decision at escalation.",
    },
    {
        "metric": "escalation_loss_rate_on_decision_success",
        "definition": "Among decision-stage successes, share that became incorrect at escalation.",
    },
    {
        "metric": "cascade_failure_rate",
        "definition": "Share of chains where the escalation-stage final decision was incorrect.",
    },
    {
        "metric": "net_escalation_gain_rate",
        "definition": "Escalation correct rate minus decision correct rate.",
    },
]


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


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def _existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            created = existing.get("created_at_utc")
            if created:
                return str(created)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _rate(successes: int, n: int) -> float | None:
    if n == 0:
        return None
    return round(successes / n, 6)


def _safe_div(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _blocked_columns(columns: list[str]) -> list[str]:
    hits = []

    for column in columns:
        lowered = column.lower()
        if any(fragment in lowered for fragment in BLOCKED_COLUMN_FRAGMENTS):
            hits.append(column)

    return hits


def _scan_risky_wording(paths: list[Path]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []

    for path in paths:
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8", errors="replace")

        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for pattern in RISKY_WORDING:
                if pattern.lower() in lowered:
                    hits.append(
                        {
                            "path": str(path),
                            "line_number": line_number,
                            "pattern": pattern,
                            "line": line.strip(),
                        }
                    )

    return hits


def _validate_source_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != 60:
        raise SystemExit(f"Expected 60 paired chain rows, found {len(rows)}.")

    keys = {(row["task_id"], row["condition"]) for row in rows}
    if len(keys) != 60:
        raise SystemExit(f"Expected 60 unique task-condition keys, found {len(keys)}.")

    condition_counts = Counter(row["condition"] for row in rows)
    expected_counts = {
        "original_evidence": 20,
        "missing_policy_rule": 20,
        "missing_one_required_unit": 20,
    }

    if dict(condition_counts) != expected_counts:
        raise SystemExit(f"Unexpected condition counts: {dict(condition_counts)}")

    required_columns = {
        "task_id",
        "condition",
        "gold_decision",
    }

    for model in MODELS:
        prefix = model["prefix"]
        required_columns.update(
            {
                f"{prefix}_decision_correct",
                f"{prefix}_escalation_correct",
                f"{prefix}_audit_passed",
                f"{prefix}_valid_json_chain",
                f"{prefix}_valid_schema_chain",
            }
        )

    missing = sorted(required_columns - set(rows[0].keys()))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    blocked_source_columns = _blocked_columns(list(rows[0].keys()))
    if blocked_source_columns:
        raise SystemExit(f"Blocked source columns found: {blocked_source_columns}")


def _model_condition_metric_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for model in MODELS:
        prefix = model["prefix"]

        for condition in CONDITIONS:
            condition_rows = [row for row in rows if row["condition"] == condition]
            n = len(condition_rows)

            decision_correct_count = sum(_is_true(row[f"{prefix}_decision_correct"]) for row in condition_rows)
            decision_failure_count = n - decision_correct_count

            escalation_correct_count = sum(_is_true(row[f"{prefix}_escalation_correct"]) for row in condition_rows)
            cascade_failure_count = n - escalation_correct_count

            audit_pass_count = sum(_is_true(row[f"{prefix}_audit_passed"]) for row in condition_rows)

            valid_chain_count = sum(
                _is_true(row[f"{prefix}_valid_json_chain"])
                and _is_true(row[f"{prefix}_valid_schema_chain"])
                for row in condition_rows
            )

            audit_false_assurance_count = sum(
                (not _is_true(row[f"{prefix}_decision_correct"]))
                and _is_true(row[f"{prefix}_audit_passed"])
                for row in condition_rows
            )

            audit_detected_decision_failure_count = sum(
                (not _is_true(row[f"{prefix}_decision_correct"]))
                and (not _is_true(row[f"{prefix}_audit_passed"]))
                for row in condition_rows
            )

            escalation_recovered_count = sum(
                (not _is_true(row[f"{prefix}_decision_correct"]))
                and _is_true(row[f"{prefix}_escalation_correct"])
                for row in condition_rows
            )

            escalation_lost_count = sum(
                _is_true(row[f"{prefix}_decision_correct"])
                and (not _is_true(row[f"{prefix}_escalation_correct"]))
                for row in condition_rows
            )

            net_escalation_gain_rate = (
                _rate(escalation_correct_count, n) - _rate(decision_correct_count, n)
                if n
                else None
            )

            output.append(
                {
                    "provider": model["provider"],
                    "model_name": model["model_name"],
                    "model_label": model["label"],
                    "condition": condition,
                    "n_chains": n,
                    "valid_chain_count": valid_chain_count,
                    "valid_chain_rate": _rate(valid_chain_count, n),
                    "decision_correct_count": decision_correct_count,
                    "decision_correct_rate": _rate(decision_correct_count, n),
                    "decision_failure_count": decision_failure_count,
                    "decision_failure_rate": _rate(decision_failure_count, n),
                    "audit_pass_count": audit_pass_count,
                    "audit_pass_rate": _rate(audit_pass_count, n),
                    "audit_false_assurance_count": audit_false_assurance_count,
                    "audit_false_assurance_rate": _rate(audit_false_assurance_count, n),
                    "audit_detected_decision_failure_count": audit_detected_decision_failure_count,
                    "audit_detection_rate_on_decision_failure": _safe_div(
                        audit_detected_decision_failure_count,
                        decision_failure_count,
                    ),
                    "undetected_decision_failure_count": audit_false_assurance_count,
                    "undetected_decision_failure_rate": _rate(audit_false_assurance_count, n),
                    "escalation_correct_count": escalation_correct_count,
                    "escalation_correct_rate": _rate(escalation_correct_count, n),
                    "escalation_recovered_decision_failure_count": escalation_recovered_count,
                    "escalation_recovery_rate_on_decision_failure": _safe_div(
                        escalation_recovered_count,
                        decision_failure_count,
                    ),
                    "escalation_lost_decision_success_count": escalation_lost_count,
                    "escalation_loss_rate_on_decision_success": _safe_div(
                        escalation_lost_count,
                        decision_correct_count,
                    ),
                    "cascade_failure_count": cascade_failure_count,
                    "cascade_failure_rate": _rate(cascade_failure_count, n),
                    "net_escalation_gain_rate": _round(net_escalation_gain_rate),
                    "safe_note": SAFE_NOTE,
                }
            )

    return output


def _evidence_condition_delta_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = [
        "decision_correct_rate",
        "decision_failure_rate",
        "audit_pass_rate",
        "audit_false_assurance_rate",
        "undetected_decision_failure_rate",
        "escalation_correct_rate",
        "cascade_failure_rate",
        "net_escalation_gain_rate",
    ]

    output: list[dict[str, Any]] = []

    baseline = {
        (row["model_name"], row["condition"]): row
        for row in metric_rows
    }

    for model in MODELS:
        model_name = model["model_name"]
        original = baseline[(model_name, "original_evidence")]

        for condition in CONDITIONS:
            current = baseline[(model_name, condition)]

            for metric in metrics:
                original_value = original[metric]
                current_value = current[metric]

                delta = None
                if original_value is not None and current_value is not None:
                    delta = round(float(current_value) - float(original_value), 6)

                output.append(
                    {
                        "provider": model["provider"],
                        "model_name": model_name,
                        "condition": condition,
                        "baseline_condition": "original_evidence",
                        "metric": metric,
                        "baseline_value": original_value,
                        "condition_value": current_value,
                        "condition_minus_baseline": delta,
                        "safe_note": SAFE_NOTE,
                    }
                )

    return output


def _cross_model_comparison_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = [
        "valid_chain_rate",
        "decision_correct_rate",
        "decision_failure_rate",
        "audit_pass_rate",
        "audit_false_assurance_rate",
        "undetected_decision_failure_rate",
        "escalation_correct_rate",
        "escalation_recovery_rate_on_decision_failure",
        "cascade_failure_rate",
        "net_escalation_gain_rate",
    ]

    by_key = {
        (row["model_name"], row["condition"]): row
        for row in metric_rows
    }

    output: list[dict[str, Any]] = []

    for condition in CONDITIONS:
        glm = by_key[("glm-5.2", condition)]
        claude = by_key[("claude-opus-4-8", condition)]

        for metric in metrics:
            glm_value = glm[metric]
            claude_value = claude[metric]

            difference = None
            if glm_value is not None and claude_value is not None:
                difference = round(float(claude_value) - float(glm_value), 6)

            output.append(
                {
                    "condition": condition,
                    "metric": metric,
                    "glm_5_2_value": glm_value,
                    "claude_opus_4_8_value": claude_value,
                    "claude_minus_glm": difference,
                    "comparison_scope": "same_20_tasks_same_evidence_condition_descriptive_difference",
                    "safe_note": SAFE_NOTE,
                }
            )

    return output


def _metric_definition_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": row["metric"],
            "definition": row["definition"],
            "safe_note": SAFE_NOTE,
        }
        for row in METRIC_DEFINITIONS
    ]


def _write_report(
    path: Path,
    *,
    manifest: dict[str, Any],
    metric_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Pilot 03 reliability cascade metrics",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        "The metrics summarize how decision-stage errors, audit behavior, and escalation-stage outcomes interact "
        "under each evidence condition.",
        "",
        "## Model-condition cascade metrics",
        "",
        "| Model | Condition | Decision failure | Audit false assurance | Undetected decision failure | Escalation recovery on decision failure | Cascade failure | Net escalation gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in metric_rows:
        lines.append(
            f"| {row['model_name']} | {row['condition']} | "
            f"{row['decision_failure_count']} ({row['decision_failure_rate']}) | "
            f"{row['audit_false_assurance_count']} ({row['audit_false_assurance_rate']}) | "
            f"{row['undetected_decision_failure_count']} ({row['undetected_decision_failure_rate']}) | "
            f"{row['escalation_recovered_decision_failure_count']} ({row['escalation_recovery_rate_on_decision_failure']}) | "
            f"{row['cascade_failure_count']} ({row['cascade_failure_rate']}) | "
            f"{row['net_escalation_gain_rate']} |"
        )

    lines.extend(
        [
            "",
            "## Evidence-condition deltas from original evidence",
            "",
            "| Model | Condition | Metric | Baseline | Condition value | Delta |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )

    for row in delta_rows:
        if row["condition"] == "original_evidence":
            continue

        lines.append(
            f"| {row['model_name']} | {row['condition']} | {row['metric']} | "
            f"{row['baseline_value']} | {row['condition_value']} | {row['condition_minus_baseline']} |"
        )

    lines.extend(
        [
            "",
            "## Descriptive cross-model cascade differences",
            "",
            "Positive values mean the Anthropic/Claude value is higher than the GLM-5.2 value under the same condition.",
            "",
            "| Condition | Metric | GLM-5.2 | Claude Opus 4.8 | Claude minus GLM |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )

    for row in comparison_rows:
        lines.append(
            f"| {row['condition']} | {row['metric']} | {row['glm_5_2_value']} | "
            f"{row['claude_opus_4_8_value']} | {row['claude_minus_glm']} |"
        )

    lines.extend(
        [
            "",
            "## Metric definitions",
            "",
            "| Metric | Definition |",
            "| --- | --- |",
        ]
    )

    for row in METRIC_DEFINITIONS:
        lines.append(f"| {row['metric']} | {row['definition']} |")

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


def generate_reliability_cascade_metrics(
    *,
    paired_chain_csv: Path,
    output_dir: Path,
) -> dict[str, Any]:
    rows = _read_csv(paired_chain_csv)
    _validate_source_rows(rows)

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "model_condition_cascade_metrics_csv": output_dir / "model_condition_cascade_metrics.csv",
        "evidence_condition_delta_metrics_csv": output_dir / "evidence_condition_delta_metrics.csv",
        "cross_model_cascade_comparison_csv": output_dir / "cross_model_cascade_comparison.csv",
        "metric_definitions_csv": output_dir / "metric_definitions.csv",
        "report_md": output_dir / "reliability_cascade_metrics_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    metric_rows = _model_condition_metric_rows(rows)
    delta_rows = _evidence_condition_delta_rows(metric_rows)
    comparison_rows = _cross_model_comparison_rows(metric_rows)
    definition_rows = _metric_definition_rows()

    export_column_sets = [
        list(metric_rows[0].keys()) if metric_rows else [],
        list(delta_rows[0].keys()) if delta_rows else [],
        list(comparison_rows[0].keys()) if comparison_rows else [],
        list(definition_rows[0].keys()) if definition_rows else [],
    ]

    blocked_export_columns = []
    for columns in export_column_sets:
        blocked_export_columns.extend(_blocked_columns(columns))

    if blocked_export_columns:
        raise SystemExit(f"Blocked export columns found: {blocked_export_columns}")

    manifest = {
        "created_at_utc": _existing_created_at(outputs["manifest_json"]),
        "status": "PASS",
        "scope": "Pilot 03 reliability cascade metrics for full 20-task GLM-5.2 and Anthropic/Claude comparison",
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "source_files": {
            "paired_chain_csv": str(paired_chain_csv),
        },
        "source_policy": "committed sanitized paired-chain comparison CSV only",
        "row_counts": {
            "paired_chain_rows": len(rows),
            "model_condition_cascade_metrics": len(metric_rows),
            "evidence_condition_delta_metrics": len(delta_rows),
            "cross_model_cascade_comparison": len(comparison_rows),
            "metric_definitions": len(definition_rows),
        },
        "metrics": [row["metric"] for row in METRIC_DEFINITIONS],
        "safe_note": SAFE_NOTE,
        "outputs": {name: str(path) for name, path in outputs.items()},
    }

    _write_csv(outputs["model_condition_cascade_metrics_csv"], metric_rows)
    _write_csv(outputs["evidence_condition_delta_metrics_csv"], delta_rows)
    _write_csv(outputs["cross_model_cascade_comparison_csv"], comparison_rows)
    _write_csv(outputs["metric_definitions_csv"], definition_rows)
    _write_json(outputs["manifest_json"], manifest)

    _write_report(
        outputs["report_md"],
        manifest=manifest,
        metric_rows=metric_rows,
        delta_rows=delta_rows,
        comparison_rows=comparison_rows,
    )

    risky_hits = _scan_risky_wording(
        [
            outputs["model_condition_cascade_metrics_csv"],
            outputs["evidence_condition_delta_metrics_csv"],
            outputs["cross_model_cascade_comparison_csv"],
            outputs["metric_definitions_csv"],
            outputs["report_md"],
            outputs["manifest_json"],
        ]
    )

    if risky_hits:
        raise SystemExit(f"Risky wording hits found: {risky_hits}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate reliability cascade metrics for the full 20-task GLM-5.2 vs Anthropic/Claude Pilot 03 comparison. "
            "This command makes no real API calls."
        )
    )
    parser.add_argument("--paired-chain-csv", default=str(DEFAULT_PAIRED_CHAIN_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = generate_reliability_cascade_metrics(
        paired_chain_csv=Path(args.paired_chain_csv),
        output_dir=Path(args.output_dir),
    )

    print("Pilot 03 reliability cascade metrics generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
