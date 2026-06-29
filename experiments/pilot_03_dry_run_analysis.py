from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from experiments.pilot_03_dry_run_runner import (
    DEFAULT_CONDITIONS,
    Pilot03RunnerResult,
    flatten_call_records,
    run_pilot_03_dry_run_chain,
)
from src.pilot_03_parser import (
    assert_all_responses_valid,
    parse_and_validate_call_records,
    summarise_parsed_responses,
)
from src.pilot_03_tasks import Pilot03Task, generate_pilot_03_tasks, summarise_pilot_03_tasks


PILOT_03_ANALYSIS_VERSION = "pilot_03_dry_run_analysis_v1"
DEFAULT_OUTPUT_DIR = Path("results/pilot_03_dry_run_analysis")


@dataclass(frozen=True)
class Pilot03AnalysisRecord:
    """One task-condition level analysis record for Pilot 03 dry-run results."""

    task_id: str
    task_type: str
    condition: str
    gold_decision: str

    visible_evidence_unit_ids: list[str]
    missing_required_evidence_unit_ids: list[str]
    required_evidence_units_total: int
    required_evidence_units_visible: int

    evidence_state_reliability: float
    evidence_state_degradation: float
    decision_critical_distortion: bool

    decision_stage_decision: str
    audit_passed: bool
    audit_detected_issue: bool
    audit_supported_decision: str
    escalation_stage_decision: str

    decision_failure: bool
    final_failure: bool
    undetected_failure: bool
    audit_false_assurance: bool
    escalation_contamination: bool


