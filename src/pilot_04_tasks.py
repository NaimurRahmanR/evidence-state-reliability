from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from random import Random
from typing import Any


TASK_TYPE = "synthetic_loan_risk_decision_support"
DEFAULT_TASK_COUNT = 24
DEFAULT_SEED = 404

CONDITION_COMPLETE = "complete"
CONDITION_PARTIAL = "partial"
CONDITION_CONFLICTED = "conflicted"

DEFAULT_CONDITIONS = [
    CONDITION_COMPLETE,
    CONDITION_PARTIAL,
    CONDITION_CONFLICTED,
]

ALLOWED_GOLD_LABELS = ["approve", "review", "decline"]


@dataclass(frozen=True)
class Pilot04EvidenceUnit:
    """One synthetic evidence item available to the downstream decision component."""

    unit_id: str
    text: str
    criterion: str
    value: bool | str | int | float
    direction: str
    required: bool = True


@dataclass(frozen=True)
class Pilot04ConditionPayload:
    """Visible evidence state for one controlled Pilot 04 evidence condition."""

    condition: str
    visible_evidence_unit_ids: list[str]
    degraded_evidence_note: str
    expected_reliability_stress: str


@dataclass(frozen=True)
class Pilot04Task:
    """A controlled, automatically judgeable synthetic loan-risk support task."""

    task_id: str
    task_type: str
    applicant_id: str
    case_summary: str
    gold_decision: str
    gold_answer: str
    gold_reason: str
    decision_rule: str
    original_evidence_units: list[Pilot04EvidenceUnit]
    required_evidence_unit_ids: list[str]
    expected_primary_evidence_unit_ids: list[str]
    condition_payloads: list[Pilot04ConditionPayload]


def _currency(amount: int) -> str:
    return f"GBP {amount:,}"


def _make_case_summary(task_number: int, profile_name: str) -> str:
    return (
        f"Synthetic loan-risk support case {task_number:04d} for {profile_name}. "
        "The case is generated only for controlled evidence-state reliability testing."
    )


def _employment_text(stable_employment: bool, task_number: int) -> str:
    if stable_employment:
        months = 18 + (task_number % 9) * 3
        return f"Applicant has been in stable employment for {months} months."

    months = 2 + (task_number % 4)
    return f"Applicant changed employment recently and has only {months} months in the current role."


def _income_text(income_margin_positive: bool, task_number: int) -> str:
    threshold = 1850 + (task_number % 4) * 100
    income = threshold + 420 + (task_number % 3) * 60 if income_margin_positive else threshold - 260 - (task_number % 3) * 70

    if income_margin_positive:
        return (
            f"Verified monthly net income is {_currency(income)}, which is above the "
            f"synthetic affordability threshold of {_currency(threshold)}."
        )

    return (
        f"Verified monthly net income is {_currency(income)}, which is below the "
        f"synthetic affordability threshold of {_currency(threshold)}."
    )


def _debt_text(low_debt_burden: bool, task_number: int) -> str:
    ratio = 24 + (task_number % 5) * 2 if low_debt_burden else 53 + (task_number % 6) * 3

    if low_debt_burden:
        return f"Existing monthly debt burden is {ratio}% of verified net income, which is within the synthetic low-risk band."

    return f"Existing monthly debt burden is {ratio}% of verified net income, which is above the synthetic risk threshold."


def _repayment_text(clean_repayment_history: bool, task_number: int) -> str:
    if clean_repayment_history:
        months = 12 + (task_number % 8) * 3
        return f"Repayment record shows no missed payments in the last {months} months."

    missed = 1 + (task_number % 3)
    return f"Repayment record shows {missed} missed payment event(s) in the last 12 months."


def _cash_buffer_text(has_cash_buffer: bool, task_number: int) -> str:
    months = 3 + (task_number % 4) if has_cash_buffer else task_number % 2

    if has_cash_buffer:
        return f"Applicant has an emergency cash buffer covering approximately {months} months of essential expenses."

    return f"Applicant has limited emergency cash buffer, covering approximately {months} months of essential expenses."


def _adverse_flag_text(no_adverse_flag: bool) -> str:
    if no_adverse_flag:
        return "No synthetic adverse risk flag is present in the case file."

    return "A synthetic adverse risk flag is present and requires review before a positive decision."


