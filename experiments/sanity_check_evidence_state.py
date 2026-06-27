"""
Small sanity check for EvidenceUnit and EvidenceState.

This is not a full experiment.
It only checks that the first research data structures behave as expected.
"""

from src.evidence_state import EvidenceUnit, EvidenceState


def main() -> None:
    required_units = [
        EvidenceUnit(unit_id="F001", text="The contract was signed on Monday."),
        EvidenceUnit(unit_id="F002", text="The refund deadline is 14 days."),
        EvidenceUnit(unit_id="F003", text="The customer requested cancellation by email."),
    ]

    summary_state = EvidenceState(
        task_id="T001",
        stage_name="summary",
        evidence_text=(
            "The contract was signed on Monday. "
            "The customer requested cancellation by email."
        ),
        preserved_units={"F001", "F003"},
        lost_units={"F002"},
    )

    reliability = summary_state.reliability_score(required_units)
    degradation = summary_state.degradation_count()

    print("Task ID:", summary_state.task_id)
    print("Stage:", summary_state.stage_name)
    print("Evidence-State Reliability:", reliability)
    print("Evidence-State Degradation Count:", degradation)

    assert reliability == 2 / 3
    assert degradation == 1

    print("Sanity check passed.")


if __name__ == "__main__":
    main()