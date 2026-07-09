# Pilot 05 — Scaled Results Interpretation Report (Task 05AR)

Generated: 2026-07-09T17:04:08.654557+00:00
Source commit: be8155f (Add Pilot 05 scaled GLM-5.2 execution metrics)

## Headline finding
Across 720 planned GLM-5.2 calls over CFPB-backed sanitized evidence states, degraded evidence conditions produced consistently negative paired deltas in stage success while parser validity increased. This divergence supports Evidence-State Reliability as a distinct evaluation layer from parser validity in multi-stage LLM decision pipelines.

## Boundary statement
This is a controlled scaled pilot, not a deployment validation, not a proof of real-world financial safety, and not a broad claim about GLM-5.2 or LLM reliability.

## Q&A

**1. What did the scaled GLM-5.2 Pilot 05 actually show?**
Across 720 planned calls, degraded evidence conditions produced
negative stage-success deltas and positive parser-validity deltas, indicating the two
layers move in opposite directions under degradation.

**2. What is the main empirical result?**
The divergence between stage success (declines) and parser validity (increases) under
evidence degradation.

**3. Why is parser validity not enough?**
Because outputs can remain parser-valid while the evidence backing them has degraded,
parser validity alone cannot certify evidence-state reliability.

**4. How do stage success and evidence-state adequacy behave under degradation?**
They deteriorate consistently, with deltas ranging from -0.517241
to -0.40678, all negative.

**5. What does the audit stage detect?**
Audit detected degraded evidence among parser-valid degraded cases at a rate of
1.0.

**6. What does the escalation stage fail to recover?**
Escalation recovered 0.0 of degraded cases in this run (0.0),
meaning detection did not translate into correction.

**7. What cascade-level pattern appears?**
A cascade failure rate of 0.929167 across
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
