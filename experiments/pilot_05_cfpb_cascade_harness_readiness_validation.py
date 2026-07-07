from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "05AH"
SCHEMA_VERSION = "pilot_05_cfpb_cascade_harness_readiness_validation_v1"
STAGES = ("decision", "audit", "escalation")
CONDITIONS = ("clean", "compressed", "partial_dropout", "noisy_conflicting")
ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "reports" / "pilot_05_cfpb_cascade_execution_harness"
OUT = ROOT / "reports" / "pilot_05_cfpb_cascade_harness_readiness_validation"

FILES = {
    "harness_script": ROOT / "experiments" / "pilot_05_cfpb_cascade_execution_harness.py",
    "manifest": INPUT_DIR / "pilot_05_cfpb_cascade_execution_harness_manifest.json",
    "plan": INPUT_DIR / "pilot_05_cfpb_cascade_execution_plan.csv",
    "batches": INPUT_DIR / "pilot_05_cfpb_cascade_execution_batches.csv",
    "guardrails": INPUT_DIR / "pilot_05_cfpb_cascade_execution_guardrails.csv",
    "expected_outputs": INPUT_DIR / "pilot_05_cfpb_cascade_expected_sanitized_outputs.csv",
    "readiness": INPUT_DIR / "pilot_05_cfpb_cascade_execution_readiness_summary.csv",
}

