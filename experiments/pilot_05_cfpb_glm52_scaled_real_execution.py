#!/usr/bin/env python3
"""
TASK 05AN: Scaled Pilot 05 GLM-5.2 Real Execution

Purpose:
- Preflight and approved execution for Option A:
  60 sanitized CFPB-backed base cases × 4 evidence conditions × 3 stages × GLM-5.2 = 720 calls.
- No .env reading.
- No raw prompt writing.
- No raw response writing.
- No JSONL writing.
- Sanitized categorical outputs only.
- API/model calls only in --mode execute with --approve-real-api-calls and positive --cost-cap-usd.

This script is intentionally conservative. It stores hashes and parsed categorical fields,
not raw prompts or raw model outputs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Any, Optional


TASK = "05AN"
SCRIPT_FIX_VERSION = "05AN_V2_CALL_PLAN_SCHEMA_FIX"
EXPECTED_PREVIOUS_COMMIT = "0e9c860"
DEFAULT_MODEL = "glm-5.2"
DEFAULT_BASE_URL = "https://api.z.ai/api/paas/v4"

EVIDENCE_CONDITIONS = [
    "clean",
    "compressed_lossy",
    "partial_dropout",
    "noisy_conflicting",
]
STAGES = ["decision", "audit", "escalation"]
EXPECTED_BASE_CASES = 60
EXPECTED_CALLS = EXPECTED_BASE_CASES * len(EVIDENCE_CONDITIONS) * len(STAGES)

OUTDIR = Path("reports/pilot_05_cfpb_glm52_scaled_real_execution")
SCRIPT_PATH = Path("experiments/pilot_05_cfpb_glm52_scaled_real_execution.py")
CONDITIONS_CSV = Path("reports/pilot_05_cfpb_evidence_state_conditions/pilot_05_cfpb_evidence_state_conditions.csv")
DESIGN_MANIFEST = Path("reports/pilot_05_cfpb_glm52_scaled_execution_design/pilot_05_scaled_execution_design_manifest.json")

FORBIDDEN_OUTPUT_SUFFIXES = {".jsonl"}
FORBIDDEN_PATH_PARTS = {
    "data/raw",
    ".env",
    "raw_prompt",
    "raw_prompts",
    "raw_response",
    "raw_responses",
    "api_key",
    "secret",
}


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def ensure_outdir() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys = []
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def append_csv(path: Path, row: Dict[str, Any], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow(row)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def safe_str(value: Any, max_len: int = 300) -> str:
    if value is None:
        return ""
    s = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


def find_column(fieldnames: List[str], candidates: List[str], contains: List[str] = None) -> Optional[str]:
    lower = {c.lower(): c for c in fieldnames}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    if contains:
        for c in fieldnames:
            lc = c.lower()
            if all(part.lower() in lc for part in contains):
                return c
    return None


def canonical_condition(value: str) -> str:
    v = (value or "").strip().lower().replace("-", "_").replace(" ", "_").replace("/", "_")
    if v in {"clean", "baseline", "control", "complete", "full"}:
        return "clean"
    if "compressed" in v or "lossy" in v:
        return "compressed_lossy"
    if "dropout" in v or ("partial" in v and "noisy" not in v) or "missing" in v:
        return "partial_dropout"
    if "noisy" in v or "conflict" in v or "contradict" in v:
        return "noisy_conflicting"
    return v


def condition_aliases() -> Dict[str, List[str]]:
    return {
        "clean": ["clean", "baseline", "control", "complete", "full", "intact"],
        "compressed_lossy": ["compressed", "lossy", "summary", "summarized", "compressed_lossy", "lossy_compressed"],
        "partial_dropout": ["partial_dropout", "dropout", "partial", "missing", "omitted", "redacted_gap", "incomplete"],
        "noisy_conflicting": ["noisy_conflicting", "noisy", "conflict", "conflicting", "contradict", "contradictory", "noise"],
    }


def infer_schema(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Infer the base-case and condition columns by validating the actual paired design.

    V1 picked the first ID-like column, which can be wrong when a condition-row ID is
    unique per row. V2 evaluates every safe candidate pair and chooses the pair that
    yields complete base cases across all four evidence conditions.
    """
    if not rows:
        raise RuntimeError("Evidence condition CSV has no rows.")

    fieldnames = list(rows[0].keys())
    lower_to_actual = {c.lower(): c for c in fieldnames}

    common_case_candidates = [
        "base_case_id", "case_id", "sanitized_base_case_id", "sanitized_case_id",
        "evidence_case_id", "evidence_base_case_id", "case_group_id", "base_group_id",
        "complaint_id_hash", "source_case_id_hash", "source_complaint_id_hash",
        "cfpb_case_id_hash", "case_hash", "base_case_hash",
    ]
    common_condition_candidates = [
        "evidence_condition", "condition", "condition_name", "evidence_state_condition",
        "state_condition", "evidence_state", "condition_label", "evidence_variant",
        "variant", "state_variant",
    ]

    case_candidates: List[str] = []
    for name in common_case_candidates:
        if name.lower() in lower_to_actual and lower_to_actual[name.lower()] not in case_candidates:
            case_candidates.append(lower_to_actual[name.lower()])
    for c in fieldnames:
        lc = c.lower()
        looks_id = ("id" in lc or "hash" in lc or "case" in lc or "complaint" in lc)
        forbidden = any(token in lc for token in ["condition", "stage", "sequence", "row_index", "sequence_index"])
        if looks_id and not forbidden and c not in case_candidates:
            case_candidates.append(c)

    condition_candidates: List[str] = []
    for name in common_condition_candidates:
        if name.lower() in lower_to_actual and lower_to_actual[name.lower()] not in condition_candidates:
            condition_candidates.append(lower_to_actual[name.lower()])
    for c in fieldnames:
        lc = c.lower()
        looks_condition = any(token in lc for token in ["condition", "evidence_state", "variant", "state"])
        forbidden = any(token in lc for token in ["id", "hash", "count", "score"])
        if looks_condition and not forbidden and c not in condition_candidates:
            condition_candidates.append(c)

    if not case_candidates:
        raise RuntimeError(f"Could not infer any base-case candidate column from columns: {fieldnames}")
    if not condition_candidates:
        raise RuntimeError(f"Could not infer any evidence-condition candidate column from columns: {fieldnames}")

    evaluations: List[Dict[str, Any]] = []
    best_eval: Optional[Dict[str, Any]] = None

    for cond_col in condition_candidates:
        for case_col in case_candidates:
            case_to_conditions: Dict[str, set] = {}
            cond_counts: Dict[str, int] = {}
            unknown_values: Dict[str, int] = {}
            nonempty_rows = 0
            for row in rows:
                case_id = safe_str(row.get(case_col), 120)
                raw_cond = safe_str(row.get(cond_col), 160)
                cond = canonical_condition(raw_cond)
                if not case_id or not raw_cond:
                    continue
                nonempty_rows += 1
                if cond in EVIDENCE_CONDITIONS:
                    cond_counts[cond] = cond_counts.get(cond, 0) + 1
                    case_to_conditions.setdefault(case_id, set()).add(cond)
                else:
                    unknown_values[raw_cond[:80]] = unknown_values.get(raw_cond[:80], 0) + 1

            complete_cases = [
                case_id for case_id, conds in case_to_conditions.items()
                if all(c in conds for c in EVIDENCE_CONDITIONS)
            ]
            unique_case_count = len(case_to_conditions)
            known_condition_rows = sum(cond_counts.values())
            eval_row = {
                "case_col": case_col,
                "condition_col": cond_col,
                "nonempty_rows": nonempty_rows,
                "known_condition_rows": known_condition_rows,
                "condition_counts": cond_counts,
                "unknown_condition_value_sample": dict(list(unknown_values.items())[:10]),
                "unique_case_count_with_known_conditions": unique_case_count,
                "complete_base_cases_with_all_four_conditions": len(complete_cases),
                "expected_call_count_if_selected": min(len(complete_cases), EXPECTED_BASE_CASES) * len(EVIDENCE_CONDITIONS) * len(STAGES),
            }
            evaluations.append(eval_row)
            if best_eval is None:
                best_eval = eval_row
            else:
                old_key = (
                    int(best_eval["complete_base_cases_with_all_four_conditions"]),
                    int(best_eval["known_condition_rows"]),
                    -abs(int(best_eval["unique_case_count_with_known_conditions"]) - EXPECTED_BASE_CASES),
                )
                new_key = (
                    int(eval_row["complete_base_cases_with_all_four_conditions"]),
                    int(eval_row["known_condition_rows"]),
                    -abs(int(eval_row["unique_case_count_with_known_conditions"]) - EXPECTED_BASE_CASES),
                )
                if new_key > old_key:
                    best_eval = eval_row

    if best_eval is None:
        raise RuntimeError("Schema inference produced no candidate evaluations.")

    # Keep full evaluated schema metadata, but bound samples for readability.
    evaluations_sorted = sorted(
        evaluations,
        key=lambda r: (int(r["complete_base_cases_with_all_four_conditions"]), int(r["known_condition_rows"])),
        reverse=True,
    )[:20]

    return {
        "fieldnames": fieldnames,
        "case_col": best_eval["case_col"],
        "condition_col": best_eval["condition_col"],
        "schema_inference_method": "candidate_pair_max_complete_four_condition_groups_v2",
        "schema_fix_version": SCRIPT_FIX_VERSION,
        "best_candidate_evaluation": best_eval,
        "top_candidate_evaluations": evaluations_sorted,
    }


