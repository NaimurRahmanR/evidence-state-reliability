from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any

from src.pilot_04_parser import (
    Pilot04ParsedRecord,
    assert_schema_valid,
    parse_audit_output,
    parse_decision_output,
    parse_escalation_output,
)
from src.pilot_04_prompts import (
    build_audit_prompt_record,
    build_decision_prompt_record,
    build_escalation_prompt_record,
    summarise_prompt_record,
)
from src.pilot_04_tasks import (
    CONDITION_COMPLETE,
    CONDITION_CONFLICTED,
    CONDITION_PARTIAL,
    DEFAULT_CONDITIONS,
    Pilot04EvidenceUnit,
    Pilot04Task,
    generate_pilot_04_tasks,
    get_condition_payload,
    get_visible_evidence_units,
)


PILOT_04_DRY_RUN_VERSION = "pilot_04_deterministic_dry_run_v1"


@dataclass(frozen=True)
class Pilot04DryRunChainResult:
    """One deterministic no-call chain for one task under one evidence condition."""

    dry_run_version: str
    task_id: str
    task_type: str
    condition: str
    gold_decision: str
    visible_evidence_unit_ids: list[str]
    missing_required_evidence_unit_ids: list[str]
    decision_record: Pilot04ParsedRecord
    audit_record: Pilot04ParsedRecord
    escalation_record: Pilot04ParsedRecord
    prompt_metadata: list[dict[str, Any]]


def _support_units(units: list[Pilot04EvidenceUnit]) -> list[str]:
    return [unit.unit_id for unit in units if unit.direction == "support"]


def _risk_units(units: list[Pilot04EvidenceUnit]) -> list[str]:
    return [unit.unit_id for unit in units if unit.direction == "risk"]


def _conflict_visible(units: list[Pilot04EvidenceUnit]) -> bool:
    return any(unit.direction == "conflict" for unit in units)


def _missing_required_ids(task: Pilot04Task, visible_unit_ids: list[str]) -> list[str]:
    visible = set(visible_unit_ids)
    return [unit_id for unit_id in task.required_evidence_unit_ids if unit_id not in visible]


def _deterministic_decision_label(task: Pilot04Task, condition: str, visible_units: list[Pilot04EvidenceUnit]) -> str:
    risk_count = len(_risk_units(visible_units))
    missing_count = len(_missing_required_ids(task, [unit.unit_id for unit in visible_units]))
    conflict = _conflict_visible(visible_units)

    if condition == CONDITION_COMPLETE:
        return task.gold_decision

    if condition == CONDITION_PARTIAL:
        if missing_count >= 2:
            return "review"
        if task.gold_decision == "approve" and missing_count > 0:
            return "review"
        if task.gold_decision == "decline" and risk_count >= 3:
            return "decline"
        return "review"

    if condition == CONDITION_CONFLICTED:
        if task.gold_decision == "approve":
            return "review"
        if task.gold_decision == "decline" and risk_count >= 3:
            return "decline"
        if conflict:
            return "review"
        return task.gold_decision

    raise ValueError(f"Unknown Pilot 04 condition: {condition}")


def _deterministic_confidence(condition: str, decision_label: str, gold_decision: str, missing_count: int, conflict: bool) -> float:
    confidence = 0.88

    if condition == CONDITION_PARTIAL:
        confidence -= 0.18
    if condition == CONDITION_CONFLICTED:
        confidence -= 0.14
    if decision_label != gold_decision:
        confidence -= 0.10
    if missing_count:
        confidence -= min(0.12, missing_count * 0.04)
    if conflict:
        confidence -= 0.06

    return round(max(0.35, min(0.95, confidence)), 3)


def _decision_summary(condition: str, decision_label: str, missing_count: int, conflict: bool) -> str:
    if condition == CONDITION_COMPLETE:
        return f"Deterministic no-call decision uses complete synthetic evidence and selects {decision_label}."

    if condition == CONDITION_PARTIAL:
        return (
            f"Deterministic no-call decision selects {decision_label} while acknowledging "
            f"{missing_count} missing required evidence unit(s)."
        )

    if conflict:
        return f"Deterministic no-call decision selects {decision_label} with a controlled conflict note visible."

    return f"Deterministic no-call decision selects {decision_label} under the controlled evidence condition."


