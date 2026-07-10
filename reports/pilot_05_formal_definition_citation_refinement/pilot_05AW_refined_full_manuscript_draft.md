<!--
Task 05AW editorial refinement.
Source boundary: committed 05AV outputs only.
Task 05AW performs manuscript-structure, notation, citation-placeholder, related-work-slot, academic-wording, threats-to-validity, and claim-boundary refinement only. It does not create, infer, or add new empirical evidence.
Citation identifiers in square brackets are unresolved placeholders, not citations.
-->

# Evidence-State Reliability in Multi-Stage LLM Decision Pipelines

## Manuscript status

Draft assembled by Task 05AV from committed 05AU synthesis artifacts only. This draft does not create new empirical evidence.

## Abstract

LLM evaluation commonly emphasizes final-output validity, parser compliance, or answer-level correctness. In multi-stage decision pipelines, however, downstream outputs may remain parser-valid even when the evidence state reaching the downstream stage has been degraded. This study introduces Evidence-State Reliability as a reliability layer concerned with whether intermediate evidence states remain sufficiently complete, grounded, and usable across a multi-stage LLM decision pipeline. Using committed Pilot 05 outputs only, the study analyzes a sanitized, CFPB-backed, scaled GLM-5.2 pipeline experiment with controlled evidence-state degradation across decision, audit, and escalation stages. The central result is a divergence between parser validity and evidence-state reliability: parser validity improves under degraded evidence while stage/evidence success deteriorates. This supports the paper's core claim that parser validity is not a sufficient proxy for evidence-state reliability. The contribution is a reproducible empirical framing for reliability cascades in multi-stage LLM decision systems, with paper-ready tables, figures, claim boundaries, and repo-wide validation artifacts.

## Keywords

Evidence-State Reliability; Reliability Cascades; LLM Evaluation; Multi-Stage Decision Pipelines; Parser Validity; Auditability; Escalation; CFPB; Reproducibility; GLM-5.2

## 1. Introduction

Multi-stage LLM decision systems do not only fail at the final answer layer. They can also fail when the evidence state passed from one stage to another becomes degraded, incomplete, or misleading while the downstream output remains structurally parser-valid. This creates a reliability problem that is easy to miss if evaluation stops at final-output parsability.

The problem is especially important in decision pipelines where an upstream evidence packet informs downstream decision, audit, and escalation behavior. A parser-valid output can satisfy the required schema while still being grounded in a degraded evidence state. In such cases, parser validity may provide a false sense of operational reliability.

This paper frames that problem as Evidence-State Reliability. Evidence-State Reliability is the reliability of the intermediate evidence state used by downstream stages in a decision pipeline. It is distinct from final-output validity, parser compliance, and answer-level surface correctness.

The central research question is:

**How can Evidence-State Reliability be measured separately from final parser validity in a multi-stage LLM decision pipeline?**

The core claim is bounded:

Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity.

The strongest empirical pattern is that parser validity can improve while evidence-state reliability deteriorates. This makes the work more than another LLM error-analysis exercise. The paper targets a reliability layer that parser-level checks can miss.

## 2. Conceptual framing

### 2.1 Evidence-State Reliability

Evidence-State Reliability refers to whether the evidence state passed through a decision pipeline remains complete, grounded, and usable enough for downstream stages. It is not the same as parser validity. Parser validity is a structural signal: it tells us whether the output satisfies a required schema. It does not tell us whether the evidence used by the pipeline was reliable.

### 2.2 Reliability cascades

A reliability cascade occurs when degradation at one stage changes downstream behavior across decision, audit, or escalation stages. In this framing, the unit of concern is not only the final answer. The concern is the pipeline state that connects stages.

### 2.3 Parser validity boundary

Parser validity means the output fits a required parser or schema contract. It must not be interpreted as answer correctness. It must also not be treated as evidence that the upstream evidence state was complete or reliable.

## 3. Methods

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

