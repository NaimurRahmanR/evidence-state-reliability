
#!/usr/bin/env python3
"""Task 05AK: Analyze GLM-5.2 execution results into reliability cascade metrics.

No API calls. No API key reads. Sanitized committed outputs only.
"""
from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TASK_ID = "05AK"
ROOT = Path(__file__).resolve().parents[1]
EXEC_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_execution_recovery_v4"
FINAL_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_execution_finalization_v5"
RUNNER_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_runner_build"
OUT_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_reliability_cascade_metrics"

SANITIZED = EXEC_DIR / "pilot_05_cfpb_glm52_micro_pilot_sanitized_outputs.csv"
PARSER = EXEC_DIR / "pilot_05_cfpb_glm52_micro_pilot_parser_status.csv"
PRIOR = EXEC_DIR / "pilot_05_cfpb_glm52_micro_pilot_prior_attempt_summary.csv"
USAGE = EXEC_DIR / "pilot_05_cfpb_glm52_micro_pilot_usage_summary.csv"
STAGE_SUMMARY = EXEC_DIR / "pilot_05_cfpb_glm52_micro_pilot_stage_summary.csv"
CONDITION_STAGE_SUMMARY = EXEC_DIR / "pilot_05_cfpb_glm52_micro_pilot_condition_stage_summary.csv"
EXEC_MANIFEST = EXEC_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_manifest.json"
FINAL_MANIFEST = FINAL_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_finalization_manifest.json"
CALL_ACCOUNTING = FINAL_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_call_accounting.csv"
RUNNER_PLAN = RUNNER_DIR / "pilot_05_cfpb_glm52_micro_pilot_runner_execution_plan.csv"


