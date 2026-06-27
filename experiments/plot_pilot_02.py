"""
Create plots for Pilot 02.

Pilot 02 tests graded evidence degradation severity.

The plots show how evidence-state reliability, evidence-state degradation,
downstream failure, undetected failure, audit false assurance, escalation
contamination, and cost per governable output change as degradation severity
increases.

These are simulation-only results under current Pilot 02 assumptions.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT_DIR / "data" / "outputs" / "pilot_02_results.csv"
OUTPUT_DIR = ROOT_DIR / "results" / "plots"

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "severe": 4,
}

MEAN_METRICS = [
    "evidence_state_reliability",
    "evidence_state_degradation",
    "final_failure",
    "undetected_failure",
    "audit_false_assurance",
    "escalation_contamination",
    "cost",
]


def check_required_columns(df: pd.DataFrame) -> None:
    required_columns = {
        "degradation_severity",
        "accepted_by_pipeline",
        "final_failure",
        "task_id",
        *MEAN_METRICS,
    }

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required column(s): {missing}")


def make_plot_summary(df: pd.DataFrame) -> pd.DataFrame:
    mean_summary = (
        df.groupby("degradation_severity")[MEAN_METRICS]
        .mean()
        .reset_index()
    )

    aggregate_summary = (
        df.assign(
            governable_output=(
                df["accepted_by_pipeline"]
                & ~df["final_failure"]
            ).astype(int)
        )
        .groupby("degradation_severity")
        .agg(
            total_cost=("cost", "sum"),
            governable_outputs=("governable_output", "sum"),
            total_outputs=("task_id", "count"),
        )
        .reset_index()
    )

    summary = mean_summary.merge(
        aggregate_summary,
        on="degradation_severity",
        how="left",
    )

    summary["cost_per_governable_output"] = (
        summary["total_cost"] / summary["governable_outputs"]
    )

    summary["severity_index"] = summary["degradation_severity"].map(SEVERITY_ORDER)
    summary = summary.sort_values("severity_index")

    return summary


def create_line_plot(
    summary: pd.DataFrame,
    metric: str,
    title: str,
    y_label: str,
    output_filename: str,
) -> None:
    output_path = OUTPUT_DIR / output_filename

    plt.figure(figsize=(8, 5))
    plt.plot(
        summary["degradation_severity"],
        summary[metric],
        marker="o",
    )
    plt.title(title)
    plt.xlabel("Degradation severity")
    plt.ylabel(y_label)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Saved plot: {output_path}")


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find input file: {INPUT_PATH}\n"
            "Run Pilot 02 before creating plots."
        )

    df = pd.read_csv(INPUT_PATH)
    check_required_columns(df)

    df["severity_index"] = df["degradation_severity"].map(SEVERITY_ORDER)

    if df["severity_index"].isna().any():
        unknown_levels = sorted(
            df.loc[df["severity_index"].isna(), "degradation_severity"].unique()
        )
        raise ValueError(f"Unknown degradation severity level(s): {unknown_levels}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = make_plot_summary(df)

    create_line_plot(
        summary=summary,
        metric="evidence_state_reliability",
        title="Pilot 02: Evidence-State Reliability by Degradation Severity",
        y_label="Evidence-state reliability",
        output_filename="pilot_02_evidence_state_reliability.png",
    )

    create_line_plot(
        summary=summary,
        metric="evidence_state_degradation",
        title="Pilot 02: Evidence-State Degradation by Degradation Severity",
        y_label="Evidence-state degradation",
        output_filename="pilot_02_evidence_state_degradation.png",
    )

    create_line_plot(
        summary=summary,
        metric="final_failure",
        title="Pilot 02: Final Failure by Degradation Severity",
        y_label="Final failure rate",
        output_filename="pilot_02_final_failure.png",
    )

    create_line_plot(
        summary=summary,
        metric="undetected_failure",
        title="Pilot 02: Undetected Failure by Degradation Severity",
        y_label="Undetected failure rate",
        output_filename="pilot_02_undetected_failure.png",
    )

    create_line_plot(
        summary=summary,
        metric="audit_false_assurance",
        title="Pilot 02: Audit False Assurance by Degradation Severity",
        y_label="Audit false assurance rate",
        output_filename="pilot_02_audit_false_assurance.png",
    )

    create_line_plot(
        summary=summary,
        metric="escalation_contamination",
        title="Pilot 02: Escalation Contamination by Degradation Severity",
        y_label="Escalation contamination rate",
        output_filename="pilot_02_escalation_contamination.png",
    )

    create_line_plot(
        summary=summary,
        metric="cost_per_governable_output",
        title="Pilot 02: Cost per Governable Output by Degradation Severity",
        y_label="Cost per governable output",
        output_filename="pilot_02_cost_per_governable_output.png",
    )

    print("\nPilot 02 plotting sanity check passed.")


if __name__ == "__main__":
    main()