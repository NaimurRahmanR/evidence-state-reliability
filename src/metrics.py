"""
Metric functions for the Evidence-State Reliability project.

These are pilot metrics for the first simulation.
They are operational definitions, not final validated theory.
"""

from src.evidence_state import EvidenceState, EvidenceUnit


def evidence_state_reliability(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
) -> float:
    """
    Compute Evidence-State Reliability.

    Pilot definition:
        preserved required evidence units / total required evidence units
    """

    return state.reliability_score(required_units)


def evidence_state_degradation(state: EvidenceState) -> int:
    """
    Compute Evidence-State Degradation.

    Pilot definition:
        count of visible degradation events
    """

    return state.degradation_count()


def final_failure(
    predicted_answer: str,
    gold_answer: str,
) -> bool:
    """
    Final Failure.

    True when the final pipeline answer does not match the gold answer.
    """

    return predicted_answer != gold_answer


def undetected_failure(
    predicted_answer: str,
    gold_answer: str,
    accepted_by_pipeline: bool,
) -> bool:
    """
    Undetected Failure.

    True when the final answer is wrong but accepted by the pipeline.
    """

    return final_failure(predicted_answer, gold_answer) and accepted_by_pipeline


def audit_false_assurance(
    predicted_answer: str,
    gold_answer: str,
    audit_accepts: bool,
) -> bool:
    """
    Audit False Assurance.

    True when the audit stage accepts a wrong answer.
    """

    return final_failure(predicted_answer, gold_answer) and audit_accepts


def escalation_contamination(
    escalation_state: EvidenceState,
    original_state: EvidenceState,
) -> bool:
    """
    Escalation Contamination.

    True when escalation receives evidence that is not equivalent to original evidence.

    Pilot definition:
        escalation evidence is contaminated if its preserved units differ from original,
        or if it contains mutation, contradiction, unsupported addition,
        uncertainty removal, or lost units.
    """

    if escalation_state.preserved_units != original_state.preserved_units:
        return True

    if escalation_state.degradation_count() > 0:
        return True

    return False


def cost_per_governable_output(
    total_cost: float,
    governable_outputs: int,
) -> float:
    """
    Cost per Governable Output.

    Pilot definition:
        total pipeline cost / outputs that pass reliability checks

    If there are no governable outputs, return infinity.
    """

    if governable_outputs == 0:
        return float("inf")

    return total_cost / governable_outputs