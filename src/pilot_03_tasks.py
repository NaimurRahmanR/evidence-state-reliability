from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from random import Random
from typing import Any


TASK_TYPE = "synthetic_administrative_approval"
DEFAULT_TASK_COUNT = 50
DEFAULT_SEED = 303


@dataclass(frozen=True)
class Pilot03EvidenceUnit:
    """One atomic evidence item available to the downstream decision component."""

    unit_id: str
    text: str
    criterion: str
    value: bool | str
    required: bool = True


@dataclass(frozen=True)
class Pilot03Task:
    """A controlled, automatically judgeable Pilot 03 task."""

    task_id: str
    task_type: str
    question: str
    gold_decision: str
    gold_answer: str
    gold_reason: str
    decision_rule: str
    original_evidence_units: list[Pilot03EvidenceUnit]
    required_evidence_unit_ids: list[str]


def _make_bool_text(label: str, passed: bool, task_number: int) -> str:
    """Create controlled but slightly varied synthetic evidence text."""
    income_threshold = 2400 + ((task_number % 5) * 100)
    income_above = income_threshold + 350 + ((task_number % 3) * 50)
    income_below = income_threshold - 200 - ((task_number % 4) * 50)

    positive_negative = {
        "income_threshold_met": (
            f"Applicant income is £{income_above} per month, which is above the £{income_threshold} required threshold.",
            f"Applicant income is £{income_below} per month, which is below the £{income_threshold} required threshold.",
        ),
        "identity_documents_submitted": (
            "Applicant has submitted the required identity documents.",
            "Applicant has not submitted the required identity documents.",
        ),
        "address_verification_completed": (
            "Applicant has completed address verification.",
            "Applicant has not completed address verification.",
        ),
        "compliance_training_completed": (
            "Applicant has completed compliance training.",
            "Applicant has not completed compliance training.",
        ),
        "no_unresolved_compliance_case": (
            "Applicant has no unresolved compliance case.",
            "Applicant has an unresolved compliance case.",
        ),
    }
    passed_text, failed_text = positive_negative[label]
    return passed_text if passed else failed_text


def _make_gold_reason(failed_criteria: list[str]) -> str:
    if not failed_criteria:
        return "Approve because all required administrative criteria are satisfied."

    readable = [criterion.replace("_", " ") for criterion in failed_criteria]
    return "Reject because the following required criteria are not satisfied: " + ", ".join(readable) + "."


def _build_task(task_number: int, pattern: dict[str, bool]) -> Pilot03Task:
    task_id = f"P03-T{task_number:04d}"
    applicant_id = f"APP-{1000 + task_number}"

    decision_rule = (
        "Approve the applicant only if all required criteria are satisfied: "
        "income threshold met, identity documents submitted, address verification completed, "
        "compliance training completed, and no unresolved compliance case. "
        "If any required criterion is not satisfied, reject the applicant."
    )

    criteria_order = [
        "income_threshold_met",
        "identity_documents_submitted",
        "address_verification_completed",
        "compliance_training_completed",
        "no_unresolved_compliance_case",
    ]

    evidence_units: list[Pilot03EvidenceUnit] = []
    for index, criterion in enumerate(criteria_order, start=1):
        evidence_units.append(
            Pilot03EvidenceUnit(
                unit_id=f"E{index}",
                text=_make_bool_text(criterion, pattern[criterion], task_number),
                criterion=criterion,
                value=pattern[criterion],
                required=True,
            )
        )

    evidence_units.append(
        Pilot03EvidenceUnit(
            unit_id="E6",
            text="Policy rule says all listed criteria are required for approval.",
            criterion="policy_rule_all_criteria_required",
            value="all_required",
            required=True,
        )
    )

    failed_criteria = [criterion for criterion in criteria_order if not pattern[criterion]]
    gold_decision = "approve" if not failed_criteria else "reject"
    gold_reason = _make_gold_reason(failed_criteria)

    return Pilot03Task(
        task_id=task_id,
        task_type=TASK_TYPE,
        question=f"Should applicant {applicant_id} be approved or rejected?",
        gold_decision=gold_decision,
        gold_answer=gold_decision,
        gold_reason=gold_reason,
        decision_rule=decision_rule,
        original_evidence_units=evidence_units,
        required_evidence_unit_ids=[unit.unit_id for unit in evidence_units if unit.required],
    )


