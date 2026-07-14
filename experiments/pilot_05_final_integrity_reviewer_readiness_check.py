from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

TASK_ID = "05BE"
VERSION = "05BE-INDEPENDENT-INTEGRITY-REVIEW-V1"
EXPECTED_BRANCH = "main"
EXPECTED_HEAD = "b424bdd5708c1102b5c5b053f2f3375a203f39e8"
EXPECTED_HEAD_MESSAGE = "Add Pilot 05 final expanded manuscript"

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_REL = "experiments/pilot_05_final_integrity_reviewer_readiness_check.py"
OUTPUT_DIR = REPO_ROOT / "reports" / "pilot_05_final_integrity_reviewer_readiness"

OUTPUTS = {
    "review": OUTPUT_DIR / "pilot_05BE_independent_integrity_review.md",
    "integrity": OUTPUT_DIR / "pilot_05BE_numerical_citation_integrity_register.csv",
    "reviewer": OUTPUT_DIR / "pilot_05BE_reviewer_readiness_register.csv",
    "verdict": OUTPUT_DIR / "pilot_05BE_submission_readiness_verdict.md",
    "validation": OUTPUT_DIR / "pilot_05BE_internal_validation_report.md",
    "manifest": OUTPUT_DIR / "pilot_05BE_manifest.json",
}

EXPECTED_UNTRACKED = sorted([
    SCRIPT_REL,
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_independent_integrity_review.md",
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_numerical_citation_integrity_register.csv",
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_reviewer_readiness_register.csv",
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_submission_readiness_verdict.md",
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_internal_validation_report.md",
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_manifest.json",
])

SOURCE_SHA256 = {
    "experiments/pilot_05_final_manuscript_writer.py":
        "08234A3967344EF39C4008CE58A3D8C8046363F46F8C2949AA6E4567EE969115",
    "reports/pilot_05_final_manuscript/pilot_05BD_claim_evidence_traceability.csv":
        "AA4E5F2A6648953267D20FA7FCDD877D396B6C00BEE230DBF2A4093C7B48DFA5",
    "reports/pilot_05_final_manuscript/pilot_05BD_final_manuscript.md":
        "ACB96B8400F598B65ACC0E3A4AD2BD133BFF82DE52494848E556F3C1B392A570",
    "reports/pilot_05_final_manuscript/pilot_05BD_internal_validation_report.md":
        "19B920A9C3083B4E4473AA9C4ACF4A505FF656CF98FE14F39DE8945732A9E97F",
    "reports/pilot_05_final_manuscript/pilot_05BD_manifest.json":
        "48FBE35214B9CFF59FB72367596D97E9DA5ABDC82D39F970ED432A4536612071",
    "reports/pilot_05_final_manuscript/pilot_05BD_section_evidence_map.csv":
        "B7F0247E213512957AC937AD48F7A761C38DF331355CE31F44D47E1E56C29601",
    "reports/pilot_05_final_manuscript/pilot_05BD_table_figure_integration_report.md":
        "5F5087FE878DCF4CDD85B3265A007C653F8385C569539B1AE05DBF5DB508D78F",
}

SOURCE_BLOBS = {
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv":
        "06ade2766d6fde3556f35f03fea3c95b522f4e5d",
    "reports/pilot_05_cfpb_glm52_scaled_real_execution_integrity/pilot_05AO_ledger_missing_sanitized_rows.csv":
        "6a77b84da09c485637832018c0cb113e274d4f14",
    "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_condition_stage_interaction.csv":
        "00f88f66d271ed0c88c420be90c8f1e6f2559b7d",
    "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_bootstrap_confidence_intervals.csv":
        "a2139720647b9750e77ce0e72e54aafd0767e224",
    "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_audit_metrics.csv":
        "c9dce06b9bda1f2b49b71dc2027857da525bee58",
    "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_escalation_metrics.csv":
        "82b1b002e02c8068dec04f8cf6f83d37d34ff4f5",
    "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_cascade_sequence_metrics.csv":
        "c756cd24734f4bac16ad9479c8ef0e4b8b87f95e",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv":
        "dab1047692fd3a6410097a1caeeb7b752e18ce12",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_audit_escalation_figure_data.csv":
        "39b363d68b8b2f50f2db9014cd0e54417fa2b0f8",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_cascade_failure_figure_data.csv":
        "56a6ae695c1400e6e427c73f7eb3a04b5e12d7c0",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_failure_family_figure_data.csv":
        "40a3d297fb4d810842a62af97008e2de1bde460b",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png":
        "e17d9a8e153b7d41553f83a1603221ca952e393e",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png":
        "fdfa360cdac143a6cd01965e06c0fb7035857528",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png":
        "29fd1a95876e63f8aed4a0331f9a8427b73a14c4",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png":
        "f9136632ee5a4d5079447d34a00fe3537e6e73f2",
    "reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_section_gap_matrix.csv":
        "db158441e07c7b8e51faf6f7e5df5d403f6756ef",
    "reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_reviewer_risk_register.csv":
        "beefa4d51d813ab1230a4cb1c4210d93e8a75876",
}

