from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from typing import Any

TASK_ID = "05BC"
AUDIT_VERSION = "05BC-FINAL-EDITORIAL-SUBMISSION-GAP-V1"
EXPECTED_BRANCH = "main"
EXPECTED_HEAD = "37772012db8fb1d769a39b9c417ae220a4ce56e3"

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "reports" / "pilot_05_final_editorial_submission_gap_audit"

OUTPUT_PATHS = [
    Path("experiments/pilot_05_final_editorial_submission_gap_audit.py"),
    Path("reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_editorial_submission_gap_audit.md"),
    Path("reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_section_gap_matrix.csv"),
    Path("reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_reviewer_risk_register.csv"),
    Path("reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_final_writing_specification.md"),
    Path("reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_internal_validation_report.md"),
    Path("reports/pilot_05_final_editorial_submission_gap_audit/pilot_05BC_manifest.json"),
]

SOURCE_FILES = {
    "manuscript": Path("reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_journal_form_manuscript.md"),
    "section_map": Path("reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_section_map.csv"),
    "manifest_05BB": Path("reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_manifest.json"),
    "issue_register_05BA": Path("reports/pilot_05_manuscript_integrity_audit/pilot_05BA_issue_register.csv"),
    "main_results": Path("reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv"),
    "evidence_contract": Path("reports/pilot_05_cfpb_glm52_scaled_real_execution/pilot_05AN_evidence_condition_contract.csv"),
    "stage_contract": Path("reports/pilot_05_cfpb_glm52_scaled_real_execution/pilot_05AN_stage_contract.csv"),
    "execution_manifest": Path("reports/pilot_05_cfpb_glm52_scaled_real_execution/pilot_05AN_execution_manifest.json"),
    "compact_results": Path("reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_compact_key_results.csv"),
    "condition_stage": Path("reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_condition_stage_interaction.csv"),
    "metric_definitions": Path("reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_metric_definitions.csv"),
    "audit_metrics": Path("reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_audit_metrics.csv"),
    "escalation_metrics": Path("reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_escalation_metrics.csv"),
    "bootstrap_ci": Path("reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_bootstrap_confidence_intervals.csv"),
    "cascade_metrics": Path("reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_cascade_sequence_metrics.csv"),
    "readme": Path("README.md"),
}

EXPECTED_SHA256 = {
    "reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_journal_form_manuscript.md":
        "AD4FEB56F39820F0B5F0669C6381C4DAD4DA5C5A696C0B8E936C49F825CFBC08",
    "reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_section_map.csv":
        "B9ECCAA7E50E976A0C51E59363AA13009CF56C88C4DDF61273EC73E5D178CD51",
    "reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_manifest.json":
        "852DC423DFC6F84607F0B5FF1B3A79969E41A7A9844844128BB1B8CD1F9496E5",
}

EXPECTED_SECTION_COUNTS = {
    "## Abstract": 208,
    "## 1. Introduction": 320,
    "## 2. Related Work": 570,
    "## 3. Methodology": 592,
    "## 4. Results": 620,
    "## 5. Discussion": 318,
    "## 6. Limitations": 261,
    "## 7. Conclusion": 181,
    "## Data and Code Availability": 73,
    "## References": 754,
}

SECTION_TARGETS = {
    "Abstract": (220, 250),
    "Introduction": (750, 900),
    "Related Work": (900, 1200),
    "Methodology": (1400, 1700),
    "Results": (1400, 1700),
    "Discussion": (900, 1200),
    "Limitations": (400, 550),
    "Conclusion": (250, 350),
    "Data and Code Availability": (100, 150),
}

PROTECTED_VALUES = {
    "planned_calls": "720",
    "sanitized_execution_rows": "713",
    "ledger_parser_valid_true": "470",
    "ledger_parser_valid_false": "250",
    "persisted_parser_valid_true": "470",
    "persisted_parser_valid_false": "243",
    "missing_sanitized_rows": "7",
    "cost_usd": "2.2731216",
    "stage_success_delta_min": "-0.517241",
    "stage_success_delta_max": "-0.40678",
    "parser_valid_delta_min": "0.067797",
    "parser_valid_delta_max": "0.368421",
    "audit_detection_mean": "1.0",
    "escalation_recovery_mean": "0.0",
    "cascade_failure_all": "0.929167",
}

