from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from experiments.pilot_03_reparse_real_run import (
    build_chain_summary,
    load_raw_response_records,
    parse_records,
)
from src.pilot_03_parser import Pilot03ParsedResponse, summarise_parsed_responses


SCRIPT_VERSION = "pilot_03_aggregate_real_runs_v1"


def _bool_rate(rows: list[dict[str, Any]], field: str) -> float | None:
    """Return the mean of a boolean field, ignoring None values."""
    values = [row.get(field) for row in rows if isinstance(row.get(field), bool)]

    if not values:
        return None

    return round(sum(1 for value in values if value) / len(values), 6)


def _counter_as_strings(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    """Count values as strings so JSON summaries are stable."""
    return dict(Counter(str(row.get(field)) for row in rows))


def _load_run(run_dir: Path) -> tuple[list[dict[str, Any]], list[Pilot03ParsedResponse], list[dict[str, Any]]]:
    """Load, parse, and summarise one saved real GLM run directory."""
    raw_responses_jsonl = run_dir / "raw_responses.jsonl"

    if not raw_responses_jsonl.exists():
        raise FileNotFoundError(f"Missing raw response log: {raw_responses_jsonl}")

    records = load_raw_response_records(raw_responses_jsonl)
    parsed_records = parse_records(records)
    chain_rows = build_chain_summary(records, parsed_records)

    for row in chain_rows:
        row["source_run_dir"] = str(run_dir)
        row["source_run_name"] = run_dir.name

    return records, parsed_records, chain_rows


def _validate_no_duplicate_chain_rows(chain_rows: list[dict[str, Any]]) -> None:
    """Fail safely if the same task-condition chain appears more than once."""
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    duplicates: list[tuple[str, str, str, str]] = []

    for row in chain_rows:
        key = (row["task_id"], row["condition"])

        if key in seen:
            duplicates.append(
                (
                    row["task_id"],
                    row["condition"],
                    seen[key]["source_run_name"],
                    row["source_run_name"],
                )
            )
        else:
            seen[key] = row

    if duplicates:
        preview = "; ".join(
            f"{task_id}/{condition}: {first_run} and {second_run}"
            for task_id, condition, first_run, second_run in duplicates[:10]
        )
        raise ValueError(
            "Duplicate task-condition chains found. "
            "This utility does not silently double-count duplicates. "
            f"Duplicates: {preview}"
        )


def _summarise_chain_rows(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise combined chain rows."""
    return {
        "n_chain_rows": len(chain_rows),
        "source_runs": dict(Counter(row["source_run_name"] for row in chain_rows)),
        "condition_counts": dict(Counter(row["condition"] for row in chain_rows)),
        "gold_decisions": _counter_as_strings(chain_rows, "gold_decision"),
        "decision_correct": _counter_as_strings(chain_rows, "decision_correct"),
        "escalation_correct": _counter_as_strings(chain_rows, "escalation_correct"),
        "audit_passed": _counter_as_strings(chain_rows, "audit_passed"),
        "valid_chain": _counter_as_strings(chain_rows, "valid_chain"),
        "decision_correct_rate": _bool_rate(chain_rows, "decision_correct"),
        "escalation_correct_rate": _bool_rate(chain_rows, "escalation_correct"),
        "valid_chain_rate": _bool_rate(chain_rows, "valid_chain"),
    }


def _summarise_by_condition(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return condition-level summaries for combined chain rows."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in chain_rows:
        grouped[row["condition"]].append(row)

    condition_summary: dict[str, Any] = {}

    for condition, rows in sorted(grouped.items()):
        condition_summary[condition] = {
            "n": len(rows),
            "gold_decisions": _counter_as_strings(rows, "gold_decision"),
            "decision_correct": _counter_as_strings(rows, "decision_correct"),
            "escalation_correct": _counter_as_strings(rows, "escalation_correct"),
            "audit_passed": _counter_as_strings(rows, "audit_passed"),
            "valid_chain": _counter_as_strings(rows, "valid_chain"),
            "decision_correct_rate": _bool_rate(rows, "decision_correct"),
            "escalation_correct_rate": _bool_rate(rows, "escalation_correct"),
            "valid_chain_rate": _bool_rate(rows, "valid_chain"),
        }

    return condition_summary


def _print_chain_table(chain_rows: list[dict[str, Any]]) -> None:
    """Print compact combined chain table."""
    print(
        "source_run,task_id,condition,gold_decision,decision,decision_correct,"
        "audit_passed,audit_supported_decision,escalation,escalation_correct,"
        "overrode,valid_chain"
    )

    for row in sorted(chain_rows, key=lambda item: (item["task_id"], item["condition"])):
        print(
            f"{row['source_run_name']},"
            f"{row['task_id']},"
            f"{row['condition']},"
            f"{row['gold_decision']},"
            f"{row['decision']},"
            f"{row['decision_correct']},"
            f"{row['audit_passed']},"
            f"{row['audit_supported_decision']},"
            f"{row['escalation']},"
            f"{row['escalation_correct']},"
            f"{row['escalation_overrode_previous_stage']},"
            f"{row['valid_chain']}"
        )


def aggregate_real_runs(run_dirs: list[Path]) -> dict[str, Any]:
    """Aggregate multiple saved Pilot 03 real GLM run directories."""
    all_records: list[dict[str, Any]] = []
    all_parsed_records: list[Pilot03ParsedResponse] = []
    all_chain_rows: list[dict[str, Any]] = []

    for run_dir in run_dirs:
        records, parsed_records, chain_rows = _load_run(run_dir)
        all_records.extend(records)
        all_parsed_records.extend(parsed_records)
        all_chain_rows.extend(chain_rows)

    _validate_no_duplicate_chain_rows(all_chain_rows)

    return {
        "script_version": SCRIPT_VERSION,
        "run_dirs": [str(run_dir) for run_dir in run_dirs],
        "n_source_runs": len(run_dirs),
        "n_raw_response_records": len(all_records),
        "parser_summary": summarise_parsed_responses(all_parsed_records),
        "combined_chain_summary": _summarise_chain_rows(all_chain_rows),
        "condition_summary": _summarise_by_condition(all_chain_rows),
        "chain_rows": sorted(
            all_chain_rows,
            key=lambda item: (item["task_id"], item["condition"], item["source_run_name"]),
        ),
        "safe_wording": "observed result under current Pilot 03 real LLM experimental conditions",
        "scope_limitation": (
            "This aggregation combines saved small controlled real GLM-5.2 Pilot 03 runs. "
            "It should not be generalised beyond the current Pilot 03 setup, model, prompts, tasks, "
            "parser, and evidence conditions."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate saved Pilot 03 real GLM run directories."
    )
    parser.add_argument(
        "--run-dirs",
        nargs="+",
        required=True,
        help="One or more saved real GLM run directories containing raw_responses.jsonl.",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional path to write the aggregate summary as JSON.",
    )

    args = parser.parse_args()
    run_dirs = [Path(item) for item in args.run_dirs]

    output = aggregate_real_runs(run_dirs)

    print("Pilot 03 real GLM aggregate")
    print("===========================")
    print()
    print("Parser summary:")
    print(json.dumps(output["parser_summary"], indent=2))
    print()
    print("Combined chain summary:")
    print(json.dumps(output["combined_chain_summary"], indent=2))
    print()
    print("Condition summary:")
    print(json.dumps(output["condition_summary"], indent=2))
    print()
    print("Combined chain table:")
    _print_chain_table(output["chain_rows"])
    print()
    print("Safe wording:")
    print(output["safe_wording"])

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print()
        print(f"output_json: {output_path}")


if __name__ == "__main__":
    main()