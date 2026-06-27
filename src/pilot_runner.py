"""
First pilot runner for Evidence-State Reliability.

This connects:
1. synthetic tasks,
2. evidence-state degradation,
3. pilot pipeline conditions,
4. simulated decision/audit models,
5. reliability metrics,
6. CSV output.

This is still a simulation pilot, not a real LLM experiment.
"""

import random
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd

from src.evidence_state import EvidenceUnit, EvidenceState
from src.task_generator import generate_synthetic_tasks
from src.degradation import (
    create_original_evidence_state,
    apply_fact_loss,
    apply_fact_mutation,
    apply_contradiction,
    apply_uncertainty_removal,
    apply_unsupported_addition,
)
from src.pipeline_conditions import PipelineCondition, get_pilot_conditions
from src.simulated_models import simulated_decision_model, simulated_audit_model
from src.metrics import (
    evidence_state_reliability,
    evidence_state_degradation,
    final_failure,
    undetected_failure,
    audit_false_assurance,
    escalation_contamination,
    cost_per_governable_output,
)


@dataclass
class PilotRunConfig:
    """
    Configuration for the first pilot run.
    """

    num_tasks: int = 50
    repeated_runs: int = 3
    seed: int = 42
    output_path: str = "data/outputs/pilot_results.csv"


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


def create_summary_state_for_condition(
    original_state: EvidenceState,
    required_units: list[EvidenceUnit],
    condition_name: str,
    rng: random.Random,
) -> EvidenceState:
    """
    Create a transformed evidence state depending on the pipeline condition.

    Pilot design:
        direct_answer and evidence_preserving keep evidence mostly intact.
        summary_only and blind_audit apply stronger degradation.
        visible_audit still has degraded decision evidence, but audit sees original.
    """

    if condition_name == "direct_answer":
        return original_state

    if condition_name == "evidence_preserving":
        return apply_fact_loss(
            state=original_state,
            required_units=required_units,
            loss_probability=0.05,
            rng=rng,
            new_stage_name="summary_evidence_preserving",
        )

    if condition_name == "summary_only":
        state = apply_fact_loss(
            state=original_state,
            required_units=required_units,
            loss_probability=0.35,
            rng=rng,
            new_stage_name="summary_only_loss",
        )
        state = apply_fact_mutation(
            state=state,
            required_units=required_units,
            mutation_probability=0.20,
            rng=rng,
            new_stage_name="summary_only_mutation",
        )
        return state

    if condition_name == "visible_audit":
        state = apply_fact_loss(
            state=original_state,
            required_units=required_units,
            loss_probability=0.30,
            rng=rng,
            new_stage_name="visible_audit_summary_loss",
        )
        return state

    if condition_name == "blind_audit":
        state = apply_fact_loss(
            state=original_state,
            required_units=required_units,
            loss_probability=0.30,
            rng=rng,
            new_stage_name="blind_audit_summary_loss",
        )
        state = apply_unsupported_addition(state)
        return state

    raise ValueError(f"Unknown condition name: {condition_name}")


def run_single_task_condition(
    task: dict,
    condition: PipelineCondition,
    run_id: int,
    rng: random.Random,
) -> dict:
    """
    Run one task under one pipeline condition.
    """

    required_units = task_required_units_from_dict(task)

    original_state = create_original_evidence_state(
        task_id=task["task_id"],
        original_evidence=task["original_evidence"],
        required_units=required_units,
    )

    decision_state = create_summary_state_for_condition(
        original_state=original_state,
        required_units=required_units,
        condition_name=condition.name,
        rng=rng,
    )

    if condition.uses_original_evidence:
        model_input_state = original_state
    else:
        model_input_state = decision_state

    predicted_answer = simulated_decision_model(
        state=model_input_state,
        required_units=required_units,
        gold_answer=task["gold_answer"],
        rng=rng,
        strong_model=True,
    )

    if condition.has_audit_stage:
        if condition.audit_sees_original_evidence:
            audit_state = original_state
        else:
            audit_state = decision_state

        audit_accepts = simulated_audit_model(
            audit_state=audit_state,
            required_units=required_units,
            predicted_answer=predicted_answer,
            gold_answer=task["gold_answer"],
            rng=rng,
            audit_strength="basic",
        )
    else:
        audit_state = model_input_state
        audit_accepts = True

    accepted_by_pipeline = audit_accepts

    if condition.has_escalation_stage:
        if condition.escalation_sees_original_evidence:
            escalation_state = original_state
        else:
            escalation_state = decision_state
    else:
        escalation_state = model_input_state

    total_cost = estimate_condition_cost(condition)
    governable_outputs = 1 if accepted_by_pipeline and not final_failure(predicted_answer, task["gold_answer"]) else 0

    return {
        "run_id": run_id,
        "task_id": task["task_id"],
        "condition": condition.name,
        "gold_answer": task["gold_answer"],
        "predicted_answer": predicted_answer,
        "accepted_by_pipeline": accepted_by_pipeline,
        "audit_accepts": audit_accepts,
        "evidence_state_reliability": evidence_state_reliability(model_input_state, required_units),
        "evidence_state_degradation": evidence_state_degradation(model_input_state),
        "final_failure": final_failure(predicted_answer, task["gold_answer"]),
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
            escalation_state,
            original_state,
        ),
        "cost": total_cost,
        "cost_per_governable_output": cost_per_governable_output(
            total_cost=total_cost,
            governable_outputs=governable_outputs,
        ),
    }


def estimate_condition_cost(condition: PipelineCondition) -> float:
    """
    Simple pilot cost model.

    Base decision cost = 1.0
    Audit stage adds 0.5
    Escalation stage adds 1.0
    Keeping original evidence available adds 0.2
    """

    cost = 1.0

    if condition.has_audit_stage:
        cost += 0.5

    if condition.has_escalation_stage:
        cost += 1.0

    if condition.uses_original_evidence:
        cost += 0.2

    return cost


def run_pilot(config: PilotRunConfig) -> pd.DataFrame:
    """
    Run the full simulation pilot.
    """

    tasks = generate_synthetic_tasks(
        num_tasks=config.num_tasks,
        seed=config.seed,
    )

    conditions = get_pilot_conditions()
    rows = []

    for run_id in range(1, config.repeated_runs + 1):
        rng = random.Random(config.seed + run_id)

        for task in tasks:
            for condition in conditions:
                row = run_single_task_condition(
                    task=task,
                    condition=condition,
                    run_id=run_id,
                    rng=rng,
                )
                rows.append(row)

    results = pd.DataFrame(rows)

    output_path = Path(config.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)

    return results