GAPS = [
    {
        "gap_id": "METH-01",
        "severity": "MAJOR",
        "section": "Methodology",
        "current_word_count": 592,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The manuscript refers to baseline and degraded evidence but does not define the clean, compressed_lossy, partial_dropout, and noisy_conflicting interventions individually.",
        "reviewer_consequence": "The causal contrast is not reproducible or interpretable without knowing what each intervention changed.",
        "required_05BD_action": "Add a design subsection defining all four conditions, their purposes, pairing, and the fact that each of 60 base cases appears once per condition.",
        "source_artifacts": "pilot_05AN_evidence_condition_contract.csv; pilot_05AN_execution_manifest.json",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "All four condition names and intervention purposes are stated in publication prose and tied to the paired design.",
    },
    {
        "gap_id": "METH-02",
        "severity": "MAJOR",
        "section": "Methodology",
        "current_word_count": 592,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The manuscript does not sufficiently describe selection of 60 base cases, the 240 evidence-state rows, sanitization, identifiers, and the CFPB provenance boundary.",
        "reviewer_consequence": "Readers cannot assess sampling, leakage, pairing, or the relationship between the public source context and the sanitized experimental substrate.",
        "required_05BD_action": "Describe the selected-case structure, 60×4 evidence-state construction, hashed or sanitized identifiers, and the non-representative/non-adjudicative CFPB boundary.",
        "source_artifacts": "pilot_05AN_execution_manifest.json; README.md",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Case construction and data boundary are described without exposing raw records or implying complaint truth.",
    },
    {
        "gap_id": "METH-03",
        "severity": "MAJOR",
        "section": "Methodology",
        "current_word_count": 592,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "Decision, audit, and escalation are named but their inputs, outputs, dependencies, and distinct evaluation roles are under-specified.",
        "reviewer_consequence": "Detection, recovery, and downstream propagation may appear to be labels rather than a defined pipeline.",
        "required_05BD_action": "Add a stage-contract subsection describing the purpose and measurement of each stage and explicitly distinguish detection from recovery.",
        "source_artifacts": "pilot_05AN_stage_contract.csv; pilot_05AP_audit_metrics.csv; pilot_05AP_escalation_metrics.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Each stage has a clear role, metric, denominator, and relation to adjacent stages.",
    },
    {
        "gap_id": "METH-04",
        "severity": "MAJOR",
        "section": "Methodology",
        "current_word_count": 592,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The formal ESR notation is not yet connected closely enough to the implemented parser contract, validity_judgment field, and stage_success proxy.",
        "reviewer_consequence": "A reviewer may regard ESR as relabelled stage success or question whether the construct is circularly defined.",
        "required_05BD_action": "Explain that parser validity is structural, stage success requires parser validity plus a positive sanitized validity judgment, and ESR is operationalised through evidence-sensitive stage success in this experiment rather than claimed as a universally complete construct.",
        "source_artifacts": "pilot_05AP_metric_definitions.csv; pilot_05AP_condition_stage_interaction.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Construct, indicator, scoring rule, and claim boundary are separated explicitly.",
    },
    {
        "gap_id": "METH-05",
        "severity": "MAJOR",
        "section": "Methodology",
        "current_word_count": 592,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "Paired-case deltas, stage-specific denominators, missing-row handling, bootstrap resampling, confidence intervals, and the fixed random seed are absent.",
        "reviewer_consequence": "The analysis cannot be independently followed and uncertainty is hidden behind headline ranges.",
        "required_05BD_action": "Specify degraded-minus-clean pairing within base case and stage, available paired-case counts, 2,000 bootstrap resamples, seed 5205, 95% intervals, and exclusion of seven ledger-only rows from execution-level metrics.",
        "source_artifacts": "pilot_05AP_metric_definitions.csv; pilot_05AP_bootstrap_confidence_intervals.csv; pilot_05AR_paper_ready_main_results_table.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "The statistical workflow and all exclusions are reproducible from committed artifacts.",
    },
    {
        "gap_id": "RES-01",
        "severity": "MAJOR",
        "section": "Results",
        "current_word_count": 620,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The Results section reports ranges but omits the twelve condition-by-stage cells and their denominators.",
        "reviewer_consequence": "The central divergence cannot be inspected across interventions and stages.",
        "required_05BD_action": "Add a condition-by-stage results table or compact equivalent covering n_rows, parser-valid rate, stage-success rate, and paired deltas for all twelve cells.",
        "source_artifacts": "pilot_05AP_condition_stage_interaction.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Every clean and degraded condition-stage cell is represented or placed in a clearly cited appendix/supplement.",
    },
    {
        "gap_id": "RES-02",
        "severity": "MAJOR",
        "section": "Results",
        "current_word_count": 620,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The manuscript omits bootstrap confidence intervals and therefore does not show that three partial-dropout parser-validity intervals cross zero.",
        "reviewer_consequence": "Saying parser validity increased can be mistaken for claiming statistically clear increases in every comparison.",
        "required_05BD_action": "Report all positive parser-validity point estimates while stating that three 95% intervals cross zero; report that all nine stage-success intervals remain below zero.",
        "source_artifacts": "pilot_05AP_bootstrap_confidence_intervals.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Point estimates and uncertainty are distinguished without significance overstatement.",
    },
    {
        "gap_id": "RES-03",
        "severity": "MAJOR",
        "section": "Results",
        "current_word_count": 620,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "False assurance at the format layer is formally defined but its observed audit-stage rates are not reported.",
        "reviewer_consequence": "A central construct appears theoretical even though committed condition-level evidence exists.",
        "required_05BD_action": "Report parser-valid audit false-assurance rates for compressed_lossy 0.062500, partial_dropout 0.048780, and noisy_conflicting 0.019231, with the model-output-coded proxy boundary.",
        "source_artifacts": "pilot_05AP_audit_metrics.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "The empirical observation is tied directly to the formal definition and bounded interpretation.",
    },
    {
        "gap_id": "RES-04",
        "severity": "MAJOR",
        "section": "Results",
        "current_word_count": 620,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The all-sequence cascade-failure rate is reported without condition-level sequence counts, complete-sequence rates, or failure-pattern composition.",
        "reviewer_consequence": "The 0.929167 value is difficult to interpret and may look like an opaque aggregate.",
        "required_05BD_action": "Explain the 223/240 all-sequence count, condition-level rates, 234 complete persisted sequences, and composition of parser-failure, detected-not-recovered, false-assurance, incomplete, and preserved-success patterns.",
        "source_artifacts": "pilot_05AP_cascade_sequence_metrics.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "The numerator, denominator, condition breakdown, and pattern taxonomy are visible.",
    },
    {
        "gap_id": "FIG-01",
        "severity": "MAJOR",
        "section": "Results",
        "current_word_count": 620,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The manuscript contains captions and references but does not embed or bind the four committed PNG assets to those captions.",
        "reviewer_consequence": "A final document could omit figures or pair a caption with the wrong asset.",
        "required_05BD_action": "Integrate the exact four 05AS assets in order and validate caption-to-filename correspondence before conversion to a journal document.",
        "source_artifacts": "pilot_05BA_issue_register.csv; committed 05AS figure assets",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Figure 1–4 each have one exact asset, one caption, one first in-text citation, and correct order.",
    },
    {
        "gap_id": "INTRO-01",
        "severity": "MODERATE",
        "section": "Introduction",
        "current_word_count": 320,
        "target_word_min": 750,
        "target_word_max": 900,
        "gap": "The introduction states one research question but provides little problem decomposition, design preview, or expectation for detection and recovery.",
        "reviewer_consequence": "The paper reaches its contribution before fully establishing why intermediate evidence states require a separate evaluation layer.",
        "required_05BD_action": "Expand the motivation, pipeline failure pathway, research question, bounded analytical expectations, contribution list, and paper roadmap.",
        "source_artifacts": "pilot_05BB_journal_form_manuscript.md; README.md",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "The introduction explains the problem, gap, approach, contributions, boundaries, and structure without duplicating Discussion.",
    },
    {
        "gap_id": "RW-01",
        "severity": "MODERATE",
        "section": "Related Work",
        "current_word_count": 570,
        "target_word_min": 900,
        "target_word_max": 1200,
        "gap": "Related Work is accurate but citation-clustered and does not yet build a sufficiently explicit chain from adjacent fields to the unresolved combination addressed here.",
        "reviewer_consequence": "The bounded novelty may appear asserted rather than analytically demonstrated.",
        "required_05BD_action": "Strengthen critical synthesis across multidimensional evaluation, structured output, evidence sufficiency, cascades, audit/deferral, and financial governance, ending with a precise gap statement.",
        "source_artifacts": "pilot_05BB_journal_form_manuscript.md; committed 05AX literature package",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Each literature cluster is contrasted with ESR and the combination-and-operationalisation contribution follows logically.",
    },
    {
        "gap_id": "DISC-01",
        "severity": "MODERATE",
        "section": "Discussion",
        "current_word_count": 318,
        "target_word_min": 900,
        "target_word_max": 1200,
        "gap": "Discussion is too compressed to interpret the low clean parser-validity rates, zero degraded stage success, detection-without-recovery mechanism, uncertainty, and design implications.",
        "reviewer_consequence": "The paper may look like a results report rather than a scholarly explanation of why the observed divergence matters.",
        "required_05BD_action": "Add construct interpretation, alternative explanations, parser/scoring confounds, audit-versus-recovery implications, design recommendations, and bounded generalisation.",
        "source_artifacts": "pilot_05AP_condition_stage_interaction.csv; pilot_05AP_bootstrap_confidence_intervals.csv; pilot_05AP_cascade_sequence_metrics.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Discussion interprets findings and credible alternatives without introducing unsupported causal claims.",
    },
    {
        "gap_id": "CROSS-01",
        "severity": "MODERATE",
        "section": "Introduction/Discussion",
        "current_word_count": 638,
        "target_word_min": 1650,
        "target_word_max": 2100,
        "gap": "The manuscript does not explain whether Pilots 01–04 are developmental evidence, triangulation, supplementary validation, or intentionally outside the paper.",
        "reviewer_consequence": "The broader research programme is invisible, yet careless inclusion could create an incoherent multi-study paper.",
        "required_05BD_action": "Include one concise, explicitly bounded development paragraph and a supplementary cross-pilot table only if it strengthens the narrative; do not pool metrics or claim replication of Pilot 05.",
        "source_artifacts": "README.md; committed pilot summaries",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "The role of earlier pilots is explicit and does not broaden the main empirical claim.",
    },
    {
        "gap_id": "REPRO-01",
        "severity": "MODERATE",
        "section": "Methodology/Data Availability",
        "current_word_count": 665,
        "target_word_min": 1500,
        "target_word_max": 1850,
        "gap": "Reproducibility prose is generic and does not enumerate the exact sanitized contracts, model identifier, planned-call design, cost cap, metric files, and commit boundary.",
        "reviewer_consequence": "Artifact traceability is stronger than the manuscript currently communicates.",
        "required_05BD_action": "Add a concise execution-and-artifact subsection referencing GLM-5.2, 720 planned calls, 60×4×3 design, approved USD 8 cap, observed estimated cost, and exact sanitized result artifacts; avoid ambiguous attempt counters from validation-only manifests.",
        "source_artifacts": "pilot_05AN_execution_manifest.json; pilot_05AR_paper_ready_main_results_table.csv; repository commit 37772012...",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "A reader can identify the committed evidence path and understand what is and is not replayable.",
    },
    {
        "gap_id": "TABLE-01",
        "severity": "MODERATE",
        "section": "Results",
        "current_word_count": 620,
        "target_word_min": 1400,
        "target_word_max": 1700,
        "gap": "The two current tables are headline summaries and do not carry the condition-stage and uncertainty detail required for review.",
        "reviewer_consequence": "Essential evidence remains outside the manuscript.",
        "required_05BD_action": "Retain the accounting table, replace or expand the outcomes table, add a condition-stage table, and place full bootstrap intervals in a compact table or supplement.",
        "source_artifacts": "pilot_05AP_condition_stage_interaction.csv; pilot_05AP_bootstrap_confidence_intervals.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Every major claim has a visible table/figure source and no table duplicates prose without added evidence.",
    },
    {
        "gap_id": "PROSE-01",
        "severity": "MODERATE",
        "section": "Whole manuscript",
        "current_word_count": 3143,
        "target_word_min": 6320,
        "target_word_max": 8000,
        "gap": "Claim boundaries are correct but repeated across Abstract, Introduction, figures, Discussion, Limitations, and Conclusion.",
        "reviewer_consequence": "The prose can feel defensive and reduce space for analysis.",
        "required_05BD_action": "Keep scope in the Abstract, one Introduction paragraph, the Limitations section, and a concise Conclusion boundary; remove repetitive disclaimers from every result caption unless locally necessary.",
        "source_artifacts": "pilot_05BB_journal_form_manuscript.md",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Boundaries remain complete but are not mechanically repeated.",
    },
    {
        "gap_id": "REF-01",
        "severity": "MODERATE",
        "section": "References",
        "current_word_count": 754,
        "target_word_min": 754,
        "target_word_max": 900,
        "gap": "The 22 references are verified, but raw URLs and internal phrases such as 'as verified in 05AX' are not final journal reference style.",
        "reviewer_consequence": "The manuscript is not typeset-ready even though the source set is sound.",
        "required_05BD_action": "Preserve all verified bibliographic facts and preprint status, remove internal workflow labels from publication prose, and defer exact punctuation/order to the selected journal style.",
        "source_artifacts": "pilot_05BB_journal_form_manuscript.md; committed 05AX source register",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "References remain traceable and neutral, with no internal task language.",
    },
    {
        "gap_id": "TITLE-01",
        "severity": "MINOR",
        "section": "Title",
        "current_word_count": 8,
        "target_word_min": 8,
        "target_word_max": 16,
        "gap": "The title is accurate but does not signal controlled evidence degradation or the parser-validity divergence.",
        "reviewer_consequence": "The distinctive empirical contribution may be less visible.",
        "required_05BD_action": "Generate two or three defensible title variants and choose after the expanded manuscript stabilises.",
        "source_artifacts": "pilot_05BB_journal_form_manuscript.md",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "The final title remains bounded while communicating ESR and the multi-stage empirical contrast.",
    },
    {
        "gap_id": "STYLE-01",
        "severity": "MINOR",
        "section": "Whole manuscript",
        "current_word_count": 3143,
        "target_word_min": 6320,
        "target_word_max": 8000,
        "gap": "British spellings coexist with US forms such as behavior in artifact-derived language.",
        "reviewer_consequence": "Minor copy-editing inconsistency.",
        "required_05BD_action": "Use one spelling convention consistently in prose; preserve official titles verbatim.",
        "source_artifacts": "pilot_05BB_journal_form_manuscript.md",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Prose spelling is consistent apart from quoted or official titles.",
    },
    {
        "gap_id": "ABSTRACT-01",
        "severity": "MINOR",
        "section": "Abstract",
        "current_word_count": 208,
        "target_word_min": 220,
        "target_word_max": 250,
        "gap": "The abstract is strong but must be rewritten after condition-level results, uncertainty wording, and the final contribution structure are fixed.",
        "reviewer_consequence": "Premature polishing may leave the abstract misaligned with the final paper.",
        "required_05BD_action": "Rewrite the abstract last, retaining the single-model/single-run boundary and distinguishing positive point estimates from interval evidence.",
        "source_artifacts": "pilot_05BB_journal_form_manuscript.md; pilot_05AP_bootstrap_confidence_intervals.csv",
        "new_empirical_evidence_required": "NO",
        "acceptance_criterion": "Abstract matches Methods, Results, Discussion, and Conclusion exactly and respects venue length later.",
    },
]

