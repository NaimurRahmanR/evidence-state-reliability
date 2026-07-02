from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


CHAIN_COLUMNS = [
    "source_run",
    "task_id",
    "condition",
    "gold_decision",
    "decision",
    "decision_correct",
    "audit_passed",
    "audit_supported_decision",
    "escalation",
    "escalation_correct",
    "overrode",
    "valid_chain",
]

CONDITION_ORDER = {
    "original_evidence": 0,
    "missing_policy_rule": 1,
    "missing_one_required_unit": 2,
}


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise ValueError(f"Cannot read boolean value: {value!r}")


def rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def counter_text(counter: Counter[str]) -> str:
    if not counter:
        return "-"
    return ", ".join(f"{key}:{counter[key]}" for key in sorted(counter))


def run_aggregator(run_dirs: list[Path], aggregate_json: Path) -> str:
    command = [
        sys.executable,
        "-m",
        "experiments.pilot_03_aggregate_real_runs",
        "--run-dirs",
        *[str(path) for path in run_dirs],
        "--output-json",
        str(aggregate_json),
    ]

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "Aggregator failed.\n\nSTDOUT:\n"
            + completed.stdout
            + "\nSTDERR:\n"
            + completed.stderr
        )

    return completed.stdout


def parse_chain_table(stdout_text: str) -> list[dict[str, str]]:
    lines = stdout_text.splitlines()

    try:
        start = next(
            index for index, line in enumerate(lines)
            if line.strip() == "Combined chain table:"
        )
    except StopIteration as exc:
        raise ValueError("Could not find Combined chain table in aggregate output.") from exc

    table_lines: list[str] = []

    for line in lines[start + 1:]:
        stripped = line.strip()

        if stripped == "Safe wording:":
            break

        if not stripped and table_lines:
            break

        if stripped:
            table_lines.append(line)

    if not table_lines:
        raise ValueError("Combined chain table was empty.")

    rows = list(csv.DictReader(io.StringIO("\n".join(table_lines))))

    if not rows:
        raise ValueError("No chain rows parsed from combined chain table.")

    missing = [column for column in CHAIN_COLUMNS if column not in rows[0]]
    if missing:
        raise ValueError(f"Missing chain columns: {missing}")

    return sorted(
        rows,
        key=lambda row: (
            row["task_id"],
            CONDITION_ORDER.get(row["condition"], 99),
            row["condition"],
        ),
    )


def condition_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    conditions = sorted(
        {row["condition"] for row in rows},
        key=lambda condition: (CONDITION_ORDER.get(condition, 99), condition),
    )

    for condition in conditions:
        subset = [row for row in rows if row["condition"] == condition]
        n = len(subset)
        decision_correct = sum(bool_value(row["decision_correct"]) for row in subset)
        escalation_correct = sum(bool_value(row["escalation_correct"]) for row in subset)
        valid_chain = sum(bool_value(row["valid_chain"]) for row in subset)

        output.append(
            {
                "condition": condition,
                "n": n,
                "gold_decisions": counter_text(Counter(row["gold_decision"] for row in subset)),
                "decision_correct": decision_correct,
                "decision_correct_rate": rate(decision_correct, n),
                "escalation_correct": escalation_correct,
                "escalation_correct_rate": rate(escalation_correct, n),
                "audit_passed": counter_text(Counter(row["audit_passed"] for row in subset)),
                "valid_chain": valid_chain,
                "valid_chain_rate": rate(valid_chain, n),
            }
        )

    return output


def taxonomy_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = {
        "decision_error": [],
        "escalation_recovery_after_decision_error": [],
        "unrecovered_final_error": [],
        "audit_pass_on_incorrect_decision": [],
        "audit_block_on_incorrect_decision": [],
        "escalation_override": [],
        "correct_complete_chain": [],
    }

    for row in rows:
        decision_correct = bool_value(row["decision_correct"])
        escalation_correct = bool_value(row["escalation_correct"])
        audit_passed = bool_value(row["audit_passed"])
        overrode = bool_value(row["overrode"])

        if not decision_correct:
            groups["decision_error"].append(row)
        if not decision_correct and escalation_correct:
            groups["escalation_recovery_after_decision_error"].append(row)
        if not escalation_correct:
            groups["unrecovered_final_error"].append(row)
        if not decision_correct and audit_passed:
            groups["audit_pass_on_incorrect_decision"].append(row)
        if not decision_correct and not audit_passed:
            groups["audit_block_on_incorrect_decision"].append(row)
        if overrode:
            groups["escalation_override"].append(row)
        if decision_correct and escalation_correct and audit_passed:
            groups["correct_complete_chain"].append(row)

    output: list[dict[str, Any]] = []

    for name, subset in groups.items():
        output.append(
            {
                "failure_or_pattern": name,
                "n": len(subset),
                "rate": rate(len(subset), len(rows)),
                "conditions": counter_text(Counter(row["condition"] for row in subset)),
                "gold_decisions": counter_text(Counter(row["gold_decision"] for row in subset)),
                "task_ids": ", ".join(row["task_id"] for row in subset) if subset else "-",
            }
        )

    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")

    return lines


