from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


OUTPUT_DIR = Path("reports/cross_pilot_figures_tables")
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"
MANIFEST_JSON = OUTPUT_DIR / "manifest.json"
TABLE_INDEX_MD = OUTPUT_DIR / "table_figure_index.md"

CROSS_FRAMEWORK_CSV = Path("reports/cross_pilot_evidence_state_reliability/cross_pilot_framework_summary.csv")
CROSS_VALIDATION_CSV = Path("reports/cross_pilot_evidence_state_reliability/pipeline_validation_summary.csv")
CROSS_CONDITION_ALIGNMENT_CSV = Path("reports/cross_pilot_evidence_state_reliability/condition_metric_alignment.csv")
CROSS_METRIC_INVENTORY_CSV = Path("reports/cross_pilot_evidence_state_reliability/metric_inventory.csv")
CROSS_REPORT_MANIFEST = Path("reports/cross_pilot_evidence_state_reliability/manifest.json")
CROSS_VALIDATION_MANIFEST = Path("reports/cross_pilot_validation/manifest.json")

PILOT_04_RELIABILITY_CSV = Path("reports/pilot_04_reliability_cascade_metrics/condition_reliability_cascade_metrics.csv")
PILOT_04_STAGE_CASCADE_CSV = Path("reports/pilot_04_stage_cascade/condition_stage_cascade_summary.csv")
PILOT_04_UNCERTAINTY_CSV = Path("reports/pilot_04_uncertainty/condition_uncertainty_summary.csv")