PATHS = {
    "manuscript": REPO_ROOT / "reports/pilot_05_final_manuscript/pilot_05BD_final_manuscript.md",
    "manifest": REPO_ROOT / "reports/pilot_05_final_manuscript/pilot_05BD_manifest.json",
    "claim_trace": REPO_ROOT / "reports/pilot_05_final_manuscript/pilot_05BD_claim_evidence_traceability.csv",
    "section_map": REPO_ROOT / "reports/pilot_05_final_manuscript/pilot_05BD_section_evidence_map.csv",
    "integration": REPO_ROOT / "reports/pilot_05_final_manuscript/pilot_05BD_table_figure_integration_report.md",
    "main_results": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv",
    "missing": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_real_execution_integrity/pilot_05AO_ledger_missing_sanitized_rows.csv",
    "condition": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_condition_stage_interaction.csv",
    "bootstrap": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_bootstrap_confidence_intervals.csv",
    "audit": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_audit_metrics.csv",
    "escalation": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_escalation_metrics.csv",
    "cascade": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_cascade_sequence_metrics.csv",
    "fig1_data": REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv",
    "fig2_data": REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_audit_escalation_figure_data.csv",
    "fig3_data": REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_cascade_failure_figure_data.csv",
    "fig4_data": REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_failure_family_figure_data.csv",
}

FIGURE_ASSETS = [
    REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png",
    REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png",
    REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png",
    REPO_ROOT / "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png",
]

TABLE_TITLES = [
    "Table 1. Execution and parser accounting.",
    "Table 2. Condition-by-stage structural and evidence-sensitive outcomes.",
    "Table 3. Nonparametric bootstrap intervals for paired degraded-minus-clean deltas",
    "Table 4. Sequence-level cascade composition.",
]

CITATION_TOKENS = [
    "Ribeiro et al., 2020",
    "Guo et al., 2017",
    "Geng et al., 2023",
    "Ray, 2026",
    "Singh et al., 2026",
    "Liu et al., 2024",
    "Es et al., 2024",
    "Saad-Falcon et al., 2024",
    "Atanasova et al., 2022",
    "Raji et al., 2020",
    "Mozannar and Sontag, 2020",
    "Geifman and El-Yaniv, 2019",
    "Consumer Financial Protection Bureau, 2025",
    "Financial Stability Board, 2017",
    "Financial Stability Board, 2026",
    "Wohlin et al., 2012",
    "Pineau et al., 2021",
    "Motter and Lai, 2002",
    "Xie et al., 2026",
    "Jamshidi et al., 2026",
    "Qiu et al., 2026",
    "Solozobov, 2026",
]

class ContractError(RuntimeError):
    pass

def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")

def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ContractError(f"{label}: expected {expected!r}, got {actual!r}")

def assert_close(actual: float, expected: float, label: str, tol: float = 5e-7) -> None:
    if abs(actual - expected) > tol:
        raise ContractError(f"{label}: expected {expected}, got {actual}")

def verify_starting_state() -> None:
    assert_equal(run_git(["branch", "--show-current"]), EXPECTED_BRANCH, "branch")
    assert_equal(run_git(["rev-parse", "HEAD"]), EXPECTED_HEAD, "HEAD")
    assert_equal(run_git(["log", "-1", "--format=%s"]), EXPECTED_HEAD_MESSAGE, "HEAD message")
    if run_git(["diff", "--name-only"]):
        raise ContractError("Tracked files are modified before 05BE.")
    if run_git(["diff", "--cached", "--name-only"]):
        raise ContractError("Files are staged before 05BE.")
    untracked = sorted(
        line.replace("\\", "/")
        for line in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines()
        if line.strip()
    )
    assert_equal(untracked, [SCRIPT_REL], "initial untracked set")
    if OUTPUT_DIR.exists():
        raise ContractError(f"Output directory already exists: {OUTPUT_DIR}")

def verify_source_contracts() -> None:
    for relative, expected in SOURCE_SHA256.items():
        path = REPO_ROOT / relative
        if not path.is_file():
            raise ContractError(f"Missing source file: {relative}")
        assert_equal(sha256(path), expected, f"SHA-256 {relative}")
    for relative, expected_blob in SOURCE_BLOBS.items():
        path = REPO_ROOT / relative
        if not path.is_file():
            raise ContractError(f"Missing committed source: {relative}")
        actual_blob = run_git(["rev-parse", f"{EXPECTED_HEAD}:{relative}"])
        assert_equal(actual_blob, expected_blob, f"git blob {relative}")
    for asset in FIGURE_ASSETS:
        if not asset.is_file():
            raise ContractError(f"Missing figure asset: {asset.relative_to(REPO_ROOT)}")
        data = asset.read_bytes()
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            raise ContractError(f"Invalid PNG signature: {asset.relative_to(REPO_ROOT)}")
        width, height = struct.unpack(">II", data[16:24])
        if width < 600 or height < 300:
            raise ContractError(
                f"Figure asset dimensions too small: {asset.name} {width}x{height}"
            )

