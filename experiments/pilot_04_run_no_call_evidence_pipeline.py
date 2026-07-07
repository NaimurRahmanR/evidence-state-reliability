from __future__ import annotations

import csv
import json
import py_compile
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from experiments.pilot_04_export_tasks import generate_pilot_04_task_exports
from experiments.pilot_04_generate_analysis_outputs import generate_pilot_04_analysis_outputs
from experiments.pilot_04_run_dry_run import generate_pilot_04_dry_run_outputs
from experiments.pilot_04_validate_committed_outputs import validate_committed_outputs


DEFAULT_OUTPUT_DIR = Path("reports/pilot_04_no_call_pipeline")

SAFE_NOTE = (
    "No-call Pilot 04 evidence pipeline runner. This command rebuilds deterministic "
    "task exports, dry-run outputs, derived analysis outputs, and committed-output "
    "validation without making real API calls."
)

SCRIPT_COMPILE_TARGETS = [
    Path("src/pilot_04_tasks.py"),
    Path("src/pilot_04_prompts.py"),
    Path("src/pilot_04_parser.py"),
    Path("src/pilot_04_dry_run.py"),
    Path("experiments/pilot_04_export_tasks.py"),
    Path("experiments/pilot_04_run_dry_run.py"),
    Path("experiments/pilot_04_generate_analysis_outputs.py"),
    Path("experiments/pilot_04_validate_committed_outputs.py"),
]


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


def _add_step(
    rows: list[dict[str, Any]],
    *,
    step_name: str,
    status: str,
    detail: str,
) -> None:
    rows.append(
        {
            "step_name": step_name,
            "status": status,
            "detail": detail,
        }
    )


def _compile_scripts(rows: list[dict[str, Any]]) -> None:
    for script_path in SCRIPT_COMPILE_TARGETS:
        if not script_path.exists():
            _add_step(
                rows,
                step_name=f"compile::{script_path}",
                status="FAIL",
                detail="script missing",
            )
            raise FileNotFoundError(f"Missing script: {script_path}")

        py_compile.compile(str(script_path), doraise=True)
        _add_step(
            rows,
            step_name=f"compile::{script_path}",
            status="PASS",
            detail="py_compile passed",
        )


def _assert_no_call_manifest(
    rows: list[dict[str, Any]],
    *,
    step_name: str,
    manifest: dict[str, Any],
    expected_status: str = "PASS",
) -> None:
    status = (
        "PASS"
        if manifest.get("status") == expected_status
        and manifest.get("real_api_calls") == 0
        and manifest.get("raw_response_inspection") is False
        else "FAIL"
    )

    detail = (
        f"status={manifest.get('status')}; "
        f"real_api_calls={manifest.get('real_api_calls')}; "
        f"raw_response_inspection={manifest.get('raw_response_inspection')}; "
        f"row_counts={manifest.get('row_counts')}"
    )

    _add_step(rows, step_name=step_name, status=status, detail=detail)

    if status != "PASS":
        raise RuntimeError(f"{step_name} failed no-call manifest checks: {detail}")


def _run_git_diff_check(rows: list[dict[str, Any]]) -> None:
    completed = subprocess.run(
        ["git", "diff", "--check"],
        check=False,
        capture_output=True,
        text=True,
    )

    status = "PASS" if completed.returncode == 0 else "FAIL"
    detail = "git diff --check passed" if status == "PASS" else completed.stdout + completed.stderr

    _add_step(
        rows,
        step_name="git_diff_check",
        status=status,
        detail=detail.strip(),
    )

    if completed.returncode != 0:
        raise RuntimeError("git diff --check failed inside Pilot 04 no-call pipeline.")


def run_pilot_04_no_call_pipeline(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    """Run the full deterministic Pilot 04 no-call evidence pipeline."""
    output_dir.mkdir(parents=True, exist_ok=True)

    step_rows: list[dict[str, Any]] = []

    _compile_scripts(step_rows)

    task_manifest = generate_pilot_04_task_exports()
    _assert_no_call_manifest(step_rows, step_name="generate_task_exports", manifest=task_manifest)

    dry_run_manifest = generate_pilot_04_dry_run_outputs()
    _assert_no_call_manifest(step_rows, step_name="generate_dry_run_outputs", manifest=dry_run_manifest)

    analysis_manifest = generate_pilot_04_analysis_outputs()
    _assert_no_call_manifest(step_rows, step_name="generate_analysis_outputs", manifest=analysis_manifest)

    validation_manifest = validate_committed_outputs()
    _assert_no_call_manifest(step_rows, step_name="validate_committed_outputs", manifest=validation_manifest)

    _run_git_diff_check(step_rows)

    n_failed = sum(1 for row in step_rows if row["status"] != "PASS")

    manifest = {
        "artifact": "pilot_04_no_call_evidence_pipeline",
        "status": "PASS" if n_failed == 0 else "FAIL",
        "created_at_utc": _load_existing_created_at(output_dir / "manifest.json"),
        "safe_note": SAFE_NOTE,
        "n_steps": len(step_rows),
        "n_failed_steps": n_failed,
        "n_skipped_steps": sum(1 for row in step_rows if row["status"] == "SKIP"),
        "step_summary": step_rows,
        "upstream_manifests": {
            "task_exports": task_manifest,
            "dry_run_outputs": dry_run_manifest,
            "analysis_outputs": analysis_manifest,
            "validation": validation_manifest,
        },
        "output_files": [
            str(output_dir / "pipeline_steps.csv"),
            str(output_dir / "manifest.json"),
        ],
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }

    _write_csv(output_dir / "pipeline_steps.csv", step_rows)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if manifest["status"] != "PASS":
        raise RuntimeError("Pilot 04 no-call pipeline failed.")

    return manifest


def main() -> None:
    manifest = run_pilot_04_no_call_pipeline()
    print("Pilot 04 no-call evidence pipeline completed.")
    print(f"output_dir: {DEFAULT_OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"n_steps: {manifest['n_steps']}")
    print(f"n_failed_steps: {manifest['n_failed_steps']}")
    print(f"n_skipped_steps: {manifest['n_skipped_steps']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")


if __name__ == "__main__":
    main()
