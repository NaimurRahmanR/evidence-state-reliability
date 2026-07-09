#!/usr/bin/env python3
"""TASK 05AP: Scaled Pilot 05 GLM-5.2 metrics analysis.

No API/model calls. Reads only sanitized 05AN/05AO CSV/JSON outputs and writes sanitized
metric tables/reports. Raw prompt/response content is neither read nor written.
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Tuple

TASK = "05AP"
EXPECTED_CALL_COUNT = 720
EXPECTED_BASE_CASES = 60
CONDITIONS = ["clean", "compressed_lossy", "partial_dropout", "noisy_conflicting"]
DEGRADED_CONDITIONS = [c for c in CONDITIONS if c != "clean"]
STAGES = ["decision", "audit", "escalation"]
BOOTSTRAP_N = 2000
RANDOM_SEED = 5205

POSITIVE_VALUES = {
    "true", "yes", "y", "1", "pass", "passed", "valid", "correct", "adequate",
    "supported", "acceptable", "success", "succeeded", "recovered", "detected",
}
NEGATIVE_VALUES = {
    "false", "no", "n", "0", "fail", "failed", "invalid", "incorrect", "inadequate",
    "unsupported", "unacceptable", "error", "not_detected", "not recovered", "not_recovered",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: List[str] = []
        seen = set()
        for row in rows:
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def parse_boolish(value: Any) -> bool | None:
    v = norm(value)
    if v in POSITIVE_VALUES:
        return True
    if v in NEGATIVE_VALUES:
        return False
    if v == "":
        return None
    return None


def is_parser_valid(row: Dict[str, str]) -> bool:
    return parse_boolish(row.get("parser_valid")) is True


def is_validity_positive(row: Dict[str, str]) -> bool | None:
    # Conservative: use explicit validity_judgment first; if absent, do not infer validity from fluency.
    v = norm(row.get("validity_judgment"))
    if v in POSITIVE_VALUES:
        return True
    if v in NEGATIVE_VALUES:
        return False
    if v == "":
        return None
    # Allow common compact labels without over-fitting exact schema.
    if v.startswith("valid") or v.startswith("correct") or v.startswith("supported") or v.startswith("adequate"):
        return True
    if v.startswith("invalid") or v.startswith("incorrect") or v.startswith("unsupported") or v.startswith("inadequate"):
        return False
    return None


def stage_success(row: Dict[str, str]) -> bool:
    # Claim-bounded metric: this is a parsed/stated stage-validity proxy, not real-world correctness.
    vp = is_validity_positive(row)
    return is_parser_valid(row) and vp is True


def safe_div(num: float, den: float) -> float | None:
    if den == 0:
        return None
    return num / den


def fmt_rate(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def group_key(row: Dict[str, str], cols: Iterable[str]) -> Tuple[str, ...]:
    return tuple(row.get(c, "") for c in cols)


def aggregate_rates(rows: List[Dict[str, str]], group_cols: List[str], source: str) -> List[Dict[str, Any]]:
    buckets: Dict[Tuple[str, ...], List[Dict[str, str]]] = defaultdict(list)
    for r in rows:
        buckets[group_key(r, group_cols)].append(r)
    out: List[Dict[str, Any]] = []
    for key in sorted(buckets.keys()):
        rs = buckets[key]
        parser_true = sum(1 for r in rs if is_parser_valid(r))
        parser_false = sum(1 for r in rs if parse_boolish(r.get("parser_valid")) is False)
        success_true = sum(1 for r in rs if stage_success(r))
        validity_known = sum(1 for r in rs if is_validity_positive(r) is not None)
        row: Dict[str, Any] = {col: val for col, val in zip(group_cols, key)}
        row.update({
            "source": source,
            "n_rows": len(rs),
            "parser_valid_true": parser_true,
            "parser_valid_false": parser_false,
            "parser_valid_rate": fmt_rate(safe_div(parser_true, len(rs))),
            "stage_success_true": success_true,
            "stage_success_rate": fmt_rate(safe_div(success_true, len(rs))),
            "validity_judgment_known_rows": validity_known,
            "validity_judgment_known_rate": fmt_rate(safe_div(validity_known, len(rs))),
        })
        out.append(row)
    return out


def value_distribution(rows: List[Dict[str, str]], field: str) -> Dict[str, int]:
    return dict(sorted(Counter(norm(r.get(field)) or "<blank>" for r in rows).items()))


def make_audit_metrics(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    audit = [r for r in rows if norm(r.get("stage")) == "audit"]
    out = []
    for cond in CONDITIONS:
        rs = [r for r in audit if norm(r.get("evidence_condition")) == cond]
        parsed = [r for r in rs if is_parser_valid(r)]
        detected = sum(1 for r in parsed if parse_boolish(r.get("audit_detected_degradation")) is True)
        false_assurance = sum(1 for r in parsed if parse_boolish(r.get("audit_false_assurance")) is True)
        out.append({
            "evidence_condition": cond,
            "is_degraded_condition": cond != "clean",
            "audit_rows": len(rs),
            "parser_valid_rows": len(parsed),
            "audit_detected_degradation_true": detected,
            "audit_detection_rate_among_parser_valid": fmt_rate(safe_div(detected, len(parsed))),
            "audit_false_assurance_true": false_assurance,
            "audit_false_assurance_rate_among_parser_valid": fmt_rate(safe_div(false_assurance, len(parsed))),
            "claim_boundary_note": "Audit metrics are model-output-coded from sanitized responses; they are not external regulatory audit outcomes.",
        })
    return out


def make_escalation_metrics(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    esc = [r for r in rows if norm(r.get("stage")) == "escalation"]
    out = []
    for cond in CONDITIONS:
        rs = [r for r in esc if norm(r.get("evidence_condition")) == cond]
        parsed = [r for r in rs if is_parser_valid(r)]
        recovery = sum(1 for r in parsed if parse_boolish(r.get("escalation_recovery")) is True)
        success = sum(1 for r in parsed if stage_success(r))
        loss = sum(1 for r in parsed if (parse_boolish(r.get("escalation_recovery")) is False or not stage_success(r)))
        out.append({
            "evidence_condition": cond,
            "is_degraded_condition": cond != "clean",
            "escalation_rows": len(rs),
            "parser_valid_rows": len(parsed),
            "escalation_recovery_true": recovery,
            "escalation_recovery_rate_among_parser_valid": fmt_rate(safe_div(recovery, len(parsed))),
            "escalation_stage_success_true": success,
            "escalation_stage_success_rate_among_parser_valid": fmt_rate(safe_div(success, len(parsed))),
            "escalation_loss_proxy_true": loss,
            "escalation_loss_proxy_rate_among_parser_valid": fmt_rate(safe_div(loss, len(parsed))),
            "claim_boundary_note": "Escalation loss/recovery are model-output-coded proxies, not real-world escalation outcomes.",
        })
    return out


def make_condition_stage_interaction(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out = []
    by_cs = aggregate_rates(rows, ["evidence_condition", "stage"], "sanitized_execution_rows")
    # Add deltas vs clean within each stage.
    clean_by_stage: Dict[str, Dict[str, Any]] = {r["stage"]: r for r in by_cs if r.get("evidence_condition") == "clean"}
    for r in by_cs:
        clean = clean_by_stage.get(r["stage"])
        parser_delta = ""
        success_delta = ""
        if clean:
            try:
                parser_delta = f"{float(r['parser_valid_rate']) - float(clean['parser_valid_rate']):.6f}"
            except Exception:
                pass
            try:
                success_delta = f"{float(r['stage_success_rate']) - float(clean['stage_success_rate']):.6f}"
            except Exception:
                pass
        rr = dict(r)
        rr["parser_valid_delta_vs_clean_same_stage"] = parser_delta
        rr["stage_success_delta_vs_clean_same_stage"] = success_delta
        out.append(rr)
    return out


def make_failure_distribution(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    buckets: Counter[Tuple[str, str, str]] = Counter()
    for r in rows:
        fam = norm(r.get("primary_failure_family")) or norm(r.get("parser_error_category")) or "<blank>"
        buckets[(norm(r.get("evidence_condition")), norm(r.get("stage")), fam)] += 1
    return [
        {"evidence_condition": c, "stage": s, "failure_family_or_parser_category": f, "n_rows": n}
        for (c, s, f), n in sorted(buckets.items())
    ]


def make_sequence_patterns(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], Dict[str, Dict[str, str]]] = defaultdict(dict)
    for r in rows:
        grouped[(r.get("base_case_id", ""), norm(r.get("evidence_condition")))][norm(r.get("stage"))] = r
    out: List[Dict[str, Any]] = []
    for (case_id, cond), by_stage in sorted(grouped.items()):
        decision = by_stage.get("decision")
        audit = by_stage.get("audit")
        escalation = by_stage.get("escalation")
        parser_flags = {s: (is_parser_valid(by_stage[s]) if s in by_stage else None) for s in STAGES}
        success_flags = {s: (stage_success(by_stage[s]) if s in by_stage else None) for s in STAGES}
        audit_false = parse_boolish(audit.get("audit_false_assurance")) if audit else None
        audit_detect = parse_boolish(audit.get("audit_detected_degradation")) if audit else None
        esc_recover = parse_boolish(escalation.get("escalation_recovery")) if escalation else None
        pattern = ""
        if all(s in by_stage for s in STAGES):
            pattern = "P" + "".join("1" if parser_flags[s] else "0" for s in STAGES)
            pattern += "_S" + "".join("1" if success_flags[s] else "0" for s in STAGES)
        else:
            pattern = "missing_stage_" + "_".join(s for s in STAGES if s not in by_stage)
        out.append({
            "base_case_id": case_id,
            "evidence_condition": cond,
            "n_stages_present": len(by_stage),
            "decision_parser_valid": parser_flags["decision"],
            "audit_parser_valid": parser_flags["audit"],
            "escalation_parser_valid": parser_flags["escalation"],
            "decision_stage_success": success_flags["decision"],
            "audit_stage_success": success_flags["audit"],
            "escalation_stage_success": success_flags["escalation"],
            "parser_all_three": all(parser_flags[s] is True for s in STAGES),
            "stage_success_all_three": all(success_flags[s] is True for s in STAGES),
            "any_parser_failure": any(parser_flags[s] is False for s in STAGES),
            "any_stage_success_failure": any(success_flags[s] is False for s in STAGES),
            "audit_detected_degradation": audit_detect,
            "audit_false_assurance": audit_false,
            "escalation_recovery": esc_recover,
            "cascade_sequence_pattern": pattern,
        })
    return out


def make_pattern_distribution(pattern_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter((r["evidence_condition"], r["cascade_sequence_pattern"]) for r in pattern_rows)
    totals = Counter(r["evidence_condition"] for r in pattern_rows)
    return [
        {
            "evidence_condition": cond,
            "cascade_sequence_pattern": pattern,
            "n_sequences": n,
            "condition_total_sequences": totals[cond],
            "rate_within_condition": fmt_rate(safe_div(n, totals[cond])),
        }
        for (cond, pattern), n in sorted(c.items())
    ]


def paired_case_stage_values(rows: List[Dict[str, str]], metric: str) -> Dict[Tuple[str, str, str], float]:
    vals: Dict[Tuple[str, str, str], float] = {}
    for r in rows:
        case = r.get("base_case_id", "")
        cond = norm(r.get("evidence_condition"))
        stage = norm(r.get("stage"))
        if metric == "parser_valid":
            vals[(case, cond, stage)] = 1.0 if is_parser_valid(r) else 0.0
        elif metric == "stage_success":
            vals[(case, cond, stage)] = 1.0 if stage_success(r) else 0.0
        elif metric == "evidence_state_adequate":
            vals[(case, cond, stage)] = 1.0 if parse_boolish(r.get("evidence_state_adequate")) is True else 0.0
    return vals


def percentile(xs: List[float], p: float) -> float | None:
    if not xs:
        return None
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    idx = (len(ys) - 1) * p
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return ys[int(idx)]
    return ys[lo] * (hi - idx) + ys[hi] * (idx - lo)


def bootstrap_ci(deltas_by_case: Dict[str, float], n: int = BOOTSTRAP_N) -> Tuple[float | None, float | None, float | None, int]:
    cases = sorted(deltas_by_case)
    if not cases:
        return None, None, None, 0
    observed = mean(deltas_by_case[c] for c in cases)
    rng = random.Random(RANDOM_SEED)
    reps = []
    for _ in range(n):
        sample = [deltas_by_case[rng.choice(cases)] for _ in cases]
        reps.append(mean(sample))
    return observed, percentile(reps, 0.025), percentile(reps, 0.975), len(cases)


def make_paired_deltas(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    paired_rows: List[Dict[str, Any]] = []
    ci_rows: List[Dict[str, Any]] = []
    metrics = ["parser_valid", "stage_success", "evidence_state_adequate"]
    for metric in metrics:
        vals = paired_case_stage_values(rows, metric)
        for stage in STAGES:
            for cond in DEGRADED_CONDITIONS:
                case_deltas: Dict[str, float] = {}
                for (case, c, s), degraded_val in vals.items():
                    if c != cond or s != stage:
                        continue
                    clean_key = (case, "clean", stage)
                    if clean_key not in vals:
                        continue
                    clean_val = vals[clean_key]
                    delta = degraded_val - clean_val
                    case_deltas[case] = delta
                    paired_rows.append({
                        "metric": metric,
                        "base_case_id": case,
                        "stage": stage,
                        "clean_condition": "clean",
                        "degraded_condition": cond,
                        "clean_value": clean_val,
                        "degraded_value": degraded_val,
                        "paired_delta_degraded_minus_clean": delta,
                    })
                obs, lo, hi, n_cases = bootstrap_ci(case_deltas)
                ci_rows.append({
                    "metric": metric,
                    "stage": stage,
                    "degraded_condition": cond,
                    "paired_cases": n_cases,
                    "mean_paired_delta_degraded_minus_clean": "" if obs is None else f"{obs:.6f}",
                    "bootstrap_n": BOOTSTRAP_N,
                    "ci_95_low": "" if lo is None else f"{lo:.6f}",
                    "ci_95_high": "" if hi is None else f"{hi:.6f}",
                    "random_seed": RANDOM_SEED,
                })
    return paired_rows, ci_rows


def make_metric_definitions() -> List[Dict[str, str]]:
    return [
        {"metric": "parser_valid_rate", "definition": "Share of rows whose sanitized model output satisfied the parser contract.", "claim_boundary": "Not a measure of real-world answer correctness."},
        {"metric": "stage_success_rate", "definition": "Share of rows that were parser-valid and had a positive sanitized validity_judgment under the task contract.", "claim_boundary": "Model-output-coded stage proxy; not external adjudication."},
        {"metric": "audit_detection_rate", "definition": "Among parser-valid audit-stage rows, share with audit_detected_degradation=true.", "claim_boundary": "Only meaningful as a model-output-coded audit behavior indicator."},
        {"metric": "audit_false_assurance_rate", "definition": "Among parser-valid audit-stage rows, share with audit_false_assurance=true.", "claim_boundary": "Proxy for false assurance inside this controlled pipeline only."},
        {"metric": "escalation_recovery_rate", "definition": "Among parser-valid escalation-stage rows, share with escalation_recovery=true.", "claim_boundary": "Proxy for escalation recovery inside this controlled pipeline only."},
        {"metric": "paired_delta_degraded_minus_clean", "definition": "Within-base-case difference between a degraded condition and clean condition for a metric/stage.", "claim_boundary": "Paired experimental contrast; not a population deployment estimate."},
        {"metric": "bootstrap_ci", "definition": "Nonparametric bootstrap CI over paired base cases for mean paired delta.", "claim_boundary": "Uncertainty over the 60 selected sanitized base cases only."},
        {"metric": "cascade_sequence_pattern", "definition": "Three-stage parser/stage-success pattern for each base_case_id × evidence_condition sequence.", "claim_boundary": "Pattern over sanitized execution rows; missing ledger-only rows are accounted separately."},
    ]


def main() -> int:
    repo = Path.cwd()
    out_dir = repo / "reports" / "pilot_05_cfpb_glm52_scaled_metrics"
    if out_dir.exists():
        raise RuntimeError(f"05AP output directory already exists; refusing to overwrite: {out_dir}")

    exec_dir = repo / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution"
    integrity_dir = repo / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution_integrity"

    ledger = read_csv(exec_dir / "pilot_05AN_call_ledger.csv")
    plan = read_csv(exec_dir / "pilot_05AN_call_plan.csv")
    sanitized = read_csv(exec_dir / "pilot_05AN_sanitized_execution_rows.csv")
    invalid_summary = read_csv(exec_dir / "pilot_05AN_parser_invalid_summary.csv")
    exec_manifest = read_json(exec_dir / "pilot_05AN_execution_manifest.json")
    integrity_manifest = read_json(integrity_dir / "pilot_05AO_integrity_manifest.json")

    if len(plan) != EXPECTED_CALL_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_CALL_COUNT} call plan rows, got {len(plan)}")
    if len(ledger) != EXPECTED_CALL_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_CALL_COUNT} ledger rows, got {len(ledger)}")
    if len(sanitized) != 713:
        raise RuntimeError(f"Expected 713 sanitized execution rows from 05AO reconciliation, got {len(sanitized)}")
    if len(invalid_summary) != 243:
        raise RuntimeError(f"Expected 243 parser invalid summary rows, got {len(invalid_summary)}")

    out_dir.mkdir(parents=True, exist_ok=False)

    parser_by_condition_stage = []
    parser_by_condition_stage.extend(aggregate_rates(ledger, ["evidence_condition", "stage"], "call_ledger"))
    parser_by_condition_stage.extend(aggregate_rates(sanitized, ["evidence_condition", "stage"], "sanitized_execution_rows"))

    stage_validity_by_condition_stage = aggregate_rates(sanitized, ["evidence_condition", "stage"], "sanitized_execution_rows")
    interaction = make_condition_stage_interaction(sanitized)
    audit_metrics = make_audit_metrics(sanitized)
    escalation_metrics = make_escalation_metrics(sanitized)
    failure_distribution = make_failure_distribution(sanitized)
    sequence_rows = make_sequence_patterns(sanitized)
    pattern_distribution = make_pattern_distribution(sequence_rows)
    paired_rows, ci_rows = make_paired_deltas(sanitized)

    row_accounting = [{
        "planned_call_count": len(plan),
        "ledger_rows": len(ledger),
        "sanitized_execution_rows": len(sanitized),
        "parser_invalid_summary_rows": len(invalid_summary),
        "ledger_parser_valid_true": sum(1 for r in ledger if is_parser_valid(r)),
        "ledger_parser_valid_false": sum(1 for r in ledger if parse_boolish(r.get("parser_valid")) is False),
        "persisted_parser_valid_true": sum(1 for r in sanitized if is_parser_valid(r)),
        "persisted_parser_valid_false": sum(1 for r in sanitized if parse_boolish(r.get("parser_valid")) is False),
        "ledger_only_missing_sanitized_rows": int(integrity_manifest.get("ledger_only_missing_sanitized_rows", 7)),
        "cumulative_estimated_cost_usd": exec_manifest.get("cumulative_estimated_cost_usd", ""),
        "ready_for_metrics_source": integrity_manifest.get("ready_for_05AP_metrics", ""),
    }]

    category_distributions: List[Dict[str, Any]] = []
    for field in [
        "parser_valid", "parser_error_category", "parser_contract_ack", "evidence_state_adequate",
        "validity_judgment", "decision_recommendation", "audit_detected_degradation",
        "audit_false_assurance", "escalation_recovery", "confidence_bucket", "primary_failure_family",
    ]:
        for value, n in value_distribution(sanitized, field).items():
            category_distributions.append({"field": field, "value": value, "n_rows": n})

    write_csv(out_dir / "pilot_05AP_row_accounting_summary.csv", row_accounting)
    write_csv(out_dir / "pilot_05AP_parser_validity_by_condition_stage.csv", parser_by_condition_stage)
    write_csv(out_dir / "pilot_05AP_stage_validity_by_condition_stage.csv", stage_validity_by_condition_stage)
    write_csv(out_dir / "pilot_05AP_condition_stage_interaction.csv", interaction)
    write_csv(out_dir / "pilot_05AP_audit_metrics.csv", audit_metrics)
    write_csv(out_dir / "pilot_05AP_escalation_metrics.csv", escalation_metrics)
    write_csv(out_dir / "pilot_05AP_failure_family_distribution.csv", failure_distribution)
    write_csv(out_dir / "pilot_05AP_cascade_sequence_rows.csv", sequence_rows)
    write_csv(out_dir / "pilot_05AP_cascade_sequence_pattern_distribution.csv", pattern_distribution)
    write_csv(out_dir / "pilot_05AP_clean_vs_degraded_paired_deltas.csv", paired_rows)
    write_csv(out_dir / "pilot_05AP_bootstrap_confidence_intervals.csv", ci_rows)
    write_csv(out_dir / "pilot_05AP_sanitized_category_distributions.csv", category_distributions)
    write_csv(out_dir / "pilot_05AP_metric_definitions.csv", make_metric_definitions())

    manifest = {
        "task": TASK,
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
        "input_sources": {
            "call_plan": str((exec_dir / "pilot_05AN_call_plan.csv").as_posix()),
            "call_ledger": str((exec_dir / "pilot_05AN_call_ledger.csv").as_posix()),
            "sanitized_execution_rows": str((exec_dir / "pilot_05AN_sanitized_execution_rows.csv").as_posix()),
            "parser_invalid_summary": str((exec_dir / "pilot_05AN_parser_invalid_summary.csv").as_posix()),
            "integrity_manifest": str((integrity_dir / "pilot_05AO_integrity_manifest.json").as_posix()),
        },
        "row_accounting": row_accounting[0],
        "outputs": sorted(p.name for p in out_dir.iterdir() if p.is_file()),
        "claim_boundary": {
            "scaled_real_model_evidence_exists": True,
            "target_research_claim_proven": False,
            "broad_model_reliability_claimed": False,
            "real_world_financial_or_regulatory_validity_claimed": False,
            "summary": "05AP computes claim-bounded metrics over sanitized real GLM-5.2 execution outputs; paper claims remain limited until interpretation and claim-boundary review.",
        },
    }
    write_json(out_dir / "pilot_05AP_scaled_metrics_manifest.json", manifest)

    report = f"""# Pilot 05AP scaled GLM-5.2 metrics report\n\nStatus: PASS\n\n## Scope\n\nThis no-call task computes metrics over the sanitized Pilot 05AN scaled GLM-5.2 execution outputs and the 05AO integrity reconciliation. It does not make API/model calls, read API keys or `.env`, write raw prompts/responses, create JSONL, stage, commit, or push.\n\n## Row accounting\n\n- Planned calls: {len(plan)}\n- Ledger rows: {len(ledger)}\n- Sanitized persisted execution rows: {len(sanitized)}\n- Parser-invalid summary rows: {len(invalid_summary)}\n- Ledger parser-valid rows: {row_accounting[0]['ledger_parser_valid_true']}\n- Ledger parser-invalid rows: {row_accounting[0]['ledger_parser_valid_false']}\n- Persisted parser-valid rows: {row_accounting[0]['persisted_parser_valid_true']}\n- Persisted parser-invalid rows: {row_accounting[0]['persisted_parser_valid_false']}\n- Ledger-only missing sanitized rows: {row_accounting[0]['ledger_only_missing_sanitized_rows']}\n- Cumulative estimated cost USD: {row_accounting[0]['cumulative_estimated_cost_usd']}\n\n## Metrics generated\n\n- Parser validity by condition and stage\n- Stage validity proxy by condition and stage\n- Condition-stage interaction table with deltas versus clean condition\n- Clean-vs-degraded paired deltas by base case\n- Bootstrap confidence intervals over paired base cases\n- Audit detection and false-assurance metrics\n- Escalation recovery/loss proxy metrics\n- Cascade sequence patterns\n- Failure-family/category distributions\n- Metric definitions and claim boundaries\n\n## Claim boundary\n\nThis is scaled, real GLM-5.2, CFPB-backed sanitized pipeline evidence. It supports metric generation for evidence-state reliability analysis. It does not yet prove the final paper claim, does not establish broad GLM-5.2 reliability, and does not establish real-world financial or regulatory validity.\n"""
    (out_dir / "pilot_05AP_scaled_metrics_report.md").write_text(report, encoding="utf-8")

    print("=== TASK 05AP: SCALED METRICS ANALYSIS COMPLETE ===")
    print("status: PASS")
    for k, v in row_accounting[0].items():
        print(f"{k}: {v}")
    print(f"bootstrap_n: {BOOTSTRAP_N}")
    print(f"outputs_dir: {out_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