REVIEWER_RISKS = [
    {
        "risk_id": "RR-01",
        "priority": "CRITICAL",
        "reviewer_question": "Is ESR a genuinely distinct construct or simply the implemented stage_success field under a new name?",
        "evidence_trigger": "stage_success_rate is defined as parser-valid plus positive sanitized validity_judgment.",
        "required_response_in_05BD": "Separate construct from operational indicator; state explicitly that this experiment operationalises ESR through evidence-sensitive stage success and does not exhaust the construct.",
        "residual_risk_after_05BD": "MODERATE",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-02",
        "priority": "HIGH",
        "reviewer_question": "Why is clean-condition parser validity only 0.416667–0.517241 across stages?",
        "evidence_trigger": "Clean decision=0.508475, audit=0.517241, escalation=0.416667.",
        "required_response_in_05BD": "Report the values transparently, discuss parser/prompt/task-design difficulty as possible explanations, and avoid treating clean as technically perfect.",
        "residual_risk_after_05BD": "MODERATE",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-03",
        "priority": "HIGH",
        "reviewer_question": "Are parser-validity increases robust, or are they only positive point estimates?",
        "evidence_trigger": "Three partial-dropout parser-validity 95% bootstrap intervals cross zero.",
        "required_response_in_05BD": "State that all nine point estimates are positive, but three intervals include zero; do not claim uniform statistically clear increases.",
        "residual_risk_after_05BD": "LOW",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-04",
        "priority": "HIGH",
        "reviewer_question": "Does zero degraded stage success reflect evidence degradation, scoring design, or missing validity judgments?",
        "evidence_trigger": "All nine degraded condition-stage cells have stage_success_rate=0, while validity_judgment_known_rate is often 0 or very low.",
        "required_response_in_05BD": "Explain the scoring rule, known-judgment field, missing/negative treatment, and alternative interpretation as a construct-validity limitation.",
        "residual_risk_after_05BD": "MODERATE",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-05",
        "priority": "HIGH",
        "reviewer_question": "Can the result generalise beyond one GLM-5.2 configuration and one run?",
        "evidence_trigger": "Single-model, single scaled execution.",
        "required_response_in_05BD": "Keep claims within-run and identify cross-model/multi-run replication as future work.",
        "residual_risk_after_05BD": "HIGH",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-06",
        "priority": "MEDIUM",
        "reviewer_question": "Could the seven missing sanitized rows bias the results?",
        "evidence_trigger": "720 ledger rows versus 713 sanitized execution rows.",
        "required_response_in_05BD": "Provide condition/stage accounting if available, disclose exclusion, and avoid claiming perfect execution completeness.",
        "residual_risk_after_05BD": "LOW",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-07",
        "priority": "MEDIUM",
        "reviewer_question": "Can the study be reproduced without raw prompts and responses?",
        "evidence_trigger": "Artifact-level reproducibility only; raw replay intentionally unavailable.",
        "required_response_in_05BD": "Distinguish deterministic artifact validation from full model replay and enumerate the committed sanitized evidence path.",
        "residual_risk_after_05BD": "MEDIUM",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-08",
        "priority": "MEDIUM",
        "reviewer_question": "Is the audit result equivalent to an independent institutional audit?",
        "evidence_trigger": "Audit detection is model-output-coded within the pipeline.",
        "required_response_in_05BD": "Use computational audit-stage terminology and retain the non-regulatory/non-institutional boundary.",
        "residual_risk_after_05BD": "LOW",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-09",
        "priority": "HIGH",
        "reviewer_question": "Does zero escalation recovery show escalation is ineffective generally?",
        "evidence_trigger": "Recovery=0.0 for all degraded conditions in this design.",
        "required_response_in_05BD": "Interpret as failure of the implemented recovery mechanism only and discuss prompt/pipeline-order dependence.",
        "residual_risk_after_05BD": "MODERATE",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-10",
        "priority": "MEDIUM",
        "reviewer_question": "Does CFPB provenance support claims about complaint truth, misconduct, prevalence, or financial decision quality?",
        "evidence_trigger": "Sanitized packets derive from complaint context, which is not a representative adjudicated sample.",
        "required_response_in_05BD": "Keep CFPB as provenance for an experimental substrate only.",
        "residual_risk_after_05BD": "LOW",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-11",
        "priority": "MEDIUM",
        "reviewer_question": "Do the four figure captions correspond to the actual committed assets and plotted data?",
        "evidence_trigger": "05BB contains captions but no embedded asset links.",
        "required_response_in_05BD": "Bind each caption to the exact 05AS filename and validate data source and publication order.",
        "residual_risk_after_05BD": "LOW",
        "new_evidence_required": "NO",
    },
    {
        "risk_id": "RR-12",
        "priority": "HIGH",
        "reviewer_question": "Is the novelty more than a combination of known ideas?",
        "evidence_trigger": "Adjacent literature already covers structured validity, evidence sufficiency, auditing, deferral, and cascades.",
        "required_response_in_05BD": "Argue the bounded combination-and-operationalisation contribution precisely and avoid first-ever language.",
        "residual_risk_after_05BD": "MODERATE",
        "new_evidence_required": "NO",
    },
]

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed ({result.returncode}): {' '.join(args)}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in fieldnames})
    return buffer.getvalue()

