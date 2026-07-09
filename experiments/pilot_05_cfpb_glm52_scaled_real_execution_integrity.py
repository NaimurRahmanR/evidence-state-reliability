from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

TASK = "05AO"
EXPECTED_CALLS = 720
ROOT = Path.cwd()
SRC_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution"
OUT_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution_integrity"
SCRIPT_PATH = ROOT / "experiments" / "pilot_05_cfpb_glm52_scaled_real_execution_integrity.py"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def sval(v: Any) -> str:
    return "" if v is None else str(v).strip()


def boolish_true(v: Any) -> bool:
    return sval(v).lower() in {"true", "1", "yes", "y"}


def boolish_false(v: Any) -> bool:
    return sval(v).lower() in {"false", "0", "no", "n"}


def counts(rows: Iterable[Dict[str, str]], col: str) -> Dict[str, int]:
    c = Counter(sval(r.get(col, "")) for r in rows)
    return dict(sorted(c.items(), key=lambda kv: kv[0]))


def group_counts(rows: Iterable[Dict[str, str]], cols: List[str]) -> List[Dict[str, Any]]:
    c: Counter = Counter(tuple(sval(r.get(col, "")) for col in cols) for r in rows)
    out: List[Dict[str, Any]] = []
    for key, n in sorted(c.items()):
        row = {col: key[i] for i, col in enumerate(cols)}
        row["count"] = n
        out.append(row)
    return out


def grouped_parser_summary(rows: List[Dict[str, str]], parser_col: str) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Dict[str, str]]] = defaultdict(list)
    for r in rows:
        groups[(sval(r.get("evidence_condition")), sval(r.get("stage")))] .append(r)
    out: List[Dict[str, Any]] = []
    for (condition, stage), rs in sorted(groups.items()):
        total = len(rs)
        valid = sum(1 for r in rs if boolish_true(r.get(parser_col)))
        invalid = sum(1 for r in rs if boolish_false(r.get(parser_col)))
        missing = total - valid - invalid
        out.append({
            "evidence_condition": condition,
            "stage": stage,
            "rows": total,
            "parser_valid_true": valid,
            "parser_valid_false": invalid,
            "parser_valid_missing_or_other": missing,
            "parser_valid_rate": round(valid / total, 6) if total else "",
            "parser_invalid_rate": round(invalid / total, 6) if total else "",
        })
    return out


def yes_no_rate_summary(rows: List[Dict[str, str]], metric_col: str) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Dict[str, str]]] = defaultdict(list)
    for r in rows:
        groups[(sval(r.get("evidence_condition")), sval(r.get("stage")))] .append(r)
    out: List[Dict[str, Any]] = []
    for (condition, stage), rs in sorted(groups.items()):
        available = [r for r in rs if sval(r.get(metric_col, ""))]
        true_n = sum(1 for r in available if boolish_true(r.get(metric_col)))
        false_n = sum(1 for r in available if boolish_false(r.get(metric_col)))
        other_n = len(available) - true_n - false_n
        out.append({
            "metric": metric_col,
            "evidence_condition": condition,
            "stage": stage,
            "available_rows": len(available),
            "true_count": true_n,
            "false_count": false_n,
            "other_count": other_n,
            "true_rate_among_available": round(true_n / len(available), 6) if available else "",
        })
    return out


def safe_float(v: Any) -> float:
    try:
        return float(sval(v) or 0.0)
    except Exception:
        return 0.0