def select_option_a_cases(rows: List[Dict[str, str]], schema: Dict[str, Any]) -> Tuple[List[str], Dict[Tuple[str, str], Dict[str, str]], Dict[str, Any]]:
    case_col = schema["case_col"]
    condition_col = schema["condition_col"]

    by_case_cond: Dict[Tuple[str, str], Dict[str, str]] = {}
    cond_counts: Dict[str, int] = {}
    case_to_conditions: Dict[str, set] = {}
    unknown_condition_values: Dict[str, int] = {}

    for row in rows:
        case_id = safe_str(row.get(case_col), 120)
        raw_cond = safe_str(row.get(condition_col, ""), 160)
        cond = canonical_condition(raw_cond)
        if not case_id or not raw_cond:
            continue
        if cond not in EVIDENCE_CONDITIONS:
            unknown_condition_values[raw_cond[:80]] = unknown_condition_values.get(raw_cond[:80], 0) + 1
            continue
        cond_counts[cond] = cond_counts.get(cond, 0) + 1
        case_to_conditions.setdefault(case_id, set()).add(cond)
        # Keep first encountered row for deterministic paired condition plan.
        by_case_cond.setdefault((case_id, cond), row)

    complete_cases = sorted([
        case_id for case_id, conds in case_to_conditions.items()
        if all(c in conds for c in EVIDENCE_CONDITIONS)
    ])

    selected = complete_cases[:EXPECTED_BASE_CASES]

    meta = {
        "schema_fix_version": SCRIPT_FIX_VERSION,
        "total_rows": len(rows),
        "case_col": case_col,
        "condition_col": condition_col,
        "condition_counts": cond_counts,
        "unknown_condition_value_sample": dict(list(unknown_condition_values.items())[:10]),
        "unique_case_count_with_known_conditions": len(case_to_conditions),
        "complete_base_cases_with_all_four_conditions": len(complete_cases),
        "selected_base_cases": len(selected),
        "expected_call_count_if_selected": len(selected) * len(EVIDENCE_CONDITIONS) * len(STAGES),
        "selected_case_id_hashes_preview": [sha256_text(x)[:16] for x in selected[:10]],
    }
    return selected, by_case_cond, meta