def verify_numerical_sources() -> dict[str, Any]:
    main = {row["metric"]: row["value"] for row in read_csv(PATHS["main_results"])}
    expected_main = {
        "call_plan_rows": 720,
        "ledger_rows": 720,
        "sanitized_execution_rows": 713,
        "parser_invalid_summary_rows": 243,
        "ledger_parser_valid_true": 470,
        "ledger_parser_valid_false": 250,
        "persisted_parser_valid_true": 470,
        "persisted_parser_valid_false": 243,
        "ledger_only_missing_sanitized_rows": 7,
    }
    for key, value in expected_main.items():
        assert_equal(int(float(main[key])), value, f"main result {key}")
    assert_close(float(main["max_cumulative_estimated_cost_usd"]), 2.2731216, "cost", 1e-10)

    condition = read_csv(PATHS["condition"])
    assert_equal(len(condition), 12, "condition-stage row count")
    expected_keys = {
        (condition_name, stage)
        for condition_name in ["clean", "compressed_lossy", "partial_dropout", "noisy_conflicting"]
        for stage in ["decision", "audit", "escalation"]
    }
    actual_keys = {(row["evidence_condition"], row["stage"]) for row in condition}
    assert_equal(actual_keys, expected_keys, "condition-stage key set")

    degraded = [row for row in condition if row["evidence_condition"] != "clean"]
    assert_equal(sum(float(row["parser_valid_delta_vs_clean_same_stage"]) > 0 for row in degraded), 9, "positive condition parser deltas")
    assert_equal(sum(float(row["stage_success_delta_vs_clean_same_stage"]) < 0 for row in degraded), 9, "negative condition stage deltas")
    assert_equal(sum(float(row["stage_success_rate"]) == 0 for row in degraded), 9, "zero degraded stage-success cells")

    bootstrap = read_csv(PATHS["bootstrap"])
    assert_equal(len(bootstrap), 27, "bootstrap row count")
    parser_rows = [row for row in bootstrap if row["metric"] == "parser_valid"]
    stage_rows = [row for row in bootstrap if row["metric"] == "stage_success"]
    adequate_rows = [row for row in bootstrap if row["metric"] == "evidence_state_adequate"]
    assert_equal(len(parser_rows), 9, "parser bootstrap rows")
    assert_equal(len(stage_rows), 9, "stage-success bootstrap rows")
    assert_equal(len(adequate_rows), 9, "evidence-adequacy bootstrap rows")
    assert_equal(sum(float(row["mean_paired_delta_degraded_minus_clean"]) > 0 for row in parser_rows), 9, "positive parser means")
    crossing = [
        row for row in parser_rows
        if float(row["ci_95_low"]) <= 0 <= float(row["ci_95_high"])
    ]
    assert_equal(len(crossing), 3, "parser intervals crossing zero")
    assert_equal({row["degraded_condition"] for row in crossing}, {"partial_dropout"}, "crossing-zero condition")
    assert_equal(sum(float(row["ci_95_high"]) < 0 for row in stage_rows), 9, "stage intervals below zero")
    assert_equal(sum(float(row["ci_95_high"]) < 0 for row in adequate_rows), 9, "adequacy intervals below zero")
    assert_equal({int(row["bootstrap_n"]) for row in bootstrap}, {2000}, "bootstrap resamples")
    assert_equal({int(row["random_seed"]) for row in bootstrap}, {5205}, "bootstrap seed")

    audit = read_csv(PATHS["audit"])
    audit_degraded = [row for row in audit if row["is_degraded_condition"] == "True"]
    assert_equal(len(audit_degraded), 3, "degraded audit rows")
    expected_audit = {
        "compressed_lossy": (48, 48, 1.0, 3, 0.0625),
        "partial_dropout": (41, 41, 1.0, 2, 0.048780),
        "noisy_conflicting": (52, 52, 1.0, 1, 0.019231),
    }
    for row in audit_degraded:
        exp = expected_audit[row["evidence_condition"]]
        assert_equal(int(row["parser_valid_rows"]), exp[0], f"audit parser rows {row['evidence_condition']}")
        assert_equal(int(row["audit_detected_degradation_true"]), exp[1], f"audit detected count {row['evidence_condition']}")
        assert_close(float(row["audit_detection_rate_among_parser_valid"]), exp[2], f"audit detection rate {row['evidence_condition']}")
        assert_equal(int(row["audit_false_assurance_true"]), exp[3], f"audit false assurance count {row['evidence_condition']}")
        assert_close(float(row["audit_false_assurance_rate_among_parser_valid"]), exp[4], f"audit false assurance rate {row['evidence_condition']}", 1e-6)

    escalation = read_csv(PATHS["escalation"])
    clean_esc = next(row for row in escalation if row["evidence_condition"] == "clean")
    assert_equal(int(clean_esc["parser_valid_rows"]), 25, "clean parser-valid escalation rows")
    assert_close(float(clean_esc["escalation_stage_success_rate_among_parser_valid"]), 1.0, "clean escalation success")
    for row in escalation:
        if row["is_degraded_condition"] != "True":
            continue
        assert_close(float(row["escalation_recovery_rate_among_parser_valid"]), 0.0, f"recovery {row['evidence_condition']}")
        assert_close(float(row["escalation_loss_proxy_rate_among_parser_valid"]), 1.0, f"loss proxy {row['evidence_condition']}")

    cascade = read_csv(PATHS["cascade"])
    assert_equal(len(cascade), 5, "cascade rows including ALL")
    all_row = next(row for row in cascade if row["evidence_condition"] == "ALL")
    assert_equal(int(all_row["sequence_groups"]), 240, "cascade sequence groups")
    assert_equal(int(all_row["complete_sequences"]), 234, "complete sequences")
    assert_equal(int(all_row["cascade_failure_count"]), 223, "cascade failures")
    assert_close(float(all_row["cascade_failure_rate"]), 0.929167, "cascade failure rate", 1e-6)
    return {
        "main": main,
        "condition": condition,
        "bootstrap": bootstrap,
        "audit": audit,
        "escalation": escalation,
        "cascade": cascade,
    }

