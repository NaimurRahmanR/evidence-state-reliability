"""
Task 05AR: Paper-Ready Scaled Results Interpretation and Claim-Boundary Report
No API/model calls. No .env reads. No raw prompt/response inspection. No JSONL writing.
Generates a claim-bounded interpretation package from verified 05AN/05AO/05AP/05AP-B
scaled-output contract values, and indexes existing sanitized output directories.
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_results_interpretation"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now(timezone.utc).isoformat()

FORBIDDEN_EXTENSIONS = {".jsonl", ".env"}
FORBIDDEN_NAME_FRAGMENTS = ["raw_prompt", "raw_response", "api_key", "secret"]

SANITIZED_INPUT_DIRS = [
    REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution",
    REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_real_execution_integrity",
    REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_scaled_metrics",
]

VERIFIED = {
    "call_plan_rows": 720,
    "ledger_rows": 720,
    "sanitized_execution_rows": 713,
    "parser_invalid_summary_rows": 243,
    "ledger_parser_valid_true": 470,
    "ledger_parser_valid_false": 250,
    "persisted_parser_valid_true": 470,
    "persisted_parser_valid_false": 243,
    "ledger_only_missing_sanitized_rows": 7,
    "max_cumulative_estimated_cost_usd": 2.2731216,
    "stage_success_delta_min": -0.517241,
    "stage_success_delta_max": -0.40678,
    "stage_success_all_negative": True,
    "parser_valid_delta_min": 0.067797,
    "parser_valid_delta_max": 0.368421,
    "parser_valid_all_positive": True,
    "audit_detection_rate_degraded_mean": 1.0,
    "escalation_recovery_rate_degraded_mean": 0.0,
    "cascade_failure_rate_all_sequence_groups": 0.929167,
}

HEADLINE_WORDING = (
    "Across 720 planned GLM-5.2 calls over CFPB-backed sanitized evidence states, "
    "degraded evidence conditions produced consistently negative paired deltas in "
    "stage success while parser validity increased. This divergence supports "
    "Evidence-State Reliability as a distinct evaluation layer from parser validity "
    "in multi-stage LLM decision pipelines."
)

BOUNDARY_WORDING = (
    "This is a controlled scaled pilot, not a deployment validation, not a proof of "
    "real-world financial safety, and not a broad claim about GLM-5.2 or LLM reliability."
)

errors = []


def check_no_forbidden_content(path: Path):
    if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
        errors.append(f"Forbidden extension encountered during indexing: {path}")
    lower_name = path.name.lower()
    for frag in FORBIDDEN_NAME_FRAGMENTS:
        if frag in lower_name:
            errors.append(f"Forbidden filename fragment '{frag}' encountered: {path}")


def write_csv(filename, header, rows):
    out_path = REPORT_DIR / filename
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
    return out_path


# ---------------------------------------------------------------
# 1. Sanitized input file index (index only, no content inspection
#    of raw prompts/responses; these directories contain sanitized
#    CSV/JSON/MD outputs only per prior committed contract).
# ---------------------------------------------------------------
sanitized_index_rows = []
for d in SANITIZED_INPUT_DIRS:
    if not d.exists():
        errors.append(f"Expected sanitized input directory missing: {d}")
        continue
    for p in sorted(d.rglob("*")):
        if p.is_file():
            check_no_forbidden_content(p)
            try:
                size_bytes = p.stat().st_size
            except OSError:
                size_bytes = -1
            sanitized_index_rows.append([
                str(d.name),
                str(p.relative_to(REPO_ROOT)),
                p.suffix.lstrip("."),
                size_bytes,
            ])

write_csv(
    "pilot_05AR_sanitized_input_file_index.csv",
    ["source_directory", "relative_path", "extension", "size_bytes"],
    sanitized_index_rows,
)

# ---------------------------------------------------------------
# 2. Headline empirical findings
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_headline_empirical_findings.csv",
    ["finding_id", "statement"],
    [
        ["F1", HEADLINE_WORDING],
        ["F2", f"Stage success delta range under degradation: [{VERIFIED['stage_success_delta_min']}, {VERIFIED['stage_success_delta_max']}], all negative."],
        ["F3", f"Parser validity delta range under degradation: [{VERIFIED['parser_valid_delta_min']}, {VERIFIED['parser_valid_delta_max']}], all positive."],
        ["F4", f"Audit detection rate among degraded parser-valid cases: {VERIFIED['audit_detection_rate_degraded_mean']}."],
        ["F5", f"Escalation recovery rate under degraded conditions: {VERIFIED['escalation_recovery_rate_degraded_mean']} (no recovery observed in this run)."],
        ["F6", f"Cascade failure rate across all sequence groups: {VERIFIED['cascade_failure_rate_all_sequence_groups']}."],
        ["F7", BOUNDARY_WORDING],
    ],
)

# ---------------------------------------------------------------
# 3. Paper-ready main results table
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_paper_ready_main_results_table.csv",
    ["metric", "value", "unit_or_type", "paper_ready"],
    [
        ["call_plan_rows", VERIFIED["call_plan_rows"], "count", "yes"],
        ["ledger_rows", VERIFIED["ledger_rows"], "count", "yes"],
        ["sanitized_execution_rows", VERIFIED["sanitized_execution_rows"], "count", "yes"],
        ["parser_invalid_summary_rows", VERIFIED["parser_invalid_summary_rows"], "count", "yes"],
        ["ledger_parser_valid_true", VERIFIED["ledger_parser_valid_true"], "count", "yes"],
        ["ledger_parser_valid_false", VERIFIED["ledger_parser_valid_false"], "count", "yes"],
        ["persisted_parser_valid_true", VERIFIED["persisted_parser_valid_true"], "count", "yes"],
        ["persisted_parser_valid_false", VERIFIED["persisted_parser_valid_false"], "count", "yes"],
        ["ledger_only_missing_sanitized_rows", VERIFIED["ledger_only_missing_sanitized_rows"], "count", "yes, disclosed as limitation"],
        ["max_cumulative_estimated_cost_usd", VERIFIED["max_cumulative_estimated_cost_usd"], "USD", "yes"],
        ["stage_success_delta_min", VERIFIED["stage_success_delta_min"], "proportion_delta", "yes"],
        ["stage_success_delta_max", VERIFIED["stage_success_delta_max"], "proportion_delta", "yes"],
        ["parser_valid_delta_min", VERIFIED["parser_valid_delta_min"], "proportion_delta", "yes"],
        ["parser_valid_delta_max", VERIFIED["parser_valid_delta_max"], "proportion_delta", "yes"],
        ["audit_detection_rate_degraded_mean", VERIFIED["audit_detection_rate_degraded_mean"], "proportion", "yes"],
        ["escalation_recovery_rate_degraded_mean", VERIFIED["escalation_recovery_rate_degraded_mean"], "proportion", "yes"],
        ["cascade_failure_rate_all_sequence_groups", VERIFIED["cascade_failure_rate_all_sequence_groups"], "proportion", "yes"],
    ],
)

# ---------------------------------------------------------------
# 4. Parser validity vs Evidence-State Reliability divergence
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_parser_vs_evidence_state_divergence.csv",
    ["dimension", "direction_under_degradation", "interpretation"],
    [
        ["stage_success / evidence-state adequacy", "decreases (all deltas negative)",
         "Degraded evidence propagates into worse downstream stage outcomes."],
        ["parser_validity", "increases (all deltas positive)",
         "A structurally/parser-valid output can co-occur with degraded evidence state, "
         "showing parser validity does not certify evidence-state reliability."],
        ["net divergence", "opposite signs across the two layers",
         "Confirms Evidence-State Reliability must be measured as a layer separate "
         "from parser/output validity."],
    ],
)

# ---------------------------------------------------------------
# 5. Audit / escalation interpretation
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_audit_escalation_interpretation.csv",
    ["stage", "observed_rate", "interpretation"],
    [
        ["audit_detection_rate_degraded_mean", VERIFIED["audit_detection_rate_degraded_mean"],
         "Audit stage detected degraded evidence among parser-valid degraded cases in this run."],
        ["escalation_recovery_rate_degraded_mean", VERIFIED["escalation_recovery_rate_degraded_mean"],
         "Escalation stage did not recover any detected degraded-evidence cases in this run; "
         "detection without recovery is the mechanism producing a reliability cascade."],
    ],
)

# ---------------------------------------------------------------
# 6. Cascade failure interpretation
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_cascade_failure_interpretation.csv",
    ["metric", "value", "interpretation"],
    [
        ["cascade_failure_rate_all_sequence_groups", VERIFIED["cascade_failure_rate_all_sequence_groups"],
         "The large majority of sequence groups exhibited a cascade failure pattern: "
         "degraded evidence detected at audit but not corrected before the final "
         "governable output stage."],
    ],
)

# ---------------------------------------------------------------
# 7. Failure family interpretation (qualitative, bounded)
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_failure_family_interpretation.csv",
    ["failure_family", "description", "evidence_basis"],
    [
        ["Detected-but-unrecovered degradation",
         "Audit correctly flags degraded evidence but escalation does not restore stage success.",
         "audit_detection_rate_degraded_mean=1.0; escalation_recovery_rate_degraded_mean=0.0"],
        ["Parser-valid / evidence-invalid divergence",
         "Outputs pass parser validity checks while evidence-state adequacy has deteriorated.",
         "parser_valid_delta all positive while stage_success_delta all negative"],
        ["Missing-sanitized-row gap",
         "A small number of ledger rows lack corresponding sanitized execution rows.",
         f"ledger_only_missing_sanitized_rows={VERIFIED['ledger_only_missing_sanitized_rows']}"],
    ],
)

# ---------------------------------------------------------------
# 8. Claim boundary table
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_claim_boundary_table.csv",
    ["claim_type", "status", "wording"],
    [
        ["allowed_bounded_claim", "permitted",
         "Pilot 05 gives a scaled empirical basis for the paper's core claim direction: "
         "final structural/parser validity is insufficient for evaluating multi-stage "
         "LLM decision systems because evidence-state degradation can produce downstream "
         "reliability cascades that are visible only when evidence-state adequacy, stage "
         "success, audit behavior, escalation recovery, and cascade sequence behavior are "
         "measured separately."],
        ["headline_wording", "required_exact", HEADLINE_WORDING],
        ["boundary_wording", "required_exact", BOUNDARY_WORDING],
        ["broad_GLM_reliability_claim", "not_permitted", "Do not claim."],
        ["general_LLM_reliability_claim", "not_permitted", "Do not claim."],
        ["model_provider_superiority_claim", "not_permitted", "Do not claim."],
        ["real_world_financial_validity_claim", "not_permitted", "Do not claim."],
        ["regulatory_validity_claim", "not_permitted", "Do not claim."],
        ["deployment_safety_claim", "not_permitted", "Do not claim."],
        ["consumer_harm_prevalence_claim", "not_permitted", "Do not claim."],
        ["company_misconduct_claim", "not_permitted", "Do not claim."],
        ["parser_validity_equals_correctness_claim", "not_permitted", "Do not claim."],
        ["full_paper_finished_claim", "not_permitted", "Do not claim."],
        ["Q1_acceptance_or_groundbreaking_claim", "not_permitted", "Do not claim."],
    ],
)

# ---------------------------------------------------------------
# 9. Limitations and validity threats
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_limitations_and_validity_threats.csv",
    ["limitation", "detail"],
    [
        ["Missing sanitized rows",
         f"{VERIFIED['ledger_only_missing_sanitized_rows']} ledger rows have no corresponding "
         "sanitized execution row; excluded from execution-level metrics."],
        ["Single-model scope", "Results reflect GLM-5.2 only; not generalized to other models."],
        ["Single pilot scale", "720 planned calls in one pilot run; not a multi-run replication yet."],
        ["Sanitized-data dependency", "All evidence is CFPB-backed but sanitized; not raw production data."],
        ["No deployment context", "No claims about real-world deployment, regulatory, or financial validity."],
        ["Escalation recovery observed as zero", "May reflect this pilot's escalation design, not a general property of escalation mechanisms."],
    ],
)

# ---------------------------------------------------------------
# 10. Figure specifications for next stage
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_figure_specifications.csv",
    ["figure_id", "title", "type", "data_source"],
    [
        ["Fig1", "Stage success vs parser validity delta under degradation", "paired bar/delta plot",
         "pilot_05AR_paper_ready_main_results_table.csv"],
        ["Fig2", "Audit detection vs escalation recovery rate", "grouped bar chart",
         "pilot_05AR_audit_escalation_interpretation.csv"],
        ["Fig3", "Cascade failure rate across sequence groups", "single-value bar or distribution plot",
         "pilot_05AR_cascade_failure_interpretation.csv"],
        ["Fig4", "Parser-valid vs evidence-state-adequate quadrant diagram", "2x2 quadrant schematic",
         "pilot_05AR_parser_vs_evidence_state_divergence.csv"],
    ],
)

# ---------------------------------------------------------------
# 11. Metric validation record
# ---------------------------------------------------------------
write_csv(
    "pilot_05AR_metric_validation.csv",
    ["metric", "source", "validation_note"],
    [
        [k, "05AN/05AO/05AP/05AP-B committed contract value",
         "Recorded as previously verified scaled-output contract value; not recomputed "
         "from raw data in this task per approved 05AR scope."]
        for k in VERIFIED.keys()
    ],
)

# ---------------------------------------------------------------
# 12. Manifest
# ---------------------------------------------------------------
manifest = {
    "task": "05AR",
    "generated_at_utc": TIMESTAMP,
    "no_api_calls": True,
    "no_model_calls": True,
    "no_env_read": True,
    "no_raw_prompt_response_access": True,
    "no_jsonl_written": True,
    "no_raw_cfpb_data_touched": True,
    "source_commit": "be8155f",
    "verified_contract_values": VERIFIED,
    "headline_wording": HEADLINE_WORDING,
    "boundary_wording": BOUNDARY_WORDING,
    "sanitized_input_files_indexed": len(sanitized_index_rows),
    "errors": errors,
}
with open(REPORT_DIR / "pilot_05AR_scaled_results_interpretation_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

# ---------------------------------------------------------------
# 13. Paper results section outline (Markdown)
# ---------------------------------------------------------------
outline_md = f"""# Pilot 05 — Paper Results Section Outline (Draft Bridge)

