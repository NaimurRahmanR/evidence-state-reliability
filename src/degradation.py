"""
Evidence degradation functions for the Evidence-State Reliability project.

These functions simulate ways evidence can become degraded before reaching
a downstream LLM component.

Pilot degradation types:
1. fact loss
2. fact mutation
3. contradiction
4. uncertainty removal
5. unsupported addition

Pilot 02 adds graded degradation severity levels:
1. none
2. low
3. medium
4. high
5. severe
"""

import random

from src.evidence_state import EvidenceState, EvidenceUnit


def create_original_evidence_state(
    task_id: str,
    original_evidence: str,
    required_units: list[EvidenceUnit],
) -> EvidenceState:
    """
    Create the original evidence state.

    In this state, all required evidence units are treated as preserved.
    """

    return EvidenceState(
        task_id=task_id,
        stage_name="original",
        evidence_text=original_evidence,
        preserved_units={unit.unit_id for unit in required_units},
    )


def apply_fact_loss(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
    loss_probability: float,
    rng: random.Random,
    new_stage_name: str = "degraded_fact_loss",
) -> EvidenceState:
    """
    Simulate fact loss by removing some required evidence units.

    This does not rewrite the evidence text perfectly yet.
    For the pilot, the metric-level state is the main object.
    """

    preserved = set(state.preserved_units)
    lost = set(state.lost_units)

    for unit in required_units:
        if unit.unit_id in preserved and rng.random() < loss_probability:
            preserved.remove(unit.unit_id)
            lost.add(unit.unit_id)

    kept_texts = [
        unit.text
        for unit in required_units
        if unit.unit_id in preserved
    ]

    return EvidenceState(
        task_id=state.task_id,
        stage_name=new_stage_name,
        evidence_text=" ".join(kept_texts),
        preserved_units=preserved,
        lost_units=lost,
        mutated_units=set(state.mutated_units),
        contradicted_units=set(state.contradicted_units),
        unsupported_additions=list(state.unsupported_additions),
        uncertainty_removed=state.uncertainty_removed,
    )


def apply_fact_mutation(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
    mutation_probability: float,
    rng: random.Random,
    new_stage_name: str = "degraded_fact_mutation",
) -> EvidenceState:
    """
    Simulate fact mutation by marking preserved facts as changed.

    Pilot assumption:
    mutated facts are no longer counted as preserved.
    """

    preserved = set(state.preserved_units)
    mutated = set(state.mutated_units)

    for unit in required_units:
        if unit.unit_id in preserved and rng.random() < mutation_probability:
            preserved.remove(unit.unit_id)
            mutated.add(unit.unit_id)

    text_parts = []

    for unit in required_units:
        if unit.unit_id in preserved:
            text_parts.append(unit.text)
        elif unit.unit_id in mutated:
            text_parts.append(f"[MUTATED] {unit.text}")

    return EvidenceState(
        task_id=state.task_id,
        stage_name=new_stage_name,
        evidence_text=" ".join(text_parts),
        preserved_units=preserved,
        lost_units=set(state.lost_units),
        mutated_units=mutated,
        contradicted_units=set(state.contradicted_units),
        unsupported_additions=list(state.unsupported_additions),
        uncertainty_removed=state.uncertainty_removed,
    )


def apply_contradiction(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
    contradiction_probability: float,
    rng: random.Random,
    new_stage_name: str = "degraded_contradiction",
) -> EvidenceState:
    """
    Simulate contradiction by marking preserved facts as contradicted.

    Pilot assumption:
    contradicted facts are no longer counted as preserved.
    """

    preserved = set(state.preserved_units)
    contradicted = set(state.contradicted_units)

    for unit in required_units:
        if unit.unit_id in preserved and rng.random() < contradiction_probability:
            preserved.remove(unit.unit_id)
            contradicted.add(unit.unit_id)

    text_parts = []

    for unit in required_units:
        if unit.unit_id in preserved:
            text_parts.append(unit.text)
        elif unit.unit_id in contradicted:
            text_parts.append(f"[CONTRADICTED] Not true: {unit.text}")

    return EvidenceState(
        task_id=state.task_id,
        stage_name=new_stage_name,
        evidence_text=" ".join(text_parts),
        preserved_units=preserved,
        lost_units=set(state.lost_units),
        mutated_units=set(state.mutated_units),
        contradicted_units=contradicted,
        unsupported_additions=list(state.unsupported_additions),
        uncertainty_removed=state.uncertainty_removed,
    )


