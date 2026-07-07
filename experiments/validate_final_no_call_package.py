from __future__ import annotations

import csv
import json
import py_compile
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path("reports/final_no_call_validation")
VALIDATION_SUMMARY_CSV = OUTPUT_DIR / "validation_summary.csv"
MANIFEST_JSON = OUTPUT_DIR / "manifest.json"
STATUS_DOC = Path("docs/cross_pilot_final_status_checkpoint.md")

SCRIPT_COMPILE_TARGETS = [
    Path("experiments/pilot_03_validate_all_committed_outputs.py"),
    Path("experiments/pilot_03_run_no_call_evidence_pipeline.py"),
    Path("experiments/pilot_04_export_tasks.py"),
    Path("experiments/pilot_04_run_dry_run.py"),
    Path("experiments/pilot_04_generate_analysis_outputs.py"),
    Path("experiments/pilot_04_validate_committed_outputs.py"),
    Path("experiments/pilot_04_run_no_call_evidence_pipeline.py"),
    Path("experiments/generate_cross_pilot_evidence_state_report.py"),
    Path("experiments/validate_cross_pilot_evidence_state_report.py"),
    Path("experiments/generate_cross_pilot_figures_tables.py"),
]

REQUIRED_MANIFESTS = [
    Path("reports/pilot_03_no_call_pipeline/manifest.json"),
    Path("reports/pilot_03_comparison_validation/manifest.json"),
    Path("reports/pilot_03_robustness_sensitivity/manifest.json"),
    Path("reports/pilot_04_no_call_pipeline/manifest.json"),
    Path("reports/pilot_04_validation/manifest.json"),
    Path("reports/cross_pilot_evidence_state_reliability/manifest.json"),
    Path("reports/cross_pilot_validation/manifest.json"),
    Path("reports/cross_pilot_figures_tables/manifest.json"),
]

REQUIRED_OUTPUTS = [
    Path("docs/pilot_04_second_domain_design.md"),
    Path("docs/cross_pilot_final_status_checkpoint.md"),
    Path("reports/cross_pilot_evidence_state_reliability/cross_pilot_report.md"),
    Path("reports/cross_pilot_figures_tables/table_figure_index.md"),
]

RISKY_PUBLIC_WORDING = [
    "Q1",
    "journal-level",
    "groundbreaking",
    "proven",
    "universal",
    "real-world deployment proof",
    "provider ranking",
    "general Claude reliability",
    "general GLM reliability",
    "live deployment validity",
    "broad LLM reliability",
    "general model superiority",
    "financial safety",
    "legal safety",
    "medical safety",
    "lending regulation",
    "compliance with lending regulation",
]

FORBIDDEN_CONTENT_MARKERS = [
    "raw_prompt_text",
    "raw_response_text",
    "api_key",
    "secret_key",
    "BEGIN_API",
    "END_API",
]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalise_raw_response_inspection(manifest: dict[str, Any]) -> bool:
    """Treat missing/blank legacy metadata as False, but preserve True as failure."""
    value = manifest.get("raw_response_inspection", False)

    if value is False or value is None:
        return False

    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}

    return bool(value)


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


def _add_step(rows: list[dict[str, Any]], step_name: str, status: str, detail: str) -> None:
    rows.append(
        {
            "step_name": step_name,
            "status": status,
            "detail": detail,
        }
    )


def _run_command(rows: list[dict[str, Any]], step_name: str, command: list[str]) -> None:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    detail = (
        f"returncode={completed.returncode}; "
        f"stdout_tail={completed.stdout[-800:].strip()}; "
        f"stderr_tail={completed.stderr[-800:].strip()}"
    )

    _add_step(rows, step_name, "PASS" if completed.returncode == 0 else "FAIL", detail)

    if completed.returncode != 0:
        raise RuntimeError(f"{step_name} failed: {detail}")