def verify_manuscript() -> dict[str, Any]:
    text = PATHS["manuscript"].read_text(encoding="utf-8")
    if "## References" not in text:
        raise ContractError("References section is missing.")
    body, references = text.split("## References", 1)
    word_count = len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", body, flags=re.UNICODE))
    if not 6320 <= word_count <= 8000:
        raise ContractError(f"Independent body word count outside target: {word_count}")
    reference_lines = [line for line in references.splitlines() if line.strip().startswith("- ")]
    assert_equal(len(reference_lines), 22, "reference count")
    assert_equal(references.count("[Preprint; not peer reviewed.]"), 7, "preprint labels")
    if "[Consultation report; not final guidance.]" not in references:
        raise ContractError("FSB consultation status is not labelled.")

    required_headings = [
        "## Abstract", "## 1. Introduction", "## 2. Related Work",
        "## 3. Methodology", "## 4. Results", "## 5. Discussion",
        "## 6. Limitations", "## 7. Conclusion",
        "## Data and Code Availability", "## References",
    ]
    for heading in required_headings:
        if heading not in text:
            raise ContractError(f"Missing required heading: {heading}")

    for title in TABLE_TITLES:
        if title not in text:
            raise ContractError(f"Missing table title: {title}")

    figure_paths = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    expected_paths = [
        "../pilot_05_cfpb_glm52_paper_figures_tables/" + asset.name
        for asset in FIGURE_ASSETS
    ]
    assert_equal(figure_paths, expected_paths, "figure path/order")

    publication_text = re.sub(r"\]\([^)]+\)", "]", text)
    forbidden = [
        "head-turning", "groundbreaking", "Q1-ready", "first-ever",
        "Task 05", "05BD", "05BC", "05AN", "05AP", "05AS",
    ]
    found = [phrase for phrase in forbidden if phrase.lower() in publication_text.lower()]
    assert_equal(found, [], "forbidden publication phrases")

    for token in CITATION_TOKENS:
        if token not in body:
            raise ContractError(f"Citation token missing from manuscript body: {token}")

    required_claims = [
        "three partial-dropout intervals include zero",
        "223 failures among 240",
        "one GLM-5.2 configuration",
        "not a probability sample",
        "not an independent institutional audit",
        "artifact-level reproducibility",
        "ESR is not defined as the `stage_success` column itself",
        "combination-and-operationalisation differentiation",
    ]
    for claim in required_claims:
        if claim.lower() not in text.lower():
            raise ContractError(f"Required bounded statement missing: {claim}")

    abstract = text.split("## Abstract", 1)[1].split("## 1. Introduction", 1)[0]
    conclusion = text.split("## 7. Conclusion", 1)[1].split("## Data and Code Availability", 1)[0]
    alignment_tokens = [
        "all nine", "three partial-dropout", "audit detection",
        "false assurance", "escalation recovery", "223", "240",
        "one model", "one pipeline",
    ]
    for token in alignment_tokens:
        if token.lower() not in abstract.lower() and token.lower() not in conclusion.lower():
            raise ContractError(f"Abstract/conclusion alignment token absent: {token}")

    return {
        "text": text,
        "body_words_independent": word_count,
        "reference_count": len(reference_lines),
        "table_count": len(TABLE_TITLES),
        "figure_count": len(figure_paths),
        "citation_tokens": len(CITATION_TOKENS),
    }

def inspect_figure_bindings() -> dict[str, Any]:
    fig1 = read_csv(PATHS["fig1_data"])
    fig2 = read_csv(PATHS["fig2_data"])
    fig3 = read_csv(PATHS["fig3_data"])
    fig4 = read_csv(PATHS["fig4_data"])

    fig1_headers = list(fig1[0].keys()) if fig1 else []
    fig1_values = [row.get("value", "") for row in fig1]
    fig1_groups = [row.get("comparison_group", "") for row in fig1]
    fig1_metrics = [row.get("metric", "") for row in fig1]
    fig1_supports_caption = (
        len(fig1) >= 9
        and any("parser" in str(value).lower() for row in fig1 for value in row.values())
        and any(
            "stage" in str(value).lower() or "evidence" in str(value).lower()
            for row in fig1 for value in row.values()
        )
        and any("delta" in header.lower() for header in fig1_headers)
    )
    assert_equal(fig1_supports_caption, False, "known Figure 1 source-data mismatch")
    assert_equal(len(fig1), 4, "Figure 1 source row count")
    assert_equal(fig1_groups, ["", "", "", ""], "Figure 1 empty comparison groups")
    assert_equal(fig1_metrics, ["value", "value", "value", "value"], "Figure 1 metric labels")
    assert_equal(fig1_values, ["243.0", "470.0", "250.0", "470.0"], "Figure 1 values")

    assert_equal(len(fig2), 2, "Figure 2 source rows")
    assert_equal(
        {(row["label"], float(row["value"])) for row in fig2},
        {
            ("audit_detection_rate_degraded_mean", 1.0),
            ("escalation_recovery_rate_degraded_mean", 0.0),
        },
        "Figure 2 source values",
    )
    assert_equal(len(fig3), 1, "Figure 3 source rows")
    assert_close(float(fig3[0]["value"]), 0.929167, "Figure 3 source value", 1e-6)

    assert_equal(len(fig4), 3, "Figure 4 source rows")
    fig4_presence_fallback = all(
        row.get("source_column") == "row_presence_count_fallback"
        and float(row.get("value", 0)) == 1.0
        for row in fig4
    )
    assert_equal(fig4_presence_fallback, True, "Figure 4 presence-fallback encoding")
    return {
        "fig1_supports_caption": False,
        "fig1_rows": len(fig1),
        "fig4_presence_fallback": True,
        "fig2_rows": len(fig2),
        "fig3_rows": len(fig3),
        "fig4_rows": len(fig4),
    }

