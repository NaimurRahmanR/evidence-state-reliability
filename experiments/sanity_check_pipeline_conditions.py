"""
Sanity check for pilot pipeline condition definitions.

This does not run the pipeline yet.
It only checks that the condition configurations are loaded correctly.
"""

from src.pipeline_conditions import get_pilot_conditions


def main() -> None:
    conditions = get_pilot_conditions()

    print("Number of pilot conditions:", len(conditions))

    for condition in conditions:
        print(
            condition.name,
            "| audit:",
            condition.has_audit_stage,
            "| audit sees original:",
            condition.audit_sees_original_evidence,
            "| escalation:",
            condition.has_escalation_stage,
        )

    condition_names = {condition.name for condition in conditions}

    assert len(conditions) == 5
    assert "direct_answer" in condition_names
    assert "evidence_preserving" in condition_names
    assert "summary_only" in condition_names
    assert "visible_audit" in condition_names
    assert "blind_audit" in condition_names

    print("Pipeline condition sanity check passed.")


if __name__ == "__main__":
    main()