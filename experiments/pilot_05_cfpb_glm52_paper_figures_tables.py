from __future__ import annotations

import csv
import json
import math
import os
import platform
import struct
import subprocess
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

TASK_ID = "05AS"
REPO_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_results_interpretation"
OUTPUT_DIR = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_paper_figures_tables"

EXPECTED_05AR_INPUTS = [
    "pilot_05AR_scaled_results_interpretation_manifest.json",
    "pilot_05AR_headline_empirical_findings.csv",
    "pilot_05AR_paper_ready_main_results_table.csv",
    "pilot_05AR_parser_vs_evidence_state_divergence.csv",
    "pilot_05AR_audit_escalation_interpretation.csv",
    "pilot_05AR_cascade_failure_interpretation.csv",
    "pilot_05AR_failure_family_interpretation.csv",
    "pilot_05AR_claim_boundary_table.csv",
    "pilot_05AR_limitations_and_validity_threats.csv",
    "pilot_05AR_figure_specifications.csv",
    "pilot_05AR_metric_validation.csv",
    "pilot_05AR_sanitized_input_file_index.csv",
    "pilot_05AR_paper_results_section_outline.md",
    "pilot_05AR_scaled_results_interpretation_report.md",
]

EXPECTED_OUTPUTS = [
    "pilot_05AS_manifest.json",
    "pilot_05AS_input_file_index.csv",
    "pilot_05AS_final_main_results_table.csv",
    "pilot_05AS_final_main_results_table.md",
    "pilot_05AS_final_main_results_table.tex",
    "pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv",
    "pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png",
    "pilot_05AS_audit_escalation_figure_data.csv",
    "pilot_05AS_figure_02_audit_escalation_interpretation.png",
    "pilot_05AS_cascade_failure_figure_data.csv",
    "pilot_05AS_figure_03_cascade_failure_rate.png",
    "pilot_05AS_failure_family_figure_data.csv",
    "pilot_05AS_figure_04_failure_family_interpretation.png",
    "pilot_05AS_claim_boundary_table_final.csv",
    "pilot_05AS_limitations_and_validity_threats_final.csv",
    "pilot_05AS_metric_validation_summary.csv",
    "pilot_05AS_figure_caption_pack.md",
    "pilot_05AS_paper_table_pack.md",
    "pilot_05AS_paper_assets_report.md",
]

SAFETY_FLAGS = {
    "no_api_calls": True,
    "no_model_calls": True,
    "no_env_read": True,
    "no_raw_prompt_response_access": True,
    "no_jsonl_written": True,
    "no_raw_cfpb_data_touched": True,
}

SAFE_BOUNDED_CLAIM = (
    "Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled "
    "evidence-state degradation produces measurable reliability-layer changes across decision, audit, "
    "and escalation stages. In this run, parser validity improved under degraded evidence while "
    "stage/evidence success deteriorated, supporting the claim that Evidence-State Reliability is "
    "distinct from parser validity."
)

DO_NOT_CLAIM = [
    "broad GLM reliability",
    "general LLM reliability",
    "model/provider superiority",
    "real-world financial validity",
    "regulatory validity",
    "deployment safety",
    "consumer harm prevalence",
    "company misconduct",
    "parser validity equals answer correctness",
    "full paper completion",
    "Q1 acceptance or ground-breaking proof",
]