def generate_pilot_03_tasks(n_tasks: int = DEFAULT_TASK_COUNT, seed: int = DEFAULT_SEED) -> list[Pilot03Task]:
    """
    Generate controlled synthetic administrative approval tasks for Pilot 03.

    The tasks are deterministic by default. They are synthetic, low-risk,
    automatically judgeable, and balanced between approve/reject decisions.
    Approval requires all criteria to pass.
    """
    if n_tasks <= 0:
        raise ValueError("n_tasks must be a positive integer.")

    criteria_order = [
        "income_threshold_met",
        "identity_documents_submitted",
        "address_verification_completed",
        "compliance_training_completed",
        "no_unresolved_compliance_case",
    ]

    approve_pattern = [True, True, True, True, True]

    reject_patterns = [
        [False, True, True, True, True],
        [True, False, True, True, True],
        [True, True, False, True, True],
        [True, True, True, False, True],
        [True, True, True, True, False],
        [False, False, True, True, True],
        [True, False, False, True, True],
        [True, True, False, False, True],
        [True, True, True, False, False],
        [False, True, True, True, False],
        [False, True, False, True, False],
        [True, False, True, False, True],
        [False, False, False, True, True],
        [True, True, False, False, False],
        [False, False, True, False, False],
    ]

    rng = Random(seed)
    reject_patterns = list(reject_patterns)
    rng.shuffle(reject_patterns)

    tasks: list[Pilot03Task] = []
    reject_index = 0

    for index in range(n_tasks):
        task_number = index + 1

        if index % 2 == 0:
            raw_pattern = approve_pattern
        else:
            raw_pattern = reject_patterns[reject_index % len(reject_patterns)]
            reject_index += 1

        pattern = dict(zip(criteria_order, raw_pattern, strict=True))
        tasks.append(_build_task(task_number=task_number, pattern=pattern))

    return tasks


def get_original_evidence_text(task: Pilot03Task) -> str:
    """Return the original evidence as a plain-text block for prompt construction."""
    evidence_lines = [f"- {unit.unit_id}: {unit.text}" for unit in task.original_evidence_units]
    return "\n".join(evidence_lines)


def task_to_dict(task: Pilot03Task) -> dict[str, Any]:
    """Convert one Pilot 03 task into a nested dictionary."""
    record = asdict(task)
    record["original_evidence_text"] = get_original_evidence_text(task)
    return record


def tasks_to_records(tasks: list[Pilot03Task]) -> list[dict[str, Any]]:
    """
    Convert Pilot 03 tasks into flat records suitable for CSV export.

    Nested evidence fields are stored as JSON strings so the output remains portable.
    """
    records: list[dict[str, Any]] = []
    for task in tasks:
        record = task_to_dict(task)
        record["original_evidence_units"] = json.dumps(record["original_evidence_units"], ensure_ascii=False)
        record["required_evidence_unit_ids"] = json.dumps(record["required_evidence_unit_ids"], ensure_ascii=False)
        records.append(record)
    return records


def export_pilot_03_tasks(
    tasks: list[Pilot03Task] | None = None,
    output_path: str | Path = "data/pilot_03_tasks.csv",
) -> Path:
    """
    Export Pilot 03 tasks to CSV, JSON, or JSONL.

    The default is CSV because it is easy to inspect manually during dry-run work.
    """
    tasks = generate_pilot_03_tasks() if tasks is None else tasks
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = output_path.suffix.lower()
    if suffix == ".json":
        output_path.write_text(
            json.dumps([task_to_dict(task) for task in tasks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    elif suffix == ".jsonl":
        with output_path.open("w", encoding="utf-8") as handle:
            for task in tasks:
                handle.write(json.dumps(task_to_dict(task), ensure_ascii=False) + "\n")
    else:
        records = tasks_to_records(tasks)
        fieldnames = list(records[0].keys()) if records else []
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    return output_path


def summarise_pilot_03_tasks(tasks: list[Pilot03Task]) -> dict[str, Any]:
    """Return a compact summary of the generated Pilot 03 task set."""
    if not tasks:
        return {
            "n_tasks": 0,
            "task_types": {},
            "gold_decisions": {},
            "evidence_units_per_task_min": 0,
            "evidence_units_per_task_max": 0,
            "required_units_per_task_min": 0,
            "required_units_per_task_max": 0,
            "approve_rate": 0.0,
        }

    evidence_counts = [len(task.original_evidence_units) for task in tasks]
    required_counts = [len(task.required_evidence_unit_ids) for task in tasks]
    decision_counts = Counter(task.gold_decision for task in tasks)

    return {
        "n_tasks": len(tasks),
        "task_types": dict(Counter(task.task_type for task in tasks)),
        "gold_decisions": dict(decision_counts),
        "evidence_units_per_task_min": min(evidence_counts),
        "evidence_units_per_task_max": max(evidence_counts),
        "required_units_per_task_min": min(required_counts),
        "required_units_per_task_max": max(required_counts),
        "approve_rate": round(decision_counts.get("approve", 0) / len(tasks), 3),
    }


if __name__ == "__main__":
    generated_tasks = generate_pilot_03_tasks()
    output_file = export_pilot_03_tasks(generated_tasks)
    print(f"Exported {len(generated_tasks)} Pilot 03 tasks to {output_file}")
    print(summarise_pilot_03_tasks(generated_tasks))