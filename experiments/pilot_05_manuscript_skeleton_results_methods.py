from __future__ import annotations

import csv
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TASK_ID = "05AU"
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REL = "experiments/pilot_05_manuscript_skeleton_results_methods.py"
OUTPUT_DIR_REL = "reports/pilot_05_manuscript_skeleton_results_methods"
OUTPUT_DIR = REPO_ROOT / OUTPUT_DIR_REL

EXPECTED_OUTPUT_NAMES = [
    "pilot_05AU_manifest.json",
    "pilot_05AU_source_file_index.csv",
    "pilot_05AU_manuscript_skeleton.md",
    "pilot_05AU_methods_section_draft.md",
    "pilot_05AU_results_section_draft.md",
    "pilot_05AU_contribution_novelty_framing.md",
    "pilot_05AU_claim_boundary_and_limitations.md",
    "pilot_05AU_table_figure_callouts.md",
    "pilot_05AU_title_abstract_keywords.md",
    "pilot_05AU_reproducibility_statement.md",
    "pilot_05AU_next_revision_roadmap.md",
    "pilot_05AU_manuscript_synthesis_report.md",
]

EXPECTED_OUTPUTS = [f"{OUTPUT_DIR_REL}/{name}" for name in EXPECTED_OUTPUT_NAMES]
EXPECTED_UNTRACKED_05AU = {SCRIPT_REL, *EXPECTED_OUTPUTS}

SOURCE_FILES = [
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_manifest.json",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_headline_empirical_findings.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_parser_vs_evidence_state_divergence.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_audit_escalation_interpretation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_cascade_failure_interpretation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_failure_family_interpretation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_claim_boundary_table.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_limitations_and_validity_threats.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_figure_specifications.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_metric_validation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_sanitized_input_file_index.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_results_section_outline.md",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_report.md",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_manifest.json",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_input_file_index.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.md",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.tex",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_audit_escalation_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_cascade_failure_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_failure_family_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_claim_boundary_table_final.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_limitations_and_validity_threats_final.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_metric_validation_summary.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_caption_pack.md",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_table_pack.md",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_assets_report.md",
    "reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_manifest.json",
    "reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_repo_validation_reproducibility_report.md",
]

SOURCE_FIGURES = [
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png",
]

REQUIRED_SAFETY_FLAGS = [
    "no_api_calls",
    "no_model_calls",
    "no_env_read",
    "no_raw_prompt_response_access",
    "no_jsonl_written",
    "no_raw_cfpb_data_touched",
]

SAFETY_FLAGS = {
    "no_api_calls": True,
    "no_model_calls": True,
    "no_env_read": True,
    "no_raw_prompt_response_access": True,
    "no_jsonl_written": True,
    "no_raw_cfpb_data_touched": True,
}

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
    "Q1 acceptance or paper completion",
]

SAFE_CLAIM = (
    "Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled "
    "evidence-state degradation produces measurable reliability-layer changes across decision, audit, "
    "and escalation stages. In this run, parser validity improved under degraded evidence while "
    "stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity."
)


class SynthesisError(RuntimeError):
    pass


def normalize(path: str) -> str:
    return path.replace("\\", "/")


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


def git_tracked(path: str) -> bool:
    return bool(run_git(["ls-files", "--", path]).strip())


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
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


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(read_text(path))


def rows_to_markdown(rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None, limit: Optional[int] = None) -> str:
    if limit is not None:
        rows = rows[:limit]

    if not rows:
        return "_No rows._\n"

    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

    def fmt(value: Any) -> str:
        value = "" if value is None else str(value)
        return value.replace("\n", " ").replace("|", "\\|")

    lines = [
        "| " + " | ".join(fieldnames) + " |",
        "| " + " | ".join(["---"] * len(fieldnames)) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col, "")) for col in fieldnames) + " |")

    return "\n".join(lines) + "\n"


