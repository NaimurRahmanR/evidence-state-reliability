from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_AGGREGATE_JSON = Path("results/pilot_03_real_llm_analysis/pilot_03_anthropic_t0020_valid_aggregate.json")
DEFAULT_SELECTOR_MANIFEST = Path("reports/pilot_03_anthropic_validity_selector/manifest.json")
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_anthropic_t0020_valid")

PROVIDER = "anthropic"
MODEL_NAME = "claude-opus-4-8"
SCOPE = "Anthropic Claude 20-task validity-aware checkpoint"

EXPECTED_CONDITION_COUNTS = {
    "original_evidence": 20,
    "missing_policy_rule": 20,
    "missing_one_required_unit": 20,
}

SAFE_NOTE = (
    "Descriptive Anthropic/Claude 20-task outputs from the controlled Pilot 03 setup. "
    "These outputs use sanitized chain-level fields only and should not be interpreted as "
    "broad cross-provider conclusions, deployment evidence, or general reliability claims."
)

BLOCKED_COLUMN_FRAGMENTS = [
    "raw",
    "prompt",
    "response",
    "api_key",
    "secret",
    "token",
]

RISKY_WORDING = [
    "Q1",
    "journal-level",
    "groundbreaking",
    "proven",
    "universal",
    "provider ranking",
    "superior",
    "real-world deployment proof",
    "general Claude reliability",
    "general GLM reliability",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = _load_json(path)
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _rate(count: int, total: int) -> float | None:
    if total == 0:
        return None
    return round(count / total, 6)


def _blocked_columns(columns: list[str]) -> list[str]:
    hits = []

    for column in columns:
        lowered = column.lower()
        if any(fragment in lowered for fragment in BLOCKED_COLUMN_FRAGMENTS):
            hits.append(column)

    return hits


def _scan_text_for_risky_wording(paths: list[Path]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []

    for path in paths:
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8", errors="replace")

        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for pattern in RISKY_WORDING:
                if pattern.lower() in lowered:
                    hits.append(
                        {
                            "path": str(path),
                            "line_number": line_number,
                            "pattern": pattern,
                            "line": line.strip(),
                        }
                    )

    return hits


def _validate_inputs(aggregate: dict[str, Any], selector_manifest: dict[str, Any]) -> None:
    parser = aggregate.get("parser_summary", {})
    chain_rows = aggregate.get("chain_rows", [])

    if selector_manifest.get("status") != "PASS":
        raise SystemExit("Selector manifest is not PASS.")

    if selector_manifest.get("selected_unique_task_condition_keys") != 60:
        raise SystemExit("Selector did not select 60 unique task-condition keys.")

    if selector_manifest.get("real_api_calls") != 0:
        raise SystemExit("Selector manifest reported non-zero real API calls.")

    if len(chain_rows) != 60:
        raise SystemExit(f"Expected 60 chain rows, found {len(chain_rows)}.")

    if aggregate.get("n_raw_response_records") != 180:
        raise SystemExit(f"Expected 180 raw response records, found {aggregate.get('n_raw_response_records')}.")

    if parser.get("n_parsed_responses") != 180:
        raise SystemExit(f"Expected 180 parsed responses, found {parser.get('n_parsed_responses')}.")

    if parser.get("stage_counts") != {"decision": 60, "audit": 60, "escalation": 60}:
        raise SystemExit(f"Unexpected parser stage counts: {parser.get('stage_counts')}.")

    if parser.get("n_invalid_json") != 0:
        raise SystemExit("Invalid JSON found in validity-aware aggregate.")

    if parser.get("n_invalid_schema") != 0:
        raise SystemExit("Invalid schema found in validity-aware aggregate.")

    if parser.get("valid_json_counts") != {"True": 180}:
        raise SystemExit(f"Unexpected valid_json_counts: {parser.get('valid_json_counts')}.")

    if parser.get("valid_schema_counts") != {"True": 180}:
        raise SystemExit(f"Unexpected valid_schema_counts: {parser.get('valid_schema_counts')}.")

    condition_counts = Counter(str(row.get("condition")) for row in chain_rows)

    if dict(condition_counts) != EXPECTED_CONDITION_COUNTS:
        raise SystemExit(f"Unexpected condition counts: {dict(condition_counts)}.")

    source_keys = set()
    for row in chain_rows:
        source_keys.update(row.keys())

    blocked = _blocked_columns(sorted(source_keys))
    if blocked:
        raise SystemExit(f"Blocked raw/prompt/response-like chain columns found: {blocked}")


def _chain_summary_rows(chain_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row in sorted(chain_rows, key=lambda item: (str(item.get("task_id")), str(item.get("condition")))):
        decision_schema = _is_true(row.get("decision_valid_schema"))
        audit_schema = _is_true(row.get("audit_valid_schema"))
        escalation_schema = _is_true(row.get("escalation_valid_schema"))
        valid_schema_chain = decision_schema and audit_schema and escalation_schema and _is_true(row.get("valid_chain"))

        rows.append(
            {
                "scope": SCOPE,
                "provider": PROVIDER,
                "model_name": MODEL_NAME,
                "task_id": row.get("task_id"),
                "task_type": "synthetic_administrative_approval",
                "condition": row.get("condition"),
                "gold_decision": row.get("gold_decision"),
                "decision_final_decision": row.get("decision"),
                "audit_passed": row.get("audit_passed"),
                "audit_detected_issue": row.get("audit_detected_issue"),
                "audit_supported_decision": row.get("audit_supported_decision"),
                "escalation_final_decision": row.get("escalation"),
                "escalation_overrode_previous_stage": row.get("escalation_overrode_previous_stage"),
                "decision_correct": row.get("decision_correct"),
                "escalation_correct": row.get("escalation_correct"),
                "stages_present": True,
                "valid_json_chain": True,
                "valid_schema_chain": valid_schema_chain,
                "source_kind": "validity_aware_anthropic_aggregate",
                "source_run_name": row.get("source_run_name"),
                "safe_note": SAFE_NOTE,
            }
        )

    return rows


def _condition_summary_rows(chain_summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for condition in ["original_evidence", "missing_policy_rule", "missing_one_required_unit"]:
        condition_rows = [
            row for row in chain_summary_rows
            if str(row.get("condition")) == condition
        ]

        n = len(condition_rows)
        decision_correct_count = sum(_is_true(row["decision_correct"]) for row in condition_rows)
        escalation_correct_count = sum(_is_true(row["escalation_correct"]) for row in condition_rows)
        audit_passed_true_count = sum(_is_true(row["audit_passed"]) for row in condition_rows)
        valid_json_chain_count = sum(_is_true(row["valid_json_chain"]) for row in condition_rows)
        valid_schema_chain_count = sum(_is_true(row["valid_schema_chain"]) for row in condition_rows)

        rows.append(
            {
                "scope": SCOPE,
                "provider": PROVIDER,
                "model_name": MODEL_NAME,
                "condition": condition,
                "n_chains": n,
                "decision_correct_count": decision_correct_count,
                "decision_correct_rate": _rate(decision_correct_count, n),
                "escalation_correct_count": escalation_correct_count,
                "escalation_correct_rate": _rate(escalation_correct_count, n),
                "audit_passed_true_count": audit_passed_true_count,
                "audit_passed_true_rate": _rate(audit_passed_true_count, n),
                "valid_json_chain_count": valid_json_chain_count,
                "valid_json_chain_rate": _rate(valid_json_chain_count, n),
                "valid_schema_chain_count": valid_schema_chain_count,
                "valid_schema_chain_rate": _rate(valid_schema_chain_count, n),
                "safe_note": SAFE_NOTE,
            }
        )

    return rows


def _parser_summary_rows(aggregate: dict[str, Any]) -> list[dict[str, Any]]:
    parser = aggregate.get("parser_summary", {})

    rows = [
        {"metric": "n_source_runs", "value": aggregate.get("n_source_runs")},
        {"metric": "n_raw_response_records", "value": aggregate.get("n_raw_response_records")},
        {"metric": "parser_version", "value": parser.get("parser_version")},
        {"metric": "n_parsed_responses", "value": parser.get("n_parsed_responses")},
        {"metric": "stage_counts", "value": json.dumps(parser.get("stage_counts"), sort_keys=True)},
        {"metric": "valid_json_counts", "value": json.dumps(parser.get("valid_json_counts"), sort_keys=True)},
        {"metric": "valid_schema_counts", "value": json.dumps(parser.get("valid_schema_counts"), sort_keys=True)},
        {"metric": "n_invalid_json", "value": parser.get("n_invalid_json")},
        {"metric": "n_invalid_schema", "value": parser.get("n_invalid_schema")},
        {"metric": "error_counts", "value": json.dumps(parser.get("error_counts"), sort_keys=True)},
    ]

    for row in rows:
        row["safe_note"] = SAFE_NOTE

    return rows


def _failure_pattern_rows(chain_summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}

    for row in chain_summary_rows:
        pattern = (
            str(row["condition"]),
            f"decision_correct={_is_true(row['decision_correct'])}",
            f"audit_passed={_is_true(row['audit_passed'])}",
            f"escalation_correct={_is_true(row['escalation_correct'])}",
        )
        groups.setdefault(pattern, []).append(row)

    output: list[dict[str, Any]] = []

    for (condition, decision_label, audit_label, escalation_label), rows in sorted(groups.items()):
        condition_n = EXPECTED_CONDITION_COUNTS[condition]

        output.append(
            {
                "scope": SCOPE,
                "provider": PROVIDER,
                "model_name": MODEL_NAME,
                "condition": condition,
                "pattern": f"{decision_label}; {audit_label}; {escalation_label}",
                "n": len(rows),
                "condition_n": condition_n,
                "condition_rate": _rate(len(rows), condition_n),
                "task_ids": ",".join(sorted(str(row["task_id"]) for row in rows)),
                "safe_note": SAFE_NOTE,
            }
        )

    return output


def _write_report(
    path: Path,
    *,
    manifest: dict[str, Any],
    condition_rows: list[dict[str, Any]],
    parser_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Pilot 03 Anthropic/Claude 20-task validity-aware report",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        "This report is generated from the validity-aware local aggregate and the committed Anthropic selector output. "
        "The raw aggregate and raw response files remain outside git.",
        "",
        "## Parser summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]

    for row in parser_rows:
        lines.append(f"| {row['metric']} | {row['value']} |")

    lines.extend(
        [
            "",
            "## Condition summary",
            "",
            "| Condition | n | Decision correct | Escalation correct | Audit passed | Valid JSON chains | Valid schema chains |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for row in condition_rows:
        lines.append(
            f"| {row['condition']} | {row['n_chains']} | "
            f"{row['decision_correct_count']} ({row['decision_correct_rate']}) | "
            f"{row['escalation_correct_count']} ({row['escalation_correct_rate']}) | "
            f"{row['audit_passed_true_count']} ({row['audit_passed_true_rate']}) | "
            f"{row['valid_json_chain_count']} ({row['valid_json_chain_rate']}) | "
            f"{row['valid_schema_chain_count']} ({row['valid_schema_chain_rate']}) |"
        )

    lines.extend(
        [
            "",
            "## Failure-pattern summary",
            "",
            "| Condition | Pattern | n | Rate | Task IDs |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )

    for row in failure_rows:
        lines.append(
            f"| {row['condition']} | {row['pattern']} | {row['n']} | {row['condition_rate']} | {row['task_ids']} |"
        )

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


def generate_report(
    *,
    aggregate_json: Path,
    selector_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    aggregate = _load_json(aggregate_json)
    selector_manifest = _load_json(selector_manifest_path)

    _validate_inputs(aggregate, selector_manifest)

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "chain_summary_csv": output_dir / "anthropic_t0020_valid_chain_summary.csv",
        "condition_summary_csv": output_dir / "anthropic_t0020_valid_condition_summary.csv",
        "parser_summary_csv": output_dir / "anthropic_t0020_valid_parser_summary.csv",
        "failure_patterns_csv": output_dir / "anthropic_t0020_valid_failure_patterns.csv",
        "report_md": output_dir / "anthropic_t0020_valid_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    chain_rows = _chain_summary_rows(aggregate["chain_rows"])
    condition_rows = _condition_summary_rows(chain_rows)
    parser_rows = _parser_summary_rows(aggregate)
    failure_rows = _failure_pattern_rows(chain_rows)

    chain_blocked = _blocked_columns(list(chain_rows[0].keys()) if chain_rows else [])
    condition_blocked = _blocked_columns(list(condition_rows[0].keys()) if condition_rows else [])
    parser_blocked = _blocked_columns(list(parser_rows[0].keys()) if parser_rows else [])
    failure_blocked = _blocked_columns(list(failure_rows[0].keys()) if failure_rows else [])

    blocked_export_columns = chain_blocked + condition_blocked + parser_blocked + failure_blocked

    if blocked_export_columns:
        raise SystemExit(f"Blocked export columns found: {blocked_export_columns}")

    manifest = {
        "created_at_utc": _existing_created_at(outputs["manifest_json"]),
        "status": "PASS",
        "provider": PROVIDER,
        "model_name": MODEL_NAME,
        "scope": SCOPE,
        "real_api_calls": 0,
        "source_aggregate_json": str(aggregate_json),
        "source_aggregate_policy": "ignored local aggregate used only for sanitized export",
        "selector_manifest": str(selector_manifest_path),
        "safe_note": SAFE_NOTE,
        "row_counts": {
            "chain_summary": len(chain_rows),
            "condition_summary": len(condition_rows),
            "parser_summary": len(parser_rows),
            "failure_patterns": len(failure_rows),
        },
        "validity": {
            "n_source_runs": aggregate.get("n_source_runs"),
            "n_raw_response_records": aggregate.get("n_raw_response_records"),
            "n_chain_rows": len(chain_rows),
            "n_parsed_responses": aggregate.get("parser_summary", {}).get("n_parsed_responses"),
            "n_invalid_json": aggregate.get("parser_summary", {}).get("n_invalid_json"),
            "n_invalid_schema": aggregate.get("parser_summary", {}).get("n_invalid_schema"),
            "valid_json_counts": aggregate.get("parser_summary", {}).get("valid_json_counts"),
            "valid_schema_counts": aggregate.get("parser_summary", {}).get("valid_schema_counts"),
        },
        "raw_prompt_or_response_columns_exported": False,
        "outputs": {name: str(path) for name, path in outputs.items()},
    }

    _write_csv(outputs["chain_summary_csv"], chain_rows)
    _write_csv(outputs["condition_summary_csv"], condition_rows)
    _write_csv(outputs["parser_summary_csv"], parser_rows)
    _write_csv(outputs["failure_patterns_csv"], failure_rows)
    _write_json(outputs["manifest_json"], manifest)

    _write_report(
        outputs["report_md"],
        manifest=manifest,
        condition_rows=condition_rows,
        parser_rows=parser_rows,
        failure_rows=failure_rows,
    )

    risky_hits = _scan_text_for_risky_wording(
        [
            outputs["report_md"],
            outputs["manifest_json"],
            outputs["chain_summary_csv"],
            outputs["condition_summary_csv"],
            outputs["parser_summary_csv"],
            outputs["failure_patterns_csv"],
        ]
    )

    if risky_hits:
        raise SystemExit(f"Risky wording hits found: {risky_hits}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate committed-safe Anthropic/Claude 20-task Pilot 03 report outputs "
            "from the validity-aware local aggregate. This command makes no real API calls."
        )
    )
    parser.add_argument("--aggregate-json", default=str(DEFAULT_AGGREGATE_JSON))
    parser.add_argument("--selector-manifest", default=str(DEFAULT_SELECTOR_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = generate_report(
        aggregate_json=Path(args.aggregate_json),
        selector_manifest_path=Path(args.selector_manifest),
        output_dir=Path(args.output_dir),
    )

    print("Pilot 03 Anthropic/Claude T0020 validity-aware report generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"provider: {manifest['provider']}")
    print(f"model_name: {manifest['model_name']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"validity: {manifest['validity']}")
    print(f"raw_prompt_or_response_columns_exported: {manifest['raw_prompt_or_response_columns_exported']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
