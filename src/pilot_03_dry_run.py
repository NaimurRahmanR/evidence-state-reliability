from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from src.pilot_03_tasks import Pilot03Task


DRY_RUN_MODEL_NAME = "pilot_03_local_dry_run_v1"

DECISION_STAGE = "decision"
AUDIT_STAGE = "audit"
ESCALATION_STAGE = "escalation"


@dataclass(frozen=True)
class Pilot03DryRunOutput:
    """One local dry-run output for a Pilot 03 pipeline stage."""

    task_id: str
    task_type: str
    stage: str
    model_name: str
    dry_run: bool
    response_text: str
    parsed_response: dict[str, Any]


def _json_dumps(payload: dict[str, Any]) -> str:
    """Return stable JSON text that looks like a real model response."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _safe_json_loads(raw_json: str) -> dict[str, Any]:
    """Parse JSON text safely for local dry-run chaining."""
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    return parsed


def _visible_unit_ids(task: Pilot03Task, visible_evidence_unit_ids: list[str] | None = None) -> list[str]:
    """Return visible evidence ids, defaulting to all original evidence units."""
    if visible_evidence_unit_ids is None:
        return [unit.unit_id for unit in task.original_evidence_units]

    valid_ids = {unit.unit_id for unit in task.original_evidence_units}
    return [unit_id for unit_id in visible_evidence_unit_ids if unit_id in valid_ids]


def _missing_required_unit_ids(task: Pilot03Task, visible_evidence_unit_ids: list[str]) -> list[str]:
    visible = set(visible_evidence_unit_ids)
    return [unit_id for unit_id in task.required_evidence_unit_ids if unit_id not in visible]


def _failed_visible_criteria(task: Pilot03Task, visible_evidence_unit_ids: list[str]) -> list[str]:
    visible = set(visible_evidence_unit_ids)
    failed: list[str] = []

    for unit in task.original_evidence_units:
        if unit.unit_id not in visible:
            continue

        if isinstance(unit.value, bool) and unit.value is False:
            failed.append(unit.criterion)

    return failed


def _criteria_to_unit_ids(task: Pilot03Task, criteria: list[str]) -> list[str]:
    criteria_set = set(criteria)
    return [unit.unit_id for unit in task.original_evidence_units if unit.criterion in criteria_set]


def _infer_decision_from_visible_evidence(
    task: Pilot03Task,
    visible_evidence_unit_ids: list[str] | None = None,
) -> tuple[str, float, list[str], str]:
    """
    Infer a local dry-run decision from the visible evidence.

    This is not a real LLM. It is a deterministic local scaffold used to test
    Pilot 03 plumbing before any API call is added.
    """
    visible_ids = _visible_unit_ids(task, visible_evidence_unit_ids)
    missing_ids = _missing_required_unit_ids(task, visible_ids)
    failed_criteria = _failed_visible_criteria(task, visible_ids)

    if failed_criteria:
        failed_units = _criteria_to_unit_ids(task, failed_criteria)
        reason = "Reject because visible evidence shows failed required criteria: " + ", ".join(failed_criteria) + "."
        return "reject", 0.9, failed_units, reason

    if missing_ids:
        reason = "Reject because required evidence units are missing from the visible evidence: " + ", ".join(missing_ids) + "."
        return "reject", 0.6, visible_ids, reason

    reason = "Approve because all visible required evidence units satisfy the approval rule."
    return "approve", 0.9, visible_ids, reason


def make_dry_run_decision_response(
    task: Pilot03Task,
    visible_evidence_unit_ids: list[str] | None = None,
) -> Pilot03DryRunOutput:
    """Create a local dry-run decision-stage response."""
    decision, confidence, used_ids, reason = _infer_decision_from_visible_evidence(
        task=task,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    parsed_response = {
        "final_decision": decision,
        "confidence": confidence,
        "used_evidence_unit_ids": used_ids,
        "reason": reason,
    }

    return Pilot03DryRunOutput(
        task_id=task.task_id,
        task_type=task.task_type,
        stage=DECISION_STAGE,
        model_name=DRY_RUN_MODEL_NAME,
        dry_run=True,
        response_text=_json_dumps(parsed_response),
        parsed_response=parsed_response,
    )


def make_dry_run_audit_response(
    task: Pilot03Task,
    decision_json: str,
    visible_evidence_unit_ids: list[str] | None = None,
) -> Pilot03DryRunOutput:
    """Create a local dry-run audit-stage response."""
    proposed_decision = _safe_json_loads(decision_json)
    proposed_final_decision = str(proposed_decision.get("final_decision", "")).lower()

    supported_decision, _confidence, used_ids, support_reason = _infer_decision_from_visible_evidence(
        task=task,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    visible_ids = _visible_unit_ids(task, visible_evidence_unit_ids)
    missing_ids = _missing_required_unit_ids(task, visible_ids)
    failed_criteria = _failed_visible_criteria(task, visible_ids)
    failed_ids = _criteria_to_unit_ids(task, failed_criteria)

    audit_passed = proposed_final_decision == supported_decision and not missing_ids
    detected_issue = not audit_passed

    issue_ids = sorted(set(missing_ids + failed_ids))

    if audit_passed:
        reason = "Audit passed because the proposed decision follows the visible evidence and decision rule."
    elif proposed_final_decision not in {"approve", "reject"}:
        reason = "Audit failed because the proposed decision is missing or invalid."
    else:
        reason = "Audit detected an issue. " + support_reason

    parsed_response = {
        "audit_passed": audit_passed,
        "detected_issue": detected_issue,
        "supported_decision": supported_decision,
        "missing_or_conflicting_evidence_unit_ids": issue_ids,
        "reason": reason,
    }

    return Pilot03DryRunOutput(
        task_id=task.task_id,
        task_type=task.task_type,
        stage=AUDIT_STAGE,
        model_name=DRY_RUN_MODEL_NAME,
        dry_run=True,
        response_text=_json_dumps(parsed_response),
        parsed_response=parsed_response,
    )


def make_dry_run_escalation_response(
    task: Pilot03Task,
    decision_json: str,
    audit_json: str,
    visible_evidence_unit_ids: list[str] | None = None,
) -> Pilot03DryRunOutput:
    """Create a local dry-run escalation-stage response."""
    proposed_decision = _safe_json_loads(decision_json)
    audit_response = _safe_json_loads(audit_json)

    proposed_final_decision = str(proposed_decision.get("final_decision", "")).lower()
    audit_supported_decision = str(audit_response.get("supported_decision", "")).lower()
    audit_detected_issue = bool(audit_response.get("detected_issue", False))

    evidence_decision, confidence, used_ids, evidence_reason = _infer_decision_from_visible_evidence(
        task=task,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    if audit_detected_issue and audit_supported_decision in {"approve", "reject"}:
        final_decision = audit_supported_decision
        overrode_previous_stage = final_decision != proposed_final_decision
        reason = "Escalation followed the audit-supported decision. " + evidence_reason
    else:
        final_decision = evidence_decision
        overrode_previous_stage = final_decision != proposed_final_decision
        reason = "Escalation followed the visible evidence and decision rule. " + evidence_reason

    parsed_response = {
        "final_decision": final_decision,
        "confidence": confidence,
        "used_evidence_unit_ids": used_ids,
        "overrode_previous_stage": overrode_previous_stage,
        "reason": reason,
    }

    return Pilot03DryRunOutput(
        task_id=task.task_id,
        task_type=task.task_type,
        stage=ESCALATION_STAGE,
        model_name=DRY_RUN_MODEL_NAME,
        dry_run=True,
        response_text=_json_dumps(parsed_response),
        parsed_response=parsed_response,
    )


def run_dry_run_for_task(
    task: Pilot03Task,
    visible_evidence_unit_ids: list[str] | None = None,
) -> list[Pilot03DryRunOutput]:
    """
    Run one local dry-run decision -> audit -> escalation chain for one task.

    This does not call any real LLM. It only checks that the Pilot 03 pipeline
    shape can be represented locally before real model calls are introduced.
    """
    decision_output = make_dry_run_decision_response(
        task=task,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    audit_output = make_dry_run_audit_response(
        task=task,
        decision_json=decision_output.response_text,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    escalation_output = make_dry_run_escalation_response(
        task=task,
        decision_json=decision_output.response_text,
        audit_json=audit_output.response_text,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    return [decision_output, audit_output, escalation_output]


def dry_run_output_to_dict(output: Pilot03DryRunOutput) -> dict[str, Any]:
    """Convert a dry-run output into a dictionary for later logging."""
    return asdict(output)


def dry_run_outputs_to_records(outputs: list[Pilot03DryRunOutput]) -> list[dict[str, Any]]:
    """Convert dry-run outputs into records for future CSV/JSON export."""
    return [dry_run_output_to_dict(output) for output in outputs]


def summarise_dry_run_outputs(outputs: list[Pilot03DryRunOutput]) -> dict[str, Any]:
    """Return a compact summary of local dry-run outputs."""
    stage_counts = Counter(output.stage for output in outputs)
    final_decisions = Counter(
        output.parsed_response.get("final_decision")
        for output in outputs
        if output.stage in {DECISION_STAGE, ESCALATION_STAGE}
    )
    audit_passed = Counter(
        str(output.parsed_response.get("audit_passed"))
        for output in outputs
        if output.stage == AUDIT_STAGE
    )

    return {
        "n_outputs": len(outputs),
        "dry_run": all(output.dry_run for output in outputs),
        "model_name": DRY_RUN_MODEL_NAME,
        "stage_counts": dict(stage_counts),
        "final_decisions": dict(final_decisions),
        "audit_passed": dict(audit_passed),
    }


if __name__ == "__main__":
    from src.pilot_03_tasks import generate_pilot_03_tasks

    task = generate_pilot_03_tasks(n_tasks=1)[0]
    outputs = run_dry_run_for_task(task)
    print(summarise_dry_run_outputs(outputs))
    for output in outputs:
        print(output.stage, output.response_text)