"""Generate Pilot 03 final figures from committed sanitized outputs only.

This script creates reproducible descriptive figures for the controlled Pilot 03
setup. It does not call external APIs and does not inspect raw prompts,
raw responses, JSONL API outputs, or ignored aggregate JSON.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILES = {
    "model_condition_summary": Path(
        "reports/pilot_03_glm_vs_claude_t0020_full/model_condition_summary.csv"
    ),
    "paired_chain_comparison": Path(
        "reports/pilot_03_glm_vs_claude_t0020_full/paired_chain_comparison.csv"
    ),
    "model_metric_uncertainty": Path(
        "reports/pilot_03_glm_vs_claude_t0020_uncertainty/model_metric_uncertainty.csv"
    ),
    "paired_delta_uncertainty": Path(
        "reports/pilot_03_glm_vs_claude_t0020_uncertainty/paired_delta_uncertainty.csv"
    ),
    "condition_pair_profile": Path(
        "reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/condition_pair_profile.csv"
    ),
    "model_condition_cascade_metrics": Path(
        "reports/pilot_03_reliability_cascade_metrics/model_condition_cascade_metrics.csv"
    ),
    "cross_model_cascade_comparison": Path(
        "reports/pilot_03_reliability_cascade_metrics/cross_model_cascade_comparison.csv"
    ),
}

DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_final_figures")

SAFE_NOTE = (
    "Observed result under current Pilot 03 real LLM experimental conditions; "
    "descriptive comparison only."
)


@dataclass(frozen=True)
class CsvData:
    path: Path
    rows: list[dict[str, str]]
    columns: list[str]


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    title: str
    source_keys: list[str]
    output_files: list[str]


def read_csv_file(path: Path) -> CsvData:
    if not path.exists():
        raise FileNotFoundError(f"Required committed sanitized input is missing: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = list(reader.fieldnames or [])

    if not columns:
        raise ValueError(f"CSV has no header: {path}")

    return CsvData(path=path, rows=rows, columns=columns)


def require_columns(data: CsvData, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"{data.path} is missing required columns: {missing}")


def as_float(value: str | int | float | None, *, default: float = math.nan) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).strip()
    if cleaned == "":
        return default

    try:
        return float(cleaned)
    except ValueError:
        lowered = cleaned.lower()
        if lowered == "true":
            return 1.0
        if lowered == "false":
            return 0.0
        return default


def as_count(value: str | int | float | None) -> int:
    parsed = as_float(value, default=0.0)
    if math.isnan(parsed):
        return 0
    return int(round(parsed))


def rate_to_percent(value: str | int | float | None) -> float:
    parsed = as_float(value)
    if math.isnan(parsed):
        return math.nan
    if abs(parsed) <= 1.0000001:
        return parsed * 100.0
    return parsed


def metric_delta_to_percentage_points(value: str | int | float | None) -> float:
    parsed = as_float(value)
    if math.isnan(parsed):
        return math.nan
    if abs(parsed) <= 1.0000001:
        return parsed * 100.0
    return parsed


def condition_sort_key(condition: str) -> tuple[int, str]:
    lowered = condition.lower().strip()
    if "original" in lowered:
        return (0, lowered)
    if "missing_policy" in lowered or "policy" in lowered:
        return (1, lowered)
    if "missing_one" in lowered or "required_unit" in lowered or "unit" in lowered:
        return (2, lowered)
    return (99, lowered)


def condition_label(condition: str) -> str:
    lowered = condition.lower().strip()
    if "original" in lowered:
        return "Original evidence"
    if "missing_policy" in lowered or "policy" in lowered:
        return "Missing policy rule"
    if "missing_one" in lowered or "required_unit" in lowered or "unit" in lowered:
        return "Missing one required unit"
    return condition.replace("_", " ").strip().title()


def metric_label(metric: str) -> str:
    lowered = metric.lower().strip()

    replacements = [
        ("decision_correct", "Decision correct"),
        ("escalation_correct", "Escalation correct"),
        ("audit_passed_true", "Audit passed"),
        ("audit_passed", "Audit passed"),
        ("valid_json_chain", "Valid JSON chain"),
        ("valid_schema_chain", "Valid schema chain"),
        ("cascade_failure_rate", "Cascade failure"),
        ("audit_false_assurance_rate", "Audit false assurance"),
        ("undetected_decision_failure_rate", "Undetected decision failure"),
        (
            "escalation_recovery_rate_on_decision_failure",
            "Escalation recovery after decision failure",
        ),
        ("net_escalation_gain_rate", "Net escalation gain"),
    ]

    for needle, label in replacements:
        if needle in lowered:
            return label

    return metric.replace("_", " ").strip().title()


def model_label(row: dict[str, str]) -> str:
    direct = (row.get("model_label") or "").strip()
    if direct:
        return direct

    provider = (row.get("provider") or "").strip()
    model_name = (row.get("model_name") or "").strip()

    if provider and model_name:
        return f"{provider}: {model_name}"
    if model_name:
        return model_name
    if provider:
        return provider
    return "model"


def unique_sorted_conditions(rows: list[dict[str, str]]) -> list[str]:
    return sorted({row["condition"] for row in rows}, key=condition_sort_key)


def unique_sorted_models(rows: list[dict[str, str]]) -> list[str]:
    return sorted({model_label(row) for row in rows})


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    removable_suffixes = {".png", ".pdf", ".md", ".json"}
    for child in output_dir.iterdir():
        if child.is_file() and child.suffix.lower() in removable_suffixes:
            child.unlink()


def save_figure(
    fig: plt.Figure,
    output_dir: Path,
    figure_id: str,
    formats: tuple[str, ...],
    dpi: int,
) -> list[str]:
    written: list[str] = []
    for fmt in formats:
        path = output_dir / f"{figure_id}.{fmt}"
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        written.append(str(path.as_posix()))
    plt.close(fig)
    return written


def plot_condition_degradation(
    data: dict[str, CsvData],
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int,
) -> FigureRecord:
    uncertainty = data["model_metric_uncertainty"]
    require_columns(
        uncertainty,
        [
            "model_label",
            "condition",
            "metric",
            "estimate",
            "ci_lower",
            "ci_upper",
        ],
    )

    rows = [
        row
        for row in uncertainty.rows
        if "decision_correct" in row["metric"].lower()
    ]

    if not rows:
        raise ValueError("No decision correctness rows found in model_metric_uncertainty.csv")

    conditions = unique_sorted_conditions(rows)
    models = unique_sorted_models(rows)

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    base_positions = list(range(len(conditions)))
    width = 0.32 if len(models) <= 2 else 0.22

    for model_index, current_model in enumerate(models):
        offset = (model_index - (len(models) - 1) / 2.0) * width
        x_values: list[float] = []
        y_values: list[float] = []
        lower_errors: list[float] = []
        upper_errors: list[float] = []

        for condition_index, condition in enumerate(conditions):
            match = next(
                (
                    row
                    for row in rows
                    if row["condition"] == condition and model_label(row) == current_model
                ),
                None,
            )
            x_values.append(base_positions[condition_index] + offset)

            if match is None:
                y_values.append(math.nan)
                lower_errors.append(0.0)
                upper_errors.append(0.0)
                continue

            estimate = rate_to_percent(match["estimate"])
            ci_lower = rate_to_percent(match["ci_lower"])
            ci_upper = rate_to_percent(match["ci_upper"])

            y_values.append(estimate)
            lower_errors.append(max(0.0, estimate - ci_lower))
            upper_errors.append(max(0.0, ci_upper - estimate))

        ax.errorbar(
            x_values,
            y_values,
            yerr=[lower_errors, upper_errors],
            fmt="o",
            capsize=4,
            label=current_model,
        )

    ax.set_title("Condition degradation: decision correctness")
    ax.set_ylabel("Decision correct rate (%)")
    ax.set_xlabel("Evidence condition")
    ax.set_ylim(0, 105)
    ax.set_xticks(base_positions)
    ax.set_xticklabels([condition_label(condition) for condition in conditions])
    ax.legend(title="Model", frameon=False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    output_files = save_figure(
        fig,
        output_dir,
        "fig01_condition_degradation_decision_correctness",
        formats,
        dpi,
    )

    return FigureRecord(
        figure_id="fig01_condition_degradation_decision_correctness",
        title="Condition degradation: decision correctness",
        source_keys=["model_metric_uncertainty"],
        output_files=output_files,
    )


def plot_decision_vs_escalation(
    data: dict[str, CsvData],
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int,
) -> FigureRecord:
    summary = data["model_condition_summary"]
    require_columns(
        summary,
        [
            "provider",
            "model_name",
            "condition",
            "decision_correct_rate",
            "escalation_correct_rate",
        ],
    )

    rows = sorted(
        summary.rows,
        key=lambda row: (condition_sort_key(row["condition"]), model_label(row)),
    )

    labels = [
        f"{condition_label(row['condition'])}\n{model_label(row)}"
        for row in rows
    ]
    decision_rates = [rate_to_percent(row["decision_correct_rate"]) for row in rows]
    escalation_rates = [rate_to_percent(row["escalation_correct_rate"]) for row in rows]

    x_values = list(range(len(rows)))
    width = 0.36

    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ax.bar([x - width / 2 for x in x_values], decision_rates, width, label="Decision stage")
    ax.bar([x + width / 2 for x in x_values], escalation_rates, width, label="Escalation stage")

    ax.set_title("Decision-stage vs escalation-stage correctness")
    ax.set_ylabel("Correct rate (%)")
    ax.set_ylim(0, 105)
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    output_files = save_figure(
        fig,
        output_dir,
        "fig02_decision_vs_escalation_correctness",
        formats,
        dpi,
    )

    return FigureRecord(
        figure_id="fig02_decision_vs_escalation_correctness",
        title="Decision-stage vs escalation-stage correctness",
        source_keys=["model_condition_summary"],
        output_files=output_files,
    )


def plot_audit_false_assurance(
    data: dict[str, CsvData],
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int,
) -> FigureRecord:
    cascade = data["model_condition_cascade_metrics"]
    require_columns(
        cascade,
        [
            "model_label",
            "condition",
            "audit_false_assurance_rate",
            "undetected_decision_failure_rate",
        ],
    )

    rows = sorted(
        cascade.rows,
        key=lambda row: (condition_sort_key(row["condition"]), model_label(row)),
    )

    labels = [
        f"{condition_label(row['condition'])}\n{model_label(row)}"
        for row in rows
    ]
    false_assurance = [
        rate_to_percent(row["audit_false_assurance_rate"])
        for row in rows
    ]
    undetected_failure = [
        rate_to_percent(row["undetected_decision_failure_rate"])
        for row in rows
    ]

    x_values = list(range(len(rows)))
    width = 0.36

    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ax.bar(
        [x - width / 2 for x in x_values],
        false_assurance,
        width,
        label="Audit false assurance",
    )
    ax.bar(
        [x + width / 2 for x in x_values],
        undetected_failure,
        width,
        label="Undetected decision failure",
    )

    ax.set_title("Audit false assurance and undetected decision failure")
    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 105)
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    output_files = save_figure(
        fig,
        output_dir,
        "fig03_audit_false_assurance_undetected_failure",
        formats,
        dpi,
    )

    return FigureRecord(
        figure_id="fig03_audit_false_assurance_undetected_failure",
        title="Audit false assurance and undetected decision failure",
        source_keys=["model_condition_cascade_metrics"],
        output_files=output_files,
    )


def plot_full_model_comparison(
    data: dict[str, CsvData],
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int,
) -> FigureRecord:
    deltas = data["paired_delta_uncertainty"]
    require_columns(
        deltas,
        [
            "condition",
            "metric",
            "claude_minus_glm",
            "paired_bootstrap_ci_lower",
            "paired_bootstrap_ci_upper",
        ],
    )

    rows = sorted(
        deltas.rows,
        key=lambda row: (condition_sort_key(row["condition"]), metric_label(row["metric"])),
    )

    labels = [
        f"{condition_label(row['condition'])}: {metric_label(row['metric'])}"
        for row in rows
    ]
    estimates = [
        metric_delta_to_percentage_points(row["claude_minus_glm"])
        for row in rows
    ]
    lower = [
        metric_delta_to_percentage_points(row["paired_bootstrap_ci_lower"])
        for row in rows
    ]
    upper = [
        metric_delta_to_percentage_points(row["paired_bootstrap_ci_upper"])
        for row in rows
    ]

    lower_errors = [
        max(0.0, estimate - low) if not math.isnan(estimate) and not math.isnan(low) else 0.0
        for estimate, low in zip(estimates, lower)
    ]
    upper_errors = [
        max(0.0, high - estimate) if not math.isnan(estimate) and not math.isnan(high) else 0.0
        for estimate, high in zip(estimates, upper)
    ]

    y_values = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(11.5, max(6.5, 0.38 * len(rows) + 2.0)))
    ax.errorbar(
        estimates,
        y_values,
        xerr=[lower_errors, upper_errors],
        fmt="o",
        capsize=3,
    )
    ax.axvline(0.0, linewidth=1)

    ax.set_title("GLM vs Claude descriptive paired comparison")
    ax.set_xlabel("Claude minus GLM rate difference (percentage points)")
    ax.set_yticks(y_values)
    ax.set_yticklabels(labels)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()

    output_files = save_figure(
        fig,
        output_dir,
        "fig04_glm_vs_claude_descriptive_paired_comparison",
        formats,
        dpi,
    )

    return FigureRecord(
        figure_id="fig04_glm_vs_claude_descriptive_paired_comparison",
        title="GLM vs Claude descriptive paired comparison",
        source_keys=["paired_delta_uncertainty"],
        output_files=output_files,
    )


def plot_reliability_cascade_metrics(
    data: dict[str, CsvData],
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int,
) -> FigureRecord:
    cascade = data["model_condition_cascade_metrics"]
    require_columns(
        cascade,
        [
            "model_label",
            "condition",
            "cascade_failure_rate",
            "audit_false_assurance_rate",
            "undetected_decision_failure_rate",
            "escalation_recovery_rate_on_decision_failure",
        ],
    )

    metric_columns = [
        "cascade_failure_rate",
        "audit_false_assurance_rate",
        "undetected_decision_failure_rate",
        "escalation_recovery_rate_on_decision_failure",
    ]

    rows = sorted(
        cascade.rows,
        key=lambda row: (condition_sort_key(row["condition"]), model_label(row)),
    )

    matrix = [
        [rate_to_percent(row[column]) for column in metric_columns]
        for row in rows
    ]

    row_labels = [
        f"{condition_label(row['condition'])}\n{model_label(row)}"
        for row in rows
    ]
    column_labels = [metric_label(column) for column in metric_columns]

    fig, ax = plt.subplots(figsize=(12.5, 6.5))
    image = ax.imshow(matrix, aspect="auto", vmin=0, vmax=100)
    fig.colorbar(image, ax=ax, label="Rate (%)")

    ax.set_title("Reliability cascade metrics by model and evidence condition")
    ax.set_xticks(list(range(len(column_labels))))
    ax.set_xticklabels(column_labels, rotation=25, ha="right")
    ax.set_yticks(list(range(len(row_labels))))
    ax.set_yticklabels(row_labels)

    for row_index, row_values in enumerate(matrix):
        for column_index, value in enumerate(row_values):
            display = "NA" if math.isnan(value) else f"{value:.1f}%"
            ax.text(column_index, row_index, display, ha="center", va="center")

    fig.tight_layout()

    output_files = save_figure(
        fig,
        output_dir,
        "fig05_reliability_cascade_metric_table",
        formats,
        dpi,
    )

    return FigureRecord(
        figure_id="fig05_reliability_cascade_metric_table",
        title="Reliability cascade metrics by model and evidence condition",
        source_keys=["model_condition_cascade_metrics"],
        output_files=output_files,
    )


def plot_paired_task_disagreement(
    data: dict[str, CsvData],
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int,
) -> FigureRecord:
    profile = data["condition_pair_profile"]
    require_columns(
        profile,
        [
            "condition",
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
        ],
    )

    condition_rows = sorted(profile.rows, key=lambda row: condition_sort_key(row["condition"]))

    stage_specs = [
        (
            "Decision",
            [
                ("Both correct", "decision_both_correct_count"),
                ("Both wrong", "decision_both_wrong_count"),
                ("GLM only", "decision_glm_only_correct_count"),
                ("Claude only", "decision_claude_only_correct_count"),
            ],
        ),
        (
            "Escalation",
            [
                ("Both correct", "escalation_both_correct_count"),
                ("Both wrong", "escalation_both_wrong_count"),
                ("GLM only", "escalation_glm_only_correct_count"),
                ("Claude only", "escalation_claude_only_correct_count"),
            ],
        ),
        (
            "Audit pass",
            [
                ("Both passed", "audit_both_passed_count"),
                ("Both not passed", "audit_both_not_passed_count"),
                ("GLM only", "audit_glm_only_passed_count"),
                ("Claude only", "audit_claude_only_passed_count"),
            ],
        ),
    ]

    bar_labels: list[str] = []
    category_order: list[str] = []
    values_by_category: dict[str, list[int]] = {}

    for row in condition_rows:
        for stage_name, stage_categories in stage_specs:
            bar_labels.append(f"{condition_label(row['condition'])}\n{stage_name}")
            for category_label, column in stage_categories:
                if category_label not in category_order:
                    category_order.append(category_label)
                values_by_category.setdefault(category_label, []).append(as_count(row[column]))

            for known_category in category_order:
                values_by_category.setdefault(known_category, [])
                while len(values_by_category[known_category]) < len(bar_labels):
                    values_by_category[known_category].append(0)

    x_values = list(range(len(bar_labels)))
    bottoms = [0 for _ in bar_labels]

    fig, ax = plt.subplots(figsize=(13.5, 6.8))

    for category in category_order:
        heights = values_by_category[category]
        ax.bar(x_values, heights, bottom=bottoms, label=category)
        bottoms = [bottom + height for bottom, height in zip(bottoms, heights)]

    ax.set_title("Paired task-level outcome profile")
    ax.set_ylabel("Number of paired task-condition cases")
    ax.set_xticks(x_values)
    ax.set_xticklabels(bar_labels, rotation=35, ha="right")
    ax.legend(frameon=False, ncols=2)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    output_files = save_figure(
        fig,
        output_dir,
        "fig06_paired_task_level_outcome_profile",
        formats,
        dpi,
    )

    return FigureRecord(
        figure_id="fig06_paired_task_level_outcome_profile",
        title="Paired task-level outcome profile",
        source_keys=["condition_pair_profile"],
        output_files=output_files,
    )


def plot_cascade_descriptive_delta(
    data: dict[str, CsvData],
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int,
) -> FigureRecord:
    comparison = data["cross_model_cascade_comparison"]
    require_columns(
        comparison,
        [
            "condition",
            "metric",
            "claude_minus_glm",
        ],
    )

    target_metrics = {
        "cascade_failure_rate",
        "audit_false_assurance_rate",
        "undetected_decision_failure_rate",
        "escalation_recovery_rate_on_decision_failure",
        "net_escalation_gain_rate",
    }

    rows = [
        row
        for row in comparison.rows
        if row["metric"] in target_metrics
    ]

    rows = sorted(
        rows,
        key=lambda row: (condition_sort_key(row["condition"]), metric_label(row["metric"])),
    )

    labels = [
        f"{condition_label(row['condition'])}: {metric_label(row['metric'])}"
        for row in rows
    ]
    values = [
        metric_delta_to_percentage_points(row["claude_minus_glm"])
        for row in rows
    ]
    y_values = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(11.5, max(6.5, 0.38 * len(rows) + 2.0)))
    ax.barh(y_values, values)
    ax.axvline(0.0, linewidth=1)

    ax.set_title("Reliability cascade metric differences: Claude minus GLM")
    ax.set_xlabel("Rate difference (percentage points)")
    ax.set_yticks(y_values)
    ax.set_yticklabels(labels)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()

    output_files = save_figure(
        fig,
        output_dir,
        "fig07_cascade_metric_descriptive_differences",
        formats,
        dpi,
    )

    return FigureRecord(
        figure_id="fig07_cascade_metric_descriptive_differences",
        title="Reliability cascade metric differences: Claude minus GLM",
        source_keys=["cross_model_cascade_comparison"],
        output_files=output_files,
    )


def write_figure_notes(output_dir: Path, figure_records: list[FigureRecord]) -> Path:
    path = output_dir / "figure_notes.md"

    lines = [
        "# Pilot 03 final figure notes",
        "",
        "These figures were generated from committed sanitized Pilot 03 CSV outputs only.",
        "",
        "Scope:",
        "",
        "- Controlled Pilot 03 setup.",
        "- Observed local result under the current committed sanitized outputs.",
        "- Descriptive comparison only.",
        "- No external API calls were made by the generator.",
        "- The generator does not inspect raw prompts, raw responses, JSONL API outputs, or ignored aggregate JSON.",
        "",
        "Safe interpretation:",
        "",
        "The figures support later paper drafting, but they should not be read as broad model claims. They show observed behavior under the current Pilot 03 real LLM experimental conditions.",
        "",
        "Generated figures:",
        "",
    ]

    for index, record in enumerate(figure_records, start=1):
        files = ", ".join(Path(file).name for file in record.output_files)
        sources = ", ".join(record.source_keys)
        lines.append(f"{index}. **{record.title}**")
        lines.append(f"   - Figure id: `{record.figure_id}`")
        lines.append(f"   - Source keys: `{sources}`")
        lines.append(f"   - Files: `{files}`")
        lines.append("")

    lines.extend(
        [
            "Reproducibility note:",
            "",
            "The companion `manifest.json` records source paths, row counts, SHA-256 hashes, generated files, and the no-call status.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_manifest(
    repo_root: Path,
    output_dir: Path,
    data: dict[str, CsvData],
    figure_records: list[FigureRecord],
    notes_path: Path,
) -> Path:
    def repo_relative(path_value: str | Path) -> str:
        current_path = Path(path_value)
        if not current_path.is_absolute():
            return current_path.as_posix()
        try:
            return current_path.relative_to(repo_root).as_posix()
        except ValueError:
            return current_path.as_posix()

    output_files = sorted(
        repo_relative(path)
        for path in output_dir.iterdir()
        if path.is_file() and path.name != "manifest.json"
    )

    source_entries = []
    for key, csv_data in data.items():
        source_entries.append(
            {
                "key": key,
                "path": repo_relative(csv_data.path),
                "rows": len(csv_data.rows),
                "columns": csv_data.columns,
                "sha256": file_sha256(csv_data.path),
            }
        )

    manifest = {
        "report_name": "pilot_03_final_figures",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "experiments/pilot_03_generate_final_figures.py",
        "input_policy": "committed sanitized CSV outputs only",
        "source_files": source_entries,
        "figures": [
            {
                "figure_id": record.figure_id,
                "title": record.title,
                "source_keys": record.source_keys,
                "output_files": [repo_relative(path) for path in record.output_files],
                "safe_note": SAFE_NOTE,
            }
            for record in figure_records
        ],
        "output_files": output_files,
        "figure_notes": repo_relative(notes_path),
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "safe_wording_check": "PASS",
        "safe_note": SAFE_NOTE,
    }

    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def validate_safe_public_text(output_dir: Path) -> None:
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

    text_paths = [
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".json"}
    ]

    failures: list[str] = []
    for path in text_paths:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for term in blocked_terms:
            if term.lower() in lowered:
                failures.append(f"{path}: blocked public wording found")

    if failures:
        raise ValueError("Safe wording check failed:\n" + "\n".join(failures))


def parse_formats(raw_formats: str) -> tuple[str, ...]:
    formats = tuple(
        item.strip().lower()
        for item in raw_formats.split(",")
        if item.strip()
    )
    allowed = {"png", "pdf"}
    unknown = [fmt for fmt in formats if fmt not in allowed]
    if unknown:
        raise ValueError(f"Unsupported output format(s): {unknown}")
    if not formats:
        raise ValueError("At least one output format is required")
    return formats


def load_all_inputs(repo_root: Path) -> dict[str, CsvData]:
    data: dict[str, CsvData] = {}
    for key, relative_path in INPUT_FILES.items():
        absolute_path = repo_root / relative_path
        data[key] = read_csv_file(absolute_path)
    return data


def list_inputs(repo_root: Path) -> None:
    print("Task 5 committed sanitized input inventory")
    print("========================================")
    for key, relative_path in INPUT_FILES.items():
        absolute_path = repo_root / relative_path
        status = "FOUND" if absolute_path.exists() else "MISSING"
        size = absolute_path.stat().st_size if absolute_path.exists() else 0
        print(f"{key}: {status} {relative_path.as_posix()} size={size}")
    print("real_api_calls: 0")
    print("raw_response_inspection: False")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Pilot 03 final figures from committed sanitized CSV outputs only."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the parent of this experiments directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for generated figures and manifest.",
    )
    parser.add_argument(
        "--formats",
        default="png,pdf",
        help="Comma-separated output formats. Supported values: png,pdf.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=220,
        help="DPI for saved figures.",
    )
    parser.add_argument(
        "--list-inputs",
        action="store_true",
        help="List expected committed sanitized inputs and exit.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()

    if args.list_inputs:
        list_inputs(repo_root)
        return 0

    formats = parse_formats(args.formats)
    output_dir = (repo_root / args.output_dir).resolve()

    data = load_all_inputs(repo_root)
    prepare_output_dir(output_dir)

    figure_records = [
        plot_condition_degradation(data, output_dir, formats, args.dpi),
        plot_decision_vs_escalation(data, output_dir, formats, args.dpi),
        plot_audit_false_assurance(data, output_dir, formats, args.dpi),
        plot_full_model_comparison(data, output_dir, formats, args.dpi),
        plot_reliability_cascade_metrics(data, output_dir, formats, args.dpi),
        plot_paired_task_disagreement(data, output_dir, formats, args.dpi),
        plot_cascade_descriptive_delta(data, output_dir, formats, args.dpi),
    ]

    notes_path = write_figure_notes(output_dir, figure_records)
    manifest_path = write_manifest(repo_root, output_dir, data, figure_records, notes_path)
    validate_safe_public_text(output_dir)

    print("Pilot 03 final figure generation")
    print("================================")
    print("status: PASS")
    print(f"output_dir: {output_dir.relative_to(repo_root).as_posix()}")
    print(f"figures_generated: {len(figure_records)}")
    print(f"figure_notes: {notes_path.relative_to(repo_root).as_posix()}")
    print(f"manifest: {manifest_path.relative_to(repo_root).as_posix()}")
    print("real_api_calls: 0")
    print("raw_response_inspection: False")
    print("")
    print("Generated files:")
    for path in sorted(output_dir.iterdir()):
        if path.is_file():
            print(f"- {path.relative_to(repo_root).as_posix()} size={path.stat().st_size}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