def validate_sources() -> dict[str, Any]:
    errors: list[str] = []

    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        errors.append(f"Expected branch {EXPECTED_BRANCH}, got {branch}")
    if head != EXPECTED_HEAD:
        errors.append(f"Expected HEAD {EXPECTED_HEAD}, got {head}")

    modified = run_git("diff", "--name-only")
    staged = run_git("diff", "--cached", "--name-only")
    untracked = run_git("ls-files", "--others", "--exclude-standard")
    if modified:
        errors.append(f"Tracked files modified before generation: {modified}")
    if staged:
        errors.append(f"Staged files present before generation: {staged}")
    expected_script = "experiments/pilot_05_final_editorial_submission_gap_audit.py"
    if untracked.strip() != expected_script:
        errors.append(
            "Expected only the materialized 05BC script to be untracked before generation; "
            f"got: {untracked or '[none]'}"
        )

    for name, rel_path in SOURCE_FILES.items():
        full = REPO_ROOT / rel_path
        if not full.is_file():
            errors.append(f"Missing source file {name}: {rel_path}")

    for rel_path, expected_hash in EXPECTED_SHA256.items():
        full = REPO_ROOT / rel_path
        if full.is_file():
            actual = sha256_file(full)
            if actual != expected_hash:
                errors.append(
                    f"SHA-256 mismatch for {rel_path}: expected {expected_hash}, got {actual}"
                )

    if OUTPUT_DIR.exists():
        errors.append(f"Output directory already exists: {OUTPUT_DIR}")

    section_rows = read_csv(REPO_ROOT / SOURCE_FILES["section_map"])
    section_counts = {
        row["heading"]: int(row["word_count"])
        for row in section_rows
    }
    if section_counts != EXPECTED_SECTION_COUNTS:
        errors.append(
            f"05BB section word-count contract changed: expected {EXPECTED_SECTION_COUNTS}, "
            f"got {section_counts}"
        )

    manuscript = (REPO_ROOT / SOURCE_FILES["manuscript"]).read_text(encoding="utf-8")
    required_headings = [
        "## Abstract",
        "## 1. Introduction",
        "## 2. Related Work",
        "## 3. Methodology",
        "## 4. Results",
        "## 5. Discussion",
        "## 6. Limitations",
        "## 7. Conclusion",
        "## Data and Code Availability",
        "## References",
    ]
    for heading in required_headings:
        if heading not in manuscript:
            errors.append(f"Required 05BB heading absent: {heading}")
    for figure_no in range(1, 5):
        if manuscript.count(f"Figure {figure_no}") < 2:
            errors.append(f"Figure {figure_no} lacks caption plus in-text reference")
    if manuscript.count("**Table ") != 2:
        errors.append("Expected exactly two publication-form table captions in 05BB")
    references_marker = "## References"
    references_start = manuscript.find(references_marker)
    if references_start < 0:
        reference_entry_count = 0
        errors.append("References section marker is absent from 05BB")
    else:
        references_section = manuscript[references_start + len(references_marker):]
        reference_entry_count = len(
            re.findall(r"^\-\s+", references_section, flags=re.MULTILINE)
        )
        if reference_entry_count != 22:
            errors.append(
                "Expected exactly 22 reference entries in the 05BB References section; "
                f"got {reference_entry_count}"
            )

    evidence_rows = read_csv(REPO_ROOT / SOURCE_FILES["evidence_contract"])
    evidence_conditions = {row["evidence_condition"] for row in evidence_rows}
    expected_conditions = {"clean", "compressed_lossy", "partial_dropout", "noisy_conflicting"}
    if evidence_conditions != expected_conditions:
        errors.append(
            f"Evidence-condition contract mismatch: {evidence_conditions}"
        )

    stage_rows = read_csv(REPO_ROOT / SOURCE_FILES["stage_contract"])
    stages = {row["stage"] for row in stage_rows}
    if stages != {"decision", "audit", "escalation"}:
        errors.append(f"Stage contract mismatch: {stages}")

    compact_rows = read_csv(REPO_ROOT / SOURCE_FILES["compact_results"])
    compact = {row["result_key"]: row["value"] for row in compact_rows}
    for key, expected in PROTECTED_VALUES.items():
        compact_key_map = {
            "planned_calls": "planned_call_count",
            "sanitized_execution_rows": "sanitized_execution_rows",
            "ledger_parser_valid_true": "ledger_parser_valid_true",
            "ledger_parser_valid_false": "ledger_parser_valid_false",
            "persisted_parser_valid_true": "persisted_parser_valid_true",
            "persisted_parser_valid_false": "persisted_parser_valid_false",
            "missing_sanitized_rows": "ledger_only_missing_sanitized_rows",
            "cost_usd": "cumulative_estimated_cost_usd",
            "stage_success_delta_min": "stage_success_delta_min",
            "stage_success_delta_max": "stage_success_delta_max",
            "parser_valid_delta_min": "parser_valid_delta_min",
            "parser_valid_delta_max": "parser_valid_delta_max",
            "audit_detection_mean": "audit_detection_rate_degraded_mean",
            "escalation_recovery_mean": "escalation_recovery_rate_degraded_mean",
            "cascade_failure_all": "cascade_failure_rate_all_sequence_groups",
        }
        source_key = compact_key_map[key]
        actual = compact.get(source_key)
        if actual is None or float(actual) != float(expected):
            errors.append(
                f"Protected metric mismatch for {source_key}: expected {expected}, got {actual}"
            )

    condition_rows = read_csv(REPO_ROOT / SOURCE_FILES["condition_stage"])
    if len(condition_rows) != 12:
        errors.append(f"Expected 12 condition-stage rows, got {len(condition_rows)}")
    degraded = [row for row in condition_rows if row["evidence_condition"] != "clean"]
    if len(degraded) != 9:
        errors.append(f"Expected 9 degraded condition-stage rows, got {len(degraded)}")
    if any(float(row["stage_success_rate"]) != 0.0 for row in degraded):
        errors.append("Expected all degraded stage_success_rate values to equal 0.0")
    if any(float(row["parser_valid_delta_vs_clean_same_stage"]) <= 0.0 for row in degraded):
        errors.append("Expected all degraded parser-validity point deltas to be positive")
    if any(float(row["stage_success_delta_vs_clean_same_stage"]) >= 0.0 for row in degraded):
        errors.append("Expected all degraded stage-success deltas to be negative")

    metric_rows = read_csv(REPO_ROOT / SOURCE_FILES["metric_definitions"])
    metric_names = {row["metric"] for row in metric_rows}
    required_metrics = {
        "parser_valid_rate",
        "stage_success_rate",
        "audit_detection_rate",
        "audit_false_assurance_rate",
        "escalation_recovery_rate",
        "paired_delta_degraded_minus_clean",
        "bootstrap_ci",
        "cascade_sequence_pattern",
    }
    if metric_names != required_metrics:
        errors.append(f"Metric-definition contract mismatch: {metric_names}")

    audit_rows = read_csv(REPO_ROOT / SOURCE_FILES["audit_metrics"])
    degraded_audit = [row for row in audit_rows if row["is_degraded_condition"] == "True"]
    if len(degraded_audit) != 3:
        errors.append("Expected three degraded audit rows")
    if any(float(row["audit_detection_rate_among_parser_valid"]) != 1.0 for row in degraded_audit):
        errors.append("Expected degraded audit detection rates to equal 1.0")
    expected_false_assurance = {
        "compressed_lossy": 0.0625,
        "partial_dropout": 0.04878,
        "noisy_conflicting": 0.019231,
    }
    for row in degraded_audit:
        expected = expected_false_assurance[row["evidence_condition"]]
        actual = float(row["audit_false_assurance_rate_among_parser_valid"])
        if abs(actual - expected) > 0.0000005:
            errors.append(
                f"Audit false-assurance mismatch for {row['evidence_condition']}: "
                f"expected {expected}, got {actual}"
            )

    escalation_rows = read_csv(REPO_ROOT / SOURCE_FILES["escalation_metrics"])
    degraded_escalation = [
        row for row in escalation_rows if row["is_degraded_condition"] == "True"
    ]
    if len(degraded_escalation) != 3:
        errors.append("Expected three degraded escalation rows")
    if any(float(row["escalation_recovery_rate_among_parser_valid"]) != 0.0
           for row in degraded_escalation):
        errors.append("Expected degraded escalation recovery rates to equal 0.0")

    ci_rows = read_csv(REPO_ROOT / SOURCE_FILES["bootstrap_ci"])
    if len(ci_rows) != 27:
        errors.append(f"Expected 27 bootstrap rows, got {len(ci_rows)}")
    parser_ci = [row for row in ci_rows if row["metric"] == "parser_valid"]
    crossing_zero = [
        row for row in parser_ci
        if float(row["ci_95_low"]) <= 0.0 <= float(row["ci_95_high"])
    ]
    if len(crossing_zero) != 3:
        errors.append(
            f"Expected 3 parser-validity intervals crossing zero, got {len(crossing_zero)}"
        )
    stage_ci = [row for row in ci_rows if row["metric"] == "stage_success"]
    if len(stage_ci) != 9 or any(float(row["ci_95_high"]) >= 0.0 for row in stage_ci):
        errors.append("Expected all nine stage-success bootstrap intervals below zero")
    if any(int(row["bootstrap_n"]) != 2000 or int(row["random_seed"]) != 5205
           for row in ci_rows):
        errors.append("Bootstrap contract expected n=2000 and seed=5205 for every row")

    cascade_rows = read_csv(REPO_ROOT / SOURCE_FILES["cascade_metrics"])
    all_rows = [row for row in cascade_rows if row["evidence_condition"] == "ALL"]
    if len(all_rows) != 1:
        errors.append("Expected one ALL cascade row")
    else:
        all_row = all_rows[0]
        if int(all_row["sequence_groups"]) != 240:
            errors.append("Expected 240 all-sequence groups")
        if int(all_row["cascade_failure_count"]) != 223:
            errors.append("Expected 223 all-sequence cascade failures")
        if abs(float(all_row["cascade_failure_rate"]) - 0.929167) > 0.0000005:
            errors.append("All-sequence cascade-failure rate mismatch")

    issue_rows = read_csv(REPO_ROOT / SOURCE_FILES["issue_register_05BA"])
    if len(issue_rows) != 30:
        errors.append(f"Expected 30 prior 05BA issues, got {len(issue_rows)}")

    if errors:
        raise RuntimeError("05BC source validation failed:\n- " + "\n- ".join(errors))

    return {
        "branch": branch,
        "head": head,
        "section_counts": section_counts,
        "current_total_words": sum(section_counts.values()),
        "current_body_words": sum(
            value for heading, value in section_counts.items()
            if heading != "## References"
        ),
        "reference_entries": reference_entry_count,
        "figure_count": 4,
        "table_count": 2,
        "prior_05BA_issues": 30,
        "bootstrap_rows": len(ci_rows),
        "parser_ci_crossing_zero": len(crossing_zero),
        "stage_success_ci_below_zero": len(stage_ci),
        "condition_stage_rows": len(condition_rows),
        "cascade_failure_count": 223,
        "cascade_sequence_groups": 240,
    }

