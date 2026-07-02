from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SAFE_WORDING = "observed comparison subset under current Pilot 03 real LLM experimental conditions"


def _load_json_text(value: str) -> dict[str, Any]:
    if value is None:
        return {}
    value = value.strip()
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {"raw_value": parsed}


def _read_call_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _make_chain_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)

    for row in records:
        metadata = _load_json_text(row.get("metadata", ""))
        parsed_response = _load_json_text(row.get("parsed_response", ""))

        condition = str(metadata.get("condition", ""))
        key = (str(row.get("task_id", "")), condition)

        grouped[key][str(row.get("stage", ""))] = {
            "row": row,
            "metadata": metadata,
            "parsed_response": parsed_response,
        }

    chain_rows: list[dict[str, Any]] = []

    for (task_id, condition), stage_map in sorted(grouped.items()):
        decision = stage_map.get("decision", {})
        audit = stage_map.get("audit", {})
        escalation = stage_map.get("escalation", {})

        decision_meta = decision.get("metadata", {})
        audit_meta = audit.get("metadata", {})
        escalation_meta = escalation.get("metadata", {})

        decision_parsed = decision.get("parsed_response", {})
        audit_parsed = audit.get("parsed_response", {})
        escalation_parsed = escalation.get("parsed_response", {})

        gold_decision = str(
            decision_meta.get("gold_decision")
            or audit_meta.get("gold_decision")
            or escalation_meta.get("gold_decision")
            or ""
        )

        decision_value = str(decision_parsed.get("final_decision", ""))
        escalation_value = str(escalation_parsed.get("final_decision", ""))
        audit_passed = audit_parsed.get("audit_passed", "")

        stages_present = all(stage in stage_map for stage in ["decision", "audit", "escalation"])
        valid_json = all(
            stage_map.get(stage, {}).get("metadata", {}).get("valid_json") is True
            for stage in ["decision", "audit", "escalation"]
        )
        valid_schema = all(
            stage_map.get(stage, {}).get("metadata", {}).get("valid_schema") is True
            for stage in ["decision", "audit", "escalation"]
        )

        chain_rows.append(
            {
                "task_id": task_id,
                "task_type": str(decision.get("row", {}).get("task_type", "")),
                "condition": condition,
                "provider": str(decision.get("row", {}).get("provider", "")),
                "model_name": str(decision.get("row", {}).get("model_name", "")),
                "gold_decision": gold_decision,
                "decision_final_decision": decision_value,
                "audit_passed": _bool_text(audit_passed),
                "escalation_final_decision": escalation_value,
                "decision_correct": _bool_text(decision_value == gold_decision),
                "escalation_correct": _bool_text(escalation_value == gold_decision),
                "stages_present": _bool_text(stages_present),
                "valid_json_chain": _bool_text(valid_json),
                "valid_schema_chain": _bool_text(valid_schema),
            }
        )

    return chain_rows