def simulate_decision_stage(task: Pilot04Task, condition: str) -> Pilot04ParsedRecord:
    """Simulate and parse a deterministic no-call decision-stage output."""
    visible_units = get_visible_evidence_units(task, condition)
    visible_ids = [unit.unit_id for unit in visible_units]
    missing_ids = _missing_required_ids(task, visible_ids)
    risk_ids = _risk_units(visible_units)
    conflict = _conflict_visible(visible_units)

    decision_label = _deterministic_decision_label(task, condition, visible_units)
    confidence = _deterministic_confidence(
        condition=condition,
        decision_label=decision_label,
        gold_decision=task.gold_decision,
        missing_count=len(missing_ids),
        conflict=conflict,
    )

    decision_output = {
        "task_id": task.task_id,
        "condition": condition,
        "decision_label": decision_label,
        "confidence": confidence,
        "primary_evidence_used": visible_ids,
        "missing_evidence_acknowledged": bool(missing_ids),
        "risk_flags_identified": risk_ids,
        "decision_rationale_summary": _decision_summary(condition, decision_label, len(missing_ids), conflict),
    }

    parsed = parse_decision_output(decision_output, task_id=task.task_id, condition=condition)
    assert_schema_valid(parsed)
    return parsed


def _alignment_score(task: Pilot04Task, condition: str, decision_record: Pilot04ParsedRecord) -> float:
    visible_units = get_visible_evidence_units(task, condition)
    visible_ids = [unit.unit_id for unit in visible_units]
    missing_count = len(_missing_required_ids(task, visible_ids))
    conflict = _conflict_visible(visible_units)
    label_matches_gold = decision_record.parsed.get("decision_label") == task.gold_decision

    score = 0.93
    if not label_matches_gold:
        score -= 0.18
    if missing_count:
        score -= min(0.20, missing_count * 0.06)
    if conflict:
        score -= 0.12
    if condition == CONDITION_PARTIAL:
        score -= 0.05
    if condition == CONDITION_CONFLICTED:
        score -= 0.04

    return round(max(0.20, min(0.98, score)), 3)


def simulate_audit_stage(task: Pilot04Task, condition: str, decision_record: Pilot04ParsedRecord) -> Pilot04ParsedRecord:
    """Simulate and parse a deterministic no-call audit-stage output."""
    visible_units = get_visible_evidence_units(task, condition)
    visible_ids = [unit.unit_id for unit in visible_units]
    missing_ids = _missing_required_ids(task, visible_ids)
    conflict = _conflict_visible(visible_units)

    decision_used = set(decision_record.parsed.get("primary_evidence_used", []))
    visible_set = set(visible_ids)
    unsupported_claim_count = len(decision_used - visible_set)

    risk_ids = set(_risk_units(visible_units))
    missed_key_evidence_count = len(visible_set - decision_used)

    alignment_score = _alignment_score(task, condition, decision_record)
    audit_pass = (
        alignment_score >= 0.72
        and unsupported_claim_count == 0
        and (not conflict or decision_record.parsed.get("decision_label") == "review")
    )

    audit_note = (
        "Audit passes because the deterministic decision is aligned with visible synthetic evidence."
        if audit_pass
        else "Audit flags evidence-state concerns in the deterministic no-call chain."
    )

    if missing_ids:
        audit_note += f" Missing required unit count: {len(missing_ids)}."
    if conflict:
        audit_note += " Controlled conflict note is visible."

    audit_output = {
        "task_id": task.task_id,
        "condition": condition,
        "audit_pass": audit_pass,
        "evidence_alignment_score": alignment_score,
        "unsupported_claim_count": unsupported_claim_count,
        "missed_key_evidence_count": missed_key_evidence_count,
        "audit_notes_summary": audit_note,
    }

    parsed = parse_audit_output(audit_output, task_id=task.task_id, condition=condition)
    assert_schema_valid(parsed)
    return parsed


def _escalation_label(condition: str, decision_record: Pilot04ParsedRecord, audit_record: Pilot04ParsedRecord) -> str:
    audit_pass = bool(audit_record.parsed.get("audit_pass"))
    alignment_score = float(audit_record.parsed.get("evidence_alignment_score", 0.0))
    missing_ack = bool(decision_record.parsed.get("missing_evidence_acknowledged"))

    if condition == CONDITION_CONFLICTED and not audit_pass:
        return "mandatory_escalation"
    if condition == CONDITION_PARTIAL and (missing_ack or alignment_score < 0.75):
        return "soft_escalation"
    if not audit_pass and alignment_score < 0.65:
        return "mandatory_escalation"
    if not audit_pass:
        return "soft_escalation"
    return "no_escalation"


