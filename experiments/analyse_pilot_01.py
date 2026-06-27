"""
Analyse the first simulation pilot results.

This script reads the pilot CSV and prints a clear condition-level summary.

Important:
    Cost per Governable Output is calculated at condition level:
        total condition cost / number of correct accepted outputs
"""

import pandas as pd


def main() -> None:
    input_path = "data/outputs/pilot_results.csv"

    results = pd.read_csv(input_path)

    results["governable_output"] = (
        (results["accepted_by_pipeline"] == True)
        & (results["final_failure"] == False)
    )

    metric_columns = [
        "evidence_state_reliability",
        "evidence_state_degradation",
        "final_failure",
        "undetected_failure",
        "audit_false_assurance",
        "escalation_contamination",
        "cost",
    ]

    summary = (
        results
        .groupby("condition")[metric_columns]
        .mean()
        .reset_index()
    )

    condition_costs = (
        results
        .groupby("condition")
        .agg(
            total_cost=("cost", "sum"),
            governable_outputs=("governable_output", "sum"),
            total_outputs=("task_id", "count"),
        )
        .reset_index()
    )

    condition_costs["cost_per_governable_output"] = (
        condition_costs["total_cost"] / condition_costs["governable_outputs"]
    )

    summary = summary.merge(
        condition_costs[
            [
                "condition",
                "total_cost",
                "governable_outputs",
                "total_outputs",
                "cost_per_governable_output",
            ]
        ],
        on="condition",
        how="left",
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
    assert "cost_per_governable_output" in summary.columns

    print("\nPilot 01 analysis sanity check passed.")


if __name__ == "__main__":
    main()