from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


SAFE_GLM_WORDING = "observed result under current Pilot 03 real LLM experimental conditions"
SAFE_CLAUDE_WORDING = "observed comparison subset under current Pilot 03 real LLM experimental conditions"

CONDITION_LABELS = {
    "original_evidence": "Original\nevidence",
    "missing_policy_rule": "Missing\npolicy rule",
    "missing_one_required_unit": "Missing one\nrequired unit",
}

CONDITION_ORDER = [
    "original_evidence",
    "missing_policy_rule",
    "missing_one_required_unit",
]

PROVIDER_LABELS = {
    "zai": "GLM-5.2",
    "anthropic": "Claude Opus 4.8",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value != "" else 0.0


def _save_figure(fig: Any, output_base: Path) -> list[str]:
    output_base.parent.mkdir(parents=True, exist_ok=True)

    png_path = output_base.with_suffix(".png")
    pdf_path = output_base.with_suffix(".pdf")

    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    return [str(png_path), str(pdf_path)]


def _plot_glm20_condition_rates(glm_condition_rows: list[dict[str, str]], output_dir: Path) -> list[str]:
    rows_by_condition = {row["condition"]: row for row in glm_condition_rows}
    rows = [rows_by_condition[condition] for condition in CONDITION_ORDER]

    labels = [CONDITION_LABELS[row["condition"]] for row in rows]
    decision_rates = [_float(row, "decision_correct_rate") for row in rows]
    escalation_rates = [_float(row, "escalation_correct_rate") for row in rows]
    valid_chain_rates = [_float(row, "valid_chain_rate") for row in rows]

    x_positions = list(range(len(rows)))
    width = 0.25

    fig = plt.figure(figsize=(8.2, 4.8))
    ax = fig.add_subplot(1, 1, 1)

    ax.bar([x - width for x in x_positions], decision_rates, width, label="Decision correct")
    ax.bar(x_positions, escalation_rates, width, label="Escalation correct")
    ax.bar([x + width for x in x_positions], valid_chain_rates, width, label="Valid chain")

    ax.set_title("Pilot 03 GLM-5.2 condition-level rates")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.08)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.legend(loc="lower left")
    ax.grid(axis="y", alpha=0.3)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", fontsize=8, padding=2)

    fig.text(
        0.01,
        0.01,
        "Source: GLM 20-task checkpoint. Level 1 wording only: observed result under current Pilot 03 real LLM experimental conditions.",
        fontsize=7,
    )

    return _save_figure(fig, output_dir / "figure_01_glm20_condition_rates")


def _provider_condition_rows(shared_rows: list[dict[str, str]], metric_key: str) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}

    for provider in ["zai", "anthropic"]:
        provider_rows = {
            row["condition"]: row
            for row in shared_rows
            if row["provider"] == provider
        }
        out[provider] = [
            _float(provider_rows[condition], metric_key)
            for condition in CONDITION_ORDER
        ]

    return out


def _plot_shared_provider_metric(
    *,
    shared_rows: list[dict[str, str]],
    output_dir: Path,
    metric_key: str,
    metric_label: str,
    title: str,
    output_name: str,
) -> list[str]:
    metric_by_provider = _provider_condition_rows(shared_rows, metric_key)

    labels = [CONDITION_LABELS[condition] for condition in CONDITION_ORDER]
    x_positions = list(range(len(CONDITION_ORDER)))
    width = 0.34

    fig = plt.figure(figsize=(8.2, 4.8))
    ax = fig.add_subplot(1, 1, 1)

    ax.bar(
        [x - width / 2 for x in x_positions],
        metric_by_provider["zai"],
        width,
        label=PROVIDER_LABELS["zai"],
    )
    ax.bar(
        [x + width / 2 for x in x_positions],
        metric_by_provider["anthropic"],
        width,
        label=PROVIDER_LABELS["anthropic"],
    )

    ax.set_title(title)
    ax.set_ylabel(metric_label)
    ax.set_ylim(0, 1.08)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.legend(loc="lower left")
    ax.grid(axis="y", alpha=0.3)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", fontsize=8, padding=2)

    fig.text(
        0.01,
        0.01,
        "Source: shared five-task Pilot 03 comparison. Descriptive only; not a general model ranking.",
        fontsize=7,
    )

    return _save_figure(fig, output_dir / output_name)


