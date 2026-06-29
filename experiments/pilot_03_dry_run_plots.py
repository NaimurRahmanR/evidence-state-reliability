from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


PILOT_03_PLOT_VERSION = "pilot_03_dry_run_plots_v1"

DEFAULT_ANALYSIS_DIR = Path("results/pilot_03_dry_run_analysis/pilot_03_dry_run_analysis_latest")
DEFAULT_CONDITION_SUMMARY_CSV = DEFAULT_ANALYSIS_DIR / "condition_summary.csv"

CONDITION_ORDER = [
    "original_evidence",
    "missing_policy_rule",
    "missing_one_required_unit",
]

CONDITION_LABELS = {
    "original_evidence": "Original evidence",
    "missing_policy_rule": "Missing policy rule",
    "missing_one_required_unit": "Missing one required unit",
}


def load_condition_summary(input_path: str | Path = DEFAULT_CONDITION_SUMMARY_CSV) -> pd.DataFrame:
    """Load Pilot 03 dry-run condition summary CSV."""
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Could not find condition summary CSV: {input_path}. "
            "Run `python -m experiments.pilot_03_dry_run_analysis` first."
        )

    df = pd.read_csv(input_path)

    if "condition" not in df.columns:
        raise ValueError(f"Missing required column 'condition' in {input_path}")

    df["condition"] = pd.Categorical(df["condition"], categories=CONDITION_ORDER, ordered=True)
    df = df.sort_values("condition").reset_index(drop=True)
    df["condition_label"] = df["condition"].astype(str).map(CONDITION_LABELS).fillna(df["condition"].astype(str))

    return df


def _require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required plot columns: {missing}")


def _save_current_figure(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    return output_path


def plot_evidence_state_metrics(df: pd.DataFrame, output_dir: str | Path) -> Path:
    """Plot evidence-state reliability and degradation by condition."""
    output_dir = Path(output_dir)

    columns = [
        "evidence_state_reliability_mean",
        "evidence_state_degradation_mean",
    ]
    _require_columns(df, columns)

    plot_df = df.set_index("condition_label")[columns]
    plot_df = plot_df.rename(
        columns={
            "evidence_state_reliability_mean": "Evidence-state reliability",
            "evidence_state_degradation_mean": "Evidence-state degradation",
        }
    )

    ax = plot_df.plot(kind="bar", figsize=(9, 5))
    ax.set_title("Pilot 03 dry-run evidence-state metrics by condition")
    ax.set_xlabel("Evidence condition")
    ax.set_ylabel("Mean value")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=20)
    ax.legend(loc="best")

    return _save_current_figure(output_dir / "evidence_state_metrics_by_condition.png")


def plot_failure_metrics(df: pd.DataFrame, output_dir: str | Path) -> Path:
    """Plot failure-related metrics by condition."""
    output_dir = Path(output_dir)

    columns = [
        "decision_failure_mean",
        "final_failure_mean",
        "undetected_failure_mean",
        "escalation_contamination_mean",
    ]
    _require_columns(df, columns)

    plot_df = df.set_index("condition_label")[columns]
    plot_df = plot_df.rename(
        columns={
            "decision_failure_mean": "Decision failure",
            "final_failure_mean": "Final failure",
            "undetected_failure_mean": "Undetected failure",
            "escalation_contamination_mean": "Escalation contamination",
        }
    )

    ax = plot_df.plot(kind="bar", figsize=(10, 5))
    ax.set_title("Pilot 03 dry-run failure metrics by condition")
    ax.set_xlabel("Evidence condition")
    ax.set_ylabel("Mean rate")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=20)
    ax.legend(loc="best")

    return _save_current_figure(output_dir / "failure_metrics_by_condition.png")


def plot_audit_metrics(df: pd.DataFrame, output_dir: str | Path) -> Path:
    """Plot audit-related metrics by condition."""
    output_dir = Path(output_dir)

    columns = [
        "audit_passed_mean",
        "audit_detected_issue_mean",
        "audit_false_assurance_mean",
    ]
    _require_columns(df, columns)

    plot_df = df.set_index("condition_label")[columns]
    plot_df = plot_df.rename(
        columns={
            "audit_passed_mean": "Audit passed",
            "audit_detected_issue_mean": "Audit detected issue",
            "audit_false_assurance_mean": "Audit false assurance",
        }
    )

    ax = plot_df.plot(kind="bar", figsize=(10, 5))
    ax.set_title("Pilot 03 dry-run audit metrics by condition")
    ax.set_xlabel("Evidence condition")
    ax.set_ylabel("Mean rate")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=20)
    ax.legend(loc="best")

    return _save_current_figure(output_dir / "audit_metrics_by_condition.png")


def generate_pilot_03_dry_run_plots(
    condition_summary_csv: str | Path = DEFAULT_CONDITION_SUMMARY_CSV,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Generate Pilot 03 dry-run plots from the condition summary CSV."""
    condition_summary_csv = Path(condition_summary_csv)
    df = load_condition_summary(condition_summary_csv)

    if output_dir is None:
        output_dir = condition_summary_csv.parent / "plots"

    output_dir = Path(output_dir)

    paths = {
        "evidence_state_metrics": plot_evidence_state_metrics(df, output_dir),
        "failure_metrics": plot_failure_metrics(df, output_dir),
        "audit_metrics": plot_audit_metrics(df, output_dir),
    }

    return {
        "plot_version": PILOT_03_PLOT_VERSION,
        "condition_summary_csv": condition_summary_csv,
        "output_dir": output_dir,
        "plots": paths,
    }


def main() -> None:
    """Generate Pilot 03 dry-run analysis plots."""
    result = generate_pilot_03_dry_run_plots()

    print("Pilot 03 dry-run plots")
    print("======================")
    print("No real LLM calls are made in this plotting script.")
    print(f"plot_version: {result['plot_version']}")
    print(f"condition_summary_csv: {result['condition_summary_csv']}")
    print(f"output_dir: {result['output_dir']}")
    print("plots:")
    for name, path in result["plots"].items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()