| metric | value | unit_or_type | paper_ready |
| --- | --- | --- | --- |
| call_plan_rows | 720 | count | yes |
| ledger_rows | 720 | count | yes |
| sanitized_execution_rows | 713 | count | yes |
| parser_invalid_summary_rows | 243 | count | yes |
| ledger_parser_valid_true | 470 | count | yes |
| ledger_parser_valid_false | 250 | count | yes |
| persisted_parser_valid_true | 470 | count | yes |
| persisted_parser_valid_false | 243 | count | yes |
| ledger_only_missing_sanitized_rows | 7 | count | yes, disclosed as limitation |
| max_cumulative_estimated_cost_usd | 2.2731216 | USD | yes |
| stage_success_delta_min | -0.517241 | proportion_delta | yes |
| stage_success_delta_max | -0.40678 | proportion_delta | yes |


## Metric validation table used by this synthesis

| metric | source | validation_note |
| --- | --- | --- |
| call_plan_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| sanitized_execution_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| parser_invalid_summary_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_parser_valid_true | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_parser_valid_false | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| persisted_parser_valid_true | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| persisted_parser_valid_false | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_only_missing_sanitized_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| max_cumulative_estimated_cost_usd | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| stage_success_delta_min | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| stage_success_delta_max | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |


## Reproducibility controls

The committed 05AT audit verifies the repo checkpoint, committed file contracts, manifest safety flags, operation-aware script safety scan, forbidden-file audit, figure integrity, input-index validation, and claim-boundary audit. 05AU uses these committed artifacts as its source boundary.

## No-new-evidence rule

05AU is a manuscript synthesis task. It does not create new empirical results. All methodological and results-language in this package must trace back to committed 05AR, 05AS, or 05AT artifacts.

## 4. Results

## Results overview

The committed run is organized around 720 planned/ledgered pipeline calls. The sanitized execution layer contains 713 retained rows after parser and execution accounting. The stage-success degradation range is reported as -0.517241 to -0.40678. The parser-validity delta range is reported as 0.067797 to 0.368421. The all-sequence cascade-failure rate is reported as 0.929167. The degraded audit detection mean is reported as 1.0. The degraded escalation recovery mean is reported as 0.0.

The central empirical finding is a divergence between parser validity and evidence-state reliability. Under controlled evidence-state degradation, parser validity improves while stage/evidence success deteriorates. This means parser validity cannot be used as a sufficient proxy for reliability in this pipeline.

## Result 1: Parser validity diverges from evidence-state reliability

The committed parser-versus-evidence-state table supports the paper's main contrast: parser-validity behavior and evidence-state reliability do not move together under degradation.

| comparison_group | metric | value | source_file | source_column |
| --- | --- | --- | --- | --- |
|  | value | 243.0 | pilot_05AR_paper_ready_main_results_table.csv | value |
|  | value | 470.0 | pilot_05AR_paper_ready_main_results_table.csv | value |
|  | value | 250.0 | pilot_05AR_paper_ready_main_results_table.csv | value |
|  | value | 470.0 | pilot_05AR_paper_ready_main_results_table.csv | value |


### Interpretation

This is the central head-turning result. A system may become more parser-valid under degraded evidence while becoming less reliable at the evidence-state layer. That pattern is exactly why Evidence-State Reliability needs to be measured separately from final-output parser validity.

## Result 2: Audit and escalation expose downstream cascade behavior

The audit and escalation outputs show how degradation affects downstream pipeline behavior after the initial decision stage.

| label | metric | value | source_file | source_column |
| --- | --- | --- | --- | --- |
| audit_detection_rate_degraded_mean | observed_rate | 1.0 | pilot_05AR_audit_escalation_interpretation.csv | observed_rate |
| escalation_recovery_rate_degraded_mean | observed_rate | 0.0 | pilot_05AR_audit_escalation_interpretation.csv | observed_rate |


### Interpretation

The audit/escalation layer is important because a downstream stage may detect degradation without recovering from it. The distinction between detection and recovery should be explicit in the paper.

## Result 3: Cascade failure rate summarizes pipeline-level reliability loss

The cascade-failure output provides a pipeline-level view of how often reliability loss propagates across sequence groups.