def load_design_manifest() -> Dict[str, Any]:
    if not DESIGN_MANIFEST.exists():
        raise RuntimeError(f"Missing 05AM design manifest: {DESIGN_MANIFEST}")
    return json.loads(DESIGN_MANIFEST.read_text(encoding="utf-8"))


def verify_no_forbidden_created_files() -> None:
    if not OUTDIR.exists():
        return
    for p in OUTDIR.rglob("*"):
        rel = p.as_posix().lower()
        if p.suffix.lower() in FORBIDDEN_OUTPUT_SUFFIXES:
            raise RuntimeError(f"Forbidden output suffix created: {p}")
        for bad in FORBIDDEN_PATH_PARTS:
            if bad in rel:
                raise RuntimeError(f"Forbidden path part created: {p}")


def build_evidence_packet(row: Dict[str, str], schema: Dict[str, Any]) -> str:
    """
    Build a prompt-only evidence packet from sanitized condition rows.
    It is never written to disk. It is deliberately bounded to reduce leakage risk.
    """
    case_col = schema["case_col"]
    condition_col = schema["condition_col"]

    excluded_keywords = {
        "raw", "api_key", "secret", "jsonl", "prompt", "response"
    }

    pieces = []
    for k, v in row.items():
        lk = k.lower()
        if any(bad in lk for bad in excluded_keywords):
            continue
        if k == case_col or k == condition_col:
            continue
        sv = safe_str(v, 500)
        if sv:
            pieces.append(f"{k}: {sv}")

    # Keep prompt bounded and auditable through hashes.
    return "\n".join(pieces[:80])


def build_prompt(case_id: str, condition: str, stage: str, evidence_packet: str) -> str:
    schema_instruction = {
        "case_id": case_id,
        "evidence_condition": condition,
        "stage": stage,
        "parser_contract_ack": True,
        "evidence_state_adequate": "true|false",
        "validity_judgment": "valid|invalid|uncertain",
        "decision_recommendation": "routine_review|follow_up|escalate|insufficient_evidence|not_applicable",
        "audit_detected_degradation": "true|false|null",
        "audit_false_assurance": "true|false|null",
        "escalation_recovery": "recovered|not_recovered|loss|not_applicable",
        "confidence_bucket": "low|medium|high",
        "primary_failure_family": "none|evidence_loss|conflict_unresolved|unsupported_inference|format_error|overconfidence|other",
    }

    return f"""You are evaluating a sanitized evidence-state reliability test case in a research-only LLM decision pipeline.

This is not a real financial, legal, regulatory, or consumer decision. Do not provide advice, do not decide a real case, and do not infer protected attributes.

Task:
- Stage: {stage}
- Evidence condition: {condition}
- Base case ID: {case_id}

Use only the sanitized evidence below.
Do not quote the evidence.
Do not include names, addresses, account numbers, narrative fragments, or any raw evidence text in your answer.
Return only one compact JSON object matching the required categorical schema.
No markdown. No prose outside JSON.

Required JSON schema and allowed values:
{json.dumps(schema_instruction, indent=2)}

Sanitized evidence-state packet:
{evidence_packet}
"""


