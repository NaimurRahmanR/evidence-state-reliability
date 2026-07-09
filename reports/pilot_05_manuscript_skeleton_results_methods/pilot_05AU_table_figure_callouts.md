# Pilot 05AU Table and Figure Callouts

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
| boundary_wording | required_exact | This is a controlled scaled pilot, not a deployment validation, not a proof of real-world financial safety, and not a broad claim about GLM-5.2 or LLM reliability. |
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
