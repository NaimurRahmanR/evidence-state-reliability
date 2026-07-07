from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "05AJ-B"
ROOT = Path(__file__).resolve().parents[1]

MODEL_PROVIDER = "Z.ai"
MODEL_DISPLAY_NAME = "GLM-5.2"
API_MODEL_NAME = "glm-5.2"
API_BASE_URL = "https://api.z.ai/api/paas/v4"
CHAT_COMPLETIONS_PATH = "/chat/completions"
MAX_CALLS = 36
MAX_COST_GBP = 3.49
API_KEY_ENV = "ZAI_API_KEY"

CONFIG_DIR = ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_config"
APPROVAL_GATE_DIR = ROOT / "reports" / "pilot_05_cfpb_tiny_llm_approval_gate"
HARNESS_DIR = ROOT / "reports" / "pilot_05_cfpb_cascade_execution_harness"
SCAFFOLD_DIR = ROOT / "reports" / "pilot_05_cfpb_cascade_scaffold"
EVIDENCE_DIR = ROOT / "reports" / "pilot_05_cfpb_evidence_state_conditions"

CONFIG_MANIFEST = CONFIG_DIR / "pilot_05_cfpb_glm52_micro_pilot_config_manifest.json"
APPROVAL_PHRASE_CSV = CONFIG_DIR / "pilot_05_cfpb_glm52_micro_pilot_final_approval_phrase.csv"
STORAGE_CONTRACT_CSV = CONFIG_DIR / "pilot_05_cfpb_glm52_micro_pilot_storage_contract.csv"
ABSTRACT_CALL_PLAN_CSV = APPROVAL_GATE_DIR / "pilot_05_cfpb_tiny_llm_recommended_abstract_call_plan.csv"
HARNESS_EXECUTION_PLAN_CSV = HARNESS_DIR / "pilot_05_cfpb_cascade_execution_plan.csv"
PROMPT_TEMPLATES_JSON = SCAFFOLD_DIR / "pilot_05_cfpb_cascade_prompt_templates.json"
RESPONSE_SCHEMA_JSON = SCAFFOLD_DIR / "pilot_05_cfpb_cascade_response_schema.json"
PARSER_RULES_CSV = SCAFFOLD_DIR / "pilot_05_cfpb_cascade_parser_validation_rules.csv"
EVIDENCE_ROWS_CSV = EVIDENCE_DIR / "pilot_05_cfpb_evidence_state_conditions.csv"
PARSER_SCRIPT = ROOT / "experiments" / "pilot_05_cfpb_cascade_response_parser.py"

OUT = ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_runner_build"
MANIFEST_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_manifest.json"
PREFLIGHT_CHECKS_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_preflight_checks.csv"
RUNNER_PLAN_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_execution_plan.csv"
ENV_GATE_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_env_gate.csv"
STORAGE_POLICY_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_storage_policy.csv"
SANITIZED_SCHEMA_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_sanitized_output_schema.csv"
ABORT_CONDITIONS_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_abort_conditions.csv"
REPORT_OUT = OUT / "pilot_05_cfpb_glm52_micro_pilot_runner_report.md"


