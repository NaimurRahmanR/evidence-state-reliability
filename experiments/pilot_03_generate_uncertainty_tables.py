from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_GLM_CONDITION_CSV = Path("reports/pilot_03_real_glm_t0020_condition_summary.csv")
DEFAULT_SHARED_COMPARISON_CSV = Path(
    "reports/pilot_03_glm_vs_claude_comparison/shared_5_task_condition_comparison.csv"
)
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_uncertainty")

CONFIDENCE_LEVEL = 0.95
Z_95 = 1.959963984540054

SAFE_SCOPE_NOTE = (
    "Descriptive uncertainty intervals only. These tables are computed from committed "
    "Pilot 03 summary CSV files and should not be read as general model-performance "
    "claims, deployment evidence, or provider rankings."
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _int_value(value: str, *, field_name: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Could not parse integer field {field_name!r}: {value!r}") from exc


def _float_text(value: float) -> str:
    return f"{value:.6f}"


def _rate(successes: int, n: int) -> float:
    if n <= 0:
        return math.nan
    return successes / n


def _wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    This is used as a descriptive interval for small Pilot 03 count tables.
    It is not used to claim general provider superiority.
    """

    if n <= 0:
        return (math.nan, math.nan)

    p_hat = successes / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    centre = p_hat + z2 / (2.0 * n)
    margin = z * math.sqrt((p_hat * (1.0 - p_hat) + z2 / (4.0 * n)) / n)

    lower = (centre - margin) / denominator
    upper = (centre + margin) / denominator

    return (max(0.0, lower), min(1.0, upper))


def _difference_interval_from_wilson(
    successes_a: int,
    n_a: int,
    successes_b: int,
    n_b: int,
) -> tuple[float, float, float]:
    """Descriptive difference and Wilson-derived interval.

    The interval uses separate Wilson intervals for each proportion and combines them
    as lower_a - upper_b and upper_a - lower_b. This is intentionally conservative
    and descriptive. It is not a paired test and does not produce a p-value.
    """

    p_a = _rate(successes_a, n_a)
    p_b = _rate(successes_b, n_b)
    lower_a, upper_a = _wilson_interval(successes_a, n_a)
    lower_b, upper_b = _wilson_interval(successes_b, n_b)

    return (p_a - p_b, lower_a - upper_b, upper_a - lower_b)


def _glm_metric_specs() -> list[dict[str, str]]:
    return [
        {
            "metric": "decision_correct",
            "count_column": "decision_correct",
            "rate_column": "decision_correct_rate",
        },
        {
            "metric": "escalation_correct",
            "count_column": "escalation_correct",
            "rate_column": "escalation_correct_rate",
        },
        {
            "metric": "valid_chain",
            "count_column": "valid_chain",
            "rate_column": "valid_chain_rate",
        },
    ]


def _shared_metric_specs() -> list[dict[str, str]]:
    return [
        {
            "metric": "decision_correct",
            "count_column": "decision_correct_count",
            "rate_column": "decision_correct_rate",
        },
        {
            "metric": "escalation_correct",
            "count_column": "escalation_correct_count",
            "rate_column": "escalation_correct_rate",
        },
        {
            "metric": "audit_passed_true",
            "count_column": "audit_passed_true_count",
            "rate_column": "audit_passed_true_rate",
        },
        {
            "metric": "valid_chain",
            "count_column": "valid_chain_count",
            "rate_column": "valid_chain_rate",
        },
    ]


def make_glm_condition_uncertainty_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []

    for row in rows:
        n = _int_value(row["n"], field_name="n")

        for spec in _glm_metric_specs():
            successes = _int_value(row[spec["count_column"]], field_name=spec["count_column"])
            estimate = _rate(successes, n)
            lower, upper = _wilson_interval(successes, n)

            output_rows.append(
                {
                    "scope": "GLM 20-task checkpoint",
                    "provider": "zai",
                    "model": "glm-5.2",
                    "condition": row["condition"],
                    "metric": spec["metric"],
                    "successes": successes,
                    "n": n,
                    "estimate": _float_text(estimate),
                    "ci_method": "wilson_score_95",
                    "ci_lower": _float_text(lower),
                    "ci_upper": _float_text(upper),
                    "safe_note": SAFE_SCOPE_NOTE,
                }
            )

    return output_rows


def make_shared_provider_uncertainty_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []

    for row in rows:
        n = _int_value(row["n_chains"], field_name="n_chains")

        for spec in _shared_metric_specs():
            successes = _int_value(row[spec["count_column"]], field_name=spec["count_column"])
            estimate = _rate(successes, n)
            lower, upper = _wilson_interval(successes, n)

            output_rows.append(
                {
                    "scope": row["scope"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "condition": row["condition"],
                    "metric": spec["metric"],
                    "successes": successes,
                    "n": n,
                    "estimate": _float_text(estimate),
                    "ci_method": "wilson_score_95",
                    "ci_lower": _float_text(lower),
                    "ci_upper": _float_text(upper),
                    "safe_wording": row.get("safe_wording", ""),
                    "safe_note": SAFE_SCOPE_NOTE,
                }
            )

    return output_rows


def make_condition_difference_rows(
    uncertainty_rows: list[dict[str, Any]],
    *,
    scope_filter: str,
    provider_filter: str,
    model_filter: str,
    baseline_condition: str = "original_evidence",
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for row in uncertainty_rows:
        if row["scope"] != scope_filter:
            continue
        if row["provider"] != provider_filter:
            continue
        if row["model"] != model_filter:
            continue

        by_key[(row["condition"], row["metric"])] = row

    output_rows: list[dict[str, Any]] = []

    for (condition, metric), row in sorted(by_key.items()):
        if condition == baseline_condition:
            continue

        baseline = by_key.get((baseline_condition, metric))
        if baseline is None:
            continue

        successes_condition = int(row["successes"])
        n_condition = int(row["n"])
        successes_baseline = int(baseline["successes"])
        n_baseline = int(baseline["n"])

        difference, lower, upper = _difference_interval_from_wilson(
            successes_condition,
            n_condition,
            successes_baseline,
            n_baseline,
        )

        output_rows.append(
            {
                "scope": scope_filter,
                "provider": provider_filter,
                "model": model_filter,
                "baseline_condition": baseline_condition,
                "comparison_condition": condition,
                "metric": metric,
                "baseline_successes": successes_baseline,
                "baseline_n": n_baseline,
                "comparison_successes": successes_condition,
                "comparison_n": n_condition,
                "difference_comparison_minus_baseline": _float_text(difference),
                "difference_interval_method": "wilson_interval_difference_descriptive_95",
                "difference_ci_lower": _float_text(lower),
                "difference_ci_upper": _float_text(upper),
                "safe_note": SAFE_SCOPE_NOTE,
            }
        )

    return output_rows


def make_provider_difference_rows(
    shared_rows: list[dict[str, str]],
    *,
    provider_a: str = "anthropic",
    provider_b: str = "zai",
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}

    for row in shared_rows:
        for spec in _shared_metric_specs():
            by_key[(row["provider"], row["condition"], spec["metric"])] = row

    output_rows: list[dict[str, Any]] = []

    for row in shared_rows:
        if row["provider"] != provider_a:
            continue

        condition = row["condition"]

        for spec in _shared_metric_specs():
            metric = spec["metric"]
            other = by_key.get((provider_b, condition, metric))

            if other is None:
                continue

            successes_a = _int_value(row[spec["count_column"]], field_name=spec["count_column"])
            n_a = _int_value(row["n_chains"], field_name="n_chains")
            successes_b = _int_value(other[spec["count_column"]], field_name=spec["count_column"])
            n_b = _int_value(other["n_chains"], field_name="n_chains")

            difference, lower, upper = _difference_interval_from_wilson(
                successes_a,
                n_a,
                successes_b,
                n_b,
            )

            output_rows.append(
                {
                    "scope": "Shared 5-task comparison",
                    "condition": condition,
                    "metric": metric,
                    "provider_a": provider_a,
                    "model_a": row["model"],
                    "successes_a": successes_a,
                    "n_a": n_a,
                    "provider_b": provider_b,
                    "model_b": other["model"],
                    "successes_b": successes_b,
                    "n_b": n_b,
                    "difference_a_minus_b": _float_text(difference),
                    "difference_interval_method": "wilson_interval_difference_descriptive_95",
                    "difference_ci_lower": _float_text(lower),
                    "difference_ci_upper": _float_text(upper),
                    "safe_note": SAFE_SCOPE_NOTE,
                }
            )

    return output_rows


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")

    return lines


def write_report(
    output_path: Path,
    *,
    glm_uncertainty_rows: list[dict[str, Any]],
    shared_uncertainty_rows: list[dict[str, Any]],
    condition_difference_rows: list[dict[str, Any]],
    provider_difference_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    lines: list[str] = [
        "# Pilot 03 uncertainty tables",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_SCOPE_NOTE,
        "",
        "The intervals are descriptive summaries of the committed Pilot 03 count tables.",
        "No p-values, provider rankings, deployment claims, or broad generalisation claims are made here.",
        "",
        "## GLM 20-task condition intervals",
        "",
    ]

    lines.extend(
        _markdown_table(
            glm_uncertainty_rows,
            [
                "condition",
                "metric",
                "successes",
                "n",
                "estimate",
                "ci_method",
                "ci_lower",
                "ci_upper",
            ],
        )
    )

    lines.extend(["", "## Shared 5-task provider-condition intervals", ""])
    lines.extend(
        _markdown_table(
            shared_uncertainty_rows,
            [
                "provider",
                "model",
                "condition",
                "metric",
                "successes",
                "n",
                "estimate",
                "ci_method",
                "ci_lower",
                "ci_upper",
            ],
        )
    )

    lines.extend(["", "## Condition differences from original evidence", ""])
    lines.extend(
        _markdown_table(
            condition_difference_rows,
            [
                "scope",
                "provider",
                "model",
                "baseline_condition",
                "comparison_condition",
                "metric",
                "difference_comparison_minus_baseline",
                "difference_interval_method",
                "difference_ci_lower",
                "difference_ci_upper",
            ],
        )
    )

    lines.extend(["", "## Shared 5-task provider differences", ""])
    lines.extend(
        _markdown_table(
            provider_difference_rows,
            [
                "condition",
                "metric",
                "provider_a",
                "model_a",
                "successes_a",
                "n_a",
                "provider_b",
                "model_b",
                "successes_b",
                "n_b",
                "difference_a_minus_b",
                "difference_interval_method",
                "difference_ci_lower",
                "difference_ci_upper",
            ],
        )
    )

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

    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_uncertainty_tables(
    *,
    glm_condition_csv: Path,
    shared_comparison_csv: Path,
    output_dir: Path,
) -> dict[str, Any]:
    glm_rows = _read_csv(glm_condition_csv)
    shared_rows = _read_csv(shared_comparison_csv)

    glm_uncertainty_rows = make_glm_condition_uncertainty_rows(glm_rows)
    shared_uncertainty_rows = make_shared_provider_uncertainty_rows(shared_rows)

    condition_difference_rows: list[dict[str, Any]] = []
    condition_difference_rows.extend(
        make_condition_difference_rows(
            glm_uncertainty_rows,
            scope_filter="GLM 20-task checkpoint",
            provider_filter="zai",
            model_filter="glm-5.2",
        )
    )
    condition_difference_rows.extend(
        make_condition_difference_rows(
            shared_uncertainty_rows,
            scope_filter="Shared 5-task comparison",
            provider_filter="zai",
            model_filter="glm-5.2",
        )
    )
    condition_difference_rows.extend(
        make_condition_difference_rows(
            shared_uncertainty_rows,
            scope_filter="Shared 5-task comparison",
            provider_filter="anthropic",
            model_filter="claude-opus-4-8",
        )
    )

    provider_difference_rows = make_provider_difference_rows(shared_rows)

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "glm_condition_uncertainty_csv": output_dir / "glm20_condition_uncertainty.csv",
        "shared_provider_condition_uncertainty_csv": output_dir / "shared5_provider_condition_uncertainty.csv",
        "condition_difference_uncertainty_csv": output_dir / "condition_difference_uncertainty.csv",
        "provider_difference_uncertainty_csv": output_dir / "shared5_provider_difference_uncertainty.csv",
        "report_md": output_dir / "uncertainty_tables_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    _write_csv(outputs["glm_condition_uncertainty_csv"], glm_uncertainty_rows)
    _write_csv(outputs["shared_provider_condition_uncertainty_csv"], shared_uncertainty_rows)
    _write_csv(outputs["condition_difference_uncertainty_csv"], condition_difference_rows)
    _write_csv(outputs["provider_difference_uncertainty_csv"], provider_difference_rows)

    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "confidence_level": CONFIDENCE_LEVEL,
        "interval_method": "wilson_score_95",
        "difference_interval_method": "wilson_interval_difference_descriptive_95",
        "real_api_calls": 0,
        "safe_note": SAFE_SCOPE_NOTE,
        "source_files": {
            "glm_condition_csv": str(glm_condition_csv),
            "shared_comparison_csv": str(shared_comparison_csv),
        },
        "outputs": {name: str(path) for name, path in outputs.items()},
        "row_counts": {
            "glm_condition_uncertainty": len(glm_uncertainty_rows),
            "shared_provider_condition_uncertainty": len(shared_uncertainty_rows),
            "condition_difference_uncertainty": len(condition_difference_rows),
            "provider_difference_uncertainty": len(provider_difference_rows),
        },
    }

    outputs["manifest_json"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    write_report(
        outputs["report_md"],
        glm_uncertainty_rows=glm_uncertainty_rows,
        shared_uncertainty_rows=shared_uncertainty_rows,
        condition_difference_rows=condition_difference_rows,
        provider_difference_rows=provider_difference_rows,
        manifest=manifest,
    )

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate descriptive Pilot 03 uncertainty tables from committed summary CSV files. "
            "This command makes no real API calls."
        )
    )
    parser.add_argument("--glm-condition-csv", default=str(DEFAULT_GLM_CONDITION_CSV))
    parser.add_argument("--shared-comparison-csv", default=str(DEFAULT_SHARED_COMPARISON_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = generate_uncertainty_tables(
        glm_condition_csv=Path(args.glm_condition_csv),
        shared_comparison_csv=Path(args.shared_comparison_csv),
        output_dir=Path(args.output_dir),
    )

    print("Pilot 03 uncertainty tables generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"row_counts: {manifest['row_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
