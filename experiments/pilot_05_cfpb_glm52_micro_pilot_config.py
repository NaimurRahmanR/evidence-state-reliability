from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_config"

TASK_ID = "05AJ-A"
MODEL_PROVIDER = "Z.ai"
MODEL_DISPLAY_NAME = "GLM-5.2"
API_MODEL_NAME = "glm-5.2"
API_BASE_URL = "https://api.z.ai/api/paas/v4"
CHAT_COMPLETIONS_ENDPOINT = "https://api.z.ai/api/paas/v4/chat/completions"
API_KEY_ENV_VAR = "ZAI_API_KEY"
MAX_CALLS = 36
MAX_COST_GBP = "3.49"
APPROVAL_STATUS = "CONFIGURED_NOT_EXECUTION_APPROVED"
FINAL_APPROVAL_PHRASE = (
    "I approve running Task 05AJ real GLM-5.2 micro-pilot: "
    "max 36 calls, max £3.49, local env key only, sanitized outputs only."
)

INPUTS = {
    "approval_gate_manifest": ROOT / "reports" / "pilot_05_cfpb_tiny_llm_approval_gate" / "pilot_05_cfpb_tiny_llm_approval_gate_manifest.json",
    "approval_required_fields": ROOT / "reports" / "pilot_05_cfpb_tiny_llm_approval_gate" / "pilot_05_cfpb_tiny_llm_approval_required_fields.csv",
    "abstract_call_plan": ROOT / "reports" / "pilot_05_cfpb_tiny_llm_approval_gate" / "pilot_05_cfpb_tiny_llm_recommended_abstract_call_plan.csv",
    "execution_plan": ROOT / "reports" / "pilot_05_cfpb_cascade_execution_harness" / "pilot_05_cfpb_cascade_execution_plan.csv",
    "readiness_validation_manifest": ROOT / "reports" / "pilot_05_cfpb_cascade_harness_readiness_validation" / "pilot_05_cfpb_cascade_harness_readiness_validation_manifest.json",
}

OUTPUTS = {
    "manifest": OUT / "pilot_05_cfpb_glm52_micro_pilot_config_manifest.json",
    "permission_config": OUT / "pilot_05_cfpb_glm52_micro_pilot_execution_permission_config.csv",
    "call_budget": OUT / "pilot_05_cfpb_glm52_micro_pilot_call_budget.csv",
    "env_requirements": OUT / "pilot_05_cfpb_glm52_micro_pilot_env_requirements.csv",
    "storage_contract": OUT / "pilot_05_cfpb_glm52_micro_pilot_storage_contract.csv",
    "final_approval_phrase": OUT / "pilot_05_cfpb_glm52_micro_pilot_final_approval_phrase.csv",
    "pre_execution_checklist": OUT / "pilot_05_cfpb_glm52_micro_pilot_pre_execution_checklist.csv",
    "report": OUT / "pilot_05_cfpb_glm52_micro_pilot_config_report.md",
}