def extract_number(patterns: List[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def check_checkpoint() -> Dict[str, Any]:
    branch = run_git(["branch", "--show-current"])
    latest_commit = run_git(["log", "-1", "--pretty=format:%h %s"])
    latest_hash = run_git(["rev-parse", "--short", "HEAD"])
    latest_subject = run_git(["log", "-1", "--pretty=format:%s"])
    ahead_behind = run_git(["rev-list", "--left-right", "--count", "origin/main...main"])

    staged = [normalize(x) for x in run_git(["diff", "--cached", "--name-only"]).splitlines() if x.strip()]
    modified_tracked = [normalize(x) for x in run_git(["diff", "--name-only"]).splitlines() if x.strip()]
    untracked = [normalize(x) for x in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines() if x.strip()]
    unexpected_untracked = [p for p in untracked if p not in EXPECTED_UNTRACKED_05AU]

    parts = ahead_behind.split()
    behind = int(parts[0]) if len(parts) == 2 else -1
    ahead = int(parts[1]) if len(parts) == 2 else -1

    if branch != "main":
        raise SynthesisError(f"Expected branch main, got {branch}")
    if latest_hash != "725c8dd" or latest_subject != "Add Pilot 05 repo validation audit":
        raise SynthesisError(f"Expected secured 05AT commit 725c8dd, got {latest_commit}")
    if behind != 0 or ahead != 0:
        raise SynthesisError(f"main is not aligned with origin/main: {ahead_behind}")
    if staged:
        raise SynthesisError(f"Unexpected staged files: {staged}")
    if modified_tracked:
        raise SynthesisError(f"Unexpected modified tracked files: {modified_tracked}")
    if unexpected_untracked:
        raise SynthesisError(f"Unexpected untracked files: {unexpected_untracked}")

    return {
        "branch": branch,
        "latest_commit": latest_commit,
        "latest_hash": latest_hash,
        "latest_subject": latest_subject,
        "behind": behind,
        "ahead": ahead,
        "staged_count": len(staged),
        "modified_tracked_count": len(modified_tracked),
        "untracked_count": len(untracked),
        "unexpected_untracked_count": len(unexpected_untracked),
    }


def verify_sources() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for path in SOURCE_FILES + SOURCE_FIGURES:
        full = REPO_ROOT / path
        exists = full.is_file()
        tracked = git_tracked(path)
        size = full.stat().st_size if exists else ""
        rows.append({
            "source_file": path,
            "exists": exists,
            "tracked": tracked,
            "size_bytes": size,
            "status": "PASS" if exists and tracked else "FAIL",
        })

    write_csv(OUTPUT_DIR / "pilot_05AU_source_file_index.csv", rows, ["source_file", "exists", "tracked", "size_bytes", "status"])

    failed = [row for row in rows if row["status"] != "PASS"]
    if failed:
        raise SynthesisError(f"Missing/untracked source files: {failed[:5]}")

    return rows


def verify_manifests() -> Dict[str, Dict[str, Any]]:
    manifest_paths = {
        "05AR": "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_manifest.json",
        "05AS": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_manifest.json",
        "05AT": "reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_manifest.json",
    }

    manifests: Dict[str, Dict[str, Any]] = {}
    for label, path in manifest_paths.items():
        manifest = read_json(REPO_ROOT / path)
        manifests[label] = manifest

        if manifest.get("status") != "PASS":
            raise SynthesisError(f"{label} manifest status is not PASS.")

        for flag in REQUIRED_SAFETY_FLAGS:
            value = manifest.get(flag)
            if value is None and isinstance(manifest.get("safety_flags"), dict):
                value = manifest["safety_flags"].get(flag)
            if value is not True:
                raise SynthesisError(f"{label} manifest safety flag missing/false: {flag}")

    return manifests


def load_source_material() -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    csv_paths = {
        "main_table": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.csv",
        "parser_divergence": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv",
        "audit_escalation": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_audit_escalation_figure_data.csv",
        "cascade_failure": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_cascade_failure_figure_data.csv",
        "failure_family": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_failure_family_figure_data.csv",
        "claim_boundary": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_claim_boundary_table_final.csv",
        "limitations": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_limitations_and_validity_threats_final.csv",
        "metric_validation": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_metric_validation_summary.csv",
    }

    for key, path in csv_paths.items():
        data[key] = read_csv(REPO_ROOT / path)

    text_paths = {
        "figure_caption_pack": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_caption_pack.md",
        "paper_table_pack": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_table_pack.md",
        "paper_assets_report": "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_assets_report.md",
        "05AR_report": "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_report.md",
        "05AT_report": "reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_repo_validation_reproducibility_report.md",
    }

    for key, path in text_paths.items():
        data[key] = read_text(REPO_ROOT / path)

    combined = "\n".join(str(value) for value in data.values())
    data["combined_text"] = combined

    return data


def get_empirical_signposts(material: Dict[str, Any]) -> Dict[str, Optional[str]]:
    text = material["combined_text"]

    signposts = {
        "planned_or_ledger_rows": extract_number([r"call_plan_rows[^0-9]*([0-9,]+)", r"ledger_rows[^0-9]*([0-9,]+)", r"planned_call_count[^0-9]*([0-9,]+)"], text),
        "sanitized_execution_rows": extract_number([r"sanitized_execution_rows[^0-9]*([0-9,]+)"], text),
        "cascade_failure_rate": extract_number([r"cascade_failure_rate_all_sequence_groups[^0-9]*([0-9.]+)", r"cascade failure[^0-9]*([0-9.]+)"], text),
        "stage_success_delta_min": extract_number([r"stage_success_delta_min[^-0-9]*(-?[0-9.]+)"], text),
        "stage_success_delta_max": extract_number([r"stage_success_delta_max[^-0-9]*(-?[0-9.]+)"], text),
        "parser_valid_delta_min": extract_number([r"parser_valid_delta_min[^-0-9]*(-?[0-9.]+)"], text),
        "parser_valid_delta_max": extract_number([r"parser_valid_delta_max[^-0-9]*(-?[0-9.]+)"], text),
        "audit_detection_rate": extract_number([r"audit_detection_rate_degraded_mean[^0-9]*([0-9.]+)"], text),
        "escalation_recovery_rate": extract_number([r"escalation_recovery_rate_degraded_mean[^0-9]*([0-9.]+)"], text),
    }

    return signposts


def paragraph_safe_signposts(signposts: Dict[str, Optional[str]]) -> str:
    parts = []
    if signposts.get("planned_or_ledger_rows"):
        parts.append(f"The committed run is organized around {signposts['planned_or_ledger_rows']} planned/ledgered pipeline calls.")
    if signposts.get("sanitized_execution_rows"):
        parts.append(f"The sanitized execution layer contains {signposts['sanitized_execution_rows']} retained rows after parser and execution accounting.")
    if signposts.get("stage_success_delta_min") and signposts.get("stage_success_delta_max"):
        parts.append(f"The stage-success degradation range is reported as {signposts['stage_success_delta_min']} to {signposts['stage_success_delta_max']}.")
    if signposts.get("parser_valid_delta_min") and signposts.get("parser_valid_delta_max"):
        parts.append(f"The parser-validity delta range is reported as {signposts['parser_valid_delta_min']} to {signposts['parser_valid_delta_max']}.")
    if signposts.get("cascade_failure_rate"):
        parts.append(f"The all-sequence cascade-failure rate is reported as {signposts['cascade_failure_rate']}.")
    if signposts.get("audit_detection_rate"):
        parts.append(f"The degraded audit detection mean is reported as {signposts['audit_detection_rate']}.")
    if signposts.get("escalation_recovery_rate"):
        parts.append(f"The degraded escalation recovery mean is reported as {signposts['escalation_recovery_rate']}.")

    if not parts:
        return "The committed 05AR/05AS tables provide the numeric values used for the manuscript tables and figure callouts; 05AU does not introduce new measurements."

    return " ".join(parts)


def create_title_abstract_keywords(signposts: Dict[str, Optional[str]]) -> str:
    signpost_sentence = paragraph_safe_signposts(signposts)

    return f"""# Pilot 05AU Title, Abstract, and Keywords Draft

## Candidate title options

1. Evidence-State Reliability in Multi-Stage LLM Decision Pipelines
2. When Parser Validity Improves While Evidence Reliability Degrades: A Study of Reliability Cascades in LLM Decision Systems
3. Evidence-State Degradation and Reliability Cascades in Sanitized CFPB-Backed LLM Pipeline Experiments
4. Beyond Output Parsability: Measuring Evidence-State Reliability in Multi-Stage LLM Decision Workflows

## Preferred working title

**Evidence-State Reliability in Multi-Stage LLM Decision Pipelines**

## Structured abstract draft

### Background

LLM evaluation commonly emphasizes final-output validity, parser compliance, or answer-level correctness. In multi-stage decision pipelines, however, downstream outputs may remain parser-valid even when the evidence state reaching the downstream stage has been degraded. This creates a reliability layer that is not fully captured by final-output parsability alone.

### Objective

This study introduces and operationalizes Evidence-State Reliability as a layer of reliability concerned with whether intermediate evidence states remain sufficiently complete, grounded, and usable across a multi-stage LLM decision pipeline.

### Method

Using committed Pilot 05 outputs only, the study analyzes a sanitized, CFPB-backed, scaled GLM-5.2 pipeline experiment with controlled evidence-state degradation. The pipeline separates decision, audit, and escalation stages and compares parser-validity behavior against evidence-state and stage-success metrics. All manuscript artifacts in this package are derived from committed 05AR, 05AS, and 05AT outputs only.

### Results

{signpost_sentence} The central pattern is that parser-validity behavior and evidence-state reliability move in opposite directions under degradation: parser validity improves while stage/evidence success deteriorates. This supports the paper's core claim that parser validity is not a sufficient proxy for evidence-state reliability.

### Contribution

The contribution is a reproducible empirical framing for reliability cascades in multi-stage LLM decision systems. The study distinguishes output parsability from evidence-state reliability, provides paper-ready tables and figures, and supplies explicit claim boundaries for responsible interpretation.

### Limitations

The results are bounded to the committed Pilot 05 GLM-5.2 setup, the sanitized CFPB-backed evidence packets, the specific pipeline stages, and the implemented evidence-state degradation conditions. The study does not claim broad LLM reliability, model/provider superiority, deployment safety, regulatory validity, or real-world consumer harm prevalence.

## Keywords

Evidence-State Reliability; Reliability Cascades; LLM Evaluation; Multi-Stage Decision Pipelines; Parser Validity; Auditability; Escalation; CFPB; Reproducibility; GLM-5.2
"""


def create_manuscript_skeleton(material: Dict[str, Any], signposts: Dict[str, Optional[str]]) -> str:
    return f"""# Pilot 05AU Manuscript Skeleton

## Working title

Evidence-State Reliability in Multi-Stage LLM Decision Pipelines

## Core thesis

{SAFE_CLAIM}

## 1. Introduction

### Problem

Multi-stage LLM decision systems do not only fail at the final answer layer. They can also fail when the evidence state passed from one stage to another becomes degraded, incomplete, or misleading while the downstream output remains structurally parser-valid.

### Gap

Existing evaluation practice often checks whether final outputs are valid, parseable, or apparently complete. That is not enough for decision systems where upstream evidence degradation can propagate downstream and produce reliability cascades.

### Research question

How can Evidence-State Reliability be measured separately from final parser validity in a multi-stage LLM decision pipeline?

### Paper claim

The paper claims that parser-valid output is not sufficient evidence of reliable pipeline behavior. Evidence-state degradation can produce measurable reliability-layer changes even when parser validity improves.

## 2. Conceptual framing

### Evidence-State Reliability

Evidence-State Reliability is the reliability of the intermediate evidence state used by downstream stages in a decision pipeline. It is separate from final-output validity.

### Reliability cascade

A reliability cascade occurs when degradation at one stage changes downstream behavior across decision, audit, or escalation stages.

### Parser validity boundary

Parser validity means the output fits a required schema or parser contract. It does not imply that the evidence used by the pipeline was sufficient, grounded, complete, or decision-reliable.

## 3. Study design

### Pipeline stages

The study separates decision, audit, and escalation stages.

### Conditions

The committed Pilot 05 experiment compares controlled evidence-state degradation against non-degraded evidence-state conditions.

### Data boundary

The experiment uses sanitized CFPB-backed evidence packets and committed derived outputs only. 05AU does not inspect raw CFPB data and does not create new empirical evidence.

### Model boundary

The empirical results are bounded to the committed GLM-5.2 Pilot 05 run.

## 4. Measures

### Parser-validity measures

Parser-validity metrics track whether model outputs satisfy the required parser/schema contract.

### Evidence-state and stage-success measures

Evidence-state and stage-success metrics track whether the pipeline retains useful evidence across stages.

### Cascade measures

Cascade measures track whether degradation propagates across decision, audit, and escalation stages.

## 5. Results

### Main result

{paragraph_safe_signposts(signposts)}

### Interpretation

The main result is a divergence between parser validity and evidence-state reliability under degradation. This is the head-turning empirical pattern: the system can look more parser-valid while becoming less reliable at the evidence-state level.

### Figure structure

- Figure 1: Parser validity versus evidence-state divergence.
- Figure 2: Audit and escalation interpretation.
- Figure 3: Cascade failure rate.
- Figure 4: Failure-family interpretation.

## 6. Discussion

### Why this matters

The results show why parser validity alone is unsafe as a reliability signal in multi-stage LLM decision systems. A system can satisfy output-format requirements while losing reliability in the evidence passed through the pipeline.

### Contribution

The paper contributes a concrete reliability layer, a reproducible empirical pipeline, paper-ready figures/tables, and explicit claim boundaries.

## 7. Limitations

The study is bounded to the committed Pilot 05 design and does not claim broad generalization beyond this setup.

## 8. Reproducibility

The committed repository contains the scaled results interpretation, paper figure/table assets, and repo-wide validation audit. 05AU is a synthesis artifact built only from those committed outputs.

## 9. Conclusion

Evidence-State Reliability should be evaluated separately from parser validity in multi-stage LLM decision systems. The Pilot 05 evidence supports this distinction and motivates reliability audits that track evidence-state degradation across pipeline stages.
"""


def create_methods_section(material: Dict[str, Any], signposts: Dict[str, Optional[str]]) -> str:
    main_table_md = rows_to_markdown(material["main_table"], limit=12)
    metric_validation_md = rows_to_markdown(material["metric_validation"], limit=12)

    return f"""# Pilot 05AU Methods Section Draft

## Study design

This study evaluates Evidence-State Reliability in a multi-stage LLM decision pipeline. The pipeline is organized around decision, audit, and escalation stages. The empirical design compares pipeline behavior under controlled evidence-state degradation against behavior under non-degraded evidence-state conditions.

## Data and evidence-state boundary

The study uses sanitized CFPB-backed evidence packets and committed derived outputs only. The manuscript synthesis does not read raw CFPB data, raw model prompts, raw model responses, JSONL model-output files, or environment/API-key material.

## Model and execution boundary

The empirical execution summarized here is bounded to the committed GLM-5.2 Pilot 05 run. The synthesis does not make API calls or model calls.

## Pipeline stages

1. **Decision stage**: produces an initial downstream decision/assessment from the evidence state.
2. **Audit stage**: evaluates whether the evidence and decision state should trigger detection or concern.
3. **Escalation stage**: evaluates whether downstream recovery or escalation behavior succeeds under degraded evidence conditions.

## Metrics

The study separates parser-validity metrics from evidence-state and stage-success metrics.

### Parser-validity metrics

Parser-validity metrics measure whether outputs satisfy the expected parser/schema contract. These metrics are useful for execution accounting but are not treated as evidence of substantive decision reliability.

### Evidence-state and stage-success metrics

Evidence-state and stage-success metrics measure whether evidence remains usable across the pipeline stages.

### Cascade metrics

Cascade metrics measure whether reliability degradation propagates across decision, audit, and escalation layers.

## Committed main table used by this synthesis

{main_table_md}

## Metric validation table used by this synthesis

{metric_validation_md}

## Reproducibility controls

The committed 05AT audit verifies the repo checkpoint, committed file contracts, manifest safety flags, operation-aware script safety scan, forbidden-file audit, figure integrity, input-index validation, and claim-boundary audit. 05AU uses these committed artifacts as its source boundary.

## No-new-evidence rule

05AU is a manuscript synthesis task. It does not create new empirical results. All methodological and results-language in this package must trace back to committed 05AR, 05AS, or 05AT artifacts.
"""


def create_results_section(material: Dict[str, Any], signposts: Dict[str, Optional[str]]) -> str:
    parser_md = rows_to_markdown(material["parser_divergence"], limit=12)
    audit_md = rows_to_markdown(material["audit_escalation"], limit=12)
    cascade_md = rows_to_markdown(material["cascade_failure"], limit=12)
    family_md = rows_to_markdown(material["failure_family"], limit=12)

    return f"""# Pilot 05AU Results Section Draft

## Results overview

{paragraph_safe_signposts(signposts)}

The central empirical finding is a divergence between parser validity and evidence-state reliability. Under controlled evidence-state degradation, parser validity improves while stage/evidence success deteriorates. This means parser validity cannot be used as a sufficient proxy for reliability in this pipeline.

## Result 1: Parser validity diverges from evidence-state reliability

The committed parser-versus-evidence-state table supports the paper's main contrast: parser-validity behavior and evidence-state reliability do not move together under degradation.

{parser_md}

### Interpretation

This is the central head-turning result. A system may become more parser-valid under degraded evidence while becoming less reliable at the evidence-state layer. That pattern is exactly why Evidence-State Reliability needs to be measured separately from final-output parser validity.

## Result 2: Audit and escalation expose downstream cascade behavior

The audit and escalation outputs show how degradation affects downstream pipeline behavior after the initial decision stage.

{audit_md}

### Interpretation

The audit/escalation layer is important because a downstream stage may detect degradation without recovering from it. The distinction between detection and recovery should be explicit in the paper.

## Result 3: Cascade failure rate summarizes pipeline-level reliability loss

The cascade-failure output provides a pipeline-level view of how often reliability loss propagates across sequence groups.

{cascade_md}

### Interpretation

Cascade failure should be framed as a pipeline reliability phenomenon, not as a model-general claim. The study shows this behavior within the committed Pilot 05 design.

## Result 4: Failure-family interpretation clarifies where degradation concentrates

The failure-family interpretation separates different kinds of reliability failures instead of collapsing them into a single final-output score.

{family_md}

### Interpretation

Failure-family structure helps make the paper stronger because it shows that reliability loss is not monolithic. Different pipeline stages and reliability layers can fail in different ways.

## Results claim boundary

The results support the Evidence-State Reliability distinction within the committed Pilot 05 GLM-5.2 experiment. They do not establish broad GLM reliability, general LLM reliability, real-world financial validity, regulatory validity, deployment safety, or consumer harm prevalence.
"""


def create_contribution_framing() -> str:
    return f"""# Pilot 05AU Contribution and Novelty Framing

## One-sentence contribution

This paper introduces Evidence-State Reliability as a reliability layer separate from parser validity and demonstrates, using a committed sanitized CFPB-backed GLM-5.2 pipeline experiment, that evidence-state degradation can worsen stage reliability even when parser validity improves.

## Main novelty

The novelty is not that LLMs can make mistakes. The novelty is that a multi-stage LLM decision pipeline can become more parser-valid while becoming less reliable at the evidence-state layer. This creates a reliability cascade that final-output parser checks can miss.

## Why this is stronger than a normal LLM evaluation paper

A normal evaluation paper often asks whether the final answer is correct, valid, or parseable. This work asks whether the evidence state passed through the system remains reliable enough for downstream decision, audit, and escalation behavior.

## What the paper contributes

1. **Conceptual layer**: Evidence-State Reliability as distinct from final-output validity.
2. **Empirical pattern**: Parser validity improves under degraded evidence while stage/evidence success deteriorates.
3. **Pipeline framing**: Reliability is measured across decision, audit, and escalation stages.
4. **Cascade framing**: Degradation is treated as a propagated pipeline phenomenon, not only a final-answer problem.
5. **Reproducibility package**: Committed 05AR, 05AS, and 05AT artifacts provide tables, figures, audit outputs, and claim boundaries.

## Strong but safe claim

{SAFE_CLAIM}

## What makes the work potentially head-turning

The result challenges a comfortable assumption: a cleaner, parser-valid output is not necessarily a more reliable decision-system output. In this experiment, parser validity can improve precisely when evidence-state reliability gets worse. That is the paper's strongest empirical and conceptual hook.

## Claim boundary

The contribution is a bounded empirical and methodological contribution. It should not be framed as a universal claim about GLM-5.2, all LLMs, all financial decision systems, or deployment safety.
"""


def create_claim_boundary_and_limitations(material: Dict[str, Any]) -> str:
    claim_md = rows_to_markdown(material["claim_boundary"], limit=20)
    limitations_md = rows_to_markdown(material["limitations"], limit=20)

    do_not = "\n".join(f"- {item}" for item in DO_NOT_CLAIM)

    return f"""# Pilot 05AU Claim Boundary and Limitations

## Safe central claim

{SAFE_CLAIM}

## Do not claim

{do_not}

## Claim-boundary table from committed outputs

{claim_md}

## Limitations table from committed outputs

{limitations_md}

## Validity threats to discuss

### Internal validity

The study depends on the implemented evidence-state degradation design, the parser accounting layer, and the committed pipeline stages. Any manuscript language should stay tied to these implementation details.

### Construct validity

Parser validity is a structural/schema signal. It must not be interpreted as answer correctness. Evidence-State Reliability is a separate construct concerned with evidence usability across pipeline stages.

### External validity

The results are bounded to the committed GLM-5.2 Pilot 05 setup, sanitized CFPB-backed evidence packets, and the specific decision/audit/escalation pipeline design.

### Reproducibility validity

The committed 05AT audit confirms the repo checkpoint and artifact integrity. The paper should describe this as a reproducibility safeguard, not as proof of broad real-world reliability.

## Required wording discipline

Use wording such as:

- "In the committed Pilot 05 setup..."
- "Within this sanitized CFPB-backed GLM-5.2 pipeline experiment..."
- "The results support the distinction between parser validity and Evidence-State Reliability..."
- "The experiment does not establish deployment safety or regulatory validity..."

Avoid wording such as:

- "LLMs are unreliable in financial decisions."
- "GLM-5.2 is unreliable."
- "This proves real-world consumer harm."
- "Parser-valid outputs are wrong."
- "The method is ready for deployment."
"""


def create_table_figure_callouts(material: Dict[str, Any]) -> str:
    captions = material["figure_caption_pack"]
    tables = material["paper_table_pack"]

    return f"""# Pilot 05AU Table and Figure Callouts

## Recommended manuscript table sequence

1. **Table 1 — Main empirical results.** Use `pilot_05AS_final_main_results_table.csv/md/tex`.
2. **Table 2 — Claim boundary and limitations.** Use `pilot_05AS_claim_boundary_table_final.csv` and `pilot_05AS_limitations_and_validity_threats_final.csv`.
3. **Table 3 — Metric validation summary.** Use `pilot_05AS_metric_validation_summary.csv`.

## Recommended manuscript figure sequence

1. **Figure 1 — Parser validity versus evidence-state divergence.**
2. **Figure 2 — Audit and escalation interpretation.**
3. **Figure 3 — Cascade failure rate.**
4. **Figure 4 — Failure-family interpretation.**

## Source caption pack

{captions}

## Source paper table pack

{tables}

## Suggested results-section callout wording

- "Figure 1 shows that parser-validity behavior diverges from evidence-state reliability under degradation."
- "Figure 2 separates audit detection from escalation recovery, preventing detection from being mistaken for recovery."
- "Figure 3 summarizes the pipeline-level cascade-failure pattern."
- "Figure 4 shows that degradation is distributed across failure families rather than reducible to a single output-validity failure."

## Caption discipline

Captions should avoid model-general claims. Every caption should remain bounded to the committed Pilot 05 setup.
"""


def create_reproducibility_statement(meta: Dict[str, Any]) -> str:
    return f"""# Pilot 05AU Reproducibility Statement

## Repository checkpoint

- latest_commit: `{meta["latest_commit"]}`
- latest_hash: `{meta["latest_hash"]}`
- latest_subject: `{meta["latest_subject"]}`
- origin_main_alignment: `{meta["behind"]} behind, {meta["ahead"]} ahead`

## Source artifacts

05AU is derived from committed 05AR, 05AS, and 05AT outputs only.

### 05AR

05AR provides scaled results interpretation outputs, including headline empirical findings, main results tables, parser-versus-evidence-state divergence, audit/escalation interpretation, cascade-failure interpretation, failure-family interpretation, claim boundaries, limitations, figure specifications, and metric validation.

### 05AS

05AS provides paper-ready tables, figure data, four committed figure PNGs, claim-boundary tables, limitations, metric-validation summaries, caption packs, table packs, and paper-asset reporting.

### 05AT

05AT provides the repo-wide validation and reproducibility audit, including committed file contracts, manifest safety checks, operation-aware script safety scanning, forbidden-file audit, figure-integrity audit, input-index validation, and claim-boundary audit.

## Safety boundary

05AU made:

- no API/model calls;
- no `.env` reads;
- no raw prompt/response access;
- no raw CFPB access;
- no JSONL writing.

## Reproduction boundary

05AU is a synthesis layer. It does not regenerate the empirical run. It organizes committed outputs into manuscript-ready structure and wording.
"""


def create_revision_roadmap() -> str:
    return """# Pilot 05AU Next Revision Roadmap

## Immediate next manuscript steps

1. Convert the manuscript skeleton into a full paper draft.
2. Move the Evidence-State Reliability definition into the introduction and formal framing.
3. Use the 05AS final main table as the primary results table.
4. Use the 05AS four-figure package as the primary figure set.
5. Keep all claims bounded to the committed Pilot 05 GLM-5.2 setup.
6. Add a clear subsection explaining why parser validity is not answer correctness.
7. Add a dedicated limitations section using the committed 05AS limitations file.
8. Add a reproducibility section using the committed 05AT audit.

## Strong paper structure

- Introduction: why parser-valid outputs can hide evidence-state degradation.
- Related work: LLM evaluation, reliability, cascading failures, decision-system auditability.
- Conceptual framework: Evidence-State Reliability.
- Methods: sanitized CFPB-backed multi-stage GLM-5.2 pipeline.
- Results: divergence, audit/escalation, cascade failure, failure families.
- Discussion: implications for LLM pipeline evaluation.
- Limitations: bounded claims.
- Reproducibility: committed audit artifacts.

## What not to do yet

- Do not claim Q1 readiness.
- Do not submit before a full literature-grounded related-work section is built.
- Do not expand claims beyond the committed evidence.
- Do not treat parser validity as answer correctness.
- Do not describe this as deployment validation.
"""


def create_report(material: Dict[str, Any], signposts: Dict[str, Optional[str]], meta: Dict[str, Any]) -> str:
    return f"""# Pilot 05AU Manuscript Synthesis Report

## Status

PASS

## Purpose

Task 05AU creates a manuscript skeleton and results-methods synthesis package from committed 05AR, 05AS, and 05AT outputs only.

## Source boundary

- 05AR: scaled results interpretation.
- 05AS: paper figures and final tables.
- 05AT: repo-wide validation and reproducibility audit.

## Git checkpoint

- latest_commit: `{meta["latest_commit"]}`
- latest_hash: `{meta["latest_hash"]}`
- latest_subject: `{meta["latest_subject"]}`
- origin_main_alignment: `{meta["behind"]} behind, {meta["ahead"]} ahead`

## Synthesis summary

{paragraph_safe_signposts(signposts)}

## Central manuscript claim

{SAFE_CLAIM}

## Generated manuscript artifacts

- `pilot_05AU_manuscript_skeleton.md`
- `pilot_05AU_methods_section_draft.md`
- `pilot_05AU_results_section_draft.md`
- `pilot_05AU_contribution_novelty_framing.md`
- `pilot_05AU_claim_boundary_and_limitations.md`
- `pilot_05AU_table_figure_callouts.md`
- `pilot_05AU_title_abstract_keywords.md`
- `pilot_05AU_reproducibility_statement.md`
- `pilot_05AU_next_revision_roadmap.md`

## Safety and claim boundary

05AU does not create new empirical evidence. It does not inspect raw CFPB data, raw prompts, raw responses, JSONL model-output files, or `.env` files. It makes no API/model calls.

## Next step

After 05AU is reviewed and committed, the next task should convert these artifacts into a full manuscript draft package while preserving all claim boundaries.
"""


def output_index() -> List[Dict[str, Any]]:
    rows = []
    for name in EXPECTED_OUTPUT_NAMES:
        path = OUTPUT_DIR / name
        rows.append({
            "output_file": rel(path),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else "",
        })
    return rows


def write_outputs(material: Dict[str, Any], signposts: Dict[str, Optional[str]], meta: Dict[str, Any]) -> None:
    outputs = {
        "pilot_05AU_title_abstract_keywords.md": create_title_abstract_keywords(signposts),
        "pilot_05AU_manuscript_skeleton.md": create_manuscript_skeleton(material, signposts),
        "pilot_05AU_methods_section_draft.md": create_methods_section(material, signposts),
        "pilot_05AU_results_section_draft.md": create_results_section(material, signposts),
        "pilot_05AU_contribution_novelty_framing.md": create_contribution_framing(),
        "pilot_05AU_claim_boundary_and_limitations.md": create_claim_boundary_and_limitations(material),
        "pilot_05AU_table_figure_callouts.md": create_table_figure_callouts(material),
        "pilot_05AU_reproducibility_statement.md": create_reproducibility_statement(meta),
        "pilot_05AU_next_revision_roadmap.md": create_revision_roadmap(),
        "pilot_05AU_manuscript_synthesis_report.md": create_report(material, signposts, meta),
    }

    for name, content in outputs.items():
        (OUTPUT_DIR / name).write_text(content, encoding="utf-8")


def validate_outputs() -> None:
    missing = [name for name in EXPECTED_OUTPUT_NAMES if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise SynthesisError(f"Missing expected 05AU outputs: {missing}")

    required_phrases = {
        "pilot_05AU_manuscript_skeleton.md": ["Evidence-State Reliability", "parser validity", "reliability cascade"],
        "pilot_05AU_methods_section_draft.md": ["sanitized CFPB-backed", "No-new-evidence rule", "GLM-5.2"],
        "pilot_05AU_results_section_draft.md": ["parser validity", "evidence-state reliability", "cascade"],
        "pilot_05AU_claim_boundary_and_limitations.md": ["Do not claim", "deployment safety", "parser validity equals answer correctness"],
        "pilot_05AU_reproducibility_statement.md": ["no API/model calls", "05AT", "committed"],
    }

    for name, phrases in required_phrases.items():
        text = (OUTPUT_DIR / name).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase.lower() not in text.lower():
                raise SynthesisError(f"Required phrase missing from {name}: {phrase}")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    existing = [item.name for item in OUTPUT_DIR.iterdir() if item.is_file()]
    unexpected_existing = [name for name in existing if name not in EXPECTED_OUTPUT_NAMES]
    if unexpected_existing:
        raise SynthesisError(f"Unexpected files in 05AU output directory before generation: {unexpected_existing}")

    meta = check_checkpoint()
    source_rows = verify_sources()
    verify_manifests()
    material = load_source_material()
    signposts = get_empirical_signposts(material)

    write_outputs(material, signposts, meta)

    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_dir": OUTPUT_DIR_REL,
        "git": meta,
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "safety_flags": dict(SAFETY_FLAGS),
        **SAFETY_FLAGS,
        "source_boundary": {
            "committed_outputs_only": True,
            "source_file_count": len(source_rows),
            "source_tasks": ["05AR", "05AS", "05AT"],
            "does_not_create_new_empirical_evidence": True,
        },
        "claim_boundary": {
            "safe_claim": SAFE_CLAIM,
            "do_not_claim": DO_NOT_CLAIM,
        },
        "expected_output_count": len(EXPECTED_OUTPUT_NAMES),
        "outputs": [],
    }

    manifest_path = OUTPUT_DIR / "pilot_05AU_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    validate_outputs()

    manifest["outputs"] = output_index()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print("TASK_05AU_STATUS=PASS")
    print(f"OUTPUT_DIR={OUTPUT_DIR_REL}")
    print(f"EXPECTED_OUTPUT_COUNT={len(EXPECTED_OUTPUT_NAMES)}")
    for row in output_index():
        print(f"OUTPUT_FILE={row['output_file']} SIZE_BYTES={row['size_bytes']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SynthesisError as exc:
        print(f"TASK_05AU_STATUS=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)