| label | metric | value | source_file | source_column |
| --- | --- | --- | --- | --- |
| cascade_failure_rate_all_sequence_groups | value | 0.929167 | pilot_05AR_cascade_failure_interpretation.csv | value |


### Interpretation

Cascade failure should be framed as a pipeline reliability phenomenon, not as a model-general claim. The study shows this behavior within the committed Pilot 05 design.

## Result 4: Failure-family interpretation clarifies where degradation concentrates

The failure-family interpretation separates different kinds of reliability failures instead of collapsing them into a single final-output score.

| failure_family | value | source_file | source_column |
| --- | --- | --- | --- |
| Detected-but-unrecovered degradation | 1.0 | pilot_05AR_failure_family_interpretation.csv | row_presence_count_fallback |
| Parser-valid / evidence-invalid divergence | 1.0 | pilot_05AR_failure_family_interpretation.csv | row_presence_count_fallback |
| Missing-sanitized-row gap | 1.0 | pilot_05AR_failure_family_interpretation.csv | row_presence_count_fallback |


### Interpretation

Failure-family structure helps make the paper stronger because it shows that reliability loss is not monolithic. Different pipeline stages and reliability layers can fail in different ways.

## Results claim boundary

The results support the Evidence-State Reliability distinction within the committed Pilot 05 GLM-5.2 experiment. They do not establish broad GLM reliability, general LLM reliability, CFPB-backed experimental validity, regulatory validity, deployment safety, or consumer harm prevalence.

## 5. Contribution and novelty

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

Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity.

## What makes the work potentially head-turning

The result challenges a comfortable assumption: a cleaner, parser-valid output is not necessarily a more reliable decision-system output. In this experiment, parser validity can improve precisely when evidence-state reliability gets worse. That is the paper's strongest empirical and conceptual hook.

## Claim boundary

The contribution is a bounded empirical and methodological contribution. It should not be framed as a universal claim about GLM-5.2, the evaluated GLM-5.2 pipeline, all financial decision systems, or deployment safety.

## 6. Tables and figures

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

# Pilot 05AS Figure Caption Pack

These captions are generated from committed 05AR outputs and preserve bounded claim language.

## pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png

Figure 1. Parser-vs-evidence-state divergence under controlled degradation. The figure is generated from committed 05AR outputs and supports the bounded claim that parser validity and Evidence-State Reliability are separate evaluation layers in this Pilot 05 run.

## pilot_05AS_figure_02_audit_escalation_interpretation.png

Figure 2. Audit/escalation behavior in the controlled Pilot 05 run. The interpretation is intentionally bounded: degraded evidence can be detected, but escalation recovery was not observed as successful recovery in this run.

## pilot_05AS_figure_03_cascade_failure_rate.png

Figure 3. Cascade-failure interpretation from committed 05AR outputs. The figure supports the manuscript need to measure evidence-state, decision, audit, escalation, and sequence-level behavior separately.

## pilot_05AS_figure_04_failure_family_interpretation.png

Figure 4. Failure-family interpretation from committed 05AR outputs. This is a descriptive reliability-cascade diagnostic and does not imply broad model, provider, regulatory, or real-world harm claims.


## Source paper table pack

# Pilot 05AS Paper Table Pack

Generated from committed 05AR interpretation outputs.

## Final main results table

| metric | value | unit_or_type | paper_ready |
| --- | --- | --- | --- |
| call_plan_rows | 720 | count | yes |
| ledger_rows | 720 | count | yes |
| sanitized_execution_rows | 713 | count | yes |
| parser_invalid_summary_rows | 243 | count | yes |
| ledger_parser_valid_true | 470 | count | yes |
| ledger_parser_valid_false | 250 | count | yes |
| persisted_parser_valid_true | 470 | count | yes |
| persisted_parser_valid_false | 243 | count | yes |
| ledger_only_missing_sanitized_rows | 7 | count | yes, disclosed as limitation |
| max_cumulative_estimated_cost_usd | 2.2731216 | USD | yes |
| stage_success_delta_min | -0.517241 | proportion_delta | yes |
| stage_success_delta_max | -0.40678 | proportion_delta | yes |
| parser_valid_delta_min | 0.067797 | proportion_delta | yes |
| parser_valid_delta_max | 0.368421 | proportion_delta | yes |
| audit_detection_rate_degraded_mean | 1.0 | proportion | yes |
| escalation_recovery_rate_degraded_mean | 0.0 | proportion | yes |
| cascade_failure_rate_all_sequence_groups | 0.929167 | proportion | yes |