def write_report(
    report_md: Path,
    aggregate_json: Path,
    condition_csv: Path,
    taxonomy_csv: Path,
    chain_rows: list[dict[str, str]],
    condition_rows: list[dict[str, Any]],
    taxonomy_rows: list[dict[str, Any]],
) -> None:
    aggregate_data = json.loads(aggregate_json.read_text(encoding="utf-8"))
    parser_summary = aggregate_data.get("parser_summary", {})
    combined_summary = aggregate_data.get("combined_summary", aggregate_data.get("combined_chain_summary", {}))

    n = len(chain_rows)
    task_count = len({row["task_id"] for row in chain_rows})
    checkpoint_label = f"{task_count}-Task"
    checkpoint_phrase = f"{task_count}-task"
    decision_correct = sum(bool_value(row["decision_correct"]) for row in chain_rows)
    escalation_correct = sum(bool_value(row["escalation_correct"]) for row in chain_rows)
    valid_chain = sum(bool_value(row["valid_chain"]) for row in chain_rows)

    lines: list[str] = [
        f"# Pilot 03 Real GLM {checkpoint_label} Results",
        "",
        "## Purpose",
        "",
        f"This report documents the {checkpoint_phrase} controlled real GLM-5.2 checkpoint for Pilot 03.",
        "Use only conservative Level 1 wording: observed result under current Pilot 03 real LLM experimental conditions.",
        "",
        "## Scope",
        "",
        "- Provider: Z.ai",
        "- Model: GLM-5.2",
        "- Pipeline: decision -> audit -> escalation",
        "- Evidence conditions: original_evidence, missing_policy_rule, missing_one_required_unit",
        f"- Aggregate source: `{aggregate_json}`",
        f"- Completed chains: {n}",
        f"- Parsed responses: {parser_summary.get('n_parsed_responses', '-')}",
        f"- Stage counts: {parser_summary.get('stage_counts', '-')}",
        f"- Valid JSON counts: {parser_summary.get('valid_json_counts', '-')}",
        f"- Valid schema counts: {parser_summary.get('valid_schema_counts', '-')}",
        "",
        "## Overall Summary",
        "",
        f"- Decision correct: {decision_correct}/{n} ({rate(decision_correct, n)})",
        f"- Escalation correct: {escalation_correct}/{n} ({rate(escalation_correct, n)})",
        f"- Valid chain: {valid_chain}/{n} ({rate(valid_chain, n)})",
        "",
        "## Condition-Level Summary",
        "",
    ]

    lines.extend(
        markdown_table(
            condition_rows,
            [
                "condition",
                "n",
                "gold_decisions",
                "decision_correct_rate",
                "escalation_correct_rate",
                "audit_passed",
                "valid_chain_rate",
            ],
        )
    )

    lines.extend(["", "## Failure and Recovery Taxonomy", ""])
    lines.extend(
        markdown_table(
            taxonomy_rows,
            [
                "failure_or_pattern",
                "n",
                "rate",
                "conditions",
                "gold_decisions",
                "task_ids",
            ],
        )
    )

    lines.extend(["", "## Chain-Level Results", ""])
    lines.extend(
        markdown_table(
            chain_rows,
            [
                "task_id",
                "condition",
                "gold_decision",
                "decision",
                "decision_correct",
                "audit_passed",
                "audit_supported_decision",
                "escalation",
                "escalation_correct",
                "overrode",
                "valid_chain",
            ],
        )
    )

    lines.extend(
        [
            "",
            "## Generated Tables",
            "",
            f"- Condition CSV: `{condition_csv}`",
            f"- Failure taxonomy CSV: `{taxonomy_csv}`",
            "",
            "## Safe Wording",
            "",
            "> observed result under current Pilot 03 real LLM experimental conditions",
            "",
            "Do not claim general GLM reliability, real-world deployment validity, or complete evidence from this checkpoint alone.",
            "",
            "## Raw Combined Summary",
            "",
            "```json",
            json.dumps(combined_summary, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )

    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate-json", required=True)
    parser.add_argument("--report-md", required=True)
    parser.add_argument("--condition-csv", required=True)
    parser.add_argument("--taxonomy-csv", required=True)
    parser.add_argument("--run-dirs", nargs="+", required=True)
    args = parser.parse_args()

    aggregate_json = Path(args.aggregate_json)
    report_md = Path(args.report_md)
    condition_csv = Path(args.condition_csv)
    taxonomy_csv = Path(args.taxonomy_csv)
    run_dirs = [Path(path) for path in args.run_dirs]

    stdout_text = run_aggregator(run_dirs, aggregate_json)
    chain_rows = parse_chain_table(stdout_text)
    condition_rows = condition_summary(chain_rows)
    taxonomy_rows = taxonomy_summary(chain_rows)

    write_csv(condition_csv, condition_rows)
    write_csv(taxonomy_csv, taxonomy_rows)
    write_report(
        report_md=report_md,
        aggregate_json=aggregate_json,
        condition_csv=condition_csv,
        taxonomy_csv=taxonomy_csv,
        chain_rows=chain_rows,
        condition_rows=condition_rows,
        taxonomy_rows=taxonomy_rows,
    )

    print("Pilot 03 report generated")
    print("=========================")
    print(f"aggregate_json: {aggregate_json}")
    print(f"report_md: {report_md}")
    print(f"condition_csv: {condition_csv}")
    print(f"taxonomy_csv: {taxonomy_csv}")
    print(f"chain_rows: {len(chain_rows)}")
    print("safe_wording: observed result under current Pilot 03 real LLM experimental conditions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