def numerical_citation_register() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    def add(check_id: str, category: str, item: str, expected: str, status: str = "PASS", note: str = "") -> None:
        rows.append({
            "check_id": check_id,
            "category": category,
            "item": item,
            "expected_or_source_value": expected,
            "status": status,
            "note": note,
        })

    core = [
        ("N001", "planned calls", "720"),
        ("N002", "ledger rows", "720"),
        ("N003", "sanitized execution rows", "713"),
        ("N004", "ledger parser-valid rows", "470"),
        ("N005", "ledger parser-invalid rows", "250"),
        ("N006", "persisted parser-valid rows", "470"),
        ("N007", "persisted parser-invalid rows", "243"),
        ("N008", "ledger-only missing rows", "7"),
        ("N009", "maximum cumulative estimated cost", "USD 2.2731216"),
        ("N010", "condition-stage rows", "12"),
        ("N011", "bootstrap rows", "27"),
        ("N012", "positive parser-validity point estimates", "9/9"),
        ("N013", "parser-validity intervals crossing zero", "3/9; all partial_dropout"),
        ("N014", "stage-success intervals below zero", "9/9"),
        ("N015", "evidence-adequacy intervals below zero", "9/9"),
        ("N016", "bootstrap resamples", "2,000"),
        ("N017", "bootstrap seed", "5205"),
        ("N018", "degraded audit detection", "1.0 in all three conditions"),
        ("N019", "audit false assurance", "3/48; 2/41; 1/52"),
        ("N020", "degraded escalation recovery", "0.0 in all three conditions"),
        ("N021", "degraded escalation loss proxy", "1.0 in all three conditions"),
        ("N022", "cascade failures", "223/240"),
        ("N023", "complete sequences", "234/240"),
        ("N024", "cascade-failure rate", "0.929167"),
        ("N025", "accounting identity", "470+250=720"),
        ("N026", "accounting identity", "470+243=713"),
        ("N027", "accounting identity", "720-713=7"),
        ("N028", "accounting identity", "470-470=0"),
    ]
    for check_id, item, value in core:
        add(check_id, "numerical_integrity", item, value)

    for index in range(1, 13):
        add(f"CELL{index:02d}", "condition_stage_completeness", f"condition-stage row {index}", "source row represented")
    for index in range(1, 28):
        add(f"CI{index:02d}", "bootstrap_completeness", f"bootstrap row {index}", "source row represented")
    for index, token in enumerate(CITATION_TOKENS, 1):
        add(f"CIT{index:02d}", "citation_reference_consistency", token, "citation token and matching reference present")
    add("REF01", "reference_integrity", "reference entries", "22")
    add("REF02", "reference_integrity", "preprint labels", "7")
    add("REF03", "reference_integrity", "FSB consultation status", "consultation report; not final guidance")
    add("TXT01", "manuscript_structure", "body word range", "6,320-8,000")
    add("TXT02", "manuscript_structure", "tables", "4")
    add("TXT03", "manuscript_structure", "figures", "4")
    return rows