## Claim-boundary table

| claim_type | status | wording |
| --- | --- | --- |
| allowed_bounded_claim | permitted | Pilot 05 gives a scaled empirical basis for the paper's core claim direction: final structural/parser validity is insufficient for evaluating multi-stage LLM decision systems because evidence-state degradation can produce downstream reliability cascades that are visible only when evidence-state adequacy, stage success, audit behavior, escalation recovery, and cascade sequence behavior are measured separately. |
| headline_wording | required_exact | Across 720 planned GLM-5.2 calls over CFPB-backed sanitized evidence states, degraded evidence conditions produced consistently negative paired deltas in stage success while parser validity increased. This divergence supports Evidence-State Reliability as a distinct evaluation layer from parser validity in multi-stage LLM decision pipelines. |
| boundary_wording | required_exact | This is a controlled scaled pilot, not a deployment validation, not a proof of CFPB-backed experimental safety, and not a broad claim about GLM-5.2 or LLM reliability. |
| broad_GLM_reliability_claim | not_permitted | Do not claim. |
| general_LLM_reliability_claim | not_permitted | Do not claim. |
| model_provider_superiority_claim | not_permitted | Do not claim. |
| real_world_financial_validity_claim | not_permitted | Do not claim. |
| regulatory_validity_claim | not_permitted | Do not claim. |
| deployment_safety_claim | not_permitted | Do not claim. |
| consumer_harm_prevalence_claim | not_permitted | Do not claim. |
| company_misconduct_claim | not_permitted | Do not claim. |
| parser_validity_equals_correctness_claim | not_permitted | Do not claim. |
| full_paper_finished_claim | not_permitted | Do not claim. |
| Q1_acceptance_or_groundbreaking_claim | not_permitted | Do not claim. |


## Limitations and validity threats

| limitation | detail |
| --- | --- |
| Missing sanitized rows | 7 ledger rows have no corresponding sanitized execution row; excluded from execution-level metrics. |
| Single-model scope | Results reflect GLM-5.2 only; not generalized to other models. |
| Single pilot scale | 720 planned calls in one pilot run; not a multi-run replication yet. |
| Sanitized-data dependency | All evidence is CFPB-backed but sanitized; not raw production data. |
| No deployment context | No claims about real-world deployment, regulatory, or financial validity. |
| Escalation recovery observed as zero | May reflect this pilot's escalation design, not a general property of escalation mechanisms. |



## Suggested results-section callout wording

- "Figure 1 shows that parser-validity behavior diverges from evidence-state reliability under degradation."
- "Figure 2 separates audit detection from escalation recovery, preventing detection from being mistaken for recovery."
- "Figure 3 summarizes the pipeline-level cascade-failure pattern."
- "Figure 4 shows that degradation is distributed across failure families rather than reducible to a single output-validity failure."

## Caption discipline

Captions should avoid model-general claims. Every caption should remain bounded to the committed Pilot 05 setup.

## 7. Claim boundary and limitations

## Safe central claim

Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity.

## Do not claim

- broad GLM reliability
- general LLM reliability
- model/provider superiority
- CFPB-backed experimental validity
- regulatory validity
- deployment safety
- consumer harm prevalence
- company misconduct
- parser validity equals answer correctness
- Q1 acceptance or paper completion

## Claim-boundary table from committed outputs

