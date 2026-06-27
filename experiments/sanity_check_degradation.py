"""
Sanity check for evidence degradation functions.

This is not a full pipeline experiment.
It only checks whether degradation functions change EvidenceState as expected.
"""

import random

from src.evidence_state import EvidenceUnit
from src.degradation import (
    create_original_evidence_state,
    apply_fact_loss,
    apply_fact_mutation,
    apply_contradiction,
    apply_uncertainty_removal,
    apply_unsupported_addition,
)


def main() -> None:
    rng = random.Random(42)

    required_units = [
        EvidenceUnit(unit_id="F001", text="The case is Case Alpha."),
        EvidenceUnit(unit_id="F002", text="Case Alpha submitted all required documents."),
        EvidenceUnit(
            unit_id="F003",
            text="A case is eligible only if all required documents are submitted before the deadline.",
        ),
    ]

    original_text = " ".join(unit.text for unit in required_units)

    original_state = create_original_evidence_state(
        task_id="T001",
        original_evidence=original_text,
        required_units=required_units,
    )

    loss_state = apply_fact_loss(
        state=original_state,
        required_units=required_units,
        loss_probability=1.0,
        rng=rng,
    )

    mutation_state = apply_fact_mutation(
        state=original_state,
        required_units=required_units,
        mutation_probability=1.0,
        rng=rng,
    )

    contradiction_state = apply_contradiction(
        state=original_state,
        required_units=required_units,
        contradiction_probability=1.0,
        rng=rng,
    )

    uncertainty_state = apply_uncertainty_removal(original_state)

    addition_state = apply_unsupported_addition(original_state)

    print("Original reliability:", original_state.reliability_score(required_units))
    print("Fact loss reliability:", loss_state.reliability_score(required_units))
    print("Fact loss degradation count:", loss_state.degradation_count())

    print("Mutation reliability:", mutation_state.reliability_score(required_units))
    print("Mutation degradation count:", mutation_state.degradation_count())

    print("Contradiction reliability:", contradiction_state.reliability_score(required_units))
    print("Contradiction degradation count:", contradiction_state.degradation_count())

    print("Uncertainty removed flag:", uncertainty_state.uncertainty_removed)
    print("Unsupported additions:", addition_state.unsupported_additions)

    assert original_state.reliability_score(required_units) == 1.0
    assert loss_state.reliability_score(required_units) == 0.0
    assert loss_state.degradation_count() == 3

    assert mutation_state.reliability_score(required_units) == 0.0
    assert mutation_state.degradation_count() == 3

    assert contradiction_state.reliability_score(required_units) == 0.0
    assert contradiction_state.degradation_count() == 3

    assert uncertainty_state.uncertainty_removed is True
    assert uncertainty_state.degradation_count() == 1

    assert len(addition_state.unsupported_additions) == 1
    assert addition_state.degradation_count() == 1

    print("Degradation sanity check passed.")


if __name__ == "__main__":
    main()