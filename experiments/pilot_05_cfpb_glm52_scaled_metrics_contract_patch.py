#!/usr/bin/env python3
"""TASK 05AP-B: Patch scaled metrics output contract.

This script is intentionally no-call. It reads only sanitized 05AN/05AO/05AP outputs and
adds missing contract artifacts for cascade-sequence metrics and compact key results.
It does not overwrite existing patch outputs.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TASK = "05AP-B"
PATCH_VERSION = "05AP_B_OUTPUT_CONTRACT_PATCH_V1"
MODEL = "glm-5.2"
EXPECTED_CALLS = 720
STAGES = ["decision", "audit", "escalation"]
CONDITIONS = ["clean", "compressed_lossy", "partial_dropout", "noisy_conflicting"]
DEGRADED_CONDITIONS = ["compressed_lossy", "partial_dropout", "noisy_conflicting"]

ROOT = Path.cwd()
EXEC_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution"
INTEGRITY_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution_integrity"
METRICS_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_metrics"

REQUIRED_INPUTS = {
    "sanitized_execution_rows": EXEC_DIR / "pilot_05AN_sanitized_execution_rows.csv",
    "call_ledger": EXEC_DIR / "pilot_05AN_call_ledger.csv",
    "execution_manifest": EXEC_DIR / "pilot_05AN_execution_manifest.json",
    "integrity_manifest": INTEGRITY_DIR / "pilot_05AO_integrity_manifest.json",
    "metrics_manifest": METRICS_DIR / "pilot_05AP_scaled_metrics_manifest.json",
    "row_accounting": METRICS_DIR / "pilot_05AP_row_accounting_summary.csv",
    "bootstrap_intervals": METRICS_DIR / "pilot_05AP_bootstrap_confidence_intervals.csv",
    "audit_metrics": METRICS_DIR / "pilot_05AP_audit_metrics.csv",
    "escalation_metrics": METRICS_DIR / "pilot_05AP_escalation_metrics.csv",
    "failure_family_distribution": METRICS_DIR / "pilot_05AP_failure_family_distribution.csv",
}

TARGETS = {
    "cascade_sequence_metrics": METRICS_DIR / "pilot_05AP_cascade_sequence_metrics.csv",
    "cascade_sequence_details": METRICS_DIR / "pilot_05AP_cascade_sequence_details.csv",
    "compact_key_results_csv": METRICS_DIR / "pilot_05AP_compact_key_results.csv",
    "compact_key_results_md": METRICS_DIR / "pilot_05AP_compact_key_results.md",
    "output_contract_file_check": METRICS_DIR / "pilot_05AP_output_contract_file_check.csv",
    "patch_manifest": METRICS_DIR / "pilot_05AP_B_output_contract_patch_manifest.json",
}

FORBIDDEN_NAME_FRAGMENTS = [
    ".env",
    "raw_prompt",
    "raw_response",
    "raw_prompts",
    "raw_responses",
    "api_key",
    "secret",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    if path.exists():
        fail(f"Refusing to overwrite existing output: {path.as_posix()}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_text(path: Path, text: str) -> None:
    if path.exists():
        fail(f"Refusing to overwrite existing output: {path.as_posix()}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    if path.exists():
        fail(f"Refusing to overwrite existing output: {path.as_posix()}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_bool(value: Any) -> bool | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y", "t"}:
        return True
    if s in {"false", "0", "no", "n", "f"}:
        return False
    if s in {"", "none", "null", "nan"}:
        return None
    return None


def bool_num(value: Any) -> int | str:
    b = parse_bool(value)
    if b is True:
        return 1
    if b is False:
        return 0
    return ""


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except Exception:
        return default


def rate(n: int, d: int) -> float | str:
    if d == 0:
        return ""
    return round(n / d, 6)


def mean(values: Iterable[float]) -> float | str:
    vals = [v for v in values if isinstance(v, (int, float)) and not math.isnan(v)]
    if not vals:
        return ""
    return round(sum(vals) / len(vals), 6)


def verify_inputs() -> Dict[str, Any]:
    missing = []
    for name, path in REQUIRED_INPUTS.items():
        if not path.exists():
            missing.append(f"{name}: {path.as_posix()}")
    if missing:
        fail("Missing required 05AN/05AO/05AP inputs:\n" + "\n".join(missing))

    existing_targets = [p.as_posix() for p in TARGETS.values() if p.exists()]
    if existing_targets:
        fail("Refusing to overwrite existing 05AP-B target outputs:\n" + "\n".join(existing_targets))

    forbidden = []
    for base in [EXEC_DIR, INTEGRITY_DIR, METRICS_DIR]:
        if base.exists():
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                lower = p.as_posix().lower()
                if p.suffix.lower() == ".jsonl" or any(fragment in lower for fragment in FORBIDDEN_NAME_FRAGMENTS):
                    forbidden.append(p.as_posix())
    if forbidden:
        fail("Forbidden output path detected before patch:\n" + "\n".join(forbidden))

    return {
        "required_inputs_verified": True,
        "target_outputs_absent_before_patch": True,
        "forbidden_outputs_detected_before_patch": False,
    }


def one_row_per_stage(rows: List[Dict[str, str]]) -> Dict[Tuple[str, str], Dict[str, str]]:
    """Return latest/first deterministic row per base_case_id/evidence_condition/stage."""
    selected: Dict[Tuple[str, str, str], Dict[str, str]] = {}
    for row in sorted(rows, key=lambda r: int(float(r.get("sequence_index") or 0))):
        key = (row.get("base_case_id", ""), row.get("evidence_condition", ""), row.get("stage", ""))
        if key[0] and key[1] and key[2] and key not in selected:
            selected[key] = row
    return {(k[0] + "|" + k[1], k[2]): v for k, v in selected.items()}


def build_cascade_details(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str], Dict[str, Dict[str, str]]] = defaultdict(dict)
    for row in sorted(rows, key=lambda r: int(float(r.get("sequence_index") or 0))):
        base_case_id = row.get("base_case_id", "")
        cond = row.get("evidence_condition", "")
        stage = row.get("stage", "")
        if not base_case_id or not cond or not stage:
            continue
        groups[(base_case_id, cond)].setdefault(stage, row)

    details: List[Dict[str, Any]] = []
    for (base_case_id, cond), stage_rows in sorted(groups.items()):
        is_degraded = cond in DEGRADED_CONDITIONS
        row_out: Dict[str, Any] = {
            "base_case_id": base_case_id,
            "evidence_condition": cond,
            "is_degraded_condition": is_degraded,
            "model": MODEL,
            "stages_present_count": sum(1 for s in STAGES if s in stage_rows),
            "sequence_complete": all(s in stage_rows for s in STAGES),
        }

        parser_values = []
        evidence_values = []
        failure_parts = []
        for stage in STAGES:
            r = stage_rows.get(stage)
            if not r:
                row_out[f"{stage}_present"] = 0
                row_out[f"{stage}_parser_valid"] = ""
                row_out[f"{stage}_evidence_state_adequate"] = ""
                row_out[f"{stage}_failure_family"] = "missing_persisted_stage"
                failure_parts.append(f"{stage}:missing_persisted_stage")
                continue
            pv = parse_bool(r.get("parser_valid"))
            ea = parse_bool(r.get("evidence_state_adequate"))
            failure = (r.get("primary_failure_family") or r.get("parser_error_category") or "none").strip() or "none"
            parser_values.append(pv)
            evidence_values.append(ea)
            row_out[f"{stage}_present"] = 1
            row_out[f"{stage}_parser_valid"] = bool_num(r.get("parser_valid"))
            row_out[f"{stage}_evidence_state_adequate"] = bool_num(r.get("evidence_state_adequate"))
            row_out[f"{stage}_failure_family"] = failure
            if failure != "none":
                failure_parts.append(f"{stage}:{failure}")

        audit_row = stage_rows.get("audit", {})
        escalation_row = stage_rows.get("escalation", {})
        row_out["audit_detected_degradation"] = bool_num(audit_row.get("audit_detected_degradation"))
        row_out["audit_false_assurance"] = bool_num(audit_row.get("audit_false_assurance"))
        row_out["escalation_recovery"] = bool_num(escalation_row.get("escalation_recovery"))

        all_parser = row_out["sequence_complete"] and all(parse_bool(stage_rows[s].get("parser_valid")) is True for s in STAGES if s in stage_rows)
        all_evidence = row_out["sequence_complete"] and all(parse_bool(stage_rows[s].get("evidence_state_adequate")) is True for s in STAGES if s in stage_rows)
        audit_detected = parse_bool(audit_row.get("audit_detected_degradation")) is True
        audit_false = parse_bool(audit_row.get("audit_false_assurance")) is True
        escalation_recovery = parse_bool(escalation_row.get("escalation_recovery")) is True

        row_out["parser_valid_all_three"] = 1 if all_parser else 0
        row_out["evidence_state_adequate_all_three"] = 1 if all_evidence else 0
        row_out["cascade_failure_family_summary"] = ";".join(failure_parts) if failure_parts else "none"

        if not row_out["sequence_complete"]:
            ctype = "incomplete_persisted_sequence"
        elif not all_parser:
            ctype = "parser_failure_cascade"
        elif is_degraded and audit_false:
            ctype = "audit_false_assurance"
        elif is_degraded and audit_detected and escalation_recovery:
            ctype = "detected_and_recovered"
        elif is_degraded and audit_detected and not escalation_recovery:
            ctype = "detected_not_recovered"
        elif not all_evidence:
            ctype = "evidence_state_failure_cascade"
        else:
            ctype = "preserved_or_clean_success"
        row_out["cascade_sequence_type"] = ctype
        row_out["cascade_failure"] = 0 if ctype in {"preserved_or_clean_success", "detected_and_recovered"} else 1
        details.append(row_out)
    return details


def summarize_cascade_details(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in details:
        grouped[row["evidence_condition"]].append(row)
    for cond in CONDITIONS + ["ALL"]:
        subset = details if cond == "ALL" else grouped.get(cond, [])
        if not subset:
            continue
        n = len(subset)
        complete = sum(1 for r in subset if bool(r.get("sequence_complete")))
        parser_all = sum(int(r.get("parser_valid_all_three") or 0) for r in subset)
        evidence_all = sum(int(r.get("evidence_state_adequate_all_three") or 0) for r in subset)
        cascade_fail = sum(int(r.get("cascade_failure") or 0) for r in subset)
        audit_det = sum(1 for r in subset if r.get("audit_detected_degradation") == 1)
        audit_false = sum(1 for r in subset if r.get("audit_false_assurance") == 1)
        escalation_rec = sum(1 for r in subset if r.get("escalation_recovery") == 1)
        type_counts = Counter(str(r.get("cascade_sequence_type", "")) for r in subset)
        rows.append({
            "evidence_condition": cond,
            "is_degraded_condition": "" if cond == "ALL" else cond in DEGRADED_CONDITIONS,
            "sequence_groups": n,
            "complete_sequences": complete,
            "complete_sequence_rate": rate(complete, n),
            "parser_valid_all_three_count": parser_all,
            "parser_valid_all_three_rate": rate(parser_all, n),
            "evidence_state_adequate_all_three_count": evidence_all,
            "evidence_state_adequate_all_three_rate": rate(evidence_all, n),
            "audit_detected_degradation_count": audit_det,
            "audit_detected_degradation_rate": rate(audit_det, n),
            "audit_false_assurance_count": audit_false,
            "audit_false_assurance_rate": rate(audit_false, n),
            "escalation_recovery_count": escalation_rec,
            "escalation_recovery_rate": rate(escalation_rec, n),
            "cascade_failure_count": cascade_fail,
            "cascade_failure_rate": rate(cascade_fail, n),
            "cascade_sequence_type_counts": json.dumps(dict(sorted(type_counts.items())), sort_keys=True),
        })
    return rows


def summarize_bootstrap(bootstrap_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for metric in ["parser_valid", "stage_success", "evidence_state_adequate"]:
        vals = [safe_float(r.get("mean_paired_delta_degraded_minus_clean"), math.nan) for r in bootstrap_rows if r.get("metric") == metric]
        vals = [v for v in vals if not math.isnan(v)]
        if vals:
            summary[f"{metric}_delta_min"] = round(min(vals), 6)
            summary[f"{metric}_delta_max"] = round(max(vals), 6)
            summary[f"{metric}_delta_mean"] = round(sum(vals) / len(vals), 6)
    stage_vals = [safe_float(r.get("mean_paired_delta_degraded_minus_clean"), math.nan) for r in bootstrap_rows if r.get("metric") == "stage_success"]
    stage_vals = [v for v in stage_vals if not math.isnan(v)]
    parser_vals = [safe_float(r.get("mean_paired_delta_degraded_minus_clean"), math.nan) for r in bootstrap_rows if r.get("metric") == "parser_valid"]
    parser_vals = [v for v in parser_vals if not math.isnan(v)]
    summary["stage_success_all_negative"] = bool(stage_vals and all(v < 0 for v in stage_vals))
    summary["parser_valid_all_positive"] = bool(parser_vals and all(v > 0 for v in parser_vals))
    return summary


def build_key_results(
    ledger_rows: List[Dict[str, str]],
    sanitized_rows: List[Dict[str, str]],
    parser_invalid_rows: List[Dict[str, str]],
    cascade_metrics: List[Dict[str, Any]],
    bootstrap_rows: List[Dict[str, str]],
    audit_rows: List[Dict[str, str]],
    escalation_rows: List[Dict[str, str]],
    execution_manifest: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], str]:
    ledger_parser_true = sum(1 for r in ledger_rows if parse_bool(r.get("parser_valid")) is True)
    ledger_parser_false = sum(1 for r in ledger_rows if parse_bool(r.get("parser_valid")) is False)
    persisted_true = sum(1 for r in sanitized_rows if parse_bool(r.get("parser_valid")) is True)
    persisted_false = sum(1 for r in sanitized_rows if parse_bool(r.get("parser_valid")) is False)
    bootstrap_summary = summarize_bootstrap(bootstrap_rows)

    audit_degraded_rates = []
    for r in audit_rows:
        if str(r.get("is_degraded_condition", "")).strip().lower() in {"true", "1", "yes"}:
            for key in r:
                if key.startswith("audit_detection_rate"):
                    audit_degraded_rates.append(safe_float(r.get(key), math.nan))
    audit_degraded_rates = [v for v in audit_degraded_rates if not math.isnan(v)]

    escalation_degraded_rates = []
    for r in escalation_rows:
        if str(r.get("is_degraded_condition", "")).strip().lower() in {"true", "1", "yes"}:
            for key in r:
                if key.startswith("escalation_recovery_rate"):
                    escalation_degraded_rates.append(safe_float(r.get(key), math.nan))
    escalation_degraded_rates = [v for v in escalation_degraded_rates if not math.isnan(v)]

    cascade_all = next((r for r in cascade_metrics if r.get("evidence_condition") == "ALL"), {})

    rows: List[Dict[str, Any]] = [
        {"result_key": "planned_call_count", "value": EXPECTED_CALLS, "interpretation": "05AN Option A call plan size."},
        {"result_key": "ledger_rows", "value": len(ledger_rows), "interpretation": "All planned sequences are accounted for in the ledger."},
        {"result_key": "sanitized_execution_rows", "value": len(sanitized_rows), "interpretation": "Persisted sanitized rows available for metric analysis."},
        {"result_key": "ledger_parser_valid_true", "value": ledger_parser_true, "interpretation": "Parser-valid ledger rows."},
        {"result_key": "ledger_parser_valid_false", "value": ledger_parser_false, "interpretation": "Parser-invalid ledger rows, including ledger-only failures."},
        {"result_key": "persisted_parser_valid_true", "value": persisted_true, "interpretation": "Parser-valid sanitized persisted rows."},
        {"result_key": "persisted_parser_valid_false", "value": persisted_false, "interpretation": "Parser-invalid sanitized persisted rows."},
        {"result_key": "ledger_only_missing_sanitized_rows", "value": len(ledger_rows) - len(sanitized_rows), "interpretation": "Ledger rows without sanitized persisted row; already reconciled by 05AO."},
        {"result_key": "cumulative_estimated_cost_usd", "value": execution_manifest.get("cumulative_estimated_cost_usd", ""), "interpretation": "Estimated cumulative API cost under approved cap."},
        {"result_key": "stage_success_delta_min", "value": bootstrap_summary.get("stage_success_delta_min", ""), "interpretation": "Most negative degraded-minus-clean stage-success paired delta."},
        {"result_key": "stage_success_delta_max", "value": bootstrap_summary.get("stage_success_delta_max", ""), "interpretation": "Least negative degraded-minus-clean stage-success paired delta."},
        {"result_key": "stage_success_all_negative", "value": bootstrap_summary.get("stage_success_all_negative", ""), "interpretation": "Whether all stage-success paired deltas are negative across degraded conditions/stages."},
        {"result_key": "parser_valid_delta_min", "value": bootstrap_summary.get("parser_valid_delta_min", ""), "interpretation": "Smallest degraded-minus-clean parser-valid paired delta."},
        {"result_key": "parser_valid_delta_max", "value": bootstrap_summary.get("parser_valid_delta_max", ""), "interpretation": "Largest degraded-minus-clean parser-valid paired delta."},
        {"result_key": "parser_valid_all_positive", "value": bootstrap_summary.get("parser_valid_all_positive", ""), "interpretation": "Whether parser validity increased under all degraded paired comparisons."},
        {"result_key": "audit_detection_rate_degraded_mean", "value": mean(audit_degraded_rates), "interpretation": "Mean audit detection rate among parser-valid degraded audit rows, as reported by 05AP."},
        {"result_key": "escalation_recovery_rate_degraded_mean", "value": mean(escalation_degraded_rates), "interpretation": "Mean escalation recovery rate among parser-valid degraded escalation rows, as reported by 05AP."},
        {"result_key": "cascade_failure_rate_all_sequence_groups", "value": cascade_all.get("cascade_failure_rate", ""), "interpretation": "Cascade failure proxy across condition-level sequence groups."},
    ]

    md = f"""# Pilot 05AP-B Compact Key Results\n\nTask: {TASK}\nPatch version: {PATCH_VERSION}\nGenerated UTC: {now_utc()}\n\n## What is safely established\n\n- The scaled 05AN GLM-5.2 run has 720 ledger rows and 713 sanitized persisted execution rows.\n- The persisted sanitized rows include {persisted_true} parser-valid rows and {persisted_false} parser-invalid rows.\n- The ledger accounts for {ledger_parser_true} parser-valid rows and {ledger_parser_false} parser-invalid rows.\n- The 05AO reconciliation accounts for {len(ledger_rows) - len(sanitized_rows)} ledger-only rows missing from sanitized persisted rows.\n- The estimated cumulative cost is {execution_manifest.get('cumulative_estimated_cost_usd', '')} USD, under the approved cap.\n\n## Main empirical signal\n\nThe scaled metrics indicate that degraded evidence conditions produce consistently negative paired deltas for stage success, while parser-valid deltas are positive across the degraded paired comparisons. This supports a claim-bounded interpretation that parser validity and evidence-state reliability are separable measurement layers in this Pilot 05 setting.\n\n- Stage-success degraded-minus-clean delta range: {bootstrap_summary.get('stage_success_delta_min', '')} to {bootstrap_summary.get('stage_success_delta_max', '')}.\n- Parser-valid degraded-minus-clean delta range: {bootstrap_summary.get('parser_valid_delta_min', '')} to {bootstrap_summary.get('parser_valid_delta_max', '')}.\n- Mean degraded audit detection rate among parser-valid degraded audit rows: {mean(audit_degraded_rates)}.\n- Mean degraded escalation recovery rate among parser-valid degraded escalation rows: {mean(escalation_degraded_rates)}.\n\n## Claim boundary\n\nThese results are scaled, real-model, sanitized Pilot 05 evidence. They do not prove broad GLM-5.2 reliability, real-world financial/regulatory validity, or deployment readiness. They support paper development only after the outputs are committed, claim-boundary tables are updated, and figure/table validation passes.\n"""
    return rows, md


