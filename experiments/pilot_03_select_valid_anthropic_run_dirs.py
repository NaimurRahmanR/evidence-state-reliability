from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_RESULTS_DIR = Path("results/pilot_03_real_llm_analysis")
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_anthropic_validity_selector")
DEFAULT_PLANNER_PS1 = DEFAULT_RESULTS_DIR / "pilot_03_anthropic_validity_selector_plan.ps1"
DEFAULT_AGGREGATE_JSON = DEFAULT_RESULTS_DIR / "pilot_03_anthropic_t0020_aggregate.json"

REQUIRED_STAGES = {"decision", "audit", "escalation"}
REQUIRED_CONDITIONS = {
    "original_evidence",
    "missing_policy_rule",
    "missing_one_required_unit",
}

SAFE_NOTE = (
    "Validity-aware Anthropic run selector for Pilot 03. This command makes no real API calls. "
    "It selects completed local run directories for aggregation and avoids known schema-invalid "
    "single-chain runs when a valid replacement exists."
)


@dataclass(frozen=True)
class ChainKey:
    task_id: str
    condition: str

    def label(self) -> str:
        return f"{self.task_id}::{self.condition}"


@dataclass
class DirInfo:
    run_dir: Path
    run_name: str
    selected_task_ids: list[str]
    summary_conditions: list[str]
    run_status: str
    n_chain_results_completed: int
    keys: set[ChainKey]
    chain_stage_counts: dict[ChainKey, int]
    chain_errors: dict[ChainKey, list[str]]
    chain_valid: dict[ChainKey, bool]
    dir_all_valid: bool
    last_write_time: float


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _repo_relative(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path.cwd().resolve()))
    except Exception:
        return str(path)


def _existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _parse_metadata_condition(raw_metadata: str, fallback_conditions: list[str]) -> str | None:
    raw_metadata = str(raw_metadata or "").strip()

    if raw_metadata:
        try:
            metadata = json.loads(raw_metadata)
            condition = metadata.get("condition")
            if condition:
                return str(condition)
        except Exception:
            pass

    if len(fallback_conditions) == 1:
        return fallback_conditions[0]

    return None


def _load_dir_info(run_dir: Path) -> DirInfo | None:
    summary_path = run_dir / "summary.json"
    call_records_path = run_dir / "call_records.csv"

    if not summary_path.exists() or not call_records_path.exists():
        return None

    summary = _read_json(summary_path)

    selected_task_ids_set: set[str] = set()
    summary_conditions_set: set[str] = set()
    chain_stages: dict[ChainKey, set[str]] = {}
    chain_errors: dict[ChainKey, list[str]] = {}

    with call_records_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            provider = str(row.get("provider", "")).strip().lower()
            client_mode = str(row.get("client_mode", "")).strip().lower()
            dry_run = str(row.get("dry_run", "")).strip().lower()

            if provider != "anthropic":
                continue

            if client_mode != "real_llm":
                continue

            if dry_run == "true":
                continue

            task_id = str(row.get("task_id", "")).strip()
            stage = str(row.get("stage", "")).strip()
            condition = _parse_metadata_condition(
                str(row.get("metadata", "")),
                [],
            )

            if not task_id or not stage or not condition:
                continue

            selected_task_ids_set.add(task_id)
            summary_conditions_set.add(condition)

            key = ChainKey(task_id=task_id, condition=condition)
            chain_stages.setdefault(key, set()).add(stage)

            error = str(row.get("error", "")).strip()
            metadata_errors: list[str] = []

            raw_metadata = str(row.get("metadata", "")).strip()
            if raw_metadata:
                try:
                    metadata = json.loads(raw_metadata)
                    parse_errors = metadata.get("parse_errors", [])
                    if isinstance(parse_errors, list):
                        metadata_errors = [str(item) for item in parse_errors if str(item).strip()]
                except Exception:
                    metadata_errors = []

            errors = []
            if error:
                errors.append(error)
            errors.extend(metadata_errors)

            chain_errors.setdefault(key, []).extend(errors)

    keys = set(chain_stages.keys())

    if not keys:
        return None

    chain_stage_counts = {
        key: len(stages)
        for key, stages in chain_stages.items()
    }

    chain_valid = {
        key: chain_stages.get(key, set()) == REQUIRED_STAGES and not chain_errors.get(key, [])
        for key in keys
    }

    dir_all_valid = bool(keys) and all(chain_valid.values())

    selected_task_ids = sorted(selected_task_ids_set)
    summary_conditions = sorted(summary_conditions_set)

    return DirInfo(
        run_dir=_normalize_path(run_dir),
        run_name=run_dir.name,
        selected_task_ids=selected_task_ids,
        summary_conditions=summary_conditions,
        run_status=str(summary.get("run_status", "completed_from_call_records")),
        n_chain_results_completed=len(keys),
        keys=keys,
        chain_stage_counts=chain_stage_counts,
        chain_errors=chain_errors,
        chain_valid=chain_valid,
        dir_all_valid=dir_all_valid,
        last_write_time=run_dir.stat().st_mtime,
    )