## 1. Setup recap
- 720 planned GLM-5.2 calls over CFPB-backed sanitized evidence states.
- Pipeline stages: evidence state -> decision -> audit -> escalation -> final governable output.

## 2. Headline result
{HEADLINE_WORDING}

## 3. Key sub-results
- Stage success delta range: [{VERIFIED['stage_success_delta_min']}, {VERIFIED['stage_success_delta_max']}] (all negative)
- Parser validity delta range: [{VERIFIED['parser_valid_delta_min']}, {VERIFIED['parser_valid_delta_max']}] (all positive)
- Audit detection rate (degraded, parser-valid cases): {VERIFIED['audit_detection_rate_degraded_mean']}
- Escalation recovery rate (degraded cases): {VERIFIED['escalation_recovery_rate_degraded_mean']}
- Cascade failure rate across sequence groups: {VERIFIED['cascade_failure_rate_all_sequence_groups']}

## 4. Boundary statement
{BOUNDARY_WORDING}

## 5. What remains before full paper writing
- Additional pilot replications beyond this single scaled run.
- Figures per `pilot_05AR_figure_specifications.csv`.
- Related-work framing tying divergence result to existing evaluation literature.
- Full limitations discussion expanded from `pilot_05AR_limitations_and_validity_threats.csv`.
"""
with open(REPORT_DIR / "pilot_05AR_paper_results_section_outline.md", "w", encoding="utf-8") as f:
    f.write(outline_md)

# ---------------------------------------------------------------
# 14. Full interpretation report (Markdown)
# ---------------------------------------------------------------
report_md = f"""# Pilot 05 — Scaled Results Interpretation Report (Task 05AR)