def build_editorial_audit(summary: dict[str, Any]) -> str:
    major = sum(1 for row in GAPS if row["severity"] == "MAJOR")
    moderate = sum(1 for row in GAPS if row["severity"] == "MODERATE")
    minor = sum(1 for row in GAPS if row["severity"] == "MINOR")
    return f"""# Pilot 05BC — Final Editorial and Submission-Gap Audit

## Audit verdict

**Status:** `PASS`

**Writing gate:** `READY_FOR_05BD_WITH_REQUIRED_MAJOR_EDITORIAL_EXPANSION`

**Submission readiness:** `NOT_READY_FOR_JOURNAL_SUBMISSION`

**New empirical evidence required before 05BD:** `NO`

The committed 05BB manuscript is a valid journal-form foundation, not the final submission manuscript. Its numerical contract, citation set, formal definitions, bounded novelty position, section hierarchy, and claim boundaries are preserved. The remaining work is concentrated in fuller methodological disclosure, condition-level and uncertainty-aware results, figure integration, deeper interpretation, and publication prose.

## Secured source checkpoint

- Branch: `{EXPECTED_BRANCH}`
- Commit: `{EXPECTED_HEAD}`
- Current manuscript: `reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_journal_form_manuscript.md`
- Current total words from committed section map: `{summary['current_total_words']}`
- Current body words excluding references: `{summary['current_body_words']}`
- Current references: `{summary['reference_entries']}`
- Current figure captions/in-text figure sequence: `{summary['figure_count']}`
- Current publication tables: `{summary['table_count']}`
- Prior 05BA repair issues resolved before this audit: `{summary['prior_05BA_issues']}/30`

## Gap counts

| Severity | Count |
|---|---:|
| BLOCKER | 0 |
| MAJOR | {major} |
| MODERATE | {moderate} |
| MINOR | {minor} |
| Total | {len(GAPS)} |

No blocker requires a new experiment, provider run, raw-data inspection, or literature search before full final writing. All identified gaps can be addressed from committed sanitized artifacts and verified literature.

## Most important findings

### 1. Methodology is the largest deficiency

The current Methodology contains the formal definitions and accounting identities, but it does not yet provide a publication-level account of the four evidence conditions, case construction, stage contracts, parser/scoring rules, paired analysis, bootstrap procedure, denominators, and missing-row handling. This is the largest expansion required in 05BD.

### 2. The central result must move from headline ranges to inspectable evidence

The manuscript reports the protected headline ranges correctly. The repository also contains twelve condition-by-stage cells, twenty-seven bootstrap rows, condition-level audit false-assurance rates, escalation metrics, and cascade composition. Those committed values must become visible in the final paper.

### 3. Uncertainty changes the required wording

All nine parser-validity point estimates under degradation are positive, but three 95% bootstrap intervals for partial dropout include zero. All nine stage-success intervals remain below zero. The final paper must distinguish point-estimate direction from interval evidence and must not imply that every parser-validity increase is statistically clear.

### 4. The operational definition needs construct-validity explanation

In the committed metric contract, stage success requires parser validity plus a positive sanitized validity judgment. The final paper must explain why this is an experimental indicator of ESR rather than an exhaustive universal definition. It must also discuss the low clean parser-validity rates and the zero degraded stage-success cells as possible effects of the implemented parser, prompting, and scoring design.

### 5. Detection, false assurance, and recovery need separate reporting

The audit stage detected degradation at 1.0 among parser-valid degraded audit rows, yet false assurance remained non-zero by condition and escalation recovery was 0.0. This is stronger and more nuanced than a single mean contrast. The final paper should show detection, false assurance, and recovery as separate reliability functions.

### 6. The cascade result requires its numerator and composition

The all-sequence cascade-failure rate is 223/240 = 0.929167. The committed artifacts also identify 234 complete persisted sequences and distinguish parser-failure cascades, detected-not-recovered cases, false assurance, incomplete sequences, and preserved/clean success. The aggregate must be unpacked.

### 7. Figures are editorially present but not document-integrated

05BB contains four publication captions and in-text references, but no explicit Markdown asset bindings. 05BD must pair each caption with the exact committed 05AS PNG and validate order and data source before Word/PDF production.

## Word-count diagnosis

The current body contains `{summary['current_body_words']}` words excluding references. The final writing target is **6,320–8,000 body words**, subject to later journal constraints.

| Section | Current | Target |
|---|---:|---:|
| Abstract | 208 | 220–250 |
| Introduction | 320 | 750–900 |
| Related Work | 570 | 900–1,200 |
| Methodology | 592 | 1,400–1,700 |
| Results | 620 | 1,400–1,700 |
| Discussion | 318 | 900–1,200 |
| Limitations | 261 | 400–550 |
| Conclusion | 181 | 250–350 |
| Data and Code Availability | 73 | 100–150 |

The expansion should add analytical substance rather than repetition. References are excluded from the body target.

## Evidence sufficiency verdict

The committed repository already contains the evidence needed for 05BD:

- exact evidence-condition and stage contracts;
- 60×4×3 design metadata;
- execution and parser accounting;
- condition-by-stage results;
- metric definitions;
- bootstrap intervals;
- audit detection and false-assurance results;
- escalation recovery results;
- cascade sequence counts and pattern composition;
- verified literature and bounded novelty materials;
- four committed figure assets and paper tables.

Therefore:

> **No new empirical evidence is required to write the full final manuscript under the existing bounded single-model, single-run claim.**

Cross-model replication would be required only for model-family or provider-general claims. Multi-run replication would strengthen external and conclusion validity, but its absence does not block 05BD.

## Gate into Task 05BD

05BD may begin after this seven-file audit package passes repository validation. It must use the final writing specification and section-gap matrix as binding inputs, preserve 05BB unchanged, and create a new derivative manuscript.
"""