def reviewer_readiness_register() -> list[dict[str, Any]]:
    return [
        {"risk_id":"RR-01","priority":"CRITICAL","status":"PASS","independent_finding":"ESR is separated from the stage-success indicator in Methods, Discussion, and Limitations.","required_action":"None before figure repair; retain wording during venue formatting."},
        {"risk_id":"RR-02","priority":"HIGH","status":"PASS","independent_finding":"Low clean parser-validity rates are reported and discussed as a design limitation.","required_action":"Retain transparent baseline discussion."},
        {"risk_id":"RR-03","priority":"HIGH","status":"PASS","independent_finding":"All nine positive point estimates and all three zero-crossing partial-dropout intervals are disclosed.","required_action":"Do not add uniform significance language."},
        {"risk_id":"RR-04","priority":"HIGH","status":"PASS","independent_finding":"Zero degraded stage success is tied to the scoring rule and model-output-coded judgments.","required_action":"Retain construct-validity limitation."},
        {"risk_id":"RR-05","priority":"HIGH","status":"PASS","independent_finding":"Single-model and single-run scope is explicit throughout.","required_action":"Retain bounded generalisation."},
        {"risk_id":"RR-06","priority":"MEDIUM","status":"PASS","independent_finding":"Seven missing rows are counted, located by condition/stage, and excluded rather than imputed.","required_action":"None."},
        {"risk_id":"RR-07","priority":"MEDIUM","status":"PASS","independent_finding":"Artifact reproducibility is distinguished from raw-response replay.","required_action":"Add final release commit or DOI after repair/formatting."},
        {"risk_id":"RR-08","priority":"MEDIUM","status":"PASS","independent_finding":"Audit indicators are explicitly computational and non-institutional.","required_action":"None."},
        {"risk_id":"RR-09","priority":"HIGH","status":"PASS","independent_finding":"Zero recovery is limited to the implemented escalation design.","required_action":"None."},
        {"risk_id":"RR-10","priority":"MEDIUM","status":"PASS","independent_finding":"CFPB provenance is bounded and no complaint-truth or misconduct claim is made.","required_action":"None."},
        {"risk_id":"RR-11","priority":"HIGH","status":"FAIL","independent_finding":"Figure 1's committed source-data file contains four parser-accounting totals (243, 470, 250, 470) with empty comparison groups, not the nine parser-validity and nine stage-success contrasts described by the caption. Figure 4 uses three value=1.0 row-presence fallbacks rather than sequence counts.","required_action":"Regenerate Figure 1 from authoritative condition-stage/bootstrap data; redesign or remove Figure 4; then repeat independent figure binding and visual review."},
        {"risk_id":"RR-12","priority":"HIGH","status":"PASS","independent_finding":"Novelty is framed as bounded combination-and-operationalisation differentiation.","required_action":"Retain no-first-ever boundary."},
    ]

def build_review() -> str:
    return """# Pilot 05BE — Independent Final Integrity and Reviewer-Readiness Review

## Executive verdict

**Audit execution status: PASS**

**Manuscript-text and numerical-integrity status: PASS**

**Figure-integrity status: FAIL**

**Submission-readiness verdict: NOT READY FOR JOURNAL SELECTION OR VENUE FORMATTING**

The final expanded manuscript is substantially stronger than the preceding journal-form draft. Its numerical accounting, condition-by-stage reporting, uncertainty disclosure, construct boundaries, citation set, and reviewer-risk responses are internally coherent and traceable to the committed sanitized evidence base. The independent review nevertheless found a submission-blocking figure-data mismatch that was not detected by the manuscript generator's path-level binding checks.

## 1. What passed independently

- The manuscript remains within the approved 6,320–8,000-word body range.
- All 12 condition-stage cells are present and agree with the authoritative condition-stage table.
- All 27 bootstrap rows are represented.
- All nine parser-validity point estimates are positive; the three partial-dropout intervals that include zero are disclosed.
- All nine stage-success intervals remain below zero.
- Audit detection, false assurance, escalation recovery, missing-row accounting, and 223/240 cascade failures are reported with bounded interpretations.
- The 22-item reference set is present, the seven preprints are labelled, and the FSB 2026 source remains labelled as consultation material.
- ESR is distinguished from parser validity and from its operational stage-success indicator.
- Single-model, single-run, sanitized-evidence, model-output-coded, and artifact-reproducibility limits remain explicit.
- No internal task identifiers, head-turning language, first-ever claim, or global-priority claim appears in publication prose.

## 2. Submission-blocking finding

### FIG-B01 — Figure 1 source data does not support its caption

The manuscript presents Figure 1 as a visual summary of nine positive parser-validity contrasts and nine negative stage-success contrasts. The committed data file bound to that asset contains only four rows. Their comparison-group fields are empty, each metric label is `value`, and the values are 243, 470, 250, and 470. Those are parser-accounting totals, not the condition-stage or bootstrap divergence results described in the caption.

Because Figure 1 visualises the paper's central empirical contrast, path existence and caption order are insufficient. The figure must be regenerated from the authoritative condition-stage or bootstrap table and then checked visually against its caption and the manuscript.

Severity: **BLOCKER**

Required repair:
1. Generate Figure 1 from the nine degraded parser-validity and nine degraded stage-success comparisons.
2. Use explicit condition and stage labels.
3. Preserve the three parser-validity intervals crossing zero where uncertainty is displayed.
4. Bind the new asset to a machine-readable source file whose rows reproduce the plotted values.
5. Repeat independent figure-data and visual-content validation.

## 3. Additional major figure finding

### FIG-M01 — Figure 4 uses row-presence fallback values

The Figure 4 source file contains three qualitative category rows, each with `value=1.0` and `source_column=row_presence_count_fallback`. It does not encode the actual sequence taxonomy reported in Table 4: 143 parser-failure cascades, 71 detected-not-recovered patterns, three audit-false-assurance patterns, six incomplete sequences, and 17 preserved successes.

The manuscript correctly calls Table 4 authoritative and describes Figure 4 as qualitative. Even so, an equal-value bar-like representation risks looking quantitative without carrying the actual counts. Figure 4 should therefore be redesigned from the sequence counts, converted into a clearly non-quantitative conceptual diagram, or removed if it adds no information beyond Table 4.

Severity: **MAJOR**

## 4. Residual editorial actions

These are not empirical blockers:

- Apply the selected journal's reference and URL style only after figure repair passes.
- Add the final release commit, archival DOI, or immutable version to Data and Code Availability after the repaired manuscript is secured.
- During typesetting, confirm that equations, Markdown tables, and figure captions render correctly in the target template.
- Preserve the current uncertainty-aware wording; do not upgrade directional parser-validity findings into uniform significance claims.

## 5. Final assessment

The manuscript's scientific text and reported numerical evidence are ready for a focused figure repair, not for journal formatting yet. No new experiment, model run, raw-data access, or literature search is required. The next task should modify only derivative figure assets, their source-data files, the corresponding manuscript bindings/captions if needed, and the associated validation artifacts. After that repair, an independent recheck should determine whether the project can proceed to journal selection and venue-specific formatting.
"""

