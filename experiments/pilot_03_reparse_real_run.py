from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.pilot_03_parser import parse_and_validate_raw_response, summarise_parsed_responses


SCRIPT_VERSION = "pilot_03_reparse_real_run_v1"


def load_raw_response_records(raw_responses_jsonl: Path) -> list[dict[str, Any]]:
    """Load raw Pilot 03 response records from a JSONL file."""
    records: list[dict[str, Any]] = []

    with raw_responses_jsonl.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Could not parse JSONL line {line_number} in {raw_responses_jsonl}: {exc}"
                ) from exc

            records.append(record)

    return records


def parse_records(records: list[dict[str, Any]]) -> list[Any]:
    """Parse raw records using the current Pilot 03 parser."""
    parsed = []

    for record in records:
        parsed.append(
            parse_and_validate_raw_response(
                call_id=record["call_id"],
                task_id=record["task_id"],
                stage=record["stage"],
                raw_response_text=record["raw_response_text"],
            )
        )

    return parsed


def build_chain_summary(records: list[dict[str, Any]], parsed_records: list[Any]) -> list[dict[str, Any]]:
    """Build one row per completed task-condition chain."""
    chains: dict[tuple[str, str], dict[str, Any]] = {}

    for record, parsed in zip(records, parsed_records, strict=True):
        metadata = record.get("metadata", {})
        task_id = record["task_id"]
        condition = metadata.get("condition", "unknown_condition")
        gold_decision = metadata.get("gold_decision", metadata.get("gold", None))
        stage = record["stage"]

        key = (task_id, condition)
        chains.setdefault(
            key,
            {
                "task_id": task_id,
                "condition": condition,
                "gold_decision": gold_decision,
                "decision": None,
                "audit_passed": None,
                "audit_detected_issue": None,
                "audit_supported_decision": None,
                "escalation": None,
                "escalation_overrode_previous_stage": None,
                "decision_valid_schema": False,
                "audit_valid_schema": False,
                "escalation_valid_schema": False,
            },
        )

        if gold_decision is not None:
            chains[key]["gold_decision"] = gold_decision

        if stage == "decision":
            chains[key]["decision"] = parsed.parsed_response.get("final_decision")
            chains[key]["decision_valid_schema"] = parsed.valid_schema

        elif stage == "audit":
            chains[key]["audit_passed"] = parsed.parsed_response.get("audit_passed")
            chains[key]["audit_detected_issue"] = parsed.parsed_response.get("detected_issue")
            chains[key]["audit_supported_decision"] = parsed.parsed_response.get("supported_decision")
            chains[key]["audit_valid_schema"] = parsed.valid_schema

        elif stage == "escalation":
            chains[key]["escalation"] = parsed.parsed_response.get("final_decision")
            chains[key]["escalation_overrode_previous_stage"] = parsed.parsed_response.get(
                "overrode_previous_stage"
            )
            chains[key]["escalation_valid_schema"] = parsed.valid_schema

    rows: list[dict[str, Any]] = []

    for row in chains.values():
        row["valid_chain"] = (
            row["decision_valid_schema"]
            and row["audit_valid_schema"]
            and row["escalation_valid_schema"]
        )

        gold_decision = row.get("gold_decision")
        decision = row.get("decision")
        escalation = row.get("escalation")

        row["decision_correct"] = decision == gold_decision if gold_decision is not None else None
        row["escalation_correct"] = escalation == gold_decision if gold_decision is not None else None

        rows.append(row)

    return sorted(rows, key=lambda item: (item["task_id"], item["condition"]))


def summarise_chain_rows(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise one-row-per-chain records."""
    return {
        "n_chain_rows": len(chain_rows),
        "condition_counts": dict(Counter(row["condition"] for row in chain_rows)),
        "gold_decisions": dict(Counter(str(row["gold_decision"]) for row in chain_rows)),
        "decision_correct": dict(Counter(str(row["decision_correct"]) for row in chain_rows)),
        "escalation_correct": dict(Counter(str(row["escalation_correct"]) for row in chain_rows)),
        "audit_passed": dict(Counter(str(row["audit_passed"]) for row in chain_rows)),
        "valid_chain": dict(Counter(str(row["valid_chain"]) for row in chain_rows)),
    }


def print_chain_table(chain_rows: list[dict[str, Any]]) -> None:
    """Print compact chain rows."""
    print(
        "task_id,condition,gold_decision,decision,decision_correct,"
        "audit_passed,audit_supported_decision,escalation,escalation_correct,"
        "overrode,valid_chain"
    )

    for row in chain_rows:
        print(
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-parse a saved Pilot 03 real LLM run using the current parser."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Saved real LLM run directory containing raw_responses.jsonl.",
    )

    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    raw_responses_jsonl = run_dir / "raw_responses.jsonl"

    if not raw_responses_jsonl.exists():
        raise FileNotFoundError(f"Missing raw response log: {raw_responses_jsonl}")

    records = load_raw_response_records(raw_responses_jsonl)
    parsed_records = parse_records(records)
    chain_rows = build_chain_summary(records, parsed_records)

    output = {
        "script_version": SCRIPT_VERSION,
        "run_dir": str(run_dir),
        "raw_responses_jsonl": str(raw_responses_jsonl),
        "parser_summary": summarise_parsed_responses(parsed_records),
        "chain_summary": summarise_chain_rows(chain_rows),
        "chain_rows": chain_rows,
    }

    print("Pilot 03 real run re-parse")
    print("==========================")
    print(json.dumps(output["parser_summary"], indent=2))
    print()
    print(json.dumps(output["chain_summary"], indent=2))
    print()
    print_chain_table(chain_rows)


if __name__ == "__main__":
    main()