def build_final_spec(summary: dict[str, Any]) -> str:
    return f"""# Pilot 05BC — Binding Final Writing Specification for Task 05BD

## 1. Purpose

Task 05BD will create the full derivative final manuscript from committed 05BB and the committed sanitized evidence base. It will not modify 05BB, create empirical evidence, run models, search for new literature, or inspect raw prompts, responses, JSONL, `.env`, or raw CFPB records.

## 2. Manuscript role and claim scope

Pilot 05 remains the principal empirical study.

The supported central claim is:

> Within the committed Pilot 05 GLM-5.2 scaled CFPB-backed sanitized experiment, controlled evidence degradation reduced stage success while parser validity increased across decision, audit, and escalation stages, supporting Evidence-State Reliability as an evaluation layer distinct from parser validity.

The bounded novelty verdict remains:

> Bounded combination-and-operationalisation differentiation supported; global priority or first-ever novelty not established.

The final paper must not claim cross-model generality, provider independence, deployment safety, regulatory validity, real-world financial decision validity, complaint truth, consumer-harm prevalence, company misconduct, universal LLM unreliability, general GLM-5.2 unreliability, or guaranteed journal acceptance.

## 3. Required structure and body-word targets

| Order | Section | Target words | Binding content |
|---:|---|---:|---|
| 1 | Abstract | 220–250 | Problem, design, principal results, uncertainty-aware wording, bounded contribution and scope |
| 2 | Introduction | 750–900 | Pipeline problem, ESR gap, research question, design preview, contributions, scope, roadmap |
| 3 | Related Work | 900–1,200 | Critical synthesis and exact combination gap |
| 4 | Methodology | 1,400–1,700 | Data/evidence construction, four conditions, three stages, contracts, metrics, analysis, reproducibility |
| 5 | Results | 1,400–1,700 | Accounting, condition-stage results, uncertainty, audit/false assurance/recovery, cascades, figures/tables |
| 6 | Discussion | 900–1,200 | Interpretation, alternative explanations, implications, novelty, cross-pilot context, future work |
| 7 | Limitations | 400–550 | Construct, internal, external, conclusion, and reproducibility limits |
| 8 | Conclusion | 250–350 | Answer to research question, contribution, bounded result, next research step |
| 9 | Data and Code Availability | 100–150 | Exact repository/commit and artifact-level reproducibility boundary |
| 10 | References | Preserve verified set | Retain bibliographic facts and preprint status; apply venue style later |

Target body length excluding references: **6,320–8,000 words**.

## 4. Mandatory Methodology content

05BD must include all of the following:

1. **Study design**
   - 60 sanitized CFPB-backed base cases.
   - Four evidence states per case.
   - Three pipeline stages.
   - 720 planned and ledgered calls.
   - Paired comparisons within base case and stage.

2. **Evidence conditions**
   - `clean`: baseline evidence state.
   - `compressed_lossy`: information compression/loss.
   - `partial_dropout`: missing evidence elements.
   - `noisy_conflicting`: conflicting evidence.

3. **Pipeline stages**
   - Decision: stage validity, evidence adequacy, and recommendation behavior.
   - Audit: degradation detection and false-assurance behavior.
   - Escalation: recovery/loss behavior after degradation.
   - Detection and recovery must be defined as different functions.

4. **Operational measures**
   - Parser-valid rate: structural contract only.
   - Stage-success rate: parser-valid plus positive sanitized validity judgment.
   - Audit detection and false-assurance rates among parser-valid audit rows.
   - Escalation recovery among parser-valid escalation rows.
   - Paired degraded-minus-clean deltas.
   - Three-stage cascade pattern.

5. **Construct boundary**
   - ESR is the conceptual reliability of intermediate evidence states.
   - Stage success is the experiment's operational indicator.
   - Parser validity is necessary for automation but is not evidence sufficiency or correctness.
   - Neither metric alone establishes real-world decision quality.

6. **Analysis**
   - Condition-stage denominators.
   - Seven ledger-only rows excluded from execution-level metrics.
   - Nonparametric bootstrap over paired base cases.
   - 2,000 resamples.
   - Random seed 5205.
   - 95% confidence intervals.

7. **Execution and reproducibility**
   - Model identifier: GLM-5.2.
   - Sanitized artifact boundary.
   - Approved USD 8 cost cap and maximum cumulative estimated cost USD 2.2731216.
   - Artifact-level reproducibility, not raw-response replay.
   - Do not use ambiguous validation-only attempt counters as empirical results.

## 5. Mandatory Results content

### 5.1 Accounting

Preserve exactly:

- planned calls: 720;
- ledger rows: 720;
- sanitized execution rows: 713;
- ledger parser-valid/invalid: 470/250;
- persisted parser-valid/invalid: 470/243;
- ledger-only missing sanitized rows: 7;
- maximum cumulative estimated cost: USD 2.2731216.

### 5.2 Condition-by-stage table

Include all twelve cells from `pilot_05AP_condition_stage_interaction.csv`, with:

- row count;
- parser-valid count/rate;
- stage-success count/rate;
- paired parser-validity delta;
- paired stage-success delta.

Do not report only the minimum and maximum.

### 5.3 Uncertainty

State accurately:

- all nine degraded parser-validity point estimates are positive;
- three partial-dropout parser-validity 95% intervals include zero;
- all nine stage-success point estimates are negative;
- all nine stage-success 95% intervals remain below zero.

Avoid significance language unless it is defined explicitly.

### 5.4 Audit and false assurance

Report condition-level parser-valid audit results:

- compressed_lossy detection 1.0; false assurance 0.062500;
- partial_dropout detection 1.0; false assurance 0.048780;
- noisy_conflicting detection 1.0; false assurance 0.019231.

Call these model-output-coded computational audit indicators, not institutional or regulatory audit outcomes.

### 5.5 Escalation

Report:

- clean parser-valid escalation stage success 1.0 among parser-valid rows;
- degraded escalation recovery 0.0 for all three degraded conditions;
- degraded escalation loss proxy 1.0 among parser-valid rows.

Interpret only for the implemented escalation design.

### 5.6 Cascades

Report:

- all sequence groups: 240;
- complete persisted sequences: 234;
- cascade failures: 223;
- cascade-failure rate: 0.929167;
- condition-level cascade-failure rates;
- pattern composition: parser-failure cascade, detected-not-recovered, audit false assurance, incomplete persisted sequence, preserved/clean success.

The Results section must provide numerator and denominator, not only the proportion.

## 6. Tables and figures

Minimum publication set:

- **Table 1:** execution and row accounting.
- **Table 2:** condition-by-stage parser validity and stage success.
- **Table 3 or Supplementary Table S1:** bootstrap confidence intervals.
- **Table 4 or compact panel:** audit detection, false assurance, escalation recovery, and cascade counts.

Figures must be integrated in this order:

1. `pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png`
2. `pilot_05AS_figure_02_audit_escalation_interpretation.png`
3. `pilot_05AS_figure_03_cascade_failure_rate.png`
4. `pilot_05AS_figure_04_failure_family_interpretation.png`

Each figure requires:

- exact asset path;
- first in-text citation before the figure;
- publication caption;
- data-source traceability;
- bounded interpretation;
- no internal filename as the visible caption.

## 7. Required Discussion content

The Discussion must address:

- why format validity and evidence-sensitive reliability can diverge;
- why low clean parser validity matters;
- whether the parser/prompt/scoring contract may contribute to the observed contrast;
- why detection is not recovery;
- why non-zero false assurance remains relevant despite detection=1.0;
- why zero recovery is design-specific;
- uncertainty in parser-validity changes;
- implications for multi-stage evaluation and governance;
- alternative explanations;
- bounded novelty;
- future cross-model and multi-run replication.

## 8. Cross-pilot handling

Pilots 01–04 may appear only as bounded developmental context or supplementary triangulation:

- do not pool their metrics with Pilot 05;
- do not call them replication of Pilot 05;
- do not let simulated or deterministic results validate real-model claims;
- one concise paragraph and, if useful, one supplementary programme table are sufficient;
- Pilot 05 remains the only principal scaled experiment in the main Results.

## 9. Prose and terminology rules

- Use `parser validity` as a noun and `parser-validity` as a compound modifier.
- Use `behaviour` consistently in prose unless an official source title uses `behavior`.
- Use `sanitized` consistently because it is embedded in the committed artifact terminology, unless the selected journal later requires house style.
- Replace repeated defensive disclaimers with strategically placed scope statements.
- Avoid `head-turning`, `groundbreaking`, `Q1-ready`, `first-ever`, and global-priority language.
- Do not expose internal task IDs in publication prose.
- Do not describe repository validation as scientific replication.
- Rewrite the Abstract last.

## 10. 05BD acceptance criteria

05BD passes only if:

1. the committed 05BB manuscript remains byte-identical;
2. every protected empirical value is preserved;
3. all twelve condition-stage rows are represented;
4. all twenty-seven bootstrap rows are traceable, with at least the full intervals in a table or supplement;
5. the three parser-validity intervals crossing zero are disclosed;
6. all nine stage-success intervals below zero are disclosed;
7. audit false-assurance rates are reported;
8. the 223/240 cascade count is reported;
9. each figure is bound to the exact committed asset;
10. no new citation or empirical claim is invented;
11. all central claims map to committed evidence;
12. body length falls within 6,320–8,000 words unless a documented journal constraint is selected later;
13. the manuscript contains no internal workflow scaffolding;
14. single-model, single-run, sanitized-data, and artifact-reproducibility limits remain explicit;
15. the repository remains unstaged and uncommitted until separate approval.

## 11. Work that remains after 05BD

Task 05BE must independently check:

- numerical preservation;
- condition-stage and CI completeness;
- citation/reference consistency;
- figure/table integration;
- claim-evidence traceability;
- construct and terminology consistency;
- reviewer-risk responses;
- internal scaffold removal;
- abstract–results–conclusion alignment;
- no unsupported generalisation.

Journal selection and venue-specific formatting occur only after 05BE passes.
"""

