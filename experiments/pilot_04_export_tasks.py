from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.pilot_04_tasks import (
    DEFAULT_CONDITIONS,
    DEFAULT_SEED,
    DEFAULT_TASK_COUNT,
    TASK_TYPE,
    condition_inventory_records,
    export_pilot_04_condition_inventory,
    export_pilot_04_tasks,
    generate_pilot_04_tasks,
    summarise_pilot_04_tasks,
    validate_pilot_04_tasks,
)


DEFAULT_DATA_OUTPUT = Path("data/pilot_04_tasks.csv")
DEFAULT_REPORT_OUTPUT_DIR = Path("reports/pilot_04_tasks")
DEFAULT_TASK_INVENTORY = DEFAULT_REPORT_OUTPUT_DIR / "task_inventory.csv"
DEFAULT_CONDITION_INVENTORY = DEFAULT_REPORT_OUTPUT_DIR / "condition_inventory.csv"
DEFAULT_MANIFEST = DEFAULT_REPORT_OUTPUT_DIR / "manifest.json"


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def _csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def generate_pilot_04_task_exports(
    *,
    data_output: Path = DEFAULT_DATA_OUTPUT,
    report_output_dir: Path = DEFAULT_REPORT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Generate deterministic sanitized Pilot 04 task exports."""
    tasks = generate_pilot_04_tasks(n_tasks=DEFAULT_TASK_COUNT, seed=DEFAULT_SEED)
    validation = validate_pilot_04_tasks(tasks)

    if validation["status"] != "PASS":
        raise RuntimeError(f"Pilot 04 task validation failed: {validation}")

    report_output_dir.mkdir(parents=True, exist_ok=True)

    task_inventory = report_output_dir / "task_inventory.csv"
    condition_inventory = report_output_dir / "condition_inventory.csv"
    manifest_path = report_output_dir / "manifest.json"

    export_pilot_04_tasks(tasks=tasks, output_path=data_output)
    export_pilot_04_tasks(tasks=tasks, output_path=task_inventory)
    export_pilot_04_condition_inventory(tasks=tasks, output_path=condition_inventory)

    task_summary = summarise_pilot_04_tasks(tasks)
    condition_records = condition_inventory_records(tasks)

    expected_condition_rows = DEFAULT_TASK_COUNT * len(DEFAULT_CONDITIONS)
    actual_condition_rows = len(condition_records)

    manifest = {
        "artifact": "pilot_04_task_exports",
        "task_type": TASK_TYPE,
        "status": "PASS",
        "created_at_utc": _load_existing_created_at(manifest_path),
        "generator": "experiments.pilot_04_export_tasks",
        "task_count": DEFAULT_TASK_COUNT,
        "seed": DEFAULT_SEED,
        "conditions": list(DEFAULT_CONDITIONS),
        "expected_condition_rows": expected_condition_rows,
        "actual_condition_rows": actual_condition_rows,
        "row_counts": {
            "data_task_inventory": _csv_row_count(data_output),
            "report_task_inventory": _csv_row_count(task_inventory),
            "condition_inventory": _csv_row_count(condition_inventory),
        },
        "task_summary": task_summary,
        "validation": validation,
        "output_files": [
            str(data_output),
            str(task_inventory),
            str(condition_inventory),
            str(manifest_path),
        ],
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }

    row_counts = manifest["row_counts"]
    if row_counts["data_task_inventory"] != DEFAULT_TASK_COUNT:
        raise RuntimeError("Unexpected data task inventory row count.")
    if row_counts["report_task_inventory"] != DEFAULT_TASK_COUNT:
        raise RuntimeError("Unexpected report task inventory row count.")
    if row_counts["condition_inventory"] != expected_condition_rows:
        raise RuntimeError("Unexpected condition inventory row count.")
    if actual_condition_rows != expected_condition_rows:
        raise RuntimeError("Unexpected in-memory condition row count.")

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    manifest = generate_pilot_04_task_exports()
    print("Pilot 04 deterministic task exports generated.")
    print(f"output_dir: {DEFAULT_REPORT_OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")


if __name__ == "__main__":
    main()
