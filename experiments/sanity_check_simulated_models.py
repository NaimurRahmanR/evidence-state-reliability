"""
Sanity check for simulated decision and audit models.

This does not test the full pipeline yet.
It only checks that simulated models behave sensibly on controlled evidence states.
"""

import random

from src.evidence_state import EvidenceUnit, EvidenceState
from src.simulated_models import (
    evidence_supports_gold_answer,
    simulated_decision_model,
    simulated_audit_model,
    flip_answer,
)


def main() -> None:
    rng = random.Random(42)

    required_units = [
        EvidenceUnit(unit_id="F001", text="Fact one."),
        EvidenceUnit(unit_id="F002", text="Fact two."),
        EvidenceUnit(unit_id="F003", text="Fact three."),
    ]

    full_state = EvidenceState(
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

    gold_answer = "eligible"

    print("Full evidence supports gold:", evidence_supports_gold_answer(full_state, required_units))
    print("Degraded evidence supports gold:", evidence_supports_gold_answer(degraded_state, required_units))

    full_answer = simulated_decision_model(
        state=full_state,
        required_units=required_units,
        gold_answer=gold_answer,
        rng=rng,
        strong_model=False,
    )

    degraded_answer = simulated_decision_model(
        state=degraded_state,
        required_units=required_units,
        gold_answer=gold_answer,
        rng=rng,
        strong_model=False,
    )

    audit_accepts_full = simulated_audit_model(
        audit_state=full_state,
        required_units=required_units,
        predicted_answer=flip_answer(gold_answer),
        gold_answer=gold_answer,
        rng=rng,
    )

    print("Decision with full evidence:", full_answer)
    print("Decision with degraded evidence:", degraded_answer)
    print("Audit accepts wrong answer with full evidence:", audit_accepts_full)

    assert evidence_supports_gold_answer(full_state, required_units) is True
    assert evidence_supports_gold_answer(degraded_state, required_units) is False
    assert full_answer == gold_answer
    assert degraded_answer in {"eligible", "not eligible"}
    assert audit_accepts_full in {True, False}

    print("Simulated model sanity check passed.")


if __name__ == "__main__":
    main()