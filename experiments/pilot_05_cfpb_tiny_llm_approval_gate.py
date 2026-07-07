from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "05AI"
STATUS = "PASS"
APPROVAL_STATUS = "NOT_APPROVED_DESIGN_ONLY"
RECOMMENDED_OPTION_ID = "B_36_CALL_PAIRED_MICRO_PILOT"
RECOMMENDED_CALL_COUNT = 36

STAGES = ("decision", "audit", "escalation")
CONDITIONS = ("clean", "compressed", "partial_dropout", "noisy_conflicting")
BASE_PACKET_SLOTS = (1, 2, 3)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "reports" / "pilot_05_cfpb_tiny_llm_approval_gate"

INPUTS = {
    "execution_harness_script": REPO / "experiments" / "pilot_05_cfpb_cascade_execution_harness.py",
    "readiness_validation_script": REPO / "experiments" / "pilot_05_cfpb_cascade_harness_readiness_validation.py",
    "execution_harness_manifest": REPO / "reports" / "pilot_05_cfpb_cascade_execution_harness" / "pilot_05_cfpb_cascade_execution_harness_manifest.json",
    "execution_plan": REPO / "reports" / "pilot_05_cfpb_cascade_execution_harness" / "pilot_05_cfpb_cascade_execution_plan.csv",
    "execution_batches": REPO / "reports" / "pilot_05_cfpb_cascade_execution_harness" / "pilot_05_cfpb_cascade_execution_batches.csv",
    "execution_guardrails": REPO / "reports" / "pilot_05_cfpb_cascade_execution_harness" / "pilot_05_cfpb_cascade_execution_guardrails.csv",
    "readiness_manifest": REPO / "reports" / "pilot_05_cfpb_cascade_harness_readiness_validation" / "pilot_05_cfpb_cascade_harness_readiness_validation_manifest.json",
    "readiness_checks": REPO / "reports" / "pilot_05_cfpb_cascade_harness_readiness_validation" / "pilot_05_cfpb_cascade_harness_readiness_checks.csv",
}

FILES = {
    "manifest": OUT / "pilot_05_cfpb_tiny_llm_approval_gate_manifest.json",
    "options": OUT / "pilot_05_cfpb_tiny_llm_pilot_options.csv",
    "abstract_call_plan": OUT / "pilot_05_cfpb_tiny_llm_recommended_abstract_call_plan.csv",
    "approval_fields": OUT / "pilot_05_cfpb_tiny_llm_approval_required_fields.csv",
    "cost_template": OUT / "pilot_05_cfpb_tiny_llm_cost_permission_template.csv",
    "storage_policy": OUT / "pilot_05_cfpb_tiny_llm_storage_policy.csv",
    "abort_conditions": OUT / "pilot_05_cfpb_tiny_llm_abort_conditions.csv",
    "sanitized_contract": OUT / "pilot_05_cfpb_tiny_llm_sanitized_output_contract.csv",
    "claim_boundary": OUT / "pilot_05_cfpb_tiny_llm_claim_boundary.csv",
    "report": OUT / "pilot_05_cfpb_tiny_llm_approval_gate_report.md",
}


