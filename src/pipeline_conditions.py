"""
Pipeline condition definitions for the Evidence-State Reliability project.

This file defines the pilot pipeline conditions.

At this stage, these are configuration objects only.
The actual pipeline simulation will be built later.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineCondition:
    """
    Configuration for one pipeline condition.

    A condition describes how evidence is passed through the pipeline.

    Example:
        direct_answer:
            downstream model sees original evidence directly

        summary_only:
            downstream model sees summarised/degraded evidence only
    """

    name: str
    description: str
    uses_original_evidence: bool
    uses_summary_evidence: bool
    has_audit_stage: bool
    audit_sees_original_evidence: bool
    has_escalation_stage: bool
    escalation_sees_original_evidence: bool


def get_pilot_conditions() -> list[PipelineCondition]:
    """
    Return the first set of pilot pipeline conditions.

    These are intentionally simple.
    Later, we can expand them into more detailed pipeline graphs.
    """

    return [
        PipelineCondition(
            name="direct_answer",
            description="The decision stage receives the original evidence directly.",
            uses_original_evidence=True,
            uses_summary_evidence=False,
            has_audit_stage=False,
            audit_sees_original_evidence=False,
            has_escalation_stage=False,
            escalation_sees_original_evidence=False,
        ),
        PipelineCondition(
            name="evidence_preserving",
            description="The pipeline keeps original evidence available alongside transformed evidence.",
            uses_original_evidence=True,
            uses_summary_evidence=True,
            has_audit_stage=True,
            audit_sees_original_evidence=True,
            has_escalation_stage=True,
            escalation_sees_original_evidence=True,
        ),
        PipelineCondition(
            name="summary_only",
            description="The decision stage receives only compressed or summarised evidence.",
            uses_original_evidence=False,
            uses_summary_evidence=True,
            has_audit_stage=False,
            audit_sees_original_evidence=False,
            has_escalation_stage=False,
            escalation_sees_original_evidence=False,
        ),
        PipelineCondition(
            name="visible_audit",
            description="The audit stage can inspect original evidence before accepting the output.",
            uses_original_evidence=False,
            uses_summary_evidence=True,
            has_audit_stage=True,
            audit_sees_original_evidence=True,
            has_escalation_stage=False,
            escalation_sees_original_evidence=False,
        ),
        PipelineCondition(
            name="blind_audit",
            description="The audit stage sees only the same transformed evidence as the decision stage.",
            uses_original_evidence=False,
            uses_summary_evidence=True,
            has_audit_stage=True,
            audit_sees_original_evidence=False,
            has_escalation_stage=False,
            escalation_sees_original_evidence=False,
        ),
    ]