def make_pilot_03_analysis_run_id(prefix: str = "pilot_03_dry_run_analysis") -> str:
    """Create a timestamped analysis run id."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}"


def _round_metric(value: float) -> float:
    return round(float(value), 6)


def _get_task_map(tasks: list[Pilot03Task]) -> dict[str, Pilot03Task]:
    return {task.task_id: task for task in tasks}


def _normalise_decision(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _get_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def build_analysis_record(
    result: Pilot03RunnerResult,
    task: Pilot03Task,
) -> Pilot03AnalysisRecord:
    """Build one analysis record from one dry-run runner result."""
    visible_ids = list(result.visible_evidence_unit_ids)
    visible_id_set = set(visible_ids)

    required_ids = list(task.required_evidence_unit_ids)
    missing_required_ids = [unit_id for unit_id in required_ids if unit_id not in visible_id_set]

    required_total = len(required_ids)
    required_visible = required_total - len(missing_required_ids)

    evidence_state_reliability = required_visible / required_total if required_total else 0.0
    evidence_state_degradation = 1.0 - evidence_state_reliability

    decision_stage_decision = _normalise_decision(result.decision_call.parsed_response.get("final_decision"))
    audit_passed = _get_bool(result.audit_call.parsed_response.get("audit_passed"))
    audit_detected_issue = _get_bool(result.audit_call.parsed_response.get("detected_issue"))
    audit_supported_decision = _normalise_decision(result.audit_call.parsed_response.get("supported_decision"))
    escalation_stage_decision = _normalise_decision(result.escalation_call.parsed_response.get("final_decision"))

    decision_failure = decision_stage_decision != result.gold_decision
    final_failure = escalation_stage_decision != result.gold_decision

    undetected_failure = final_failure and not audit_detected_issue
    audit_false_assurance = decision_failure and audit_passed
    escalation_contamination = final_failure and decision_failure and escalation_stage_decision == decision_stage_decision

    return Pilot03AnalysisRecord(
        task_id=result.task_id,
        task_type=result.task_type,
        condition=result.condition,
        gold_decision=result.gold_decision,
        visible_evidence_unit_ids=visible_ids,
        missing_required_evidence_unit_ids=missing_required_ids,
        required_evidence_units_total=required_total,
        required_evidence_units_visible=required_visible,
        evidence_state_reliability=_round_metric(evidence_state_reliability),
        evidence_state_degradation=_round_metric(evidence_state_degradation),
        decision_critical_distortion=bool(missing_required_ids),
        decision_stage_decision=decision_stage_decision,
        audit_passed=audit_passed,
        audit_detected_issue=audit_detected_issue,
        audit_supported_decision=audit_supported_decision,
        escalation_stage_decision=escalation_stage_decision,
        decision_failure=decision_failure,
        final_failure=final_failure,
        undetected_failure=undetected_failure,
        audit_false_assurance=audit_false_assurance,
        escalation_contamination=escalation_contamination,
    )


def run_pilot_03_dry_run_analysis(
    n_tasks: int = 50,
    conditions: list[str] | None = None,
) -> tuple[list[Pilot03Task], list[Pilot03RunnerResult], list[Pilot03AnalysisRecord]]:
    """Run Pilot 03 dry-run chains and convert them into analysis records."""
    conditions = DEFAULT_CONDITIONS if conditions is None else conditions
    tasks = generate_pilot_03_tasks(n_tasks=n_tasks)
    task_map = _get_task_map(tasks)

    results: list[Pilot03RunnerResult] = []
    for task in tasks:
        for condition in conditions:
            results.append(run_pilot_03_dry_run_chain(task=task, condition=condition))

    call_records = flatten_call_records(results)
    parsed_responses = parse_and_validate_call_records(call_records)
    assert_all_responses_valid(parsed_responses)

    analysis_records = [
        build_analysis_record(result=result, task=task_map[result.task_id])
        for result in results
    ]

    return tasks, results, analysis_records


def analysis_records_to_dataframe(records: list[Pilot03AnalysisRecord]) -> pd.DataFrame:
    """Convert analysis records to a pandas DataFrame."""
    rows = []
    for record in records:
        row = asdict(record)
        row["visible_evidence_unit_ids"] = json.dumps(row["visible_evidence_unit_ids"], ensure_ascii=False)
        row["missing_required_evidence_unit_ids"] = json.dumps(
            row["missing_required_evidence_unit_ids"],
            ensure_ascii=False,
        )
        rows.append(row)

    return pd.DataFrame(rows)


def summarise_analysis_records(records: list[Pilot03AnalysisRecord]) -> dict[str, Any]:
    """Return a compact analysis summary."""
    if not records:
        return {
            "analysis_version": PILOT_03_ANALYSIS_VERSION,
            "n_analysis_records": 0,
        }

    df = analysis_records_to_dataframe(records)

    metric_columns = [
        "evidence_state_reliability",
        "evidence_state_degradation",
        "decision_critical_distortion",
        "decision_failure",
        "final_failure",
        "undetected_failure",
        "audit_false_assurance",
        "escalation_contamination",
        "audit_passed",
        "audit_detected_issue",
    ]

    condition_summary: dict[str, dict[str, float]] = {}
    for condition, condition_df in df.groupby("condition", sort=True):
        condition_summary[str(condition)] = {
            "n": int(len(condition_df)),
            **{
                f"{metric}_mean": _round_metric(condition_df[metric].astype(float).mean())
                for metric in metric_columns
            },
        }

    return {
        "analysis_version": PILOT_03_ANALYSIS_VERSION,
        "n_analysis_records": len(records),
        "condition_counts": dict(Counter(record.condition for record in records)),
        "gold_decisions": dict(Counter(record.gold_decision for record in records)),
        "condition_summary": condition_summary,
    }


def build_condition_summary_dataframe(records: list[Pilot03AnalysisRecord]) -> pd.DataFrame:
    """Build a flat condition-level summary DataFrame."""
    summary = summarise_analysis_records(records)
    rows = []

    for condition, values in summary.get("condition_summary", {}).items():
        row = {"condition": condition}
        row.update(values)
        rows.append(row)

    return pd.DataFrame(rows)


def write_pilot_03_analysis_outputs(
    records: list[Pilot03AnalysisRecord],
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    run_id: str | None = None,
    extra_summary: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Write Pilot 03 dry-run analysis outputs to disk."""
    run_id = make_pilot_03_analysis_run_id() if run_id is None else run_id
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    records_df = analysis_records_to_dataframe(records)
    condition_summary_df = build_condition_summary_dataframe(records)
    summary = summarise_analysis_records(records)
    summary["run_id"] = run_id
    summary["output_dir"] = str(run_dir)

    if extra_summary is not None:
        summary["extra_summary"] = extra_summary

    analysis_records_csv = run_dir / "analysis_records.csv"
    condition_summary_csv = run_dir / "condition_summary.csv"
    summary_json = run_dir / "analysis_summary.json"

    records_df.to_csv(analysis_records_csv, index=False)
    condition_summary_df.to_csv(condition_summary_csv, index=False)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    return {
        "run_dir": run_dir,
        "analysis_records_csv": analysis_records_csv,
        "condition_summary_csv": condition_summary_csv,
        "analysis_summary_json": summary_json,
    }


def main() -> None:
    """Run Pilot 03 dry-run analysis."""
    n_tasks = 50

    tasks, results, analysis_records = run_pilot_03_dry_run_analysis(n_tasks=n_tasks)
    call_records = flatten_call_records(results)
    parsed_responses = parse_and_validate_call_records(call_records)

    task_summary = summarise_pilot_03_tasks(tasks)
    parser_summary = summarise_parsed_responses(parsed_responses)
    analysis_summary = summarise_analysis_records(analysis_records)

    paths = write_pilot_03_analysis_outputs(
        records=analysis_records,
        run_id="pilot_03_dry_run_analysis_latest",
        extra_summary={
            "task_summary": task_summary,
            "parser_summary": parser_summary,
        },
    )

    print("Pilot 03 dry-run analysis")
    print("=========================")
    print("No real LLM calls are made in this analysis.")
    print("Task summary:")
    print(task_summary)
    print()
    print("Parser summary:")
    print(parser_summary)
    print()
    print("Analysis summary:")
    print(analysis_summary)
    print()
    print("Output files:")
    for key, path in paths.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()