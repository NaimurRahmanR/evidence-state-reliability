from __future__ import annotations

import argparse
import csv
import json
import math
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_PAIRED_CHAIN_CSV = Path("reports/pilot_03_glm_vs_claude_t0020_full/paired_chain_comparison.csv")
DEFAULT_OUTPUT_DIR = Path("reports/pilot_03_glm_vs_claude_t0020_uncertainty")

CONDITIONS = [
    "original_evidence",
    "missing_policy_rule",
    "missing_one_required_unit",
]

METRICS = [
    {
        "metric": "decision_correct",
        "glm_column": "glm_decision_correct",
        "claude_column": "claude_decision_correct",
        "interpretation": "Whether the decision-stage final decision matched the task gold decision.",
    },
    {
        "metric": "escalation_correct",
        "glm_column": "glm_escalation_correct",
        "claude_column": "claude_escalation_correct",
        "interpretation": "Whether the escalation-stage final decision matched the task gold decision.",
    },
    {
        "metric": "audit_passed",
        "glm_column": "glm_audit_passed",
        "claude_column": "claude_audit_passed",
        "interpretation": "Whether the audit stage passed the chain output.",
    },
    {
        "metric": "valid_json_chain",
        "glm_column": "glm_valid_json_chain",
        "claude_column": "claude_valid_json_chain",
        "interpretation": "Whether the selected sanitized chain is treated as JSON-valid for comparison.",
    },
    {
        "metric": "valid_schema_chain",
        "glm_column": "glm_valid_schema_chain",
        "claude_column": "claude_valid_schema_chain",
        "interpretation": "Whether the selected sanitized chain is schema-valid for comparison.",
    },
]

SAFE_NOTE = (
    "Uncertainty estimates are descriptive for the controlled Pilot 03 20-task comparison and use committed "
    "sanitized paired-chain outputs only. They should not be interpreted as broad deployment evidence or broad "
    "cross-provider conclusions."
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


def _rate(successes: int, n: int) -> float | None:
    if n == 0:
        return None
    return round(successes / n, 6)


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float | None, float | None]:
    if n == 0:
        return None, None

    phat = successes / n
    denom = 1 + (z * z / n)
    centre = phat + (z * z / (2 * n))
    margin = z * math.sqrt((phat * (1 - phat) / n) + (z * z / (4 * n * n)))

    lower = (centre - margin) / denom
    upper = (centre + margin) / denom

    return max(0.0, lower), min(1.0, upper)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("Cannot compute percentile of empty list.")

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    rank = (len(ordered) - 1) * percentile
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)

    if lower_index == upper_index:
        return ordered[int(rank)]

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    fraction = rank - lower_index

    return lower_value + ((upper_value - lower_value) * fraction)


def _paired_bootstrap_ci(
    differences: list[float],
    *,
    seed: int,
    n_bootstrap: int,
) -> tuple[float, float]:
    if not differences:
        raise ValueError("No paired differences supplied.")

    rng = random.Random(seed)
    n = len(differences)
    bootstrap_means: list[float] = []

    for _ in range(n_bootstrap):
        sample = [differences[rng.randrange(n)] for _ in range(n)]
        bootstrap_means.append(sum(sample) / n)

    return _percentile(bootstrap_means, 0.025), _percentile(bootstrap_means, 0.975)


def _mcnemar_exact_two_sided_p(glm_only_success: int, claude_only_success: int) -> float | None:
    discordant = glm_only_success + claude_only_success

    if discordant == 0:
        return None

    smaller = min(glm_only_success, claude_only_success)
    cumulative = 0.0

    for k in range(smaller + 1):
        cumulative += math.comb(discordant, k) * (0.5 ** discordant)

    return min(1.0, 2.0 * cumulative)


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

    condition_counts = {
        condition: sum(1 for row in rows if row["condition"] == condition)
        for condition in CONDITIONS
    }

    expected = {
        "original_evidence": 20,
        "missing_policy_rule": 20,
        "missing_one_required_unit": 20,
    }

    if condition_counts != expected:
        raise SystemExit(f"Unexpected condition counts: {condition_counts}")

    blocked_source_columns = _blocked_columns(list(rows[0].keys()) if rows else [])
    if blocked_source_columns:
        raise SystemExit(f"Blocked source columns found: {blocked_source_columns}")

    required_columns = {"task_id", "condition"}
    for metric in METRICS:
        required_columns.add(metric["glm_column"])
        required_columns.add(metric["claude_column"])

    missing = sorted(required_columns - set(rows[0].keys()))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")


