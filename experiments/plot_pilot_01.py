"""
Create basic plots for Pilot 01.

This script reads the condition summary table and saves simple bar plots.

Plots:
1. Evidence-State Reliability by condition
2. Final Failure by condition
3. Undetected Failure by condition
4. Cost per Governable Output by condition
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def save_bar_plot(
    summary: pd.DataFrame,
    metric: str,
    title: str,
    ylabel: str,
    output_path: str,
) -> None:
    """
    Save a simple bar plot for one metric.
    """

    ordered = summary.sort_values(metric, ascending=False)

    plt.figure(figsize=(10, 5))
    plt.bar(ordered["condition"], ordered[metric])
    plt.title(title)
    plt.xlabel("Pipeline condition")
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    input_path = "results/tables/pilot_01_condition_summary.csv"
    output_dir = Path("results/plots")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(input_path)

    plots = [
        (
            "evidence_state_reliability",
            "Evidence-State Reliability by Condition",
            "Mean reliability",
            output_dir / "pilot_01_evidence_state_reliability.png",
        ),
        (
            "final_failure",
            "Final Failure by Condition",
            "Mean final failure rate",
            output_dir / "pilot_01_final_failure.png",
        ),
        (
            "undetected_failure",
            "Undetected Failure by Condition",
            "Mean undetected failure rate",
            output_dir / "pilot_01_undetected_failure.png",
        ),
        (
            "cost_per_governable_output",
            "Cost per Governable Output by Condition",
            "Cost per governable output",
            output_dir / "pilot_01_cost_per_governable_output.png",
        ),
    ]

    for metric, title, ylabel, output_path in plots:
        save_bar_plot(
            summary=summary,
            metric=metric,
            title=title,
            ylabel=ylabel,
            output_path=str(output_path),
        )
        print("Saved plot:", output_path)

    assert len(list(output_dir.glob("pilot_01_*.png"))) >= 4

    print("\nPilot 01 plotting sanity check passed.")


if __name__ == "__main__":
    main()