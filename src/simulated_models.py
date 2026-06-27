"""
Simulated model logic for the Evidence-State Reliability project.

This file creates simple deterministic/probabilistic model behaviour
without calling real LLM APIs.

Purpose:
    Test the experimental design first without API cost.
"""

import random

from src.evidence_state import EvidenceState, EvidenceUnit


def evidence_supports_gold_answer(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
) -> bool:
    """
    Check whether the evidence state preserves all required units.

    Pilot assumption:
        If all required evidence units are preserved, the model has enough
        evidence to produce the gold answer.

    This is a simulation assumption, not a validated claim.
    """

    required_ids = {unit.unit_id for unit in required_units}
    return required_ids.issubset(state.preserved_units)


def simulated_decision_model(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
    gold_answer: str,
    rng: random.Random,
    strong_model: bool = False,
) -> str:
    """
    Simulate a downstream decision model.

    Pilot behaviour:
        - If all required evidence is preserved, return the gold answer.
        - If evidence is degraded, the model may fail.
        - A strong model has a lower failure probability, but it can still fail
          when evidence is already degraded.

    This directly supports the research hypothesis we want to test later.
    """

    has_full_evidence = evidence_supports_gold_answer(state, required_units)

    if has_full_evidence and state.degradation_count() == 0:
        return gold_answer

    if strong_model:
        failure_probability = 0.25
    else:
        failure_probability = 0.60

    if rng.random() < failure_probability:
        return flip_answer(gold_answer)

    return gold_answer


def simulated_audit_model(
    audit_state: EvidenceState,
    required_units: list[EvidenceUnit],
    predicted_answer: str,
    gold_answer: str,
    rng: random.Random,
    audit_strength: str = "basic",
) -> bool:
    """
    Simulate an audit model.

    Returns:
        True if audit accepts the answer.
        False if audit rejects the answer.

    Pilot behaviour:
        - If audit sees full original evidence, it is more likely to reject wrong answers.
        - If audit sees degraded evidence, it may give false assurance.
    """

    has_full_evidence = evidence_supports_gold_answer(audit_state, required_units)
    answer_is_correct = predicted_answer == gold_answer

    if answer_is_correct:
        return True

    if has_full_evidence and audit_state.degradation_count() == 0:
        false_accept_probability = 0.10
    elif audit_strength == "strong":
        false_accept_probability = 0.35
    else:
        false_accept_probability = 0.70

    return rng.random() < false_accept_probability


def flip_answer(gold_answer: str) -> str:
    """
    Flip binary eligibility answer.
    """

    if gold_answer == "eligible":
        return "not eligible"

    if gold_answer == "not eligible":
        return "eligible"

    raise ValueError(f"Unsupported answer label: {gold_answer}")