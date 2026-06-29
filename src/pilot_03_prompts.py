from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.pilot_03_tasks import Pilot03Task, get_original_evidence_text


PROMPT_VERSION = "pilot_03_prompt_v1"
DECISION_PROMPT_TYPE = "decision"
AUDIT_PROMPT_TYPE = "audit"
ESCALATION_PROMPT_TYPE = "escalation"


@dataclass(frozen=True)
class Pilot03PromptRecord:
    """A prompt record that can be logged before any LLM call is made."""

    task_id: str
    task_type: str
    prompt_type: str
    prompt_version: str
    prompt_text: str
    metadata: dict[str, Any]


def _join_required_unit_ids(task: Pilot03Task) -> str:
    return ", ".join(task.required_evidence_unit_ids)


def _json_only_instruction() -> str:
    return (
        "Return JSON only. Do not include markdown, explanation outside JSON, or extra text. "
        "Use lowercase approve/reject decisions."
    )


def build_decision_prompt(task: Pilot03Task, evidence_text: str | None = None) -> str:
    """
    Build the downstream decision prompt for a Pilot 03 task.

    This prompt asks the model to make an approval decision from the evidence state.
    """
    evidence_text = get_original_evidence_text(task) if evidence_text is None else evidence_text

    return f"""You are a careful administrative decision assistant.

Your job is to decide whether the applicant should be approved or rejected.

Question:
{task.question}

Decision rule:
{task.decision_rule}

Evidence:
{evidence_text}

Required evidence unit ids:
{_join_required_unit_ids(task)}

Instructions:
- Use only the evidence given above.
- If all required criteria are satisfied, decide approve.
- If any required criterion is not satisfied, decide reject.
- Identify which evidence unit ids you used.
- Give a short reason.

Output format:
{{
  "final_decision": "approve or reject",
  "confidence": 0.0,
  "used_evidence_unit_ids": ["E1"],
  "reason": "short reason"
}}

{_json_only_instruction()}
"""


def build_audit_prompt(task: Pilot03Task, decision_json: str, evidence_text: str | None = None) -> str:
    """
    Build the audit prompt for a Pilot 03 task.

    This prompt asks the auditor to check whether a downstream decision is supported
    by the available evidence state.
    """
    evidence_text = get_original_evidence_text(task) if evidence_text is None else evidence_text

    return f"""You are a careful audit assistant.

Your job is to check whether the proposed decision is supported by the evidence.

Question:
{task.question}

Decision rule:
{task.decision_rule}

Evidence:
{evidence_text}

Proposed decision JSON:
{decision_json}

Required evidence unit ids:
{_join_required_unit_ids(task)}

Instructions:
- Use only the evidence and proposed decision shown above.
- Check whether the proposed decision follows the decision rule.
- Check whether the proposed decision used the required evidence.
- Do not change the task or invent missing evidence.
- Give a short audit reason.

Output format:
{{
  "audit_passed": true,
  "detected_issue": false,
  "supported_decision": "approve or reject",
  "missing_or_conflicting_evidence_unit_ids": ["E1"],
  "reason": "short reason"
}}

{_json_only_instruction()}
"""


def build_escalation_prompt(
    task: Pilot03Task,
    decision_json: str,
    audit_json: str,
    evidence_text: str | None = None,
) -> str:
    """
    Build the escalation prompt for a Pilot 03 task.

    This prompt asks the escalation component to make a final decision using the
    evidence state, downstream decision, and audit output.
    """
    evidence_text = get_original_evidence_text(task) if evidence_text is None else evidence_text

    return f"""You are a careful escalation assistant.

Your job is to make the final approval decision after reviewing the evidence, the proposed decision, and the audit output.

Question:
{task.question}

Decision rule:
{task.decision_rule}

Evidence:
{evidence_text}

Proposed decision JSON:
{decision_json}

Audit JSON:
{audit_json}

Required evidence unit ids:
{_join_required_unit_ids(task)}

Instructions:
- Use only the evidence, proposed decision, and audit output shown above.
- The final decision must follow the decision rule.
- If the proposed decision or audit output conflicts with the evidence, prioritise the evidence and decision rule.
- Give a short reason.

Output format:
{{
  "final_decision": "approve or reject",
  "confidence": 0.0,
  "used_evidence_unit_ids": ["E1"],
  "overrode_previous_stage": false,
  "reason": "short reason"
}}

{_json_only_instruction()}
"""


