from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


DRY_RUN_CHAIN_CSV = Path("reports/pilot_04_dry_run/chain_outputs.csv")
DECISION_OUTPUTS_CSV = Path("reports/pilot_04_dry_run/decision_outputs.csv")
AUDIT_OUTPUTS_CSV = Path("reports/pilot_04_dry_run/audit_outputs.csv")
ESCALATION_OUTPUTS_CSV = Path("reports/pilot_04_dry_run/escalation_outputs.csv")

STAGE_CASCADE_DIR = Path("reports/pilot_04_stage_cascade")
UNCERTAINTY_DIR = Path("reports/pilot_04_uncertainty")
RELIABILITY_CASCADE_DIR = Path("reports/pilot_04_reliability_cascade_metrics")
ROBUSTNESS_DIR = Path("reports/pilot_04_robustness_sensitivity")

CONDITIONS = ["complete", "partial", "conflicted"]
BASELINE_CONDITION = "complete"
DEGRADED_CONDITIONS = ["partial", "conflicted"]


@dataclass(frozen=True)
class OutputSpec:
    path: Path
    rows: list[dict[str, Any]]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _as_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"Expected serialized boolean True/False, got {value!r}")


def _as_int(value: str) -> int:
    return int(value)


def _as_float(value: str) -> float:
    return float(value)


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(mean(values), 6)


def _condition_order(condition: str) -> int:
    return CONDITIONS.index(condition)


