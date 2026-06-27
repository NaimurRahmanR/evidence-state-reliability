"""
Sanity check for pilot metric functions.

This checks the metric functions using a tiny controlled example.
It is not a full experiment yet.
"""

from src.evidence_state import EvidenceUnit, EvidenceState
from src.metrics import (
    evidence_state_reliability,
    evidence_state_degradation,
    final_failure,
    undetected_failure,
    audit_false_assurance,
    escalation_contamination,
    cost_per_governable_output,
)


def main() -> None:
    required_units = [
        EvidenceUnit(unit_id="F001", text="Fact one."),
        EvidenceUnit(unit_id="F002", text="Fact two."),
        EvidenceUnit(unit_id="F003", text="Fact three."),
    ]

    original_state = EvidenceState(
        task_id="T001",
        stage_name="original",
        evidence_text="Fact one. Fact two. Fact three.",
        preserved_units={"F001", "F002", "F003"},
    )

    degraded_state = EvidenceState(
        task_id="T001",
        stage_name="summary",
        evidence_text="Fact one. Fact three.",
        preserved_units={"F001", "F003"},
        lost_units={"F002"},
    )

    predicted_answer = "eligible"
    gold_answer = "not eligible"
    accepted_by_pipeline = True
    audit_accepts = True

    print("Evidence-State Reliability:", evidence_state_reliability(degraded_state, required_units))
    print("Evidence-State Degradation:", evidence_state_degradation(degraded_state))
    print("Final Failure:", final_failure(predicted_answer, gold_answer))
    print("Undetected Failure:", undetected_failure(predicted_answer, gold_answer, accepted_by_pipeline))
    print("Audit False Assurance:", audit_false_assurance(predicted_answer, gold_answer, audit_accepts))
    print("Escalation Contamination:", escalation_contamination(degraded_state, original_state))
    print("Cost per Governable Output:", cost_per_governable_output(total_cost=12.0, governable_outputs=3))

    assert evidence_state_reliability(degraded_state, required_units) == 2 / 3
    assert evidence_state_degradation(degraded_state) == 1
    assert final_failure(predicted_answer, gold_answer) is True
    assert undetected_failure(predicted_answer, gold_answer, accepted_by_pipeline) is True
    assert audit_false_assurance(predicted_answer, gold_answer, audit_accepts) is True
    assert escalation_contamination(degraded_state, original_state) is True
    assert cost_per_governable_output(total_cost=12.0, governable_outputs=3) == 4.0

    print("Metric sanity check passed.")


if __name__ == "__main__":
    main()