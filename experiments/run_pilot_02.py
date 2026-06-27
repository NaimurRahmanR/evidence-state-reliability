"""
Run Pilot 02 for Evidence-State Reliability.

Pilot 02 tests graded evidence degradation severity.
"""

from src.pilot_02_runner import Pilot02RunConfig, run_pilot_02


def main() -> None:
    config = Pilot02RunConfig()
    results = run_pilot_02(config)

    print("Pilot 02 run completed.")
    print(f"Rows: {len(results)}")
    print(f"Columns: {len(results.columns)}")
    print(f"Output saved to: {config.output_path}")

    print("\nMean results by degradation severity:")
    print(
        results.groupby("degradation_severity")[
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
    )

    expected_rows = (
        config.num_tasks
        * config.repeated_runs
        * results["degradation_severity"].nunique()
    )

    assert len(results) == expected_rows
    assert results["degradation_severity"].nunique() == 5

    print("\nPilot 02 sanity check passed.")


if __name__ == "__main__":
    main()