def _group_by_condition(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {condition: [] for condition in CONDITIONS}
    for row in rows:
        grouped[row["condition"]].append(row)
    return grouped


def _chain_key(row: dict[str, str]) -> tuple[str, str]:
    return (row["task_id"], row["condition"])


def _load_chain_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {_chain_key(row): row for row in rows}


def _stage_cascade_outputs(chain_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = _group_by_condition(chain_rows)

    condition_rows: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []

    for condition in CONDITIONS:
        rows = grouped[condition]
        n = len(rows)

        decision_match_count = sum(1 for row in rows if _as_bool(row["decision_matches_gold"]))
        audit_pass_count = sum(1 for row in rows if _as_bool(row["audit_pass"]))
        escalation_count = sum(1 for row in rows if _as_bool(row["requires_human_review"]))
        schema_valid_count = sum(1 for row in rows if _as_bool(row["all_stage_schemas_valid"]))
        missing_ack_count = sum(1 for row in rows if _as_bool(row["missing_evidence_acknowledged"]))

        condition_rows.append(
            {
                "condition": condition,
                "n_chains": n,
                "schema_valid_rate": _safe_rate(schema_valid_count, n),
                "decision_match_rate": _safe_rate(decision_match_count, n),
                "audit_pass_rate": _safe_rate(audit_pass_count, n),
                "escalation_rate": _safe_rate(escalation_count, n),
                "missing_evidence_acknowledgement_rate": _safe_rate(missing_ack_count, n),
                "mean_decision_confidence": _mean([_as_float(row["decision_confidence"]) for row in rows]),
                "mean_evidence_alignment_score": _mean([_as_float(row["evidence_alignment_score"]) for row in rows]),
                "mean_escalation_confidence": _mean([_as_float(row["escalation_confidence"]) for row in rows]),
                "mean_missing_required_evidence_units": _mean(
                    [_as_float(row["n_missing_required_evidence_units"]) for row in rows]
                ),
                "real_api_calls": 0,
            }
        )

        transition_rows.append(
            {
                "condition": condition,
                "transition": "decision_to_audit",
                "n_chains": n,
                "source_positive_rate": _safe_rate(decision_match_count, n),
                "target_positive_rate": _safe_rate(audit_pass_count, n),
                "cascade_drop": round(_safe_rate(decision_match_count, n) - _safe_rate(audit_pass_count, n), 6),
                "real_api_calls": 0,
            }
        )
        transition_rows.append(
            {
                "condition": condition,
                "transition": "audit_to_escalation",
                "n_chains": n,
                "source_positive_rate": _safe_rate(audit_pass_count, n),
                "target_positive_rate": _safe_rate(escalation_count, n),
                "cascade_drop": round(_safe_rate(audit_pass_count, n) - _safe_rate(escalation_count, n), 6),
                "real_api_calls": 0,
            }
        )
        transition_rows.append(
            {
                "condition": condition,
                "transition": "decision_to_escalation",
                "n_chains": n,
                "source_positive_rate": _safe_rate(decision_match_count, n),
                "target_positive_rate": _safe_rate(escalation_count, n),
                "cascade_drop": round(_safe_rate(decision_match_count, n) - _safe_rate(escalation_count, n), 6),
                "real_api_calls": 0,
            }
        )

    paired_rows: list[dict[str, Any]] = []
    by_task: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in chain_rows:
        by_task[row["task_id"]][row["condition"]] = row

    for task_id in sorted(by_task):
        if BASELINE_CONDITION not in by_task[task_id]:
            continue

        baseline = by_task[task_id][BASELINE_CONDITION]
        for condition in DEGRADED_CONDITIONS:
            if condition not in by_task[task_id]:
                continue

            degraded = by_task[task_id][condition]

            paired_rows.append(
                {
                    "task_id": task_id,
                    "baseline_condition": BASELINE_CONDITION,
                    "degraded_condition": condition,
                    "gold_decision": baseline["gold_decision"],
                    "baseline_decision_label": baseline["decision_label"],
                    "degraded_decision_label": degraded["decision_label"],
                    "decision_changed": baseline["decision_label"] != degraded["decision_label"],
                    "decision_match_delta": int(_as_bool(degraded["decision_matches_gold"]))
                    - int(_as_bool(baseline["decision_matches_gold"])),
                    "audit_pass_delta": int(_as_bool(degraded["audit_pass"])) - int(_as_bool(baseline["audit_pass"])),
                    "escalation_delta": int(_as_bool(degraded["requires_human_review"]))
                    - int(_as_bool(baseline["requires_human_review"])),
                    "alignment_score_delta": round(
                        _as_float(degraded["evidence_alignment_score"])
                        - _as_float(baseline["evidence_alignment_score"]),
                        6,
                    ),
                    "decision_confidence_delta": round(
                        _as_float(degraded["decision_confidence"]) - _as_float(baseline["decision_confidence"]),
                        6,
                    ),
                    "missing_required_evidence_delta": _as_int(degraded["n_missing_required_evidence_units"])
                    - _as_int(baseline["n_missing_required_evidence_units"]),
                    "real_api_calls": 0,
                }
            )

    return condition_rows, transition_rows, paired_rows


def _uncertainty_outputs(chain_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = _group_by_condition(chain_rows)

    condition_rows: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        rows = grouped[condition]
        n = len(rows)
        confidences = [_as_float(row["decision_confidence"]) for row in rows]
        alignment_scores = [_as_float(row["evidence_alignment_score"]) for row in rows]
        escalation_confidences = [_as_float(row["escalation_confidence"]) for row in rows]

        low_decision_confidence = sum(1 for value in confidences if value < 0.70)
        low_alignment = sum(1 for value in alignment_scores if value < 0.75)
        high_review_need = sum(1 for row in rows if _as_bool(row["requires_human_review"]))

        condition_rows.append(
            {
                "condition": condition,
                "n_chains": n,
                "mean_decision_confidence": _mean(confidences),
                "min_decision_confidence": round(min(confidences), 6) if confidences else 0.0,
                "max_decision_confidence": round(max(confidences), 6) if confidences else 0.0,
                "low_decision_confidence_rate_lt_0_70": _safe_rate(low_decision_confidence, n),
                "mean_evidence_alignment_score": _mean(alignment_scores),
                "low_alignment_rate_lt_0_75": _safe_rate(low_alignment, n),
                "mean_escalation_confidence": _mean(escalation_confidences),
                "human_review_rate": _safe_rate(high_review_need, n),
                "real_api_calls": 0,
            }
        )

    task_rows: list[dict[str, Any]] = []
    by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in chain_rows:
        by_task[row["task_id"]].append(row)

    for task_id in sorted(by_task):
        rows = sorted(by_task[task_id], key=lambda row: _condition_order(row["condition"]))
        confidences = [_as_float(row["decision_confidence"]) for row in rows]
        alignments = [_as_float(row["evidence_alignment_score"]) for row in rows]
        human_review_conditions = [row["condition"] for row in rows if _as_bool(row["requires_human_review"])]

        task_rows.append(
            {
                "task_id": task_id,
                "gold_decision": rows[0]["gold_decision"],
                "n_conditions": len(rows),
                "decision_confidence_range": round(max(confidences) - min(confidences), 6),
                "alignment_score_range": round(max(alignments) - min(alignments), 6),
                "n_human_review_conditions": len(human_review_conditions),
                "human_review_conditions": json.dumps(human_review_conditions, ensure_ascii=False),
                "any_decision_shift": len({row["decision_label"] for row in rows}) > 1,
                "real_api_calls": 0,
            }
        )

    return condition_rows, task_rows


def _reliability_cascade_outputs(
    chain_rows: list[dict[str, str]],
    paired_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = _group_by_condition(chain_rows)

    condition_metric_rows: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        rows = grouped[condition]
        n = len(rows)

        structural_validity_rate = _safe_rate(sum(1 for row in rows if _as_bool(row["all_stage_schemas_valid"])), n)
        decision_reliability_rate = _safe_rate(sum(1 for row in rows if _as_bool(row["decision_matches_gold"])), n)
        audit_pass_rate = _safe_rate(sum(1 for row in rows if _as_bool(row["audit_pass"])), n)
        escalation_rate = _safe_rate(sum(1 for row in rows if _as_bool(row["requires_human_review"])), n)
        missing_ack_rate = _safe_rate(sum(1 for row in rows if _as_bool(row["missing_evidence_acknowledged"])), n)
        alignment_mean = _mean([_as_float(row["evidence_alignment_score"]) for row in rows])

        reliability_cascade_index = round(
            (decision_reliability_rate + audit_pass_rate + alignment_mean + (1 - escalation_rate)) / 4,
            6,
        )
        structural_validity_gap = round(structural_validity_rate - reliability_cascade_index, 6)

        condition_metric_rows.append(
            {
                "condition": condition,
                "n_chains": n,
                "structural_validity_rate": structural_validity_rate,
                "decision_reliability_rate": decision_reliability_rate,
                "audit_pass_rate": audit_pass_rate,
                "escalation_rate": escalation_rate,
                "missing_evidence_acknowledgement_rate": missing_ack_rate,
                "mean_evidence_alignment_score": alignment_mean,
                "reliability_cascade_index": reliability_cascade_index,
                "structural_validity_gap": structural_validity_gap,
                "real_api_calls": 0,
            }
        )

    baseline = next(row for row in condition_metric_rows if row["condition"] == BASELINE_CONDITION)
    delta_rows: list[dict[str, Any]] = []

    for row in condition_metric_rows:
        if row["condition"] == BASELINE_CONDITION:
            continue

        delta_rows.append(
            {
                "baseline_condition": BASELINE_CONDITION,
                "degraded_condition": row["condition"],
                "decision_reliability_delta": round(
                    row["decision_reliability_rate"] - baseline["decision_reliability_rate"],
                    6,
                ),
                "audit_pass_delta": round(row["audit_pass_rate"] - baseline["audit_pass_rate"], 6),
                "escalation_rate_delta": round(row["escalation_rate"] - baseline["escalation_rate"], 6),
                "alignment_score_delta": round(
                    row["mean_evidence_alignment_score"] - baseline["mean_evidence_alignment_score"],
                    6,
                ),
                "reliability_cascade_index_delta": round(
                    row["reliability_cascade_index"] - baseline["reliability_cascade_index"],
                    6,
                ),
                "structural_validity_gap_delta": round(
                    row["structural_validity_gap"] - baseline["structural_validity_gap"],
                    6,
                ),
                "real_api_calls": 0,
            }
        )

    paired_metric_rows: list[dict[str, Any]] = []
    by_condition = defaultdict(list)
    for row in paired_rows:
        by_condition[row["degraded_condition"]].append(row)

    for condition in DEGRADED_CONDITIONS:
        rows = by_condition[condition]
        n = len(rows)

        paired_metric_rows.append(
            {
                "baseline_condition": BASELINE_CONDITION,
                "degraded_condition": condition,
                "n_paired_tasks": n,
                "decision_shift_rate": _safe_rate(sum(1 for row in rows if row["decision_changed"] is True), n),
                "mean_decision_match_delta": _mean([float(row["decision_match_delta"]) for row in rows]),
                "mean_audit_pass_delta": _mean([float(row["audit_pass_delta"]) for row in rows]),
                "mean_escalation_delta": _mean([float(row["escalation_delta"]) for row in rows]),
                "mean_alignment_score_delta": _mean([float(row["alignment_score_delta"]) for row in rows]),
                "mean_decision_confidence_delta": _mean([float(row["decision_confidence_delta"]) for row in rows]),
                "real_api_calls": 0,
            }
        )

    return condition_metric_rows, delta_rows, paired_metric_rows


def _robustness_outputs(
    chain_rows: list[dict[str, str]],
    condition_metric_rows: list[dict[str, Any]],
    paired_metric_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in chain_rows:
        by_task[row["task_id"]].append(row)

    leave_one_task_out_rows: list[dict[str, Any]] = []
    for omitted_task_id in sorted(by_task):
        kept_rows = [row for row in chain_rows if row["task_id"] != omitted_task_id]
        metrics, _, _ = _reliability_cascade_outputs(kept_rows, _stage_cascade_outputs(kept_rows)[2])

        for metric in metrics:
            leave_one_task_out_rows.append(
                {
                    "omitted_task_id": omitted_task_id,
                    "condition": metric["condition"],
                    "n_chains": metric["n_chains"],
                    "decision_reliability_rate": metric["decision_reliability_rate"],
                    "audit_pass_rate": metric["audit_pass_rate"],
                    "escalation_rate": metric["escalation_rate"],
                    "reliability_cascade_index": metric["reliability_cascade_index"],
                    "real_api_calls": 0,
                }
            )

    threshold_rows: list[dict[str, Any]] = []
    for threshold in [0.65, 0.70, 0.75, 0.80, 0.85]:
        for condition in CONDITIONS:
            rows = [row for row in chain_rows if row["condition"] == condition]
            n = len(rows)
            low_alignment = sum(1 for row in rows if _as_float(row["evidence_alignment_score"]) < threshold)
            low_confidence = sum(1 for row in rows if _as_float(row["decision_confidence"]) < threshold)

            threshold_rows.append(
                {
                    "threshold": threshold,
                    "condition": condition,
                    "n_chains": n,
                    "low_alignment_rate": _safe_rate(low_alignment, n),
                    "low_decision_confidence_rate": _safe_rate(low_confidence, n),
                    "real_api_calls": 0,
                }
            )

    condition_order_rows: list[dict[str, Any]] = []
    for order_name, ordered_conditions in {
        "design_order": CONDITIONS,
        "degradation_first": ["partial", "conflicted", "complete"],
        "conflict_first": ["conflicted", "partial", "complete"],
    }.items():
        ordered_metric_values = [
            next(row for row in condition_metric_rows if row["condition"] == condition)["reliability_cascade_index"]
            for condition in ordered_conditions
        ]
        condition_order_rows.append(
            {
                "order_name": order_name,
                "condition_order": json.dumps(ordered_conditions, ensure_ascii=False),
                "ordered_reliability_cascade_indices": json.dumps(ordered_metric_values, ensure_ascii=False),
                "range_reliability_cascade_index": round(max(ordered_metric_values) - min(ordered_metric_values), 6),
                "real_api_calls": 0,
            }
        )

    high_signal_rows: list[dict[str, Any]] = []
    for row in chain_rows:
        high_signal = (
            _as_bool(row["requires_human_review"])
            or not _as_bool(row["decision_matches_gold"])
            or not _as_bool(row["audit_pass"])
            or _as_float(row["evidence_alignment_score"]) < 0.75
        )
        if high_signal:
            high_signal_rows.append(
                {
                    "task_id": row["task_id"],
                    "condition": row["condition"],
                    "gold_decision": row["gold_decision"],
                    "decision_label": row["decision_label"],
                    "decision_matches_gold": row["decision_matches_gold"],
                    "audit_pass": row["audit_pass"],
                    "requires_human_review": row["requires_human_review"],
                    "evidence_alignment_score": row["evidence_alignment_score"],
                    "escalation_label": row["escalation_label"],
                    "signal_reason": "review_or_mismatch_or_audit_or_low_alignment",
                    "real_api_calls": 0,
                }
            )

    high_signal_rows = sorted(
        high_signal_rows,
        key=lambda row: (row["condition"], row["task_id"]),
    )

    return leave_one_task_out_rows, threshold_rows, condition_order_rows, high_signal_rows


def _manifest(
    *,
    artifact: str,
    generator: str,
    output_dir: Path,
    row_counts: dict[str, int],
    output_files: list[Path],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest_path = output_dir / "manifest.json"
    payload: dict[str, Any] = {
        "artifact": artifact,
        "status": "PASS",
        "created_at_utc": _load_existing_created_at(manifest_path),
        "generator": generator,
        "row_counts": row_counts,
        "output_files": [str(path) for path in output_files],
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }
    if extra:
        payload.update(extra)
    return payload


def generate_pilot_04_analysis_outputs() -> dict[str, Any]:
    """Generate Pilot 04 derived outputs from deterministic no-call dry-run CSVs."""
    for required_path in [DRY_RUN_CHAIN_CSV, DECISION_OUTPUTS_CSV, AUDIT_OUTPUTS_CSV, ESCALATION_OUTPUTS_CSV]:
        if not required_path.exists():
            raise FileNotFoundError(f"Missing required dry-run input: {required_path}")

    chain_rows = _read_csv(DRY_RUN_CHAIN_CSV)

    stage_condition_rows, transition_rows, paired_rows = _stage_cascade_outputs(chain_rows)
    uncertainty_condition_rows, uncertainty_task_rows = _uncertainty_outputs(chain_rows)
    condition_metric_rows, delta_rows, paired_metric_rows = _reliability_cascade_outputs(chain_rows, paired_rows)
    leave_one_out_rows, threshold_rows, condition_order_rows, high_signal_rows = _robustness_outputs(
        chain_rows,
        condition_metric_rows,
        paired_metric_rows,
    )

    outputs = [
        OutputSpec(STAGE_CASCADE_DIR / "condition_stage_cascade_summary.csv", stage_condition_rows),
        OutputSpec(STAGE_CASCADE_DIR / "stage_transition_metrics.csv", transition_rows),
        OutputSpec(STAGE_CASCADE_DIR / "paired_task_stage_deltas.csv", paired_rows),
        OutputSpec(UNCERTAINTY_DIR / "condition_uncertainty_summary.csv", uncertainty_condition_rows),
        OutputSpec(UNCERTAINTY_DIR / "task_uncertainty_profiles.csv", uncertainty_task_rows),
        OutputSpec(RELIABILITY_CASCADE_DIR / "condition_reliability_cascade_metrics.csv", condition_metric_rows),
        OutputSpec(RELIABILITY_CASCADE_DIR / "evidence_condition_delta_metrics.csv", delta_rows),
        OutputSpec(RELIABILITY_CASCADE_DIR / "paired_task_reliability_deltas.csv", paired_metric_rows),
        OutputSpec(ROBUSTNESS_DIR / "leave_one_task_out_sensitivity.csv", leave_one_out_rows),
        OutputSpec(ROBUSTNESS_DIR / "cascade_threshold_sensitivity.csv", threshold_rows),
        OutputSpec(ROBUSTNESS_DIR / "condition_order_sensitivity.csv", condition_order_rows),
        OutputSpec(ROBUSTNESS_DIR / "high_signal_case_profile.csv", high_signal_rows),
    ]

    for output in outputs:
        _write_csv(output.path, output.rows)

    stage_manifest = _manifest(
        artifact="pilot_04_stage_cascade",
        generator="experiments.pilot_04_generate_analysis_outputs",
        output_dir=STAGE_CASCADE_DIR,
        row_counts={
            "condition_stage_cascade_summary": len(stage_condition_rows),
            "stage_transition_metrics": len(transition_rows),
            "paired_task_stage_deltas": len(paired_rows),
        },
        output_files=[
            STAGE_CASCADE_DIR / "condition_stage_cascade_summary.csv",
            STAGE_CASCADE_DIR / "stage_transition_metrics.csv",
            STAGE_CASCADE_DIR / "paired_task_stage_deltas.csv",
            STAGE_CASCADE_DIR / "manifest.json",
        ],
    )

    uncertainty_manifest = _manifest(
        artifact="pilot_04_uncertainty",
        generator="experiments.pilot_04_generate_analysis_outputs",
        output_dir=UNCERTAINTY_DIR,
        row_counts={
            "condition_uncertainty_summary": len(uncertainty_condition_rows),
            "task_uncertainty_profiles": len(uncertainty_task_rows),
        },
        output_files=[
            UNCERTAINTY_DIR / "condition_uncertainty_summary.csv",
            UNCERTAINTY_DIR / "task_uncertainty_profiles.csv",
            UNCERTAINTY_DIR / "manifest.json",
        ],
    )

    reliability_manifest = _manifest(
        artifact="pilot_04_reliability_cascade_metrics",
        generator="experiments.pilot_04_generate_analysis_outputs",
        output_dir=RELIABILITY_CASCADE_DIR,
        row_counts={
            "condition_reliability_cascade_metrics": len(condition_metric_rows),
            "evidence_condition_delta_metrics": len(delta_rows),
            "paired_task_reliability_deltas": len(paired_metric_rows),
        },
        output_files=[
            RELIABILITY_CASCADE_DIR / "condition_reliability_cascade_metrics.csv",
            RELIABILITY_CASCADE_DIR / "evidence_condition_delta_metrics.csv",
            RELIABILITY_CASCADE_DIR / "paired_task_reliability_deltas.csv",
            RELIABILITY_CASCADE_DIR / "manifest.json",
        ],
    )

    robustness_manifest = _manifest(
        artifact="pilot_04_robustness_sensitivity",
        generator="experiments.pilot_04_generate_analysis_outputs",
        output_dir=ROBUSTNESS_DIR,
        row_counts={
            "leave_one_task_out_sensitivity": len(leave_one_out_rows),
            "cascade_threshold_sensitivity": len(threshold_rows),
            "condition_order_sensitivity": len(condition_order_rows),
            "high_signal_case_profile": len(high_signal_rows),
        },
        output_files=[
            ROBUSTNESS_DIR / "leave_one_task_out_sensitivity.csv",
            ROBUSTNESS_DIR / "cascade_threshold_sensitivity.csv",
            ROBUSTNESS_DIR / "condition_order_sensitivity.csv",
            ROBUSTNESS_DIR / "high_signal_case_profile.csv",
            ROBUSTNESS_DIR / "manifest.json",
        ],
        extra={
            "high_signal_case_profile_is_diagnostic": True,
            "not_model_failure_claim": True,
        },
    )

    _write_json(STAGE_CASCADE_DIR / "manifest.json", stage_manifest)
    _write_json(UNCERTAINTY_DIR / "manifest.json", uncertainty_manifest)
    _write_json(RELIABILITY_CASCADE_DIR / "manifest.json", reliability_manifest)
    _write_json(ROBUSTNESS_DIR / "manifest.json", robustness_manifest)

    combined = {
        "artifact": "pilot_04_analysis_outputs",
        "status": "PASS",
        "generator": "experiments.pilot_04_generate_analysis_outputs",
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "manifests": {
            "stage_cascade": stage_manifest,
            "uncertainty": uncertainty_manifest,
            "reliability_cascade_metrics": reliability_manifest,
            "robustness_sensitivity": robustness_manifest,
        },
        "row_counts": {
            "condition_stage_cascade_summary": len(stage_condition_rows),
            "stage_transition_metrics": len(transition_rows),
            "paired_task_stage_deltas": len(paired_rows),
            "condition_uncertainty_summary": len(uncertainty_condition_rows),
            "task_uncertainty_profiles": len(uncertainty_task_rows),
            "condition_reliability_cascade_metrics": len(condition_metric_rows),
            "evidence_condition_delta_metrics": len(delta_rows),
            "paired_task_reliability_deltas": len(paired_metric_rows),
            "leave_one_task_out_sensitivity": len(leave_one_out_rows),
            "cascade_threshold_sensitivity": len(threshold_rows),
            "condition_order_sensitivity": len(condition_order_rows),
            "high_signal_case_profile": len(high_signal_rows),
        },
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }

    return combined


def main() -> None:
    manifest = generate_pilot_04_analysis_outputs()
    print("Pilot 04 derived analysis outputs generated.")
    print("status:", manifest["status"])
    print("row_counts:", manifest["row_counts"])
    print("real_api_calls:", manifest["real_api_calls"])
    print("raw_response_inspection:", manifest["raw_response_inspection"])


if __name__ == "__main__":
    main()