def _policy_text() -> str:
    return (
        "Synthetic decision rule: approve only when income, employment, debt burden, repayment history, "
        "cash buffer, and adverse-flag checks are all supportive. Use review when the evidence is mixed "
        "or materially incomplete. Use decline when multiple required risk checks are not supportive."
    )


def _gold_label(pattern: dict[str, bool]) -> str:
    failed_count = sum(1 for value in pattern.values() if not value)

    if failed_count == 0:
        return "approve"
    if failed_count <= 2:
        return "review"
    return "decline"


def _gold_reason(pattern: dict[str, bool], gold_decision: str) -> str:
    failed = [criterion.replace("_", " ") for criterion, passed in pattern.items() if not passed]

    if gold_decision == "approve":
        return "Approve because all synthetic loan-risk support criteria are satisfied."

    if gold_decision == "review":
        return (
            "Review because the case has limited risk concerns or incomplete support on: "
            + ", ".join(failed)
            + "."
        )

    return (
        "Decline because multiple synthetic risk criteria are not satisfied: "
        + ", ".join(failed)
        + "."
    )


def _condition_payloads(gold_decision: str) -> list[Pilot04ConditionPayload]:
    complete_ids = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]

    if gold_decision == "approve":
        partial_ids = ["E1", "E2", "E3", "E4", "E7"]
    else:
        partial_ids = ["E1", "E3", "E4", "E6", "E7"]

    conflicted_ids = ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]

    return [
        Pilot04ConditionPayload(
            condition=CONDITION_COMPLETE,
            visible_evidence_unit_ids=complete_ids,
            degraded_evidence_note="All core synthetic evidence units are visible.",
            expected_reliability_stress="baseline evidence state",
        ),
        Pilot04ConditionPayload(
            condition=CONDITION_PARTIAL,
            visible_evidence_unit_ids=partial_ids,
            degraded_evidence_note="Some relevant evidence units are hidden from the downstream stages.",
            expected_reliability_stress="missing evidence sensitivity",
        ),
        Pilot04ConditionPayload(
            condition=CONDITION_CONFLICTED,
            visible_evidence_unit_ids=conflicted_ids,
            degraded_evidence_note="Core evidence remains visible, with one controlled conflicting note added.",
            expected_reliability_stress="ambiguity and contradiction sensitivity",
        ),
    ]


