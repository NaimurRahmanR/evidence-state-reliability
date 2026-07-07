from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_PAIRED_CHAIN_CSV = Path("reports/pilot_03_glm_vs_claude_t0020_full/paired_chain_comparison.csv")
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis")

CONDITIONS = [
    "original_evidence",
    "missing_policy_rule",
    "missing_one_required_unit",
]

SAFE_NOTE = (
    "Paired task-level analysis for the controlled Pilot 03 20-task GLM-5.2 and Anthropic/Claude comparison. "
    "This analysis uses committed sanitized paired-chain outputs only and should not be interpreted as broad "
    "deployment evidence or broad cross-provider conclusions."
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


def _validate_source_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != 60:
        raise SystemExit(f"Expected 60 paired chain rows, found {len(rows)}.")

    keys = {(row["task_id"], row["condition"]) for row in rows}

    if len(keys) != 60:
        raise SystemExit(f"Expected 60 unique task-condition keys, found {len(keys)}.")

    condition_counts = Counter(row["condition"] for row in rows)
    expected_counts = {
        "original_evidence": 20,
        "missing_policy_rule": 20,
        "missing_one_required_unit": 20,
    }

    if dict(condition_counts) != expected_counts:
        raise SystemExit(f"Unexpected condition counts: {dict(condition_counts)}")

    task_counts = Counter(row["task_id"] for row in rows)
    bad_task_counts = {
        task_id: count for task_id, count in task_counts.items()
        if count != 3
    }

    if bad_task_counts:
        raise SystemExit(f"Expected 3 conditions per task. Bad task counts: {bad_task_counts}")

    required_columns = {
        "task_id",
        "task_type",
        "condition",
        "gold_decision",
        "glm_decision_final_decision",
        "claude_decision_final_decision",
        "glm_escalation_final_decision",
        "claude_escalation_final_decision",
        "glm_decision_correct",
        "claude_decision_correct",
        "glm_escalation_correct",
        "claude_escalation_correct",
        "glm_audit_passed",
        "claude_audit_passed",
        "glm_valid_json_chain",
        "claude_valid_json_chain",
        "glm_valid_schema_chain",
        "claude_valid_schema_chain",
    }

    missing = sorted(required_columns - set(rows[0].keys()))
    if missing:
        raise SystemExit(f"Missing required paired comparison columns: {missing}")

    blocked_source_columns = _blocked_columns(list(rows[0].keys()))
    if blocked_source_columns:
        raise SystemExit(f"Blocked source columns found: {blocked_source_columns}")

    invalid_rows = [
        row for row in rows
        if not (
            _is_true(row["glm_valid_json_chain"])
            and _is_true(row["claude_valid_json_chain"])
            and _is_true(row["glm_valid_schema_chain"])
            and _is_true(row["claude_valid_schema_chain"])
        )
    ]

    if invalid_rows:
        raise SystemExit(f"Invalid paired rows found: {len(invalid_rows)}")


def _pair_outcome(glm_value: bool, claude_value: bool, *, positive_label: str = "correct") -> str:
    if glm_value and claude_value:
        return f"both_{positive_label}"
    if glm_value and not claude_value:
        return f"glm_only_{positive_label}"
    if claude_value and not glm_value:
        return f"claude_only_{positive_label}"
    return f"both_not_{positive_label}"


def _audit_pair_outcome(glm_passed: bool, claude_passed: bool) -> str:
    if glm_passed and claude_passed:
        return "both_audit_passed"
    if glm_passed and not claude_passed:
        return "glm_only_audit_passed"
    if claude_passed and not glm_passed:
        return "claude_only_audit_passed"
    return "both_audit_not_passed"


def _transition(decision_correct: bool, escalation_correct: bool) -> str:
    if decision_correct and escalation_correct:
        return "decision_correct_preserved"
    if not decision_correct and escalation_correct:
        return "decision_wrong_recovered_by_escalation"
    if not decision_correct and not escalation_correct:
        return "decision_wrong_not_recovered"
    return "decision_correct_lost_at_escalation"


def _task_condition_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for row in sorted(rows, key=lambda item: (item["task_id"], CONDITIONS.index(item["condition"]))):
        glm_decision_correct = _is_true(row["glm_decision_correct"])
        claude_decision_correct = _is_true(row["claude_decision_correct"])
        glm_escalation_correct = _is_true(row["glm_escalation_correct"])
        claude_escalation_correct = _is_true(row["claude_escalation_correct"])
        glm_audit_passed = _is_true(row["glm_audit_passed"])
        claude_audit_passed = _is_true(row["claude_audit_passed"])

        glm_transition = _transition(glm_decision_correct, glm_escalation_correct)
        claude_transition = _transition(claude_decision_correct, claude_escalation_correct)

        output.append(
            {
                "task_id": row["task_id"],
                "task_type": row["task_type"],
                "condition": row["condition"],
                "gold_decision": row["gold_decision"],
                "glm_decision_final_decision": row["glm_decision_final_decision"],
                "claude_decision_final_decision": row["claude_decision_final_decision"],
                "glm_escalation_final_decision": row["glm_escalation_final_decision"],
                "claude_escalation_final_decision": row["claude_escalation_final_decision"],
                "glm_decision_correct": _bool_str(glm_decision_correct),
                "claude_decision_correct": _bool_str(claude_decision_correct),
                "glm_escalation_correct": _bool_str(glm_escalation_correct),
                "claude_escalation_correct": _bool_str(claude_escalation_correct),
                "glm_audit_passed": _bool_str(glm_audit_passed),
                "claude_audit_passed": _bool_str(claude_audit_passed),
                "decision_pair_outcome": _pair_outcome(glm_decision_correct, claude_decision_correct),
                "escalation_pair_outcome": _pair_outcome(glm_escalation_correct, claude_escalation_correct),
                "audit_pair_outcome": _audit_pair_outcome(glm_audit_passed, claude_audit_passed),
                "glm_escalation_transition": glm_transition,
                "claude_escalation_transition": claude_transition,
                "same_escalation_transition": _bool_str(glm_transition == claude_transition),
                "decision_correct_disagreement": _bool_str(glm_decision_correct != claude_decision_correct),
                "escalation_correct_disagreement": _bool_str(glm_escalation_correct != claude_escalation_correct),
                "audit_passed_disagreement": _bool_str(glm_audit_passed != claude_audit_passed),
                "both_decision_wrong": _bool_str((not glm_decision_correct) and (not claude_decision_correct)),
                "both_escalation_wrong": _bool_str((not glm_escalation_correct) and (not claude_escalation_correct)),
                "either_model_recovered_at_escalation": _bool_str(
                    glm_transition == "decision_wrong_recovered_by_escalation"
                    or claude_transition == "decision_wrong_recovered_by_escalation"
                ),
                "either_model_lost_at_escalation": _bool_str(
                    glm_transition == "decision_correct_lost_at_escalation"
                    or claude_transition == "decision_correct_lost_at_escalation"
                ),
                "safe_note": SAFE_NOTE,
            }
        )

    return output


def _task_level_summary_rows(task_condition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in task_condition_rows:
        grouped[row["task_id"]].append(row)

    output: list[dict[str, Any]] = []

    for task_id in sorted(grouped):
        rows = sorted(grouped[task_id], key=lambda item: CONDITIONS.index(item["condition"]))
        n = len(rows)

        glm_decision_correct_count = sum(_is_true(row["glm_decision_correct"]) for row in rows)
        claude_decision_correct_count = sum(_is_true(row["claude_decision_correct"]) for row in rows)
        glm_escalation_correct_count = sum(_is_true(row["glm_escalation_correct"]) for row in rows)
        claude_escalation_correct_count = sum(_is_true(row["claude_escalation_correct"]) for row in rows)
        glm_audit_passed_count = sum(_is_true(row["glm_audit_passed"]) for row in rows)
        claude_audit_passed_count = sum(_is_true(row["claude_audit_passed"]) for row in rows)

        decision_disagreement_count = sum(_is_true(row["decision_correct_disagreement"]) for row in rows)
        escalation_disagreement_count = sum(_is_true(row["escalation_correct_disagreement"]) for row in rows)
        audit_disagreement_count = sum(_is_true(row["audit_passed_disagreement"]) for row in rows)

        glm_recovery_count = sum(
            row["glm_escalation_transition"] == "decision_wrong_recovered_by_escalation"
            for row in rows
        )
        claude_recovery_count = sum(
            row["claude_escalation_transition"] == "decision_wrong_recovered_by_escalation"
            for row in rows
        )

        both_decision_wrong_count = sum(_is_true(row["both_decision_wrong"]) for row in rows)
        both_escalation_wrong_count = sum(_is_true(row["both_escalation_wrong"]) for row in rows)

        if both_escalation_wrong_count:
            task_pattern = "shared_escalation_error_present"
        elif escalation_disagreement_count:
            task_pattern = "escalation_disagreement_present"
        elif both_decision_wrong_count:
            task_pattern = "shared_decision_error_recovered_or_contained"
        elif audit_disagreement_count:
            task_pattern = "audit_disagreement_only"
        else:
            task_pattern = "paired_outcomes_aligned"

        output.append(
            {
                "task_id": task_id,
                "task_type": rows[0]["task_type"],
                "n_conditions": n,
                "conditions": ",".join(row["condition"] for row in rows),
                "gold_decisions": ",".join(row["gold_decision"] for row in rows),
                "glm_decision_correct_count": glm_decision_correct_count,
                "claude_decision_correct_count": claude_decision_correct_count,
                "glm_escalation_correct_count": glm_escalation_correct_count,
                "claude_escalation_correct_count": claude_escalation_correct_count,
                "glm_audit_passed_count": glm_audit_passed_count,
                "claude_audit_passed_count": claude_audit_passed_count,
                "decision_disagreement_count": decision_disagreement_count,
                "escalation_disagreement_count": escalation_disagreement_count,
                "audit_disagreement_count": audit_disagreement_count,
                "glm_escalation_recovery_count": glm_recovery_count,
                "claude_escalation_recovery_count": claude_recovery_count,
                "both_decision_wrong_count": both_decision_wrong_count,
                "both_escalation_wrong_count": both_escalation_wrong_count,
                "task_pattern": task_pattern,
                "safe_note": SAFE_NOTE,
            }
        )

    return output


def _condition_profile_rows(task_condition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for condition in CONDITIONS:
        rows = [row for row in task_condition_rows if row["condition"] == condition]
        n = len(rows)

        decision_counts = Counter(row["decision_pair_outcome"] for row in rows)
        escalation_counts = Counter(row["escalation_pair_outcome"] for row in rows)
        audit_counts = Counter(row["audit_pair_outcome"] for row in rows)
        glm_transition_counts = Counter(row["glm_escalation_transition"] for row in rows)
        claude_transition_counts = Counter(row["claude_escalation_transition"] for row in rows)

        output.append(
            {
                "condition": condition,
                "n_pairs": n,
                "decision_both_correct_count": decision_counts["both_correct"],
                "decision_both_correct_rate": _rate(decision_counts["both_correct"], n),
                "decision_both_wrong_count": decision_counts["both_not_correct"],
                "decision_both_wrong_rate": _rate(decision_counts["both_not_correct"], n),
                "decision_glm_only_correct_count": decision_counts["glm_only_correct"],
                "decision_claude_only_correct_count": decision_counts["claude_only_correct"],
                "escalation_both_correct_count": escalation_counts["both_correct"],
                "escalation_both_correct_rate": _rate(escalation_counts["both_correct"], n),
                "escalation_both_wrong_count": escalation_counts["both_not_correct"],
                "escalation_both_wrong_rate": _rate(escalation_counts["both_not_correct"], n),
                "escalation_glm_only_correct_count": escalation_counts["glm_only_correct"],
                "escalation_claude_only_correct_count": escalation_counts["claude_only_correct"],
                "audit_both_passed_count": audit_counts["both_audit_passed"],
                "audit_both_passed_rate": _rate(audit_counts["both_audit_passed"], n),
                "audit_both_not_passed_count": audit_counts["both_audit_not_passed"],
                "audit_both_not_passed_rate": _rate(audit_counts["both_audit_not_passed"], n),
                "audit_glm_only_passed_count": audit_counts["glm_only_audit_passed"],
                "audit_claude_only_passed_count": audit_counts["claude_only_audit_passed"],
                "glm_recovered_by_escalation_count": glm_transition_counts["decision_wrong_recovered_by_escalation"],
                "claude_recovered_by_escalation_count": claude_transition_counts["decision_wrong_recovered_by_escalation"],
                "glm_not_recovered_count": glm_transition_counts["decision_wrong_not_recovered"],
                "claude_not_recovered_count": claude_transition_counts["decision_wrong_not_recovered"],
                "glm_lost_at_escalation_count": glm_transition_counts["decision_correct_lost_at_escalation"],
                "claude_lost_at_escalation_count": claude_transition_counts["decision_correct_lost_at_escalation"],
                "safe_note": SAFE_NOTE,
            }
        )

    return output


def _high_signal_case_rows(task_condition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for row in task_condition_rows:
        reasons: list[str] = []

        if _is_true(row["decision_correct_disagreement"]):
            reasons.append("decision_disagreement")

        if _is_true(row["escalation_correct_disagreement"]):
            reasons.append("escalation_disagreement")

        if _is_true(row["audit_passed_disagreement"]):
            reasons.append("audit_disagreement")

        if _is_true(row["both_decision_wrong"]):
            reasons.append("both_decision_wrong")

        if _is_true(row["both_escalation_wrong"]):
            reasons.append("both_escalation_wrong")

        if row["glm_escalation_transition"] == "decision_wrong_recovered_by_escalation":
            reasons.append("glm_recovered_by_escalation")

        if row["claude_escalation_transition"] == "decision_wrong_recovered_by_escalation":
            reasons.append("claude_recovered_by_escalation")

        if row["glm_escalation_transition"] == "decision_correct_lost_at_escalation":
            reasons.append("glm_lost_at_escalation")

        if row["claude_escalation_transition"] == "decision_correct_lost_at_escalation":
            reasons.append("claude_lost_at_escalation")

        if not reasons:
            continue

        output.append(
            {
                "task_id": row["task_id"],
                "condition": row["condition"],
                "gold_decision": row["gold_decision"],
                "reasons": ",".join(reasons),
                "glm_decision_correct": row["glm_decision_correct"],
                "claude_decision_correct": row["claude_decision_correct"],
                "glm_escalation_correct": row["glm_escalation_correct"],
                "claude_escalation_correct": row["claude_escalation_correct"],
                "glm_audit_passed": row["glm_audit_passed"],
                "claude_audit_passed": row["claude_audit_passed"],
                "glm_escalation_transition": row["glm_escalation_transition"],
                "claude_escalation_transition": row["claude_escalation_transition"],
                "safe_note": SAFE_NOTE,
            }
        )

    return output


def _write_report(
    path: Path,
    *,
    manifest: dict[str, Any],
    condition_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    high_signal_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Pilot 03 full GLM-5.2 vs Anthropic/Claude paired task-level analysis",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        "This report focuses on task-condition paired behavior: agreement, disagreement, shared errors, "
        "audit differences, and escalation recovery patterns.",
        "",
        "## Condition-level paired profile",
        "",
        "| Condition | n | Decision both correct | Decision both wrong | Escalation both correct | Escalation both wrong | Audit both passed | Audit disagreement | GLM recoveries | Claude recoveries |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in condition_rows:
        audit_disagreement = row["audit_glm_only_passed_count"] + row["audit_claude_only_passed_count"]
        lines.append(
            f"| {row['condition']} | {row['n_pairs']} | "
            f"{row['decision_both_correct_count']} ({row['decision_both_correct_rate']}) | "
            f"{row['decision_both_wrong_count']} ({row['decision_both_wrong_rate']}) | "
            f"{row['escalation_both_correct_count']} ({row['escalation_both_correct_rate']}) | "
            f"{row['escalation_both_wrong_count']} ({row['escalation_both_wrong_rate']}) | "
            f"{row['audit_both_passed_count']} ({row['audit_both_passed_rate']}) | "
            f"{audit_disagreement} | "
            f"{row['glm_recovered_by_escalation_count']} | "
            f"{row['claude_recovered_by_escalation_count']} |"
        )

    task_pattern_counts = Counter(row["task_pattern"] for row in task_rows)

    lines.extend(
        [
            "",
            "## Task-pattern counts",
            "",
            "| Task pattern | n tasks |",
            "| --- | ---: |",
        ]
    )

    for pattern, count in sorted(task_pattern_counts.items()):
        lines.append(f"| {pattern} | {count} |")

    lines.extend(
        [
            "",
            "## High-signal task-condition cases",
            "",
            "| Task | Condition | Reasons | GLM transition | Claude transition |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for row in high_signal_rows:
        lines.append(
            f"| {row['task_id']} | {row['condition']} | {row['reasons']} | "
            f"{row['glm_escalation_transition']} | {row['claude_escalation_transition']} |"
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


def generate_paired_task_analysis(
    *,
    paired_chain_csv: Path,
    output_dir: Path,
) -> dict[str, Any]:
    rows = _read_csv(paired_chain_csv)
    _validate_source_rows(rows)

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "task_condition_paired_outcomes_csv": output_dir / "task_condition_paired_outcomes.csv",
        "task_level_summary_csv": output_dir / "task_level_summary.csv",
        "condition_pair_profile_csv": output_dir / "condition_pair_profile.csv",
        "high_signal_cases_csv": output_dir / "high_signal_cases.csv",
        "report_md": output_dir / "paired_task_level_analysis_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    task_condition_rows = _task_condition_rows(rows)
    task_rows = _task_level_summary_rows(task_condition_rows)
    condition_rows = _condition_profile_rows(task_condition_rows)
    high_signal_rows = _high_signal_case_rows(task_condition_rows)

    export_column_sets = [
        list(task_condition_rows[0].keys()) if task_condition_rows else [],
        list(task_rows[0].keys()) if task_rows else [],
        list(condition_rows[0].keys()) if condition_rows else [],
        list(high_signal_rows[0].keys()) if high_signal_rows else [],
    ]

    blocked_export_columns = []
    for columns in export_column_sets:
        blocked_export_columns.extend(_blocked_columns(columns))

    if blocked_export_columns:
        raise SystemExit(f"Blocked export columns found: {blocked_export_columns}")

    manifest = {
        "created_at_utc": _existing_created_at(outputs["manifest_json"]),
        "status": "PASS",
        "scope": "Pilot 03 full 20-task GLM-5.2 vs Anthropic/Claude paired task-level analysis",
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "source_files": {
            "paired_chain_csv": str(paired_chain_csv),
        },
        "source_policy": "committed sanitized paired-chain comparison CSV only",
        "row_counts": {
            "paired_chain_rows": len(rows),
            "task_condition_paired_outcomes": len(task_condition_rows),
            "task_level_summary": len(task_rows),
            "condition_pair_profile": len(condition_rows),
            "high_signal_cases": len(high_signal_rows),
        },
        "methods": {
            "pairing": "same task_id and same evidence condition across GLM-5.2 and Anthropic/Claude",
            "transition_categories": [
                "decision_correct_preserved",
                "decision_wrong_recovered_by_escalation",
                "decision_wrong_not_recovered",
                "decision_correct_lost_at_escalation",
            ],
        },
        "safe_note": SAFE_NOTE,
        "outputs": {name: str(path) for name, path in outputs.items()},
    }

    _write_csv(outputs["task_condition_paired_outcomes_csv"], task_condition_rows)
    _write_csv(outputs["task_level_summary_csv"], task_rows)
    _write_csv(outputs["condition_pair_profile_csv"], condition_rows)
    _write_csv(outputs["high_signal_cases_csv"], high_signal_rows)
    _write_json(outputs["manifest_json"], manifest)

    _write_report(
        outputs["report_md"],
        manifest=manifest,
        condition_rows=condition_rows,
        task_rows=task_rows,
        high_signal_rows=high_signal_rows,
    )

    risky_hits = _scan_risky_wording(
        [
            outputs["task_condition_paired_outcomes_csv"],
            outputs["task_level_summary_csv"],
            outputs["condition_pair_profile_csv"],
            outputs["high_signal_cases_csv"],
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
            "Generate paired task-level analysis for the full 20-task GLM-5.2 vs Anthropic/Claude Pilot 03 comparison. "
            "This command makes no real API calls."
        )
    )
    parser.add_argument("--paired-chain-csv", default=str(DEFAULT_PAIRED_CHAIN_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    manifest = generate_paired_task_analysis(
        paired_chain_csv=Path(args.paired_chain_csv),
        output_dir=Path(args.output_dir),
    )

    print("Pilot 03 full GLM-5.2 vs Anthropic/Claude paired task-level analysis generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