def fail(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"Missing CSV input: {rel(path)}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        fail(f"No rows in CSV input: {rel(path)}")
    return rows


def read_json(path: Path) -> Any:
    if not path.exists():
        fail(f"Missing JSON input: {rel(path)}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if path.exists():
        fail(f"Refusing to overwrite output: {rel(path)}")
    if not rows:
        fail(f"Refusing to write empty CSV: {rel(path)}")
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, obj: dict[str, Any]) -> None:
    if path.exists():
        fail(f"Refusing to overwrite output: {rel(path)}")
    with path.open("w", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, sort_keys=True)
        handle.write("\n")


def pick_col(rows: list[dict[str, str]], candidates: tuple[str, ...], contains: tuple[str, ...], purpose: str) -> str:
    columns = list(rows[0].keys())
    normalized = {norm(col): col for col in columns}
    for candidate in candidates:
        key = norm(candidate)
        if key in normalized:
            return normalized[key]
    for col in columns:
        col_norm = norm(col)
        if all(term in col_norm for term in contains):
            return col
    fail(f"Could not find column for {purpose}. Available columns: {columns}")
    return ""


def get_approval_phrase(rows: list[dict[str, str]]) -> str:
    for row in rows:
        for key, value in row.items():
            if norm(key) == "approval_phrase":
                return value.strip()
        values = list(row.values())
        if len(values) >= 2 and "approve running task 05aj" in values[-1].lower():
            return values[-1].strip()
    serialized = json.dumps(rows, ensure_ascii=False)
    match = re.search(r"I approve running Task 05AJ[^,\n]*(?:,[^\n]*)?", serialized)
    if match:
        return match.group(0).strip()
    fail("Could not find final approval phrase in config CSV.")


def validate_config_manifest(config: dict[str, Any]) -> None:
    expected = {
        "status": "PASS",
        "approval_status": "CONFIGURED_NOT_EXECUTION_APPROVED",
        "model_provider": MODEL_PROVIDER,
        "model_display_name": MODEL_DISPLAY_NAME,
        "api_model_name": API_MODEL_NAME,
        "api_key_source": "LOCAL_ENV_ONLY_NOT_COMMITTED",
    }
    for key, value in expected.items():
        if str(config.get(key)) != str(value):
            fail(f"Config manifest mismatch for {key}: expected {value}, found {config.get(key)}")
    if int(config.get("max_future_real_llm_calls", -1)) != MAX_CALLS:
        fail("Config manifest max_future_real_llm_calls mismatch.")
    if float(config.get("max_cost_permission_gbp", -1)) != MAX_COST_GBP:
        fail("Config manifest max_cost_permission_gbp mismatch.")

    safety = config.get("safety_flags", {})
    checks = {
        "model_calls": 0,
        "api_calls": 0,
        "raw_prompt_instances_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "model_execution_enabled": False,
        "future_explicit_execution_approval_required": True,
    }
    for key, value in checks.items():
        observed = safety.get(key, config.get(key))
        if str(observed) != str(value):
            fail(f"Config safety mismatch for {key}: expected {value}, found {observed}")


def validate_storage_contract(rows: list[dict[str, str]]) -> None:
    serialized = json.dumps(rows, ensure_ascii=False).lower()

    # The committed 05AJ-A storage contract uses explicit artifact names such as
    # raw_prompt_instances and raw_model_responses. Accept the semantic family
    # rather than requiring one brittle singular token. This remains conservative:
    # raw prompt storage, raw response storage, JSONL storage, and sanitized-only
    # output policy must all be represented before the runner can build.
    token_groups = {
        "raw_prompt_family": ("raw_prompt", "raw_prompts", "raw_prompt_instances"),
        "raw_response_family": ("raw_response", "raw_responses", "raw_model_response", "raw_model_responses"),
        "jsonl_family": ("jsonl", "jsonl_outputs"),
        "forbidden_policy": ("forbidden",),
        "sanitized_policy": ("sanitized", "sanitized_parsed_outputs"),
    }

    for group_name, tokens in token_groups.items():
        if not any(token in serialized for token in tokens):
            fail(f"Storage contract missing semantic token group: {group_name}")


def build_runner_plan(abstract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    stage_col = pick_col(abstract_rows, ("stage", "cascade_stage", "request_stage"), ("stage",), "abstract call stage")
    condition_col = pick_col(
        abstract_rows,
        ("evidence_condition", "condition", "degradation_condition", "evidence_state_condition"),
        ("condition",),
        "abstract call condition",
    )

    rows: list[dict[str, Any]] = []
    stage_counts: dict[str, int] = {"decision": 0, "audit": 0, "escalation": 0}

    for index, row in enumerate(abstract_rows, start=1):
        stage = norm(row.get(stage_col, ""))
        condition = norm(row.get(condition_col, ""))
        if stage not in stage_counts:
            fail(f"Unexpected stage in abstract call plan: {stage}")
        if condition not in {"clean", "compressed", "partial_dropout", "noisy_conflicting"}:
            fail(f"Unexpected condition in abstract call plan: {condition}")

        stage_counts[stage] += 1
        rows.append(
            {
                "runner_call_order": index,
                "runner_call_id": f"pilot05_glm52_micro_{index:04d}",
                "stage": stage,
                "evidence_condition": condition,
                "api_model_name": API_MODEL_NAME,
                "api_endpoint": API_BASE_URL + CHAT_COMPLETIONS_PATH,
                "execution_mode": "future_real_call_requires_exact_approval",
                "approval_phrase_required": True,
                "api_key_env_required": API_KEY_ENV,
                "raw_prompt_storage": "FORBIDDEN",
                "raw_response_storage": "FORBIDDEN",
                "jsonl_storage": "FORBIDDEN",
                "sanitized_output_only": True,
                "model_call_allowed_now": False,
            }
        )

    if len(rows) != MAX_CALLS:
        fail(f"Runner plan expected {MAX_CALLS} rows, found {len(rows)}")
    for stage, count in stage_counts.items():
        if count != 12:
            fail(f"Runner plan expected 12 rows for stage {stage}, found {count}")

    return rows


def make_preflight_checks(
    config: dict[str, Any],
    approval_phrase: str,
    abstract_rows: list[dict[str, str]],
    harness_rows: list[dict[str, str]],
    prompt_templates: Any,
    response_schema: Any,
    parser_rules: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(category: str, check: str, observed: Any, expected: Any, status: str = "PASS", notes: str = "") -> None:
        checks.append(
            {
                "category": category,
                "check": check,
                "observed": observed,
                "expected": expected,
                "status": status,
                "notes": notes,
            }
        )

    add("config", "status", config.get("status"), "PASS")
    add("config", "approval_status", config.get("approval_status"), "CONFIGURED_NOT_EXECUTION_APPROVED")
    add("config", "model_provider", config.get("model_provider"), MODEL_PROVIDER)
    add("config", "model_display_name", config.get("model_display_name"), MODEL_DISPLAY_NAME)
    add("config", "api_model_name", config.get("api_model_name"), API_MODEL_NAME)
    add("config", "max_future_real_llm_calls", config.get("max_future_real_llm_calls"), MAX_CALLS)
    add("config", "max_cost_permission_gbp", config.get("max_cost_permission_gbp"), MAX_COST_GBP)

    add("approval", "approval_phrase_present", bool(approval_phrase), True)
    add("approval", "approval_phrase_contains_task", "Task 05AJ" in approval_phrase, True)
    add("approval", "approval_phrase_contains_model", "GLM-5.2" in approval_phrase, True)
    add("approval", "approval_phrase_contains_36", "36" in approval_phrase, True)
    add("approval", "approval_phrase_contains_3.49", "3.49" in approval_phrase, True)
    add("approval", "approval_phrase_contains_sanitized", "sanitized" in approval_phrase.lower(), True)

    add("inputs", "abstract_call_plan_rows", len(abstract_rows), MAX_CALLS)
    add("inputs", "harness_execution_plan_rows", len(harness_rows), 720)
    add("inputs", "parser_rule_rows", len(parser_rules), 17)
    add("inputs", "evidence_rows", len(evidence_rows), 240)
    add("inputs", "prompt_templates_loaded", bool(prompt_templates), True)
    add("inputs", "response_schema_loaded", bool(response_schema), True)

    add("runner_gate", "build_mode_reads_api_key", False, False)
    add("runner_gate", "build_mode_model_calls", 0, 0)
    add("runner_gate", "build_mode_api_calls", 0, 0)
    add("runner_gate", "raw_prompt_storage", "FORBIDDEN", "FORBIDDEN")
    add("runner_gate", "raw_response_storage", "FORBIDDEN", "FORBIDDEN")
    add("runner_gate", "jsonl_storage", "FORBIDDEN", "FORBIDDEN")
    add("runner_gate", "future_exact_approval_required", True, True)

    for row in checks:
        if str(row["observed"]) != str(row["expected"]):
            row["status"] = "FAIL"

    return checks


def build_env_gate() -> list[dict[str, Any]]:
    return [
        {
            "requirement": "api_key_environment_variable",
            "name": API_KEY_ENV,
            "required_for_build_only": False,
            "required_for_real_execution": True,
            "read_in_build_only_mode": False,
            "commit_allowed": False,
            "notes": "Key must stay local and must never be committed.",
        },
        {
            "requirement": "exact_approval_phrase",
            "name": "PILOT_05AJ_APPROVAL_PHRASE or --approval-phrase",
            "required_for_build_only": False,
            "required_for_real_execution": True,
            "read_in_build_only_mode": False,
            "commit_allowed": False,
            "notes": "Must exactly match the committed approval phrase before future real execution.",
        },
        {
            "requirement": "explicit_execute_mode",
            "name": "--mode execute",
            "required_for_build_only": False,
            "required_for_real_execution": True,
            "read_in_build_only_mode": False,
            "commit_allowed": True,
            "notes": "Default mode is build_only and cannot call the API.",
        },
    ]


def build_storage_policy() -> list[dict[str, Any]]:
    return [
        {"artifact": "raw_prompt_instances", "storage": "FORBIDDEN", "future_execution": "in_memory_only", "commit_allowed": False},
        {"artifact": "raw_model_responses", "storage": "FORBIDDEN", "future_execution": "in_memory_only_for_parse_then_discard", "commit_allowed": False},
        {"artifact": "jsonl_outputs", "storage": "FORBIDDEN", "future_execution": "not_written", "commit_allowed": False},
        {"artifact": "api_keys_or_env_files", "storage": "FORBIDDEN", "future_execution": "local_environment_only", "commit_allowed": False},
        {"artifact": "sanitized_parsed_outputs_csv", "storage": "ALLOWED_AFTER_VALIDATION", "future_execution": "write_only_sanitized_fields", "commit_allowed": True},
        {"artifact": "execution_audit_manifest", "storage": "ALLOWED_AFTER_VALIDATION", "future_execution": "counts_flags_no_raw_content", "commit_allowed": True},
    ]


def build_sanitized_schema() -> list[dict[str, Any]]:
    fields = [
        ("runner_call_id", "string", "Synthetic call identifier; no raw prompt or raw response."),
        ("stage", "enum", "decision/audit/escalation."),
        ("evidence_condition", "enum", "clean/compressed/partial_dropout/noisy_conflicting."),
        ("model_provider", "string", "Z.ai."),
        ("api_model_name", "string", "glm-5.2."),
        ("request_succeeded", "boolean", "Whether the HTTP call succeeded."),
        ("parser_status", "enum", "PASS/FAIL/NOT_RUN."),
        ("schema_valid", "boolean", "Whether parsed output passed schema validation."),
        ("parsed_decision_label", "sanitized_enum_or_blank", "Parsed label only; no free-text response."),
        ("parsed_confidence_band", "sanitized_enum_or_blank", "Parsed confidence band only."),
        ("parsed_audit_label", "sanitized_enum_or_blank", "Parsed audit label only."),
        ("parsed_escalation_label", "sanitized_enum_or_blank", "Parsed escalation label only."),
        ("error_category", "sanitized_enum_or_blank", "Transport/parser/schema/cost/approval category only."),
        ("raw_prompt_written", "boolean", "Always False."),
        ("raw_response_written", "boolean", "Always False."),
        ("jsonl_written", "boolean", "Always False."),
    ]
    return [{"field": a, "type": b, "notes": c} for a, b, c in fields]


def build_abort_conditions() -> list[dict[str, Any]]:
    return [
        {"abort_condition": "approval_phrase_missing_or_mismatch", "action": "hard_stop_before_api_call"},
        {"abort_condition": f"{API_KEY_ENV}_missing", "action": "hard_stop_before_api_call"},
        {"abort_condition": "planned_call_count_not_36", "action": "hard_stop_before_api_call"},
        {"abort_condition": "raw_prompt_storage_requested", "action": "hard_stop"},
        {"abort_condition": "raw_response_storage_requested", "action": "hard_stop"},
        {"abort_condition": "jsonl_storage_requested", "action": "hard_stop"},
        {"abort_condition": "estimated_or_actual_cost_exceeds_3.49_gbp", "action": "hard_stop"},
        {"abort_condition": "parser_contract_missing", "action": "hard_stop_before_api_call"},
        {"abort_condition": "unexpected_stage_or_condition", "action": "hard_stop_before_api_call"},
    ]


def build_report(approval_phrase: str) -> str:
    return (
        "# Pilot 05 CFPB GLM-5.2 Micro-Pilot Runner Build\n\n"
        "Status: PASS\n\n"
        "This task builds an approval-gated real GLM-5.2 micro-pilot runner in no-call mode. "
        "It does not read an API key, does not call the model, and does not write raw prompts, raw responses, or JSONL files.\n\n"
        "Configured future execution boundary:\n\n"
        "- Provider: Z.ai\n"
        "- Model display name: GLM-5.2\n"
        "- API model name: glm-5.2\n"
        "- Future call cap: 36\n"
        "- Future cost cap: GBP 3.49\n"
        "- API key source: local environment only, not committed\n"
        "- Storage: sanitized parsed outputs only\n\n"
        "Required future approval phrase:\n\n"
        f"`{approval_phrase}`\n\n"
        "Research claim boundary: this commit would add only an execution-capable, approval-gated runner. "
        "No Pilot 05 model-result evidence exists until a future explicitly approved execution task runs and parsed sanitized outputs are validated.\n"
    )


def run_build_only() -> None:
    if OUT.exists():
        fail(f"Output directory already exists: {rel(OUT)}")

    config = read_json(CONFIG_MANIFEST)
    validate_config_manifest(config)

    approval_rows = read_csv_rows(APPROVAL_PHRASE_CSV)
    approval_phrase = get_approval_phrase(approval_rows)

    storage_contract = read_csv_rows(STORAGE_CONTRACT_CSV)
    validate_storage_contract(storage_contract)

    abstract_rows = read_csv_rows(ABSTRACT_CALL_PLAN_CSV)
    harness_rows = read_csv_rows(HARNESS_EXECUTION_PLAN_CSV)
    prompt_templates = read_json(PROMPT_TEMPLATES_JSON)
    response_schema = read_json(RESPONSE_SCHEMA_JSON)
    parser_rules = read_csv_rows(PARSER_RULES_CSV)
    evidence_rows = read_csv_rows(EVIDENCE_ROWS_CSV)

    runner_plan = build_runner_plan(abstract_rows)
    checks = make_preflight_checks(
        config=config,
        approval_phrase=approval_phrase,
        abstract_rows=abstract_rows,
        harness_rows=harness_rows,
        prompt_templates=prompt_templates,
        response_schema=response_schema,
        parser_rules=parser_rules,
        evidence_rows=evidence_rows,
    )

    failed_checks = [row for row in checks if row["status"] != "PASS"]
    if failed_checks:
        fail(f"Preflight checks failed: {failed_checks}")

    env_gate = build_env_gate()
    storage_policy = build_storage_policy()
    sanitized_schema = build_sanitized_schema()
    abort_conditions = build_abort_conditions()

    OUT.mkdir(parents=True, exist_ok=False)

    write_csv(PREFLIGHT_CHECKS_OUT, checks)
    write_csv(RUNNER_PLAN_OUT, runner_plan)
    write_csv(ENV_GATE_OUT, env_gate)
    write_csv(STORAGE_POLICY_OUT, storage_policy)
    write_csv(SANITIZED_SCHEMA_OUT, sanitized_schema)
    write_csv(ABORT_CONDITIONS_OUT, abort_conditions)
    REPORT_OUT.write_text(build_report(approval_phrase), encoding="utf-8")

    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_utc": now_utc(),
        "runner_mode": "BUILD_ONLY_NO_CALL",
        "model_provider": MODEL_PROVIDER,
        "model_display_name": MODEL_DISPLAY_NAME,
        "api_model_name": API_MODEL_NAME,
        "api_base_url": API_BASE_URL,
        "chat_completions_path": CHAT_COMPLETIONS_PATH,
        "configured_call_count": len(runner_plan),
        "max_cost_permission_gbp": MAX_COST_GBP,
        "api_key_env": API_KEY_ENV,
        "approval_phrase_required": True,
        "approval_phrase_sha256": hashlib.sha256(approval_phrase.encode("utf-8")).hexdigest(),
        "preflight_check_rows": len(checks),
        "failed_preflight_checks": len(failed_checks),
        "input_files": {
            "config_manifest": rel(CONFIG_MANIFEST),
            "approval_phrase": rel(APPROVAL_PHRASE_CSV),
            "storage_contract": rel(STORAGE_CONTRACT_CSV),
            "abstract_call_plan": rel(ABSTRACT_CALL_PLAN_CSV),
            "harness_execution_plan": rel(HARNESS_EXECUTION_PLAN_CSV),
            "prompt_templates": rel(PROMPT_TEMPLATES_JSON),
            "response_schema": rel(RESPONSE_SCHEMA_JSON),
            "parser_rules": rel(PARSER_RULES_CSV),
            "evidence_rows": rel(EVIDENCE_ROWS_CSV),
            "parser_script": rel(PARSER_SCRIPT),
        },
        "output_files": [
            rel(MANIFEST_OUT),
            rel(PREFLIGHT_CHECKS_OUT),
            rel(RUNNER_PLAN_OUT),
            rel(ENV_GATE_OUT),
            rel(STORAGE_POLICY_OUT),
            rel(SANITIZED_SCHEMA_OUT),
            rel(ABORT_CONDITIONS_OUT),
            rel(REPORT_OUT),
        ],
        "safety_flags": {
            "api_key_read": False,
            "model_execution_enabled": False,
            "model_calls": 0,
            "api_calls": 0,
            "raw_prompt_instances_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "raw_cfpb_data_read": False,
            "raw_cfpb_data_written": False,
            "staged_or_committed_by_script": False,
        },
    }
    write_json(MANIFEST_OUT, manifest)

    print("Pilot 05 CFPB GLM-5.2 approval-gated runner build generated.")
    print(f"output_dir: {rel(OUT)}")
    print("status: PASS")
    print("runner_mode: BUILD_ONLY_NO_CALL")
    print(f"model_provider: {MODEL_PROVIDER}")
    print(f"model_display_name: {MODEL_DISPLAY_NAME}")
    print(f"api_model_name: {API_MODEL_NAME}")
    print(f"configured_call_count: {len(runner_plan)}")
    print(f"max_cost_permission_gbp: {MAX_COST_GBP}")
    print("api_key_read: False")
    print("model_calls: 0")
    print("api_calls: 0")
    print("raw_prompt_instances_written: False")
    print("raw_responses_written: False")
    print("jsonl_written: False")
    print("model_execution_enabled: False")
    print("future_exact_approval_required: True")


def run_execute(_: argparse.Namespace) -> None:
    fail(
        "Real execution is intentionally not performed by Task 05AJ-B. "
        "This committed runner must first be reviewed and committed. "
        "A later task may enable execution only with the exact approval phrase, "
        f"{API_KEY_ENV} present locally, and sanitized-output-only storage."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("build_only", "execute"), default="build_only")
    parser.add_argument("--approval-phrase", default="")
    args = parser.parse_args()

    if args.mode == "build_only":
        run_build_only()
    else:
        run_execute(args)


if __name__ == "__main__":
    main()