def die(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if path.exists():
        die(f"Refusing to overwrite output: {rel(path)}")
    if not rows:
        die(f"No rows for output: {rel(path)}")
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def check_inputs() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    missing = [rel(path) for path in INPUTS.values() if not path.exists()]
    if missing:
        die(f"Missing required inputs: {missing}")

    harness_manifest = read_json(INPUTS["execution_harness_manifest"])
    readiness_manifest = read_json(INPUTS["readiness_manifest"])
    plan_rows = read_csv(INPUTS["execution_plan"])
    batch_rows = read_csv(INPUTS["execution_batches"])
    readiness_rows = read_csv(INPUTS["readiness_checks"])

    if harness_manifest.get("status") != "PASS":
        die("05AG harness manifest is not PASS")
    if readiness_manifest.get("status") != "PASS":
        die("05AH readiness manifest is not PASS")

    counts = harness_manifest.get("counts", {})
    safety = harness_manifest.get("safety_flags", {})
    if int(counts.get("dry_run_rows", -1)) != 720:
        die("05AG dry_run_rows is not 720")
    if int(counts.get("execution_plan_rows", -1)) != 720:
        die("05AG execution_plan_rows is not 720")
    if int(counts.get("execution_batch_rows", -1)) != 12:
        die("05AG execution_batch_rows is not 12")
    if int(safety.get("model_calls", -1)) != 0:
        die("05AG model_calls is not 0")
    if int(safety.get("api_calls", -1)) != 0:
        die("05AG api_calls is not 0")
    if safety.get("model_execution_enabled") is not False:
        die("05AG model_execution_enabled is not False")

    readiness_counts = readiness_manifest.get("counts", {})
    if int(readiness_counts.get("failed_checks", -1)) != 0:
        die("05AH failed_checks is not 0")
    if int(readiness_counts.get("check_rows", -1)) != 111:
        die("05AH check_rows is not 111")

    if len(plan_rows) != 720:
        die(f"Execution plan CSV has {len(plan_rows)} rows, expected 720")
    if len(batch_rows) != 12:
        die(f"Execution batches CSV has {len(batch_rows)} rows, expected 12")

    return harness_manifest, readiness_manifest, plan_rows, batch_rows, readiness_rows


def build_options() -> list[dict[str, Any]]:
    return [
        {
            "option_id": "A_12_CALL_WIRING_SENTINEL",
            "future_call_count": 12,
            "structure": "1 base-packet slot x 4 evidence conditions x 3 cascade stages",
            "research_strength": "Low",
            "main_use": "API/parser/storage wiring check only; not enough for condition-level empirical claims.",
            "tradeoff": "Fastest and cheapest, but too weak for meaningful cascade metrics.",
            "recommended": False,
            "future_explicit_approval_required": True,
        },
        {
            "option_id": "B_36_CALL_PAIRED_MICRO_PILOT",
            "future_call_count": 36,
            "structure": "3 base-packet slots x 4 evidence conditions x 3 cascade stages",
            "research_strength": "Minimum credible tiny pilot",
            "main_use": "Small paired real-LLM smoke pilot for decision/audit/escalation behaviour across conditions.",
            "tradeoff": "Still not inferentially strong, but more research-useful than a 12-call wiring check.",
            "recommended": True,
            "future_explicit_approval_required": True,
        },
        {
            "option_id": "C_72_CALL_SMALL_PILOT",
            "future_call_count": 72,
            "structure": "6 base-packet slots x 4 evidence conditions x 3 cascade stages",
            "research_strength": "Stronger small pilot",
            "main_use": "Better preliminary cascade metric stability before scaling.",
            "tradeoff": "More cost/time than a tiny pilot; still not a full Pilot 05 run.",
            "recommended": False,
            "future_explicit_approval_required": True,
        },
    ]


def build_abstract_call_plan() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 0
    for slot in BASE_PACKET_SLOTS:
        for condition in CONDITIONS:
            for stage in STAGES:
                order += 1
                rows.append(
                    {
                        "abstract_call_order": order,
                        "recommended_option_id": RECOMMENDED_OPTION_ID,
                        "base_packet_slot": slot,
                        "stage": stage,
                        "evidence_condition": condition,
                        "future_call_type": "real_llm_call_only_after_explicit_approval",
                        "model_provider": "TO_BE_APPROVED_BY_USER",
                        "model_name": "TO_BE_APPROVED_BY_USER",
                        "raw_prompt_write_allowed": False,
                        "raw_response_write_allowed": False,
                        "jsonl_write_allowed": False,
                        "sanitized_parser_required": True,
                        "abort_on_parse_failure": True,
                    }
                )
    if len(rows) != RECOMMENDED_CALL_COUNT:
        die("Abstract call plan does not have 36 rows")
    return rows


def build_approval_fields() -> list[dict[str, Any]]:
    return [
        {"field": "model_provider", "required_before_execution": True, "current_value": "TO_BE_APPROVED_BY_USER", "notes": "Examples could include OpenAI, Anthropic, GLM/Z.ai, or another provider, but none is selected by this design."},
        {"field": "model_name", "required_before_execution": True, "current_value": "TO_BE_APPROVED_BY_USER", "notes": "Exact model/version must be approved before any real call."},
        {"field": "max_future_real_llm_calls", "required_before_execution": True, "current_value": RECOMMENDED_CALL_COUNT, "notes": "Recommended tiny pilot is 36 calls; user can approve fewer/more explicitly."},
        {"field": "max_cost_permission", "required_before_execution": True, "current_value": "TO_BE_APPROVED_BY_USER", "notes": "Cost must be approved after current provider pricing is checked."},
        {"field": "api_key_source", "required_before_execution": True, "current_value": "LOCAL_ENV_ONLY_NOT_COMMITTED", "notes": "No key or .env is created or committed by this task."},
        {"field": "raw_prompt_storage", "required_before_execution": True, "current_value": "FORBIDDEN", "notes": "Future runner must not write raw prompt instances."},
        {"field": "raw_response_storage", "required_before_execution": True, "current_value": "FORBIDDEN", "notes": "Future runner must not write raw model responses."},
        {"field": "jsonl_storage", "required_before_execution": True, "current_value": "FORBIDDEN", "notes": "Future runner must not write JSONL raw dumps."},
        {"field": "approval_phrase", "required_before_execution": True, "current_value": "NOT_PROVIDED", "notes": "Future execution requires a clear explicit approval phrase after model/cost/call-count are shown."},
    ]


def build_cost_template() -> list[dict[str, Any]]:
    return [
        {"item": "provider_pricing_status", "value": "NOT_CHECKED_IN_05AI", "notes": "Pricing can change; check official current pricing before execution approval."},
        {"item": "model_provider", "value": "TO_BE_APPROVED_BY_USER", "notes": "No provider selected by this design."},
        {"item": "model_name", "value": "TO_BE_APPROVED_BY_USER", "notes": "No model selected by this design."},
        {"item": "recommended_future_calls", "value": RECOMMENDED_CALL_COUNT, "notes": "36-call paired micro-pilot."},
        {"item": "estimated_input_tokens_per_call", "value": "TO_BE_MEASURED_BEFORE_EXECUTION", "notes": "Must be estimated from sanitized prompt template without writing raw prompts."},
        {"item": "estimated_output_tokens_per_call", "value": "TO_BE_APPROVED_BY_USER", "notes": "Use strict parser schema and low max output tokens."},
        {"item": "estimated_total_cost", "value": "TO_BE_CALCULATED_AFTER_MODEL_SELECTION", "notes": "Do not execute until user approves cost ceiling."},
    ]


def build_storage_policy() -> list[dict[str, Any]]:
    return [
        {"storage_item": "raw_cfpb_data", "allowed": False, "future_policy": "Never commit raw CFPB data."},
        {"storage_item": "raw_prompt_instances", "allowed": False, "future_policy": "Do not write raw prompt instances to repo."},
        {"storage_item": "raw_model_responses", "allowed": False, "future_policy": "Do not write raw model responses to repo."},
        {"storage_item": "jsonl_api_outputs", "allowed": False, "future_policy": "Do not write JSONL raw dumps."},
        {"storage_item": "env_or_secrets", "allowed": False, "future_policy": "Do not commit .env, keys, or secrets."},
        {"storage_item": "sanitized_parsed_outputs", "allowed": True, "future_policy": "Commit only after parser and safety validators pass."},
        {"storage_item": "aggregate_metrics", "allowed": True, "future_policy": "Commit only after no-raw-data and claim-boundary scans pass."},
    ]


def build_abort_conditions() -> list[dict[str, Any]]:
    return [
        {"abort_condition": "missing_explicit_user_approval", "stage": "pre_execution", "action": "hard_stop"},
        {"abort_condition": "model_provider_or_model_name_not_approved", "stage": "pre_execution", "action": "hard_stop"},
        {"abort_condition": "cost_ceiling_not_approved", "stage": "pre_execution", "action": "hard_stop"},
        {"abort_condition": "api_key_missing_or_not_local", "stage": "pre_execution", "action": "hard_stop"},
        {"abort_condition": "attempt_to_write_raw_prompt", "stage": "execution", "action": "hard_stop"},
        {"abort_condition": "attempt_to_write_raw_response", "stage": "execution", "action": "hard_stop"},
        {"abort_condition": "attempt_to_write_jsonl", "stage": "execution", "action": "hard_stop"},
        {"abort_condition": "parser_schema_failure", "stage": "post_call", "action": "stop_batch_and_report"},
        {"abort_condition": "unsafe_claim_boundary_detected", "stage": "validation", "action": "stop_before_commit"},
        {"abort_condition": "unexpected_raw_cfpb_status_entry", "stage": "validation", "action": "stop_before_commit"},
    ]


def build_sanitized_contract() -> list[dict[str, Any]]:
    return [
        {"field_group": "identifier", "required": True, "raw_sensitive": False, "notes": "Use request/evidence IDs only; no complaint IDs."},
        {"field_group": "stage", "required": True, "raw_sensitive": False, "notes": "decision/audit/escalation."},
        {"field_group": "evidence_condition", "required": True, "raw_sensitive": False, "notes": "clean/compressed/partial_dropout/noisy_conflicting."},
        {"field_group": "parsed_structured_output", "required": True, "raw_sensitive": False, "notes": "Schema-constrained fields only."},
        {"field_group": "parse_status", "required": True, "raw_sensitive": False, "notes": "Accepted/rejected with rejection reason."},
        {"field_group": "raw_prompt", "required": False, "raw_sensitive": True, "notes": "Forbidden."},
        {"field_group": "raw_response", "required": False, "raw_sensitive": True, "notes": "Forbidden."},
        {"field_group": "chain_of_thought_or_free_text_rationale", "required": False, "raw_sensitive": True, "notes": "Forbidden."},
    ]


def build_claim_boundary() -> list[dict[str, Any]]:
    return [
        {"claim_type": "allowed", "wording": "Pilot 05 has an approval-gated design for a tiny real-LLM cascade pilot."},
        {"claim_type": "allowed", "wording": "No Pilot 05 model-result evidence exists until explicitly approved execution is performed and parsed."},
        {"claim_type": "allowed", "wording": "Future real-LLM outputs, if approved, will be sanitized and parser-validated before metrics."},
        {"claim_type": "forbidden", "wording": "Do not claim deployment validity, financial/legal safety, provider superiority, or consumer harm prevalence."},
        {"claim_type": "forbidden", "wording": "Do not call the result proven, ground-breaking, or Q1-level based on design infrastructure."},
    ]


def write_report(path: Path) -> None:
    if path.exists():
        die(f"Refusing to overwrite report: {rel(path)}")
    text = f"""# Pilot 05 CFPB Tiny Real-LLM Approval Gate\n\nStatus: PASS — design only.\n\nApproval status: {APPROVAL_STATUS}.\n\nRecommended option: {RECOMMENDED_OPTION_ID}.\n\nRecommended future call count: {RECOMMENDED_CALL_COUNT}.\n\nThis task does not execute any model/API call, does not write raw prompt instances, does not write raw responses, and does not write JSONL.\n\n## Research role\n\nThis approval gate protects the transition from no-call infrastructure to a future tiny real-LLM cascade pilot. The recommended minimum credible tiny pilot is 36 calls: 3 base-packet slots x 4 evidence conditions x 3 cascade stages.\n\nA 12-call option is documented as a wiring sentinel only, but it is too weak for meaningful cascade metric claims.\n\n## Claim boundary\n\nNo Pilot 05 model-result evidence exists yet. This is an approval-gated design/checklist only.\n\nBefore any future real execution, the user must approve the exact model provider, model name, maximum call count, cost ceiling, API-key handling, and sanitized-only storage policy.\n"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    harness_manifest, readiness_manifest, plan_rows, batch_rows, readiness_rows = check_inputs()

    if OUT.exists():
        die(f"Output directory already exists: {rel(OUT)}")
    OUT.mkdir(parents=True, exist_ok=False)

    options = build_options()
    abstract_call_plan = build_abstract_call_plan()
    approval_fields = build_approval_fields()
    cost_template = build_cost_template()
    storage_policy = build_storage_policy()
    abort_conditions = build_abort_conditions()
    sanitized_contract = build_sanitized_contract()
    claim_boundary = build_claim_boundary()

    write_csv(FILES["options"], options)
    write_csv(FILES["abstract_call_plan"], abstract_call_plan)
    write_csv(FILES["approval_fields"], approval_fields)
    write_csv(FILES["cost_template"], cost_template)
    write_csv(FILES["storage_policy"], storage_policy)
    write_csv(FILES["abort_conditions"], abort_conditions)
    write_csv(FILES["sanitized_contract"], sanitized_contract)
    write_csv(FILES["claim_boundary"], claim_boundary)
    write_report(FILES["report"])

    stage_counts = Counter(row["stage"] for row in abstract_call_plan)
    condition_counts = Counter(row["evidence_condition"] for row in abstract_call_plan)
    if any(stage_counts[stage] != 12 for stage in STAGES):
        die(f"Bad abstract stage counts: {dict(stage_counts)}")
    if any(condition_counts[condition] != 9 for condition in CONDITIONS):
        die(f"Bad abstract condition counts: {dict(condition_counts)}")

    manifest = {
        "task_id": TASK_ID,
        "schema_version": "pilot_05_cfpb_tiny_llm_approval_gate_v1",
        "status": STATUS,
        "approval_status": APPROVAL_STATUS,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "approval_gate_design_only_no_call",
        "recommended_option_id": RECOMMENDED_OPTION_ID,
        "recommended_future_call_count": RECOMMENDED_CALL_COUNT,
        "claim_boundary": "No Pilot 05 model-result evidence exists yet. This task only designs the explicit approval gate for a future tiny real-LLM pilot.",
        "input_files": {name: rel(path) for name, path in INPUTS.items()},
        "output_files": {name: rel(path) for name, path in FILES.items()},
        "model_selection": {
            "model_provider": "TO_BE_APPROVED_BY_USER",
            "model_name": "TO_BE_APPROVED_BY_USER",
            "current_pricing_checked": False,
            "api_key_required_later": True,
            "api_key_storage_policy": "LOCAL_ENV_ONLY_NOT_COMMITTED",
        },
        "counts": {
            "existing_harness_plan_rows": len(plan_rows),
            "existing_harness_batch_rows": len(batch_rows),
            "existing_readiness_check_rows": len(readiness_rows),
            "pilot_option_rows": len(options),
            "recommended_abstract_call_plan_rows": len(abstract_call_plan),
            "approval_required_field_rows": len(approval_fields),
            "abort_condition_rows": len(abort_conditions),
            "abstract_stage_counts": dict(stage_counts),
            "abstract_condition_counts": dict(condition_counts),
        },
        "safety_flags": {
            "model_execution_enabled": False,
            "future_explicit_approval_required": True,
            "api_calls": 0,
            "model_calls": 0,
            "dataset_downloads": 0,
            "raw_prompt_instances_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "raw_cfpb_data_read": False,
            "raw_cfpb_data_written": False,
            "api_outputs_written": False,
            "staged_or_committed_by_script": False,
        },
    }

    if FILES["manifest"].exists():
        die(f"Refusing to overwrite manifest: {rel(FILES['manifest'])}")
    with FILES["manifest"].open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("Pilot 05 CFPB tiny real-LLM approval gate generated.")
    print(f"output_dir: {rel(OUT)}")
    print(f"status: {STATUS}")
    print(f"approval_status: {APPROVAL_STATUS}")
    print(f"recommended_option_id: {RECOMMENDED_OPTION_ID}")
    print(f"recommended_future_call_count: {RECOMMENDED_CALL_COUNT}")
    print("model_provider: TO_BE_APPROVED_BY_USER")
    print("model_name: TO_BE_APPROVED_BY_USER")
    print("model_calls: 0")
    print("api_calls: 0")
    print("raw_prompt_instances_written: False")
    print("raw_responses_written: False")
    print("jsonl_written: False")
    print("model_execution_enabled: False")
    print("future_explicit_approval_required: True")


if __name__ == "__main__":
    main()