def parse_model_json(content: str) -> Tuple[bool, Dict[str, Any], str]:
    try:
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return False, {}, "json_not_object"
        return True, parsed, ""
    except Exception:
        return False, {}, "json_parse_error"


def normalize_boolish(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    s = str(value).strip().lower()
    if s in {"true", "false", "null", ""}:
        return "" if s == "null" else s
    return s[:50]


def categorical(parsed: Dict[str, Any], key: str, max_len: int = 80) -> str:
    v = parsed.get(key, "")
    if isinstance(v, (dict, list)):
        return "invalid_nested_value"
    return safe_str(v, max_len)


def estimate_cost(input_tokens: int, output_tokens: int, input_per_m: float, output_per_m: float) -> float:
    return (input_tokens / 1_000_000.0) * input_per_m + (output_tokens / 1_000_000.0) * output_per_m


def call_openai_compatible_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_output_tokens: int,
    timeout_seconds: int,
    use_response_format: bool,
) -> Tuple[str, Dict[str, int], Dict[str, Any]]:
    url = base_url.rstrip("/") + "/chat/completions"
    body: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict JSON-only research evaluator. Return only valid compact JSON with categorical fields.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": max_output_tokens,
    }
    if use_response_format:
        body["response_format"] = {"type": "json_object"}

    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        data = resp.read().decode("utf-8", errors="replace")
    obj = json.loads(data)

    content = obj["choices"][0]["message"]["content"]
    usage_obj = obj.get("usage") or {}
    usage = {
        "input_tokens": int(usage_obj.get("prompt_tokens") or usage_obj.get("input_tokens") or 0),
        "output_tokens": int(usage_obj.get("completion_tokens") or usage_obj.get("output_tokens") or 0),
        "total_tokens": int(usage_obj.get("total_tokens") or 0),
    }
    return content, usage, obj


def load_existing_sequence_ids(path: Path) -> set:
    if not path.exists():
        return set()
    out = set()
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            sid = row.get("sequence_id")
            if sid:
                out.add(sid)
    return out


ROW_FIELDS = [
    "run_id", "sequence_index", "sequence_id", "timestamp_utc", "model",
    "base_case_id", "evidence_condition", "stage",
    "parser_valid", "parser_error_category",
    "parser_contract_ack", "evidence_state_adequate", "validity_judgment",
    "decision_recommendation", "audit_detected_degradation", "audit_false_assurance",
    "escalation_recovery", "confidence_bucket", "primary_failure_family",
    "input_tokens", "output_tokens", "estimated_cost_usd",
    "prompt_hash", "response_hash",
]

LEDGER_FIELDS = [
    "run_id", "sequence_index", "sequence_id", "timestamp_utc", "model",
    "base_case_id", "evidence_condition", "stage",
    "call_attempted", "call_succeeded", "parser_valid",
    "input_tokens", "output_tokens", "estimated_cost_usd",
    "cumulative_estimated_cost_usd", "prompt_hash", "response_hash", "error_category",
]

INVALID_FIELDS = [
    "run_id", "sequence_index", "sequence_id", "timestamp_utc", "model",
    "base_case_id", "evidence_condition", "stage", "parser_error_category",
    "response_hash", "input_tokens", "output_tokens", "estimated_cost_usd",
]


def build_call_plan(selected_cases: List[str], by_case_cond: Dict[Tuple[str, str], Dict[str, str]]) -> List[Dict[str, str]]:
    plan = []
    idx = 0
    for case_id in selected_cases:
        for cond in EVIDENCE_CONDITIONS:
            for stage in STAGES:
                idx += 1
                sequence_id = sha256_text(f"{case_id}|{cond}|{stage}")[:24]
                if (case_id, cond) not in by_case_cond:
                    raise RuntimeError(f"Missing row for selected case/condition: {case_id} / {cond}")
                plan.append({
                    "sequence_index": idx,
                    "sequence_id": sequence_id,
                    "base_case_id": case_id,
                    "evidence_condition": cond,
                    "stage": stage,
                })
    return plan