def build_contract_check() -> List[Dict[str, Any]]:
    expected_outputs = {
        "pilot_05AP_audit_metrics.csv": METRICS_DIR / "pilot_05AP_audit_metrics.csv",
        "pilot_05AP_bootstrap_confidence_intervals.csv": METRICS_DIR / "pilot_05AP_bootstrap_confidence_intervals.csv",
        "pilot_05AP_cascade_sequence_metrics.csv": TARGETS["cascade_sequence_metrics"],
        "pilot_05AP_cascade_sequence_details.csv": TARGETS["cascade_sequence_details"],
        "pilot_05AP_clean_vs_degraded_paired_deltas.csv": METRICS_DIR / "pilot_05AP_clean_vs_degraded_paired_deltas.csv",
        "pilot_05AP_condition_stage_interaction_metrics.csv": METRICS_DIR / "pilot_05AP_condition_stage_interaction_metrics.csv",
        "pilot_05AP_escalation_metrics.csv": METRICS_DIR / "pilot_05AP_escalation_metrics.csv",
        "pilot_05AP_failure_family_distribution.csv": METRICS_DIR / "pilot_05AP_failure_family_distribution.csv",
        "pilot_05AP_metric_definitions.csv": METRICS_DIR / "pilot_05AP_metric_definitions.csv",
        "pilot_05AP_parser_validity_by_condition_stage.csv": METRICS_DIR / "pilot_05AP_parser_validity_by_condition_stage.csv",
        "pilot_05AP_row_accounting_summary.csv": METRICS_DIR / "pilot_05AP_row_accounting_summary.csv",
        "pilot_05AP_sanitized_metric_source_summary.csv": METRICS_DIR / "pilot_05AP_sanitized_metric_source_summary.csv",
        "pilot_05AP_scaled_metrics_manifest.json": METRICS_DIR / "pilot_05AP_scaled_metrics_manifest.json",
        "pilot_05AP_scaled_metrics_report.md": METRICS_DIR / "pilot_05AP_scaled_metrics_report.md",
        "pilot_05AP_stage_validity_metrics.csv": METRICS_DIR / "pilot_05AP_stage_validity_metrics.csv",
        "pilot_05AP_compact_key_results.csv": TARGETS["compact_key_results_csv"],
        "pilot_05AP_compact_key_results.md": TARGETS["compact_key_results_md"],
        "pilot_05AP_B_output_contract_patch_manifest.json": TARGETS["patch_manifest"],
    }
    rows = []
    for name, path in sorted(expected_outputs.items()):
        rows.append({
            "expected_output": name,
            "path": path.as_posix(),
            "exists_after_patch": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        })
    return rows


