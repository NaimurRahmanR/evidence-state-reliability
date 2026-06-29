from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from src.pilot_03_llm_client import (
    DRY_RUN_CLIENT_MODE,
    Pilot03LLMCallRecord,
    get_pilot_03_client,
    summarise_llm_call_records,
)
from src.pilot_03_prompts import (
    build_audit_prompt_record,
    build_decision_prompt_record,
    build_escalation_prompt_record,
)
from src.pilot_03_tasks import Pilot03Task, generate_pilot_03_tasks, summarise_pilot_03_tasks


PILOT_03_RUNNER_VERSION = "pilot_03_dry_run_runner_v1"

CONDITION_ORIGINAL = "original_evidence"
CONDITION_MISSING_POLICY = "missing_policy_rule"
CONDITION_MISSING_ONE_REQUIRED_UNIT = "missing_one_required_unit"

DEFAULT_CONDITIONS = [
    CONDITION_ORIGINAL,
    CONDITION_MISSING_POLICY,
    CONDITION_MISSING_ONE_REQUIRED_UNIT,
]


@dataclass(frozen=True)
class Pilot03RunnerResult:
    """One completed dry-run chain for one task under one evidence condition."""

    task_id: str
    task_type: str
    condition: str
    gold_decision: str
    visible_evidence_unit_ids: list[str]
    decision_call: Pilot03LLMCallRecord
    audit_call: Pilot03LLMCallRecord
    escalation_call: Pilot03LLMCallRecord


def _all_evidence_unit_ids(task: Pilot03Task) -> list[str]:
    return [unit.unit_id for unit in task.original_evidence_units]


def _first_decision_required_unit_id(task: Pilot03Task) -> str:
    """
    Return the first non-policy required evidence unit.

    E6 is the policy rule in our current task design, so this picks one
    applicant-specific evidence unit when possible.
    """
    for unit in task.original_evidence_units:
        if unit.unit_id != "E6" and unit.required:
            return unit.unit_id

    return task.required_evidence_unit_ids[0]


def get_visible_evidence_unit_ids_for_condition(task: Pilot03Task, condition: str) -> list[str]:
    """Return visible evidence unit ids for one dry-run evidence condition."""
    all_ids = _all_evidence_unit_ids(task)

    if condition == CONDITION_ORIGINAL:
        return all_ids

    if condition == CONDITION_MISSING_POLICY:
        return [unit_id for unit_id in all_ids if unit_id != "E6"]

    if condition == CONDITION_MISSING_ONE_REQUIRED_UNIT:
        missing_unit_id = _first_decision_required_unit_id(task)
        return [unit_id for unit_id in all_ids if unit_id != missing_unit_id]

    raise ValueError(f"Unknown Pilot 03 condition: {condition}")


def run_pilot_03_dry_run_chain(
    task: Pilot03Task,
    condition: str,
) -> Pilot03RunnerResult:
    """
    Run decision -> audit -> escalation for one task and one evidence condition.

    This uses the dry-run client only. It does not call a real LLM.
    """
    visible_evidence_unit_ids = get_visible_evidence_unit_ids_for_condition(task, condition)
    client = get_pilot_03_client(mode=DRY_RUN_CLIENT_MODE)

    decision_prompt = build_decision_prompt_record(task)
    decision_call = client.run_decision(
        task=task,
        prompt_record=decision_prompt,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    audit_prompt = build_audit_prompt_record(
        task=task,
        decision_json=decision_call.raw_response_text,
    )
    audit_call = client.run_audit(
        task=task,
        prompt_record=audit_prompt,
        decision_response_text=decision_call.raw_response_text,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    escalation_prompt = build_escalation_prompt_record(
        task=task,
        decision_json=decision_call.raw_response_text,
        audit_json=audit_call.raw_response_text,
    )
    escalation_call = client.run_escalation(
        task=task,
        prompt_record=escalation_prompt,
        decision_response_text=decision_call.raw_response_text,
        audit_response_text=audit_call.raw_response_text,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
    )

    return Pilot03RunnerResult(
        task_id=task.task_id,
        task_type=task.task_type,
        condition=condition,
        gold_decision=task.gold_decision,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
        decision_call=decision_call,
        audit_call=audit_call,
        escalation_call=escalation_call,
    )


def run_pilot_03_dry_run(
    n_tasks: int = 10,
    conditions: list[str] | None = None,
) -> list[Pilot03RunnerResult]:
    """Run the Pilot 03 local dry-run scaffold for multiple tasks and conditions."""
    conditions = DEFAULT_CONDITIONS if conditions is None else conditions
    tasks = generate_pilot_03_tasks(n_tasks=n_tasks)

    results: list[Pilot03RunnerResult] = []
    for task in tasks:
        for condition in conditions:
            results.append(run_pilot_03_dry_run_chain(task=task, condition=condition))

    return results


def flatten_call_records(results: list[Pilot03RunnerResult]) -> list[Pilot03LLMCallRecord]:
    """Collect all decision, audit, and escalation call records from runner results."""
    records: list[Pilot03LLMCallRecord] = []
    for result in results:
        records.extend([result.decision_call, result.audit_call, result.escalation_call])
    return records


def summarise_runner_results(results: list[Pilot03RunnerResult]) -> dict[str, Any]:
    """Return a compact summary of Pilot 03 dry-run runner results."""
    call_records = flatten_call_records(results)

    condition_counts = Counter(result.condition for result in results)
    gold_decisions = Counter(result.gold_decision for result in results)

    escalation_correct = Counter()
    audit_passed = Counter()

    for result in results:
        escalation_decision = result.escalation_call.parsed_response.get("final_decision")
        is_correct = escalation_decision == result.gold_decision
        escalation_correct[str(is_correct)] += 1

        audit_value = result.audit_call.parsed_response.get("audit_passed")
        audit_passed[str(audit_value)] += 1

    return {
        "runner_version": PILOT_03_RUNNER_VERSION,
        "n_runner_results": len(results),
        "n_call_records": len(call_records),
        "condition_counts": dict(condition_counts),
        "gold_decisions": dict(gold_decisions),
        "escalation_correct": dict(escalation_correct),
        "audit_passed": dict(audit_passed),
        "call_record_summary": summarise_llm_call_records(call_records),
    }


def print_runner_preview(results: list[Pilot03RunnerResult], n_preview: int = 3) -> None:
    """Print a small human-readable preview without writing files yet."""
    print("Pilot 03 dry-run preview")
    print("========================")
    print(summarise_runner_results(results))
    print()

    for result in results[:n_preview]:
        decision = result.decision_call.parsed_response.get("final_decision")
        audit_passed = result.audit_call.parsed_response.get("audit_passed")
        escalation = result.escalation_call.parsed_response.get("final_decision")

        print(
            f"{result.task_id} | condition={result.condition} | "
            f"gold={result.gold_decision} | decision={decision} | "
            f"audit_passed={audit_passed} | escalation={escalation} | "
            f"visible_units={result.visible_evidence_unit_ids}"
        )


def main() -> None:
    """Run a small local Pilot 03 dry-run scaffold."""
    n_tasks = 10
    tasks = generate_pilot_03_tasks(n_tasks=n_tasks)

    print("Pilot 03 dry-run scaffold")
    print("=========================")
    print("No real LLM calls are made in this runner.")
    print("Task summary:")
    print(summarise_pilot_03_tasks(tasks))
    print()

    results: list[Pilot03RunnerResult] = []
    for task in tasks:
        for condition in DEFAULT_CONDITIONS:
            results.append(run_pilot_03_dry_run_chain(task=task, condition=condition))

    print_runner_preview(results)


if __name__ == "__main__":
    main()