def _build_task(task_number: int, profile_name: str, raw_pattern: list[bool]) -> Pilot04Task:
    criteria_order = [
        "income_margin_positive",
        "stable_employment",
        "low_debt_burden",
        "clean_repayment_history",
        "cash_buffer_present",
        "no_adverse_flag",
    ]

    pattern = dict(zip(criteria_order, raw_pattern, strict=True))
    task_id = f"P04-T{task_number:04d}"
    applicant_id = f"LOAN-SYN-{4000 + task_number}"

    evidence_units = [
        Pilot04EvidenceUnit(
            unit_id="E1",
            text=_income_text(pattern["income_margin_positive"], task_number),
            criterion="income_margin_positive",
            value=pattern["income_margin_positive"],
            direction="support" if pattern["income_margin_positive"] else "risk",
            required=True,
        ),
        Pilot04EvidenceUnit(
            unit_id="E2",
            text=_employment_text(pattern["stable_employment"], task_number),
            criterion="stable_employment",
            value=pattern["stable_employment"],
            direction="support" if pattern["stable_employment"] else "risk",
            required=True,
        ),
        Pilot04EvidenceUnit(
            unit_id="E3",
            text=_debt_text(pattern["low_debt_burden"], task_number),
            criterion="low_debt_burden",
            value=pattern["low_debt_burden"],
            direction="support" if pattern["low_debt_burden"] else "risk",
            required=True,
        ),
        Pilot04EvidenceUnit(
            unit_id="E4",
            text=_repayment_text(pattern["clean_repayment_history"], task_number),
            criterion="clean_repayment_history",
            value=pattern["clean_repayment_history"],
            direction="support" if pattern["clean_repayment_history"] else "risk",
            required=True,
        ),
        Pilot04EvidenceUnit(
            unit_id="E5",
            text=_cash_buffer_text(pattern["cash_buffer_present"], task_number),
            criterion="cash_buffer_present",
            value=pattern["cash_buffer_present"],
            direction="support" if pattern["cash_buffer_present"] else "risk",
            required=True,
        ),
        Pilot04EvidenceUnit(
            unit_id="E6",
            text=_adverse_flag_text(pattern["no_adverse_flag"]),
            criterion="no_adverse_flag",
            value=pattern["no_adverse_flag"],
            direction="support" if pattern["no_adverse_flag"] else "risk",
            required=True,
        ),
        Pilot04EvidenceUnit(
            unit_id="E7",
            text=_policy_text(),
            criterion="synthetic_policy_rule",
            value="all_core_checks_required",
            direction="rule",
            required=True,
        ),
        Pilot04EvidenceUnit(
            unit_id="E8",
            text="Controlled conflict note: one case note gives a different risk interpretation than the structured evidence.",
            criterion="controlled_conflict_note",
            value="conflict_note_present",
            direction="conflict",
            required=False,
        ),
    ]

    gold_decision = _gold_label(pattern)
    gold_reason = _gold_reason(pattern, gold_decision)

    return Pilot04Task(
        task_id=task_id,
        task_type=TASK_TYPE,
        applicant_id=applicant_id,
        case_summary=_make_case_summary(task_number, profile_name),
        gold_decision=gold_decision,
        gold_answer=gold_decision,
        gold_reason=gold_reason,
        decision_rule=_policy_text(),
        original_evidence_units=evidence_units,
        required_evidence_unit_ids=[unit.unit_id for unit in evidence_units if unit.required],
        expected_primary_evidence_unit_ids=["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
        condition_payloads=_condition_payloads(gold_decision),
    )


def generate_pilot_04_tasks(n_tasks: int = DEFAULT_TASK_COUNT, seed: int = DEFAULT_SEED) -> list[Pilot04Task]:
    """
    Generate deterministic synthetic loan-risk support tasks for Pilot 04.

    The tasks are controlled, synthetic, automatically judgeable, and balanced
    across approve, review, and decline labels. They are not lending advice and
    must not be interpreted as operational credit-risk assessment.
    """
    if n_tasks <= 0:
        raise ValueError("n_tasks must be a positive integer.")

    approve_patterns = [
        [True, True, True, True, True, True],
        [True, True, True, True, True, True],
        [True, True, True, True, True, True],
        [True, True, True, True, True, True],
        [True, True, True, True, True, True],
        [True, True, True, True, True, True],
        [True, True, True, True, True, True],
        [True, True, True, True, True, True],
    ]

    review_patterns = [
        [False, True, True, True, True, True],
        [True, False, True, True, True, True],
        [True, True, False, True, True, True],
        [True, True, True, False, True, True],
        [True, True, True, True, False, True],
        [True, True, True, True, True, False],
        [False, True, True, False, True, True],
        [True, False, True, True, False, True],
    ]

    decline_patterns = [
        [False, False, True, False, True, True],
        [False, True, False, False, True, True],
        [True, False, False, False, True, True],
        [False, True, False, True, False, False],
        [False, False, False, True, True, False],
        [True, False, False, False, False, True],
        [False, False, True, False, False, False],
        [False, False, False, False, True, True],
    ]

    pattern_pool = [
        ("low-risk profile", pattern) for pattern in approve_patterns
    ] + [
        ("mixed-risk profile", pattern) for pattern in review_patterns
    ] + [
        ("high-risk profile", pattern) for pattern in decline_patterns
    ]

    rng = Random(seed)
    rng.shuffle(pattern_pool)

    tasks: list[Pilot04Task] = []
    for index in range(n_tasks):
        profile_name, pattern = pattern_pool[index % len(pattern_pool)]
        task_number = index + 1
        tasks.append(_build_task(task_number=task_number, profile_name=profile_name, raw_pattern=pattern))

    return tasks


def get_original_evidence_text(task: Pilot04Task) -> str:
    """Return the complete synthetic evidence as a plain-text block for local prompt construction."""
    return "\n".join(f"- {unit.unit_id}: {unit.text}" for unit in task.original_evidence_units)


def get_condition_payload(task: Pilot04Task, condition: str) -> Pilot04ConditionPayload:
    """Return the condition payload for one Pilot 04 task."""
    for payload in task.condition_payloads:
        if payload.condition == condition:
            return payload
    raise ValueError(f"Unknown Pilot 04 condition for {task.task_id}: {condition}")


def get_visible_evidence_units(task: Pilot04Task, condition: str) -> list[Pilot04EvidenceUnit]:
    """Return visible evidence units for one controlled evidence condition."""
    payload = get_condition_payload(task, condition)
    visible_ids = set(payload.visible_evidence_unit_ids)
    return [unit for unit in task.original_evidence_units if unit.unit_id in visible_ids]


def get_visible_evidence_text(task: Pilot04Task, condition: str) -> str:
    """Return visible evidence text for one evidence condition."""
    units = get_visible_evidence_units(task, condition)
    return "\n".join(f"- {unit.unit_id}: {unit.text}" for unit in units)


def task_to_dict(task: Pilot04Task) -> dict[str, Any]:
    """Convert one Pilot 04 task into a nested dictionary."""
    record = asdict(task)
    record["original_evidence_text"] = get_original_evidence_text(task)
    return record


def tasks_to_records(tasks: list[Pilot04Task]) -> list[dict[str, Any]]:
    """
    Convert Pilot 04 tasks into flat records suitable for CSV export.

    Nested fields are stored as JSON strings so the output remains portable and sanitized.
    """
    records: list[dict[str, Any]] = []
    for task in tasks:
        record = task_to_dict(task)
        record["original_evidence_units"] = json.dumps(record["original_evidence_units"], ensure_ascii=False)
        record["required_evidence_unit_ids"] = json.dumps(record["required_evidence_unit_ids"], ensure_ascii=False)
        record["expected_primary_evidence_unit_ids"] = json.dumps(
            record["expected_primary_evidence_unit_ids"],
            ensure_ascii=False,
        )
        record["condition_payloads"] = json.dumps(record["condition_payloads"], ensure_ascii=False)
        records.append(record)
    return records


def condition_inventory_records(tasks: list[Pilot04Task]) -> list[dict[str, Any]]:
    """Return one flat row per task and evidence condition."""
    rows: list[dict[str, Any]] = []
    for task in tasks:
        for payload in task.condition_payloads:
            visible_units = get_visible_evidence_units(task, payload.condition)
            rows.append(
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "condition": payload.condition,
                    "gold_decision": task.gold_decision,
                    "visible_evidence_unit_ids": json.dumps(payload.visible_evidence_unit_ids, ensure_ascii=False),
                    "n_visible_evidence_units": len(payload.visible_evidence_unit_ids),
                    "n_required_visible": sum(
                        1
                        for unit_id in payload.visible_evidence_unit_ids
                        if unit_id in task.required_evidence_unit_ids
                    ),
                    "n_required_total": len(task.required_evidence_unit_ids),
                    "n_risk_units_visible": sum(1 for unit in visible_units if unit.direction == "risk"),
                    "n_support_units_visible": sum(1 for unit in visible_units if unit.direction == "support"),
                    "conflict_note_visible": "E8" in payload.visible_evidence_unit_ids,
                    "degraded_evidence_note": payload.degraded_evidence_note,
                    "expected_reliability_stress": payload.expected_reliability_stress,
                    "visible_evidence_text": get_visible_evidence_text(task, payload.condition),
                }
            )
    return rows


