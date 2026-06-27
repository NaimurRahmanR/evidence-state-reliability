"""
Sanity check for Pilot 02 graded degradation.

This checks that the new severity-based degradation function runs
and produces broadly sensible evidence-state changes.
"""

import random

from src.degradation import (
    create_original_evidence_state,
    apply_graded_degradation,
    get_degradation_severity_levels,
)
from src.evidence_state import EvidenceUnit
from src.metrics import evidence_state_reliability, evidence_state_degradation


def build_test_units() -> list[EvidenceUnit]:
    return [
        EvidenceUnit(
            unit_id="u1",
            text="The applicant income is above the approval threshold.",
            importance=1.0,
        ),
        EvidenceUnit(
            unit_id="u2",
            text="The applicant has no recent default record.",
            importance=1.0,
        ),
        EvidenceUnit(
            unit_id="u3",
            text="The debt-to-income ratio is acceptable.",
            importance=1.0,
        ),
        EvidenceUnit(
            unit_id="u4",
            text="The submitted documents are complete.",
            importance=1.0,
        ),
    ]


def main() -> None:
    rng = random.Random(42)
    required_units = build_test_units()

    original_state = create_original_evidence_state(
        task_id="sanity_task_001",
        original_evidence=" ".join(unit.text for unit in required_units),
        required_units=required_units,
    )

    print("\nPilot 02 graded degradation sanity check")
    print("=" * 48)

    rows = []

    for severity in get_degradation_severity_levels():
        degraded_state = apply_graded_degradation(
            state=original_state,
            required_units=required_units,
            severity=severity,
            rng=rng,
        )

        reliability = evidence_state_reliability(
            degraded_state,
            required_units,
        )
        degradation = evidence_state_degradation(degraded_state)

        rows.append(
            {
                "severity": severity,
                "stage_name": degraded_state.stage_name,
                "reliability": reliability,
                "degradation": degradation,
                "preserved_units": len(degraded_state.preserved_units),
                "lost_units": len(degraded_state.lost_units),
                "mutated_units": len(degraded_state.mutated_units),
                "contradicted_units": len(degraded_state.contradicted_units),
                "unsupported_additions": len(degraded_state.unsupported_additions),
                "uncertainty_removed": degraded_state.uncertainty_removed,
            }
        )

    for row in rows:
        print(
            f"{row['severity']:>7} | "
            f"reliability={row['reliability']:.4f} | "
            f"degradation={row['degradation']:.4f} | "
            f"preserved={row['preserved_units']} | "
            f"lost={row['lost_units']} | "
            f"mutated={row['mutated_units']} | "
            f"contradicted={row['contradicted_units']} | "
            f"unsupported={row['unsupported_additions']} | "
            f"uncertainty_removed={row['uncertainty_removed']}"
        )

    none_row = next(row for row in rows if row["severity"] == "none")
    severe_row = next(row for row in rows if row["severity"] == "severe")

    assert none_row["reliability"] == 1.0
    assert none_row["degradation"] == 0.0
    assert severe_row["degradation"] > none_row["degradation"]

    print("\nSanity check passed.")


if __name__ == "__main__":
    main()