def main() -> int:
    print("=== TASK 05AO: NO-CALL 05AN INTEGRITY RECONCILIATION ===")
    print("API/model calls: NO")
    print("API key read: NO")
    print(".env read: NO")
    print("Raw prompt/response writing: NO")
    print("JSONL writing: NO")
    print("Stages/commits/pushes: NO")

    if OUT_DIR.exists():
        raise RuntimeError(f"Refusing to overwrite existing output directory: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True)

    required = {
        "call_plan": SRC_DIR / "pilot_05AN_call_plan.csv",
        "ledger": SRC_DIR / "pilot_05AN_call_ledger.csv",
        "sanitized": SRC_DIR / "pilot_05AN_sanitized_execution_rows.csv",
        "parser_invalid": SRC_DIR / "pilot_05AN_parser_invalid_summary.csv",
        "execution_manifest": SRC_DIR / "pilot_05AN_execution_manifest.json",
        "call_plan_validation": SRC_DIR / "pilot_05AN_call_plan_validation.json",
    }
    for name, path in required.items():
        if not path.exists():
            raise RuntimeError(f"Missing required {name}: {path}")

    call_plan = read_csv(required["call_plan"])
    ledger = read_csv(required["ledger"])
    sanitized = read_csv(required["sanitized"])
    parser_invalid = read_csv(required["parser_invalid"])
    execution_manifest = read_json(required["execution_manifest"])
    call_plan_validation = read_json(required["call_plan_validation"])

    ledger_by_seq = {sval(r.get("sequence_id")): r for r in ledger}
    sanitized_by_seq = {sval(r.get("sequence_id")): r for r in sanitized}
    call_plan_by_seq = {sval(r.get("sequence_id")): r for r in call_plan}

    duplicate_ledger_sequence_ids = len(ledger) - len(ledger_by_seq)
    duplicate_sanitized_sequence_ids = len(sanitized) - len(sanitized_by_seq)
    duplicate_call_plan_sequence_ids = len(call_plan) - len(call_plan_by_seq)

    missing_sanitized_rows: List[Dict[str, Any]] = []
    for seq_id, r in sorted(ledger_by_seq.items(), key=lambda kv: int(sval(kv[1].get("sequence_index", "0")) or 0)):
        if seq_id not in sanitized_by_seq:
            missing_sanitized_rows.append({
                "sequence_index": r.get("sequence_index", ""),
                "sequence_id": seq_id,
                "base_case_id": r.get("base_case_id", ""),
                "evidence_condition": r.get("evidence_condition", ""),
                "stage": r.get("stage", ""),
                "call_attempted": r.get("call_attempted", ""),
                "call_succeeded": r.get("call_succeeded", ""),
                "parser_valid": r.get("parser_valid", ""),
                "error_category": r.get("error_category", ""),
                "input_tokens": r.get("input_tokens", ""),
                "output_tokens": r.get("output_tokens", ""),
                "estimated_cost_usd": r.get("estimated_cost_usd", ""),
                "reconciliation_note": "present_in_call_ledger_missing_from_sanitized_execution_rows",
            })

    sanitized_not_in_ledger = [
        {
            "sequence_index": r.get("sequence_index", ""),
            "sequence_id": seq_id,
            "base_case_id": r.get("base_case_id", ""),
            "evidence_condition": r.get("evidence_condition", ""),
            "stage": r.get("stage", ""),
            "parser_valid": r.get("parser_valid", ""),
            "reconciliation_note": "present_in_sanitized_execution_rows_missing_from_call_ledger",
        }
        for seq_id, r in sorted(sanitized_by_seq.items()) if seq_id not in ledger_by_seq
    ]

    call_plan_not_in_ledger = [
        {
            "sequence_index": r.get("sequence_index", ""),
            "sequence_id": seq_id,
            "base_case_id": r.get("base_case_id", ""),
            "evidence_condition": r.get("evidence_condition", ""),
            "stage": r.get("stage", ""),
            "reconciliation_note": "present_in_call_plan_missing_from_call_ledger",
        }
        for seq_id, r in sorted(call_plan_by_seq.items()) if seq_id not in ledger_by_seq
    ]

    ledger_parser_valid_true = sum(1 for r in ledger if boolish_true(r.get("parser_valid")))
    ledger_parser_valid_false = sum(1 for r in ledger if boolish_false(r.get("parser_valid")))
    persisted_parser_valid_true = sum(1 for r in sanitized if boolish_true(r.get("parser_valid")))
    persisted_parser_valid_false = sum(1 for r in sanitized if boolish_false(r.get("parser_valid")))
    ledger_call_succeeded_true = sum(1 for r in ledger if boolish_true(r.get("call_succeeded")))
    ledger_call_succeeded_false = sum(1 for r in ledger if boolish_false(r.get("call_succeeded")))
    ledger_call_attempted_true = sum(1 for r in ledger if boolish_true(r.get("call_attempted")))

    cumulative_cost = safe_float(execution_manifest.get("cumulative_estimated_cost_usd"))
    ledger_cost_sum = sum(safe_float(r.get("estimated_cost_usd")) for r in ledger)
    ledger_input_tokens = sum(int(safe_float(r.get("input_tokens"))) for r in ledger)
    ledger_output_tokens = sum(int(safe_float(r.get("output_tokens"))) for r in ledger)

    accounting_rows = [
        {"metric": "planned_call_count", "value": EXPECTED_CALLS},
        {"metric": "call_plan_rows", "value": len(call_plan)},
        {"metric": "call_ledger_rows", "value": len(ledger)},
        {"metric": "sanitized_execution_rows", "value": len(sanitized)},
        {"metric": "parser_invalid_summary_rows", "value": len(parser_invalid)},
        {"metric": "ledger_parser_valid_true", "value": ledger_parser_valid_true},
        {"metric": "ledger_parser_valid_false", "value": ledger_parser_valid_false},
        {"metric": "persisted_parser_valid_true", "value": persisted_parser_valid_true},
        {"metric": "persisted_parser_valid_false", "value": persisted_parser_valid_false},
        {"metric": "ledger_only_missing_sanitized_rows", "value": len(missing_sanitized_rows)},
        {"metric": "sanitized_not_in_ledger_rows", "value": len(sanitized_not_in_ledger)},
        {"metric": "call_plan_not_in_ledger_rows", "value": len(call_plan_not_in_ledger)},
        {"metric": "ledger_call_attempted_true", "value": ledger_call_attempted_true},
        {"metric": "ledger_call_succeeded_true", "value": ledger_call_succeeded_true},
        {"metric": "ledger_call_succeeded_false", "value": ledger_call_succeeded_false},
        {"metric": "duplicate_call_plan_sequence_ids", "value": duplicate_call_plan_sequence_ids},
        {"metric": "duplicate_ledger_sequence_ids", "value": duplicate_ledger_sequence_ids},
        {"metric": "duplicate_sanitized_sequence_ids", "value": duplicate_sanitized_sequence_ids},
        {"metric": "ledger_input_tokens", "value": ledger_input_tokens},
        {"metric": "ledger_output_tokens", "value": ledger_output_tokens},
        {"metric": "ledger_cost_sum_usd", "value": round(ledger_cost_sum, 8)},
        {"metric": "execution_manifest_cumulative_estimated_cost_usd", "value": cumulative_cost},
    ]

    write_csv(OUT_DIR / "pilot_05AO_call_accounting_summary.csv", accounting_rows, ["metric", "value"])
    write_csv(OUT_DIR / "pilot_05AO_ledger_missing_sanitized_rows.csv", missing_sanitized_rows, [
        "sequence_index", "sequence_id", "base_case_id", "evidence_condition", "stage",
        "call_attempted", "call_succeeded", "parser_valid", "error_category",
        "input_tokens", "output_tokens", "estimated_cost_usd", "reconciliation_note"
    ])
    write_csv(OUT_DIR / "pilot_05AO_sanitized_not_in_ledger_rows.csv", sanitized_not_in_ledger, [
        "sequence_index", "sequence_id", "base_case_id", "evidence_condition", "stage", "parser_valid", "reconciliation_note"
    ])
    write_csv(OUT_DIR / "pilot_05AO_call_plan_not_in_ledger_rows.csv", call_plan_not_in_ledger, [
        "sequence_index", "sequence_id", "base_case_id", "evidence_condition", "stage", "reconciliation_note"
    ])
    write_csv(OUT_DIR / "pilot_05AO_ledger_parser_by_condition_stage.csv", grouped_parser_summary(ledger, "parser_valid"), [
        "evidence_condition", "stage", "rows", "parser_valid_true", "parser_valid_false", "parser_valid_missing_or_other", "parser_valid_rate", "parser_invalid_rate"
    ])
    write_csv(OUT_DIR / "pilot_05AO_persisted_parser_by_condition_stage.csv", grouped_parser_summary(sanitized, "parser_valid"), [
        "evidence_condition", "stage", "rows", "parser_valid_true", "parser_valid_false", "parser_valid_missing_or_other", "parser_valid_rate", "parser_invalid_rate"
    ])
    write_csv(OUT_DIR / "pilot_05AO_failure_family_distribution.csv", group_counts(sanitized, ["evidence_condition", "stage", "primary_failure_family"]), [
        "evidence_condition", "stage", "primary_failure_family", "count"
    ])
    write_csv(OUT_DIR / "pilot_05AO_parser_invalid_by_condition_stage.csv", group_counts(parser_invalid, ["evidence_condition", "stage", "parser_error_category"]), [
        "evidence_condition", "stage", "parser_error_category", "count"
    ])

    metric_rows: List[Dict[str, Any]] = []
    for metric in [
        "evidence_state_adequate",
        "parser_contract_ack",
        "audit_detected_degradation",
        "audit_false_assurance",
        "escalation_recovery",
    ]:
        if sanitized and metric in sanitized[0]:
            metric_rows.extend(yes_no_rate_summary(sanitized, metric))
    write_csv(OUT_DIR / "pilot_05AO_stage_condition_metric_availability.csv", metric_rows, [
        "metric", "evidence_condition", "stage", "available_rows", "true_count", "false_count", "other_count", "true_rate_among_available"
    ])

    # Determine whether this is ready for the next no-call metrics step.
    critical_pass = (
        len(call_plan) == EXPECTED_CALLS
        and len(ledger) == EXPECTED_CALLS
        and duplicate_call_plan_sequence_ids == 0
        and duplicate_ledger_sequence_ids == 0
        and len(call_plan_not_in_ledger) == 0
        and len(sanitized_not_in_ledger) == 0
        and execution_manifest.get("raw_prompts_written") is False
        and execution_manifest.get("raw_responses_written") is False
        and execution_manifest.get("jsonl_written") is False
        and execution_manifest.get("raw_cfpb_data_touched") is False
    )
    ready_for_metrics = critical_pass and len(sanitized) > 0 and persisted_parser_valid_true > 0

    manifest = {
        "task": TASK,
        "status": "PASS" if critical_pass else "REVIEW_REQUIRED",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_policy": "sanitized 05AN execution outputs only; no raw prompts/responses; no jsonl; no raw CFPB data",
        "api_model_calls": 0,
        "api_key_read": False,
        "env_file_read": False,
        "raw_prompts_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "raw_cfpb_data_touched": False,
        "call_plan_rows": len(call_plan),
        "ledger_rows": len(ledger),
        "sanitized_execution_rows": len(sanitized),
        "parser_invalid_summary_rows": len(parser_invalid),
        "ledger_parser_valid_true": ledger_parser_valid_true,
        "ledger_parser_valid_false": ledger_parser_valid_false,
        "persisted_parser_valid_true": persisted_parser_valid_true,
        "persisted_parser_valid_false": persisted_parser_valid_false,
        "ledger_only_missing_sanitized_rows": len(missing_sanitized_rows),
        "sanitized_not_in_ledger_rows": len(sanitized_not_in_ledger),
        "call_plan_not_in_ledger_rows": len(call_plan_not_in_ledger),
        "ledger_call_attempted_true": ledger_call_attempted_true,
        "ledger_call_succeeded_true": ledger_call_succeeded_true,
        "ledger_call_succeeded_false": ledger_call_succeeded_false,
        "duplicate_call_plan_sequence_ids": duplicate_call_plan_sequence_ids,
        "duplicate_ledger_sequence_ids": duplicate_ledger_sequence_ids,
        "duplicate_sanitized_sequence_ids": duplicate_sanitized_sequence_ids,
        "ledger_input_tokens": ledger_input_tokens,
        "ledger_output_tokens": ledger_output_tokens,
        "ledger_cost_sum_usd": round(ledger_cost_sum, 8),
        "cumulative_estimated_cost_usd": cumulative_cost,
        "execution_manifest_status": execution_manifest.get("status"),
        "execution_manifest_run_id": execution_manifest.get("run_id"),
        "execution_manifest_model": execution_manifest.get("model"),
        "call_plan_validation_status": call_plan_validation.get("status"),
        "ready_for_05AP_metrics": bool(ready_for_metrics),
        "claim_boundary_status": "scaled real model evidence exists, but claims remain limited until metrics, paired deltas, uncertainty intervals, and claim-boundary report are generated",
        "important_reconciliation_note": "720 ledger rows exist, but sanitized persisted rows are fewer. Ledger-only missing sanitized rows must be treated explicitly as non-persisted/API/parse failures in downstream metrics rather than ignored.",
        "outputs": {
            "manifest_json": str((OUT_DIR / "pilot_05AO_integrity_manifest.json").relative_to(ROOT)),
            "call_accounting_summary_csv": str((OUT_DIR / "pilot_05AO_call_accounting_summary.csv").relative_to(ROOT)),
            "ledger_missing_sanitized_rows_csv": str((OUT_DIR / "pilot_05AO_ledger_missing_sanitized_rows.csv").relative_to(ROOT)),
            "sanitized_not_in_ledger_rows_csv": str((OUT_DIR / "pilot_05AO_sanitized_not_in_ledger_rows.csv").relative_to(ROOT)),
            "call_plan_not_in_ledger_rows_csv": str((OUT_DIR / "pilot_05AO_call_plan_not_in_ledger_rows.csv").relative_to(ROOT)),
            "ledger_parser_by_condition_stage_csv": str((OUT_DIR / "pilot_05AO_ledger_parser_by_condition_stage.csv").relative_to(ROOT)),
            "persisted_parser_by_condition_stage_csv": str((OUT_DIR / "pilot_05AO_persisted_parser_by_condition_stage.csv").relative_to(ROOT)),
            "failure_family_distribution_csv": str((OUT_DIR / "pilot_05AO_failure_family_distribution.csv").relative_to(ROOT)),
            "parser_invalid_by_condition_stage_csv": str((OUT_DIR / "pilot_05AO_parser_invalid_by_condition_stage.csv").relative_to(ROOT)),
            "stage_condition_metric_availability_csv": str((OUT_DIR / "pilot_05AO_stage_condition_metric_availability.csv").relative_to(ROOT)),
            "report_md": str((OUT_DIR / "pilot_05AO_integrity_reconciliation_report.md").relative_to(ROOT)),
        },
    }
    write_json(OUT_DIR / "pilot_05AO_integrity_manifest.json", manifest)

    report = f"""# Pilot 05AN Integrity Reconciliation Report

## Status

05AO status: **{manifest['status']}**  
Ready for 05AP metrics: **{manifest['ready_for_05AP_metrics']}**

This is a no-call reconciliation step over sanitized 05AN outputs only. It did not read API keys, did not read `.env`, did not write raw prompts, did not write raw responses, and did not create JSONL.

## Core accounting

| Item | Count |
|---|---:|
| Planned calls | {EXPECTED_CALLS} |
| Call plan rows | {len(call_plan)} |
| Call ledger rows | {len(ledger)} |
| Persisted sanitized execution rows | {len(sanitized)} |
| Parser-invalid summary rows | {len(parser_invalid)} |
| Ledger parser-valid rows | {ledger_parser_valid_true} |
| Ledger parser-invalid/false rows | {ledger_parser_valid_false} |
| Persisted parser-valid rows | {persisted_parser_valid_true} |
| Persisted parser-invalid rows | {persisted_parser_valid_false} |
| Ledger-only rows missing from sanitized execution rows | {len(missing_sanitized_rows)} |
| Cumulative estimated cost USD | {cumulative_cost} |

## Interpretation boundary

This is now scaled real GLM-5.2 execution evidence, but not yet a paper-ready result. The correct claim is that the scaled run produced a complete call ledger and a large sanitized persisted execution set suitable for no-call analysis. The seven ledger-only/non-persisted rows must be explicitly accounted for in downstream metrics.

Do **not** claim broad GLM reliability, broad LLM reliability, real-world financial validity, regulated-decision validity, or deployment safety.

## Next recommended task

**TASK 05AP: Scaled Pilot 05 cascade metrics and paired uncertainty analysis**

05AP should use the 05AN ledger plus persisted sanitized execution rows, treat ledger-only rows as accountable failures/missing persisted outputs, and generate parser validity, stage reliability, evidence-condition deltas, audit false assurance, escalation recovery/loss, cascade sequence metrics, and bootstrap/paired confidence intervals.
"""
    (OUT_DIR / "pilot_05AO_integrity_reconciliation_report.md").write_text(report, encoding="utf-8")

    print("=== 05AO SUMMARY ===")
    for k in [
        "status", "call_plan_rows", "ledger_rows", "sanitized_execution_rows",
        "parser_invalid_summary_rows", "ledger_parser_valid_true", "ledger_parser_valid_false",
        "persisted_parser_valid_true", "persisted_parser_valid_false",
        "ledger_only_missing_sanitized_rows", "cumulative_estimated_cost_usd",
        "ready_for_05AP_metrics"
    ]:
        print(f"{k}: {manifest[k]}")
    print("05AO outputs written:")
    for p in sorted(OUT_DIR.rglob("*")):
        if p.is_file():
            print(f"- {p.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
