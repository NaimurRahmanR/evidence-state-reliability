"""
Run the first simulation pilot for Evidence-State Reliability.

This script runs:
- 50 synthetic tasks
- 5 pipeline conditions
- 3 repeated runs

Expected rows:
    50 tasks × 5 conditions × 3 runs = 750 rows
"""

from src.pilot_runner import PilotRunConfig, run_pilot


def main() -> None:
    config = PilotRunConfig(
        num_tasks=50,
        repeated_runs=3,
        seed=42,
        output_path="data/outputs/pilot_results.csv",
    )

    results = run_pilot(config)

    print("Pilot run completed.")
    print("Rows:", len(results))
    print("Columns:", len(results.columns))
    print("Output saved to:", config.output_path)

    print("\nMean results by condition:")
    summary = results.groupby("condition")[
        [
            "evidence_state_reliability",
            "evidence_state_degradation",
            "final_failure",
            "undetected_failure",
            "audit_false_assurance",
            "escalation_contamination",
            "cost",
        ]
    ].mean()

    print(summary)

    assert len(results) == 50 * 5 * 3

    print("\nPilot 01 sanity check passed.")


if __name__ == "__main__":
    main()