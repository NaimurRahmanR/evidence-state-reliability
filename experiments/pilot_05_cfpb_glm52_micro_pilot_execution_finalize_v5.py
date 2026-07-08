from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

TASK_ID = "05AJ-C-V5"
REPO = Path.cwd()
V4_DIR = REPO / "reports" / "pilot_05_cfpb_glm52_micro_pilot_execution_recovery_v4"
OUT_DIR = REPO / "reports" / "pilot_05_cfpb_glm52_micro_pilot_execution_finalization_v5"
APPROVED_CALL_CAP = 36
PRIOR_CALLS_FROM_FAILED_V3 = 3
RECOVERY_CALLS_FROM_V4 = 33
TOTAL_APPROVED_CALL_ATTEMPTS_CONSUMED = 36


def fail(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str] | None = None) -> None:
    if fieldnames is None:
        keys: List[str] = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe_lower(s: Any) -> str:
    return str(s).lower()


def inventory_files() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(V4_DIR.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(REPO).as_posix()
        suffix = path.suffix.lower()
        name_l = path.name.lower()
        # Legitimate 'audit' is allowed. Forbid only actual raw/secret artifact families.
        forbidden_reason = ""
        forbidden_name_tokens = [
            "raw_prompt",
            "raw_prompts",
            "raw_response",
            "raw_responses",
            "raw_completion",
            "request_body",
            "response_body",
            "api_key",
            "zai_api_key",
            "secret",
            "bearer",
        ]
        if suffix == ".jsonl":
            forbidden_reason = "jsonl_artifact"
        elif path.name == ".env" or rel.endswith("/.env"):
            forbidden_reason = "env_file"
        else:
            for token in forbidden_name_tokens:
                if token in name_l:
                    forbidden_reason = f"forbidden_filename_token:{token}"
                    break
        rows.append(
            {
                "relative_path": rel,
                "filename": path.name,
                "extension": suffix,
                "size_bytes": path.stat().st_size,
                "forbidden_reason": forbidden_reason,
                "audit_filename_allowed": bool("audit" in name_l and not forbidden_reason),
            }
        )
    return rows


def scan_file_content_safety(paths: List[Path]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    risky_content_tokens = ["ZAI_API_KEY=", "Authorization: Bearer", "Bearer "]
    raw_content_tokens = ["raw_prompt_text", "raw_response_text", "full_raw_response", "full_prompt_text"]
    for path in paths:
        if path.suffix.lower() not in {".csv", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(REPO).as_posix()
        for token in risky_content_tokens + raw_content_tokens:
            if token in text:
                checks.append({"relative_path": rel, "token": token, "status": "FAIL"})
    return checks


def collect_manifest_facts() -> Dict[str, Any]:
    facts: Dict[str, Any] = {}
    manifest_paths = sorted(V4_DIR.glob("*manifest*.json"))
    if manifest_paths:
        facts["manifest_path"] = manifest_paths[0].relative_to(REPO).as_posix()
        try:
            data = read_json(manifest_paths[0])
            facts["manifest_status"] = data.get("status", "")
            facts["manifest_runner_or_execution_mode"] = data.get("runner_mode", data.get("execution_mode", ""))
            facts["manifest_model_provider"] = data.get("model_provider", "")
            facts["manifest_model_display_name"] = data.get("model_display_name", "")
            facts["manifest_api_model_name"] = data.get("api_model_name", "")
            facts["manifest_model_calls"] = data.get("model_calls", data.get("api_calls", ""))
            facts["manifest_api_calls"] = data.get("api_calls", "")
            facts["manifest_raw_prompt_instances_written"] = data.get("raw_prompt_instances_written", "")
            facts["manifest_raw_responses_written"] = data.get("raw_responses_written", "")
            facts["manifest_jsonl_written"] = data.get("jsonl_written", "")
        except Exception as exc:  # noqa: BLE001
            facts["manifest_read_error"] = str(exc)
    return facts


def collect_csv_row_summary() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    summary_rows: List[Dict[str, Any]] = []
    aggregate: Dict[str, Any] = {
        "csv_files": 0,
        "total_csv_rows": 0,
        "largest_candidate_call_table_rows": 0,
        "largest_candidate_call_table": "",
        "parse_valid_true_rows": 0,
        "parse_valid_false_rows": 0,
        "stages_seen": "",
    }
    stages = set()
    for path in sorted(V4_DIR.glob("*.csv")):
        try:
            rows = read_csv_rows(path)
        except Exception as exc:  # noqa: BLE001
            summary_rows.append(
                {
                    "relative_path": path.relative_to(REPO).as_posix(),
                    "row_count": "READ_ERROR",
                    "columns": "",
                    "candidate_call_table": False,
                    "error": str(exc),
                }
            )
            continue
        aggregate["csv_files"] += 1
        aggregate["total_csv_rows"] += len(rows)
        columns = list(rows[0].keys()) if rows else []
        lower_cols = {c.lower() for c in columns}
        is_candidate = bool({"stage", "parse_valid"}.issubset(lower_cols) or {"stage", "call_index"}.issubset(lower_cols) or {"stage", "call_number"}.issubset(lower_cols))
        if is_candidate and len(rows) > int(aggregate["largest_candidate_call_table_rows"]):
            aggregate["largest_candidate_call_table_rows"] = len(rows)
            aggregate["largest_candidate_call_table"] = path.relative_to(REPO).as_posix()
        p_true = 0
        p_false = 0
        for row in rows:
            stage_val = ""
            for key, value in row.items():
                if key.lower() == "stage":
                    stage_val = value
                if key.lower() == "parse_valid":
                    if safe_lower(value) == "true":
                        p_true += 1
                    elif safe_lower(value) == "false":
                        p_false += 1
            if stage_val:
                stages.add(stage_val)
        aggregate["parse_valid_true_rows"] += p_true
        aggregate["parse_valid_false_rows"] += p_false
        summary_rows.append(
            {
                "relative_path": path.relative_to(REPO).as_posix(),
                "row_count": len(rows),
                "columns": "|".join(columns),
                "candidate_call_table": is_candidate,
                "parse_valid_true_rows": p_true,
                "parse_valid_false_rows": p_false,
                "error": "",
            }
        )
    aggregate["stages_seen"] = "|".join(sorted(stages))
    return summary_rows, aggregate


def main() -> None:
    ensure(V4_DIR.exists(), f"Missing V4 execution output directory: {V4_DIR}")
    ensure(not OUT_DIR.exists(), f"Output directory already exists: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=False)

    inv = inventory_files()
    ensure(inv, "V4 output directory contains no files.")
    forbidden = [row for row in inv if row["forbidden_reason"]]
    ensure(not forbidden, f"Forbidden artifacts found: {forbidden[:3]}")

    file_paths = [REPO / row["relative_path"] for row in inv]
    content_hits = scan_file_content_safety(file_paths)
    ensure(not content_hits, f"Forbidden secret/raw content token found: {content_hits[:3]}")

    csv_summary, csv_aggregate = collect_csv_row_summary()
    facts = collect_manifest_facts()

    call_accounting = [
        {
            "accounting_item": "prior_attempted_calls_from_failed_v3_terminal_verified",
            "count": PRIOR_CALLS_FROM_FAILED_V3,
            "source": "V3 terminal output in user transcript; these were not rerun by V4/V5",
        },
        {
            "accounting_item": "remaining_calls_attempted_by_v4_terminal_verified",
            "count": RECOVERY_CALLS_FROM_V4,
            "source": "V4 terminal output showed CALL 04/36 through CALL 36/36",
        },
        {
            "accounting_item": "total_approved_call_attempts_consumed",
            "count": TOTAL_APPROVED_CALL_ATTEMPTS_CONSUMED,
            "source": "3 prior + 33 recovery = approved 36-call cap",
        },
        {
            "accounting_item": "new_calls_made_by_v5_finalizer",
            "count": 0,
            "source": "V5 performs filesystem validation only",
        },
    ]

    validation_rows = [
        {"check": "v4_output_directory_exists", "status": "PASS", "detail": str(V4_DIR.relative_to(REPO))},
        {"check": "sanitized_audit_filename_allowed", "status": "PASS", "detail": "audit is a legitimate stage/validation artifact token, not a raw artifact token"},
        {"check": "no_jsonl_files", "status": "PASS", "detail": "no .jsonl files in V4 outputs"},
        {"check": "no_env_file", "status": "PASS", "detail": "no .env file in V4 outputs"},
        {"check": "no_forbidden_raw_filename_tokens", "status": "PASS", "detail": "no raw_prompt/raw_response/request_body/response_body filename family detected"},
        {"check": "no_api_key_or_bearer_token_content", "status": "PASS", "detail": "no ZAI_API_KEY/Authorization: Bearer/Bearer content tokens detected"},
        {"check": "v5_api_calls", "status": "PASS", "detail": "0"},
        {"check": "v5_api_key_read", "status": "PASS", "detail": "False"},
        {"check": "approved_call_cap_accounting", "status": "PASS", "detail": "36 approved attempts consumed; V5 makes no new calls"},
    ]

    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "finalization_mode": "NO_CALL_FINALIZE_EXISTING_V4_OUTPUTS",
        "source_execution_output_dir": V4_DIR.relative_to(REPO).as_posix(),
        "api_calls_in_v5": 0,
        "api_key_read_in_v5": False,
        "model_calls_in_v5": 0,
        "call_accounting": {
            "prior_attempted_calls_from_failed_v3": PRIOR_CALLS_FROM_FAILED_V3,
            "remaining_calls_attempted_by_v4": RECOVERY_CALLS_FROM_V4,
            "total_approved_call_attempts_consumed": TOTAL_APPROVED_CALL_ATTEMPTS_CONSUMED,
            "approved_call_cap": APPROVED_CALL_CAP,
            "additional_calls_allowed_without_new_approval": 0,
        },
        "storage_safety": {
            "raw_prompt_instances_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "api_key_written": False,
            "sanitized_audit_filename_allowed": True,
        },
        "v4_manifest_facts": facts,
        "csv_aggregate": csv_aggregate,
        "research_boundary": {
            "model_result_evidence_exists": True,
            "claim_scope": "single GLM-5.2 micro-pilot with sanitized partial/validity accounting; not a deployment or provider superiority claim",
            "known_limitation": "V3 first three successful calls were terminal-observed but not persisted before V4 recovery; V5 records the call-accounting boundary explicitly.",
        },
    }

    write_json(OUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_finalization_manifest.json", manifest)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_file_inventory.csv", inv)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_call_accounting.csv", call_accounting)
    write_csv(OUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_validation_summary.csv", validation_rows)

    report = f"""# Pilot 05 CFPB GLM-5.2 Micro-Pilot Execution Finalization V5

Status: PASS

This finalization step made no API/model calls and did not read the API key. It finalizes the existing V4 sanitized execution artifacts after the V4 post-run validator falsely treated a legitimate sanitized audit filename as a raw artifact token.

## Call accounting

- Prior attempted calls from failed V3: {PRIOR_CALLS_FROM_FAILED_V3}
- Remaining calls attempted by V4: {RECOVERY_CALLS_FROM_V4}
- Total approved call attempts consumed: {TOTAL_APPROVED_CALL_ATTEMPTS_CONSUMED}
- Approved call cap: {APPROVED_CALL_CAP}
- New calls made by V5: 0

## Storage safety

- Raw prompts written: False
- Raw responses written: False
- JSONL written: False
- API key written: False
- Sanitized audit filename allowed: True

## CSV aggregate

- CSV files inspected: {csv_aggregate.get('csv_files')}
- Total CSV rows inspected: {csv_aggregate.get('total_csv_rows')}
- Largest candidate call table: {csv_aggregate.get('largest_candidate_call_table')}
- Largest candidate call table rows: {csv_aggregate.get('largest_candidate_call_table_rows')}
- Parse-valid true rows found across CSVs: {csv_aggregate.get('parse_valid_true_rows')}
- Parse-valid false rows found across CSVs: {csv_aggregate.get('parse_valid_false_rows')}
- Stages seen: {csv_aggregate.get('stages_seen')}

## Claim boundary

These outputs support only a controlled GLM-5.2 micro-pilot under the approved 36-call cap. They do not support broad model superiority, regulated lending validity, deployment safety, or real-world consumer harm claims.
"""
    (OUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_finalization_report.md").write_text(report, encoding="utf-8")

    print("Pilot 05 CFPB GLM-5.2 execution finalization generated.")
    print(f"output_dir: {OUT_DIR.relative_to(REPO).as_posix()}")
    print("status: PASS")
    print("finalization_mode: NO_CALL_FINALIZE_EXISTING_V4_OUTPUTS")
    print("api_calls_in_v5: 0")
    print("api_key_read_in_v5: False")
    print(f"total_approved_call_attempts_consumed: {TOTAL_APPROVED_CALL_ATTEMPTS_CONSUMED}")
    print("raw_prompt_instances_written: False")
    print("raw_responses_written: False")
    print("jsonl_written: False")
    print("sanitized_audit_filename_allowed: True")


if __name__ == "__main__":
    main()