def make_preflight_manifest(args: argparse.Namespace) -> Dict[str, Any]:
    design = load_design_manifest()
    rows = read_csv_rows(CONDITIONS_CSV)
    schema = infer_schema(rows)
    selected_cases, by_case_cond, meta = select_option_a_cases(rows, schema)
    call_plan = build_call_plan(selected_cases, by_case_cond)

    recommended = design.get("recommendation", {})
    safety = design.get("safety_flags", {})

    manifest = {
        "task": TASK,
        "status": "PASS" if len(call_plan) == EXPECTED_CALLS else "BLOCKED",
        "timestamp_utc": now_iso(),
        "checkpoint_required": "0e9c860 Add Pilot 05 scaled execution design",
        "mode": "preflight",
        "model": args.model,
        "base_url": args.base_url,
        "option": "A",
        "expected_base_cases": EXPECTED_BASE_CASES,
        "selected_base_cases": len(selected_cases),
        "evidence_conditions": EVIDENCE_CONDITIONS,
        "stages": STAGES,
        "expected_call_count": EXPECTED_CALLS,
        "planned_call_count": len(call_plan),
        "input_schema": schema,
        "condition_input_meta": meta,
        "inherited_05am_recommendation": {
            "recommended_option": recommended.get("recommended_option"),
            "recommended_call_count": recommended.get("recommended_call_count"),
        },
        "inherited_05am_safety_flags": safety,
        "safety_contract": {
            "real_api_calls_in_preflight": 0,
            "model_calls_in_preflight": 0,
            "env_file_read": False,
            "api_key_read_in_preflight": False,
            "raw_prompts_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "raw_cfpb_data_touched": False,
            "only_sanitized_outputs_planned": True,
            "actual_execute_requires_approve_real_api_calls_flag": True,
            "actual_execute_requires_positive_cost_cap_usd": True,
        },
        "pricing_defaults_usd_per_million_tokens": {
            "input": args.input_price_per_million,
            "output": args.output_price_per_million,
            "pricing_source_note": "Default values reflect current public Z.AI / provider pricing; user must approve a cost cap before execution.",
        },
    }
    return manifest


def write_preflight_outputs(args: argparse.Namespace) -> None:
    ensure_outdir()
    manifest = make_preflight_manifest(args)
    write_json(OUTDIR / "pilot_05AN_preflight_manifest.json", manifest)

    # V2 fix: preflight must validate the actual constructed call plan, not print a constant.
    rows_for_plan = read_csv_rows(CONDITIONS_CSV)
    schema_for_plan = infer_schema(rows_for_plan)
    selected_cases_for_plan, by_case_cond_for_plan, meta_for_plan = select_option_a_cases(rows_for_plan, schema_for_plan)
    call_plan_for_preview = build_call_plan(selected_cases_for_plan, by_case_cond_for_plan)
    write_csv(OUTDIR / "pilot_05AN_call_plan_preview.csv", call_plan_for_preview[:min(30, len(call_plan_for_preview))])
    write_json(OUTDIR / "pilot_05AN_call_plan_validation.json", {
        "task": TASK,
        "schema_fix_version": SCRIPT_FIX_VERSION,
        "timestamp_utc": now_iso(),
        "expected_call_count": EXPECTED_CALLS,
        "actual_planned_call_count": len(call_plan_for_preview),
        "status": "PASS" if len(call_plan_for_preview) == EXPECTED_CALLS else "BLOCKED",
        "input_schema": schema_for_plan,
        "condition_input_meta": meta_for_plan,
        "raw_prompts_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "raw_cfpb_data_touched": False,
        "api_key_read": False,
        "model_calls": 0,
    })
    if len(call_plan_for_preview) != EXPECTED_CALLS:
        raise RuntimeError(f"V2 preflight call-plan validation failed: expected {EXPECTED_CALLS}, got {len(call_plan_for_preview)}. See pilot_05AN_call_plan_validation.json")

    rows = []
    for cond in EVIDENCE_CONDITIONS:
        rows.append({
            "evidence_condition": cond,
            "included": True,
            "purpose": {
                "clean": "baseline evidence state",
                "compressed_lossy": "tests whether information compression/loss degrades downstream stage behavior",
                "partial_dropout": "tests sensitivity to missing evidence elements",
                "noisy_conflicting": "tests audit/escalation behavior under conflicting evidence",
            }[cond],
        })
    write_csv(OUTDIR / "pilot_05AN_evidence_condition_contract.csv", rows)

    stage_rows = []
    for stage in STAGES:
        stage_rows.append({
            "stage": stage,
            "included": True,
            "primary_measurement": {
                "decision": "stage validity, evidence adequacy, decision recommendation under evidence conditions",
                "audit": "degradation detection and false-assurance behavior",
                "escalation": "recovery/loss behavior after degraded evidence state",
            }[stage],
        })
    write_csv(OUTDIR / "pilot_05AN_stage_contract.csv", stage_rows)

    abort_rows = [
        {"abort_rule": "missing_api_key", "threshold": "execute mode only: API key env var must exist", "action": "abort before first call"},
        {"abort_rule": "cost_cap", "threshold": "cumulative estimated cost >= approved cap", "action": "abort before next call"},
        {"abort_rule": "api_error_rate", "threshold": ">= 20% after at least 50 attempted calls", "action": "abort"},
        {"abort_rule": "consecutive_api_errors", "threshold": "5 consecutive API errors", "action": "abort"},
        {"abort_rule": "parser_invalid_rate", "threshold": "> 70% after at least 60 successful calls", "action": "abort for parser/contract review"},
        {"abort_rule": "forbidden_output", "threshold": "any .jsonl/raw prompt/raw response/.env/raw CFPB path", "action": "abort and report"},
    ]
    write_csv(OUTDIR / "pilot_05AN_abort_rules.csv", abort_rows)

    approval_md = f"""# TASK 05AN Approval Gate

Current package status: **preflight only**.

This preflight created no API/model calls and read no API key.

## Proposed real execution

- Model: `{args.model}`
- Option: A
- Base cases: {EXPECTED_BASE_CASES}
- Evidence conditions: {len(EVIDENCE_CONDITIONS)} ({", ".join(EVIDENCE_CONDITIONS)})
- Stages: {len(STAGES)} ({", ".join(STAGES)})
- Planned calls: {EXPECTED_CALLS}
- Output contract: sanitized categorical CSV/JSON only
- Forbidden outputs: raw prompts, raw responses, JSONL, `.env`, raw CFPB data
- Default pricing assumption: ${args.input_price_per_million}/M input tokens and ${args.output_price_per_million}/M output tokens
- Exact spend: depends on actual token usage and must be bounded by user-approved cost cap

## To run real execution later

Only run after explicitly approving the model, call count, cost cap, storage contract, and abort rules.

Example:

```powershell
python experiments/pilot_05_cfpb_glm52_scaled_real_execution.py --mode execute --approve-real-api-calls --model {args.model} --base-url "{args.base_url}" --api-key-env-var ZAI_API_KEY --cost-cap-usd 8 --expected-call-count {EXPECTED_CALLS}
```

Replace `25` with the cost cap you actually approve.
"""
    (OUTDIR / "pilot_05AN_execution_approval_gate.md").write_text(approval_md, encoding="utf-8")

    verify_no_forbidden_created_files()


