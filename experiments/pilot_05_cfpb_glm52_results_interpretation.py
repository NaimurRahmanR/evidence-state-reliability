#!/usr/bin/env python3
"""
TASK 05AL: Pilot 05 GLM-5.2 Results Interpretation and Claim-Boundary Report

No-call, sanitized-output-only interpretation layer for the Pilot 05 GLM-5.2 micro-pilot.

This script reads committed sanitized 05AJ-C and 05AK outputs and writes a readable
interpretation report plus auditable CSV/JSON outputs. It does not call external APIs,
does not read .env, does not touch raw CFPB data, and does not create JSONL files.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

TASK_ID = "05AL"
TASK_NAME = "PILOT 05 GLM-5.2 RESULTS INTERPRETATION AND CLAIM-BOUNDARY REPORT"
ANALYSIS_MODE = "NO_CALL_SANITIZED_INTERPRETATION"
EXPECTED_INPUT_COMMIT_SHORT = "f9eb074"
EXPECTED_INPUT_COMMIT_SUBJECT = "Add Pilot 05 GLM-5.2 reliability cascade metrics"

REPORT_ROOT = Path("reports")
EXPERIMENT_ROOT = Path("experiments")

AK_DIR = REPORT_ROOT / "pilot_05_cfpb_glm52_reliability_cascade_metrics"
V4_DIR = REPORT_ROOT / "pilot_05_cfpb_glm52_micro_pilot_execution_recovery_v4"
V5_DIR = REPORT_ROOT / "pilot_05_cfpb_glm52_micro_pilot_execution_finalization_v5"
OUT_DIR = REPORT_ROOT / "pilot_05_cfpb_glm52_results_interpretation"

INPUT_FILES = {
    "ak_manifest": AK_DIR / "pilot_05_cfpb_glm52_reliability_cascade_metrics_manifest.json",
    "call_accounting": AK_DIR / "pilot_05_cfpb_glm52_call_accounting_metrics.csv",
    "stage_validity": AK_DIR / "pilot_05_cfpb_glm52_parser_validity_by_stage.csv",
    "condition_validity": AK_DIR / "pilot_05_cfpb_glm52_parser_validity_by_condition.csv",
    "condition_stage_validity": AK_DIR / "pilot_05_cfpb_glm52_parser_validity_by_condition_stage.csv",
    "failure_family": AK_DIR / "pilot_05_cfpb_glm52_failure_family_metrics.csv",
    "cascade_sequence": AK_DIR / "pilot_05_cfpb_glm52_cascade_sequence_metrics.csv",
    "usage_cost": AK_DIR / "pilot_05_cfpb_glm52_usage_cost_metrics.csv",
    "metric_definitions": AK_DIR / "pilot_05_cfpb_glm52_metric_definitions.csv",
    "claim_boundary_summary": AK_DIR / "pilot_05_cfpb_glm52_claim_boundary_summary.csv",
    "cascade_report": AK_DIR / "pilot_05_cfpb_glm52_reliability_cascade_report.md",
}

OUTPUT_FILES = {
    "manifest": OUT_DIR / "pilot_05_cfpb_glm52_results_interpretation_manifest.json",
    "key_findings": OUT_DIR / "pilot_05_cfpb_glm52_key_findings.csv",
    "stage_interpretation": OUT_DIR / "pilot_05_cfpb_glm52_stage_interpretation.csv",
    "condition_interpretation": OUT_DIR / "pilot_05_cfpb_glm52_condition_interpretation.csv",
    "parser_failure_interpretation": OUT_DIR / "pilot_05_cfpb_glm52_parser_failure_interpretation.csv",
    "cascade_sequence_interpretation": OUT_DIR / "pilot_05_cfpb_glm52_cascade_sequence_interpretation.csv",
    "claim_boundary_review": OUT_DIR / "pilot_05_cfpb_glm52_claim_boundary_review.csv",
    "publication_readiness_notes": OUT_DIR / "pilot_05_cfpb_glm52_publication_readiness_notes.csv",
    "report": OUT_DIR / "pilot_05_cfpb_glm52_results_interpretation_report.md",
}

FORBIDDEN_OUTPUT_PATTERNS = (
    "*.jsonl",
    "*raw_prompt*",
    "*raw_response*",
    "*prompt_instance*",
    "*.env",
)

BROAD_CLAIMS_FORBIDDEN = [
    "Q1-level result already proven",
    "ground-breaking result already proven",
    "real-world deployment validity",
    "financial safety",
    "legal safety",
    "medical safety",
    "regulated lending validity",
    "real lending decision validity",
    "real loan-data validation",
    "provider/model superiority",
    "general GLM reliability",
    "general Claude reliability",
    "broad LLM reliability",
    "consumer harm prevalence",
    "company misconduct",
    "parser validity equals answer correctness",
    "small micro-pilot proves domain reliability",
]

SAFE_CORE_WORDING = (
    "Pilot 05 provides controlled, CFPB-backed, sanitized micro-pilot evidence that "
    "evidence-state degradation and reliability-layer behavior can be measured across "
    "decision, audit, and escalation stages. The current GLM-5.2 results are preliminary "
    "micro-pilot evidence and should not be interpreted as broad model or deployment validity."
)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def norm_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in fieldnames})


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def flatten_json(obj: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_json(value, new_prefix))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            new_prefix = f"{prefix}[{idx}]"
            out.update(flatten_json(value, new_prefix))
    else:
        out[prefix] = obj
    return out


def try_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    text = clean_text(value)
    if text == "":
        return None
    text = text.replace(",", "")
    if text.endswith("%"):
        base = try_float(text[:-1])
        return None if base is None else base / 100.0
    try:
        val = float(text)
    except ValueError:
        return None
    if math.isnan(val) or math.isinf(val):
        return None
    return val


def try_int(value: Any) -> Optional[int]:
    val = try_float(value)
    if val is None:
        return None
    if abs(val - round(val)) < 1e-9:
        return int(round(val))
    return None


def lookup_flat(flat: Dict[str, Any], candidates: Sequence[str]) -> Optional[Any]:
    norm_candidates = [norm_text(c) for c in candidates]
    norm_map = {norm_text(k.split(".")[-1]): v for k, v in flat.items()}
    full_norm_map = {norm_text(k): v for k, v in flat.items()}
    for cand in norm_candidates:
        if cand in norm_map:
            return norm_map[cand]
        if cand in full_norm_map:
            return full_norm_map[cand]
    for cand in norm_candidates:
        cand_tokens = [token for token in cand.split("_") if token]
        for key, value in full_norm_map.items():
            if all(token in key for token in cand_tokens):
                return value
    return None


def find_col(rows: Sequence[Dict[str, str]], candidates: Sequence[str]) -> Optional[str]:
    if not rows:
        return None
    cols = list(rows[0].keys())
    norm_cols = {norm_text(col): col for col in cols}
    for cand in candidates:
        n = norm_text(cand)
        if n in norm_cols:
            return norm_cols[n]
    for cand in candidates:
        tokens = [t for t in norm_text(cand).split("_") if t]
        for col in cols:
            ncol = norm_text(col)
            if all(t in ncol for t in tokens):
                return col
    return None


def first_nonempty(row: Dict[str, str], columns: Sequence[Optional[str]], default: str = "not_available") -> str:
    for col in columns:
        if col and clean_text(row.get(col)):
            return clean_text(row.get(col))
    return default


def row_number(row: Dict[str, str], columns: Sequence[Optional[str]]) -> Optional[float]:
    for col in columns:
        if col and col in row:
            val = try_float(row.get(col))
            if val is not None:
                return val
    return None


def format_number(value: Any, digits: int = 4) -> str:
    val = try_float(value)
    if val is None:
        return "not_available"
    if abs(val - round(val)) < 1e-9:
        return str(int(round(val)))
    return f"{val:.{digits}f}".rstrip("0").rstrip(".")


def format_rate(value: Any) -> str:
    val = try_float(value)
    if val is None:
        return "not_available"
    if val > 1.0 and val <= 100.0:
        val = val / 100.0
    return f"{val:.1%}"


def compute_rate(valid: Optional[float], total: Optional[float]) -> Optional[float]:
    if valid is None or total is None or total <= 0:
        return None
    return valid / total


def classify_parser_rate(rate: Optional[float]) -> Tuple[str, str]:
    if rate is None:
        return (
            "rate_not_available",
            "Parser-validity rate was not available from the metric row; interpretation is limited to the row-level evidence provided.",
        )
    if rate >= 0.80:
        return (
            "mostly_parser_valid",
            "Most responses in this slice were parser-valid, but this still does not establish answer correctness or domain validity.",
        )
    if rate >= 0.55:
        return (
            "moderately_parser_valid",
            "Parser-valid behavior was more common than invalid behavior in this slice, with remaining parser fragility still visible.",
        )
    if rate >= 0.45:
        return (
            "mixed_parser_validity",
            "Parser-valid and parser-invalid behavior were closely balanced, making this a useful reliability-layer stress signal.",
        )
    if rate > 0:
        return (
            "parser_invalid_dominant",
            "Parser-invalid behavior was more common than parser-valid behavior in this slice, suggesting interface/schema fragility under the tested conditions.",
        )
    return (
        "no_parser_valid_rows",
        "No parser-valid rows were observed in this slice; this is an interface/schema reliability signal, not a direct measure of answer correctness.",
    )


def extract_count_summary(manifest_flat: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "status": lookup_flat(manifest_flat, ["status"]),
        "analysis_mode": lookup_flat(manifest_flat, ["analysis_mode", "mode"]),
        "api_calls": lookup_flat(manifest_flat, ["api_calls", "api_calls_in_05ak", "n_api_calls"]),
        "api_key_read": lookup_flat(manifest_flat, ["api_key_read", "api_key_read_in_05ak"]),
        "total_approved_call_attempts_accounted_for": lookup_flat(
            manifest_flat,
            [
                "total_approved_glm_5_2_call_attempts_accounted_for",
                "total_approved_call_attempts_accounted_for",
                "approved_call_attempts_accounted_for",
            ],
        ),
        "persisted_execution_rows_analyzed": lookup_flat(
            manifest_flat,
            [
                "persisted_execution_rows_analyzed",
                "persisted_sanitized_output_rows_analyzed",
                "persisted_execution_rows",
            ],
        ),
        "prior_attempt_rows_accounted_for": lookup_flat(
            manifest_flat,
            ["prior_attempt_rows_accounted_for", "prior_attempt_rows", "prior_calls_accounted_for"],
        ),
        "parser_status_rows_analyzed": lookup_flat(
            manifest_flat,
            ["parser_status_rows_analyzed", "parser_rows_analyzed", "parser_status_rows"],
        ),
        "cascade_sequence_rows": lookup_flat(
            manifest_flat,
            ["cascade_sequence_rows", "n_cascade_sequence_rows"],
        ),
        "persisted_parser_valid_count": lookup_flat(
            manifest_flat,
            ["persisted_parser_valid_count", "parser_valid_count", "valid_count"],
        ),
        "persisted_parser_invalid_count": lookup_flat(
            manifest_flat,
            ["persisted_parser_invalid_count", "parser_invalid_count", "invalid_count"],
        ),
        "persisted_parser_unknown_count": lookup_flat(
            manifest_flat,
            ["persisted_parser_unknown_count", "parser_unknown_count", "unknown_count"],
        ),
        "raw_prompt_instances_written": lookup_flat(
            manifest_flat,
            ["raw_prompt_instances_written", "raw_prompts_written", "raw_prompt_written"],
        ),
        "raw_responses_written": lookup_flat(
            manifest_flat,
            ["raw_responses_written", "raw_response_written"],
        ),
        "jsonl_written": lookup_flat(manifest_flat, ["jsonl_written", "jsonl_files_written"]),
    }

    # Fallback from condition metrics if manifest uses different key names.
    condition_rows = loaded.get("condition_validity", [])
    if condition_rows:
        total_col = find_col(condition_rows, ["total", "total_count", "n", "row_count", "parser_status_rows"])
        valid_col = find_col(condition_rows, ["parser_valid_count", "valid_count", "n_valid"])
        invalid_col = find_col(condition_rows, ["parser_invalid_count", "invalid_count", "n_invalid"])
        unknown_col = find_col(condition_rows, ["parser_unknown_count", "unknown_count", "n_unknown"])
        if summary["persisted_parser_valid_count"] is None and valid_col:
            summary["persisted_parser_valid_count"] = sum((try_int(r.get(valid_col)) or 0) for r in condition_rows)
        if summary["persisted_parser_invalid_count"] is None and invalid_col:
            summary["persisted_parser_invalid_count"] = sum((try_int(r.get(invalid_col)) or 0) for r in condition_rows)
        if summary["persisted_parser_unknown_count"] is None and unknown_col:
            summary["persisted_parser_unknown_count"] = sum((try_int(r.get(unknown_col)) or 0) for r in condition_rows)
        if summary["parser_status_rows_analyzed"] is None and total_col:
            summary["parser_status_rows_analyzed"] = sum((try_int(r.get(total_col)) or 0) for r in condition_rows)

    cascade_rows = loaded.get("cascade_sequence", [])
    if summary["cascade_sequence_rows"] is None:
        summary["cascade_sequence_rows"] = len(cascade_rows)

    return summary


def make_key_findings(summary: Dict[str, Any], row_counts: Dict[str, int]) -> List[Dict[str, Any]]:
    valid = try_int(summary.get("persisted_parser_valid_count"))
    invalid = try_int(summary.get("persisted_parser_invalid_count"))
    unknown = try_int(summary.get("persisted_parser_unknown_count"))
    parser_rows = try_int(summary.get("parser_status_rows_analyzed"))
    persisted_rows = try_int(summary.get("persisted_execution_rows_analyzed"))
    total_calls = try_int(summary.get("total_approved_call_attempts_accounted_for"))
    prior_attempts = try_int(summary.get("prior_attempt_rows_accounted_for"))
    sequence_rows = try_int(summary.get("cascade_sequence_rows")) or row_counts.get("cascade_sequence", 0)

    valid_rate = compute_rate(valid, parser_rows)
    invalid_rate = compute_rate(invalid, parser_rows)

    findings: List[Dict[str, Any]] = []
    findings.append(
        {
            "finding_id": "KF-01",
            "theme": "sanitized_no_call_interpretation",
            "evidence_source": "05AK manifest and committed sanitized metric files",
            "finding": (
                f"05AL is a no-call interpretation layer over committed sanitized outputs. "
                f"The upstream 05AK analysis status is {clean_text(summary.get('status')) or 'not_available'} "
                f"with analysis mode {clean_text(summary.get('analysis_mode')) or 'not_available'}."
            ),
            "publication_relevance": "Supports reproducibility and auditability of the empirical pipeline without exposing raw prompts, raw responses, secrets, or raw CFPB data.",
            "claim_boundary": "This is an interpretation/reporting layer only; it does not add new model evidence.",
        }
    )
    findings.append(
        {
            "finding_id": "KF-02",
            "theme": "call_accounting",
            "evidence_source": "05AK call accounting metrics and manifest",
            "finding": (
                f"The micro-pilot accounting records {format_number(total_calls)} approved GLM-5.2 call attempts, "
                f"{format_number(persisted_rows)} persisted sanitized execution rows, and "
                f"{format_number(prior_attempts)} prior attempt rows accounted for."
            ),
            "publication_relevance": "Call accounting is important because reliability claims require denominator clarity, especially when persisted outputs differ from attempted calls.",
            "claim_boundary": "This supports micro-pilot accounting only, not broad provider or model reliability.",
        }
    )
    findings.append(
        {
            "finding_id": "KF-03",
            "theme": "parser_validity_split",
            "evidence_source": "05AK parser validity metrics",
            "finding": (
                f"Parser-status accounting records {format_number(parser_rows)} analyzed parser-status rows: "
                f"{format_number(valid)} parser-valid, {format_number(invalid)} parser-invalid, and "
                f"{format_number(unknown)} parser-unknown. "
                f"The parser-valid rate is {format_rate(valid_rate)} and the parser-invalid rate is {format_rate(invalid_rate)} when these values are available."
            ),
            "publication_relevance": "The split is directly relevant to Evidence-State Reliability because interface/schema validity can fail even before final answer correctness is assessed.",
            "claim_boundary": "Parser validity is not answer correctness; parser invalidity is a reliability-layer signal, not a validated domain-error label.",
        }
    )
    findings.append(
        {
            "finding_id": "KF-04",
            "theme": "stage_level_behavior",
            "evidence_source": "05AK parser validity by stage metrics",
            "finding": f"Stage-level metrics are available for {row_counts.get('stage_validity', 0)} stage rows, allowing decision, audit, and escalation behavior to be interpreted separately.",
            "publication_relevance": "Stage separation supports the core argument that reliability should be measured across intermediate evidence/decision/audit/escalation states, not only at the final output.",
            "claim_boundary": "Stage-level patterns are preliminary because this is still a small controlled micro-pilot.",
        }
    )
    findings.append(
        {
            "finding_id": "KF-05",
            "theme": "cascade_sequence_behavior",
            "evidence_source": "05AK cascade sequence metrics",
            "finding": f"Cascade-sequence metrics are available for {format_number(sequence_rows)} sequence rows, making it possible to inspect how reliability-layer behavior propagates across the pipeline.",
            "publication_relevance": "Cascade sequence rows are publication-relevant because they operationalize reliability cascades rather than treating each output as an isolated prediction.",
            "claim_boundary": "The sequence results show measurable cascade behavior in this controlled run, not general deployment validity.",
        }
    )
    findings.append(
        {
            "finding_id": "KF-06",
            "theme": "safe_core_claim",
            "evidence_source": "05AK metrics plus explicit claim-boundary review",
            "finding": SAFE_CORE_WORDING,
            "publication_relevance": "This is the strongest safe wording for the current state of the empirical evidence.",
            "claim_boundary": "Do not upgrade this into broad model, financial, legal, lending, or real-world safety claims without larger experiments and external validation.",
        }
    )
    return findings


def make_stage_interpretation(stage_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    stage_col = find_col(stage_rows, ["stage", "pipeline_stage", "stage_name", "llm_stage"])
    total_col = find_col(stage_rows, ["total", "total_count", "n", "row_count", "parser_status_rows", "stage_rows"])
    valid_col = find_col(stage_rows, ["parser_valid_count", "valid_count", "n_valid"])
    invalid_col = find_col(stage_rows, ["parser_invalid_count", "invalid_count", "n_invalid"])
    unknown_col = find_col(stage_rows, ["parser_unknown_count", "unknown_count", "n_unknown"])
    rate_col = find_col(stage_rows, ["parser_valid_rate", "valid_rate", "parser_valid_fraction"])

    output: List[Dict[str, Any]] = []
    for idx, row in enumerate(stage_rows, start=1):
        stage = first_nonempty(row, [stage_col], f"stage_{idx}")
        total = row_number(row, [total_col])
        valid = row_number(row, [valid_col])
        invalid = row_number(row, [invalid_col])
        unknown = row_number(row, [unknown_col])
        rate = row_number(row, [rate_col])
        if rate is None:
            rate = compute_rate(valid, total)
        classification, interpretation = classify_parser_rate(rate)
        output.append(
            {
                "stage": stage,
                "n_rows": format_number(total),
                "parser_valid_count": format_number(valid),
                "parser_invalid_count": format_number(invalid),
                "parser_unknown_count": format_number(unknown),
                "parser_valid_rate": format_rate(rate),
                "interpretation_label": classification,
                "interpretation": interpretation,
                "evidence_state_relevance": "This stage should be read as a reliability-layer checkpoint in the multi-stage cascade, not as a standalone final-answer correctness result.",
                "claim_boundary": "Stage patterns are preliminary micro-pilot evidence only.",
            }
        )
    return output


def make_condition_interpretation(condition_rows: List[Dict[str, str]], condition_stage_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    condition_col = find_col(condition_rows, ["condition", "evidence_condition", "condition_name", "degradation_condition"])
    total_col = find_col(condition_rows, ["total", "total_count", "n", "row_count", "parser_status_rows"])
    valid_col = find_col(condition_rows, ["parser_valid_count", "valid_count", "n_valid"])
    invalid_col = find_col(condition_rows, ["parser_invalid_count", "invalid_count", "n_invalid"])
    unknown_col = find_col(condition_rows, ["parser_unknown_count", "unknown_count", "n_unknown"])
    rate_col = find_col(condition_rows, ["parser_valid_rate", "valid_rate", "parser_valid_fraction"])

    stage_condition_col = find_col(condition_stage_rows, ["condition", "evidence_condition", "condition_name", "degradation_condition"])
    stage_stage_col = find_col(condition_stage_rows, ["stage", "pipeline_stage", "stage_name", "llm_stage"])
    stage_rate_col = find_col(condition_stage_rows, ["parser_valid_rate", "valid_rate", "parser_valid_fraction"])
    stage_total_col = find_col(condition_stage_rows, ["total", "total_count", "n", "row_count"])
    stage_valid_col = find_col(condition_stage_rows, ["parser_valid_count", "valid_count", "n_valid"])

    output: List[Dict[str, Any]] = []
    for idx, row in enumerate(condition_rows, start=1):
        condition = first_nonempty(row, [condition_col], f"condition_{idx}")
        total = row_number(row, [total_col])
        valid = row_number(row, [valid_col])
        invalid = row_number(row, [invalid_col])
        unknown = row_number(row, [unknown_col])
        rate = row_number(row, [rate_col])
        if rate is None:
            rate = compute_rate(valid, total)
        classification, interpretation = classify_parser_rate(rate)

        stage_notes = []
        for sr in condition_stage_rows:
            sr_condition = first_nonempty(sr, [stage_condition_col], "not_available")
            if norm_text(sr_condition) != norm_text(condition) and stage_condition_col:
                continue
            sr_stage = first_nonempty(sr, [stage_stage_col], "stage_not_available")
            sr_total = row_number(sr, [stage_total_col])
            sr_valid = row_number(sr, [stage_valid_col])
            sr_rate = row_number(sr, [stage_rate_col])
            if sr_rate is None:
                sr_rate = compute_rate(sr_valid, sr_total)
            stage_notes.append(f"{sr_stage}: valid_rate={format_rate(sr_rate)}, n={format_number(sr_total)}")
        output.append(
            {
                "condition": condition,
                "n_rows": format_number(total),
                "parser_valid_count": format_number(valid),
                "parser_invalid_count": format_number(invalid),
                "parser_unknown_count": format_number(unknown),
                "parser_valid_rate": format_rate(rate),
                "interpretation_label": classification,
                "condition_interpretation": interpretation,
                "stage_breakdown_note": "; ".join(stage_notes) if stage_notes else "No condition-stage breakdown matched this condition or breakdown columns were unavailable.",
                "evidence_state_relevance": "Condition-level behavior helps separate evidence degradation effects from final-output-only evaluation.",
                "claim_boundary": "Condition-level interpretation is descriptive and micro-pilot bounded.",
            }
        )
    return output


def make_failure_interpretation(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    family_col = find_col(rows, ["failure_family", "family", "parser_failure_family", "failure_type", "error_family"])
    count_col = find_col(rows, ["count", "n", "row_count", "failure_count", "parser_invalid_count"])
    rate_col = find_col(rows, ["rate", "fraction", "share", "failure_rate"])
    example_col = find_col(rows, ["example", "sanitized_example", "representative_example", "note"])

    output: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        family = first_nonempty(row, [family_col], f"failure_family_{idx}")
        count = row_number(row, [count_col])
        rate = row_number(row, [rate_col])
        example = first_nonempty(row, [example_col], "not_available")
        output.append(
            {
                "failure_family": family,
                "count": format_number(count),
                "rate_or_share": format_rate(rate) if rate is not None else "not_available",
                "sanitized_note_or_example": example,
                "interpretation": "This failure family is treated as a parser/interface reliability signal. It should not be interpreted as validated domain incorrectness unless later checked against task-specific correctness labels.",
                "publication_relevance": "Failure-family grouping is useful for showing where structured-output reliability breaks in the cascade.",
                "claim_boundary": "Do not use failure-family counts to claim consumer harm, company misconduct, financial safety, or broad model reliability.",
            }
        )
    return output


def make_sequence_interpretation(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    sequence_col = find_col(rows, ["sequence", "cascade_sequence", "sequence_id", "case_id", "packet_id", "task_id"])
    condition_col = find_col(rows, ["condition", "evidence_condition", "condition_name"])
    valid_col = find_col(rows, ["parser_valid_count", "valid_count", "n_valid"])
    invalid_col = find_col(rows, ["parser_invalid_count", "invalid_count", "n_invalid"])
    unknown_col = find_col(rows, ["parser_unknown_count", "unknown_count", "n_unknown"])
    total_col = find_col(rows, ["total", "total_count", "n", "row_count", "sequence_rows"])
    sequence_pattern_col = find_col(rows, ["pattern", "parser_sequence", "stage_pattern", "validity_sequence"])
    rate_col = find_col(rows, ["parser_valid_rate", "valid_rate", "parser_valid_fraction"])

    output: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        seq = first_nonempty(row, [sequence_col], f"sequence_{idx:02d}")
        condition = first_nonempty(row, [condition_col], "not_available")
        pattern = first_nonempty(row, [sequence_pattern_col], "not_available")
        total = row_number(row, [total_col])
        valid = row_number(row, [valid_col])
        invalid = row_number(row, [invalid_col])
        unknown = row_number(row, [unknown_col])
        rate = row_number(row, [rate_col])
        if rate is None:
            rate = compute_rate(valid, total)
        classification, interpretation = classify_parser_rate(rate)
        output.append(
            {
                "cascade_sequence": seq,
                "condition": condition,
                "parser_sequence_or_pattern": pattern,
                "n_rows": format_number(total),
                "parser_valid_count": format_number(valid),
                "parser_invalid_count": format_number(invalid),
                "parser_unknown_count": format_number(unknown),
                "parser_valid_rate": format_rate(rate),
                "interpretation_label": classification,
                "cascade_interpretation": interpretation,
                "evidence_state_relevance": "Sequence-level interpretation is the closest 05AL output to the reliability-cascade concept because it keeps stage order and propagation visible.",
                "claim_boundary": "This sequence-level evidence is controlled and preliminary; it does not establish real-world deployment validity.",
            }
        )
    return output


def make_claim_boundary_review(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = [
        {
            "boundary_id": "CB-01",
            "claim_type": "supported_safe_claim",
            "claim_text": "Pilot 05 has controlled real GLM-5.2 micro-pilot evidence over sanitized CFPB-backed evidence-state cascades.",
            "status": "allowed_with_micro_pilot_boundary",
            "reason": "The current artifacts account for the approved micro-pilot calls and contain sanitized derived metrics.",
            "required_next_evidence_to_strengthen": "Scale task count, add comparison models, preserve denominator accounting, and add correctness/human-review labels where appropriate.",
        },
        {
            "boundary_id": "CB-02",
            "claim_type": "supported_safe_claim",
            "claim_text": "Parser validity and reliability-layer behavior can be measured separately from final output validity.",
            "status": "allowed",
            "reason": "05AK separates parser-validity accounting by stage, condition, failure family, and cascade sequence.",
            "required_next_evidence_to_strengthen": "Add task correctness labels and evidence-state perturbation contrasts so parser validity can be compared with downstream correctness.",
        },
        {
            "boundary_id": "CB-03",
            "claim_type": "forbidden_overclaim",
            "claim_text": "The micro-pilot proves broad GLM-5.2 reliability or provider superiority.",
            "status": "not_allowed",
            "reason": "The run is small, controlled, single-model, and not designed as a broad provider benchmark.",
            "required_next_evidence_to_strengthen": "Multi-model, larger-scale, repeated, cost-accounted, task-balanced experiments with predefined hypotheses.",
        },
        {
            "boundary_id": "CB-04",
            "claim_type": "forbidden_overclaim",
            "claim_text": "The results prove financial, legal, lending, regulatory, medical, or deployment safety.",
            "status": "not_allowed",
            "reason": "The artifacts are sanitized research metrics and do not validate real lending decisions, legal safety, medical safety, or deployment outcomes.",
            "required_next_evidence_to_strengthen": "External domain validation, governance review, human annotation, and explicit deployment-context risk analysis would be needed before any applied safety claim.",
        },
        {
            "boundary_id": "CB-05",
            "claim_type": "forbidden_overclaim",
            "claim_text": "Parser validity equals answer correctness.",
            "status": "not_allowed",
            "reason": "Parser validity only shows whether the response matched expected structure/schema; it does not validate semantic correctness.",
            "required_next_evidence_to_strengthen": "Add independent answer-correctness labels and compare parser-valid/invalid behavior against correctness outcomes.",
        },
        {
            "boundary_id": "CB-06",
            "claim_type": "recommended_wording",
            "claim_text": SAFE_CORE_WORDING,
            "status": "recommended",
            "reason": "This wording preserves the empirical contribution while staying micro-pilot bounded.",
            "required_next_evidence_to_strengthen": "Use the same wording until larger controlled experiments justify stronger language.",
        },
    ]
    return rows


def make_publication_readiness_notes(summary: Dict[str, Any], row_counts: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {
            "note_id": "PR-01",
            "area": "core_framing",
            "current_status": "promising",
            "note": "The strongest contribution is the separation of Evidence-State Reliability from final output validity.",
            "next_action": "Turn the frame into formal definitions: evidence state, evidence degradation, stage reliability, parser/interface reliability, cascade propagation, and governable output.",
            "risk_if_ignored": "The work may look like another parser-validity or LLM-output-formatting study instead of a reliability-cascade contribution.",
        },
        {
            "note_id": "PR-02",
            "area": "empirical_strength",
            "current_status": "micro_pilot_only",
            "note": f"Current interpreted evidence includes {row_counts.get('cascade_sequence', 0)} cascade-sequence rows and {row_counts.get('stage_validity', 0)} stage-level rows from the GLM-5.2 micro-pilot.",
            "next_action": "Scale beyond the micro-pilot with predefined task/condition grids, preserve call accounting, and maintain sanitized-output-only storage.",
            "risk_if_ignored": "The paper claim will remain too small for a strong publication unless framed only as a method/proof-of-concept.",
        },
        {
            "note_id": "PR-03",
            "area": "comparison_models",
            "current_status": "missing_for_broad_claims",
            "note": "Single-model GLM-5.2 evidence is useful but not enough for broad LLM reliability statements.",
            "next_action": "Add at least one comparison model under the same no-raw-output, denominator-accounted protocol after explicit user approval for model/API calls and cost.",
            "risk_if_ignored": "Reviewers may read the evidence as model-specific or accidental rather than a general reliability-layer phenomenon.",
        },
        {
            "note_id": "PR-04",
            "area": "correctness_labels",
            "current_status": "not_yet_established",
            "note": "Parser-validity analysis is necessary but not enough to claim final answer correctness or domain validity.",
            "next_action": "Create a claim-bounded correctness/audit label layer that evaluates semantic outputs without exposing raw prompts/responses.",
            "risk_if_ignored": "Parser-validity results could be misread or overclaimed as correctness results.",
        },
        {
            "note_id": "PR-05",
            "area": "claim_boundary",
            "current_status": "strong_and_necessary",
            "note": "The current claim-boundary discipline is a strength because it makes the research auditable and harder to overstate.",
            "next_action": "Keep explicit allowed/not-allowed claim tables in every generated report and paper draft.",
            "risk_if_ignored": "Overclaiming could damage credibility and weaken the head-turning novelty argument.",
        },
        {
            "note_id": "PR-06",
            "area": "publication_path",
            "current_status": "method_plus_empirical_micro_pilot",
            "note": "The current work is best positioned as a controlled empirical method with preliminary model evidence, not as a completed broad reliability benchmark.",
            "next_action": "After scaling and adding comparison/correctness layers, write the paper around reliability cascades caused by degraded intermediate evidence states.",
            "risk_if_ignored": "The paper may appear underpowered if the micro-pilot is presented as the final empirical result.",
        },
    ]


def markdown_table(rows: Sequence[Dict[str, Any]], columns: Sequence[str], max_rows: int = 20) -> str:
    if not rows:
        return "No rows available.\n"
    selected = list(rows[:max_rows])
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in selected:
        cells = []
        for col in columns:
            text = clean_text(row.get(col, ""))
            text = text.replace("|", "\\|")
            if len(text) > 240:
                text = text[:237] + "..."
            cells.append(text)
        body.append("| " + " | ".join(cells) + " |")
    suffix = ""
    if len(rows) > max_rows:
        suffix = f"\n\n_Only the first {max_rows} of {len(rows)} rows are shown in this Markdown table; see the CSV for the full version._\n"
    return "\n".join([header, sep] + body) + suffix + "\n"


def make_report(
    summary: Dict[str, Any],
    row_counts: Dict[str, int],
    key_findings: List[Dict[str, Any]],
    stage_interpretation: List[Dict[str, Any]],
    condition_interpretation: List[Dict[str, Any]],
    failure_interpretation: List[Dict[str, Any]],
    sequence_interpretation: List[Dict[str, Any]],
    claim_boundary_review: List[Dict[str, Any]],
    publication_notes: List[Dict[str, Any]],
) -> str:
    valid = try_int(summary.get("persisted_parser_valid_count"))
    invalid = try_int(summary.get("persisted_parser_invalid_count"))
    unknown = try_int(summary.get("persisted_parser_unknown_count"))
    parser_rows = try_int(summary.get("parser_status_rows_analyzed"))
    valid_rate = compute_rate(valid, parser_rows)

    lines: List[str] = []
    lines.append(f"# Task {TASK_ID}: Pilot 05 GLM-5.2 Results Interpretation and Claim-Boundary Report")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append("- Status: PASS")
    lines.append(f"- Analysis mode: `{ANALYSIS_MODE}`")
    lines.append("- API/model calls in 05AL: 0")
    lines.append("- API key read in 05AL: false")
    lines.append("- Raw prompts written in 05AL: false")
    lines.append("- Raw responses written in 05AL: false")
    lines.append("- JSONL written in 05AL: false")
    lines.append("- Raw CFPB data touched in 05AL: false")
    lines.append("")
    lines.append("## What the GLM-5.2 micro-pilot actually shows")
    lines.append("")
    lines.append(
        "The current evidence shows a controlled GLM-5.2 micro-pilot analyzed through a sanitized reliability-cascade metric layer. "
        f"The available accounting records {format_number(summary.get('total_approved_call_attempts_accounted_for'))} approved call attempts, "
        f"{format_number(summary.get('persisted_execution_rows_analyzed'))} persisted sanitized execution rows, and "
        f"{format_number(summary.get('prior_attempt_rows_accounted_for'))} prior attempt rows accounted for. "
        "This is real micro-pilot model evidence, but it remains small and should be used as preliminary empirical support rather than a broad benchmark."
    )
    lines.append("")
    lines.append("## Parser-valid versus parser-invalid behavior")
    lines.append("")
    lines.append(
        f"The corrected parser-status accounting records {format_number(parser_rows)} analyzed rows: "
        f"{format_number(valid)} parser-valid, {format_number(invalid)} parser-invalid, and {format_number(unknown)} parser-unknown. "
        f"The parser-valid rate is {format_rate(valid_rate)} when computed from the available counts. "
        "This matters because parser validity is a reliability-layer signal that can be measured separately from final output validity. It should not be treated as answer correctness."
    )
    lines.append("")
    lines.append("## Stage behavior")
    lines.append("")
    lines.append(markdown_table(stage_interpretation, ["stage", "n_rows", "parser_valid_count", "parser_invalid_count", "parser_valid_rate", "interpretation_label", "interpretation"]))
    lines.append("")
    lines.append("## Condition behavior")
    lines.append("")
    lines.append(markdown_table(condition_interpretation, ["condition", "n_rows", "parser_valid_count", "parser_invalid_count", "parser_valid_rate", "interpretation_label", "condition_interpretation"]))
    lines.append("")
    lines.append("## Parser failure-family interpretation")
    lines.append("")
    lines.append(markdown_table(failure_interpretation, ["failure_family", "count", "rate_or_share", "interpretation"]))
    lines.append("")
    lines.append("## Cascade sequence interpretation")
    lines.append("")
    lines.append(markdown_table(sequence_interpretation, ["cascade_sequence", "condition", "parser_sequence_or_pattern", "parser_valid_rate", "interpretation_label", "cascade_interpretation"], max_rows=12))
    lines.append("")
    lines.append("## Safe claim boundary")
    lines.append("")
    lines.append(SAFE_CORE_WORDING)
    lines.append("")
    lines.append(markdown_table(claim_boundary_review, ["boundary_id", "claim_type", "claim_text", "status", "reason"], max_rows=20))
    lines.append("")
    lines.append("## Publication-relevant metrics")
    lines.append("")
    lines.append("The most publication-relevant metric groups at this checkpoint are:")
    lines.append("")
    lines.append("1. Call-accounting metrics, because the denominator of attempted and persisted calls must be auditable.")
    lines.append("2. Parser validity by stage, because stage separation supports the Evidence-State Reliability framing.")
    lines.append("3. Parser validity by condition and condition-stage, because evidence degradation must be separated from generic output failure.")
    lines.append("4. Failure-family metrics, because they show structured-output reliability modes rather than a single pass/fail count.")
    lines.append("5. Cascade-sequence metrics, because they keep the propagation story visible across decision, audit, and escalation stages.")
    lines.append("6. Usage/cost metrics, because larger reliability experiments must remain auditable by budget and call count.")
    lines.append("")
    lines.append("## What cannot be claimed yet")
    lines.append("")
    for item in BROAD_CLAIMS_FORBIDDEN:
        lines.append(f"- Do not claim {item}.")
    lines.append("")
    lines.append("## Additional experiments needed before a stronger paper claim")
    lines.append("")
    lines.append(markdown_table(publication_notes, ["note_id", "area", "current_status", "note", "next_action"], max_rows=20))
    lines.append("")
    lines.append("## Generated output row counts")
    lines.append("")
    for key, value in row_counts.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("")
    lines.append(
        "05AL converts the corrected GLM-5.2 reliability-cascade metrics into a readable interpretation layer. "
        "The strongest current result is not broad model reliability; it is the auditable demonstration that evidence-state degradation and reliability-layer behavior can be measured across a multi-stage LLM decision pipeline."
    )
    lines.append("")
    return "\n".join(lines)


def verify_environment() -> None:
    if not Path.cwd().joinpath(".git").exists():
        fail("This script must be run from the repository root containing .git.")
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        fail(f"Output directory already exists and is not empty: {OUT_DIR}. Refusing to overwrite without explicit approval.")
    for name, path in INPUT_FILES.items():
        if not path.exists():
            fail(f"Required sanitized input missing: {name} -> {path}")
    for name, path in [("v4_dir", V4_DIR), ("v5_dir", V5_DIR), ("ak_dir", AK_DIR)]:
        if not path.exists() or not path.is_dir():
            fail(f"Required sanitized input directory missing: {name} -> {path}")
    # Do not read .env or raw data. Only check that local output target is safe.


def scan_outputs_for_forbidden_files() -> List[str]:
    hits: List[str] = []
    if not OUT_DIR.exists():
        return hits
    for pattern in FORBIDDEN_OUTPUT_PATTERNS:
        for path in OUT_DIR.rglob(pattern):
            hits.append(str(path))
    return sorted(set(hits))


def main() -> None:
    verify_environment()

    loaded: Dict[str, Any] = {}
    loaded["ak_manifest"] = read_json(INPUT_FILES["ak_manifest"])
    for key in [
        "call_accounting",
        "stage_validity",
        "condition_validity",
        "condition_stage_validity",
        "failure_family",
        "cascade_sequence",
        "usage_cost",
        "metric_definitions",
        "claim_boundary_summary",
    ]:
        loaded[key] = read_csv_rows(INPUT_FILES[key])

    manifest_flat = flatten_json(loaded["ak_manifest"])
    summary = extract_count_summary(manifest_flat, loaded)
    row_counts = {
        "call_accounting": len(loaded["call_accounting"]),
        "stage_validity": len(loaded["stage_validity"]),
        "condition_validity": len(loaded["condition_validity"]),
        "condition_stage_validity": len(loaded["condition_stage_validity"]),
        "failure_family": len(loaded["failure_family"]),
        "cascade_sequence": len(loaded["cascade_sequence"]),
        "usage_cost": len(loaded["usage_cost"]),
        "metric_definitions": len(loaded["metric_definitions"]),
        "claim_boundary_summary": len(loaded["claim_boundary_summary"]),
    }

    key_findings = make_key_findings(summary, row_counts)
    stage_interpretation = make_stage_interpretation(loaded["stage_validity"])
    condition_interpretation = make_condition_interpretation(loaded["condition_validity"], loaded["condition_stage_validity"])
    failure_interpretation = make_failure_interpretation(loaded["failure_family"])
    sequence_interpretation = make_sequence_interpretation(loaded["cascade_sequence"])
    claim_boundary_review = make_claim_boundary_review(summary)
    publication_notes = make_publication_readiness_notes(summary, row_counts)

    OUT_DIR.mkdir(parents=True, exist_ok=False)

    write_csv(
        OUTPUT_FILES["key_findings"],
        key_findings,
        ["finding_id", "theme", "evidence_source", "finding", "publication_relevance", "claim_boundary"],
    )
    write_csv(
        OUTPUT_FILES["stage_interpretation"],
        stage_interpretation,
        [
            "stage",
            "n_rows",
            "parser_valid_count",
            "parser_invalid_count",
            "parser_unknown_count",
            "parser_valid_rate",
            "interpretation_label",
            "interpretation",
            "evidence_state_relevance",
            "claim_boundary",
        ],
    )
    write_csv(
        OUTPUT_FILES["condition_interpretation"],
        condition_interpretation,
        [
            "condition",
            "n_rows",
            "parser_valid_count",
            "parser_invalid_count",
            "parser_unknown_count",
            "parser_valid_rate",
            "interpretation_label",
            "condition_interpretation",
            "stage_breakdown_note",
            "evidence_state_relevance",
            "claim_boundary",
        ],
    )
    write_csv(
        OUTPUT_FILES["parser_failure_interpretation"],
        failure_interpretation,
        [
            "failure_family",
            "count",
            "rate_or_share",
            "sanitized_note_or_example",
            "interpretation",
            "publication_relevance",
            "claim_boundary",
        ],
    )
    write_csv(
        OUTPUT_FILES["cascade_sequence_interpretation"],
        sequence_interpretation,
        [
            "cascade_sequence",
            "condition",
            "parser_sequence_or_pattern",
            "n_rows",
            "parser_valid_count",
            "parser_invalid_count",
            "parser_unknown_count",
            "parser_valid_rate",
            "interpretation_label",
            "cascade_interpretation",
            "evidence_state_relevance",
            "claim_boundary",
        ],
    )
    write_csv(
        OUTPUT_FILES["claim_boundary_review"],
        claim_boundary_review,
        ["boundary_id", "claim_type", "claim_text", "status", "reason", "required_next_evidence_to_strengthen"],
    )
    write_csv(
        OUTPUT_FILES["publication_readiness_notes"],
        publication_notes,
        ["note_id", "area", "current_status", "note", "next_action", "risk_if_ignored"],
    )

    report_text = make_report(
        summary,
        row_counts,
        key_findings,
        stage_interpretation,
        condition_interpretation,
        failure_interpretation,
        sequence_interpretation,
        claim_boundary_review,
        publication_notes,
    )
    OUTPUT_FILES["report"].write_text(report_text, encoding="utf-8")

    forbidden_hits = scan_outputs_for_forbidden_files()
    if forbidden_hits:
        fail("Forbidden output file(s) generated: " + ", ".join(forbidden_hits))

    input_digests = {name: file_sha256(path) for name, path in INPUT_FILES.items() if path.exists() and path.is_file()}
    output_digests = {name: file_sha256(path) for name, path in OUTPUT_FILES.items() if name != "manifest" and path.exists()}

    manifest = {
        "task_id": TASK_ID,
        "task_name": TASK_NAME,
        "status": "PASS",
        "analysis_mode": ANALYSIS_MODE,
        "expected_input_commit_short": EXPECTED_INPUT_COMMIT_SHORT,
        "expected_input_commit_subject": EXPECTED_INPUT_COMMIT_SUBJECT,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "api_calls_in_05al": 0,
        "api_key_read_in_05al": False,
        "raw_prompt_instances_written_in_05al": False,
        "raw_responses_written_in_05al": False,
        "jsonl_written_in_05al": False,
        "raw_cfpb_data_touched_in_05al": False,
        "input_directories": {
            "05aj_c_recovery_v4": str(V4_DIR),
            "05aj_c_finalization_v5": str(V5_DIR),
            "05ak_metrics": str(AK_DIR),
        },
        "input_files": {name: str(path) for name, path in INPUT_FILES.items()},
        "input_file_sha256": input_digests,
        "output_files": {name: str(path) for name, path in OUTPUT_FILES.items()},
        "output_file_sha256_except_manifest": output_digests,
        "source_summary_from_05ak": {key: clean_text(value) for key, value in summary.items()},
        "input_row_counts": row_counts,
        "output_row_counts": {
            "key_findings": len(key_findings),
            "stage_interpretation": len(stage_interpretation),
            "condition_interpretation": len(condition_interpretation),
            "parser_failure_interpretation": len(failure_interpretation),
            "cascade_sequence_interpretation": len(sequence_interpretation),
            "claim_boundary_review": len(claim_boundary_review),
            "publication_readiness_notes": len(publication_notes),
        },
        "safe_core_wording": SAFE_CORE_WORDING,
        "forbidden_broad_claims": BROAD_CLAIMS_FORBIDDEN,
        "validation_notes": [
            "05AL performed no API/model calls.",
            "05AL did not read .env or API keys.",
            "05AL read only committed sanitized 05AJ-C/05AK output locations supplied by the task contract.",
            "05AL generated CSV, JSON manifest, and Markdown report outputs only.",
            "05AL generated no JSONL, raw prompt, or raw response files.",
        ],
    }
    write_json(OUTPUT_FILES["manifest"], manifest)

    print(f"=== TASK {TASK_ID} COMPLETE ===")
    print(f"status: PASS")
    print(f"analysis_mode: {ANALYSIS_MODE}")
    print("api_calls_in_05al: 0")
    print("api_key_read_in_05al: False")
    print("raw_prompt_instances_written_in_05al: False")
    print("raw_responses_written_in_05al: False")
    print("jsonl_written_in_05al: False")
    print(f"output_dir: {OUT_DIR}")
    print("output_row_counts:")
    print(f"  key_findings: {len(key_findings)}")
    print(f"  stage_interpretation: {len(stage_interpretation)}")
    print(f"  condition_interpretation: {len(condition_interpretation)}")
    print(f"  parser_failure_interpretation: {len(failure_interpretation)}")
    print(f"  cascade_sequence_interpretation: {len(sequence_interpretation)}")
    print(f"  claim_boundary_review: {len(claim_boundary_review)}")
    print(f"  publication_readiness_notes: {len(publication_notes)}")
    print("created_files:")
    for name, path in OUTPUT_FILES.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
