from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_GLM_CHAIN_CSV = Path("reports/pilot_03_stage_cascade/glm20_sanitized_chain_summary.csv")
DEFAULT_CLAUDE_CHAIN_CSV = Path("reports/pilot_03_anthropic_t0020_valid/anthropic_t0020_valid_chain_summary.csv")
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_glm_vs_claude_t0020_full")

CONDITIONS = [
    "original_evidence",
    "missing_policy_rule",
    "missing_one_required_unit",
]

METRICS = [
    "decision_correct",
    "escalation_correct",
    "audit_passed",
    "valid_json_chain",
    "valid_schema_chain",
]

SAFE_NOTE = (
    "Descriptive full 20-task GLM-5.2 and Anthropic/Claude comparison under the controlled Pilot 03 setup. "
    "This report uses committed sanitized chain-level outputs only and should not be interpreted as broad "
    "deployment evidence, broad cross-provider conclusions, or general reliability claims."
)

RISKY_WORDING = [
    "Q1",
    "journal-level",
    "groundbreaking",
    "proven",
    "universal",
    "provider ranking",
    "provider rankings",
    "general Claude reliability",
    "general GLM reliability",
    "real-world deployment proof",
]

BLOCKED_COLUMN_FRAGMENTS = [
    "raw",
    "prompt",
    "response",
    "api_key",
    "secret",
    "token",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
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


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def _existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            created = existing.get("created_at_utc")
            if created:
                return str(created)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _bool_str(value: bool) -> str:
    return "True" if value else "False"


def _valid_json_chain_from_sanitized_source(row: dict[str, str], *, provider: str) -> bool:
    value = str(row.get("valid_json_chain", "")).strip()

    if value:
        return _is_true(value)

    # The committed GLM stage-cascade chain summary has a blank valid_json_chain
    # field, while the committed GLM checkpoint validation is handled by the
    # existing Pilot 03 committed-output validator. For the comparison export,
    # blank GLM valid_json_chain values are treated as valid only when all
    # chain-level stage/schema fields in the sanitized source are valid.
    if provider == "zai":
        return (
            _is_true(row.get("stages_present", ""))
            and _is_true(row.get("valid_schema_chain", ""))
        )

    return False


def _rate(successes: int, n: int) -> float | None:
    if n == 0:
        return None
    return round(successes / n, 6)


def _blocked_columns(columns: list[str]) -> list[str]:
    hits = []

    for column in columns:
        lowered = column.lower()
        if any(fragment in lowered for fragment in BLOCKED_COLUMN_FRAGMENTS):
            hits.append(column)

    return hits


def _scan_risky_wording(paths: list[Path]) -> list[dict[str, Any]]:
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


def _canonicalize_chain_rows(
    rows: list[dict[str, str]],
    *,
    provider: str,
    model_name: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for row in rows:
        output.append(
            {
                "provider": provider,
                "model_name": model_name,
                "task_id": row["task_id"],
                "task_type": row.get("task_type", "synthetic_administrative_approval"),
                "condition": row["condition"],
                "gold_decision": row["gold_decision"],
                "decision_final_decision": row["decision_final_decision"],
                "audit_passed": _is_true(row["audit_passed"]),
                "escalation_final_decision": row["escalation_final_decision"],
                "decision_correct": _is_true(row["decision_correct"]),
                "escalation_correct": _is_true(row["escalation_correct"]),
                "stages_present": _is_true(row.get("stages_present", "True")),
                "valid_json_chain": _valid_json_chain_from_sanitized_source(row, provider=provider),
                "valid_schema_chain": _is_true(row.get("valid_schema_chain", "True")),
                "source_kind": row.get("source_kind", ""),
                "source_run_name": row.get("source_run_name", ""),
            }
        )

    return output


def _validate_source_rows(
    *,
    glm_rows: list[dict[str, Any]],
    claude_rows: list[dict[str, Any]],
    glm_source_columns: list[str],
    claude_source_columns: list[str],
) -> None:
    if len(glm_rows) != 60:
        raise SystemExit(f"Expected 60 GLM chain rows, found {len(glm_rows)}.")

    if len(claude_rows) != 60:
        raise SystemExit(f"Expected 60 Claude chain rows, found {len(claude_rows)}.")

    glm_keys = {(row["task_id"], row["condition"]) for row in glm_rows}
    claude_keys = {(row["task_id"], row["condition"]) for row in claude_rows}

    if len(glm_keys) != 60:
        raise SystemExit(f"Expected 60 unique GLM task-condition keys, found {len(glm_keys)}.")

    if len(claude_keys) != 60:
        raise SystemExit(f"Expected 60 unique Claude task-condition keys, found {len(claude_keys)}.")

    if glm_keys != claude_keys:
        missing_in_claude = sorted(glm_keys - claude_keys)
        missing_in_glm = sorted(claude_keys - glm_keys)
        raise SystemExit(
            "GLM and Claude task-condition keys do not match. "
            f"missing_in_claude={missing_in_claude}; missing_in_glm={missing_in_glm}"
        )

    for provider, rows in [("glm", glm_rows), ("claude", claude_rows)]:
        condition_counts = Counter(row["condition"] for row in rows)

        expected = {
            "original_evidence": 20,
            "missing_policy_rule": 20,
            "missing_one_required_unit": 20,
        }

        if dict(condition_counts) != expected:
            raise SystemExit(f"Unexpected {provider} condition counts: {dict(condition_counts)}")

        invalid_json = [row for row in rows if not row["valid_json_chain"]]
        invalid_schema = [row for row in rows if not row["valid_schema_chain"]]
        missing_stage = [row for row in rows if not row["stages_present"]]

        if invalid_json:
            raise SystemExit(f"{provider} has invalid JSON chain rows: {len(invalid_json)}")

        if invalid_schema:
            raise SystemExit(f"{provider} has invalid schema chain rows: {len(invalid_schema)}")

        if missing_stage:
            raise SystemExit(f"{provider} has missing-stage chain rows: {len(missing_stage)}")

    blocked_source_columns = _blocked_columns(glm_source_columns) + _blocked_columns(claude_source_columns)
    if blocked_source_columns:
        raise SystemExit(f"Blocked raw/prompt/response-like source columns found: {blocked_source_columns}")


def _paired_chain_rows(
    *,
    glm_rows: list[dict[str, Any]],
    claude_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    glm_index = {(row["task_id"], row["condition"]): row for row in glm_rows}
    claude_index = {(row["task_id"], row["condition"]): row for row in claude_rows}

    output: list[dict[str, Any]] = []

    for key in sorted(glm_index.keys()):
        glm = glm_index[key]
        claude = claude_index[key]

        task_id, condition = key

        if glm["gold_decision"] != claude["gold_decision"]:
            raise SystemExit(f"Gold decision mismatch for {task_id}::{condition}")

        row: dict[str, Any] = {
            "task_id": task_id,
            "task_type": glm["task_type"],
            "condition": condition,
            "gold_decision": glm["gold_decision"],
            "glm_model_name": glm["model_name"],
            "claude_model_name": claude["model_name"],
            "glm_decision_final_decision": glm["decision_final_decision"],
            "claude_decision_final_decision": claude["decision_final_decision"],
            "glm_escalation_final_decision": glm["escalation_final_decision"],
            "claude_escalation_final_decision": claude["escalation_final_decision"],
            "glm_decision_correct": _bool_str(glm["decision_correct"]),
            "claude_decision_correct": _bool_str(claude["decision_correct"]),
            "glm_escalation_correct": _bool_str(glm["escalation_correct"]),
            "claude_escalation_correct": _bool_str(claude["escalation_correct"]),
            "glm_audit_passed": _bool_str(glm["audit_passed"]),
            "claude_audit_passed": _bool_str(claude["audit_passed"]),
            "glm_valid_json_chain": _bool_str(glm["valid_json_chain"]),
            "claude_valid_json_chain": _bool_str(claude["valid_json_chain"]),
            "glm_valid_schema_chain": _bool_str(glm["valid_schema_chain"]),
            "claude_valid_schema_chain": _bool_str(claude["valid_schema_chain"]),
            "decision_correct_agreement": _bool_str(glm["decision_correct"] == claude["decision_correct"]),
            "escalation_correct_agreement": _bool_str(glm["escalation_correct"] == claude["escalation_correct"]),
            "audit_passed_agreement": _bool_str(glm["audit_passed"] == claude["audit_passed"]),
            "glm_decision_only_correct": _bool_str(glm["decision_correct"] and not claude["decision_correct"]),
            "claude_decision_only_correct": _bool_str(claude["decision_correct"] and not glm["decision_correct"]),
            "both_decision_correct": _bool_str(glm["decision_correct"] and claude["decision_correct"]),
            "both_decision_wrong": _bool_str((not glm["decision_correct"]) and (not claude["decision_correct"])),
            "glm_escalation_only_correct": _bool_str(glm["escalation_correct"] and not claude["escalation_correct"]),
            "claude_escalation_only_correct": _bool_str(claude["escalation_correct"] and not glm["escalation_correct"]),
            "both_escalation_correct": _bool_str(glm["escalation_correct"] and claude["escalation_correct"]),
            "both_escalation_wrong": _bool_str((not glm["escalation_correct"]) and (not claude["escalation_correct"])),
            "safe_note": SAFE_NOTE,
        }

        output.append(row)

    return output


def _model_condition_summary_rows(
    *,
    glm_rows: list[dict[str, Any]],
    claude_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for provider, model_name, rows in [
        ("zai", "glm-5.2", glm_rows),
        ("anthropic", "claude-opus-4-8", claude_rows),
    ]:
        for condition in CONDITIONS:
            condition_rows = [row for row in rows if row["condition"] == condition]
            n = len(condition_rows)

            decision_correct_count = sum(row["decision_correct"] for row in condition_rows)
            escalation_correct_count = sum(row["escalation_correct"] for row in condition_rows)
            audit_passed_count = sum(row["audit_passed"] for row in condition_rows)
            valid_json_count = sum(row["valid_json_chain"] for row in condition_rows)
            valid_schema_count = sum(row["valid_schema_chain"] for row in condition_rows)

            output.append(
                {
                    "provider": provider,
                    "model_name": model_name,
                    "condition": condition,
                    "n_chains": n,
                    "decision_correct_count": decision_correct_count,
                    "decision_correct_rate": _rate(decision_correct_count, n),
                    "escalation_correct_count": escalation_correct_count,
                    "escalation_correct_rate": _rate(escalation_correct_count, n),
                    "audit_passed_true_count": audit_passed_count,
                    "audit_passed_true_rate": _rate(audit_passed_count, n),
                    "valid_json_chain_count": valid_json_count,
                    "valid_json_chain_rate": _rate(valid_json_count, n),
                    "valid_schema_chain_count": valid_schema_count,
                    "valid_schema_chain_rate": _rate(valid_schema_count, n),
                    "safe_note": SAFE_NOTE,
                }
            )

    return output


def _condition_delta_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (row["model_name"], row["condition"]): row
        for row in summary_rows
    }

    output: list[dict[str, Any]] = []

    for condition in CONDITIONS:
        glm = by_key[("glm-5.2", condition)]
        claude = by_key[("claude-opus-4-8", condition)]

        for metric in [
            "decision_correct_rate",
            "escalation_correct_rate",
            "audit_passed_true_rate",
            "valid_json_chain_rate",
            "valid_schema_chain_rate",
        ]:
            glm_value = float(glm[metric])
            claude_value = float(claude[metric])

            output.append(
                {
                    "condition": condition,
                    "metric": metric,
                    "glm_5_2_value": glm_value,
                    "claude_opus_4_8_value": claude_value,
                    "claude_minus_glm": round(claude_value - glm_value, 6),
                    "absolute_difference": round(abs(claude_value - glm_value), 6),
                    "comparison_scope": "paired_20_task_same_condition_descriptive_difference",
                    "safe_note": SAFE_NOTE,
                }
            )

    return output


def _paired_agreement_rows(paired_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for condition in CONDITIONS:
        condition_rows = [row for row in paired_rows if row["condition"] == condition]
        n = len(condition_rows)

        metric_map = {
            "decision_correct": {
                "agreement": "decision_correct_agreement",
                "glm_only": "glm_decision_only_correct",
                "claude_only": "claude_decision_only_correct",
                "both_correct": "both_decision_correct",
                "both_wrong": "both_decision_wrong",
            },
            "escalation_correct": {
                "agreement": "escalation_correct_agreement",
                "glm_only": "glm_escalation_only_correct",
                "claude_only": "claude_escalation_only_correct",
                "both_correct": "both_escalation_correct",
                "both_wrong": "both_escalation_wrong",
            },
            "audit_passed": {
                "agreement": "audit_passed_agreement",
            },
        }

        for metric, columns in metric_map.items():
            row: dict[str, Any] = {
                "condition": condition,
                "metric": metric,
                "n_pairs": n,
                "agreement_count": sum(_is_true(item[columns["agreement"]]) for item in condition_rows),
                "agreement_rate": _rate(sum(_is_true(item[columns["agreement"]]) for item in condition_rows), n),
                "safe_note": SAFE_NOTE,
            }

            if "glm_only" in columns:
                row["glm_only_correct_count"] = sum(_is_true(item[columns["glm_only"]]) for item in condition_rows)
                row["glm_only_correct_rate"] = _rate(row["glm_only_correct_count"], n)
                row["claude_only_correct_count"] = sum(_is_true(item[columns["claude_only"]]) for item in condition_rows)
                row["claude_only_correct_rate"] = _rate(row["claude_only_correct_count"], n)
                row["both_correct_count"] = sum(_is_true(item[columns["both_correct"]]) for item in condition_rows)
                row["both_correct_rate"] = _rate(row["both_correct_count"], n)
                row["both_wrong_count"] = sum(_is_true(item[columns["both_wrong"]]) for item in condition_rows)
                row["both_wrong_rate"] = _rate(row["both_wrong_count"], n)
            else:
                row["glm_only_correct_count"] = "N/A"
                row["glm_only_correct_rate"] = "N/A"
                row["claude_only_correct_count"] = "N/A"
                row["claude_only_correct_rate"] = "N/A"
                row["both_correct_count"] = "N/A"
                row["both_correct_rate"] = "N/A"
                row["both_wrong_count"] = "N/A"
                row["both_wrong_rate"] = "N/A"

            output.append(row)

    return output


def _failure_pattern_rows(
    *,
    glm_rows: list[dict[str, Any]],
    claude_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for provider, model_name, rows in [
        ("zai", "glm-5.2", glm_rows),
        ("anthropic", "claude-opus-4-8", claude_rows),
    ]:
        grouped: dict[tuple[str, str], list[str]] = defaultdict(list)

        for row in rows:
            pattern = (
                f"decision_correct={_bool_str(row['decision_correct'])}; "
                f"audit_passed={_bool_str(row['audit_passed'])}; "
                f"escalation_correct={_bool_str(row['escalation_correct'])}"
            )
            grouped[(row["condition"], pattern)].append(row["task_id"])

        for (condition, pattern), task_ids in sorted(grouped.items()):
            condition_n = sum(1 for row in rows if row["condition"] == condition)

            output.append(
                {
                    "provider": provider,
                    "model_name": model_name,
                    "condition": condition,
                    "pattern": pattern,
                    "n": len(task_ids),
                    "condition_n": condition_n,
                    "condition_rate": _rate(len(task_ids), condition_n),
                    "task_ids": ",".join(sorted(task_ids)),
                    "safe_note": SAFE_NOTE,
                }
            )

    return output


def _count_rate_display(row: dict[str, Any], count_key: str, rate_key: str) -> str:
    count = row.get(count_key, "")
    rate = row.get(rate_key, "")

    if count in {"", "N/A", None} or rate in {"", "N/A", None}:
        return "N/A"

    return f"{count} ({rate})"


def _write_report(
    path: Path,
    *,
    manifest: dict[str, Any],
    condition_summary_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    paired_agreement_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Pilot 03 full GLM-5.2 vs Anthropic/Claude 20-task comparison",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        "This report compares committed sanitized chain-level outputs only. "
        "It does not inspect raw prompts, raw responses, API keys, or ignored local aggregate files.",
        "",
        "## Model-condition summary",
        "",
        "| Model | Condition | n | Decision correct | Escalation correct | Audit passed | Valid JSON chains | Valid schema chains |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in condition_summary_rows:
        lines.append(
            f"| {row['model_name']} | {row['condition']} | {row['n_chains']} | "
            f"{row['decision_correct_count']} ({row['decision_correct_rate']}) | "
            f"{row['escalation_correct_count']} ({row['escalation_correct_rate']}) | "
            f"{row['audit_passed_true_count']} ({row['audit_passed_true_rate']}) | "
            f"{row['valid_json_chain_count']} ({row['valid_json_chain_rate']}) | "
            f"{row['valid_schema_chain_count']} ({row['valid_schema_chain_rate']}) |"
        )

    lines.extend(
        [
            "",
            "## Descriptive rate differences",
            "",
            "Positive values mean the Anthropic/Claude rate is higher than the GLM-5.2 rate under the same condition.",
            "",
            "| Condition | Metric | GLM-5.2 | Claude Opus 4.8 | Claude minus GLM |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )

    for row in delta_rows:
        lines.append(
            f"| {row['condition']} | {row['metric']} | {row['glm_5_2_value']} | "
            f"{row['claude_opus_4_8_value']} | {row['claude_minus_glm']} |"
        )

    lines.extend(
        [
            "",
            "## Paired agreement summary",
            "",
            "| Condition | Metric | n pairs | Agreement | GLM only correct | Claude only correct | Both correct | Both wrong |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for row in paired_agreement_rows:
        lines.append(
            f"| {row['condition']} | {row['metric']} | {row['n_pairs']} | "
            f"{row['agreement_count']} ({row['agreement_rate']}) | "
            f"{_count_rate_display(row, 'glm_only_correct_count', 'glm_only_correct_rate')} | "
            f"{_count_rate_display(row, 'claude_only_correct_count', 'claude_only_correct_rate')} | "
            f"{_count_rate_display(row, 'both_correct_count', 'both_correct_rate')} | "
            f"{_count_rate_display(row, 'both_wrong_count', 'both_wrong_rate')} |"
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


def generate_comparison(
    *,
    glm_chain_csv: Path,
    claude_chain_csv: Path,
    output_dir: Path,
) -> dict[str, Any]:
    glm_source_rows = _read_csv(glm_chain_csv)
    claude_source_rows = _read_csv(claude_chain_csv)

    glm_source_columns = list(glm_source_rows[0].keys()) if glm_source_rows else []
    claude_source_columns = list(claude_source_rows[0].keys()) if claude_source_rows else []

    glm_rows = _canonicalize_chain_rows(
        glm_source_rows,
        provider="zai",
        model_name="glm-5.2",
    )
    claude_rows = _canonicalize_chain_rows(
        claude_source_rows,
        provider="anthropic",
        model_name="claude-opus-4-8",
    )

    _validate_source_rows(
        glm_rows=glm_rows,
        claude_rows=claude_rows,
        glm_source_columns=glm_source_columns,
        claude_source_columns=claude_source_columns,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "paired_chain_comparison_csv": output_dir / "paired_chain_comparison.csv",
        "model_condition_summary_csv": output_dir / "model_condition_summary.csv",
        "condition_delta_summary_csv": output_dir / "condition_delta_summary.csv",
        "paired_agreement_summary_csv": output_dir / "paired_agreement_summary.csv",
        "failure_pattern_comparison_csv": output_dir / "failure_pattern_comparison.csv",
        "report_md": output_dir / "glm_vs_claude_t0020_full_comparison_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    paired_rows = _paired_chain_rows(glm_rows=glm_rows, claude_rows=claude_rows)
    condition_summary_rows = _model_condition_summary_rows(glm_rows=glm_rows, claude_rows=claude_rows)
    delta_rows = _condition_delta_rows(condition_summary_rows)
    paired_agreement_rows = _paired_agreement_rows(paired_rows)
    failure_rows = _failure_pattern_rows(glm_rows=glm_rows, claude_rows=claude_rows)

    export_column_sets = [
        list(paired_rows[0].keys()) if paired_rows else [],
        list(condition_summary_rows[0].keys()) if condition_summary_rows else [],
        list(delta_rows[0].keys()) if delta_rows else [],
        list(paired_agreement_rows[0].keys()) if paired_agreement_rows else [],
        list(failure_rows[0].keys()) if failure_rows else [],
    ]

    blocked_export_columns = []
    for columns in export_column_sets:
        blocked_export_columns.extend(_blocked_columns(columns))

    if blocked_export_columns:
        raise SystemExit(f"Blocked export columns found: {blocked_export_columns}")

    manifest = {
        "created_at_utc": _existing_created_at(outputs["manifest_json"]),
        "status": "PASS",
        "scope": "Pilot 03 full 20-task GLM-5.2 vs Anthropic/Claude comparison",
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "source_files": {
            "glm_chain_csv": str(glm_chain_csv),
            "claude_chain_csv": str(claude_chain_csv),
        },
        "source_policy": "committed sanitized chain-level CSVs only",
        "models": [
            {"provider": "zai", "model_name": "glm-5.2"},
            {"provider": "anthropic", "model_name": "claude-opus-4-8"},
        ],
        "row_counts": {
            "glm_chain_rows": len(glm_rows),
            "claude_chain_rows": len(claude_rows),
            "paired_chain_comparison": len(paired_rows),
            "model_condition_summary": len(condition_summary_rows),
            "condition_delta_summary": len(delta_rows),
            "paired_agreement_summary": len(paired_agreement_rows),
            "failure_pattern_comparison": len(failure_rows),
        },
        "validity": {
            "glm_valid_json_chain_count": sum(row["valid_json_chain"] for row in glm_rows),
            "glm_valid_schema_chain_count": sum(row["valid_schema_chain"] for row in glm_rows),
            "claude_valid_json_chain_count": sum(row["valid_json_chain"] for row in claude_rows),
            "claude_valid_schema_chain_count": sum(row["valid_schema_chain"] for row in claude_rows),
        },
        "safe_note": SAFE_NOTE,
        "outputs": {name: str(path) for name, path in outputs.items()},
    }

    _write_csv(outputs["paired_chain_comparison_csv"], paired_rows)
    _write_csv(outputs["model_condition_summary_csv"], condition_summary_rows)
    _write_csv(outputs["condition_delta_summary_csv"], delta_rows)
    _write_csv(outputs["paired_agreement_summary_csv"], paired_agreement_rows)
    _write_csv(outputs["failure_pattern_comparison_csv"], failure_rows)
    _write_json(outputs["manifest_json"], manifest)

    _write_report(
        outputs["report_md"],
        manifest=manifest,
        condition_summary_rows=condition_summary_rows,
        delta_rows=delta_rows,
        paired_agreement_rows=paired_agreement_rows,
    )

    risky_hits = _scan_risky_wording(
        [
            outputs["paired_chain_comparison_csv"],
            outputs["model_condition_summary_csv"],
            outputs["condition_delta_summary_csv"],
            outputs["paired_agreement_summary_csv"],
            outputs["failure_pattern_comparison_csv"],
            outputs["report_md"],
            outputs["manifest_json"],
        ]
    )

    if risky_hits:
        raise SystemExit(f"Risky wording hits found: {risky_hits}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a committed-safe full 20-task GLM-5.2 vs Anthropic/Claude Pilot 03 comparison. "
            "This command makes no real API calls."
        )
    )
    parser.add_argument("--glm-chain-csv", default=str(DEFAULT_GLM_CHAIN_CSV))
    parser.add_argument("--claude-chain-csv", default=str(DEFAULT_CLAUDE_CHAIN_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = generate_comparison(
        glm_chain_csv=Path(args.glm_chain_csv),
        claude_chain_csv=Path(args.claude_chain_csv),
        output_dir=Path(args.output_dir),
    )

    print("Pilot 03 full GLM-5.2 vs Anthropic/Claude comparison generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"validity: {manifest['validity']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