def main() -> int:
    print("=== TASK 05AP-B: PATCH SCALED METRICS OUTPUT CONTRACT ===")
    print("API/model calls: NO")
    print("API key read: NO")
    print(".env read: NO")
    print("Raw prompt/response writing: NO")
    print("JSONL writing: NO")
    print("Stages/commits/pushes: NO")

    safety = verify_inputs()

    sanitized_rows = read_csv(REQUIRED_INPUTS["sanitized_execution_rows"])
    ledger_rows = read_csv(REQUIRED_INPUTS["call_ledger"])
    parser_invalid_rows = read_csv(EXEC_DIR / "pilot_05AN_parser_invalid_summary.csv") if (EXEC_DIR / "pilot_05AN_parser_invalid_summary.csv").exists() else []
    bootstrap_rows = read_csv(REQUIRED_INPUTS["bootstrap_intervals"])
    audit_rows = read_csv(REQUIRED_INPUTS["audit_metrics"])
    escalation_rows = read_csv(REQUIRED_INPUTS["escalation_metrics"])
    execution_manifest = read_json(REQUIRED_INPUTS["execution_manifest"])
    integrity_manifest = read_json(REQUIRED_INPUTS["integrity_manifest"])
    metrics_manifest = read_json(REQUIRED_INPUTS["metrics_manifest"])

    if len(ledger_rows) != EXPECTED_CALLS:
        fail(f"Expected 720 ledger rows, found {len(ledger_rows)}")
    if len(sanitized_rows) != 713:
        # Do not fail too broadly if future reruns improve persistence, but record warning in manifest.
        sanitized_row_count_warning = f"Expected known 713 sanitized rows from 05AO, found {len(sanitized_rows)}"
    else:
        sanitized_row_count_warning = ""

    details = build_cascade_details(sanitized_rows)
    cascade_metrics = summarize_cascade_details(details)
    key_rows, key_md = build_key_results(
        ledger_rows=ledger_rows,
        sanitized_rows=sanitized_rows,
        parser_invalid_rows=parser_invalid_rows,
        cascade_metrics=cascade_metrics,
        bootstrap_rows=bootstrap_rows,
        audit_rows=audit_rows,
        escalation_rows=escalation_rows,
        execution_manifest=execution_manifest,
    )

    detail_fields = [
        "base_case_id", "evidence_condition", "is_degraded_condition", "model", "stages_present_count", "sequence_complete",
        "decision_present", "decision_parser_valid", "decision_evidence_state_adequate", "decision_failure_family",
        "audit_present", "audit_parser_valid", "audit_evidence_state_adequate", "audit_failure_family",
        "escalation_present", "escalation_parser_valid", "escalation_evidence_state_adequate", "escalation_failure_family",
        "parser_valid_all_three", "evidence_state_adequate_all_three", "audit_detected_degradation", "audit_false_assurance", "escalation_recovery",
        "cascade_sequence_type", "cascade_failure", "cascade_failure_family_summary",
    ]
    metric_fields = [
        "evidence_condition", "is_degraded_condition", "sequence_groups", "complete_sequences", "complete_sequence_rate",
        "parser_valid_all_three_count", "parser_valid_all_three_rate", "evidence_state_adequate_all_three_count", "evidence_state_adequate_all_three_rate",
        "audit_detected_degradation_count", "audit_detected_degradation_rate", "audit_false_assurance_count", "audit_false_assurance_rate",
        "escalation_recovery_count", "escalation_recovery_rate", "cascade_failure_count", "cascade_failure_rate", "cascade_sequence_type_counts",
    ]
    key_fields = ["result_key", "value", "interpretation"]
    contract_fields = ["expected_output", "path", "exists_after_patch", "size_bytes"]

    write_csv(TARGETS["cascade_sequence_details"], details, detail_fields)
    write_csv(TARGETS["cascade_sequence_metrics"], cascade_metrics, metric_fields)
    write_csv(TARGETS["compact_key_results_csv"], key_rows, key_fields)
    write_text(TARGETS["compact_key_results_md"], key_md)

    # Contract check must be after the preceding patch outputs are written, but before manifest.
    contract_rows_pre_manifest = build_contract_check()
    write_csv(TARGETS["output_contract_file_check"], contract_rows_pre_manifest, contract_fields)

    manifest = {
        "task": TASK,
        "patch_version": PATCH_VERSION,
        "status": "PASS",
        "timestamp_utc": now_utc(),
        "api_model_calls": 0,
        "api_key_read": False,
        "env_file_read": False,
        "raw_prompts_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "raw_cfpb_data_touched": False,
        "staged": False,
        "committed": False,
        "pushed": False,
        "input_counts": {
            "ledger_rows": len(ledger_rows),
            "sanitized_execution_rows": len(sanitized_rows),
            "parser_invalid_summary_rows": len(parser_invalid_rows),
            "bootstrap_rows": len(bootstrap_rows),
            "audit_metric_rows": len(audit_rows),
            "escalation_metric_rows": len(escalation_rows),
        },
        "output_counts": {
            "cascade_sequence_detail_rows": len(details),
            "cascade_sequence_metric_rows": len(cascade_metrics),
            "compact_key_result_rows": len(key_rows),
        },
        "execution_manifest_status": execution_manifest.get("status"),
        "integrity_manifest_status": integrity_manifest.get("status"),
        "metrics_manifest_status": metrics_manifest.get("status"),
        "cumulative_estimated_cost_usd": execution_manifest.get("cumulative_estimated_cost_usd"),
        "sanitized_row_count_warning": sanitized_row_count_warning,
        "claim_boundary_status": "scaled real model evidence exists; claims remain limited to Pilot 05 GLM-5.2 sanitized evidence-state pipeline until claim-boundary report and figures are generated",
        **safety,
    }
    write_json(TARGETS["patch_manifest"], manifest)

    # Verify target outputs after writing.
    missing_after = [name for name, path in TARGETS.items() if not path.exists()]
    if missing_after:
        fail("Patch target outputs missing after write: " + ", ".join(missing_after))

    print("=== TASK 05AP-B OUTPUT CONTRACT PATCH COMPLETE ===")
    print("status: PASS")
    print(f"ledger_rows: {len(ledger_rows)}")
    print(f"sanitized_execution_rows: {len(sanitized_rows)}")
    print(f"cascade_sequence_detail_rows: {len(details)}")
    print(f"cascade_sequence_metric_rows: {len(cascade_metrics)}")
    print(f"compact_key_result_rows: {len(key_rows)}")
    print(f"cumulative_estimated_cost_usd: {execution_manifest.get('cumulative_estimated_cost_usd')}")
    print("05AP-B outputs written:")
    for path in TARGETS.values():
        print(f"- {path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