def _run_planner(
    *,
    planner_ps1: Path,
    aggregate_json: Path,
) -> None:
    planner_ps1.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "experiments.pilot_03_plan_real_runs",
        "--task-start",
        "1",
        "--task-end",
        "20",
        "--provider",
        "anthropic",
        "--conditions",
        "all",
        "--output-ps1",
        str(planner_ps1),
        "--aggregate-output-json",
        str(aggregate_json),
    ]

    completed = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    log_path = planner_ps1.with_suffix(".log.txt")
    log_path.write_text(
        "COMMAND:\n"
        + " ".join(cmd)
        + "\n\nSTDOUT:\n"
        + completed.stdout
        + "\n\nSTDERR:\n"
        + completed.stderr
        + "\n\nRETURN_CODE:\n"
        + str(completed.returncode)
        + "\n",
        encoding="utf-8",
    )

    if completed.returncode != 0:
        raise RuntimeError(f"Planner failed. See log: {log_path}")


def _parse_planner_run_dirs(planner_ps1: Path) -> list[Path]:
    text = planner_ps1.read_text(encoding="utf-8", errors="replace")
    run_dirs: list[Path] = []

    for line in text.splitlines():
        stripped = line.strip().rstrip("`").strip()

        if stripped.startswith(".\\results\\pilot_03_real_llm_analysis\\pilot_03_anthropic_small_chain"):
            normalized = stripped.replace(".\\", "")
            run_dirs.append(Path(normalized))

    return run_dirs


def _normalize_path(path: Path) -> Path:
    return Path(path).resolve()


def _discover_candidate_dirs(results_dir: Path) -> dict[Path, DirInfo]:
    output: dict[Path, DirInfo] = {}

    resolved_results_dir = _normalize_path(results_dir)

    for run_dir in sorted(resolved_results_dir.glob("pilot_03_anthropic_small_chain*")):
        info = _load_dir_info(run_dir)
        if info is None:
            continue
        output[_normalize_path(run_dir)] = info

    return output


def _build_candidate_index(candidate_infos: dict[Path, DirInfo]) -> dict[ChainKey, list[DirInfo]]:
    index: dict[ChainKey, list[DirInfo]] = {}

    for info in candidate_infos.values():
        for key in info.keys:
            index.setdefault(key, []).append(info)

    for key in index:
        # Prefer valid single-chain directories first, then newest valid directory.
        index[key].sort(
            key=lambda info: (
                not (info.chain_valid.get(key, False) and info.dir_all_valid),
                len(info.keys),
                -info.last_write_time,
            )
        )

    return index