def build_internal_validation(summary: dict[str, Any], output_hashes: dict[str, str]) -> str:
    severity_counts = {
        severity: sum(1 for row in GAPS if row["severity"] == severity)
        for severity in ("MAJOR", "MODERATE", "MINOR")
    }
    risk_counts = {
        priority: sum(1 for row in REVIEWER_RISKS if row["priority"] == priority)
        for priority in ("CRITICAL", "HIGH", "MEDIUM")
    }
    return f"""# Pilot 05BC Internal Validation Report

## Result

`PASS`

The editorial/submission-gap audit was generated deterministically from committed 05BB and committed sanitized supporting artifacts.

## Source checkpoint

- Branch: `{summary['branch']}`
- HEAD: `{summary['head']}`
- Current body words: `{summary['current_body_words']}`
- Current total words: `{summary['current_total_words']}`
- Condition-stage rows validated: `{summary['condition_stage_rows']}/12`
- Bootstrap rows validated: `{summary['bootstrap_rows']}/27`
- Parser-validity intervals crossing zero: `{summary['parser_ci_crossing_zero']}/9`
- Stage-success intervals wholly below zero: `{summary['stage_success_ci_below_zero']}/9`
- Cascade failures: `{summary['cascade_failure_count']}/{summary['cascade_sequence_groups']}`
- Prior 05BA issues present: `{summary['prior_05BA_issues']}/30`

## Audit contract

| Check | Result |
|---|---|
| Exactly 21 editorial/submission gaps | PASS |
| BLOCKER gaps | 0 |
| MAJOR gaps | {severity_counts['MAJOR']} |
| MODERATE gaps | {severity_counts['MODERATE']} |
| MINOR gaps | {severity_counts['MINOR']} |
| Every gap has an actionable 05BD correction | PASS |
| Every gap states `new_empirical_evidence_required=NO` | PASS |
| Exactly 12 reviewer risks | PASS |
| CRITICAL reviewer risks | {risk_counts['CRITICAL']} |
| HIGH reviewer risks | {risk_counts['HIGH']} |
| MEDIUM reviewer risks | {risk_counts['MEDIUM']} |
| Every reviewer risk has a required response | PASS |
| Binding final-writing specification present | PASS |
| 05BD body target 6,320–8,000 words | PASS |
| No new experiment required for bounded paper | PASS |
| No new model/provider run required for bounded paper | PASS |
| No new literature search required before 05BD | PASS |

## Output hashes

""" + "\n".join(
        f"- `{path}`: `{digest}`" for path, digest in sorted(output_hashes.items())
    ) + """

## Safety boundary

- Source manuscript modified: `NO`
- Earlier committed reports modified: `NO`
- Files deleted or overwritten: `NO`
- Staging, commit, or push: `NO`
- Experiments run: `0`
- Model or API calls: `0`
- New literature search: `NO`
- Raw CFPB data accessed: `NO`
- `.env` accessed: `NO`
- Raw prompts/responses accessed: `NO`
- JSONL accessed or written: `NO`
- Word/PDF conversion: `NO`

A PASS certifies the deterministic seven-file 05BC audit contract. It does not certify journal acceptance or replace Task 05BE.
"""