def execute(args: argparse.Namespace) -> None:
    if not args.approve_real_api_calls:
        raise RuntimeError("execute mode requires --approve-real-api-calls")
    if args.cost_cap_usd is None or args.cost_cap_usd <= 0:
        raise RuntimeError("execute mode requires positive --cost-cap-usd")
    if args.expected_call_count != EXPECTED_CALLS:
        raise RuntimeError(f"expected call count must be {EXPECTED_CALLS}; got {args.expected_call_count}")

    # Only now read API key from environment. Do not read .env.
    api_key = os.environ.get(args.api_key_env_var)
    if not api_key:
        raise RuntimeError(f"Missing API key environment variable: {args.api_key_env_var}. This script does not read .env files.")

    ensure_outdir()

    rows = read_csv_rows(CONDITIONS_CSV)
    schema = infer_schema(rows)
    selected_cases, by_case_cond, meta = select_option_a_cases(rows, schema)
    call_plan = build_call_plan(selected_cases, by_case_cond)

    if len(call_plan) != EXPECTED_CALLS:
        raise RuntimeError(f"Call plan count expected {EXPECTED_CALLS}, got {len(call_plan)}")

    run_id = args.run_id or f"pilot05AN_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    execution_rows_path = OUTDIR / "pilot_05AN_sanitized_execution_rows.csv"
    ledger_path = OUTDIR / "pilot_05AN_call_ledger.csv"
    invalid_path = OUTDIR / "pilot_05AN_parser_invalid_summary.csv"

    completed = load_existing_sequence_ids(ledger_path) if args.resume else set()

    cumulative_cost = 0.0
    attempted = 0
    succeeded = 0
    parser_invalid = 0
    api_errors = 0
    consecutive_api_errors = 0

    # Recover cumulative counters from existing ledger if resuming.
    if args.resume and ledger_path.exists():
        with ledger_path.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    cumulative_cost = max(cumulative_cost, float(row.get("cumulative_estimated_cost_usd") or 0))
                except Exception:
                    pass

    start_manifest = {
        "task": TASK,
        "schema_fix_version": SCRIPT_FIX_VERSION,
        "mode": "execute",
        "run_id": run_id,
        "timestamp_utc": now_iso(),
        "model": args.model,
        "base_url": args.base_url,
        "api_key_env_var_used": args.api_key_env_var,
        "api_key_value_written_or_printed": False,
        "option": "A",
        "planned_call_count": len(call_plan),
        "condition_input_meta": meta,
        "input_schema": schema,
        "cost_cap_usd": args.cost_cap_usd,
        "input_price_per_million": args.input_price_per_million,
        "output_price_per_million": args.output_price_per_million,
        "raw_prompts_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "raw_cfpb_data_touched": False,
        "status": "RUNNING",
    }
    write_json(OUTDIR / "pilot_05AN_execution_manifest.json", start_manifest)
    write_csv(OUTDIR / "pilot_05AN_call_plan.csv", call_plan)

    print(f"=== TASK 05AN EXECUTE: {len(call_plan)} planned calls ===")
    print(f"run_id: {run_id}")
    print(f"model: {args.model}")
    print(f"cost_cap_usd: {args.cost_cap_usd}")
    print("raw prompt/response writing: NO")
    print("jsonl writing: NO")
    print("env file reading: NO")
    print("api key printing: NO")

    for item in call_plan:
        sid = item["sequence_id"]
        idx = int(item["sequence_index"])
        if sid in completed:
            print(f"SKIP already attempted sequence {idx}/{len(call_plan)} {sid}")
            continue

        if cumulative_cost >= args.cost_cap_usd:
            raise RuntimeError(f"Cost cap reached before next call: {cumulative_cost:.6f} >= {args.cost_cap_usd:.6f}")

        row = by_case_cond[(item["base_case_id"], item["evidence_condition"])]
        evidence_packet = build_evidence_packet(row, schema)
        prompt = build_prompt(item["base_case_id"], item["evidence_condition"], item["stage"], evidence_packet)
        prompt_hash = sha256_text(prompt)

        attempted += 1
        timestamp = now_iso()
        content = ""
        response_hash = ""
        input_tokens = 0
        output_tokens = 0
        call_cost = 0.0

        try:
            content, usage, _raw_obj = call_openai_compatible_chat(
                base_url=args.base_url,
                api_key=api_key,
                model=args.model,
                prompt=prompt,
                max_output_tokens=args.max_output_tokens,
                timeout_seconds=args.timeout_seconds,
                use_response_format=args.use_response_format,
            )
            response_hash = sha256_text(content)
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            call_cost = estimate_cost(input_tokens, output_tokens, args.input_price_per_million, args.output_price_per_million)
            cumulative_cost += call_cost
            succeeded += 1
            consecutive_api_errors = 0

            parser_valid, parsed, parser_error = parse_model_json(content)
            if not parser_valid:
                parser_invalid += 1
            contract_ack = normalize_boolish(parsed.get("parser_contract_ack")) if parser_valid else ""

            clean_row = {
                "run_id": run_id,
                "sequence_index": idx,
                "sequence_id": sid,
                "timestamp_utc": timestamp,
                "model": args.model,
                "base_case_id": item["base_case_id"],
                "evidence_condition": item["evidence_condition"],
                "stage": item["stage"],
                "parser_valid": str(parser_valid),
                "parser_error_category": parser_error,
                "parser_contract_ack": contract_ack,
                "evidence_state_adequate": normalize_boolish(parsed.get("evidence_state_adequate")) if parser_valid else "",
                "validity_judgment": categorical(parsed, "validity_judgment") if parser_valid else "",
                "decision_recommendation": categorical(parsed, "decision_recommendation") if parser_valid else "",
                "audit_detected_degradation": normalize_boolish(parsed.get("audit_detected_degradation")) if parser_valid else "",
                "audit_false_assurance": normalize_boolish(parsed.get("audit_false_assurance")) if parser_valid else "",
                "escalation_recovery": categorical(parsed, "escalation_recovery") if parser_valid else "",
                "confidence_bucket": categorical(parsed, "confidence_bucket") if parser_valid else "",
                "primary_failure_family": categorical(parsed, "primary_failure_family") if parser_valid else "",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": f"{call_cost:.8f}",
                "prompt_hash": prompt_hash,
                "response_hash": response_hash,
            }
            append_csv(execution_rows_path, clean_row, ROW_FIELDS)

            if not parser_valid:
                append_csv(invalid_path, {
                    "run_id": run_id,
                    "sequence_index": idx,
                    "sequence_id": sid,
                    "timestamp_utc": timestamp,
                    "model": args.model,
                    "base_case_id": item["base_case_id"],
                    "evidence_condition": item["evidence_condition"],
                    "stage": item["stage"],
                    "parser_error_category": parser_error,
                    "response_hash": response_hash,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "estimated_cost_usd": f"{call_cost:.8f}",
                }, INVALID_FIELDS)

            append_csv(ledger_path, {
                "run_id": run_id,
                "sequence_index": idx,
                "sequence_id": sid,
                "timestamp_utc": timestamp,
                "model": args.model,
                "base_case_id": item["base_case_id"],
                "evidence_condition": item["evidence_condition"],
                "stage": item["stage"],
                "call_attempted": "True",
                "call_succeeded": "True",
                "parser_valid": str(parser_valid),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": f"{call_cost:.8f}",
                "cumulative_estimated_cost_usd": f"{cumulative_cost:.8f}",
                "prompt_hash": prompt_hash,
                "response_hash": response_hash,
                "error_category": "",
            }, LEDGER_FIELDS)

            print(f"CALL {idx}/{len(call_plan)} ok parser_valid={parser_valid} cost={call_cost:.6f} cumulative={cumulative_cost:.6f}")

        except urllib.error.HTTPError as e:
            api_errors += 1
            consecutive_api_errors += 1
            err_category = f"http_error_{e.code}"
            append_csv(ledger_path, {
                "run_id": run_id,
                "sequence_index": idx,
                "sequence_id": sid,
                "timestamp_utc": timestamp,
                "model": args.model,
                "base_case_id": item["base_case_id"],
                "evidence_condition": item["evidence_condition"],
                "stage": item["stage"],
                "call_attempted": "True",
                "call_succeeded": "False",
                "parser_valid": "False",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": f"{call_cost:.8f}",
                "cumulative_estimated_cost_usd": f"{cumulative_cost:.8f}",
                "prompt_hash": prompt_hash,
                "response_hash": "",
                "error_category": err_category,
            }, LEDGER_FIELDS)
            print(f"CALL {idx}/{len(call_plan)} API ERROR {err_category}")
        except Exception as e:
            api_errors += 1
            consecutive_api_errors += 1
            err_category = type(e).__name__
            append_csv(ledger_path, {
                "run_id": run_id,
                "sequence_index": idx,
                "sequence_id": sid,
                "timestamp_utc": timestamp,
                "model": args.model,
                "base_case_id": item["base_case_id"],
                "evidence_condition": item["evidence_condition"],
                "stage": item["stage"],
                "call_attempted": "True",
                "call_succeeded": "False",
                "parser_valid": "False",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": f"{call_cost:.8f}",
                "cumulative_estimated_cost_usd": f"{cumulative_cost:.8f}",
                "prompt_hash": prompt_hash,
                "response_hash": "",
                "error_category": err_category,
            }, LEDGER_FIELDS)
            print(f"CALL {idx}/{len(call_plan)} ERROR {err_category}")

        finally:
            verify_no_forbidden_created_files()

        if cumulative_cost >= args.cost_cap_usd:
            print(f"ABORT: cost cap reached after call attempt. cumulative={cumulative_cost:.6f} cap={args.cost_cap_usd:.6f}")
            break

        if consecutive_api_errors >= args.max_consecutive_api_errors:
            raise RuntimeError(f"Abort rule triggered: {consecutive_api_errors} consecutive API errors.")

        if attempted >= 50 and api_errors / max(attempted, 1) >= args.max_api_error_rate:
            raise RuntimeError(f"Abort rule triggered: API error rate {api_errors}/{attempted} >= {args.max_api_error_rate}")

        if succeeded >= 60 and parser_invalid / max(succeeded, 1) > args.max_parser_invalid_rate_after_60:
            raise RuntimeError(f"Abort rule triggered: parser invalid rate {parser_invalid}/{succeeded} > {args.max_parser_invalid_rate_after_60}")

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    final_manifest = dict(start_manifest)
    final_manifest.update({
        "status": "COMPLETE_OR_COST_CAPPED",
        "completed_timestamp_utc": now_iso(),
        "attempted_in_this_run": attempted,
        "succeeded_in_this_run": succeeded,
        "api_errors_in_this_run": api_errors,
        "parser_invalid_in_this_run": parser_invalid,
        "cumulative_estimated_cost_usd": round(cumulative_cost, 8),
        "raw_prompts_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "raw_cfpb_data_touched": False,
    })
    write_json(OUTDIR / "pilot_05AN_execution_manifest.json", final_manifest)
    verify_no_forbidden_created_files()
    print("=== TASK 05AN EXECUTION FINISHED/STOPPED SAFELY ===")
    print(json.dumps(final_manifest, indent=2))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["preflight", "execute"], required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--api-key-env-var", default="ZAI_API_KEY")
    ap.add_argument("--approve-real-api-calls", action="store_true")
    ap.add_argument("--expected-call-count", type=int, default=EXPECTED_CALLS)
    ap.add_argument("--cost-cap-usd", type=float, default=None)
    ap.add_argument("--input-price-per-million", type=float, default=1.40)
    ap.add_argument("--output-price-per-million", type=float, default=4.40)
    ap.add_argument("--max-output-tokens", type=int, default=700)
    ap.add_argument("--timeout-seconds", type=int, default=90)
    ap.add_argument("--sleep-ms", type=int, default=250)
    ap.add_argument("--resume", action="store_true", default=True)
    ap.add_argument("--use-response-format", action="store_true")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--max-consecutive-api-errors", type=int, default=5)
    ap.add_argument("--max-api-error-rate", type=float, default=0.20)
    ap.add_argument("--max-parser-invalid-rate-after-60", type=float, default=0.70)
    args = ap.parse_args(argv)

    if args.mode == "preflight":
        write_preflight_outputs(args)
        print("=== TASK 05AN PREFLIGHT COMPLETE ===")
        print(f"planned_call_count: {make_preflight_manifest(args).get('planned_call_count')}")
        print("real_api_calls: 0")
        print("model_calls: 0")
        print("api_key_read: False")
        print("env_file_read: False")
        print("raw_prompts_written: False")
        print("raw_responses_written: False")
        print("jsonl_written: False")
        print(f"approval_gate: {OUTDIR / 'pilot_05AN_execution_approval_gate.md'}")
        return 0

    if args.mode == "execute":
        execute(args)
        return 0

    raise RuntimeError(f"Unknown mode {args.mode}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        ensure_outdir()
        error_report = {
            "task": TASK,
            "status": "ERROR",
            "timestamp_utc": now_iso(),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback_tail": traceback.format_exc().splitlines()[-8:],
            "raw_prompts_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "raw_cfpb_data_touched": False,
        }
        write_json(OUTDIR / "pilot_05AN_error_report.json", error_report)
        print(f"ERROR: 05AN failed: {exc}")
        raise
