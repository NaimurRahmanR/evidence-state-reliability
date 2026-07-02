from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SAFE_GLM_WORDING = "observed result under current Pilot 03 real LLM experimental conditions"
SAFE_CLAUDE_WORDING = "observed comparison subset under current Pilot 03 real LLM experimental conditions"
SHARED_TASK_IDS = ["P03-T0001", "P03-T0002", "P03-T0003", "P03-T0004", "P03-T0005"]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _truth(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _parse_glm_chain_rows_from_report(path: Path) -> list[dict[str, Any]]:
    """Parse the chain-level markdown table from the committed GLM report."""
    rows: list[dict[str, Any]] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("| P03-T"):
            continue

        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != 11:
            raise ValueError(f"Unexpected GLM chain table row shape: {line}")

        (
            task_id,
            condition,
            gold_decision,
            decision,
            decision_correct,
            audit_passed,
            audit_supported_decision,
            escalation,
            escalation_correct,
            overrode,
            valid_chain,
        ) = parts

        rows.append(
            {
                "task_id": task_id,
                "condition": condition,
                "provider": "zai",
                "model_name": "glm-5.2",
                "gold_decision": gold_decision,
                "decision_final_decision": decision,
                "audit_passed": audit_passed,
                "audit_supported_decision": audit_supported_decision,
                "escalation_final_decision": escalation,
                "decision_correct": decision_correct,
                "escalation_correct": escalation_correct,
                "overrode": overrode,
                "valid_chain": valid_chain,
            }
        )

    return rows


def _normalise_claude_chain_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    normalised: list[dict[str, Any]] = []

    for row in rows:
        normalised.append(
            {
                "task_id": row["task_id"],
                "condition": row["condition"],
                "provider": row["provider"],
                "model_name": row["model_name"],
                "gold_decision": row["gold_decision"],
                "decision_final_decision": row["decision_final_decision"],
                "audit_passed": row["audit_passed"],
                "audit_supported_decision": "",
                "escalation_final_decision": row["escalation_final_decision"],
                "decision_correct": row["decision_correct"],
                "escalation_correct": row["escalation_correct"],
                "overrode": "",
                "valid_chain": row["valid_schema_chain"],
            }
        )

    return normalised


def _condition_summary_from_chains(
    *,
    rows: list[dict[str, Any]],
    provider_label: str,
    model_label: str,
    scope_label: str,
    safe_wording: str,
) -> list[dict[str, Any]]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        by_condition[row["condition"]].append(row)

    out: list[dict[str, Any]] = []

    for condition in sorted(by_condition):
        condition_rows = by_condition[condition]
        n = len(condition_rows)
        n_tasks = len({row["task_id"] for row in condition_rows})

        decision_correct = sum(1 for row in condition_rows if _truth(row["decision_correct"]))
        escalation_correct = sum(1 for row in condition_rows if _truth(row["escalation_correct"]))
        audit_passed_true = sum(1 for row in condition_rows if _truth(row["audit_passed"]))
        valid_chain = sum(1 for row in condition_rows if _truth(row["valid_chain"]))

        out.append(
            {
                "scope": scope_label,
                "provider": provider_label,
                "model": model_label,
                "condition": condition,
                "n_tasks": n_tasks,
                "n_chains": n,
                "decision_correct_count": decision_correct,
                "decision_correct_rate": _rate(decision_correct, n),
                "escalation_correct_count": escalation_correct,
                "escalation_correct_rate": _rate(escalation_correct, n),
                "audit_passed_true_count": audit_passed_true,
                "audit_passed_true_rate": _rate(audit_passed_true, n),
                "valid_chain_count": valid_chain,
                "valid_chain_rate": _rate(valid_chain, n),
                "safe_wording": safe_wording,
            }
        )

    return out


def _count_true_from_counter_text(value: str) -> int:
    """Parse compact counter text like 'False:18, True:2' and return True count."""
    value = value.strip()
    if not value:
        return 0

    counts: dict[str, int] = {}
    for part in value.split(","):
        if ":" not in part:
            continue
        key, raw_count = part.split(":", 1)
        key = key.strip()
        raw_count = raw_count.strip()
        if raw_count.isdigit():
            counts[key] = int(raw_count)

    return counts.get("True", 0)


def _normalise_glm_full_condition_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    for row in rows:
        n_chains = int(row["n"])
        audit_passed_true_count = _count_true_from_counter_text(row["audit_passed"])

        out.append(
            {
                "scope": "GLM full 20-task checkpoint",
                "provider": "zai",
                "model": "glm-5.2",
                "condition": row["condition"],
                "n_tasks": n_chains,
                "n_chains": n_chains,
                "decision_correct_count": int(row["decision_correct"]),
                "decision_correct_rate": float(row["decision_correct_rate"]),
                "escalation_correct_count": int(row["escalation_correct"]),
                "escalation_correct_rate": float(row["escalation_correct_rate"]),
                "audit_passed_true_count": audit_passed_true_count,
                "audit_passed_true_rate": _rate(audit_passed_true_count, n_chains),
                "valid_chain_count": int(row["valid_chain"]),
                "valid_chain_rate": float(row["valid_chain_rate"]),
                "safe_wording": SAFE_GLM_WORDING,
            }
        )

    return out


def _normalise_claude_condition_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    for row in rows:
        out.append(
            {
                "scope": "Claude 5-task comparison subset",
                "provider": "anthropic",
                "model": "claude-opus-4-8",
                "condition": row["condition"],
                "n_tasks": int(row["n_chains"]),
                "n_chains": int(row["n_chains"]),
                "decision_correct_count": int(row["decision_correct_count"]),
                "decision_correct_rate": float(row["decision_correct_rate"]),
                "escalation_correct_count": int(row["escalation_correct_count"]),
                "escalation_correct_rate": float(row["escalation_correct_rate"]),
                "audit_passed_true_count": int(row["audit_passed_true_count"]),
                "audit_passed_true_rate": float(row["audit_passed_true_rate"]),
                "valid_chain_count": int(row["valid_schema_chain_count"]),
                "valid_chain_rate": float(row["valid_schema_chain_rate"]),
                "safe_wording": SAFE_CLAUDE_WORDING,
            }
        )

    return out


def _make_report(
    *,
    output_path: Path,
    shared_rows: list[dict[str, Any]],
    reference_rows: list[dict[str, Any]],
    shared_task_ids: list[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "# Pilot 03 GLM-vs-Claude comparison report",
        "",
        f"Generated at UTC: {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
        "## Reliability framing",
        "",
        f"- GLM wording: {SAFE_GLM_WORDING}",
        f"- Claude wording: {SAFE_CLAUDE_WORDING}",
        "- This report is descriptive only.",
        "- It must not be read as a general model ranking.",
        "- The shared-task comparison is the safer comparison because both providers are evaluated on the same five task IDs.",
        "- The 20-task GLM result is included only as a larger GLM checkpoint reference.",
        "",
        "## Shared 5-task condition comparison",
        "",
        f"Shared task IDs: `{shared_task_ids}`",
        "",
        "| provider | model | condition | n_chains | decision rate | escalation rate | audit passed true rate | valid chain rate |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]

    for row in shared_rows:
        lines.append(
            "| {provider} | {model} | {condition} | {n_chains} | {decision_correct_rate} | "
            "{escalation_correct_rate} | {audit_passed_true_rate} | {valid_chain_rate} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Scope reference condition comparison",
            "",
            "This table places the full 20-task GLM checkpoint beside the 5-task Claude comparison subset. The sample sizes are different, so this section should be used as context only.",
            "",
            "| scope | provider | model | condition | n_chains | decision rate | escalation rate | valid chain rate |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
    )

    for row in reference_rows:
        lines.append(
            "| {scope} | {provider} | {model} | {condition} | {n_chains} | "
            "{decision_correct_rate} | {escalation_correct_rate} | {valid_chain_rate} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Conservative interpretation",
            "",
            "Under the shared five-task Pilot 03 comparison, both providers show preserved structured-output validity while decision and escalation correctness vary by evidence condition. This is an observed comparison subset under current Pilot 03 real LLM experimental conditions only.",
            "",
            "The result supports continued analysis of evidence-state degradation as a pipeline-level phenomenon, but it does not establish general reliability properties of GLM-5.2, Claude Opus 4.8, Z.ai, Anthropic, or deployed systems.",
            "",
            "For paper writing, the safest claim is that Pilot 03 demonstrates a reproducible method for comparing how downstream decision-audit-escalation chains behave when required evidence is removed under controlled tasks and prompts.",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a commit-safe Pilot 03 GLM-vs-Claude comparison report."
    )
    parser.add_argument(
        "--glm-report",
        default="reports/pilot_03_real_glm_t0020_results.md",
    )
    parser.add_argument(
        "--glm-condition-csv",
        default="reports/pilot_03_real_glm_t0020_condition_summary.csv",
    )
    parser.add_argument(
        "--claude-chain-csv",
        default="reports/pilot_03_claude_comparison_subset/claude_subset_chain_summary.csv",
    )
    parser.add_argument(
        "--claude-condition-csv",
        default="reports/pilot_03_claude_comparison_subset/claude_subset_condition_summary.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/pilot_03_glm_vs_claude_comparison",
    )

    args = parser.parse_args()

    glm_report = Path(args.glm_report)
    glm_condition_csv = Path(args.glm_condition_csv)
    claude_chain_csv = Path(args.claude_chain_csv)
    claude_condition_csv = Path(args.claude_condition_csv)
    output_dir = Path(args.output_dir)

    glm_chain_rows = _parse_glm_chain_rows_from_report(glm_report)
    claude_chain_rows = _normalise_claude_chain_rows(_read_csv(claude_chain_csv))

    glm_shared_rows = [
        row for row in glm_chain_rows if row["task_id"] in SHARED_TASK_IDS
    ]
    claude_shared_rows = [
        row for row in claude_chain_rows if row["task_id"] in SHARED_TASK_IDS
    ]

    shared_condition_rows = []
    shared_condition_rows.extend(
        _condition_summary_from_chains(
            rows=glm_shared_rows,
            provider_label="zai",
            model_label="glm-5.2",
            scope_label="Shared 5-task comparison",
            safe_wording=SAFE_GLM_WORDING,
        )
    )
    shared_condition_rows.extend(
        _condition_summary_from_chains(
            rows=claude_shared_rows,
            provider_label="anthropic",
            model_label="claude-opus-4-8",
            scope_label="Shared 5-task comparison",
            safe_wording=SAFE_CLAUDE_WORDING,
        )
    )

    reference_rows = []
    reference_rows.extend(_normalise_glm_full_condition_rows(_read_csv(glm_condition_csv)))
    reference_rows.extend(_normalise_claude_condition_rows(_read_csv(claude_condition_csv)))

    output_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(output_dir / "shared_5_task_condition_comparison.csv", shared_condition_rows)
    _write_csv(output_dir / "scope_reference_condition_comparison.csv", reference_rows)

    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "safe_glm_wording": SAFE_GLM_WORDING,
        "safe_claude_wording": SAFE_CLAUDE_WORDING,
        "shared_task_ids": SHARED_TASK_IDS,
        "source_files": {
            "glm_report": str(glm_report),
            "glm_condition_csv": str(glm_condition_csv),
            "claude_chain_csv": str(claude_chain_csv),
            "claude_condition_csv": str(claude_condition_csv),
        },
        "outputs": [
            "shared_5_task_condition_comparison.csv",
            "scope_reference_condition_comparison.csv",
            "glm_vs_claude_comparison_report.md",
            "manifest.json",
        ],
    }

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    _make_report(
        output_path=output_dir / "glm_vs_claude_comparison_report.md",
        shared_rows=shared_condition_rows,
        reference_rows=reference_rows,
        shared_task_ids=SHARED_TASK_IDS,
    )

    print("Pilot 03 GLM-vs-Claude comparison report generated.")
    print(f"glm_chain_rows_total: {len(glm_chain_rows)}")
    print(f"glm_shared_rows: {len(glm_shared_rows)}")
    print(f"claude_shared_rows: {len(claude_shared_rows)}")
    print(f"shared_condition_rows: {len(shared_condition_rows)}")
    print(f"reference_rows: {len(reference_rows)}")
    print(f"output_dir: {output_dir}")
    print("real_api_calls: 0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