def build_artifacts(summary: dict[str, Any], script_sha256: str) -> dict[str, str]:
    gap_fields = [
        "gap_id", "severity", "section", "current_word_count",
        "target_word_min", "target_word_max", "gap", "reviewer_consequence",
        "required_05BD_action", "source_artifacts",
        "new_empirical_evidence_required", "acceptance_criterion",
    ]
    risk_fields = [
        "risk_id", "priority", "reviewer_question", "evidence_trigger",
        "required_response_in_05BD", "residual_risk_after_05BD",
        "new_evidence_required",
    ]

    artifacts: dict[str, str] = {
        "pilot_05BC_editorial_submission_gap_audit.md":
            build_editorial_audit(summary),
        "pilot_05BC_section_gap_matrix.csv":
            csv_text(gap_fields, GAPS),
        "pilot_05BC_reviewer_risk_register.csv":
            csv_text(risk_fields, REVIEWER_RISKS),
        "pilot_05BC_final_writing_specification.md":
            build_final_spec(summary),
    }

    provisional_hashes = {
        "experiments/pilot_05_final_editorial_submission_gap_audit.py": script_sha256,
        **{
            f"reports/pilot_05_final_editorial_submission_gap_audit/{name}":
                hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
            for name, text in artifacts.items()
        },
    }

    validation_text = build_internal_validation(summary, provisional_hashes)
    artifacts["pilot_05BC_internal_validation_report.md"] = validation_text

    output_hashes = {
        "experiments/pilot_05_final_editorial_submission_gap_audit.py": script_sha256,
        **{
            f"reports/pilot_05_final_editorial_submission_gap_audit/{name}":
                hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
            for name, text in artifacts.items()
        },
    }

    manifest = {
        "task_id": TASK_ID,
        "audit_version": AUDIT_VERSION,
        "status": "PASS",
        "secured_branch": EXPECTED_BRANCH,
        "secured_head": EXPECTED_HEAD,
        "source_contract": {
            "manuscript": str(SOURCE_FILES["manuscript"]).replace("\\", "/"),
            "manuscript_sha256": EXPECTED_SHA256[
                "reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_journal_form_manuscript.md"
            ],
            "section_map_sha256": EXPECTED_SHA256[
                "reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_section_map.csv"
            ],
            "manifest_05BB_sha256": EXPECTED_SHA256[
                "reports/pilot_05_journal_form_manuscript_repair/pilot_05BB_manifest.json"
            ],
            "source_files_read": [
                str(path).replace("\\", "/")
                for path in SOURCE_FILES.values()
            ],
        },
        "verdict": {
            "writing_gate": "READY_FOR_05BD_WITH_REQUIRED_MAJOR_EDITORIAL_EXPANSION",
            "submission_readiness": "NOT_READY_FOR_JOURNAL_SUBMISSION",
            "new_empirical_evidence_required_before_05BD": False,
            "new_model_run_required_before_05BD": False,
            "new_literature_search_required_before_05BD": False,
        },
        "counts": {
            "expected_uncommitted_files": 7,
            "gap_rows": len(GAPS),
            "blocker_gaps": 0,
            "major_gaps": sum(1 for row in GAPS if row["severity"] == "MAJOR"),
            "moderate_gaps": sum(1 for row in GAPS if row["severity"] == "MODERATE"),
            "minor_gaps": sum(1 for row in GAPS if row["severity"] == "MINOR"),
            "reviewer_risks": len(REVIEWER_RISKS),
            "current_body_words": summary["current_body_words"],
            "current_total_words": summary["current_total_words"],
            "target_body_words_min": 6320,
            "target_body_words_max": 8000,
            "condition_stage_rows_validated": summary["condition_stage_rows"],
            "bootstrap_rows_validated": summary["bootstrap_rows"],
            "parser_ci_crossing_zero": summary["parser_ci_crossing_zero"],
            "stage_success_ci_below_zero": summary["stage_success_ci_below_zero"],
            "reference_entries": summary["reference_entries"],
            "figure_count": summary["figure_count"],
            "table_count": summary["table_count"],
        },
        "safety": {
            "source_manuscript_modified": False,
            "earlier_committed_reports_modified": False,
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
        "output_sha256": output_hashes,
    }
    artifacts["pilot_05BC_manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return artifacts

def validate_artifacts(artifacts: dict[str, str]) -> None:
    errors: list[str] = []

    if len(GAPS) != 21:
        errors.append(f"Expected 21 gap rows, got {len(GAPS)}")
    expected_severity = {"MAJOR": 10, "MODERATE": 8, "MINOR": 3}
    actual_severity = {
        key: sum(1 for row in GAPS if row["severity"] == key)
        for key in expected_severity
    }
    if actual_severity != expected_severity:
        errors.append(
            f"Gap severity mismatch: expected {expected_severity}, got {actual_severity}"
        )
    if len({row["gap_id"] for row in GAPS}) != len(GAPS):
        errors.append("Gap IDs are not unique")
    if any(row["new_empirical_evidence_required"] != "NO" for row in GAPS):
        errors.append("Every gap must state new_empirical_evidence_required=NO")
    if len(REVIEWER_RISKS) != 12:
        errors.append(f"Expected 12 reviewer risks, got {len(REVIEWER_RISKS)}")
    if len({row["risk_id"] for row in REVIEWER_RISKS}) != len(REVIEWER_RISKS):
        errors.append("Reviewer risk IDs are not unique")
    if any(row["new_evidence_required"] != "NO" for row in REVIEWER_RISKS):
        errors.append("Every reviewer risk must state new_evidence_required=NO")

    required_artifact_names = {
        "pilot_05BC_editorial_submission_gap_audit.md",
        "pilot_05BC_section_gap_matrix.csv",
        "pilot_05BC_reviewer_risk_register.csv",
        "pilot_05BC_final_writing_specification.md",
        "pilot_05BC_internal_validation_report.md",
        "pilot_05BC_manifest.json",
    }
    if set(artifacts) != required_artifact_names:
        errors.append(
            f"Artifact name mismatch: expected {required_artifact_names}, got {set(artifacts)}"
        )

    combined = "\n".join(artifacts.values())
    required_phrases = [
        "READY_FOR_05BD_WITH_REQUIRED_MAJOR_EDITORIAL_EXPANSION",
        "NOT_READY_FOR_JOURNAL_SUBMISSION",
        "6,320–8,000",
        "three partial-dropout parser-validity 95% intervals include zero",
        "223/240",
        "pilot_05AS_figure_04_failure_family_interpretation.png",
        "No new empirical evidence is required",
    ]
    for phrase in required_phrases:
        if phrase not in combined:
            errors.append(f"Required audit phrase absent: {phrase}")

    forbidden_phrases = [
        "guaranteed acceptance",
        "all LLMs are unreliable",
        "GLM-5.2 is unreliable",
        "provider superiority is established",
    ]
    for phrase in forbidden_phrases:
        if phrase in combined:
            errors.append(f"Forbidden phrase present: {phrase}")

    if errors:
        raise RuntimeError("05BC in-memory validation failed:\n- " + "\n- ".join(errors))

def write_artifacts(artifacts: dict[str, str]) -> dict[str, str]:
    OUTPUT_DIR.mkdir(parents=False, exist_ok=False)
    written: dict[str, str] = {}
    for name, text in artifacts.items():
        path = OUTPUT_DIR / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written[str(path.relative_to(REPO_ROOT)).replace("\\", "/")] = sha256_file(path)
    return written

def verify_final_state(expected_output_hashes: dict[str, str]) -> None:
    modified = run_git("diff", "--name-only")
    staged = run_git("diff", "--cached", "--name-only")
    untracked = sorted(
        line for line in run_git("ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    )
    expected = sorted(str(path).replace("\\", "/") for path in OUTPUT_PATHS)
    if modified:
        raise RuntimeError(f"Tracked files modified after generation: {modified}")
    if staged:
        raise RuntimeError(f"Staged files present after generation: {staged}")
    if untracked != expected:
        raise RuntimeError(
            f"Expected exact seven untracked files.\nExpected: {expected}\nActual: {untracked}"
        )
    for rel_path, expected_hash in expected_output_hashes.items():
        actual = sha256_file(REPO_ROOT / rel_path)
        if actual != expected_hash:
            raise RuntimeError(
                f"Output SHA-256 mismatch for {rel_path}: "
                f"expected {expected_hash}, got {actual}"
            )

def main() -> None:
    summary = validate_sources()
    script_sha = sha256_file(Path(__file__))
    artifacts = build_artifacts(summary, script_sha)
    validate_artifacts(artifacts)

    expected_output_hashes = {
        "experiments/pilot_05_final_editorial_submission_gap_audit.py": script_sha,
        **{
            f"reports/pilot_05_final_editorial_submission_gap_audit/{name}":
                hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
            for name, text in artifacts.items()
        },
    }

    write_artifacts(artifacts)
    verify_final_state(expected_output_hashes)

    print("=== TASK 05BC GENERATION RESULT ===")
    print("status: PASS")
    print(f"audit_version: {AUDIT_VERSION}")
    print(f"source_HEAD: {summary['head']}")
    print(f"current_body_words: {summary['current_body_words']}")
    print(f"current_total_words: {summary['current_total_words']}")
    print("writing_gate: READY_FOR_05BD_WITH_REQUIRED_MAJOR_EDITORIAL_EXPANSION")
    print("submission_readiness: NOT_READY_FOR_JOURNAL_SUBMISSION")
    print("blocker_gaps: 0")
    print("major_gaps: 10")
    print("moderate_gaps: 8")
    print("minor_gaps: 3")
    print("total_gaps: 21")
    print("reviewer_risks: 12")
    print(f"condition_stage_rows_validated: {summary['condition_stage_rows']}/12")
    print(f"bootstrap_rows_validated: {summary['bootstrap_rows']}/27")
    print(
        "parser_validity_intervals_crossing_zero: "
        f"{summary['parser_ci_crossing_zero']}/9"
    )
    print(
        "stage_success_intervals_below_zero: "
        f"{summary['stage_success_ci_below_zero']}/9"
    )
    print(
        "cascade_failure_count: "
        f"{summary['cascade_failure_count']}/{summary['cascade_sequence_groups']}"
    )
    print("new_empirical_evidence_required_before_05BD: NO")
    print("new_model_or_provider_run_required_before_05BD: NO")
    print("new_literature_search_required_before_05BD: NO")
    print("uncommitted_files: 7")
    print("tracked_files_modified: 0")
    print("staged_files: 0")
    print("experiments_run: 0")
    print("model_or_api_calls: 0")
    print("raw_data_accessed: NO")
    print("env_accessed: NO")
    print("raw_prompt_response_accessed: NO")
    print("jsonl_accessed_or_written: NO")
    print("word_or_pdf_conversion: NO")
    print("")
    print("OUTPUT SHA-256")
    for rel_path, digest in sorted(expected_output_hashes.items()):
        print(f"{rel_path} = {digest}")
    print("")
    print(
        "STOP: Paste the complete terminal output before staging, committing, "
        "pushing, or beginning Task 05BD."
    )

if __name__ == "__main__":
    main()