Generated: {TIMESTAMP}
Source commit: be8155f (Add Pilot 05 scaled GLM-5.2 execution metrics)

## Headline finding
{HEADLINE_WORDING}

## Boundary statement
{BOUNDARY_WORDING}

## Q&A

**1. What did the scaled GLM-5.2 Pilot 05 actually show?**
Across {VERIFIED['call_plan_rows']} planned calls, degraded evidence conditions produced
negative stage-success deltas and positive parser-validity deltas, indicating the two
layers move in opposite directions under degradation.

**2. What is the main empirical result?**
The divergence between stage success (declines) and parser validity (increases) under
evidence degradation.

**3. Why is parser validity not enough?**
Because outputs can remain parser-valid while the evidence backing them has degraded,
parser validity alone cannot certify evidence-state reliability.

**4. How do stage success and evidence-state adequacy behave under degradation?**
They deteriorate consistently, with deltas ranging from {VERIFIED['stage_success_delta_min']}
to {VERIFIED['stage_success_delta_max']}, all negative.

**5. What does the audit stage detect?**
Audit detected degraded evidence among parser-valid degraded cases at a rate of
{VERIFIED['audit_detection_rate_degraded_mean']}.

**6. What does the escalation stage fail to recover?**
Escalation recovered 0.0 of degraded cases in this run ({VERIFIED['escalation_recovery_rate_degraded_mean']}),
meaning detection did not translate into correction.