RISKY_PUBLIC_WORDING = [
    "Q1",
    "journal-level",
    "groundbreaking",
    "proven",
    "universal",
    "real-world deployment proof",
    "provider ranking",
    "general Claude reliability",
    "general GLM reliability",
    "live deployment validity",
    "broad LLM reliability",
    "general model superiority",
    "financial safety",
    "legal safety",
    "medical safety",
    "lending regulation",
    "compliance with lending regulation",
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _as_float(value: str) -> float:
    return float(value)


def _as_int_or_zero(value: str) -> int:
    if value == "":
        return 0
    return int(float(value))


def _copy_selected_rows(rows: list[dict[str, str]], selected_columns: list[str]) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for row in rows:
        copied.append({column: row.get(column, "") for column in selected_columns})
    return copied


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")

    return "\n".join([header, separator] + body)


def _save_bar_figure(path: Path, labels: list[str], values: list[float], title: str, ylabel: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def _save_line_figure(path: Path, labels: list[str], values: list[float], title: str, ylabel: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.plot(labels, values, marker="o")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.ylim(0, 1.05)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def _public_wording_hits(text: str) -> list[str]:
    return [phrase for phrase in RISKY_PUBLIC_WORDING if phrase in text]


def _build_tables() -> dict[str, list[dict[str, Any]]]:
    framework_rows = _read_csv(CROSS_FRAMEWORK_CSV)
    validation_rows = _read_csv(CROSS_VALIDATION_CSV)
    condition_rows = _read_csv(CROSS_CONDITION_ALIGNMENT_CSV)
    metric_inventory_rows = _read_csv(CROSS_METRIC_INVENTORY_CSV)
    p04_reliability_rows = _read_csv(PILOT_04_RELIABILITY_CSV)
    p04_stage_rows = _read_csv(PILOT_04_STAGE_CASCADE_CSV)
    p04_uncertainty_rows = _read_csv(PILOT_04_UNCERTAINTY_CSV)

    framework_table = _copy_selected_rows(
        framework_rows,
        [
            "pilot_id",
            "domain",
            "evidence_package_role",
            "pipeline_type",
            "domain_status",
            "condition_metric_rows",
            "claim_boundary",
            "real_api_calls_in_cross_pilot_generation",
            "raw_response_inspection",
        ],
    )

    validation_table = _copy_selected_rows(
        validation_rows,
        [
            "pilot_id",
            "validation_source",
            "status",
            "n_steps",
            "n_failed_steps",
            "n_checks",
            "n_failed_checks",
            "real_api_calls",
            "raw_response_inspection",
        ],
    )

    condition_alignment_table = _copy_selected_rows(
        condition_rows,
        [
            "pilot_id",
            "domain",
            "condition",
            "structural_metric_value",
            "reliability_metric_value",
            "audit_metric_value",
            "escalation_metric_value",
            "metric_scope_note",
            "real_api_calls",
        ],
    )

    p04_reliability_table = _copy_selected_rows(
        p04_reliability_rows,
        [
            "condition",
            "n_chains",
            "structural_validity_rate",
            "decision_reliability_rate",
            "audit_pass_rate",
            "escalation_rate",
            "mean_evidence_alignment_score",
            "reliability_cascade_index",
            "structural_validity_gap",
            "real_api_calls",
        ],
    )

    p04_stage_table = _copy_selected_rows(
        p04_stage_rows,
        [
            "condition",
            "n_chains",
            "schema_valid_rate",
            "decision_match_rate",
            "audit_pass_rate",
            "escalation_rate",
            "missing_evidence_acknowledgement_rate",
            "mean_decision_confidence",
            "mean_evidence_alignment_score",
            "real_api_calls",
        ],
    )

    p04_uncertainty_table = _copy_selected_rows(
        p04_uncertainty_rows,
        [
            "condition",
            "n_chains",
            "mean_decision_confidence",
            "low_decision_confidence_rate_lt_0_70",
            "mean_evidence_alignment_score",
            "low_alignment_rate_lt_0_75",
            "human_review_rate",
            "real_api_calls",
        ],
    )

    numeric_metric_inventory = [
        row
        for row in metric_inventory_rows
        if row.get("n_numeric_values") not in {"", "0", 0}
    ]

    compact_metric_inventory = _copy_selected_rows(
        numeric_metric_inventory,
        [
            "source",
            "column_name",
            "n_rows",
            "n_numeric_values",
            "mean_numeric_value",
            "min_numeric_value",
            "max_numeric_value",
            "real_api_calls",
        ],
    )

    return {
        "table_01_framework_summary": framework_table,
        "table_02_validation_status": validation_table,
        "table_03_condition_metric_alignment": condition_alignment_table,
        "table_04_pilot04_reliability_by_condition": p04_reliability_table,
        "table_05_pilot04_stage_cascade_summary": p04_stage_table,
        "table_06_pilot04_uncertainty_summary": p04_uncertainty_table,
        "table_07_metric_inventory_compact": compact_metric_inventory,
    }


def _write_tables(tables: dict[str, list[dict[str, Any]]]) -> dict[str, Path]:
    table_paths: dict[str, Path] = {}

    for table_name, rows in tables.items():
        path = TABLE_DIR / f"{table_name}.csv"
        _write_csv(path, rows)
        table_paths[table_name] = path

    return table_paths


def _build_figures(tables: dict[str, list[dict[str, Any]]]) -> dict[str, Path]:
    figure_paths = {
        "figure_01_validation_steps": FIGURE_DIR / "figure_01_validation_steps.png",
        "figure_02_validation_checks": FIGURE_DIR / "figure_02_validation_checks.png",
        "figure_03_pilot04_reliability_index": FIGURE_DIR / "figure_03_pilot04_reliability_index.png",
        "figure_04_pilot04_structural_gap": FIGURE_DIR / "figure_04_pilot04_structural_gap.png",
        "figure_05_pilot04_escalation_rate": FIGURE_DIR / "figure_05_pilot04_escalation_rate.png",
        "figure_06_metric_inventory_numeric_counts": FIGURE_DIR / "figure_06_metric_inventory_numeric_counts.png",
    }

    validation_rows = tables["table_02_validation_status"]
    no_call_rows = [row for row in validation_rows if row["n_steps"] != ""]
    check_rows = [row for row in validation_rows if row["n_checks"] != ""]

    _save_bar_figure(
        figure_paths["figure_01_validation_steps"],
        [f"{row['pilot_id']} no-call" for row in no_call_rows],
        [_as_int_or_zero(str(row["n_steps"])) for row in no_call_rows],
        "No-call pipeline steps by pilot",
        "Number of steps",
    )

    _save_bar_figure(
        figure_paths["figure_02_validation_checks"],
        [f"{row['pilot_id']} checks" for row in check_rows],
        [_as_int_or_zero(str(row["n_checks"])) for row in check_rows],
        "Committed-output validation checks by pilot",
        "Number of checks",
    )

    p04_rows = tables["table_04_pilot04_reliability_by_condition"]
    labels = [row["condition"] for row in p04_rows]

    _save_line_figure(
        figure_paths["figure_03_pilot04_reliability_index"],
        labels,
        [_as_float(str(row["reliability_cascade_index"])) for row in p04_rows],
        "Pilot 04 reliability-cascade index by evidence condition",
        "Reliability-cascade index",
    )

    _save_bar_figure(
        figure_paths["figure_04_pilot04_structural_gap"],
        labels,
        [_as_float(str(row["structural_validity_gap"])) for row in p04_rows],
        "Pilot 04 structural-validity gap by evidence condition",
        "Structural-validity gap",
    )

    _save_bar_figure(
        figure_paths["figure_05_pilot04_escalation_rate"],
        labels,
        [_as_float(str(row["escalation_rate"])) for row in p04_rows],
        "Pilot 04 escalation rate by evidence condition",
        "Escalation rate",
    )

    metric_rows = tables["table_07_metric_inventory_compact"]
    source_counts: dict[str, int] = {}
    for row in metric_rows:
        source = str(row["source"])
        source_counts[source] = source_counts.get(source, 0) + 1

    _save_bar_figure(
        figure_paths["figure_06_metric_inventory_numeric_counts"],
        list(source_counts.keys()),
        [float(value) for value in source_counts.values()],
        "Numeric metric inventory by source table",
        "Number of numeric columns",
    )

    return figure_paths


def _write_index(
    *,
    tables: dict[str, list[dict[str, Any]]],
    table_paths: dict[str, Path],
    figure_paths: dict[str, Path],
) -> None:
    framework_preview = _markdown_table(
        tables["table_01_framework_summary"],
        ["pilot_id", "domain", "domain_status", "condition_metric_rows", "claim_boundary"],
    )

    validation_preview = _markdown_table(
        tables["table_02_validation_status"],
        ["pilot_id", "status", "n_steps", "n_failed_steps", "n_checks", "n_failed_checks", "real_api_calls"],
    )

    p04_preview = _markdown_table(
        tables["table_04_pilot04_reliability_by_condition"],
        ["condition", "structural_validity_rate", "reliability_cascade_index", "structural_validity_gap"],
    )

    table_lines = "\n".join(f"- {name}: `{path}`" for name, path in table_paths.items())
    figure_lines = "\n".join(f"- {name}: `{path}`" for name, path in figure_paths.items())

    text = f"""# Cross-Pilot Figure and Table Index

## Scope

These tables and figures are generated from committed sanitized outputs only. They support controlled evidence-state reliability reporting across Pilot 03 and Pilot 04.

They do not export prompt text, raw model outputs, or secret values.

## Tables

{table_lines}

## Figures

{figure_lines}

## Framework summary preview

{framework_preview}

## Validation summary preview

{validation_preview}

## Pilot 04 reliability-condition preview

{p04_preview}

## Safe interpretation

The tables and figures support a controlled measurement claim: structural validity and reliability-layer behaviour can be represented separately across the current evidence-state pipeline outputs.

- real_api_calls: 0
- raw_response_inspection: False
"""

    hits = _public_wording_hits(text)
    if hits:
        raise RuntimeError(f"Public wording safety check failed for table/figure index: {hits}")

    TABLE_INDEX_MD.write_text(text, encoding="utf-8")


def generate_cross_pilot_figures_tables(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    required_inputs = [
        CROSS_FRAMEWORK_CSV,
        CROSS_VALIDATION_CSV,
        CROSS_CONDITION_ALIGNMENT_CSV,
        CROSS_METRIC_INVENTORY_CSV,
        CROSS_REPORT_MANIFEST,
        CROSS_VALIDATION_MANIFEST,
        PILOT_04_RELIABILITY_CSV,
        PILOT_04_STAGE_CASCADE_CSV,
        PILOT_04_UNCERTAINTY_CSV,
    ]

    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required Task 21 inputs: {missing}")

    report_manifest = _load_json(CROSS_REPORT_MANIFEST)
    validation_manifest = _load_json(CROSS_VALIDATION_MANIFEST)

    if report_manifest.get("status") != "PASS":
        raise RuntimeError("Cross-pilot report manifest is not PASS.")
    if validation_manifest.get("status") != "PASS":
        raise RuntimeError("Cross-pilot validation manifest is not PASS.")

    output_dir.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    tables = _build_tables()
    table_paths = _write_tables(tables)
    figure_paths = _build_figures(tables)
    _write_index(tables=tables, table_paths=table_paths, figure_paths=figure_paths)

    for figure_name, figure_path in figure_paths.items():
        if not figure_path.exists():
            raise FileNotFoundError(f"Missing generated figure: {figure_path}")
        if figure_path.stat().st_size < 1000:
            raise RuntimeError(f"Generated figure appears too small: {figure_name} -> {figure_path.stat().st_size} bytes")

    index_text = TABLE_INDEX_MD.read_text(encoding="utf-8")
    wording_hits = _public_wording_hits(index_text)
    if wording_hits:
        raise RuntimeError(f"Public wording safety check failed: {wording_hits}")

    row_counts = {name: len(rows) for name, rows in tables.items()}

    manifest = {
        "artifact": "cross_pilot_figures_tables",
        "status": "PASS",
        "created_at_utc": _load_existing_created_at(MANIFEST_JSON),
        "generator": "experiments.generate_cross_pilot_figures_tables",
        "source_manifests": [
            str(CROSS_REPORT_MANIFEST),
            str(CROSS_VALIDATION_MANIFEST),
        ],
        "row_counts": row_counts,
        "n_tables": len(table_paths),
        "n_figures": len(figure_paths),
        "table_files": [str(path) for path in table_paths.values()],
        "figure_files": [str(path) for path in figure_paths.values()],
        "index_file": str(TABLE_INDEX_MD),
        "public_wording_safety_check": "PASS",
        "public_wording_hits": wording_hits,
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }

    _write_json(MANIFEST_JSON, manifest)
    return manifest


def main() -> None:
    manifest = generate_cross_pilot_figures_tables()
    print("Cross-pilot figures and tables generated.")
    print(f"output_dir: {OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"n_tables: {manifest['n_tables']}")
    print(f"n_figures: {manifest['n_figures']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")


if __name__ == "__main__":
    main()