def simulate_escalation_stage(
    task: Pilot04Task,
    condition: str,
    decision_record: Pilot04ParsedRecord,
    audit_record: Pilot04ParsedRecord,
) -> Pilot04ParsedRecord:
    """Simulate and parse a deterministic no-call escalation-stage output."""
    label = _escalation_label(condition, decision_record, audit_record)
    requires_human_review = label in {"soft_escalation", "mandatory_escalation"}

    alignment_score = float(audit_record.parsed.get("evidence_alignment_score", 0.0))
    confidence = round(max(0.40, min(0.94, 0.62 + abs(alignment_score - 0.50))), 3)

    if label == "no_escalation":
        reason = "Audit passed and no deterministic escalation trigger is active."
    elif label == "soft_escalation":
        reason = "Evidence-state degradation or audit concern triggers soft synthetic review."
    else:
        reason = "Audit concern under conflicted or low-alignment evidence triggers mandatory synthetic review."

    escalation_output = {
        "task_id": task.task_id,
        "condition": condition,
        "escalation_label": label,
        "escalation_reason": reason,
        "requires_human_review": requires_human_review,
        "escalation_confidence": confidence,
    }

    parsed = parse_escalation_output(escalation_output, task_id=task.task_id, condition=condition)
    assert_schema_valid(parsed)
    return parsed


def run_pilot_04_dry_run_chain(task: Pilot04Task, condition: str) -> Pilot04DryRunChainResult:
    """Run deterministic decision -> audit -> escalation for one task-condition pair."""
    payload = get_condition_payload(task, condition)
    visible_ids = list(payload.visible_evidence_unit_ids)
    missing_ids = _missing_required_ids(task, visible_ids)

    decision_prompt = build_decision_prompt_record(task, condition)
    decision_record = simulate_decision_stage(task, condition)

    audit_prompt = build_audit_prompt_record(task, condition, decision_record.parsed)
    audit_record = simulate_audit_stage(task, condition, decision_record)

    escalation_prompt = build_escalation_prompt_record(task, condition, decision_record.parsed, audit_record.parsed)
    escalation_record = simulate_escalation_stage(task, condition, decision_record, audit_record)

    prompt_metadata = [
        summarise_prompt_record(decision_prompt),
        summarise_prompt_record(audit_prompt),
        summarise_prompt_record(escalation_prompt),
    ]

    return Pilot04DryRunChainResult(
        dry_run_version=PILOT_04_DRY_RUN_VERSION,
        task_id=task.task_id,
        task_type=task.task_type,
        condition=condition,
        gold_decision=task.gold_decision,
        visible_evidence_unit_ids=visible_ids,
        missing_required_evidence_unit_ids=missing_ids,
        decision_record=decision_record,
        audit_record=audit_record,
        escalation_record=escalation_record,
        prompt_metadata=prompt_metadata,
    )


def run_pilot_04_dry_run(
    n_tasks: int = 24,
    conditions: list[str] | None = None,
) -> list[Pilot04DryRunChainResult]:
    """Run deterministic no-call Pilot 04 chains for multiple tasks and conditions."""
    active_conditions = list(DEFAULT_CONDITIONS if conditions is None else conditions)
    tasks = generate_pilot_04_tasks(n_tasks=n_tasks)

    results: list[Pilot04DryRunChainResult] = []
    for task in tasks:
        for condition in active_conditions:
            results.append(run_pilot_04_dry_run_chain(task, condition))

    return results


def stage_rows(results: list[Pilot04DryRunChainResult], stage: str) -> list[dict[str, Any]]:
    """Return sanitized flat rows for one stage."""
    rows: list[dict[str, Any]] = []

    for result in results:
        if stage == "decision":
            parsed = result.decision_record.parsed
            rows.append(
                {
                    "dry_run_version": result.dry_run_version,
                    "task_id": result.task_id,
                    "task_type": result.task_type,
                    "condition": result.condition,
                    "gold_decision": result.gold_decision,
                    "schema_valid": result.decision_record.schema_valid,
                    "decision_label": parsed["decision_label"],
                    "decision_matches_gold": parsed["decision_label"] == result.gold_decision,
                    "confidence": parsed["confidence"],
                    "n_primary_evidence_used": len(parsed["primary_evidence_used"]),
                    "primary_evidence_used": json.dumps(parsed["primary_evidence_used"], ensure_ascii=False),
                    "missing_evidence_acknowledged": parsed["missing_evidence_acknowledged"],
                    "n_risk_flags_identified": len(parsed["risk_flags_identified"]),
                    "risk_flags_identified": json.dumps(parsed["risk_flags_identified"], ensure_ascii=False),
                    "decision_rationale_summary": parsed["decision_rationale_summary"],
                }
            )
        elif stage == "audit":
            parsed = result.audit_record.parsed
            rows.append(
                {
                    "dry_run_version": result.dry_run_version,
                    "task_id": result.task_id,
                    "task_type": result.task_type,
                    "condition": result.condition,
                    "gold_decision": result.gold_decision,
                    "schema_valid": result.audit_record.schema_valid,
                    "audit_pass": parsed["audit_pass"],
                    "evidence_alignment_score": parsed["evidence_alignment_score"],
                    "unsupported_claim_count": parsed["unsupported_claim_count"],
                    "missed_key_evidence_count": parsed["missed_key_evidence_count"],
                    "audit_notes_summary": parsed["audit_notes_summary"],
                }
            )
        elif stage == "escalation":
            parsed = result.escalation_record.parsed
            rows.append(
                {
                    "dry_run_version": result.dry_run_version,
                    "task_id": result.task_id,
                    "task_type": result.task_type,
                    "condition": result.condition,
                    "gold_decision": result.gold_decision,
                    "schema_valid": result.escalation_record.schema_valid,
                    "escalation_label": parsed["escalation_label"],
                    "requires_human_review": parsed["requires_human_review"],
                    "escalation_confidence": parsed["escalation_confidence"],
                    "escalation_reason": parsed["escalation_reason"],
                }
            )
        else:
            raise ValueError(f"Unknown Pilot 04 stage: {stage}")

    return rows


