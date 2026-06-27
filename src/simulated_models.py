"""
Simulated model logic for the Evidence-State Reliability project.

This file creates simple deterministic/probabilistic model behaviour
without calling real LLM APIs.

Purpose:
    Test the experimental design first without API cost.

Important:
    These are simulation assumptions only. They do not claim real LLM behaviour.
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


def evidence_reliability_score(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
) -> float:
    """
    Calculate a simple evidence reliability score for simulated model behaviour.

    This mirrors the basic intuition of Evidence-State Reliability:
    the more required units are preserved, the more reliable the evidence state is.
    """

    if not required_units:
        return 0.0

    required_ids = {unit.unit_id for unit in required_units}
    preserved_required_ids = required_ids.intersection(state.preserved_units)

    return len(preserved_required_ids) / len(required_ids)


def simulated_decision_model(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
    gold_answer: str,
    rng: random.Random,
    strong_model: bool = False,
) -> str:
    """
    Simulate a downstream decision model.

    Pilot 01 behaviour:
        - If all required evidence is preserved, return the gold answer.
        - If evidence is degraded, the model may fail.
        - A strong model has a lower failure probability, but it can still fail
          when evidence is already degraded.

    This function is kept for Pilot 01 reproducibility.
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

    Pilot 01 behaviour:
        - If audit sees full original evidence, it is more likely to reject wrong answers.
        - If audit sees degraded evidence, it may give false assurance.

    This function is kept for Pilot 01 reproducibility.
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


def simulated_decision_model_severity_sensitive(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
    gold_answer: str,
    rng: random.Random,
    strong_model: bool = True,
) -> str:
    """
    Simulate a downstream decision model for Pilot 02.

    Unlike the Pilot 01 model, this function makes failure probability depend
    on the quality of the evidence state.

    Simulation assumption:
        Lower evidence reliability should increase the probability of a wrong
        downstream decision, even when the downstream model is strong.
    """

    reliability = evidence_reliability_score(state, required_units)

    if reliability == 1.0 and state.degradation_count() == 0:
        return gold_answer

    evidence_damage = 1.0 - reliability

    if strong_model:
        base_failure_probability = 0.05
        evidence_damage_weight = 0.55
    else:
        base_failure_probability = 0.15
        evidence_damage_weight = 0.75

    failure_probability = base_failure_probability + (
        evidence_damage_weight * evidence_damage
    )

    failure_probability = min(max(failure_probability, 0.0), 0.95)

    if rng.random() < failure_probability:
        return flip_answer(gold_answer)

    return gold_answer


def simulated_audit_model_severity_sensitive(
    audit_state: EvidenceState,
    required_units: list[EvidenceUnit],
    predicted_answer: str,
    gold_answer: str,
    rng: random.Random,
    audit_strength: str = "basic",
) -> bool:
    """
    Simulate an audit model for Pilot 02.

    Simulation assumption:
        If the audit also sees degraded evidence, false assurance becomes more
        likely as evidence reliability decreases.
    """

    answer_is_correct = predicted_answer == gold_answer

    if answer_is_correct:
        return True

    reliability = evidence_reliability_score(audit_state, required_units)

    if reliability == 1.0 and audit_state.degradation_count() == 0:
        false_accept_probability = 0.10
    else:
        evidence_damage = 1.0 - reliability

        if audit_strength == "strong":
            base_false_accept_probability = 0.20
            evidence_damage_weight = 0.45
        else:
            base_false_accept_probability = 0.35
            evidence_damage_weight = 0.50

        false_accept_probability = base_false_accept_probability + (
            evidence_damage_weight * evidence_damage
        )

    false_accept_probability = min(max(false_accept_probability, 0.0), 0.95)

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