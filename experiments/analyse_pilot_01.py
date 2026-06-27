"""
Analyse the first simulation pilot results.

This script reads the pilot CSV and prints a clear condition-level summary.
"""

import pandas as pd


def main() -> None:
    input_path = "data/outputs/pilot_results.csv"

    results = pd.read_csv(input_path)

    metric_columns = [
        "evidence_state_reliability",
        "evidence_state_degradation",
        "final_failure",
        "undetected_failure",
        "audit_false_assurance",
        "escalation_contamination",
        "cost",
        "cost_per_governable_output",
    ]

    summary = (
        results
        .groupby("condition")[metric_columns]
        .mean()
        .reset_index()
    )

    summary = summary.round(4)

    output_path = "results/tables/pilot_01_condition_summary.csv"
    summary.to_csv(output_path, index=False)

    print("Pilot 01 condition summary:")
    print(summary.to_string(index=False))

    print("\nSaved summary to:", output_path)

    print("\nBasic checks:")
    print("Rows in raw results:", len(results))
    print("Conditions:", sorted(results["condition"].unique()))
    print("Runs:", sorted(results["run_id"].unique()))

    assert len(results) == 750
    assert len(summary) == 5

    print("\nPilot 01 analysis sanity check passed.")


if __name__ == "__main__":
    main()