OUT_FILES = {
    "manifest": OUT / "pilot_05_cfpb_cascade_harness_readiness_validation_manifest.json",
    "checks": OUT / "pilot_05_cfpb_cascade_harness_readiness_checks.csv",
    "matrix": OUT / "pilot_05_cfpb_cascade_harness_readiness_stage_condition_matrix.csv",
    "batches": OUT / "pilot_05_cfpb_cascade_harness_readiness_batch_consistency.csv",
    "guardrails": OUT / "pilot_05_cfpb_cascade_harness_readiness_guardrail_review.csv",
    "report": OUT / "pilot_05_cfpb_cascade_harness_readiness_report.md",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def die(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        die(f"missing csv: {rel(path)}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        die(f"empty csv: {rel(path)}")
    return rows


def read_json(path: Path) -> Any:
    if not path.exists():
        die(f"missing json: {rel(path)}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    if path.exists():
        die(f"refusing to overwrite output: {rel(path)}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def as_int(value: Any) -> int:
    return int(str(value).strip())


checks: list[dict[str, Any]] = []


def check(category: str, name: str, expected: Any, observed: Any, notes: str = "") -> None:
    status = "PASS" if str(expected) == str(observed) else "FAIL"
    checks.append({
        "check_id": f"05AH-{len(checks)+1:03d}",
        "category": category,
        "check_name": name,
        "expected": expected,
        "observed": observed,
        "status": status,
        "notes": notes,
    })


def require_pass() -> None:
    failed = [row for row in checks if row["status"] != "PASS"]
    if failed:
        for row in failed:
            print(f"FAILED_CHECK: {row['check_id']} {row['category']} {row['check_name']} expected={row['expected']} observed={row['observed']}")
        die(f"{len(failed)} readiness checks failed")


def main() -> None:
    if OUT.exists():
        die(f"output directory already exists: {rel(OUT)}")

    for label, path in FILES.items():
        check("input_presence", f"input_exists_{label}", True, path.exists(), rel(path))

    manifest = read_json(FILES["manifest"])
    plan = read_csv(FILES["plan"])
    batches = read_csv(FILES["batches"])
    guardrails = read_csv(FILES["guardrails"])
    expected_outputs = read_csv(FILES["expected_outputs"])
    readiness = read_csv(FILES["readiness"])

    check("manifest", "05ag_status", "PASS", manifest.get("status"))
    check("manifest", "05ag_execution_mode", "no_call_readiness_plan_only", manifest.get("execution_mode"))
    check("manifest", "dry_run_rows", 720, manifest.get("counts", {}).get("dry_run_rows"))
    check("manifest", "execution_plan_rows", 720, manifest.get("counts", {}).get("execution_plan_rows"))
    check("manifest", "execution_batch_rows", 12, manifest.get("counts", {}).get("execution_batch_rows"))

    stage_counts_manifest = manifest.get("counts", {}).get("stage_counts", {})
    for stage in STAGES:
        check("manifest_stage_counts", f"manifest_stage_rows_{stage}", 240, stage_counts_manifest.get(stage))

    safety = manifest.get("safety_flags", {})
    expected_safety = {
        "model_execution_enabled": False,
        "hard_stop_without_future_approval": True,
        "api_calls": 0,
        "model_calls": 0,
        "raw_prompt_instances_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "raw_cfpb_data_read": False,
        "raw_cfpb_data_written": False,
        "staged_or_committed_by_script": False,
    }
    for key, expected in expected_safety.items():
        check("manifest_safety", key, expected, safety.get(key))

    check("csv_counts", "plan_rows", 720, len(plan))
    check("csv_counts", "batch_rows", 12, len(batches))
    check("csv_counts", "guardrail_rows", 10, len(guardrails))
    check("csv_counts", "readiness_rows", 19, len(readiness))

    orders = [as_int(row["execution_order"]) for row in plan]
    check("plan_structure", "execution_order_min", 1, min(orders))
    check("plan_structure", "execution_order_max", 720, max(orders))
    check("plan_structure", "execution_order_unique", 720, len(set(orders)))

    plan_stage_counts = Counter(row["stage"] for row in plan)
    plan_condition_counts = Counter(row["evidence_condition"] for row in plan)
    plan_pair_counts = Counter((row["stage"], row["evidence_condition"]) for row in plan)

    for stage in STAGES:
        check("plan_stage_counts", f"plan_stage_rows_{stage}", 240, plan_stage_counts[stage])
    for condition in CONDITIONS:
        check("plan_condition_counts", f"plan_condition_rows_{condition}", 180, plan_condition_counts[condition])

    matrix_rows: list[dict[str, Any]] = []
    for stage in STAGES:
        for condition in CONDITIONS:
            count = plan_pair_counts[(stage, condition)]
            matrix_rows.append({
                "stage": stage,
                "evidence_condition": condition,
                "plan_rows": count,
                "expected_plan_rows": 60,
                "status": "PASS" if count == 60 else "FAIL",
            })
            check("stage_condition_matrix", f"plan_rows_{stage}_{condition}", 60, count)

    plan_zero_fields = {
        "api_calls_planned": "0",
        "model_calls_planned": "0",
        "model_execution_enabled": "False",
        "raw_prompt_instance_written": "False",
        "raw_response_written": "False",
        "jsonl_written": "False",
        "approval_required_before_execution": "True",
    }
    for field, expected in plan_zero_fields.items():
        bad = sum(1 for row in plan if str(row.get(field)) != expected)
        check("plan_guardrails", f"bad_rows_{field}", 0, bad)

    batch_rows: list[dict[str, Any]] = []
    batch_key_set = set()
    for row in batches:
        stage = row["stage"]
        condition = row["evidence_condition"]
        batch_key_set.add((stage, condition))
        plan_count = plan_pair_counts[(stage, condition)]
        batch_count = as_int(row["request_count"])
        status = "PASS" if plan_count == 60 and batch_count == 60 else "FAIL"
        batch_rows.append({
            "batch_id": row["batch_id"],
            "stage": stage,
            "evidence_condition": condition,
            "plan_rows": plan_count,
            "batch_request_count": batch_count,
            "expected_count": 60,
            "status": status,
        })
        check("batch_consistency", f"batch_count_{stage}_{condition}", 60, batch_count)
        check("batch_consistency", f"batch_matches_plan_{stage}_{condition}", plan_count, batch_count)

    check("batch_consistency", "unique_stage_condition_batches", 12, len(batch_key_set))

    batch_guardrail_fields = {
        "api_calls_planned": "0",
        "model_calls_planned": "0",
        "model_execution_enabled": "False",
        "raw_prompt_instances_written": "False",
        "raw_responses_written": "False",
        "jsonl_written": "False",
        "approval_required_before_execution": "True",
    }
    for field, expected in batch_guardrail_fields.items():
        bad = sum(1 for row in batches if str(row.get(field)) != expected)
        check("batch_guardrails", f"bad_batches_{field}", 0, bad)

    guardrail_review: list[dict[str, Any]] = []
    required_guardrails = {
        "model_execution_enabled",
        "hard_stop_without_future_approval",
        "api_calls",
        "model_calls",
        "dataset_downloads",
        "raw_prompt_instances_written",
        "raw_responses_written",
        "jsonl_written",
        "raw_cfpb_data_read",
        "git_stage_commit_push",
    }
    observed_guardrails = {row["guardrail"] for row in guardrails}
    check("guardrails", "required_guardrail_names_present", sorted(required_guardrails), sorted(observed_guardrails))
    check("guardrails", "guardrails_all_pass", 0, sum(1 for row in guardrails if row.get("status") != "PASS"))
    for row in guardrails:
        guardrail_review.append({
            "guardrail": row.get("guardrail", ""),
            "expected_value": row.get("expected_value", ""),
            "observed_value": row.get("observed_value", ""),
            "source_status": row.get("status", ""),
            "review_status": "PASS" if row.get("status") == "PASS" else "FAIL",
        })

    check("readiness", "readiness_all_pass", 0, sum(1 for row in readiness if row.get("status") != "PASS"))
    readiness_lookup = {row["metric"]: row for row in readiness}
    for metric, expected in {
        "dry_run_rows": "720",
        "evidence_state_rows": "240",
        "evidence_label_rows": "240",
        "parser_rule_rows": "17",
        "execution_plan_rows": "720",
        "execution_batch_rows": "12",
        "model_calls": "0",
        "api_calls": "0",
        "raw_prompt_instances_written": "False",
        "raw_responses_written": "False",
        "jsonl_written": "False",
        "model_execution_enabled": "False",
        "hard_stop_without_future_approval": "True",
    }.items():
        check("readiness_metrics", f"readiness_{metric}", expected, readiness_lookup.get(metric, {}).get("value"))

    for field in ("raw_prompt_instances_allowed", "raw_responses_allowed", "jsonl_allowed"):
        bad = sum(1 for row in expected_outputs if str(row.get(field)) != "False")
        check("expected_outputs", f"bad_rows_{field}", 0, bad)
    approval_bad = sum(1 for row in expected_outputs if str(row.get("requires_future_explicit_approval")) != "True")
    check("expected_outputs", "bad_rows_requires_future_explicit_approval", 0, approval_bad)

    jsonl_paths = [path for path in OUT_FILES.values() if path.suffix.lower() == ".jsonl"]
    check("output_safety", "planned_jsonl_outputs", 0, len(jsonl_paths))

    failed_count = sum(1 for row in checks if row["status"] != "PASS")
    status = "PASS" if failed_count == 0 else "FAIL"

    OUT.mkdir(parents=True, exist_ok=False)
    write_csv(OUT_FILES["checks"], checks, ["check_id", "category", "check_name", "expected", "observed", "status", "notes"])
    write_csv(OUT_FILES["matrix"], matrix_rows, ["stage", "evidence_condition", "plan_rows", "expected_plan_rows", "status"])
    write_csv(OUT_FILES["batches"], batch_rows, ["batch_id", "stage", "evidence_condition", "plan_rows", "batch_request_count", "expected_count", "status"])
    write_csv(OUT_FILES["guardrails"], guardrail_review, ["guardrail", "expected_value", "observed_value", "source_status", "review_status"])

    report = f"""# Pilot 05 CFPB Cascade Harness Readiness Validation\n\nTask: 05AH\n\nStatus: {status}\n\n## Scope\n\nThis validation checks the committed no-call Pilot 05 execution harness and sanitized harness outputs. It does not execute any model, call any API, write raw prompts, write raw responses, or write JSONL.\n\n## Key counts\n\n- Execution plan rows: {len(plan)}\n- Execution batches: {len(batches)}\n- Decision rows: {plan_stage_counts['decision']}\n- Audit rows: {plan_stage_counts['audit']}\n- Escalation rows: {plan_stage_counts['escalation']}\n- Failed checks: {failed_count}\n\n## Claim boundary\n\nThis is infrastructure/readiness validation only. It creates no Pilot 05 model-result evidence and does not support claims about provider/model superiority, real-world deployment validity, financial safety, legal safety, or consumer harm prevalence.\n"""
    if OUT_FILES["report"].exists():
        die(f"refusing to overwrite output: {rel(OUT_FILES['report'])}")
    OUT_FILES["report"].write_text(report, encoding="utf-8")

    validation_manifest = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "validated_input_checkpoint": "2b57c07 Add Pilot 05 CFPB no-call execution harness",
        "execution_mode": "no_call_readiness_validation_only",
        "claim_boundary": "Harness readiness validation only. No Pilot 05 model-result evidence created.",
        "input_files": {key: rel(path) for key, path in FILES.items()},
        "output_files": {key: rel(path) for key, path in OUT_FILES.items()},
        "counts": {
            "check_rows": len(checks),
            "failed_checks": failed_count,
            "plan_rows": len(plan),
            "batch_rows": len(batches),
            "guardrail_rows": len(guardrails),
            "readiness_rows": len(readiness),
            "stage_counts": dict(plan_stage_counts),
            "condition_counts": dict(plan_condition_counts),
            "stage_condition_rows": {f"{stage}|{condition}": plan_pair_counts[(stage, condition)] for stage in STAGES for condition in CONDITIONS},
        },
        "safety_flags": {
            "model_execution_enabled": False,
            "hard_stop_without_future_approval": True,
            "api_calls": 0,
            "model_calls": 0,
            "dataset_downloads": 0,
            "raw_prompt_instances_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "raw_cfpb_data_read": False,
            "raw_cfpb_data_written": False,
            "staged_or_committed_by_script": False,
        },
    }
    if OUT_FILES["manifest"].exists():
        die(f"refusing to overwrite output: {rel(OUT_FILES['manifest'])}")
    OUT_FILES["manifest"].write_text(json.dumps(validation_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("Pilot 05 CFPB no-call harness readiness validation generated.")
    print(f"output_dir: {rel(OUT)}")
    print(f"status: {status}")
    print(f"check_rows: {len(checks)}")
    print(f"failed_checks: {failed_count}")
    print(f"plan_rows: {len(plan)}")
    print(f"batch_rows: {len(batches)}")
    print(f"decision_stage_rows: {plan_stage_counts['decision']}")
    print(f"audit_stage_rows: {plan_stage_counts['audit']}")
    print(f"escalation_stage_rows: {plan_stage_counts['escalation']}")
    print("model_calls: 0")
    print("api_calls: 0")
    print("raw_prompt_instances_written: False")
    print("raw_responses_written: False")
    print("jsonl_written: False")
    print("model_execution_enabled: False")
    print("hard_stop_without_future_approval: True")

    require_pass()


if __name__ == "__main__":
    main()
