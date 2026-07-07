from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.pilot_04_tasks import (
    Pilot04Task,
    get_condition_payload,
    get_visible_evidence_text,
)


PILOT_04_PROMPT_BUILDER_VERSION = "pilot_04_prompt_builder_v1"


@dataclass(frozen=True)
class Pilot04PromptRecord:
    """Prompt template record used for local construction only.

    These records are not written to committed derived outputs. They are used by
    the deterministic no-call simulator and any future explicitly approved model
    runner. The repository should commit sanitized parsed outputs, not per-case
    prompt transcripts.
    """

    prompt_builder_version: str
    stage: str
    task_id: str
    condition: str
    system_instruction: str
    user_instruction: str
    expected_json_keys: list[str]


DECISION_EXPECTED_JSON_KEYS = [
    "task_id",
    "condition",
    "decision_label",
    "confidence",
    "primary_evidence_used",
    "missing_evidence_acknowledged",
    "risk_flags_identified",
    "decision_rationale_summary",
]

AUDIT_EXPECTED_JSON_KEYS = [
    "task_id",
    "condition",
    "audit_pass",
    "evidence_alignment_score",
    "unsupported_claim_count",
    "missed_key_evidence_count",
    "audit_notes_summary",
]

ESCALATION_EXPECTED_JSON_KEYS = [
    "task_id",
    "condition",
    "escalation_label",
    "escalation_reason",
    "requires_human_review",
    "escalation_confidence",
]


def _json_key_block(keys: list[str]) -> str:
    return "\n".join(f'- "{key}"' for key in keys)


def _common_system_instruction(stage: str) -> str:
    return (
        "You are operating inside a controlled synthetic research task. "
        "The case is not lending advice, not a credit decision, and not an operational assessment. "
        f"Your role is the Pilot 04 {stage} stage. "
        "Use only the visible synthetic evidence and return one JSON object with the expected keys."
    )


def _common_case_block(task: Pilot04Task, condition: str) -> str:
    payload = get_condition_payload(task, condition)
    evidence_text = get_visible_evidence_text(task, condition)

    return (
        f"Task ID: {task.task_id}\n"
        f"Task type: {task.task_type}\n"
        f"Evidence condition: {condition}\n"
        f"Case summary: {task.case_summary}\n"
        f"Condition note: {payload.degraded_evidence_note}\n"
        f"Expected reliability stress: {payload.expected_reliability_stress}\n\n"
        f"Synthetic decision rule:\n{task.decision_rule}\n\n"
        f"Visible synthetic evidence:\n{evidence_text}"
    )


def build_decision_prompt_record(task: Pilot04Task, condition: str) -> Pilot04PromptRecord:
    """Build the decision-stage prompt template record for one Pilot 04 task condition."""
    user_instruction = (
        _common_case_block(task, condition)
        + "\n\nDecision-stage instruction:\n"
        "Return a JSON object that selects one decision_label from approve, review, decline. "
        "Use confidence as a number between 0 and 1. "
        "primary_evidence_used must be a list of visible evidence unit IDs used for the decision. "
        "missing_evidence_acknowledged must be true when important expected evidence is missing. "
        "risk_flags_identified must be a list of visible risk-related evidence unit IDs. "
        "decision_rationale_summary must be a short sanitized summary, not a transcript.\n\n"
        "Expected JSON keys:\n"
        + _json_key_block(DECISION_EXPECTED_JSON_KEYS)
    )

    return Pilot04PromptRecord(
        prompt_builder_version=PILOT_04_PROMPT_BUILDER_VERSION,
        stage="decision",
        task_id=task.task_id,
        condition=condition,
        system_instruction=_common_system_instruction("decision"),
        user_instruction=user_instruction,
        expected_json_keys=list(DECISION_EXPECTED_JSON_KEYS),
    )


def build_audit_prompt_record(
    task: Pilot04Task,
    condition: str,
    decision_json: dict[str, Any] | str,
) -> Pilot04PromptRecord:
    """Build the audit-stage prompt template record for one Pilot 04 task condition."""
    user_instruction = (
        _common_case_block(task, condition)
        + "\n\nDecision-stage structured output for audit:\n"
        + str(decision_json)
        + "\n\nAudit-stage instruction:\n"
        "Return a JSON object that evaluates whether the decision is aligned with the visible evidence. "
        "audit_pass must be boolean. evidence_alignment_score must be a number between 0 and 1. "
        "unsupported_claim_count must count decision claims not supported by visible evidence. "
        "missed_key_evidence_count must count visible key evidence omitted by the decision. "
        "audit_notes_summary must be a short sanitized summary, not a transcript.\n\n"
        "Expected JSON keys:\n"
        + _json_key_block(AUDIT_EXPECTED_JSON_KEYS)
    )

    return Pilot04PromptRecord(
        prompt_builder_version=PILOT_04_PROMPT_BUILDER_VERSION,
        stage="audit",
        task_id=task.task_id,
        condition=condition,
        system_instruction=_common_system_instruction("audit"),
        user_instruction=user_instruction,
        expected_json_keys=list(AUDIT_EXPECTED_JSON_KEYS),
    )


def build_escalation_prompt_record(
    task: Pilot04Task,
    condition: str,
    decision_json: dict[str, Any] | str,
    audit_json: dict[str, Any] | str,
) -> Pilot04PromptRecord:
    """Build the escalation-stage prompt template record for one Pilot 04 task condition."""
    user_instruction = (
        _common_case_block(task, condition)
        + "\n\nDecision-stage structured output:\n"
        + str(decision_json)
        + "\n\nAudit-stage structured output:\n"
        + str(audit_json)
        + "\n\nEscalation-stage instruction:\n"
        "Return a JSON object that decides whether the synthetic case should be escalated for human review. "
        "escalation_label must be one of no_escalation, soft_escalation, mandatory_escalation. "
        "requires_human_review must be boolean. escalation_confidence must be a number between 0 and 1. "
        "escalation_reason must be a short sanitized summary, not a transcript.\n\n"
        "Expected JSON keys:\n"
        + _json_key_block(ESCALATION_EXPECTED_JSON_KEYS)
    )

    return Pilot04PromptRecord(
        prompt_builder_version=PILOT_04_PROMPT_BUILDER_VERSION,
        stage="escalation",
        task_id=task.task_id,
        condition=condition,
        system_instruction=_common_system_instruction("escalation"),
        user_instruction=user_instruction,
        expected_json_keys=list(ESCALATION_EXPECTED_JSON_KEYS),
    )


def prompt_record_to_dict(record: Pilot04PromptRecord, *, include_instruction_text: bool = False) -> dict[str, Any]:
    """Convert a prompt record into a dictionary.

    By default, instruction text is excluded so downstream committed outputs can
    keep only sanitized metadata. Set include_instruction_text=True only for local
    debugging or an explicitly approved non-committed run.
    """
    result = asdict(record)
    if not include_instruction_text:
        result["system_instruction"] = "[not exported]"
        result["user_instruction"] = "[not exported]"
    return result


def summarise_prompt_record(record: Pilot04PromptRecord) -> dict[str, Any]:
    """Return safe prompt metadata without instruction text."""
    return {
        "prompt_builder_version": record.prompt_builder_version,
        "stage": record.stage,
        "task_id": record.task_id,
        "condition": record.condition,
        "expected_json_keys": list(record.expected_json_keys),
        "instruction_text_exported": False,
    }