def build_verdict() -> str:
    return """# Pilot 05BE — Submission-Readiness Verdict

## Verdict

**NOT_READY_FOR_JOURNAL_SELECTION_OR_VENUE_FORMATTING**

## Decision basis

- Numerical integrity: **PASS**
- Accounting integrity: **PASS**
- Condition-stage completeness: **PASS (12/12)**
- Bootstrap completeness: **PASS (27/27)**
- Citation/reference consistency: **PASS (22 references)**
- Construct and scope discipline: **PASS**
- Reviewer-risk responses: **11 PASS / 1 FAIL**
- Table integration: **PASS**
- Figure integration: **FAIL**

## Blocking issue

Figure 1's committed source-data file does not contain the condition-stage or bootstrap divergence values claimed by its caption. It contains four parser-accounting totals with empty comparison groups. The central visual therefore lacks a valid data-to-caption contract.

## Major issue

Figure 4 uses equal row-presence fallback values rather than the actual sequence-family counts. It should be redesigned, explicitly made conceptual, or removed.

## Required next gate

**FIGURE_REPAIR_AND_INDEPENDENT_REVALIDATION_REQUIRED**

No new empirical evidence, model/provider run, or literature search is required. Journal selection and venue formatting should begin only after the repaired figures and their data bindings pass an independent check.
"""

def build_validation() -> str:
    return """# Pilot 05BE — Internal Validation Report

## Task result

- Audit generation status: **PASS**
- Source checkpoint: `b424bdd5708c1102b5c5b053f2f3375a203f39e8`
- Review version: `05BE-INDEPENDENT-INTEGRITY-REVIEW-V1`
- Final readiness verdict: **NOT_READY_FOR_JOURNAL_SELECTION_OR_VENUE_FORMATTING**

## Independently recomputed contract

- Protected 05BD source files: 7/7 hash-verified
- Authoritative source blob contracts: 17/17 verified
- Condition-stage rows: 12/12
- Bootstrap rows: 27/27
- Parser-validity means positive: 9/9
- Parser-validity intervals crossing zero: 3/9, all partial-dropout
- Stage-success intervals below zero: 9/9
- Evidence-adequacy intervals below zero: 9/9
- Audit degraded-condition rows: 3/3
- Escalation degraded-condition rows: 3/3
- Cascade failures: 223/240
- References: 22
- Citation tokens checked: 22
- Tables: 4
- Figure paths: 4

## Findings

- BLOCKER: 1
- MAJOR: 1
- MODERATE: 0
- MINOR: 2 venue-stage actions
- Reviewer-risk rows: 12
- Reviewer-risk PASS: 11
- Reviewer-risk FAIL: 1

## Safety

- Manuscript modified: NO
- README or earlier reports modified: NO
- Files deleted or overwritten: NO
- Files staged, committed, or pushed: NO
- Experiments run: NO
- Model/API calls: NO
- New literature search: NO
- Raw CFPB data accessed: NO
- `.env` accessed: NO
- Raw prompts/responses accessed: NO
- JSONL accessed or written: NO
- Word/PDF conversion: NO
"""