def _model_uncertainty_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for condition in CONDITIONS:
        condition_rows = [row for row in rows if row["condition"] == condition]

        for model_label, provider, model_name, column_prefix in [
            ("GLM-5.2", "zai", "glm-5.2", "glm"),
            ("Claude Opus 4.8", "anthropic", "claude-opus-4-8", "claude"),
        ]:
            for metric in METRICS:
                column = metric[f"{column_prefix}_column"]
                n = len(condition_rows)
                successes = sum(_is_true(row[column]) for row in condition_rows)
                estimate = successes / n
                ci_lower, ci_upper = _wilson_ci(successes, n)

                output.append(
                    {
                        "provider": provider,
                        "model_name": model_name,
                        "model_label": model_label,
                        "condition": condition,
                        "metric": metric["metric"],
                        "successes": successes,
                        "n": n,
                        "estimate": _round(estimate),
                        "ci_method": "wilson_95",
                        "ci_lower": _round(ci_lower),
                        "ci_upper": _round(ci_upper),
                        "interpretation": metric["interpretation"],
                        "safe_note": SAFE_NOTE,
                    }
                )

    return output


def _paired_delta_rows(
    rows: list[dict[str, str]],
    *,
    n_bootstrap: int,
    seed: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for condition_index, condition in enumerate(CONDITIONS):
        condition_rows = [row for row in rows if row["condition"] == condition]

        for metric_index, metric in enumerate(METRICS):
            glm_column = metric["glm_column"]
            claude_column = metric["claude_column"]

            glm_values = [1 if _is_true(row[glm_column]) else 0 for row in condition_rows]
            claude_values = [1 if _is_true(row[claude_column]) else 0 for row in condition_rows]
            differences = [claude - glm for glm, claude in zip(glm_values, claude_values)]

            n = len(differences)
            glm_successes = sum(glm_values)
            claude_successes = sum(claude_values)
            glm_rate = glm_successes / n
            claude_rate = claude_successes / n
            paired_difference = sum(differences) / n

            bootstrap_seed = seed + (condition_index * 100) + metric_index
            ci_lower, ci_upper = _paired_bootstrap_ci(
                differences,
                seed=bootstrap_seed,
                n_bootstrap=n_bootstrap,
            )

            both_success = sum(1 for glm, claude in zip(glm_values, claude_values) if glm == 1 and claude == 1)
            both_failure = sum(1 for glm, claude in zip(glm_values, claude_values) if glm == 0 and claude == 0)
            glm_only_success = sum(1 for glm, claude in zip(glm_values, claude_values) if glm == 1 and claude == 0)
            claude_only_success = sum(1 for glm, claude in zip(glm_values, claude_values) if glm == 0 and claude == 1)
            discordant = glm_only_success + claude_only_success
            exact_p = _mcnemar_exact_two_sided_p(glm_only_success, claude_only_success)

            output.append(
                {
                    "condition": condition,
                    "metric": metric["metric"],
                    "n_pairs": n,
                    "glm_successes": glm_successes,
                    "claude_successes": claude_successes,
                    "glm_rate": _round(glm_rate),
                    "claude_rate": _round(claude_rate),
                    "claude_minus_glm": _round(paired_difference),
                    "paired_bootstrap_ci_method": f"paired_bootstrap_percentile_95_B{n_bootstrap}",
                    "paired_bootstrap_ci_lower": _round(ci_lower),
                    "paired_bootstrap_ci_upper": _round(ci_upper),
                    "both_success": both_success,
                    "both_failure": both_failure,
                    "glm_only_success": glm_only_success,
                    "claude_only_success": claude_only_success,
                    "discordant_pairs": discordant,
                    "mcnemar_exact_two_sided_p": _round(exact_p),
                    "bootstrap_seed": bootstrap_seed,
                    "interpretation": metric["interpretation"],
                    "safe_note": SAFE_NOTE,
                }
            )

    return output


def _write_report(
    path: Path,
    *,
    manifest: dict[str, Any],
    model_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Pilot 03 full GLM-5.2 vs Anthropic/Claude uncertainty report",
        "",
        f"Generated at UTC: {manifest['created_at_utc']}",
        "",
        "## Scope",
        "",
        SAFE_NOTE,
        "",
        "This report is based on the committed full 20-task paired comparison outputs. "
        "It makes no model calls and does not inspect ignored local source artifacts.",
        "",
        "## Model-condition Wilson intervals",
        "",
        "| Model | Condition | Metric | Successes / n | Estimate | 95% CI |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]

    for row in model_rows:
        lines.append(
            f"| {row['model_name']} | {row['condition']} | {row['metric']} | "
            f"{row['successes']} / {row['n']} | {row['estimate']} | "
            f"[{row['ci_lower']}, {row['ci_upper']}] |"
        )

    lines.extend(
        [
            "",
            "## Paired Claude-minus-GLM uncertainty",
            "",
            "Positive differences mean the Anthropic/Claude rate is higher under the same task-condition pairs.",
            "",
            "| Condition | Metric | GLM rate | Claude rate | Claude minus GLM | 95% paired bootstrap CI | Discordant pairs | Exact paired p |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for row in delta_rows:
        p_value = row["mcnemar_exact_two_sided_p"]
        p_text = "N/A" if p_value is None else str(p_value)

        lines.append(
            f"| {row['condition']} | {row['metric']} | {row['glm_rate']} | "
            f"{row['claude_rate']} | {row['claude_minus_glm']} | "
            f"[{row['paired_bootstrap_ci_lower']}, {row['paired_bootstrap_ci_upper']}] | "
            f"{row['discordant_pairs']} | {p_text} |"
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


def generate_uncertainty(
    *,
    paired_chain_csv: Path,
    output_dir: Path,
    n_bootstrap: int,
    seed: int,
) -> dict[str, Any]:
    rows = _read_csv(paired_chain_csv)
    _validate_source_rows(rows)

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "model_metric_uncertainty_csv": output_dir / "model_metric_uncertainty.csv",
        "paired_delta_uncertainty_csv": output_dir / "paired_delta_uncertainty.csv",
        "report_md": output_dir / "glm_vs_claude_t0020_uncertainty_report.md",
        "manifest_json": output_dir / "manifest.json",
    }

    model_rows = _model_uncertainty_rows(rows)
    delta_rows = _paired_delta_rows(rows, n_bootstrap=n_bootstrap, seed=seed)

    export_column_sets = [
        list(model_rows[0].keys()) if model_rows else [],
        list(delta_rows[0].keys()) if delta_rows else [],
    ]

    blocked_export_columns = []
    for columns in export_column_sets:
        blocked_export_columns.extend(_blocked_columns(columns))

    if blocked_export_columns:
        raise SystemExit(f"Blocked export columns found: {blocked_export_columns}")

    manifest = {
        "created_at_utc": _existing_created_at(outputs["manifest_json"]),
        "status": "PASS",
        "scope": "Pilot 03 full 20-task GLM-5.2 vs Anthropic/Claude uncertainty analysis",
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "source_files": {
            "paired_chain_csv": str(paired_chain_csv),
        },
        "source_policy": "committed sanitized paired-chain comparison CSV only",
        "row_counts": {
            "paired_chain_rows": len(rows),
            "model_metric_uncertainty": len(model_rows),
            "paired_delta_uncertainty": len(delta_rows),
        },
        "methods": {
            "single_model_interval": "Wilson 95% confidence interval for binomial proportions",
            "paired_difference_interval": "Deterministic paired bootstrap percentile 95% interval over task-condition pairs",
            "paired_disagreement_test": "Exact two-sided binomial form of McNemar discordant-pair test where discordant pairs exist",
            "n_bootstrap": n_bootstrap,
            "seed": seed,
        },
        "safe_note": SAFE_NOTE,
        "outputs": {name: str(path) for name, path in outputs.items()},
    }

    _write_csv(outputs["model_metric_uncertainty_csv"], model_rows)
    _write_csv(outputs["paired_delta_uncertainty_csv"], delta_rows)
    _write_json(outputs["manifest_json"], manifest)

    _write_report(
        outputs["report_md"],
        manifest=manifest,
        model_rows=model_rows,
        delta_rows=delta_rows,
    )

    risky_hits = _scan_risky_wording(
        [
            outputs["model_metric_uncertainty_csv"],
            outputs["paired_delta_uncertainty_csv"],
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
            "Generate uncertainty summaries for the full 20-task GLM-5.2 vs Anthropic/Claude Pilot 03 comparison. "
            "This command makes no real API calls."
        )
    )
    parser.add_argument("--paired-chain-csv", default=str(DEFAULT_PAIRED_CHAIN_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--n-bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260707)
    args = parser.parse_args()

    if args.n_bootstrap < 1000:
        raise SystemExit("--n-bootstrap must be at least 1000 for a stable descriptive interval.")

    manifest = generate_uncertainty(
        paired_chain_csv=Path(args.paired_chain_csv),
        output_dir=Path(args.output_dir),
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
    )

    print("Pilot 03 full GLM-5.2 vs Anthropic/Claude uncertainty report generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"methods: {manifest['methods']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