def _select_valid_dirs(
    *,
    baseline_dirs: list[Path],
    candidate_infos: dict[Path, DirInfo],
) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_index = _build_candidate_index(candidate_infos)

    selected_dirs: list[Path] = []
    replacement_rows: list[dict[str, Any]] = []
    unresolved_rows: list[dict[str, Any]] = []

    selected_set: set[Path] = set()

    for baseline_dir in baseline_dirs:
        info = candidate_infos.get(Path(baseline_dir))

        if info is None:
            unresolved_rows.append(
                {
                    "issue": "baseline_dir_missing_or_unreadable",
                    "baseline_dir": _repo_relative(baseline_dir),
                    "task_id": "",
                    "condition": "",
                    "replacement_dir": "",
                    "detail": "Baseline directory from planner was not found or did not contain readable completed outputs.",
                }
            )
            continue

        if info.dir_all_valid:
            if info.run_dir not in selected_set:
                selected_dirs.append(info.run_dir)
                selected_set.add(info.run_dir)
            continue

        if len(info.keys) != 1:
            unresolved_rows.append(
                {
                    "issue": "invalid_multi_chain_dir",
                    "baseline_dir": _repo_relative(info.run_dir),
                    "task_id": "",
                    "condition": "",
                    "replacement_dir": "",
                    "detail": "Directory has at least one invalid chain and multiple chains; cannot safely exclude only one chain at directory level.",
                }
            )
            continue

        key = next(iter(info.keys))
        replacements = [
            candidate
            for candidate in candidate_index.get(key, [])
            if candidate.run_dir != info.run_dir
            and candidate.chain_valid.get(key, False)
            and candidate.dir_all_valid
            and candidate.run_dir not in selected_set
        ]

        if not replacements:
            unresolved_rows.append(
                {
                    "issue": "no_valid_replacement_available",
                    "baseline_dir": _repo_relative(info.run_dir),
                    "task_id": key.task_id,
                    "condition": key.condition,
                    "replacement_dir": "",
                    "detail": f"errors={info.chain_errors.get(key, [])}",
                }
            )
            continue

        replacement = replacements[0]
        selected_dirs.append(replacement.run_dir)
        selected_set.add(replacement.run_dir)

        replacement_rows.append(
            {
                "issue": "invalid_single_chain_replaced",
                "baseline_dir": str(info.run_dir),
                "task_id": key.task_id,
                "condition": key.condition,
                "replacement_dir": str(replacement.run_dir),
                "detail": f"old_errors={info.chain_errors.get(key, [])}",
            }
        )

    return selected_dirs, replacement_rows, unresolved_rows


def _selected_key_counts(selected_dirs: list[Path], candidate_infos: dict[Path, DirInfo]) -> tuple[dict[ChainKey, int], list[dict[str, Any]]]:
    counts: dict[ChainKey, int] = {}
    invalid_selected_rows: list[dict[str, Any]] = []

    for run_dir in selected_dirs:
        info = candidate_infos[Path(run_dir)]

        for key in info.keys:
            counts[key] = counts.get(key, 0) + 1

            if not info.chain_valid.get(key, False):
                invalid_selected_rows.append(
                    {
                        "run_dir": _repo_relative(run_dir),
                        "task_id": key.task_id,
                        "condition": key.condition,
                        "errors": ";".join(info.chain_errors.get(key, [])),
                    }
                )

    return counts, invalid_selected_rows