def apply_uncertainty_removal(
    state: EvidenceState,
    new_stage_name: str = "degraded_uncertainty_removed",
) -> EvidenceState:
    """
    Simulate uncertainty removal.

    For the pilot, this is represented as a flag.
    Later we can make uncertainty explicit in the task text.
    """

    return EvidenceState(
        task_id=state.task_id,
        stage_name=new_stage_name,
        evidence_text=state.evidence_text + " The evidence is certain.",
        preserved_units=set(state.preserved_units),
        lost_units=set(state.lost_units),
        mutated_units=set(state.mutated_units),
        contradicted_units=set(state.contradicted_units),
        unsupported_additions=list(state.unsupported_additions),
        uncertainty_removed=True,
    )


def apply_unsupported_addition(
    state: EvidenceState,
    addition_text: str = "The case has prior approval.",
    new_stage_name: str = "degraded_unsupported_addition",
) -> EvidenceState:
    """
    Simulate an unsupported addition.

    This adds a claim that was not present in the original required evidence.
    """

    unsupported_additions = list(state.unsupported_additions)
    unsupported_additions.append(addition_text)

    return EvidenceState(
        task_id=state.task_id,
        stage_name=new_stage_name,
        evidence_text=state.evidence_text + " " + addition_text,
        preserved_units=set(state.preserved_units),
        lost_units=set(state.lost_units),
        mutated_units=set(state.mutated_units),
        contradicted_units=set(state.contradicted_units),
        unsupported_additions=unsupported_additions,
        uncertainty_removed=state.uncertainty_removed,
    )


DEGRADATION_SEVERITY_CONFIGS = {
    "none": {
        "loss_probability": 0.00,
        "mutation_probability": 0.00,
        "contradiction_probability": 0.00,
        "remove_uncertainty": False,
        "add_unsupported_claim": False,
    },
    "low": {
        "loss_probability": 0.10,
        "mutation_probability": 0.05,
        "contradiction_probability": 0.00,
        "remove_uncertainty": False,
        "add_unsupported_claim": False,
    },
    "medium": {
        "loss_probability": 0.25,
        "mutation_probability": 0.10,
        "contradiction_probability": 0.05,
        "remove_uncertainty": False,
        "add_unsupported_claim": False,
    },
    "high": {
        "loss_probability": 0.40,
        "mutation_probability": 0.20,
        "contradiction_probability": 0.10,
        "remove_uncertainty": True,
        "add_unsupported_claim": False,
    },
    "severe": {
        "loss_probability": 0.55,
        "mutation_probability": 0.30,
        "contradiction_probability": 0.20,
        "remove_uncertainty": True,
        "add_unsupported_claim": True,
    },
}


def get_degradation_severity_levels() -> list[str]:
    """
    Return the supported degradation severity levels for Pilot 02.
    """

    return list(DEGRADATION_SEVERITY_CONFIGS.keys())


def apply_graded_degradation(
    state: EvidenceState,
    required_units: list[EvidenceUnit],
    severity: str,
    rng: random.Random,
) -> EvidenceState:
    """
    Apply graded evidence degradation for Pilot 02.

    This keeps Pilot 01 degradation functions intact, but gives Pilot 02
    a clean way to test increasing degradation severity.
    """

    if severity not in DEGRADATION_SEVERITY_CONFIGS:
        valid_levels = ", ".join(get_degradation_severity_levels())
        raise ValueError(
            f"Unknown degradation severity: {severity}. "
            f"Valid levels are: {valid_levels}"
        )

    config = DEGRADATION_SEVERITY_CONFIGS[severity]

    degraded_state = state

    degraded_state = apply_fact_loss(
        state=degraded_state,
        required_units=required_units,
        loss_probability=config["loss_probability"],
        rng=rng,
        new_stage_name=f"pilot_02_{severity}_loss",
    )

    degraded_state = apply_fact_mutation(
        state=degraded_state,
        required_units=required_units,
        mutation_probability=config["mutation_probability"],
        rng=rng,
        new_stage_name=f"pilot_02_{severity}_mutation",
    )

    degraded_state = apply_contradiction(
        state=degraded_state,
        required_units=required_units,
        contradiction_probability=config["contradiction_probability"],
        rng=rng,
        new_stage_name=f"pilot_02_{severity}_contradiction",
    )

    if config["remove_uncertainty"]:
        degraded_state = apply_uncertainty_removal(
            state=degraded_state,
            new_stage_name=f"pilot_02_{severity}_uncertainty_removed",
        )

    if config["add_unsupported_claim"]:
        degraded_state = apply_unsupported_addition(
            state=degraded_state,
            addition_text=(
                "The case has additional supporting evidence not shown "
                "in the record."
            ),
            new_stage_name=f"pilot_02_{severity}_unsupported_addition",
        )

    return degraded_state