from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.pilot_03_dry_run_runner import DEFAULT_CONDITIONS


RESULTS_DIR = Path("results/pilot_03_real_llm_analysis")
STAGES_REQUIRED = {"decision", "audit", "escalation"}


@dataclass(frozen=True)
class CompletedChain:
    task_id: str
    condition: str
    run_dir: Path
    stages: tuple[str, ...]


def _task_id(task_number: int) -> str:
    if task_number <= 0:
        raise ValueError("Task number must be positive.")
    return f"P03-T{task_number:04d}"


def _condition_order(conditions: list[str]) -> dict[str, int]:
    return {condition: index for index, condition in enumerate(conditions)}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    if not path.exists():
        return records

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL in {path} at line {line_number}: {exc}") from exc

        if isinstance(value, dict):
            records.append(value)

    return records


def _extract_condition(record: dict[str, Any]) -> str | None:
    metadata = record.get("metadata", {})
    if isinstance(metadata, dict):
        condition = metadata.get("condition")
        if isinstance(condition, str) and condition:
            return condition
    return None


def _completed_chains_in_run_dir(run_dir: Path) -> list[CompletedChain]:
    raw_path = run_dir / "raw_responses.jsonl"
    records = _read_jsonl(raw_path)

    grouped: dict[tuple[str, str], set[str]] = {}

    for record in records:
        task_id = record.get("task_id")
        stage = record.get("stage")
        condition = _extract_condition(record)

        if not isinstance(task_id, str) or not isinstance(stage, str) or condition is None:
            continue

        grouped.setdefault((task_id, condition), set()).add(stage)

    chains: list[CompletedChain] = []

    for (task_id, condition), stages in grouped.items():
        if STAGES_REQUIRED.issubset(stages):
            chains.append(
                CompletedChain(
                    task_id=task_id,
                    condition=condition,
                    run_dir=run_dir,
                    stages=tuple(sorted(stages)),
                )
            )

    return chains


def scan_completed_chains(results_dir: Path) -> list[CompletedChain]:
    if not results_dir.exists():
        return []

    chains: list[CompletedChain] = []

    for run_dir in sorted(path for path in results_dir.iterdir() if path.is_dir()):
        chains.extend(_completed_chains_in_run_dir(run_dir))

    return chains


def _latest_completed_map(chains: list[CompletedChain]) -> dict[tuple[str, str], CompletedChain]:
    latest: dict[tuple[str, str], CompletedChain] = {}

    for chain in chains:
        key = (chain.task_id, chain.condition)

        if key not in latest:
            latest[key] = chain
            continue

        old_mtime = latest[key].run_dir.stat().st_mtime
        new_mtime = chain.run_dir.stat().st_mtime

        if new_mtime >= old_mtime:
            latest[key] = chain

    return latest


def _make_run_command(task_id: str, condition: str) -> str:
    return (
        "python -m experiments.pilot_03_zai_small_chain_run "
        "--confirm-real-llm-call "
        f"--task-ids {task_id} "
        f"--conditions {condition}"
    )


def _make_aggregate_command(run_dirs: list[Path], output_json: Path) -> str:
    lines = [
        "python -m experiments.pilot_03_aggregate_real_runs `",
        "  --run-dirs `",
    ]

    for run_dir in run_dirs:
        lines.append(f"  .\\{run_dir} `")

    lines.append(f"  --output-json .\\{output_json}")
    return "\n".join(lines)


def _unique_run_dirs_for_selected_chains(
    *,
    latest_map: dict[tuple[str, str], CompletedChain],
    task_ids: list[str],
    conditions: list[str],
) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()

    for task_id in task_ids:
        for condition in conditions:
            chain = latest_map.get((task_id, condition))
            if chain is None:
                continue

            if chain.run_dir not in seen:
                ordered.append(chain.run_dir)
                seen.add(chain.run_dir)

    return ordered


def write_plan_file(path: Path, commands: list[str], aggregate_command: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "# Pilot 03 real GLM run plan",
        "# Generated helper file. Review before running.",
        "# These commands make real API calls only when executed manually.",
        "",
    ]

    if commands:
        lines.append("# Real GLM chain commands")
        lines.extend(commands)
        lines.append("")
    else:
        lines.append("# No missing task-condition chains found for this range.")
        lines.append("")

    if aggregate_command:
        lines.append("# Aggregate command after the planned runs are complete")
        lines.append(aggregate_command)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan guarded Pilot 03 real GLM chain runs without making API calls."
    )
    parser.add_argument("--task-start", type=int, required=True)
    parser.add_argument("--task-end", type=int, required=True)
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=list(DEFAULT_CONDITIONS),
        help="Evidence conditions to plan, or all.",
    )
    parser.add_argument(
        "--results-dir",
        default=str(RESULTS_DIR),
        help="Directory containing ignored real LLM run folders.",
    )
    parser.add_argument(
        "--output-ps1",
        default=None,
        help="Optional path to write a PowerShell plan file.",
    )
    parser.add_argument(
        "--aggregate-output-json",
        default=None,
        help="Optional aggregate JSON path to include in the aggregate command.",
    )

    args = parser.parse_args()

    if args.task_end < args.task_start:
        raise ValueError("--task-end must be greater than or equal to --task-start")

    conditions = list(DEFAULT_CONDITIONS) if "all" in [item.lower() for item in args.conditions] else args.conditions
    task_ids = [_task_id(task_number) for task_number in range(args.task_start, args.task_end + 1)]

    completed_chains = scan_completed_chains(Path(args.results_dir))
    latest_map = _latest_completed_map(completed_chains)

    missing_commands: list[str] = []

    for task_id in task_ids:
        for condition in conditions:
            if (task_id, condition) not in latest_map:
                missing_commands.append(_make_run_command(task_id, condition))

    aggregate_command = None
    if args.aggregate_output_json:
        aggregate_task_ids = [_task_id(task_number) for task_number in range(1, args.task_end + 1)]
        selected_run_dirs = _unique_run_dirs_for_selected_chains(
            latest_map=latest_map,
            task_ids=aggregate_task_ids,
            conditions=conditions,
        )
        aggregate_command = _make_aggregate_command(
            run_dirs=selected_run_dirs,
            output_json=Path(args.aggregate_output_json),
        )

    print("Pilot 03 real GLM run planner")
    print("=============================")
    print(f"results_dir: {Path(args.results_dir)}")
    print(f"task_range: {task_ids[0]} -> {task_ids[-1]}")
    print(f"conditions: {conditions}")
    print(f"completed_chain_keys_found: {len(latest_map)}")
    print(f"missing_commands: {len(missing_commands)}")
    print()

    if missing_commands:
        print("Commands to run manually:")
        print("-------------------------")
        for command in missing_commands:
            print(command)
        print()
    else:
        print("No missing task-condition chains found for this range.")
        print()

    if aggregate_command:
        print("Aggregate command for completed chains currently found:")
        print("------------------------------------------------------")
        print(aggregate_command)
        print()

    if args.output_ps1:
        write_plan_file(Path(args.output_ps1), missing_commands, aggregate_command)
        print(f"Wrote plan file: {args.output_ps1}")

    print()
    print("Safe note:")
    print("This planner made no API calls. It only generated commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
