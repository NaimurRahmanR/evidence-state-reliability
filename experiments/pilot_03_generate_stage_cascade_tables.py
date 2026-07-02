from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_GLM_AGGREGATE_JSON = Path(
    "results/pilot_03_real_llm_analysis/pilot_03_real_glm_t0020_aggregate.json"
)
DEFAULT_CLAUDE_CHAIN_CSV = Path(
    "reports/pilot_03_claude_comparison_subset/claude_subset_chain_summary.csv"
)
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_stage_cascade")

SAFE_NOTE = (
    "Stage-cascade tables are descriptive outputs from the controlled Pilot 03 setup. "
    "They use sanitized chain-level fields only and should not be interpreted as broad "
    "provider rankings, deployment evidence, or general model reliability claims."
)

CANONICAL_COLUMNS = [
    "scope",
    "provider",
    "model_name",
    "task_id",
    "task_type",
    "condition",
    "gold_decision",
    "decision_final_decision",
    "audit_passed",
    "escalation_final_decision",
    "decision_correct",
    "escalation_correct",
    "stages_present",
    "valid_json_chain",
    "valid_schema_chain",
    "source_kind",
    "safe_note",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _bool_text(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"

    if value is None:
        return ""

    value_text = str(value).strip()
    if value_text.lower() in {"true", "1", "yes"}:
        return "True"
    if value_text.lower() in {"false", "0", "no"}:
        return "False"

    return value_text


def _is_true(value: Any) -> bool:
    return _bool_text(value) == "True"


def _rate_text(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return ""
    return f"{numerator / denominator:.6f}"


def _safe_task_type(task_id: str) -> str:
    # Pilot 03 T0001-T0020 tasks are synthetic administrative approval tasks.
    # This metadata is repeated here for a sanitized chain-level export because the
    # ignored GLM aggregate does not carry task_type in chain_rows.
    if task_id.startswith("P03-T"):
        return "synthetic_administrative_approval"
    return ""


def _valid_schema_chain_from_glm_row(row: dict[str, Any]) -> str:
    schema_flags = [
        row.get("decision_valid_schema"),
        row.get("audit_valid_schema"),
        row.get("escalation_valid_schema"),
    ]

    if any(flag is None for flag in schema_flags):
        return ""

    return "True" if all(_is_true(flag) for flag in schema_flags) else "False"


def _load_glm_chain_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing GLM aggregate JSON: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("chain_rows", [])

    if not isinstance(rows, list):
        raise ValueError("Expected GLM aggregate field 'chain_rows' to be a list.")

    raw_like_columns: list[str] = []
    if rows:
        for key in rows[0].keys():
            key_lower = str(key).lower()
            if "raw" in key_lower or "prompt" in key_lower or "response" in key_lower:
                raw_like_columns.append(key)

    if raw_like_columns:
        raise ValueError(
            "Refusing to export GLM chain rows because raw/prompt/response-like columns "
            f"were found: {raw_like_columns}"
        )

    normalized_rows: list[dict[str, Any]] = []

    for row in rows:
        task_id = str(row.get("task_id", ""))

        normalized_rows.append(
            {
                "scope": "GLM 20-task checkpoint",
                "provider": "zai",
                "model_name": "glm-5.2",
                "task_id": task_id,
                "task_type": _safe_task_type(task_id),
                "condition": row.get("condition", ""),
                "gold_decision": row.get("gold_decision", ""),
                "decision_final_decision": row.get("decision", ""),
                "audit_passed": _bool_text(row.get("audit_passed")),
                "escalation_final_decision": row.get("escalation", ""),
                "decision_correct": _bool_text(row.get("decision_correct")),
                "escalation_correct": _bool_text(row.get("escalation_correct")),
                "stages_present": _bool_text(row.get("valid_chain")),
                "valid_json_chain": "",
                "valid_schema_chain": _valid_schema_chain_from_glm_row(row),
                "source_kind": "sanitized_from_ignored_glm_aggregate",
                "safe_note": SAFE_NOTE,
            }
        )

    return sorted(normalized_rows, key=lambda item: (item["task_id"], item["condition"]))


def _load_claude_chain_rows(path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    normalized_rows: list[dict[str, Any]] = []

    for row in rows:
        normalized_rows.append(
            {
                "scope": "Claude 5-task comparison subset",
                "provider": row.get("provider", "anthropic"),
                "model_name": row.get("model_name", "claude-opus-4-8"),
                "task_id": row.get("task_id", ""),
                "task_type": row.get("task_type", ""),
                "condition": row.get("condition", ""),
                "gold_decision": row.get("gold_decision", ""),
                "decision_final_decision": row.get("decision_final_decision", ""),
                "audit_passed": _bool_text(row.get("audit_passed")),
                "escalation_final_decision": row.get("escalation_final_decision", ""),
                "decision_correct": _bool_text(row.get("decision_correct")),
                "escalation_correct": _bool_text(row.get("escalation_correct")),
                "stages_present": _bool_text(row.get("stages_present")),
                "valid_json_chain": _bool_text(row.get("valid_json_chain")),
                "valid_schema_chain": _bool_text(row.get("valid_schema_chain")),
                "source_kind": "committed_claude_chain_summary",
                "safe_note": SAFE_NOTE,
            }
        )

    return sorted(normalized_rows, key=lambda item: (item["task_id"], item["condition"]))


def _cascade_pattern(row: dict[str, Any]) -> str:
    return (
        f"decision_correct={row['decision_correct']}; "
        f"audit_passed={row['audit_passed']}; "
        f"escalation_correct={row['escalation_correct']}"
    )


def _cascade_short_code(row: dict[str, Any]) -> str:
    decision = "D1" if _is_true(row["decision_correct"]) else "D0"
    audit = "A1" if _is_true(row["audit_passed"]) else "A0"
    escalation = "E1" if _is_true(row["escalation_correct"]) else "E0"
    return f"{decision}_{audit}_{escalation}"


def make_cascade_pattern_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, str], int] = Counter()

    denominators: Counter[tuple[str, str, str, str]] = Counter()

    for row in rows:
        denominator_key = (
            row["scope"],
            row["provider"],
            row["model_name"],
            row["condition"],
        )
        denominators[denominator_key] += 1

        pattern_key = (
            row["scope"],
            row["provider"],
            row["model_name"],
            row["condition"],
            _cascade_short_code(row),
            _cascade_pattern(row),
        )
        grouped[pattern_key] += 1

    output_rows: list[dict[str, Any]] = []

    for key, count in sorted(grouped.items()):
        scope, provider, model_name, condition, pattern_code, pattern_label = key
        denominator_key = (scope, provider, model_name, condition)
        n_condition = denominators[denominator_key]

        output_rows.append(
            {
                "scope": scope,
                "provider": provider,
                "model_name": model_name,
                "condition": condition,
                "cascade_pattern_code": pattern_code,
                "cascade_pattern_label": pattern_label,
                "n": count,
                "condition_n": n_condition,
                "condition_rate": _rate_text(count, n_condition),
                "safe_note": SAFE_NOTE,
            }
        )

    return output_rows


def make_stage_transition_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        key = (
            row["scope"],
            row["provider"],
            row["model_name"],
            row["condition"],
        )
        grouped[key].append(row)

    output_rows: list[dict[str, Any]] = []

    for key, group_rows in sorted(grouped.items()):
        scope, provider, model_name, condition = key
        n = len(group_rows)

        decision_correct_count = sum(_is_true(row["decision_correct"]) for row in group_rows)
        audit_passed_count = sum(_is_true(row["audit_passed"]) for row in group_rows)
        escalation_correct_count = sum(_is_true(row["escalation_correct"]) for row in group_rows)

        decision_wrong_count = n - decision_correct_count
        audit_passed_when_decision_wrong = sum(
            (not _is_true(row["decision_correct"])) and _is_true(row["audit_passed"])
            for row in group_rows
        )
        audit_failed_when_decision_correct = sum(
            _is_true(row["decision_correct"]) and (not _is_true(row["audit_passed"]))
            for row in group_rows
        )
        escalation_correct_when_decision_wrong = sum(
            (not _is_true(row["decision_correct"])) and _is_true(row["escalation_correct"])
            for row in group_rows
        )
        escalation_wrong_after_audit_passed = sum(
            _is_true(row["audit_passed"]) and (not _is_true(row["escalation_correct"]))
            for row in group_rows
        )

        output_rows.append(
            {
                "scope": scope,
                "provider": provider,
                "model_name": model_name,
                "condition": condition,
                "n": n,
                "decision_correct_count": decision_correct_count,
                "decision_correct_rate": _rate_text(decision_correct_count, n),
                "audit_passed_count": audit_passed_count,
                "audit_passed_rate": _rate_text(audit_passed_count, n),
                "escalation_correct_count": escalation_correct_count,
                "escalation_correct_rate": _rate_text(escalation_correct_count, n),
                "decision_wrong_count": decision_wrong_count,
                "audit_passed_when_decision_wrong_count": audit_passed_when_decision_wrong,
                "audit_passed_when_decision_wrong_rate_among_wrong_decisions": _rate_text(
                    audit_passed_when_decision_wrong,
                    decision_wrong_count,
                ),
                "audit_failed_when_decision_correct_count": audit_failed_when_decision_correct,
                "audit_failed_when_decision_correct_rate_among_correct_decisions": _rate_text(
                    audit_failed_when_decision_correct,
                    decision_correct_count,
                ),
                "escalation_correct_when_decision_wrong_count": escalation_correct_when_decision_wrong,
                "escalation_correct_when_decision_wrong_rate_among_wrong_decisions": _rate_text(
                    escalation_correct_when_decision_wrong,
                    decision_wrong_count,
                ),
                "escalation_wrong_after_audit_passed_count": escalation_wrong_after_audit_passed,
                "escalation_wrong_after_audit_passed_rate_among_audit_passed": _rate_text(
                    escalation_wrong_after_audit_passed,
                    audit_passed_count,
                ),
                "safe_note": SAFE_NOTE,
            }
        )

    return output_rows


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")

    return lines


def write_report(
    output_path: Path,
    *,
    cascade_pattern_rows: list[dict[str, Any]],
    stage_transition_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    lines: list[str] = [
        "# Pilot 03 stage-cascade tables",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        "The GLM chain-level table is a sanitized export from an ignored local aggregate JSON.",
        "The Claude chain-level table is read from the committed comparison-subset CSV.",
        "No raw prompts, raw responses, API keys, or raw result folders are committed by this script.",
        "",
        "## Cascade pattern summary",
        "",
    ]

    lines.extend(
        _markdown_table(
            cascade_pattern_rows,
            [
                "scope",
                "provider",
                "model_name",
                "condition",
                "cascade_pattern_code",
                "cascade_pattern_label",
                "n",
                "condition_n",
                "condition_rate",
            ],
        )
    )

    lines.extend(["", "## Stage transition summary", ""])

    lines.extend(
        _markdown_table(
            stage_transition_rows,
            [
                "scope",
                "provider",
                "model_name",
                "condition",
                "n",
                "decision_correct_rate",
                "audit_passed_rate",
                "escalation_correct_rate",
                "audit_passed_when_decision_wrong_count",
                "audit_passed_when_decision_wrong_rate_among_wrong_decisions",
                "audit_failed_when_decision_correct_count",
                "audit_failed_when_decision_correct_rate_among_correct_decisions",
                "escalation_correct_when_decision_wrong_count",
                "escalation_correct_when_decision_wrong_rate_among_wrong_decisions",
                "escalation_wrong_after_audit_passed_count",
                "escalation_wrong_after_audit_passed_rate_among_audit_passed",
            ],
        )
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

    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_stage_cascade_tables(
    *,
    glm_aggregate_json: Path,
    claude_chain_csv: Path,
    output_dir: Path,
) -> dict[str, Any]:
    glm_rows = _load_glm_chain_rows(glm_aggregate_json)
    claude_rows = _load_claude_chain_rows(claude_chain_csv)

    shared_task_ids = {f"P03-T{index:04d}" for index in range(1, 6)}
    glm_shared_rows = [
        {**row, "scope": "GLM shared 5-task subset"}
        for row in glm_rows
        if row["task_id"] in shared_task_ids
    ]

    shared_rows = sorted(
        glm_shared_rows + claude_rows,
        key=lambda item: (item["provider"], item["task_id"], item["condition"]),
    )

    cascade_input_rows = glm_rows + shared_rows

    cascade_pattern_rows = make_cascade_pattern_rows(cascade_input_rows)
    stage_transition_rows = make_stage_transition_rows(cascade_input_rows)

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "glm20_sanitized_chain_summary_csv": output_dir / "glm20_sanitized_chain_summary.csv",
        "shared5_sanitized_chain_summary_csv": output_dir / "shared5_sanitized_chain_summary.csv",
        "cascade_pattern_summary_csv": output_dir / "cascade_pattern_summary.csv",
        "stage_transition_summary_csv": output_dir / "stage_transition_summary.csv",
        "report_md": output_dir / "stage_cascade_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    _write_csv(outputs["glm20_sanitized_chain_summary_csv"], glm_rows, CANONICAL_COLUMNS)
    _write_csv(outputs["shared5_sanitized_chain_summary_csv"], shared_rows, CANONICAL_COLUMNS)
    _write_csv(outputs["cascade_pattern_summary_csv"], cascade_pattern_rows)
    _write_csv(outputs["stage_transition_summary_csv"], stage_transition_rows)

    existing_manifest_path = outputs["manifest_json"]
    if existing_manifest_path.exists():
        try:
            existing_manifest = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
            created_at_utc = str(
                existing_manifest.get("created_at_utc")
                or datetime.now(UTC).isoformat(timespec="seconds")
            )
        except Exception:
            created_at_utc = datetime.now(UTC).isoformat(timespec="seconds")
    else:
        created_at_utc = datetime.now(UTC).isoformat(timespec="seconds")

    manifest = {
        "created_at_utc": created_at_utc,
        "real_api_calls": 0,
        "safe_note": SAFE_NOTE,
        "source_files": {
            "glm_aggregate_json": str(glm_aggregate_json),
            "claude_chain_csv": str(claude_chain_csv),
        },
        "source_file_policy": {
            "glm_aggregate_json": "ignored local aggregate used only for sanitized chain-level export",
            "claude_chain_csv": "committed comparison-subset chain summary",
        },
        "outputs": {name: str(path) for name, path in outputs.items()},
        "row_counts": {
            "glm20_sanitized_chain_summary": len(glm_rows),
            "shared5_sanitized_chain_summary": len(shared_rows),
            "cascade_pattern_summary": len(cascade_pattern_rows),
            "stage_transition_summary": len(stage_transition_rows),
        },
        "raw_prompt_or_response_columns_exported": False,
        "shared_task_ids": sorted(shared_task_ids),
    }

    outputs["manifest_json"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    write_report(
        outputs["report_md"],
        cascade_pattern_rows=cascade_pattern_rows,
        stage_transition_rows=stage_transition_rows,
        manifest=manifest,
    )

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate sanitized Pilot 03 stage-cascade tables. "
            "This command makes no real API calls and exports no raw prompts or raw responses."
        )
    )
    parser.add_argument("--glm-aggregate-json", default=str(DEFAULT_GLM_AGGREGATE_JSON))
    parser.add_argument("--claude-chain-csv", default=str(DEFAULT_CLAUDE_CHAIN_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = generate_stage_cascade_tables(
        glm_aggregate_json=Path(args.glm_aggregate_json),
        claude_chain_csv=Path(args.claude_chain_csv),
        output_dir=Path(args.output_dir),
    )

    print("Pilot 03 stage-cascade tables generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"raw_prompt_or_response_columns_exported: {manifest['raw_prompt_or_response_columns_exported']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