def select_valid_anthropic_run_dirs(
    *,
    results_dir: Path,
    output_dir: Path,
    planner_ps1: Path,
    aggregate_json: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_planner(planner_ps1=planner_ps1, aggregate_json=aggregate_json)
    baseline_dirs = _parse_planner_run_dirs(planner_ps1)
    candidate_infos = _discover_candidate_dirs(results_dir)

    baseline_dirs = [_normalize_path(path) for path in baseline_dirs]

    selected_dirs, replacement_rows, unresolved_rows = _select_valid_dirs(
        baseline_dirs=baseline_dirs,
        candidate_infos=candidate_infos,
    )

    selected_key_counts, invalid_selected_rows = _selected_key_counts(
        selected_dirs,
        candidate_infos,
    )

    required_keys = {
        ChainKey(task_id=f"P03-T{i:04d}", condition=condition)
        for i in range(1, 21)
        for condition in sorted(REQUIRED_CONDITIONS)
    }

    selected_keys = set(selected_key_counts.keys())

    missing_keys = sorted(
        required_keys - selected_keys,
        key=lambda key: (key.task_id, key.condition),
    )

    duplicate_keys = sorted(
        [key for key, count in selected_key_counts.items() if count > 1],
        key=lambda key: (key.task_id, key.condition),
    )

    status = (
        "PASS"
        if not unresolved_rows
        and not missing_keys
        and not duplicate_keys
        and not invalid_selected_rows
        and len(selected_keys) == 60
        else "NEEDS_REPAIR"
    )

    outputs = {
        "selected_run_dirs_txt": output_dir / "selected_run_dirs.txt",
        "selector_report_md": output_dir / "anthropic_validity_selector_report.md",
        "candidate_rows_csv": output_dir / "candidate_rows.csv",
        "selection_issues_csv": output_dir / "selection_issues.csv",
        "manifest_json": output_dir / "manifest.json",
    }

    outputs["selected_run_dirs_txt"].write_text(
        "\n".join(_repo_relative(path) for path in selected_dirs) + ("\n" if selected_dirs else ""),
        encoding="utf-8",
    )

    candidate_rows: list[dict[str, Any]] = []
    for info in sorted(candidate_infos.values(), key=lambda item: item.run_name):
        for key in sorted(info.keys, key=lambda item: (item.task_id, item.condition)):
            candidate_rows.append(
                {
                    "run_dir": _repo_relative(info.run_dir),
                    "run_name": info.run_name,
                    "task_id": key.task_id,
                    "condition": key.condition,
                    "chain_stage_count": info.chain_stage_counts.get(key, 0),
                    "chain_valid": info.chain_valid.get(key, False),
                    "dir_all_valid": info.dir_all_valid,
                    "errors": ";".join(info.chain_errors.get(key, [])),
                }
            )

    issue_rows = []
    issue_rows.extend(replacement_rows)
    issue_rows.extend(unresolved_rows)
    issue_rows.extend(
        {
            "issue": "missing_selected_valid_key",
            "baseline_dir": "",
            "task_id": key.task_id,
            "condition": key.condition,
            "replacement_dir": "",
            "detail": "No selected valid directory covers this task-condition key.",
        }
        for key in missing_keys
    )
    issue_rows.extend(
        {
            "issue": "duplicate_selected_key",
            "baseline_dir": "",
            "task_id": key.task_id,
            "condition": key.condition,
            "replacement_dir": "",
            "detail": f"selected_count={selected_key_counts[key]}",
        }
        for key in duplicate_keys
    )
    issue_rows.extend(
        {
            "issue": "invalid_selected_key",
            "baseline_dir": row["run_dir"],
            "task_id": row["task_id"],
            "condition": row["condition"],
            "replacement_dir": "",
            "detail": row["errors"],
        }
        for row in invalid_selected_rows
    )

    _write_csv(
        outputs["candidate_rows_csv"],
        candidate_rows,
        [
            "run_dir",
            "run_name",
            "task_id",
            "condition",
            "chain_stage_count",
            "chain_valid",
            "dir_all_valid",
            "errors",
        ],
    )

    _write_csv(
        outputs["selection_issues_csv"],
        issue_rows,
        [
            "issue",
            "baseline_dir",
            "task_id",
            "condition",
            "replacement_dir",
            "detail",
        ],
    )

    manifest = {
        "created_at_utc": _existing_created_at(outputs["manifest_json"]),
        "status": status,
        "real_api_calls": 0,
        "safe_note": SAFE_NOTE,
        "baseline_run_dirs_from_planner": len(baseline_dirs),
        "candidate_run_dirs_found": len(candidate_infos),
        "selected_run_dirs": len(selected_dirs),
        "selected_unique_task_condition_keys": len(selected_keys),
        "required_task_condition_keys": len(required_keys),
        "missing_selected_valid_keys": [key.label() for key in missing_keys],
        "duplicate_selected_keys": [key.label() for key in duplicate_keys],
        "n_replacements": len(replacement_rows),
        "n_unresolved": len(unresolved_rows),
        "n_invalid_selected_rows": len(invalid_selected_rows),
        "outputs": {name: str(path) for name, path in outputs.items()},
    }

    _write_json(outputs["manifest_json"], manifest)

    report_lines = [
        "# Pilot 03 Anthropic validity-aware run selector",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        f"Selector status: **{status}**",
        "",
        "## Summary",
        "",
        f"- Baseline run dirs from planner: {manifest['baseline_run_dirs_from_planner']}",
        f"- Candidate run dirs found: {manifest['candidate_run_dirs_found']}",
        f"- Selected run dirs: {manifest['selected_run_dirs']}",
        f"- Selected unique task-condition keys: {manifest['selected_unique_task_condition_keys']}",
        f"- Required task-condition keys: {manifest['required_task_condition_keys']}",
        f"- Missing selected valid keys: {len(missing_keys)}",
        f"- Duplicate selected keys: {len(duplicate_keys)}",
        f"- Replacements: {len(replacement_rows)}",
        f"- Unresolved issues: {len(unresolved_rows)}",
        f"- Invalid selected rows: {len(invalid_selected_rows)}",
        "",
        "## Missing selected valid keys",
        "",
    ]

    if missing_keys:
        report_lines.extend(f"- {key.label()}" for key in missing_keys)
    else:
        report_lines.append("None.")

    report_lines.extend(["", "## Replacements", ""])

    if replacement_rows:
        for row in replacement_rows:
            report_lines.append(
                f"- {row['task_id']}::{row['condition']} replaced "
                f"{row['baseline_dir']} with {row['replacement_dir']}"
            )
    else:
        report_lines.append("None.")

    report_lines.extend(["", "## Unresolved issues", ""])

    if unresolved_rows:
        for row in unresolved_rows:
            report_lines.append(
                f"- {row['issue']} | {row['task_id']}::{row['condition']} | {row['detail']}"
            )
    else:
        report_lines.append("None.")

    report_lines.extend(["", "## Outputs", ""])

    for name, output_path in outputs.items():
        report_lines.append(f"- {name}: `{output_path}`")

    outputs["selector_report_md"].write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Select validity-aware Anthropic Pilot 03 run directories for aggregation. "
            "This command makes no real API calls."
        )
    )
    parser.add_argument("--results-dir", default=str(DEFAULT_RESULTS_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--planner-ps1", default=str(DEFAULT_PLANNER_PS1))
    parser.add_argument("--aggregate-json", default=str(DEFAULT_AGGREGATE_JSON))
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Exit non-zero unless selector status is PASS.",
    )
    args = parser.parse_args()

    manifest = select_valid_anthropic_run_dirs(
        results_dir=Path(args.results_dir),
        output_dir=Path(args.output_dir),
        planner_ps1=Path(args.planner_ps1),
        aggregate_json=Path(args.aggregate_json),
    )

    print("Pilot 03 Anthropic validity-aware run selector completed.")
    print(f"status: {manifest['status']}")
    print(f"baseline_run_dirs_from_planner: {manifest['baseline_run_dirs_from_planner']}")
    print(f"candidate_run_dirs_found: {manifest['candidate_run_dirs_found']}")
    print(f"selected_run_dirs: {manifest['selected_run_dirs']}")
    print(f"selected_unique_task_condition_keys: {manifest['selected_unique_task_condition_keys']}")
    print(f"required_task_condition_keys: {manifest['required_task_condition_keys']}")
    print(f"missing_selected_valid_keys: {manifest['missing_selected_valid_keys']}")
    print(f"n_replacements: {manifest['n_replacements']}")
    print(f"n_unresolved: {manifest['n_unresolved']}")
    print(f"n_invalid_selected_rows: {manifest['n_invalid_selected_rows']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")

    if args.require_pass and manifest["status"] != "PASS":
        raise SystemExit("Selector status is not PASS.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