def build_outputs() -> dict[str, str]:
    integrity_rows = numerical_citation_register()
    reviewer_rows = reviewer_readiness_register()
    write_text(OUTPUTS["review"], build_review())
    write_csv(
        OUTPUTS["integrity"],
        ["check_id", "category", "item", "expected_or_source_value", "status", "note"],
        integrity_rows,
    )
    write_csv(
        OUTPUTS["reviewer"],
        ["risk_id", "priority", "status", "independent_finding", "required_action"],
        reviewer_rows,
    )
    write_text(OUTPUTS["verdict"], build_verdict())
    write_text(OUTPUTS["validation"], build_validation())

    hashes = {
        SCRIPT_REL: sha256(SCRIPT_PATH),
        str(OUTPUTS["review"].relative_to(REPO_ROOT)).replace("\\", "/"): sha256(OUTPUTS["review"]),
        str(OUTPUTS["integrity"].relative_to(REPO_ROOT)).replace("\\", "/"): sha256(OUTPUTS["integrity"]),
        str(OUTPUTS["reviewer"].relative_to(REPO_ROOT)).replace("\\", "/"): sha256(OUTPUTS["reviewer"]),
        str(OUTPUTS["verdict"].relative_to(REPO_ROOT)).replace("\\", "/"): sha256(OUTPUTS["verdict"]),
        str(OUTPUTS["validation"].relative_to(REPO_ROOT)).replace("\\", "/"): sha256(OUTPUTS["validation"]),
    }
    manifest = {
        "task_id": TASK_ID,
        "version": VERSION,
        "status": "PASS",
        "secured_branch": EXPECTED_BRANCH,
        "secured_head": EXPECTED_HEAD,
        "counts": {
            "expected_uncommitted_files": 7,
            "protected_05BD_files": 7,
            "source_blob_contracts": 17,
            "condition_stage_rows": 12,
            "bootstrap_rows": 27,
            "parser_positive_means": 9,
            "parser_ci_crossing_zero": 3,
            "stage_success_ci_below_zero": 9,
            "evidence_adequacy_ci_below_zero": 9,
            "reference_entries": 22,
            "citation_tokens_checked": 22,
            "tables": 4,
            "figures": 4,
            "integrity_register_rows": len(integrity_rows),
            "reviewer_risk_rows": len(reviewer_rows),
            "reviewer_risk_pass": 11,
            "reviewer_risk_fail": 1,
            "blocker_findings": 1,
            "major_findings": 1,
            "moderate_findings": 0,
            "minor_venue_actions": 2,
        },
        "verdict": {
            "manuscript_text_integrity": "PASS",
            "numerical_integrity": "PASS",
            "citation_integrity": "PASS",
            "table_integrity": "PASS",
            "figure_integrity": "FAIL",
            "reviewer_readiness": "FAIL",
            "submission_readiness": "NOT_READY_FOR_JOURNAL_SELECTION_OR_VENUE_FORMATTING",
            "required_next_gate": "FIGURE_REPAIR_AND_INDEPENDENT_REVALIDATION_REQUIRED",
            "new_empirical_evidence_required": False,
            "new_model_run_required": False,
            "new_literature_search_required": False,
        },
        "findings": [
            {
                "finding_id": "FIG-B01",
                "severity": "BLOCKER",
                "summary": "Figure 1 source data does not support its central divergence caption.",
            },
            {
                "finding_id": "FIG-M01",
                "severity": "MAJOR",
                "summary": "Figure 4 uses row-presence fallback values instead of sequence-family counts.",
            },
        ],
        "safety": {
            "manuscript_modified": False,
            "readme_or_earlier_reports_modified": False,
            "files_deleted_or_overwritten": False,
            "files_staged_committed_or_pushed": False,
            "experiments_run": False,
            "model_calls": False,
            "api_calls": False,
            "new_literature_search": False,
            "raw_cfpb_data_accessed": False,
            "env_accessed": False,
            "raw_prompt_response_accessed": False,
            "jsonl_accessed_or_written": False,
            "word_or_pdf_conversion": False,
        },
        "output_sha256": hashes,
    }
    write_text(OUTPUTS["manifest"], json.dumps(manifest, indent=2, sort_keys=True))
    return hashes

def verify_final_state() -> None:
    assert_equal(run_git(["rev-parse", "HEAD"]), EXPECTED_HEAD, "final HEAD")
    if run_git(["diff", "--name-only"]):
        raise ContractError("Tracked files changed during 05BE.")
    if run_git(["diff", "--cached", "--name-only"]):
        raise ContractError("Files were staged during 05BE.")
    untracked = sorted(
        line.replace("\\", "/")
        for line in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines()
        if line.strip()
    )
    assert_equal(untracked, EXPECTED_UNTRACKED, "final untracked set")

def main() -> None:
    verify_starting_state()
    verify_source_contracts()
    verify_numerical_sources()
    verify_manuscript()
    inspect_figure_bindings()

    OUTPUT_DIR.mkdir(parents=False, exist_ok=False)
    hashes = build_outputs()
    verify_final_state()

    print("=== TASK 05BE GENERATION RESULT ===")
    print("status: PASS")
    print(f"version: {VERSION}")
    print(f"source_HEAD: {EXPECTED_HEAD}")
    print("manuscript_text_integrity: PASS")
    print("numerical_integrity: PASS")
    print("citation_integrity: PASS")
    print("table_integrity: PASS")
    print("figure_integrity: FAIL")
    print("reviewer_readiness: FAIL")
    print("submission_readiness: NOT_READY_FOR_JOURNAL_SELECTION_OR_VENUE_FORMATTING")
    print("required_next_gate: FIGURE_REPAIR_AND_INDEPENDENT_REVALIDATION_REQUIRED")
    print("blocker_findings: 1")
    print("major_findings: 1")
    print("condition_stage_rows: 12/12")
    print("bootstrap_rows: 27/27")
    print("references: 22")
    print("reviewer_risks: 11 PASS / 1 FAIL")
    print("new_empirical_evidence_required: NO")
    print("new_model_run_required: NO")
    print("new_literature_search_required: NO")
    print("uncommitted_files: 7")
    print("tracked_files_modified: 0")
    print("staged_files: 0")
    print("")
    print("OUTPUT SHA-256")
    for relative, digest in sorted(hashes.items()):
        print(f"{relative} = {digest}")
    print(f"{OUTPUTS['manifest'].relative_to(REPO_ROOT).as_posix()} = {sha256(OUTPUTS['manifest'])}")
    print("")
    print("STOP: Paste the complete terminal output before any repair, staging, commit, push, journal selection, or venue formatting.")

if __name__ == "__main__":
    main()