def fail(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        fail(f"Missing CSV input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        fail(f"Missing JSON input: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: List[str] = []
        seen = set()
        for row in rows:
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        fieldnames = keys or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def boolish(value: Any) -> Optional[bool]:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y", "valid", "pass", "passed"}:
        return True
    if s in {"false", "0", "no", "n", "invalid", "fail", "failed"}:
        return False
    return None


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip().replace("£", "").replace("$", "").replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def to_int(value: Any) -> Optional[int]:
    x = to_float(value)
    if x is None:
        return None
    try:
        return int(round(x))
    except Exception:
        return None


def first_present(row: Dict[str, Any], candidates: Iterable[str], default: str = "UNKNOWN") -> str:
    lower_map = {k.lower(): k for k in row.keys()}
    for cand in candidates:
        k = lower_map.get(cand.lower())
        if k is not None:
            val = row.get(k)
            if val is not None and str(val).strip() != "":
                return str(val).strip()
    return default


def get_field(row: Dict[str, Any], candidates: Iterable[str]) -> Optional[str]:
    lower_map = {k.lower(): k for k in row.keys()}
    for cand in candidates:
        k = lower_map.get(cand.lower())
        if k is not None:
            val = row.get(k)
            if val is not None and str(val).strip() != "":
                return str(val).strip()
    return None


def detect_parse_valid(row: Dict[str, Any]) -> Optional[bool]:
    # V3: include the concrete V4 column name (`parsed_json_valid`) and parser-prefixed
    # fields created during the sanitized/parser merge. V2 missed these and reported
    # 33 parser-status rows but zero valid/invalid counts.
    candidates = [
        "parsed_json_valid", "parser_parsed_json_valid",
        "parse_valid", "parser_parse_valid",
        "parser_valid", "parser_parser_valid",
        "valid_parse", "parser_valid_parse",
        "schema_valid", "parser_schema_valid",
        "response_valid", "parser_response_valid",
        "parsed_successfully", "parser_parsed_successfully",
        "is_valid", "parser_is_valid",
        "valid", "parser_valid",
    ]
    for cand in candidates:
        val = get_field(row, [cand])
        b = boolish(val)
        if b is not None:
            return b

    status = first_present(
        row,
        [
            "parser_status", "parser_parser_status",
            "parse_status", "parser_parse_status",
            "status", "parser_status_text",
            "parse_method", "parser_parse_method",
            "parser_error_family", "parser_parser_error_family",
        ],
        "",
    )
    if status:
        b = boolish(status)
        if b is not None:
            return b
        s = status.lower()
        if any(tok in s for tok in ["invalid", "fail", "error", "missing", "schema_uncertainty", "missing_message_content", "not_json"]):
            return False
        # Avoid classifying strings like "invalid" as valid just because they contain "valid".
        if any(tok in s for tok in ["valid_parse", "valid_json", "pass", "parsed"]):
            return True
    return None


def infer_stage(row: Dict[str, Any], fallback_index: int) -> str:
    stage = first_present(row, ["stage", "pipeline_stage", "cascade_stage", "task_stage"], "")
    if stage:
        s = stage.lower()
        if "decision" in s:
            return "decision"
        if "audit" in s:
            return "audit"
        if "escal" in s:
            return "escalation"
        return stage
    return ["decision", "audit", "escalation"][(fallback_index - 1) % 3]


def infer_condition(row: Dict[str, Any]) -> str:
    return first_present(
        row,
        [
            "evidence_condition", "condition", "condition_id", "evidence_state_condition",
            "evidence_condition_id", "condition_label", "evidence_state"
        ],
        "UNKNOWN_CONDITION",
    )


def infer_call_number(row: Dict[str, Any], fallback: int) -> int:
    val = get_field(row, [
        "call_number", "call_index", "approved_call_index", "execution_call_index", "abstract_call_index",
        "sequence_number", "run_call_number"
    ])
    parsed = to_int(val)
    if parsed is not None:
        return parsed
    return fallback


def infer_case_id(row: Dict[str, Any], call_number: int) -> str:
    val = first_present(
        row,
        [
            "case_id", "chain_id", "packet_id", "evidence_packet_id", "complaint_id_hash",
            "sanitized_packet_id", "scenario_id", "task_id"
        ],
        "",
    )
    if val:
        return val
    return f"call_group_{math.ceil(call_number / 3):02d}"


def infer_failure_family(row: Dict[str, Any], parse_valid: Optional[bool]) -> str:
    if parse_valid is True:
        return "valid_parse"
    explicit = first_present(
        row,
        [
            "failure_family", "parser_failure_family", "parse_failure_family", "error_family",
            "failure_type", "sanitized_failure_family", "response_status_family"
        ],
        "",
    )
    if explicit:
        return explicit
    status_text = " ".join(str(v) for k, v in row.items() if v is not None and k.lower() in {
        "parser_status", "parse_status", "status", "error", "sanitized_error", "response_status"
    }).lower()
    if "missing" in status_text and "content" in status_text:
        return "schema_uncertainty_missing_message_content"
    if "schema" in status_text:
        return "schema_uncertainty"
    if "json" in status_text:
        return "json_parse_or_schema_failure"
    if parse_valid is False:
        return "invalid_parse_unspecified"
    return "unknown_or_not_recorded"


def summarize_group(rows: List[Dict[str, Any]], keys: List[str]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(k, "UNKNOWN")) for k in keys)].append(row)
    out: List[Dict[str, Any]] = []
    for key, gr in sorted(groups.items()):
        total = len(gr)
        valid = sum(1 for r in gr if r.get("parse_valid_bool") is True)
        invalid = sum(1 for r in gr if r.get("parse_valid_bool") is False)
        unknown = total - valid - invalid
        tokens = [to_float(r.get("total_tokens")) for r in gr]
        tokens = [x for x in tokens if x is not None]
        costs = [to_float(r.get("est_cost_gbp")) for r in gr]
        costs = [x for x in costs if x is not None]
        row = {k: v for k, v in zip(keys, key)}
        row.update({
            "rows": total,
            "parse_valid_count": valid,
            "parse_invalid_count": invalid,
            "parse_unknown_count": unknown,
            "parse_valid_rate": round(valid / total, 6) if total else "",
            "mean_total_tokens": round(sum(tokens) / len(tokens), 3) if tokens else "",
            "estimated_cost_gbp": round(sum(costs), 6) if costs else "",
        })
        out.append(row)
    return out