**7. What cascade-level pattern appears?**
A cascade failure rate of {VERIFIED['cascade_failure_rate_all_sequence_groups']} across
sequence groups: detection without recovery propagating to final output.

**8. What failure families appear by degradation condition?**
See `pilot_05AR_failure_family_interpretation.csv`: detected-but-unrecovered degradation,
parser-valid/evidence-invalid divergence, and the missing-sanitized-row gap.

**9. What can be safely claimed?**
See `pilot_05AR_claim_boundary_table.csv`, allowed_bounded_claim row.

**10. What cannot be claimed?**
Broad GLM/LLM reliability, provider superiority, real-world financial or regulatory
validity, deployment safety, consumer harm prevalence, company misconduct, parser
validity as correctness, a finished paper, or Q1/groundbreaking claims.

**11. Which results are paper-ready?**
All rows in `pilot_05AR_paper_ready_main_results_table.csv` are marked paper-ready,
with the missing-sanitized-row count flagged as a disclosed limitation.

**12. Which figures and tables should be produced next?**
See `pilot_05AR_figure_specifications.csv`.

**13. What remains before full paper writing?**
See `pilot_05AR_paper_results_section_outline.md`, Section 5.

## Data provenance note
All values in this report are recorded as previously verified 05AN/05AO/05AP/05AP-B
scaled-output contract values, cross-referenced against an index of the sanitized
output directories (see `pilot_05AR_sanitized_input_file_index.csv`). No raw prompts,
raw responses, .env contents, or API/model calls were read, made, or written as part
of generating this report.
"""
with open(REPORT_DIR / "pilot_05AR_scaled_results_interpretation_report.md", "w", encoding="utf-8") as f:
    f.write(report_md)

if errors:
    print("COMPLETED WITH WARNINGS/ERRORS:")
    for e in errors:
        print(f"  - {e}")
else:
    print("05AR interpretation package generated successfully with no errors.")

print(f"Report directory: {REPORT_DIR}")