def _write_notes(output_dir: Path, generated_files: list[str]) -> None:
    lines = [
        "# Pilot 03 paper-ready figure notes",
        "",
        f"Generated at UTC: {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        "- Figures are generated only from committed CSV summaries.",
        "- Real API calls: 0.",
        "- Raw real LLM outputs are not used directly by this figure script.",
        f"- GLM wording: {SAFE_GLM_WORDING}",
        f"- Claude wording: {SAFE_CLAUDE_WORDING}",
        "",
        "## Figures",
        "",
        "1. `figure_01_glm20_condition_rates`: GLM-5.2 20-task condition-level decision, escalation, and valid-chain rates.",
        "2. `figure_02_shared5_provider_decision_rates`: shared five-task GLM-vs-Claude decision-correct rates.",
        "3. `figure_03_shared5_provider_escalation_rates`: shared five-task GLM-vs-Claude escalation-correct rates.",
        "",
        "## Conservative interpretation",
        "",
        "These figures should be described as observed results under current Pilot 03 real LLM experimental conditions. The GLM 20-task figure is a larger GLM checkpoint. The GLM-vs-Claude figures are shared five-task comparison figures and should not be treated as general model rankings.",
        "",
        "## Generated files",
        "",
    ]

    for file_path in generated_files:
        lines.append(f"- `{file_path}`")

    (output_dir / "figure_notes.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    output_dir = Path("reports/pilot_03_figures")

    glm_condition_csv = Path("reports/pilot_03_real_glm_t0020_condition_summary.csv")
    shared_comparison_csv = Path(
        "reports/pilot_03_glm_vs_claude_comparison/shared_5_task_condition_comparison.csv"
    )

    if not glm_condition_csv.exists():
        raise FileNotFoundError(f"Missing GLM condition CSV: {glm_condition_csv}")
    if not shared_comparison_csv.exists():
        raise FileNotFoundError(f"Missing shared comparison CSV: {shared_comparison_csv}")

    glm_condition_rows = _read_csv(glm_condition_csv)
    shared_rows = _read_csv(shared_comparison_csv)

    generated_files: list[str] = []

    generated_files.extend(
        _plot_glm20_condition_rates(
            glm_condition_rows=glm_condition_rows,
            output_dir=output_dir,
        )
    )

    generated_files.extend(
        _plot_shared_provider_metric(
            shared_rows=shared_rows,
            output_dir=output_dir,
            metric_key="decision_correct_rate",
            metric_label="Decision correct rate",
            title="Pilot 03 shared five-task decision correctness",
            output_name="figure_02_shared5_provider_decision_rates",
        )
    )

    generated_files.extend(
        _plot_shared_provider_metric(
            shared_rows=shared_rows,
            output_dir=output_dir,
            metric_key="escalation_correct_rate",
            metric_label="Escalation correct rate",
            title="Pilot 03 shared five-task escalation correctness",
            output_name="figure_03_shared5_provider_escalation_rates",
        )
    )

    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "real_api_calls": 0,
        "safe_glm_wording": SAFE_GLM_WORDING,
        "safe_claude_wording": SAFE_CLAUDE_WORDING,
        "source_files": {
            "glm_condition_csv": str(glm_condition_csv),
            "shared_comparison_csv": str(shared_comparison_csv),
        },
        "generated_files": generated_files + [str(output_dir / "figure_notes.md"), str(output_dir / "figure_manifest.json")],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figure_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    _write_notes(output_dir=output_dir, generated_files=generated_files)

    print("Pilot 03 paper-ready figures generated.")
    print(f"output_dir: {output_dir}")
    print(f"generated_files: {len(generated_files)}")
    for file_path in generated_files:
        print(file_path)
    print("real_api_calls: 0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
