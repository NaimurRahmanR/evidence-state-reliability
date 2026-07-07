from __future__ import annotations

import argparse
import csv
import json
import py_compile
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from experiments.pilot_03_generate_stage_cascade_tables import (
    DEFAULT_CLAUDE_CHAIN_CSV,
    DEFAULT_GLM_AGGREGATE_JSON,
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE_CASCADE_OUTPUT_DIR,
    generate_stage_cascade_tables,
)
from experiments.pilot_03_generate_uncertainty_tables import (
    DEFAULT_GLM_CONDITION_CSV,
    DEFAULT_OUTPUT_DIR as DEFAULT_UNCERTAINTY_OUTPUT_DIR,
    DEFAULT_SHARED_COMPARISON_CSV,
    generate_uncertainty_tables,
)
from experiments.pilot_03_generate_robustness_sensitivity_checks import (
    DEFAULT_OUTPUT_DIR as DEFAULT_ROBUSTNESS_OUTPUT_DIR,
    generate_robustness_sensitivity_checks,
)
from experiments.pilot_03_validate_committed_outputs import (
    DEFAULT_OUTPUT_DIR as DEFAULT_VALIDATION_OUTPUT_DIR,
    validate_committed_outputs,
)
from experiments.pilot_03_validate_comparison_outputs import (
    DEFAULT_OUTPUT_DIR as DEFAULT_COMPARISON_VALIDATION_OUTPUT_DIR,
    validate_comparison_outputs,
)


DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_no_call_pipeline")

SAFE_NOTE = (
    "No-call Pilot 03 evidence pipeline runner. This command rebuilds committed "
    "derived evidence tables, final figures, and robustness/sensitivity checks, "
    "then validates committed outputs without making real API calls."
)

