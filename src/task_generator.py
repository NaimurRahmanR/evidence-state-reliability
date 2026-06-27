"""
Synthetic task generator for the Evidence-State Reliability project.

This creates small controlled tasks where we know:
1. the original evidence,
2. the required evidence units,
3. the correct final answer.

This is simulation-first. No real LLM calls yet.
"""

from dataclasses import asdict
import json
import random
from pathlib import Path

from src.evidence_state import EvidenceUnit


def generate_synthetic_tasks(
    num_tasks: int = 50,
    seed: int = 42,
) -> list[dict]:
    """
    Generate synthetic evidence-based decision tasks.

    Each task has 3 required evidence units:
    - entity
    - condition/status
    - decision rule

    The gold answer is deterministic based on those units.
    """

    random.seed(seed)

    entities = [
        "Case Alpha",
        "Case Beta",
        "Case Gamma",
        "Case Delta",
        "Case Epsilon",
    ]

    statuses = [
        ("submitted all required documents", "eligible"),
        ("missed one required document", "not eligible"),
        ("submitted documents after the deadline", "not eligible"),
        ("submitted all required documents before the deadline", "eligible"),
        ("has conflicting identity information", "not eligible"),
    ]

    rules = [
        "A case is eligible only if all required documents are submitted before the deadline.",
        "A case is not eligible if any required document is missing.",
        "A case is not eligible if submitted after the deadline.",
        "A case requires escalation if identity information conflicts.",
    ]

    tasks = []

    for i in range(1, num_tasks + 1):
        task_id = f"T{i:03d}"

        entity = random.choice(entities)
        status_text, gold_answer = random.choice(statuses)
        rule = random.choice(rules)

        required_units = [
            EvidenceUnit(
                unit_id="F001",
                text=f"The case is {entity}.",
                importance=1.0,
            ),
            EvidenceUnit(
                unit_id="F002",
                text=f"{entity} {status_text}.",
                importance=1.0,
            ),
            EvidenceUnit(
                unit_id="F003",
                text=rule,
                importance=1.0,
            ),
        ]

        original_evidence = " ".join(unit.text for unit in required_units)

        question = f"Based on the evidence, is {entity} eligible?"

        task = {
            "task_id": task_id,
            "question": question,
            "original_evidence": original_evidence,
            "required_units": [asdict(unit) for unit in required_units],
            "gold_answer": gold_answer,
        }

        tasks.append(task)

    return tasks


def save_tasks_to_json(
    tasks: list[dict],
    output_path: str | Path,
) -> None:
    """
    Save synthetic tasks to a JSON file.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=2)


def load_tasks_from_json(input_path: str | Path) -> list[dict]:
    """
    Load synthetic tasks from a JSON file.
    """

    input_path = Path(input_path)

    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)