def _compile_scripts(rows: list[dict[str, Any]]) -> None:
    for script_path in SCRIPT_COMPILE_TARGETS:
        if not script_path.exists():
            _add_step(rows, f"compile::{script_path}", "FAIL", "script missing")
            raise FileNotFoundError(f"Missing script: {script_path}")

        py_compile.compile(str(script_path), doraise=True)
        _add_step(rows, f"compile::{script_path}", "PASS", "py_compile passed")


def _validate_manifests(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_summaries: dict[str, Any] = {}

    for manifest_path in REQUIRED_MANIFESTS:
        if not manifest_path.exists():
            _add_step(rows, f"manifest_exists::{manifest_path}", "FAIL", "manifest missing")
            raise FileNotFoundError(f"Missing manifest: {manifest_path}")

        manifest = _load_json(manifest_path)
        status = manifest.get("status")
        real_api_calls = manifest.get("real_api_calls")
        raw_response_inspection = _normalise_raw_response_inspection(manifest)

        pass_condition = (
            status == "PASS"
            and real_api_calls == 0
            and raw_response_inspection is False
        )

        _add_step(
            rows,
            f"manifest_safety::{manifest_path}",
            "PASS" if pass_condition else "FAIL",
            (
                f"status={status}; "
                f"real_api_calls={real_api_calls}; "
                f"raw_response_inspection={raw_response_inspection}"
            ),
        )

        if not pass_condition:
            raise RuntimeError(f"Manifest safety check failed for {manifest_path}")

        manifest_summaries[manifest_path.as_posix()] = {
            "artifact": manifest.get("artifact"),
            "status": status,
            "real_api_calls": real_api_calls,
            "raw_response_inspection": raw_response_inspection,
            "n_steps": manifest.get("n_steps", ""),
            "n_failed_steps": manifest.get("n_failed_steps", ""),
            "n_checks": manifest.get("n_checks", ""),
            "n_failed_checks": manifest.get("n_failed_checks", ""),
            "row_counts": manifest.get("row_counts", {}),
        }

    return manifest_summaries


def _validate_figures_tables(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = _load_json(Path("reports/cross_pilot_figures_tables/manifest.json"))

    table_files = [Path(path) for path in manifest["table_files"]]
    figure_files = [Path(path) for path in manifest["figure_files"]]

    missing_tables = [str(path) for path in table_files if not path.exists()]
    missing_figures = [str(path) for path in figure_files if not path.exists()]
    small_figures = [f"{path}:{path.stat().st_size}" for path in figure_files if path.exists() and path.stat().st_size < 1000]

    pass_condition = not missing_tables and not missing_figures and not small_figures

    _add_step(
        rows,
        "cross_pilot_figures_tables_files",
        "PASS" if pass_condition else "FAIL",
        f"tables={len(table_files)}; figures={len(figure_files)}; missing_tables={missing_tables}; missing_figures={missing_figures}; small_figures={small_figures}",
    )

    if not pass_condition:
        raise RuntimeError("Cross-pilot figure/table file validation failed.")

    return {
        "n_tables": len(table_files),
        "n_figures": len(figure_files),
    }


def _public_wording_scan(rows: list[dict[str, Any]]) -> None:
    scanned_paths = [
        Path("docs/pilot_04_second_domain_design.md"),
        Path("reports/cross_pilot_evidence_state_reliability/cross_pilot_report.md"),
        Path("reports/cross_pilot_figures_tables/table_figure_index.md"),
    ]

    hits: list[str] = []
    for path in scanned_paths:
        text = path.read_text(encoding="utf-8")
        for phrase in RISKY_PUBLIC_WORDING:
            if phrase in text:
                hits.append(f"{path}::{phrase}")

    _add_step(
        rows,
        "public_wording_safety_scan",
        "PASS" if not hits else "FAIL",
        f"hits={hits}",
    )

    if hits:
        raise RuntimeError(f"Public wording safety scan failed: {hits}")


def _raw_secret_marker_scan(rows: list[dict[str, Any]]) -> None:
    tracked_files = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    skipped_placeholder_files = {
        ".env.example",
        ".gitignore",
    }

    skipped_suffixes = {
        ".py",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".pdf",
    }

    scanned_count = 0
    skipped_count = 0
    hits: list[str] = []

    for file_name in tracked_files:
        normalised_name = file_name.replace("\\", "/")
        path = Path(file_name)

        if not path.exists():
            continue

        if normalised_name in skipped_placeholder_files:
            skipped_count += 1
            continue

        if path.suffix.lower() in skipped_suffixes:
            skipped_count += 1
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            skipped_count += 1
            continue

        scanned_count += 1
        for marker in FORBIDDEN_CONTENT_MARKERS:
            if marker in text:
                hits.append(f"{file_name}::{marker}")

    _add_step(
        rows,
        "tracked_content_no_raw_or_secret_markers",
        "PASS" if not hits else "FAIL",
        f"scanned_files={scanned_count}; skipped_files={skipped_count}; hits={hits[:10]}",
    )

    if hits:
        raise RuntimeError(f"Tracked content marker scan failed: {hits[:10]}")


def _tracked_filename_safety_scan(rows: list[dict[str, Any]]) -> None:
    tracked_files = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    unsafe = [
        file_name
        for file_name in tracked_files
        if file_name.endswith(".env")
        or file_name.endswith(".jsonl")
        or "secret" in file_name.lower()
        or "api_key" in file_name.lower()
    ]

    _add_step(
        rows,
        "tracked_filename_safety_scan",
        "PASS" if not unsafe else "FAIL",
        f"unsafe={unsafe[:10]}",
    )

    if unsafe:
        raise RuntimeError(f"Unsafe tracked filenames detected: {unsafe[:10]}")


def _manifest_summary(manifest_summaries: dict[str, Any], path_text: str) -> dict[str, Any]:
    normalised = path_text.replace("\\", "/")
    if normalised in manifest_summaries:
        return manifest_summaries[normalised]

    windows_style = normalised.replace("/", "\\")
    if windows_style in manifest_summaries:
        return manifest_summaries[windows_style]

    raise KeyError(f"Manifest summary not found for {path_text}. Available keys: {sorted(manifest_summaries)}")


def _write_status_doc(manifest_summaries: dict[str, Any], figure_summary: dict[str, Any]) -> None:
    p03_no_call = _manifest_summary(manifest_summaries, "reports/pilot_03_no_call_pipeline/manifest.json")
    p03_comparison = _manifest_summary(manifest_summaries, "reports/pilot_03_comparison_validation/manifest.json")
    p04_no_call = _manifest_summary(manifest_summaries, "reports/pilot_04_no_call_pipeline/manifest.json")
    p04_validation = _manifest_summary(manifest_summaries, "reports/pilot_04_validation/manifest.json")
    cross_report = _manifest_summary(manifest_summaries, "reports/cross_pilot_evidence_state_reliability/manifest.json")
    cross_validation = _manifest_summary(manifest_summaries, "reports/cross_pilot_validation/manifest.json")
    figures_tables = _manifest_summary(manifest_summaries, "reports/cross_pilot_figures_tables/manifest.json")

    text = f"""# Cross-Pilot Final Status Checkpoint

## Scope

This checkpoint records the current committed state of the Evidence-State Reliability work after Pilot 04 and cross-pilot integration.

The repository now contains:

- Pilot 03: locked synthetic administrative approval evidence package.
- Pilot 04: deterministic no-call synthetic loan-risk decision-support evidence package.
- Cross-pilot outputs: framework summary, validation summary, condition alignment, metric inventory, figures, and tables.

## Validation status

| Component | Status | Steps | Failed steps | Checks | Failed checks | API calls | Raw response inspection |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pilot 03 no-call pipeline | {p03_no_call['status']} | {p03_no_call['n_steps']} | {p03_no_call['n_failed_steps']} |  |  | {p03_no_call['real_api_calls']} | {p03_no_call['raw_response_inspection']} |
| Pilot 03 comparison validation | {p03_comparison['status']} |  |  | {p03_comparison['n_checks']} | {p03_comparison['n_failed_checks']} | {p03_comparison['real_api_calls']} | {p03_comparison['raw_response_inspection']} |
| Pilot 04 no-call pipeline | {p04_no_call['status']} | {p04_no_call['n_steps']} | {p04_no_call['n_failed_steps']} |  |  | {p04_no_call['real_api_calls']} | {p04_no_call['raw_response_inspection']} |
| Pilot 04 committed-output validation | {p04_validation['status']} |  |  | {p04_validation['n_checks']} | {p04_validation['n_failed_checks']} | {p04_validation['real_api_calls']} | {p04_validation['raw_response_inspection']} |
| Cross-pilot report | {cross_report['status']} |  |  |  |  | {cross_report['real_api_calls']} | {cross_report['raw_response_inspection']} |
| Cross-pilot validation | {cross_validation['status']} |  |  | {cross_validation['n_checks']} | {cross_validation['n_failed_checks']} | {cross_validation['real_api_calls']} | {cross_validation['raw_response_inspection']} |
| Cross-pilot figures/tables | {figures_tables['status']} |  |  |  |  | {figures_tables['real_api_calls']} | {figures_tables['raw_response_inspection']} |

## Cross-pilot figure/table status

- Tables: {figure_summary['n_tables']}
- Figures: {figure_summary['n_figures']}

## Safe interpretation

The current repo supports a conservative controlled-experiment claim:

- evidence-state degradation is measurable;
- structural validity and reliability-layer behaviour are separate measurements;
- decision, audit, and escalation metrics can be compared across evidence conditions;
- the same measurement framing is implemented across two controlled synthetic domains.

The current repo does not establish operational deployment validity, overall model superiority, or safety for regulated use cases.

## Reproducibility boundary

This final checkpoint was generated from committed sanitized outputs and no-call validation scripts.

- real_api_calls: 0
- raw_response_inspection: False
"""

    STATUS_DOC.write_text(text, encoding="utf-8")


def run_final_validation() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    step_rows: list[dict[str, Any]] = []

    _compile_scripts(step_rows)

    _run_command(step_rows, "pilot_03_master_committed_output_validation", [sys.executable, "-m", "experiments.pilot_03_validate_all_committed_outputs"])
    _run_command(step_rows, "pilot_04_no_call_evidence_pipeline", [sys.executable, "-m", "experiments.pilot_04_run_no_call_evidence_pipeline"])
    _run_command(step_rows, "cross_pilot_report_validation", [sys.executable, "-m", "experiments.validate_cross_pilot_evidence_state_report"])

    manifest_summaries = _validate_manifests(step_rows)
    figure_summary = _validate_figures_tables(step_rows)

    _write_status_doc(manifest_summaries, figure_summary)
    _public_wording_scan(step_rows)
    _raw_secret_marker_scan(step_rows)
    _tracked_filename_safety_scan(step_rows)

    n_failed = sum(1 for row in step_rows if row["status"] != "PASS")

    manifest = {
        "artifact": "final_no_call_validation",
        "status": "PASS" if n_failed == 0 else "FAIL",
        "created_at_utc": _load_existing_created_at(MANIFEST_JSON),
        "validator": "experiments.validate_final_no_call_package",
        "n_steps": len(step_rows),
        "n_failed_steps": n_failed,
        "manifest_summaries": manifest_summaries,
        "figure_summary": figure_summary,
        "output_files": [
            str(VALIDATION_SUMMARY_CSV),
            str(MANIFEST_JSON),
            str(STATUS_DOC),
        ],
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }

    _write_csv(VALIDATION_SUMMARY_CSV, step_rows)
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if manifest["status"] != "PASS":
        raise RuntimeError("Final no-call validation failed.")

    return manifest


def main() -> None:
    manifest = run_final_validation()
    print("Final no-call validation completed.")
    print(f"output_dir: {OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"n_steps: {manifest['n_steps']}")
    print(f"n_failed_steps: {manifest['n_failed_steps']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")


if __name__ == "__main__":
    main()