def build_prompt_record(
    task: Pilot03Task,
    prompt_type: str,
    prompt_text: str,
    metadata: dict[str, Any] | None = None,
) -> Pilot03PromptRecord:
    """Build a structured prompt record for logging and reproducibility."""
    return Pilot03PromptRecord(
        task_id=task.task_id,
        task_type=task.task_type,
        prompt_type=prompt_type,
        prompt_version=PROMPT_VERSION,
        prompt_text=prompt_text,
        metadata={} if metadata is None else metadata,
    )


def build_decision_prompt_record(task: Pilot03Task, evidence_text: str | None = None) -> Pilot03PromptRecord:
    """Build a logged decision prompt record."""
    prompt_text = build_decision_prompt(task=task, evidence_text=evidence_text)
    return build_prompt_record(
        task=task,
        prompt_type=DECISION_PROMPT_TYPE,
        prompt_text=prompt_text,
        metadata={
            "gold_decision": task.gold_decision,
            "required_evidence_unit_ids": task.required_evidence_unit_ids,
        },
    )


def build_audit_prompt_record(
    task: Pilot03Task,
    decision_json: str,
    evidence_text: str | None = None,
) -> Pilot03PromptRecord:
    """Build a logged audit prompt record."""
    prompt_text = build_audit_prompt(task=task, decision_json=decision_json, evidence_text=evidence_text)
    return build_prompt_record(
        task=task,
        prompt_type=AUDIT_PROMPT_TYPE,
        prompt_text=prompt_text,
        metadata={
            "gold_decision": task.gold_decision,
            "required_evidence_unit_ids": task.required_evidence_unit_ids,
        },
    )


def build_escalation_prompt_record(
    task: Pilot03Task,
    decision_json: str,
    audit_json: str,
    evidence_text: str | None = None,
) -> Pilot03PromptRecord:
    """Build a logged escalation prompt record."""
    prompt_text = build_escalation_prompt(
        task=task,
        decision_json=decision_json,
        audit_json=audit_json,
        evidence_text=evidence_text,
    )
    return build_prompt_record(
        task=task,
        prompt_type=ESCALATION_PROMPT_TYPE,
        prompt_text=prompt_text,
        metadata={
            "gold_decision": task.gold_decision,
            "required_evidence_unit_ids": task.required_evidence_unit_ids,
        },
    )


def prompt_record_to_dict(record: Pilot03PromptRecord) -> dict[str, Any]:
    """Convert a prompt record into a dictionary for future CSV/JSON logging."""
    return asdict(record)


def build_all_decision_prompt_records(tasks: list[Pilot03Task]) -> list[Pilot03PromptRecord]:
    """Build decision prompt records for a list of Pilot 03 tasks."""
    return [build_decision_prompt_record(task) for task in tasks]


def summarise_prompt_records(records: list[Pilot03PromptRecord]) -> dict[str, Any]:
    """Return a compact summary of prompt records."""
    prompt_type_counts: dict[str, int] = {}
    for record in records:
        prompt_type_counts[record.prompt_type] = prompt_type_counts.get(record.prompt_type, 0) + 1

    prompt_lengths = [len(record.prompt_text) for record in records]

    return {
        "n_prompt_records": len(records),
        "prompt_version": PROMPT_VERSION,
        "prompt_types": prompt_type_counts,
        "prompt_length_min": min(prompt_lengths) if prompt_lengths else 0,
        "prompt_length_max": max(prompt_lengths) if prompt_lengths else 0,
    }


if __name__ == "__main__":
    from src.pilot_03_tasks import generate_pilot_03_tasks

    tasks = generate_pilot_03_tasks(n_tasks=2)
    records = build_all_decision_prompt_records(tasks)
    print(summarise_prompt_records(records))
    print(records[0].prompt_text)