SCRIPT_COMPILE_TARGETS = [
    Path("experiments/pilot_03_generate_uncertainty_tables.py"),
    Path("experiments/pilot_03_generate_stage_cascade_tables.py"),
    Path("experiments/pilot_03_validate_committed_outputs.py"),
    Path("experiments/pilot_03_plan_real_runs.py"),
    Path("experiments/pilot_03_generate_paper_figures.py"),
    Path("experiments/pilot_03_generate_final_figures.py"),
    Path("experiments/pilot_03_generate_robustness_sensitivity_checks.py"),
    Path("experiments/pilot_03_validate_comparison_outputs.py"),
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


def _run_uncertainty(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = generate_uncertainty_tables(
        glm_condition_csv=DEFAULT_GLM_CONDITION_CSV,
        shared_comparison_csv=DEFAULT_SHARED_COMPARISON_CSV,
        output_dir=DEFAULT_UNCERTAINTY_OUTPUT_DIR,
    )

    status = "PASS" if manifest.get("real_api_calls") == 0 else "FAIL"

    _add_step(
        rows,
        step_name="generate_uncertainty_tables",
        status=status,
        detail=f"real_api_calls={manifest.get('real_api_calls')}; row_counts={manifest.get('row_counts')}",
    )

    if status != "PASS":
        raise RuntimeError("Uncertainty table generation did not report zero real API calls.")

    return manifest


def _run_stage_cascade(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not DEFAULT_GLM_AGGREGATE_JSON.exists():
        _add_step(
            rows,
            step_name="generate_stage_cascade_tables",
            status="SKIP",
            detail=(
                "ignored local GLM aggregate is missing; committed validation can still run, "
                "but stage-cascade regeneration requires local aggregate JSON"
            ),
        )
        return {
            "status": "SKIP",
            "real_api_calls": 0,
            "reason": "missing ignored local GLM aggregate JSON",
            "missing_path": str(DEFAULT_GLM_AGGREGATE_JSON),
        }

    manifest = generate_stage_cascade_tables(
        glm_aggregate_json=DEFAULT_GLM_AGGREGATE_JSON,
        claude_chain_csv=DEFAULT_CLAUDE_CHAIN_CSV,
        output_dir=DEFAULT_STAGE_CASCADE_OUTPUT_DIR,
    )

    status = (
        "PASS"
        if manifest.get("real_api_calls") == 0
        and manifest.get("raw_prompt_or_response_columns_exported") is False
        else "FAIL"
    )

    _add_step(
        rows,
        step_name="generate_stage_cascade_tables",
        status=status,
        detail=(
            f"real_api_calls={manifest.get('real_api_calls')}; "
            f"raw_prompt_or_response_columns_exported={manifest.get('raw_prompt_or_response_columns_exported')}; "
            f"row_counts={manifest.get('row_counts')}"
        ),
    )

    if status != "PASS":
        raise RuntimeError("Stage-cascade generation failed safety checks.")

    return manifest


def _run_final_figures(rows: list[dict[str, Any]]) -> dict[str, Any]:
    command = [sys.executable, "-m", "experiments.pilot_03_generate_final_figures"]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest_path = Path("reports/pilot_03_final_figures/manifest.json")
    if not manifest_path.exists():
        _add_step(
            rows,
            step_name="generate_final_figures",
            status="FAIL",
            detail="manifest missing after final figure generation",
        )
        raise FileNotFoundError(f"Missing final figure manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    n_figures = len(manifest.get("figures", []))
    n_output_files = len(manifest.get("output_files", []))

    status = (
        "PASS"
        if manifest.get("real_api_calls") == 0
        and manifest.get("raw_response_inspection") is False
        and manifest.get("safe_wording_check") == "PASS"
        and n_figures >= 7
        and n_output_files >= 15
        else "FAIL"
    )

    detail = (
        f"real_api_calls={manifest.get('real_api_calls')}; "
        f"raw_response_inspection={manifest.get('raw_response_inspection')}; "
        f"safe_wording_check={manifest.get('safe_wording_check')}; "
        f"n_figures={n_figures}; "
        f"n_output_files={n_output_files}"
    )

    _add_step(
        rows,
        step_name="generate_final_figures",
        status=status,
        detail=detail,
    )

    if status != "PASS":
        raise RuntimeError(
            "Final figure generation failed no-call safety validation. "
            f"stdout={completed.stdout} stderr={completed.stderr}"
        )

    return manifest


def _run_robustness_sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = generate_robustness_sensitivity_checks(output_dir=DEFAULT_ROBUSTNESS_OUTPUT_DIR)

    expected_row_counts = {
        "leave_one_task_out_sensitivity": 18,
        "condition_order_sensitivity": 12,
        "paired_delta_interval_sensitivity": 15,
        "cascade_threshold_sensitivity": 30,
        "high_signal_case_profile": 7,
    }

    row_counts = manifest.get("row_counts", {})
    row_counts_pass = all(row_counts.get(key) == value for key, value in expected_row_counts.items())

    status = (
        "PASS"
        if manifest.get("status") == "PASS"
        and manifest.get("real_api_calls") == 0
        and manifest.get("raw_response_inspection") is False
        and manifest.get("safe_wording_check") == "PASS"
        and row_counts_pass
        and len(manifest.get("source_files", [])) == 14
        and len(manifest.get("output_files", [])) >= 6
        else "FAIL"
    )

    _add_step(
        rows,
        step_name="generate_robustness_sensitivity_checks",
        status=status,
        detail=(
            f"status={manifest.get('status')}; "
            f"real_api_calls={manifest.get('real_api_calls')}; "
            f"raw_response_inspection={manifest.get('raw_response_inspection')}; "
            f"safe_wording_check={manifest.get('safe_wording_check')}; "
            f"row_counts={row_counts}"
        ),
    )

    if status != "PASS":
        raise RuntimeError("Robustness/sensitivity generation failed no-call safety validation.")

    return manifest


def _run_validator(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = validate_committed_outputs(output_dir=DEFAULT_VALIDATION_OUTPUT_DIR)

    status = (
        "PASS"
        if manifest.get("status") == "PASS"
        and manifest.get("real_api_calls") == 0
        and manifest.get("n_failed_checks") == 0
        else "FAIL"
    )

    _add_step(
        rows,
        step_name="validate_committed_outputs",
        status=status,
        detail=(
            f"status={manifest.get('status')}; "
            f"n_checks={manifest.get('n_checks')}; "
            f"n_failed_checks={manifest.get('n_failed_checks')}; "
            f"real_api_calls={manifest.get('real_api_calls')}"
        ),
    )

    if status != "PASS":
        raise RuntimeError("Committed-output validation failed.")

    return manifest


def _run_comparison_validator(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = validate_comparison_outputs(output_dir=DEFAULT_COMPARISON_VALIDATION_OUTPUT_DIR)

    status = (
        "PASS"
        if manifest.get("status") == "PASS"
        and manifest.get("real_api_calls") == 0
        and manifest.get("raw_response_inspection") is False
        and manifest.get("n_failed_checks") == 0
        and manifest.get("validated_csv_count") >= 20
        and manifest.get("validated_manifest_count") >= 6
        else "FAIL"
    )

    _add_step(
        rows,
        step_name="validate_comparison_outputs",
        status=status,
        detail=(
            f"status={manifest.get('status')}; "
            f"n_checks={manifest.get('n_checks')}; "
            f"n_failed_checks={manifest.get('n_failed_checks')}; "
            f"validated_csv_count={manifest.get('validated_csv_count')}; "
            f"validated_manifest_count={manifest.get('validated_manifest_count')}; "
            f"real_api_calls={manifest.get('real_api_calls')}; "
            f"raw_response_inspection={manifest.get('raw_response_inspection')}"
        ),
    )

    if status != "PASS":
        raise RuntimeError("Comparison-output validation failed.")

    return manifest


def _write_report(
    path: Path,
    *,
    step_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    lines = [
        "# Pilot 03 no-call evidence pipeline report",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        f"Pipeline status: **{manifest['status']}**",
        "",
        "## Steps",
        "",
        "| step_name | status | detail |",
        "| --- | --- | --- |",
    ]

    for row in step_rows:
        lines.append(f"| {row['step_name']} | {row['status']} | {row['detail']} |")

    lines.extend(
        [
            "",
            "## Manifest",
            "",
            "```json",
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
            "```",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def run_no_call_evidence_pipeline(*, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "pipeline_steps_csv": output_dir / "pipeline_steps.csv",
        "pipeline_report_md": output_dir / "no_call_evidence_pipeline_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    step_rows: list[dict[str, Any]] = []

    _compile_scripts(step_rows)
    uncertainty_manifest = _run_uncertainty(step_rows)
    stage_cascade_manifest = _run_stage_cascade(step_rows)
    final_figures_manifest = _run_final_figures(step_rows)
    robustness_manifest = _run_robustness_sensitivity(step_rows)
    validation_manifest = _run_validator(step_rows)
    comparison_validation_manifest = _run_comparison_validator(step_rows)

    failed_steps = [row for row in step_rows if row["status"] == "FAIL"]
    skipped_steps = [row for row in step_rows if row["status"] == "SKIP"]

    status = "PASS" if not failed_steps else "FAIL"

    manifest = {
        "created_at_utc": _load_existing_created_at(outputs["manifest_json"]),
        "status": status,
        "real_api_calls": 0,
        "safe_note": SAFE_NOTE,
        "n_steps": len(step_rows),
        "n_failed_steps": len(failed_steps),
        "n_skipped_steps": len(skipped_steps),
        "outputs": {name: str(path) for name, path in outputs.items()},
        "component_manifests": {
            "uncertainty": {
                "status": "PASS",
                "real_api_calls": uncertainty_manifest.get("real_api_calls"),
                "row_counts": uncertainty_manifest.get("row_counts"),
            },
            "stage_cascade": {
                "status": stage_cascade_manifest.get("status", "PASS"),
                "real_api_calls": stage_cascade_manifest.get("real_api_calls"),
                "row_counts": stage_cascade_manifest.get("row_counts"),
                "raw_prompt_or_response_columns_exported": stage_cascade_manifest.get(
                    "raw_prompt_or_response_columns_exported"
                ),
            },
            "final_figures": {
                "status": "PASS",
                "real_api_calls": final_figures_manifest.get("real_api_calls"),
                "raw_response_inspection": final_figures_manifest.get("raw_response_inspection"),
                "safe_wording_check": final_figures_manifest.get("safe_wording_check"),
                "n_figures": len(final_figures_manifest.get("figures", [])),
                "n_output_files": len(final_figures_manifest.get("output_files", [])),
            },
            "robustness_sensitivity": {
                "status": robustness_manifest.get("status"),
                "real_api_calls": robustness_manifest.get("real_api_calls"),
                "raw_response_inspection": robustness_manifest.get("raw_response_inspection"),
                "safe_wording_check": robustness_manifest.get("safe_wording_check"),
                "row_counts": robustness_manifest.get("row_counts"),
                "n_output_files": len(robustness_manifest.get("output_files", [])),
            },
            "validation": {
                "status": validation_manifest.get("status"),
                "real_api_calls": validation_manifest.get("real_api_calls"),
                "n_checks": validation_manifest.get("n_checks"),
                "n_failed_checks": validation_manifest.get("n_failed_checks"),
            },
            "comparison_validation": {
                "status": comparison_validation_manifest.get("status"),
                "real_api_calls": comparison_validation_manifest.get("real_api_calls"),
                "raw_response_inspection": comparison_validation_manifest.get("raw_response_inspection"),
                "n_checks": comparison_validation_manifest.get("n_checks"),
                "n_failed_checks": comparison_validation_manifest.get("n_failed_checks"),
                "validated_csv_count": comparison_validation_manifest.get("validated_csv_count"),
                "validated_manifest_count": comparison_validation_manifest.get("validated_manifest_count"),
            },
        },
    }

    _write_csv(
        outputs["pipeline_steps_csv"],
        step_rows,
        ["step_name", "status", "detail"],
    )

    outputs["manifest_json"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    _write_report(
        outputs["pipeline_report_md"],
        step_rows=step_rows,
        manifest=manifest,
    )

    if failed_steps:
        raise SystemExit(f"No-call evidence pipeline failed: {failed_steps}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Pilot 03 no-call evidence pipeline: compile scripts, rebuild derived "
            "tables, final figures, and robustness/sensitivity checks, and validate committed "
            "outputs. This command makes no real API calls."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = run_no_call_evidence_pipeline(output_dir=Path(args.output_dir))

    print("Pilot 03 no-call evidence pipeline completed.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"n_steps: {manifest['n_steps']}")
    print(f"n_failed_steps: {manifest['n_failed_steps']}")
    print(f"n_skipped_steps: {manifest['n_skipped_steps']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