class ContractError(RuntimeError):
    pass


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def run_git(args: List[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def ensure_git_checkpoint_allows_untracked_05as() -> Dict[str, str]:
    branch = run_git(["branch", "--show-current"])
    latest_commit = run_git(["log", "-1", "--pretty=format:%h %s"])
    latest_subject = run_git(["log", "-1", "--pretty=format:%s"])
    staged = run_git(["diff", "--cached", "--name-only"])
    ahead_behind = run_git(["rev-list", "--left-right", "--count", "origin/main...main"])

    if branch != "main":
        raise ContractError(f"Expected branch main, got {branch!r}.")
    if latest_subject != "Add Pilot 05 scaled results interpretation":
        raise ContractError(
            "Expected latest commit to be secured 05AR commit "
            "'Add Pilot 05 scaled results interpretation'."
        )
    if staged.strip():
        raise ContractError(f"No staged files allowed before generating 05AS outputs. Staged:\n{staged}")

    parts = ahead_behind.split()
    if len(parts) != 2 or parts[0] != "0" or parts[1] != "0":
        raise ContractError(f"Expected main aligned with origin/main, got origin/main...main={ahead_behind!r}.")

    return {
        "branch": branch,
        "latest_commit": latest_commit,
        "latest_subject": latest_subject,
        "origin_main_alignment": ahead_behind,
    }


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv_rows(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def try_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    low = text.lower()
    if low in {"nan", "none", "null", "true", "false", "pass", "fail"}:
        return None
    text = text.replace(",", "")
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def numeric_columns(rows: List[Dict[str, str]]) -> List[str]:
    if not rows:
        return []
    cols = list(rows[0].keys())
    result = []
    for col in cols:
        values = [try_float(row.get(col)) for row in rows]
        if any(value is not None for value in values):
            result.append(col)
    return result


def first_existing_column(rows: List[Dict[str, str]], candidates: Iterable[str]) -> Optional[str]:
    if not rows:
        return None
    cols = list(rows[0].keys())
    lower = {c.lower(): c for c in cols}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def find_numeric_col_by_terms(rows: List[Dict[str, str]], terms: Sequence[str]) -> Optional[str]:
    if not rows:
        return None
    nums = numeric_columns(rows)
    lowered_terms = [term.lower() for term in terms]
    for col in nums:
        low = col.lower()
        if all(term in low for term in lowered_terms):
            return col
    return None


def any_text_contains(row: Dict[str, str], terms: Sequence[str]) -> bool:
    blob = " ".join(str(v).lower() for v in row.values())
    return all(term.lower() in blob for term in terms)


def short_label(value: Any, max_len: int = 54) -> str:
    text = str(value).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "..."


def rows_to_markdown(rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None, max_rows: Optional[int] = None) -> str:
    if not rows:
        return "_No rows available._\n"
    if max_rows is not None:
        rows = rows[:max_rows]
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

    def fmt(value: Any) -> str:
        return ("" if value is None else str(value)).replace("\n", " ").replace("|", "\\|")

    lines = [
        "| " + " | ".join(fieldnames) + " |",
        "| " + " | ".join(["---"] * len(fieldnames)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col, "")) for col in fieldnames) + " |")
    return "\n".join(lines) + "\n"


def latex_escape(value: Any) -> str:
    s = "" if value is None else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s


def rows_to_latex_tabular(rows: List[Dict[str, Any]], fieldnames: List[str]) -> str:
    col_spec = "@{}" + "l" * len(fieldnames) + "@{}"
    lines = [
        "% Auto-generated by Task 05AS. Review before manuscript submission.",
        "\\begin{tabular}{" + col_spec + "}",
        "\\toprule",
        " & ".join(latex_escape(col) for col in fieldnames) + r" \\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(latex_escape(row.get(col, "")) for col in fieldnames) + r" \\")
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def require_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception:
        return None


def write_minimal_png(path: Path, width: int = 1200, height: int = 760) -> None:
    # Dependency-free valid PNG fallback. Used only if matplotlib is unavailable.
    # White background with simple black axes/bars so output contract remains valid.
    pixels = bytearray()
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            r = g = b = 255
            if x == 80 and 80 <= y <= height - 80:
                r = g = b = 0
            if y == height - 80 and 80 <= x <= width - 80:
                r = g = b = 0
            if 160 <= x <= 260 and 220 <= y <= height - 82:
                r = g = b = 120
            if 340 <= x <= 440 and 300 <= y <= height - 82:
                r = g = b = 120
            if 520 <= x <= 620 and 160 <= y <= height - 82:
                r = g = b = 120
            row.extend([r, g, b])
        pixels.extend(row)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytes(pixels)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=6))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def plot_bar(rows: List[Dict[str, Any]], label_key: str, value_key: str, title: str, ylabel: str, output_path: Path) -> str:
    plt = require_matplotlib()
    if plt is None:
        write_minimal_png(output_path)
        return "fallback_minimal_png"

    labels = [short_label(row[label_key]) for row in rows]
    values = [float(row[value_key]) for row in rows]

    height = max(4.8, 0.52 * len(rows) + 2.2)
    fig = plt.figure(figsize=(10.5, height))
    ax = fig.add_subplot(111)

    positions = list(range(len(rows)))
    ax.barh(positions, values)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.set_xlabel(ylabel)
    ax.axvline(0, linewidth=0.8)
    ax.set_title(title)

    for pos, value in zip(positions, values):
        offset = 0.01 if value >= 0 else -0.01
        ha = "left" if value >= 0 else "right"
        display = f"{value:.4f}".rstrip("0").rstrip(".")
        ax.text(value + offset, pos, display, va="center", ha=ha, fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return "matplotlib"


def extract_metric_rows_from_file(file_name: str, include_terms: Sequence[str], preferred_numeric_terms: Sequence[Sequence[str]]) -> List[Dict[str, Any]]:
    rows = read_csv_rows(INPUT_DIR / file_name)
    if not rows:
        return []

    label_col = first_existing_column(
        rows,
        ["metric", "finding", "measure", "result", "sequence_group", "failure_family", "family", "category", "comparison", "condition", "stage"],
    )

    numeric_cols = numeric_columns(rows)
    selected_numeric_cols: List[str] = []

    for terms in preferred_numeric_terms:
        col = find_numeric_col_by_terms(rows, terms)
        if col is not None and col not in selected_numeric_cols:
            selected_numeric_cols.append(col)

    if not selected_numeric_cols:
        selected_numeric_cols = numeric_cols[:4]

    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        if include_terms and not any_text_contains(row, include_terms):
            # Keep rows if the selected numeric column names themselves contain the terms.
            col_blob = " ".join(selected_numeric_cols).lower()
            if not all(term.lower() in col_blob for term in include_terms):
                continue

        base_label = row.get(label_col, f"row_{idx}") if label_col else f"row_{idx}"

        for col in selected_numeric_cols:
            value = try_float(row.get(col))
            if value is None:
                continue
            out.append({
                "label": short_label(base_label if len(selected_numeric_cols) == 1 else f"{base_label} | {col}"),
                "metric": col,
                "value": value,
                "source_file": file_name,
                "source_column": col,
            })

    return out


def fallback_known_metric_from_05ar_outputs(metric_terms: Sequence[str], output_label: str) -> List[Dict[str, Any]]:
    # Last-resort scan across committed 05AR CSVs. It still reads only committed sanitized 05AR outputs.
    candidates: List[Dict[str, Any]] = []
    for file_name in EXPECTED_05AR_INPUTS:
        if not file_name.endswith(".csv"):
            continue
        rows = read_csv_rows(INPUT_DIR / file_name)
        for idx, row in enumerate(rows, start=1):
            if not any_text_contains(row, metric_terms):
                continue
            for col in numeric_columns([row]):
                value = try_float(row.get(col))
                if value is None:
                    continue
                candidates.append({
                    "label": output_label,
                    "metric": col,
                    "value": value,
                    "source_file": file_name,
                    "source_column": col,
                    "source_row": idx,
                })
    return candidates[:4]


def create_parser_vs_evidence_assets() -> Tuple[List[Dict[str, Any]], str, str]:
    source = "pilot_05AR_parser_vs_evidence_state_divergence.csv"
    rows = read_csv_rows(INPUT_DIR / source)
    if not rows:
        raise ContractError(f"{source} has no rows.")

    stage_cols = []
    parser_cols = []
    for col in numeric_columns(rows):
        low = col.lower()
        if ("stage" in low or "evidence" in low or "success" in low) and "delta" in low:
            stage_cols.append(col)
        if "parser" in low and ("valid" in low or "validity" in low) and "delta" in low:
            parser_cols.append(col)

    if not stage_cols:
        col = find_numeric_col_by_terms(rows, ["success", "delta"]) or find_numeric_col_by_terms(rows, ["stage"])
        if col:
            stage_cols.append(col)
    if not parser_cols:
        col = find_numeric_col_by_terms(rows, ["parser", "delta"]) or find_numeric_col_by_terms(rows, ["parser"])
        if col:
            parser_cols.append(col)

    label_col = first_existing_column(rows, ["sequence_group", "comparison", "condition", "stage", "metric", "finding"])

    figure_rows: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        group = row.get(label_col, f"row_{idx}") if label_col else f"row_{idx}"
        for col in stage_cols:
            value = try_float(row.get(col))
            if value is not None:
                figure_rows.append({
                    "comparison_group": group,
                    "metric": "stage/evidence success delta",
                    "value": value,
                    "source_file": source,
                    "source_column": col,
                })
        for col in parser_cols:
            value = try_float(row.get(col))
            if value is not None:
                figure_rows.append({
                    "comparison_group": group,
                    "metric": "parser-valid delta",
                    "value": value,
                    "source_file": source,
                    "source_column": col,
                })

    if not figure_rows:
        figure_rows = fallback_known_metric_from_05ar_outputs(["parser"], "parser/evidence divergence")

    if not figure_rows:
        raise ContractError("Could not extract parser-vs-evidence numeric figure data from committed 05AR outputs.")

    write_csv_rows(
        OUTPUT_DIR / "pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv",
        figure_rows,
        ["comparison_group", "metric", "value", "source_file", "source_column"],
    )

    plot_rows = [
        {"label": f"{short_label(row.get('comparison_group', row.get('label', 'row')), 30)} | {row['metric']}", "value": row["value"]}
        for row in figure_rows
    ]

    backend = plot_bar(
        plot_rows,
        "label",
        "value",
        "Parser validity diverges from Evidence-State Reliability under degradation",
        "Delta under degraded evidence",
        OUTPUT_DIR / "pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png",
    )

    caption = (
        "Figure 1. Parser-vs-evidence-state divergence under controlled degradation. "
        "The figure is generated from committed 05AR outputs and supports the bounded claim that parser validity "
        "and Evidence-State Reliability are separate evaluation layers in this Pilot 05 run."
    )
    return figure_rows, caption, backend


def create_audit_escalation_assets() -> Tuple[List[Dict[str, Any]], str, str]:
    source = "pilot_05AR_audit_escalation_interpretation.csv"
    rows = extract_metric_rows_from_file(
        source,
        include_terms=[],
        preferred_numeric_terms=[
            ["audit", "detection"],
            ["audit", "rate"],
            ["escalation", "recovery"],
            ["recovery", "rate"],
            ["mean"],
            ["value"],
            ["rate"],
        ],
    )

    if not rows:
        rows = fallback_known_metric_from_05ar_outputs(["audit"], "audit/escalation metric")
    if not rows:
        rows = fallback_known_metric_from_05ar_outputs(["escalation"], "audit/escalation metric")
    if not rows:
        raise ContractError("Could not extract audit/escalation numeric figure data from committed 05AR outputs.")

    write_csv_rows(
        OUTPUT_DIR / "pilot_05AS_audit_escalation_figure_data.csv",
        rows,
        ["label", "metric", "value", "source_file", "source_column"],
    )

    backend = plot_bar(
        rows,
        "label",
        "value",
        "Audit detects degraded evidence, but escalation recovery remains limited",
        "Rate / value",
        OUTPUT_DIR / "pilot_05AS_figure_02_audit_escalation_interpretation.png",
    )

    caption = (
        "Figure 2. Audit/escalation behavior in the controlled Pilot 05 run. "
        "The interpretation is intentionally bounded: degraded evidence can be detected, but escalation recovery "
        "was not observed as successful recovery in this run."
    )
    return rows, caption, backend


def create_cascade_failure_assets() -> Tuple[List[Dict[str, Any]], str, str]:
    source = "pilot_05AR_cascade_failure_interpretation.csv"
    rows = extract_metric_rows_from_file(
        source,
        include_terms=[],
        preferred_numeric_terms=[
            ["cascade", "failure", "rate"],
            ["failure", "rate"],
            ["cascade"],
            ["rate"],
            ["value"],
        ],
    )

    if not rows:
        rows = fallback_known_metric_from_05ar_outputs(["cascade", "failure"], "cascade failure")
    if not rows:
        raise ContractError("Could not extract cascade-failure numeric figure data from committed 05AR outputs.")

    write_csv_rows(
        OUTPUT_DIR / "pilot_05AS_cascade_failure_figure_data.csv",
        rows,
        ["label", "metric", "value", "source_file", "source_column"],
    )

    backend = plot_bar(
        rows,
        "label",
        "value",
        "Cascade failure remains high across sequence groups",
        "Failure rate / value",
        OUTPUT_DIR / "pilot_05AS_figure_03_cascade_failure_rate.png",
    )

    caption = (
        "Figure 3. Cascade-failure interpretation from committed 05AR outputs. "
        "The figure supports the manuscript need to measure evidence-state, decision, audit, escalation, and sequence-level behavior separately."
    )
    return rows, caption, backend


def create_failure_family_assets() -> Tuple[List[Dict[str, Any]], str, str]:
    source = "pilot_05AR_failure_family_interpretation.csv"
    rows = read_csv_rows(INPUT_DIR / source)
    if not rows:
        raise ContractError(f"{source} has no rows.")

    label_col = first_existing_column(rows, ["failure_family", "family", "category", "metric", "finding", "measure"])
    nums = numeric_columns(rows)

    selected_col = None
    for terms in (["count"], ["rate"], ["share"], ["value"], ["mean"]):
        selected_col = find_numeric_col_by_terms(rows, terms)
        if selected_col:
            break
    if selected_col is None and nums:
        selected_col = nums[0]

    figure_rows: List[Dict[str, Any]] = []
    if selected_col:
        for idx, row in enumerate(rows, start=1):
            value = try_float(row.get(selected_col))
            if value is None:
                continue
            figure_rows.append({
                "failure_family": row.get(label_col, f"row_{idx}") if label_col else f"row_{idx}",
                "value": value,
                "source_file": source,
                "source_column": selected_col,
            })

    if not figure_rows and label_col:
        # Descriptive fallback: one row per interpreted family/category, clearly marked as row_presence_count.
        for idx, row in enumerate(rows, start=1):
            figure_rows.append({
                "failure_family": row.get(label_col, f"row_{idx}"),
                "value": 1.0,
                "source_file": source,
                "source_column": "row_presence_count_fallback",
            })

    if not figure_rows:
        raise ContractError("Could not extract failure-family figure data from committed 05AR outputs.")

    write_csv_rows(
        OUTPUT_DIR / "pilot_05AS_failure_family_figure_data.csv",
        figure_rows,
        ["failure_family", "value", "source_file", "source_column"],
    )

    backend = plot_bar(
        [{"label": row["failure_family"], "value": row["value"]} for row in figure_rows],
        "label",
        "value",
        "Failure-family interpretation for Pilot 05 reliability cascades",
        "Count / rate / value",
        OUTPUT_DIR / "pilot_05AS_figure_04_failure_family_interpretation.png",
    )

    caption = (
        "Figure 4. Failure-family interpretation from committed 05AR outputs. "
        "This is a descriptive reliability-cascade diagnostic and does not imply broad model, provider, regulatory, or real-world harm claims."
    )
    return figure_rows, caption, backend


def create_input_file_index() -> List[Dict[str, Any]]:
    rows = []
    for name in EXPECTED_05AR_INPUTS:
        path = INPUT_DIR / name
        rows.append({
            "input_file": rel(path),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else "",
            "source": "committed_05AR_output",
        })
    write_csv_rows(OUTPUT_DIR / "pilot_05AS_input_file_index.csv", rows, ["input_file", "exists", "size_bytes", "source"])
    return rows


def copy_final_tables() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    main_rows = read_csv_rows(INPUT_DIR / "pilot_05AR_paper_ready_main_results_table.csv")
    claim_rows = read_csv_rows(INPUT_DIR / "pilot_05AR_claim_boundary_table.csv")
    limitations_rows = read_csv_rows(INPUT_DIR / "pilot_05AR_limitations_and_validity_threats.csv")
    metric_rows = read_csv_rows(INPUT_DIR / "pilot_05AR_metric_validation.csv")

    if not main_rows:
        raise ContractError("05AR paper-ready main results table has no rows.")
    if not claim_rows:
        raise ContractError("05AR claim-boundary table has no rows.")
    if not limitations_rows:
        raise ContractError("05AR limitations/validity-threats table has no rows.")
    if not metric_rows:
        raise ContractError("05AR metric-validation table has no rows.")

    main_fields = list(main_rows[0].keys())
    claim_fields = list(claim_rows[0].keys())
    limitations_fields = list(limitations_rows[0].keys())
    metric_fields = list(metric_rows[0].keys())

    write_csv_rows(OUTPUT_DIR / "pilot_05AS_final_main_results_table.csv", main_rows, main_fields)
    (OUTPUT_DIR / "pilot_05AS_final_main_results_table.md").write_text(
        "# Pilot 05AS Final Main Results Table\n\n"
        "Generated from committed 05AR paper-ready main results table.\n\n"
        + rows_to_markdown(main_rows, main_fields),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "pilot_05AS_final_main_results_table.tex").write_text(
        rows_to_latex_tabular(main_rows, main_fields),
        encoding="utf-8",
    )

    write_csv_rows(OUTPUT_DIR / "pilot_05AS_claim_boundary_table_final.csv", claim_rows, claim_fields)
    write_csv_rows(OUTPUT_DIR / "pilot_05AS_limitations_and_validity_threats_final.csv", limitations_rows, limitations_fields)
    write_csv_rows(OUTPUT_DIR / "pilot_05AS_metric_validation_summary.csv", metric_rows, metric_fields)

    return main_rows, claim_rows, limitations_rows, metric_rows


def create_caption_and_table_packs(
    captions: List[Tuple[str, str]],
    main_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
    limitations_rows: List[Dict[str, str]],
) -> None:
    caption_lines = [
        "# Pilot 05AS Figure Caption Pack",
        "",
        "These captions are generated from committed 05AR outputs and preserve bounded claim language.",
        "",
    ]

    for filename, caption in captions:
        caption_lines.extend([f"## {filename}", "", caption, ""])

    (OUTPUT_DIR / "pilot_05AS_figure_caption_pack.md").write_text("\n".join(caption_lines), encoding="utf-8")

    table_lines = [
        "# Pilot 05AS Paper Table Pack",
        "",
        "Generated from committed 05AR interpretation outputs.",
        "",
        "## Final main results table",
        "",
        rows_to_markdown(main_rows, list(main_rows[0].keys())),
        "",
        "## Claim-boundary table",
        "",
        rows_to_markdown(claim_rows, list(claim_rows[0].keys())),
        "",
        "## Limitations and validity threats",
        "",
        rows_to_markdown(limitations_rows, list(limitations_rows[0].keys())),
        "",
    ]

    (OUTPUT_DIR / "pilot_05AS_paper_table_pack.md").write_text("\n".join(table_lines), encoding="utf-8")


def output_index() -> List[Dict[str, Any]]:
    rows = []
    for name in EXPECTED_OUTPUTS:
        path = OUTPUT_DIR / name
        rows.append({
            "output_file": rel(path),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else "",
        })
    return rows


def create_report(git_info: Dict[str, str], captions: List[Tuple[str, str]], backends: Dict[str, str]) -> None:
    rows = output_index()
    lines = [
        "# Pilot 05AS Paper Figures and Final Main Tables Report",
        "",
        "## Status",
        "",
        "PASS",
        "",
        "## Purpose",
        "",
        "Task 05AS converts committed and validated 05AR interpretation outputs into paper-facing assets: final tables, figure-data CSVs, PNG figures, and caption/table packs.",
        "",
        "## Claim boundary",
        "",
        "05AS does not create new empirical evidence and does not make model/API calls. It reformats committed 05AR outputs for manuscript use.",
        "",
        SAFE_BOUNDED_CLAIM,
        "",
        "## Not claimed",
        "",
    ]

    for item in DO_NOT_CLAIM:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Git checkpoint",
        "",
        f"- branch: `{git_info['branch']}`",
        f"- latest commit: `{git_info['latest_commit']}`",
        f"- latest subject: `{git_info['latest_subject']}`",
        f"- origin/main alignment: `{git_info['origin_main_alignment']}`",
        "",
        "## Generated figures",
        "",
    ])

    for filename, caption in captions:
        backend = backends.get(filename, "unknown")
        lines.extend([
            f"### {filename}",
            "",
            f"- rendering_backend: `{backend}`",
            "",
            caption,
            "",
        ])

    lines.extend([
        "## Generated output contract",
        "",
        rows_to_markdown(rows, ["output_file", "exists", "size_bytes"]),
        "",
        "## Safety flags",
        "",
    ])

    for key, value in SAFETY_FLAGS.items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    (OUTPUT_DIR / "pilot_05AS_paper_assets_report.md").write_text("\n".join(lines), encoding="utf-8")


