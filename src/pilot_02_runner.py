"""
Pilot 02 runner for Evidence-State Reliability.

Pilot 02 tests graded evidence degradation severity.

Core research question:
As evidence degradation severity increases, do downstream failure,
undetected failure, audit false assurance, and escalation contamination increase?

This is still a simulation pilot, not a real LLM experiment.
"""

import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.degradation import (
    create_original_evidence_state,
    apply_graded_degradation,
    get_degradation_severity_levels,
)
from src.evidence_state import EvidenceUnit
from src.metrics import (
    evidence_state_reliability,
    evidence_state_degradation,
    final_failure,
    undetected_failure,
    audit_false_assurance,
    escalation_contamination,
    cost_per_governable_output,
)
from src.simulated_models import (
    simulated_decision_model_severity_sensitive,
    simulated_audit_model_severity_sensitive,
)
from src.task_generator import generate_synthetic_tasks


@dataclass
class Pilot02RunConfig:
    """
    Configuration for Pilot 02.
    """

    num_tasks: int = 50
    repeated_runs: int = 3
    seed: int = 202
    output_path: str = "data/outputs/pilot_02_results.csv"


def task_required_units_from_dict(task: dict) -> list[EvidenceUnit]:
    """
    Convert required unit dictionaries back into EvidenceUnit objects.
    """

    return [
        EvidenceUnit(
            unit_id=unit["unit_id"],
            text=unit["text"],
            importance=unit["importance"],
        )
        for unit in task["required_units"]
    ]


def estimate_pilot_02_cost() -> float:
    """
    Simple fixed cost model for Pilot 02.

    Pilot 02 uses:
    1. degraded evidence creation,
    2. one decision stage,
    3. one blind audit stage.

    We keep cost fixed so the severity effect is easier to interpret.
    """

    decision_cost = 1.0
    audit_cost = 0.5

    return decision_cost + audit_cost


def run_single_task_severity(
    task: dict,
    degradation_severity: str,
    run_id: int,
    rng: random.Random,
) -> dict:
    """
    Run one task under one degradation severity level.
    """

    required_units = task_required_units_from_dict(task)

    original_state = create_original_evidence_state(
        task_id=task["task_id"],
        original_evidence=task["original_evidence"],
        required_units=required_units,
    )

    degraded_state = apply_graded_degradation(
        state=original_state,
        required_units=required_units,
        severity=degradation_severity,
        rng=rng,
    )

    predicted_answer = simulated_decision_model_severity_sensitive(
        state=degraded_state,
        required_units=required_units,
        gold_answer=task["gold_answer"],
        rng=rng,
        strong_model=True,
    )

    audit_accepts = simulated_audit_model_severity_sensitive(
        audit_state=degraded_state,
        required_units=required_units,
        predicted_answer=predicted_answer,
        gold_answer=task["gold_answer"],
        rng=rng,
        audit_strength="basic",
    )

    accepted_by_pipeline = audit_accepts
    total_cost = estimate_pilot_02_cost()

    output_is_failure = final_failure(
        predicted_answer,
        task["gold_answer"],
    )

    governable_outputs = 1 if accepted_by_pipeline and not output_is_failure else 0

    return {
        "run_id": run_id,
        "task_id": task["task_id"],
        "degradation_severity": degradation_severity,
        "gold_answer": task["gold_answer"],
        "predicted_answer": predicted_answer,
        "accepted_by_pipeline": accepted_by_pipeline,
        "audit_accepts": audit_accepts,
        "evidence_state_reliability": evidence_state_reliability(
            degraded_state,
            required_units,
        ),
        "evidence_state_degradation": evidence_state_degradation(degraded_state),
        "final_failure": output_is_failure,
        "undetected_failure": undetected_failure(
            predicted_answer,
            task["gold_answer"],
            accepted_by_pipeline,
        ),
        "audit_false_assurance": audit_false_assurance(
            predicted_answer,
            task["gold_answer"],
            audit_accepts,
        ),
        "escalation_contamination": escalation_contamination(
            degraded_state,
            original_state,
        ),
        "cost": total_cost,
        "cost_per_governable_output": cost_per_governable_output(
            total_cost=total_cost,
            governable_outputs=governable_outputs,
        ),
    }


def run_pilot_02(config: Pilot02RunConfig) -> pd.DataFrame:
    """
    Run the full Pilot 02 simulation.
    """

    tasks = generate_synthetic_tasks(
        num_tasks=config.num_tasks,
        seed=config.seed,
    )

    severity_levels = get_degradation_severity_levels()
    rows = []

    for run_id in range(1, config.repeated_runs + 1):
        rng = random.Random(config.seed + run_id)

        for task in tasks:
            for degradation_severity in severity_levels:
                row = run_single_task_severity(
                    task=task,
                    degradation_severity=degradation_severity,
                    run_id=run_id,
                    rng=rng,
                )
                rows.append(row)

    results = pd.DataFrame(rows)

    output_path = Path(config.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)

    return results