def run_git(args: List[str]) -> str:
    try:
        return subprocess.check_output(["git"] + args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def nested_get(obj: Dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    cur: Any = obj
    for part in dotted_path.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def first_present_int(*values: Any, default: int = 0) -> int:
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool):
            continue
        text = str(value).strip()
        if text == "":
            continue
        try:
            return int(float(text))
        except Exception:
            continue
    return default


def call_accounting_value(rows: List[Dict[str, str]], key: str) -> Any:
    # Supports CSVs shaped as accounting_item,count OR metric,value OR key,value.
    target = key.strip().lower()
    for row in rows:
        row_l = {str(k).strip().lower(): v for k, v in row.items()}
        label = (row_l.get('accounting_item') or row_l.get('metric') or row_l.get('key') or row_l.get('item') or '').strip().lower()
        if label == target:
            return row_l.get('count') or row_l.get('value') or row_l.get('metric_value')
    return None


def main() -> None:
    if OUT_DIR.exists():
        existing_items = list(OUT_DIR.iterdir())
        if existing_items:
            fail(f"Output directory already exists and is not empty: {OUT_DIR}")
    else:
        OUT_DIR.mkdir(parents=True)

    # Explicitly avoid secrets/API reads.
    if os.environ.get("ZAI_API_KEY_READ_BY_05AK_SENTINEL"):
        fail("Unexpected secret-read sentinel set")

    sanitized = read_csv(SANITIZED)
    parser = read_csv(PARSER)
    prior = read_csv(PRIOR)
    usage = read_csv(USAGE)
    stage_summary_existing = read_csv(STAGE_SUMMARY)
    condition_stage_existing = read_csv(CONDITION_STAGE_SUMMARY)
    runner_plan = read_csv(RUNNER_PLAN)
    final_manifest = read_json(FINAL_MANIFEST)
    exec_manifest = read_json(EXEC_MANIFEST)
    call_accounting = read_csv(CALL_ACCOUNTING)

    if len(sanitized) != 33:
        fail(f"Expected 33 sanitized execution rows, found {len(sanitized)}")
    if len(parser) != 33:
        fail(f"Expected 33 parser status rows, found {len(parser)}")
    if len(prior) != 3:
        fail(f"Expected 3 prior attempt rows, found {len(prior)}")

    total_accounted = first_present_int(
        final_manifest.get("total_approved_call_attempts_consumed"),
        final_manifest.get("total_approved_call_attempts_accounted_for"),
        nested_get(final_manifest, "call_accounting.total_approved_call_attempts_consumed"),
        nested_get(final_manifest, "call_accounting.total_approved_call_attempts_accounted_for"),
        call_accounting_value(call_accounting, "total_approved_call_attempts_consumed"),
        call_accounting_value(call_accounting, "total_approved_call_attempts_accounted_for"),
        default=0,
    )
    approved_cap = first_present_int(
        final_manifest.get("approved_call_cap"),
        nested_get(final_manifest, "call_accounting.approved_call_cap"),
        call_accounting_value(call_accounting, "approved_call_cap"),
        default=36,
    )
    if total_accounted != 36 or approved_cap != 36:
        fail(f"Expected finalization to account for 36/36 calls, found {total_accounted}/{approved_cap}")

    # Merge parser status and sanitized rows by position. This avoids depending on provider/raw content.
    normalized: List[Dict[str, Any]] = []
    for idx, san in enumerate(sanitized, start=1):
        p = parser[idx - 1] if idx - 1 < len(parser) else {}
        merged = {**san}
        # Preserve parser fields without clobbering more specific sanitized fields.
        for k, v in p.items():
            if k not in merged or str(merged.get(k, "")).strip() == "":
                merged[k] = v
            else:
                merged[f"parser_{k}"] = v
        fallback_call_number = idx + len(prior)  # V4 resumes from call 4.
        call_number = infer_call_number(merged, fallback_call_number)
        stage = infer_stage(merged, call_number)
        condition = infer_condition(merged)
        case_id = infer_case_id(merged, call_number)
        parse_valid = detect_parse_valid(merged)
        failure_family = infer_failure_family(merged, parse_valid)
        total_tokens = get_field(merged, ["total_tokens", "usage_total_tokens", "tokens_total"])
        est_cost = get_field(merged, ["est_cost_gbp", "estimated_cost_gbp", "cost_gbp", "estimated_call_cost_gbp"])
        normalized.append({
            "source_scope": "persisted_v4_sanitized_execution",
            "call_number": call_number,
            "case_id": case_id,
            "cascade_sequence_id": f"cascade_{math.ceil(call_number / 3):02d}",
            "stage": stage,
            "condition": condition,
            "parse_valid": "True" if parse_valid is True else "False" if parse_valid is False else "UNKNOWN",
            "parse_valid_bool": parse_valid,
            "failure_family": failure_family,
            "total_tokens": total_tokens or "",
            "est_cost_gbp": est_cost or "",
        })

    # Prior calls are accounted for, but not re-materialized as model-result rows unless their CSV has fields.
    prior_norm: List[Dict[str, Any]] = []
    for idx, row in enumerate(prior, start=1):
        call_number = infer_call_number(row, idx)
        stage = infer_stage(row, call_number)
        parse_valid = detect_parse_valid(row)
        if parse_valid is None:
            # We know from terminal run that prior attempts were valid, but avoid relying on terminal logs here.
            # Keep them as accounted/prior unless CSV explicitly says valid.
            parse_label = "ACCOUNTED_PRIOR_ATTEMPT_PARSE_NOT_REANALYZED"
        else:
            parse_label = "True" if parse_valid else "False"
        prior_norm.append({
            "source_scope": "prior_attempt_accounting_not_in_sanitized_outputs",
            "call_number": call_number,
            "case_id": infer_case_id(row, call_number),
            "cascade_sequence_id": f"cascade_{math.ceil(call_number / 3):02d}",
            "stage": stage,
            "condition": infer_condition(row),
            "parse_valid": parse_label,
            "parse_valid_bool": parse_valid,
            "failure_family": infer_failure_family(row, parse_valid) if parse_valid is not None else "prior_attempt_not_reanalyzed",
            "total_tokens": get_field(row, ["total_tokens", "usage_total_tokens", "tokens_total"]) or "",
            "est_cost_gbp": get_field(row, ["est_cost_gbp", "estimated_cost_gbp", "cost_gbp", "estimated_call_cost_gbp"]) or "",
        })

    # Core metric tables use persisted rows; call accounting table accounts for prior rows separately.
    call_accounting_metrics = [
        {"metric": "approved_call_cap", "value": 36, "scope": "05AJ approval"},
        {"metric": "total_approved_call_attempts_accounted_for", "value": total_accounted, "scope": "V5 finalization"},
        {"metric": "persisted_sanitized_execution_rows", "value": len(sanitized), "scope": "V4 committed sanitized outputs"},
        {"metric": "prior_attempt_rows_accounted_for", "value": len(prior), "scope": "V4 prior attempt summary"},
        {"metric": "new_api_calls_in_05ak", "value": 0, "scope": "05AK analysis"},
        {"metric": "api_key_read_in_05ak", "value": False, "scope": "05AK analysis"},
        {"metric": "raw_prompt_instances_written", "value": False, "scope": "05AK analysis"},
        {"metric": "raw_responses_written", "value": False, "scope": "05AK analysis"},
        {"metric": "jsonl_written", "value": False, "scope": "05AK analysis"},
    ]

    by_stage = summarize_group(normalized, ["stage"])
    by_condition = summarize_group(normalized, ["condition"])
    by_condition_stage = summarize_group(normalized, ["condition", "stage"])

    # Failure-family metrics.
    ff_counter: Counter[Tuple[str, str, str]] = Counter()
    for row in normalized:
        ff_counter[(str(row["condition"]), str(row["stage"]), str(row["failure_family"]))] += 1
    ff_rows = [
        {
            "condition": cond,
            "stage": stage,
            "failure_family": fam,
            "rows": count,
            "share_of_persisted_rows": round(count / len(normalized), 6) if normalized else "",
        }
        for (cond, stage, fam), count in sorted(ff_counter.items())
    ]

    # Cascade sequence metrics: include persisted v4 rows and prior-accounting rows, but mark prior as not reanalyzed when needed.
    all_for_cascade = prior_norm + normalized
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in all_for_cascade:
        groups[str(row["cascade_sequence_id"])].append(row)

    cascade_rows: List[Dict[str, Any]] = []
    stage_order = ["decision", "audit", "escalation"]
    for cid, rows in sorted(groups.items()):
        row_by_stage: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            s = str(r.get("stage", "")).lower()
            if s in stage_order and s not in row_by_stage:
                row_by_stage[s] = r
        stage_valid = {}
        for s in stage_order:
            b = row_by_stage.get(s, {}).get("parse_valid_bool")
            stage_valid[s] = b
        complete_three_stage_sequence = all(s in row_by_stage for s in stage_order)
        persisted_stage_count = sum(1 for r in rows if r.get("source_scope") == "persisted_v4_sanitized_execution")
        prior_stage_count = sum(1 for r in rows if r.get("source_scope") == "prior_attempt_accounting_not_in_sanitized_outputs")
        known_invalid = [s for s in stage_order if stage_valid[s] is False]
        known_valid = [s for s in stage_order if stage_valid[s] is True]
        unknown_or_prior = [s for s in stage_order if stage_valid[s] is None]
        if known_invalid:
            first_failure_stage = known_invalid[0]
        elif unknown_or_prior:
            first_failure_stage = "unknown_or_prior_not_reanalyzed"
        else:
            first_failure_stage = "none_observed"
        cascade_rows.append({
            "cascade_sequence_id": cid,
            "complete_three_stage_sequence": complete_three_stage_sequence,
            "persisted_stage_count": persisted_stage_count,
            "prior_accounted_stage_count": prior_stage_count,
            "decision_parse_valid": stage_valid["decision"] if stage_valid["decision"] is not None else "UNKNOWN_OR_PRIOR",
            "audit_parse_valid": stage_valid["audit"] if stage_valid["audit"] is not None else "UNKNOWN_OR_PRIOR",
            "escalation_parse_valid": stage_valid["escalation"] if stage_valid["escalation"] is not None else "UNKNOWN_OR_PRIOR",
            "all_known_stages_parse_valid": bool(complete_three_stage_sequence and not unknown_or_prior and not known_invalid),
            "any_known_stage_parse_invalid": bool(known_invalid),
            "first_known_failure_stage": first_failure_stage,
            "condition_values_observed": ";".join(sorted({str(r.get("condition", "")) for r in rows if str(r.get("condition", "")).strip()})),
        })

    # Usage/cost metrics from normalized rows; include usage_summary fields as source if available.
    token_vals = [to_float(r.get("total_tokens")) for r in normalized]
    token_vals = [x for x in token_vals if x is not None]
    cost_vals = [to_float(r.get("est_cost_gbp")) for r in normalized]
    cost_vals = [x for x in cost_vals if x is not None]
    usage_metrics = [
        {"metric": "persisted_rows_with_token_counts", "value": len(token_vals), "scope": "persisted V4 sanitized outputs"},
        {"metric": "persisted_total_tokens", "value": int(sum(token_vals)) if token_vals else "UNKNOWN", "scope": "persisted V4 sanitized outputs"},
        {"metric": "persisted_mean_tokens_per_call", "value": round(sum(token_vals) / len(token_vals), 3) if token_vals else "UNKNOWN", "scope": "persisted V4 sanitized outputs"},
        {"metric": "persisted_estimated_cost_gbp", "value": round(sum(cost_vals), 6) if cost_vals else "UNKNOWN", "scope": "persisted V4 sanitized outputs"},
        {"metric": "approved_cost_cap_gbp", "value": 3.49, "scope": "05AJ approval"},
        {"metric": "usage_summary_rows_available", "value": len(usage), "scope": "committed usage summary"},
    ]
    # Add flattened usage summary without relying on schema.
    for i, row in enumerate(usage, start=1):
        for k, v in row.items():
            if str(v).strip():
                usage_metrics.append({"metric": f"usage_summary_row_{i}_{k}", "value": v, "scope": "committed usage summary passthrough"})

    definitions = [
        {"metric": "parse_valid_rate", "definition": "parse_valid_count divided by rows for a group of persisted sanitized GLM-5.2 outputs.", "claim_boundary": "Measures parser/schema validity, not substantive correctness."},
        {"metric": "parse_invalid_count", "definition": "Number of persisted sanitized outputs whose parser/schema status is invalid or missing required content.", "claim_boundary": "Does not expose raw response text."},
        {"metric": "failure_family", "definition": "Sanitized family label for parser/schema outcome, e.g. valid_parse or schema uncertainty.", "claim_boundary": "Diagnostic label only; not a provider-wide error rate."},
        {"metric": "condition_stage_rows", "definition": "Rows grouped by evidence condition and cascade stage.", "claim_boundary": "Small micro-pilot sample; descriptive metrics only."},
        {"metric": "cascade_sequence_id", "definition": "Sequence grouping inferred from the 36-call plan, three stages per cascade sequence.", "claim_boundary": "First sequence includes prior attempts accounted for separately."},
        {"metric": "all_known_stages_parse_valid", "definition": "Whether every known stage in a cascade sequence has parser-valid sanitized output.", "claim_boundary": "Prior attempts may be accounted but not reanalyzed from sanitized result rows."},
        {"metric": "first_known_failure_stage", "definition": "Earliest stage in sequence with known parser-invalid status; unknown when prior attempt row lacks parse detail.", "claim_boundary": "Not a causal proof of stage failure."},
        {"metric": "persisted_estimated_cost_gbp", "definition": "Sum of estimated GBP cost fields available in persisted sanitized output rows.", "claim_boundary": "Provider billing may differ; used for reproducibility accounting only."},
        {"metric": "total_approved_call_attempts_accounted_for", "definition": "Approved call attempts consumed and accounted by V5 finalization.", "claim_boundary": "Counts attempts, not necessarily valid parsed outputs."},
        {"metric": "prior_attempt_rows_accounted_for", "definition": "The three calls completed before V4 recovery, tracked separately from V4 sanitized output rows.", "claim_boundary": "Not merged into model-result metrics unless explicit sanitized fields are present."},
        {"metric": "api_calls_in_05ak", "definition": "Number of API/model calls made by this analysis task.", "claim_boundary": "Must remain zero."},
        {"metric": "raw_prompt_instances_written/raw_responses_written/jsonl_written", "definition": "Safety flags for forbidden artifact storage.", "claim_boundary": "Must remain false for this sanitized analysis."},
    ]

    claim_boundary = [
        {"claim_type": "supported", "claim": "A 36-attempt approved GLM-5.2 micro-pilot was accounted for, with 33 persisted sanitized output rows and 3 prior-attempt accounting rows."},
        {"claim_type": "supported", "claim": "05AK generated descriptive parser-validity, stage, condition, cascade-sequence, and usage/cost metrics from sanitized committed outputs only."},
        {"claim_type": "supported", "claim": "05AK made no API/model calls, did not read the API key, and wrote no raw prompt, raw response, or JSONL artifact."},
        {"claim_type": "not_supported_yet", "claim": "This does not prove broad GLM-5.2 reliability, provider superiority, or deployment safety."},
        {"claim_type": "not_supported_yet", "claim": "This does not yet establish Q1-level evidence; it is a small real-LLM micro-pilot requiring aggregation, robustness checks, and cross-model/cross-domain analysis."},
        {"claim_type": "not_supported_yet", "claim": "Parser validity is not equivalent to substantive decision correctness."},
        {"claim_type": "next_step", "claim": "05AL should produce figures/tables and a stronger reliability-cascade interpretation, still without new API calls unless explicitly approved."},
    ]

    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_call_accounting_metrics.csv", call_accounting_metrics)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_parser_validity_by_stage.csv", by_stage)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_parser_validity_by_condition.csv", by_condition)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_parser_validity_by_condition_stage.csv", by_condition_stage)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_failure_family_metrics.csv", ff_rows)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_cascade_sequence_metrics.csv", cascade_rows)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_usage_cost_metrics.csv", usage_metrics)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_metric_definitions.csv", definitions)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_claim_boundary_summary.csv", claim_boundary)

    stage_valid_count = sum(int(r["parse_valid_count"]) for r in by_stage if str(r.get("parse_valid_count", "")).isdigit())
    persisted_valid_count = sum(1 for r in normalized if r.get("parse_valid_bool") is True)
    persisted_invalid_count = sum(1 for r in normalized if r.get("parse_valid_bool") is False)
    persisted_unknown_count = len(normalized) - persisted_valid_count - persisted_invalid_count
    all_known_valid_sequences = sum(1 for r in cascade_rows if r.get("all_known_stages_parse_valid") is True)
    any_known_invalid_sequences = sum(1 for r in cascade_rows if r.get("any_known_stage_parse_invalid") is True)

    report = f"""# Pilot 05 CFPB GLM-5.2 Reliability Cascade Metrics (Task 05AK)

Status: PASS  
Mode: no-call sanitized analysis  
Source commit: {run_git(['rev-parse', '--short', 'HEAD'])}  
Generated UTC: {datetime.now(timezone.utc).isoformat()}  

## Input accounting

- Approved call attempts accounted for: 36/36
- Persisted sanitized execution rows analyzed: {len(normalized)}
- Prior attempt rows accounted separately: {len(prior_norm)}
- Parser status rows analyzed: {len(parser)}
- Runner plan rows available: {len(runner_plan)}

## Parser-validity snapshot

- Persisted parser-valid rows: {persisted_valid_count}
- Persisted parser-invalid rows: {persisted_invalid_count}
- Persisted parser-unknown rows: {persisted_unknown_count}
- Persisted parser-valid rate: {round(persisted_valid_count / len(normalized), 6) if normalized else 'NA'}

## Cascade-sequence snapshot

- Cascade sequence rows generated: {len(cascade_rows)}
- Sequences with all known stages parser-valid: {all_known_valid_sequences}
- Sequences with at least one known parser-invalid stage: {any_known_invalid_sequences}

## Safety and claim boundary

Task 05AK made no API/model calls, did not read the API key, and wrote no raw prompt, raw response, or JSONL artifact. The metrics are descriptive reliability-cascade diagnostics from a small GLM-5.2 micro-pilot. They support analysis of parser/schema validity and stage/condition patterns, not broad claims about provider reliability, deployment safety, or final decision correctness.
"""
    (OUT_DIR / "pilot_05_cfpb_glm52_reliability_cascade_report.md").write_text(report, encoding="utf-8")

    manifest = {
        "task_id": TASK_ID,
        "script_version": "V3_CORRECTED_PARSER_VALIDITY_ACCOUNTING",
        "status": "PASS",
        "analysis_mode": "NO_CALL_SANITIZED_ANALYSIS",
        "source_commit": run_git(["rev-parse", "--short", "HEAD"]),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "api_calls_in_05ak": 0,
        "api_key_read_in_05ak": False,
        "model_calls_in_05ak": 0,
        "raw_prompt_instances_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "total_approved_call_attempts_accounted_for": total_accounted,
        "approved_call_cap": approved_cap,
        "persisted_execution_rows_analyzed": len(sanitized),
        "parser_status_rows_analyzed": len(parser),
        "prior_attempt_rows_accounted_for": len(prior),
        "runner_plan_rows_available": len(runner_plan),
        "stage_metric_rows": len(by_stage),
        "condition_metric_rows": len(by_condition),
        "condition_stage_metric_rows": len(by_condition_stage),
        "failure_family_rows": len(ff_rows),
        "cascade_sequence_rows": len(cascade_rows),
        "metric_definition_rows": len(definitions),
        "persisted_parser_valid_count": persisted_valid_count,
        "persisted_parser_invalid_count": persisted_invalid_count,
        "persisted_parser_unknown_count": persisted_unknown_count,
        "persisted_parser_valid_rate": round(persisted_valid_count / len(normalized), 6) if normalized else None,
        "safe_claim_boundary": "descriptive real-LLM micro-pilot metrics only; no broad reliability/deployment/provider claims",
        "source_files": {
            "sanitized_outputs": str(SANITIZED.relative_to(ROOT)),
            "parser_status": str(PARSER.relative_to(ROOT)),
            "prior_attempt_summary": str(PRIOR.relative_to(ROOT)),
            "finalization_manifest": str(FINAL_MANIFEST.relative_to(ROOT)),
            "runner_plan": str(RUNNER_PLAN.relative_to(ROOT)),
        },
        "outputs": sorted(p.name for p in OUT_DIR.iterdir()),
    }
    write_json(OUT_DIR / "pilot_05_cfpb_glm52_reliability_cascade_metrics_manifest.json", manifest)

    print("Pilot 05 CFPB GLM-5.2 reliability cascade metrics generated.")
    print(f"output_dir: {OUT_DIR.relative_to(ROOT).as_posix()}")
    print("status: PASS")
    print("analysis_mode: NO_CALL_SANITIZED_ANALYSIS")
    print("api_calls_in_05ak: 0")
    print("api_key_read_in_05ak: False")
    print(f"total_approved_call_attempts_accounted_for: {total_accounted}")
    print(f"persisted_execution_rows_analyzed: {len(sanitized)}")
    print(f"parser_status_rows_analyzed: {len(parser)}")
    print(f"prior_attempt_rows_accounted_for: {len(prior)}")
    print(f"persisted_parser_valid_count: {persisted_valid_count}")
    print(f"persisted_parser_invalid_count: {persisted_invalid_count}")
    print(f"cascade_sequence_rows: {len(cascade_rows)}")
    print("raw_prompt_instances_written: False")
    print("raw_responses_written: False")
    print("jsonl_written: False")


if __name__ == "__main__":
    main()