def _make_condition_rows(chain_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in chain_rows:
        by_condition[row["condition"]].append(row)

    condition_rows: list[dict[str, Any]] = []

    for condition, rows in sorted(by_condition.items()):
        n = len(rows)
        decision_correct = sum(1 for row in rows if row["decision_correct"] == "True")
        escalation_correct = sum(1 for row in rows if row["escalation_correct"] == "True")
        audit_passed_true = sum(1 for row in rows if row["audit_passed"] == "True")
        valid_schema_chain = sum(1 for row in rows if row["valid_schema_chain"] == "True")

        condition_rows.append(
            {
                "condition": condition,
                "n_chains": n,
                "decision_correct_count": decision_correct,
                "decision_correct_rate": _rate(decision_correct, n),
                "escalation_correct_count": escalation_correct,
                "escalation_correct_rate": _rate(escalation_correct, n),
                "audit_passed_true_count": audit_passed_true,
                "audit_passed_true_rate": _rate(audit_passed_true, n),
                "valid_schema_chain_count": valid_schema_chain,
                "valid_schema_chain_rate": _rate(valid_schema_chain, n),
            }
        )

    return condition_rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(
    *,
    path: Path,
    run_dir: Path,
    summary: dict[str, Any],
    chain_rows: list[dict[str, Any]],
    condition_rows: list[dict[str, Any]],
) -> None:
    provider_counts = Counter(row["provider"] for row in chain_rows)
    model_counts = Counter(row["model_name"] for row in chain_rows)

    n_chains = len(chain_rows)
    decision_correct = sum(1 for row in chain_rows if row["decision_correct"] == "True")
    escalation_correct = sum(1 for row in chain_rows if row["escalation_correct"] == "True")
    valid_schema_chain = sum(1 for row in chain_rows if row["valid_schema_chain"] == "True")

    real_chain_summary = (
        summary.get("extra_summary", {})
        .get("real_chain_summary", {})
    )

    lines = [
        "# Pilot 03 Claude comparison subset summary",
        "",
        f"Generated at UTC: {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        f"- Safe wording: {SAFE_WORDING}",
        f"- Source run directory: `{run_dir}`",
        f"- Provider counts: `{dict(provider_counts)}`",
        f"- Model counts: `{dict(model_counts)}`",
        f"- Selected task IDs: `{real_chain_summary.get('selected_task_ids', [])}`",
        f"- Conditions: `{real_chain_summary.get('conditions', [])}`",
        "",
        "## Validation",
        "",
        f"- Completed chains: {n_chains}",
        f"- Saved call records: {real_chain_summary.get('n_call_records_saved')}",
        f"- Expected call count: {real_chain_summary.get('expected_call_count')}",
        f"- Parser summary: `{real_chain_summary.get('parser_summary', {})}`",
        f"- Valid schema chains: {valid_schema_chain}/{n_chains} = {_rate(valid_schema_chain, n_chains)}",
        "",
        "## Aggregate observed results",
        "",
        f"- Decision correct: {decision_correct}/{n_chains} = {_rate(decision_correct, n_chains)}",
        f"- Escalation correct: {escalation_correct}/{n_chains} = {_rate(escalation_correct, n_chains)}",
        "",
        "## Condition-level observed results",
        "",
        "| condition | n | decision correct | decision rate | escalation correct | escalation rate | audit passed true | audit passed true rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in condition_rows:
        lines.append(
            "| {condition} | {n_chains} | {decision_correct_count} | {decision_correct_rate} | "
            "{escalation_correct_count} | {escalation_correct_rate} | "
            "{audit_passed_true_count} | {audit_passed_true_rate} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Conservative interpretation",
            "",
            "This is a small Claude comparison subset under the current Pilot 03 real LLM experimental setup. "
            "It should not be interpreted as a general claim about Claude, Anthropic models, or real-world deployment reliability. "
            "The subset is useful because it applies the same Pilot 03 tasks, evidence conditions, prompts, parser, and decision-audit-escalation chain structure used in the GLM track.",
            "",
            "The observed subset pattern is consistent with the evidence-state reliability thesis: when required evidence is removed, downstream decision and escalation behaviour can change even though the model remains capable of producing valid structured outputs. This wording is local to the current Pilot 03 setup only.",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create commit-safe Pilot 03 provider subset summaries from ignored raw run outputs."
    )
    parser.add_argument("--run-dir", required=True, help="Ignored raw real LLM run directory.")
    parser.add_argument(
        "--output-dir",
        default="reports/pilot_03_claude_comparison_subset",
        help="Commit-safe output directory for summaries.",
    )

    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    output_dir = Path(args.output_dir)

    call_records_csv = run_dir / "call_records.csv"
    summary_json = run_dir / "summary.json"

    if not call_records_csv.exists():
        raise FileNotFoundError(f"Missing call records CSV: {call_records_csv}")
    if not summary_json.exists():
        raise FileNotFoundError(f"Missing summary JSON: {summary_json}")

    records = _read_call_records(call_records_csv)
    summary = json.loads(summary_json.read_text(encoding="utf-8"))

    chain_rows = _make_chain_rows(records)
    condition_rows = _make_condition_rows(chain_rows)

    output_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(output_dir / "claude_subset_chain_summary.csv", chain_rows)
    _write_csv(output_dir / "claude_subset_condition_summary.csv", condition_rows)

    manifest = {
        "safe_wording": SAFE_WORDING,
        "source_run_dir": str(run_dir),
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "n_chain_rows": len(chain_rows),
        "n_condition_rows": len(condition_rows),
        "outputs": [
            "claude_subset_chain_summary.csv",
            "claude_subset_condition_summary.csv",
            "claude_subset_report.md",
            "manifest.json",
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    _write_report(
        path=output_dir / "claude_subset_report.md",
        run_dir=run_dir,
        summary=summary,
        chain_rows=chain_rows,
        condition_rows=condition_rows,
    )

    print("Pilot 03 Claude subset summary generated.")
    print(f"source_run_dir: {run_dir}")
    print(f"output_dir: {output_dir}")
    print(f"chain_rows: {len(chain_rows)}")
    print(f"condition_rows: {len(condition_rows)}")
    print(f"safe_wording: {SAFE_WORDING}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
