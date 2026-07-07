from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.pilot_04_dry_run import (
    PILOT_04_DRY_RUN_VERSION,
    chain_rows,
    run_pilot_04_dry_run,
    stage_rows,
    summarise_pilot_04_dry_run,
)
from src.pilot_04_tasks import DEFAULT_CONDITIONS, DEFAULT_TASK_COUNT


DEFAULT_OUTPUT_DIR = Path("reports/pilot_04_dry_run")
DEFAULT_DECISION_OUTPUT = DEFAULT_OUTPUT_DIR / "decision_outputs.csv"
DEFAULT_AUDIT_OUTPUT = DEFAULT_OUTPUT_DIR / "audit_outputs.csv"
DEFAULT_ESCALATION_OUTPUT = DEFAULT_OUTPUT_DIR / "escalation_outputs.csv"
DEFAULT_CHAIN_OUTPUT = DEFAULT_OUTPUT_DIR / "chain_outputs.csv"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "manifest.json"


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _load_existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def generate_pilot_04_dry_run_outputs(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    """Generate sanitized deterministic Pilot 04 dry-run outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    decision_output = output_dir / "decision_outputs.csv"
    audit_output = output_dir / "audit_outputs.csv"
    escalation_output = output_dir / "escalation_outputs.csv"
    chain_output = output_dir / "chain_outputs.csv"
    manifest_path = output_dir / "manifest.json"

    results = run_pilot_04_dry_run(n_tasks=DEFAULT_TASK_COUNT, conditions=list(DEFAULT_CONDITIONS))

    decision_rows = stage_rows(results, "decision")
    audit_rows = stage_rows(results, "audit")
    escalation_rows = stage_rows(results, "escalation")
    chains = chain_rows(results)

    _write_csv(decision_output, decision_rows)
    _write_csv(audit_output, audit_rows)
    _write_csv(escalation_output, escalation_rows)
    _write_csv(chain_output, chains)

    expected_chain_rows = DEFAULT_TASK_COUNT * len(DEFAULT_CONDITIONS)
    expected_stage_rows = expected_chain_rows

    row_counts = {
        "decision_outputs": _csv_row_count(decision_output),
        "audit_outputs": _csv_row_count(audit_output),
        "escalation_outputs": _csv_row_count(escalation_output),
        "chain_outputs": _csv_row_count(chain_output),
    }

    if row_counts["decision_outputs"] != expected_stage_rows:
        raise RuntimeError("Unexpected decision output row count.")
    if row_counts["audit_outputs"] != expected_stage_rows:
        raise RuntimeError("Unexpected audit output row count.")
    if row_counts["escalation_outputs"] != expected_stage_rows:
        raise RuntimeError("Unexpected escalation output row count.")
    if row_counts["chain_outputs"] != expected_chain_rows:
        raise RuntimeError("Unexpected chain output row count.")

    summary = summarise_pilot_04_dry_run(results)
    if summary["all_stage_schemas_valid"] is not True:
        raise RuntimeError("Pilot 04 dry-run produced schema-invalid stage output.")
    if summary["prompt_instruction_text_exported"] is not False:
        raise RuntimeError("Pilot 04 dry-run attempted to export prompt instruction text.")

    manifest = {
        "artifact": "pilot_04_deterministic_dry_run",
        "status": "PASS",
        "created_at_utc": _load_existing_created_at(manifest_path),
        "generator": "experiments.pilot_04_run_dry_run",
        "dry_run_version": PILOT_04_DRY_RUN_VERSION,
        "task_count": DEFAULT_TASK_COUNT,
        "conditions": list(DEFAULT_CONDITIONS),
        "expected_chain_rows": expected_chain_rows,
        "expected_stage_rows_per_stage": expected_stage_rows,
        "row_counts": row_counts,
        "summary": summary,
        "output_files": [
            str(decision_output),
            str(audit_output),
            str(escalation_output),
            str(chain_output),
            str(manifest_path),
        ],
        "prompt_instruction_text_exported": False,
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    manifest = generate_pilot_04_dry_run_outputs()
    print("Pilot 04 deterministic no-call dry-run outputs generated.")
    print(f"output_dir: {DEFAULT_OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"all_stage_schemas_valid: {manifest['summary']['all_stage_schemas_valid']}")
    print(f"prompt_instruction_text_exported: {manifest['prompt_instruction_text_exported']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")


if __name__ == "__main__":
    main()