def chain_rows(results: list[Pilot04DryRunChainResult]) -> list[dict[str, Any]]:
    """Return sanitized one-row-per-chain outputs."""
    rows: list[dict[str, Any]] = []

    for result in results:
        decision = result.decision_record.parsed
        audit = result.audit_record.parsed
        escalation = result.escalation_record.parsed

        rows.append(
            {
                "dry_run_version": result.dry_run_version,
                "task_id": result.task_id,
                "task_type": result.task_type,
                "condition": result.condition,
                "gold_decision": result.gold_decision,
                "visible_evidence_unit_ids": json.dumps(result.visible_evidence_unit_ids, ensure_ascii=False),
                "missing_required_evidence_unit_ids": json.dumps(
                    result.missing_required_evidence_unit_ids,
                    ensure_ascii=False,
                ),
                "n_visible_evidence_units": len(result.visible_evidence_unit_ids),
                "n_missing_required_evidence_units": len(result.missing_required_evidence_unit_ids),
                "decision_label": decision["decision_label"],
                "decision_matches_gold": decision["decision_label"] == result.gold_decision,
                "decision_confidence": decision["confidence"],
                "missing_evidence_acknowledged": decision["missing_evidence_acknowledged"],
                "audit_pass": audit["audit_pass"],
                "evidence_alignment_score": audit["evidence_alignment_score"],
                "unsupported_claim_count": audit["unsupported_claim_count"],
                "missed_key_evidence_count": audit["missed_key_evidence_count"],
                "escalation_label": escalation["escalation_label"],
                "requires_human_review": escalation["requires_human_review"],
                "escalation_confidence": escalation["escalation_confidence"],
                "all_stage_schemas_valid": (
                    result.decision_record.schema_valid
                    and result.audit_record.schema_valid
                    and result.escalation_record.schema_valid
                ),
                "prompt_instruction_text_exported": any(
                    item.get("instruction_text_exported") for item in result.prompt_metadata
                ),
                "real_api_calls": 0,
            }
        )

    return rows


def summarise_pilot_04_dry_run(results: list[Pilot04DryRunChainResult]) -> dict[str, Any]:
    """Return deterministic dry-run summary metadata."""
    chains_by_condition = Counter(result.condition for result in results)
    decision_by_condition = Counter(
        f"{result.condition}:{result.decision_record.parsed['decision_label']}"
        for result in results
    )
    escalation_by_condition = Counter(
        f"{result.condition}:{result.escalation_record.parsed['escalation_label']}"
        for result in results
    )

    all_schema_valid = all(
        result.decision_record.schema_valid
        and result.audit_record.schema_valid
        and result.escalation_record.schema_valid
        for result in results
    )

    prompt_instruction_text_exported = any(
        item.get("instruction_text_exported")
        for result in results
        for item in result.prompt_metadata
    )

    return {
        "dry_run_version": PILOT_04_DRY_RUN_VERSION,
        "n_chains": len(results),
        "n_stage_records": len(results) * 3,
        "chains_by_condition": dict(sorted(chains_by_condition.items())),
        "decision_by_condition": dict(sorted(decision_by_condition.items())),
        "escalation_by_condition": dict(sorted(escalation_by_condition.items())),
        "all_stage_schemas_valid": all_schema_valid,
        "prompt_instruction_text_exported": prompt_instruction_text_exported,
        "real_api_calls": 0,
        "raw_response_inspection": False,
    }