| claim_type | status | wording |
| --- | --- | --- |
| allowed_bounded_claim | permitted | Pilot 05 gives a scaled empirical basis for the paper's core claim direction: final structural/parser validity is insufficient for evaluating multi-stage LLM decision systems because evidence-state degradation can produce downstream reliability cascades that are visible only when evidence-state adequacy, stage success, audit behavior, escalation recovery, and cascade sequence behavior are measured separately. |
| headline_wording | required_exact | Across 720 planned GLM-5.2 calls over CFPB-backed sanitized evidence states, degraded evidence conditions produced consistently negative paired deltas in stage success while parser validity increased. This divergence supports Evidence-State Reliability as a distinct evaluation layer from parser validity in multi-stage LLM decision pipelines. |
| boundary_wording | required_exact | This is a controlled scaled pilot, not a deployment validation, not a proof of CFPB-backed experimental safety, and not a broad claim about GLM-5.2 or LLM reliability. |
| broad_GLM_reliability_claim | not_permitted | Do not claim. |
| general_LLM_reliability_claim | not_permitted | Do not claim. |
| model_provider_superiority_claim | not_permitted | Do not claim. |
| real_world_financial_validity_claim | not_permitted | Do not claim. |
| regulatory_validity_claim | not_permitted | Do not claim. |
| deployment_safety_claim | not_permitted | Do not claim. |
| consumer_harm_prevalence_claim | not_permitted | Do not claim. |
| company_misconduct_claim | not_permitted | Do not claim. |
| parser_validity_equals_correctness_claim | not_permitted | Do not claim. |
| full_paper_finished_claim | not_permitted | Do not claim. |
| Q1_acceptance_or_groundbreaking_claim | not_permitted | Do not claim. |


## Limitations table from committed outputs

| limitation | detail |
| --- | --- |
| Missing sanitized rows | 7 ledger rows have no corresponding sanitized execution row; excluded from execution-level metrics. |
| Single-model scope | Results reflect GLM-5.2 only; not generalized to other models. |
| Single pilot scale | 720 planned calls in one pilot run; not a multi-run replication yet. |
| Sanitized-data dependency | All evidence is CFPB-backed but sanitized; not raw production data. |
| No deployment context | No claims about real-world deployment, regulatory, or financial validity. |
| Escalation recovery observed as zero | May reflect this pilot's escalation design, not a general property of escalation mechanisms. |


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

## 8. Reproducibility statement

## Repository checkpoint

- latest_commit: `725c8dd Add Pilot 05 repo validation audit`
- latest_hash: `725c8dd`
- latest_subject: `Add Pilot 05 repo validation audit`
- origin_main_alignment: `0 behind, 0 ahead`

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

## 9. Discussion

The Pilot 05 results motivate a shift in how multi-stage LLM decision systems are evaluated. A parser-valid output should not be treated as a reliable output unless the evidence state that produced it is also evaluated. In this study, the divergence between parser validity and evidence-state reliability is the main reliability signal.

This matters because production-style LLM pipelines often contain multiple handoffs: evidence is summarized, transformed, checked, audited, escalated, and interpreted. If evaluation only checks whether the final object is parseable, it may miss reliability loss that occurred earlier in the pipeline.

The Evidence-State Reliability framing therefore supports three practical evaluation requirements. First, evaluators should track evidence-state quality separately from output-format validity. Second, they should measure whether degradation propagates across stages. Third, they should distinguish detection from recovery, because a system may detect degraded evidence without successfully recovering from it.

## 10. Conclusion

This manuscript draft argues that Evidence-State Reliability should be evaluated separately from parser validity in multi-stage LLM decision systems. Within the committed Pilot 05 GLM-5.2 setup, controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. The key result is that parser validity improves while stage/evidence success deteriorates. That pattern supports the paper's main thesis: parser validity is not a sufficient proxy for evidence-state reliability.

## Appendix A. Next revision roadmap

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

## Appendix B. Assembly checkpoint

- latest_commit: `10465f5 Add Pilot 05 manuscript synthesis`
- latest_hash: `10465f5`
- latest_subject: `Add Pilot 05 manuscript synthesis`
- origin_main_alignment: `0 behind, 0 ahead`

## Appendix C. Do-not-claim boundary