def fail(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing CSV input: {rel(path)}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        fail(f"empty CSV input: {rel(path)}")
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing JSON input: {rel(path)}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"JSON input is not an object: {rel(path)}")
    return data


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if path.exists():
        fail(f"refusing to overwrite output: {rel(path)}")
    if not rows:
        fail(f"no rows for output: {rel(path)}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def approval_field_map(rows: list[dict[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows:
        key = row.get("field", "").strip()
        value = row.get("current_value", "").strip()
        if key:
            out[key] = value
    return out


def main() -> None:
    if OUT.exists():
        fail(f"output directory already exists: {rel(OUT)}")

    for path in INPUTS.values():
        if not path.exists():
            fail(f"missing input: {rel(path)}")

    gate_manifest = read_json(INPUTS["approval_gate_manifest"])
    approval_fields = approval_field_map(read_csv(INPUTS["approval_required_fields"]))
    abstract_plan = read_csv(INPUTS["abstract_call_plan"])
    execution_plan = read_csv(INPUTS["execution_plan"])
    readiness_manifest = read_json(INPUTS["readiness_validation_manifest"])

    if gate_manifest.get("status") != "PASS":
        fail("05AI approval gate manifest is not PASS")
    if gate_manifest.get("approval_status") != "NOT_APPROVED_DESIGN_ONLY":
        fail("05AI approval gate should still be design-only")
    if int(gate_manifest.get("recommended_future_call_count", -1)) != MAX_CALLS:
        fail("05AI recommended future call count is not 36")
    if len(abstract_plan) != MAX_CALLS:
        fail("abstract call plan does not contain 36 rows")
    if len(execution_plan) != 720:
        fail("05AG execution plan does not contain 720 rows")
    if readiness_manifest.get("status") != "PASS":
        fail("05AH readiness manifest is not PASS")

    expected_pending_fields = {
        "model_provider": "TO_BE_APPROVED_BY_USER",
        "model_name": "TO_BE_APPROVED_BY_USER",
        "max_future_real_llm_calls": "36",
        "max_cost_permission": "TO_BE_APPROVED_BY_USER",
        "api_key_source": "LOCAL_ENV_ONLY_NOT_COMMITTED",
        "raw_prompt_storage": "FORBIDDEN",
        "raw_response_storage": "FORBIDDEN",
        "jsonl_storage": "FORBIDDEN",
        "approval_phrase": "NOT_PROVIDED",
    }
    for key, expected in expected_pending_fields.items():
        observed = approval_fields.get(key)
        if observed != expected:
            fail(f"approval field {key} expected {expected}, found {observed}")

    stage_counts: dict[str, int] = {"decision": 0, "audit": 0, "escalation": 0}
    for row in abstract_plan:
        stage = row.get("stage", "")
        if stage not in stage_counts:
            fail(f"unexpected abstract plan stage: {stage}")
        stage_counts[stage] += 1
    if stage_counts != {"decision": 12, "audit": 12, "escalation": 12}:
        fail(f"unexpected stage counts: {stage_counts}")

    permission_rows = [
        {"field": "model_provider", "configured_value": MODEL_PROVIDER, "source": "user_approved", "execution_ready": False},
        {"field": "model_display_name", "configured_value": MODEL_DISPLAY_NAME, "source": "user_approved", "execution_ready": False},
        {"field": "api_model_name", "configured_value": API_MODEL_NAME, "source": "official_docs_checked", "execution_ready": False},
        {"field": "api_base_url", "configured_value": API_BASE_URL, "source": "official_docs_checked", "execution_ready": False},
        {"field": "chat_completions_endpoint", "configured_value": CHAT_COMPLETIONS_ENDPOINT, "source": "official_docs_checked", "execution_ready": False},
        {"field": "max_future_real_llm_calls", "configured_value": MAX_CALLS, "source": "05AI_gate", "execution_ready": False},
        {"field": "max_cost_permission_gbp", "configured_value": MAX_COST_GBP, "source": "user_approved", "execution_ready": False},
        {"field": "api_key_source", "configured_value": "LOCAL_ENV_ONLY_NOT_COMMITTED", "source": "project_policy", "execution_ready": False},
        {"field": "api_key_env_var", "configured_value": API_KEY_ENV_VAR, "source": "local_runtime_only", "execution_ready": False},
        {"field": "approval_status", "configured_value": APPROVAL_STATUS, "source": "05AJ-A", "execution_ready": False},
    ]

    call_budget_rows = [
        {"budget_item": "maximum_real_llm_calls", "value": MAX_CALLS, "unit": "calls", "status": "CONFIGURED_NOT_RUN"},
        {"budget_item": "decision_stage_calls", "value": 12, "unit": "calls", "status": "CONFIGURED_NOT_RUN"},
        {"budget_item": "audit_stage_calls", "value": 12, "unit": "calls", "status": "CONFIGURED_NOT_RUN"},
        {"budget_item": "escalation_stage_calls", "value": 12, "unit": "calls", "status": "CONFIGURED_NOT_RUN"},
    ]

    env_rows = [
        {"requirement": "api_key_env_var", "value": API_KEY_ENV_VAR, "allowed_to_commit": False, "notes": "Key must exist only in local environment."},
        {"requirement": "env_file", "value": ".env", "allowed_to_commit": False, "notes": ".env must not be created or committed by this task."},
        {"requirement": "api_base_url", "value": API_BASE_URL, "allowed_to_commit": True, "notes": "Endpoint URL is not a secret."},
    ]

    storage_rows = [
        {"storage_item": "raw_prompt_instances", "policy": "FORBIDDEN", "commit_allowed": False},
        {"storage_item": "raw_model_responses", "policy": "FORBIDDEN", "commit_allowed": False},
        {"storage_item": "jsonl_outputs", "policy": "FORBIDDEN", "commit_allowed": False},
        {"storage_item": "api_outputs", "policy": "FORBIDDEN", "commit_allowed": False},
        {"storage_item": "sanitized_parsed_outputs", "policy": "ALLOWED_AFTER_VALIDATION", "commit_allowed": True},
        {"storage_item": "execution_manifest_without_raw_payloads", "policy": "ALLOWED_AFTER_VALIDATION", "commit_allowed": True},
    ]

    approval_phrase_rows = [
        {
            "required_before_execution": True,
            "approval_phrase": FINAL_APPROVAL_PHRASE,
            "current_status": "NOT_PROVIDED_IN_TERMINAL_FOR_EXECUTION",
            "notes": "This exact phrase is required before a future real-call runner may execute GLM-5.2 calls.",
        }
    ]

    checklist_rows = [
        {"check": "repo_clean", "required_before_execution": True, "status_now": "NOT_CHECKED_BY_CONFIG_ONLY"},
        {"check": "latest_commit_is_05AJ_A_or_later", "required_before_execution": True, "status_now": "NOT_COMMITTED_YET"},
        {"check": "ZAI_API_KEY_present_in_local_env", "required_before_execution": True, "status_now": "NOT_CHECKED_TO_AVOID_SECRET_ACCESS"},
        {"check": "max_calls_36", "required_before_execution": True, "status_now": "CONFIGURED"},
        {"check": "max_cost_gbp_3_49", "required_before_execution": True, "status_now": "CONFIGURED"},
        {"check": "raw_prompt_storage_forbidden", "required_before_execution": True, "status_now": "CONFIGURED"},
        {"check": "raw_response_storage_forbidden", "required_before_execution": True, "status_now": "CONFIGURED"},
        {"check": "jsonl_storage_forbidden", "required_before_execution": True, "status_now": "CONFIGURED"},
        {"check": "final_approval_phrase_provided", "required_before_execution": True, "status_now": "NOT_PROVIDED"},
    ]

    OUT.mkdir(parents=True, exist_ok=False)
    write_csv(OUTPUTS["permission_config"], permission_rows)
    write_csv(OUTPUTS["call_budget"], call_budget_rows)
    write_csv(OUTPUTS["env_requirements"], env_rows)
    write_csv(OUTPUTS["storage_contract"], storage_rows)
    write_csv(OUTPUTS["final_approval_phrase"], approval_phrase_rows)
    write_csv(OUTPUTS["pre_execution_checklist"], checklist_rows)

    report = f"""# Pilot 05 CFPB GLM-5.2 Micro-Pilot Configuration\n\nStatus: PASS\n\nThis task configures a future GLM-5.2 micro-pilot but does not execute it.\n\nConfigured values:\n\n- Provider: {MODEL_PROVIDER}\n- Model display name: {MODEL_DISPLAY_NAME}\n- API model name: `{API_MODEL_NAME}`\n- Maximum future calls: {MAX_CALLS}\n- Maximum user-approved cost: £{MAX_COST_GBP}\n- API key source: local environment only (`{API_KEY_ENV_VAR}`)\n\nSafety boundary:\n\n- No API calls were made.\n- No model calls were made.\n- No raw prompts were written.\n- No raw responses were written.\n- No JSONL files were written.\n- Future execution still requires the exact approval phrase in the generated approval phrase CSV.\n"""
    if OUTPUTS["report"].exists():
        fail(f"refusing to overwrite report: {rel(OUTPUTS['report'])}")
    OUTPUTS["report"].write_text(report, encoding="utf-8")

    output_file_list = [rel(path) for path in OUTPUTS.values()]
    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "approval_status": APPROVAL_STATUS,
        "model_provider": MODEL_PROVIDER,
        "model_display_name": MODEL_DISPLAY_NAME,
        "api_model_name": API_MODEL_NAME,
        "api_base_url": API_BASE_URL,
        "chat_completions_endpoint": CHAT_COMPLETIONS_ENDPOINT,
        "max_future_real_llm_calls": MAX_CALLS,
        "max_cost_permission_gbp": MAX_COST_GBP,
        "api_key_source": "LOCAL_ENV_ONLY_NOT_COMMITTED",
        "api_key_env_var": API_KEY_ENV_VAR,
        "abstract_plan_rows": len(abstract_plan),
        "abstract_plan_stage_counts": stage_counts,
        "input_files": {key: rel(path) for key, path in INPUTS.items()},
        "output_files": output_file_list,
        "future_explicit_execution_approval_required": True,
        "required_final_approval_phrase": FINAL_APPROVAL_PHRASE,
        "claim_boundary": "This task configures a future GLM-5.2 micro-pilot only. It creates no Pilot 05 model-result evidence.",
        "safety_flags": {
            "model_execution_enabled": False,
            "api_calls": 0,
            "model_calls": 0,
            "raw_prompt_instances_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "raw_cfpb_data_read": False,
            "raw_cfpb_data_written": False,
            "api_outputs_written": False,
            "staged_or_committed_by_script": False,
        },
    }
    if OUTPUTS["manifest"].exists():
        fail(f"refusing to overwrite manifest: {rel(OUTPUTS['manifest'])}")
    with OUTPUTS["manifest"].open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("Pilot 05 CFPB GLM-5.2 micro-pilot configuration generated.")
    print(f"output_dir: {rel(OUT)}")
    print("status: PASS")
    print(f"approval_status: {APPROVAL_STATUS}")
    print(f"model_provider: {MODEL_PROVIDER}")
    print(f"model_display_name: {MODEL_DISPLAY_NAME}")
    print(f"api_model_name: {API_MODEL_NAME}")
    print(f"max_future_real_llm_calls: {MAX_CALLS}")
    print(f"max_cost_permission_gbp: {MAX_COST_GBP}")
    print("api_key_source: LOCAL_ENV_ONLY_NOT_COMMITTED")
    print("model_calls: 0")
    print("api_calls: 0")
    print("raw_prompt_instances_written: False")
    print("raw_responses_written: False")
    print("jsonl_written: False")
    print("model_execution_enabled: False")
    print("future_explicit_execution_approval_required: True")


if __name__ == "__main__":
    main()