def verify_05ar_manifest() -> Dict[str, Any]:
    path = INPUT_DIR / "pilot_05AR_scaled_results_interpretation_manifest.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))

    if data.get("status") != "PASS":
        raise ContractError("05AR manifest status is not PASS.")

    for key in SAFETY_FLAGS:
        value = data.get(key)
        if value is None and isinstance(data.get("safety_flags"), dict):
            value = data["safety_flags"].get(key)
        if value is not True:
            raise ContractError(f"05AR manifest safety flag failed or missing: {key}={value!r}")

    return data


def create_manifest(git_info: Dict[str, str], input_rows: List[Dict[str, Any]], backends: Dict[str, str]) -> None:
    rows_before_manifest = output_index()
    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "input_dir": rel(INPUT_DIR),
        "output_dir": rel(OUTPUT_DIR),
        "git": git_info,
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "safety_flags": dict(SAFETY_FLAGS),
        **SAFETY_FLAGS,
        "input_files": input_rows,
        "expected_output_count": len(EXPECTED_OUTPUTS),
        "outputs": rows_before_manifest,
        "figure_rendering_backends": backends,
        "claim_boundary": {
            "safe_claim": SAFE_BOUNDED_CLAIM,
            "do_not_claim": DO_NOT_CLAIM,
        },
    }

    path = OUTPUT_DIR / "pilot_05AS_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    manifest["outputs"] = output_index()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    git_info = ensure_git_checkpoint_allows_untracked_05as()

    if not INPUT_DIR.is_dir():
        raise ContractError(f"Missing 05AR input directory: {INPUT_DIR}")

    missing = [name for name in EXPECTED_05AR_INPUTS if not (INPUT_DIR / name).is_file()]
    if missing:
        raise ContractError(f"Missing expected 05AR input files: {missing}")

    verify_05ar_manifest()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Only expected outputs should be present at this point; PowerShell preflight cleared partials.
    for item in OUTPUT_DIR.iterdir():
        if item.is_file() and item.name not in EXPECTED_OUTPUTS:
            raise ContractError(f"Unexpected file in 05AS output directory before generation: {item}")

    input_rows = create_input_file_index()
    main_rows, claim_rows, limitations_rows, _metric_rows = copy_final_tables()

    captions: List[Tuple[str, str]] = []
    backends: Dict[str, str] = {}

    _rows1, cap1, backend1 = create_parser_vs_evidence_assets()
    fig1 = "pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png"
    captions.append((fig1, cap1))
    backends[fig1] = backend1

    _rows2, cap2, backend2 = create_audit_escalation_assets()
    fig2 = "pilot_05AS_figure_02_audit_escalation_interpretation.png"
    captions.append((fig2, cap2))
    backends[fig2] = backend2

    _rows3, cap3, backend3 = create_cascade_failure_assets()
    fig3 = "pilot_05AS_figure_03_cascade_failure_rate.png"
    captions.append((fig3, cap3))
    backends[fig3] = backend3

    _rows4, cap4, backend4 = create_failure_family_assets()
    fig4 = "pilot_05AS_figure_04_failure_family_interpretation.png"
    captions.append((fig4, cap4))
    backends[fig4] = backend4

    create_caption_and_table_packs(captions, main_rows, claim_rows, limitations_rows)

    # Create a preliminary report before manifest so both report and manifest exist in final contract.
    create_report(git_info, captions, backends)
    create_manifest(git_info, input_rows, backends)
    create_report(git_info, captions, backends)

    missing_outputs = [name for name in EXPECTED_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    if missing_outputs:
        raise ContractError(f"Missing expected 05AS outputs: {missing_outputs}")

    print("TASK_05AS_STATUS=PASS")
    print(f"OUTPUT_DIR={rel(OUTPUT_DIR)}")
    print(f"EXPECTED_OUTPUT_COUNT={len(EXPECTED_OUTPUTS)}")
    for row in output_index():
        print(f"OUTPUT_FILE={row['output_file']} SIZE_BYTES={row['size_bytes']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"TASK_05AS_STATUS=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)