- broad GLM reliability
- general LLM reliability
- model/provider superiority
- CFPB-backed experimental validity
- regulatory validity
- deployment safety
- consumer harm prevalence
- company misconduct
- parser validity equals answer correctness
- Q1 acceptance or paper completion

---

## Formal Definitions and Notation

The manuscript distinguishes evidence-state reliability from structural output
validity. Let \(E_{i,c,k}\) denote the evidence state supplied to case \(i\),
condition \(c\), and stage \(k\); let \(V_{i,c,k}\) indicate parser validity;
and let \(R_{i,c,k}\) indicate stage/evidence success under the committed Pilot 05
scoring contract.

For condition \(c\) and stage \(k\),

\[
\widehat{\mathrm{PV}}_{c,k}
=
\frac{1}{N_c}\sum_{i=1}^{N_c}V_{i,c,k},
\qquad
\widehat{\mathrm{ESR}}_{c,k}
=
\frac{1}{N_c}\sum_{i=1}^{N_c}R_{i,c,k}.
\]

The central analytical distinction is that
\(\widehat{\mathrm{PV}}_{c,k}\) measures machine-readable structural
conformance, whereas \(\widehat{\mathrm{ESR}}_{c,k}\) measures success under an
evidence-sensitive stage criterion. A parser-valid output may therefore remain
evidence-unsuccessful. Full definitions and claim qualifications are provided in
the companion 05AW formalisation artefact.

[CIT-ESR-01] [CIT-PARSER-01] [CIT-PIPELINE-01]

---

## Related Work Structure

The final literature review should position this study across seven bounded areas:
output-level versus process-level reliability; multi-stage LLM pipelines; cascading
failure and error propagation; audit and assurance; uncertainty and escalation;
consumer-finance data provenance; and reproducible computational evaluation.

No external literature was searched during Task 05AW. The following identifiers are
unresolved placeholders rather than citations:
[CIT-ESR-01], [CIT-CASCADE-01], [CIT-PIPELINE-01], [CIT-PARSER-01],
[CIT-AUDIT-01], [CIT-UNCERTAINTY-01], [CIT-FINAI-01], [CIT-CFPB-01],
[CIT-VALIDITY-01], and [CIT-REPRO-01].

---

## Threats to Validity

### Construct validity

Evidence-State Reliability is operationalised through the committed Pilot 05
stage/evidence criteria. Parser validity captures structural conformance only, and
the controlled degradation conditions do not represent every form of real-world
evidence loss or ambiguity.

### Internal validity

The result is conditional on the committed prompts, pipeline ordering, parser,
scoring rules, runtime, and model configuration. Sanitization and the prohibition on
raw-response access prevent qualitative reinspection in this refinement task.

### External validity

The main evidence is bounded to the evaluated GLM-5.2 configuration, selected
CFPB-backed cases, defined evidence conditions, and experimental decision-audit-
escalation pipeline. It does not establish deployment, jurisdictional, provider,
model-family, or financial-decision generality.

### Conclusion validity

The central pattern is descriptive of the committed run. Final reporting must
preserve denominators, absolute rates, condition deltas, and metric distinctions.
Experimental failure rates must not be converted into prevalence estimates for
consumer harm, company misconduct, or deployed-system failure.

### Reproducibility limitations

Committed sanitized outputs permit artefact-level validation but not raw prompt or
response replay. Citation placeholders remain unresolved pending an explicitly
approved literature-search task.

[CIT-VALIDITY-01] [CIT-REPRO-01]

---

## Claim Boundary

The strongest supported interpretation is:

> Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that
> controlled evidence-state degradation produces measurable reliability-layer
> changes across decision, audit, and escalation stages. In this run, parser
> validity improved under degraded evidence while stage/evidence success
> deteriorated, supporting Evidence-State Reliability as distinct from parser
> validity.

This result does not establish broad GLM reliability, general LLM reliability,
provider superiority, real-world financial validity, regulatory validity,
deployment safety, consumer-harm prevalence, company misconduct, or equivalence
between parser validity and answer correctness.