def summarise_pilot_04_tasks(tasks: list[Pilot04Task]) -> dict[str, Any]:
    """Return a deterministic summary of the generated Pilot 04 task set."""
    label_counts = Counter(task.gold_decision for task in tasks)
    condition_counts = Counter(
        payload.condition
        for task in tasks
        for payload in task.condition_payloads
    )

    return {
        "task_type": TASK_TYPE,
        "n_tasks": len(tasks),
        "n_conditions": len(DEFAULT_CONDITIONS),
        "condition_names": list(DEFAULT_CONDITIONS),
        "gold_decision_counts": dict(sorted(label_counts.items())),
        "condition_counts": dict(sorted(condition_counts.items())),
        "real_api_calls": 0,
        "raw_response_inspection": False,
    }


def export_pilot_04_tasks(
    tasks: list[Pilot04Task] | None = None,
    output_path: str | Path = "data/pilot_04_tasks.csv",
) -> Path:
    """Export Pilot 04 task inventory to CSV or JSON."""
    tasks = generate_pilot_04_tasks() if tasks is None else tasks
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = output_path.suffix.lower()
    if suffix == ".json":
        output_path.write_text(
            json.dumps([task_to_dict(task) for task in tasks], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    elif suffix == ".jsonl":
        raise ValueError("JSONL export is intentionally disabled for Pilot 04 committed task outputs.")
    else:
        records = tasks_to_records(tasks)
        fieldnames = list(records[0].keys()) if records else []
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    return output_path


def export_pilot_04_condition_inventory(
    tasks: list[Pilot04Task] | None = None,
    output_path: str | Path = "reports/pilot_04_tasks/condition_inventory.csv",
) -> Path:
    """Export one row per task-condition pair for downstream deterministic runs."""
    tasks = generate_pilot_04_tasks() if tasks is None else tasks
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = condition_inventory_records(tasks)
    fieldnames = list(records[0].keys()) if records else []
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return output_path


def validate_pilot_04_tasks(tasks: list[Pilot04Task]) -> dict[str, Any]:
    """Validate deterministic task integrity before export."""
    errors: list[str] = []

    task_ids = [task.task_id for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        errors.append("task IDs are not unique")

    for task in tasks:
        if task.task_type != TASK_TYPE:
            errors.append(f"{task.task_id}: unexpected task_type={task.task_type}")

        if task.gold_decision not in ALLOWED_GOLD_LABELS:
            errors.append(f"{task.task_id}: invalid gold_decision={task.gold_decision}")

        evidence_ids = [unit.unit_id for unit in task.original_evidence_units]
        if len(evidence_ids) != len(set(evidence_ids)):
            errors.append(f"{task.task_id}: duplicate evidence unit IDs")

        required_ids = set(task.required_evidence_unit_ids)
        evidence_id_set = set(evidence_ids)
        if not required_ids.issubset(evidence_id_set):
            errors.append(f"{task.task_id}: required evidence IDs are not all present")

        if set(task.expected_primary_evidence_unit_ids) != set(task.required_evidence_unit_ids):
            errors.append(f"{task.task_id}: expected primary evidence does not match required evidence")

        conditions = [payload.condition for payload in task.condition_payloads]
        if conditions != DEFAULT_CONDITIONS:
            errors.append(f"{task.task_id}: condition order mismatch: {conditions}")

        for payload in task.condition_payloads:
            visible_ids = set(payload.visible_evidence_unit_ids)
            if not visible_ids.issubset(evidence_id_set):
                errors.append(f"{task.task_id}/{payload.condition}: visible evidence ID not present")

            if payload.condition == CONDITION_COMPLETE and set(payload.visible_evidence_unit_ids) != set(task.required_evidence_unit_ids):
                errors.append(f"{task.task_id}/{payload.condition}: complete condition should expose required evidence")

            if payload.condition == CONDITION_PARTIAL and len(visible_ids) >= len(task.required_evidence_unit_ids):
                errors.append(f"{task.task_id}/{payload.condition}: partial condition did not remove evidence")

            if payload.condition == CONDITION_CONFLICTED and "E8" not in visible_ids:
                errors.append(f"{task.task_id}/{payload.condition}: conflicted condition missing conflict note")

    summary = summarise_pilot_04_tasks(tasks)
    summary["status"] = "PASS" if not errors else "FAIL"
    summary["n_errors"] = len(errors)
    summary["errors"] = errors
    return summary


def main() -> None:
    tasks = generate_pilot_04_tasks()
    validation = validate_pilot_04_tasks(tasks)
    print("Pilot 04 task generator validation")
    print("==================================")
    print(json.dumps(validation, indent=2, ensure_ascii=False))

    if validation["status"] != "PASS":
        raise SystemExit(1)

    output_path = export_pilot_04_tasks(tasks)
    condition_path = export_pilot_04_condition_inventory(tasks)

    print(f"Exported task inventory: {output_path}")
    print(f"Exported condition inventory: {condition_path}")
    print("real_api_calls: 0")


if __name__ == "__main__":
    main()
